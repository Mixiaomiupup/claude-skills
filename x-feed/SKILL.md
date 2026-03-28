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
created_block_id = resp['data']['children'][0]['block_id']

# CRITICAL: API may wrap file block in a View block (type 33).
# Must get the actual file block (child of View block) for upload & PATCH.
import time; time.sleep(0.5)
block_resp = curl_json(['-X', 'GET',
    f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{created_block_id}',
    '-H', f'Authorization: Bearer {token}',
])
block_data = block_resp.get('data', {}).get('block', {})
if block_data.get('block_type') == 33 and block_data.get('children'):
    file_block_id = block_data['children'][0]  # Real file block inside View wrapper
else:
    file_block_id = created_block_id

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
| PATCH on View block wrapper (type 33) | error 1770025 `operation and block not match` | Must PATCH the child file block, not the View wrapper |

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
anyweb type "AI programming leaders worth following on Twitter. Include tweet URLs."

# Step 4: Submit with Enter key (CRITICAL: do NOT use \n in type, it becomes literal text)
anyweb keys Enter

# Step 5: Wait for response — detect "Copy text" button (see observer pattern in Digest Mode Step 1)
anyweb eval "<observer JS>"
```

For multiple discover queries, use `--page` for parallel execution (see Digest Mode Step 1).

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

**完整流程 checklist（每步必须执行，不可跳过）**：
0. 计算采集时间窗口 → 1. Grok 三轮查询 → 2. Core Account 补充 → 3. Tavily 搜索 → 4. 去重 → 5. 排序分类 → 6. 生成 Markdown → 7. 保存 Obsidian → **7.5. 媒体收集（封面图 + 截图 + 视频）** → **8. 发布飞书（含媒体上传 + 视频插入）**

### Step 0: 计算采集时间窗口

确定本次采集覆盖的时间范围，用于调整 Grok 查询日期和去重基准。

1. **读取上次采集时间**：
   ```
   Glob ~/Documents/obsidian/mixiaomi/日报/X日报-*.md → 按日期倒序取第 1 篇
   Read frontmatter 的 collected_at 字段（如 "2026-03-27T15:00+08:00"）
   若无 collected_at，则以文件名日期 + "T23:59" 为近似值
   ```

2. **确定查询日期列表**：
   ```
   last_date = collected_at 的日历日（如 2026-03-27）
   today = 当前日历日（如 2026-03-28）
   若 last_date == today → query_dates = [today]
   若 last_date == yesterday → query_dates = [today]（去重会过滤昨天已报道的）
   若 last_date < yesterday → query_dates = [last_date+1, ..., today]（每天一组查询）
   ```

3. **传递给后续步骤**：`query_dates` 列表和 `last_collected_at` 时间戳供 Step 1 和 Step 4 使用

### Step 1: Grok Hot Topic Scan (primary source)

Use anyweb `--page` flag to run 3 Grok queries in **full parallel** (headless mode). Each `--page` creates a named tab sharing the same x.com cookies.

```bash
# Phase 1: Open 3 Grok pages in parallel
anyweb open --page grok1 "https://x.com/i/grok?new=true"  # first open starts daemon
anyweb open --page grok2 "https://x.com/i/grok?new=true" &
anyweb open --page grok3 "https://x.com/i/grok?new=true" &
wait

# Phase 2: Wait for textareas in parallel
anyweb wait --page grok1 selector "textarea" --timeout 15000 &
anyweb wait --page grok2 selector "textarea" --timeout 15000 &
anyweb wait --page grok3 selector "textarea" --timeout 15000 &
wait

# Phase 3: Submit all 3 queries in parallel (headless — no focus competition)
(anyweb click --page grok1 "textarea" && anyweb type --page grok1 "<Round 1 prompt>" && anyweb keys --page grok1 Enter) &
(anyweb click --page grok2 "textarea" && anyweb type --page grok2 "<Round 2 prompt>" && anyweb keys --page grok2 Enter) &
(anyweb click --page grok3 "textarea" && anyweb type --page grok3 "<Round 3 prompt>" && anyweb keys --page grok3 Enter) &
wait

