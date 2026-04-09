---
name: article-gen
description: "Universal article generation engine. Supports 9 article types: news, reference, research, architecture, review, tutorial, notes, essay, idea. ALL content creation/saving to Obsidian vault goes through this skill. Use when user shares a URL ('保存', '存ob', '存一下'), says '调研XX公司', '帮我了解XX', 'XX是什么公司', '记个点子', '新想法', '记下来', '写个测评', '架构分析', '记个教程', '读书笔记', '分享到飞书', or any content creation flow. NOT for vault queries — searching/browsing/syncing use ob skill."
---

# Article Gen

通用文章生成引擎。支持 9 种文章类型，统筹从素材到发布的完整流程。所有内容创建/保存到 Obsidian vault 都通过本 skill。

## 文章类型 (`type`)

| type | 说明 | 典型输入 | 典型触发 |
|------|------|---------|---------|
| `news` | 资讯/推文转述 | X 链接、新闻 URL | "保存这条推文"、X 链接 |
| `architecture` | 技术架构分析 | GitHub 仓库、代码笔记 | "架构分析"、GitHub 链接 |
| `review` | 产品/项目测评 | 产品 URL、试用笔记 | "测评一下"、"对比" |
| `tutorial` | 技术教程 | 问题描述、代码片段 | "写个教程"、"怎么做" |
| `notes` | 读书/论文笔记 | PDF、文章链接、手写要点 | "读书笔记"、"读完了" |
| `essay` | 个人观点/思考 | 口述、大纲、零散想法 | "我觉得"、"想聊聊" |
| `idea` | 产品想法/创意点子 | 口述、灵感 | "记个点子"、"新想法"、"我想做..." |
| `reference` | 外部技术文章搬运 | 博客/文章 URL | URL + "保存"、"存一下" |
| `research` | 公司/项目调研报告 | 公司名 | "调研 XX"、"帮我了解 XX"、"XX 是什么公司" |

### 类型推断（混合模式）

根据输入自动推断，推断不了就问用户：

- X/Twitter 链接 → `news`
- GitHub 链接 → `architecture`
- 用户说"测评/对比/评测" → `review`
- 用户说"怎么做/教程/步骤" → `tutorial`
- 用户说"读完了/笔记/摘录" → `notes`
- 用户说"我觉得/想聊聊/观点" → `essay`
- 用户说"记个点子/新想法/我想做" → `idea`
- 非 X 的外部 URL + "保存/存ob/存一下" → `reference`
- 用户说"调研 XX/帮我了解 XX/XX 是什么公司" → `research`
- 推断不了 → 问用户选择

## 调用的 Skill

| Skill | 职责 | 何时调用 |
|-------|------|---------|
| `x2md` | X/Twitter → Markdown 转换 | `news` 类型且输入是 X 链接时 |
| `article-image` | 封面配图（官方图优先，无则 AI 生成） | enrichment 后（所有类型） |
| `feishu` | 飞书知识库发布 + 全员广播 | 用户确认发布时（所有类型） |

`x2md` 和 `article-image` 是独立 skill，不知道彼此的存在。`article-gen` 负责串联它们。

## 存储路径

按 type 选择目标 vault 和子目录：

| type | 目录 | 文件名 |
|------|------|--------|
| `news` | `~/Documents/obsidian/mixiaomi/raw/{category一级}/` | `<作者> - <标题>.md` |
| `reference` | `~/Documents/obsidian/mixiaomi/raw/{category一级}/` | `<作者> - <标题>.md` |
| `review` | `~/Documents/obsidian/mixiaomi/notes/{category一级}/` | `<标题>.md` |
| `tutorial` | `~/Documents/obsidian/mixiaomi/notes/{category一级}/` | `<标题>.md` |
| `architecture` | `~/Documents/obsidian/mixiaomi/notes/学习笔记/` | `<标题>.md` |
| `notes` | `~/Documents/obsidian/mixiaomi/notes/学习笔记/` | `<标题>.md` |
| `essay` | `~/Documents/obsidian/mixiaomi/notes/创意点子/` | `<标题>.md` |
| `idea` | `~/Documents/obsidian/mixiaomi/notes/创意点子/` | `<标题>.md` |
| `research` | `~/Documents/obsidian/mixiaomi/raw/{category一级}/` | `<公司名> - 公司调研.md` |

