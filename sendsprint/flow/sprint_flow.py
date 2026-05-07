"""SprintFlow - composes operators + architecture mapper into the end-to-end flow."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from sendsprint.architecture import ArchitectureMapper
from sendsprint.llm import LlmClient
from sendsprint.models import ArchitectureReport, Sprint
from sendsprint.operators.base import BaseOperator

logger = logging.getLogger(__name__)


class SprintFlowResult(BaseModel):
    sprint: Sprint
    architecture: ArchitectureReport | None = None
    repo_path: str | None = None
    notes: list[str] = Field(default_factory=list)


class SprintFlow:
    """Step 1 - read the sprint via the operator. Step 2 - inspect repo architecture."""

    def __init__(
        self,
        operator: BaseOperator,
        mapper: ArchitectureMapper | None = None,
        llm: LlmClient | None = None,
    ) -> None:
        self.operator = operator
        self.mapper = mapper or ArchitectureMapper()
        self.llm = llm

    def run(
        self,
        sprint_id: str | int | None = None,
        iteration_path: str | None = None,
        repo_path: str | None = None,
        **kwargs: Any,
    ) -> SprintFlowResult:
        identifier = sprint_id if sprint_id is not None else iteration_path
        if identifier is None:
            raise ValueError("provide sprint_id (Jira) or iteration_path (Azure DevOps)")
        read_kwargs = (
            {"sprint_id": identifier} if sprint_id is not None else {"iteration_path": identifier}
        )
        sprint = self.operator.read_sprint(**read_kwargs, **kwargs)
        logger.info(
            "[%s] step 1 complete: %d items read", self.operator.source, len(sprint.items)
        )
        architecture = None
        notes: list[str] = []
        if repo_path:
            architecture = self.mapper.inspect(repo_path)
            logger.info(
                "[%s] step 2 complete: architecture score %.2f",
                self.operator.source,
                architecture.score,
            )
            if not architecture.is_mapped:
                notes.append(
                    f"architecture mapping incomplete - missing: {', '.join(architecture.missing)}"
                )
        else:
            notes.append("repo_path not provided - skipped Step 2 architecture check")
        return SprintFlowResult(
            sprint=sprint,
            architecture=architecture,
            repo_path=repo_path,
            notes=notes,
        )
