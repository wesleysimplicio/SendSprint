"""Tests for sendsprint/telemetry (Backlog issue #14)."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from sendsprint.telemetry import Telemetry, aggregate_histogram
from sendsprint.telemetry.recorder import (
    JsonlFileBackend,
    NullBackend,
    Span,
    StreamBackend,
)


class TestDefaultPrivacy:
    def test_disabled_when_env_unset(self) -> None:
        tel = Telemetry.from_env(env={})
        assert tel.enabled is False
        assert isinstance(tel.backend, NullBackend)

    def test_disabled_when_env_false(self) -> None:
        tel = Telemetry.from_env(env={"SENDSPRINT_TELEMETRY": "0"})
        assert tel.enabled is False

    def test_no_writes_when_disabled(self, tmp_path: Path) -> None:
        tel = Telemetry(enabled=False, backend=NullBackend())
        with tel.span("step-3-dev") as span:
            assert span is not None
        # No telemetry directory created when disabled.
        assert not any(tmp_path.iterdir())


class TestEnabled:
    def test_enabled_writes_jsonl_to_file(self, tmp_path: Path) -> None:
        tel = Telemetry.from_env(env={"SENDSPRINT_TELEMETRY": "1"}, base_dir=tmp_path)
        assert tel.enabled is True
        with tel.span("step-3-dev", repo_tech="bun", step="3") as span:
            span.set_status("ok")
        files = list(tmp_path.glob("*.jsonl"))
        assert len(files) == 1
        contents = files[0].read_text(encoding="utf-8").strip().splitlines()
        assert len(contents) == 1
        record = json.loads(contents[0])
        assert record["name"] == "step-3-dev"
        assert record["tags"]["repo_tech"] == "bun"
        assert record["tags"]["step"] == "3"
        assert record["status"] == "ok"
        assert "duration_ms" in record

    def test_exception_sets_status_failed_and_propagates(self) -> None:
        buf = io.StringIO()
        tel = Telemetry(enabled=True, backend=StreamBackend(buf))
        with pytest.raises(RuntimeError), tel.span("step-5-tests"):
            raise RuntimeError("boom")
        records = [json.loads(line) for line in buf.getvalue().splitlines() if line]
        assert records[0]["status"] == "failed"

    def test_default_status_ok_when_no_exception(self) -> None:
        buf = io.StringIO()
        tel = Telemetry(enabled=True, backend=StreamBackend(buf))
        with tel.span("step-4-lint"):
            pass
        records = [json.loads(line) for line in buf.getvalue().splitlines() if line]
        assert records[0]["status"] == "ok"


class TestTagAllowlist:
    def test_unknown_tag_raises(self) -> None:
        span = Span(name="x", run_id="r", started_at=0)
        with pytest.raises(ValueError, match="not in allowlist"):
            span.set_tag("user_email", "leaked@example.com")

    def test_allowed_tags_accepted(self) -> None:
        span = Span(name="x", run_id="r", started_at=0)
        for key in ("step", "step_name", "repo_tech", "status"):
            span.set_tag(key, "value")
        assert span.tags == {
            "step": "value",
            "step_name": "value",
            "repo_tech": "value",
            "status": "value",
        }


class TestAggregateHistogram:
    def test_aggregates_by_name(self, tmp_path: Path) -> None:
        path = tmp_path / "spans.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for ms in (10, 20, 30, 40, 50):
                fh.write(
                    json.dumps(
                        {
                            "name": "step-3-dev",
                            "run_id": "r",
                            "started_at": 0,
                            "duration_ms": ms,
                            "status": "ok",
                            "tags": {},
                        }
                    )
                    + "\n"
                )
        hist = aggregate_histogram(path)
        bucket = hist["step-3-dev"]
        assert bucket["count"] == 5
        assert bucket["min"] == 10
        assert bucket["max"] == 50
        assert bucket["p50"] == 30
        assert bucket["p95"] == 50

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert aggregate_histogram(tmp_path / "missing.jsonl") == {}

    def test_skips_invalid_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "spans.jsonl"
        path.write_text(
            "not json\n"
            + json.dumps({"name": "x", "run_id": "r", "started_at": 0, "duration_ms": 10})
            + "\n"
        )
        hist = aggregate_histogram(path)
        assert hist["x"]["count"] == 1


class TestJsonlBackend:
    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        nested = tmp_path / "deeply" / "nested" / "out.jsonl"
        backend = JsonlFileBackend(nested)
        backend.emit(Span(name="x", run_id="r", started_at=0, duration_ms=1))
        assert nested.exists()
        assert "x" in nested.read_text(encoding="utf-8")
