---
name: x-feed
description: "X/Twitter information feed system - follow expansion, hot topic extraction, and knowledge distillation. Use when user says: 'discover people to follow', 'expand follow list', 'twitter digest', 'what's hot on twitter today', 'twitter weekly report', 'save this tweet', or any Chinese equivalents like '推特日报', '今天推特有什么', '扩展关注', '发现值得关注的人', '推特周报', '保存这篇推文'."
---

# X/Twitter Feed System

Orchestrate existing tools to manage Twitter information flow: discover accounts, extract hot content, distill knowledge.

**Tools used**: `ucal_browser_action`, `ucal_platform_read`, `ucal_platform_search` (load via ToolSearch first), `x2md` skill, `kb` skill, `feishu` skill.

**Prerequisite**: Load ucal tools via `ToolSearch` query `+ucal` before any mode.

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

1. `ucal_browser_action` with `url: "https://x.com/i/grok"` and actions:
   - `wait` for `textarea[placeholder='Ask anything']` (timeout 15s)
   - `keyboard_type` (NOT `type`) on that selector with question text + `\n` to submit
   - `eval_js` with `new Promise(r => setTimeout(() => r(document.body.innerText.substring(0, 4000)), 15000))` to wait for and extract Grok's response
2. Ask domain-specific questions, e.g.:
   - "AI programming leaders worth following on Twitter"
   - "Best indie hacker Chinese Twitter accounts"
   - User-specified domain queries
3. Grok returns recommendations + referenced posts
4. Optionally click "Posts" tab to extract recommended accounts from cited tweets
5. Filter out already-followed accounts
6. Present candidates to user

**Important**: Use `keyboard_type` (keyboard events), not `type` (page.fill), as Grok's textarea is a React controlled component. Keep all actions in a single `browser_action` call — the page closes between separate calls.

### Method B: Seed Cross-Analysis (deep)

1. **Select seeds** - User-specified or from `references/core_accounts.yaml` `discover_seeds` list
2. **Fetch following lists** - For each seed:
   ```
   ucal_platform_read(platform="x", url="https://x.com/{seed}/following")
   ```
   Collect 50-100 following per seed
3. **Cross-reference** - Find accounts followed by multiple seeds:
   - Count `overlap_count` (how many seeds follow this account)
   - Filter out already-followed accounts
4. **Rank** - Sort by `overlap_count` descending
5. **Optional enrichment** - Visit candidate profiles to get bio, use LLM to judge domain relevance
6. **Present results**:
   ```
   @handle | Display Name | Bio | Followed by N seeds
   ```

Methods A+B can combine: Grok for fast discovery, seed analysis for validation.

### Batch Follow (requires user confirmation)

Present recommended list -> user selects -> `ucal_browser_action` to Follow each selected account one by one.

---

## 2. Digest Mode

Generate a daily Twitter digest of hot content.

### Step 1: Grok Hot Topic Scan (primary source)

1. `ucal_browser_action` with `url: "https://x.com/i/grok"` and actions:
   - `wait` for `textarea[placeholder='Ask anything']` (timeout 15s)
   - `keyboard_type` on that selector with question + `\n`
   - `eval_js` wait 15s then extract `document.body.innerText` (up to 4000 chars)
2. Ask topic-focused questions:
   - "What are this week's hot topics in AI programming?"
   - "Latest developments with Claude/GPT?"
   - User-specified topics
3. Grok returns summary + cited posts (e.g. "37 posts", "12 web pages")
4. Optionally navigate to the conversation URL (`x.com/i/grok?conversation=<id>`) for follow-up extraction

### Step 2: Core Account Supplement

1. Read `references/core_accounts.yaml` -> select 5-10 accounts across categories
2. For each account:
   ```
   ucal_platform_read(platform="x", url="https://x.com/{user}")
   ```
   Grab recent 5 tweets per account
3. Supplements niche high-quality content Grok may miss

### Step 3: Keyword Search (optional)

```
ucal_platform_search(platform="x", query="AI OR Claude OR GPT OR LLM", limit=10)
```

### Step 3.5: Dedup Against Previous Digests

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

### Step 4: Rank and Classify

- Sort by engagement (likes + retweets + replies) descending
- LLM classify each into: Breaking News / Deep Read / Hot Discussion / Tool Recommendation / Opinion Clash

### Step 5: Generate Digest Markdown

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

