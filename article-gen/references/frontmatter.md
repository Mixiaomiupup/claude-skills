# Frontmatter 设计

## 核心字段（所有类型共享）

```yaml
---
title: ""
author: ""
type: news              # news/article/reference/architecture/review/tutorial/notes/essay/idea/research/digest/tweet/moc
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
derived_from: []          # 可选，引用的 raw vault 素材文件路径列表
---
```

## 类型扩展字段

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

**idea：**
```yaml
target_user: "独立开发者"
```

**reference：**
```yaml
original_author: "Ryan Lopopolo"
original_date: "2026-02-11"
original_site: "OpenAI Blog"
```

**article：**
```yaml
original_author: "Tw93"
original_date: "2026-03-15"
original_site: "公众号"
original_url: "https://mp.weixin.qq.com/..."
```

**tweet：**
```yaml
author_handle: "@borischerny"
likes: 500
retweets: 120
```

**digest：**
```yaml
digest_name: "智涌日报"
digest_date: "2026-04-09"
source_count: 5
```

**research：**
```yaml
company_name: "Generalist AI"
founded: "2024"
funding: "Series A"
headquarters: "San Francisco"
```

## 完整示例

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
