from __future__ import annotations

from pathlib import Path

from uiw.infra.clock import now_stamp
from uiw.models import WorkspaceConfig
from uiw.ops import git_ops
from uiw.ops.workspace_ops import require_workspace
from uiw.services.workspace_registry import WorkspaceRegistry


def build_patch_file_path(config: WorkspaceConfig, workspace_name: str) -> Path:
    return config.paths.patches_root / f"{workspace_name}-{now_stamp()}.patch"


def export_workspace_patch(config: WorkspaceConfig, registry: WorkspaceRegistry, name: str) -> Path:
    meta = require_workspace(registry, name)
    patch_path = build_patch_file_path(config, name)
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(
        git_ops.export_diff_patch(meta.path, config.git.main_branch),
        encoding="utf-8",
    )
    return patch_path
