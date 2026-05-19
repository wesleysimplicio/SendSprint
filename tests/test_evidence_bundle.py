"""Tests for portable evidence bundles."""

from __future__ import annotations

from pathlib import Path

from sendsprint.evidence import create_evidence_bundle
from sendsprint.models.reports import PrInfo, RunReport


def test_create_evidence_bundle_writes_manifest_and_report(tmp_path: Path) -> None:
    report = RunReport(workspace="ws", sprint_id="42", summary="ok")
    report.prs.append(
        PrInfo(
            provider="github",
            repo="repo",
            title="PR",
            source_branch="feature/x",
            target_branch="main",
            url="https://github.com/o/r/pull/1",
        )
    )
    manifest = create_evidence_bundle(report, tmp_path, issue_updates=["closed #1"])
    root = Path(manifest.root)
    assert (root / "run-report.json").exists()
    assert (root / "manifest.json").exists()
    assert manifest.pr_urls == ["https://github.com/o/r/pull/1"]
    assert manifest.issue_updates == ["closed #1"]


def test_create_evidence_bundle_includes_rollback_plan(tmp_path: Path) -> None:
    """Issue #58: rollback plan JSON ships inside the evidence bundle."""
    from sendsprint.rollback import build_rollback_plan

    report = RunReport(workspace="ws", sprint_id="rb-1", summary="ok")
    report.prs.append(
        PrInfo(
            provider="github",
            repo="r",
            title="PR",
            source_branch="sendsprint/X-1",
            target_branch="main",
            url="https://github.com/o/r/pull/9",
        )
    )
    plan = build_rollback_plan(report, run_id="rb-1")
    manifest = create_evidence_bundle(report, tmp_path, rollback=plan)
    root = Path(manifest.root)
    rollback_file = next((f for f in manifest.files if f.kind == "rollback-plan"), None)
    assert rollback_file is not None
    assert (root / rollback_file.path).exists()
