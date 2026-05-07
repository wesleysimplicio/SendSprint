# SendSprint v0.2 - Codex Agent

Auto-loaded by Codex CLI when present in repo. Activates on prompts mentioning
"sprint flow", "ler sprint", "rodar sprint", "send sprint", "executar sprint",
"iniciar entrega da sprint", "ler issues da sprint" or English/Spanish equivalents.

## Mission

End-to-end sprint delivery in 9 steps.

### Step 1 — Read sprint
Pick the operator: `JiraOperator(sprint_id)` or `AzureDevopsOperator(iteration_path)`.
Transport: `mcp` -> `api` -> `playwright`. Supports `--scope mine`.

### Step 2 — Architecture mapping
`ArchitectureMapper.inspect()` + `build_architecture()` if score < 0.6.

### Step 3 — Dev (install + build)
`DevAgent` per repo with tech detection and worktree isolation.

### Step 4 — Tests
`TestRunner.run_all()` — unit + Playwright E2E with screenshot evidence.

### Step 5 — Security review
`SecurityReviewer.scan()` — flag-only (secrets, env, npm audit).

### Step 6 — Fix loop
Re-build + re-test up to 3 rounds on failure.

### Step 7 — Create PR
`PrCreator` via GitHub (gh CLI) or Azure DevOps REST.

### Step 8 — PR review
`PrReviewer` diff analysis (TODO, debug, long lines).

### Step 9 — Delivered

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
from sendsprint.operators import JiraOperator

result = SprintFlow(operator=JiraOperator()).run(sprint_id=1234)
```

## Env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT`,
`PLAYWRIGHT_CDP_URL` (default `http://127.0.0.1:9222`),
`LLM_PROVIDER`, `LLM_MODEL`, plus the matching provider key.
