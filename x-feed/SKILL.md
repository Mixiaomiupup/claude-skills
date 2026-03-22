---
name: x-feed
description: "X/Twitter information feed system - follow expansion, hot topic extraction, and knowledge distillation. Use when user says: 'discover people to follow', 'expand follow list', 'twitter digest', 'what's hot on twitter today', 'twitter weekly report', 'save this tweet', or any Chinese equivalents like '推特日报', '今天推特有什么', '扩展关注', '发现值得关注的人', '推特周报', '保存这篇推文'."
---

# X/Twitter Feed System

Orchestrate existing tools to manage Twitter information flow: discover accounts, extract hot content, distill knowledge.

**Tools used**: `anyweb` CLI (via Bash tool), `x2md` skill, `kb` skill, `feishu` skill.

**Prerequisite**: anyweb must be installed (`pip install -e ~/projects/anyweb` or `pip install anyweb`). Verify with `anyweb doctor`.

---

## 0. Video Download & Embed (cross-cutting capability)

Download videos from X/Twitter tweets and embed them in Feishu documents.

### 0.1 Download Video via yt-dlp

```bash
yt-dlp --cookies-from-browser chrome -f "bestvideo+bestaudio/best" \
  -o "$HOME/Downloads/x-videos/%(uploader)s-%(id)s.%(ext)s" \
  "https://x.com/{user}/status/{tweet_id}"
```

**Prerequisites**: `brew install yt-dlp ffmpeg`
**Output**: Video file in `~/Downloads/x-videos/`

### 0.2 Embed Video in Feishu Document (3-step method)

File block (block_type 23) is the only API-supported way to embed playable video in Feishu docs.
The `view_type` is controlled by the auto-generated View block (block_type 33), which defaults to card view.
API does NOT support creating inline video players (preview view) — only the Feishu UI can do that.

```python
# Step 1: Create empty file block
body = {"children": [{"block_type": 23, "file": {}}], "index": -1}
resp = curl_json(['-X', 'POST',
    f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{parent_block_id}/children',
    '-H', f'Authorization: Bearer {token}',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(body),
])
file_block_id = resp['data']['children'][0]['block_id']

# Step 2: Upload video with parent_node = file_block_id (CRITICAL!)
resp = curl_json(['-X', 'POST',
    'https://open.feishu.cn/open-apis/drive/v1/medias/upload_all',
    '-H', f'Authorization: Bearer {token}',
    '-F', f'file_name={video_filename}',
    '-F', 'parent_type=docx_file',
    '-F', f'parent_node={file_block_id}',  # Must be file_block_id, NOT doc_token
    '-F', f'size={file_size}',
    '-F', f'file=@{video_path}',
])
media_token = resp['data']['file_token']

# Step 3: PATCH replace_file
resp = curl_json(['-X', 'PATCH',
    f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{file_block_id}',
    '-H', f'Authorization: Bearer {token}',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({"replace_file": {"token": media_token}}),
])
```

**Critical**: `parent_node` in Step 2 MUST be the `file_block_id` from Step 1, NOT the doc_token. Using doc_token causes `relation mismatch` (error 1770013).

### 0.3 What doesn't work

| Approach | Result | Reason |
|----------|--------|--------|
| Create file block with token in one call | `invalid param` | API only accepts empty `file: {}` at creation |
| iframe block with x.com URL | `ERR_CONNECTION_CLOSED` | X.com blocked in China |
| image block with video | Shows static thumbnail | Image block treats video as image |
| PATCH view block to change view_type | `invalid param` | View block view_type not updatable via API |
| Create view block directly | `block not support to create` | View blocks are auto-generated only |

### 0.4 Integration with digest/article flow

When a tweet contains a video:
1. Download with yt-dlp during content collection
2. After creating the Feishu document, insert video file block at the appropriate position
3. The video shows as a file card with play button — users click to play

## Mode Router

| User intent | Mode | Key action |
|-------------|------|------------|
| "discover people to follow" | **discover** | Grok recommendations + seed cross-analysis |
| "twitter digest / what's hot" | **digest** | Grok hot topics + core account tweets -> daily report |
| "save this tweet" | **deep-save** | Delegate to `x2md` skill |
| "weekly/monthly twitter summary" | **report** | Synthesize past digests via `kb` skill |

---

## 1. Discover Mode

Expand follow matrix by finding valuable accounts.

### Method A: Grok Recommendations (fast)

