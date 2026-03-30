from __future__ import annotations

from pathlib import Path

from uiw.errors import DirtyWorkspaceError
from uiw.infra.process import command_exists, run_cmd, RunResult


def check_svn_available() -> bool:
    return command_exists("svn")


def svn_update(svn_main: Path) -> RunResult:
    return run_cmd(["svn", "update"], cwd=svn_main)


def svn_status(svn_main: Path) -> RunResult:
    return run_cmd(["svn", "status"], cwd=svn_main)


def is_svn_working_copy_clean(svn_main: Path) -> bool:
    return svn_status(svn_main).stdout.strip() == ""


def assert_svn_clean(svn_main: Path) -> None:
    if not is_svn_working_copy_clean(svn_main):
        raise DirtyWorkspaceError(f"svn-main has uncommitted changes: {svn_main}")
