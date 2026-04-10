---
name: article-gen
description: "Universal article generation engine. Operation-first routing: create, repost, rewrite, translate, summarize, extract, update. ALL content creation/modification in Obsidian vault goes through this skill. Use when user shares a URL ('保存', '存ob', '存一下'), says '记个点子', '新想法', '写个测评', '架构分析', '翻译', '总结一下', '提炼', '重新梳理', or any content creation/modification flow. NOT for vault queries — searching/browsing/syncing use ob skill."
---

# Article Gen

通用文章生成引擎。以**操作（operation）为一级路由**，内容类型（type）为二级差异化。所有 Obsidian vault 内容的创建和修改都通过本 skill。

## 路由总览

```
用户意图 → 识别 operation → 按 operation 执行流程 → 流程中按 type 做差异化
```

### Operation 路由表

| operation | 触发词 | 输入 | 产出 |
|-----------|-------|------|------|
| **create** | "写个/记个/新建" | 素材/口述/大纲 | 新文章 |
| **repost** | "保存/存ob/存一下" + URL | URL | 搬运到 vault 的文章 |
| **rewrite** | "重新梳理/改写/重组" | 已有 .md | 重组后的文章 |
| **translate** | "翻译/translate" | 外文 URL 或已有外文 .md | 翻译后的文章 |
| **summarize** | "总结/摘要/概括" | 已有 .md 或 URL | 摘要 |
| **extract** | "提炼/精简/核心观点" | 多篇 .md 或长文 | 提炼后的精简版 |
| **update** | "补充/追加/更新" | 已有 .md + 新内容 | 局部修改后的文章 |

### Operation 推断规则

- URL + "保存/存/存一下" → `repost`
- URL + "翻译" → `translate`
- "重新梳理/改写/重组" + 已有文章 → `rewrite`
- "总结/摘要" → `summarize`
- "提炼/精简/核心观点" → `extract`
- "补充/追加/更新一下" → `update`
- "写个/记个/新想法" → `create`
- X 链接（无额外指令）→ `repost`
- 推断不了 → 问用户

### Type 列表

| type | 说明 | 典型触发 |
|------|------|---------|
| `news` | 资讯/推文转述 | X 链接、新闻 URL |
| `article` | 外部文章搬运 | 博客/公众号 URL |
| `reference` | 技术参考文档 | 技术文章 URL |
| `architecture` | 技术架构分析 | "架构分析"、GitHub 链接 |
| `review` | 产品/项目测评 | "测评一下"、"对比" |
| `tutorial` | 技术教程 | "写个教程"、"怎么做" |
| `notes` | 读书/论文/项目笔记 | "读书笔记"、"记一下" |
| `essay` | 个人观点/思考 | "我觉得"、"想聊聊" |
| `idea` | 产品想法/创意点子 | "记个点子"、"新想法" |
| `research` | 公司/项目调研报告 | "调研 XX"、"帮我了解" |
| `digest` | 日报/摘要 | 由 x-feed/embodied-intel 生成 |
| `tweet` | X 推文原文 | X 短推文 |
| `moc` | Map of Content 索引 | 手动创建 |

**type 推断**：根据来源和内容自动推断，推断不了就问用户。

## 各 Operation 详细流程

---

### Operation: create（新建）

**场景**：从零或从素材创建一篇新文章。

**流程**：
1. **推断 type**：根据用户意图确定（architecture/review/tutorial/notes/essay/idea/research）
2. **收集素材**：用户提供，或按 type 引导收集
3. **Enrichment**：完整生成正文（按 type 加载模板）
4. **分类标签**：从 categories.md 匹配 category + tags + summary
5. **写入 frontmatter**：新建，`status: enriched`
6. **追加 `## 我的笔记`**：空节
7. **配图**：调用 `article-image` skill
8. **飞书发布**：询问用户
9. **Ingest 标记**：更新 index.md + log.md
10. **报告**

**按 type 加载风格参考**（enrichment 前必读）：
- `news` → [references/news-style.md](references/news-style.md)
- `notes` → [references/notes-style.md](references/notes-style.md)
- `research` → [references/research-style.md](references/research-style.md)
- 其他 type 遵循通用写作约束

---

### Operation: repost（转载/搬运）

**场景**：把外部 URL 的内容搬运到 vault，保留原文 + 补 frontmatter + enrichment。

**流程**：
1. **抓取原文**：
   - X 链接 → 调用 `x2md` skill
   - 其他 URL → `anyweb read` 获取正文 + `anyweb eval` 提取图片
   - 如需登录态 → `anyweb --chrome` 模式
