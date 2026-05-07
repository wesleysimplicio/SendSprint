---
name: sendsprint
description: Multi-agent skill that automates sprint delivery. Reads a sprint from Jira or Azure DevOps (MCP / REST API / Playwright), then verifies architecture mapping in the target repo.
command: sendsprint
---

# SendSprint - Claude Skill

Trigger automatically whenever the user asks to "ler sprint", "rodar sprint", "send sprint",
"sprint flow", "executar sprint", "iniciar entrega da sprint", "ler issues da sprint",
or any equivalent in English / pt-BR / es-ES.

## Step 1 - Read sprint

Pick the operator from the source the user names:

- **Jira** -> `JiraOperator` (sprint id required).
- **Azure DevOps** -> `AzureDevopsOperator` (iteration path required, e.g. `Team\Sprint 12`).

Transport priority: `mcp` -> `api` -> `playwright`. Use `auto` unless the user pins one.
For Playwright, the user must have Chrome running with `--remote-debugging-port=9222`
(or set `PLAYWRIGHT_CDP_URL`).

Extract every Story, Task, Subtask, Bug, Epic, Feature, and Issue with: key, type, title,
description, status, assignee, story points, parent key, labels, comments, links,
attachments, acceptance criteria, source URL.

## Step 2 - Architecture mapping

Run `ArchitectureMapper.inspect(repo_path)` on each repository touched by the sprint and
fail loudly when the score is below `0.6`. Surface the missing artifacts list:
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
from sendsprint.operators import JiraOperator
from sendsprint.flow import SprintFlow

sprint = SprintFlow(operator=JiraOperator()).run(sprint_id=1234, repo_path="./repo")
```

## Required env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` (Jira API)
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT` (Azure DevOps API)
`PLAYWRIGHT_CDP_URL` (Playwright fallback, default `http://127.0.0.1:9222`)
`LLM_PROVIDER`, `LLM_MODEL`, plus the matching provider key (LLM step, optional).
