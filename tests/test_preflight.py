"""Tests for preflight checks."""

from __future__ import annotations

from typing import Any

from sendsprint.models.sprint import Sprint, SprintItem
from sendsprint.operators.base import BaseOperator
from sendsprint.preflight import run_preflight


class FakeOperator(BaseOperator):
    source = "jira"

    def _api_available(self) -> bool:
        return True

    def _read_via_mcp(self, **kwargs: Any) -> Sprint:
        raise AssertionError("mcp should not be used")

    def _read_via_api(self, **kwargs: Any) -> Sprint:
        return Sprint(
            id="42",
            name="Sprint 42",
            source="jira",
            items=[SprintItem(id="PROJ-1", key="PROJ-1", type="Task", title="Task", status="New")],
        )

    def _read_via_playwright(self, **kwargs: Any) -> Sprint:
        raise AssertionError("playwright should not be used")


def test_run_preflight_reads_sprint_and_checks_repo(tmp_path) -> None:
    report = run_preflight(FakeOperator(transport="api"), identifier="42", repo_path=tmp_path)

    assert report.ok is True
    assert report.sprint is not None
    assert any(check.name == "transport" and check.status == "ok" for check in report.checks)
    assert any(check.name == "sprint" and check.status == "ok" for check in report.checks)
