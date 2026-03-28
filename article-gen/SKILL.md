---
name: article-gen
description: "Universal article generation engine. Supports 6 article types: news, architecture, review, tutorial, notes, essay. Orchestrates convert -> enrich -> translate -> cover image -> publish. Use when user shares a link to save, says '保存', '写个测评', '架构分析', '记个教程', '读书笔记', '分享到飞书', or any article generation flow."
---

# Article Gen

通用文章生成引擎。支持 6 种文章类型，统筹从素材到发布的完整流程。

## 文章类型 (`type`)

| type | 说明 | 典型输入 | 典型触发 |
|------|------|---------|---------|
| `news` | 资讯/推文转述 | X 链接、新闻 URL | "保存这条推文"、X 链接 |
| `architecture` | 技术架构分析 | GitHub 仓库、代码笔记 | "架构分析"、GitHub 链接 |
| `review` | 产品/项目测评 | 产品 URL、试用笔记 | "测评一下"、"对比" |
| `tutorial` | 技术教程 | 问题描述、代码片段 | "写个教程"、"怎么做" |
| `notes` | 读书/论文笔记 | PDF、文章链接、手写要点 | "读书笔记"、"读完了" |
| `essay` | 个人观点/思考 | 口述、大纲、零散想法 | "我觉得"、"想聊聊" |

### 类型推断（混合模式）

根据输入自动推断，推断不了就问用户：

- X/Twitter 链接 → `news`
- GitHub 链接 → `architecture`
- 用户说"测评/对比/评测" → `review`
- 用户说"怎么做/教程/步骤" → `tutorial`
- 用户说"读完了/笔记/摘录" → `notes`
- 用户说"我觉得/想聊聊/观点" → `essay`
- 推断不了 → 问用户选择

## 调用的 Skill

| Skill | 职责 | 何时调用 |
|-------|------|---------|
| `x2md` | X/Twitter → Markdown 转换 | `news` 类型且输入是 X 链接时 |
| `article-image` | 封面配图（5D 风格 + 生图） | enrichment 后（所有类型） |
| `feishu` | 飞书知识库发布 + 全员广播 | 用户确认发布时（所有类型） |

`x2md` 和 `article-image` 是独立 skill，不知道彼此的存在。`article-gen` 负责串联它们。

## 分类体系 (`category`)

**`category` 与 `type` 解耦**：`type` 描述文章形式，`category` 描述内容领域。

**Category 列表从索引文件读取**：`~/Documents/obsidian/mixiaomi/meta/categories.md`

**半自动扩展机制**：
1. Enrichment 时从索引文件读取已知 category 列表
2. 如果内容不属于任何已知 category，提议一个新 category（遵循 `一级/二级` 格式）
3. 用户确认后，追加到索引文件对应一级分类下
4. 已确认的 category 下次直接可用

## 工作流

```
输入 → 类型推断 → 转换 → Enrichment → 翻译 → 配图 → 发布 → 报告
  │        │         │        │          │       │       │       │
  │    自动/问     按type   Claude     Claude  cover   feishu  feishu
  │     用户      分支      (内置)     (内置)  -image  (skill) (skill)
  │                                           (skill)
  ▼
 报告结果
```

### Step 0: 类型推断

根据上文「类型推断」规则确定 `type`。推断不了就问用户。

### Step 1: 转换

根据 `type` 和输入来源调用对应转换工具：

| type | 输入 | 转换方式 |
|------|------|---------|
| `news` | X 链接 | 调用 `x2md` skill → `.md`（`status: raw`） |
| `news` | 其他 URL | `tavily_extract`（`include_images: true`）+ 存 Markdown |
| `architecture` | 项目路径或笔记 | 用户已完成研究，直接提供素材 |
| `review` | 产品 URL 或试用笔记 | 用户已完成研究，直接提供素材 |
| `tutorial` | 代码片段 / 问题描述 | 用户直接提供 |
| `notes` | PDF / URL / 手写要点 | ucal 抓取或用户直接提供 |
| `essay` | 口述 / 大纲 | 用户直接提供 |
| 所有 | 本地已有 .md | 跳过转换，直接进入 enrichment |

**研究与写作分离**：非 `news` 类型的前置研究（代码探索、产品试用、资料搜集）在 article-gen 之外完成。article-gen 从"有素材"开始。

**非 X 链接抓取注意事项**：

抓取非 X/Twitter 的 URL 时，**必须使用 `tavily_extract` 并开启 `include_images: true`**，否则文章中的架构图、流程图等内联图片会丢失。

```python
# 正确做法
tavily_extract(urls=["https://..."], include_images=True, format="markdown")

# 错误做法（图片会丢失）
tavily_extract(urls=["https://..."])  # include_images 默认 false
anyweb --json read "https://..."  # 不返回图片 URL
```

