from __future__ import annotations

from pathlib import Path

import typer

from uiw.config.defaults import build_default_config_dict
from uiw.config.schema import parse_workspace_config
from uiw.config.loader import save_config
from uiw.constants import WORKSPACE_CONFIG_NAME, WORKSPACES_REGISTRY_NAME
from uiw.errors import ValidationError
from uiw.infra.paths import ensure_dir
from uiw.infra.yaml_io import save_yaml
from uiw.ops import git_ops, svn_ops
from uiw.ui.console import print_success


def init_command(svn: Path, git: Path, worktrees: Path) -> None:
    if not svn_ops.check_svn_available():
        raise typer.BadParameter("svn command not found")
    if not git_ops.check_git_available():
        raise typer.BadParameter("git command not found")
    if not svn.exists():
        raise typer.BadParameter(f"svn path does not exist: {svn}")

    workspace_root = git.parent
    if worktrees.resolve() == git.resolve() or svn.resolve() == git.resolve() or svn.resolve() == worktrees.resolve():
        raise ValidationError("svn, git, and worktrees paths must be different")
    config_root = workspace_root / "config"
    patches_root = workspace_root / "patches"
    logs_root = workspace_root / "logs"
    for path in [git, worktrees, config_root, patches_root, logs_root, logs_root / "backups"]:
        ensure_dir(path)

    git_dir = git / ".git"
    if git_dir.exists() and not git_ops.is_git_repo(git):
        raise ValidationError(f"git-main exists but is not a valid git repo: {git}")
    if not git_ops.is_git_repo(git):
        git_ops.git_init(git)
        git_ops.ensure_branch_exists(git, "main")

    data = build_default_config_dict(svn.resolve(), git.resolve(), worktrees.resolve())
    config = parse_workspace_config(data)
    config_path = config_root / WORKSPACE_CONFIG_NAME
    save_config(config, config_path)
    save_yaml(config_root / WORKSPACES_REGISTRY_NAME, {"workspaces": {}})
    print_success(f"Initialized workspace config at {config_path}")


def register(app: typer.Typer) -> None:
    app.command("init")(init_command)
