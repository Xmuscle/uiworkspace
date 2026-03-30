from pathlib import Path

from uiw.models import WorkspaceMeta
from uiw.services.workspace_registry import WorkspaceRegistry


def test_registry_add_and_get(tmp_path: Path) -> None:
    registry = WorkspaceRegistry(tmp_path / "workspaces.yaml")
    meta = WorkspaceMeta(
        name="event-a",
        branch="event-a",
        path=tmp_path / "event-a",
        from_branch="main",
        created_at="2026-03-30T10:30:00",
    )
    registry.add(meta)
    loaded = registry.get("event-a")
    assert loaded.name == "event-a"
    assert loaded.branch == "event-a"
