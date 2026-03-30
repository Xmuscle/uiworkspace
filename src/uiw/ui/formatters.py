from __future__ import annotations

from pathlib import Path


def format_ahead_behind(ahead: int, behind: int) -> str:
    return f"+{ahead} / -{behind}"


def format_path(path: Path) -> str:
    return path.as_posix()


def format_check(ok: bool) -> str:
    return "ok" if ok else "fail"


def format_change_summary(modified: int, added: int, deleted: int) -> str:
    return f"Modified: {modified}, Added: {added}, Deleted: {deleted}"
