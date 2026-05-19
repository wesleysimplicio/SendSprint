"""Unified agent-facing sprint observability snapshot."""

from __future__ import annotations

from sendsprint.api.runs import events, manager
from sendsprint.api.schemas import AgentRunSnapshot, AgentTimelineEvent


def build_agent_snapshot(run_id: str) -> AgentRunSnapshot | None:
    status = manager.get_run(run_id)
    request = manager.get_run_request(run_id)
    if status is None or request is None:
        return None

    history = [AgentTimelineEvent.model_validate(item) for item in events.history(run_id)]
    latest_step = events.latest_of_type(run_id, "step") or {}
    latest_loop = events.latest_of_type(run_id, "loop") or {}
    latest_regression = events.latest_of_type(run_id, "regression") or {}

    evidence_paths = [item.evidence_path for item in history if item.evidence_path is not None]
    recent_logs = [item.message for item in history if item.type == "log" and item.message][-10:]
    blockers = [
        item.message for item in history if item.type in {"error", "regression"} and item.message
    ]

    return AgentRunSnapshot(
        run_id=run_id,
        sprint_id=status.sprint_id,
        provider=status.provider,
        state=status.state,
        mode=request.mode,
        item_keys=request.item_keys,
        repo_path=request.repo_path,
        workspace_path=request.workspace_path,
        started_at=status.started_at,
        finished_at=status.finished_at,
        summary=status.summary,
        pr_url=status.pr_url,
        failed=status.failed,
        current_step=latest_step.get("step"),
        current_step_name=latest_step.get("name"),
        current_step_status=latest_step.get("status"),
        progress=latest_step.get("progress"),
        iteration=latest_loop.get("iteration"),
        max_iterations=latest_loop.get("max_iterations"),
        failing_tests=latest_regression.get("failing_tests") or [],
        evidence_paths=evidence_paths,
        blockers=blockers,
        recent_logs=recent_logs,
        timeline=history,
    )
