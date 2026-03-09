---
name: article-gen
description: "Orchestrate article generation pipeline: convert → enrich → translate → cover image → publish. Use when user shares an X/Twitter link to save, says '保存这条推文', '分享到飞书', or any full article processing flow. This is the top-level coordinator that calls x2md, cover-image, feishu etc."
---

# Article Gen

文章生成总编排。统筹从内容抓取到发布的完整流程，按需调用各专职 skill。

## 调用的 Skill

| Skill | 职责 | 何时调用 |
|-------|------|---------|
| `x2md` | X/Twitter → Markdown 转换 | 输入是 X 链接时 |
| `cover-image` | 封面配图（5D 风格 + 生图） | enrichment 后 |
| `feishu` | 飞书知识库发布 + 全员广播 | 用户确认发布时 |

`x2md` 和 `cover-image` 是独立 skill，不知道彼此的存在。`article-gen` 负责串联它们。

## 工作流

```
输入 → 转换 → Enrichment → 翻译 → 配图 → 发布 → 推送
  │       │        │          │       │       │       │
  │    x2md     Claude     Claude  cover   feishu  feishu
  │   (skill)   (内置)     (内置)  -image  (skill) (skill)
  │                                (skill)
  ▼
 报告结果
```

### Step 1: 转换

根据输入来源调用对应转换工具：

| 输入 | 转换方式 | 产出 |
|------|---------|------|
| X/Twitter 链接 | 调用 `x2md` skill | `.md` 文件（`status: raw`） |
| 其他 URL | 调用 `ucal` 抓取 + 手动存 Markdown | `.md` 文件 |
| 本地已有 .md | 跳过转换 | 直接进入 enrichment |

### Step 2: Enrichment

读取 `.md` 文件，Claude 分析内容并填充 frontmatter：

a. **分类**（category，9 选 1）：

| category | 适用内容 |
|----------|---------|
| `AI/发展` | 模型发布、能力进展、AGI |
| `AI/应用` | 工具、工作流、Agent |
| `AI/影响` | 就业、社会、伦理 |
| `技术/趋势` | MCP、CLI-first、平台趋势 |
| `技术/开发` | 编程技巧、架构、Vibe Coding |
| `商业/创业` | 创业、融资、商业 |
| `商业/产品` | 产品思维、UX |
| `思考/创意` | 灵感、创新方法 |
| `思考/社会` | 监管、哲学、未来 |

b. **标签**（tags）：1-3 个层级标签（如 `AI/发展`、`AI/影响`）

c. **摘要**（summary）：3-5 条中文要点

d. **更新 frontmatter**：
- 填入 `tags`、`category`、`summary`
- `status: raw` → `status: enriched`

e. 追加 `## 我的笔记` 空节（供后续笔记用）

### Step 3: 翻译

如果 `lang` 不是 `zh`（非中文内容），重组正文结构：

```markdown
## 翻译
（中文译文）

## 原文
（英文原文）
```

翻译标准：信达雅，专有名词不翻译，技术术语保留英文并括号注中文。

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
- category 和 tags
- 封面图路径（如生成）
- 飞书节点信息（如发布）

## 快捷流程

用户给 X 链接时的典型完整流程：

```
用户: "https://x.com/... 保存到飞书"

article-gen:
  1. 调用 x2md → 得到 raw .md
  2. Enrichment → 分类/标签/摘要 → enriched
  3. 翻译（如非中文）
  4. 调用 cover-image → 生成封面
  5. 调用 feishu → 发布 + 广播
  6. 报告结果
```

用户只说"保存这条推文"时，只做 step 1-4，不发布飞书。

## Frontmatter 完整示例

经过 article-gen 完整流程后的 frontmatter：

```yaml
---
title: "Something Big Is Happening"
author: "Matt Shumer"
author_handle: "@mattshumer_"
source: "https://x.com/i/status/2021256989876109403"
type: article
date: 2026-02-10
saved_at: 2026-02-14
lang: en
likes: 12500
retweets: 3200
views: 850000
tags:
  - AI/发展
  - AI/影响
category: AI/发展
summary:
  - AI 能力在 2026 年 2 月出现质变
  - GPT-5.3 Codex 和 Opus 4.6 同日发布标志新时代
  - 1-5 年内 50% 入门级白领工作可能被 AI 取代
status: enriched
cover: "Matt Shumer - Something Big Is Happening.png"
feishu_node_token: "Mb0BwR45OiJd97k3iAXcYmILndd"
feishu_sync_time: "2026-03-09T22:00:00+08:00"
---
```

## 与其他 Skill 的关系

```
article-gen (本 skill，总编排)
  ├── x2md ——— X → Markdown（纯转换，不做 enrichment）
  ├── cover-image ——— 风格决策 + 生图（自包含 5D 体系）
  ├── feishu ——— 飞书发布 + 广播（API 操作）
  └── Claude ——— enrichment + 翻译（内置能力，非 skill）

x-feed digest 模式也可调用 article-gen 的 enrichment + 发布流程。
kb sync 模式调用 feishu skill 做双向同步。
```

每个 skill 只做一件事，article-gen 负责串联。
