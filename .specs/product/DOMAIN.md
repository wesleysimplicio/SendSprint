# SendSprint — Domain Model

> Core entities, their fields, and relationships. Source of truth for Pydantic v2 models in `sendsprint/models/`.

---

## Entities (top-level)

```
Workspace ──┬── RepoConfig (1..N)
            └── ScopeConfig (0..1)

Sprint ─── SprintItem (0..N)

RunReport ─┬── StepReport (10)
           ├── PrInfo (0..N)
           └── FixLoopRecord (0..3)
```

---

## Sprint

> What we read from Jira/ADO at Step 1.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `str` | Sprint id (Jira) or iteration path (ADO) |
| `name` | `str` | Display name |
| `state` | `Literal["active","closed","future"]` | Current state |
| `start_date` | `datetime \| None` | UTC |
| `end_date` | `datetime \| None` | UTC |
| `items` | `list[SprintItem]` | Scope-filtered items |
| `provider` | `Literal["jira","azuredevops"]` | Source operator |
| `transport` | `Literal["mcp","api","playwright"]` | How it was fetched |

---

## SprintItem

| Field | Type | Notes |
|-------|------|-------|
| `key` | `str` | `PROJ-123` (Jira) or numeric id (ADO) |
| `type` | `Literal["story","bug","task","epic","spike"]` | Normalized |
| `title` | `str` | Summary |
| `status` | `str` | Free-form (`To Do`, `In Progress`, `Done`, custom) |
| `assignee_email` | `str \| None` | Used by `--scope mine` |
| `assignee_account_id` | `str \| None` | Jira-only |
| `assignee_descriptor` | `str \| None` | ADO-only |
| `assignee_display_name` | `str \| None` | Last-resort match |
| `repo_hint` | `str \| None` | Optional `[repo:backend-api]` tag in title |
| `labels` | `list[str]` | Free-form |
| `url` | `str` | Direct link |

**Validation:** `key` non-empty; `type` lowercased; assignee fields nullable but at least one populated when `--scope mine`.

---

## Workspace

> Multi-repo descriptor loaded from `workspace.yaml` at runtime.

| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | Project name |
| `root_path` | `Path` | Where repos live |
| `new_projects_dir` | `Path` | Where to clone new repos |
| `pr_provider` | `Literal["github","azuredevops"]` | PR backend |
| `repos` | `list[RepoConfig]` | One per repo |

---

## RepoConfig

| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | Logical name |
| `path` | `Path` | Relative to `Workspace.root_path` |
| `role` | `Literal["api","front","worker","mobile","infra","lib"]` | Used for routing |
| `tech` | `str` | Hint (`dotnet`, `angular`, `python`, …) — overrides `detect_tech` |
| `default_branch` | `str` | Usually `main` or `master` |

---

## ScopeConfig

| Field | Type | Notes |
|-------|------|-------|
| `mode` | `Literal["all","mine"]` | Default `all` |
| `user_email` | `str \| None` | Required if `mode == "mine"` |
| `user_account_id` | `str \| None` | Jira-specific |
| `user_descriptor` | `str \| None` | ADO-specific |
| `user_display_name` | `str \| None` | Fallback match |

**Match logic** (`--scope mine`): item kept if assignee_account_id == user_account_id OR assignee_email == user_email OR assignee_descriptor == user_descriptor OR assignee_display_name == user_display_name. All falsy → no filter.

---

## RunReport

> Output of `SprintFlow.run()`. Serialized to `report.json`.

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | `UUID` | Auto-generated |
| `started_at` | `datetime` | UTC |
| `finished_at` | `datetime` | UTC |
| `failed` | `bool` | True if any step failed permanently |
| `summary` | `str` | Human-readable one-liner |
| `steps` | `list[StepReport]` | 10 entries, in order |
| `prs` | `list[PrInfo]` | One per repo with changes |
| `fix_loops` | `list[FixLoopRecord]` | 0–3 entries |
| `sprint` | `Sprint` | What was processed |
| `workspace` | `Workspace` | What context |

---

## StepReport

| Field | Type | Notes |
|-------|------|-------|
| `step` | `int` | 1–10 (must match flow position) |
| `name` | `str` | `read_sprint`, `architecture`, `dev`, … |
| `status` | `Literal["pass","fail","skipped","retried"]` | |
| `duration_ms` | `int` | |
| `output` | `dict[str, Any]` | Step-specific payload |
| `error` | `str \| None` | Stack trace if failed |

---

## PrInfo

| Field | Type | Notes |
|-------|------|-------|
| `repo` | `str` | `RepoConfig.name` |
| `branch` | `str` | Pushed branch |
| `url` | `str` | Provider URL |
| `provider` | `Literal["github","azuredevops"]` | |
| `commit_sha` | `str` | Head of branch |

---

## FixLoopRecord

| Field | Type | Notes |
|-------|------|-------|
| `round` | `int` | 1–3 |
| `triggered_by` | `list[Literal["lint","tests","security"]]` | Which check forced the retry |
| `resolved` | `bool` | True if retry made the check pass |

---

## Agent step ↔ module map

> **Step numbers must match these positions.** Changing flow order = update all `step=N` in agents.

| Step | Module | Class | Notes |
|------|--------|-------|-------|
| 1 | `sendsprint/operators/` | `JiraOperator` / `AzureDevopsOperator` | Transport `auto` |
| 2 | `sendsprint/architecture/` | `ArchitectureMapper` | Baseline if score < 0.6 |
| 3 | `sendsprint/agents/` | `DevAgent` | Uses `WorktreeManager` |
| 4 | `sendsprint/agents/` | `LintRunner` | 19 stacks |
| 5 | `sendsprint/agents/` | `TestRunner` | Unit + E2E + screenshots |
| 6 | `sendsprint/agents/` | `SecurityReviewer` | Flag-only (ADR-005) |
| 7 | `sendsprint/flow/` | `SprintFlow._fix_loop` | Max 3 rounds |
| 8 | `sendsprint/flow/` | `SprintFlow._push_branch` | `--force-with-lease` |
| 9 | `sendsprint/agents/` | `PrCreator` | `gh` / ADO REST |
| 10 | `sendsprint/agents/` | `PrReviewer` | Diff static checks |

---

## Invariants

1. **Step numbers are stable** — moving them = breaking change.
2. **Worktrees are real** — created via `git worktree add`, cleaned in `__exit__`.
3. **Transport order is fixed**: `mcp` → `api` → `playwright`.
4. **Fix loop max = 3** — beyond that: `failed=true`.
5. **Security findings halt the run** — never auto-fixed (ADR-005).
6. **Push must precede PR** — `_push_branch` runs before `pr_creator`.

---

## See also

- [VISION.md](VISION.md) — product north star
- [/AGENTS.md](../../AGENTS.md) — canonical instructions
- [/.specs/architecture/PATTERNS.md](../architecture/PATTERNS.md) — code patterns
