"""SendSprint CLI v2 — workspace-aware, scoped, 9-step orchestration."""

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
from sendsprint.architecture import ArchitectureMapper, build_architecture
from sendsprint.flow import SprintFlow
from sendsprint.models import Sprint
from sendsprint.operators import AzureDevopsOperator, JiraOperator
from sendsprint.scope import build_scope
from sendsprint.tech import detect_tech
from sendsprint.workspace import load_workspace

app = typer.Typer(
    add_completion=False,
    help="SendSprint — automated sprint delivery skill (Jira / Azure DevOps).",
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
    """Step 1 — read a Jira sprint and print its items."""
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
    """Step 1 — read an Azure DevOps iteration."""
    operator = AzureDevopsOperator(
        organization=organization, project=project, pat=pat, transport=transport
    )
    sprint = operator.read_sprint(iteration_path=iteration_path)
    _render_sprint(sprint)
    if output:
        output.write_text(sprint.model_dump_json(indent=2))
        console.print(f"[green]wrote sprint to {output}[/green]")


@app.command(name="check-architecture")
def check_architecture(
    repo_path: Path = typer.Argument(..., exists=True, file_okay=False),
    build_if_missing: bool = typer.Option(False, "--build", help="Generate baseline docs if missing"),
) -> None:
    """Step 2 — inspect (and optionally build) repo architecture docs."""
    if build_if_missing:
        fp = detect_tech(repo_path)
        result = build_architecture(repo_path, fingerprint=fp)
        console.print(f"created: {result.created_files}")
        console.print(f"skipped: {result.skipped_files}")
        console.print(f"score: {result.final_score:.2f}  mapped: {result.is_mapped}")
    else:
        report = ArchitectureMapper().inspect(repo_path)
        console.print_json(data=json.loads(report.model_dump_json()))
        if not report.is_mapped:
            console.print(f"[yellow]missing: {', '.join(report.missing)}[/yellow]")
            sys.exit(1)


@app.command(name="detect-tech")
def detect_tech_cmd(
    repo_path: Path = typer.Argument(..., exists=True, file_okay=False),
) -> None:
    """Detect a repo's tech stack (fingerprint)."""
    fp = detect_tech(repo_path)
    console.print_json(data=json.loads(fp.model_dump_json()))


@app.command(name="run")
def run_flow(
    source: str = typer.Argument(..., help="jira | azuredevops"),
    identifier: str = typer.Argument(..., help="sprint id or iteration path"),
    workspace_file: Optional[Path] = typer.Option(
        None, "--workspace", "-w", help="workspace.yaml path"
    ),
    repo_path: Optional[Path] = typer.Option(None, "--repo", "-r", exists=True, file_okay=False),
    transport: str = typer.Option("auto"),
    scope_mode: str = typer.Option("all", "--scope", help="all | mine"),
    output: Optional[Path] = typer.Option(None, "-o", help="Write RunReport JSON"),
) -> None:
    """Run the full 9-step SendSprint flow."""
    ws = load_workspace(workspace_file) if workspace_file else None

    if source == "jira":
        operator = JiraOperator(transport=transport)
        user_info = operator.current_user()
        scope = build_scope(
            mode=scope_mode,
            user_email=user_info.get("emailAddress"),
            user_account_id=user_info.get("accountId"),
        )
    elif source == "azuredevops":
        operator = AzureDevopsOperator(transport=transport)
        user_info = operator.current_user()
        scope = build_scope(
            mode=scope_mode,
            user_email=user_info.get("emailAddress"),
            user_descriptor=user_info.get("descriptor"),
            user_display_name=user_info.get("displayName"),
        )
    else:
        raise typer.BadParameter("source must be 'jira' or 'azuredevops'")

    flow = SprintFlow(operator=operator, workspace=ws, scope=scope)

    sprint_id = None
    iteration_path = None
    if source == "jira":
        sprint_id = int(identifier)
    else:
        iteration_path = identifier

    result = flow.run(
        sprint_id=sprint_id,
        iteration_path=iteration_path,
        repo_path=str(repo_path) if repo_path else None,
    )

    _render_sprint(result.sprint)
    if result.architecture:
        console.rule("Architecture")
        console.print_json(data=json.loads(result.architecture.model_dump_json()))
    if result.run_report:
        console.rule("Run Report")
        _render_run_report(result.run_report)
    for note in result.notes:
        console.print(f"[yellow]note:[/yellow] {note}")
    if output:
        data = result.run_report.model_dump_json(indent=2) if result.run_report else result.model_dump_json(indent=2)
        output.write_text(data)
        console.print(f"[green]wrote report to {output}[/green]")


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


def _render_run_report(report) -> None:
    table = Table(show_header=True, header_style="bold")
    for col in ("Step", "Name", "Status", "Message"):
        table.add_column(col)
    for s in report.steps:
        style = {"ok": "green", "failed": "red", "skipped": "yellow"}.get(s.status, "")
        table.add_row(str(s.step), s.name, f"[{style}]{s.status}[/{style}]", (s.message or "")[:80])
    console.print(table)
    if report.prs:
        console.print(f"[bold]PRs:[/bold] {', '.join(p.url or str(p.number) for p in report.prs)}")
    console.print(f"[bold]Summary:[/bold] {report.summary}")


if __name__ == "__main__":
    app()
