---
name: rtk-cli
description: Use RTK CLI (https://github.com/rtk-ai/rtk) to cut tokens during repo exploration and verbose validation — read/grep/find/git/pytest without losing signal.
trigger: any task with shell-heavy exploration, git status/diff/log, grep/find across files, or verbose CLI validation where summary output is enough.
---

## Why

`rtk` is a thin shell wrapper that produces compact, agent-friendly output for common commands. Cuts ~40-70% of tokens during inspection and validation without losing technical signal. Optional dependency — falls back to plain commands when absent.

## Steps

1. Detect `rtk` on PATH: `command -v rtk`.
2. Replace these patterns when present:

   | Plain | RTK |
   |---|---|
   | `cat <file>` | `rtk read <file>` |
   | `grep -r "x" .` | `rtk grep "x" .` |
   | `find . -name "*.py"` | `rtk find "*.py" .` |
   | `git status` | `rtk git status` |
   | `git diff` | `rtk git diff` |
   | `git log -n 10` | `rtk git log -n 10` |
   | `pytest -v` (smoke) | `rtk pytest` |
   | `npm test` (smoke) | `rtk npm test` |

3. If `rtk` is not installed, run the plain command — no blocking.

## Do NOT route through RTK

- Interactive prompts (`gh auth login`, REPLs, `python -i`).
- Streaming logs that must be preserved verbatim (uvicorn, docker logs --follow).
- Playwright runners — full trace/screenshot output is the artifact.
- `curl`/`httpx` where the response body itself is the evidence.
- Any command whose raw stdout is committed/uploaded as proof.

## Trigger examples

- "Map the repo" → `rtk find "*.py" .` + `rtk read sendsprint/__init__.py`.
- "What changed in the last commit?" → `rtk git diff HEAD~1`.
- "Find references to `AgentRegistry`" → `rtk grep "AgentRegistry" sendsprint/`.
- "Smoke-test the suite" → `rtk pytest`.

## DoD

- [ ] `command -v rtk` checked before invoking `rtk <cmd>`.
- [ ] Plain command used as fallback when `rtk` missing.
- [ ] No interactive/streaming/evidence command routed through RTK.
- [ ] Output is sufficient for next decision (not truncated past the signal).

## References

- RTK repo: https://github.com/rtk-ai/rtk
- AGENTS.md `## Shell token-smart (RTK CLI, optional)` section.
