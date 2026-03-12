# Auto-Selection Rules

When dimensions are omitted, select based on content signals.

## Illustration Type (for `illustrate` mode)

| Content Signals | Type |
|-----------------|------|
| API, metrics, data, numbers, percentage | `infographic` |
| Story, emotion, journey, personal experience | `scene` |
| How-to, steps, workflow, process, tutorial | `flowchart` |
| vs, pros/cons, before/after, alternatives | `comparison` |
| Framework, model, architecture, principles | `framework` |
| History, timeline, progress, evolution | `timeline` |

## Mermaid vs AI Generation (for `illustrate` mode)

Before selecting style, determine rendering method:

| Content Feature | Method | Reason |
|----------------|--------|--------|
| Flow/steps/lifecycle | Mermaid flowchart | Text precision, clear arrows |
| Architecture/components | Mermaid flowchart + subgraph | Accurate hierarchy and connections |
| Sequence/interaction | Mermaid sequence | Call order must be exact |
| State transitions | Mermaid stateDiagram | State names and conditions are key |
| Concept/visual metaphor | AI generation | Creative expression, text not critical |
| Data comparison/infographic | AI generation | Visual layout matters more than text |
| Atmosphere/decoration | AI generation | Pure aesthetics |

**Rule of thumb**: Text is core information -> Mermaid. Text is decoration -> AI generation.

## Illustration Style (for `illustrate` mode)

| Content Signals | Style |
|-----------------|-------|
| Knowledge, SaaS, productivity, concept | `notion` |
| Business, professional, corporate | `elegant` |
| Personal, lifestyle, education, warm | `warm` |
| Philosophy, zen, core concepts | `minimal` |
| Architecture, system design, API, code | `blueprint` |
| Travel, lifestyle, creative, dreamy | `watercolor` |
| Tech explainer, journalism, magazine | `editorial` |
| Biology, chemistry, academic, research | `scientific` |
| Tutorial, notes, onboarding, friendly | `sketch-notes` |
| Teaching, classroom, explanation | `chalkboard` |
| Gaming, retro tech, fun, nostalgic | `pixel-art` |
| 80s/90s, nostalgia, bold energy | `retro` |
| Lightweight, casual, cheerful | `flat-doodle` |
| Animation, magical, storybook | `fantasy-animation` |
| History, heritage, exploration | `vintage` |

## Type x Style Compatibility

| | notion | warm | minimal | blueprint | watercolor | elegant | editorial | scientific | sketch-notes | chalkboard | pixel-art | retro | flat-doodle | fantasy-animation | vintage |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| infographic | ++ | + | ++ | ++ | + | ++ | ++ | ++ | ++ | + | + | + | + | - | + |
| scene | + | ++ | + | - | ++ | + | + | - | + | - | + | + | + | ++ | ++ |
| flowchart | ++ | + | + | ++ | - | + | ++ | + | ++ | ++ | - | + | + | - | - |
| comparison | ++ | + | ++ | + | + | ++ | ++ | + | + | + | + | + | ++ | - | + |
| framework | ++ | + | ++ | ++ | - | ++ | + | ++ | + | + | - | + | - | - | + |
| timeline | ++ | + | + | + | ++ | ++ | ++ | + | + | + | + | ++ | + | + | ++ |

`++` = recommended | `+` = works | `-` = avoid

## Cover Type (for `cover` mode)

| Signals | Type |
|---------|------|
| Product, launch, announcement, reveal | `hero` |
| Architecture, framework, system, API, technical | `conceptual` |
| Quote, opinion, insight, headline, statement | `typography` |
| Philosophy, growth, abstract, reflection | `metaphor` |
| Story, journey, travel, lifestyle, narrative | `scene` |
| Zen, focus, essential, core, simple, pure | `minimal` |

## Cover Palette

| Signals | Palette |
|---------|---------|
| Personal story, emotion, lifestyle | `warm` |
| Business, professional, luxury | `elegant` |
| Architecture, system, API, code | `cool` |
| Entertainment, premium, cinematic | `dark` |
| Nature, wellness, eco, organic | `earth` |
| Product launch, gaming, promotion | `vivid` |
| Fantasy, children, gentle, creative | `pastel` |
| Zen, focus, essential, pure | `mono` |
| History, vintage, classic | `retro` |

## Cover Rendering

| Signals | Rendering |
|---------|-----------|
| Clean, modern, tech, infographic | `flat-vector` |
| Sketch, note, personal, casual, doodle | `hand-drawn` |
| Art, watercolor, soft, dreamy, creative | `painterly` |
| Data, dashboard, SaaS, corporate | `digital` |
| Gaming, retro, 8-bit, nostalgic | `pixel` |
| Education, tutorial, classroom | `chalk` |
