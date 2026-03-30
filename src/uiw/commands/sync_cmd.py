from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.ops.sync_ops import sync_svn_to_git
from uiw.ui.console import console, print_success


def sync_command(message: str | None = None, config: Path | None = None) -> None:
    loaded = load_config(config)
    result = sync_svn_to_git(loaded, message)
    print_success("Sync completed")
    console.print(result)


def register(app: typer.Typer) -> None:
    app.command("sync")(sync_command)
