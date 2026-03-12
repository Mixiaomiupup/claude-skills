# Universal Article Gen Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade article-gen from news-only to a universal 6-type article generation engine, with shared category index.

**Architecture:** article-gen SKILL.md is rewritten to support 6 article types (news/architecture/review/tutorial/notes/essay) with type inference, per-type frontmatter extensions, recommended body templates, and a shared category index file. kb SKILL.md is updated to read categories from the same index file instead of hardcoding.

**Tech Stack:** Markdown skill files, Obsidian vault

---

### Task 1: Create category index file

**Files:**
- Create: `~/Documents/obsidian/mixiaomi/meta/categories.md`

**Step 1: Create meta directory**

Run: `mkdir -p ~/Documents/obsidian/mixiaomi/meta`

**Step 2: Create categories.md**

```markdown
---
title: "Category Index"
description: "Shared category registry for article-gen and kb skills"
updated: 2026-03-10
---

# Category Index

Article-gen and kb skills read from this file. Semi-auto expandable: Claude proposes new categories, user confirms, then append here.

Format: `category` - description

## AI
- `AI/发展` - 模型发布、能力进展、AGI
- `AI/应用` - 工具、工作流、Agent
- `AI/影响` - 就业、社会、伦理

## 技术
- `技术/趋势` - MCP、CLI-first、平台趋势
- `技术/开发` - 编程技巧、架构、Vibe Coding
- `技术/架构` - 系统设计、架构分析、模块设计

## 商业
- `商业/创业` - 创业、融资、商业
- `商业/产品` - 产品思维、UX

## 思考
- `思考/创意` - 灵感、创新方法
- `思考/社会` - 监管、哲学、未来
- `思考/成长` - 个人成长、学习方法、心态
```

**Step 3: Verify file**

Run: `cat ~/Documents/obsidian/mixiaomi/meta/categories.md`
Expected: File contents as above

**Step 4: Commit**

```bash
cd ~/Documents/obsidian/mixiaomi && git add meta/categories.md && git commit -m "feat: add shared category index for article-gen and kb skills"
```

---

### Task 2: Rewrite article-gen SKILL.md

**Files:**
- Modify: `~/.claude/skills/article-gen/SKILL.md` (full rewrite)

**Step 1: Read current SKILL.md**

Run: Read `~/.claude/skills/article-gen/SKILL.md`
Purpose: Confirm current content before overwrite

**Step 2: Write new SKILL.md**

Replace entire file with the following content:

````markdown
---
name: article-gen
description: "Universal article generation engine. Supports 6 article types: news, architecture, review, tutorial, notes, essay. Orchestrates convert -> enrich -> translate -> cover image -> publish. Use when user shares a link to save, says '保存', '写个测评', '架构分析', '记个教程', '读书笔记', '分享到飞书', or any article generation flow."
---

# Article Gen

通用文章生成引擎。支持 6 种文章类型，统筹从素材到发布的完整流程。

## 文章类型 (`type`)

| type | 说明 | 典型输入 | 典型触发 |
|------|------|---------|---------|
| `news` | 资讯/推文转述 | X 链接、新闻 URL | "保存这条推文"、X 链接 |
| `architecture` | 技术架构分析 | GitHub 仓库、代码笔记 | "架构分析"、GitHub 链接 |
| `review` | 产品/项目测评 | 产品 URL、试用笔记 | "测评一下"、"对比" |
| `tutorial` | 技术教程 | 问题描述、代码片段 | "写个教程"、"怎么做" |
| `notes` | 读书/论文笔记 | PDF、文章链接、手写要点 | "读书笔记"、"读完了" |
| `essay` | 个人观点/思考 | 口述、大纲、零散想法 | "我觉得"、"想聊聊" |

### 类型推断（混合模式）

根据输入自动推断，推断不了就问用户：

- X/Twitter 链接 → `news`
- GitHub 链接 → `architecture`
- 用户说"测评/对比/评测" → `review`
- 用户说"怎么做/教程/步骤" → `tutorial`
- 用户说"读完了/笔记/摘录" → `notes`
- 用户说"我觉得/想聊聊/观点" → `essay`
- 推断不了 → 问用户选择

## 调用的 Skill

| Skill | 职责 | 何时调用 |
|-------|------|---------|
| `x2md` | X/Twitter → Markdown 转换 | `news` 类型且输入是 X 链接时 |
| `cover-image` | 封面配图（5D 风格 + 生图） | enrichment 后（所有类型） |
| `feishu` | 飞书知识库发布 + 全员广播 | 用户确认发布时（所有类型） |

