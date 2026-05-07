# SendSprint v0.2 - GitHub Copilot Instructions

Copy this file to `.github/copilot-instructions.md` at the repo root so
Copilot Chat injects it as context. Activates when the prompt mentions
sprint reading or delivery: "ler sprint", "rodar sprint", "send sprint",
"sprint flow", "executar sprint" (pt-BR/en/es).

## What SendSprint does

Full 9-step automated sprint delivery:

1. **Read sprint** from Jira or Azure DevOps (mcp->api->playwright).
   Supports `--scope mine` for current-user filtering.
2. **Architecture mapping** — inspect + auto-generate baseline docs if score < 0.6.
3. **Dev** — tech detection, worktree isolation, install + build.
4. **Tests** — unit + Playwright E2E with screenshot evidence.
5. **Security review** — flag-only scan (secrets, env, npm audit).
6. **Fix loop** — re-build + re-test up to 3 rounds on failure.
7. **Create PR** — GitHub (gh CLI) or Azure DevOps REST.
8. **PR review** — diff analysis (TODO, debug statements, long lines).
9. **Delivered** — RunReport with all evidence.

## CLI

```bash
sendsprint run jira 1234 --workspace workspace.yaml --scope mine -o report.json
sendsprint run azuredevops "Team\\Sprint 12" --repo ./repo
sendsprint detect-tech ./repo
sendsprint check-architecture ./repo --build
```

## Python

```python
from sendsprint.flow import SprintFlow
from sendsprint.operators import JiraOperator, AzureDevopsOperator
from sendsprint.workspace import load_workspace
from sendsprint.scope import build_scope

ws = load_workspace("workspace.yaml")
scope = build_scope(mode="mine", user_email="dev@example.com")
result = SprintFlow(operator=JiraOperator(), workspace=ws, scope=scope).run(sprint_id=1234)
```

## Env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT`,
`PLAYWRIGHT_CDP_URL` (default `http://127.0.0.1:9222`),
`LLM_PROVIDER`, `LLM_MODEL`, provider key.

## Code style

- Python >= 3.11. Pydantic v2 for models.
- Typer for CLI, Rich for console output.
- httpx for HTTP, Playwright sync API for CDP.
- Mirror existing patterns in `sendsprint/operators/` and `sendsprint/agents/`.
