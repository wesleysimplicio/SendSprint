# Contributing to SendSprint

> What reviewers expect. How to land changes fast.

---

## Before you start

1. **Read [/AGENTS.md](../../AGENTS.md)** — canonical project instructions.
2. **Read [WORKFLOW.md](WORKFLOW.md)** — daily loop, branch + commit conventions.
3. **Read [/.specs/architecture/DESIGN.md](../architecture/DESIGN.md)** + relevant ADRs.
4. **Search existing issues + PRs** — avoid duplicate work.

---

## What we accept

| Contribution | Difficulty | Likelihood of merge |
|--------------|-----------|---------------------|
| New stack support in `detect_tech` | Easy | Very high |
| New lint/test command in `LintRunner._STACK_COMMANDS` | Easy | Very high |
| New PR provider (e.g., GitLab MR) | Medium | High — needs ADR |
| New operator (e.g., Linear, ClickUp) | Medium | High — needs ADR |
| Bug fix with regression test | Any | Very high |
| Docs (README, ADR, skill manifest) | Easy | Very high |
| New LLM provider | Medium | Medium — needs cost ADR |
| Reorder transport chain | Hard | **Very low** — see ADR-002 |
| Auto-fix security findings | Hard | **Will not be merged** — see ADR-005 |
| Drop Pydantic v2 | Hard | **Will not be merged** — see ADR-001 |

---

## PR requirements

Every PR must:

1. **Pass CI** (`ruff check`, `ruff format --check`, `mypy`, `pytest -m "not canary"`).
2. **Update CHANGELOG.md** under `[Unreleased]` with one line per user-visible change.
3. **Cite the ADR** if touching architecture (worktree, transport, security, mock tiers, stack).
4. **Include a regression test** for bug fixes.
5. **Include doc updates** if changing public API (`SprintFlow`, `JiraOperator`, `Workspace`, `RunReport`).

### PR description template

```markdown
## What
<one paragraph>

## Why
<one paragraph — link to issue if any>

## How
<bullet list of approach>

## Testing
- [ ] unit tests pass (`pytest -m "not integration and not canary"`)
- [ ] integration tests pass (if touched)
- [ ] manual smoke run: `sendsprint run jira <id> --workspace ...`

## ADRs touched
- (none) OR ADR-NNN
```

---

## Code review SLA

- **First response**: within 2 working days.
- **Approval or actionable feedback**: within 5 working days.
- **Stale PRs** (no author response 14 days): closed with a "feel free to reopen" note.

---

## Style

- Follow [/.specs/architecture/PATTERNS.md](../architecture/PATTERNS.md) **exactly**.
- New code: type hints everywhere, `from __future__ import annotations`.
- New tests: pytest, not unittest.
- New HTTP: `httpx`, not `requests`.
- New subprocess: `subprocess.run(..., timeout=N, check=False)`, list-form, no `shell=True`.

---

## Adding a new ADR

1. Copy [/templates/ADR-template.md](../../templates/ADR-template.md) to `.specs/architecture/ADR-NNN-<short-name>.md` (next available NNN).
2. Fill out: Status (Proposed initially), Date, Deciders, Context, Decision, Consequences, Alternatives.
3. Link from `DESIGN.md` "See also" + `AGENTS.md` §10.
4. Open PR with `docs(adr):` commit prefix.
5. After approval and merge, update Status to `Accepted`.

---

## Adding a new skill manifest

> A "skill" = AI agent platform integration (Claude / Codex / Hermes / Openclaw / Copilot / …).

1. Create `skills/<platform>/<filename>` (filename per platform convention: `SKILL.md`, `AGENTS.md`, `<name>.md`, `copilot-instructions.md`).
2. Use existing manifests as template (frontmatter + Trigger + Steps + Stack + Comandos + Padrão de código + Pegadinhas + DoD).
3. Add cross-link to `/AGENTS.md` §11 (skills index).
4. Bump MINOR version (new platform support = minor).

---

## Reporting security issues

**Do NOT open a public issue.** Email security@beyondlabs.io with:
- Description
- Reproduction
- Suggested fix (optional)
- Whether you want public credit

We respond within 48h and ship a fix in the next patch release.

---

## License

By contributing, you agree your contributions are licensed under the same license as the project (MIT — see [/LICENSE](../../LICENSE)).

---

## See also

- [WORKFLOW.md](WORKFLOW.md) — daily loop
- [/AGENTS.md](../../AGENTS.md) — canonical instructions
- [/.specs/architecture/PATTERNS.md](../architecture/PATTERNS.md) — code idioms
