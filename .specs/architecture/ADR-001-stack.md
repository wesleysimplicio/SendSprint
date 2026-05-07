# ADR-001: Python 3.11+ + Pydantic v2 + Typer

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-04-01 |
| Deciders | wesley@beyondlabs |
| Supersedes | — |

---

## Context

SendSprint orchestrates 10 deterministic steps over multi-repo workspaces, integrating with Jira/ADO REST APIs, GitHub `gh` CLI, ADO REST, Playwright (CDP), and optional LLMs. Need is for:

- Strong typing for `RunReport` serialization (Pydantic v2 `model_dump_json()` is a single source of truth).
- Subprocess orchestration (git, npm/pip/dotnet, eslint, pytest, playwright).
- Sync HTTP with timeouts (Jira/ADO + gh fallback).
- Optional async for multi-repo runs (planned v0.3).
- AI-agent friendly: every major LLM platform has Python SDKs.

---

## Decision

- **Python ≥ 3.11**: needed for `Self`, `tomllib` stdlib, exception groups, fast PEG parser.
- **Pydantic v2**: 5–50× faster than v1, native `model_dump`/`model_validate`, strict mode, `Literal` support.
- **Typer**: argparse-on-steroids with type-driven CLI, autocompletion, rich help.
- **Rich**: console output (logs + progress bars + tables).
- **httpx**: sync + async HTTP with proper timeouts (drop `requests`).
- **playwright (sync)**: CDP fallback for headless Jira/ADO scraping when API blocked.
- **pyyaml**: `workspace.yaml` parser.

---

## Consequences

### Positive
- **One stack** for CLI + lib + tests. No JS/TS runtime needed.
- **Type-safe end-to-end**: `RunReport` serialized identically across CLI output, JSON file, and tests.
- **AI-platform native**: skill manifests directly invoke Python (`from sendsprint.flow import SprintFlow`).
- **Fast import startup** (<200ms cold) thanks to lazy module loading.

### Negative
- Python 3.10 and below not supported (acceptable: 3.11 is 3 years old at decision time).
- Pydantic v1 codebases need migration if vendoring as a library.
- Async multi-repo requires careful subprocess handling (no `asyncio.subprocess` mixed with sync runs).

---

## Alternatives considered

| Stack | Rejected because |
|-------|------------------|
| **Go** | Slow Pydantic equivalent (manual struct tags); LLM SDKs less mature; `gh` CLI integration awkward |
| **Node 22 + TS** | Heavy install (~500MB node_modules), Playwright also slower in TS, less idiomatic for subprocess-heavy CLI |
| **Rust** | Build complexity blocks AI-agent contribution; LLM SDKs early-stage; no clear benefit for I/O-bound workload |
| **Python 3.10 + Pydantic v1** | Pydantic v1 deprecated; `tomllib` requires 3.11 |

---

## See also

- [DESIGN.md](DESIGN.md) — where this stack fits
- [PATTERNS.md](PATTERNS.md) — code idioms enforcing this stack
- [ADR-002-multi-transport.md](ADR-002-multi-transport.md) — transport order built on httpx/playwright
- [/AGENTS.md](../../AGENTS.md)
