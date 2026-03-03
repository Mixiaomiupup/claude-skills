---
name: gemini-image
description: "AI-powered image generation, editing, and understanding via Gemini Vertex AI. THIS IS THE PREFERRED SKILL for any image-related task. Use when user asks to: (1) generate/create an image, picture, illustration, photo, or artwork from a text description, (2) analyze/understand/describe an existing image, (3) edit/modify an existing image (add elements, change style, remove objects), (4) illustrate an article or create article cover images, (5) says 'draw', 'paint', 'create a picture', 'generate an image', 'what is in this image', 'describe this image', 'edit this photo', 'illustrate this article', '配图', '封面图'. This skill calls Gemini API for real AI image generation — prefer this over code-based drawing skills (canvas-design, algorithmic-art) unless user specifically requests code-generated art."
---

# Gemini Image

Generate, edit, understand images, and create structured illustrations using Gemini on Vertex AI.

## Script

```bash
SCRIPT="$HOME/.claude/skills/gemini-image/scripts/gemini_image.py"
```

## Modes

| Mode | Trigger | Description |
|------|---------|-------------|
| `generate` | "generate an image of..." | Free-form text → image |
| `understand` | "what is in this image" | Image → text analysis |
| `edit` | "add X to this image" | Image + instruction → edited image |
| `illustrate` | "illustrate this article", "配图" | Article → structured multi-image illustrations |
| `cover` | "create a cover image", "封面图" | Article → structured cover image |

---

## Mode: generate

```bash
python3 "$SCRIPT" generate "A sunset over mountains" -o /tmp/sunset.png
```

1. Run `generate` with user's prompt and output path
2. Use Read tool to display the saved image
3. If user wants changes, refine prompt or use `edit`

**Prompt Tips**: Be specific about subject, style ("photorealistic", "watercolor", "flat illustration"), composition ("close-up", "bird's eye view"), lighting.

---

## Mode: understand

```bash
python3 "$SCRIPT" understand /path/to/image.png "What is shown here?"
```

---

## Mode: edit

```bash
python3 "$SCRIPT" edit /path/to/image.png "Add a rainbow" -o /tmp/edited.png
```

---

## Mode: illustrate

Analyze an article, identify illustration positions, construct structured prompts, and generate images.

**Dimension system**: Type × Style (see [references/styles.md](references/styles.md))

| Dimension | Controls | Values |
|-----------|----------|--------|
| **Type** | Information structure, layout | infographic, scene, flowchart, comparison, framework, timeline |
| **Style** | Visual aesthetics, colors, mood | notion, warm, minimal, blueprint, watercolor, elegant, editorial, scientific |

### Workflow

```
Read article → Analyze → Select Type × Style → Construct prompts → Generate images
```

#### Step 1: Analyze Content

Read the article and identify:
- Content type (technical / tutorial / methodology / narrative)
- 2-5 core arguments to visualize
- Visual opportunities (positions where illustrations add value)

**Illustrate** (core arguments, abstract concepts, data comparisons, processes).
**Do NOT illustrate** (metaphors literally, decorative scenes, generic illustrations).

**CRITICAL**: If article uses metaphors (e.g., "chainsaw cutting watermelon"), do NOT illustrate literally. Visualize the **underlying concept**.

#### Step 2: Select Dimensions

Auto-select Type × Style based on content signals (see [references/auto-selection.md](references/auto-selection.md)).

| Content Signals | Type | Style |
|-----------------|------|-------|
| API, metrics, data, numbers | infographic | blueprint, notion |
| Story, emotion, journey | scene | warm, watercolor |
| How-to, steps, workflow | flowchart | notion, minimal |
| vs, pros/cons, before/after | comparison | notion, elegant |
| Framework, model, architecture | framework | blueprint, notion |
| History, timeline, progress | timeline | elegant, warm |

Present recommendation to user, confirm before proceeding.

#### Step 3: Construct Prompts

Follow the Type-specific template from [references/prompt-templates.md](references/prompt-templates.md). Key rules:

1. **Layout structure first** — describe composition/zones before content
2. **Real data only** — labels, numbers must come from the article
3. **Include hex codes** — pull color palette from style definition in [references/styles.md](references/styles.md)
4. **Style-specific elements** — mention the style's visual characteristics (e.g., "hand-drawn wobble" for notion, "90-degree grid lines" for blueprint)

**Example** (infographic + blueprint):

```
AI Agent Architecture - Data Visualization

Layout: hierarchical, top-down

ZONES:
- Zone 1 (top): "3 Core Components" — LLM Engine, Tool Layer, Memory Store
- Zone 2 (middle): Data flow arrows showing request→reasoning→action→response cycle
- Zone 3 (bottom): Performance metrics — "Response: 2.3s, Accuracy: 94%, Tools: 12 integrated"

LABELS: LLM Engine, Tool Layer, Memory Store, 2.3s, 94%, 12 tools
COLORS: Primary=#2563EB (core nodes), Secondary=#1E3A5F (connections), Accent=#F59E0B (metrics), Background=#FAF8F5 (blueprint paper)
VISUAL ELEMENTS: Precise grid-aligned vectors, 90-degree connection lines, dimension indicators, consistent stroke weights
STYLE: blueprint — technical precision, engineering aesthetic, schematic drawing quality
ASPECT: 16:9
```

#### Step 4: Generate

For each illustration:
1. Call `python3 "$SCRIPT" generate "<assembled prompt>" -o <output_path>`
2. Use Read tool to display result
3. On failure: refine prompt and retry once

Output naming: `NN-{type}-{slug}.png` (e.g., `01-infographic-ai-architecture.png`)

---

## Mode: cover

Generate a structured cover image with 5-dimensional customization.

**Dimensions**:

| Dimension | Controls | Values | Default |
|-----------|----------|--------|---------|
| **Type** | Composition | hero, conceptual, typography, metaphor, scene, minimal | auto |
| **Palette** | Colors | warm, elegant, cool, dark, earth, vivid, pastel, mono, retro | auto |
| **Rendering** | Line quality, texture | flat-vector, hand-drawn, painterly, digital, pixel, chalk | auto |
| **Text** | Text density | none, title-only, title-subtitle, text-rich | title-only |
| **Mood** | Emotional intensity | subtle, balanced, bold | balanced |

### Workflow

```
Read content → Analyze → Auto-select or confirm 5 dimensions → Construct prompt → Generate
```

#### Step 1: Analyze Content

Extract topic, core message, tone, keywords. Detect content type.

#### Step 2: Select Dimensions

Auto-select based on content signals (see [references/auto-selection.md](references/auto-selection.md)).
Present recommendation. If user specifies `--quick`, skip confirmation.

#### Step 3: Construct Prompt

Follow the cover template from [references/prompt-templates.md](references/prompt-templates.md):

1. Fill **Content Context** (title, summary, keywords from article)
2. Fill **Visual Design** (all 5 confirmed dimensions with hex codes from [references/styles.md](references/styles.md))
3. Fill **Text Elements** (based on text level: max 8 chars for title)
4. Fill **Mood Application** (contrast/saturation/weight based on mood level)
5. Fill **Composition** (type-specific layout + visual metaphor from article meaning)

#### Step 4: Generate

```bash
python3 "$SCRIPT" generate "<assembled prompt>" -o cover.png
```

Aspect ratio: default 16:9, also supports 2.35:1, 1:1, 3:4.

---

## References

| File | Content |
|------|---------|
| [references/prompt-templates.md](references/prompt-templates.md) | Type-specific prompt templates + cover template |
| [references/styles.md](references/styles.md) | Style definitions with color palettes, visual elements, rules |
| [references/auto-selection.md](references/auto-selection.md) | Content signal → dimension auto-mapping |

## Config

- Auth: `~/YOUR_SERVICE_ACCOUNT_FILE` (service account)
- Project: `YOUR_GCP_PROJECT`, Location: `us-central1`
- Gen model: `gemini-2.0-flash-preview-image-generation`
- Understand model: `gemini-2.5-flash`
- Deps: `google-genai`, `Pillow`, `google-auth`
