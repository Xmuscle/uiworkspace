from pathlib import Path

APP_NAME = "uiw"
DEFAULT_MAIN_BRANCH = "main"
DEFAULT_REFRESH_MODE = "merge"
WORKSPACE_CONFIG_NAME = "workspace.yaml"
WORKSPACES_REGISTRY_NAME = "workspaces.yaml"
DEFAULT_SYNC_COMMIT_PREFIX = "sync from svn"
DEFAULT_SYNC_IGNORE = [
    ".git",
    ".svn",
    ".idea",
    ".vs",
    "Library",
    "Temp",
    "Logs",
    "obj",
    "bin",
]
CONFIG_DIR_NAME = "config"
PATCHES_DIR_NAME = "patches"
LOGS_DIR_NAME = "logs"
BACKUPS_DIR_NAME = "backups"
MERGE_HEAD_REF = "MERGE_HEAD"
VALID_WORKSPACE_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")


def default_workspace_root_from_git(git_main: Path) -> Path:
    return git_main.parent
