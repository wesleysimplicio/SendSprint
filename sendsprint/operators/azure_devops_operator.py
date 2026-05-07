"""AzureDevopsOperator - reads work items from an Azure DevOps iteration."""

from __future__ import annotations

import base64
import logging
import os
from datetime import datetime
from typing import Any

import httpx

from sendsprint.models import Sprint, SprintItem
from sendsprint.operators.base import BaseOperator, TransportUnavailable

logger = logging.getLogger(__name__)

ADO_TYPE_MAP = {
    "user story": "Story",
    "product backlog item": "Story",
    "task": "Task",
    "bug": "Bug",
    "feature": "Feature",
    "epic": "Epic",
    "issue": "Issue",
}


class AzureDevopsOperator(BaseOperator):
    """Reads an Azure DevOps iteration (sprint) via MCP, REST API, or Playwright.

    Identifies the iteration by its ``IterationPath`` (e.g. ``MyTeam\\Sprint 12``).
    """

    source = "azuredevops"

    def __init__(
        self,
        organization: str | None = None,
        project: str | None = None,
        team: str | None = None,
        pat: str | None = None,
        transport: str = "auto",
        cdp_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(transport=transport, **kwargs)
        self.organization = organization or os.getenv("AZURE_DEVOPS_ORG", "")
        self.project = project or os.getenv("AZURE_DEVOPS_PROJECT", "")
        self.team = team or os.getenv("AZURE_DEVOPS_TEAM", "")
        self.pat = pat or os.getenv("AZURE_DEVOPS_PAT", "")
        self.cdp_url = cdp_url or os.getenv("PLAYWRIGHT_CDP_URL", "http://127.0.0.1:9222")

    def _api_available(self) -> bool:
        return bool(self.organization and self.project and self.pat)

    def _read_via_mcp(self, iteration_path: str, **_: Any) -> Sprint:
        try:
            from sendsprint.operators import _mcp_bridge
        except ImportError as exc:
            raise TransportUnavailable("MCP bridge module missing") from exc
        return _mcp_bridge.call_ado_mcp(iteration_path=iteration_path)

    def _read_via_api(self, iteration_path: str, **_: Any) -> Sprint:
        if not self._api_available():
            raise TransportUnavailable("Azure DevOps credentials missing (ORG/PROJECT/PAT)")
        token = base64.b64encode(f":{self.pat}".encode()).decode()
        headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
        base = f"https://dev.azure.com/{self.organization}/{self.project}"
        wiql = {
            "query": (
                f"SELECT [System.Id] FROM WorkItems "
                f"WHERE [System.IterationPath] = '{iteration_path}' "
                f"AND [System.TeamProject] = '{self.project}'"
            )
        }
        with httpx.Client(timeout=30.0, headers=headers) as client:
            wiql_resp = client.post(
                f"{base}/_apis/wit/wiql?api-version=7.1",
                json=wiql,
            )
            wiql_resp.raise_for_status()
            ids = [w["id"] for w in wiql_resp.json().get("workItems", [])]
            items: list[SprintItem] = []
            for chunk in _chunked(ids, 200):
                if not chunk:
                    continue
                ids_param = ",".join(str(i) for i in chunk)
                detail = client.get(
                    f"{base}/_apis/wit/workitems",
                    params={
                        "ids": ids_param,
                        "$expand": "all",
                        "api-version": "7.1",
                    },
                )
                detail.raise_for_status()
                for wi in detail.json().get("value", []):
                    items.append(self._workitem_to_item(wi, base))
        return Sprint(
            id=iteration_path,
            name=iteration_path.split("\\")[-1],
            state="active",
            items=items,
            source="azuredevops",
            transport="api",
        )

    def _read_via_playwright(self, iteration_path: str, **_: Any) -> Sprint:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise TransportUnavailable("playwright not installed") from exc
        if not (self.organization and self.project):
            raise TransportUnavailable("ORG and PROJECT required for Playwright transport")
        url = (
            f"https://dev.azure.com/{self.organization}/{self.project}/_sprints/backlog/"
            f"{self.team or self.project}"
        )
        items: list[SprintItem] = []
        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(self.cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
            page.goto(url)
            page.wait_for_load_state("networkidle", timeout=20000)
            rows = page.locator("[role='row']").all()
            for row in rows:
                title = row.locator("[class*='title']").first
                if not title:
                    continue
                text = title.text_content() or ""
                if not text.strip():
                    continue
                items.append(
                    SprintItem(
                        id=text.strip(),
                        key=text.strip(),
                        type="Story",
                        title=text.strip(),
                        status="unknown",
                    )
                )
            page.close()
        return Sprint(
            id=iteration_path,
            name=iteration_path.split("\\")[-1],
            state="active",
            items=items,
            source="azuredevops",
            transport="playwright",
        )

    def _workitem_to_item(self, wi: dict[str, Any], base: str) -> SprintItem:
        fields = wi.get("fields", {})
        wi_type = fields.get("System.WorkItemType", "Issue").lower()
        item_type = ADO_TYPE_MAP.get(wi_type, "Issue")
        assigned_raw = fields.get("System.AssignedTo")
        assignee = (
            assigned_raw.get("displayName")
            if isinstance(assigned_raw, dict)
            else assigned_raw
        )
        return SprintItem(
            id=str(wi.get("id", "")),
            key=str(wi.get("id", "")),
            type=item_type,  # type: ignore[arg-type]
            title=fields.get("System.Title", ""),
            description=_strip_html(fields.get("System.Description")),
            status=fields.get("System.State", "unknown"),
            assignee=assignee,
            story_points=fields.get("Microsoft.VSTS.Scheduling.StoryPoints"),
            parent_key=str(fields.get("System.Parent")) if fields.get("System.Parent") else None,
            labels=(fields.get("System.Tags", "") or "").split("; ") if fields.get("System.Tags") else [],
            acceptance_criteria=_strip_html(fields.get("Microsoft.VSTS.Common.AcceptanceCriteria")),
            created_at=_parse_dt(fields.get("System.CreatedDate")),
            updated_at=_parse_dt(fields.get("System.ChangedDate")),
            source_url=f"{base}/_workitems/edit/{wi.get('id')}",
        )


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _strip_html(value: Any) -> str | None:
    if not value:
        return None
    import re

    text = re.sub(r"<[^>]+>", " ", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _chunked(seq: list[Any], n: int) -> list[list[Any]]:
    return [seq[i : i + n] for i in range(0, len(seq), n)]
