from pathlib import Path

import pytest

from uiw.errors import UnsafePathError
from uiw.infra.paths import ensure_within_root


def test_ensure_within_root_allows_child(tmp_path: Path) -> None:
    child = tmp_path / "a" / "b.txt"
    child.parent.mkdir(parents=True)
    child.write_text("x", encoding="utf-8")
    ensure_within_root(child, tmp_path)


def test_ensure_within_root_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(UnsafePathError):
        ensure_within_root(Path("C:/outside"), tmp_path)
