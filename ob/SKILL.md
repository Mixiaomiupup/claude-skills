---
name: ob
description: "Obsidian 知识库查询与管理 — 搜索内容、综合分析、维护个人洞察、浏览目录、双向同步飞书知识库、管理待办事项。当用户说'搜一下知识库'、'总结一下'、'有什么关于...'、'知识库有什么'、'同步飞书'、'看看飞书有什么新的'、'加个待办'、'看看待办'、'完成了XX'时使用。不负责内容创建 — 存文章、记点子、写笔记走 article-gen。"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# Obsidian 知识库管理

单一 vault 的检索、综合、洞察、浏览、飞书同步和待办操作。

**Vault**: `~/Documents/obsidian/mixiaomi`

| 层 | 目录 | 定位 |
|----|------|------|
| **raw/** | `raw/` | 外部文章（抓取、剪藏、转载） |
| **notes/** | `notes/` | 个人笔记（洞察、点子、待办） |
| **wiki/** | `wiki/` | LLM 编译的概念页（知识图谱） |

关键文件：`index.md`（wiki 导航索引）、`AGENTS.md`（schema 定义）

**前置条件**: Obsidian 应用必须正在运行。CLI 命令统一前缀：
```bash
export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS" && obsidian <command>
```

**工具优先级**: 本地 vault 操作优先使用 Obsidian CLI（搜索、浏览、读取、待办），仅在 CLI 无法完成时降级到 Grep/Glob/Read。飞书操作和 AI 综合仍用原有方式。

**边界**:
- 所有内容创建/保存 → `article-gen` skill（包括外部 URL、记点子、写笔记）
- X/Twitter 链接轻量转 MD → `x2md` skill
- 本 skill 只做查询和管理，不创建新的 .md 文件（synthesize 和 insight 的写入是管理操作，不是内容创建）

## 操作模式

| 模式 | 触发词 | 操作 |
|------|--------|------|
| **search** | "搜一下"、"有什么关于..."、"找一下"、"知识库里..." | 搜索 vault（支持飞书） |
| **synthesize** | "总结一下XX主题"、"综合分析"、"对比一下" | 生成综合笔记 |
| **insight** | "更新洞察"、"我最近在想..."、"加到洞察里" | 追加到洞察文件 |
| **browse** | "知识库有什么"、"看看最近的笔记"、"列一下" | 列出 vault 内容 |
| **sync** | "同步飞书"、"看看飞书有什么新的"、"同步知识库" | 双向同步飞书知识库 |
| **todo** | "加个待办"、"看看待办"、"完成了XX"、"待办列表" | 管理待办事项 |

---

## 1. Search 模式

### 1.1 搜索范围（scope）

| scope | 说明 | 触发词 |
|-------|------|--------|
| `local`（默认） | 仅搜索本地 vault | "搜一下"、"找一下" |
| `feishu` | 仅搜索飞书知识库 | "飞书里有什么关于..." |
| `all` | 同时搜索本地 + 飞书 | "全部搜一下"、"两边都找找" |

### 1.2 本地搜索策略

**搜索三个层**（raw + notes + wiki），结果用 `[raw]`、`[notes]`、`[wiki]` 标注来源。

**查询策略**：先读 `index.md` 找相关 wiki 页，再读原文。Wiki 页提供概念概览和交叉引用，能快速定位相关的 raw/notes 文件。

**优先使用 Obsidian CLI**（利用 Obsidian 索引，比 Grep 更快更准）：

```bash
# 搜索整个 vault
obsidian search query="Agent"

# 带上下文的搜索（显示匹配行）
obsidian search:context query="Agent"

# 限定目录搜索（按层过滤）
obsidian search query="Agent" path="raw"
obsidian search query="Agent" path="notes"
obsidian search query="Agent" path="wiki"

# 按标签查找
obsidian tags                          # 列出所有标签
obsidian tag name="AI/发展" verbose    # 查看某标签下的文件

# 按属性查找
obsidian properties name="type"        # 查看某属性的所有值
obsidian property:read name="category" file="文件名"

# 查看文件内容
obsidian read file="文件名"
obsidian read path="raw/AI/某文章.md"
```

**降级到 Grep**（仅当 CLI 不可用或需要正则匹配时）：

```bash
Grep "关键词" path="~/Documents/obsidian/mixiaomi"
```

| 搜索方式 | Grep 模式 | 场景 |
|---------|-----------|------|
| 按分类 | `Grep "^category: AI/发展"` | frontmatter 精确匹配 |
| 按时间 | `Grep "^date: 2026-02"` | 按日期范围过滤 |
| 按类型 | `Grep "^type: idea"` | 按文档类型过滤 |

### 1.3 飞书搜索策略

当 scope 为 `feishu` 或 `all` 时：

1. 获取 `tenant_access_token`（参考 `feishu` skill）
2. 遍历飞书「具身行业资讯」4 个子节点（AI/技术/商业/思考），列出所有文档（飞书节点名仍为「具身行业资讯」）
3. 用 `docx_v1_document_rawContent` 读取文档内容，匹配关键词
4. 或尝试 `wiki_v1_node_search`（如可用）直接搜索

### 1.4 结果展示

对每个匹配文件，读取 frontmatter 并展示：

```
📄 标题 | 目录 | 分类 | 日期 | 来源
   摘要（frontmatter summary 或正文前 50 字）
```

来源标注：`[raw]` / `[notes]` / `[wiki]` / `[飞书]`

表格形式汇总：

| 标题 | 层 | 目录 | 分类 | 日期 | 来源 |
|------|-----|------|------|------|------|

---

## 2. Synthesize 模式

### 2.1 综合流程

1. 用户指定分类或主题（如 "AI/发展"）
2. 搜索匹配文章：`obsidian search query="AI/发展"` 或 `obsidian tag name="AI/发展" verbose`
3. **至少 2 篇**才执行综合，否则提示 "相关文章不足"
4. 读取匹配文章：`obsidian read file="文章名"` 或 `obsidian read path="路径"`
5. 生成综合笔记

### 2.2 综合笔记结构

```yaml
---
title: "XX综合洞察"
type: synthesis
date: YYYY-MM-DD
updated: YYYY-MM-DD
source_count: N
tags:
  - 对应分类标签
category: 对应分类
status: raw
---
```

正文结构：

```markdown
# [主题]综合洞察

## 核心趋势
- ...

## 观点对比
| 来源 | 观点 | 立场 |
|------|------|------|

## 时间线
- YYYY-MM-DD: ...

## 知识空白
- 尚未覆盖的角度...

## 来源文章
- [[文章1标题]]
- [[文章2标题]]
```

### 2.3 写入规则

- 路径: `~/Documents/obsidian/mixiaomi/洞察/综合/`
- 文件名: `<分类简称>综合.md`（如 `AI发展综合.md`）
- **已存在则 Edit 更新**，追加新内容，不覆盖已有
- 更新时同步更新 frontmatter 的 `updated` 和 `source_count`

---

## 3. Insight 模式

### 3.1 目标文件

`~/Documents/obsidian/mixiaomi/洞察/我的洞察.md`

### 3.2 文件结构

```markdown
---
title: "我的洞察"
type: insight
updated: YYYY-MM-DD
---

# 我的洞察

## 核心关注方向
<!-- 持续关注的主题和方向 -->

## 关键观点
<!-- 通过阅读和对话积累的核心认知 -->

## 待探索问题
<!-- 还没有答案、值得深入研究的问题 -->

## 阅读脉络
<!-- 记录阅读顺序和思考演进 -->
```

### 3.3 操作流程

1. 读取当前文件：`obsidian read path="洞察/我的洞察.md"`
2. 根据用户内容判断属于哪个区域：
   - 关注方向 → `## 核心关注方向`
   - 观点/认知 → `## 关键观点`
   - 问题 → `## 待探索问题`
   - 阅读记录 → `## 阅读脉络`
3. **Edit 追加**到对应区域（需要精确插入位置，CLI append 只能追加到文件末尾，所以此处仍用 Edit 工具）
4. 格式: `- [YYYY-MM-DD] 内容`
5. 更新 frontmatter 的 `updated` 日期

---

## 4. Browse 模式

### 4.1 浏览流程

**使用 Obsidian CLI**：

```bash
# 列出所有文件（按目录过滤）
obsidian files                           # 全部文件
obsidian files folder="行业资讯"          # 指定目录
obsidian files total                     # 文件总数

# 列出目录结构
obsidian folders

# 查看标签分布
obsidian tags counts sort=count          # 按使用次数排序

# 查看属性统计
obsidian properties sort=count counts    # 按使用次数排序

# 最近打开的文件
obsidian recents

# 查看单个文件信息
obsidian file file="文件名"

# 查看大纲
obsidian outline file="文件名"
```

按结果分组统计，表格展示。

### 4.2 展示格式

```
行业资讯 (N 篇)
| 标题 | 作者 | 分类 | 日期 |
|------|------|------|------|

日报 (N 篇)
| 标题 | 日期 |
|------|------|

创意点子 (N 篇)
| 标题 | 类型 | 日期 |
|------|------|------|

洞察 (N 篇)
| 标题 | 日期 |
|------|------|
```

---

## 5. Sync 模式（双向同步飞书知识库）

### 5.1 飞书知识库配置

- **space_id**: `7559794508562251778`
- **目标节点**: 具身行业资讯（飞书节点名未变，详见 `feishu` skill 的已知知识库结构）

### 5.2 同步方向

#### 本地→飞书（Push）

扫描本地 vault 中有 `feishu_node_token` 但内容已更新的文件：

1. `obsidian search query="feishu_node_token"` 或 `Grep "^feishu_node_token:"` 找到所有已同步文件（排除空值）
2. 对比 `feishu_sync_time` 与文件修改时间
3. 若本地更新 → 执行飞书重新发布：
   a. 用 `wiki_v2_space_getNode` 获取旧文档的 `obj_token`
   b. 用 `drive_v1_file_delete` 删除旧文档
   c. 预处理 Markdown（去 frontmatter、wikilink、Obsidian 图片）
   d. curl 上传导入 → 移入 wiki 同一父节点
   e. 如含 Mermaid → mmdc 转 PNG → 替换飞书代码块为图片
   详细步骤见 `feishu` skill 的「curl 文件上传导入」
4. 更新本地 `feishu_node_token`（新值）和 `feishu_sync_time`

#### 飞书→本地（Pull）

扫描飞书「具身行业资讯」下的新文档，拉取到本地：

1. 获取 `tenant_access_token`
2. 遍历飞书 4 个子节点（AI/技术/商业/思考），列出所有文档
3. 收集本地已有的 `feishu_node_token` 集合
4. 对比找出飞书上有但本地没有的新文档
5. 用 `docx_v1_document_rawContent` 读取新文档内容
6. 转换为 Markdown，根据来源节点确定本地目录和分类：
   - AI 节点 → `行业资讯/AI/`，tags: `AI/应用`
   - 技术节点 → `行业资讯/技术/`，tags: `技术/趋势`
   - 商业节点 → `行业资讯/商业/`，tags: `商业/创业`
   - 思考节点 → `行业资讯/思考/`，tags: `思考/创意`
7. 添加 frontmatter（含 `feishu_node_token` 和 `feishu_sync_time`）
8. 保存到本地 vault

### 5.3 同步状态追踪

通过本地 frontmatter 中的两个字段判断同步状态：

```yaml
feishu_node_token: "xxx"           # 飞书对应节点 token
feishu_sync_time: "2026-02-28T23:00:00"  # 最后同步时间
```

| 状态 | feishu_node_token | feishu_sync_time | 操作 |
|------|------------------|-----------------|------|
| 未同步 | 空 | 空 | 可选推送到飞书 |
| 已同步 | 有值 | 有值 | 检查是否需要更新 |
| 本地更新 | 有值 | 早于文件修改时间 | Push 到飞书 |
| 飞书新文档 | 本地不存在 | — | Pull 到本地 |

### 5.4 使用示例

```
用户: "同步飞书知识库"
→ 执行双向同步：先 Pull 飞书新文档，再 Push 本地更新
→ 报告同步结果：新增 N 篇、更新 N 篇

用户: "看看飞书有什么新的"
→ 仅执行 Pull 方向
→ 展示新文档列表

用户: "把本地更新推到飞书"
→ 仅执行 Push 方向
→ 展示更新的文档列表
```

---

## 6. Todo 模式

### 6.1 目录和文件结构

- 路径: `~/Documents/obsidian/mixiaomi/待办/`
- 看板: `待办看板.md`（聚合入口）
- 按项目分文件: `<项目名>待办.md`

### 6.2 操作

| 子操作 | 触发词 | 动作 |
|--------|--------|------|
| **add** | "加个待办"、"记个任务" | 添加 `- [ ]` 到对应文件 |
| **list** | "看看待办"、"待办列表" | 扫描所有 `- [ ]` 展示 |
| **done** | "完成了XX"、"搞定了" | 将 `- [ ]` 改为 `- [x]` |
| **new-project** | "新建XX项目待办" | 创建新的项目待办文件 |

### 6.3 添加待办流程

1. 判断是否属于已有项目：`obsidian files folder="待办"`
2. 若属于已有项目 → `obsidian append path="待办/<项目名>待办.md" content="- [ ] 任务内容"`
3. 若不属于任何项目 → `obsidian append path="待办/待办看板.md" content="- [ ] 任务内容"`
4. 若用户指定新项目 → `obsidian create path="待办/<项目名>待办.md" content="..."` + 更新看板链接

### 6.4 查看待办流程

**使用 Obsidian CLI**：

```bash
# 查看所有未完成待办
obsidian tasks todo

# 查看已完成待办
obsidian tasks done

# 按文件分组查看（含行号）
obsidian tasks todo verbose

# 限定待办目录
obsidian tasks todo path="待办"

# 统计总数
obsidian tasks total
obsidian tasks todo total
```

### 6.5 完成待办流程

```bash
# 按行号精确标记完成
obsidian task path="待办/XX待办.md" line=N done

# 或切换状态
obsidian task path="待办/XX待办.md" line=N toggle
```

流程：先 `obsidian tasks todo verbose` 找到匹配项及行号，再用 `task done` 标记完成。

### 6.6 新项目待办模板

```yaml
---
title: "<项目名>待办"
type: note
date: YYYY-MM-DD
tags:
  - 对应分类标签
category: 对应分类
status: raw
---
```

```markdown
# <项目名>待办

## 待办事项

- [ ] 第一个任务

## 我的笔记

```

创建后在 `待办看板.md` 的 `## 活跃项目` 下追加 `- [[<项目名>待办]]`

---

## 7. 输出回流

search 或 synthesize 完成后，主动询问用户："要回流到知识库吗？" 提供三个选项：

### 选项 A：追加到现有文章

在相关文章（raw/ 或 notes/）的 `## 我的笔记` 区域追加（如无此区域则创建）：

```markdown
> [YYYY-MM-DD] 通过 ob 搜索发现：<结论摘要>
```

使用 Edit 工具精确插入到 `## 我的笔记` 末尾。

### 选项 B：回流到 wiki 页

将结论更新到 `wiki/` 中对应的概念页：

1. 读 `index.md` 找到相关 wiki 页
2. Edit 更新 wiki 页内容（追加新发现、修正过时信息）
3. 在 `wiki/log.md` 追加变更记录：`- [YYYY-MM-DD] 更新 [[概念页名]]：<变更摘要>`

如相关 wiki 页不存在，提示用户是否创建新 wiki 页。

### 选项 C：生成新文章

调用 `article-gen` skill，使用 notes 或 essay 类型，将搜索/综合结果作为输入内容。

---

## 参考资料

详细 schema、示例和搜索模式见 `references/architecture.md`（按需加载）。

加载方式: `Read ~/.claude/skills/ob/references/architecture.md`
