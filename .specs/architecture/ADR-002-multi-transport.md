# ADR-002: Multi-transport with fixed `mcp` → `api` → `playwright` order

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-04-02 |
| Deciders | wesley@beyondlabs |
| Supersedes | — |

---

## Context

Reading sprint state from Jira/ADO can fail in three independent ways:

1. **MCP server** (modelcontextprotocol bridge): may not be running locally, or may not yet be configured for that org.
2. **REST API** (Jira `/rest/agile/1.0/`, ADO `/_apis/wit/`): may be blocked by IP allowlist, expired PAT, or rate limit (Jira 429 after 100 req/min).
3. **Playwright (CDP)**: may have stale session, missing cookies, or DOM changes after Atlassian/Microsoft UI updates.

Each transport has a different failure mode. Hard-pinning one fails brittly; trying random order produces inconsistent error messages and double-charges quotas.

---

## Decision

**Fixed transport priority**, evaluated in order, with one and only one winner per `read()`:

```python
TRANSPORT_ORDER = ("mcp", "api", "playwright")

class JiraOperator:
    def read(self, sprint_id: int) -> Sprint:
        last_err: Exception | None = None
        for transport in TRANSPORT_ORDER:
            if not self._available(transport):
                continue
            try:
                return self._read_via(transport, sprint_id)
            except TransportError as exc:
                last_err = exc
                console.log(f"[yellow]transport {transport} failed: {exc}[/]")
        raise TransportError(f"all transports failed: {last_err}")
```

**Rationale per position:**
1. **MCP first**: zero quota cost, fastest (local IPC), and richest payload (typed responses). When available, never miss.
2. **API second**: most reliable when MCP absent. Costs quota (1 req per sprint).
3. **Playwright last**: brittle and slow (~10s per sprint), but works behind SSO and IP allowlists when API blocked.

---

## Consequences

### Positive
- **Predictable**: same order every run, easy to reason about logs.
- **Cheap when possible**: MCP path is free; only escalate when needed.
- **Compatible across org policies**: works whether team uses MCP, API tokens, or only browser SSO.

### Negative
- **MCP requires config**: users without MCP server installed always pay API cost.
- **Playwright fallback can take 10s+**: must surface clear "trying playwright" log so users understand the wait.
- **Cannot skip a transport** (by design — see "rejected alternatives").

---

## Alternatives considered

| Approach | Rejected because |
|----------|------------------|
| User-selected transport | Removes the "it just works" promise; users won't know which to pick |
| Parallel transports, first-wins | Doubles/triples quota cost; race conditions on rate limits |
| Random order | Inconsistent error messages confuse users |
| Skip API when MCP available | Some MCP servers return partial data; API still needed for full sprint |
| Reorder per env var | Adds config burden; breaks "deterministic 10-step flow" promise |

---

## See also

- [DESIGN.md](DESIGN.md) — operators layer
- [PATTERNS.md](PATTERNS.md) — httpx + subprocess idioms
- [/.specs/product/DOMAIN.md](../product/DOMAIN.md) — Sprint.transport field
- [/AGENTS.md](../../AGENTS.md)
