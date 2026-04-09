---
name: x-feed
description: "X/Twitter information feed system - follow expansion, hot topic extraction, and knowledge distillation. Use when user says: 'discover people to follow', 'expand follow list', 'twitter digest', 'what's hot on twitter today', 'twitter weekly report', 'save this tweet', '科技日报', '日报', 'today's AI news', or any Chinese equivalents like '推特日报', '今天推特有什么', '扩展关注', '发现值得关注的人', '推特周报', '保存这篇推文'. Also trigger for '搜集日报', '搜集新闻'."
---

# X/Twitter Feed System

Orchestrate existing tools to manage Twitter information flow: discover accounts, extract hot content, distill knowledge.

**Tools used**: `anyweb` CLI (via Bash tool), `x2md` skill, `kb` skill, `feishu` skill.

**Prerequisite**: anyweb must be installed (`pip install -e ~/projects/anyweb` or `pip install anyweb`). Verify with `anyweb doctor`.

**Chrome 模式（必须使用）**：所有 anyweb 命令加 `--chrome` 标志，连接系统 Chrome 复用 X 登录态。不要用 Playwright 模式（需要单独登录且容易被检测）。首次使用需安装扩展：`anyweb --chrome doctor`。

---

## Mode Router

| User intent | Mode | Key action |
|-------------|------|------------|
| "discover people to follow" | **discover** | Grok recommendations + seed cross-analysis |
| "twitter digest / what's hot / 科技日报" | **digest** | Grok hot topics + core account tweets -> daily report |
| "save this tweet" | **deep-save** | Delegate to `x2md` skill |
| "weekly/monthly twitter summary" | **report** | Synthesize past digests via `kb` skill |

---

## 1. Discover Mode

Expand follow matrix by finding valuable accounts.

### Method A: Grok Recommendations (fast)

Use anyweb atomic commands to interact with Grok. The daemon keeps page state between commands.

```bash
anyweb --chrome open "https://x.com/i/grok?new=true"
anyweb --chrome wait selector "textarea" --timeout 15000
anyweb --chrome click "textarea"
anyweb --chrome type "AI programming leaders worth following on Twitter. Include tweet URLs."
anyweb --chrome keys Enter
# Wait for response — use observer pattern (see Digest Mode Step 1)
```

For multiple queries, use `--page` for parallel execution (see Digest Mode Step 1).

### Method B: Seed Cross-Analysis (deep)

1. **Select seeds** from `references/core_accounts.yaml` `discover_seeds` list
2. **Fetch following lists**: `anyweb --chrome --json read "https://x.com/{seed}/following"`
3. **Cross-reference** — find accounts followed by multiple seeds
4. **Rank** by `overlap_count` descending

---

## 2. Digest Mode

Generate a daily Twitter digest of hot content.

**完整流程 checklist（每步必须执行，不可跳过）**：
0. 确认日期 + 计算采集窗口 → 1. Grok 四轮查询 → 2. Core Account 补充 → 3. Tavily 搜索 → 4. 去重 → **4.5. URL 验证** → 5. 排序 → **5.5. 重大事件深度溯源** → 6. 生成 Markdown → 7. 保存 Obsidian → **7.5. 媒体收集** → **8. 发布飞书**

### Step 0: 确认日期 + 计算采集时间窗口

**首先运行 `date` 命令确认当前日期**，不要依赖对话上下文或记忆文件中的日期。

1. **读取上次采集时间**：
   ```
   Glob ~/Documents/obsidian/mixiaomi/日报/{智涌日报,X日报}-*.md → 按日期倒序取第 1 篇
   Read frontmatter 的 collected_at 字段
   若无 collected_at，则以文件名日期 + "T23:59" 为近似值
   ```

2. **确定查询日期列表**：
   ```
   last_date = collected_at 的日历日
   today = date 命令返回的当前日历日
   若 last_date == today → query_dates = [today]
   若 last_date == yesterday → query_dates = [today]
   若 last_date < yesterday → query_dates = [last_date+1, ..., today]
   ```

3. **传递给后续步骤**：`query_dates` 和 `last_collected_at` 供 Step 1 和 Step 4 使用

### Step 1: Grok 四轮查询 (primary source)

用 anyweb `--page` 并行打开 4 个 Grok 页面，分别提交查询。