# Phase 4: Wait for all 3 responses in parallel (observer pattern)
anyweb eval --page grok1 '<observer JS>' > /tmp/grok1.txt &
anyweb eval --page grok2 '<observer JS>' > /tmp/grok2.txt &
anyweb eval --page grok3 '<observer JS>' > /tmp/grok3.txt &
wait
```

**Observer JS** — detect `aria-label="Copy text"` button (completion signal), then extract:
```javascript
new Promise(resolve => { const start = Date.now(); const check = () => { const elapsed = Math.floor((Date.now() - start) / 1000); const btns = document.querySelectorAll("button"); let hasCopy = false; for (const b of btns) { if (b.getAttribute("aria-label") === "Copy text" && b.offsetHeight > 0) { hasCopy = true; break; } } if (hasCopy && elapsed > 15) { const main = document.querySelector("main"); resolve(main ? main.innerText.substring(0, 15000) : "no main"); } else if (elapsed > 180) { const main = document.querySelector("main"); resolve("[TIMEOUT] " + (main ? main.innerText.substring(0, 15000) : "no main")); } else { setTimeout(check, 3000); } }; setTimeout(check, 10000); })
```

**三轮查询按信息源头分类**（避免重复，每轮列出具体公司名引导精准结果）。

**日期模板**：根据 Step 0 的 `query_dates` 动态生成：
- 单日（常见）：`"today March 28 2026"`
- 跨天（漏采补查）：`"on March 27 and March 28 2026"`

以下模板中 `{DATE_RANGE}` 替换为实际日期表达。

**Round 1: AI 实验室 & 公司动态**（官方视角）
```
What did AI companies announce or release {DATE_RANGE}? Organize by these categories:
1. New model releases or updates (Claude, GPT, Gemini, DeepSeek, Qwen, Llama, Mistral etc.)
2. Product feature launches or API changes (pricing, rate limits, new capabilities)
3. Funding rounds, acquisitions, IPOs, partnerships
4. Research papers or benchmark results from major labs
For each item include: company name, what happened, engagement stats if available, and tweet URLs.
```

**Round 2: 开发者社区 & 开源生态**（社区视角）
```
What are developers building and discussing on Twitter {DATE_RANGE}? Organize by these categories:
1. Trending open source repos or new project launches (GitHub stars, Show HN etc.)
2. Viral developer demos, workflows, or tips
3. Hot debates, controversies, or opinion threads
4. New framework versions, library updates, or SDK releases
For each item include: author, what it does, engagement stats if available, and tweet URLs.
```

**Round 3: 具身智能 & 硬件**
```
What are the biggest news in robotics and physical AI {DATE_RANGE}? Organize by these categories:
1. Humanoid robot demos, product launches, or company announcements (Tesla Optimus, Figure, Unitree, Boston Dynamics, AGIBOT etc.)
2. Research breakthroughs in robot learning, manipulation, locomotion, sim-to-real, VLA models
3. AI chip, edge computing, or hardware announcements (NVIDIA, custom silicon etc.)
4. Funding, IPOs, or industry partnerships in robotics
For each item include: company/author, what happened, engagement stats if available, and tweet URLs.
```

**观察者逻辑（按钮检测法）**：
1. 先等 10 秒让 Grok 开始处理
2. 每 3 秒检查是否出现 `aria-label="Copy text"` 按钮（Grok 回答完成后才渲染）
3. 按钮出现且已过 15 秒 → 提取 `main.innerText`（最多 15000 字符）
4. 超过 180 秒兜底超时

**为什么不用文本增长稳定性检测**：Grok 在"Thinking"阶段会先输出少量文字后暂停 10-30 秒做搜索，旧方法的 9 秒稳定窗口会误判为已完成，实际回答还没开始。按钮检测法利用 Grok UI 的确定性信号，无误触发风险。

**关键参数**：
- 每次调用 `?new=true` 开新对话，避免历史残留
- **必须在每个问题中加 "Include tweet URLs"**，否则 Grok 不返回链接

**并发模式（headless，推荐）**：
- anyweb 支持 `--page` 参数创建命名页面，同一 platform 的页面共享 cookies
- **Grok 三轮查询全并行**：3 个 `--page grokN` 独立提交和等待（已验证 ~3.5 分钟完成）
- **Core Account 读取并行**：`anyweb read` 内部使用 `new_page()`，每次创建独立页面，可并行（建议 semaphore(5) 限流）
- **Tavily 搜索**不依赖 anyweb daemon，可与任何 anyweb 操作并行
- Agent 子进程可调用 anyweb daemon（命名页面互不干扰），适合并行读核心账号
- 第一个 `anyweb open` 必须串行执行（确保 daemon 启动），后续可并行
- 用 `anyweb log` 查看命令执行日志（每条含 page=, 耗时, 结果状态）

**headed 模式注意**：headed 模式下浏览器窗口焦点全局共享，键盘操作（click/type/keys）会互相抢焦点。如需 headed 调试，Grok 提交阶段必须串行，仅 observer eval 可并行

### Step 2: Core Account Supplement

1. Read `references/core_accounts.yaml` -> select 8-15 accounts across categories (ai_company, ai_frontline, robotics, cn_dev 各取 2-4 个)
2. For each account:
   ```bash
   anyweb --json read "https://x.com/{user}"
   ```
   Grab recent 5 tweets per account — **each tweet now includes a `[View tweet](URL)` link**
3. Supplements niche high-quality content Grok may miss

### Step 3: Tavily Search (supplementary)

```
tavily_search(query="AI OR Claude OR GPT OR LLM OR humanoid robot OR embodied AI", time_range="day", max_results=10)
```

**Tavily URL 可信度规则**：
- **可信域名（直接使用）**：cnet.com, tomshardware.com, bloomberg.com, reuters.com, techcrunch.com, theverge.com, arstechnica.com, wired.com, venturebeat.com, semafor.com, cnbc.com, nytimes.com, wsj.com, x.com, github.com, arxiv.org, huggingface.co
- **未知域名** → 标注 `[来源待验证]` 或不使用
- **绝不编造或猜测 URL** — 如果没有真实 URL，宁可不放链接

### Step 3.5: Keyword Search (optional)

```bash
anyweb --json search x "AI OR Claude OR GPT OR LLM OR humanoid robot OR embodied AI" --limit 10
```

### Step 4: Dedup Against Previous Digests

**必须在排序前执行**，避免重复报道已有内容。使用 Step 0 得到的 `last_collected_at` 确定去重范围。

1. **读取上次采集以来的日报**：
   ```
   Glob ~/Documents/obsidian/mixiaomi/日报/X日报-*.md → 取 last_collected_at 所在日期及之后的所有日报
   若无 collected_at 可回退为按日期倒序取最近 1-3 篇
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

