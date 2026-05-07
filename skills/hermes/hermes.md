# SendSprint v0.2 - Hermes Agent

Skill manifest consumed by Hermes Agent (https://github.com/hermes-agent).

## Trigger

- pt-BR: "ler sprint", "rodar sprint", "executar sprint", "iniciar entrega da sprint"
- en: "send sprint", "sprint flow", "deliver sprint", "read sprint"
- es: "ejecutar sprint", "leer sprint"

## 10-Step Flow

| Step | Name | Agent/Module |
|------|------|-------------|
| 1 | Read sprint | `JiraOperator` / `AzureDevopsOperator` |
| 2 | Architecture mapping | `ArchitectureMapper` + `build_architecture()` |
| 3 | Dev (install + build) | `DevAgent` with worktree isolation |
| 4 | Lint | `LintRunner` (eslint, ruff, clippy, etc.) |
| 5 | Tests (unit + E2E) | `TestRunner` with screenshot evidence |
| 6 | Security review | `SecurityReviewer` (flag-only) |
| 7 | Fix loop | Re-build + re-lint + re-test + re-scan (max 3) |
| 8 | Commit | `git add -A && git commit` on worktree branch |
| 9 | Create PR | `PrCreator` (GitHub / Azure DevOps) |
| 10 | PR review + Delivered | `PrReviewer` + RunReport with `to_json()` |

Transport priority: `mcp` -> `api` -> `playwright`.
Supports `--scope mine` to filter only current user's items.
Supports `--workspace workspace.yaml` for multi-repo workspaces.

## CLI

```bash
sendsprint run jira 1234 --workspace workspace.yaml --scope mine
sendsprint run azuredevops "Team\\Sprint 12" --repo ./repo
sendsprint detect-tech ./repo
sendsprint check-architecture ./repo --build
```

## Python

```python
from sendsprint.flow import SprintFlow
from sendsprint.operators import JiraOperator

result = SprintFlow(operator=JiraOperator()).run(sprint_id=1234)
```

## Env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT`,
`PLAYWRIGHT_CDP_URL`,
`LLM_PROVIDER`, `LLM_MODEL`, provider key (`ANTHROPIC_API_KEY` etc).
