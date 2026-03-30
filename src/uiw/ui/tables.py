from __future__ import annotations

from rich.table import Table

from uiw.models import DoctorCheck, WorkspaceStatus
from uiw.ui.formatters import format_ahead_behind


def build_workspace_list_table(items: list[WorkspaceStatus]) -> Table:
    table = Table(title="Workspaces")
    table.add_column("Name")
    table.add_column("Branch")
    table.add_column("State")
    table.add_column("Ahead/Behind")
    table.add_column("Path")
    for item in items:
        table.add_row(item.name, item.branch, item.state, format_ahead_behind(item.ahead, item.behind), item.path.as_posix())
    return table


def build_doctor_table(checks: list[DoctorCheck]) -> Table:
    table = Table(title="Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    for check in checks:
        table.add_row(check.name, "ok" if check.ok else "fail", check.detail)
    return table


def build_conflicts_table(paths: list[str]) -> Table:
    table = Table(title="Conflicts")
    table.add_column("Path")
    for path in paths:
        table.add_row(path)
    return table
