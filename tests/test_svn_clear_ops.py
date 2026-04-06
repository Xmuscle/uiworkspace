from pathlib import Path

import pytest

from uiw.errors import ValidationError
from uiw.models import ApplySettings, GitSettings, SyncSettings, WorkspaceConfig, WorkspacePaths
from uiw.ops.svn_clear_ops import clear_svn_main, find_latest_apply_log
from uiw.infra.json_io import save_json


def make_config(tmp_path: Path) -> WorkspaceConfig:
    svn_main = tmp_path / "svn-main"
    git_main = tmp_path / "git-main"
    worktrees_root = tmp_path / "worktrees"
    logs_root = tmp_path / "logs"
    backup_root = logs_root / "backups"
    config_root = tmp_path / "config"
    patches_root = tmp_path / "patches"
    for path in [svn_main, git_main, worktrees_root, logs_root, backup_root, config_root, patches_root]:
        path.mkdir(parents=True, exist_ok=True)
    return WorkspaceConfig(
        paths=WorkspacePaths(
            svn_main=svn_main,
            git_main=git_main,
            worktrees_root=worktrees_root,
            patches_root=patches_root,
            logs_root=logs_root,
            config_root=config_root,
            backup_root=backup_root,
        ),
        git=GitSettings(
            main_branch="main",
            default_new_from="main",
            refresh_mode="merge",
            sync_commit_prefix="sync from svn",
        ),
        sync=SyncSettings(),
        apply=ApplySettings(backup=True, backup_root=backup_root, mode="copy"),
    )


def write_apply_log(logs_root: Path, name: str, payload: dict) -> Path:
    path = logs_root / name
    save_json(path, payload)
    return path


def test_find_latest_apply_log_returns_latest_name(tmp_path: Path) -> None:
    logs_root = tmp_path / "logs"
    logs_root.mkdir()
    older = write_apply_log(logs_root, "apply-a-20260406-100000.json", {"target": "x", "modified": [], "added": [], "deleted": [], "backup_dir": None})
    newer = write_apply_log(logs_root, "apply-a-20260406-110000.json", {"target": "x", "modified": [], "added": [], "deleted": [], "backup_dir": None})
    assert find_latest_apply_log(logs_root) == newer
    assert older.exists()


def test_clear_svn_main_restores_modified_deleted_and_removes_added(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    svn_root = config.paths.svn_main
    backup_dir = config.apply.backup_root / "apply-event-a-20260406-100000"
    (backup_dir / "dir").mkdir(parents=True, exist_ok=True)

    modified_path = svn_root / "dir" / "modified.txt"
    deleted_path = svn_root / "deleted.txt"
    added_path = svn_root / "added.txt"

    modified_path.parent.mkdir(parents=True, exist_ok=True)
    modified_path.write_text("after apply", encoding="utf-8")
    added_path.write_text("new file", encoding="utf-8")

    (backup_dir / "dir" / "modified.txt").write_text("before apply", encoding="utf-8")
    (backup_dir / "deleted.txt").write_text("restored file", encoding="utf-8")

    apply_log = write_apply_log(
        config.paths.logs_root,
        "apply-event-a-20260406-100000.json",
        {
            "workspace": "event-a",
            "source": (tmp_path / "worktrees" / "event-a").as_posix(),
            "target": svn_root.as_posix(),
            "modified": ["dir/modified.txt"],
            "added": ["added.txt"],
            "deleted": ["deleted.txt"],
            "backup_dir": backup_dir.as_posix(),
            "result": {},
        },
    )

    result = clear_svn_main(config)

    assert result["apply_log"] == apply_log
    assert modified_path.read_text(encoding="utf-8") == "before apply"
    assert not added_path.exists()
    assert deleted_path.read_text(encoding="utf-8") == "restored file"
    assert result["restored_modified"] == 1
    assert result["removed_added"] == 1
    assert result["restored_deleted"] == 1
    assert result["clear_log"].exists()


def test_clear_svn_main_rejects_missing_apply_log(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    with pytest.raises(ValidationError):
        clear_svn_main(config)


def test_clear_svn_main_rejects_missing_backup_for_restore(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    write_apply_log(
        config.paths.logs_root,
        "apply-event-a-20260406-100000.json",
        {
            "workspace": "event-a",
            "source": (tmp_path / "worktrees" / "event-a").as_posix(),
            "target": config.paths.svn_main.as_posix(),
            "modified": ["a.txt"],
            "added": [],
            "deleted": [],
            "backup_dir": None,
            "result": {},
        },
    )
    with pytest.raises(ValidationError):
        clear_svn_main(config)


def test_clear_svn_main_rejects_path_escape(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    backup_dir = config.apply.backup_root / "apply-event-a-20260406-100000"
    backup_dir.mkdir(parents=True, exist_ok=True)
    write_apply_log(
        config.paths.logs_root,
        "apply-event-a-20260406-100000.json",
        {
            "workspace": "event-a",
            "source": (tmp_path / "worktrees" / "event-a").as_posix(),
            "target": config.paths.svn_main.as_posix(),
            "modified": ["../oops.txt"],
            "added": [],
            "deleted": [],
            "backup_dir": backup_dir.as_posix(),
            "result": {},
        },
    )
    with pytest.raises(Exception):
        clear_svn_main(config)
