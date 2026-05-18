"""Telemetry recorder — opt-in, privacy-first step duration tracking."""

from __future__ import annotations

import json
import math
import os
import statistics
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import IO, Any
from uuid import uuid4

DEFAULT_DIR = Path.home() / ".sendsprint" / "telemetry"

ALLOWED_TAGS = {"step", "step_name", "repo_tech", "status"}


@dataclass
class Span:
    """A single timed unit of work. Tags are restricted to a privacy allowlist."""

    name: str
    run_id: str
    started_at: float
    duration_ms: int = 0
    status: str = "running"
    tags: dict[str, str] = field(default_factory=dict)

    def set_tag(self, key: str, value: str) -> None:
        if key not in ALLOWED_TAGS:
            raise ValueError(f"telemetry tag {key!r} not in allowlist {sorted(ALLOWED_TAGS)}")
        self.tags[key] = value

    def set_status(self, status: str) -> None:
        self.status = status

    def to_jsonl(self) -> str:
        payload = asdict(self)
        return json.dumps(payload, separators=(",", ":")) + "\n"


class TelemetryBackend:
    """Pluggable sink for spans. Default backend is a JSONL file."""

    def emit(self, span: Span) -> None:  # pragma: no cover - abstract
        raise NotImplementedError


class JsonlFileBackend(TelemetryBackend):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, span: Span) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(span.to_jsonl())


class StreamBackend(TelemetryBackend):
    """Write JSONL spans to an arbitrary stream (used by tests)."""

    def __init__(self, stream: IO[str]) -> None:
        self.stream = stream

    def emit(self, span: Span) -> None:
        self.stream.write(span.to_jsonl())
        self.stream.flush()


class NullBackend(TelemetryBackend):
    """No-op backend used when telemetry is disabled."""

    def emit(self, span: Span) -> None:
        return None


@dataclass
class Telemetry:
    """Top-level opt-in telemetry handle.

    Default behavior is **disabled**. Spans go to the null backend so no
    bytes are written. Enable via ``SENDSPRINT_TELEMETRY=1`` env or
    constructor argument.
    """

    enabled: bool = False
    run_id: str = field(default_factory=lambda: uuid4().hex)
    backend: TelemetryBackend = field(default_factory=NullBackend)

    @classmethod
    def from_env(
        cls, env: dict[str, str] | None = None, *, base_dir: Path | None = None
    ) -> Telemetry:
        e = env if env is not None else os.environ
        flag = (e.get("SENDSPRINT_TELEMETRY") or "").strip().lower()
        enabled = flag in {"1", "true", "yes", "on"}
        if not enabled:
            return cls(enabled=False, backend=NullBackend())
        run_id = uuid4().hex
        target_dir = base_dir or DEFAULT_DIR
        backend: TelemetryBackend = JsonlFileBackend(target_dir / f"{run_id}.jsonl")
        return cls(enabled=True, run_id=run_id, backend=backend)

    @contextmanager
    def span(self, name: str, **tags: str):
        if not self.enabled:
            yield _NoopSpan()
            return
        start = time.perf_counter()
        span = Span(name=name, run_id=self.run_id, started_at=time.time())
        for k, v in tags.items():
            span.set_tag(k, str(v))
        try:
            yield span
            if span.status == "running":
                span.set_status("ok")
        except Exception:
            span.set_status("failed")
            raise
        finally:
            span.duration_ms = int((time.perf_counter() - start) * 1000)
            self.backend.emit(span)


class _NoopSpan:
    """Returned when telemetry is disabled. Accepts the same API as Span."""

    def set_tag(self, key: str, value: str) -> None:  # pragma: no cover - trivial
        return None

    def set_status(self, status: str) -> None:  # pragma: no cover - trivial
        return None


def aggregate_histogram(jsonl_path: Path, *, by: str = "name") -> dict[str, dict[str, Any]]:
    """Read a JSONL telemetry file and compute basic latency stats per group.

    Returns a mapping ``{group: {count, p50, p95, p99, max, min}}``.
    """
    buckets: dict[str, list[int]] = {}
    if not jsonl_path.exists():
        return {}
    with jsonl_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = record.get(by) or record.get("tags", {}).get(by) or "unknown"
            buckets.setdefault(str(key), []).append(int(record.get("duration_ms", 0)))
    out: dict[str, dict[str, Any]] = {}
    for key, samples in buckets.items():
        samples_sorted = sorted(samples)
        n = len(samples_sorted)
        out[key] = {
            "count": n,
            "min": samples_sorted[0],
            "max": samples_sorted[-1],
            "p50": samples_sorted[_pct_idx(0.5, n)],
            "p95": samples_sorted[_pct_idx(0.95, n)],
            "p99": samples_sorted[_pct_idx(0.99, n)],
            "mean": int(statistics.fmean(samples_sorted)),
        }
    return out


def _pct_idx(pct: float, n: int) -> int:
    """Nearest-rank percentile index (ceil method, capped at n-1)."""
    if n <= 0:
        return 0
    return min(n - 1, max(0, math.ceil(pct * n) - 1))
