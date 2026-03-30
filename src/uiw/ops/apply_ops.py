from __future__ import annotations

from pathlib import Path

from uiw.errors import ValidationError, WorkspaceConflictError
from uiw.infra.paths import ensure_within_root
from uiw.models import ApplyPlan, FileChange, WorkspaceConfig, WorkspaceMeta
from uiw.ops import git_ops, svn_ops
from uiw.ops.workspace_ops import require_workspace
from uiw.services.backup_service import BackupService
from uiw.services.log_service import LogService
from uiw.services.workspace_registry import WorkspaceRegistry


def parse_name_status(entries: list[tuple[str, str]]) -> tuple[list[FileChange], list[FileChange], list[FileChange]]:
    modified: list[FileChange] = []
    added: list[FileChange] = []
    deleted: list[FileChange] = []
    for status, path in entries:
        code = status[0]
        if code == "M":
            modified.append(FileChange(path=path, change_type="modified"))
        elif code == "A":
            added.append(FileChange(path=path, change_type="added"))
        elif code == "D":
            deleted.append(FileChange(path=path, change_type="deleted"))
        else:
            modified.append(FileChange(path=path, change_type="modified"))
    return modified, added, deleted


def assert_apply_allowed(config: WorkspaceConfig, workspace: WorkspaceMeta) -> None:
    if not workspace.path.exists():
        raise ValidationError(f"Workspace path does not exist: {workspace.path}")
    if git_ops.has_unmerged_files(workspace.path):
        raise WorkspaceConflictError(f"Workspace has unresolved conflicts: {workspace.path}")
    svn_ops.assert_svn_clean(config.paths.svn_main)


def build_apply_plan(config: WorkspaceConfig, registry: WorkspaceRegistry, name: str) -> ApplyPlan:
    workspace = require_workspace(registry, name)
    assert_apply_allowed(config, workspace)
    entries = git_ops.diff_name_status(workspace.path, config.git.main_branch)
    modified, added, deleted = parse_name_status(entries)
    return ApplyPlan(workspace=workspace, modified=modified, added=added, deleted=deleted)


def collect_backup_targets(config: WorkspaceConfig, plan: ApplyPlan) -> list[str]:
    return [change.path for change in [*plan.modified, *plan.deleted] if (config.paths.svn_main / change.path).exists()]


def backup_existing_files(svn_root: Path, backup_root: Path, rel_paths: list[str]) -> int:
    service = BackupService()
    return service.backup_files(svn_root, backup_root, rel_paths)


def copy_changed_files(worktree_root: Path, svn_root: Path, changes: list[FileChange]) -> int:
    count = 0
    for change in changes:
        source = (worktree_root / change.path).resolve()
        target = (svn_root / change.path).resolve()
        ensure_within_root(source, worktree_root)
        ensure_within_root(target, svn_root)
        if not source.exists() or not source.is_file():
            raise ValidationError(f"Source file does not exist for apply: {change.path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        count += 1
    return count


def delete_removed_files(svn_root: Path, changes: list[FileChange]) -> int:
    count = 0
    for change in changes:
        target = (svn_root / change.path).resolve()
        ensure_within_root(target, svn_root)
        if target.exists() and target.is_file():
            target.unlink()
            count += 1
    return count


def write_apply_audit_log(config: WorkspaceConfig, plan: ApplyPlan, result: dict, backup_dir: Path | None) -> Path:
    service = LogService()
    log_path = service.build_apply_log_path(config, plan.workspace.name)
    service.write_apply_log(
        log_path,
        {
            "workspace": plan.workspace.name,
            "source": plan.workspace.path.as_posix(),
            "target": config.paths.svn_main.as_posix(),
            "modified": [item.path for item in plan.modified],
            "added": [item.path for item in plan.added],
            "deleted": [item.path for item in plan.deleted],
            "backup_dir": backup_dir.as_posix() if backup_dir else None,
            "result": result,
        },
    )
    return log_path


def apply_plan_to_svn(config: WorkspaceConfig, plan: ApplyPlan) -> dict:
    backup_dir = None
    backup_count = 0
    if config.apply.backup:
        backup_service = BackupService()
        backup_dir = backup_service.create_backup_dir(config, plan.workspace.name)
        backup_count = backup_existing_files(
            config.paths.svn_main,
            backup_dir,
            collect_backup_targets(config, plan),
        )
    modified_count = copy_changed_files(plan.workspace.path, config.paths.svn_main, plan.modified)
    added_count = copy_changed_files(plan.workspace.path, config.paths.svn_main, plan.added)
    deleted_count = delete_removed_files(config.paths.svn_main, plan.deleted)
    result = {
        "modified": modified_count,
        "added": added_count,
        "deleted": deleted_count,
        "backup_count": backup_count,
        "backup_dir": backup_dir,
    }
    log_path = write_apply_audit_log(config, plan, result, backup_dir)
    result["log_path"] = log_path
    return result