`x2md` 和 `cover-image` 是独立 skill，不知道彼此的存在。`article-gen` 负责串联它们。

## 分类体系 (`category`)

**`category` 与 `type` 解耦**：`type` 描述文章形式，`category` 描述内容领域。

**Category 列表从索引文件读取**：`~/Documents/obsidian/mixiaomi/meta/categories.md`

**半自动扩展机制**：
1. Enrichment 时从索引文件读取已知 category 列表
2. 如果内容不属于任何已知 category，提议一个新 category（遵循 `一级/二级` 格式）
3. 用户确认后，追加到索引文件对应一级分类下
4. 已确认的 category 下次直接可用

## 工作流

```
输入 → 类型推断 → 转换 → Enrichment → 翻译 → 配图 → 发布 → 报告
  │        │         │        │          │       │       │       │
  │    自动/问     按type   Claude     Claude  cover   feishu  feishu
  │     用户      分支      (内置)     (内置)  -image  (skill) (skill)
  │                                           (skill)
  ▼
 报告结果
```

### Step 0: 类型推断

根据上文「类型推断」规则确定 `type`。推断不了就问用户。

### Step 1: 转换

根据 `type` 和输入来源调用对应转换工具：

| type | 输入 | 转换方式 |
|------|------|---------|
| `news` | X 链接 | 调用 `x2md` skill → `.md`（`status: raw`） |
| `news` | 其他 URL | 调用 `ucal` 抓取 + 存 Markdown |
| `architecture` | 项目路径或笔记 | 用户已完成研究，直接提供素材 |
| `review` | 产品 URL 或试用笔记 | 用户已完成研究，直接提供素材 |
| `tutorial` | 代码片段 / 问题描述 | 用户直接提供 |
| `notes` | PDF / URL / 手写要点 | ucal 抓取或用户直接提供 |
| `essay` | 口述 / 大纲 | 用户直接提供 |
| 所有 | 本地已有 .md | 跳过转换，直接进入 enrichment |

**研究与写作分离**：非 `news` 类型的前置研究（代码探索、产品试用、资料搜集）在 article-gen 之外完成。article-gen 从"有素材"开始。

### Step 2: Enrichment

读取素材，Claude 分析内容并生成文章：

a. **分类**（category）：从 `~/Documents/obsidian/mixiaomi/meta/categories.md` 读取列表，选最匹配的。不匹配则提议新 category。

b. **标签**（tags）：1-3 个 category 级标签

c. **摘要**（summary）：3-5 条中文要点

d. **正文生成/重组**：按 `type` 加载推荐正文模板（见下文），根据素材灵活调整

e. **扩展字段**：填充当前 type 的扩展字段（有数据就填，没有不强制）

f. **更新 frontmatter**：填入所有字段，`status: raw` → `status: enriched`

g. 追加 `## 我的笔记` 空节（供后续笔记用）

### Step 3: 翻译

如果 `lang` 不是 `zh`（非中文内容），重组正文结构：

```markdown
## 翻译
（中文译文）

## 原文
（英文原文）
```

翻译标准：信达雅，专有名词不翻译，技术术语保留英文并括号注中文。

**注意**：`tutorial` 和 `architecture` 中的代码块不翻译。

### Step 4: 配图

调用 `cover-image` skill（quick 模式）：

```
cover-image skill:
- 文章路径: <.md 绝对路径>
- category: <从 frontmatter 读取>
- 模式: quick
```

`cover-image` 会自动完成风格选择 → 生图 → 嵌入文章。

### Step 5: 飞书发布

询问用户「是否同步到飞书知识库？」

- **用户确认**：
  a. 根据 `category` 一级分类确定目标飞书节点（查 `feishu` skill 的标签→节点映射表）
  b. 获取 `tenant_access_token`
  c. 预处理 Markdown（去 frontmatter、`![[]]`、`[[wikilink]]`、`[toc]`）
  d. curl 文件上传 + 导入任务发布文档（参考 `feishu` skill 的「curl 文件上传导入」方法）
  e. curl 移入 wiki 对应节点
  f. 回写本地 frontmatter：`feishu_node_token`、`feishu_sync_time`
  g. 报告同步成功

- **用户拒绝**：跳过，仅保存本地

