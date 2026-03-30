from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.export_ops import export_workspace_patch
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import print_success


def export_command(name: str, config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    path = export_workspace_patch(loaded, registry, name)
    print_success(f"Patch exported to {path}")


def register(app: typer.Typer) -> None:
    app.command("export")(export_command)
