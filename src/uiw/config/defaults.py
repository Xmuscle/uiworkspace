from __future__ import annotations

from pathlib import Path

from uiw.constants import (
    CONFIG_DIR_NAME,
    DEFAULT_MAIN_BRANCH,
    DEFAULT_REFRESH_MODE,
    DEFAULT_SYNC_COMMIT_PREFIX,
    DEFAULT_SYNC_IGNORE,
)


def default_sync_ignore() -> list[str]:
    return list(DEFAULT_SYNC_IGNORE)


def build_default_config_dict(svn_main: Path, git_main: Path, worktrees_root: Path) -> dict:
    workspace_root = git_main.parent
    config_root = workspace_root / CONFIG_DIR_NAME
    logs_root = workspace_root / "logs"
    patches_root = workspace_root / "patches"
    backup_root = logs_root / "backups"
    return {
        "paths": {
            "svn_main": svn_main.as_posix(),
            "git_main": git_main.as_posix(),
            "worktrees_root": worktrees_root.as_posix(),
            "patches_root": patches_root.as_posix(),
            "logs_root": logs_root.as_posix(),
            "config_root": config_root.as_posix(),
            "backup_root": backup_root.as_posix(),
        },
        "git": {
            "main_branch": DEFAULT_MAIN_BRANCH,
            "default_new_from": DEFAULT_MAIN_BRANCH,
            "refresh_mode": DEFAULT_REFRESH_MODE,
            "sync_commit_prefix": DEFAULT_SYNC_COMMIT_PREFIX,
        },
        "sync": {"ignore": default_sync_ignore()},
        "apply": {
            "backup": True,
            "backup_root": backup_root.as_posix(),
            "mode": "copy",
        },
    }
