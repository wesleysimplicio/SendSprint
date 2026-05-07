# ADR-NNN: <short decision title>

> Copy this file to `.specs/architecture/ADR-NNN-<short-name>.md` (next available NNN).
> Replace `<...>` placeholders. Delete this blockquote before merging.

| Field | Value |
|-------|-------|
| Status | Proposed | Accepted | Superseded by ADR-NNN | Deprecated |
| Date | YYYY-MM-DD |
| Deciders | @<github-handle> |
| Supersedes | — OR ADR-NNN |

---

## Context

<2–4 paragraphs — what problem are we solving, what forces are at play, what constraints apply>

- Constraint 1
- Constraint 2
- Stakeholder need

---

## Decision

<one-paragraph summary of what we're doing>

**Concretely:**

- Decision point 1 (with config/code snippet if relevant)
- Decision point 2
- Decision point 3

```python
# Example code showing the decided pattern
```

---

## Consequences

### Positive

- <benefit 1>
- <benefit 2>

### Negative

- <cost / trade-off 1 — and how we mitigate it>
- <cost / trade-off 2>

### Neutral

- <side effect that's neither good nor bad but worth noting>

---

## Alternatives considered

| Approach | Rejected because |
|----------|------------------|
| <alt 1> | <reason — be specific> |
| <alt 2> | <reason> |
| <alt 3> | <reason> |

---

## Implementation notes

- File(s) where this lives: `sendsprint/<module>/<file>.py`
- Test(s) that lock it in: `tests/<module>/test_<file>.py`
- Telemetry / metric to watch: <name OR n/a>

---

## See also

- [DESIGN.md](DESIGN.md) — bird's-eye architecture
- [PATTERNS.md](PATTERNS.md) — code idioms
- ADR-NNN — related decision
- <external link if any>
