"""Opt-in telemetry for SendSprint step duration histograms.

Implements Backlog issue #14: opt-in spans for step latency analysis,
JSONL backend by default, no payload leaves the host without explicit
config. Default privacy is opt-out (nothing emitted).

Usage::

    from sendsprint.telemetry import Telemetry

    tel = Telemetry.from_env()  # honors SENDSPRINT_TELEMETRY env var
    with tel.span("step-3-dev", repo_tech="bun") as span:
        ...
        span.set_status("ok")
"""

from __future__ import annotations

from .recorder import Span, Telemetry, TelemetryBackend, aggregate_histogram

__all__ = ["Span", "Telemetry", "TelemetryBackend", "aggregate_histogram"]
