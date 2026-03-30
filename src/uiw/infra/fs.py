from __future__ import annotations

import shutil
from collections.abc import Callable, Iterator
from pathlib import Path

def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def copy_file(src: Path, dst: Path) -> None:
    ensure_parent_dir(dst)
    shutil.copy2(src, dst)


def remove_file(path: Path) -> None:
    if path.exists():
        path.unlink()


def remove_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def iter_relative_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path.relative_to(root)


def safe_delete_paths(paths: list[Path], root: Path) -> None:
    for path in paths:
        resolved = path.resolve()
        resolved.relative_to(root.resolve())
        if resolved.is_dir():
            shutil.rmtree(resolved)
        elif resolved.exists():
            resolved.unlink()


def mirror_tree(
    source_root: Path,
    target_root: Path,
    *,
    ignore_matcher: Callable[[Path], bool],
) -> tuple[int, int]:
    copied = 0
    deleted = 0
    source_files = {path for path in iter_relative_files(source_root) if not ignore_matcher(path)}
    target_files = {path for path in iter_relative_files(target_root) if not ignore_matcher(path)}

    for relative_path in source_files:
        src = source_root / relative_path
        dst = target_root / relative_path
        ensure_parent_dir(dst)
        if not dst.exists() or src.read_bytes() != dst.read_bytes():
            shutil.copy2(src, dst)
            copied += 1

    for relative_path in sorted(target_files - source_files):
        dst = target_root / relative_path
        if dst.exists():
            dst.unlink()
            deleted += 1

    return copied, deleted
