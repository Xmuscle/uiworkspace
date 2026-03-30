from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.workspace_ops import remove_workspace
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import print_success


def remove_command(
    name: str,
    keep_branch: bool = False,
    config: Path | None = None,
) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    result = remove_workspace(loaded, registry, name, keep_branch=keep_branch)
    print_success(f"Removed workspace {name} ({result['path']})")


def register(app: typer.Typer) -> None:
    app.command("remove")(remove_command)
