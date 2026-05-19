"""HTTP API for the SendSprint web flow.

Lazy exports avoid requiring FastAPI just to import API-adjacent helpers in
tests or MCP utilities.
"""

from __future__ import annotations

from typing import Any

__all__ = ["app", "create_app"]


def __getattr__(name: str) -> Any:
    if name in {"app", "create_app"}:
        from sendsprint.api.server import app, create_app

        return {"app": app, "create_app": create_app}[name]
    raise AttributeError(name)
