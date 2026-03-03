# Prompt Construction Guide

## Principles

1. **Layout structure first**: Describe composition, zones, flow direction before content
2. **Use real data**: Labels, numbers, terms must come from the source article — never fabricate
3. **Semantic colors**: Meaning-based color choices (red=warning, green=efficient, blue=technical)
4. **Style characteristics**: Include specific line treatment, texture, mood from style definition
5. **Aspect ratio**: End with ratio specification
6. **No vagueness**: Never use "a nice image" or "beautiful illustration" — be structural and specific

## Anti-Patterns

- Vague descriptions ("make it look good")
- Literal metaphor illustrations (if article says "chainsaw cutting watermelon" as metaphor, visualize the **underlying concept**, not the literal scene)
- Missing concrete labels/annotations
- Generic decorative elements with no semantic meaning
- Fabricated data points not from source

---

## Illustration Templates (by Type)

### infographic

```
[Title] - Data Visualization

Layout: [grid/radial/hierarchical]

ZONES:
- Zone 1: [data point with specific values from article]
- Zone 2: [comparison with real metrics]
- Zone 3: [summary/conclusion]

LABELS: [specific numbers, percentages, terms from article]
COLORS: [semantic color mapping from style definition, with hex codes]
VISUAL ELEMENTS: [style-specific elements: e.g., "hand-drawn wobble lines" for notion, "precise grid-aligned vectors" for blueprint]
STYLE: [style name] — [2-3 key characteristics from style definition]
ASPECT: 16:9
```

### scene

```
[Title] - Atmospheric Scene

FOCAL POINT: [main subject derived from article's core message]
ATMOSPHERE: [lighting, mood, environment]
MOOD: [emotion the article conveys]
COLOR TEMPERATURE: [warm/cool/neutral, with palette hex codes]
VISUAL ELEMENTS: [style-specific elements]
STYLE: [style name] — [2-3 key characteristics]
ASPECT: 16:9
```

### flowchart

```
[Title] - Process Flow

Layout: [left-right/top-down/circular]

STEPS:
1. [Step name from article] — [brief description]
2. [Step name from article] — [brief description]
...

CONNECTIONS: [arrow types based on style: "90-degree lines" for blueprint, "curved hand-drawn arrows" for notion]
COLORS: [semantic: start=green, process=blue, decision=amber, end=coral]
STYLE: [style name] — [2-3 key characteristics]
ASPECT: 16:9
```

### comparison

```
[Title] - Comparison View

LEFT SIDE — [Option A from article]:
- [Point 1 with real data]
- [Point 2 with real data]

RIGHT SIDE — [Option B from article]:
- [Point 1 with real data]
- [Point 2 with real data]

DIVIDER: [visual separator matching style]
COLORS: [Left=palette primary, Right=palette accent]
STYLE: [style name] — [2-3 key characteristics]
ASPECT: 16:9
```

### framework

```
[Title] - Conceptual Framework

STRUCTURE: [hierarchical/network/matrix — as described in article]

NODES:
- [Concept 1 from article] — [role]
- [Concept 2 from article] — [role]

RELATIONSHIPS: [how nodes connect, using article's logic]
COLORS: [semantic: core=primary, supporting=secondary, connections=accent]
STYLE: [style name] — [2-3 key characteristics]
ASPECT: 16:9
```

### timeline

```
[Title] - Chronological View

DIRECTION: [horizontal/vertical]

EVENTS:
- [Date/Period 1 from article]: [milestone]
- [Date/Period 2 from article]: [milestone]

MARKERS: [style-appropriate indicators]
COLORS: [semantic: past=muted, present=primary, future=accent]
STYLE: [style name] — [2-3 key characteristics]
ASPECT: 16:9
```

---

## Cover Image Template (5-Dimension)

```
# Content Context
Article title: [full original title]
Content summary: [2-3 sentence summary]
Keywords: [5-8 key terms]

# Visual Design
Cover theme: [2-3 word visual interpretation]
Type: [hero/conceptual/typography/metaphor/scene/minimal]
Palette: [name] — primary: [hex], background: [hex], accent: [hex]
Rendering: [name] — [key characteristics: lines, texture, depth]
Text level: [none/title-only/title-subtitle/text-rich]
Mood: [subtle/balanced/bold]
Aspect ratio: [16:9 / 2.35:1 / 1:1 / 3:4]

# Text Elements
[Based on text level:]
- none: "No text elements. Pure visual."
- title-only: "Title: [max 8 chars, punchy headline]"
- title-subtitle: "Title: [headline] / Subtitle: [max 15 chars]"
- text-rich: "Title: [headline] / Subtitle: [context] / Tags: [2-4 keywords]"

# Mood Application
[Based on mood:]
- subtle: "Low contrast, muted colors, light visual weight, calm."
- balanced: "Medium contrast, normal saturation, balanced weight."
- bold: "High contrast, vivid saturated colors, heavy weight, dynamic energy."

# Composition
Type composition:
- hero: Large focal visual (60-70%), title overlay, dramatic.
- conceptual: Abstract shapes for core ideas, information hierarchy, clean zones.
- typography: Title as primary element (40%+), minimal supporting visuals.
- metaphor: Concrete object representing abstract idea, symbolic.
- scene: Atmospheric environment, narrative elements, mood lighting.
- minimal: Single focal element, generous whitespace (60%+), essential shapes.

Visual:
- Main visual: [metaphor derived from article meaning, NOT literal]
- Layout: [positioning based on type]
- Decorative: [palette-specific decorative hints]

Color scheme: [from palette definition]
Rendering notes: [from rendering definition]
```

---

## Title Guidelines (for covers)

- Max 8 characters for title, punchy headline
- Engagement hooks: numbers ("3 Traps"), questions ("Why X?"), contrasts ("A vs B"), pain points
- Match content language

## Assembly Checklist

Before calling `generate`, verify:
- [ ] Layout/composition described before content
- [ ] All data points come from source article
- [ ] Colors include hex codes from style definition
- [ ] Style-specific visual elements mentioned (not generic)
- [ ] Metaphors visualize underlying concept, not literal meaning
- [ ] Aspect ratio specified
