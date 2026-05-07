# ADR-004: Per-repo branch isolation via `git worktree`

| Field | Value |
|-------|-------|
| Status | Accepted |
| Date | 2026-04-04 |
| Deciders | wesley@beyondlabs |
| Supersedes | — |

---

## Context

A single sprint may touch **multiple repos** in a workspace (e.g., `backend-api`, `frontend-web`, `mobile-app`). For each repo, SendSprint must:

1. Create a sprint branch (`sprint/<id>`).
2. Run install + build + lint + tests + security scan.
3. Commit changes.
4. Push the branch.
5. Open a PR.

Doing this **in the working tree** of each repo would:
- Block the developer's current branch (forced checkout).
- Lose uncommitted local changes.
- Conflict with editor LSP/Watcher running in parallel.

Doing it in **a clone** would:
- Re-download the full repo per run (slow, disk-heavy).
- Skip access to local untracked config (e.g., `.env`, IDE settings).

---

## Decision

Use **`git worktree add`** to create an isolated working tree per repo per run, scoped via a context manager:

```python
class WorktreeManager:
    """Per-branch git worktree with auto-cleanup."""

    def __init__(self, repo: Path, branch: str) -> None:
        self._repo = repo
        self._branch = branch
        self._path: Path | None = None

    def __enter__(self) -> Path:
        self._path = Path(tempfile.mkdtemp(prefix=f"ss-wt-{self._branch}-"))
        subprocess.run(
            ["git", "worktree", "add", "-B", self._branch, str(self._path), "HEAD"],
            cwd=self._repo, check=True, timeout=60, capture_output=True, text=True,
        )
        return self._path

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._path is None:
            return
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(self._path)],
            cwd=self._repo, check=False, timeout=30,
        )
        shutil.rmtree(self._path, ignore_errors=True)
```

Used as:

```python
with WorktreeManager(repo.path, branch=f"sprint/{sprint.id}") as wt:
    DevAgent(wt).install_and_build()
    LintRunner(wt).run()
    # ... commit, push from `wt`
```

---

## Consequences

### Positive
- **Parallel-safe**: each worktree has its own index + HEAD; multiple repos can run concurrently with zero contention.
- **Non-destructive**: developer's main checkout is untouched, including uncommitted work.
- **Fast**: `git worktree add` is O(1) regardless of repo size — shares object database.
- **Clean by design**: `__exit__` always removes the worktree, even on exception.

### Negative
- **Disk usage**: temporary worktrees live in `/tmp` until cleanup. A 1GB repo with 10 sprint branches = up to 10GB transient.
- **Submodule complexity**: worktrees + submodules need `git worktree add --recurse-submodules` (handled in v0.2.x).
- **Hooks may misfire**: pre-commit hooks tied to the main checkout path may not see worktree paths correctly. Document workaround.

---

## Alternatives considered

| Approach | Rejected because |
|----------|------------------|
| `git stash` + `git checkout` in main tree | Loses uncommitted work; serial only |
| Fresh `git clone` per run | Slow (full transfer), disk-heavy, loses local config |
| In-memory git (libgit2 / pygit2) | No subprocess access (npm/pip/cargo can't see `.git`) |
| Docker volumes per repo | Adds Docker dependency, slower startup |
| Symlink farm | Race conditions on shared `.git/index` |

---

## See also

- [DESIGN.md](DESIGN.md) — concurrency
- [PATTERNS.md](PATTERNS.md) — context manager idiom
- [/.specs/product/DOMAIN.md](../product/DOMAIN.md) — invariant 2
- [/AGENTS.md](../../AGENTS.md)
