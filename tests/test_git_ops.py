from uiw.ops.git_ops import get_ahead_behind


def test_get_ahead_behind_symbol_exists() -> None:
    assert callable(get_ahead_behind)
