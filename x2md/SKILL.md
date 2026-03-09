---
name: x2md
description: "Convert X/Twitter posts, threads, and long-form articles to Markdown. Pure conversion only — no enrichment, no publishing. Use when user provides an X/Twitter URL (x.com, twitter.com) and wants to convert it to markdown. For the full pipeline (enrich + cover + publish), use article-gen skill instead."
---

# X/Twitter to Markdown

将 X/Twitter 内容转为干净的 Markdown 文件，带结构化 frontmatter。**纯转换**，不做 enrichment、翻译、配图、发布。

## Usage

```bash
cd ~/Documents/obsidian/mixiaomi && python3 ~/.claude/skills/x2md/scripts/x2md.py "<URL>"
```

输出到 `具身行业资讯/` 子目录（fallback `X收藏/`），同时复制到剪贴板。

## Workflow

1. 从用户输入提取 URL（支持 `x.com` 和 `twitter.com`）
2. 运行脚本，生成 `.md` 文件
3. 报告保存路径和文件名

完成。后续 enrichment、配图、翻译、飞书发布由 `article-gen` skill 统筹。

## Supported Content Types

| 类型 | 说明 |
|------|------|
| **X Article** | 长文，含标题、小标题、粗斜体、图片 |
| **Regular tweet** | 单条推文，含媒体和引用推文 |
| **Thread** | 自动追溯回复链，重组完整线程 |

## Output Format

- **文件名**: `<作者> - <标题>.md`（长文用标题，单推取前 30 字，线程标注条数）
- **位置**: `具身行业资讯/` 子目录
- **内容**: YAML frontmatter + 正文 Markdown（作者、日期、来源链接、标题、行内样式、嵌入图片）
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

`tags`、`category`、`summary`、`status` 由 `article-gen` skill 在 enrichment 阶段填充。
