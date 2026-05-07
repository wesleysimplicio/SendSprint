---
name: sendsprint
description: SendSprint 10-step sprint delivery flow (Jira/ADO → PR). Reusable Copilot manifest — copy to .github/copilot-instructions.md if vendoring.
version: 0.2.2
platform: github-copilot
---

# SendSprint — GitHub Copilot skill

> **Active version of this lives at [/.github/copilot-instructions.md](../../.github/copilot-instructions.md)** (auto-loaded by Copilot in this repo). This file = portable copy you can drop into other repos that vendor SendSprint as a skill.

> Canonical project instructions: [/AGENTS.md](../../AGENTS.md).

---

## Trigger

Copilot Chat injects when prompt mentions:

- pt-BR: "rode o sendsprint", "executar sprint", "entregar sprint", "processar sprint do Jira", "processar sprint do ADO"
- en: "run sendsprint", "execute sprint", "deliver sprint", "process Jira sprint", "process ADO sprint", "ship sprint"
- es: "ejecutar sprint", "procesar sprint", "entregar sprint"

---

## Steps

1. **Read sprint** → `JiraOperator(sprint_id)` or `AzureDevopsOperator(iteration_path)`. Transport `auto` resolves `mcp` → `api` → `playwright`.
2. **Architecture mapping** → `ArchitectureMapper.map(repo)`. Auto-baseline if score < 0.6.
3. **Dev** → `detect_tech(repo)` + `WorktreeManager` + `DevAgent.install_and_build()`.
4. **Lint** → `LintRunner.run()` per detected stack.
5. **Tests** → `TestRunner.run_unit() + run_e2e()` with screenshot evidence to `evidence/`.
6. **Security review** → `SecurityReviewer.scan()` (flag-only per ADR-005).
7. **Fix loop** → max 3 rounds re-running dev/lint/tests/security.
8. **Commit + push** → `git add -A && git commit` then `git push -u origin <branch> --force-with-lease`.
9. **PR creation** → `PrCreator.create()` via GitHub `gh` or ADO REST.
10. **PR review + Delivered** → `PrReviewer.review_diff()` + `RunReport.to_json()`.

---

## Stack

Python ≥ 3.11 · Pydantic v2 · Typer · Rich · httpx · playwright (sync) · pyyaml.

---

## Comandos

```bash
sendsprint version
sendsprint detect-tech ./repo
sendsprint check-architecture ./repo --build
sendsprint read-jira 42
sendsprint read-ado "Team\\Sprint 12"
sendsprint run jira 42 --workspace workspace.yaml --scope mine -o report.json
sendsprint run azuredevops "Sprint 12" --repo ./repo
```

---

## Padrão de código

```python
from sendsprint.flow import SprintFlow
from sendsprint.operators import JiraOperator
from sendsprint.workspace import load_workspace
from sendsprint.scope import build_scope

ws = load_workspace("workspace.yaml")
scope = build_scope(mode="mine", user_email="dev@example.com")
result = SprintFlow(operator=JiraOperator(), workspace=ws, scope=scope).run(sprint_id=42)
print(result.to_json())
```

---

## Env

| Var | Required for |
|---|---|
| `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` | Jira API |
| `AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT` | Azure DevOps API |
| `PLAYWRIGHT_CDP_URL` | Playwright fallback (default `http://127.0.0.1:9222`) |
| `LLM_PROVIDER`, `LLM_MODEL`, provider key | LLM step (optional) |

---

## Code style (Copilot DOs/DON'Ts)

- DO: Pydantic v2, type hints, `from __future__ import annotations`, `pathlib.Path`, `subprocess.run(..., timeout=N, check=False)`, `httpx`.
- DON'T: `requests`, `os.system`, `os.path`, Pydantic v1 (`dict()`/`json()`), auto-fix security findings, reorder transport chain.

Mirror existing patterns in `sendsprint/operators/` and `sendsprint/agents/`.

---

## Definition of Done

- [ ] All 10 steps reported
- [ ] `RunReport.failed == false`
- [ ] PR URL per repo with changes
- [ ] `report.json` exported via `result.to_json()`
- [ ] Worktrees cleaned up
- [ ] Zero security findings
