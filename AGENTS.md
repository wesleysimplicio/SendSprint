# AGENTS.md — SendSprint

Master instruction file for AI agents working in this repo. Read this FIRST. All other agent files (CLAUDE.md, copilot-instructions.md, skills/) reference this as source of truth.

---

## 1. What this project is

**SendSprint** = multi-agent skill that automates **end-to-end sprint delivery** in a 10-step flow:

1. Read sprint (Jira / Azure DevOps)
2. Architecture mapping (inspect + auto-generate baseline if missing)
3. Dev: tech detection, worktree, install, build
4. Lint (19 stacks)
5. Tests (unit + Playwright E2E with screenshot evidence)
6. Security review (flag-only: secrets, env, npm/pip/cargo audit)
7. Fix loop (max 3 rounds, re-runs lint+tests+security)
8. Commit (worktree branch)
9. Create PR (GitHub `gh` CLI / Azure DevOps REST)
10. PR review (diff static analysis) + Delivered

Transport priority: `mcp` → `api` → `playwright`.

Multi-repo: `workspace.yaml` defines repos with role + tech.

Filtering: `--scope mine` filters items to current user only.

---

## 2. Stack

- **Python ≥ 3.11** (3.12 supported in CI matrix)
- **Pydantic v2** for all models
- **Typer + Rich** for CLI
- **httpx** for REST calls
- **playwright** (sync) for browser fallback
- **pyyaml** for workspace config
- **pytest + pytest-asyncio + pytest-cov** for tests
- **ruff + mypy** for lint/type-check
- Build: **hatchling**

---

## 3. Layout

```
sendsprint/
├── operators/         JiraOperator, AzureDevopsOperator (mcp|api|playwright)
├── models/            Sprint, SprintItem, StepReport, RunReport (Pydantic v2)
├── agents/
│   ├── worktree.py    Git worktree isolation
│   ├── dev.py         Install + build (16 package managers)
│   ├── lint_runner.py 19 linters
│   ├── test_runner.py Unit + E2E
│   ├── security_reviewer.py  12 secret patterns + npm/pip/cargo audit
│   ├── pr_creator.py  GitHub gh / Azure DevOps REST
│   └── pr_reviewer.py Diff static checks
├── architecture/
│   ├── mapper.py      Weighted scoring
│   └── builder.py     Auto-generate baseline docs
├── tech/detector.py   25+ tech filesystem markers
├── workspace/loader.py YAML/JSON multi-repo loader
├── scope.py           --scope mine filter
├── flow/sprint_flow.py 10-step orchestrator
├── llm/               Provider-agnostic LLM client
└── cli.py             Typer CLI entrypoint

skills/                Per-platform manifests (Claude/Codex/Hermes/Openclaw/Copilot)
.specs/                Product/architecture/workflow specs + ADRs
.claude/hooks/         Pre/post-edit hooks
templates/             Task + ADR templates
tests/                 pytest suite (103 tests)
```

---

## 4. Commands

```bash
# Install
pip install -e ".[dev]"
playwright install chromium

# Test (run before any commit)
pytest tests/ -v
pytest tests/ --cov=sendsprint --cov-report=term-missing

# Lint + type check
ruff check sendsprint/
ruff format sendsprint/
mypy sendsprint/

# CLI
sendsprint version
sendsprint detect-tech ./repo
sendsprint check-architecture ./repo --build
sendsprint read-jira 42
sendsprint read-ado "Team\\Sprint 12"
sendsprint run jira 42 --workspace workspace.yaml --scope mine -o report.json
sendsprint run azuredevops "Sprint 12" --repo ./repo
```

---

## 5. Code patterns (HARD RULES)

### Operator
```python
from sendsprint.operators import JiraOperator
op = JiraOperator(base_url="https://org.atlassian.net", transport="auto")
sprint = op.read_sprint(sprint_id=42)
```

### Flow
```python
from sendsprint.flow import SprintFlow
from sendsprint.workspace import load_workspace
from sendsprint.scope import build_scope

ws = load_workspace("workspace.yaml")
scope = build_scope(mode="mine", user_email="dev@example.com")
flow = SprintFlow(operator=op, workspace=ws, scope=scope)
result = flow.run(sprint_id=42)
print(result.run_report.summary)
print(result.to_json())
```

