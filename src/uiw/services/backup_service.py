from __future__ import annotations

from pathlib import Path

from uiw.infra.clock import now_stamp
from uiw.infra.fs import copy_file
from uiw.infra.paths import resolve_under_root
from uiw.models import WorkspaceConfig


class BackupService:
    def create_backup_dir(self, config: WorkspaceConfig, workspace_name: str) -> Path:
        path = config.apply.backup_root / f"apply-{workspace_name}-{now_stamp()}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def backup_files(self, source_root: Path, backup_root: Path, relative_paths: list[str]) -> int:
        count = 0
        for relative in relative_paths:
            source = resolve_under_root(source_root, relative)
            if source.exists() and source.is_file():
                destination = backup_root / relative
                copy_file(source, destination)
                count += 1
        return count
