---
name: cover-image
description: "Generate cover images for articles/notes. Self-contained 5D style system + gemini-image generation. Use when user says '配图', '封面图', 'generate cover', or when article-gen needs a cover image."
---

# Cover Image

为文章生成封面配图。自包含 5D 风格体系，调用 `gemini-image` 生成图片。

## 依赖

| 组件 | 角色 |
|------|------|
| `gemini-image` skill | 实际图片生成（Gemini Vertex AI） |

## 工作流

```
输入文章 → 内容分析 → 5D 风格决策 → 构建 prompt → 生成图片 → 嵌入文章
```

### Step 1: 内容分析

读取文章内容，提取：
- 核心主题和关键词
- 内容类型（新闻/观点/教程/分析/叙事）
- 情绪基调（积极/中性/严肃/激进）
- category（如有 frontmatter）

### Step 2: 5D 风格决策

根据内容分析结果，确定 5 个维度参数：

| 维度 | 控制什么 | 可选值 |
|------|---------|--------|
| **type** | 视觉构图 | hero / conceptual / typography / metaphor / scene / minimal |
| **palette** | 色彩方案 | warm / elegant / cool / dark / earth / vivid / pastel / mono / retro |
| **rendering** | 线条质感 | flat-vector / hand-drawn / painterly / digital / pixel / chalk |
| **text** | 文字密度 | none / title-only / title-subtitle / text-rich |
| **mood** | 情绪强度 | subtle / balanced / bold |

#### Type 选择

| Type | 适合 | 构图特征 |
|------|------|---------|
| `hero` | 重大新闻、产品发布 | 大视觉冲击，标题叠加 |
| `conceptual` | 技术文章、方法论 | 概念可视化，抽象核心想法 |
| `typography` | 观点、语录、洞察 | 文字为主体，突出标题 |
| `metaphor` | 哲学、成长、抽象主题 | 视觉隐喻，具象表达抽象 |
| `scene` | 故事、旅行、生活方式 | 场景氛围，叙事感 |
| `minimal` | 工具简讯、核心概念 | 极简构图，大量留白 |

#### Palette 选择

| Palette | 调性 | 主色 |
|---------|------|------|
| `warm` | 友好、亲切 | 橙色、金黄、赤陶 |
| `elegant` | 精致、优雅 | 柔珊瑚、灰蓝绿、灰玫瑰 |
| `cool` | 技术、专业 | 工程蓝、海军蓝、青色 |
| `dark` | 电影感、高端 | 电紫、青、品红 |
| `earth` | 自然、有机 | 森林绿、鼠尾草、泥土棕 |
| `vivid` | 活力、大胆 | 亮红、霓虹绿、电蓝 |
| `pastel` | 柔和、轻盈 | 柔粉、薄荷、薰衣草 |
| `mono` | 干净、聚焦 | 黑、近黑、白 |
| `retro` | 怀旧、复古 | 柔橙、灰粉、栗色 |

#### Rendering 选择

| Rendering | 特征 |
|-----------|------|
| `flat-vector` | 均匀轮廓、平面填充、几何图标 |
| `hand-drawn` | 不完美笔触、纸张纹理、涂鸦感 |
| `painterly` | 笔触痕迹、色彩晕染、柔和边缘 |
| `digital` | 精确边缘、微妙渐变、UI 组件感 |
| `pixel` | 像素网格、抖动、粗块形状 |
| `chalk` | 粉笔笔触、粉尘效果、黑板纹理 |

#### 自动选择规则（category → 风格）

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

默认 text: `title-only`，默认 mood: `balanced`。

### Step 3: 构建 Prompt

基于 5D 参数和文章内容构建 prompt：

1. **主题描述**：从文章核心观点提炼视觉意象（概念化，非字面翻译）
2. **构图指令**：根据 type 确定布局
3. **色彩指令**：根据 palette 指定色调方向
4. **渲染指令**：根据 rendering 指定线条/纹理风格
5. **文字指令**：根据 text 级别决定是否含标题（≤8 字）
6. **情绪指令**：根据 mood 调整对比度/饱和度/视觉重量

### Step 4: 生成图片

调用 `gemini-image` skill：

```bash
python3 "$HOME/.claude/skills/gemini-image/scripts/gemini_image.py" generate "<prompt>" -o <output_path>
```

- 默认宽高比 16:9
- 失败自动重试一次（简化 prompt）

### Step 5: 嵌入文章

1. 保存图片到文章同目录，文件名与文章同名（`.png`）
2. 在 Markdown 正文顶部（标题下方）插入 `![[<图片文件名>]]`
3. 在 frontmatter 中添加 `cover: "<图片文件名>"`

## 调用模式

| 模式 | 触发方式 | 行为 |
|------|---------|------|
| **quick** | 被 `article-gen` 等 skill 调用 | 跳过确认，直接用自动选择结果 |
| **interactive** | 用户直接说"配图" | 展示推荐参数，用户可调整后确认 |

调用时传入：
```
- 文章路径: <.md 文件绝对路径>
- category: <从 frontmatter 读取>（可选，辅助自动选择）
- 模式: quick / interactive
```

## 注意事项

- 封面图要在小尺寸预览下仍可辨识
- 视觉隐喻优于字面表达（文章说"链锯切西瓜"，不要画链锯和西瓜）
- 标题文字最多 8 个字，简洁有力
- 飞书发布时 `![[]]` 会被预处理去掉，封面图仅用于 Obsidian 本地展示
