"""Tests for sendsprint/agents/code_generator.py (Sprint 2 issue #9)."""

from __future__ import annotations

from pathlib import Path

from sendsprint.agents.code_generator import (
    CodegenBudget,
    CodeGenerator,
    _estimate_cost,
    _rough_tokens,
)


class MockClient:
    def __init__(self, response: str | None = None, exc: Exception | None = None) -> None:
        self.response = response
        self.exc = exc
        self.captured_prompt: str | None = None

    def complete(self, prompt: str, system: str | None = None, max_tokens: int = 1024) -> str:
        self.captured_prompt = prompt
        if self.exc is not None:
            raise self.exc
        return self.response or ""


SAMPLE_DIFF = """diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1 +1 @@
-old
+new
"""


class TestCodeGenerator:
    def test_ok_when_diff_block_present(self, tmp_path: Path) -> None:
        client = MockClient(response=f"Sure, here's the diff:\n```diff\n{SAMPLE_DIFF}```\n")
        gen = CodeGenerator(
            tmp_path,
            "Add bun detector",
            "Detect bun.lockb",
            ["AC-1 detect bun.lockb"],
            client=client,
        )
        report = gen.generate()
        assert report.status == "ok"
        assert "diff line" in (report.message or "")
        assert any(ev.title == "llm-codegen.diff" for ev in report.evidence)

    def test_failed_when_no_diff_block(self, tmp_path: Path) -> None:
        client = MockClient(response="I cannot help with this request.")
        gen = CodeGenerator(tmp_path, "x", "y", ["z"], client=client)
        report = gen.generate()
        assert report.status == "failed"
        assert "no diff block" in (report.message or "")

    def test_failed_when_llm_raises(self, tmp_path: Path) -> None:
        from sendsprint.llm import LlmError

        client = MockClient(exc=LlmError("rate limited"))
        gen = CodeGenerator(tmp_path, "x", "y", ["z"], client=client)
        report = gen.generate()
        assert report.status == "failed"
        assert "rate limited" in (report.message or "")

    def test_failed_when_unexpected_exception(self, tmp_path: Path) -> None:
        client = MockClient(exc=RuntimeError("oops"))
        gen = CodeGenerator(tmp_path, "x", "y", ["z"], client=client)
        report = gen.generate()
        assert report.status == "failed"
        assert "oops" in (report.message or "")

    def test_budget_cap_aborts(self, tmp_path: Path) -> None:
        big_diff = "```diff\n" + ("+x\n" * 10_000) + "```\n"
        # Give the model a huge response and tiny budget.
        client = MockClient(response=big_diff)
        gen = CodeGenerator(
            tmp_path,
            "title",
            "desc " * 10_000,
            ["ac"],
            client=client,
            budget=CodegenBudget(max_usd=0.0001, max_tokens=200_000),
        )
        report = gen.generate()
        assert report.status == "failed"
        assert "budget exceeded" in (report.message or "")

    def test_secret_filter_invoked(self, tmp_path: Path) -> None:
        captured = {}
        client = MockClient(response=f"```diff\n{SAMPLE_DIFF}```\n")

        def filter_fn(prompt: str) -> str:
            captured["prompt"] = prompt
            return prompt.replace("API_KEY=xxx", "API_KEY=<redacted>")

        gen = CodeGenerator(
            tmp_path,
            "title",
            "API_KEY=xxx",
            ["ac"],
            client=client,
            secret_filter=filter_fn,
        )
        gen.generate()
        assert "API_KEY=xxx" in captured["prompt"]
        # Sent to LLM with redaction applied.
        assert "API_KEY=<redacted>" in (client.captured_prompt or "")

    def test_diff_fallback_no_code_block(self, tmp_path: Path) -> None:
        """Some models drop the ``` fence — accept raw `diff --git` output."""
        raw = SAMPLE_DIFF  # already starts with `diff --git`
        client = MockClient(response=raw)
        gen = CodeGenerator(tmp_path, "x", "y", ["z"], client=client)
        report = gen.generate()
        assert report.status == "ok"


class TestEstimators:
    def test_rough_tokens_floor_one(self) -> None:
        assert _rough_tokens("") == 1
        assert _rough_tokens("abcd") == 1
        assert _rough_tokens("abcd" * 1000) == 1000

    def test_estimate_cost_positive(self) -> None:
        cost = _estimate_cost(1000, 500)
        assert cost > 0


class TestPromptBuilding:
    def test_prompt_includes_title_and_acs(self, tmp_path: Path) -> None:
        client = MockClient(response=f"```diff\n{SAMPLE_DIFF}```\n")
        gen = CodeGenerator(
            tmp_path,
            "TASK-001 Add bun detector",
            "Bun runtime support",
            ["AC-1 detect bun.lockb", "AC-2 bun wins over node"],
            client=client,
        )
        gen.generate()
        prompt = client.captured_prompt or ""
        assert "TASK-001 Add bun detector" in prompt
        assert "AC-1 detect bun.lockb" in prompt
        assert "unified diff" in prompt
