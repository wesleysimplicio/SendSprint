# C4 Level 2 - Containers

SendSprint is shipped as a Python package with a Typer CLI, optional FastAPI
backend, React Native Web dashboard, and local execution/evidence storage.

```mermaid
flowchart TB
  Operator["Human operator"]

  subgraph Local["Local workstation or CI runner"]
    CLI["CLI container\nTyper commands"]
    API["API container\nFastAPI run/status/events"]
    Web["Dashboard container\nReact Native Web"]
    Core["Orchestration core\nSprintFlow + agents"]
    State["Run state store\n.sendsprint/runs"]
    Evidence["Evidence bundles\nlogs, traces, reports"]
    Worktrees["Git worktrees\nisolated task execution"]
  end

  subgraph External["External systems"]
    GitHub["GitHub CLI/API\nIssues, PRs, Actions"]
    Trackers["Tracker APIs\nJira, Azure DevOps"]
    PackageIndex["PyPI\nsendsprint package"]
    LLM["Optional LLM APIs"]
  end

  Operator --> CLI
  Operator --> Web
  Web --> API
  CLI --> Core
  API --> Core
  Core --> State
  Core --> Evidence
  Core --> Worktrees
  Core --> GitHub
  Core --> Trackers
  Core --> LLM
  GitHub --> PackageIndex
```

## Container Notes

- CLI is the primary operator entry point and owns command-line policy switches.
- API and dashboard expose the same run/report surface without creating a second domain model.
- Core orchestration owns planning, worktree isolation, validation, PR creation, and reporting.
- Local state and evidence are plain files so failed runs remain inspectable.
- Publishing is delegated to GitHub Actions and PyPI, not direct runtime code.