### Adding a new tech to detector
1. Add markers tuple to `KNOWN_TECHS` in `sendsprint/tech/detector.py`
2. Categorize in `FRONT_TECHS` / `BACK_TECHS` / `MOBILE_TECHS` / `INFRA_TECHS`
3. Add lint command to `LINT_COMMANDS` in `sendsprint/agents/lint_runner.py`
4. Add install/build command in `sendsprint/agents/dev.py`
5. Add unit/E2E test command in `sendsprint/agents/test_runner.py`
6. Write tests in `tests/test_tech_detector.py` and `tests/test_agents.py`

### Adding a new agent
1. Create `sendsprint/agents/<name>.py` with class accepting `RepoConfig` + `Path`
2. Method must return `StepReport` (`step`, `name`, `status`, `details`)
3. Wire into `SprintFlow` step ordering (`flow/sprint_flow.py`)
4. Update `MAX_FIX_LOOPS` integration if step participates in fix loop
5. Add to all 5 skill manifests step list

### Mock fallback (when ext tools missing)
```python
try:
    result = subprocess.run([cmd], ...)
except FileNotFoundError:
    return StepReport(step=N, name="...", status="skipped", details={"reason": "tool not installed"})
```

---

## 6. Test rules

- **Every** new agent/operator/model gets a test in `tests/`
- Use `monkeypatch` to mock `httpx.Client.request` and `subprocess.run`
- Test both happy path AND fallback path
- Run full suite (`pytest tests/ -v`) before commit — must be 100% green
- Coverage target: ≥ 85% (currently 103 tests)

---

## 7. Gotchas

- **Transport fallback order is fixed**: `mcp` → `api` → `playwright`. Don't reorder. `auto` resolves first available.
- **Worktree side effects**: `WorktreeManager` creates real git worktrees. Tests must clean up (`tempfile.TemporaryDirectory()`).
- **Fix loop max 3**: hard cap. Beyond that = give up + report failed.
- **Security reviewer is flag-only**: NEVER auto-fix secrets. Always report + halt.
- **Step numbers must match flow order**: changing step order = update step numbers in ALL agent files (`step=N` in StepReport).
- **PR creation requires push first**: `_push_branch()` must run before `pr_creator`. Otherwise commit lives only locally.
- **Workspace `new_projects_dir`**: relative to `root_path`. Don't make absolute.
- **`--scope mine` matches**: account_id (Jira) OR email OR descriptor (ADO) OR display_name. Falsy = no filter.

---

## 8. Commit conventions

- **Language: English, imperative mood** (`add`, `fix`, `refactor`)
- Format: `<type>: <subject>` then blank line then body
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
- Body explains **why**, not what (diff shows what)
- Reference ADR if architectural: `Refs ADR-003`
- NEVER commit secrets, `.env`, `uv.lock` (see `.gitignore`)

Example:
```
feat: add cargo-audit to security reviewer

Step 6 now checks Rust dependency vulns via `cargo audit --json`.
Caps at 20 findings per repo to avoid report bloat.

Refs ADR-005
```

---

## 9. Versioning

- **SemVer**. Bump in `sendsprint/__init__.py` + `pyproject.toml` + `README.md` status line + `CHANGELOG.md` entry.
- Patch: bug fix only. Minor: new feature, backwards-compatible. Major: breaking API change.
- All version files must match exactly.

---

## 10. References

- **Vision**: `.specs/product/VISION.md`
- **Domain model**: `.specs/product/DOMAIN.md`
- **Architecture diagram**: `.specs/architecture/DESIGN.md`
- **How-to extend**: `.specs/architecture/PATTERNS.md`
- **ADRs**: `.specs/architecture/ADR-*.md`
- **Workflow**: `.specs/workflow/WORKFLOW.md`
- **Contributing**: `.specs/workflow/CONTRIBUTING.md`
- **Per-platform skills**: `skills/{claude,codex,hermes,openclaw,copilot}/`
- **Templates**: `templates/`

---

## 11. Definition of Done (any change)

- [ ] Code written following patterns above
- [ ] Tests written and pass (`pytest tests/ -v`)
- [ ] Lint clean (`ruff check sendsprint/`)
- [ ] Format applied (`ruff format sendsprint/`)
- [ ] Type-check clean (`mypy sendsprint/`) — best effort
- [ ] Version bumped in 4 places (`__init__.py`, `pyproject.toml`, `README.md`, `CHANGELOG.md`)
- [ ] Commit message in English, imperative
- [ ] Pushed to `origin/main` (or feature branch + PR)
- [ ] If new pattern → ADR added in `.specs/architecture/`
