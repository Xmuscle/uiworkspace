# UI Workspace CLI 用户使用文档

## 1. 工具简介

`uiw` 用于在 **SVN 仍为正式提交流程** 的前提下，提供本地多工作区能力。

核心思路：
- `svn-main`：正式 SVN working copy
- `git-main`：本地 Git 基线仓库
- `worktrees/*`：每个任务一个独立工作目录

你仍然使用 `svn commit` 提交，但日常开发切任务、并行需求、临时实验可以通过 `uiw` 管理。

---

## 2. 安装与运行

推荐做法是 **全局安装 `uiw` 命令**，这样后续在任意目录都可以直接执行 `uiw`。

### 2.1 推荐：全局安装

在仓库根目录执行：

```bash
uv tool install .
```

如果你是在开发过程中频繁修改当前仓库，推荐使用可编辑方式重新安装：

```bash
uv tool install --editable .
```

安装完成后可直接使用：

```bash
uiw --help
```

### 2.2 开发阶段的临时运行方式

如果你还不想安装到全局，也可以直接在仓库内运行：

```bash
uv run python -m uiw.cli --help
```

### 2.3 运行测试

```bash
uv run --with pytest pytest
```

---

## 3. 初始化工作区

命令：

```bash
uiw init <svn-main> <git-main> <worktrees>
```

示例：

```bash
uiw init D:/mmo-ui/svn-main D:/mmo-ui/git-main D:/mmo-ui/worktrees
```

作用：
- 检查 `svn` 和 `git` 命令可用
- 创建目录结构
- 初始化 `git-main`
- 生成配置文件 `config/workspace.yaml`
- 初始化 `config/workspaces.yaml`

注意：
- `svn`、`git`、`worktrees` 三个路径不能相同
- `git-main` 若已有异常 `.git` 状态会拒绝初始化
- `init` 不会自动创建 `svn-main/.ignore`，如需忽略同步内容请手工在 `svn-main` 下创建该文件
- Windows 下如果路径用了引号，**不要以 `\` 结尾**，否则命令行可能把结尾引号吞掉，导致参数解析异常，例如报 `Missing argument 'WORKTREES'`
- 推荐写法：去掉结尾反斜杠，例如 `uiw init "H:/path/to/svn-main" "G:/path/to/git-main" "G:/path/to/worktrees"`

---

## 4. 基本目录结构

初始化后会形成类似结构：

```text
D:/mmo-ui/
  svn-main/
  git-main/
  worktrees/
  patches/
  logs/
  config/
    workspace.yaml
    workspaces.yaml
```

---

## 5. 日常工作流

## 5.1 同步主线

```bash
uiw sync
```

可选：

```bash
uiw sync --message "sync from svn 2026-03-30 10:30"
```

作用：
1. 在 `svn-main` 中执行 `svn update`
2. 将 `svn-main` 文件同步到 `git-main`
3. 若有变更，则生成新的 baseline commit

忽略规则来源：
- 内建保护目录：如 `.git`、`.svn`、`worktrees`
- `svn-main/.ignore`

`.ignore` 支持：
- 空行
- `#` 注释
- 不带 `/` 的路径段规则
- 带 `/` 的相对路径前缀规则

示例：

```text
# 忽略任意 node_modules 目录
node_modules

# 忽略指定子树
docs/generated/
```

限制：
- 若 `git-main` 有未提交改动，`sync` 会拒绝执行
- 若 `git-main` 不是 Git 仓库，`sync` 会拒绝执行

---

## 5.2 创建新任务工作区

```bash
uiw new event-spring
```

或指定来源分支：

```bash
uiw new bugfix-chat --from-branch main
```

说明：
- 默认来源分支是配置里的 `default_new_from`
- workspace 名称只能包含字母、数字、`.`、`_`、`-`

失败场景：
- workspace 名已存在
- branch 名已存在
- 来源 branch 不存在
- 目标目录已存在

---

## 5.3 查看所有工作区

```bash
uiw list
```

输出会展示：
- 名称
- 分支
- 状态（clean / dirty / conflict / missing）
- 相对 `main` 的 ahead/behind
- 路径

---

## 5.4 查看单个工作区详情

```bash
uiw info event-spring
```

会展示：
- path
- branch
- head commit
- created_at
- from_branch
- last commit
- uncommitted 文件列表
- conflicts 列表

---

## 5.5 将主线合并进任务工作区

```bash
uiw refresh event-spring
```

作用：
- 在对应 worktree 中执行 `git merge main`

限制：
- 如果 worktree dirty，会拒绝 refresh
- 如果当前有 unresolved conflict，会拒绝 refresh
- 如果 merge 已在进行中，会拒绝 refresh

### 冲突后继续

```bash
uiw refresh-continue event-spring
```

### 冲突后放弃

```bash
uiw refresh-abort event-spring
```

### 查看当前冲突文件

```bash
uiw conflicts event-spring
```

推荐手工处理流程：

```bash
git status
git diff --name-only --diff-filter=U
uiw refresh-continue event-spring
```

---

## 5.6 查看工作区差异

默认摘要：

