# Claude Code Skills

个人编写的 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 自定义技能集合，用于增强日常开发工作流。

## 技能列表

| 技能 | 触发场景 | 说明 |
|------|----------|------|
| [commit](commit/) | 创建 git commit | 按照 Google convention 风格自动生成规范的提交信息 |
| [debug](debug/) | 遇到 bug 或异常行为 | 五步法系统性调试：理解问题 → 复现 → 假设 → 隔离 → 验证 |
| [doc-control](doc-control/) | 创建/更新文档前 | 智能判断是否需要生成文档，防止过度文档化 |
| [explain](explain/) | "这段代码怎么工作的？" | 用类比、ASCII 图示和逐步分解来解释代码 |
| [python-style](python-style/) | 检查/修复 Python 代码风格 | 基于 PEP 8 / Google Style Guide，集成 Ruff、Black、isort、mypy |
| [refactor](refactor/) | "怎么改进这段代码？" | 检测代码异味，检查 SOLID 原则，提供 before/after 对比 |
| [review](review/) | 代码审查 | 从安全、正确性、性能、可读性、可维护性、最佳实践六个维度审查 |
| [sync-config](sync-config/) | 同步/备份 Claude 配置 | 将 `~/.claude/` 配置单向同步到远程 Git 仓库，支持预览和选择性恢复 |
| [test](test/) | 编写测试用例 | 生成单元测试和集成测试，支持 Jest、pytest、Go testing |
| [x2md](x2md/) | 保存 X/Twitter 内容 | 将推文/线程/长文转为 Markdown 并存入 Obsidian，自动补充 AI 分类和标签 |

## 安装

将本仓库克隆到 Claude Code 的 skills 目录：

```bash
git clone git@codeup.aliyun.com:696f3f56b28d0aba0f5e4371/Innovation-Project/dade-flexible-welding/claude_skills.git ~/.claude/skills
```

如果 `~/.claude/skills` 目录已有内容，可以将各技能文件夹单独复制进去。

## 目录结构

```
.
├── commit/          # Git 提交信息生成
│   └── SKILL.md
├── debug/           # 系统性调试
│   └── SKILL.md
├── doc-control/     # 文档生成控制
│   └── SKILL.md
├── explain/         # 代码解释
│   └── SKILL.md
├── python-style/    # Python 代码风格
│   └── SKILL.md
├── refactor/        # 代码重构建议
│   └── SKILL.md
├── review/          # 代码审查
│   └── SKILL.md
├── sync-config/     # 配置同步
│   └── SKILL.md
├── test/            # 测试用例生成
│   └── SKILL.md
└── x2md/            # X/Twitter 转 Markdown
    ├── SKILL.md
    └── scripts/
        └── x2md.py
```

## 使用方式

技能会在 Claude Code 对话中根据触发条件自动激活，也可以通过斜杠命令手动调用：

```
/commit          # 生成提交信息
/debug           # 启动调试流程
/review          # 审查代码
/test            # 生成测试
/explain         # 解释代码
/refactor        # 重构建议
/python-style    # 检查 Python 风格
/sync-config     # 同步配置
/x2md            # 转换 X/Twitter 内容
```

## 许可

个人使用。