- **用户要求推送到资讯 bot**：
  a. 完成上述飞书知识库同步
  b. 按 `feishu` skill 的「资讯推送」工作流，获取 bot 可用范围内的所有用户
  c. 构建卡片消息（标题 + 摘要 + 原文链接 + 知识库链接按钮）
  d. 向所有用户发送私信（DM）
  e. 报告发送结果（成功/失败数量）

### Step 6: 报告

向用户报告：
- 保存路径和文件名
- 文章标题、作者
- type 和 category
- tags
- 封面图路径（如生成）
- 飞书节点信息（如发布）

## 推荐正文模板

每种 type 一套推荐章节结构。Claude 根据内容灵活调整——可以合并、拆分、增删章节，但整体骨架尽量贴近模板。

### news（资讯）
```
## 翻译（非中文时）
## 原文（非中文时）
## 要点分析
## 我的笔记
```

### architecture（架构分析）
```
## 项目概述
## 技术栈
## 核心架构
## 关键模块分析
## 设计亮点与不足
## 总结
```

### review（产品测评）
```
## 产品简介
## 核心功能
## 实际体验
## 优缺点
## 竞品对比（如有）
## 结论
```

### tutorial（技术教程）
```
## 问题背景
## 方案概述
## 实现步骤
## 常见问题
## 总结
```

### notes（读书/论文笔记）
```
## 核心论点
## 关键概念
## 精彩摘录
## 我的思考
```

### essay（个人观点）
```
## 观点
## 论据
## 反面思考
## 结论
```

## Frontmatter 设计

### 核心字段（所有类型共享）

```yaml
---
title: ""
author: ""
type: news              # news/architecture/review/tutorial/notes/essay
source: ""              # 来源 URL（essay 可为空）
date: 2026-03-10        # 内容日期
saved_at: 2026-03-10    # 保存日期
lang: zh
category: AI/应用       # 从索引文件选取
tags: []                # 1-3 个 category 级标签
summary: []             # 3-5 条中文要点
status: raw             # raw → enriched → published
cover: ""               # 封面图路径
feishu_node_token: ""
feishu_sync_time: ""
---
```

### 类型扩展字段

每种 type 有固定的扩展字段，直接平铺在 frontmatter 中（不用 meta 嵌套）。有数据就填，没有不强制。

**news：**
```yaml
author_handle: "@mattshumer_"
likes: 12500
retweets: 3200
views: 850000
```

**architecture：**
```yaml
repo_url: "https://github.com/openclaw/openclaw"
tech_stack:
  - TypeScript
  - Node.js
stars: 15000
license: MIT
```

**review：**
```yaml
product_name: "Cursor"
product_url: "https://cursor.com"
rating: 4               # 1-5
verdict: "推荐"
```

**tutorial：**
```yaml
difficulty: intermediate  # beginner/intermediate/advanced
prerequisites:
  - Node.js 22+
  - pnpm
```

**notes：**
```yaml
book_title: "Thinking, Fast and Slow"
book_author: "Daniel Kahneman"
isbn: "978-0374533557"
reading_progress: "completed"
```

**essay：**
```yaml
thesis: "独立开发者最大的敌人不是技术，是心态"
```

## Frontmatter 完整示例

### news 示例

```yaml
---
title: "Something Big Is Happening"
author: "Matt Shumer"
type: news
source: "https://x.com/i/status/2021256989876109403"
date: 2026-02-10
saved_at: 2026-02-14
lang: en
category: AI/发展
tags:
  - AI/发展
  - AI/影响
summary:
  - AI 能力在 2026 年 2 月出现质变
  - GPT-5.3 Codex 和 Opus 4.6 同日发布标志新时代
  - 1-5 年内 50% 入门级白领工作可能被 AI 取代
status: enriched
cover: "Matt Shumer - Something Big Is Happening.png"
author_handle: "@mattshumer_"
likes: 12500
retweets: 3200
views: 850000
feishu_node_token: "Mb0BwR45OiJd97k3iAXcYmILndd"
feishu_sync_time: "2026-03-09T22:00:00+08:00"
---
```

### architecture 示例

```yaml
---
title: "OpenClaw 架构解析"
author: "mixiaomi"
type: architecture
source: "https://github.com/openclaw/openclaw"
date: 2026-03-10
saved_at: 2026-03-10
lang: zh
category: 技术/架构
tags:
  - 技术/架构
  - AI/应用
summary:
  - TypeScript ESM 单体仓库，pnpm workspace
  - 插件化多渠道消息网关架构
  - 支持 20+ 消息渠道
status: enriched
cover: "OpenClaw Architecture.png"
repo_url: "https://github.com/openclaw/openclaw"
tech_stack:
  - TypeScript
  - Node.js
  - Vitest
stars: 15000
license: MIT
---
```

