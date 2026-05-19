"""Tests for sendsprint.rollback (issue #58)."""

from __future__ import annotations

from sendsprint.models.reports import PrInfo, RunReport, StepReport, TestEvidence
from sendsprint.planning import DeliveryPlan, PlannedDelivery
from sendsprint.rollback import (
    RollbackAction,
    RollbackPlan,
    build_rollback_plan,
    evidence_filename,
    pr_body_rollback_section,
)


def _sample_report(*, with_pr: bool = True, failed: bool = False) -> RunReport:
    steps = [
        StepReport(step=1, name="read-sprint", status="ok"),
        StepReport(step=2, name="architecture", status="ok"),
        StepReport(step=3, name="dev-build", status="ok", repo="/r/api"),
        StepReport(step=4, name="lint", status="ok", repo="/r/api"),
        StepReport(
            step=5,
            name="tests",
            status="ok",
            repo="/r/api",
            evidence=[
                TestEvidence(
                    kind="screenshot", title="login flow", passed=True, path="evidence/login.png"
                ),
                TestEvidence(
                    kind="screenshot",
                    title="dashboard render",
                    passed=True,
                    path="evidence/dashboard.png",
                ),
            ],
        ),
        StepReport(step=6, name="security", status="ok", repo="/r/api"),
        StepReport(step=7, name="fix-loop", status="ok"),
        StepReport(step=8, name="commit", status="ok", repo="/r/api"),
    ]
    prs = (
        [
            PrInfo(
                provider="github",
                repo="/r/api",
                number=42,
                url="https://github.com/acme/api/pull/42",
                title="feat: deliver PROJ-1",
                source_branch="sendsprint/PROJ-1",
                target_branch="main",
            )
        ]
        if with_pr
        else []
    )
    return RunReport(
        workspace="ws",
        sprint_id="sprint-9",
        sprint_name="Sprint 9",
        steps=steps,
        prs=prs,
        failed=failed,
        summary="Delivered 1 item.",
    )


def _sample_delivery_plan() -> DeliveryPlan:
    return DeliveryPlan(
        source="jira",
        sprint_id="sprint-9",
        sprint_name="Sprint 9",
        deliveries=[
            PlannedDelivery(
                item_key="PROJ-1",
                item_type="Story",
                title="Onboarding rework",
                repo="/r/api",
                repo_role="api",
                branch="sendsprint/PROJ-1",
                target_branch="main",
                confidence="high",
                reason="explicit scope label",
                worktree_path="/r/api-wt-sendsprint-PROJ-1",
                validation_template="python",
                validation_commands=["pytest"],
            )
        ],
    )


def test_build_records_pr_branch_and_worktree_actions():
    report = _sample_report()
    plan = build_rollback_plan(report, delivery_plan=_sample_delivery_plan(), run_id="abc123")

    kinds = [a.kind for a in plan.actions]
    assert "pr" in kinds
    assert "branch" in kinds
    assert "worktree" in kinds
    assert "artifact" in kinds  # evidence files captured

    pr_action = next(a for a in plan.actions if a.kind == "pr")
    assert pr_action.destructive is True
    assert pr_action.requires_approval is True
    assert "gh pr close" in pr_action.instruction

    branch_action = next(a for a in plan.actions if a.kind == "branch")
    assert branch_action.destructive is True
    assert "git push --delete origin sendsprint/PROJ-1" in branch_action.instruction

    worktree_action = next(a for a in plan.actions if a.kind == "worktree")
    assert worktree_action.destructive is False
    assert "git worktree remove" in worktree_action.instruction


def test_run_without_pr_still_emits_safe_stop_points():
    report = _sample_report(with_pr=False)
    plan = build_rollback_plan(report, run_id="no-pr")

    assert not any(a.kind == "pr" for a in plan.actions)
    assert plan.safe_stop_points  # steps 2, 4, 7, 8 all completed
    assert any("step 4" in p for p in plan.safe_stop_points)
    assert any("step 8" in p for p in plan.safe_stop_points)


def test_to_markdown_lists_actions_and_stops():
    report = _sample_report()
    plan = build_rollback_plan(report, delivery_plan=_sample_delivery_plan(), run_id="md-1")
    md = plan.to_markdown()

    assert "Actions executed (reverse order):" in md
    assert "🔒 requires approval" in md  # PR carries approval gate
    assert "⚠ destructive" in md
    assert "Safe stop points:" in md
    assert "Notes:" in md


def test_empty_plan_renders_friendly_placeholder():
    plan = RollbackPlan(run_id="empty")
    assert plan.to_markdown() == "_No reversible side effects recorded for this run._"
    assert plan.has_destructive is False
    assert plan.requires_approval is False


def test_release_tag_marked_destructive_and_requires_approval():
    report = _sample_report()
    plan = build_rollback_plan(report, run_id="rel", release_tag="v1.4.2")
    release = next(a for a in plan.actions if a.kind == "release")
    assert release.destructive is True
    assert release.requires_approval is True
    assert "gh release delete v1.4.2" in release.instruction
    assert plan.has_destructive is True


def test_failed_run_adds_review_note():
    report = _sample_report(failed=True)
    plan = build_rollback_plan(report, run_id="failed-1")
    assert any("failed=true" in note for note in plan.notes)


def test_pr_body_section_wraps_markdown_with_heading():
    report = _sample_report()
    plan = build_rollback_plan(report, run_id="sec")
    section = pr_body_rollback_section(plan)
    assert section.startswith("\n## Rollback\n\n")
    assert "PR opened on github" in section


def test_evidence_filename_is_stable_and_path_safe():
    assert evidence_filename("abc") == "rollback-plan-abc.json"
    assert evidence_filename(None) == "rollback-plan-run.json"
    assert evidence_filename("a/b/c") == "rollback-plan-a_b_c.json"


def test_action_serializes_round_trip():
    action = RollbackAction(
        kind="commit",
        target="abc123",
        note="initial commit",
        instruction="git reset --hard <prev>",
        destructive=False,
    )
    again = RollbackAction.model_validate_json(action.model_dump_json())
    assert again == action


def test_issue_updates_become_non_destructive_actions():
    report = _sample_report()
    plan = build_rollback_plan(
        report,
        run_id="iss",
        issue_updates=["PROJ-1 transitioned: To Do → In Review"],
    )
    issue_actions = [a for a in plan.actions if a.kind == "issue_update"]
    assert len(issue_actions) == 1
    assert issue_actions[0].destructive is False
    assert "Manually revert" in issue_actions[0].instruction
