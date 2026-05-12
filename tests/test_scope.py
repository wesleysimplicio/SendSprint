"""Unit tests for sendsprint/scope.py — build_scope, apply_scope, _matches_user."""

from __future__ import annotations

import pytest

from sendsprint.models.sprint import Sprint, SprintItem
from sendsprint.models.workspace import ScopeConfig
from sendsprint.scope import _matches_user, apply_scope, build_scope

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _item(
    id: str = "1",
    key: str = "PROJ-1",
    assignee: str | None = None,
    assignee_email: str | None = None,
    assignee_account_id: str | None = None,
    assignee_descriptor: str | None = None,
) -> SprintItem:
    return SprintItem(
        id=id,
        key=key,
        type="Task",
        title="Test task",
        status="In Progress",
        assignee=assignee,
        assignee_email=assignee_email,
        assignee_account_id=assignee_account_id,
        assignee_descriptor=assignee_descriptor,
    )


def _sprint(*items: SprintItem) -> Sprint:
    return Sprint(id="SP-1", name="Sprint 1", items=list(items))


# ---------------------------------------------------------------------------
# build_scope
# ---------------------------------------------------------------------------


def test_build_scope_all_mode() -> None:
    scope = build_scope(mode="all")
    assert scope.mode == "all"
    assert scope.user_email is None
    assert scope.user_account_id is None
    assert scope.user_descriptor is None
    assert scope.user_display_name is None


def test_build_scope_mine_with_email() -> None:
    scope = build_scope(mode="mine", user_email="dev@example.com")
    assert scope.mode == "mine"
    assert scope.user_email == "dev@example.com"


def test_build_scope_mine_all_identity_fields() -> None:
    scope = build_scope(
        mode="mine",
        user_email="dev@example.com",
        user_account_id="acc-123",
        user_descriptor="desc-abc",
        user_display_name="Dev User",
    )
    assert scope.user_account_id == "acc-123"
    assert scope.user_descriptor == "desc-abc"
    assert scope.user_display_name == "Dev User"


def test_build_scope_invalid_mode_raises() -> None:
    with pytest.raises(ValueError, match="scope mode must be 'all' or 'mine'"):
        build_scope(mode="team")


# ---------------------------------------------------------------------------
# apply_scope — mode="all"
# ---------------------------------------------------------------------------


def test_apply_scope_all_preserves_items_when_status_developable() -> None:
    item = _item(assignee_email="a@b.com")
    sprint = _sprint(item)
    scope = ScopeConfig(mode="all")
    result = apply_scope(sprint, scope)
    assert [i.id for i in result.items] == [i.id for i in sprint.items]


def test_apply_scope_all_preserves_all_items() -> None:
    sprint = _sprint(
        _item("1", assignee_email="a@x.com"),
        _item("2", assignee_email="b@x.com"),
        _item("3"),
    )
    scope = ScopeConfig(mode="all")
    result = apply_scope(sprint, scope)
    assert len(result.items) == 3


# ---------------------------------------------------------------------------
# apply_scope — mode="mine", filter by account_id
# ---------------------------------------------------------------------------


def test_apply_scope_mine_filters_by_account_id() -> None:
    me = _item("1", assignee_account_id="acc-me")
    other = _item("2", assignee_account_id="acc-other")
    sprint = _sprint(me, other)
    scope = ScopeConfig(mode="mine", user_account_id="acc-me")
    result = apply_scope(sprint, scope)
    assert len(result.items) == 1
    assert result.items[0].id == "1"


# ---------------------------------------------------------------------------
# apply_scope — mode="mine", filter by email (case-insensitive)
# ---------------------------------------------------------------------------


def test_apply_scope_mine_filters_by_email_case_insensitive() -> None:
    me = _item("1", assignee_email="Dev@Example.COM")
    other = _item("2", assignee_email="other@example.com")
    sprint = _sprint(me, other)
    scope = ScopeConfig(mode="mine", user_email="dev@example.com")
    result = apply_scope(sprint, scope)
    assert len(result.items) == 1
    assert result.items[0].id == "1"


# ---------------------------------------------------------------------------
# apply_scope — mode="mine", filter by display_name
# ---------------------------------------------------------------------------


def test_apply_scope_mine_filters_by_display_name() -> None:
    me = _item("1", assignee="Alice Smith")
    other = _item("2", assignee="Bob Jones")
    sprint = _sprint(me, other)
    scope = ScopeConfig(mode="mine", user_display_name="Alice Smith")
    result = apply_scope(sprint, scope)
    assert len(result.items) == 1
    assert result.items[0].id == "1"


def test_apply_scope_mine_display_name_is_case_insensitive() -> None:
    me = _item("1", assignee="  alice smith  ")
    sprint = _sprint(me)
    scope = ScopeConfig(mode="mine", user_display_name="Alice Smith")
    result = apply_scope(sprint, scope)
    assert len(result.items) == 1


# ---------------------------------------------------------------------------
# apply_scope — mode="mine", filter by descriptor
# ---------------------------------------------------------------------------


