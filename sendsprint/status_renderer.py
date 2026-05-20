"""Deterministic tri-agent status answer renderer.

Converts ``RunSnapshot`` instances into structured status answers consumed
by Claude, Codex, and Hermes adapters.  The renderer is strictly read-only
— no mutations, no side effects, same input always yields the same output.

See: https://github.com/wesleysimplicio/SendSprint/issues/116
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sendsprint.status_relay import RunSnapshot

# ---------------------------------------------------------------------------
# Status answer model
# ---------------------------------------------------------------------------

_UNKNOWN = "unknown"
_MAX_EVIDENCE_DISPLAY = 5
_MAX_HISTORY_SUMMARY = 50


class StatusAnswer(BaseModel):
    """Structured answer to an operator status query.

    Every field has a sensible default so sparse snapshots produce valid
    answers instead of guesses.
    """

    model_config = ConfigDict(extra="forbid")

    current_action: str = _UNKNOWN
    failures: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    next_step: str = _UNKNOWN
    active_agents: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    pr_links: list[str] = Field(default_factory=list)
    run_id: str = ""
    event_count: int = 0
    last_evidence: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------


class StatusRenderer:
    """Pure-function renderer: ``RunSnapshot`` -> ``StatusAnswer``.

    Deterministic — same snapshot always produces the same answer.
    No network, no disk, no mutation.
    """

    def render(self, snapshot: RunSnapshot) -> StatusAnswer:
        """Build a ``StatusAnswer`` from a point-in-time snapshot."""
        return StatusAnswer(
            current_action=snapshot.current_action or _UNKNOWN,
            failures=list(snapshot.failures),
            blockers=list(snapshot.blockers),
            next_step=snapshot.next_step or _UNKNOWN,
            active_agents=list(snapshot.active_agents),
            evidence_refs=list(snapshot.evidence_refs),
            pr_links=list(snapshot.pr_links),
            run_id=snapshot.run_id,
            event_count=snapshot.event_count,
            last_evidence=snapshot.last_evidence or "",
            timestamp=snapshot.updated_at,
        )


# ---------------------------------------------------------------------------
# Human-readable formatter (Markdown)
# ---------------------------------------------------------------------------


def format_human_readable(answer: StatusAnswer) -> str:
    """Render a ``StatusAnswer`` as clean Markdown.

    Long evidence lists are truncated with a count of remaining items.
    """
    lines: list[str] = [
        f"## Status — `{answer.run_id}`",
        "",
        f"**Current action:** {answer.current_action}",
        f"**Next step:** {answer.next_step}",
        f"**Active agents:** {', '.join(answer.active_agents) or 'none'}",
        f"**Events:** {answer.event_count}",
    ]

    if answer.last_evidence:
        lines.append(f"**Last evidence:** {answer.last_evidence}")

    if answer.blockers:
        lines.append("")
        lines.append("### Blockers")
        for b in answer.blockers:
            lines.append(f"- {b}")

    if answer.failures:
        lines.append("")
        lines.append("### Failures")
        for f in answer.failures:
            lines.append(f"- {f}")

    if answer.pr_links:
        lines.append("")
        lines.append("### PRs / Issues")
        for pr in answer.pr_links:
            lines.append(f"- {pr}")

    if answer.evidence_refs:
        lines.append("")
        lines.append("### Evidence")
        for ref in answer.evidence_refs[:_MAX_EVIDENCE_DISPLAY]:
            lines.append(f"- {ref}")
        remaining = len(answer.evidence_refs) - _MAX_EVIDENCE_DISPLAY
        if remaining > 0:
            lines.append(f"- ... and {remaining} more")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Machine-readable formatter (JSON-serializable dict)
# ---------------------------------------------------------------------------


def format_machine_readable(answer: StatusAnswer) -> dict[str, Any]:
    """Render a ``StatusAnswer`` as a plain JSON-serializable dict.

    Evidence refs are capped at ``_MAX_HISTORY_SUMMARY`` with a separate
    ``evidence_total`` key for the full count.
    """
    return {
        "run_id": answer.run_id,
        "current_action": answer.current_action,
        "failures": answer.failures,
        "blockers": answer.blockers,
        "next_step": answer.next_step,
        "active_agents": answer.active_agents,
        "evidence_refs": answer.evidence_refs[:_MAX_HISTORY_SUMMARY],
        "evidence_total": len(answer.evidence_refs),
        "pr_links": answer.pr_links,
        "event_count": answer.event_count,
        "last_evidence": answer.last_evidence,
        "timestamp": answer.timestamp.isoformat(),
    }