**核心原则：**

1. **每条新闻/推文必须附真实原文链接。链接不真实不如不放。**

2. **信源溯源（一手 vs 二手）**：区分原始信源和转译/评论者。
   - **一手信源**（官方账号、原始公告）→ 作为 `[来源]` 主链接
   - **二手信源**（KOL 转译、评论、解读）→ 作为附加参考，格式：`[中文解读](URL)` 或 `[评论](URL)`
   - **典型错误**：宝玉 @dotey 引用了 @soraofficialapp 的 Sora 关停公告并添加中文解读，应该用 @soraofficialapp 作为主来源，宝玉作为 `[中文解读]` 附上
   - **判断方法**：推文中有引用/转推 → 点进被引用的原文 → 该原文才是一手信源
   - **core_accounts.yaml 中的 KOL**（dotey, HiTw93, Gorden_Sun 等）通常是二手信源，他们引用的内容才是一手

**每条新闻三层结构**：
1. **事实层**：一手信源的客观事实摘要 + 来源链接 + 截图
2. **评论层**：KOL/业内人士的评论（粗体 @账号 + 摘要），从推文引用、回复、quote tweet 中提取。没有评论时可省略
3. **点评层**：💡 开头的一句话编辑判断——为什么重要 / 意味着什么 / 对行业的影响

**板块趋势**：每个 `##` 板块末尾加 `### 板块趋势`，综合该板块多条新闻做 2-3 句趋势判断