## Breaking News
- **[Title/Summary]** by @author (likes count)
  > One-line summary

## Hot Discussions
- **[Topic]** - Multi-person debate
  > Pro: ... | Con: ...

## Worth Reading
- **[Title]** by @author - [Why worth reading]
  > URL: https://x.com/...

## Tool/Product Recommendations
- **[Product]** by @author - [One-line description]

## 持续发酵（前日已报，热度上升）
- **[事件]** (当前 likes，前日报道时 likes) — 新动态简述
```

### Step 6: Save & Publish

1. Save to `~/Documents/obsidian/mixiaomi/日报/X日报-YYYY-MM-DD.md`
2. Frontmatter: `type: digest`, tags from content analysis, `category` matching dominant topic
3. Publish to Feishu wiki and broadcast (see Step 7)

### Step 7: Feishu Publish & Broadcast (automatic)

After saving the digest locally, **always** publish to Feishu and broadcast. Do not ask — this is part of the digest flow.

All Feishu operations use curl（MCP 不支持文件上传，且 `im_v1_message_create` 对卡片消息有 JSON 序列化问题）。凭据从 `~/.claude.json` > `mcpServers` > `lark-mcp` > `args` 中读取 `-a` (app_id) 和 `-s` (app_secret)。

用一个 Python 脚本完成 7a + 7b 全流程，示例：

```python
import json, subprocess, time, re, os

def curl_json(args):
    r = subprocess.run(['curl', '-s'] + args, capture_output=True, text=True)
    return json.loads(r.stdout)

# --- 读取凭据 ---
with open(os.path.expanduser('~/.claude.json')) as f:
    config = json.load(f)
lark_args = config['mcpServers']['lark-mcp']['args']
app_id = lark_args[lark_args.index('-a') + 1]
app_secret = lark_args[lark_args.index('-s') + 1]

# --- 获取 tenant_access_token ---
token = curl_json(['-X', 'POST',
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({'app_id': app_id, 'app_secret': app_secret})
])['tenant_access_token']
```

**7a. Publish to wiki**:

1. **预处理 markdown**：去掉 YAML frontmatter、`![[image]]`、`[[wikilink]]` → 写入 `/tmp/` 临时文件

2. **上传文件到云盘**：
```python
fsize = os.path.getsize(tmp_path)
resp = curl_json(['-X', 'POST',
    'https://open.feishu.cn/open-apis/drive/v1/files/upload_all',
    '-H', f'Authorization: Bearer {token}',
    '-F', f'file_name={filename}',
    '-F', 'parent_type=explorer', '-F', 'parent_node=',
    '-F', f'size={fsize}', '-F', f'file=@{tmp_path}',
])
file_token = resp['data']['file_token']
```

3. **创建导入任务**（`point.mount_key` 是应用根目录 token）：
```python
resp = curl_json(['-X', 'POST',
    'https://open.feishu.cn/open-apis/drive/v1/import_tasks',
    '-H', f'Authorization: Bearer {token}',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({
        'file_extension': 'md', 'file_token': file_token,
        'type': 'docx', 'file_name': '文档标题',
        'point': {'mount_type': 1, 'mount_key': 'nodcn8QDoQdhGBYxo9yRouGWEpb'}
    })
])
ticket = resp['data']['ticket']
```

4. **轮询获取 doc_token**（通常 2-4 秒完成）：
```python
for i in range(10):
    time.sleep(2)
    result = curl_json([
        f'https://open.feishu.cn/open-apis/drive/v1/import_tasks/{ticket}',
        '-H', f'Authorization: Bearer {token}',
    ])
    doc_token = result.get('data', {}).get('result', {}).get('token')
    if doc_token:
        break
