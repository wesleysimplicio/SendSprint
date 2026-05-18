# C4 Level 3 - Python Package Components

This view maps the main `sendsprint/` package responsibilities to the delivery
flow used by CLI, API, dashboard, tests, and evidence generation.

```mermaid
flowchart TD
  CLI["cli.py\nTyper commands"]
  APIRoutes["api/routes.py\nHTTP endpoints"]
  APIRuns["api/runs.py\nrun registry + SSE"]
  Flow["flow/sprint_flow.py\norchestration"]
  Policy["policy.py\nautonomy gates"]
  Planning["planning.py\nDeliveryPlan"]
  Scope["scope.py\nitem filtering"]
  Loops["loops.py\nRalph / Goal contracts"]
  Templates["templates.py\nstack validation recipes"]
  Doctor["doctor.py\nreadiness checks"]
  Evidence["evidence.py\nartifact bundle"]
  Reports["reports/executive.py\nexecutive summaries"]
  Control["control_plane.py\nmulti-agent ownership"]
  Transcripts["ingest/transcripts.py\nmeeting task extraction"]
  Models["models/*.py\nshared contracts"]
  Trackers["operators/* + trackers/github_issues.py\nwork item sources"]
  Agents["agents/*\ndev, lint, tests, security, PR"]
  Tech["tech/detector.py\nstack detection"]
  Arch["architecture/*\nproject mapping"]
  State["run_state.py\nresume/progress"]

  CLI --> Flow
  CLI --> Doctor
  CLI --> Evidence
  CLI --> Reports
  CLI --> Transcripts
  CLI --> Templates
  APIRoutes --> APIRuns
  APIRoutes --> Flow
  Flow --> Policy
  Flow --> Planning
  Flow --> Scope
  Flow --> Loops
  Flow --> Models
  Flow --> Trackers
  Flow --> Agents
  Flow --> Evidence
  Flow --> Control
  Flow --> State
  Planning --> Tech
  Planning --> Arch
  Doctor --> Templates
  Doctor --> Tech
  Doctor --> Arch
  Evidence --> Models
  Reports --> Models
  Transcripts --> Trackers
```

## Component Rules

- Pure planning, policy, transcript, template, and report modules should stay independent of Typer and FastAPI.
- Side-effect boundaries should stay mockable through adapters around `gh`, HTTP, subprocesses, and filesystem writes.
- Dashboard/API changes should extend `RunReport` and API schemas instead of creating one-off UI-only fields.
- New tracker sources should feed the same sprint item and delivery plan models used by Jira, Azure DevOps, and GitHub Issues.
