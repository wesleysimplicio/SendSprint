"""SprintImporter: materializes sprint items as agentic-starter task specs.

Writes one task file per SprintItem under `.specs/sprints/sprint-{id}/<key>.task.md`,
following the layout in `.specs/sprints/task-template.md`. Enables Ralph loop +
DoD gate to operate per item with full context.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path

from sendsprint.models import Sprint, SprintItem
from sendsprint.models.reports import StepReport

logger = logging.getLogger(__name__)


def _slugify(value: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return s[:max_len] or "task"


def _sprint_dir_name(sprint: Sprint) -> str:
    raw = sprint.id or sprint.name or "current"
    return f"sprint-{_slugify(str(raw), 40)}"


def _ac_lines(item: SprintItem) -> list[str]:
    if not item.acceptance_criteria:
        return ["- [ ] AC-1 — define per requirement (no AC found in source)"]
    lines: list[str] = []
    for idx, raw in enumerate(item.acceptance_criteria.splitlines(), start=1):
        line = raw.strip(" -*•\t")
        if not line:
            continue
        lines.append(f"- [ ] AC-{idx} — {line}")
    return lines or ["- [ ] AC-1 — define per requirement"]


def _render_task(item: SprintItem, sprint: Sprint, sprint_slug: str) -> str:
    title = item.title.strip().replace("\n", " ")
    owner = item.assignee or "@unassigned"
    description = (item.description or "N/A").strip()
    ac_block = "\n".join(_ac_lines(item))
    labels = ", ".join(item.labels) if item.labels else "none"
    parent = item.parent_key or "none"
    source_url = item.source_url or "n/a"
    points = item.story_points if item.story_points is not None else "n/a"

    return f"""---
id: {item.key}
title: {title}
sprint: {sprint_slug}
owner: {owner}
status: todo
source: {sprint.source}
type: {item.type}
parent: {parent}
labels: [{labels}]
imported_at: {datetime.now(UTC).isoformat()}
---

# {item.key} — {title}

> Auto-imported by SendSprint from {sprint.source} sprint `{sprint.name}`.

## Contexto

{description}

- Origem: {sprint.source} `{sprint.name}` ({sprint.id})
- Tipo: {item.type}
- Status remoto: {item.status}
- Story points: {points}
- Link: {source_url}

## Acceptance Criteria

{ac_block}

## Out of scope

- Mudanças fora do escopo descrito em Contexto.
- Refactors não justificados pelos ACs acima.

## Test plan

### Unit
- [ ] Cobrir caminho feliz dos ACs.
- [ ] Cobrir 1 erro/edge case.
- [ ] Coverage diff ≥ 80% nos arquivos alterados.

### Integration
- [ ] Validar contrato com dependências diretas.

### End-to-end (Playwright)
- [ ] Happy path com screenshot + trace + video em `test-results/`.
- [ ] Erro esperado (4xx/5xx, input inválido).

## Definition of Done

- [ ] Todos ACs marcados.
- [ ] Lint verde (stack-specific).
- [ ] Unit + E2E verde.
- [ ] Coverage diff ≥ 80%.
- [ ] PR aberta linkando esta task e item de origem.
- [ ] ADR aberta se decisão arquitetural.
- [ ] CHANGELOG atualizado se release-relevant.

## Links

- Sprint spec: `.specs/sprints/{sprint_slug}/SPRINT.md`
- Source item: {source_url}
- Parent: {parent}
"""


class SprintImporter:
    """Writes one task spec per sprint item under `.specs/sprints/sprint-<id>/`."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = Path(repo_root)

    def import_sprint(self, sprint: Sprint) -> StepReport:
        step = StepReport(
            step=2,
            name="import-sprint-specs",
            status="running",
            started_at=datetime.now(UTC),
        )
        sprint_slug = _sprint_dir_name(sprint)
        target_dir = self.repo_root / ".specs" / "sprints" / sprint_slug
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            created: list[str] = []
            skipped: list[str] = []
            for item in sprint.items:
                fname = f"{_slugify(item.key, 40)}.task.md"
                fpath = target_dir / fname
                if fpath.exists():
                    skipped.append(item.key)
                    continue
                fpath.write_text(_render_task(item, sprint, sprint_slug), encoding="utf-8")
                created.append(item.key)

            sprint_md = target_dir / "SPRINT.md"
            if not sprint_md.exists():
                sprint_md.write_text(self._render_sprint_md(sprint, sprint_slug), encoding="utf-8")

            step.status = "ok"
            step.message = (
                f"imported {len(created)} task(s) to "
                f"{target_dir.relative_to(self.repo_root)}"
                + (f"; skipped {len(skipped)} existing" if skipped else "")
            )
        except Exception as exc:  # noqa: BLE001
            step.status = "failed"
            step.message = f"sprint import failed: {exc}"
            logger.exception("SprintImporter.import_sprint failed")
        step.finished_at = datetime.now(UTC)
        return step

    def _render_sprint_md(self, sprint: Sprint, slug: str) -> str:
        items = (
            "\n".join(
                f"- [{i.key}]({_slugify(i.key, 40)}.task.md) — {i.title} ({i.type}, {i.status})"
                for i in sprint.items
            )
            or "- (no items)"
        )
        return f"""---
sprint: {slug}
name: {sprint.name}
source: {sprint.source}
state: {sprint.state}
start: {sprint.start_date.isoformat() if sprint.start_date else "n/a"}
end: {sprint.end_date.isoformat() if sprint.end_date else "n/a"}
---

# Sprint {sprint.name}

> Auto-imported by SendSprint.

## Goal

{sprint.goal or "N/A"}

## Items

{items}
"""
