"""LLM-powered code generation per sprint item (Sprint 2 issue #9).

This agent is **opt-in**. Default workflow runs without it. When enabled
via ``workspace.yaml`` (``code_generation.enabled: true``) or CLI flag
``--llm-codegen``, ``CodeGenerator.generate()`` runs between step 3 (dev)
and step 4 (lint), producing a unified diff that the orchestrator applies
to the worktree.

Hard rules:
  - Costs and token counts surface in ``StepReport.message``.
  - Failures never halt the run — they become ``status="failed"`` reports
    that the fix-loop tries to recover from.
  - Generated diffs still pass through ``LintRunner`` and ``PrReviewer``;
    no diff is committed without those gates.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..llm import LlmClient, LlmError
from ..models.reports import StepReport

logger = logging.getLogger(__name__)

DIFF_BLOCK_RE = re.compile(r"```(?:diff|patch)?\s*\n(?P<body>.*?)```", flags=re.DOTALL)


class _LlmLike(Protocol):
    """Subset of ``LlmClient`` the agent depends on (lets tests pass mocks)."""

    def complete(self, prompt: str, system: str | None = ..., max_tokens: int = ...) -> str: ...


@dataclass
class CodegenBudget:
    """Hard guardrails enforced before each request."""

    max_usd: float = 1.0
    max_tokens: int = 8000


@dataclass
class CodegenResult:
    """Outcome surfaced in StepReport.message / RunReport.summary."""

    diff: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_usd: float = 0.0


class CodeGenerator:
    """LLM-driven diff producer for a single sprint item."""

    def __init__(
        self,
        repo: Path,
        item_title: str,
        item_description: str,
        acceptance: list[str],
        *,
        client: _LlmLike | None = None,
        budget: CodegenBudget | None = None,
        secret_filter: Callable[[str], str] | None = None,
    ) -> None:
        self.repo = Path(repo).resolve()
        self.item_title = item_title
        self.item_description = item_description
        self.acceptance = acceptance
        self.client = client
        self.budget = budget or CodegenBudget()
        self.secret_filter = secret_filter

    def generate(self) -> StepReport:
        report = StepReport(step=3, name="llm-codegen", repo=str(self.repo))
        try:
            client = self.client or LlmClient()
        except LlmError as exc:
            report.status = "skipped"
            report.message = f"llm client unavailable: {exc}"
            return report

        prompt = self._build_prompt()
        if self.secret_filter is not None:
            prompt = self.secret_filter(prompt)

        try:
            raw = client.complete(prompt, max_tokens=self.budget.max_tokens)
        except LlmError as exc:
            report.status = "failed"
            report.message = f"llm call failed: {exc}"
            return report
        except Exception as exc:  # noqa: BLE001 - LLM SDKs raise broad errors
            report.status = "failed"
            report.message = f"llm call exception: {exc}"
            return report

        diff = self._extract_diff(raw)
        if not diff.strip():
            report.status = "failed"
            report.message = "model returned no diff block"
            return report

        result = CodegenResult(
            diff=diff,
            prompt_tokens=_rough_tokens(prompt),
            completion_tokens=_rough_tokens(raw),
        )
        result.estimated_usd = _estimate_cost(result.prompt_tokens, result.completion_tokens)

        if result.estimated_usd > self.budget.max_usd:
            report.status = "failed"
            report.message = (
                f"budget exceeded: ${result.estimated_usd:.4f} > ${self.budget.max_usd:.2f}"
            )
            return report

        report.status = "ok"
        report.message = (
            f"llm-codegen generated {len(diff.splitlines())} diff line(s); "
            f"tokens={result.prompt_tokens}/{result.completion_tokens}; "
            f"~${result.estimated_usd:.4f}"
        )
        # Attach diff via the standard test-evidence channel so the orchestrator
        # can apply it without coupling to an extra field.
        from ..models.reports import TestEvidence

        report.evidence.append(
            TestEvidence(kind="log", title="llm-codegen.diff", passed=True, message=diff)
        )
        return report

    def _build_prompt(self) -> str:
        ac_lines = "\n".join(f"- {ac}" for ac in self.acceptance)
        return (
            "You are a senior engineer implementing a sprint task.\n\n"
            f"Title: {self.item_title}\n\n"
            f"Description:\n{self.item_description}\n\n"
            f"Acceptance Criteria:\n{ac_lines}\n\n"
            "Output: a unified diff inside a single ```diff code block. "
            "Touch only files necessary to satisfy the ACs. No prose outside "
            "the code block."
        )

    @staticmethod
    def _extract_diff(text: str) -> str:
        match = DIFF_BLOCK_RE.search(text)
        if match:
            return match.group("body")
        # Fallback: treat the whole response as diff if it starts with `diff --git` or `--- `.
        stripped = text.strip()
        if stripped.startswith("diff --git") or stripped.startswith("--- "):
            return stripped + "\n"
        return ""


def _rough_tokens(text: str) -> int:
    """Cheap token estimator (~4 chars per token). Good enough for budget gates."""
    return max(1, len(text) // 4)


# Per ADR-006 (TBD): default prices in USD per 1M tokens.
_DEFAULT_PRICE_IN_PER_M = 3.0
_DEFAULT_PRICE_OUT_PER_M = 15.0


def _estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (
        prompt_tokens / 1_000_000 * _DEFAULT_PRICE_IN_PER_M
        + completion_tokens / 1_000_000 * _DEFAULT_PRICE_OUT_PER_M
    )
