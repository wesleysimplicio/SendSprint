# SendSprint — Kiro steering

Place this file at `.kiro/steering/sendsprint.md` in any repo where Kiro should
know about the SendSprint skill.

## Trigger phrases

Activate `sendsprint sprint` when the user types any of:

- pt-BR: "rode o sendsprint", "executar sprint", "Faça todas as minhas tarefas da sprint", "entregar sprint"
- en: "run sendsprint", "ship my sprint", "deliver my sprint", "process my Jira sprint", "process my ADO sprint"
- es: "ejecutar sprint", "procesar sprint"
- slash: `/sendsprint`

## Execute

Run exactly **one** shell command — do not split, do not narrate the inner steps:

```bash
sendsprint sprint
```

Behaviour:

1. Loads `~/.config/sendsprint/profile.yaml` for cached defaults.
2. Resolves credentials from the OS keyring (Keychain / Secret Service / Credential Manager). Prompts only the first time, then persists.
3. Defaults to `--scope mine`.
4. Runs the 10-step delivery: read sprint → architecture map → dev (worktree+install+build) → lint → tests (unit+E2E) → security (flag-only) → fix loop → commit+push → PR creation → PR review.

## First-run setup

If the repo has no `.specs/`:

```bash
sendsprint init
```

If credentials missing:

```bash
sendsprint login jira          # or: sendsprint login azuredevops
```

## Don'ts

- Don't bypass `sendsprint sprint` and try to re-implement the flow.
- Don't auto-fix security findings — `SecurityReviewer` halts by design (ADR-005).
- Don't commit on `main`. The flow uses an isolated worktree branch.

## Reference

- `skills/claude/SKILL.md` — full skill source
- `.specs/architecture/DESIGN.md` — architecture
- `.specs/workflow/WORKFLOW.md` — daily loop
- `.specs/architecture/ADR-00*.md` — design decisions
