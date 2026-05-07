# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-05-07

### Added

- Initial scaffold: Python package, CLI (`sendsprint`), pyproject, requirements, MIT license.
- `BaseOperator` abstract class with `transport` resolver (mcp / api / playwright / auto).
- `JiraOperator` reads Stories, Tasks, Subtasks, Bugs, Epics, Features, Issues from a sprint via API or Playwright fallback.
- `AzureDevopsOperator` reads Work Items (Story/Task/Bug/Feature/Epic) from an iteration path via API or Playwright fallback.
- `ArchitectureMapper` verifies presence of `ARCHITECTURE.md`, `docs/architecture/*`, `C4`, ADRs, dependency graph, deploy topology in target repos.
- Pydantic models: `Sprint`, `SprintItem`, `Link`, `Comment`, `Attachment`, `ArchitectureReport`.
- Provider-agnostic `LlmClient` (Anthropic / OpenAI / Google / Groq / Ollama).
- `SprintFlow` orchestrator wiring Step 1 (read) -> Step 2 (architecture check).
- Multi-platform skill manifests under `skills/` for Claude, Codex, Hermes, Openclaw, GitHub Copilot.
- Pytest scaffolding with operator unit tests using monkeypatched HTTP layer.