Use anyweb atomic commands to interact with Grok. The daemon keeps page state between commands.

```bash
# Step 1: Open Grok (auto-loads X session cookies)
anyweb open "https://x.com/i/grok?new=true"

# Step 2: Wait for textarea
anyweb wait selector "textarea" --timeout 15000

# Step 3: Type question (keyboard events for React)
anyweb click "textarea"
anyweb type "AI programming leaders worth following on Twitter. Include tweet URLs.\n"

# Step 4: Wait for response with observer pattern
anyweb eval "<observer JS>"
```

Ask domain-specific questions:
- "AI programming leaders worth following on Twitter. Include tweet URLs."
- "Best indie hacker Chinese Twitter accounts. Include tweet URLs."
- User-specified domain queries

### Method B: Seed Cross-Analysis (deep)

1. **Select seeds** - User-specified or from `references/core_accounts.yaml` `discover_seeds` list
2. **Fetch following lists** - For each seed:
   ```bash
   anyweb --json read "https://x.com/{seed}/following"
   ```
   Collect 50-100 following per seed
3. **Cross-reference** - Find accounts followed by multiple seeds
4. **Rank** - Sort by `overlap_count` descending
5. **Present results**

Methods A+B can combine: Grok for fast discovery, seed analysis for validation.

### Batch Follow (requires user confirmation)

Present recommended list -> user selects -> use anyweb atomic commands (open profile → click Follow) for each.

---

## 2. Digest Mode

Generate a daily Twitter digest of hot content.

### Step 1: Grok Hot Topic Scan (primary source)

Use anyweb atomic commands for Grok interaction. **All commands share the same daemon page**.

```bash
# 1. Open Grok
anyweb open "https://x.com/i/grok?new=true"

# 2. Wait for textarea
anyweb wait selector "textarea" --timeout 15000

# 3. Type question
anyweb click "textarea"
anyweb type "<问题>. Include tweet URLs.\n"

# 4. Observer pattern — wait for response to stabilize, then extract
anyweb eval "new Promise(resolve=>{let lastLen=0,maxLen=0,stableCount=0,growthSeen=false;const start=Date.now();const check=()=>{const elapsed=Math.floor((Date.now()-start)/1000);const text=document.body.innerText;const len=text.length;if(len>maxLen)maxLen=len;if(len>lastLen+50){growthSeen=true;stableCount=0}else if(Math.abs(len-lastLen)<10){stableCount++}else{stableCount=0}lastLen=len;if(growthSeen&&stableCount>=3&&elapsed>20){resolve(text.substring(0,8000))}else if(elapsed>120){resolve(text.substring(0,8000))}else{setTimeout(check,3000)}};setTimeout(check,10000)})"
```

Ask topic-focused questions (**always include "Include tweet URLs"**):
- "What are today's hot topics in AI and programming? Include tweet URLs."
- "Latest developments with Claude/GPT/LLM today? Include tweet URLs."

**For subsequent Grok questions**, reopen with `?new=true` to start a fresh conversation:
```bash
anyweb open "https://x.com/i/grok?new=true"
anyweb wait selector "textarea" --timeout 15000
anyweb click "textarea"
anyweb type "<next question>. Include tweet URLs.\n"
anyweb eval "<observer JS>"
```

**观察者逻辑**：
1. 先等 10 秒让 Grok 开始处理
2. 每 3 秒检查文本长度变化
3. 文本**经历过增长**（>50 字符）且**连续 3 次无变化**（9 秒稳定） → 判定完成
4. 超过 120 秒兜底超时

**关键参数**：
- 每次调用 `?new=true` 开新对话，避免历史残留
- **必须在每个问题中加 "Include tweet URLs"**，否则 Grok 不返回链接

### Step 2: Core Account Supplement

1. Read `references/core_accounts.yaml` -> select 5-10 accounts across categories
2. For each account:
   ```bash
   anyweb --json read "https://x.com/{user}"
   ```
   Grab recent 5 tweets per account — **each tweet now includes a `[View tweet](URL)` link**
3. Supplements niche high-quality content Grok may miss

### Step 3: Tavily Search (supplementary)

```
tavily_search(query="AI OR Claude OR GPT OR LLM", time_range="day", max_results=10)
```

