"""Tests for sendsprint/agents/ modules."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sendsprint.agents.worktree import WorktreeError, WorktreeManager
from sendsprint.agents.dev import DevAgent
from sendsprint.agents.test_runner import TestRunner
from sendsprint.agents.security_reviewer import SecurityReviewer
from sendsprint.agents.pr_reviewer import PrReviewer
from sendsprint.tech import TechFingerprint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_fp(tmp_path: Path, *, techs: list[str] | None = None, pms: list[str] | None = None) -> TechFingerprint:
    return TechFingerprint(
        repo_path=str(tmp_path),
        techs=techs or [],
        roles=["other"],
        package_managers=pms or [],
    )


def init_git(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=str(path),
        capture_output=True,
        check=True,
        env={
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@test.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@test.com",
            "HOME": str(path),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        },
    )


# ---------------------------------------------------------------------------
# WorktreeManager
# ---------------------------------------------------------------------------


class TestWorktreeManager:
    def test_init_raises_on_non_git_dir(self, tmp_path: Path) -> None:
        with pytest.raises(WorktreeError, match="not a git repo"):
            WorktreeManager(tmp_path)

    def test_init_succeeds_on_git_repo(self, tmp_path: Path) -> None:
        init_git(tmp_path)
        wm = WorktreeManager(tmp_path)
        assert wm.repo == tmp_path.resolve()

    def test_list_worktrees_includes_main(self, tmp_path: Path) -> None:
        init_git(tmp_path)
        wm = WorktreeManager(tmp_path)
        worktrees = wm.list_worktrees()
        assert len(worktrees) >= 1
        assert any(str(tmp_path.resolve()) in wt for wt in worktrees)

    def test_current_branch_returns_string(self, tmp_path: Path) -> None:
        init_git(tmp_path)
        wm = WorktreeManager(tmp_path)
        branch = wm.current_branch()
        assert isinstance(branch, str)
        assert len(branch) > 0


# ---------------------------------------------------------------------------
# DevAgent
# ---------------------------------------------------------------------------


class TestDevAgent:
    def test_init_stores_repo_and_fingerprint(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path)
        agent = DevAgent(tmp_path, fp)
        assert agent.repo == tmp_path.resolve()
        assert agent.fp is fp

    def test_install_skipped_when_no_package_managers(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path, pms=[])
        agent = DevAgent(tmp_path, fp)
        report = agent.install()
        assert report.status == "skipped"
        assert "no package manager" in (report.message or "")

    def test_build_skipped_for_unknown_tech(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path, techs=["cobol"])
        agent = DevAgent(tmp_path, fp)
        report = agent.build()
        assert report.status == "skipped"

    def test_build_skipped_when_no_techs(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path, techs=[])
        agent = DevAgent(tmp_path, fp)
        report = agent.build()
        assert report.status == "skipped"

    def test_build_failed_when_custom_command_binary_missing(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path)
        agent = DevAgent(tmp_path, fp)
        report = agent.build(custom_command="__nonexistent_binary_xyz__ --flag")
        assert report.status == "failed"
        assert "__nonexistent_binary_xyz__" in (report.message or "")


# ---------------------------------------------------------------------------
# TestRunner
# ---------------------------------------------------------------------------


class TestTestRunner:
    def test_run_unit_skipped_for_unknown_tech(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path, techs=["cobol"])
        runner = TestRunner(tmp_path, fp)
        report = runner.run_unit()
        assert report.status == "skipped"

    def test_run_unit_skipped_when_no_techs(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path, techs=[])
        runner = TestRunner(tmp_path, fp)
        report = runner.run_unit()
        assert report.status == "skipped"

    def test_run_e2e_skipped_for_unknown_tech(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path, techs=["cobol"])
        runner = TestRunner(tmp_path, fp)
        report = runner.run_e2e()
        assert report.status == "skipped"

    def test_run_e2e_skipped_when_no_techs(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path, techs=[])
        runner = TestRunner(tmp_path, fp)
        report = runner.run_e2e()
        assert report.status == "skipped"

    def test_run_all_returns_two_reports(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path, techs=[])
        runner = TestRunner(tmp_path, fp)
        reports = runner.run_all()
        assert len(reports) == 2

    def test_evidence_dir_created_on_init(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path)
        runner = TestRunner(tmp_path, fp)
        assert runner.evidence_dir.exists()
        assert runner.evidence_dir.is_dir()


# ---------------------------------------------------------------------------
# SecurityReviewer
# ---------------------------------------------------------------------------


class TestSecurityReviewer:
    def test_scan_empty_repo_ok_zero_findings(self, tmp_path: Path) -> None:
        fp = make_fp(tmp_path)
        reviewer = SecurityReviewer(tmp_path, fp)
        report = reviewer.scan()
        assert report.status == "ok"
        assert len(report.findings) == 0

    def test_scan_detects_hardcoded_secret(self, tmp_path: Path) -> None:
        (tmp_path / "config.py").write_text('API_KEY = "sk-1234567890abcdefghij"')
        fp = make_fp(tmp_path)
        reviewer = SecurityReviewer(tmp_path, fp)
        report = reviewer.scan()
        rules = [f.rule for f in report.findings]
        assert any(r in ("hardcoded-api-key", "openai-key") for r in rules)

    def test_scan_flags_env_not_gitignored(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("SECRET=super_secret_value\n")
        fp = make_fp(tmp_path)
        reviewer = SecurityReviewer(tmp_path, fp)
        report = reviewer.scan()
        rules = [f.rule for f in report.findings]
        assert "env-not-gitignored" in rules

    def test_scan_no_finding_for_env_example(self, tmp_path: Path) -> None:
        (tmp_path / ".env.example").write_text("SECRET=changeme\n")
        fp = make_fp(tmp_path)
        reviewer = SecurityReviewer(tmp_path, fp)
        report = reviewer.scan()
        files = [f.file for f in report.findings]
        assert ".env.example" not in files

    def test_scan_env_gitignored_no_finding(self, tmp_path: Path) -> None:
        (tmp_path / ".env").write_text("SECRET=super_secret_value\n")
        (tmp_path / ".gitignore").write_text(".env\n")
        fp = make_fp(tmp_path)
        reviewer = SecurityReviewer(tmp_path, fp)
        report = reviewer.scan()
        rules = [f.rule for f in report.findings]
        assert "env-not-gitignored" not in rules


# ---------------------------------------------------------------------------
# PrReviewer
# ---------------------------------------------------------------------------


class TestPrReviewer:
    def _reviewer(self, tmp_path: Path) -> PrReviewer:
        return PrReviewer(tmp_path)

    def test_static_checks_todo_marker(self, tmp_path: Path) -> None:
        reviewer = self._reviewer(tmp_path)
        diff = "+const x = 1; // TODO: fix this later\n"
        issues = reviewer._static_checks(diff)
        rules = [i["rule"] for i in issues]
        assert "todo-marker" in rules

    def test_static_checks_debug_statement(self, tmp_path: Path) -> None:
        reviewer = self._reviewer(tmp_path)
        diff = "+console.log('debug value', value);\n"
        issues = reviewer._static_checks(diff)
        rules = [i["rule"] for i in issues]
        assert "debug-statement" in rules

    def test_static_checks_long_line(self, tmp_path: Path) -> None:
        reviewer = self._reviewer(tmp_path)
        long_code = "x" * 201
        diff = f"+{long_code}\n"
        issues = reviewer._static_checks(diff)
        rules = [i["rule"] for i in issues]
        assert "long-line" in rules

    def test_static_checks_clean_diff_no_issues(self, tmp_path: Path) -> None:
        reviewer = self._reviewer(tmp_path)
        diff = "+const value = compute(a, b);\n+return value;\n"
        issues = reviewer._static_checks(diff)
        assert issues == []

    def test_static_checks_ignores_removed_lines(self, tmp_path: Path) -> None:
        reviewer = self._reviewer(tmp_path)
        # Removed line with TODO should not be flagged
        diff = "-const x = 1; // TODO: old code\n"
        issues = reviewer._static_checks(diff)
        assert issues == []
