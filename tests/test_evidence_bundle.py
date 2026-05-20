"""Tests for portable evidence bundles."""

from __future__ import annotations

import json
from pathlib import Path

from sendsprint.evidence import (
    BundleManager,
    EvidenceBundle,
    EvidenceItem,
    EvidenceItemType,
    create_evidence_bundle,
)
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


# ---------------------------------------------------------------------------
# First-class evidence bundle tests (issue #96)
# ---------------------------------------------------------------------------


class TestEvidenceItemType:
    def test_all_expected_types_exist(self) -> None:
        expected = {"command", "log", "screenshot", "coverage", "risk", "decision"}
        assert {t.value for t in EvidenceItemType} == expected


class TestEvidenceItem:
    def test_create_item(self) -> None:
        item = EvidenceItem(
            type=EvidenceItemType.command,
            content="pytest tests/ -v",
            metadata={"exit_code": 0},
        )
        assert item.type == EvidenceItemType.command
        assert item.content == "pytest tests/ -v"
        assert item.metadata == {"exit_code": 0}
        assert item.timestamp is not None


class TestEvidenceBundle:
    def test_bundle_defaults(self) -> None:
        bundle = EvidenceBundle(run_id="r-1")
        assert bundle.schema_version == "2.0"
        assert bundle.items == []
        assert bundle.tuple_ids == []
        assert bundle.receipt_ids == []
        assert bundle.yool_ids == []
        assert bundle.finalized_at is None

    def test_bundle_with_ids(self) -> None:
        bundle = EvidenceBundle(
            run_id="r-2",
            tuple_ids=["t-abc"],
            receipt_ids=["rec-1"],
            yool_ids=["agent.codex.plan"],
        )
        assert bundle.tuple_ids == ["t-abc"]
        assert bundle.receipt_ids == ["rec-1"]
        assert bundle.yool_ids == ["agent.codex.plan"]


class TestBundleManager:
    def test_create_and_load_bundle(self, tmp_path: Path) -> None:
        mgr = BundleManager(base_dir=tmp_path)
        bundle = mgr.create_bundle("run-42")
        assert bundle.run_id == "run-42"
        bundle_path = tmp_path / ".sendsprint" / "evidence" / "run-42" / "bundle.json"
        assert bundle_path.exists()

        loaded = mgr.load_bundle("run-42")
        assert loaded is not None
        assert loaded.run_id == "run-42"

    def test_add_item_persists(self, tmp_path: Path) -> None:
        mgr = BundleManager(base_dir=tmp_path)
        bundle = mgr.create_bundle("run-43")
        mgr.add_item(bundle, EvidenceItemType.command, "ruff check .")
        mgr.add_item(bundle, "log", "All checks passed", {"lines": 12})
        assert len(bundle.items) == 2
        assert bundle.items[0].type == EvidenceItemType.command
        assert bundle.items[1].type == EvidenceItemType.log

        reloaded = mgr.load_bundle("run-43")
        assert reloaded is not None
        assert len(reloaded.items) == 2

    def test_finalize_sets_timestamp(self, tmp_path: Path) -> None:
        mgr = BundleManager(base_dir=tmp_path)
        bundle = mgr.create_bundle("run-44")
        assert bundle.finalized_at is None
        mgr.finalize(bundle)
        assert bundle.finalized_at is not None

    def test_export_manifest_returns_dict(self, tmp_path: Path) -> None:
        mgr = BundleManager(base_dir=tmp_path)
        bundle = mgr.create_bundle("run-45")
        mgr.add_item(bundle, EvidenceItemType.risk, "no rollback plan")
        manifest = mgr.export_manifest(bundle)
        assert isinstance(manifest, dict)
        assert manifest["run_id"] == "run-45"
        assert len(manifest["items"]) == 1

    def test_summarize_for_pr(self, tmp_path: Path) -> None:
        mgr = BundleManager(base_dir=tmp_path)
        bundle = mgr.create_bundle("run-46")
        bundle.tuple_ids = ["t-1"]
        bundle.yool_ids = ["agent.codex.plan"]
        mgr.add_item(bundle, EvidenceItemType.command, "pytest tests/ -v")
        mgr.add_item(bundle, EvidenceItemType.coverage, "85% line coverage")
        mgr.add_item(bundle, EvidenceItemType.decision, "skip e2e — no UI")

        summary = mgr.summarize_for_pr(bundle)
        assert "run-46" in summary
        assert "**Tuples:** t-1" in summary
        assert "**Yools:** agent.codex.plan" in summary
        assert "### Command (1)" in summary
        assert "### Coverage (1)" in summary
        assert "### Decision (1)" in summary

    def test_list_bundles(self, tmp_path: Path) -> None:
        mgr = BundleManager(base_dir=tmp_path)
        assert mgr.list_bundles() == []
        mgr.create_bundle("b-1")
        mgr.create_bundle("b-2")
        assert mgr.list_bundles() == ["b-1", "b-2"]

    def test_load_nonexistent_returns_none(self, tmp_path: Path) -> None:
        mgr = BundleManager(base_dir=tmp_path)
        assert mgr.load_bundle("nope") is None

    def test_bundle_json_format_stable(self, tmp_path: Path) -> None:
        """Manifest JSON must include schema_version for forward compat."""
        mgr = BundleManager(base_dir=tmp_path)
        bundle = mgr.create_bundle("fmt-1")
        mgr.add_item(bundle, EvidenceItemType.screenshot, "/tmp/shot.png")
        mgr.finalize(bundle)

        raw = json.loads(
            (tmp_path / ".sendsprint" / "evidence" / "fmt-1" / "bundle.json").read_text()
        )
        assert raw["schema_version"] == "2.0"
        assert raw["finalized_at"] is not None
        assert len(raw["items"]) == 1
        assert raw["items"][0]["type"] == "screenshot"
