"""Audit trail for operator actions on runs.

Every mutation triggered by a human operator (pause, resume, cancel, rerun,
approve) is recorded as an immutable AuditEntry. The AuditLog provides
append-only storage with query and export capabilities.

Issue: #104
"""

from __future__ import annotations

import threading
from collections import deque
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OperatorAction = Literal[
    "pause",
    "resume",
    "cancel",
    "rerun",
    "approve",
    "open_evidence",
    "open_pr",
]


class AuditEntry(BaseModel):
    """Single audit record for an operator action."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operator: str
    action: OperatorAction
    run_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    result: str = "ok"
    detail: dict[str, Any] = Field(default_factory=dict)


class AuditLog:
    """Thread-safe, append-only audit log with query and export."""

    def __init__(self, max_entries: int = 5000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[AuditEntry] = deque(maxlen=max_entries)

    def append(self, entry: AuditEntry) -> AuditEntry:
        """Record an audit entry. Returns the entry for chaining."""
        with self._lock:
            self._entries.append(entry)
        return entry

    def query(
        self,
        *,
        run_id: str | None = None,
        operator: str | None = None,
        action: OperatorAction | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Return matching entries (newest first), up to *limit*."""
        with self._lock:
            entries = list(self._entries)
        # Filter
        if run_id is not None:
            entries = [e for e in entries if e.run_id == run_id]
        if operator is not None:
            entries = [e for e in entries if e.operator == operator]
        if action is not None:
            entries = [e for e in entries if e.action == action]
        # Newest first, capped
        return list(reversed(entries))[:limit]

    def export(self, *, run_id: str | None = None) -> list[dict[str, Any]]:
        """Export entries as JSON-serializable dicts."""
        entries = self.query(run_id=run_id, limit=99999)
        return [e.model_dump(mode="json") for e in entries]

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


# Module-level singleton used by the API routes.
audit_log = AuditLog()
