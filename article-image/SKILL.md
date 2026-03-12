---
name: article-image
description: "Generate cover images and article illustrations with unified 5D style system + Mermaid smart routing. Use when user says '封面图', '配图', '文章配图', '插图', 'cover image', 'illustrate article', or when article-gen needs images."
---

# Article Image

为文章生成封面图和内配图。统一 5D 风格体系，15 种风格预设，智能分流 Mermaid / AI 生成。

## 依赖

| 组件 | 角色 |
|------|------|
| `gemini-image` skill | 图片生成引擎（generate 模式） |

## 模式

| 模式 | 触发 | 输出 |
|------|------|------|
| **cover** | "封面图"、"配图"（单张）、"cover" | 1 张封面，嵌入 frontmatter + 正文顶部 |
| **illustrate** | "给文章配图"、"插图"、"illustrate" | 2-5 张 AI 图 + 0-N 个 Mermaid 代码块 |

---

## 5D 维度体系

两个模式共享同一套维度，style 预设是 palette + rendering 的快捷方式。

| 维度 | 控制 | 可选值 |
|------|------|--------|
| **type** | 构图/布局 | cover: hero / conceptual / typography / metaphor / scene / minimal |
| | | illustrate: infographic / scene / flowchart / comparison / framework / timeline |
| **palette** | 色彩方案 | warm / elegant / cool / dark / earth / vivid / pastel / mono / retro |
| **rendering** | 线条质感 | flat-vector / hand-drawn / painterly / digital / pixel / chalk |
| **text** | 文字密度 | none / title-only / title-subtitle / text-rich |
| **mood** | 情绪强度 | subtle / balanced / bold |

### Style 预设

`--style <name>` 展开为 palette + rendering，其余维度独立选。详见 [references/style-presets.md](references/style-presets.md)。

15 种可用预设：notion, blueprint, warm, elegant, minimal, watercolor, editorial, scientific, sketch-notes, chalkboard, pixel-art, retro, flat-doodle, fantasy-animation, vintage

可叠加覆盖：`--style elegant --rendering digital` -> palette=elegant, rendering=digital

默认 text: `title-only`，默认 mood: `balanced`。

---

## Mode: cover

生成文章封面图。

### Workflow

```
读取文章 -> 内容分析 -> 5D 维度决策 -> 构建 prompt -> 生成图片 -> 嵌入文章
```

#### Step 1: 内容分析

读取文章内容，提取：
- 核心主题和关键词
- 内容类型（新闻/观点/教程/分析/叙事）
- 情绪基调（积极/中性/严肃/激进）
- category（如有 frontmatter）

#### Step 2: 5D 维度决策

根据内容分析结果，确定 5 个维度参数。自动选择规则见 [references/auto-selection.md](references/auto-selection.md)。

也可用 style 预设快速选择，如 `--style blueprint` 自动设定 palette=cool, rendering=digital。

#### Step 3: 构建 Prompt

基于 5D 参数和文章内容构建 prompt。模板见 [references/prompt-templates.md](references/prompt-templates.md)。

1. **主题描述**：从文章核心观点提炼视觉意象（概念化，非字面翻译）
2. **构图指令**：根据 type 确定布局
3. **色彩指令**：根据 palette 指定色调方向（含 hex 色值，从 [references/styles/](references/styles/) 获取）
4. **渲染指令**：根据 rendering 指定线条/纹理风格
5. **文字指令**：根据 text 级别决定是否含标题（max 8 字）
6. **情绪指令**：根据 mood 调整对比度/饱和度/视觉重量

#### Step 4: 生成图片

调用 `gemini-image` skill：

```bash
python3 "$HOME/.claude/skills/gemini-image/scripts/gemini_image.py" generate "<prompt>" -o <output_path>
```

- 默认宽高比 16:9
- 失败自动重试一次（简化 prompt）

#### Step 5: 嵌入文章

1. 保存图片到 vault 的 `attachments/` 目录（`~/Documents/obsidian/mixiaomi/attachments/`），文件名与文章同名（`.png`）
2. 在 Markdown 正文顶部（标题下方）插入 `![[<图片文件名>]]`（Obsidian 自动从 attachments/ 解析）
3. 在 frontmatter 中添加 `cover: "<图片文件名>"`（仅文件名，不含路径）

### 调用模式

