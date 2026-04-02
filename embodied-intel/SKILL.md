---
name: embodied-intel
description: "Embodied AI industry intelligence briefing system - daily digest of humanoid robot and embodied intelligence news, person tracking, talent movement detection. Use when user says: '具身内参', '今天具身有什么新闻', '具身智能日报', '更新人物表', '添加跟踪人物', '删除跟踪人物', 'embodied digest', 'robot industry news'."
---

# 具身内参 - 具身智能行业情报系统

面向企业管理者的具身AI/人形机器人行业日报。通过多源数据采集（Grok 搜索 + 核心账号 + Tavily），生成情报摘要，发布到飞书并推送。

**工具依赖**：`anyweb` CLI（Grok 搜索 + 核心账号推文）、`tavily_search`（补充搜索）、lark-cli bitable（人物表）、飞书 API（发布+推送）

## Mode Router

| 用户意图 | Mode | 关键动作 |
|---------|------|---------|
| "具身内参"、"今天具身有什么新闻" | **digest** | 全流程情报生成 |
| "更新人物表"、"添加/删除跟踪人物" | **manage** | Bitable CRUD |

---

## 1. Digest Mode

### Step 1: Load Tools

```
# anyweb CLI available via Bash tool (anyweb open/read/eval/type/wait/scroll)
ToolSearch: "+tavily search" -> tavily_search
ToolSearch: "+lark bitable record" -> appTableRecord_list, appTableRecord_batchUpdate
```

### Step 2: Multi-Source Data Collection

**数据源优先级**：platform_read(核心账号) > Grok 搜索 > Tavily 搜索

三个数据源可以并行采集（Grok 各轮之间串行，但 Grok 整体与 platform_read/Tavily 可并行）。

#### 2a: Core Account Tweets（新增，最可靠源）

读取 `references/core_accounts.yaml` → 对核心账号抓取最新推文：

```bash
anyweb --json read "https://x.com/{account}"
```

每个账号抓取最近 5-10 条推文。**每条推文现在包含 `[View tweet](URL)` 链接**，直接使用。

推荐并行 3-5 个 read 调用。

#### 2b: Grok Search（主搜索源）

通过 `anyweb` 原子命令调用 Grok 搜索 X/Twitter。anyweb daemon 在命令间保持页面状态，每步串行执行即可。

**Grok 搜索模板（观察者模式）**：

用轮询代替固定等待 — 观察页面文本是否经历过增长并稳定下来，自动判断回复完成。
典型 20-40 秒完成。

```bash
# 1. 打开 Grok 新对话
anyweb open "https://x.com/i/grok?new=true"
# 2. 等待输入框出现
anyweb wait selector "textarea[placeholder='Ask anything']" --timeout 15000
# 3. 点击输入框并输入问题（用 type 命令，底层是键盘事件）
anyweb click "textarea[placeholder='Ask anything']"
anyweb type "<问题>. Include tweet URLs.\n"
# 4. 观察者等待回复完成
anyweb eval "new Promise(resolve=>{let lastLen=0,maxLen=0,stableCount=0,growthSeen=false;const start=Date.now();const check=()=>{const elapsed=Math.floor((Date.now()-start)/1000);const text=document.body.innerText;const len=text.length;if(len>maxLen)maxLen=len;if(len>lastLen+50){growthSeen=true;stableCount=0}else if(Math.abs(len-lastLen)<10){stableCount++}else{stableCount=0}lastLen=len;if(growthSeen&&stableCount>=3&&elapsed>20){resolve(text.substring(0,8000))}else if(elapsed>120){resolve(text.substring(0,8000))}else{setTimeout(check,3000)}};setTimeout(check,10000)})"
```

**观察者逻辑**：
1. 先等 10 秒让 Grok 开始处理
2. 每 3 秒检查文本长度变化
3. 文本**经历过增长**（>50 字符）且**连续 3 次无变化**（9 秒稳定） → 判定完成
4. 超过 120 秒兜底超时

**关键注意事项**：
- anyweb `type` 命令底层使用键盘事件（`page.keyboard.type`），适配 React 受控组件
- 提交方式：问题末尾加 `\n`
- 每次调用 `?new=true` 开新对话，避免历史残留
- **anyweb daemon 在命令间保持页面状态**，不需要把所有操作塞进一次调用
- **每个问题必须包含 "Include tweet URLs"**

