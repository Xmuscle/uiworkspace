from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from uiw.errors import DirtyWorkspaceError, ValidationError
from uiw.infra.fs import mirror_tree
from uiw.infra.process import RunResult
from uiw.infra.clock import now_stamp
from uiw.models import WorkspaceConfig
from uiw.ops import git_ops, svn_ops


def build_sync_ignore_matcher(config: WorkspaceConfig) -> Callable[[Path], bool]:
    ignored = set(config.sync.ignore)
    worktrees_name = config.paths.worktrees_root.name

    def matcher(relative_path: Path) -> bool:
        parts = set(relative_path.parts)
        return bool(parts & ignored) or worktrees_name in parts

    return matcher


def compose_sync_commit_message(config: WorkspaceConfig, custom_message: str | None = None) -> str:
    if custom_message:
        return custom_message
    return f"{config.git.sync_commit_prefix} {now_stamp()}"


def commit_git_baseline_if_needed(config: WorkspaceConfig, message: str | None = None) -> str | None:
    git_ops.git_add_all(config.paths.git_main)
    if not git_ops.has_staged_changes(config.paths.git_main):
        return None
    return git_ops.commit(config.paths.git_main, compose_sync_commit_message(config, message))


def assert_sync_allowed(config: WorkspaceConfig) -> None:
    if not config.paths.svn_main.exists():
        raise ValidationError(f"svn-main path does not exist: {config.paths.svn_main}")
    if not config.paths.git_main.exists():
        raise ValidationError(f"git-main path does not exist: {config.paths.git_main}")
    if not git_ops.is_git_repo(config.paths.git_main):
        raise ValidationError(f"git-main is not a git repository: {config.paths.git_main}")
    if git_ops.is_dirty(config.paths.git_main):
        raise DirtyWorkspaceError(f"git-main has uncommitted changes: {config.paths.git_main}")


def sync_svn_to_git(config: WorkspaceConfig, message: str | None = None) -> dict:
    assert_sync_allowed(config)
    svn_result: RunResult = svn_ops.svn_update(config.paths.svn_main)
    copied, deleted = mirror_tree(
        config.paths.svn_main,
        config.paths.git_main,
        ignore_matcher=build_sync_ignore_matcher(config),
    )
    commit_hash = commit_git_baseline_if_needed(config, message)
    return {
        "svn_stdout": svn_result.stdout.strip(),
        "copied": copied,
        "deleted": deleted,
        "committed": commit_hash is not None,
        "commit_hash": commit_hash,
    }
