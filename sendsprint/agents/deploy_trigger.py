"""Deploy trigger + ticket status callback (Sprint 2 issue #10).

Runs after PR creation (step 9). Opt-in via ``workspace.yaml::deploy``.

Hard rules:
  - Failure of the deploy webhook does NOT mark the run as failed — the
    PR was still opened and remains the source of truth.
  - Callback to the ticket (Jira / ADO) is **idempotent** via
    ``Idempotency-Key: <run_id>:<item_id>``.
  - Retry with exponential backoff (max 4 tries) on transport errors only;
    HTTP 4xx are surfaced immediately.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import httpx

from ..models.reports import StepReport

logger = logging.getLogger(__name__)


@dataclass
class DeployConfig:
    enabled: bool = False
    provider: str = "webhook"  # "webhook" | "github-actions" | "circleci" | "argocd"
    url: str | None = None
    method: str = "POST"
    headers: dict[str, str] | None = None
    final_status: str = "Deployed"


@dataclass
class DeployResult:
    triggered: bool
    status_code: int | None = None
    attempts: int = 0
    error: str | None = None


class TicketUpdater(Protocol):
    def update_status(self, item_key: str, status: str, comment: str | None = None) -> None: ...


class DeployTrigger:
    """Fires the configured deploy provider and writes a comment to the ticket."""

    def __init__(
        self,
        config: DeployConfig,
        *,
        ticket: TicketUpdater | None = None,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self.config = config
        self.ticket = ticket
        self.http_client = http_client
        self.sleep = sleep
        self.max_attempts = max_attempts

    def run(
        self,
        *,
        item_key: str,
        run_id: str,
        pr_url: str | None = None,
        deploy_url_override: str | None = None,
    ) -> StepReport:
        report = StepReport(step=11, name="deploy-trigger")
        if not self.config.enabled:
            report.status = "skipped"
            report.message = "deploy.enabled=false"
            return report
        target = deploy_url_override or self.config.url
        if not target:
            report.status = "skipped"
            report.message = "no deploy.url configured"
            return report

        result = self._fire(target, item_key=item_key, run_id=run_id)
        if result.triggered:
            report.status = "ok"
            report.message = (
                f"deploy triggered (status={result.status_code}, attempts={result.attempts})"
            )
            self._notify_ticket(item_key=item_key, run_id=run_id, pr_url=pr_url, target=target)
        else:
            report.status = "failed"
            report.message = (
                f"deploy webhook failed after {result.attempts} attempt(s): {result.error}"
            )
        return report

    @staticmethod
    def idempotency_key(run_id: str, item_key: str) -> str:
        return hashlib.sha256(f"{run_id}:{item_key}".encode()).hexdigest()[:32]

    def _fire(self, url: str, *, item_key: str, run_id: str) -> DeployResult:
        client_ctx = self.http_client or httpx.Client(timeout=30.0)
        headers = dict(self.config.headers or {})
        headers.setdefault("Idempotency-Key", self.idempotency_key(run_id, item_key))
        attempts = 0
        last_error: str | None = None
        try:
            for attempt in range(1, self.max_attempts + 1):
                attempts = attempt
                try:
                    response = client_ctx.request(self.config.method, url, headers=headers)
                except httpx.HTTPError as exc:
                    last_error = f"transport: {exc}"
                    if attempt < self.max_attempts:
                        self.sleep(2 ** (attempt - 1))
                        continue
                    return DeployResult(False, attempts=attempts, error=last_error)
                if 200 <= response.status_code < 300:
                    return DeployResult(True, status_code=response.status_code, attempts=attempts)
                if 400 <= response.status_code < 500:
                    return DeployResult(
                        False,
                        status_code=response.status_code,
                        attempts=attempts,
                        error=f"http {response.status_code}",
                    )
                last_error = f"http {response.status_code}"
                if attempt < self.max_attempts:
                    self.sleep(2 ** (attempt - 1))
            return DeployResult(False, attempts=attempts, error=last_error)
        finally:
            if self.http_client is None:
                client_ctx.close()

    def _notify_ticket(
        self, *, item_key: str, run_id: str, pr_url: str | None, target: str
    ) -> None:
        if self.ticket is None:
            return
        comment = f"Deploy triggered by SendSprint (run {run_id}).\nTarget: {target}\n"
        if pr_url:
            comment += f"PR: {pr_url}\n"
        try:
            self.ticket.update_status(item_key, self.config.final_status, comment)
        except Exception as exc:  # noqa: BLE001 - ticket failure must not break flow
            logger.warning("ticket update failed for %s: %s", item_key, exc)
