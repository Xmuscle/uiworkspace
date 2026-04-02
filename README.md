# uiworkspace

UI Workspace CLI (`uiw`) 是一个面向 SVN 团队的本地多工作区 CLI 工具，利用 Git mirror 和 Git worktree 提供更低成本的并行开发体验。

## 文档

- [技术设计文档](docs/technical-design.md)
- [用户使用文档](docs/user-guide.md)

## 当前状态

当前仓库已经具备可运行的 MVP 骨架，包括：
- `init`
- `sync`
- `new`
- `list`
- `info`
- `refresh`
- `conflicts`
- `diff`
- `export`
- `apply`
- `remove`
- `doctor`

`sync` 的忽略规则现在默认来自 `svn-main/.ignore`，不再使用 `sync.ignore` 配置项。

## 快速验证

```bash
uv run python -m uiw.cli --help
uv run --with pytest pytest
```