| 模式 | 触发方式 | 行为 |
|------|---------|------|
| **quick** | 被 `article-gen` 等 skill 调用 | 跳过确认，直接用自动选择结果 |
| **interactive** | 用户直接说"封面图" | 展示推荐参数，用户可调整后确认 |

---

## Mode: illustrate

分析文章，识别配图位置，智能选择 Mermaid 或 AI 生成，插入图片/代码块。

### Workflow

```
读取文章 -> 分析内容 -> 识别配图位置 -> 分流判断 -> 生成 -> 插入文章
```

#### Step 1: 分析内容

读取文章，识别：
- 内容类型（technical / tutorial / methodology / narrative）
- 2-5 个核心论点或概念
- 适合配图的位置（段落间隙）

**适合配图的**：核心论点、抽象概念、数据对比、流程步骤。
**不适合配图的**：字面隐喻、纯装饰、通用插画。

#### Step 2: 分流判断（Mermaid vs AI）

对每个配图位置，判断渲染方式：

| 内容特征 | 方式 | 原因 |
|---------|------|------|
| 流程/步骤/生命周期 | **Mermaid** flowchart | 文字精准，箭头关系清晰 |
| 架构/组件关系 | **Mermaid** flowchart + subgraph | 层级和连接必须准确 |
| 时序/交互过程 | **Mermaid** sequence | 调用顺序不能模糊 |
| 状态变化 | **Mermaid** stateDiagram | 状态名和转换条件是关键信息 |
| 概念解释/视觉隐喻 | **AI 生成** | 需要创意表达，文字不重要 |
| 数据对比/信息图 | **AI 生成** | 视觉排版比精确文字更重要 |
| 氛围/节奏装饰 | **AI 生成** | 纯美感 |

**判断标准**：图里的文字是核心信息 -> Mermaid，文字是点缀 -> AI 生成。

详见 [references/auto-selection.md](references/auto-selection.md)。

#### Step 3: 选择维度

对 AI 生成的配图，选择 5D 维度。

- 可用 style 预设快速选择：`--style blueprint`
- 也可逐维度指定
- 一篇文章内所有 AI 配图建议使用同一 style，保持视觉一致性

自动选择规则见 [references/auto-selection.md](references/auto-selection.md)。
类型兼容性矩阵见 auto-selection.md 中的 Type x Style Compatibility 表。

#### Step 4: 生成

**AI 生成**：
1. 按 [references/prompt-templates.md](references/prompt-templates.md) 中对应 type 的模板构建 prompt
2. 从 [references/styles/](references/styles/) 获取 hex 色值和视觉元素
3. 调用 `python3 "$HOME/.claude/skills/gemini-image/scripts/gemini_image.py" generate "<prompt>" -o <output_path>`
4. 输出命名：`NN-{type}-{slug}.png`（如 `01-infographic-ai-architecture.png`）

**Mermaid 生成**：
1. 根据内容编写 Mermaid 代码块
2. 中文标签用双引号包裹（`"中文标签"`）
3. 选择合适的图表方向（TD/LR）
4. 直接以 ` ```mermaid ` 代码块插入文章

#### Step 5: 插入文章

- AI 生成的图片：保存到 `~/Documents/obsidian/mixiaomi/attachments/`，在目标位置插入 `![[图片文件名]]`
- Mermaid 代码块：直接插入 markdown

---

## 注意事项

- 封面图要在小尺寸预览下仍可辨识
- 视觉隐喻优于字面表达（文章说"链锯切西瓜"，不要画链锯和西瓜）
- 标题文字最多 8 个字，简洁有力
- 飞书发布时 `![[]]` 会被预处理去掉，封面图仅用于 Obsidian 本地展示
- Mermaid 代码块在 Obsidian 中原生渲染，飞书发布前需用 mmdc 转为 PNG

## References

| File | Content |
|------|---------|
| [references/style-presets.md](references/style-presets.md) | 15 种风格预设（name -> palette + rendering 映射） |
| [references/auto-selection.md](references/auto-selection.md) | 内容信号 -> 维度自动映射 + Mermaid 分流规则 |
| [references/prompt-templates.md](references/prompt-templates.md) | 各 type 的 prompt 模板 + 封面模板 |
| [references/styles/](references/styles/) | 15 种风格的详细定义（色值、视觉元素、规则） |
