from pathlib import Path
from unittest.mock import patch

import pytest

from uiw.errors import DirtyWorkspaceError, ValidationError, WorkspaceConflictError
from uiw.models import ApplySettings, GitSettings, SyncSettings, WorkspaceConfig, WorkspaceMeta, WorkspacePaths
from uiw.ops.apply_ops import assert_apply_allowed, copy_changed_files, delete_removed_files
from uiw.ops.sync_ops import assert_sync_allowed
from uiw.ops.workspace_ops import create_workspace, refresh_workspace


class DummyRegistry:
    def __init__(self, meta: WorkspaceMeta | None = None) -> None:
        self.meta = meta
        self.added = None

    def exists(self, name: str) -> bool:
        return False

    def add(self, meta: WorkspaceMeta) -> None:
        self.added = meta

    def get(self, name: str) -> WorkspaceMeta:
        assert self.meta is not None
        return self.meta


def make_config(tmp_path: Path) -> WorkspaceConfig:
    svn_main = tmp_path / "svn-main"
    git_main = tmp_path / "git-main"
    worktrees_root = tmp_path / "worktrees"
    for path in [svn_main, git_main, worktrees_root, tmp_path / "patches", tmp_path / "logs", tmp_path / "config", tmp_path / "logs" / "backups"]:
        path.mkdir(parents=True, exist_ok=True)
    return WorkspaceConfig(
        paths=WorkspacePaths(
            svn_main=svn_main,
            git_main=git_main,
            worktrees_root=worktrees_root,
            patches_root=tmp_path / "patches",
            logs_root=tmp_path / "logs",
            config_root=tmp_path / "config",
            backup_root=tmp_path / "logs" / "backups",
        ),
        git=GitSettings(
            main_branch="main",
            default_new_from="main",
            refresh_mode="merge",
            sync_commit_prefix="sync from svn",
        ),
        sync=SyncSettings(ignore=[".git", ".svn"]),
        apply=ApplySettings(backup=True, backup_root=tmp_path / "logs" / "backups", mode="copy"),
    )


def test_assert_sync_allowed_rejects_dirty_git_main(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    with patch("uiw.ops.sync_ops.git_ops.is_git_repo", return_value=True), patch(
        "uiw.ops.sync_ops.git_ops.is_dirty", return_value=True
    ):
        with pytest.raises(DirtyWorkspaceError):
            assert_sync_allowed(config)


def test_create_workspace_rejects_missing_source_branch(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    registry = DummyRegistry()
    with patch("uiw.ops.workspace_ops.git_ops.branch_exists", return_value=False), patch(
        "uiw.ops.workspace_ops.git_ops.assert_branch_exists", side_effect=ValidationError("Branch does not exist: main")
    ):
        with pytest.raises(ValidationError):
            create_workspace(config, registry, "event-a")


def test_refresh_workspace_rejects_dirty_workspace(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    meta_path = tmp_path / "worktrees" / "event-a"
    meta_path.mkdir(parents=True)
    registry = DummyRegistry(WorkspaceMeta("event-a", "event-a", meta_path, "main", "2026-03-30T10:00:00"))
    with patch("uiw.ops.workspace_ops.git_ops.is_merge_in_progress", return_value=False), patch(
        "uiw.ops.workspace_ops.git_ops.has_unmerged_files", return_value=False
    ), patch("uiw.ops.workspace_ops.git_ops.is_dirty", return_value=True):
        with pytest.raises(DirtyWorkspaceError):
            refresh_workspace(config, registry, "event-a")


def test_assert_apply_allowed_rejects_missing_workspace_path(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    workspace = WorkspaceMeta("event-a", "event-a", tmp_path / "missing", "main", "2026-03-30T10:00:00")
    with pytest.raises(ValidationError):
        assert_apply_allowed(config, workspace)


def test_assert_apply_allowed_rejects_conflicts(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    workspace_path = tmp_path / "worktrees" / "event-a"
    workspace_path.mkdir(parents=True)
    workspace = WorkspaceMeta("event-a", "event-a", workspace_path, "main", "2026-03-30T10:00:00")
    with patch("uiw.ops.apply_ops.git_ops.has_unmerged_files", return_value=True):
        with pytest.raises(WorkspaceConflictError):
            assert_apply_allowed(config, workspace)


def test_copy_changed_files_rejects_escape(tmp_path: Path) -> None:
    worktree = tmp_path / "wt"
    svn_root = tmp_path / "svn"
    worktree.mkdir()
    svn_root.mkdir()
    with pytest.raises(Exception):
        copy_changed_files(worktree, svn_root, [type("C", (), {"path": "../oops.txt"})()])


def test_delete_removed_files_rejects_escape(tmp_path: Path) -> None:
    svn_root = tmp_path / "svn"
    svn_root.mkdir()
    with pytest.raises(Exception):
        delete_removed_files(svn_root, [type("C", (), {"path": "../oops.txt"})()])
