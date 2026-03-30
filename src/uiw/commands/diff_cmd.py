from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.diff_ops import get_workspace_diff
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import console


def diff_command(
    name: str,
    name_only: bool = False,
    stat: bool = False,
    config: Path | None = None,
) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    mode = "name-only" if name_only else "stat" if stat else "compact"
    console.print(get_workspace_diff(loaded, registry, name, mode=mode))


def register(app: typer.Typer) -> None:
    app.command("diff")(diff_command)
