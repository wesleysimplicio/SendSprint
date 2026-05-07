# SendSprint - Openclaw Skill

Skill manifest for the Openclaw agent runtime. Drop the `sendsprint`
package into the runtime's Python path and Openclaw will surface it on
prompts that match the trigger list below.

## Trigger

- pt-BR: "ler sprint", "rodar sprint", "executar sprint", "iniciar entrega da sprint"
- en: "send sprint", "sprint flow", "deliver sprint", "read sprint"
- es: "ejecutar sprint", "leer sprint"

## Steps

1. **Read sprint** - pick the operator from the source the user names.
   - Jira -> `sendsprint.operators.JiraOperator(transport="auto").read_sprint(sprint_id=...)`
   - Azure DevOps -> `sendsprint.operators.AzureDevopsOperator(transport="auto").read_sprint(iteration_path=...)`
   - Transport priority: `mcp` -> `api` -> `playwright` (CDP at `PLAYWRIGHT_CDP_URL`).
   - Capture every Story, Task, Subtask, Bug, Epic, Feature, Issue with full
     metadata (key, type, title, description, status, assignee, story points,
     parent, labels, comments, links, attachments, acceptance criteria, URL).

2. **Architecture mapping** - per repo touched by the sprint:
   - `sendsprint.architecture.ArchitectureMapper().inspect(repo_path)`
   - Fail when `score < 0.6` and surface the missing artifacts list:
     `ARCHITECTURE.md`, `docs/architecture/`, `docs/c4/`, `docs/adr/`,
     dependency graph, deploy topology, README.

## CLI

```bash
sendsprint read-jira 1234
sendsprint read-ado "Team\\Sprint 12"
sendsprint check-architecture ./path/to/repo
sendsprint run jira 1234 --repo-path ./path/to/repo
```

## Required env

`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`,
`AZURE_DEVOPS_ORG`, `AZURE_DEVOPS_PROJECT`, `AZURE_DEVOPS_PAT`,
`PLAYWRIGHT_CDP_URL` (default `http://127.0.0.1:9222`),
`LLM_PROVIDER`, `LLM_MODEL`, provider key.
