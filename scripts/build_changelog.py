"""Build a CHANGELOG `[Unreleased]` block from Conventional Commits.

Usage:
    python scripts/build_changelog.py --since vX.Y.Z
    python scripts/build_changelog.py --since vX.Y.Z --promote 0.13.0
    python scripts/build_changelog.py --commits-file <file>  # offline / tests

The promote mode rewrites `CHANGELOG.md` in place, moving the current
``[Unreleased]`` section to ``[X.Y.Z] - YYYY-MM-DD``. Without ``--promote``
the script prints the markdown block to stdout (suitable for CI snippets).

Implements Sprint-4 issue #13 (Coverage badge + CHANGELOG automation).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path

COMMIT_RE = re.compile(
    r"^(?P<type>feat|fix|chore|docs|refactor|test|perf|style|ci|build|revert)"
    r"(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<subject>.+)$"
)

GROUP_ORDER: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Added", ("feat",)),
    ("Fixed", ("fix",)),
    ("Changed", ("refactor", "perf", "style")),
    ("Tests", ("test",)),
    ("Docs", ("docs",)),
    ("CI", ("ci", "build")),
    ("Chore", ("chore", "revert")),
    ("Other", ()),
)


def _git_commits_since(ref: str | None) -> list[str]:
    cmd = ["git", "log", "--pretty=%s", "--no-merges"]
    if ref:
        cmd.append(f"{ref}..HEAD")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def parse_commit(subject: str) -> tuple[str, str, str, bool] | None:
    """Parse a Conventional Commit subject. Returns (type, scope, subject, breaking)."""
    match = COMMIT_RE.match(subject.strip())
    if not match:
        return None
    return (
        match.group("type"),
        match.group("scope") or "",
        match.group("subject"),
        bool(match.group("breaking")),
    )


def group_commits(commits: Iterable[str]) -> dict[str, list[str]]:
    """Bucket commits by changelog group, preserving order."""
    groups: dict[str, list[str]] = {label: [] for label, _ in GROUP_ORDER}
    for raw in commits:
        parsed = parse_commit(raw)
        if parsed is None:
            groups["Other"].append(raw)
            continue
        ctype, scope, subject, breaking = parsed
        bucket = next(
            (label for label, types in GROUP_ORDER if types and ctype in types),
            "Other",
        )
        marker = " (BREAKING)" if breaking else ""
        line = f"{scope}: {subject}" if scope else subject
        groups[bucket].append(f"{line}{marker}")
    return groups


def render_block(groups: dict[str, list[str]], *, heading: str = "## [Unreleased]") -> str:
    """Render a CHANGELOG markdown block. Empty groups are omitted."""
    lines: list[str] = [heading, ""]
    for label, _types in GROUP_ORDER:
        items = groups.get(label) or []
        if not items:
            continue
        lines.append(f"### {label}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    if lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def promote_unreleased(changelog: Path, version: str, today: date | None = None) -> str:
    """Rename the `[Unreleased]` heading to `[version] - YYYY-MM-DD`.

    Returns the new content. Idempotent: if no `[Unreleased]` is present,
    returns the file unchanged.
    """
    text = changelog.read_text(encoding="utf-8")
    stamp = (today or date.today()).isoformat()
    pattern = re.compile(r"^## \[Unreleased\]\s*$", flags=re.MULTILINE)
    new_text, count = pattern.subn(f"## [{version}] - {stamp}", text, count=1)
    if count == 0:
        return text
    return new_text


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--since",
        help="Git ref to collect commits from (e.g. v0.11.0). Defaults to last tag.",
    )
    parser.add_argument(
        "--commits-file",
        type=Path,
        help="Read commit subjects from this file (one per line). Skips git log.",
    )
    parser.add_argument(
        "--promote",
        metavar="VERSION",
        help="Rewrite CHANGELOG.md: rename [Unreleased] → [VERSION] - YYYY-MM-DD.",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Path to CHANGELOG.md (default: ./CHANGELOG.md).",
    )
    args = parser.parse_args(argv)

    if args.promote:
        new = promote_unreleased(args.changelog, args.promote)
        args.changelog.write_text(new, encoding="utf-8")
        return 0

    if args.commits_file:
        commits = [
            line for line in args.commits_file.read_text(encoding="utf-8").splitlines() if line
        ]
    else:
        commits = _git_commits_since(args.since)

    block = render_block(group_commits(commits))
    sys.stdout.write(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
