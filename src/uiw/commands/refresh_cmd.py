from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.workspace_ops import abort_refresh, continue_refresh, refresh_workspace
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import console, print_success


def refresh_command(name: str, config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    result = refresh_workspace(loaded, registry, name)
    if result["conflicts"]:
        console.print({
            "message": "Conflict detected",
            "conflicts": result["conflicts"],
            "continue": f"uiw refresh-continue {name}",
            "abort": f"uiw refresh-abort {name}",
        })
        raise typer.Exit(code=1)
    print_success("Refresh completed")
    console.print(result)


def refresh_continue_command(name: str, config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    console.print(continue_refresh(loaded, registry, name))


def refresh_abort_command(name: str, config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    console.print(abort_refresh(loaded, registry, name))


def register(app: typer.Typer) -> None:
    app.command("refresh")(refresh_command)
    app.command("refresh-continue")(refresh_continue_command)
    app.command("refresh-abort")(refresh_abort_command)
