"""Registry for multi-agent providers and their capabilities."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CapabilityCost = Literal["mass", "research", "deep"]


class AgentCapability(BaseModel):
    """One executable capability exposed by an agent provider."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    description: str
    cost_profile: CapabilityCost = "research"
    parallel_safe: bool = True
    requires_clean_worktree: bool = False


class AgentProvider(BaseModel):
    """A concrete agent runtime SendSprint can route work to."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    name: str
    runtime: str
    capabilities: list[AgentCapability] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    def supports(self, capability_key: str) -> bool:
        return any(item.key == capability_key for item in self.capabilities)

    def capability(self, capability_key: str) -> AgentCapability:
        for item in self.capabilities:
            if item.key == capability_key:
                return item
        raise KeyError(capability_key)


class AgentRegistry(BaseModel):
    """Policy-free registry used by planners/schedulers/control-plane."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    providers: list[AgentProvider] = Field(default_factory=list)

    def register(self, provider: AgentProvider) -> AgentRegistry:
        if any(item.key == provider.key for item in self.providers):
            raise ValueError(f"provider already registered: {provider.key}")
        return self.model_copy(update={"providers": [*self.providers, provider]})

    def resolve(self, provider_key: str) -> AgentProvider:
        for provider in self.providers:
            if provider.key == provider_key:
                return provider
        raise KeyError(provider_key)

    def providers_for(self, capability_key: str) -> list[AgentProvider]:
        return [provider for provider in self.providers if provider.supports(capability_key)]

    def preferred_provider_for(self, capability_key: str) -> AgentProvider | None:
        providers = self.providers_for(capability_key)
        if not providers:
            return None
        # Prefer cheaper/mechanical providers when capability coverage is equivalent.
        providers = sorted(
            providers,
            key=lambda provider: _cost_rank(provider.capability(capability_key).cost_profile),
        )
        return providers[0]


def default_agent_registry() -> AgentRegistry:
    """Return the built-in provider catalog for the control plane."""
    shared_parallel = [
        AgentCapability(
            key="plan",
            description="Break an issue into scoped implementation steps.",
            cost_profile="research",
        ),
        AgentCapability(
            key="implement",
            description="Edit code and complete the scoped task.",
            cost_profile="research",
            requires_clean_worktree=True,
        ),
        AgentCapability(
            key="test",
            description="Run targeted or regression validation.",
            cost_profile="mass",
            requires_clean_worktree=True,
        ),
        AgentCapability(
            key="review",
            description="Review diffs, risks, and regressions.",
            cost_profile="deep",
        ),
    ]
    providers = [
        AgentProvider(
            key="codex",
            name="Codex",
            runtime="goal",
            capabilities=[
                *shared_parallel,
                AgentCapability(
                    key="map-project",
                    description="Map repository structure and reusable project skills.",
                    cost_profile="research",
                ),
            ],
            notes=["Preferred for validated code delivery loops."],
        ),
        AgentProvider(
            key="claude-code",
            name="Claude Code",
            runtime="ralph-loop",
            capabilities=[
                *shared_parallel,
                AgentCapability(
                    key="browser-e2e",
                    description="Drive web flows and capture evidence.",
                    cost_profile="research",
                    requires_clean_worktree=True,
                ),
            ],
            notes=["Preferred for long autonomous loops and browser validation."],
        ),
        AgentProvider(
            key="hermes",
            name="Hermes Agent",
            runtime="autopilot",
            capabilities=[
                AgentCapability(
                    key="implement",
                    description="Fast implementation pass for bounded code tasks.",
                    cost_profile="mass",
                    requires_clean_worktree=True,
                ),
                AgentCapability(
                    key="test",
                    description="Fast focused regression pass.",
                    cost_profile="mass",
                    requires_clean_worktree=True,
                ),
            ],
            notes=["Fast-path provider for high-throughput implementation."],
        ),
        AgentProvider(
            key="openclaw",
            name="OpenClaw",
            runtime="autopilot",
            capabilities=[
                AgentCapability(
                    key="review",
                    description="Independent review or adversarial sanity check.",
                    cost_profile="deep",
                ),
                AgentCapability(
                    key="security-review",
                    description="Security-oriented validation pass.",
                    cost_profile="deep",
                ),
            ],
            notes=["Useful as an independent reviewer."],
        ),
    ]
    return AgentRegistry(providers=providers)


def _cost_rank(value: CapabilityCost) -> int:
    return {"mass": 0, "research": 1, "deep": 2}[value]
