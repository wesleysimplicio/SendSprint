"""Worker resolver — picks the best available runtime.

Priority: Go worker (if binary on PATH) > Python fallback (always).
"""

from __future__ import annotations

import logging
from typing import Union

from sendsprint.workers.go_spec import GoWorkerProxy, detect_go_worker
from sendsprint.workers.python_worker import PythonWorker

logger = logging.getLogger(__name__)

Worker = Union[PythonWorker, GoWorkerProxy]


def resolve_worker(
    *,
    prefer_go: bool = True,
    max_concurrency: int = 4,
) -> Worker:
    """Return the best available worker runtime.

    When *prefer_go* is True and the Go binary is on PATH, returns a
    GoWorkerProxy.  Otherwise returns a PythonWorker (always available).
    """
    if prefer_go and detect_go_worker():
        logger.info("Go worker detected — using GoWorkerProxy")
        return GoWorkerProxy()

    logger.info("Using PythonWorker fallback (concurrency=%d)", max_concurrency)
    return PythonWorker(max_concurrency=max_concurrency)
