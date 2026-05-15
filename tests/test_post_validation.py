"""Tests for post-mutation validation helpers."""

from __future__ import annotations

from sendsprint.models.reports import PrInfo, StepReport
from sendsprint.models.sprint import Sprint, SprintItem
from sendsprint.post_validation import validate_pr_step, validate_sprint_links


def test_validate_sprint_links_flags_azure_issue_task_parent() -> None:
    sprint = Sprint(
        id="Sprint 29",
        name="Sprint 29",
        source="azuredevops",
        items=[
            SprintItem(id="179778", key="179778", type="Issue", title="Issue", status="New"),
            SprintItem(
                id="179822",
                key="179822",
                type="Task",
                title="Task",
                status="New",
                parent_key="179778",
            ),
        ],
    )

    report = validate_sprint_links(sprint)

    assert report.status == "failed"
    assert "179778->179822" in (report.message or "")


def test_validate_pr_step_requires_metadata() -> None:
    pr_step = StepReport(step=9, name="create-pr", status="ok")
    pr_step.pr = PrInfo(
        provider="github",
        repo="org/repo",
        url="https://github.example/pull/1",
        title="PR",
        source_branch="feature/1",
        target_branch="develop",
    )

    report = validate_pr_step(pr_step)

    assert report.status == "ok"
    assert "feature/1 -> develop" in (report.message or "")
