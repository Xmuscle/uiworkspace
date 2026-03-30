from __future__ import annotations

from pathlib import Path

from uiw.errors import UnsafePathError, ValidationError


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def ensure_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise ValidationError(f"{label} does not exist: {path}")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ensure_within_root(path: Path, root: Path) -> None:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise UnsafePathError(f"Path escapes root: {path} (root: {root})") from exc


def resolve_under_root(root: Path, relative_path: str | Path) -> Path:
    target = (root / relative_path).resolve()
    ensure_within_root(target, root)
    return target


def workspace_dir_for(root: Path, name: str) -> Path:
    return root / name


def config_dir_for(git_main: Path) -> Path:
    return git_main.parent / "config"
