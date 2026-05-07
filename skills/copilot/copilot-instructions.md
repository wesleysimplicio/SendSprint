# SendSprint - GitHub Copilot Instructions

Copy this file to `.github/copilot-instructions.md` at the repo root so
Copilot Chat injects it as context. Activates when the prompt mentions
sprint reading or delivery: "ler sprint", "rodar sprint", "send sprint",
"sprint flow", "executar sprint", "iniciar entrega da sprint",
"ler issues da sprint" (pt-BR/en/es).

## What SendSprint does

Two-step automated sprint delivery:

1. **Read sprint** from Jira or Azure DevOps using one of three transports
   (`mcp` -> `api` -> `playwright`). Operators:
   - `sendsprint.operators.JiraOperator` (sprint id required)
   - `sendsprint.operators.AzureDevopsOperator` (iteration path required)
   - Captures every Story, Task, Subtask, Bug, Epic, Feature, Issue with
     full metadata.

2. **Architecture mapping** via `sendsprint.architecture.ArchitectureMapper`.
   `score < 0.6` blocks delivery and surfaces missing artifacts.

## CLI

```bash
sendsprint read-jira 1234
sendsprint read-ado "Team\\Sprint 12"
sendsprint check-architecture ./path/to/repo
sendsprint run jira 1234 --repo-path ./path/to/repo
```

## Python

```python
from sendsprint.flow import SprintFlow
from sendsprint.operators import JiraOperator, AzureDevopsOperator

result = SprintFlow(operator=JiraOperator()).run(sprint_id=1234, repo_path="./repo")
```

## Env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT`,
`PLAYWRIGHT_CDP_URL` (default `http://127.0.0.1:9222`),
`LLM_PROVIDER`, `LLM_MODEL`, provider key.

## Code style

- Python >= 3.11.
- Pydantic v2 for models.
- Typer for CLI, Rich for console output.
- httpx for HTTP, Playwright sync API for CDP.
- Mirror existing patterns in `sendsprint/operators/`.
