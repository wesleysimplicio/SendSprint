# GitHub Copilot Instructions — SendSprint

**Read [AGENTS.md](../AGENTS.md) FIRST** — canonical source for stack, layout, commands, patterns, gotchas, commit conventions, and Definition of Done.

This file = GitHub Copilot-specific shorthand. Do not duplicate AGENTS.md content here.

---

## Quick context

SendSprint = Python multi-agent skill, 10-step sprint delivery flow, Jira/ADO → PR. Stack: Python ≥ 3.11, Pydantic v2, Typer, Rich, httpx, Playwright sync.

---

## Copilot suggestions — DO

- Use **Pydantic v2** (`BaseModel`, `Field`, `model_dump`, `model_dump_json`). NOT v1 (`dict()`, `json()`).
- Use **type hints everywhere**. `from __future__ import annotations` at top of every Python file.
- Use **`pathlib.Path`** not `os.path`.
- Use **`subprocess.run(..., capture_output=True, text=True, timeout=N, check=False)`**. Always set timeout.
- Wrap external tool calls in `try/except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError)` and return `StepReport(status="skipped"|"failed", details={...})`.
- Match step numbers to flow position: TestRunner=5, SecurityReviewer=6, LintRunner=4, PrCreator=9, PrReviewer=10.
- Cap report list lengths (e.g., max 20 secrets, max 20 vulns) to avoid bloat.
- Use **`sendsprint.platform`** helpers for cross-platform code (`is_windows()`, `shell_command()`, `vendor_bin()`).
- Prefer **`pathlib.Path`** over string concatenation for file paths.

## Copilot suggestions — DON'T

- DON'T use `requests` — use `httpx`.
- DON'T use `os.system` or `os.popen` — use `subprocess.run`.
- DON'T add new deps without confirming in pyproject.toml first.
- DON'T auto-fix security findings (ADR-005: flag-only).
- DON'T reorder transport fallback chain (`mcp` → `api` → `playwright`).
- DON'T modify step numbers without updating ALL agents + skill manifests.
- DON'T hardcode Unix paths (`/bin/`, `source .venv/bin/activate`) -- use `sendsprint.platform` helpers.
- DON'T assume `bash` or `sh` are available -- Windows only has `cmd` and PowerShell by default.

---

## SendSprint flow overview

SendSprint delivers a sprint in 10 sequential steps:

1. **Import** -- read sprint items from Jira / Azure DevOps / GitHub Issues.
2. **Plan** -- group items into tasks, detect tech stack.
3. **Scaffold** -- generate `.specs/` docs for new repos.
4. **Lint** -- run stack-appropriate linters.
5. **Test** -- run unit + E2E (Playwright) tests.
6. **Security** -- scan for secrets, dependency vulns, SAST findings (flag-only, never auto-fix).
7. **Review** -- automated PR review against coding standards.
8. **Build** -- compile / bundle where applicable.
9. **PR Create** -- open a pull request with evidence bundle.
10. **PR Review** -- final automated review pass.

Copilot can follow these steps using `sendsprint` CLI commands and the repo documentation. When in doubt, consult `sendsprint run --help` and `sendsprint validate --help`.

---

## Quality gates and safe autonomy

- All agent steps produce a `StepReport` with status `ok | failed | skipped`.
- Security findings are **never auto-fixed** (ADR-005). Always flag for human review.
- The `DeliveryQualityGate` in `sendsprint/quality_gate.py` consolidates all checks before publish. A `blocking` or `error` failure forces `needs_rework`.
- When `AutonomyPolicy.require_human_review` is true, warnings escalate to `needs_human_approval`.
- Evidence bundles persist every decision for audit trail.

---

## Windows install path (PowerShell)

```powershell
# 1. Clone and enter the repo
git clone https://github.com/wesleysimplicio/SendSprint.git
cd SendSprint

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install in editable mode
pip install -e ".[dev]"

# 4. Verify
sendsprint --version
python -m pytest tests/ -v
```

