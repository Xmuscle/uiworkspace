from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CommandResult:
    ok: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def success(message: str, **details: Any) -> CommandResult:
    return CommandResult(ok=True, message=message, details=details)


def failure(message: str, **details: Any) -> CommandResult:
    return CommandResult(ok=False, message=message, details=details)
