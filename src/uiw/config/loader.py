from __future__ import annotations

from pathlib import Path

from uiw.constants import WORKSPACE_CONFIG_NAME
from uiw.errors import ConfigError
from uiw.infra.yaml_io import load_yaml, save_yaml
from uiw.models import WorkspaceConfig
from uiw.config.schema import parse_workspace_config, workspace_config_to_dict


def resolve_config_path(explicit_path: Path | None = None, start_dir: Path | None = None) -> Path:
    if explicit_path is not None:
        return explicit_path.resolve()

    current = (start_dir or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        config_path = candidate / "config" / WORKSPACE_CONFIG_NAME
        if config_path.exists():
            return config_path
    raise ConfigError("Could not find config/workspace.yaml from current directory")


def load_config(config_path: Path | None = None) -> WorkspaceConfig:
    path = resolve_config_path(config_path)
    data = load_yaml(path)
    if not data:
        raise ConfigError(f"Config file is empty: {path}")
    return parse_workspace_config(data)


def save_config(config: WorkspaceConfig, config_path: Path) -> None:
    save_yaml(config_path, workspace_config_to_dict(config))


def ensure_config_exists(config_path: Path) -> None:
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