```bash
# Phase 1: Open pages (first must be serial to start daemon)
anyweb --chrome open --page grok1 "https://x.com/i/grok?new=true"
anyweb --chrome open --page grok2 "https://x.com/i/grok?new=true" &
anyweb --chrome open --page grok3 "https://x.com/i/grok?new=true" &
anyweb --chrome open --page grok4 "https://x.com/i/grok?new=true" &
wait

# Phase 2: Wait for textareas
anyweb --chrome wait --page grok1 selector "textarea" --timeout 15000 &
# ... (同理 grok2/3/4)
wait

# Phase 3: Submit queries (headless, no focus competition)
(anyweb --chrome click --page grok1 "textarea" && anyweb --chrome type --page grok1 "<Round 1>" && anyweb --chrome keys --page grok1 Enter) &
# ... (同理 grok2/3/4)
wait

# Phase 4: Wait for responses + read content
# 方案 A (推荐): AX Tree 轮询 — 用 state --ax 检测完成信号并读取内容
# 1. 轮询检测完成：AX tree 中出现 "Copy text" 按钮 = 回答完成
#    while true; do
#      anyweb --chrome state --page grok1 --ax -i 2>/dev/null | grep -q '"Copy text"' && break
#      sleep 3
#    done
# 2. 读取完整回答：AX tree 包含所有 StaticText 节点，即 Grok 全文
#    anyweb --chrome state --page grok1 --ax > /tmp/grok1.txt

# 方案 B (回退): JS Observer — 当 AX tree 不可用时
anyweb --chrome eval --page grok1 '<OBSERVER_JS>' > /tmp/grok1.txt &
# ... (同理 grok2/3/4)
wait
```

**方案 A: AX Tree 轮询（推荐）**

AX tree 的 `state --ax -i`（interactive-only）输出中包含所有按钮的 `aria-label`。检测 `"Copy text"` 按钮出现即表示 Grok 回答完成。完成后用 `state --ax` 获取全文，AX tree 的 StaticText 节点包含 Grok 完整回答（含 URL、列表结构）。

```bash
# 轮询检测完成（每 3 秒，超时 180 秒）
for i in $(seq 1 60); do
  sleep 3
  anyweb --chrome state --page grok1 --ax -i 2>/dev/null | grep -q '"Copy text"' && break
done

# 读取 Grok 完整回答
anyweb --chrome state --page grok1 --ax > /tmp/grok1.txt
```

**优势**：不需要复杂 JS Promise；AX tree 天然包含结构化文本（标题、列表、链接 URL），信息量比 `main.innerText` 更丰富。

**方案 B: JS Observer（回退）** — 检测 `aria-label="Copy text"` 按钮出现：
```javascript
new Promise(resolve => { const start = Date.now(); const check = () => { const elapsed = Math.floor((Date.now() - start) / 1000); const btns = document.querySelectorAll("button"); let hasCopy = false; for (const b of btns) { if (b.getAttribute("aria-label") === "Copy text" && b.offsetHeight > 0) { hasCopy = true; break; } } if (hasCopy && elapsed > 15) { const main = document.querySelector("main"); resolve(main ? main.innerText.substring(0, 15000) : "no main"); } else if (elapsed > 180) { const main = document.querySelector("main"); resolve("[TIMEOUT] " + (main ? main.innerText.substring(0, 15000) : "no main")); } else { setTimeout(check, 3000); } }; setTimeout(check, 10000); })
```

**日期模板**：根据 Step 0 的 `query_dates` 动态生成：
- 单日：`"today March 30 2026"`
- 跨天：`"on March 29 and March 30 2026"`

以下模板中 `{DATE_RANGE}` 替换为实际日期。

**Round 1: AI 行业动态**（官方/宏观视角）
```
What happened in the AI industry {DATE_RANGE}? Cover ALL of these categories:
1. New model releases, updates, or benchmarks (Claude, GPT, Gemini, DeepSeek, Grok, Qwen, Llama, Mistral etc.)
2. Product launches, API changes, pricing updates
3. Funding rounds, acquisitions, IPOs, partnerships
4. Executive and key personnel changes, departures, hirings (e.g. co-founders leaving, major talent moves between labs)
5. Company strategy shifts, org restructures, controversies, policy changes
6. Major research papers from AI labs
For each item include: company name, what happened, engagement stats if available, tweet URLs, and official announcement URLs (blog posts, press releases) if applicable.
```

