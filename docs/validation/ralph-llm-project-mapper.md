# Ralph Validation Target — `llm-project-mapper`

This note explains how Sprint 1 validation should be interpreted for SendSprint.

## Canonical interpretation

When Sprint 1 says "Ralph", it refers to:

- the Ralph Wiggum skill in Claude Code (`/ralph-loop ...`)
- the equivalent `/goal ...` command in Codex

It does **not** mean the legacy standalone `ralph` binary as the primary proof surface.

## Canonical pilot repo

The target repo for the autonomous-loop validation is:

- `wesleysimplicio/llm-project-mapper`

The purpose of the experiment is to prove that SendSprint's task/spec contract is usable by an external host repo, not only by SendSprint itself.

## Evidence expected

At least one of these paths should be recorded before closing Sprint-1 validation issues:

1. Claude Code Ralph Wiggum skill completes the mapped pilot task flow in `llm-project-mapper`.
2. Codex `/goal` completes the mapped pilot task flow in `llm-project-mapper`.
3. The run stops with a concrete blocker and leaves enough evidence to diagnose the host/tooling gap.

## Non-goals

- Proving a self-hosted `ralph run` flow inside SendSprint only.
- Treating the old standalone `ralph` CLI as the sole acceptance path.
