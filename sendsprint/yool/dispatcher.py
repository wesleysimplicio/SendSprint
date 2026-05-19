"""Cache-aware sync dispatcher (issue #80, spec §8).

Computes ``input_id = sha256(canonical(payload))``, looks up a prior
receipt via ``ReceiptStore.find_by_input``. On hit, returns the cached
output. On miss, runs the executor, writes a receipt, returns the fresh
output. ``no_cache=True`` bypasses lookup but still writes a receipt.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .budgets import BudgetExceeded, BudgetGuard, BudgetLedger
from .catalog_v2 import YoolEntry
from .receipts import (
    Receipt,
    ReceiptCost,
    ReceiptStore,
    sha256_canonical,
    utcnow_iso,
    write_err_receipt,
    write_ok_receipt,
)
from .tuples import AgentTerms

Executor = Callable[[YoolEntry, Any], Any]
ExecutorWithCost = Callable[[YoolEntry, Any], tuple[Any, ReceiptCost]]


@dataclass
class DispatchResult:
    yool_id: str
    input_id: str
    output: Any
    receipt: Receipt
    cached: bool


class Dispatcher:
    """Cache-or-execute glue between the catalog and a runtime executor."""

    def __init__(
        self,
        *,
        store: ReceiptStore,
        executor: Executor | ExecutorWithCost,
        ledger: BudgetLedger | None = None,
        executor_returns_cost: bool = False,
    ) -> None:
        self.store = store
        self.executor = executor
        self.ledger = ledger or BudgetLedger()
        self._with_cost = executor_returns_cost

    def dispatch(
        self,
        entry: YoolEntry,
        payload: Any,
        *,
        no_cache: bool = False,
        agent_terms: AgentTerms | None = None,
    ) -> DispatchResult:
        input_id = sha256_canonical(payload)
        if not no_cache:
            cached = self.store.find_by_input(entry.yool_id, input_id)
            if cached is not None and cached.status == "ok":
                self.ledger.record(entry.yool_id, ReceiptCost())
                return DispatchResult(
                    yool_id=entry.yool_id,
                    input_id=input_id,
                    output=self._materialise_cached_output(cached),
                    receipt=cached,
                    cached=True,
                )

        guard = BudgetGuard(terms=agent_terms or AgentTerms())
        started = utcnow_iso()
        t0 = time.perf_counter()
        try:
            if self._with_cost:
                output, cost = self.executor(entry, payload)  # type: ignore[misc]
            else:
                output = self.executor(entry, payload)
                cost = ReceiptCost(
                    wall_ms=int((time.perf_counter() - t0) * 1000),
                )
            guard.check(
                tokens=cost.tokens_in + cost.tokens_out,
                wall_ms=cost.wall_ms,
                usd=cost.usd,
            )
            guard.commit(
                tokens=cost.tokens_in + cost.tokens_out,
                wall_ms=cost.wall_ms,
                usd=cost.usd,
            )
        except BudgetExceeded as exc:
            ended = utcnow_iso()
            receipt = write_err_receipt(
                self.store,
                yool_id=entry.yool_id,
                input_payload=payload,
                started_at=started,
                ended_at=ended,
                err=str(exc),
                status="err.budget",
                cost=ReceiptCost(wall_ms=int((time.perf_counter() - t0) * 1000)),
            )
            self.ledger.record(entry.yool_id, receipt.cost)
            raise
        except Exception as exc:  # noqa: BLE001
            ended = utcnow_iso()
            receipt = write_err_receipt(
                self.store,
                yool_id=entry.yool_id,
                input_payload=payload,
                started_at=started,
                ended_at=ended,
                err=f"{type(exc).__name__}: {exc}",
                status="err",
                cost=ReceiptCost(wall_ms=int((time.perf_counter() - t0) * 1000)),
            )
            self.ledger.record(entry.yool_id, receipt.cost)
            raise

        ended = utcnow_iso()
        receipt = write_ok_receipt(
            self.store,
            yool_id=entry.yool_id,
            input_payload=payload,
            output_payload=output,
            started_at=started,
            ended_at=ended,
            cost=cost,
        )
        self.ledger.record(entry.yool_id, receipt.cost)
        return DispatchResult(
            yool_id=entry.yool_id,
            input_id=input_id,
            output=output,
            receipt=receipt,
            cached=False,
        )

    def _materialise_cached_output(self, receipt: Receipt) -> Any:
        if receipt.output_payload is not None:
            return receipt.output_payload
        return {"output_id": receipt.output_id, "from_receipt": receipt.id}