**单 Vault 三层结构**：news/reference 存入 raw/（外部素材），其他类型存入 notes/（个人内容）。wiki/ 由 LLM 编译维护。

category 一级分类直接对应 vault 顶级目录：`模型前沿/`、`具身动态/`、`编程范式/`、`工程实战/`、`AI思考/`、`商业观察/`。不做二次映射。

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
| `news` | 其他 URL | `anyweb read URL`（提取正文 + 图片）+ 存 Markdown |
| `architecture` | 项目路径或笔记 | 用户已完成研究，直接提供素材 |
| `review` | 产品 URL 或试用笔记 | 用户已完成研究，直接提供素材 |
| `tutorial` | 代码片段 / 问题描述 | 用户直接提供 |
| `notes` | PDF / URL / 手写要点 | analyze 抓取或用户直接提供 |
| `essay` | 口述 / 大纲 | 用户直接提供 |
| `idea` | 用户口述 / 灵感 | 用户直接提供 |
| `reference` | 外部 URL | `anyweb read URL`（提取正文 + 图片）+ 存 Markdown |
| `research` | 公司名 | 三路发现 + anyweb read 全文 + X 推文采集（详见 [research-style.md](references/research-style.md)） |
| 所有 | 本地已有 .md | 跳过转换，直接进入 enrichment |

**研究与写作分离**：非 `news` 类型的前置研究（代码探索、产品试用、资料搜集）在 article-gen 之外完成。article-gen 从"有素材"开始。

**非 X 链接抓取注意事项**：

抓取非 X/Twitter 的 URL 时，用 `anyweb read` 获取正文，再用 `anyweb eval` 提取页面中的图片 URL：

```bash
# 1. 获取正文
anyweb --json read "https://..."

# 2. 提取页面图片（hero image、正文内联图、OG image）
anyweb open "https://..."
anyweb eval "JSON.stringify([...document.querySelectorAll('article img, .post img, .blog img, meta[property=\"og:image\"]')].map(e => e.tagName === 'META' ? {src: e.content, alt: 'og-image'} : {src: e.src, alt: e.alt}).filter(i => i.src && !i.src.includes('data:image')))"
anyweb close
```

保存文章时：
1. 保留所有 `![...](url)` 图片引用，插入到正文对应位置
2. 如果是翻译文章（Step 3），图片只在 `## 翻译` 部分保留（翻译在前，读者主要看翻译），`## 原文` 部分不重复放图片

### Step 2: Enrichment

读取素材，Claude 分析内容并生成文章：

a. **分类**（category）：从 `~/Documents/obsidian/mixiaomi/meta/categories.md` 读取列表，选最匹配的。不匹配则提议新 category。

b. **标签**（tags）：1-3 个 category 级标签

c. **摘要**（summary）：3-5 条中文要点

d. **正文生成/重组**：按 `type` 加载风格参考和正文模板（见下文），根据素材灵活调整

**写作风格约束**（enrichment 正文生成时逐条自检）：
- 禁止"一句话总结"、"一个类比"、"核心要点"这类格式化小标题，用自然段落过渡
- 禁止"第一招/第二招/第三招"编号式标题，直接用加粗关键词起段
- 文章若以名人/热点为 hook，必须先讲他们，再接自己的内容做对照，不能反过来
- 避免用力过猛的动词（"偷"→"补"/"借鉴"），保持口语化但不刻意
- 避免总结性套话（"综上所述"、"总而言之"）
- 不在正文中堆社交指标（赞/转发/浏览量），读者不关心
- 术语不硬翻：业界通用英文术语保留原文，首次出现括号加中文解释（如 `System Card（模型的出厂安全评估报告）`），之后直接用英文
- 标题要"事实 + 观点"，一句话，不超过 30 字（news 类型），详见各 type 风格参考

