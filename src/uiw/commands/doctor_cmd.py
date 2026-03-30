from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.constants import WORKSPACES_REGISTRY_NAME
from uiw.ops.doctor_ops import run_doctor
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ui.console import console
from uiw.ui.tables import build_doctor_table


def doctor_command(config: Path | None = None) -> None:
    loaded = load_config(config)
    registry = WorkspaceRegistry(loaded.paths.config_root / WORKSPACES_REGISTRY_NAME)
    console.print(build_doctor_table(run_doctor(loaded, registry)))


def register(app: typer.Typer) -> None:
    app.command("doctor")(doctor_command)
