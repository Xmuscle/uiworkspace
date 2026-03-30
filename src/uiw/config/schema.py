from __future__ import annotations

from pathlib import Path
from typing import Any

from uiw.errors import ConfigError
from uiw.models import ApplySettings, GitSettings, SyncSettings, WorkspaceConfig, WorkspacePaths


REQUIRED_TOP_LEVEL_KEYS = {"paths", "git", "sync", "apply"}


def _require(data: dict[str, Any], key: str, section: str) -> Any:
    if key not in data:
        raise ConfigError(f"Missing key '{key}' in {section}")
    return data[key]


def parse_workspace_config(data: dict[str, Any]) -> WorkspaceConfig:
    missing = REQUIRED_TOP_LEVEL_KEYS - set(data)
    if missing:
        raise ConfigError(f"Missing config sections: {', '.join(sorted(missing))}")

    paths_data = data["paths"]
    git_data = data["git"]
    sync_data = data["sync"]
    apply_data = data["apply"]

    paths = WorkspacePaths(
        svn_main=Path(_require(paths_data, "svn_main", "paths")),
        git_main=Path(_require(paths_data, "git_main", "paths")),
        worktrees_root=Path(_require(paths_data, "worktrees_root", "paths")),
        patches_root=Path(_require(paths_data, "patches_root", "paths")),
        logs_root=Path(_require(paths_data, "logs_root", "paths")),
        config_root=Path(_require(paths_data, "config_root", "paths")),
        backup_root=Path(_require(paths_data, "backup_root", "paths")),
    )
    git = GitSettings(
        main_branch=_require(git_data, "main_branch", "git"),
        default_new_from=_require(git_data, "default_new_from", "git"),
        refresh_mode=_require(git_data, "refresh_mode", "git"),
        sync_commit_prefix=_require(git_data, "sync_commit_prefix", "git"),
    )
    sync = SyncSettings(ignore=list(sync_data.get("ignore", [])))
    apply = ApplySettings(
        backup=bool(_require(apply_data, "backup", "apply")),
        backup_root=Path(_require(apply_data, "backup_root", "apply")),
        mode=_require(apply_data, "mode", "apply"),
    )
    config = WorkspaceConfig(paths=paths, git=git, sync=sync, apply=apply)
    validate_workspace_config(config)
    return config


def workspace_config_to_dict(config: WorkspaceConfig) -> dict[str, Any]:
    return {
        "paths": {
            "svn_main": config.paths.svn_main.as_posix(),
            "git_main": config.paths.git_main.as_posix(),
            "worktrees_root": config.paths.worktrees_root.as_posix(),
            "patches_root": config.paths.patches_root.as_posix(),
            "logs_root": config.paths.logs_root.as_posix(),
            "config_root": config.paths.config_root.as_posix(),
            "backup_root": config.paths.backup_root.as_posix(),
        },
        "git": {
            "main_branch": config.git.main_branch,
            "default_new_from": config.git.default_new_from,
            "refresh_mode": config.git.refresh_mode,
            "sync_commit_prefix": config.git.sync_commit_prefix,
        },
        "sync": {"ignore": list(config.sync.ignore)},
        "apply": {
            "backup": config.apply.backup,
            "backup_root": config.apply.backup_root.as_posix(),
            "mode": config.apply.mode,
        },
    }


def validate_workspace_config(config: WorkspaceConfig) -> None:
    if not config.git.main_branch:
        raise ConfigError("git.main_branch cannot be empty")
    if not config.paths.svn_main:
        raise ConfigError("paths.svn_main is required")
    if not config.paths.git_main:
        raise ConfigError("paths.git_main is required")
    if not config.paths.worktrees_root:
        raise ConfigError("paths.worktrees_root is required")
