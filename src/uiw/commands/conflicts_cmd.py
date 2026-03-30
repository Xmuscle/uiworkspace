from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.workspace_ops import get_workspace_conflicts
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import console
from uiw.ui.tables import build_conflicts_table


def conflicts_command(name: str, config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    conflicts = get_workspace_conflicts(loaded, registry, name)
    if conflicts:
        console.print(build_conflicts_table(conflicts))
    else:
        console.print("No unresolved conflicts.")


def register(app: typer.Typer) -> None:
    app.command("conflicts")(conflicts_command)
