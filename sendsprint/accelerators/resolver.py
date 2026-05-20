"""Resolve the best available accelerator backend.

:func:`resolve_accelerator` returns a :class:`RustBridge` wired to the Rust
binary when available, otherwise a ``RustBridge(None)`` that transparently
uses :mod:`python_impl` for every call.

Issue: #108
"""

from __future__ import annotations

import logging
import time
from typing import Any

from sendsprint.accelerators import python_impl
from sendsprint.accelerators.rust_bridge import RustBridge, detect_rust_accelerator

logger = logging.getLogger(__name__)


def resolve_accelerator() -> RustBridge:
    """Return a :class:`RustBridge` using the best backend found at runtime."""
    binary = detect_rust_accelerator()
    if binary:
        logger.info("rust accelerator found: %s", binary)
    else:
        logger.debug("rust accelerator not found — using python fallback")
    return RustBridge(binary)


# ---------------------------------------------------------------------------
# Benchmark helper
# ---------------------------------------------------------------------------


class BenchmarkResult:
    """Holds timing results for a single operation comparison."""

    __slots__ = ("name", "python_ms", "rust_ms")

    def __init__(self, name: str, python_ms: float, rust_ms: float) -> None:
        self.name = name
        self.python_ms = python_ms
        self.rust_ms = rust_ms

    @property
    def speedup(self) -> float:
        if self.rust_ms <= 0:
            return 0.0
        return self.python_ms / self.rust_ms

    def __repr__(self) -> str:
        return (
            f"BenchmarkResult({self.name!r}, "
            f"py={self.python_ms:.2f}ms, "
            f"rs={self.rust_ms:.2f}ms, "
            f"speedup={self.speedup:.1f}x)"
        )


def benchmark(
    diff_text: str,
    items: list[str] | None = None,
    payload: Any | None = None,
    *,
    iterations: int = 100,
) -> list[BenchmarkResult]:
    """Compare Python vs Rust for each hot path.

    Returns a list of :class:`BenchmarkResult`.  When Rust is unavailable the
    ``rust_ms`` field equals ``python_ms`` (speedup = 1.0x).
    """
    bridge = resolve_accelerator()
    results: list[BenchmarkResult] = []

    if items is None:
        items = ["a", "b", "c", "a", "b", "d"]
    if payload is None:
        payload = {"key": "value", "n": 42}

    # -- fast_scan ---------------------------------------------------------
    t0 = time.perf_counter()
    for _ in range(iterations):
        python_impl.fast_scan(diff_text)
    py_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(iterations):
        bridge.fast_scan(diff_text)
    rs_ms = (time.perf_counter() - t0) * 1000
    results.append(BenchmarkResult("fast_scan", py_ms, rs_ms))

    # -- fast_diff ---------------------------------------------------------
    t0 = time.perf_counter()
    for _ in range(iterations):
        python_impl.fast_diff(diff_text)
    py_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(iterations):
        bridge.fast_diff(diff_text)
    rs_ms = (time.perf_counter() - t0) * 1000
    results.append(BenchmarkResult("fast_diff", py_ms, rs_ms))

    # -- fast_dedupe -------------------------------------------------------
    t0 = time.perf_counter()
    for _ in range(iterations):
        python_impl.fast_dedupe(items)
    py_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(iterations):
        bridge.fast_dedupe(items)
    rs_ms = (time.perf_counter() - t0) * 1000
    results.append(BenchmarkResult("fast_dedupe", py_ms, rs_ms))

    # -- fast_receipt_hash -------------------------------------------------
    t0 = time.perf_counter()
    for _ in range(iterations):
        python_impl.fast_receipt_hash(payload)
    py_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(iterations):
        bridge.fast_receipt_hash(payload)
    rs_ms = (time.perf_counter() - t0) * 1000
    results.append(BenchmarkResult("fast_receipt_hash", py_ms, rs_ms))

    return results
