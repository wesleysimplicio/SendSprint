"""Post-mutation validation for Jira/Azure work items and pull requests."""

from __future__ import annotations

from datetime import UTC, datetime

from sendsprint.agents.story_task_planner import ADO_TASK_PARENT_TYPES
from sendsprint.models import Sprint
from sendsprint.models.reports import StepReport


def validate_sprint_links(sprint: Sprint) -> StepReport:
    """Validate known work-item link safety rules after planning/mutation."""
    step = StepReport(step=2, name="validate-work-item-links", status="running")
    step.started_at = datetime.now(UTC)
    if sprint.source != "azuredevops":
        step.status = "skipped"
        step.message = "work-item hierarchy validation applies to Azure DevOps only"
        step.finished_at = datetime.now(UTC)
        return step

    by_key = {item.key: item for item in sprint.items}
    by_id = {item.id: item for item in sprint.items}
    invalid: list[str] = []
    for item in sprint.items:
        if item.type not in {"Task", "Subtask"} or not item.parent_key:
            continue
        parent = by_key.get(item.parent_key) or by_id.get(item.parent_key)
        if parent and parent.type not in ADO_TASK_PARENT_TYPES:
            invalid.append(f"{parent.key}->{item.key} ({parent.type}->{item.type})")

    if invalid:
        step.status = "failed"
        step.message = "invalid Azure hierarchy link(s): " + ", ".join(invalid)
    else:
        step.status = "ok"
        step.message = "Azure work-item hierarchy links are safe"
    step.finished_at = datetime.now(UTC)
    return step


def validate_pr_step(pr_step: StepReport) -> StepReport:
    """Validate that a PR creation step returned enough data to continue safely."""
    step = StepReport(step=9, name="validate-pr", repo=pr_step.repo, status="running")
    step.started_at = datetime.now(UTC)
    if pr_step.status != "ok":
        step.status = "skipped"
        step.message = "PR validation skipped because PR creation did not succeed"
    elif not pr_step.pr:
        step.status = "failed"
        step.message = "PR creation reported ok without PR metadata"
    elif not (pr_step.pr.url or pr_step.pr.number):
        step.status = "failed"
        step.message = "PR metadata has no URL or number"
    elif not pr_step.pr.source_branch or not pr_step.pr.target_branch:
        step.status = "failed"
        step.message = "PR metadata is missing source or target branch"
    else:
        step.status = "ok"
        step.message = f"PR validated: {pr_step.pr.source_branch} -> {pr_step.pr.target_branch}"
    step.finished_at = datetime.now(UTC)
    return step
