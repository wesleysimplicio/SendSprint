# SendSprint — Code Patterns

> Canonical idioms. Mirror these in any new code under `sendsprint/`.

---

## File header

Every Python module starts with:

```python
"""<one-line purpose>.

<optional 2–3 line context>.
"""

from __future__ import annotations

# stdlib
# third-party
# local
```

`from __future__ import annotations` is **mandatory** (PEP 563 deferred evaluation).

---

## Pydantic v2 models

```python
from pydantic import BaseModel, Field, ConfigDict

class Sprint(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    state: Literal["active", "closed", "future"]
    items: list[SprintItem] = Field(default_factory=list)
```

**Rules:**
- Always set `model_config` explicitly. Default to `frozen=True` for value objects.
- Use `Field(default_factory=list)` not `[]`.
- Prefer `Literal[...]` over `Enum` for string enums (lighter, JSON-friendly).
- Never use Pydantic v1 (`.dict()`, `.json()`, `Config` inner class).

---

## Subprocess

```python
import subprocess

result = subprocess.run(
    ["git", "worktree", "add", str(path), branch],
    cwd=repo,
    timeout=60,
    check=False,
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    raise WorktreeError(f"git worktree add failed: {result.stderr}")
```

**Rules:**
- Always pass `timeout` (never unbounded).
- Always `check=False` + manual returncode check (more informative errors).
- Always `capture_output=True, text=True`.
- Never use `os.system`, `os.popen`, `subprocess.call`, or `shell=True`.

---

## HTTP

```python
import httpx

with httpx.Client(timeout=30.0) as client:
    r = client.get(url, headers=headers)
    r.raise_for_status()
    return r.json()
```

**Rules:**
- Use `httpx`, never `requests`.
- Always `timeout=...` explicit.
- Use sync client for CLI flows; async only for proven concurrency wins.

---

## Paths

```python
from pathlib import Path

repo_path = Path(repo).expanduser().resolve()
config_file = repo_path / "pyproject.toml"
if config_file.exists():
    ...
```

**Rules:**
- Use `pathlib.Path` everywhere.
- Never `os.path.join`, `os.path.exists`, string concatenation.
- Always `.expanduser().resolve()` for user-supplied paths.

---

## Context managers

```python
class WorktreeManager:
    def __enter__(self) -> Path:
        self._path = Path(tempfile.mkdtemp(prefix="ss-wt-"))
        subprocess.run(["git", "worktree", "add", str(self._path), self._branch],
                       cwd=self._repo, check=True, timeout=60)
        return self._path

    def __exit__(self, exc_type, exc, tb) -> None:
        subprocess.run(["git", "worktree", "remove", "--force", str(self._path)],
                       cwd=self._repo, check=False, timeout=30)
```

**Rules:**
- Anything with paired setup/teardown gets `__enter__`/`__exit__`.
- Cleanup must be best-effort (`check=False` in `__exit__`).

---

## Logging

```python
from rich.console import Console

console = Console()
console.log("[cyan]step 3[/]: dev install")
console.print("[red]error[/]: lint failed")
```

**Rules:**
- Use `rich.console.Console`, never `print()` in library code.
- CLI is allowed `console.print`; agents should `console.log` (timestamped).

---

## Errors

```python
class SendSprintError(Exception):
    """Base exception."""

class TransportError(SendSprintError):
    """Operator transport failure."""

class WorktreeError(SendSprintError):
    """git worktree command failed."""
```

**Rules:**
- All custom exceptions inherit from `SendSprintError`.
- Never `raise Exception(...)`. Always a typed subclass.
- Catch specifically: `except TransportError:` not `except Exception:` (except top-level `cli.py`).

---

## Tests

```python
import pytest
from sendsprint.operators import JiraOperator

def test_jira_operator_falls_back_to_api(monkeypatch, httpx_mock):
    monkeypatch.setattr("sendsprint.operators.jira_operator._mcp_available", lambda: False)
    httpx_mock.add_response(json={"values": [...]})
    sprint = JiraOperator(transport="auto").read(sprint_id=42)
    assert sprint.id == "42"
```

**Rules:**
- pytest, not unittest.
- Use `monkeypatch` for env/config; `pytest-httpx` for HTTP; `tmp_path` for filesystem.
- Never `time.sleep` — use `pytest-freezegun` or `monkeypatch.setattr(time, "sleep", lambda _: None)`.
- One assertion concept per test (multiple asserts OK if same concept).

---

## Async

```python
import asyncio

async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        return await asyncio.gather(*(client.get(u) for u in urls))
```

**Rules:**
- Async only when measured concurrency benefit (multi-repo, multi-API).
- Never mix sync subprocess with async HTTP in same function.

---

## Type hints

```python
from typing import Literal
from pathlib import Path

def detect_tech(repo: Path) -> Literal["python", "node", "dotnet", "rust", "go", "unknown"]:
    ...
```

**Rules:**
- Type **everything** (params, returns, instance attrs).
- Use `Literal` for closed string sets, `TypeAlias` for complex unions.
- `from __future__ import annotations` lets you skip `typing.List` → use `list[X]`.

---

## DON'Ts

| Don't | Do instead |
|-------|------------|
| `requests` | `httpx` |
| `os.system`, `os.popen` | `subprocess.run(..., timeout=N, check=False)` |
| `os.path.*` | `pathlib.Path` |
| Pydantic v1 (`.dict()`, `.json()`) | `model_dump()`, `model_dump_json()` |
| `print()` in library code | `rich.console.Console.log()` |
| `raise Exception(...)` | `raise SendSprintError(...)` subclass |
| Auto-fix security findings | Halt + report (ADR-005) |
| Reorder transport chain | Fixed `mcp` → `api` → `playwright` (ADR-002) |
| `time.sleep` in tests | `monkeypatch` time |
| `subprocess.run(..., shell=True)` | List form `["cmd", "arg"]` |
| Untyped function signatures | Always annotate |

---

## See also

- [DESIGN.md](DESIGN.md) — system design
- [/.specs/product/DOMAIN.md](../product/DOMAIN.md) — entities
- [/AGENTS.md](../../AGENTS.md) — canonical instructions
- [ADR-001-stack.md](ADR-001-stack.md) — stack rationale
