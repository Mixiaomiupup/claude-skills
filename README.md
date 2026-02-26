# Claude Code Skills

> 15 个自研 skill | 1 个第三方 | 6 大类

个人 Claude Code skill 合集，通过 `cc-sync` 同步至 GitHub 和云效。

## 总览

| Skill | 分类 | 触发词 | 一句话 |
|-------|------|--------|--------|
| [ucal](ucal/SKILL.md) | 内容与知识 | 给链接、"调研XX" | 跨平台内容深度分析与话题调研 |
| [kb](kb/SKILL.md) | 内容与知识 | "记下来"、"搜知识库" | Obsidian 知识库管理 |
| [x2md](x2md/SKILL.md) | 内容与知识 | X 链接 + "保存" | 推文/线程转 Markdown 存 Obsidian |
| [gemini-image](gemini-image/SKILL.md) | 图像与媒体 | "画一张"、"这图是什么" | Gemini AI 图片生成/编辑/理解 |
| [review](review/SKILL.md) | 代码质量 | "review"、"审查" | 六维度代码审查 |
| [python-style](python-style/SKILL.md) | 代码质量 | "check style" | PEP 8 风格检查 |
| [refactor](refactor/SKILL.md) | 代码质量 | "重构" | 重构建议 |
| [debug](debug/SKILL.md) | 代码质量 | bug、报错 | 系统性调试 |
| [test](test/SKILL.md) | 代码质量 | "写测试" | 测试生成 |
| [commit](commit/SKILL.md) | 开发流程 | "提交" | Google convention commit |
| [remote-repos](remote-repos/SKILL.md) | 开发流程 | push/pull、PR | GitHub + 云效操作 |
| [explain](explain/SKILL.md) | 开发流程 | "explain this" | 代码图解 |
| [server](server/SKILL.md) | 基础设施 | SSH、部署 | 阿里云服务器管理 |
| [sync-config](sync-config/SKILL.md) | 基础设施 | "sync"、"备份配置" | 配置与 skill 双平台同步 |
| [doc-control](doc-control/SKILL.md) | 文档 | 创建/更新文档前 | 文档生成控制 |

---

## 内容与知识

### [ucal](ucal/SKILL.md) — 跨平台内容分析与话题调研

这是花了最多心思打磨的 skill 之一。核心思路是：ucal MCP 解决"怎么取数据"，skill 解决"取到后怎么分析"。

**两个模式**：

- **Read 模式** — 给一个链接，自动识别平台，按平台特征差异化分析。不是简单总结正文，而是根据平台内容结构做不同侧重：
  - **小红书**：帖子本身就几句话，真正的信息在评论区。分析重心放在评论观点图谱 — 合并相似观点、提取争议焦点、挖出被忽略的独特视角
  - **知乎**：长文答案，价值在论证结构。拆解核心论点、论据链、引用数据，并指出论证薄弱点
  - **X/Twitter**：推文短小，重点在观点提炼和传播度分析（转赞比异常检测）
  - **通用网页**：纯内容提炼

- **Research 模式** — 说"调研XX"触发。这是一个完整的调研流程，不是简单搜几篇凑一起：
  1. **问题锐化**：不直接搜原始词，先拆成子问题，生成语义变体搜索词（比如"调研火锅蘸料"→ 拆出"选择决策/身份认同/情绪争议"三个角度）
  2. **选帖策略**：从搜索结果中选 3-4 篇，要求互动量梯度（高+低）、立场分布（正+反）、作者多样性
  3. **Pre-read hypothesis**：读之前先写预期，读完后对照验证 — 被证实的、被推翻的、意外发现的
  4. **证据追踪**：每个判断都要挂引用证据和来源，区分"直接发现"和"推断"
  5. **反思决策**：默认 SUFFICIENT，只有能说出具体缺口和具体搜索词时才追搜（上限 6 篇）
  6. **叙事报告**：不按帖子顺序排列，按洞察惊喜度排列。包含"扎心原文"（情感冲击力最强的评论）和"社区真正在争什么"（挖争议背后的断层线）

**常用说法**：`帮我看看这个链接`、`分析一下`、`调研XX话题`、`大家怎么看`

---

### [kb](kb/SKILL.md) — Obsidian 知识库管理

管理 `~/Documents/obsidian/mixiaomi` vault，五种模式覆盖知识管理全流程：

- **write**：写笔记/记点子，自动按内容类型分目录（创意点子/知识库/Vibe Coding），带 9 类标签体系的 frontmatter
- **search**：在 vault 中搜索内容
- **synthesize**：跨笔记综合分析，生成综合笔记
- **insight**：追加个人洞察和反思
- **browse**：列出 vault 内容概览

与 x2md 有明确边界：X/Twitter 链接一律拒绝，提示走 x2md。

**常用说法**：`记个点子`、`记下来`、`搜一下知识库`、`总结一下XX主题`

---

### [x2md](x2md/SKILL.md) — 推文转 Markdown

把 X/Twitter 的推文、线程、长文转成干净的 Markdown 存进 Obsidian。不只是格式转换 — 保存后还会做 AI enrichment：自动分类（9 个类目如 AI/发展、技术/趋势、商业/创业等）、打标签、写中文摘要，把 `status` 从 `raw` 改为 `enriched`。

