#!/usr/bin/env bash
# Claude Code PreToolUse hook for Bash matcher 'git commit*'.
# Runs fast unit tests + ruff check before allowing commit.
# Reads JSON from stdin: { tool_name, tool_input: { command } }
# Exits 0 to allow, prints JSON {decision:"block", reason:...} to stdout to block.

set -uo pipefail

PAYLOAD="$(cat)"

if command -v jq >/dev/null 2>&1; then
  CMD="$(echo "$PAYLOAD" | jq -r '.tool_input.command // empty')"
else
  CMD="$(echo "$PAYLOAD" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')"
fi

case "$CMD" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

case "$CMD" in
  *"--no-verify"*|*"git commit --amend"*|*"git commit -m \"Merge"*) exit 0 ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"
cd "$REPO_ROOT" || exit 0

if ! git diff --cached --name-only | grep -q '\.py$'; then
  exit 0
fi

FAILED=()

if command -v ruff >/dev/null 2>&1; then
  if ! ruff check . --output-format=concise >&2; then
    FAILED+=("ruff check")
  fi
fi

if command -v pytest >/dev/null 2>&1; then
  if ! pytest -m "not integration and not canary" -q --no-header --tb=line >&2; then
    FAILED+=("pytest unit tier")
  fi
fi

if [ "${#FAILED[@]}" -gt 0 ]; then
  REASON="pre-commit blocked: ${FAILED[*]} failed. Fix or bypass with --no-verify."
  printf '{"decision":"block","reason":%s}\n' "$(printf '%s' "$REASON" | jq -Rs . 2>/dev/null || printf '"%s"' "$REASON")"
  exit 0
fi

exit 0
