---
name: cover-image
description: "Generate cover images for articles/notes. Orchestrates style selection (baoyu-cover-image 5D system) and image generation (gemini-image). Use when user says '配图', '封面图', 'generate cover', or when x2md/kb/x-feed needs a cover image for saved content."
---

# Cover Image

为文章/笔记生成封面配图。编排风格选择和图片生成两个环节，被 x2md、kb、x-feed 等 skill 调用。

## 依赖 Skill

| Skill | 角色 | 提供什么 |
|-------|------|---------|
| `baoyu-cover-image` | 风格决策 | 5D 参数体系（type/palette/rendering/text/mood）+ 自动选择规则 |
| `gemini-image` | 图片生成 | Gemini Vertex AI 实际生成图片 |

## 触发方式

| 来源 | 场景 |
|------|------|
| 用户直接说 | "给这篇文章配图"、"生成封面"、"封面图" |
| `x2md` skill 调用 | 推文保存后的 enrichment 阶段（step 3g） |
| `x-feed` skill 调用 | 日报生成后（可选） |
| `kb` skill 调用 | 知识库文章需要配图时 |

## 工作流

```
输入文章 → 内容分析 → 5D 风格决策 → 构建 prompt → 生成图片 → 嵌入文章
```

### Step 1: 内容分析

读取文章内容，提取：
- 核心主题和关键词
- 内容类型（新闻/观点/教程/分析/叙事）
- 情绪基调（积极/中性/严肃/激进）
- category 标签（如有 frontmatter）

### Step 2: 5D 风格决策

调用 `baoyu-cover-image` skill 的自动选择规则，根据 Step 1 的分析结果确定 5 个维度：

| 维度 | 决策依据 | 可选值 |
|------|---------|--------|
| **type** | 内容类型 | hero / conceptual / typography / metaphor / scene / minimal |
| **palette** | 情绪基调 + category | warm / elegant / cool / dark / earth / vivid / pastel / mono / retro |
| **rendering** | 内容正式度 | flat-vector / hand-drawn / painterly / digital / pixel / chalk |
| **text** | 是否需要标题文字 | none / title-only / title-subtitle / text-rich |
| **mood** | 情绪强度 | subtle / balanced / bold |

**category → 风格映射参考**：

| category | 推荐 type | 推荐 palette | 推荐 rendering |
|----------|-----------|-------------|---------------|
| AI/发展 | hero / conceptual | cool / dark | digital / flat-vector |
| AI/应用 | conceptual / minimal | cool / mono | flat-vector / digital |
| AI/影响 | metaphor / typography | dark / earth | painterly / hand-drawn |
| 技术/趋势 | conceptual | cool / mono | digital / flat-vector |
| 技术/开发 | minimal / conceptual | mono / cool | flat-vector / digital |
| 商业/创业 | hero / scene | warm / vivid | digital / flat-vector |
| 商业/产品 | minimal / conceptual | elegant / pastel | flat-vector / digital |
| 思考/创意 | metaphor / typography | warm / elegant | hand-drawn / painterly |
| 思考/社会 | typography / metaphor | earth / mono | painterly / chalk |

**快速模式**（被其他 skill 调用时默认）：跳过确认，直接用自动选择结果。

**交互模式**（用户直接触发时）：展示推荐参数，用户可调整后确认。

### Step 3: 构建 Prompt

基于 5D 参数和文章内容构建图片生成 prompt：

1. **主题描述**：从文章核心观点提炼视觉意象（概念化，非字面翻译）
2. **构图指令**：根据 type 确定布局（hero 大视觉冲击、minimal 大留白等）
3. **色彩指令**：从 palette 拉取具体色值（参考 `baoyu-cover-image/references/palettes/`）
4. **渲染指令**：根据 rendering 指定线条/纹理风格
5. **文字指令**：根据 text 级别决定是否含标题文字
6. **情绪指令**：根据 mood 调整对比度/饱和度/视觉重量

### Step 4: 生成图片

调用 `gemini-image` skill 的 generate 模式：

```bash
python3 "$HOME/.claude/skills/gemini-image/scripts/gemini_image.py" generate "<prompt>" -o <output_path>
```

- 默认宽高比 16:9
- 失败自动重试一次（简化 prompt）

### Step 5: 嵌入文章

将生成的图片关联到文章：

1. 保存图片到文章同目录，文件名与文章同名（`.png`）
2. 在 Markdown 正文顶部（标题下方）插入 `![[<图片文件名>]]`
3. 在 frontmatter 中添加 `cover: "<图片文件名>"`

## 被调用接口

其他 skill 调用 cover-image 时，传入以下上下文：

```
调用 cover-image skill:
- 文章路径: <.md 文件绝对路径>
- category: <从 frontmatter 读取>
- 模式: quick（跳过确认）
```

cover-image 完成后返回：
- 图片路径
- 使用的 5D 参数
- 是否成功嵌入文章

## 注意事项

- 封面图要在小尺寸预览下仍可辨识
- 视觉隐喻优于字面表达（文章说"链锯切西瓜"，不要画链锯和西瓜）
- 标题文字最多 8 个字，简洁有力
- 飞书发布时会去掉 `![[]]` 引用（飞书不支持本地图片），封面图仅用于 Obsidian 本地展示
