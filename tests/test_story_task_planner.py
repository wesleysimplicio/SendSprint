"""Tests for User Story decomposition into front/back tasks."""

from sendsprint.agents.story_task_planner import (
    delivery_items,
    infer_item_scopes,
    item_matches_repo,
    normalize_azure_backlog_hierarchy,
    plan_story_tasks,
)
from sendsprint.models.sprint import Sprint, SprintItem
from sendsprint.models.workspace import RepoConfig, WorkspaceConfig


def _story() -> SprintItem:
    return SprintItem(
        id="179500",
        key="179500",
        type="Story",
        title="Criar filtro de Raiz ou CNPJ",
        status="New",
        description="Adicionar filtro na tela de envio de emails.",
    )


def _sprint(items: list[SprintItem]) -> Sprint:
    return Sprint(id="Sprint 29", name="Sprint 29", source="azuredevops", items=items)


def test_plan_story_tasks_creates_front_and_back_tasks_when_story_has_no_tasks() -> None:
    ws = WorkspaceConfig(
        root_path="/tmp",
        repos=[
            RepoConfig(name="api", path="api", role="api"),
            RepoConfig(name="web", path="web", role="front"),
        ],
    )

    sprint, report = plan_story_tasks(_sprint([_story()]), ws)

    generated = [item for item in sprint.items if "auto:generated" in item.labels]
    assert report.status == "ok"
    assert [item.key for item in generated] == ["179500-FRONT", "179500-BACK"]
    assert all(item.parent_key == "179500" for item in generated)
    assert all("SendSprint" not in (item.description or "") for item in generated)


def test_plan_story_tasks_skips_story_when_child_task_exists() -> None:
    child = SprintItem(
        id="1",
        key="1",
        type="Task",
        title="Front task",
        status="New",
        parent_key="179500",
    )

    sprint, report = plan_story_tasks(_sprint([_story(), child]))

    assert report.status == "skipped"
    assert sprint.items == [_story(), child]


def test_plan_story_tasks_normalizes_azure_issue_task_hierarchy() -> None:
    issue = SprintItem(
        id="179778",
        key="179778",
        type="Issue",
        title="Corrigir divergencia de backlog",
        status="New",
        source_url="https://dev.azure.com/org/project/_workitems/edit/179778",
    )
    child = SprintItem(
        id="179822",
        key="179822",
        type="Task",
        title="Front task",
        status="New",
        parent_key="179778",
    )

    sprint, report = plan_story_tasks(
        Sprint(id="Sprint 29", name="Sprint 29", source="azuredevops", items=[issue, child])
    )

    normalized = next(item for item in sprint.items if item.key == "179822")
    assert normalized.parent_key is None
    assert normalized.links[0].type == "Related"
    assert normalized.links[0].target_key == "179778"
    assert "normalized 1 invalid Azure hierarchy link(s)" in (report.message or "")


def test_normalize_azure_backlog_hierarchy_keeps_story_task_parent() -> None:
    child = SprintItem(
        id="1",
        key="1",
        type="Task",
        title="Front task",
        status="New",
        parent_key="179500",
    )

    sprint, normalized = normalize_azure_backlog_hierarchy(
        Sprint(id="Sprint 29", name="Sprint 29", source="azuredevops", items=[_story(), child])
    )

    assert normalized == 0
    assert sprint.items[1].parent_key == "179500"


def test_delivery_items_skips_parent_story_with_child_tasks() -> None:
    sprint, _ = plan_story_tasks(_sprint([_story()]))

    deliverable = delivery_items(sprint)

    assert [item.key for item in deliverable] == ["179500-FRONT", "179500-BACK"]


def test_item_matches_repo_routes_generated_tasks_by_scope() -> None:
    sprint, _ = plan_story_tasks(_sprint([_story()]))
    front = next(item for item in sprint.items if item.key.endswith("-FRONT"))
    back = next(item for item in sprint.items if item.key.endswith("-BACK"))

    assert item_matches_repo(front, "front") is True
    assert item_matches_repo(front, None) is True
    assert item_matches_repo(front, "api") is False
    assert item_matches_repo(back, "api") is True
    assert item_matches_repo(back, "front") is False


def test_item_matches_repo_infers_scope_from_text_when_label_missing() -> None:
    front = SprintItem(
        id="1",
        key="1",
        type="Task",
        title="Ajustar tela de aprovacao",
        status="New",
    )
    back = SprintItem(
        id="2",
        key="2",
        type="Task",
        title="Criar endpoint de politica",
        status="New",
    )

    assert infer_item_scopes(front) == {"front"}
    assert item_matches_repo(front, "front") is True
    assert item_matches_repo(front, "api") is False
    assert infer_item_scopes(back) == {"back"}
    assert item_matches_repo(back, "api") is True
    assert item_matches_repo(back, "front") is False