> **Note:** Use `python` (not `python3`) on Windows. Use `.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`. Environment variables use `$env:VAR = "value"` in PowerShell, not `export`.

---

## Cross-platform guidance

- Use `pathlib.Path` for all path operations -- never hardcode `/` or `\`.
- Use `sendsprint.platform.is_windows()` / `is_unix()` for platform-conditional logic.
- Use `sendsprint.platform.shell_command()` to wrap subprocess commands portably.
- Use `sendsprint.platform.vendor_bin(tool)` for PHP `vendor/bin/` paths.
- Never assume `bash`, `source`, or `/bin/sh` are available -- they are absent on stock Windows.
- PHP commands: `vendor/bin/phpcs` on Unix, `vendor\bin\phpcs.bat` on Windows.
- Venv activation: `source .venv/bin/activate` on Unix, `.venv\Scripts\Activate.ps1` on Windows.

---

## Optional accelerators (Codex / Claude only)

The following commands are **optional** and only available in specific AI agent runtimes:

- **`/goal`** -- Codex CLI command to set a long-running goal. Not available in Copilot or Claude Code.
- **`/ralph-loop`** -- Claude Code skill for autonomous loop execution. Not available in Copilot or Codex.

These are accelerators, not requirements. Copilot users should follow the standard `sendsprint` CLI workflow documented above and in AGENTS.md.

---

## Validation recipes by stack (all platforms)

### Python
```bash
python -m pytest tests/ -v
ruff check .
ruff format --check .
```
> **Windows:** Use `python` not `python3`. Activate with `.venv\Scripts\Activate.ps1`.

### Node / TypeScript
```bash
npm test
npm run build
npx playwright test
```
> **Windows:** Use `npx.cmd` or `npm.cmd` in CI scripts. Run `npx playwright install` with admin privileges if needed.

### Go
```bash
go test ./...
go vet ./...
```
> **Windows:** CGO may require mingw-w64. Use `$env:VAR = "value"` instead of `export VAR=value` in PowerShell.

### Rust (optional)
```bash
cargo test
cargo clippy -- -D warnings
```
> **Windows:** Requires MSVC toolchain by default. Use `rustup default stable-x86_64-pc-windows-msvc` if builds fail.

---

## Common file edits

When editing any of these, also bump version + CHANGELOG:

- `sendsprint/__init__.py` → `__version__`
- `pyproject.toml` → `version = "..."`
- `README.md` → status line
- `CHANGELOG.md` → new entry (Added/Changed/Fixed/Removed/Security)

---

## Test pattern

```python
def test_<thing>_<case>(monkeypatch, tmp_path):
    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout="ok", stderr="")
    monkeypatch.setattr(subprocess, "run", mock_run)
    # arrange + act + assert
```

<!-- rtk-cli:start -->
## Shell token-smart (RTK CLI, optional)

If `rtk` (https://github.com/rtk-ai/rtk) is on PATH, prefer `rtk read|grep|find|git|pytest` for repo exploration and verbose validators. Falls back to plain commands when absent. Full rules in AGENTS.md and `.skills/rtk-cli/SKILL.md`.
<!-- rtk-cli:end -->

<!-- codex-long-running-agent-overlay:start -->
## Universal Long-Running Agent Overlay

This section complements the repository-specific guidance already in this file. If anything here conflicts with the repo-specific rules above, the repo-specific rules win.

- `PRD.md` is the task source of truth for long-running sessions.
- `PROGRESS.md` is the persistent checkpoint log.
- `GOAL_RESULT.md` is the final execution report.
- Before coding, read this file, `PRD.md`, `PROGRESS.md` when it exists, `README.md`, project manifests, tests, and the relevant source folders.
- Work in small checkpoints, run the smallest relevant validation after each meaningful change, update `PROGRESS.md`, and continue until complete or genuinely blocked.
- Stop only when the requested work is complete, validation is documented, and `GOAL_RESULT.md` reflects the outcome.
- Do not rewrite unrelated architecture, fake successful validation, expose secrets, or push without explicit operator instruction for the active session.
<!-- codex-long-running-agent-overlay:end -->
