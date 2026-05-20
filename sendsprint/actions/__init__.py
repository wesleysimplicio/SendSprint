"""Generic action lifecycle and domain adapter contracts."""

from sendsprint.actions.adapter import DomainAdapter
from sendsprint.actions.lifecycle import (
    Action,
    ActionPhase,
    ActionStatus,
    ApprovalPolicy,
    DomainDescriptor,
    ExecutionStep,
    LearningRecord,
    Objective,
    ValidationResult,
)
from sendsprint.actions.marketing_adapter import (
    MARKETING_DOMAIN,
    MARKETING_TEMPLATES,
    MarketingActionTemplate,
    MarketingDomainAdapter,
)

__all__ = [
    "Action",
    "ActionPhase",
    "ActionStatus",
    "ApprovalPolicy",
    "DomainAdapter",
    "DomainDescriptor",
    "ExecutionStep",
    "LearningRecord",
    "MARKETING_DOMAIN",
    "MARKETING_TEMPLATES",
    "MarketingActionTemplate",
    "MarketingDomainAdapter",
    "Objective",
    "ValidationResult",
]