抓取结果中的图片以 `![alt](url)` 格式出现在 raw content 中。保存文章时：
1. 保留所有 `![...](...)` 图片引用，插入到正文对应位置
2. 如果是翻译文章（Step 3），翻译和原文两个部分都要插入图片
3. 图片 alt text 在翻译部分用中文描述，原文部分保留英文原始 alt

### Step 2: Enrichment

读取素材，Claude 分析内容并生成文章：

a. **分类**（category）：从 `~/Documents/obsidian/mixiaomi/meta/categories.md` 读取列表，选最匹配的。不匹配则提议新 category。

b. **标签**（tags）：1-3 个 category 级标签

c. **摘要**（summary）：3-5 条中文要点

d. **正文生成/重组**：按 `type` 加载推荐正文模板（见下文），根据素材灵活调整

e. **扩展字段**：填充当前 type 的扩展字段（有数据就填，没有不强制）

f. **更新 frontmatter**：填入所有字段，`status: raw` → `status: enriched`

g. 追加 `## 我的笔记` 空节（供后续笔记用）

### Step 3: 翻译

如果 `lang` 不是 `zh`（非中文内容），**重组**正文结构（不是在末尾追加翻译）：

```markdown
## 翻译
（中文译文）

## 原文
（英文原文）
```

**执行要点**：这是「重组」操作——将原文移到 `## 原文` 下，翻译放在 `## 翻译` 下，翻译在前。用 Write 工具整体重写文件，不要用 Edit 在末尾追加。

翻译标准：信达雅，专有名词不翻译，技术术语保留英文并括号注中文。

**注意**：`tutorial` 和 `architecture` 中的代码块不翻译。

### Step 4: 配图

调用 `article-image` skill（cover 模式，quick）：

```
article-image skill:
- 模式: cover
- 文章路径: <.md 绝对路径>
- category: <从 frontmatter 读取>
- 调用模式: quick
```

`article-image` 会自动完成风格选择 → 生图 → 嵌入文章。

### Step 5: 飞书发布

询问用户「是否同步到飞书知识库？」

- **用户确认**：
  a. 根据 `category` 一级分类确定目标飞书节点（查 `feishu` skill 的标签→节点映射表）
  b. 获取 `tenant_access_token`
  c. 预处理 Markdown（去 frontmatter、`![[]]`、`[[wikilink]]`、`[toc]`）
  d. curl 文件上传 + 导入任务发布文档（参考 `feishu` skill 的「curl 文件上传导入」方法）
  e. curl 移入 wiki 对应节点
  f. **如文章含外部图片**：执行图片上传流程（见下方「飞书图片上传」）
  g. 回写本地 frontmatter：`feishu_node_token`、`feishu_sync_time`
  h. 报告同步成功

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
- type 和 category
- tags
- 封面图路径（如生成）
- 飞书节点信息（如发布）

## 飞书图片上传（Step 5f 详细流程）

飞书 Markdown 导入**不会自动获取外部图片 URL**，导入后显示"无法导入该图片"。文章含 `![](https://...)` 内联图片时，必须在文档导入后手动上传图片。

### 前置条件

- `user_access_token`（UAT）：图片操作必须用 UAT，tenant token 不行。缓存在 `/tmp/feishu_uat.json`，过期自动 refresh
- `doc_token`：Step 5d 导入后获得的文档 token
- 已安装 `librsvg`：`brew install librsvg`（SVG 转 PNG 用）

### 完整流程

```python
# 1. 下载外部图片
curl -s -o /tmp/img.svg "https://images.ctfassets.net/..."

# 2. SVG 转 PNG（飞书不支持 SVG）
#    ✅ rsvg-convert -w 1460 input.svg -o output.png  （保持宽高比）
#    ❌ qlmanage -t -s 1460  （生成正方形缩略图，图片会拉伸）
rsvg-convert -w 1460 /tmp/img.svg -o /tmp/img.png

# 3. 列出文档所有 blocks，找到 image block（block_type=27）
GET /docx/v1/documents/{doc}/blocks?page_size=500
# → 记录每个 image block 的 block_id

# 4. 对每个 image block 执行上传+绑定（需 UAT）
# 4a. 上传图片（parent_type=docx_image, parent_node=block_id）
POST /drive/v1/medias/upload_all
  -F file_name=img.png
  -F parent_type=docx_image
  -F parent_node={block_id}    # 必须是 block_id，不是 doc_id
  -F size={file_size}
  -F file=@/tmp/img.png
# → 获得 file_token

# 4b. replace_image 绑定图片到 block
PATCH /docx/v1/documents/{doc}/blocks/{block_id}
  {"replace_image": {"token": "{file_token}"}}
```

### 关键注意事项

