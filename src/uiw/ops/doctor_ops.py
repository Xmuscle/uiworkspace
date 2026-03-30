from __future__ import annotations

from uiw.models import DoctorCheck, WorkspaceConfig
from uiw.ops import git_ops, svn_ops
from uiw.services.workspace_registry import WorkspaceRegistry


def check_svn_command() -> DoctorCheck:
    ok = svn_ops.check_svn_available()
    return DoctorCheck(name="svn", ok=ok, detail="svn command available" if ok else "svn not found")


def check_git_command() -> DoctorCheck:
    ok = git_ops.check_git_available()
    return DoctorCheck(name="git", ok=ok, detail="git command available" if ok else "git not found")


def check_config_readable(config: WorkspaceConfig) -> DoctorCheck:
    return DoctorCheck(name="config", ok=True, detail=f"config loaded for {config.paths.git_main}")


def check_svn_main_exists(config: WorkspaceConfig) -> DoctorCheck:
    ok = config.paths.svn_main.exists()
    return DoctorCheck(name="svn-main", ok=ok, detail=str(config.paths.svn_main))


def check_git_main_repo(config: WorkspaceConfig) -> DoctorCheck:
    ok = config.paths.git_main.exists() and git_ops.is_git_repo(config.paths.git_main)
    return DoctorCheck(name="git-main", ok=ok, detail=str(config.paths.git_main))


def check_main_branch_exists(config: WorkspaceConfig) -> DoctorCheck:
    ok = config.paths.git_main.exists() and git_ops.branch_exists(config.paths.git_main, config.git.main_branch)
    return DoctorCheck(name="main-branch", ok=ok, detail=config.git.main_branch)


def check_registry_consistency(config: WorkspaceConfig, registry: WorkspaceRegistry) -> DoctorCheck:
    names = [meta.name for meta in registry.list_workspaces()]
    return DoctorCheck(name="registry", ok=True, detail=", ".join(names) if names else "no workspaces")


def check_worktree_paths_exist(registry: WorkspaceRegistry) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    for meta in registry.list_workspaces():
        checks.append(
            DoctorCheck(
                name=f"workspace:{meta.name}",
                ok=meta.path.exists(),
                detail=str(meta.path),
            )
        )
    return checks


def run_doctor(config: WorkspaceConfig, registry: WorkspaceRegistry) -> list[DoctorCheck]:
    checks = [
        check_svn_command(),
        check_git_command(),
        check_config_readable(config),
        check_svn_main_exists(config),
        check_git_main_repo(config),
        check_main_branch_exists(config),
        check_registry_consistency(config, registry),
    ]
    checks.extend(check_worktree_paths_exist(registry))
    return checks
