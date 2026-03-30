from __future__ import annotations

from pathlib import Path

from uiw.constants import MERGE_HEAD_REF
from uiw.errors import ValidationError
from uiw.infra.process import RunResult, command_exists, run_cmd


def check_git_available() -> bool:
    return command_exists("git")


def is_git_repo(path: Path) -> bool:
    result = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd=path, check=False)
    return result.returncode == 0 and result.stdout.strip() == "true"


def git_init(path: Path) -> None:
    run_cmd(["git", "init"], cwd=path)


def has_commits(repo: Path) -> bool:
    result = run_cmd(["git", "rev-parse", "--verify", "HEAD"], cwd=repo, check=False)
    return result.returncode == 0


def ensure_branch_exists(repo: Path, branch: str) -> None:
    current = run_cmd(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], cwd=repo, check=False)
    current_branch = current.stdout.strip()
    if current_branch == branch:
        return
    if branch_exists(repo, branch):
        run_cmd(["git", "checkout", branch], cwd=repo)
        return
    if has_commits(repo):
        run_cmd(["git", "checkout", "-b", branch], cwd=repo)
        return
    run_cmd(["git", "checkout", "--orphan", branch], cwd=repo)
    run_cmd(["git", "reset", "--mixed"], cwd=repo)


def branch_exists(repo: Path, branch: str) -> bool:
    result = run_cmd(["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=repo, check=False)
    return result.returncode == 0


def assert_branch_exists(repo: Path, branch: str) -> None:
    if not branch_exists(repo, branch):
        raise ValidationError(f"Branch does not exist: {branch}")


def create_branch(repo: Path, branch: str, from_ref: str) -> None:
    run_cmd(["git", "branch", branch, from_ref], cwd=repo)


def add_worktree(repo: Path, path: Path, branch: str, from_ref: str) -> None:
    run_cmd(["git", "worktree", "add", path.as_posix(), "-b", branch, from_ref], cwd=repo)


def remove_worktree(repo: Path, path: Path) -> None:
    run_cmd(["git", "worktree", "remove", path.as_posix()], cwd=repo)


def remove_branch(repo: Path, branch: str) -> None:
    run_cmd(["git", "branch", "-d", branch], cwd=repo)


def list_worktrees(repo: Path) -> list[dict]:
    result = run_cmd(["git", "worktree", "list", "--porcelain"], cwd=repo)
    entries: list[dict] = []
    current: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        entries.append(current)
    return entries


def get_current_branch(repo: Path) -> str:
    return run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo).stdout.strip()


def get_head_commit(repo: Path) -> str:
    return run_cmd(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()


def get_last_commit_summary(repo: Path) -> str:
    return run_cmd(["git", "log", "-1", "--oneline"], cwd=repo).stdout.strip()


def is_dirty(repo: Path) -> bool:
    return bool(run_cmd(["git", "status", "--porcelain"], cwd=repo).stdout.strip())


def has_unmerged_files(repo: Path) -> bool:
    return bool(get_unmerged_files(repo))


def get_unmerged_files(repo: Path) -> list[str]:
    output = run_cmd(["git", "diff", "--name-only", "--diff-filter=U"], cwd=repo).stdout
    return [line for line in output.splitlines() if line.strip()]


def is_merge_in_progress(repo: Path) -> bool:
    result = run_cmd(["git", "rev-parse", "-q", "--verify", MERGE_HEAD_REF], cwd=repo, check=False)
    return result.returncode == 0


def get_status_porcelain(repo: Path) -> list[str]:
    output = run_cmd(["git", "status", "--porcelain"], cwd=repo).stdout
    return [line for line in output.splitlines() if line.strip()]


def get_ahead_behind(repo: Path, base: str, branch: str) -> tuple[int, int]:
    result = run_cmd(["git", "rev-list", "--left-right", "--count", f"{base}...{branch}"], cwd=repo)
    left_count, right_count = result.stdout.strip().split()
    return int(right_count), int(left_count)


def diff_name_only(repo: Path, base_ref: str, head_ref: str = "HEAD") -> list[str]:
    output = run_cmd(["git", "diff", "--name-only", f"{base_ref}...{head_ref}"], cwd=repo).stdout
    return [line for line in output.splitlines() if line.strip()]


def diff_stat(repo: Path, base_ref: str, head_ref: str = "HEAD") -> str:
    return run_cmd(["git", "diff", "--stat", f"{base_ref}...{head_ref}"], cwd=repo).stdout


def diff_compact(repo: Path, base_ref: str, head_ref: str = "HEAD") -> str:
    return run_cmd(["git", "diff", "--compact-summary", f"{base_ref}...{head_ref}"], cwd=repo).stdout


def diff_name_status(repo: Path, base_ref: str, head_ref: str = "HEAD") -> list[tuple[str, str]]:
    output = run_cmd(["git", "diff", "--name-status", f"{base_ref}...{head_ref}"], cwd=repo).stdout
    parsed: list[tuple[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        status, path = line.split("\t", 1)
        parsed.append((status, path))
    return parsed


def merge_branch(repo: Path, branch: str) -> RunResult:
    return run_cmd(["git", "merge", branch], cwd=repo, check=False)


def merge_continue(repo: Path) -> RunResult:
    return run_cmd(["git", "commit", "--no-edit"], cwd=repo, check=False)


def merge_abort(repo: Path) -> RunResult:
    return run_cmd(["git", "merge", "--abort"], cwd=repo, check=False)


def git_add_all(repo: Path) -> None:
    run_cmd(["git", "add", "-A"], cwd=repo)


def has_staged_changes(repo: Path) -> bool:
    result = run_cmd(["git", "diff", "--cached", "--quiet"], cwd=repo, check=False)
    return result.returncode != 0


def commit(repo: Path, message: str) -> str:
    run_cmd(["git", "commit", "-m", message], cwd=repo)
    return get_head_commit(repo)


def commit_merge(repo: Path) -> str:
    run_cmd(["git", "commit", "--no-edit"], cwd=repo)
    return get_head_commit(repo)


def export_diff_patch(repo: Path, base_ref: str, head_ref: str = "HEAD") -> str:
    return run_cmd(["git", "diff", f"{base_ref}...{head_ref}"], cwd=repo).stdout