**飞书排版约束**：`![[tweet-{id}.png]]` 截图必须放在 blockquote (`>`) **外面**，作为列表项下的独立行。图片在 blockquote 内会打断引用块，导致后续的 💡 点评变成独立列表项，排版混乱。正确结构：blockquote 包含事实+来源+评论+💡，图片在 blockquote 下方。

**按话题维度组织**（不按内容类型），具身智能排最前（公司定位）：

```markdown
---
title: "X/Twitter Daily Digest - YYYY-MM-DD"
type: digest
date: YYYY-MM-DD
collected_at: "YYYY-MM-DDTHH:MM+08:00"
tags:
  - AI/development
category: AI/development
status: enriched
cover: "X日报-YYYY-MM-DD-cover.png"
---

# X/Twitter Daily Digest - YYYY-MM-DD

![[X日报-YYYY-MM-DD-cover.png]]

## 概览

> 5-7 条一句话摘要，覆盖当日最重要事件，每条标注所属板块

## 具身智能

- **[Title]** by @author (N likes)
  > 事实摘要：技术细节、SDK、API、开源代码、论文
  > [来源](URL)
  > **@评论者1**: 评论摘要（从推文引用/回复中提取）
  > **@评论者2**: 另一条评论...
  > 💡 一句话编辑点评：为什么重要 / 意味着什么

  ![[tweet-{id}.png]]

### 板块趋势
> 综合本板块多条新闻的趋势判断（2-3 句）

## 模型与研究

（同上三层结构：事实 → 三方评论 → 💡点评）

### 板块趋势

## 产品与工具

（同上三层结构）

### 板块趋势

## 行业动向

（同上三层结构）

### 板块趋势

## 前瞻与观点

（同上三层结构）

### 板块趋势

## 持续发酵（前日已报，热度上升）

- **[事件]** (当前 N likes，前日报道时 M likes) — 新动态简述
  > [来源](URL)

## 溯源表

| # | 标题 | 来源 | 互动数据 | 归属模块 |
|---|------|------|---------|---------|
| 1 | [title] | [来源](URL) | N likes / M retweets | 具身智能 |
| 2 | [title] | [来源](URL) | N likes / M retweets | 模型与研究 |
| ... | | | | |

---

> 数据来源: Grok Search + Core Accounts (anyweb read) + Tavily
> 去重参考: X日报-YYYY-MM-DD
```

### Step 7: Save

1. Save to `~/Documents/obsidian/mixiaomi/日报/X日报-YYYY-MM-DD.md`
2. Frontmatter: `type: digest`, tags from content analysis, `category` matching dominant topic

### Step 7.5: Media Collection (封面图 + 推文截图 + 视频) — MANDATORY

**此步骤为日报流程必须环节，不可跳过。** 在 Step 7 保存日报后、Step 8 发布飞书前，必须完成以下全部子步骤。

**选取规则**：
- **封面图**：必做，每期日报一张
- **推文截图**：选取日报中 **互动量 Top 5** 的推文截图（必须有真实 tweet URL）
- **视频下载**：收集阶段发现含视频的推文，且该推文已入选日报正文，则下载视频

#### 7.5.1 封面图生成

使用 `gemini-image` skill 生成日报封面，结合当日热点内容。

**风格**：手绘信息图风格（baoyu-inspired），5 个话题卡片，粉彩配色，wobble 线条。

```bash
# 生成封面（不含中文文字，避免 AI 文字错误）
python3 ~/.claude/skills/gemini-image/scripts/gemini_image.py generate "<prompt>" \
  -o ~/Downloads/x-daily/YYYY-MM-DD/cover-raw.png
```

**AI 中文文字已知问题**：Gemini 生成中文经常写错字。解决方案：prompt 中 "NO Chinese text"，用 Pillow 叠加正确文字（`STHeiti Medium.ttc` 简体字体，勿用 Hiragino Sans 繁体）。

#### 7.5.2 推文截图

使用 anyweb 截取推文**仅正文区域**（不含侧边栏、顶栏、回复区）。