def test_apply_scope_mine_filters_by_descriptor() -> None:
    me = _item("1", assignee_descriptor="vstfs:///Classification/TeamProject/abc")
    other = _item("2", assignee_descriptor="vstfs:///Classification/TeamProject/xyz")
    sprint = _sprint(me, other)
    scope = ScopeConfig(mode="mine", user_descriptor="vstfs:///Classification/TeamProject/abc")
    result = apply_scope(sprint, scope)
    assert len(result.items) == 1
    assert result.items[0].id == "1"


# ---------------------------------------------------------------------------
# apply_scope — mode="mine", no matches
# ---------------------------------------------------------------------------


def test_apply_scope_mine_no_matches_returns_empty_items() -> None:
    sprint = _sprint(
        _item("1", assignee_email="a@x.com"),
        _item("2", assignee_email="b@x.com"),
    )
    scope = ScopeConfig(mode="mine", user_email="nobody@x.com")
    result = apply_scope(sprint, scope)
    assert result.items == []
    assert result.id == sprint.id
    assert result.name == sprint.name


def test_apply_scope_mine_empty_sprint_returns_empty() -> None:
    sprint = _sprint()
    scope = ScopeConfig(mode="mine", user_email="dev@x.com")
    result = apply_scope(sprint, scope)
    assert result.items == []


# ---------------------------------------------------------------------------
# _matches_user (unit)
# ---------------------------------------------------------------------------


def test_matches_user_account_id_priority() -> None:
    item = _item(assignee_account_id="acc-me", assignee_email="wrong@x.com")
    scope = ScopeConfig(mode="mine", user_account_id="acc-me", user_email="other@x.com")
    assert _matches_user(item, scope) is True


def test_matches_user_no_identity_on_scope_returns_false() -> None:
    item = _item(assignee="Alice", assignee_email="alice@x.com")
    scope = ScopeConfig(mode="mine")
    assert _matches_user(item, scope) is False


def test_matches_user_unassigned_item_returns_false() -> None:
    item = _item()
    scope = ScopeConfig(mode="mine", user_email="dev@x.com", user_display_name="Dev")
    assert _matches_user(item, scope) is False


def test_matches_user_email_none_on_item_skips_email_check() -> None:
    item = _item(assignee_account_id="other-acc")
    scope = ScopeConfig(mode="mine", user_email="dev@x.com")
    assert _matches_user(item, scope) is False


# ---------------------------------------------------------------------------
# apply_scope — status whitelist
# ---------------------------------------------------------------------------


def _item_status(id: str, status: str) -> SprintItem:
    return SprintItem(id=id, key=f"K-{id}", type="Task", title="t", status=status)


def test_apply_scope_status_filter_keeps_developable() -> None:
    sprint = _sprint(
        _item_status("1", "New"),
        _item_status("2", "Active"),
        _item_status("3", "Done"),
        _item_status("4", "In Progress"),
    )
    scope = ScopeConfig(mode="all", allowed_statuses=["new", "active", "in progress"])
    result = apply_scope(sprint, scope)
    assert [i.id for i in result.items] == ["1", "2", "4"]


def test_apply_scope_status_filter_case_insensitive() -> None:
    sprint = _sprint(_item_status("1", "NEW"), _item_status("2", "done"))
    scope = ScopeConfig(mode="all", allowed_statuses=["new"])
    result = apply_scope(sprint, scope)
    assert [i.id for i in result.items] == ["1"]


def test_apply_scope_empty_allowed_statuses_is_passthrough() -> None:
    sprint = _sprint(_item_status("1", "Done"), _item_status("2", "Closed"))
    scope = ScopeConfig(mode="all", allowed_statuses=[])
    result = apply_scope(sprint, scope)
    assert len(result.items) == 2


# ---------------------------------------------------------------------------
# apply_scope — task_keys precedence
# ---------------------------------------------------------------------------


def test_apply_scope_task_keys_overrides_mode_and_status() -> None:
    sprint = _sprint(
        _item_status("1", "Done"),  # would be filtered by status
        _item_status("2", "New"),
        _item_status("3", "Active"),
    )
    scope = ScopeConfig(
        mode="mine",
        user_email="nobody@x.com",  # would filter everything
        allowed_statuses=["new"],
        task_keys=["K-1", "K-3"],
    )
    result = apply_scope(sprint, scope)
    assert {i.id for i in result.items} == {"1", "3"}


def test_apply_scope_task_keys_match_by_id_or_key_case_insensitive() -> None:
    sprint = _sprint(_item_status("99", "Done"))
    scope = ScopeConfig(mode="all", task_keys=["k-99"])
    result = apply_scope(sprint, scope)
    assert len(result.items) == 1


# ---------------------------------------------------------------------------
# build_scope — new args
# ---------------------------------------------------------------------------


def test_build_scope_default_statuses_seeded() -> None:
    scope = build_scope(mode="all")
    assert "new" in scope.allowed_statuses
    assert "active" in scope.allowed_statuses
    assert "in progress" in scope.allowed_statuses


def test_build_scope_custom_statuses_replace_defaults() -> None:
    scope = build_scope(mode="all", allowed_statuses=["ready"])
    assert scope.allowed_statuses == ["ready"]


def test_build_scope_task_keys_trimmed_and_stored() -> None:
    scope = build_scope(mode="all", task_keys=["  PROJ-1 ", "", "PROJ-2"])
    assert scope.task_keys == ["PROJ-1", "PROJ-2"]
