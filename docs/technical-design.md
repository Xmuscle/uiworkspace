# UI Workspace CLI 技术设计文档

## 1. 概述

`uiw` 是一个基于 Python 3.11+ 的本地 CLI 工具，用于在 **SVN 仍为正式上游** 的前提下，提供基于 **Git mirror + Git worktree** 的多工作区开发体验。

当前实现采用：
- CLI: Typer
- 输出: Rich
- 配置: YAML
- 文件模型: dataclass
- Git/SVN 调用: `subprocess.run(..., shell=False)` 封装

入口文件：`src/uiw/cli.py:22`

---

## 2. 当前代码结构

```text
src/uiw/
  cli.py
  constants.py
  errors.py
  models.py
  result.py

  commands/
    init_cmd.py
    sync_cmd.py
    new_cmd.py
    list_cmd.py
    info_cmd.py
    refresh_cmd.py
    conflicts_cmd.py
    diff_cmd.py
    export_cmd.py
    apply_cmd.py
    remove_cmd.py
    doctor_cmd.py

  config/
    defaults.py
    schema.py
    loader.py

  infra/
    process.py
    paths.py
    fs.py
    clock.py
    yaml_io.py
    json_io.py

  services/
    workspace_registry.py
    backup_service.py
    log_service.py
    status_service.py

  ops/
    svn_ops.py
    git_ops.py
    sync_ops.py
    workspace_ops.py
    diff_ops.py
    export_ops.py
    apply_ops.py
    doctor_ops.py

  ui/
    console.py
    formatters.py
    tables.py
```

---

## 3. 分层职责

### 3.1 commands
负责：
- 接收命令行参数
- 加载配置
- 调用 ops / services
- 渲染结果

例如：
- `src/uiw/commands/init_cmd.py:18`
- `src/uiw/commands/sync_cmd.py:12`
- `src/uiw/commands/apply_cmd.py:14`

### 3.2 ops
负责业务编排。

关键模块：
- `src/uiw/ops/sync_ops.py:49`：执行 `svn-main -> git-main`
- `src/uiw/ops/workspace_ops.py:40`：workspace 创建、refresh、remove
- `src/uiw/ops/apply_ops.py:40`：构造 apply plan 并回灌 `svn-main`
- `src/uiw/ops/doctor_ops.py:44`：环境检查

### 3.3 services
负责跨命令复用的中间服务：
- registry 读写：`src/uiw/services/workspace_registry.py:8`
- 备份：`src/uiw/services/backup_service.py:10`
- apply 日志：`src/uiw/services/log_service.py:10`
- workspace 状态聚合：`src/uiw/services/status_service.py:8`

### 3.4 infra
负责基础设施能力：
- 进程执行：`src/uiw/infra/process.py:24`
- 路径安全：`src/uiw/infra/paths.py:17`
- 文件复制 / 镜像同步：`src/uiw/infra/fs.py:44`
- YAML/JSON 序列化

### 3.5 ui
负责命令行输出，不参与业务逻辑。

---

## 4. 核心数据模型

定义在：`src/uiw/models.py:1`

主要类型：
- `WorkspacePaths`
- `GitSettings`
- `SyncSettings`
- `ApplySettings`
- `WorkspaceConfig`
- `WorkspaceMeta`
- `WorkspaceStatus`
- `FileChange`
- `ApplyPlan`
- `DoctorCheck`

说明：
- `SyncSettings` 当前仅作为保留扩展点，不再保存 `ignore` 列表
- sync 的忽略规则由内建保护项和 `svn-main/.ignore` 决定

这些模型使配置、状态和流程对象结构化，避免命令层直接操作原始 dict。

---

## 5. 配置与状态文件

### 5.1 主配置
位置：`config/workspace.yaml`

由 `init` 生成，加载入口：`src/uiw/config/loader.py:25`

主要内容：
- `paths`
- `git`
- `sync`
- `apply`

说明：
- `sync` 配置段当前不再保存 `ignore` 列表
- `sync` 的文件忽略规则默认从 `svn-main/.ignore` 读取

### 5.2 workspace registry
位置：`config/workspaces.yaml`

读写服务：`src/uiw/services/workspace_registry.py:8`

用于记录：
- workspace name
- branch
- path
- from_branch
- created_at

---

## 6. 核心流程设计

### 6.1 init
实现：`src/uiw/commands/init_cmd.py:18`

流程：
1. 检查 `svn` / `git` 命令存在
2. 检查 `svn` 路径存在
3. 检查 `svn/git/worktrees` 路径不重叠
4. 创建 `git-main`、`worktrees`、`config`、`patches`、`logs/backups`
5. 若 `git-main` 不是 Git repo，则初始化并确保存在 `main`
6. 写入 `workspace.yaml`
7. 初始化 `workspaces.yaml`

稳定性保护：
- 路径不能相同：`src/uiw/commands/init_cmd.py:27`
- 已存在异常 `.git` 状态直接报错：`src/uiw/commands/init_cmd.py:35`

### 6.2 sync
实现：`src/uiw/ops/sync_ops.py:49`

流程：
1. `assert_sync_allowed`
2. `svn update`
3. 将 `svn-main` 镜像同步到 `git-main`
4. `git add -A`
5. 若有 staged changes，则创建 baseline commit

