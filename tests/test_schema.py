from pathlib import Path

from uiw.config.defaults import build_default_config_dict
from uiw.config.schema import parse_workspace_config


def test_parse_workspace_config_roundtrip_shape() -> None:
    data = build_default_config_dict(Path("D:/svn-main"), Path("D:/git-main"), Path("D:/worktrees"))
    config = parse_workspace_config(data)
    assert config.paths.svn_main == Path("D:/svn-main")
    assert config.git.main_branch == "main"
    assert ".git" in config.sync.ignore
