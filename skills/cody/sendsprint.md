# SendSprint — Sourcegraph Cody rule

Place this file at `.sourcegraph/cody/instructions.md` (per-repo) or copy the JSON
section to `.cody/commands/sendsprint.json`.

## Trigger phrases

When the user types any of these in Cody chat, run `sendsprint sprint`:

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

## Custom command (`.cody/commands/sendsprint.json`)

```json
{
  "sendsprint": {
    "description": "Run the SendSprint 10-step delivery flow.",
    "prompt": "Execute exactly: `sendsprint sprint`. Do not split into sub-steps. Do not re-implement the flow. Do not auto-fix security findings. Surface PR URL and report.json path when done.",
    "context": {
      "currentDir": true,
      "selection": false
    },
    "mode": "ask"
  }
}
```

## First-run

```bash
sendsprint init                 # if repo lacks `.specs/`
sendsprint login jira           # or: sendsprint login azuredevops
```

## Hard rules

- Always defer to `sendsprint sprint`. Do not re-implement the 10 steps.
- Do not auto-fix security findings — `SecurityReviewer` halts the run by design (ADR-005).
- Never commit on `main`. The flow uses an isolated worktree branch.

## Reference

- `skills/claude/SKILL.md` — full skill source
- `.specs/architecture/DESIGN.md`
- `.specs/workflow/WORKFLOW.md`
