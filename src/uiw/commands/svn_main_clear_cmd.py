from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.loader import load_config
from uiw.ops.svn_clear_ops import clear_svn_main
from uiw.ui.console import console, print_success


def svn_main_clear_command(config: Path | None = None) -> None:
    loaded = load_config(config)
    result = clear_svn_main(loaded)
    print_success("svn-main clear completed")
    console.print(
        {
            "apply_log": str(result["apply_log"]),
            "restored_modified": result["restored_modified"],
            "removed_added": result["removed_added"],
            "restored_deleted": result["restored_deleted"],
            "clear_log": str(result["clear_log"]),
        }
    )


def register(app: typer.Typer) -> None:
    app.command("svn-main-clear")(svn_main_clear_command)
