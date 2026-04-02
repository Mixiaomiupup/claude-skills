# Claude Code Skills

> 18 个自研 skill | 1 个第三方 | 6 大类

个人 Claude Code skill 合集，通过 `cc-sync` 同步至 GitHub 和云效。完整能力展示见[能力全景指南](https://huazhi-ai.feishu.cn/docx/ENUFdpeoxopStLxcU5pceHhnnUe)。

## 总览

| Skill | 分类 | 触发词 | 一句话 |
|-------|------|--------|--------|
| [article-gen](article-gen/SKILL.md) | 内容与知识 | X 链接 + "保存/分享" | 文章生成总编排（转换→enrichment→配图→发布） |
| [x2md](x2md/SKILL.md) | 内容与知识 | X 链接 + "转换" | X/Twitter → Markdown 纯转换 |
| [ucal](ucal/SKILL.md) | 内容与知识 | 给链接、"调研XX" | 跨平台内容深度分析与话题调研 |
| [kb](kb/SKILL.md) | 内容与知识 | "记下来"、"搜知识库" | Obsidian 知识库管理 |
| [x-feed](x-feed/SKILL.md) | 内容与知识 | "twitter digest" | X/Twitter 信息流（发现账号、热点、日报） |
| [feishu](feishu/SKILL.md) | 内容与知识 | 飞书操作 | 飞书知识库/文档/群聊/多维表格集成 |
| [cover-image](cover-image/SKILL.md) | 图像与媒体 | "配图"、"封面图" | 文章封面配图（5D 风格 + 生图） |
| [gemini-image](gemini-image/SKILL.md) | 图像与媒体 | "画一张"、"这图是什么" | Gemini AI 图片生成/编辑/理解 |
| [review](review/SKILL.md) | 代码质量 | "review"、"审查" | 六维度代码审查 |
| [python-style](python-style/SKILL.md) | 代码质量 | "check style" | PEP 8 风格检查 |
| [refactor](refactor/SKILL.md) | 代码质量 | "重构" | 重构建议 |
| [debug](debug/SKILL.md) | 代码质量 | bug、报错 | 系统性调试 |
| [test](test/SKILL.md) | 代码质量 | "写测试" | 测试生成 |
| [commit](commit/SKILL.md) | 开发流程 | "提交" | Google convention commit |
| [remote-repos](remote-repos/SKILL.md) | 开发流程 | push/pull、PR | GitHub + 云效操作 |
| [explain](explain/SKILL.md) | 开发流程 | "explain this" | 代码图解 |
| [server](server/SKILL.md) | 基础设施 | SSH、部署 | 阿里云服务器管理 |
| [sync-config](sync-config/SKILL.md) | 基础设施 | "sync"、"备份配置" | 配置与 skill 双平台同步 |
| [doc-control](doc-control/SKILL.md) | 文档 | 创建/更新文档前 | 文档生成控制 |
| [youpin](youpin/SKILL.md) | 工具 | "悠悠有品"、"收益" | CS2 饰品交易查询 |

---

## 内容与知识

### [article-gen](article-gen/SKILL.md) — 文章生成总编排

**最常用的入口 skill。** 用户给 X 链接说"保存"或"分享到飞书"时，就是它在统筹一切。

自己不做具体操作，而是按需调用各专职 skill：

```
article-gen
  ├── x2md ——— X → Markdown（纯转换）
  ├── Claude ——— enrichment（分类/标签/摘要）+ 翻译
  ├── cover-image ——— 封面配图（5D 风格 + 生图）
  └── feishu ——— 飞书发布 + 全员广播
```

完整流程：转换 → enrichment → 翻译（非中文时）→ 配图 → 飞书发布 → 推送。每步可选跳过。

**常用说法**：`保存这条推文`、`分享到飞书`、给 X 链接

---

### [x2md](x2md/SKILL.md) — X/Twitter → Markdown

**纯转换工具**，把推文/线程/长文转成 Markdown 文件存进 Obsidian，`status: raw`。不做 enrichment、翻译、配图、发布。这些都是 `article-gen` 的事。

支持三种内容：X Article（长文）、Regular tweet、Thread。

**常用说法**：直接给 X 链接（由 article-gen 调用，通常不需要单独触发）

---

### [ucal](ucal/SKILL.md) — 跨平台内容分析与话题调研

核心思路：ucal MCP 解决"怎么取数据"，skill 解决"取到后怎么分析"。

**两个模式**：

- **Read 模式** — 给链接，按平台差异化分析（小红书重评论观点图谱、知乎重论证结构、X 重观点提炼）
- **Research 模式** — "调研XX"触发，完整调研流程（问题锐化→选帖策略→Pre-read hypothesis→证据追踪→叙事报告）

**常用说法**：`帮我看看这个链接`、`调研XX话题`

---

### [x-feed](x-feed/SKILL.md) — X/Twitter 信息流

四种模式：discover（发现账号）、digest（热点日报）、deep-save（委托 article-gen）、report（周/月总结）。

**常用说法**：`twitter digest`、`discover people to follow`

---

### [kb](kb/SKILL.md) — Obsidian 知识库管理

六种模式：write / search / synthesize / insight / browse / sync。

与 x2md 有明确边界：X 链接一律拒绝，提示走 article-gen。

**常用说法**：`记个点子`、`搜一下知识库`、`同步飞书`

---

### [feishu](feishu/SKILL.md) — 飞书集成

飞书平台的全面集成，覆盖知识库、文档、群聊、多维表格。被 article-gen、kb、x-feed 调用来完成飞书端操作。

**常用场景**：`发布文档到飞书`、`看看飞书知识库`

---

## 图像与媒体

### [cover-image](cover-image/SKILL.md) — 文章封面配图

**自包含**的配图 skill。内化 5D 风格体系（type/palette/rendering/text/mood），自己做风格决策，调用 `gemini-image` 生成图片。

被 `article-gen` 在 enrichment 后调用，也可由用户直接触发。

**常用说法**：`给这篇文章配图`、`封面图`

---

### [gemini-image](gemini-image/SKILL.md) — Gemini AI 图片工具

通过 Vertex AI 调用 Gemini 模型。三种模式：generate（文字→图片）、edit（修改图片）、understand（分析图片）。

被 `cover-image` 调用来执行实际生成，也可由用户直接触发做自由生图。

**常用说法**：`画一张日落`、`这张图里是什么`

---

## 代码质量

| Skill | 做什么 | 说一句 |
|-------|--------|--------|
| [review](review/SKILL.md) | 安全/正确性/性能/可读性/可维护/最佳实践，六个维度扫一遍 | `review 一下` |
| [python-style](python-style/SKILL.md) | ruff/black/isort/mypy 检查 PEP 8，自动修复 | `check style` |
| [refactor](refactor/SKILL.md) | 找 code smell，检查 SOLID，给出 before/after 对比 | `重构这段` |
| [debug](debug/SKILL.md) | 理解→复现→假设→隔离→验证，系统性调试 | `帮我 debug` |
| [test](test/SKILL.md) | Arrange-Act-Assert 模式，支持 Python/JS/TS/Go | `写测试` |

---

## 开发流程

| Skill | 做什么 | 说一句 |
|-------|--------|--------|
| [commit](commit/SKILL.md) | 按 Google convention 生成 commit message | `提交` |
| [remote-repos](remote-repos/SKILL.md) | 双平台操作 — GitHub gh CLI + 云效 MCP | `create PR` |
| [explain](explain/SKILL.md) | 全局概览 + ASCII 图 + 类比 + 逐步分解 | `explain this` |

---

## 基础设施

### [sync-config](sync-config/SKILL.md) — 配置同步系统 (cc-sync)

配置和 skill 拆成两个 Git 仓库，推到 GitHub + 云效双平台。自带脱敏系统、staging 隔离、dry-run 预览。

```bash
cc-sync push --dry-run    # 预览
cc-sync push --yes        # 推送
cc-sync pull              # 拉取恢复
```

---

### [server](server/SKILL.md) — 阿里云服务器

阿里云 Ubuntu 服务器管理，SSH 连接、部署、nginx、服务管理。

---

## 文档

### [doc-control](doc-control/SKILL.md) — 文档生成控制

防止过度文档化的门控。Level 1-3 分级，检查文档模式，决定创建/更新/跳过。

---

## 工具

### [youpin](youpin/SKILL.md) — CS2 饰品交易查询

悠悠有品平台只读查询：订单、库存、收益统计、市场行情。严禁买卖操作。

---

## Skill 联动

Skills 之间通过「调用」和「委托」形成协作链。每个 skill 只做一件事，通过 `article-gen` 等编排 skill 组合完成复杂流程。

### 联动关系图

```
用户给 X 链接
    │
    ▼
  article-gen (总编排)
    │
    ├── 1. x2md ───── X → Markdown（纯转换，status: raw）
    │
    ├── 2. Claude ──── enrichment（分类/标签/摘要）+ 翻译
    │
    ├── 3. cover-image ── 风格决策(5D) + gemini-image(生图) → 嵌入文章
    │
    └── 4. feishu ───── 发布知识库 + 广播卡片私信
```

### 调用关系表

| 调用方 | 被调用方 | 场景 |
|--------|---------|------|
| `article-gen` | `x2md` | X 链接转 Markdown |
| `article-gen` | `cover-image` | enrichment 后生成封面 |
| `article-gen` | `feishu` | 发布 + 广播 |
| `cover-image` | `gemini-image` | 实际图片生成 |
| `x-feed` | `article-gen` | deep-save 模式 |
| `x-feed` | `feishu` | digest 发布 + 广播 |
| `kb` | `feishu` | sync 模式（push/pull） |

### 边界规则

| 规则 | 说明 |
|------|------|
| 完整文章流程 → `article-gen` | 不要直接调 x2md + enrichment + 发布，用 article-gen 统筹 |
| 纯转换 → `x2md` | x2md 只管 X → Markdown，不做 enrichment |
| 配图 → `cover-image` | 自包含 5D 风格体系，不再转发 baoyu-cover-image |
| 生图 → `gemini-image` | cover-image 调它，用户也可直接调 |
| 飞书操作 → `feishu` | 其他 skill 不直接调飞书 API |
| 飞书操作 → lark-cli | 所有飞书 API 统一用 `lark-cli api` 调用，不再依赖 MCP server |

---

## 第三方

| Skill | 来源 | 备注 |
|-------|------|------|
| baoyu-skills | [baoyu/claude-code-skills](https://github.com/baoyu/claude-code-skills) | 独立 Git 仓库，在 `component-manifest.json` 中追踪 |

## 同步

```bash
cc-sync push --target skills --dry-run   # 预览 skill 变更
cc-sync push --target skills --yes       # 推送
cc-sync status                           # 查看状态
```
