---
name: kb
description: "管理 Obsidian 知识库 — 写笔记、记点子、搜索内容、综合分析、维护个人洞察。当用户说'记个点子'、'记下来'、'搜一下知识库'、'总结一下'、'有什么关于...'、'知识库有什么'，或任何涉及保存/查找/综合知识的操作时使用。"
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Obsidian 知识库管理

管理 `~/Documents/obsidian/mixiaomi` vault 的写入、检索、综合、洞察和浏览操作。

**边界**: X/Twitter 链接 → 拒绝，提示用户使用 `x2md` skill。本 skill 管理除 `X收藏/` 写入外的所有操作（可读取 `X收藏/` 用于检索和综合）。

## 操作模式

根据用户意图选择模式：

| 模式 | 触发词 | 操作 |
|------|--------|------|
| **write** | "记个点子"、"新想法"、"记下来"、"coding心得"、"我想做..." | 写入笔记 |
| **search** | "搜一下"、"有什么关于..."、"找一下"、"知识库里..." | 搜索 vault |
| **synthesize** | "总结一下XX主题"、"综合分析"、"对比一下" | 生成综合笔记 |
| **insight** | "更新洞察"、"我最近在想..."、"加到洞察里" | 追加到洞察文件 |
| **browse** | "知识库有什么"、"看看最近的笔记"、"列一下" | 列出 vault 内容 |

---

## 1. Write 模式

### 1.1 目录选择

根据内容类型自动选目录：

| 内容类型 | 目录 | 示例 |
|---------|------|------|
| 产品想法、项目企划、创业点子 | `创意点子/` | "做一个 AI 读书助手" |
| 技术笔记、学习总结、概念记录 | `知识库/` | "MCP 协议工作原理" |
| 编程心得、开发经验、Vibe Coding | `Vibe Coding/` | "用 Claude Code 的体验" |
| X/Twitter 链接 | **拒绝** | 提示: "这是 X 链接，请用 `/x2md` 保存" |

不确定时问用户。

### 1.2 Frontmatter 格式

```yaml
---
title: "标题"
type: idea | note | article
date: YYYY-MM-DD
tags:
  - 分类/子分类
category: 分类/子分类
status: raw
---
```

**type 对照**:
- `idea` → `创意点子/`
- `note` → `知识库/`、`Vibe Coding/`
- `article` → `知识库/`（长篇技术文章）

### 1.3 Tag 分类体系

从以下 9 个层级标签中选择 1-3 个最匹配的：

```
AI/发展        — 模型发布、能力进展、AGI
AI/应用        — 工具、工作流、Agent
AI/影响        — 就业、社会、伦理
技术/趋势      — MCP、CLI-first、平台趋势
技术/开发      — 编程技巧、架构、Vibe Coding
商业/创业      — 创业、融资、商业
商业/产品      — 产品思维、UX
思考/创意      — 灵感、创新方法
思考/社会      — 监管、哲学、未来
```

### 1.4 写入流程

1. 判断内容类型 → 选目录
2. 生成 frontmatter（title, type, date, tags, category, status: raw）
3. 写正文内容（用户提供的内容，整理为结构化 Markdown）
4. 末尾追加空的 `## 我的笔记` 区域
5. 文件名：用中文，简洁概括内容主题（如 `AI读书助手.md`）

### 1.5 写入示例

用户: "记个点子：做一个 AI 读书助手，帮人拆书"

```markdown
---
title: "AI读书助手"
type: idea
date: 2026-02-16
tags:
  - AI/应用
  - 商业/产品
category: AI/应用
status: raw
---

# AI读书助手

做一个 AI 读书助手，帮人拆书。

[整理用户提供的具体内容...]

## 我的笔记

```

写入路径: `~/Documents/obsidian/mixiaomi/创意点子/AI读书助手.md`

---

## 2. Search 模式

### 2.1 搜索策略

根据用户查询选择合适的搜索方式，**搜索范围覆盖全 vault（包括 X收藏/）**：

