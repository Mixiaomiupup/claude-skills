# article-image skill 设计文档

- **日期**: 2026-03-10
- **状态**: approved
- **目标**: 合并封面/配图工作流为统一 skill，融合 baoyu 风格库，集成 Mermaid 智能分流

## 背景

当前存在三个问题：
1. `gemini-image` 同时包含引擎和工作流，职责混杂
2. `cover-image` 和 `gemini-image` 的 cover/illustrate 模式重复
3. baoyu-skills 的风格库未融入工具链，每次需手动跨 skill 拼装

## 方案

### 架构变更

```
现在（3 个入口，职责模糊）:
  gemini-image  →  generate / edit / understand / cover / illustrate
  cover-image   →  cover（重复）

改后（2 个入口，职责清晰）:
  gemini-image  →  generate / edit / understand（纯引擎）
  article-image →  cover / illustrate（工作流，共享风格库）
```

### gemini-image 瘦身

删除内容：
- SKILL.md 中 `Mode: illustrate` 和 `Mode: cover` 两整段
- `references/auto-selection.md`
- `references/prompt-templates.md`（移到 article-image）
- `references/styles.md`（移到 article-image）
- description 中去掉 illustrate/配图/封面图 等触发词

保留：generate / edit / understand 三个引擎模式。脚本 `gemini_image.py` 不动。

### article-image skill

由 cover-image 重命名并扩展。

#### 目录结构

```
article-image/
├── SKILL.md
└── references/
    ├── style-presets.md
    ├── auto-selection.md
    ├── prompt-templates.md
    └── styles/
        ├── notion.md
        ├── warm.md
        ├── elegant.md
        ├── minimal.md
        ├── blueprint.md
        ├── watercolor.md
        ├── editorial.md
        ├── scientific.md
        ├── sketch-notes.md       # 来自 baoyu
        ├── chalkboard.md         # 来自 baoyu
        ├── pixel-art.md          # 来自 baoyu
        ├── retro.md              # 来自 baoyu
        ├── flat-doodle.md        # 来自 baoyu
        ├── fantasy-animation.md  # 来自 baoyu
        └── vintage.md            # 来自 baoyu
```

#### 两个模式

| | cover 模式 | illustrate 模式 |
|---|---|---|
| 触发 | "封面图"、"配图"（单张）、"cover" | "给文章配图"、"插图"、"illustrate" |
| 输出 | 1 张，嵌入 frontmatter + 正文顶部 | 2-5 张（AI）+ 0-N 个 Mermaid 代码块 |
| 宽高比 | 16:9（默认） | 16:9（默认） |

#### 统一 5D 维度

| 维度 | 控制 | 可选值 |
|------|------|--------|
| type | 构图/布局 | cover: hero / conceptual / typography / metaphor / scene / minimal; illustrate: infographic / scene / flowchart / comparison / framework / timeline |
| palette | 色彩 | warm / elegant / cool / dark / earth / vivid / pastel / mono / retro |
| rendering | 线条质感 | flat-vector / hand-drawn / painterly / digital / pixel / chalk |
| text | 文字密度 | none / title-only / title-subtitle / text-rich |
| mood | 情绪强度 | subtle / balanced / bold |

#### 预设机制

`--style <name>` 展开为 palette + rendering，其余维度独立选或自动选。

| style 预设 | palette | rendering |
|-----------|---------|-----------|
| elegant | elegant | hand-drawn |
| blueprint | cool | digital |
| chalkboard | dark | chalk |
| warm | warm | hand-drawn |
| minimal | mono | flat-vector |
| notion | mono | digital |
| watercolor | earth | painterly |
| editorial | cool | digital |
| scientific | cool | digital |
| sketch-notes | warm | hand-drawn |
| pixel-art | vivid | pixel |
| retro | retro | digital |
| flat-doodle | pastel | flat-vector |
| fantasy-animation | pastel | painterly |
| vintage | retro | hand-drawn |

可叠加覆盖：`--style elegant --rendering digital` → palette=elegant, rendering=digital

#### Mermaid 智能分流

illustrate 模式分析文章时，按以下规则分流：

| 内容特征 | 推荐方式 | 原因 |
|---------|---------|------|
| 流程/步骤/生命周期 | Mermaid flowchart | 文字精准，箭头关系清晰 |
| 架构/组件关系 | Mermaid flowchart + subgraph | 层级和连接必须准确 |
| 时序/交互过程 | Mermaid sequence | 调用顺序不能模糊 |
| 状态变化 | Mermaid stateDiagram | 状态名和转换条件是关键信息 |
| 概念解释/视觉隐喻 | AI 生成 | 需要创意表达，文字不重要 |
| 数据对比/信息图 | AI 生成 | 视觉排版比精确文字更重要 |
| 氛围/节奏装饰 | AI 生成 | 纯美感 |

判断标准：图里的文字是核心信息 → Mermaid，文字是点缀 → AI 生成。

### 上游联动

| 上游 | 现在调用 | 改后调用 |
|------|---------|---------|
| article-gen | cover-image | article-image（cover 模式） |
| 用户说"给文章配图" | gemini-image illustrate | article-image（illustrate 模式） |
| 用户说"生成一张图" | gemini-image generate | gemini-image（不变） |

### 触发词分配

| 触发词 | 路由 |
|--------|------|
| "封面图"、"配图"（单张）、"cover" | article-image → cover |
| "给文章加插图"、"illustrate"、"文章配图" | article-image → illustrate |
| "生成一张图"、"画一个..."、"draw" | gemini-image → generate |
| "分析这张图"、"看看这张图" | gemini-image → understand |
| "修改这张图"、"加个..." | gemini-image → edit |

## 执行任务

### Task 1: 创建 article-image skill 目录和 references

1. 创建 `~/.claude/skills/article-image/` 目录结构
2. 从 gemini-image 移入 `references/prompt-templates.md`、`references/auto-selection.md`
3. 从 gemini-image 移入并重组 `references/styles.md` → 拆为 `references/styles/` 下 8 个独立文件
4. 从 baoyu 复制 7 种新风格的详细定义到 `references/styles/`
5. 创建 `references/style-presets.md`（预设映射表）

### Task 2: 编写 article-image SKILL.md

1. 基于 cover-image SKILL.md 重写
2. 加入 illustrate 模式（从 gemini-image 移入并增强）
3. 统一 5D 维度描述
4. 加入 Mermaid 分流逻辑
5. 更新 description 和触发词

### Task 3: gemini-image 瘦身

1. 删除 SKILL.md 中 cover 和 illustrate 段落
2. 删除 references/auto-selection.md、references/prompt-templates.md、references/styles.md
3. 更新 description

### Task 4: 删除旧 cover-image skill

1. 删除 `~/.claude/skills/cover-image/` 目录

### Task 5: 更新上游 skill 引用

1. 检查 article-gen SKILL.md 中对 cover-image 的引用，改为 article-image
2. 检查其他 skill 是否有引用需要更新