## 快捷流程示例

### 资讯（现有流程不变）
```
用户: "https://x.com/... 保存到飞书"
→ 推断 type=news → x2md → enrichment → 翻译 → 配图 → 飞书发布 → 报告
```

### 架构分析
```
用户: [已用代码探索研究完 openclaw] "帮我写个架构分析"
→ 推断 type=architecture → 用户提供素材/笔记 → enrichment（架构模板） → 配图 → 报告
```

### 产品测评
```
用户: [已试用完产品] "写个 Cursor 测评"
→ 推断 type=review → 用户提供体验笔记 → enrichment（测评模板） → 配图 → 报告
```

### 技术教程
```
用户: "写个教程，讲怎么用 MCP 连飞书"
→ 推断 type=tutorial → 用户提供步骤/代码 → enrichment（教程模板） → 配图 → 报告
```

## 与其他 Skill 的关系

```
article-gen (本 skill，总编排)
  ├── x2md ——— X → Markdown（仅 news 类型调用）
  ├── cover-image ——— 封面配图（所有类型）
  ├── feishu ——— 飞书发布（所有类型）
  └── Claude ——— enrichment + 翻译（内置能力，非 skill）

共享资源：
  └── ~/Documents/obsidian/mixiaomi/meta/categories.md（与 kb skill 共享）

x-feed digest 模式也可调用 article-gen 的 enrichment + 发布流程。
kb sync 模式调用 feishu skill 做双向同步。
```

每个 skill 只做一件事，article-gen 负责串联。
````

**Step 3: Verify new SKILL.md**

Run: `head -5 ~/.claude/skills/article-gen/SKILL.md`
Expected: New frontmatter with updated description mentioning 6 types

---

### Task 3: Update kb SKILL.md to use shared category index

**Files:**
- Modify: `~/.claude/skills/kb/SKILL.md` (Section 1.3 only)

**Step 1: Read current kb SKILL.md**

Run: Read `~/.claude/skills/kb/SKILL.md`
Purpose: Find the hardcoded category list in Section 1.3

**Step 2: Replace hardcoded category list**

In `~/.claude/skills/kb/SKILL.md`, find Section `### 1.3 Tag 分类体系` and replace the hardcoded 9-category list with a reference to the shared index file.

Replace this block (approximately lines 68-85):
```markdown
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
```

With:
```markdown
### 1.3 Tag 分类体系

**从共享索引文件读取 category 列表**：`~/Documents/obsidian/mixiaomi/meta/categories.md`

从该文件中选择 1-3 个最匹配的标签作为 tags，选 1 个作为 category。

**半自动扩展**：如果内容不属于任何已知 category，提议一个新 category（遵循 `一级/二级` 格式），用户确认后追加到索引文件。
```

**Step 3: Verify changes**

Run: `grep -A 5 "1.3 Tag" ~/.claude/skills/kb/SKILL.md`
Expected: Shows reference to shared index file, not hardcoded list

---

### Task 4: Verify end-to-end consistency

**Step 1: Verify category index file exists and is valid**

Run: `cat ~/Documents/obsidian/mixiaomi/meta/categories.md`
Expected: 11 categories (9 original + 2 new) with descriptions

**Step 2: Verify article-gen SKILL.md references index file**

Run: `grep "categories.md" ~/.claude/skills/article-gen/SKILL.md`
Expected: At least 2 references to `~/Documents/obsidian/mixiaomi/meta/categories.md`

**Step 3: Verify kb SKILL.md references index file**

Run: `grep "categories.md" ~/.claude/skills/kb/SKILL.md`
Expected: At least 1 reference to `~/Documents/obsidian/mixiaomi/meta/categories.md`

**Step 4: Verify article-gen has all 6 types**

Run: `grep -c "news\|architecture\|review\|tutorial\|notes\|essay" ~/.claude/skills/article-gen/SKILL.md`
Expected: Multiple matches (>20), confirming all types are documented

**Step 5: Verify no hardcoded category lists remain in kb**

Run: `grep "9 个层级标签" ~/.claude/skills/kb/SKILL.md`
Expected: No matches (old hardcoded reference removed)
