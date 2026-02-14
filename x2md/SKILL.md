---
name: x2md
description: Convert X/Twitter posts, threads, and long-form articles to Markdown and save to Obsidian vault. Use when user provides an X/Twitter URL (x.com, twitter.com) and wants to save it as a note, or asks to clip/save/convert a tweet or X article to markdown/Obsidian.
---

# X/Twitter to Markdown

Convert X/Twitter content to clean Markdown with structured frontmatter, save to Obsidian vault, and enrich with AI-generated classification.

## Usage

Run the bundled script with the tweet URL:

```bash
python3 ~/.claude/skills/x2md/scripts/x2md.py "<URL>"
```

The script outputs to `X收藏/` subdirectory if it exists under the current working directory, otherwise to the current directory.

## Workflow

1. Extract the URL from user input (supports `x.com` and `twitter.com` links)
2. Run the script from the Obsidian vault directory:
   ```bash
   cd ~/Documents/obsidian/mixiaomi && python3 ~/.claude/skills/x2md/scripts/x2md.py "<URL>"
   ```
3. **Enrich the saved file** — Read the saved `.md` file and perform Claude enrichment:
   a. Analyze the article content (title, body text, context)
   b. Determine the best-fit **category** from the taxonomy:
      - `AI/发展` — 模型发布、能力进展、AGI
      - `AI/应用` — 工具、工作流、Agent
      - `AI/影响` — 就业、社会、伦理
      - `技术/趋势` — MCP、CLI-first、平台趋势
      - `技术/开发` — 编程技巧、架构、Vibe Coding
      - `商业/创业` — 创业、融资、商业
      - `商业/产品` — 产品思维、UX
      - `思考/创意` — 灵感、创新方法
      - `思考/社会` — 监管、哲学、未来
   c. Assign 1-3 **tags** (hierarchical format, e.g. `AI/发展`, `AI/影响`)
   d. Write a **summary** as 3-5 bullet points (Chinese, concise)
   e. Update the frontmatter:
      - Fill in `tags` (as YAML list)
      - Fill in `category`
      - Fill in `summary` (as YAML list)
      - Change `status` from `raw` to `enriched`
   f. Append a `## 我的笔记` section at the end of the file (empty, for future dialog notes)
4. Report the saved filename, article title, category, and tags to the user

## Supported Content Types

- **X Article (long-form)** — Full article with title, headings, bold/italic, images
- **Regular tweets** — Single tweets with media and quoted tweets
- **Threads** — Auto-traces reply chains to reconstruct full thread

## Output Format

- Filename: `<作者> - <标题>.md` (Article uses article title, single tweet takes first 30 chars, thread indicates count)
- Location: `X收藏/` subdirectory under the vault root
- Content: YAML frontmatter + clean Markdown with metadata (author, date, source link), cover image, headings, inline styles, and embedded images
- Frontmatter fields: title, author, author_handle, source, type, date, saved_at, lang, likes, retweets, views, tags, category, summary, status
- Also copied to clipboard (macOS)

## Frontmatter Example

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
  - AI 能力在 2026 年 2 月出现质变，作者已不再需要亲自完成技术工作
  - GPT-5.3 Codex 和 Opus 4.6 同日发布标志新时代
  - 1-5 年内 50% 入门级白领工作可能被 AI 取代
status: enriched
---
```
