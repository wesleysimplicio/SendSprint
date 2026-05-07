# ADR-003: Three-tier test strategy (unit mocks + integration recorded + live canary)

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-04-03 |
| Deciders | wesley@beyondlabs |
| Supersedes | — |

---

## Context

SendSprint integrates with **external systems** that are slow, rate-limited, or require credentials:

- Jira REST (PAT-protected, 100 req/min)
- ADO REST (PAT-protected, throttled)
- GitHub `gh` CLI (PAT-protected, 5000 req/hr)
- Playwright CDP (requires Chrome session)
- LLM APIs (Anthropic / OpenAI) — paid per token

Running every test against live APIs is **slow** (>30s per `JiraOperator` test) and **expensive** (LLM tests = real $). But mocking everything risks silent drift when upstream changes payload shape.

---

## Decision

**Three test tiers**, each runnable independently:

### Tier 1 — Unit (default, runs in CI on every commit)

```python
def test_jira_operator_parses_payload(httpx_mock):
    httpx_mock.add_response(json={"values": [{"id": 42, "name": "Sprint 12", "state": "active"}]})
    sprint = JiraOperator(transport="api").read(sprint_id=42)
    assert sprint.id == "42"
    assert sprint.state == "active"
```

- Mock all I/O (httpx via `pytest-httpx`, subprocess via `monkeypatch`, time via fixture).
- Run on every PR. Must pass before merge.
- Fast (<1s per test).

### Tier 2 — Integration (recorded cassettes, runs nightly)

```python
@pytest.mark.integration
@pytest.mark.vcr  # records once, replays after
def test_jira_operator_real_payload():
    sprint = JiraOperator(transport="api").read(sprint_id=42)
    assert len(sprint.items) > 0
```

- Uses `pytest-vcr` to record real Jira/ADO responses once, replay forever.
- Run nightly via `pytest -m integration`.
- Recordings checked into `tests/cassettes/`.

### Tier 3 — Live canary (manual, runs weekly)

```python
@pytest.mark.canary
def test_jira_canary():
    sprint = JiraOperator(transport="auto").read(sprint_id=int(os.environ["CANARY_SPRINT_ID"]))
    assert sprint.id
```

- Hits real APIs with real credentials (`JIRA_API_TOKEN`, `AZURE_DEVOPS_PAT`).
- Run via `pytest -m canary` weekly or on-demand.
- Detects upstream payload drift before users do.

---

## Consequences

### Positive
- **Fast PR feedback**: Tier 1 runs in <30s for full suite.
- **No drift**: Tier 2 catches schema changes via VCR replay diff.
- **Real-world validation**: Tier 3 catches auth/quota/regional issues.
- **Cheap by default**: zero LLM/API cost per commit.

### Negative
- **Three test discipline**: contributors must understand which tier their change needs.
- **Cassette maintenance**: when upstream payload changes intentionally, must re-record.
- **Canary needs secrets**: requires CI secrets for nightly run (or gated to maintainers).

---

## Alternatives considered

| Approach | Rejected because |
|----------|------------------|
| All-mock | Silent drift when Jira/ADO change payload |
| All-live | $$$ + slow + flaky on rate limits |
| Manual smoke tests | Forgotten; not enforceable |
| Contract tests (Pact) | Overkill for read-only operators; adds infra |

---

## See also

- [PATTERNS.md](PATTERNS.md) — pytest idioms (Tier 1)
- [DESIGN.md](DESIGN.md) — failure model
- [/AGENTS.md](../../AGENTS.md)
