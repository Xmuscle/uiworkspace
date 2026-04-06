from __future__ import annotations

from pathlib import Path
from typing import Any

from uiw.errors import ValidationError
from uiw.infra.fs import copy_file, remove_file
from uiw.infra.json_io import load_json, save_json
from uiw.infra.paths import resolve_under_root
from uiw.models import WorkspaceConfig
from uiw.services.log_service import LogService


APPLY_LOG_GLOB = "apply-*.json"
CLEAR_OPERATION_NAME = "svn-main-clear"


def find_latest_apply_log(logs_root: Path) -> Path:
    candidates = sorted(logs_root.glob(APPLY_LOG_GLOB))
    if not candidates:
        raise ValidationError(f"No apply log found in logs root: {logs_root}")
    return candidates[-1]


def _require_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValidationError(f"Apply log field '{key}' must be a list")
    if any(not isinstance(item, str) for item in value):
        raise ValidationError(f"Apply log field '{key}' must contain only strings")
    return value


def load_apply_log(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if not data:
        raise ValidationError(f"Apply log is empty: {path}")
    if not isinstance(data.get("target"), str):
        raise ValidationError(f"Apply log missing target: {path}")
    _require_list(data, "modified")
    _require_list(data, "added")
    _require_list(data, "deleted")
    backup_dir = data.get("backup_dir")
    if backup_dir is not None and not isinstance(backup_dir, str):
        raise ValidationError(f"Apply log field 'backup_dir' must be a string or null: {path}")
    return data


def ensure_apply_log_matches_config(config: WorkspaceConfig, apply_log: dict[str, Any], apply_log_path: Path) -> None:
    target = Path(apply_log["target"]).resolve()
    if target != config.paths.svn_main.resolve():
        raise ValidationError(
            f"Apply log target does not match current svn-main: {apply_log_path}"
        )


def require_backup_dir(apply_log: dict[str, Any], apply_log_path: Path) -> Path:
    backup_dir_value = apply_log.get("backup_dir")
    modified = _require_list(apply_log, "modified")
    deleted = _require_list(apply_log, "deleted")
    if not modified and not deleted:
        if isinstance(backup_dir_value, str):
            return Path(backup_dir_value).resolve()
        return Path()
    if not isinstance(backup_dir_value, str):
        raise ValidationError(f"Apply log does not contain backup_dir: {apply_log_path}")
    backup_dir = Path(backup_dir_value).resolve()
    if not backup_dir.exists() or not backup_dir.is_dir():
        raise ValidationError(f"Backup directory does not exist: {backup_dir}")
    return backup_dir


def restore_files_from_backup(backup_root: Path, svn_root: Path, relative_paths: list[str]) -> int:
    count = 0
    for relative_path in relative_paths:
        source = resolve_under_root(backup_root, relative_path)
        if not source.exists() or not source.is_file():
            raise ValidationError(f"Backup file does not exist for clear: {relative_path}")
        target = resolve_under_root(svn_root, relative_path)
        copy_file(source, target)
        count += 1
    return count


def remove_empty_parent_dirs(path: Path, root: Path) -> None:
    current = path.resolve()
    root_resolved = root.resolve()
    while current != root_resolved and current.exists() and current.is_dir() and not any(current.iterdir()):
        current.rmdir()
        current = current.parent


def remove_added_files(svn_root: Path, relative_paths: list[str]) -> int:
    count = 0
    for relative_path in relative_paths:
        target = resolve_under_root(svn_root, relative_path)
        existed = target.exists() and target.is_file()
        remove_file(target)
        if existed:
            count += 1
            remove_empty_parent_dirs(target.parent, svn_root)
    return count


def write_clear_log(
    config: WorkspaceConfig,
    apply_log_path: Path,
    restored_modified: int,
    removed_added: int,
    restored_deleted: int,
) -> Path:
    service = LogService()
    log_path = service.build_operation_log_path(config, CLEAR_OPERATION_NAME)
    save_json(
        log_path,
        {
            "operation": CLEAR_OPERATION_NAME,
            "apply_log": apply_log_path.as_posix(),
            "target": config.paths.svn_main.as_posix(),
            "restored_modified": restored_modified,
            "removed_added": removed_added,
            "restored_deleted": restored_deleted,
        },
    )
    return log_path


def clear_svn_main(config: WorkspaceConfig) -> dict[str, Any]:
    apply_log_path = find_latest_apply_log(config.paths.logs_root)
    apply_log = load_apply_log(apply_log_path)
    ensure_apply_log_matches_config(config, apply_log, apply_log_path)

    modified = _require_list(apply_log, "modified")
    added = _require_list(apply_log, "added")
    deleted = _require_list(apply_log, "deleted")
    backup_dir = require_backup_dir(apply_log, apply_log_path)

    restored_modified = restore_files_from_backup(backup_dir, config.paths.svn_main, modified) if modified else 0
    removed_added = remove_added_files(config.paths.svn_main, added)
    restored_deleted = restore_files_from_backup(backup_dir, config.paths.svn_main, deleted) if deleted else 0
    clear_log_path = write_clear_log(config, apply_log_path, restored_modified, removed_added, restored_deleted)

    return {
        "apply_log": apply_log_path,
        "restored_modified": restored_modified,
        "removed_added": removed_added,
        "restored_deleted": restored_deleted,
        "clear_log": clear_log_path,
    }
