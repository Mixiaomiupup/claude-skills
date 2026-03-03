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

## Type × Style Compatibility

| | notion | warm | minimal | blueprint | watercolor | elegant | editorial | scientific |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| infographic | ++ | + | ++ | ++ | + | ++ | ++ | ++ |
| scene | + | ++ | + | - | ++ | + | + | - |
| flowchart | ++ | + | + | ++ | - | + | ++ | + |
| comparison | ++ | + | ++ | + | + | ++ | ++ | + |
| framework | ++ | + | ++ | ++ | - | ++ | + | ++ |
| timeline | ++ | + | + | + | ++ | ++ | ++ | + |

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
