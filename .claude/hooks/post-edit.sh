#!/usr/bin/env bash
# Claude Code PostToolUse hook for Edit/Write.
# Auto-formats .py files with ruff and shows quick lint summary.
# Reads JSON from stdin: { tool_name, tool_input: { file_path }, tool_response: { success } }
# Exits 0 always (non-blocking). Logs to stderr.

set -uo pipefail

PAYLOAD="$(cat)"

if command -v jq >/dev/null 2>&1; then
  FILE="$(echo "$PAYLOAD" | jq -r '.tool_input.file_path // empty')"
  SUCCESS="$(echo "$PAYLOAD" | jq -r '.tool_response.success // empty')"
else
  FILE="$(echo "$PAYLOAD" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)"/\1/')"
  SUCCESS="true"
fi

[[ -z "$FILE" ]] && exit 0
[[ "$FILE" != *.py ]] && exit 0
[[ "$SUCCESS" == "false" ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

case "$FILE" in
  */.venv/*|*/venv/*|*/node_modules/*|*/dist/*|*/build/*|*/.tox/*) exit 0 ;;
esac

if command -v ruff >/dev/null 2>&1; then
  ruff format "$FILE" >&2 2>&1 || true
  ruff check "$FILE" --output-format=concise >&2 2>&1 || true
else
  echo "post-edit: ruff not installed; skipping format for $FILE" >&2
fi

exit 0
