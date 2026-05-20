# Node Dashboard and Playwright Lane Architecture

> Issue: [#109](https://github.com/wesleysimplicio/SendSprint/issues/109)
> Parent epic: [#105](https://github.com/wesleysimplicio/SendSprint/issues/105)

## Principle

**Node is UI-only.** Python owns orchestration, scheduling, quality gates,
operational memory, and PR publishing. The Node dashboard consumes the
Python API and renders state. It never becomes the core scheduler or
CPU-bound runtime.

## Node Dashboard Scope

### What it does

- Renders run state (queued, running, done, failed)
- Renders agent state (current step, progress, blockers)
- Renders validation evidence (screenshots, traces, coverage)
- Renders operator chat messages
- Subscribes to SSE events for real-time updates
- Calls read-only and control APIs on the Python backend

### What it does NOT do

- Own the run loop or scheduler
- Manage worker processes (Python, Go, Rust)
- Evaluate quality gates or readiness scores
- Write to operational memory
- Publish PRs or update tracker issues
- Schedule or queue runs directly (delegates to Python API)
- Manage credentials or secrets

## API Consumption Pattern

The dashboard is a thin client over the Python FastAPI server
(`sendsprint.api.server`). All state lives server-side.

### Read APIs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness check |
| GET | `/runs` | List all runs |
| GET | `/runs/{run_id}` | Run status |
| GET | `/runs/{run_id}/agent-status` | Agent-level snapshot |
| GET | `/runs/{run_id}/dashboard` | Dashboard composite view |
| GET | `/runs/{run_id}/events` | SSE event stream |
| GET | `/runs/{run_id}/evidence/{name}` | Evidence file download |
| GET | `/api/runs` | Control-plane enriched run list |
| GET | `/api/runs/{run_id}` | Control-plane run detail |
| GET | `/api/runs/{run_id}/evidence` | Evidence bundle summary |
| GET | `/api/runs/{run_id}/quality` | Quality gate report |

### Write APIs (delegated operations)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/runs` | Start a run |
| POST | `/api/runs` | Start via control plane |

The dashboard may trigger a run via POST, but the Python backend owns
the actual orchestration. The POST returns a `run_id` and the dashboard
switches to polling/SSE.

## SSE Event Protocol

Transport: Server-Sent Events over `GET /runs/{run_id}/events`.

### Event types

| Type | Payload highlights | Terminal? |
|------|-------------------|-----------|
| `hello` | `run_id` | No |
| `step` | `step`, `name`, `status`, `progress` | No |
| `log` | `message` | No |
| `evidence` | `evidence_path`, `evidence_label` | No |
| `loop` | `iteration`, `max_iterations` | No |
| `regression` | `failing_tests` | No |
| `summary` | `summary`, `pr_url` | No |
| `done` | `summary`, `pr_url` | Yes |
| `error` | `message`, `failed` | Yes |
| `agent_state` | `agent_name`, `agent_status` | No |
| `operator_chat` | `chat_message`, `chat_sender` | No |
| keepalive | empty comment line | No |

### Delivery guarantees

- Events arrive in causal order per `run_id`.
- Keepalive every 30 seconds.
- Terminal events (`done`, `error`) close the stream.
- Missed events are not replayed. After reconnect, poll
  `GET /runs/{run_id}` for current state.

### Reconnect strategy

Exponential backoff starting at 1s, capped at 30s. On reconnect, fetch
current run state via REST before re-subscribing to SSE.

## Playwright Evidence Isolation

Playwright runs in an isolated Node/browser context for evidence capture.
It has no import path to Python packages and communicates only via the
filesystem and HTTP API.

### Evidence flow

```
Playwright   -->  evidence/{run_id}/   -->  Python API   -->  Dashboard
(captures)        (filesystem)              (serves)          (renders)
```

1. Playwright captures artifact (screenshot, trace, video, HAR).
2. Writes to `evidence/{run_id}/` directory.
3. Python worker emits SSE event `type=evidence` with `evidence_path`.
4. Dashboard receives SSE event and renders evidence link.
5. Dashboard fetches artifact via `GET /runs/{run_id}/evidence/{name}`.

### Evidence kinds

- `screenshot` -- PNG/JPEG page captures
- `trace` -- Playwright trace ZIP files
- `video` -- WebM/MP4 recordings
- `har` -- HTTP Archive logs
- `accessibility_snapshot` -- A11y tree dumps
- `console_log` -- Browser console output

### Isolation rules

- Playwright process has no import path to `sendsprint` Python packages.
- Communication with Python is via filesystem (evidence dir) or HTTP API only.
- Playwright never reads or writes `.sendsprint/runs/` state files.
- Playwright never evaluates quality gates or readiness scores.
- Playwright browser context is disposable (one per evidence capture session).
- Playwright evidence is append-only; Python never mutates captured artifacts.

## Formal Specs

Python-side contracts are defined in `sendsprint/dashboard_spec.py`:

- `NodeDashboardSpec` -- dashboard scope, consumed APIs, forbidden actions
- `PlaywrightLaneSpec` -- evidence capture isolation, flow, allowed/forbidden
- `DashboardEventProtocol` -- SSE event types, payload schemas, guarantees
- `SSEEventType` / `SSEEventPayload` -- canonical event wire format

## Related

- [#105](https://github.com/wesleysimplicio/SendSprint/issues/105) -- Runtime split epic
- [#106](https://github.com/wesleysimplicio/SendSprint/issues/106) -- Control-plane contracts
- [#102](https://github.com/wesleysimplicio/SendSprint/issues/102) -- Web control plane API
- [#103](https://github.com/wesleysimplicio/SendSprint/issues/103) -- Related Node boundary
- [ADR-001](./ADR-001-stack.md) -- Stack decision (Python-first)