```bash
uiw diff event-spring
```

仅文件名：

```bash
uiw diff event-spring --name-only
```

统计：

```bash
uiw diff event-spring --stat
```

---

## 5.7 导出 patch

```bash
uiw export event-spring
```

输出位置：
- `patches/<workspace>-<timestamp>.patch`

用途：
- 临时归档
- 手工审查
- 共享参考

---

## 5.8 将任务改动回灌到 svn-main

```bash
uiw apply event-spring
```

作用：
1. 检查 workspace 无冲突
2. 检查 `svn-main` 干净
3. 计算相对 `main` 的改动
4. 备份将覆盖/删除的 `svn-main` 文件
5. 将工作区改动复制回 `svn-main`
6. 写 apply 日志

完成后建议手工执行：

```bash
svn status
svn diff
svn commit
```

限制：
- `svn-main` 有未提交改动时，禁止 apply
- workspace 有 unresolved conflicts 时，禁止 apply

安全保护：
- 工具会阻止 `../` 这类路径逃逸写入
- 会先做文件备份

---

## 5.9 删除工作区

```bash
uiw remove event-spring
```

保留分支：

```bash
uiw remove event-spring --keep-branch
```

当前限制：
- dirty worktree 默认不能删除
- 还没有 `--force`
- 还没有交互确认

---

## 5.10 环境检查

```bash
uiw doctor
```

会检查：
- `svn` 是否可用
- `git` 是否可用
- 配置是否可读
- `svn-main` 是否存在
- `git-main` 是否是 git repo
- `main` 分支是否存在
- registry 中 workspace 路径是否存在

---

## 6. 推荐使用流程

### 场景 A：开始新需求

```bash
uiw sync
uiw new event-april
uiw list
```

然后进入 `worktrees/event-april` 开发。

### 场景 B：插入紧急 bugfix

```bash
uiw new bugfix-mailbox
```

开发完成后：

```bash
uiw diff bugfix-mailbox
uiw apply bugfix-mailbox
```

然后进入 `svn-main`：

```bash
svn status
svn diff
svn commit
```

### 场景 C：主线更新后刷新任务分支

```bash
uiw sync
uiw refresh event-april
```

若冲突：

```bash
uiw conflicts event-april
uiw refresh-continue event-april
```

---

### 5.1.1 `.ignore` 使用建议

推荐把需要长期忽略的同步规则写在 `svn-main/.ignore`。

示例：

```text
# 忽略缓存目录
Temp

# 忽略生成目录
Library

# 忽略指定子路径
UI/Generated/
```

说明：
- 不带 `/` 的规则会按路径段匹配
- 带 `/` 的规则会按相对 `svn-main` 的路径前缀匹配
- 当前不支持完整 gitignore 语法，也不支持 `!` 反向规则

---

## 7. 常见问题

### 7.1 `sync` 失败：git-main has uncommitted changes
原因：
- `git-main` 里有本地脏改动

处理：
- 先检查 `git-main`
- 清理或提交后再执行 `uiw sync`

### 7.2 `new` 失败：Branch does not exist
原因：
- 指定的来源分支不存在

处理：
- 先确认 `git-main` 当前 baseline 分支是否正确
- 或改用已有 branch

### 7.3 `refresh` 失败：Workspace has uncommitted changes
原因：
- 当前任务工作区有未提交改动

处理：
- 先提交、stash 或手工整理后再 refresh

### 7.4 `apply` 失败：svn-main has uncommitted changes
原因：
- `svn-main` 已经有本地修改

处理：
- 先在 `svn-main` 清理状态，再执行 apply

### 7.5 `apply` 失败：Source file does not exist for apply
原因：
- diff 记录的源文件在 worktree 中缺失

处理：
- 检查 worktree 当前文件状态
- 确认是否有异常删除或未完成操作

### 7.6 `.ignore` 没生效
原因：
- `.ignore` 不在 `svn-main` 根目录
- 规则写法不符合当前支持的简化语法
- 规则本身没有匹配到实际相对路径

处理：
- 确认文件路径为 `svn-main/.ignore`
- 先用简单规则验证，例如 `Temp` 或 `UI/Generated/`
- 再执行一次 `uiw sync`

---

## 8. 当前版本限制

当前版本是可运行的 MVP 骨架增强版，仍有以下限制：
- `remove` 还没有 `--force`
- `doctor` 还不是完全一致性审计版
- `apply` 还没有 dry-run
- `.ignore` 目前不是完整 gitignore 语法，只支持注释、路径段规则和相对路径前缀规则
- 输出样式还会继续优化
- 真实 SVN/Git 集成测试还需要继续补齐

---

## 9. 推荐命令速查

```bash
uiw init D:/mmo-ui/svn-main D:/mmo-ui/git-main D:/mmo-ui/worktrees

uiw sync

uiw new event-spring
uiw list
uiw info event-spring

uiw refresh event-spring
uiw conflicts event-spring
uiw refresh-continue event-spring
uiw refresh-abort event-spring

uiw diff event-spring --name-only
uiw export event-spring

uiw apply event-spring

uiw remove event-spring

uiw doctor
```