| 搜索方式 | Grep 模式 | 场景 |
|---------|-----------|------|
| 按标签 | `Grep "^  - AI/发展"` (glob: `*.md`) | "关于 AI 发展的" |
| 按分类 | `Grep "^category: AI/发展"` | "AI 发展分类下的" |
| 按关键词 | `Grep "Agent"` (glob: `*.md`) | "关于 Agent 的内容" |
| 按时间 | `Grep "^date: 2026-02"` | "最近的笔记" |
| 按类型 | `Grep "^type: idea"` | "所有点子" |

### 2.2 结果展示

对每个匹配文件，读取 frontmatter 并展示：

```
📄 标题 | 目录 | 分类 | 日期
   摘要（frontmatter summary 或正文前 50 字）
```

表格形式汇总：

| 标题 | 目录 | 分类 | 日期 |
|------|------|------|------|

---

## 3. Synthesize 模式

### 3.1 综合流程

1. 用户指定分类或主题（如 "AI/发展"）
2. 搜索匹配文章（全 vault，包括 X收藏/）
3. **至少 2 篇**才执行综合，否则提示 "相关文章不足"
4. 读取所有匹配文章的 frontmatter + 正文
5. 生成综合笔记

### 3.2 综合笔记结构

```yaml
---
title: "XX综合洞察"
type: synthesis
date: YYYY-MM-DD
updated: YYYY-MM-DD
source_count: N
tags:
  - 对应分类标签
category: 对应分类
status: raw
---
```

正文结构：

```markdown
# [主题]综合洞察

## 核心趋势
- ...

## 观点对比
| 来源 | 观点 | 立场 |
|------|------|------|

## 时间线
- YYYY-MM-DD: ...

## 知识空白
- 尚未覆盖的角度...

## 来源文章
- [[文章1标题]]
- [[文章2标题]]
```

### 3.3 写入规则

- 路径: `~/Documents/obsidian/mixiaomi/知识库/综合/`
- 文件名: `<分类简称>综合.md`（如 `AI发展综合.md`）
- **已存在则 Edit 更新**，追加新内容，不覆盖已有
- 更新时同步更新 frontmatter 的 `updated` 和 `source_count`

---

## 4. Insight 模式

### 4.1 目标文件

`~/Documents/obsidian/mixiaomi/知识库/我的洞察.md`

### 4.2 文件结构

```markdown
---
title: "我的洞察"
type: insight
updated: YYYY-MM-DD
---

# 我的洞察

## 核心关注方向
<!-- 持续关注的主题和方向 -->

## 关键观点
<!-- 通过阅读和对话积累的核心认知 -->

## 待探索问题
<!-- 还没有答案、值得深入研究的问题 -->

## 阅读脉络
<!-- 记录阅读顺序和思考演进 -->
```

### 4.3 操作流程

1. Read 当前 `我的洞察.md`
2. 根据用户内容判断属于哪个区域：
   - 关注方向 → `## 核心关注方向`
   - 观点/认知 → `## 关键观点`
   - 问题 → `## 待探索问题`
   - 阅读记录 → `## 阅读脉络`
3. **Edit 追加**到对应区域，不覆盖已有内容
4. 格式: `- [YYYY-MM-DD] 内容`
5. 更新 frontmatter 的 `updated` 日期

---

## 5. Browse 模式

### 5.1 浏览流程

1. `Glob "*.md"` 列出各目录下的文件（路径: `~/Documents/obsidian/mixiaomi`）
2. 对每个目录分组统计
3. 读取每个文件的 frontmatter（仅前 10 行）
4. 表格展示

### 5.2 展示格式

```
知识库 (N 篇)
| 标题 | 类型 | 分类 | 日期 |
|------|------|------|------|

创意点子 (N 篇)
| 标题 | 类型 | 日期 |
|------|------|------|

Vibe Coding (N 篇)
| 标题 | 日期 |
|------|------|

X收藏 (N 篇)
| 标题 | 作者 | 分类 | 日期 |
|------|------|------|------|
```

---

## 参考资料

详细 schema、示例和搜索模式见 `references/architecture.md`（按需加载）。

加载方式: `Read ~/.claude/skills/kb/references/architecture.md`
