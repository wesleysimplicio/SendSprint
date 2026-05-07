# SendSprint - Hermes Agent

Skill manifest consumed by Hermes Agent (https://github.com/hermes-agent).

## Trigger

Activate when the prompt matches:
- pt-BR: "ler sprint", "rodar sprint", "executar sprint", "iniciar entrega da sprint", "ler issues da sprint"
- en: "send sprint", "sprint flow", "deliver sprint", "read sprint"
- es: "ejecutar sprint", "leer sprint"

## Two-step flow

### Step 1 - Read sprint

Build the right operator:

| Source | Class | Required arg |
|--------|-------|--------------|
| Jira | `sendsprint.operators.JiraOperator` | `sprint_id: int` |
| Azure DevOps | `sendsprint.operators.AzureDevopsOperator` | `iteration_path: str` |

Transport priority: `mcp` -> `api` -> `playwright`. Use `transport="auto"`
unless the user pins one. Playwright requires Chrome running with
`--remote-debugging-port=9222` (or `PLAYWRIGHT_CDP_URL`).

Extract for every Story, Task, Subtask, Bug, Epic, Feature, Issue:
key, type, title, description, status, assignee, story points, parent key,
labels, comments, links, attachments, acceptance criteria, source URL.

### Step 2 - Architecture mapping

Call `ArchitectureMapper().inspect(repo_path)` per repo. Score below `0.6`
fails the gate; surface the missing artifacts list.

## CLI shortcuts

```bash
sendsprint read-jira 1234
sendsprint read-ado "Team\\Sprint 12"
sendsprint check-architecture ./path/to/repo
sendsprint run jira 1234 --repo-path ./path/to/repo
```

## Python entry point

```python
from sendsprint.flow import SprintFlow
from sendsprint.operators import JiraOperator

result = SprintFlow(operator=JiraOperator()).run(sprint_id=1234, repo_path="./repo")
```

## Env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT`,
`PLAYWRIGHT_CDP_URL`,
`LLM_PROVIDER`, `LLM_MODEL`, provider key (`ANTHROPIC_API_KEY` etc).
