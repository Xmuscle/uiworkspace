from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class WorkspacePaths:
    svn_main: Path
    git_main: Path
    worktrees_root: Path
    patches_root: Path
    logs_root: Path
    config_root: Path
    backup_root: Path


@dataclass(slots=True)
class GitSettings:
    main_branch: str
    default_new_from: str
    refresh_mode: str
    sync_commit_prefix: str


@dataclass(slots=True)
class SyncSettings:
    ignore: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ApplySettings:
    backup: bool
    backup_root: Path
    mode: str


@dataclass(slots=True)
class WorkspaceConfig:
    paths: WorkspacePaths
    git: GitSettings
    sync: SyncSettings
    apply: ApplySettings


@dataclass(slots=True)
class WorkspaceMeta:
    name: str
    branch: str
    path: Path
    from_branch: str
    created_at: str


@dataclass(slots=True)
class WorkspaceStatus:
    name: str
    branch: str
    path: Path
    state: str
    ahead: int
    behind: int
    has_conflicts: bool
    is_dirty: bool


@dataclass(slots=True)
class FileChange:
    path: str
    change_type: str


@dataclass(slots=True)
class ApplyPlan:
    workspace: WorkspaceMeta
    modified: list[FileChange]
    added: list[FileChange]
    deleted: list[FileChange]


@dataclass(slots=True)
class DoctorCheck:
    name: str
    ok: bool
    detail: str
    hint: str | None = None
