"""Tests for agent provider registry and capability routing."""

from __future__ import annotations

import pytest

from sendsprint.agent_registry import AgentProvider, default_agent_registry


def test_default_registry_exposes_foundational_capabilities() -> None:
    registry = default_agent_registry()

    codex = registry.resolve("codex")
    assert codex.supports("plan")
    assert codex.supports("implement")
    assert codex.supports("map-project")

    claude = registry.resolve("claude-code")
    assert claude.supports("browser-e2e")


def test_preferred_provider_for_implement_prefers_mass_cost() -> None:
    registry = default_agent_registry()

    preferred = registry.preferred_provider_for("implement")

    assert preferred is not None
    assert preferred.key == "hermes"


def test_register_rejects_duplicate_keys() -> None:
    registry = default_agent_registry()

    with pytest.raises(ValueError):
        registry.register(
            AgentProvider(
                key="codex",
                name="Codex Duplicate",
                runtime="goal",
            )
        )
