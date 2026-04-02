# 知识库架构参考

详细 schema、示例和搜索模式。按需加载，不占用 SKILL.md 空间。

---

## 1. Vault 完整目录结构

```
~/Documents/obsidian/mixiaomi/
├── 创意点子/              # 产品想法、项目企划（kb skill 管理）
│   └── *.md
├── 知识库/                # 技术笔记、学习总结（kb skill 管理）
│   ├── 我的洞察.md        # 个人洞察汇总（insight 模式专用）
│   ├── 综合/              # 综合笔记（synthesize 模式生成）
│   │   └── *.md
│   └── *.md
├── Vibe Coding/           # 编程心得、开发经验（kb skill 管理）
│   └── *.md
├── X收藏/                 # X/Twitter 内容剪藏（x2md skill 管理写入，kb 可读取）
│   └── *.md
└── .obsidian/             # Obsidian 配置（不操作）
```

---

## 2. 五种 Frontmatter Schema

### 2.1 idea（创意点子）

```yaml
---
title: "AI读书助手"
type: idea
date: 2026-02-16
tags:
  - AI/应用
  - 商业/产品
category: AI/应用
status: raw
---
```

### 2.2 note（技术笔记 / 编程心得）

```yaml
---
title: "MCP 协议工作原理"
type: note
date: 2026-02-16
tags:
  - 技术/趋势
category: 技术/趋势
status: raw
---
```

### 2.3 article（长篇技术文章，知识库中）

```yaml
---
title: "Agent 架构设计深度分析"
type: article
date: 2026-02-16
tags:
  - AI/应用
  - 技术/开发
category: AI/应用
status: raw
---
```

### 2.4 synthesis（综合笔记）

```yaml
---
title: "AI发展综合洞察"
type: synthesis
date: 2026-02-16
updated: 2026-02-16
source_count: 5
tags:
  - AI/发展
category: AI/发展
status: raw
---
```

### 2.5 insight（个人洞察）

```yaml
---
title: "我的洞察"
type: insight
updated: 2026-02-16
---
```

---

## 3. Type 系统对照表

| type | 可用目录 | 谁管理写入 | 谁可读取 |
|------|---------|-----------|---------|
| `idea` | `创意点子/` | kb skill | kb skill |
| `note` | `知识库/`、`Vibe Coding/` | kb skill | kb skill |
| `article` (kb) | `知识库/` | kb skill | kb skill |
| `article` (x) | `X收藏/` | x2md skill | kb skill (只读) |
| `thread` | `X收藏/` | x2md skill | kb skill (只读) |
| `tweet` | `X收藏/` | x2md skill | kb skill (只读) |
| `synthesis` | `知识库/综合/` | kb skill | kb skill |
| `insight` | `知识库/我的洞察.md` | kb skill | kb skill |

---

## 4. 三层架构图

```
┌─────────────────────────────────────────────────────────┐
│                    记忆链（Memory Chain）                 │
│  新会话 → 读洞察 → 读综合 → 恢复上下文 → 持续积累       │
└─────────────────────────────────────────────────────────┘
                          ↑ 读取
┌─────────────────────────────────────────────────────────┐
│                   操作层（kb skill）                      │
│  write | search | synthesize | insight | browse          │
│  管理: 创意点子/ + 知识库/ + Vibe Coding/                │
│  可读: X收藏/ (只读)                                     │
└─────────────────────────────────────────────────────────┘
                          ↑ 读取
┌─────────────────────────────────────────────────────────┐
│                   采集层（x2md skill）                    │
│  X/Twitter URL → 解析 → Markdown → X收藏/               │
│  自动 frontmatter + AI 分类 + enrichment                 │
└─────────────────────────────────────────────────────────┘
```

**数据流**:
```
外部内容 ──x2md──→ X收藏/ ──kb search/synthesize──→ 综合笔记
用户想法 ──kb write──→ 创意点子/ / 知识库/ / Vibe Coding/
阅读感悟 ──kb insight──→ 我的洞察.md
多篇文章 ──kb synthesize──→ 知识库/综合/
```

---

## 5. 综合笔记完整示例

文件: `~/Documents/obsidian/mixiaomi/知识库/综合/AI发展综合.md`

