# C4 Level 1 - System Context

SendSprint coordinates sprint delivery work for a human operator. It reads
tracker items, plans repository work, executes validation, captures evidence,
and synchronizes GitHub pull requests, issues, releases, and package publishing.

```mermaid
flowchart LR
  Operator["Human operator\nProduct/engineering owner"]
  SendSprint["SendSprint\nSprint delivery operator"]
  GitHub["GitHub\nRepos, Issues, PRs, Actions, Releases"]
  Trackers["Jira / Azure DevOps\nSprint and iteration sources"]
  TargetRepos["Target repositories\nCode, tests, docs, changelog"]
  PyPI["PyPI\nPython package distribution"]
  LLMs["Optional LLM providers\nOpenAI, Anthropic, Gemini, Groq, Ollama"]
  Evidence["Local evidence store\nReports, traces, logs, bundles"]

  Operator -->|"configures scope, autonomy, commands"| SendSprint
  SendSprint -->|"reads work items"| Trackers
  SendSprint -->|"reads and modifies with policy gates"| TargetRepos
  SendSprint -->|"creates issues, PRs, release metadata"| GitHub
  GitHub -->|"Actions publish release artifacts"| PyPI
  SendSprint -->|"optional code generation"| LLMs
  SendSprint -->|"writes auditable output"| Evidence
  Operator -->|"reviews evidence and PRs"| GitHub
  Operator -->|"reviews reports"| Evidence
```

## Responsibilities

- Keep dry-run and planning paths side-effect free.
- Gate write, commit, push, PR, release, and deploy actions by autonomy policy.
- Preserve a human-reviewable evidence trail for each run.
- Treat external systems as replaceable adapters instead of core domain logic.
