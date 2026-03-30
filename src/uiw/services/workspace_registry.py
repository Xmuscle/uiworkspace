from __future__ import annotations

from pathlib import Path

from uiw.errors import RegistryError, WorkspaceNotFoundError
from uiw.infra.yaml_io import load_yaml, save_yaml
from uiw.models import WorkspaceMeta


class WorkspaceRegistry:
    def __init__(self, registry_path: Path) -> None:
        self.registry_path = registry_path

    def load(self) -> dict[str, WorkspaceMeta]:
        data = load_yaml(self.registry_path)
        items = data.get("workspaces", {})
        return {name: workspace_meta_from_dict(name, item) for name, item in items.items()}

    def save(self, items: dict[str, WorkspaceMeta]) -> None:
        payload = {
            "workspaces": {
                name: workspace_meta_to_dict(meta) for name, meta in sorted(items.items())
            }
        }
        save_yaml(self.registry_path, payload)

    def list_workspaces(self) -> list[WorkspaceMeta]:
        return list(self.load().values())

    def get(self, name: str) -> WorkspaceMeta:
        items = self.load()
        if name not in items:
            raise WorkspaceNotFoundError(f"Workspace not found: {name}")
        return items[name]

    def exists(self, name: str) -> bool:
        return name in self.load()

    def add(self, meta: WorkspaceMeta) -> None:
        items = self.load()
        if meta.name in items:
            raise RegistryError(f"Workspace already registered: {meta.name}")
        items[meta.name] = meta
        self.save(items)

    def remove(self, name: str) -> None:
        items = self.load()
        if name not in items:
            raise WorkspaceNotFoundError(f"Workspace not found: {name}")
        del items[name]
        self.save(items)

    def update(self, meta: WorkspaceMeta) -> None:
        items = self.load()
        items[meta.name] = meta
        self.save(items)


def workspace_meta_to_dict(meta: WorkspaceMeta) -> dict:
    return {
        "branch": meta.branch,
        "path": meta.path.as_posix(),
        "from_branch": meta.from_branch,
        "created_at": meta.created_at,
    }


def workspace_meta_from_dict(name: str, data: dict) -> WorkspaceMeta:
    return WorkspaceMeta(
        name=name,
        branch=data["branch"],
        path=Path(data["path"]),
        from_branch=data["from_branch"],
        created_at=data["created_at"],
    )
