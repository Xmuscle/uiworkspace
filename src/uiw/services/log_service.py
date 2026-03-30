from __future__ import annotations

from pathlib import Path
from typing import Any

from uiw.infra.clock import now_stamp
from uiw.infra.json_io import save_json
from uiw.models import WorkspaceConfig


class LogService:
    def build_apply_log_path(self, config: WorkspaceConfig, workspace_name: str) -> Path:
        return config.paths.logs_root / f"apply-{workspace_name}-{now_stamp()}.json"

    def write_apply_log(self, path: Path, payload: dict[str, Any]) -> None:
        save_json(path, payload)

    def build_operation_log_path(self, config: WorkspaceConfig, operation: str) -> Path:
        return config.paths.logs_root / f"{operation}-{now_stamp()}.json"