**Round 2: AI 从业者动态**（一线/个人视角）
```
What are AI engineers, researchers, and developers sharing on Twitter {DATE_RANGE}? Focus on:
1. Frontier company engineers sharing technical insights, demos, or behind-the-scenes (from Anthropic, OpenAI, Google, Meta, Cursor, xAI etc.)
2. Developers sharing experiences building with or using AI tools (Claude Code, Cursor, Codex, Devin, v0 etc.)
3. Open source AI projects, new repos, or significant updates (LLM tools, agent frameworks, inference engines)
4. Hot debates or opinion threads about AI development practices, vibe coding, prompt engineering
For each item include: author, what they shared, engagement stats if available, and tweet URLs.
```

**Round 3: 具身智能行业动态**（官方/宏观视角）
```
What are the biggest industry news in robotics and physical AI {DATE_RANGE}? Cover ALL categories:
1. Humanoid robot product launches or company announcements (Tesla Optimus, Figure, Unitree, Boston Dynamics, AGIBOT, UBTech etc.)
2. AI chip, edge computing, or hardware product announcements (NVIDIA, custom silicon etc.)
3. Funding, IPOs, or industry partnerships in robotics
4. Key personnel changes, talent moves, or company strategy shifts in robotics
5. Government policy, regulations, or standards related to robotics and embodied AI
For each item include: company name, what happened, engagement stats if available, tweet URLs, and official announcement URLs (blog posts, press releases) if applicable.
Flag any tweets that contain demo videos with [VIDEO].
```

**Round 4: 具身智能从业者动态**（一线/研究视角）
```
What are robotics researchers and engineers sharing on Twitter {DATE_RANGE}? Focus on:
1. New research demos or papers in robot learning, manipulation, locomotion, sim-to-real, VLA/VLM models
2. Engineers from robotics companies sharing technical insights or behind-the-scenes
3. Open source robotics projects, datasets, simulation tools, or significant updates
4. Opinions and debates about embodied AI approaches, scaling, commercialization
For each item include: author, what they shared, engagement stats if available, and tweet URLs.
Flag any tweets that contain demo videos with [VIDEO].
```

**Grok 交互要点**：
- 必须用 `anyweb type`（键盘事件），不要在 type 末尾加 `\n`
- 提交用 `anyweb keys Enter`
- 每次 `?new=true` 开新对话
- 必须在每个问题中加 "Include tweet URLs"
- 用 `anyweb log` 排查操作失败
- **推荐用 AX Tree 读取 Grok 回答**：`state --ax` 返回结构化文本（含 URL），比 `eval main.innerText` 信息更完整
- **AX Tree 完成检测**：`state --ax -i | grep "Copy text"` 替代复杂 JS observer，更简洁可靠

**低新闻量降级策略**：如果 4 轮 Grok 中有 2 轮以上返回"No major announcements"或有效新闻条目不足 3 条，执行以下降级：
1. 扩大 Core Account 扫描范围：从 8-15 个增加到 20-30 个
2. Tavily 拆为 3-4 组更细分的查询
3. 日报标注"轻量日报"，概览中说明新闻量偏少

### Step 2: Core Account Supplement (并行化)

1. Read `references/core_accounts.yaml` → select 8-15 accounts across categories (ai_company, ai_frontline, robotics_company, robotics_dev, cn_dev 各取 2-4 个)
2. **并行读取**：直接并行多个 `anyweb read`，分批每批 5 个：

```bash
# Batch 1: 5 accounts in parallel
anyweb --chrome --json read "https://x.com/AnthropicAI" > /tmp/ca_AnthropicAI.json &
anyweb --chrome --json read "https://x.com/OpenAI" > /tmp/ca_OpenAI.json &
anyweb --chrome --json read "https://x.com/karpathy" > /tmp/ca_karpathy.json &
anyweb --chrome --json read "https://x.com/DrJimFan" > /tmp/ca_DrJimFan.json &
anyweb --chrome --json read "https://x.com/dotey" > /tmp/ca_dotey.json &
wait

# Batch 2: next 5 accounts
anyweb --chrome --json read "https://x.com/Figure_robot" > /tmp/ca_Figure_robot.json &
anyweb --chrome --json read "https://x.com/cursor_ai" > /tmp/ca_cursor_ai.json &
# ... continue with remaining accounts
wait

# Batch 3: repeat until all accounts done
```

**关键约束**：
- 每批最多 5 个并发，避免 X 限流
- **不需要 `--page` 或 `--session`**：`read` 内部自动 `new_page()` + `close()`，同一 daemon 天然支持并发
- 每个 JSON 输出到 `/tmp/ca_{username}.json`，后续统一读取合并
- **性能**：5 并发 ~6s/批，15 账号 3 批 ≈ 20 秒

