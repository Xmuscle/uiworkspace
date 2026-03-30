from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.apply_ops import apply_plan_to_svn, build_apply_plan
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import console, print_success


def apply_command(name: str, config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    plan = build_apply_plan(loaded, registry, name)
    result = apply_plan_to_svn(loaded, plan)
    print_success("Apply completed")
    console.print({
        "modified": result["modified"],
        "added": result["added"],
        "deleted": result["deleted"],
        "backup_dir": str(result["backup_dir"]) if result["backup_dir"] else None,
        "log_path": str(result["log_path"]),
        "next_steps": ["svn status", "svn diff", "svn commit"],
    })


def register(app: typer.Typer) -> None:
    app.command("apply")(apply_command)