2. **推断 type**：X → `news`/`tweet`；博客/技术文章 → `article`/`reference`
3. **Enrichment**：保留原文，补充 summary/category/tags
4. **翻译**（如 `lang != zh`）：重组为 `## 翻译` → `## 原文` 结构
5. **写入 frontmatter**：新建，含 source URL
6. **追加 `## 我的笔记`**
7. **配图**：官方 OG image 优先 → 原帖截图 → AI 生成
8. **飞书发布**：询问用户
9. **Ingest 标记**
10. **报告**

**存储路径**：`raw/{category一级}/` + `<作者> - <标题>.md`

---

### Operation: rewrite（改写/重组）

**场景**：已有文章的结构大幅调整、内容重组、版本升级。

**流程**：
1. **读取原文**：读取已有 .md 文件
2. **确认 type**：从 frontmatter 读取，或重新推断
3. **Enrichment**：按新结构重组正文（按 type 加载模板），保留原有数据和截图
4. **更新 frontmatter**：
   - 保留 `date`（原创建日期）
   - 更新 `updated`
   - 更新 `summary`/`category`/`tags`（如有变化）
   - `status: enriched`
5. **确保 `## 我的笔记`** 存在
6. **配图**：已有截图保留，可选新增
7. **飞书发布**：询问用户（如已发布过，提示更新）
8. **Ingest 标记**：更新 index.md + log.md
9. **报告**

**注意**：rewrite 不创建新文件，而是原地修改已有文件。

---

### Operation: translate（翻译）

**场景**：翻译一篇外文文章到中文。

**流程**：
1. **获取原文**：
   - URL → 抓取
   - 已有 .md → 直接读取
2. **推断 type**：同 repost
3. **翻译**：重组为 `## 翻译` → `## 原文` 结构（翻译在前）
4. **Enrichment**：基于译文生成 summary/category/tags
5. **写入 frontmatter**：`lang` 记录原文语言
6. **追加 `## 我的笔记`**
7. **配图**：图片只在 `## 翻译` 部分保留
8. **飞书发布**
9. **Ingest 标记**
10. **报告**

**翻译标准**：
- 信达雅，中文为主体
- 括号附英文：仅限业内常用英文缩写/术语（VLA、VLM、world model、fine-tune）
- 直接用中文：中文已表达清楚的词（预训练、缩放定律、感知、微调）
- 首次出现"中文（English）"，后续直接用中文
- 普通词一律中文：evidence→证据、data→数据、goal→目标
- 代码块不翻译

---

### Operation: summarize（摘要）

**场景**：对已有文章或 URL 生成简短摘要。

**流程**：
1. **读取内容**：已有 .md 或抓取 URL
2. **生成摘要**：3-5 条核心要点
3. **输出方式**（取决于用途）：
   - 更新到已有文章的 frontmatter `summary` 字段 → `update` 已有文件
   - 生成独立摘要文件 → 新建 `digest` 类型文件
   - 用于飞书推送 → 直接输出，不存文件
4. **Ingest 标记**：仅在新建文件时
5. **报告**

---

### Operation: extract（提炼）

**场景**：从长文或多篇文章中提炼核心观点，生成精简版。

**流程**：
1. **读取多篇**：指定的 .md 文件列表
2. **分析交叉**：找出共同主题、互补观点、矛盾点
3. **生成提炼文**：
   - type 通常为 `notes` 或 `essay`
   - frontmatter 中 `derived_from` 列出源文件路径
4. **Enrichment**：完整 frontmatter + summary + category
5. **追加 `## 我的笔记`**
6. **Ingest 标记**
7. **报告**

**存储路径**：`notes/{category一级}/`

---

### Operation: update（追加/修正）

**场景**：已有文章的小幅修改——补几行、更新数据、追加内容。

**流程**：
1. **读取原文**
2. **定位修改点**：用户指定或自动判断
3. **Edit 修改**：局部修改，不重组结构
4. **更新 frontmatter**：仅更新 `updated` 日期
5. **不做** Ingest 标记（小改动不需要）
6. **报告**

**注意**：update 不触发 enrichment，不改 category/tags/summary，不配图。

---

## 通用模块

### 存储路径

| 来源 | 目录 | 文件名 |
|------|------|--------|
| 外部内容（repost/translate） | `raw/{category一级}/` | `<作者> - <标题>.md` |
| 个人内容（create/rewrite/extract） | `notes/{category一级}/` | `<标题>.md` |
| 日报摘要（summarize → digest） | `wiki/日报/` | `<日报名>-YYYY-MM-DD.md` |

### 分类体系（category）

从 `~/Documents/obsidian/mixiaomi/meta/categories.md` 读取列表，选最匹配的。不匹配则提议新 category（`一级/二级` 格式），用户确认后追加到索引文件。

### Frontmatter 设计

详见 [references/frontmatter.md](references/frontmatter.md)（核心字段、类型扩展字段、完整示例）。