3. **时间过滤**：只处理 `last_collected_at` 之后发布的推文，跳过更早的推文
4. **视频标记**：如果推文包含视频内容（尤其是 robotics_company/robotics_dev 的 demo 视频），标记 🎬
5. 每条推文包含 `[View tweet](URL)` 链接可直接使用

### Step 3: Tavily Search (supplementary)

```
tavily_search(query="AI OR Claude OR GPT OR LLM OR humanoid robot OR embodied AI", time_range="day", max_results=10)
```

**Tavily URL 可信度规则**：
- **可信域名**：cnet.com, bloomberg.com, reuters.com, techcrunch.com, theverge.com, arstechnica.com, wired.com, venturebeat.com, cnbc.com, nytimes.com, wsj.com, x.com, github.com, arxiv.org, huggingface.co
- **未知域名** → 标注 `[来源待验证]` 或不使用
- **绝不编造或猜测 URL**

### Step 3.5: Keyword Search (conditional)

**仅当 Grok 有效结果不足 5 条时执行**，作为补充搜索：

```bash
anyweb --chrome --json search x "AI OR Claude OR GPT OR LLM OR humanoid robot OR embodied AI" --limit 10
```

### Step 3.9: Data Source Barrier — MANDATORY

**在进入 Step 4 之前，必须确认所有数据源已返回。** 这是硬性屏障，不可跳过。

检查清单：
- [ ] Grok 4 轮查询全部完成（Step 1）
- [ ] Core Account 扫描全部完成（Step 2）— 如果使用了后台 Agent，必须用 `TaskGet`/`TaskOutput` 等待结果返回并读取
- [ ] Tavily 搜索完成（Step 3）

**Core Account 结果是 Grok 的关键补充**：Grok 偏向英文大事件，对中文开发者社区、中等热度推文覆盖不足。Core Account 扫描是唯一能补上这些盲区的数据源。如果跳过等待，日报将系统性遗漏关注列表中高互动内容。

只有三个数据源全部就绪，才能进入去重和排序。

### Step 4: Dedup Against Previous Digests

**必须在排序前执行**。

1. 读取 `last_collected_at` 之后的日报，提取已报道事件
2. **去重分类**：
   - **已报道且无新进展** → 移除
   - **已报道但有显著新数据**（如 likes 翻倍）→ 降级到「持续发酵」区
   - **全新事件** → 正常参与排序

### Step 4.5: URL 真实性校验 — MANDATORY

所有进入日报的推文 URL 必须经过验证。**两类假链接来源**都必须拦截：

**来源 1：Grok 编造 URL**——Grok 可能给出看似合理的 `x.com/user/status/ID`，但 ID 指向该用户多年前的无关推文。

**来源 2：Claude 自身补充时编造 URL**——在整合阶段，Claude 可能知道某事件存在但没有真实 URL，会猜测性地拼一个。**严禁这样做。没有从数据源（Grok/Core Account/Tavily）获得的 URL，就不能放 URL。** 如果事件确实重要但缺少 URL，用 `anyweb search x "关键词"` 搜索获取真实 URL。

**批量验证**：用 `anyweb read` 并行验证，每批 5 个（实测 ~6s/批，25 条 URL 约 30 秒）：

```bash
anyweb --chrome --json read "https://x.com/OpenAI/status/2039085161971896807" > /tmp/verify_1.json &
anyweb --chrome --json read "https://x.com/AnthropicAI/status/XXX" > /tmp/verify_2.json &
# ... 最多 5 个并发
wait
```

对每条推文检查：
1. **日期校验**：`Posted:` 字段日期必须在采集窗口内（`last_collected_at` 之后）
2. **内容校验**：推文实际内容必须与日报描述匹配
3. 不匹配 → 删除条目或用 `anyweb search x` 找到正确 URL 替换

**处理原则**：宁可少一条新闻，不可放一条假链接。链接不真实的条目一律删除。

### Step 5: Rank

按互动量（likes + retweets + replies）降序排列，然后分配到日报的五个板块：
- **具身智能** — 机器人公司动态、demo、部署、政策
- **模型与研究** — 新模型、论文、基准测试
- **产品与工具** — AI 工具、开源项目、SDK、开发者体验
- **行业动向** — 融资、收购、人事变动、战略调整
- **前瞻与观点** — 大佬观点、行业辩论、趋势判断

### Step 5.5: Deep Sourcing for Major Events

