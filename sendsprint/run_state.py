"""Persistent run state for resumable and idempotent sprint delivery."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from sendsprint.policy import AutonomyLevel


def stable_run_id(*parts: object) -> str:
    """Build a deterministic run id from user-visible inputs."""
    raw = "|".join(str(part or "") for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"run-{digest}"


class RunState(BaseModel):
    """State persisted under `.sendsprint/runs/<run_id>.json`."""

    run_id: str
    source: str
    sprint_id: str
    autonomy_level: AutonomyLevel = "plan"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    planned: list[str] = Field(default_factory=list)
    completed: dict[str, str] = Field(default_factory=dict)
    failed: dict[str, str] = Field(default_factory=dict)

    def mark_planned(self, delivery_key: str) -> None:
        if delivery_key not in self.planned:
            self.planned.append(delivery_key)
        self.updated_at = datetime.now(UTC)

    def mark_completed(self, delivery_key: str) -> None:
        self.completed[delivery_key] = datetime.now(UTC).isoformat()
        self.failed.pop(delivery_key, None)
        self.updated_at = datetime.now(UTC)

    def mark_failed(self, delivery_key: str, reason: str) -> None:
        self.failed[delivery_key] = reason[:1000]
        self.updated_at = datetime.now(UTC)

    def is_completed(self, delivery_key: str) -> bool:
        return delivery_key in self.completed


class RunStateStore:
    """Loads and saves run state in the workspace/repo."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.runs_dir = self.root / ".sendsprint" / "runs"

    def path_for(self, run_id: str) -> Path:
        safe = "".join(ch for ch in run_id if ch.isalnum() or ch in {"-", "_"}).strip("-_")
        return self.runs_dir / f"{safe or 'run'}.json"

    def load_or_create(
        self,
        run_id: str,
        *,
        source: str,
        sprint_id: str,
        autonomy_level: AutonomyLevel = "plan",
    ) -> RunState:
        path = self.path_for(run_id)
        if path.exists():
            return RunState.model_validate_json(path.read_text(encoding="utf-8"))
        return RunState(
            run_id=run_id,
            source=source,
            sprint_id=sprint_id,
            autonomy_level=autonomy_level,
        )

    def save(self, state: RunState) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.path_for(state.run_id)
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        return path


def delivery_key(item_key: str, repo_name: str) -> str:
    """Unique key for one work item in one repository."""
    return f"{item_key}::{repo_name}"
