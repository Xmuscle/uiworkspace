from __future__ import annotations

import typer

from uiw.errors import UIWError
from uiw.ui.console import print_error
from uiw.commands import (
    apply_cmd,
    conflicts_cmd,
    diff_cmd,
    doctor_cmd,
    export_cmd,
    info_cmd,
    init_cmd,
    list_cmd,
    new_cmd,
    refresh_cmd,
    remove_cmd,
    sync_cmd,
)

app = typer.Typer(help="UI Workspace CLI")


def register_commands() -> None:
    for module in [
        init_cmd,
        sync_cmd,
        new_cmd,
        list_cmd,
        info_cmd,
        refresh_cmd,
        conflicts_cmd,
        diff_cmd,
        export_cmd,
        apply_cmd,
        remove_cmd,
        doctor_cmd,
    ]:
        module.register(app)


register_commands()


def main() -> None:
    try:
        app()
    except UIWError as exc:
        print_error(exc.message)
        if exc.hint:
            print_error(exc.hint)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
