"""Tests for Ralph Wiggum and Codex Goal loop contracts."""

from __future__ import annotations

from sendsprint.loops import LoopAttempt, LoopContract, LoopReport


def test_loop_report_records_exit_signal() -> None:
    contract = LoopContract(
        kind="codex-goal",
        objective="finish issue",
        acceptance_criteria=["tests pass"],
        validation_gates=["pytest"],
    )
    report = LoopReport(contract=contract)
    report = report.record(LoopAttempt(attempt=1, status="passed", exit_signal=True))
    assert report.exit_signal is True
    assert report.final_status == "passed"
    assert contract.display_name == "Codex /goal"
    assert contract.command_hint == "/goal finish issue"


def test_loop_contract_exposes_claude_ralph_command() -> None:
    contract = LoopContract(
        kind="ralph-wiggum",
        objective="fix issue with tests",
        max_attempts=7,
        completion_promise="DONE",
    )

    assert contract.display_name == "Claude Code Ralph Wiggum"
    assert (
        contract.command_hint
        == '/ralph-loop "fix issue with tests" --max-iterations 7 --completion-promise "DONE"'
    )
