# SendSprint v0.2 - Openclaw Skill

Skill manifest for the Openclaw agent runtime.

## Trigger

- pt-BR: "ler sprint", "rodar sprint", "executar sprint", "iniciar entrega da sprint"
- en: "send sprint", "sprint flow", "deliver sprint", "read sprint"
- es: "ejecutar sprint", "leer sprint"

## 10-Step Flow

1. **Read sprint** — `JiraOperator` or `AzureDevopsOperator` (mcp->api->playwright).
   Supports `--scope mine` for current-user filtering.
2. **Architecture mapping** — inspect + auto-build baseline docs if score < 0.6.
3. **Dev** — `DevAgent` with tech detection, worktree isolation, install + build.
4. **Lint** — `LintRunner` static analysis per tech (eslint, ruff, clippy, etc.).
5. **Tests** — `TestRunner` unit + Playwright E2E, screenshot evidence (pass + fail).
6. **Security review** — `SecurityReviewer` flag-only (secrets, env, npm audit).
7. **Fix loop** — re-build + re-lint + re-test + re-scan up to 3 rounds. Reports trigger.
8. **Commit** — `git add -A && git commit` on worktree branch. Skips if no changes.
9. **Create PR** — `PrCreator` GitHub (gh CLI) or Azure DevOps REST.
10. **PR review + Delivered** — `PrReviewer` diff analysis. RunReport with `to_json()`.

## CLI

```bash
sendsprint run jira 1234 --workspace workspace.yaml --scope mine -o report.json
sendsprint run azuredevops "Team\\Sprint 12" --repo ./repo
sendsprint detect-tech ./repo
sendsprint check-architecture ./repo --build
```

## Required env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT`,
`PLAYWRIGHT_CDP_URL` (default `http://127.0.0.1:9222`),
`LLM_PROVIDER`, `LLM_MODEL`, provider key.