**Tavily URL 可信度规则**：
- **可信域名（直接使用）**：cnet.com, tomshardware.com, bloomberg.com, reuters.com, techcrunch.com, theverge.com, arstechnica.com, wired.com, venturebeat.com, semafor.com, cnbc.com, nytimes.com, wsj.com, x.com, github.com, arxiv.org, huggingface.co
- **未知域名** → 标注 `[来源待验证]` 或不使用
- **绝不编造或猜测 URL** — 如果没有真实 URL，宁可不放链接

### Step 3.5: Keyword Search (optional)

```bash
anyweb --json search x "AI OR Claude OR GPT OR LLM" --limit 10
```

### Step 4: Dedup Against Previous Digests

**必须在排序前执行**，避免重复报道已有内容：

1. **读取最近 1-3 天日报**：
   ```
   Glob ~/Documents/obsidian/mixiaomi/日报/X日报-*.md → 按日期倒序取最近 1-3 篇
   Read 每篇的 frontmatter + 正文标题
   ```
2. **提取已报道事件**：从前日日报中提取所有新闻条目（标题、关键词、涉及账号）
3. **去重分类**：
   - **已报道且无新进展** → 直接移除（如 GPT-5.4 发布、Promptfoo 收购）
   - **已报道但有显著新数据** → 降级到「持续发酵」区，标注热度变化（如 likes 从 7K→16K）
   - **全新事件** → 正常参与排序
4. **补充引用**：在日报末尾 `数据来源` 中加 `去重参考: X日报-YYYY-MM-DD`

**判断标准**：同一事件（同一公告/产品/人物动态），即使 likes 翻倍也算「已报道」，不应作为新的重大新闻重复出现。

### Step 5: Rank and Classify

- Sort by engagement (likes + retweets + replies) descending
- LLM classify each into: Breaking News / Deep Read / Hot Discussion / Tool Recommendation / Opinion Clash

### Step 6: Generate Digest Markdown

**核心原则：每条新闻/推文必须附真实原文链接。链接不真实不如不放。**

```markdown
---
title: "X/Twitter Daily Digest - YYYY-MM-DD"
type: digest
date: YYYY-MM-DD
tags:
  - AI/development
category: AI/development
status: enriched
---

# X/Twitter Daily Digest - YYYY-MM-DD

## 重大新闻
- **[Title/Summary]** by @author (N likes)
  > One-line summary
  > [来源](https://x.com/author/status/xxx)

## 热门讨论
- **[Topic]** - Multi-person debate
  > Pro: ... | Con: ...
  > [来源](URL)

## 值得关注
- **[Title]** by @author - [Why worth reading]
  > [来源](URL)

## 工具/产品推荐
- **[Product]** by @author - [One-line description]
  > [来源](URL)

## 持续发酵（前日已报，热度上升）
- **[事件]** (当前 N likes，前日报道时 M likes) — 新动态简述
  > [来源](URL)

## 趋势观察
- [宏观趋势分析，跨多条信息的综合判断]

## 溯源表

| # | 标题 | 来源 | 互动数据 | 归属模块 |
|---|------|------|---------|---------|
| 1 | [title] | [来源](URL) | N likes / M retweets | 重大新闻 |
| 2 | [title] | [来源](URL) | N likes / M retweets | 热门讨论 |
| ... | | | | |

---

> 数据来源: Grok Search + Core Accounts (anyweb read) + Tavily
> 去重参考: X日报-YYYY-MM-DD
```

### Step 7: Save & Publish

1. Save to `~/Documents/obsidian/mixiaomi/日报/X日报-YYYY-MM-DD.md`
2. Frontmatter: `type: digest`, tags from content analysis, `category` matching dominant topic
3. Publish to Feishu wiki and broadcast (see Step 8)

### Step 8: Feishu Publish & Broadcast (automatic)

After saving the digest locally, **always** publish to Feishu and broadcast. Do not ask — this is part of the digest flow.

**更新模式**: `publish_to_feishu()` 自动检测 frontmatter 中的 `feishu_node_token`。若已存在，则清空旧文档并覆盖内容（URL 不变、不产生重复文档）；若不存在，则新建文档并移入知识库。

**使用共享脚本** `~/.claude/skills/_shared/feishu_publish.py`：

