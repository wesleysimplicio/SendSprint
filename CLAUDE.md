# CLAUDE.md

Claude Code-specific instructions for SendSprint. **Read [AGENTS.md](./AGENTS.md) FIRST** — that's the canonical source. This file only adds Claude-specific behavior.

---

## Source of truth

All stack, layout, commands, patterns, gotchas, commit conventions, and Definition of Done are in [AGENTS.md](./AGENTS.md). Do not duplicate that content here.

---

## Claude Code-specific behavior

### Skill invocation

When user says any of:
- pt-BR: "rode o sendsprint", "executar sprint", "entregar sprint", "processar sprint do Jira", "processar sprint do ADO"
- en: "run sendsprint", "execute sprint", "deliver sprint", "process Jira sprint", "process ADO sprint"
- es: "ejecutar sprint", "procesar sprint"

→ Invoke the SendSprint flow per `skills/claude/SKILL.md`.

### Subagent delegation

Use specialized subagents in parallel where possible:

| Trigger | Agent |
|---|---|
| Adding new tech stack support | `Explore` (find existing patterns) + `python-reviewer` |
| New agent class | `Plan` + `python-reviewer` after edit |
| Bug in operator | `everything-claude-code:python-reviewer` |
| Test missing | `everything-claude-code:tdd-guide` |
| Build error | `everything-claude-code:build-error-resolver` |
| Security finding in flow | `security-reviewer` (NEVER auto-fix — flag only per ADR-005) |

### Hook integration

Pre-commit hook at `.claude/hooks/pre-commit.sh` blocks commit if `pytest tests/ -v` fails.
Post-edit hook at `.claude/hooks/post-edit.sh` runs `ruff format` on `.py` edits.

### Tool preferences

- **Edit > Write** for existing files
- **Read full file** before edit (mandatory)
- **Bash for tests/lint/git**, never for file content (use Read/Edit/Write)
- **Parallel tool calls** for independent reads (e.g., reading 5 skill manifests at once)

### MCP servers (when available)

- `atlassian` MCP → use for Jira sprint reading instead of REST fallback when configured
- `playwright-global` MCP → use for E2E Playwright fallback when CDP browser unreachable
- `github` MCP → use for PR creation when `gh` CLI absent

Order matches transport priority in AGENTS.md §4: `mcp` → `api` → `playwright`.
