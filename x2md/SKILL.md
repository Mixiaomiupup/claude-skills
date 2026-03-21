---
name: x2md
description: "Convert X/Twitter posts, threads, and long-form articles to Markdown. Use when user provides an X/Twitter URL (x.com, twitter.com) and wants to convert it to markdown. If user also asks to publish to Feishu, handles author research + translation + publishing in one flow."
---

# X/Twitter to Markdown

将 X/Twitter 内容转为干净的 Markdown 文件，带结构化 frontmatter。支持可选的翻译 + 飞书发布流程。

## Usage

```bash
cd ~/Documents/obsidian/mixiaomi && python3 ~/.claude/skills/x2md/scripts/x2md.py "<URL>"
```

输出到 `行业资讯/` 子目录（按 category 一级分类存入 AI/技术/商业/思考），同时复制到剪贴板。

## Workflow

### 基础流程（仅转换）

1. 从用户输入提取 URL（支持 `x.com` 和 `twitter.com`）
2. 运行脚本，生成 `.md` 文件（原文，`status: raw`）
3. 报告保存路径和文件名

### 完整流程（转换 + 翻译 + 飞书发布）

当用户要求「推送到飞书」「发到飞书」或类似意图时，执行完整流程：

1. **转换**: 运行脚本生成原始 `.md` 文件
2. **调研作者**: 用 tavily_search 搜索作者背景信息（身份、公司、代表作品）
3. **翻译 + 组装**: Claude 直接翻译原文为中文，按以下结构组装最终文档：
   ```
   # 中文标题

   ## 作者简介
   （作者背景、身份、代表作品，2-3 段）

   ---

   ## 译文
   （完整中文翻译，保留原文结构、标题层级、列表格式）

   ---

   ## 原文
   （完整英文原文）
   ```
4. **更新本地文件**: 用组装后的内容覆盖本地 `.md` 文件，更新 frontmatter `status: enriched`
5. **发布飞书**: 调用 `publish_to_feishu()`（自动检测更新模式：frontmatter 已有 `feishu_node_token` 时更新原文档，无则新建）
6. **广播推送**: 构建卡片消息，广播给所有可见用户

### 翻译规则

- 技术术语保留英文（如 Skills、Claude Code、API、SDK、Hook）
- 专有名词首次出现时附英文（如「渐进式披露（Progressive Disclosure）」）
- 代码块、命令、文件路径不翻译
- 保留原文的标题层级和列表结构
- 翻译风格：准确、流畅、自然，不要翻译腔

## Supported Content Types

| 类型 | 说明 |
|------|------|
| **X Article** | 长文，含标题、小标题、粗斜体、图片 |
| **Regular tweet** | 单条推文，含媒体和引用推文 |
| **Thread** | 自动追溯回复链，重组完整线程 |

## Output Format

- **文件名**: `<作者> - <标题>.md`（长文用标题，单推取前 30 字，线程标注条数）
- **位置**: `行业资讯/` 子目录
- **内容**: YAML frontmatter + 正文 Markdown
- **剪贴板**: macOS 自动复制

## Frontmatter

脚本生成的 frontmatter 含原始元数据，`status: raw`：

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
tags: []
category: ""
summary: []
status: raw
---
```

完整流程后 `status` 更新为 `enriched`，`tags` 和 `category` 填充实际值。
