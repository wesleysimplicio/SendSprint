"""Tests for scripts/build_changelog.py (Sprint 4 issue #13)."""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

import pytest

# Load the script module without making it part of the installable package.
SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "build_changelog.py"
spec = importlib.util.spec_from_file_location("build_changelog", SCRIPT_PATH)
assert spec and spec.loader
build_changelog = importlib.util.module_from_spec(spec)
sys.modules["build_changelog"] = build_changelog
spec.loader.exec_module(build_changelog)


class TestParseCommit:
    def test_feat_with_scope(self) -> None:
        parsed = build_changelog.parse_commit("feat(detector): add bun runtime")
        assert parsed == ("feat", "detector", "add bun runtime", False)

    def test_fix_without_scope(self) -> None:
        parsed = build_changelog.parse_commit("fix: handle missing binary")
        assert parsed == ("fix", "", "handle missing binary", False)

    def test_breaking_marker(self) -> None:
        parsed = build_changelog.parse_commit("feat(api)!: drop /v1 endpoint")
        assert parsed is not None
        assert parsed[3] is True

    def test_non_conventional_returns_none(self) -> None:
        assert build_changelog.parse_commit("random commit message") is None

    def test_uppercase_type_returns_none(self) -> None:
        assert build_changelog.parse_commit("FEAT: shout") is None


class TestGroupCommits:
    def test_groups_by_type(self) -> None:
        groups = build_changelog.group_commits(
            [
                "feat(detector): add bun",
                "fix: cleanup worktree",
                "docs: update README",
                "chore: bump deps",
                "test: add cargo audit cases",
            ]
        )
        assert any("add bun" in c for c in groups["Added"])
        assert any("cleanup worktree" in c for c in groups["Fixed"])
        assert any("update README" in c for c in groups["Docs"])
        assert any("bump deps" in c for c in groups["Chore"])
        assert any("add cargo audit cases" in c for c in groups["Tests"])

    def test_non_conventional_falls_back_to_other(self) -> None:
        groups = build_changelog.group_commits(["random work item"])
        assert groups["Other"] == ["random work item"]

    def test_breaking_marker_annotated(self) -> None:
        groups = build_changelog.group_commits(["feat(api)!: drop /v1"])
        assert any("BREAKING" in c for c in groups["Added"])


class TestRenderBlock:
    def test_renders_unreleased_heading(self) -> None:
        text = build_changelog.render_block(
            build_changelog.group_commits(["feat: add bun runtime"])
        )
        assert text.startswith("## [Unreleased]\n")
        assert "### Added" in text
        assert "- add bun runtime" in text

    def test_empty_groups_omitted(self) -> None:
        text = build_changelog.render_block(build_changelog.group_commits(["feat: only feature"]))
        assert "### Fixed" not in text
        assert "### Docs" not in text


class TestPromoteUnreleased:
    def test_promote_renames_unreleased(self, tmp_path: Path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("## [Unreleased]\n\n### Added\n\n- thing\n", encoding="utf-8")
        new = build_changelog.promote_unreleased(changelog, "0.13.0", today=date(2026, 6, 1))
        assert "## [0.13.0] - 2026-06-01" in new
        assert "## [Unreleased]" not in new

    def test_promote_idempotent_when_unreleased_missing(self, tmp_path: Path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        original = "## [0.12.0] - 2026-05-18\n"
        changelog.write_text(original, encoding="utf-8")
        new = build_changelog.promote_unreleased(changelog, "0.13.0")
        assert new == original


class TestMain:
    def test_main_with_commits_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        commits = tmp_path / "commits.txt"
        commits.write_text("feat(detector): add deno\nfix: handle timeout\n", encoding="utf-8")
        rc = build_changelog.main(["--commits-file", str(commits)])
        out = capsys.readouterr().out
        assert rc == 0
        assert "## [Unreleased]" in out
        assert "add deno" in out
        assert "handle timeout" in out

    def test_main_promote_writes_changelog(self, tmp_path: Path) -> None:
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("## [Unreleased]\n\n### Added\n\n- x\n", encoding="utf-8")
        rc = build_changelog.main(["--promote", "0.13.0", "--changelog", str(changelog)])
        assert rc == 0
        text = changelog.read_text(encoding="utf-8")
        assert "## [0.13.0] - " in text