**核心流程**：
1. `anyweb open "https://x.com/{user}/status/{id}"` 打开推文
2. **展开全文**：检查是否有"显示更多"/"Show more"按钮，若有则点击展开：
   ```javascript
   // 展开被截断的推文正文
   const showMore = document.querySelector('[data-testid="tweet-text-show-more-link"]');
   if (showMore) showMore.click();
   ```
   **不展开就截图会导致内容不完整**（半张图），这是常见错误。
3. 启用深色模式（便于微信公众号深色模式下视觉融合）：
   `anyweb eval "document.cookie='night_mode=2;domain=.x.com;path=/'; location.reload()"`
   或通过 CDP `Emulation.setEmulatedMedia` 设置 `prefers-color-scheme: dark`
3. `anyweb eval "<HIDE_JS>"` 隐藏非正文元素并返回正文边界
4. `anyweb screenshot` 全页截图
5. Pillow 裁切到正文边界

**HIDE_JS 要点**：
```javascript
// 隐藏：sidebarColumn, header[role="banner"], BottomBar, dialog
// 约束：primaryColumn maxWidth=620px, margin=0 auto
// 隐藏回复：articles[1:] display=none
// 返回：JSON.stringify(articles[0].getBoundingClientRect())
```

**Pillow 裁切关键：先检测 devicePixelRatio**：

```bash
# 1. 获取实际 viewport 和 dpr
anyweb eval 'JSON.stringify({dpr: window.devicePixelRatio, vw: window.innerWidth})'
# 典型结果: {"dpr":1,"vw":1536}
```

```python
# 2. 用 dpr 计算缩放因子，不要硬编码 viewport 宽度
#    错误写法: scale = img.width / 1280  ← 猜测的值，会导致裁切偏移
#    正确写法:
scale = dpr  # dpr=1 时坐标直接映射，dpr=2 时坐标 ×2
left = max(0, int(bounds['left'] * scale) - 5)
top = max(0, int(bounds['top'] * scale) - 5)
right = min(img.width, int(bounds['right'] * scale) + 5)
bottom = min(img.height, int(bounds['bottom'] * scale) + 15)
cropped = img.crop((left, top, right, bottom))
```

**已知坑**：anyweb 默认 viewport 为 1536x864（非 1280），且 dpr=1。如果用 `img.width / 1280` 算 scale 会得到 1.2，导致所有坐标右移 20%，截图左侧被裁掉、右侧多出黑边。

#### 7.5.3 嵌入 Obsidian

1. 复制图片到 `~/Documents/obsidian/mixiaomi/attachments/`：
   - `cover.png` → `X日报-YYYY-MM-DD-cover.png`
   - `tweet-{id}.png` 直接复制

2. 更新日报 Markdown：
   - frontmatter: `cover: "X日报-YYYY-MM-DD-cover.png"`
   - 标题下: `![[X日报-YYYY-MM-DD-cover.png]]`
   - 每条推文来源链接后: `![[tweet-{id}.png]]`

#### 7.5.4 视频下载

在 Step 1-3 收集内容时，**标记含视频的推文**。在媒体收集阶段统一下载。

```bash
yt-dlp --cookies-from-browser chrome -f "bestvideo+bestaudio/best" \
  -o "$HOME/Downloads/x-daily/YYYY-MM-DD/%(id)s.%(ext)s" \
  "https://x.com/{user}/status/{tweet_id}"
```

下载后的视频在 Step 8 发布飞书后，通过 `insert_videos_to_doc()` 插入文档（参见 Section 0.2）。

#### 7.5.5 媒体目录与清理

```
~/Downloads/x-daily/YYYY-MM-DD/
├── cover.png          # 最终封面（Pillow 叠加文字后）
├── cover-raw.png      # Gemini 原始输出（发布前删除）
├── tweet-{id}.png     # 推文截图（仅正文，裁切后）
├── tweet-full-{id}.png # 全页截图（发布前删除）
└── {tweet_id}.mp4     # 视频文件（发布后可保留或删除）
```

**发布前必须清理**：删除 `cover-raw.png` 和 `tweet-full-*.png`，否则会被 `publish_to_feishu()` 的 `media_dir` 参数一并上传到飞书。