- **翻译文章有双倍图片**：翻译和原文两部分各有一组图片 block，需要全部替换
- **`parent_node` 必须是 block_id**，不是 doc_id，否则 `replace_image` 报 `1770013 relation mismatch`
- **PNG 格式优先**：飞书支持 PNG/JPG，不支持 SVG/WebP
- **UAT 获取**：运行 `python3 ~/.claude/skills/feishu/scripts/oauth_server.py` 启动 OAuth，或检查 `/tmp/feishu_uat.json` 缓存是否有效
- 详细的 UAT 获取和 block API 参考见 `feishu` skill 的「文档图片上传」章节

## 推荐正文模板

每种 type 一套推荐章节结构。Claude 根据内容灵活调整——可以合并、拆分、增删章节，但整体骨架尽量贴近模板。

### news（资讯）
```
## 翻译（非中文时）
## 原文（非中文时）
## 要点分析
## 我的笔记
```

### architecture（架构分析）
```
## 项目概述
## 技术栈
## 核心架构
## 关键模块分析
## 设计亮点与不足
## 总结
```

### review（产品测评）
```
## 产品简介
## 核心功能
## 实际体验
## 优缺点
## 竞品对比（如有）
## 结论
```

### tutorial（技术教程）
```
## 问题背景
## 方案概述
## 实现步骤
## 常见问题
## 总结
```

### notes（读书/论文笔记）
```
## 核心论点
## 关键概念
## 精彩摘录
## 我的思考
```

### essay（个人观点）
```
## 观点
## 论据
## 反面思考
## 结论
```

## Frontmatter 设计

### 核心字段（所有类型共享）

```yaml
---
title: ""
author: ""
type: news              # news/architecture/review/tutorial/notes/essay
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
---
```

### 类型扩展字段

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

## Frontmatter 完整示例

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

## 快捷流程示例

### 资讯（现有流程不变）
```
用户: "https://x.com/... 保存到飞书"
→ 推断 type=news → x2md → enrichment → 翻译 → 配图 → 飞书发布 → 报告
```

### 架构分析
```
用户: [已用代码探索研究完 openclaw] "帮我写个架构分析"
→ 推断 type=architecture → 用户提供素材/笔记 → enrichment（架构模板） → 配图 → 报告
```

### 产品测评
```
用户: [已试用完产品] "写个 Cursor 测评"
→ 推断 type=review → 用户提供体验笔记 → enrichment（测评模板） → 配图 → 报告
```

### 技术教程
```
用户: "写个教程，讲怎么用 MCP 连飞书"
→ 推断 type=tutorial → 用户提供步骤/代码 → enrichment（教程模板） → 配图 → 报告
```

## 与其他 Skill 的关系

```
article-gen (本 skill，总编排)
  ├── x2md ——— X → Markdown（仅 news 类型调用）
  ├── article-image ——— 封面配图（所有类型）
  ├── feishu ——— 飞书发布（所有类型）
  └── Claude ——— enrichment + 翻译（内置能力，非 skill）

共享资源：
  └── ~/Documents/obsidian/mixiaomi/meta/categories.md（与 kb skill 共享）

x-feed digest 模式也可调用 article-gen 的 enrichment + 发布流程。
kb sync 模式调用 feishu skill 做双向同步。
```

每个 skill 只做一件事，article-gen 负责串联。

## 内容格式规则

| 内容 | 格式 | 禁止 |
|------|------|------|
| **流程图/架构图** | Mermaid (`\`\`\`mermaid`) | ASCII art（箭头、方框字符画） |
| **PPT/幻灯片** | Marp (Markdown slides) | 其他 PPT 方案 |
| **飞书文档更新** | Block API 原地修改 | 删除重建（没有删除权限） |

**Mermaid 发布到飞书注意**：飞书不渲染 Mermaid，导入前用 `mmdc -w 1460 -b white --scale 2` 转 PNG，导入后替换代码块为图片。详见 feishu skill「Mermaid 图表发布到飞书」。

## 执行检查清单

每篇文章完成后，逐项自检：

- [ ] **Step 2**: frontmatter 的 `status` 已从 `raw` → `enriched`
- [ ] **Step 2**: `category`、`tags`、`summary` 已填充
- [ ] **Step 2**: 末尾有 `## 我的笔记` 空节
- [ ] **Step 1**: 非 X 链接抓取时使用了 `include_images: true`，图片已插入正文对应位置
- [ ] **Step 3**: 非中文文章的正文结构是 `## 翻译` → `## 原文`（翻译在前）
- [ ] **Step 3**: 不是在末尾追加翻译，而是整体重组了文件
- [ ] **Step 3**: 翻译和原文两部分都包含了原文中的内联图片
- [ ] **Step 5**: 飞书发布后已回写 `feishu_node_token` 和 `feishu_sync_time`
- [ ] **格式**: 流程图用 Mermaid，不是 ASCII art
