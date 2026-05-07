# SendSprint — Zed AI rule

Place this file at `.rules` (or append its contents to your existing `.rules`)
in any repo where Zed's assistant should know about SendSprint.

## Trigger phrases

When the user types any of these in the Assistant panel, run `sendsprint sprint`:

- pt-BR: "rode o sendsprint", "executar sprint", "Faça todas as minhas tarefas da sprint", "entregar sprint"
- en: "run sendsprint", "ship my sprint", "deliver my sprint", "process my Jira sprint"
- es: "ejecutar sprint", "procesar sprint"
- slash: `/sendsprint`

## Single command

```bash
sendsprint sprint
```

That:

1. Loads `~/.config/sendsprint/profile.yaml`.
2. Resolves credentials from the OS keyring (prompts only once, then persists).
3. Defaults to `--scope mine`.
4. Runs all 10 steps: read sprint → arch map → dev → lint → tests → security → fix loop → commit+push → PR → PR review.

## First-run

```bash
sendsprint init                # if .specs/ missing
sendsprint login jira          # or: sendsprint login azuredevops
```

## Rules

- Always defer to `sendsprint sprint`; never re-implement the flow.
- Never auto-fix security findings (ADR-005).
- Never commit on `main` — the flow uses an isolated worktree.

## Reference

- `skills/claude/SKILL.md`
- `.specs/architecture/DESIGN.md`
- `.specs/workflow/WORKFLOW.md`
