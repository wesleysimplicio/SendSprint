"""Sprint scope filtering: 'all' or 'mine' (current user only)."""

from __future__ import annotations

from .models.sprint import Sprint, SprintItem
from .models.workspace import ScopeConfig


def _matches_user(item: SprintItem, scope: ScopeConfig) -> bool:
    """True if item assignee matches the configured user identity."""
    if scope.user_account_id and item.assignee_account_id == scope.user_account_id:
        return True
    if scope.user_descriptor and item.assignee_descriptor == scope.user_descriptor:
        return True
    if scope.user_email and item.assignee_email and (
        item.assignee_email.lower() == scope.user_email.lower()
    ):
        return True
    if scope.user_display_name and item.assignee and (
        item.assignee.strip().lower() == scope.user_display_name.strip().lower()
    ):
        return True
    return False


def apply_scope(sprint: Sprint, scope: ScopeConfig) -> Sprint:
    """Return a new Sprint with items filtered per scope mode.

    mode='all'  -> sprint unchanged
    mode='mine' -> only items assigned to the configured user
    """
    if scope.mode == "all":
        return sprint
    filtered = [i for i in sprint.items if _matches_user(i, scope)]
    return sprint.model_copy(update={"items": filtered})


def build_scope(
    mode: str = "all",
    user_email: str | None = None,
    user_account_id: str | None = None,
    user_descriptor: str | None = None,
    user_display_name: str | None = None,
) -> ScopeConfig:
    """Build a ScopeConfig from CLI/programmatic args."""
    if mode not in ("all", "mine"):
        raise ValueError(f"scope mode must be 'all' or 'mine', got {mode!r}")
    return ScopeConfig(
        mode=mode,  # type: ignore[arg-type]
        user_email=user_email,
        user_account_id=user_account_id,
        user_descriptor=user_descriptor,
        user_display_name=user_display_name,
    )