**搜索轮次**（3-4 轮，串行）：

| 轮次 | 问题模板 | 目标 |
|------|---------|------|
| 1 | "Top tweets this week about humanoid robots, embodied AI. Include URLs." | 综合热门 |
| 2 | "Top tweets this week about {company names}, Tesla Optimus, dexterous hands, embodied AI funding. Include URLs." | 公司/供应链 |
| 3 | "Top tweets this week about Chinese humanoid robots at {event}, Xiaomi robot, robot funding in China. URLs please." | 中国市场 |
| 4 | "Top tweets this week from @DrJimFan @adcock_brett @TheHumanoidHub @CyberRobooo about robots or AI. URLs please." | KOL 动态 |

**Grok 返回格式**：每条推文包含作者、摘要、Likes/Reposts/Views、真实 URL。直接使用这些 URL，**不要编造或修改**。

#### 2c: Tavily Search（补充/降级源，新增）

当 Grok 不可用或需要补充非推文来源时使用：

```
tavily_search(query="humanoid robot embodied AI", time_range="day", max_results=10)
tavily_search(query="人形机器人 具身智能 融资", time_range="day", max_results=10, include_domains=["x.com", "techcrunch.com", "reuters.com"])
```

**Tavily URL 可信度规则**：
- **可信域名（直接使用）**：x.com, techcrunch.com, reuters.com, bloomberg.com, ieee.org, arxiv.org, therobotreport.com, venturebeat.com, cnbc.com, 36kr.com, cls.cn
- **未知域名** → 标注 `[来源待验证]` 或不使用
- **绝不编造或猜测 URL**

### Step 3: Read Person Table（可与 Step 2 并行）

```
bitable_v1_appTableRecord_list(
  app_token: "Fnsyb4Fu4a4ONPshEyEct0ntn0c",
  table_id: "tblNlbYmRM2HB1Aa",
  page_size: 100
)
```

### Step 4: Talent Cross-Check

将所有数据源（Grok + core accounts + Tavily）中提到的人物与 bitable `当前机构/公司` 比对：
- 不一致 → 标记 **[人事异动]**，写入模块一
- 一致且有观点 → 写入模块二

### Step 5: Dedup Against Previous Digests

```
Glob ~/Documents/obsidian/mixiaomi/日报/具身内参-*.md -> 最近 1-3 期
Read 标题 + 模块三事件标题
```
- 已报道无新进展 → 删除
- 已报道有重大更新 → 标注"持续发酵"
- 全新事件 → 正常排序

### Step 6: Generate Markdown

**格式规范**：
- 标签加粗（`**事件描述**：`）+ 空行分隔，不用 blockquote `>`
- 链接用 markdown 格式：`[查看原文](URL)`
- 模块四溯源表增加「互动」列和「来源渠道」列

```markdown
---
title: "具身内参 - YYYY-MM-DD"
type: digest
domain: embodied-ai
date: YYYY-MM-DD
tags:
  - AI/发展
category: AI/发展
status: enriched
---

# 具身内参 YYYY-MM-DD

**今日核心洞察**：[一句话概括今天最具商业价值的动态]

---

## 模块一：人才流向与关键人物异动

(若无异动：今日暂无关键人物异动)

- **[人名]** ([原机构/头衔]) -> [新机构/头衔]

  **异动分析**：[结合过往背景评估影响]

  **来源**：[查看原文](URL)

## 模块二：关键人物最新观点

- **[人名]**（[机构]-[头衔]）

  **核心观点**：[80字以内概括]

  **管理者点评**：[商业化视角评估]

  **信息源**：[查看原文](URL)

## 模块三：行业关键事项与商业洞察

- **[事件标题（互动数据）]**

  **事件描述**：[50字]

  **商业壁垒及产业链影响分析**：[管理者视角分析]

  **来源**：[查看原文](URL)

## 模块四：扩展阅读溯源

| # | 标题 | 来源 | 互动 | 渠道 | 模块 |
|---|------|------|------|------|------|
| 1 | [title] | [url] | [likes/views] | Grok/Core/Tavily | 模块X |

## 行业趋势观察

- [宏观趋势分析：跨多条信息的综合判断，技术路线演进、资本流向、产业链变化等]

## 给研发团队的特别提示

- [技术关注点]
- [竞品动态]

---

> 数据来源: X/Twitter (Grok Search + Core Accounts + Tavily)
> 跟踪人物: N人 (P0: n, P1: n, P2: n)
> 今日搜索: Grok N轮 + Core Accounts N个 + Tavily N条
> 去重参考: 具身内参-YYYY-MM-DD
```