### Step 8: Feishu Publish & Broadcast (automatic) — MANDATORY

After saving the digest locally, **always** publish to Feishu and broadcast. Do not ask — this is part of the digest flow.

**发布子步骤（必须全部执行）**：

1. **清理媒体目录** — 删除 `cover-raw.png` 和 `tweet-full-*.png`（避免上传多余文件）
2. **调用 `publish_to_feishu()`** — 必须传 `media_dir` 参数，函数内部自动：
   - 创建/覆盖飞书文档（检测 frontmatter `feishu_node_token`）
   - 上传封面图（`cover.png`）
   - 上传推文截图（`tweet-{id}.png`）并插入对应位置
   - 上传视频（`*.mp4`/`*.webm`）并通过 file block 插入文档
   - 发送飞书卡片消息广播

**更新模式**: `publish_to_feishu()` 自动检测 frontmatter 中的 `feishu_node_token`。若已存在，则清空旧文档并覆盖内容（URL 不变、不产生重复文档）；若不存在，则新建文档并移入知识库。

**使用共享脚本** `~/.claude/skills/_shared/feishu_publish.py`：

```python
exec(open(os.path.expanduser('~/.claude/skills/_shared/feishu_publish.py')).read())

# Step 8.1: 清理多余文件
import glob, os
media_dir = os.path.expanduser('~/Downloads/x-daily/YYYY-MM-DD')
for f in glob.glob(os.path.join(media_dir, 'cover-raw.png')) + glob.glob(os.path.join(media_dir, 'tweet-full-*.png')):
    os.remove(f)

# Step 8.2: 发布（含封面、截图、视频上传 + 卡片广播）
result = publish_to_feishu(
    md_path=os.path.expanduser('~/Documents/obsidian/mixiaomi/日报/X日报-YYYY-MM-DD.md'),
    doc_title='X/Twitter 日报 - YYYY-MM-DD',
    wiki_parent_node='Rs4fwW23SiU0mCk0aBZcupXNnvd',  # X日报
    media_dir=media_dir,  # 封面 + 截图 + 视频
    card_template='blue',
    card_title='X/Twitter 日报 - YYYY-MM-DD',
    card_summary='**本日 AI 热点速览**\n\n**具身智能**\n* 要点1\n\n**模型与研究**\n* 要点1\n\n**产品与工具**\n* 要点1',
    recipients='all',  # 全员推送
)
```

**注意**：`media_dir` 不传或传 `None` 则只发布文本，不会上传任何图片/视频。**必须传此参数。**

**父节点映射**：
| 内容类型 | parent_wiki_token | 飞书节点 |
|---------|-------------------|---------|
| X日报 | `Rs4fwW23SiU0mCk0aBZcupXNnvd` | 日报/X日报 |
| 模型前沿 | `Za2NwAddOidZ1Ikm4CKcyHS7nSc` | 行业前沿/模型前沿 |
| 具身动态 | `UzfowFW4sidwVdkZulecDOQ3nyd` | 行业前沿/具身动态 |
| 编程范式 | `Nvrzwk0MAi5bPYkBucMcn1uJnkh` | 行业前沿/编程范式 |
| AI思考 | `Me5EwNgwciDpKRk0YSPcKaWHnAo` | 行业前沿/AI思考 |
| 商业观察 | `End8wv8oei8eQ6kr5pzcOpmVnyh` | 行业前沿/商业观察 |

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
- 提交用 `anyweb keys Enter`（不要在 type 末尾加 `\n`，会变成字面文字）
- 等待回复用 **观察者模式**（检测 `aria-label="Copy text"` 按钮），典型 15-60 秒完成
- 每次新问题用 `anyweb open "https://x.com/i/grok?new=true"` 开新对话
- `anyweb open` 自动从 URL 识别平台并加载对应 session cookie
- 多个 Grok 查询用 `--page grok1/grok2/grok3` 全并行（headless 模式下无焦点竞争）
- 用 `anyweb log` 查看 daemon 命令日志，排查 headless 下的操作失败

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