排序完成后，审视所有条目，判断是否存在**重大事件**需要深度溯源 + 官方源交叉验证。

**什么是重大事件**（由 AI 综合判断，不设硬阈值）：
- 产品/模型源码泄露、重大安全漏洞、供应链攻击
- 行业格局性融资、IPO、收购
- 重大人事变动（CEO/联创离职、关键人才流动）
- 新模型/产品发布引发全网讨论
- 重大政策/监管事件
- 核心判断标准：**这件事是否会被多家主流媒体报道？是否会在未来一周内持续发酵？**

**溯源动作**（对每个重大事件执行，按优先级排序）：
1. **官方源交叉验证**（首要）：仅有推文 URL 不够，必须找到官方一手源交叉确认。用 `tavily_extract` 验证（~5 秒），用 `tavily_search("site:xxx.com keyword")` 搜索官网链接。
   - 公司官方公告（融资、产品发布、战略调整）→ 查官网博客/新闻页
   - 论文发布 → 查 arxiv / 官方 research blog
   - 开源项目 → 查 GitHub repo
   - 政策/标准 → 查政府官网原文
   - **官方源 URL 获取**：Grok 原始输出 → Core Account 推文外链 → `tavily_search` → 都找不到则只放推文链接，不编造
2. **Grok 溯源**：向 Grok 提问"谁最早公开报道了 X 事件？找到原始推文 URL 和互动数据"——Grok 拥有实时 X 数据，是找原始推文和时间线的最佳工具
3. **anyweb search x**（补充推文搜索）：`anyweb --chrome --json search x "关键词"` 精确搜索相关推文，Grok 遗漏时用
4. **Tavily 深搜**（补充外部深度）：`tavily_search(search_depth="advanced")` 搜索权威媒体报道（arstechnica, venturebeat, cnbc, reuters, techcrunch 等）、GitHub 仓库、技术分析文章、HN 讨论
5. **社区反应**：core_accounts 中的评论降级为"社区反应"子板块，不作为主信源
6. **截图更新**：如果该事件进入 Top 5 截图，用原始推文替换二手评论截图

**重大事件的输出格式**（比普通条目多 3 层）：
```
- **事件标题** by @原始发现者
  > 事件经过（一手信源 + 技术细节 + 官方回应）
  > [来源](推文URL) | [官方公告](官网URL) | [媒体报道](URL)
  > **关键发现**：要点1 / 要点2 / 要点3（用 / 分隔，不要用子列表 `- item`）
  > **社区反应**：**@account1** 评论摘要。[推文](URL) **@account2** 评论摘要。[推文](URL)
  > **深度分析**：[文章1](URL) | [文章2](URL) | [文章3](URL)
  > 💡 编辑点评
```

**链接原则**：官方源找不到时只放推文链接，不编造。推文和官方源内容矛盾时，以官方源为准。

**不是重大事件的条目**：保持原有三层结构（事实层 + 评论层 + 点评层），不需要深度溯源。

### Step 6: Generate Digest Markdown

**核心原则：**

1. **每条新闻/推文必须附真实原文链接。链接不真实不如不放。**

2. **信源溯源（一手 vs 二手）**：
   - **一手信源**（官方账号、原始公告）→ 作为 `[来源]` 主链接
   - **二手信源**（KOL 转译/解读）→ 作为 `[中文解读](URL)` 附上
   - **core_accounts.yaml 中的 KOL**（dotey, HiTw93, Gorden_Sun 等）通常是二手信源

3. **视频标记**：含 demo 视频的推文在来源链接旁标注 🎬，供 Step 7.5 识别下载

**每条新闻三层结构**：
1. **事实层**：一手信源的客观事实摘要 + 来源链接
2. **评论层**：KOL 评论（粗体 @账号 + 摘要），可省略
3. **点评层**：💡 一句话编辑判断

**板块趋势**：每个 `##` 板块末尾加 `### 板块趋势`（2-3 句）

**排版约束**（飞书 + 微信共用）：
- `![[tweet-{id}.png]]` 截图必须放在 blockquote (`>`) **外面**
- **blockquote 内禁止嵌套子列表**（`> - item`）——飞书导入会变成空 bullet。改用 `/` 分隔的行内文本
- **正文不显示互动数据**——标题行不加 `(37,696 likes)`，内容中不提 likes/reposts 数字。互动数据仅保留在溯源表中
- **不加数据来源 footer**——文末不放"数据来源: Grok..."等 meta 信息

**Markdown 模板**：

