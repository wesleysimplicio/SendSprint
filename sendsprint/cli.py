"""SendSprint CLI - typer entry point."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from sendsprint import __version__
from sendsprint.architecture import ArchitectureMapper
from sendsprint.flow import SprintFlow
from sendsprint.models import Sprint
from sendsprint.operators import AzureDevopsOperator, JiraOperator

app = typer.Typer(
    add_completion=False,
    help="SendSprint - automated sprint delivery skill (Jira / Azure DevOps).",
)
console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


@app.command()
def version() -> None:
    """Print the installed SendSprint version."""
    console.print(f"sendsprint {__version__}")


@app.command(name="read-jira")
def read_jira(
    sprint_id: int = typer.Argument(..., help="Jira sprint id"),
    transport: str = typer.Option("auto", help="auto | mcp | api | playwright"),
    base_url: Optional[str] = typer.Option(None, envvar="JIRA_BASE_URL"),
    email: Optional[str] = typer.Option(None, envvar="JIRA_EMAIL"),
    api_token: Optional[str] = typer.Option(None, envvar="JIRA_API_TOKEN"),
    output: Optional[Path] = typer.Option(None, help="Write Sprint JSON to this path"),
) -> None:
    """Step 1 - read a Jira sprint and print its items."""
    operator = JiraOperator(
        base_url=base_url, email=email, api_token=api_token, transport=transport
    )
    sprint = operator.read_sprint(sprint_id=sprint_id)
    _render_sprint(sprint)
    if output:
        output.write_text(sprint.model_dump_json(indent=2))
        console.print(f"[green]wrote sprint to {output}[/green]")


@app.command(name="read-ado")
def read_ado(
    iteration_path: str = typer.Argument(..., help="e.g. MyTeam\\Sprint 12"),
    transport: str = typer.Option("auto", help="auto | mcp | api | playwright"),
    organization: Optional[str] = typer.Option(None, envvar="AZURE_DEVOPS_ORG"),
    project: Optional[str] = typer.Option(None, envvar="AZURE_DEVOPS_PROJECT"),
    pat: Optional[str] = typer.Option(None, envvar="AZURE_DEVOPS_PAT"),
    output: Optional[Path] = typer.Option(None),
) -> None:
    """Step 1 - read an Azure DevOps iteration."""
    operator = AzureDevopsOperator(
        organization=organization, project=project, pat=pat, transport=transport
    )
    sprint = operator.read_sprint(iteration_path=iteration_path)
    _render_sprint(sprint)
    if output:
        output.write_text(sprint.model_dump_json(indent=2))
        console.print(f"[green]wrote sprint to {output}[/green]")


@app.command(name="check-architecture")
def check_architecture(repo_path: Path = typer.Argument(..., exists=True, file_okay=False)) -> None:
    """Step 2 - inspect a repo for architecture documentation."""
    report = ArchitectureMapper().inspect(repo_path)
    console.print_json(data=json.loads(report.model_dump_json()))
    if not report.is_mapped:
        console.print(f"[yellow]missing: {', '.join(report.missing)}[/yellow]")
        sys.exit(1)


@app.command(name="run")
def run_flow(
    source: str = typer.Argument(..., help="jira | azuredevops"),
    identifier: str = typer.Argument(..., help="sprint id (Jira) or iteration path (Azure DevOps)"),
    repo_path: Optional[Path] = typer.Option(None, exists=True, file_okay=False),
    transport: str = typer.Option("auto"),
    output: Optional[Path] = typer.Option(None),
) -> None:
    """Run the full SendSprint flow (Step 1 + Step 2)."""
    if source == "jira":
        operator = JiraOperator(transport=transport)
        result = SprintFlow(operator=operator).run(
            sprint_id=int(identifier), repo_path=str(repo_path) if repo_path else None
        )
    elif source == "azuredevops":
        operator = AzureDevopsOperator(transport=transport)
        result = SprintFlow(operator=operator).run(
            iteration_path=identifier, repo_path=str(repo_path) if repo_path else None
        )
    else:
        raise typer.BadParameter("source must be 'jira' or 'azuredevops'")
    _render_sprint(result.sprint)
    if result.architecture:
        console.rule("Architecture")
        console.print_json(data=json.loads(result.architecture.model_dump_json()))
    for note in result.notes:
        console.print(f"[yellow]note:[/yellow] {note}")
    if output:
        output.write_text(result.model_dump_json(indent=2))
        console.print(f"[green]wrote flow result to {output}[/green]")


def _render_sprint(sprint: Sprint) -> None:
    console.rule(f"Sprint {sprint.id}: {sprint.name} ({sprint.transport})")
    table = Table(show_header=True, header_style="bold")
    for col in ("Key", "Type", "Title", "Status", "Assignee", "SP"):
        table.add_column(col)
    for item in sprint.items:
        table.add_row(
            item.key,
            item.type,
            (item.title or "")[:60],
            item.status,
            item.assignee or "-",
            str(item.story_points) if item.story_points is not None else "-",
        )
    console.print(table)
    console.print(
        f"[bold]totals[/bold] stories={len(sprint.stories)} tasks={len(sprint.tasks)} "
        f"subtasks={len(sprint.subtasks)} bugs={len(sprint.bugs)} "
        f"epics={len(sprint.epics)} features={len(sprint.features)} issues={len(sprint.issues)}"
    )


if __name__ == "__main__":
    app()
