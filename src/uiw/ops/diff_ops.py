from __future__ import annotations

from uiw.models import WorkspaceConfig
from uiw.ops import git_ops
from uiw.services.workspace_registry import WorkspaceRegistry
from uiw.ops.workspace_ops import require_workspace


def get_workspace_diff(
    config: WorkspaceConfig,
    registry: WorkspaceRegistry,
    name: str,
    *,
    mode: str = "compact",
) -> str:
    meta = require_workspace(registry, name)
    if mode == "name-only":
        return "\n".join(git_ops.diff_name_only(meta.path, config.git.main_branch))
    if mode == "stat":
        return git_ops.diff_stat(meta.path, config.git.main_branch)
    return git_ops.diff_compact(meta.path, config.git.main_branch)
