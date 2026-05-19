"""Rollback and safe-exit plan generator (Issue #58).

This module produces *informational* rollback plans from a run. It records
every meaningful side effect SendSprint touched during a delivery — git
worktrees, branches, commits, pushes, PRs, releases, tags, and tracker
status updates — and renders a Markdown section that fits inside a PR body
or human review pack so a reviewer can stop or unwind the change safely.

It deliberately does NOT execute destructive local operations. The plan is
a checklist; the operator (or a higher-level policy gate) chooses what to
run. See ADR ideas in #58 acceptance criteria.

Typical flow:

    from sendsprint.rollback import build_rollback_plan, pr_body_rollback_section

    plan = build_rollback_plan(run_report, delivery_plan=plan, run_id="abc")
    pr_body += pr_body_rollback_section(plan)

The output is small and stable enough to embed in evidence bundles and in
live activity (`safe_stop_points`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

from sendsprint.models.reports import PrInfo, RunReport, StepReport

if TYPE_CHECKING:
    from sendsprint.planning import DeliveryPlan, PlannedDelivery

ActionKind = Literal[
    "worktree",
    "branch",
    "commit",
    "push",
    "pr",
    "tag",
    "release",
    "issue_update",
    "file",
    "artifact",
]


class RollbackAction(BaseModel):
    """One reversible (or noteworthy) side effect SendSprint touched.

    `destructive` flags actions whose rollback would mutate shared state
    (PR close, release delete, tag delete, force-push) — those always carry
    `requires_approval=True` so the operator must opt in.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ActionKind
    target: str
    note: str
    instruction: str
    destructive: bool = False
    requires_approval: bool = False


