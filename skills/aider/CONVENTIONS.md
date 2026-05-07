# SendSprint — Aider conventions

Place this file at the repo root as `CONVENTIONS.md` (or load with `aider --read CONVENTIONS.md`).

## Trigger phrases

When the user types any of these, run `sendsprint sprint` in the shell:

- pt-BR: "rode o sendsprint", "executar sprint", "Faça todas as minhas tarefas da sprint", "entregar sprint"
- en: "run sendsprint", "ship my sprint", "deliver my sprint", "process my Jira sprint", "process my ADO sprint"
- es: "ejecutar sprint", "procesar sprint"
- slash: `/sendsprint`

## Single command

```bash
sendsprint sprint
```

That:

1. Loads `~/.config/sendsprint/profile.yaml`.
2. Resolves credentials from OS keyring (Keychain / Secret Service / Credential Manager). Prompts only the first time, then persists.
3. Defaults to `--scope mine`.
4. Runs the 10 steps: read sprint → architecture map → dev → lint → tests → security → fix loop → commit+push → PR → PR review.

## First-run

```bash
sendsprint init                 # if repo lacks `.specs/`
sendsprint login jira           # or: sendsprint login azuredevops
```

## Hard rules for the agent

- Always defer to `sendsprint sprint`. Do not re-implement the 10 steps.
- Do not auto-fix security findings — `SecurityReviewer` halts by design (ADR-005).
- Never commit on `main`. The flow uses an isolated worktree branch.
- After the run, surface the resulting PR URL and `report.json` path.

## Reference

- `skills/claude/SKILL.md` — full skill source
- `.specs/architecture/DESIGN.md`
- `.specs/workflow/WORKFLOW.md`
- `.specs/architecture/ADR-00*.md`