**按 type 加载风格参考**（enrichment 前必读）：
- `news` → [references/news-style.md](references/news-style.md)（标题结构、正文骨架、语气、配图规则）
- `notes` → [references/notes-style.md](references/notes-style.md)（个人对照、原话引用、评论区挖掘）
- `research` → [references/research-style.md](references/research-style.md)（采集流程、采集清单、写作原则）
- 其他 type 暂无独立风格参考，遵循上方通用约束

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

翻译标准：信达雅，中文为主体。术语处理规则：
- **括号附英文**：仅限业内讨论时经常直接用英文、不附读者会对不上号的缩写/术语。如 VLA、VLM、world model、foundation model、action head、zero-shot、fine-tune
- **直接用中文**：中文已经表达清楚、业内人看中文就懂的词。如"预训练"不附 pretraining，"缩放定律"不附 scaling law，"感知"不附 perception，"微调"不附 fine-tune，"联合训练"不附 co-training
- **格式**：首次出现写"中文（English）"或"English（中文）"（取决于哪个更常用），后续直接用中文
- **决策方法**：不要看到原文有英文就条件反射地附上。问自己"这个中文会让读者困惑吗？"——不会就不附
- **普通词一律中文**：evidence→证据、data→数据、goal→目标、method→方法、build→构建、constraint→约束。绝不保留英文

**图片处理**：翻译文章中图片只在 `## 翻译` 部分保留（翻译在前，读者主要看翻译），`## 原文` 部分不重复放图片。

**注意**：`tutorial` 和 `architecture` 中的代码块不翻译。

### Step 4: 配图

**封面图优先级**（按顺序尝试）：
1. **官方图优先**：如果文章来源有官方 OG image 或 hero 图，直接下载使用（`meta[property="og:image"]`）
2. **原帖截图**：如果是 X/Twitter 内容，用原帖截图作为封面
3. **AI 生成**：以上都没有时，调用 `article-image` skill

AI 生成时调用 `article-image` skill（cover 模式，quick）：

```
article-image skill:
- 模式: cover
- 文章路径: <.md 绝对路径>
- category: <从 frontmatter 读取>
- 调用模式: quick
```

**文中截图规则**：
- **推文截图**：用 x-feed 标准流程（HIDE_JS + `getBoundingClientRect()` + Pillow 动态裁剪），不硬编码坐标
- **官网截图**：隐藏导航栏和侧边栏后再截，只保留内容区域
- 截图紧跟对应段落，不堆在文章开头或末尾

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

### Step 5.5: Ingest 标记

文章保存后，在 vault 根目录做两处追加：

1. **index.md** 的 `## 待处理` 区域追加一行：
   - `- [[raw/xxx/文件名.md]] (YYYY-MM-DD)`（news/reference 类型）
   - `- [[notes/xxx/文件名.md]] (YYYY-MM-DD)`（其他类型）

2. **log.md** 追加：
   - `## [YYYY-MM-DD] ingest | 文章标题`

### Step 6: 报告

向用户报告：
- 保存路径和文件名
- 文章标题、作者
- type 和 category
- tags
- 封面图路径（如生成）
- 飞书节点信息（如发布）

## 飞书图片上传（Step 5f）

文章含外部图片时，飞书导入后需手动上传替换。详细流程见 `feishu` skill 的「文档图片上传」章节。

**注意**：翻译文章有双倍图片（翻译 + 原文各一组），需全部替换。

## 推荐正文模板

每种 type 一套推荐章节结构。Claude 根据内容灵活调整——可以合并、拆分、增删章节，但整体骨架尽量贴近模板。

### news（资讯）
详见 [references/news-style.md](references/news-style.md) 的「正文结构」。骨架：开头 → 前情/背景 → 面向非专业读者的科普 → 核心内容（数据/能力）→ 多方观点 → 为什么重要。不能假设读者了解专业背景，必须补上下文。

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
详见 [references/notes-style.md](references/notes-style.md) 的「正文结构」。骨架：开头 → 他在做什么 → 反直觉的细节 → 我的体系（对比表）→ 我准备补的短板 → 评论区好观点 → 结尾。强调原话引用和个人对照。

