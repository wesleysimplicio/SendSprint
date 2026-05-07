---
name: sendsprint
description: "Multi-agent skill that automates sprint delivery end-to-end: read sprint, map architecture, dev, test, security scan, fix loop, PR creation, PR review, deliver."
command: sendsprint
---

# SendSprint v0.2 - Claude Skill

Trigger automatically whenever the user asks to "ler sprint", "rodar sprint", "send sprint",
"sprint flow", "executar sprint", "iniciar entrega da sprint", "ler issues da sprint",
or any equivalent in English / pt-BR / es-ES.

## 9-Step Flow

### Step 1 — Read sprint
Pick the operator from the source the user names:
- **Jira** -> `JiraOperator` (sprint id required).
- **Azure DevOps** -> `AzureDevopsOperator` (iteration path required).

Transport priority: `mcp` -> `api` -> `playwright`. Use `auto` unless the user pins one.
Supports `--scope mine` to filter only the current user's assigned items.

### Step 2 — Architecture mapping
Run `ArchitectureMapper.inspect(repo_path)`. If score < 0.6, auto-generate baseline
docs (ARCHITECTURE.md, README.md, docs/architecture/, docs/adr/, docs/dependencies.md,
docs/deploy.md) via `build_architecture()`, then re-inspect.

### Step 3 — Dev (install + build)
Per repo, detect tech stack via `detect_tech()`, create a git worktree for isolation,
run install + build via `DevAgent`.

### Step 4 — Tests (unit + E2E)
Run unit tests and Playwright E2E via `TestRunner`. Screenshot evidence captured
for both pass and fail states in `sendsprint-evidence/`.

### Step 5 — Security review (flag only)
`SecurityReviewer` scans for hardcoded secrets, env files not gitignored,
npm audit vulnerabilities. Flags only — never auto-fixes.

### Step 6 — Fix loop
If tests or security fail, re-build + re-test up to 3 times.

### Step 7 — Create PR
`PrCreator` creates PR on GitHub (gh CLI) or Azure DevOps (REST API).

### Step 8 — PR review
`PrReviewer` analyzes the diff for TODO markers, debug statements, long lines.

### Step 9 — Delivered
PR delivered. RunReport with all steps, evidence, and findings.

## CLI

```bash
sendsprint version
sendsprint read-jira 1234
sendsprint read-ado "Team\\Sprint 12"
sendsprint check-architecture ./repo --build
sendsprint detect-tech ./repo
sendsprint run jira 1234 --workspace workspace.yaml --scope mine -o report.json
sendsprint run azuredevops "Team\\Sprint 12" --repo ./repo
```

## Python

```python
from sendsprint.flow import SprintFlow
from sendsprint.operators import JiraOperator
from sendsprint.workspace import load_workspace
from sendsprint.scope import build_scope

ws = load_workspace("workspace.yaml")
scope = build_scope(mode="mine", user_email="dev@example.com")
flow = SprintFlow(operator=JiraOperator(), workspace=ws, scope=scope)
result = flow.run(sprint_id=1234)
print(result.run_report.summary)
```

## Required env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` (Jira API)
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT` (Azure DevOps API)
`PLAYWRIGHT_CDP_URL` (Playwright fallback, default `http://127.0.0.1:9222`)
`LLM_PROVIDER`, `LLM_MODEL`, plus the matching provider key (LLM step, optional).
