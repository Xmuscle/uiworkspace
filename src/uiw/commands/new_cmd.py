from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.workspace_ops import create_workspace
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import print_success


def new_command(name: str, from_branch: str | None = None, config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    meta = create_workspace(loaded, registry, name, from_branch)
    print_success(f"Created workspace {meta.name} at {meta.path}")


def register(app: typer.Typer) -> None:
    app.command("new")(new_command)
