---
trigger: always_on
description: SendSprint — one-command sprint delivery (Jira / Azure DevOps → 10-step flow → PR).
---

# SendSprint — Windsurf rule

Activate when the user types any of:

- pt-BR: "rode o sendsprint", "executar sprint", "Faça todas as minhas tarefas da sprint", "entregar sprint"
- en: "run sendsprint", "ship my sprint", "deliver my sprint", "process my Jira sprint"
- es: "ejecutar sprint", "procesar sprint"
- slash: `/sendsprint`

Run exactly:

```bash
sendsprint sprint
```

That single command:

1. Loads cached profile from `~/.config/sendsprint/profile.yaml`.
2. Resolves credentials from OS keyring (prompts only the first time, then persists).
3. Defaults to `--scope mine`.
4. Runs the 10-step flow: read sprint → architecture map → dev (worktree+install+build) → lint → tests → security (flag-only) → fix loop → commit+push → PR creation → PR review.

## First-run onboarding

If the project lacks `.specs/`, run **first**:

```bash
sendsprint init        # auto-discovers stack and LLM-fills .specs/
```

If credentials missing:

```bash
sendsprint login jira          # or: sendsprint login azuredevops
```

## Rules for the agent

- Do **not** re-implement the 10 steps. Always defer to `sendsprint sprint`.
- Do **not** auto-fix security findings — the SecurityReviewer halts the run by design (ADR-005).
- Surface the resulting PR URL and `report.json` path to the user when the run completes.

## Reference

`skills/claude/SKILL.md`, `.specs/architecture/DESIGN.md`, `.specs/workflow/WORKFLOW.md`.
