from __future__ import annotations

from uiw.models import WorkspaceConfig, WorkspaceMeta, WorkspaceStatus
from uiw.ops import git_ops


class StatusService:
    def build_workspace_status(self, config: WorkspaceConfig, meta: WorkspaceMeta) -> WorkspaceStatus:
        exists = meta.path.exists()
        if not exists:
            return WorkspaceStatus(
                name=meta.name,
                branch=meta.branch,
                path=meta.path,
                state="missing",
                ahead=0,
                behind=0,
                has_conflicts=False,
                is_dirty=False,
            )
        has_conflicts = git_ops.has_unmerged_files(meta.path)
        is_dirty = git_ops.is_dirty(meta.path)
        ahead, behind = git_ops.get_ahead_behind(meta.path, config.git.main_branch, meta.branch)
        state = "conflict" if has_conflicts else "dirty" if is_dirty else "clean"
        return WorkspaceStatus(
            name=meta.name,
            branch=meta.branch,
            path=meta.path,
            state=state,
            ahead=ahead,
            behind=behind,
            has_conflicts=has_conflicts,
            is_dirty=is_dirty,
        )

    def list_workspace_statuses(
        self,
        config: WorkspaceConfig,
        metas: list[WorkspaceMeta],
    ) -> list[WorkspaceStatus]:
        return [self.build_workspace_status(config, meta) for meta in metas]

    def detect_workspace_state(self, path):
        if git_ops.has_unmerged_files(path):
            return "conflict"
        if git_ops.is_dirty(path):
            return "dirty"
        return "clean"
