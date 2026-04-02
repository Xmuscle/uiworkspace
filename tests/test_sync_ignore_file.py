from pathlib import Path

from uiw.models import ApplySettings, GitSettings, SyncSettings, WorkspaceConfig, WorkspacePaths
from uiw.ops.sync_ops import build_sync_ignore_matcher, load_ignore_file_rules


def make_config(tmp_path: Path) -> WorkspaceConfig:
    svn_main = tmp_path / "svn-main"
    git_main = tmp_path / "git-main"
    worktrees_root = tmp_path / "worktrees"
    for path in [svn_main, git_main, worktrees_root, tmp_path / "patches", tmp_path / "logs", tmp_path / "config", tmp_path / "logs" / "backups"]:
        path.mkdir(parents=True, exist_ok=True)
    return WorkspaceConfig(
        paths=WorkspacePaths(
            svn_main=svn_main,
            git_main=git_main,
            worktrees_root=worktrees_root,
            patches_root=tmp_path / "patches",
            logs_root=tmp_path / "logs",
            config_root=tmp_path / "config",
            backup_root=tmp_path / "logs" / "backups",
        ),
        git=GitSettings(
            main_branch="main",
            default_new_from="main",
            refresh_mode="merge",
            sync_commit_prefix="sync from svn",
        ),
        sync=SyncSettings(),
        apply=ApplySettings(backup=True, backup_root=tmp_path / "logs" / "backups", mode="copy"),
    )


def test_load_ignore_file_rules_returns_empty_when_missing(tmp_path: Path) -> None:
    segments, prefixes = load_ignore_file_rules(tmp_path / ".ignore")
    assert segments == set()
    assert prefixes == []


def test_ignore_file_supports_segments_comments_and_prefixes(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    (config.paths.svn_main / ".ignore").write_text(
        "# comment\nnode_modules\n/docs/generated/\nTemp\n",
        encoding="utf-8",
    )
    matcher = build_sync_ignore_matcher(config)
    assert matcher(Path("web/node_modules/react/index.js")) is True
    assert matcher(Path("docs/generated/api.md")) is True
    assert matcher(Path("Temp/cache.txt")) is True
    assert matcher(Path("docs/manual/readme.md")) is False


def test_ignore_file_keeps_internal_protection_without_file(tmp_path: Path) -> None:
    config = make_config(tmp_path)
    matcher = build_sync_ignore_matcher(config)
    assert matcher(Path(".git/config")) is True
    assert matcher(Path(".svn/wc.db")) is True
    assert matcher(Path("src/main.py")) is False