稳定性保护：
- `git-main` 必须存在且是 git repo：`src/uiw/ops/sync_ops.py:38`
- `git-main` 有脏改动时拒绝：`src/uiw/ops/sync_ops.py:45`
- 永久保护 `.git`、`.svn` 和 `worktrees` 目录
- 额外从 `svn-main/.ignore` 读取忽略规则

`.ignore` 规则说明：
- 空行忽略
- `#` 开头为注释
- 不带 `/` 的规则按路径段匹配
- 带 `/` 的规则按相对 `svn-main` 的前缀路径匹配

### 6.3 new
实现：`src/uiw/ops/workspace_ops.py:40`

流程：
1. 校验 workspace 名称合法
2. 校验 registry 中不存在同名 workspace
3. 校验目标目录不存在
4. 校验 branch 不冲突
5. 校验来源 branch 存在
6. 执行 `git worktree add -b`
7. 写 registry

稳定性保护：
- workspace 名校验：`src/uiw/ops/workspace_ops.py:14`
- branch 冲突检查：`src/uiw/ops/workspace_ops.py:54`
- 来源 branch 必须存在：`src/uiw/ops/workspace_ops.py:56`

### 6.4 refresh
实现：`src/uiw/ops/workspace_ops.py:83`

流程：
1. 找到目标 workspace
2. 检查路径存在
3. 检查是否 merge in progress
4. 检查 unresolved conflicts
5. 检查 dirty 状态
6. merge `main` 进入当前 workspace
7. 若冲突，返回冲突文件列表

稳定性保护：
- merge 中禁止再次 refresh：`src/uiw/ops/workspace_ops.py:86`
- 冲突存在时拒绝继续：`src/uiw/ops/workspace_ops.py:88`
- dirty workspace 禁止 refresh：`src/uiw/ops/workspace_ops.py:90`

### 6.5 apply
实现：`src/uiw/ops/apply_ops.py:40`

流程：
1. 找到 workspace
2. 校验 workspace 路径存在
3. 校验无 unresolved conflicts
4. 校验 `svn-main` clean
5. 计算 `git diff --name-status main...HEAD`
6. 生成 `ApplyPlan`
7. 对待覆盖/删除文件做备份
8. 将 modified/added 文件复制回 `svn-main`
9. 删除 deleted 文件
10. 写 apply audit log

稳定性保护：
- `svn-main` dirty 时禁止 apply：`src/uiw/ops/apply_ops.py:32`
- source/target 路径都做 root boundary 校验：`src/uiw/ops/apply_ops.py:57`
- 源文件不存在时直接失败：`src/uiw/ops/apply_ops.py:64`

---

## 7. 错误模型

定义：`src/uiw/errors.py:1`

主要异常：
- `UIWError`
- `ConfigError`
- `ValidationError`
- `CommandExecutionError`
- `WorkspaceNotFoundError`
- `WorkspaceConflictError`
- `DirtyWorkspaceError`
- `UnsafePathError`
- `RegistryError`

CLI 层统一捕获入口：`src/uiw/cli.py:46`

---

## 8. 路径安全设计

关键函数：`src/uiw/infra/paths.py:17`

`ensure_within_root(path, root)` 会检查路径是否逃逸出目标根目录。当前主要用于：
- apply 复制文件
- apply 删除文件

这是为了避免类似 `../` 导致越界写入或删除。

---

## 9. 测试设计

当前测试目录：`tests/`

主要测试：
- 配置解析：`tests/test_schema.py:1`
- 路径安全：`tests/test_paths.py:1`
- registry：`tests/test_registry.py:1`
- apply 解析：`tests/test_apply_ops.py:1`
- workflow guard：`tests/test_workflow_guards.py:1`
- `.ignore` 匹配规则：`tests/test_sync_ignore_file.py:1`

已覆盖的关键稳定性场景：
- dirty `git-main` 禁止 sync
- 缺少 source branch 禁止 new
- dirty workspace 禁止 refresh
- 缺失 workspace path 禁止 apply
- conflict workspace 禁止 apply
- apply 路径逃逸被拦截

---

## 10. 当前已知限制

当前实现是 MVP 骨架增强版，仍有以下限制：

1. `remove` 还没有交互确认和 `--force`
2. `doctor` 仍偏基础，尚未核对所有 git worktree 与 registry 的一致性
3. `apply` 目前对目录删除、空目录清理未完全覆盖
4. CLI 输出目前偏结构化字典，尚未完全优化成最终产品风格
5. 还没有真实 Git/SVN 集成测试，只做了命令和逻辑层校验

---

## 11. 验证命令

当前可用验证方式：

```bash
uv run python -m uiw.cli --help
uv run --with pytest pytest
uv run python -m compileall src tests
```

最近验证结果：
- `pytest`: 16 passed
- `compileall`: 通过

---

## 12. 后续推荐演进

优先建议：
1. 增加 `CliRunner` 命令级测试
2. 增加真实 git repo 集成测试
3. 补 `remove --force` / 显式确认
4. 优化 `doctor` 一致性检查
5. 改善命令输出格式
