"""Tests for PrBodyBuilder — composes PR markdown body with evidence + DoD."""

from __future__ import annotations

from pathlib import Path

from sendsprint.agents.pr_body_builder import PrBodyBuilder
from sendsprint.models import Sprint, SprintItem
from sendsprint.models.reports import (
    SecurityFinding,
    StepReport,
    TestEvidence,
)


def _sprint() -> Sprint:
    return Sprint(
        id="42",
        name="Demo Sprint",
        state="active",
        source="jira",
        transport="api",
        items=[
            SprintItem(
                id="PROJ-1",
                key="PROJ-1",
                type="Task",
                title="Sample",
                status="To Do",
                source_url="https://jira.example/PROJ-1",
            ),
        ],
    )


def test_build_contains_summary_and_dod(tmp_path: Path):
    body = PrBodyBuilder(tmp_path).build(_sprint(), "demo-repo", [], "sprint-42")
    assert "## Summary" in body
    assert "Demo Sprint" in body
    assert "## Definition of Done" in body
    assert "Coverage diff ≥ 80%" in body


def test_items_block_renders_item_link():
    body = PrBodyBuilder(Path(".")).build(_sprint(), "demo-repo", [], "sprint-42")
    assert "PROJ-1" in body
    assert "https://jira.example/PROJ-1" in body


def test_evidence_block_renders_passed_and_failed():
    steps = [
        StepReport(
            step=5,
            name="unit",
            repo="demo-repo",
            status="ok",
            evidence=[
                TestEvidence(
                    kind="unit", title="pytest pass", passed=True, path="reports/unit.xml"
                ),
                TestEvidence(kind="e2e", title="playwright fail", passed=False),
            ],
        ),
    ]
    body = PrBodyBuilder(Path(".")).build(_sprint(), "demo-repo", steps, "sprint-42")
    assert "✓ [unit] pytest pass" in body
    assert "✗ [e2e] playwright fail" in body
    assert "reports/unit.xml" in body


def test_findings_block_renders_when_present():
    steps = [
        StepReport(
            step=6,
            name="security",
            repo="demo-repo",
            status="failed",
            findings=[
                SecurityFinding(
                    rule="hardcoded-secret",
                    severity="high",
                    file="src/cfg.py",
                    line=12,
                    message="AWS key detected",
                ),
            ],
        ),
    ]
    body = PrBodyBuilder(Path(".")).build(_sprint(), "demo-repo", steps, "sprint-42")
    assert "[high] `hardcoded-secret`" in body
    assert "src/cfg.py:12" in body


def test_empty_findings_shows_none():
    body = PrBodyBuilder(Path(".")).build(_sprint(), "demo-repo", [], "sprint-42")
    assert "_(none)_" in body


def test_step_table_filters_by_repo():
    steps = [
        StepReport(step=4, name="lint", repo="demo-repo", status="ok", message="clean"),
        StepReport(step=4, name="lint", repo="other-repo", status="failed", message="x"),
    ]
    body = PrBodyBuilder(Path(".")).build(_sprint(), "demo-repo", steps, "sprint-42")
    assert "clean" in body
    assert "| 4 | lint | failed | x |" not in body
