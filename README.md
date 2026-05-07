# SendSprint

Multi-agent skill that automates sprint delivery. Reads Jira / Azure DevOps boards, verifies project architecture mapping, plans work, and drives implementation across Claude, Codex, Hermes Agent, Openclaw, and GitHub Copilot.

> **Status:** v0.1.0 — Step 1 (sprint reading) and Step 2 (architecture mapping check) implemented. Steps 3–N (planning, code generation, PR, deploy) on roadmap.

---

## What it does

Given a sprint ID (Jira) or iteration path (Azure DevOps), SendSprint:

1. **Reads the entire sprint** — Stories, Tasks, Subtasks, Issues, Features, Bugs, Epics, links, attachments, comments, status, assignees, story points, acceptance criteria.
2. **Verifies architecture mapping** of every referenced project (presence of `ARCHITECTURE.md`, `docs/architecture/*`, `C4`, ADRs, dependency graph, deploy topology).
3. Hands an enriched, structured plan to the active agent (Claude / Codex / Hermes / Openclaw / Copilot) for execution.

Reading layer supports three transports, in order of preference:

| Transport      | When                                                        |
| -------------- | ----------------------------------------------------------- |
| **MCP**        | If Atlassian / Azure DevOps MCP server is connected         |
| **REST API**   | If `JIRA_API_TOKEN` / `AZURE_DEVOPS_PAT` env vars are set   |
| **Playwright** | Fallback. Drives an already-open browser tab with a session |

---

## Requirements

- Python `>=3.11`
- Playwright (`playwright install chromium`)
- One LLM provider: Anthropic (Claude), OpenAI (Codex / GPT), Google (Gemini), Groq, or local (Ollama)
- Optional: Atlassian / Azure DevOps MCP server, or Jira API token / Azure DevOps PAT

---

## Install

```bash
git clone https://github.com/wesleysimplicio/SendSprint.git
cd SendSprint
pip install -e .
playwright install chromium
cp .env.example .env  # fill in credentials
```

---

## Quick start

### Read a Jira sprint

```python
from sendsprint.operators.jira_operator import JiraOperator

op = JiraOperator(
    base_url="https://your-org.atlassian.net",
    transport="auto",  # mcp | api | playwright | auto
)
sprint = op.read_sprint(sprint_id=42)
print(f"{sprint.name}: {len(sprint.items)} items")
for item in sprint.items:
    print(f"  [{item.type}] {item.key} — {item.title} ({item.status})")
```

### Read an Azure DevOps iteration

```python
from sendsprint.operators.azure_devops_operator import AzureDevopsOperator

op = AzureDevopsOperator(
    organization="your-org",
    project="YourProject",
    transport="auto",
)
sprint = op.read_sprint(iteration_path="YourProject\\Sprint 42")
```

### Full flow (read + architecture check)

```bash
sendsprint run --provider jira --sprint 42 --repos ./repos/*
```

### CLI

```
sendsprint read   --provider {jira|azuredevops} --sprint <id|path>
sendsprint check  --repos <glob>
sendsprint run    --provider <p> --sprint <id> --repos <glob>
```

---

## Architecture

```
sendsprint/
├── operators/         JiraOperator, AzureDevopsOperator (mcp|api|playwright)
├── llm/               Provider-agnostic LLM client
├── architecture/      ArchitectureMapper — verifies project docs
├── models/            Sprint, SprintItem, ArchitectureReport (pydantic)
├── flow/              SprintFlow — orchestrates Step 1 → 2 → N
└── cli.py             Typer CLI
```

---

## Skills

Per-platform entry points live under `skills/`:

- `skills/claude/SKILL.md` — Claude Code skill manifest
- `skills/codex/AGENTS.md` — Codex / OpenAI agent contract
- `skills/hermes/hermes.md` — Hermes Agent definition
- `skills/openclaw/openclaw.md` — Openclaw persona
- `skills/copilot/copilot-instructions.md` — GitHub Copilot Chat instructions

Each one references the same Python core; the skill file just teaches the host agent how to invoke it.

---

## Roadmap

- [x] Step 1 — Sprint reading (Jira + Azure DevOps, MCP / API / Playwright)
- [x] Step 2 — Architecture mapping verification
- [ ] Step 3 — Per-item plan generation via LLM
- [ ] Step 4 — Branch / commit / PR automation
- [ ] Step 5 — Test execution + green-gate before PR
- [ ] Step 6 — Deploy trigger + status callback to ticket

---

## License

MIT — see [LICENSE](./LICENSE).
