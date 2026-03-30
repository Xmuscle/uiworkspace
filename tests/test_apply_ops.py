from pathlib import Path

from uiw.ops.apply_ops import parse_name_status


def test_parse_name_status() -> None:
    modified, added, deleted = parse_name_status([
        ("M", "a.txt"),
        ("A", "b.txt"),
        ("D", "c.txt"),
    ])
    assert [item.path for item in modified] == ["a.txt"]
    assert [item.path for item in added] == ["b.txt"]
    assert [item.path for item in deleted] == ["c.txt"]
