---
name: commit
description: Generate git commit messages following Google's convention style. Use when user asks to create a commit, make a git commit, or write commit message.
allowed-tools: Bash, Grep, Read, Glob
---

# Git Commit Message Generator (Google Style)

You are specialized in creating clear, structured git commit messages following **Google's convention style**. Before committing, you automatically format code to ensure style consistency.

## Step 0: Pre-commit — Auto Format

Before analyzing changes, automatically format staged/changed files by language:

```bash
# Detect changed file types
CHANGED_PY=$(git diff --cached --name-only --diff-filter=ACMR -- '*.py' 2>/dev/null)
CHANGED_JS=$(git diff --cached --name-only --diff-filter=ACMR -- '*.js' '*.ts' '*.tsx' '*.jsx' 2>/dev/null)
CHANGED_CPP=$(git diff --cached --name-only --diff-filter=ACMR -- '*.cpp' '*.cc' '*.h' '*.hpp' 2>/dev/null)
```

| Language | Format Command | Lint Command |
|----------|---------------|-------------|
| Python (.py) | `uvx ruff format <files>` | `uvx ruff check <files>` |
| JS/TS (.js/.ts/.tsx) | `npx prettier --write <files>` | `npx eslint <files>` |
| C++ (.cpp/.h) | `clang-format -i <files>` | — |

**Rules**:
- Only format files that are already staged (`git diff --cached`)
- After formatting, re-stage the formatted files: `git add <files>`
- Lint warnings are informational — report but don't block (except errors)
- If no formatter is installed, skip with a warning and continue
- Markdown files: skip formatting

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

## Type Values

| type | 含义 | 示例 |
|------|------|------|
| feat | 新功能 | `feat(chingmu): 新增 TCP 位置标定模块` |
| fix | 修复 bug | `fix(vision): 修复检测模型加载路径` |
| refactor | 重构（不改行为） | `refactor(sdk): 抽取公共基类` |
| docs | 文档 | `docs(readme): 更新部署说明` |
| test | 测试 | `test(core): 新增几何变换单元测试` |
| chore | 杂务 | `chore(data): 清理过期日志` |
| style | 格式调整 | `style(api): 统一缩进和导入排序` |
| perf | 性能优化 | `perf(robomimic): 优化推理速度` |
| build | 构建/依赖 | `build(deps): 升级 opencv 到 4.9` |
| ci | CI 配置 | `ci(pipeline): 添加 commitlint 检查` |
| sync | 配置同步 | `sync(skills): 同步 2026-03-25 更新` |

## Breaking Changes

For breaking changes, append `!` after the type:

```
feat(api)!: 移除旧版标定接口
```

## Guidelines

1. type 后**半角冒号 + 空格**，禁止全角冒号 `：` 和无空格 `feat:xxx`
2. scope 可选但推荐，按模块填写
3. subject 用中文，**动词开头**（新增/修复/重构/更新/删除/优化/上传/迁移）
4. subject 不超过 50 字，不加句号
5. body 说明 what 和 why，wrap at 72 chars
6. footer 关联 Issue 或标注 BREAKING CHANGE

## Steps

1. **Format**: Run pre-commit format (Step 0) on staged files
2. `git status` to see all changes
3. `git diff --staged` to see staged changes (if any)
4. `git diff` to see unstaged changes (if no staged changes)
5. `git log --oneline -5` to understand recent commit style
6. Analyze the changes and generate an appropriate commit message
7. `git add` for relevant files (ask user first if needed)
8. Create the commit with the generated message

## Example Output

Simple commit:
```
feat(vision): 新增视觉检测模块
```

Commit with body:
```
feat(auth): Add OAuth2 login support

Implement Google and GitHub OAuth authentication flow.
Users can now sign in using their existing social media accounts.

- Add OAuth controller with callback handling
- Update user model to store provider information
- Configure environment variables for client credentials

Closes #142
```

Always explain your reasoning for the chosen type before creating the commit.