### essay（个人观点）
```
## 观点
## 论据
## 反面思考
## 结论
```

### idea（创意点子）
```
## 核心想法
## 目标用户
## 可能的实现路径
## 我的笔记
```

### research（公司调研）
无固定模板。详见 [references/research-style.md](references/research-style.md)。
产品和能力放最前面，按内容自然分段，多引创始人/同行原话。

### reference（技术参考）
```
## 翻译（非中文时）
## 原文（非中文时）
## 要点提炼
## 我的笔记
```

## Frontmatter 设计

详见 [references/frontmatter.md](references/frontmatter.md)（核心字段、类型扩展字段、完整示例）。

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
  └── ~/Documents/obsidian/mixiaomi/meta/categories.md（与 ob skill 共享）

x-feed digest 模式也可调用 article-gen 的 enrichment + 发布流程。
ob sync 模式调用 feishu skill 做双向同步。
```

每个 skill 只做一件事，article-gen 负责串联。

## 内容格式规则

| 内容 | 格式 | 禁止 |
|------|------|------|
| **流程图/架构图** | Mermaid (`\`\`\`mermaid`) | ASCII art（箭头、方框字符画） |
| **PPT/幻灯片** | Marp (Markdown slides) | 其他 PPT 方案 |
| **飞书文档更新** | Block API 原地修改 | 删除重建（没有删除权限） |

**Mermaid 可读性规则**：

- **Sequence diagram 参与者 ≤ 4-5 个**：超过就按阶段拆成 2-3 张小图，底层细节用 `Note` 折叠进上层节点
- **选对格式**：流向关系（谁调谁）→ Mermaid；对照/比较（问题→方案、工具对比）→ 表格；线性阶段（v1→v2→v3）→ 一行文字 + 分段标题；层次架构 → Mermaid flowchart（控制节点数）
- Mermaid flowchart 节点内不要放列表或多行文本，Obsidian 会渲染为 "Unsupported markdown"

**Mermaid 发布到飞书注意**：飞书不渲染 Mermaid，导入前用 `mmdc -w 1460 -b white --scale 2` 转 PNG，导入后替换代码块为图片。详见 feishu skill「Mermaid 图表发布到飞书」。

## 执行检查清单

每篇文章完成后，逐项自检：

- [ ] **Step 2**: 已读对应 type 的风格参考文件（news→news-style.md, notes→notes-style.md）
- [ ] **Step 2**: 标题符合 type 风格要求（news: 事实+观点一句话≤30字）
- [ ] **Step 2**: 无社交指标堆砌、无叙事腔、无术语硬翻
- [ ] **Step 2**: 不假设读者了解专业背景，关键概念有解释或类比
- [ ] **Step 2**: frontmatter 的 `status` 已从 `raw` → `enriched`
- [ ] **Step 2**: `category`、`tags`、`summary` 已填充
- [ ] **Step 2**: 末尾有 `## 我的笔记` 空节
- [ ] **Step 1**: 非 X 链接用 `anyweb read` 抓取正文，用 `anyweb eval` 提取图片 URL
- [ ] **Step 3**: 非中文文章的正文结构是 `## 翻译` → `## 原文`（翻译在前）
- [ ] **Step 3**: 不是在末尾追加翻译，而是整体重组了文件
- [ ] **Step 3**: 图片只在 `## 翻译` 部分保留（读者主要看翻译），原文部分不重复
- [ ] **存储**: news/reference 存入 raw/，其他类型存入 notes/
- [ ] **Step 5**: 飞书发布后已回写 `feishu_node_token` 和 `feishu_sync_time`
- [ ] **格式**: 流程图用 Mermaid，不是 ASCII art
- [ ] **图片位置**: 每张图片（`![[]]`）紧跟其描述的段落，不要堆在文章开头或末尾