```markdown
---
title: "智涌日报 - YYYY-MM-DD"
type: digest
date: YYYY-MM-DD
collected_at: "YYYY-MM-DDTHH:MM+08:00"
tags:
  - AI/development
category: AI/development
status: enriched
cover: "智涌日报-YYYY-MM-DD-cover.png"
---

# 智涌日报 - YYYY-MM-DD

![[智涌日报-YYYY-MM-DD-cover.png]]

## 概览
> 5-7 条一句话摘要，每条标注所属板块

## 具身智能
（三层结构 + 🎬 视频标记）

### 板块趋势

## 模型与研究
### 板块趋势

## 产品与工具
### 板块趋势

## 行业动向
### 板块趋势

## 前瞻与观点
### 板块趋势

## 持续发酵（前日已报，热度上升）

## 溯源表
| # | 标题 | 来源 | 互动数据 | 归属模块 |
```

### Step 7: Save

Save to `~/Documents/obsidian/mixiaomi/日报/智涌日报-YYYY-MM-DD.md`

### Step 7.5: Media Collection — MANDATORY

**此步骤不可跳过。** 详细实现见 `references/media-collection.md`。

**选取规则**：
- **封面图**：必做，每期日报一张
- **推文截图**：互动量 Top 5 的推文（必须有真实 tweet URL）
- **视频下载**：具身智能板块所有 🎬 标记的推文一律下载；其他板块仅 Top 5 且含视频的下载

**子步骤**：
1. 生成封面图（gemini-image skill）
2. 截取推文（anyweb + Pillow）
3. 下载视频（yt-dlp）
4. 嵌入 Obsidian 日报
5. 清理临时文件

### Step 8: Feishu Publish & Broadcast — MANDATORY

保存日报后**自动发布到飞书**，不需要询问。详细实现见 `references/feishu-publish.md`。

**核心步骤**：
1. 清理媒体目录（删除 cover-raw.png, tweet-full-*.png）
2. 调用 `publish_to_feishu()` — 必须传 `media_dir` 参数
3. 函数自动：创建/覆盖文档 + 上传图片/视频 + 发送卡片广播

---

## 3. Deep-Save Mode

Delegate to `x2md` skill with the tweet URL. No additional logic needed.

---

## 4. Report Mode

Generate periodic summaries from accumulated digests.

1. Glob `~/Documents/obsidian/mixiaomi/` for `type: digest` files in date range
2. Synthesize via `kb` skill: top events, ongoing trends, tools, accounts to watch
3. Save to `~/Documents/obsidian/mixiaomi/knowledge-base/synthesis/`
4. Ask user about Feishu sync

---

## Core Accounts

Managed in `references/core_accounts.yaml`. Read at the start of `digest` and `discover` modes.

---

## Known Limitations

### anyweb Chrome 模式

- **所有命令必须加 `--chrome`**：连接系统 Chrome，复用 X 登录态，不启动 Playwright
- anyweb daemon 在命令间保持页面状态
- 必须用 `anyweb --chrome type`（键盘事件），Grok textarea 是 React 受控组件
- 提交用 `anyweb --chrome keys Enter`（不要在 type 末尾加 `\n`）
- 每次 `?new=true` 开新对话
- 多页面用 `--page` 参数，Chrome 扩展支持多 tab 并行
- 第一个 `anyweb --chrome open` 必须串行（启动 daemon + 等待扩展连接），后续可并行
- 首次使用：`anyweb --chrome doctor` 安装 Chrome 扩展

### 推文抓取

- `anyweb read` 返回的推文包含 `[View tweet](URL)` 链接
- 深度抓取：`anyweb scroll down` → `anyweb eval` 提取
- DOM 选择器：`article[role="article"]`, `[data-testid="tweetText"]`, `time[datetime]`

### AX Tree 新特性（v2.2+）

- `anyweb state --ax`：获取完整 Accessibility Tree，包含页面所有文本和交互元素
- `anyweb state --ax -i`：仅交互元素（按钮、链接、输入框），用于检测 UI 状态
- `anyweb state --ax --depth N`：限制深度，减少输出量
- `anyweb click e5`：通过 AX ref ID 点击元素，比 CSS 选择器更稳定
- **Grok 场景优势**：AX tree 能看到 Grok 完整回答文本（包括列表和 URL），而旧 `state` 命令看不到动态渲染的内容

### 日报路径

中文目录: `~/Documents/obsidian/mixiaomi/日报/智涌日报-YYYY-MM-DD.md`
