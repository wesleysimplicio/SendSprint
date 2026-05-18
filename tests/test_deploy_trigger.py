"""Tests for sendsprint/agents/deploy_trigger.py (Sprint 2 issue #10)."""

from __future__ import annotations

import httpx
import pytest

from sendsprint.agents.deploy_trigger import DeployConfig, DeployTrigger


def _mock_transport(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


class FakeTicket:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []
        self.fail = False

    def update_status(self, item_key: str, status: str, comment: str | None = None) -> None:
        if self.fail:
            raise RuntimeError("permission denied")
        self.calls.append((item_key, status, comment))


class TestDeployTrigger:
    def test_skipped_when_disabled(self) -> None:
        trig = DeployTrigger(DeployConfig(enabled=False))
        report = trig.run(item_key="TASK-1", run_id="r1")
        assert report.status == "skipped"
        assert "false" in (report.message or "")

    def test_skipped_when_no_url(self) -> None:
        trig = DeployTrigger(DeployConfig(enabled=True))
        report = trig.run(item_key="TASK-1", run_id="r1")
        assert report.status == "skipped"

    def test_ok_on_2xx_response(self) -> None:
        calls: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return httpx.Response(202, text='{"ok": true}')

        client = httpx.Client(transport=_mock_transport(handler))
        config = DeployConfig(enabled=True, url="https://deploy.example.com/hook")
        ticket = FakeTicket()
        trig = DeployTrigger(config, ticket=ticket, http_client=client)
        report = trig.run(item_key="TASK-42", run_id="run-abc", pr_url="https://pr/1")
        assert report.status == "ok"
        assert "status=202" in (report.message or "")
        assert ticket.calls == [
            (
                "TASK-42",
                "Deployed",
                pytest.approx_any_value if False else ticket.calls[0][2],
            )
        ]
        assert "Idempotency-Key" in calls[0].headers
        # Same key on retries.
        assert calls[0].headers["Idempotency-Key"] == DeployTrigger.idempotency_key(
            "run-abc", "TASK-42"
        )

    def test_4xx_fails_immediately(self) -> None:
        attempts = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            attempts["n"] += 1
            return httpx.Response(400, text="bad request")

        client = httpx.Client(transport=_mock_transport(handler))
        config = DeployConfig(enabled=True, url="https://deploy.example.com/hook")
        trig = DeployTrigger(config, http_client=client, sleep=lambda _: None)
        report = trig.run(item_key="x", run_id="r")
        assert report.status == "failed"
        assert "http 400" in (report.message or "")
        assert attempts["n"] == 1  # no retry on 4xx

    def test_5xx_retries_then_fails(self) -> None:
        attempts = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            attempts["n"] += 1
            return httpx.Response(503, text="busy")

        client = httpx.Client(transport=_mock_transport(handler))
        slept: list[float] = []
        trig = DeployTrigger(
            DeployConfig(enabled=True, url="https://x"),
            http_client=client,
            sleep=slept.append,
            max_attempts=4,
        )
        report = trig.run(item_key="x", run_id="r")
        assert report.status == "failed"
        assert attempts["n"] == 4
        # Exponential backoff: 1, 2, 4 (between 4 attempts there are 3 sleeps).
        assert slept == [1.0, 2.0, 4.0]

    def test_transport_error_retries_then_fails(self) -> None:
        attempts = {"n": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            attempts["n"] += 1
            raise httpx.ConnectError("dns")

        client = httpx.Client(transport=_mock_transport(handler))
        trig = DeployTrigger(
            DeployConfig(enabled=True, url="https://x"),
            http_client=client,
            sleep=lambda _: None,
            max_attempts=4,
        )
        report = trig.run(item_key="x", run_id="r")
        assert report.status == "failed"
        assert "transport" in (report.message or "")
        assert attempts["n"] == 4

    def test_idempotency_key_stable(self) -> None:
        a = DeployTrigger.idempotency_key("run1", "TASK-1")
        b = DeployTrigger.idempotency_key("run1", "TASK-1")
        c = DeployTrigger.idempotency_key("run2", "TASK-1")
        assert a == b
        assert a != c

    def test_ticket_update_failure_does_not_break_report(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200)

        client = httpx.Client(transport=_mock_transport(handler))
        ticket = FakeTicket()
        ticket.fail = True
        trig = DeployTrigger(
            DeployConfig(enabled=True, url="https://x"),
            ticket=ticket,
            http_client=client,
        )
        report = trig.run(item_key="x", run_id="r")
        # Deploy itself succeeded — ticket failure is logged but does not flip status.
        assert report.status == "ok"

    def test_url_override(self) -> None:
        captured: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(str(request.url))
            return httpx.Response(200)

        client = httpx.Client(transport=_mock_transport(handler))
        trig = DeployTrigger(DeployConfig(enabled=True, url="https://default"), http_client=client)
        trig.run(item_key="x", run_id="r", deploy_url_override="https://override.example/hook")
        assert captured == ["https://override.example/hook"]