### Step 7: Save Local

```
Save to ~/Documents/obsidian/mixiaomi/日报/具身内参-YYYY-MM-DD.md
```

### Step 8: Feishu Publish + Broadcast

**使用共享脚本** `~/.claude/skills/_shared/feishu_publish.py`：

**更新模式**: `publish_to_feishu()` 自动检测 frontmatter 中的 `feishu_node_token`。若已存在，则清空旧文档并覆盖内容（URL 不变、不产生重复文档）；若不存在，则新建文档并移入知识库。

```python
exec(open(os.path.expanduser('~/.claude/skills/_shared/feishu_publish.py')).read())

publish_to_feishu(
    md_path=os.path.expanduser('~/Documents/obsidian/mixiaomi/日报/具身内参-YYYY-MM-DD.md'),
    doc_title='具身内参 - YYYY-MM-DD',
    wiki_parent_node='JZIOwcpzGijmAYk6d4ecBXSlnig',  # 具身内参节点
    card_template='orange',
    card_title='具身内参 - YYYY-MM-DD',
    card_summary='**今日核心洞察**\n...\n\n**关键人物观点**\n- ...\n\n**行业要闻 TOP6**\n1. ...',
    recipients=['米冠飞', '陈卿', '李玮', '谢娟', '邓子晗'],
)
```

**飞书配置常量**：
```yaml
wiki_space_id: "7559794508562251778"
parent_node_token: "JZIOwcpzGijmAYk6d4ecBXSlnig"  # 具身内参 wiki 节点
card_header_template: "orange"
doc_url_pattern: "https://huazhi-ai.feishu.cn/docx/{doc_token}"
```

### Step 9: Update Bitable

```
bitable_v1_appTableRecord_batchUpdate(
  app_token, table_id,
  records: [{record_id: "...", fields: {"最后检测时间": <timestamp_ms>}}]
)
```
- 检测到人事异动时同步更新 `最新状态备注`

---

## 2. Manage Mode

CRUD operations on the person tracking table.

**Bitable 配置**：
```yaml
app_token: "Fnsyb4Fu4a4ONPshEyEct0ntn0c"
table_id: "tblNlbYmRM2HB1Aa"
```

### View Person List
```
bitable_v1_appTableRecord_list(app_token, table_id, page_size: 100)
```
Display as table: 姓名 | 机构 | 头衔 | 优先级

### Add Person
```
bitable_v1_appTableRecord_create(app_token, table_id,
  fields: {姓名, 英文名, 当前机构/公司, 头衔/身份, 关注的细分领域, 过往关键背景, 追踪优先级, Twitter Handle})
```

### Update / Delete / Search Person
```
bitable_v1_appTableRecord_update(app_token, table_id, record_id, fields: {...})
bitable_v1_appTableRecord_delete(app_token, table_id, record_id)
bitable_v1_appTableRecord_search(app_token, table_id, filter: "CurrentValue.[姓名].contains(\"<name>\")")
```

---

## Core Accounts

Managed in `references/core_accounts.yaml`. Read this file at the start of digest mode. Users can edit it anytime to add/remove accounts.

---

## Known Limitations

- **Grok 搜索耗时**：观察者模式下每轮 ~20-40 秒，3-4 轮总计 ~1.5-2.5 分钟。兜底超时 120 秒。
- **Grok 不可并行**：每个 Grok 调用独占一个浏览器页面，不能通过 Agent 并行多个 Grok 搜索。但 Grok 与 platform_read/Tavily 可以并行。
- **X 登录要求**：浏览器必须已登录 X 账号，否则 Grok 页面无法加载。
- **Bitable 分页**：人物超过 100 人时需用 `page_token` 翻页。
- **时间戳格式**：Bitable DateTime 字段用毫秒时间戳（`int(time.time() * 1000)`）。
- **飞书用户查找**：不能用 `/contact/v3/departments/0/children`（无权限），必须用 `/contact/v3/scopes` 获取授权范围后遍历。
- **Tavily 降级**：Tavily 无 JS 渲染能力，小众中文站有时搜不到；作为 Grok 不可用时的降级方案。
