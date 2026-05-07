"""SendSprint - basic usage examples for Jira and Azure DevOps."""

from __future__ import annotations

from sendsprint.flow import SprintFlow
from sendsprint.operators import AzureDevopsOperator, JiraOperator

JIRA_SPRINT_ID = 1234
ADO_ITERATION_PATH = r"Team\Sprint 12"
REPO_PATH = "./repo"


def read_jira_sprint() -> None:
    """Step 1 only - read every item from a Jira sprint."""
    operator = JiraOperator(transport="auto")
    sprint = operator.read_sprint(sprint_id=JIRA_SPRINT_ID)
    print(f"[jira] sprint={sprint.name} transport={sprint.transport} items={len(sprint.items)}")
    for item in sprint.items:
        print(f"  - {item.type}/{item.key}: {item.title} ({item.status})")


def read_ado_iteration() -> None:
    """Step 1 only - read every work item from an Azure DevOps iteration."""
    operator = AzureDevopsOperator(transport="auto")
    sprint = operator.read_sprint(iteration_path=ADO_ITERATION_PATH)
    print(f"[ado] sprint={sprint.name} transport={sprint.transport} items={len(sprint.items)}")
    for item in sprint.items:
        print(f"  - {item.type}/{item.key}: {item.title} ({item.status})")


def run_full_flow_jira() -> None:
    """Step 1 + Step 2 - read Jira sprint and verify repo architecture mapping."""
    flow = SprintFlow(operator=JiraOperator(transport="auto"))
    result = flow.run(sprint_id=JIRA_SPRINT_ID, repo_path=REPO_PATH)
    arch = result.architecture
    print(f"[flow] sprint={result.sprint.name} items={len(result.sprint.items)}")
    if arch is not None:
        print(f"[arch] score={arch.score} mapped={arch.is_mapped} missing={arch.missing}")


def run_full_flow_ado() -> None:
    """Step 1 + Step 2 - read Azure DevOps iteration and verify repo architecture mapping."""
    flow = SprintFlow(operator=AzureDevopsOperator(transport="auto"))
    result = flow.run(iteration_path=ADO_ITERATION_PATH, repo_path=REPO_PATH)
    arch = result.architecture
    print(f"[flow] sprint={result.sprint.name} items={len(result.sprint.items)}")
    if arch is not None:
        print(f"[arch] score={arch.score} mapped={arch.is_mapped} missing={arch.missing}")


if __name__ == "__main__":
    read_jira_sprint()
    read_ado_iteration()
    run_full_flow_jira()
    run_full_flow_ado()
