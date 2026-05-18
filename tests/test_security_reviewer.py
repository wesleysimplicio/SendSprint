"""Tests for sendsprint/agents/security_reviewer.py — cargo + pip audit branches.

Covers TASK-002 (cargo-audit) and the pip-audit backlog item. The npm-audit
path is exercised via integration in `tests/test_agents.py::TestSecurityReviewer`.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from sendsprint.agents.security_reviewer import SecurityReviewer
from sendsprint.tech import TechFingerprint

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _fp(tmp_path: Path) -> TechFingerprint:
    return TechFingerprint(repo_path=str(tmp_path), techs=[], roles=["other"])


def _make_cargo_repo(tmp_path: Path) -> Path:
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "test"\nversion = "0.1.0"\n')
    return tmp_path


def _make_pip_repo(tmp_path: Path) -> Path:
    (tmp_path / "requirements.txt").write_text("requests==2.20.0\n")
    return tmp_path


def _fake_process(
    *, returncode: int, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["cargo", "audit", "--json"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


# ---------------------------------------------------------------------------
# cargo-audit (TASK-002)
# ---------------------------------------------------------------------------


class TestCargoAudit:
    def test_cargo_clean_zero_findings(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """AC-1: returncode 0 → status='ok', cargo_findings=0."""
        _make_cargo_repo(tmp_path)
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _fake_process(returncode=0))
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        report = reviewer.scan()
        cargo = reviewer.tool_results.get("cargo-audit", {})
        assert cargo.get("status") == "ok"
        assert cargo.get("cargo_findings") == 0
        assert report.step == 6
        assert not any(f.rule == "cargo-audit" for f in report.findings)

    def test_cargo_three_vulns_from_fixture(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """AC-2: 3 vulns parsed → cargo_findings=3, findings include id+package+severity."""
        _make_cargo_repo(tmp_path)
        payload = (FIXTURE_DIR / "cargo-audit-output.json").read_text()
        monkeypatch.setattr(
            subprocess, "run", lambda *a, **kw: _fake_process(returncode=1, stdout=payload)
        )
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        report = reviewer.scan()
        cargo_findings = [f for f in report.findings if f.rule == "cargo-audit"]
        assert len(cargo_findings) == 3
        # Each finding carries advisory id, package, severity.
        messages = " ".join(f.message for f in cargo_findings)
        assert "RUSTSEC-2024-0001" in messages
        assert "openssl" in messages
        assert {f.severity for f in cargo_findings} == {"high", "medium"}
        assert reviewer.tool_results["cargo-audit"]["cargo_findings"] == 3
        assert reviewer.tool_results["cargo-audit"]["truncated"] is False

    def test_cargo_missing_binary(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """AC-3: cargo not in PATH → status='skipped', reason='cargo not installed'."""
        _make_cargo_repo(tmp_path)

        def raise_fnf(*args, **kwargs):
            raise FileNotFoundError(2, "No such file: 'cargo'")

        monkeypatch.setattr(subprocess, "run", raise_fnf)
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        reviewer.scan()
        cargo = reviewer.tool_results["cargo-audit"]
        assert cargo["status"] == "skipped"
        assert cargo["reason"] == "cargo not installed"
        # No exception bubbled up.

    def test_cargo_invalid_json_stdout(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """AC-4: invalid JSON → status='failed', error mentions parse."""
        _make_cargo_repo(tmp_path)
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **kw: _fake_process(returncode=1, stdout="not json at all"),
        )
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        reviewer.scan()
        cargo = reviewer.tool_results["cargo-audit"]
        assert cargo["status"] == "failed"
        assert "json parse" in str(cargo.get("error", "")).lower()

    def test_cargo_truncates_at_twenty(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """AC-5: 25 vulns input → 20 in findings, truncated=True."""
        _make_cargo_repo(tmp_path)
        big = {
            "vulnerabilities": {
                "found": True,
                "count": 25,
                "list": [
                    {
                        "advisory": {
                            "id": f"RUSTSEC-2024-{i:04d}",
                            "package": f"pkg-{i}",
                            "title": "Vulnerability",
                            "severity": "high",
                        }
                    }
                    for i in range(25)
                ],
            }
        }
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **kw: _fake_process(returncode=1, stdout=json.dumps(big)),
        )
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        report = reviewer.scan()
        cargo_findings = [f for f in report.findings if f.rule == "cargo-audit"]
        assert len(cargo_findings) == 20
        assert reviewer.tool_results["cargo-audit"]["truncated"] is True
        assert reviewer.tool_results["cargo-audit"]["cargo_findings"] == 20

    def test_cargo_timeout_recorded(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _make_cargo_repo(tmp_path)

        def raise_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="cargo", timeout=120)

        monkeypatch.setattr(subprocess, "run", raise_timeout)
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        reviewer.scan()
        assert reviewer.tool_results["cargo-audit"]["status"] == "failed"
        assert reviewer.tool_results["cargo-audit"]["error"] == "timeout"

    def test_cargo_no_repo_marker_skips_invocation(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """No Cargo.toml → cargo audit never invoked, no entry in tool_results."""
        called = []

        def fake(*args, **kwargs):
            called.append(args[0])
            return _fake_process(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake)
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        reviewer.scan()
        assert "cargo-audit" not in reviewer.tool_results
        for invocation in called:
            assert "cargo" not in invocation[0]


# ---------------------------------------------------------------------------
# pip-audit (Backlog #15 — analog of TASK-002)
# ---------------------------------------------------------------------------


class TestPipAudit:
    def test_pip_clean_zero_findings(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _make_pip_repo(tmp_path)
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **kw: subprocess.CompletedProcess(args=[], returncode=0, stdout="[]"),
        )
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        reviewer.scan()
        pip = reviewer.tool_results["pip-audit"]
        assert pip["status"] == "ok"
        assert pip["findings"] == 0

    def test_pip_vulns_from_fixture(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _make_pip_repo(tmp_path)
        payload = (FIXTURE_DIR / "pip-audit-output.json").read_text()
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **kw: subprocess.CompletedProcess(args=[], returncode=1, stdout=payload),
        )
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        report = reviewer.scan()
        pip_findings = [f for f in report.findings if f.rule == "pip-audit"]
        assert len(pip_findings) == 3
        messages = " ".join(f.message for f in pip_findings)
        assert "urllib3" in messages
        assert "GHSA-v845-jxx5-vc9f" in messages
        # Severities: high when fix_versions present, medium otherwise.
        severities = {f.severity for f in pip_findings}
        assert "high" in severities
        assert "medium" in severities

    def test_pip_missing_binary(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _make_pip_repo(tmp_path)

        def raise_fnf(*args, **kwargs):
            raise FileNotFoundError(2, "No such file: 'pip-audit'")

        monkeypatch.setattr(subprocess, "run", raise_fnf)
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        reviewer.scan()
        pip = reviewer.tool_results["pip-audit"]
        assert pip["status"] == "skipped"
        assert pip["reason"] == "pip-audit not installed"

    def test_pip_invalid_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _make_pip_repo(tmp_path)
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **kw: subprocess.CompletedProcess(args=[], returncode=1, stdout="not json"),
        )
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        reviewer.scan()
        pip = reviewer.tool_results["pip-audit"]
        assert pip["status"] == "failed"
        assert "json parse" in str(pip.get("error", "")).lower()

    def test_pip_truncates_at_twenty(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _make_pip_repo(tmp_path)
        big = [
            {
                "name": f"pkg-{i}",
                "version": "0.0.1",
                "vulns": [{"id": f"GHSA-{i}", "fix_versions": ["1.0.0"], "description": "x"}],
            }
            for i in range(25)
        ]
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *a, **kw: subprocess.CompletedProcess(
                args=[], returncode=1, stdout=json.dumps(big)
            ),
        )
        reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
        report = reviewer.scan()
        pip_findings = [f for f in report.findings if f.rule == "pip-audit"]
        # 20 packages enter the loop, each yielding 1 vuln → 20 findings.
        assert len(pip_findings) == 20
        assert reviewer.tool_results["pip-audit"]["truncated"] is True


# ---------------------------------------------------------------------------
# Integration: scan() surfaces tool_results in StepReport.message
# ---------------------------------------------------------------------------


def test_scan_message_includes_tool_summary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _make_cargo_repo(tmp_path)
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _fake_process(returncode=0))
    reviewer = SecurityReviewer(tmp_path, _fp(tmp_path))
    report = reviewer.scan()
    assert "cargo-audit=ok" in (report.message or "")
