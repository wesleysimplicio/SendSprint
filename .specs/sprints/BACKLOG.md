# Backlog — SendSprint

Lista priorizada de tudo que precisa ser feito no SendSprint. Fonte da verdade de pendências.

## Como usar este backlog

- Cada linha vira uma `task.md` ao entrar em sprint.
- Prioridades: **P0** (bloqueador), **P1** (próximas 1-2 sprints), **P2** (radar).
- Status: `todo`, `doing`, `done`.
- Ordenação: P0 → P1 → P2; dentro da mesma prioridade, por sprint alvo.

## Regras de manutenção

- Toda nova ideia entra como P2 até alguém defender priorizar.
- Itens `done` ficam no histórico por uma sprint, depois arquivados em `BACKLOG-archive.md`.
- Item parado 2 sprints como `todo` → reavalia ou remove.
- Quem altera prioridade ou move pra `doing` atualiza tabela no mesmo PR.

## Backlog atual

| #   | Título                                                               | Prioridade | Sprint alvo | Status |
| --- | -------------------------------------------------------------------- | ---------- | ----------- | ------ |
| 1   | Adopt agentic-starter pipeline (specs, skills, dod, ralph)           | P0         | sprint-1    | done   |
| 2   | Validate Ralph autonomous loop against sprint-1 tasks                | P0         | sprint-1    | doing  |
| 3   | LLM-powered code generation per sprint item                          | P1         | sprint-2    | done   |
| 4   | Deploy trigger + status callback to Jira/ADO ticket                  | P1         | sprint-2    | done   |
| 5   | MCP server mode (expose SendSprint as MCP tool)                      | P1         | sprint-3    | done   |
| 6   | Add Bun/Deno detectors to `tech/detector.py`                         | P2         | sprint-3    | done   |
| 7   | Coverage badge + CHANGELOG automation in CI                          | P2         | sprint-4    | doing  |
| 8   | Telemetry (opt-in) for step duration histograms                      | P2         | backlog     | done   |

## Histórico recente (últimos done)

| #   | Título                                                       | Sprint     | Concluído em |
| --- | ------------------------------------------------------------ | ---------- | ------------ |
| 8   | Telemetry (opt-in) for step duration histograms              | backlog    | 2026-05-18   |
| 6   | Add Bun/Deno detectors to `tech/detector.py`                 | sprint-3   | 2026-05-18   |
| 5   | MCP server mode (expose SendSprint as MCP tool)              | sprint-3   | 2026-05-18   |
| 4   | Deploy trigger + status callback to Jira/ADO ticket          | sprint-2   | 2026-05-18   |
| 3   | LLM-powered code generation per sprint item                  | sprint-2   | 2026-05-18   |
| 1   | Adopt agentic-starter pipeline (specs, skills, dod, ralph)  | sprint-1   | 2026-05-18   |
| 0   | v0.4.0 — chat-trigger UX + 8 IDE manifests + OS-keyring     | sprint-0   | 2026-05-07   |

## Itens descartados ou movidos pra fora

- Nenhum item descartado ainda.

## Próximas decisões pendentes

- Validar `ralph run --max-iterations 5` fim a fim para item #2 sem depender de serviços externos.
- Completar a automação do badge de coverage no item #7 e expor o SVG no README.
