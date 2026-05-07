# SendSprint - Codex Agent

Auto-loaded by Codex CLI when present in repo. Activates on prompts mentioning
"sprint flow", "ler sprint", "rodar sprint", "send sprint", "executar sprint",
"iniciar entrega da sprint", "ler issues da sprint" or English/Spanish equivalents.

## Mission

End-to-end sprint delivery in two steps.

### Step 1 - Read sprint

Pick the operator from the source the user names:

- **Jira** -> `JiraOperator(transport="auto")`. Required: sprint id.
- **Azure DevOps** -> `AzureDevopsOperator(transport="auto")`. Required: iteration path
  (e.g. `MyTeam\Sprint 12`).

Transport priority: `mcp` -> `api` -> `playwright`. Use `auto` unless overridden.

Extract for every Story, Task, Subtask, Bug, Epic, Feature and Issue:
key, type, title, description, status, assignee, story points, parent key,
labels, comments, links, attachments, acceptance criteria, source URL.

### Step 2 - Architecture mapping

Run `ArchitectureMapper().inspect(repo_path)` for every repo touched by the sprint.
Fail with a clear message when `score < 0.6` and list the missing artifacts:
`ARCHITECTURE.md`, `docs/architecture/`, `docs/c4/`, `docs/adr/`, dependency graph,
deploy topology, README.

## CLI

```bash
sendsprint read-jira 1234
sendsprint read-ado "Team\\Sprint 12"
sendsprint check-architecture ./path/to/repo
sendsprint run jira 1234 --repo-path ./path/to/repo
```

## Python

```python
from sendsprint.operators import AzureDevopsOperator, JiraOperator
from sendsprint.flow import SprintFlow

result = SprintFlow(operator=JiraOperator()).run(
    sprint_id=1234, repo_path="./repo"
)
```

## Env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT`,
`PLAYWRIGHT_CDP_URL` (default `http://127.0.0.1:9222`),
`LLM_PROVIDER`, `LLM_MODEL`, plus the matching provider key.

## Playwright fallback

User must have Chrome running with `--remote-debugging-port=9222` (or set
`PLAYWRIGHT_CDP_URL`). The operator connects via CDP, navigates the project,
opens each issue, and scrapes title + status + assignee.
