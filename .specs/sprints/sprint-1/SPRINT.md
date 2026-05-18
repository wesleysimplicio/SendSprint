---
sprint: sprint-1
status: doing
start: 2026-05-08
end: 2026-05-22
owner: @sendsprint-core
---

# Sprint 1 — Agentic-starter pipeline + Ralph Wiggum / Codex goal validation

## Objetivo

Adotar o padrão `agentic-starter` no SendSprint (specs/sprints, skills, DoD gate) e validar o loop autônomo via skill Ralph Wiggum do Claude Code e via `/goal` do Codex contra um repo host real, começando por `wesleysimplicio/llm-project-mapper`, sem depender de Jira/ADO. Resultado: contribuidores e agents seguem um único contrato e o experimento de loop autônomo fica reproduzível no repo alvo certo.

## Datas

- **Início:** 2026-05-08
- **Fim previsto:** 2026-05-22
- **Demo/review:** 2026-05-21
- **Retrospectiva:** 2026-05-22

## Deliverables

A sprint só fecha como `done` quando os 4 entregáveis estão cumpridos:

1. **`.specs/sprints/` ativo** — `task-template.md`, `BACKLOG.md` e `sprint-1/SPRINT.md` em uso. Toda task nova obrigatoriamente segue o template.
2. **DoD gate** — `.github/workflows/dod.yml` adaptado para Python (ruff + pytest + coverage ≥ 80% + checagem de referência a task) bloqueia merge.
3. **Loop autônomo documentado corretamente** — a sprint deixa explícito que a validação usa a skill Ralph Wiggum do Claude Code e o `/goal` do Codex, tendo `llm-project-mapper` como repo piloto do experimento.
4. **2 tasks pilotos verdes** — `01-add-bun-detector.task.md` e `02-add-cargo-audit-tests.task.md` saem de `todo` para `done` com tests + cobertura + PR, enquanto o item aberto restante fica restrito à validação do loop no repo alvo.

## Tasks da sprint

| Arquivo                                       | Status | Owner                  |
| --------------------------------------------- | ------ | ---------------------- |
| `01-add-bun-detector.task.md`                 | done   | @sendsprint-core       |
| `02-add-cargo-audit-tests.task.md`            | done   | @sendsprint-core       |

## Riscos

- **O loop autônomo pode entrar em iteração improdutiva** se não reconhecer DoD verde. Mitigação: limite explícito de iterações (`--max-iterations 5` no Ralph Wiggum skill / goal equivalente) + revisão manual antes de merge.
- **Cobertura ≥ 80%** pode quebrar PRs antigos. Mitigação: aplicar gate só em arquivos do diff (não no total).
- **A validação depende do host agent correto** (Claude Code com Ralph Wiggum skill ou Codex com `/goal`). Mitigação: documentar o comando/skill e o repo piloto em um playbook dedicado.

## Dependências

- Claude Code com a skill Ralph Wiggum disponível.
- Codex CLI com `/goal` habilitado.
- `wesleysimplicio/llm-project-mapper` disponível como repo piloto do experimento.
- `pytest`, `pytest-cov`, `ruff` no `[dev]` extras de `pyproject.toml`.
- ADR a abrir se `dod.yml` mudar contrato com PRs já abertos.

## Critérios de pronto da sprint

- [x] As 2 tasks com status `done` no `BACKLOG.md`.
- [ ] CI verde nos PRs de ambas as tasks.
- [ ] A skill Ralph Wiggum do Claude Code ou o `/goal` do Codex completam o piloto no `llm-project-mapper`, ou deixam evidência objetiva do bloqueio no repo alvo.
- [ ] Demo registrada em `presentation/` (opcional).
- [ ] Retrospectiva preenchida ao fim.

## Notas de retrospectiva (preencher no fim)

- O que funcionou bem:
- O que travou:
- O que mudar na sprint-2:
