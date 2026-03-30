from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from uiw.errors import CommandExecutionError


@dataclass(slots=True)
class RunResult:
    args: list[str]
    cwd: Path | None
    returncode: int
    stdout: str
    stderr: str


def format_command(args: list[str]) -> str:
    return " ".join(args)


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_cmd(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    timeout: float | None = None,
) -> RunResult:
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    result = RunResult(
        args=args,
        cwd=cwd,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if check and completed.returncode != 0:
        raise CommandExecutionError(
            f"Command failed ({completed.returncode}): {format_command(args)}",
            hint=(completed.stderr or completed.stdout).strip() or None,
        )
    return result