```markdown
---
title: "AI发展综合洞察"
type: synthesis
date: 2026-02-14
updated: 2026-02-16
source_count: 3
tags:
  - AI/发展
category: AI/发展
status: raw
---

# AI发展综合洞察

## 核心趋势
- 2026年2月出现AI能力质变，多个前沿模型同期发布
- Agent 正在改变软件行业的用户界面范式
- AI 工具链从辅助编程走向自主开发

## 观点对比
| 来源 | 观点 | 立场 |
|------|------|------|
| Matt Shumer | AI已达到不需人类完成技术工作的水平 | 激进乐观 |
| 宝玉 | 软件正在为AI Agent重做接口 | 技术演进 |

## 时间线
- 2026-02-10: Matt Shumer 发文"Something Big Is Happening"
- 2026-02-11: 宝玉分析Agent接口重做趋势

## 知识空白
- 国内AI发展进度的对比数据
- Agent 对非技术领域的影响评估

## 来源文章
- [[Matt Shumer - Something Big Is Happening]]
- [[宝玉 - 软件正在为AI Agent重做接口]]
```

---

## 6. 文件名命名规则

| 目录 | 命名模式 | 示例 |
|------|---------|------|
| `创意点子/` | `<主题>.md` | `AI读书助手.md`、`食格测试企划.md` |
| `知识库/` | `<主题>.md` | `MCP协议工作原理.md` |
| `知识库/综合/` | `<分类简称>综合.md` | `AI发展综合.md`、`技术趋势综合.md` |
| `Vibe Coding/` | `<主题>.md` | `Vibe coding心得.md` |
| `X收藏/` | `<作者> - <标题>.md` | `宝玉 - 软件正在为AI Agent重做接口.md` |

**通用规则**:
- 用中文命名（除非内容本身是英文主题）
- 简洁概括内容，避免过长文件名
- 不含特殊字符: `< > : " / \ | ? *`

---

## 7. Grep 搜索模式速查

### 按 tag 搜索
```
Grep "^  - AI/发展" --glob "*.md" --path ~/Documents/obsidian/mixiaomi
```

### 按 category 搜索
```
Grep "^category: AI/发展" --glob "*.md" --path ~/Documents/obsidian/mixiaomi
```

### 按 date 搜索
```
Grep "^date: 2026-02" --glob "*.md" --path ~/Documents/obsidian/mixiaomi
```

### 按 type 搜索
```
Grep "^type: idea" --glob "*.md" --path ~/Documents/obsidian/mixiaomi
```

### 全文关键词搜索
```
Grep "Agent" --glob "*.md" --path ~/Documents/obsidian/mixiaomi
```

### 按 status 搜索
```
Grep "^status: enriched" --glob "*.md" --path ~/Documents/obsidian/mixiaomi
```

### 按作者搜索（X收藏）
```
Grep "^author: \"宝玉\"" --glob "*.md" --path ~/Documents/obsidian/mixiaomi/X收藏
```

---

## 8. 记忆链协议

### 新会话恢复上下文

当需要恢复用户的知识上下文时，按以下顺序读取：

1. **读洞察**: `Read ~/Documents/obsidian/mixiaomi/知识库/我的洞察.md`
   - 获取用户的核心关注方向、关键观点、待探索问题

2. **读综合**: `Glob "*.md" ~/Documents/obsidian/mixiaomi/知识库/综合/`
   - 获取已有的综合笔记列表
   - 读取最近更新的 1-2 篇综合笔记

3. **读最近笔记**: `Glob "*.md" ~/Documents/obsidian/mixiaomi/知识库/`
   - 按修改时间排序，读取最近的 3-5 篇

### 持续积累

每次有价值的对话后，建议用户：
- 重要观点 → `insight` 模式追加到洞察
- 新话题积累足够 → `synthesize` 模式生成综合
- 新想法 → `write` 模式记录

---

## 9. 分类体系完整说明

9 个层级标签，与 x2md skill 共享同一套体系：

| 标签 | 含义 | 典型内容 |
|------|------|---------|
| `AI/发展` | 模型发布、能力进展、AGI | GPT-5 发布、Opus 4.6 能力 |
| `AI/应用` | 工具、工作流、Agent | Claude Code、MCP、AI 编程 |
| `AI/影响` | 就业、社会、伦理 | 白领替代、版权争议 |
| `技术/趋势` | MCP、CLI-first、平台趋势 | 新协议、新范式 |
| `技术/开发` | 编程技巧、架构、Vibe Coding | 代码架构、开发经验 |
| `商业/创业` | 创业、融资、商业 | 创业机会、商业模式 |
| `商业/产品` | 产品思维、UX | 产品设计、用户体验 |
| `思考/创意` | 灵感、创新方法 | 创新方法论、灵感记录 |
| `思考/社会` | 监管、哲学、未来 | AI 监管、未来展望 |

**选择规则**:
- 每篇文章选 1-3 个标签
- `category` 字段选最主要的 1 个标签
- 优先选择更具体的标签（`AI/应用` 优于 `AI/发展`）