**常用说法**：`保存这条推文`、给一个 x.com 链接

---

## 图像与媒体

### [gemini-image](gemini-image/SKILL.md) — Gemini AI 图片工具

通过 Vertex AI 调用 Gemini 模型，三种模式：

- **generate**：文字描述生成图片，支持写实、水彩、插画、油画、3D 等风格
- **edit**：在现有图片上修改（加元素、换风格、去除物体）
- **understand**：分析图片内容，回答关于图片的问题

**常用说法**：`画一张日落`、`这张图里是什么`、`给照片加彩虹`、`generate a logo`

---

## 代码质量

日常写代码用的一组工具，各司其职：

| Skill | 做什么 | 说一句 |
|-------|--------|--------|
| [review](review/SKILL.md) | 安全/正确性/性能/可读性/可维护/最佳实践，六个维度扫一遍，按 critical/important/optional 分级 | `review 一下` |
| [python-style](python-style/SKILL.md) | 用 ruff/black/isort/mypy 检查 PEP 8，自动修复 | `check style` |
| [refactor](refactor/SKILL.md) | 找 code smell，检查 SOLID，给出 before/after 对比 | `重构这段` |
| [debug](debug/SKILL.md) | 理解问题 → 复现 → 假设 → 隔离 → 验证修复，系统性调试 | `帮我 debug` |
| [test](test/SKILL.md) | Arrange-Act-Assert 模式，支持 Python/JS/TS/Go | `写测试` |

---

## 开发流程

| Skill | 做什么 | 说一句 |
|-------|--------|--------|
| [commit](commit/SKILL.md) | 按 Google convention 生成 commit message，支持 feat/fix/chore 等类型 | `提交` |
| [remote-repos](remote-repos/SKILL.md) | 双平台操作 — GitHub 用 gh CLI，云效用 MCP，覆盖 repo/branch/PR/CI/CD | `create PR`、`push` |
| [explain](explain/SKILL.md) | 用全局概览、ASCII 图、类比、逐步分解来解释代码，适配不同水平 | `explain this` |

---

## 基础设施

### [sync-config](sync-config/SKILL.md) — 配置同步系统 (cc-sync)

另一个花了大力气的 skill。解决的问题：Claude Code 的配置散落在 `~/.claude/` 下的十几个文件和目录里（CLAUDE.md、settings、hooks、agents、commands、plans、plugins、15 个 skill...），怎么在多台机器间保持同步，怎么安全地推到远程仓库。

**架构设计**：

配置和 skill 拆成两个独立 Git 仓库，各自推到 GitHub + 云效双平台：

| 组件 | 仓库 | 内容 |
|------|------|------|
| **config** | `claude-config` | CLAUDE.md、settings、hooks、agents、commands、output-styles、plans 基础设施、plugins |
| **skills** | `claude-skills` | 15 个自研 skill（不含第三方） |
| **第三方** | 各自独立仓库 | baoyu-skills 等，通过 `component-manifest.json` 追踪 |

**核心机制**：

- **脱敏系统**：推送前自动替换敏感信息 — settings.json 里的 API token、server/SKILL.md 里的密码和 IP、gemini-image/SKILL.md 里的 GCP 凭据。规则在 `component-manifest.json` 的 `sanitize` 字段里声明，cc-sync 通用循环遍历处理
- **Staging 隔离**：不直接操作本地文件，先 rsync 到 `/private/tmp/` 下的 staging 目录，在 staging 里脱敏、diff、commit，再 push
- **Dry-run 优先**：每次推送先 `--dry-run` 预览变更，确认后再执行
- **锁机制**：防止并发 push 冲突
- **Pull 恢复**：新机器上三步 bootstrap — clone config repo、复制 cc-sync 脚本、`cc-sync pull`，本地 token 会自动保留

**常用命令**：

```bash
cc-sync status                    # 查看同步状态
cc-sync push --dry-run            # 预览变更
cc-sync push --yes                # 推送（跳过确认）
cc-sync push --target skills      # 只推 skills
cc-sync pull                      # 从远程拉取恢复
```

---

### [server](server/SKILL.md) — 阿里云服务器

阿里云 Ubuntu 服务器管理（华东 2，2 vCPU / 2 GiB），SSH 连接、部署流程、nginx 配置、服务管理。

**常用说法**：`部署`、`看看服务器状态`

---

## 文档

### [doc-control](doc-control/SKILL.md) — 文档生成控制

防止过度文档化的门控。把变更分为 Level 1-3，检查项目文档模式（strict/standard/comprehensive），决定该创建、更新还是跳过文档。

---

## 第三方

| Skill | 来源 | 备注 |
|-------|------|------|
| baoyu-skills | [baoyu/claude-code-skills](https://github.com/baoyu/claude-code-skills) | 独立 Git 仓库，在 `component-manifest.json` 中追踪 |

## 同步

```bash
cc-sync push --target skills --dry-run   # 预览 skill 变更
cc-sync push --target skills --yes       # 推送
cc-sync status                           # 查看状态（应显示 15/15）
```
