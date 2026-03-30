from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.workspace_ops import get_workspace_info
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import console


def info_command(name: str, config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    console.print(get_workspace_info(loaded, registry, name))


def register(app: typer.Typer) -> None:
    app.command("info")(info_command)