class RollbackPlan(BaseModel):
    """Plan that explains how to undo or safely stop a SendSprint run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    run_id: str | None = None
    actions: list[RollbackAction] = Field(default_factory=list)
    safe_stop_points: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def has_destructive(self) -> bool:
        return any(a.destructive for a in self.actions)

    @property
    def requires_approval(self) -> bool:
        return any(a.requires_approval for a in self.actions)

    def to_markdown(self) -> str:
        """Render the plan as a Markdown block suitable for PR bodies."""
        if not self.actions and not self.safe_stop_points and not self.notes:
            return "_No reversible side effects recorded for this run._"

        lines: list[str] = []
        if self.actions:
            lines.append("**Actions executed (reverse order):**")
            for action in self.actions:
                badge = " ⚠ destructive" if action.destructive else ""
                gate = " 🔒 requires approval" if action.requires_approval else ""
                lines.append(
                    f"- **[{action.kind}]** {action.note}{badge}{gate}\n"
                    f"  - target: `{action.target}`\n"
                    f"  - rollback: `{action.instruction}`"
                )
            lines.append("")
        if self.safe_stop_points:
            lines.append("**Safe stop points:**")
            lines.extend(f"- {p}" for p in self.safe_stop_points)
            lines.append("")
        if self.notes:
            lines.append("**Notes:**")
            lines.extend(f"- {n}" for n in self.notes)
        return "\n".join(lines).rstrip()


# ---------- Builder ----------


def build_rollback_plan(
    report: RunReport,
    *,
    delivery_plan: DeliveryPlan | None = None,
    run_id: str | None = None,
    release_tag: str | None = None,
    issue_updates: list[str] | None = None,
) -> RollbackPlan:
    """Derive a RollbackPlan from a completed (or in-flight) RunReport.

    Actions are recorded in reverse-execution order so the operator can walk
    them top-down to undo state.
    """
    plan = RollbackPlan(run_id=run_id or report.sprint_id)
    actions: list[RollbackAction] = []

    # Step 9-10 — PRs (one per repo).
    for pr in report.prs:
        actions.append(_action_for_pr(pr))

    # Optional release/tag.
    if release_tag:
        actions.append(
            RollbackAction(
                kind="release",
                target=release_tag,
                note=f"GitHub Release `{release_tag}` was created.",
                instruction=(
                    f"gh release delete {release_tag} --yes && "
                    f"git push --delete origin {release_tag}"
                ),
                destructive=True,
                requires_approval=True,
            )
        )

    # Step 8 — commits & branches per repo, derived from PRInfo and plan.
    seen_branches: set[str] = set()
    for pr in report.prs:
        if pr.source_branch and pr.source_branch not in seen_branches:
            seen_branches.add(pr.source_branch)
            actions.append(_action_for_branch(pr.source_branch, pr.repo))
    if delivery_plan:
        for delivery in delivery_plan.deliveries:
            if delivery.branch and delivery.branch not in seen_branches:
                seen_branches.add(delivery.branch)
                actions.append(_action_for_branch(delivery.branch, delivery.repo))
            if delivery.worktree_path:
                actions.append(_action_for_worktree(delivery))

    # Issue / ticket updates (Jira/ADO).
    for note in issue_updates or []:
        actions.append(
            RollbackAction(
                kind="issue_update",
                target=note,
                note=f"Tracker comment / status change: {note}",
                instruction="Manually revert the tracker status or comment via Jira/ADO UI.",
                destructive=False,
            )
        )

    # Step 5 — evidence files (non-destructive cleanup only).
    evidence_paths = [ev.path for step in report.steps for ev in step.evidence if ev.path]
    if evidence_paths:
        actions.append(
            RollbackAction(
                kind="artifact",
                target=", ".join(evidence_paths[:3]) + ("…" if len(evidence_paths) > 3 else ""),
                note=f"{len(evidence_paths)} evidence file(s) written under `evidence/`",
                instruction="rm -r evidence/<run-id>   # safe — local-only artifacts",
                destructive=False,
            )
        )

    plan.actions = actions

    # Derive safe stop points from the step ladder.
    plan.safe_stop_points = _safe_stop_points(report)

    # Notes for the reviewer.
    plan.notes = _notes_for(report, delivery_plan)
    return plan


def _action_for_pr(pr: PrInfo) -> RollbackAction:
    if pr.provider == "github":
        if pr.url:
            instruction = f"gh pr close {pr.url} --delete-branch"
        else:
            instruction = "gh pr close <pr-url> --delete-branch"
    else:
        instruction = "az repos pr update --id <id> --status abandoned"
    return RollbackAction(
        kind="pr",
        target=pr.url or f"{pr.repo}#{pr.number or '?'}",
        note=f"PR opened on {pr.provider} ({pr.source_branch} → {pr.target_branch})",
        instruction=instruction,
        destructive=True,
        requires_approval=True,
    )


def _action_for_branch(branch: str, repo: str) -> RollbackAction:
    return RollbackAction(
        kind="branch",
        target=f"{repo}:{branch}",
        note=f"Branch `{branch}` was created and pushed.",
        instruction=(f"git -C <repo> branch -D {branch} && git push --delete origin {branch}"),
        destructive=True,
        requires_approval=True,
    )


def _action_for_worktree(delivery: PlannedDelivery) -> RollbackAction:
    return RollbackAction(
        kind="worktree",
        target=delivery.worktree_path or delivery.repo,
        note=f"Worktree for `{delivery.item_key}` at `{delivery.worktree_path}`.",
        instruction=f"git worktree remove --force '{delivery.worktree_path}'",
        destructive=False,
    )


def _safe_stop_points(report: RunReport) -> list[str]:
    """Identify checkpoints where stopping is low-risk.

    Returns up to four progressive stop points based on which steps
    completed (steps numbered per 10-step flow).
    """
    completed = {s.step for s in report.steps if s.status in {"ok", "skipped"}}
    points: list[str] = []
    if 2 in completed:
        points.append(
            "After step 2 (architecture mapping) — no repo state mutated yet; safe to abort."
        )
    if 4 in completed:
        points.append("After step 4 (lint) — only worktree state, no remote refs pushed yet.")
    if 7 in completed:
        points.append(
            "After step 7 (fix loop) — local commits exist; "
            "can be discarded by removing the worktree."
        )
    if 8 in completed:
        points.append(
            "After step 8 (commit + push) — branch is on origin; "
            "rollback requires `git push --delete`."
        )
    return points


def _notes_for(report: RunReport, delivery_plan: DeliveryPlan | None) -> list[str]:
    notes: list[str] = []
    if report.failed:
        notes.append(
            "Run is marked `failed=true`; review the step report before unwinding any action."
        )
    if delivery_plan and delivery_plan.low_confidence_count:
        notes.append(
            f"DeliveryPlan reported {delivery_plan.low_confidence_count} low-confidence route(s); "
            "double-check the affected repos before rollback."
        )
    if not notes:
        notes.append(
            "Rollback steps marked `requires approval` mutate shared remote state — "
            "never run them automatically."
        )
    return notes


# ---------- Integration helpers ----------


def pr_body_rollback_section(plan: RollbackPlan) -> str:
    """Return a `## Rollback` Markdown block to append to a PR body."""
    return "\n## Rollback\n\n" + plan.to_markdown() + "\n"


def evidence_filename(run_id: str | None) -> str:
    """Stable filename for embedding the plan in evidence bundles."""
    safe = (run_id or "run").replace("/", "_")
    return f"rollback-plan-{safe}.json"


__all__ = [
    "ActionKind",
    "RollbackAction",
    "RollbackPlan",
    "build_rollback_plan",
    "evidence_filename",
    "pr_body_rollback_section",
]


def _legacy_action_for_step(step: StepReport) -> RollbackAction | None:  # pragma: no cover
    """Kept as a hook point for callers that want per-step action overrides."""
    _ = step
    return None
