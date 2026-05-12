"""Tests for SprintImporter — materializes sprint items as task specs."""

from __future__ import annotations

from pathlib import Path

from sendsprint.agents.sprint_importer import SprintImporter, _slugify, _sprint_dir_name
from sendsprint.models import Sprint, SprintItem


def _make_sprint(items: list[SprintItem] | None = None) -> Sprint:
    return Sprint(
        id="42",
        name="Demo Sprint",
        state="active",
        source="jira",
        items=items or [],
    )


def _make_item(key: str = "PROJ-1", **kw) -> SprintItem:
    defaults = dict(
        id=key,
        key=key,
        type="Task",
        title="Sample task",
        status="To Do",
    )
    defaults.update(kw)
    return SprintItem(**defaults)


def test_slugify_strips_unsafe_chars():
    assert _slugify("Hello World!") == "hello-world"
    assert _slugify("PROJ-123 / fix bug") == "proj-123-fix-bug"
    assert _slugify("") == "task"


def test_sprint_dir_name_uses_id():
    s = _make_sprint()
    assert _sprint_dir_name(s) == "sprint-42"


def test_import_writes_task_and_sprint_md(tmp_path: Path):
    sprint = _make_sprint([_make_item("PROJ-1"), _make_item("PROJ-2", type="Bug")])
    importer = SprintImporter(tmp_path)
    step = importer.import_sprint(sprint)

    assert step.status == "ok"
    sprint_dir = tmp_path / ".specs" / "sprints" / "sprint-42"
    assert (sprint_dir / "proj-1.task.md").exists()
    assert (sprint_dir / "proj-2.task.md").exists()
    assert (sprint_dir / "SPRINT.md").exists()


def test_import_is_idempotent_skips_existing(tmp_path: Path):
    sprint = _make_sprint([_make_item("PROJ-1")])
    importer = SprintImporter(tmp_path)
    importer.import_sprint(sprint)

    task_path = tmp_path / ".specs" / "sprints" / "sprint-42" / "proj-1.task.md"
    task_path.write_text("USER EDITS", encoding="utf-8")

    step = importer.import_sprint(sprint)
    assert step.status == "ok"
    assert "skipped 1 existing" in (step.message or "")
    assert task_path.read_text(encoding="utf-8") == "USER EDITS"


def test_task_content_includes_ac_and_links(tmp_path: Path):
    item = _make_item(
        "PROJ-7",
        title="Add deno detector",
        description="Detect deno via deno.json",
        acceptance_criteria="must detect deno.json\nmust return tech=deno",
        source_url="https://jira.example/PROJ-7",
        labels=["tech", "detector"],
    )
    sprint = _make_sprint([item])
    SprintImporter(tmp_path).import_sprint(sprint)

    content = (tmp_path / ".specs" / "sprints" / "sprint-42" / "proj-7.task.md").read_text(
        encoding="utf-8"
    )

    assert "PROJ-7" in content
    assert "Add deno detector" in content
    assert "AC-1 — must detect deno.json" in content
    assert "AC-2 — must return tech=deno" in content
    assert "https://jira.example/PROJ-7" in content
    assert "tech, detector" in content


def test_empty_ac_falls_back_to_placeholder(tmp_path: Path):
    sprint = _make_sprint([_make_item("PROJ-9", acceptance_criteria=None)])
    SprintImporter(tmp_path).import_sprint(sprint)
    content = (tmp_path / ".specs" / "sprints" / "sprint-42" / "proj-9.task.md").read_text(
        encoding="utf-8"
    )
    assert "AC-1 — define per requirement" in content


def test_import_failed_status_on_write_error(tmp_path: Path, monkeypatch):
    sprint = _make_sprint([_make_item("PROJ-1")])
    importer = SprintImporter(tmp_path)

    def boom(*a, **kw):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", boom)
    step = importer.import_sprint(sprint)
    assert step.status == "failed"
    assert "disk full" in (step.message or "")