### 调用的 Skill

| Skill | 职责 | 何时调用 |
|-------|------|---------|
| `x2md` | X/Twitter → Markdown | repost 且 X 链接时 |
| `article-image` | 封面配图 | create/repost 后 |
| `feishu` | 飞书知识库发布 | 用户确认发布时 |

### Ingest 标记

文章保存/重大修改后：

1. **index.md** 的 `## 待处理` 追加：`- [[路径/文件名.md]] (YYYY-MM-DD)`
2. **log.md** 追加：`## [YYYY-MM-DD] ingest | 文章标题`

适用于：create, repost, rewrite, translate, extract。不适用于：update, summarize（仅更新 summary 字段时）。

### 飞书发布

询问用户「是否同步到飞书知识库？」

- **确认**：获取 token → 预处理 Markdown → curl 上传导入 → 移入 wiki 节点 → 图片上传 → 回写 frontmatter
- **拒绝**：跳过
- **推送资讯 bot**：完成同步 + 构建卡片 → 私信全员

### 非 X 链接抓取

```bash
# 1. 获取正文
anyweb --json read "https://..."

# 2. 提取页面图片
anyweb open "https://..."
anyweb eval "JSON.stringify([...document.querySelectorAll('article img, .post img, .blog img, meta[property=\"og:image\"]')].map(e => e.tagName === 'META' ? {src: e.content, alt: 'og-image'} : {src: e.src, alt: e.alt}).filter(i => i.src && !i.src.includes('data:image')))"
anyweb close
```

如需登录态：`anyweb --chrome` 模式。

## 写作风格约束

enrichment 正文生成时逐条自检：

- 禁止"一句话总结"、"核心要点"这类格式化小标题，用自然段落过渡
- 禁止"第一招/第二招"编号式标题，直接用加粗关键词起段
- 避免总结性套话（"综上所述"、"总而言之"）
- 不在正文中堆社交指标（赞/转发/浏览量）
- 术语不硬翻：业界通用英文术语保留原文，首次出现括号加中文解释
- 流程图/架构图用 Mermaid，禁止 ASCII art
- Mermaid flowchart 节点内不放列表或多行文本（Obsidian 渲染问题）
- Mermaid 发布到飞书前用 `mmdc` 转 PNG

## 正文模板

按 type 加载推荐章节结构，Claude 灵活调整。

| type | 骨架 |
|------|------|
| `news` | 详见 [references/news-style.md](references/news-style.md) |
| `notes` | 详见 [references/notes-style.md](references/notes-style.md) |
| `research` | 详见 [references/research-style.md](references/research-style.md) |
| `architecture` | 项目概述 → 技术栈 → 核心架构 → 关键模块 → 设计亮点与不足 |
| `review` | 产品简介 → 核心功能 → 实际体验 → 优缺点 → 竞品对比 → 结论 |
| `tutorial` | 问题背景 → 方案概述 → 实现步骤 → 常见问题 |
| `essay` | 观点 → 论据 → 反面思考 → 结论 |
| `idea` | 核心想法 → 目标用户 → 可能的实现路径 |
| `reference` | 要点提炼 → 我的笔记（非中文时加翻译/原文） |

## 执行检查清单

每篇文章完成后逐项自检：

- [ ] operation 正确识别
- [ ] type 正确推断
- [ ] 已读对应 type 的风格参考文件（如有）
- [ ] frontmatter 完整（title/type/date/category/tags/summary/status）
- [ ] `status` 已设为 `enriched`（create/repost/rewrite/translate/extract）
- [ ] 末尾有 `## 我的笔记` 空节（create/repost/rewrite/translate/extract）
- [ ] 非中文文章结构为 `## 翻译` → `## 原文`（翻译在前）
- [ ] 图片紧跟对应段落，不堆在开头或末尾
- [ ] 流程图用 Mermaid，不是 ASCII art
- [ ] Ingest 标记已更新（index.md + log.md）
- [ ] 存储路径正确（外部→raw/，个人→notes/）
- [ ] 飞书发布后已回写 `feishu_node_token` 和 `feishu_sync_time`

## 快捷流程示例

```
URL + "保存"     → repost  → 抓取 → enrichment → 配图 → 飞书 → 报告
URL + "翻译"     → translate → 抓取 → 翻译重组 → enrichment → 报告
"写个架构分析"    → create  → 素材 → enrichment(architecture) → 配图 → 报告
"重新梳理这篇"    → rewrite → 读取 → 重组 → 更新 frontmatter → 报告
"总结一下这篇"    → summarize → 读取 → 生成摘要 → 报告
"提炼这几篇的观点" → extract → 读取多篇 → 交叉分析 → 新文章 → 报告
"补充一段"        → update  → 读取 → Edit → 更新 updated → 报告
```