```

5. **移入 wiki 知识库**（根据日报主 tag 选择父节点）：
```python
curl_json(['-X', 'POST',
    'https://open.feishu.cn/open-apis/wiki/v2/spaces/7559794508562251778/nodes/move_docs_to_wiki',
    '-H', f'Authorization: Bearer {token}',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({
        'parent_wiki_token': parent_node_token,  # 见下方映射
        'obj_type': 'docx', 'obj_token': doc_token
    })
])
```

**父节点映射**：
| 主 tag | parent_wiki_token | 飞书节点 |
|--------|-------------------|---------|
| `AI/*` | `IOsNwtIPdiLTYukHdgqcMIE9nad` | 行业资讯/AI |
| `技术/*` | `T1mzw30Bkir5IKkzbx9cxDFHnDe` | 行业资讯/技术 |
| `商业/*` | `EdB8wcEbeigCFPkYqUXcNpZWnlc` | 行业资讯/商业 |
| `思考/*` | `Xps2wjrCiixmB3kUKZscWLQQnge` | 行业资讯/思考 |

6. **获取 node_token**（等 3 秒让异步移动完成）：
```python
time.sleep(3)
resp = curl_json([
    f'https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node?token={doc_token}&obj_type=docx',
    '-H', f'Authorization: Bearer {token}',
])
node_token = resp['data']['node']['node_token']
```

7. **回写本地 frontmatter**：更新 `feishu_node_token` 和 `feishu_sync_time`

**7b. Broadcast card to all users**:

1. **获取 bot 可用范围内所有用户**：
```python
all_users = {}  # {open_id: name}

# 获取授权范围
scopes = curl_json([
    'https://open.feishu.cn/open-apis/contact/v3/scopes',
    '-H', f'Authorization: Bearer {token}',
]).get('data', {})

# 遍历每个部门获取成员
for dept_id in scopes.get('department_ids', []):
    resp = curl_json([
        f'https://open.feishu.cn/open-apis/contact/v3/users/find_by_department'
        f'?department_id={dept_id}&user_id_type=open_id'
        f'&department_id_type=open_department_id&page_size=50',
        '-H', f'Authorization: Bearer {token}',
    ])
    for user in resp.get('data', {}).get('items', []):
        all_users[user['open_id']] = user.get('name', 'unknown')

# 补充直接指定的用户
for uid in scopes.get('user_ids', []):
    if uid not in all_users:
        all_users[uid] = f'user_{uid[-8:]}'
```

2. **构建卡片消息**：
```python
card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": "日报标题"},
        "template": "blue"
    },
    "elements": [
        {"tag": "div", "text": {"tag": "lark_md", "content": (
            "**本周 AI 热点速览**\n\n"
            "**重大新闻**\n* 要点1\n* 要点2\n\n"
            "**热门讨论**\n* 要点1\n* 要点2\n\n"
            "**工具推荐**\n* 要点1\n* 要点2"
        )}},
        {"tag": "action", "actions": [{
            "tag": "button",
            "text": {"tag": "plain_text", "content": "查看完整日报"},
            "url": f"https://huazhi-ai.feishu.cn/docx/{doc_token}",
            "type": "primary"
        }]}
    ]
}
```

3. **逐个发送私信**（限流 0.1s/条）：
```python
for uid, name in all_users.items():
    body = {"receive_id": uid, "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False)}
    resp = curl_json(['-X', 'POST',
        'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id',
        '-H', f'Authorization: Bearer {token}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(body, ensure_ascii=False),
    ])
    time.sleep(0.1)
```

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

- 必须用 `keyboard_type`（键盘事件），不能用 `type`（page.fill），因为 Grok textarea 是 React 受控组件
- 提交用 `\n` 结尾即可，无需找发送按钮
- 所有 action 必须在同一次 `browser_action` 调用中完成（含 url 参数），页面在调用间会关闭
- 等待回复用 `eval_js` + `setTimeout` 15 秒后提取 `document.body.innerText`

### 推文抓取最佳实践

`platform_read(platform="generic")` 只拿到首屏/置顶推文。深度抓取用 `browser_action`:

```javascript
// 1. 先滚动加载更多
{"type": "scroll", "direction": "down", "amount": 2000}
// 2. 等待加载
{"type": "eval_js", "expression": "new Promise(r => setTimeout(r, 2000))"}
// 3. JS 提取推文数据
{"type": "eval_js", "expression": "document.querySelectorAll('article[role=\"article\"]')..."}
```

**推文 DOM 选择器**:
- 推文容器: `article[role="article"]`
- 正文: `[data-testid="tweetText"]`
- 时间: `time[datetime]`
- 互动: `[data-testid="reply"]`, `[data-testid="retweet"]`, `[data-testid="like"]` 的 `aria-label`

### MCP Server 代码更新

修改 `twitter.py` 或 `server.py` 后需重启 Claude Code 会话，MCP server 才会加载新代码。运行中的 server 用旧代码。

### 日报保存路径

实际路径用中文目录: `~/Documents/obsidian/mixiaomi/日报/X日报-YYYY-MM-DD.md`。