```python
exec(open(os.path.expanduser('~/.claude/skills/_shared/feishu_publish.py')).read())

publish_to_feishu(
    md_path=os.path.expanduser('~/Documents/obsidian/mixiaomi/日报/X日报-YYYY-MM-DD.md'),
    doc_title='X/Twitter 日报 - YYYY-MM-DD',
    wiki_parent_node='IOsNwtIPdiLTYukHdgqcMIE9nad',  # 行业资讯/AI
    card_template='blue',
    card_title='X/Twitter 日报 - YYYY-MM-DD',
    card_summary='**本日 AI 热点速览**\n\n**重大新闻**\n* 要点1\n* 要点2\n\n**热门讨论**\n* 要点1',
    recipients='all',  # 全员推送
)
```

**父节点映射**：
| 主 tag | parent_wiki_token | 飞书节点 |
|--------|-------------------|---------|
| `AI/*` | `IOsNwtIPdiLTYukHdgqcMIE9nad` | 行业资讯/AI |
| `技术/*` | `T1mzw30Bkir5IKkzbx9cxDFHnDe` | 行业资讯/技术 |
| `商业/*` | `EdB8wcEbeigCFPkYqUXcNpZWnlc` | 行业资讯/商业 |
| `思考/*` | `Xps2wjrCiixmB3kUKZscWLQQnge` | 行业资讯/思考 |

**权限要求**：`wiki:wiki` + `drive:drive` + `im:message` + `contact:user.base:readonly`

---

## 3. Deep-Save Mode

Save individual tweets/articles for long-term reference.

1. Invoke `x2md` skill with the tweet URL
2. `x2md` handles: fetch -> convert to Markdown -> Claude enrichment (classify, tag, summarize) -> save to Obsidian
3. `x2md` asks about Feishu sync
4. No additional logic needed - pure delegation to `x2md`

---

## 4. Report Mode

Generate periodic summaries from accumulated digests.

### Weekly/Monthly Report Flow

1. **Find past digests** in Obsidian vault:
   ```
   Grep "type: digest" in ~/Documents/obsidian/mixiaomi/ (glob: **/*.md)
   ```
   Filter by date range (this week / this month / user-specified)

2. **Read all matching digests** - Load frontmatter + body of each

3. **Synthesize** via `kb` skill synthesize mode:
   - Top 3-5 most important events of the period
   - Ongoing/escalating topics
   - Long-term trends worth watching
   - Notable new tools/products

4. **Generate report** with structure:
   ```markdown
   ---
   title: "X/Twitter Weekly Report - YYYY-WNN"
   type: synthesis
   date: YYYY-MM-DD
   source_count: N
   tags: [relevant tags]
   category: relevant category
   status: enriched
   ---

   # X/Twitter Weekly Report

   ## Top Stories
   ## Ongoing Trends
   ## Notable Tools & Products
   ## Accounts to Watch
   ## Source Digests
   - [[X-Daily-YYYY-MM-DD]]
   ```

5. **Save** to `~/Documents/obsidian/mixiaomi/knowledge-base/synthesis/`

6. Ask user about Feishu sync (delegate to `kb` skill).

---

## Core Accounts

Managed in `references/core_accounts.yaml`. Read this file at the start of `digest` and `discover` modes. Users can edit it anytime to add/remove accounts.

---

## Known Limitations & Workarounds

### Grok 交互注意事项

- anyweb daemon 在命令间保持页面状态，不需要把所有操作塞进一次调用
- 必须用 `anyweb type`（键盘事件），Grok textarea 是 React 受控组件
- 提交用 `\n` 结尾即可，无需找发送按钮
- 等待回复用 **观察者模式**（eval JS 轮询文本长度变化），典型 20-40 秒完成
- 每次新问题用 `anyweb open "https://x.com/i/grok?new=true"` 开新对话
- `anyweb open` 自动从 URL 识别平台并加载对应 session cookie

### 推文抓取最佳实践

`anyweb read "https://x.com/{user}"` 每条推文包含 `[View tweet](URL)` 链接，可直接使用。

深度抓取用原子命令组合:

```bash
# 1. 先滚动加载更多
anyweb scroll down --amount 2000
# 2. 等待加载
anyweb eval "new Promise(r => setTimeout(r, 2000))"
# 3. JS 提取推文数据
anyweb eval "..."
```

**推文 DOM 选择器**:
- 推文容器: `article[role="article"]`
- 正文: `[data-testid="tweetText"]`
- 时间: `time[datetime]`
- 互动: `[data-testid="reply"]`, `[data-testid="retweet"]`, `[data-testid="like"]` 的 `aria-label`

### 日报保存路径

实际路径用中文目录: `~/Documents/obsidian/mixiaomi/日报/X日报-YYYY-MM-DD.md`。
