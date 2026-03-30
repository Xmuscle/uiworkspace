from __future__ import annotations

from pathlib import Path

from uiw.constants import VALID_WORKSPACE_NAME_CHARS
from uiw.errors import DirtyWorkspaceError, ValidationError, WorkspaceConflictError
from uiw.infra.clock import now_iso
from uiw.models import WorkspaceConfig, WorkspaceMeta
from uiw.ops import git_ops
from uiw.services.status_service import StatusService
from uiw.services.workspace_registry import WorkspaceRegistry


def validate_workspace_name(name: str) -> None:
    if not name:
        raise ValidationError("Workspace name cannot be empty")
    if any(ch not in VALID_WORKSPACE_NAME_CHARS for ch in name):
        raise ValidationError(f"Invalid workspace name: {name}")


def require_workspace(registry: WorkspaceRegistry, name: str) -> WorkspaceMeta:
    return registry.get(name)


def assert_workspace_exists_on_disk(meta: WorkspaceMeta) -> None:
    if not meta.path.exists():
        raise ValidationError(f"Workspace path does not exist: {meta.path}")


def assert_workspace_not_dirty(path: Path) -> None:
    if git_ops.is_dirty(path):
        raise DirtyWorkspaceError(f"Workspace has uncommitted changes: {path}")


def assert_workspace_not_in_conflict(path: Path) -> None:
    if git_ops.has_unmerged_files(path):
        raise WorkspaceConflictError(f"Workspace has unresolved conflicts: {path}")


def create_workspace(
    config: WorkspaceConfig,
    registry: WorkspaceRegistry,
    name: str,
    from_branch: str | None = None,
) -> WorkspaceMeta:
    validate_workspace_name(name)
    if registry.exists(name):
        raise ValidationError(f"Workspace already exists: {name}")
    branch = name
    source = from_branch or config.git.default_new_from
    path = config.paths.worktrees_root / name
    if path.exists():
        raise ValidationError(f"Worktree path already exists: {path}")
    if git_ops.branch_exists(config.paths.git_main, branch):
        raise ValidationError(f"Branch already exists: {branch}")
    git_ops.assert_branch_exists(config.paths.git_main, source)
    git_ops.add_worktree(config.paths.git_main, path, branch, source)
    meta = WorkspaceMeta(name=name, branch=branch, path=path, from_branch=source, created_at=now_iso())
    registry.add(meta)
    return meta


def list_workspaces(config: WorkspaceConfig, registry: WorkspaceRegistry):
    service = StatusService()
    return service.list_workspace_statuses(config, registry.list_workspaces())


def get_workspace_info(config: WorkspaceConfig, registry: WorkspaceRegistry, name: str) -> dict:
    meta = require_workspace(registry, name)
    assert_workspace_exists_on_disk(meta)
    return {
        "path": meta.path,
        "branch": meta.branch,
        "head": git_ops.get_head_commit(meta.path),
        "created_at": meta.created_at,
        "from_branch": meta.from_branch,
        "last_commit": git_ops.get_last_commit_summary(meta.path),
        "uncommitted": git_ops.get_status_porcelain(meta.path),
        "conflicts": git_ops.get_unmerged_files(meta.path),
    }


def refresh_workspace(config: WorkspaceConfig, registry: WorkspaceRegistry, name: str) -> dict:
    meta = require_workspace(registry, name)
    assert_workspace_exists_on_disk(meta)
    if git_ops.is_merge_in_progress(meta.path):
        raise WorkspaceConflictError(f"Merge already in progress: {meta.path}")
    if git_ops.has_unmerged_files(meta.path):
        raise WorkspaceConflictError(f"Workspace has unresolved conflicts: {meta.path}")
    if git_ops.is_dirty(meta.path):
        raise DirtyWorkspaceError(f"Workspace has uncommitted changes: {meta.path}")
    git_ops.assert_branch_exists(meta.path, config.git.main_branch)
    result = git_ops.merge_branch(meta.path, config.git.main_branch)
    conflicts = git_ops.get_unmerged_files(meta.path)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "conflicts": conflicts,
    }


def continue_refresh(config: WorkspaceConfig, registry: WorkspaceRegistry, name: str) -> dict:
    meta = require_workspace(registry, name)
    if not git_ops.is_merge_in_progress(meta.path):
        raise ValidationError(f"No merge in progress for workspace: {name}")
    conflicts = git_ops.get_unmerged_files(meta.path)
    if conflicts:
        raise WorkspaceConflictError("Cannot continue refresh while conflicts remain")
    result = git_ops.merge_continue(meta.path)
    return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def abort_refresh(config: WorkspaceConfig, registry: WorkspaceRegistry, name: str) -> dict:
    meta = require_workspace(registry, name)
    if not git_ops.is_merge_in_progress(meta.path):
        raise ValidationError(f"No merge in progress for workspace: {name}")
    result = git_ops.merge_abort(meta.path)
    return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def get_workspace_conflicts(config: WorkspaceConfig, registry: WorkspaceRegistry, name: str) -> list[str]:
    meta = require_workspace(registry, name)
    assert_workspace_exists_on_disk(meta)
    return git_ops.get_unmerged_files(meta.path)


def remove_workspace(
    config: WorkspaceConfig,
    registry: WorkspaceRegistry,
    name: str,
    *,
    keep_branch: bool = False,
) -> dict:
    meta = require_workspace(registry, name)
    assert_workspace_exists_on_disk(meta)
    assert_workspace_not_dirty(meta.path)
    git_ops.remove_worktree(config.paths.git_main, meta.path)
    if not keep_branch:
        git_ops.remove_branch(config.paths.git_main, meta.branch)
    registry.remove(name)
    return {"path": meta.path, "branch": meta.branch, "keep_branch": keep_branch}
