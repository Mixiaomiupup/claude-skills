# Universal Article Gen Design

Date: 2026-03-10
Status: validated

## Goal

Upgrade article-gen from news-only to a universal article generation engine supporting 6 article types with different styles, templates, and frontmatter schemas.

## Key Decisions

| Decision | Conclusion |
|----------|-----------|
| Article types | 6 fixed enum: news/architecture/review/tutorial/notes/essay |
| Type inference | Hybrid: auto-infer when possible, ask when uncertain |
| Taxonomy | `type` (form) and `category` (domain) decoupled |
| Category expansion | Semi-auto: Claude proposes, user confirms, persisted to index file |
| Category storage | `~/Documents/obsidian/mixiaomi/meta/categories.md` |
| Frontmatter | Shared core fields + fixed extension fields per type |
| Body templates | Recommended structure, Claude adjusts flexibly |
| Research vs writing | Separated: article-gen only handles writing + enrichment + publish |
| Input format | Each type accepts different input, article-gen consumes by type |
| Skill architecture | Only modify article-gen SKILL.md, no new skills |
| Workflow | Add "type inference" step before existing flow, enrichment branches by type |

## Type System

### `type` (article form) - 6 fixed values

| type | Description | Typical input |
|------|------------|---------------|
| `news` | News/tweet coverage | X link, news URL |
| `architecture` | Technical architecture analysis | GitHub repo, code notes |
| `review` | Product/project review | Product URL, usage notes |
| `tutorial` | Technical tutorial | Problem description, code snippets |
| `notes` | Book/paper notes | PDF, article URL, handwritten points |
| `essay` | Personal opinion/thoughts | Verbal, outline, scattered ideas |

### `category` (content domain) - decoupled, semi-auto expandable

Existing 9 + new:

- AI/development, AI/application, AI/impact
- Tech/trends, Tech/development, **Tech/architecture** (new)
- Business/startup, Business/product
- Thoughts/creativity, Thoughts/society, **Thoughts/growth** (new)

Stored in: `~/Documents/obsidian/mixiaomi/meta/categories.md`

### Type inference rules

- X/Twitter link -> news
- GitHub link -> architecture
- User says "review/compare" -> review
- User says "how to/tutorial" -> tutorial
- User says "finished reading/notes" -> notes
- User says "I think/want to discuss" -> essay
- Cannot infer -> ask user

## Frontmatter Design

### Core fields (all types)

```yaml
title: ""
author: ""
type: news
source: ""          # can be empty for essay
date: 2026-03-10
saved_at: 2026-03-10
lang: zh
category: AI/application
tags: []
summary: []
status: raw         # raw -> enriched -> published
cover: ""
feishu_node_token: ""
feishu_sync_time: ""
```

### Extension fields per type

| type | Extension fields |
|------|-----------------|
| `news` | `author_handle`, `likes`, `retweets`, `views` |
| `architecture` | `repo_url`, `tech_stack: []`, `stars`, `license` |
| `review` | `product_name`, `product_url`, `rating: 1-5`, `verdict` |
| `tutorial` | `difficulty: beginner/intermediate/advanced`, `prerequisites: []` |
| `notes` | `book_title`, `book_author`, `isbn`, `reading_progress` |
| `essay` | `thesis` (core argument, one sentence) |

## Body Templates (recommended, flexible)

### news
- Translation (if non-Chinese)
- Original (if non-Chinese)
- Key analysis
- My notes

### architecture
- Project overview
- Tech stack
- Core architecture
- Key module analysis
- Design highlights and weaknesses
- Summary

### review
- Product intro
- Core features
- Hands-on experience
- Pros and cons
- Competitor comparison (if applicable)
- Conclusion

### tutorial
- Problem background
- Solution overview
- Implementation steps
- Common issues
- Summary

### notes
- Core arguments
- Key concepts
- Notable excerpts
- My thoughts

### essay
- Viewpoint
- Evidence
- Counter-arguments
- Conclusion

## Workflow

```
Input -> Type Inference -> Convert -> Enrichment -> Translate -> Cover -> Publish -> Report
```

### Convert (by type)

| type | Input | Method |
|------|-------|--------|
| `news` | X link / URL | x2md / ucal |
| `architecture` | Project path or notes | User provides research material |
| `review` | Product URL or usage notes | User provides research material |
| `tutorial` | Code / problem description | User provides directly |
| `notes` | PDF / URL / handwritten | ucal or user provides directly |
| `essay` | Verbal / outline | User provides directly |

### Enrichment (all types)
- Auto-classify category, assign tags, generate summary
- Load recommended body template by type, generate/restructure body
- Fill type extension fields
- status: raw -> enriched
- Category not in known list -> propose new, user confirms -> persist

### Translate
- Same as current: translate when lang != zh
- Code blocks in tutorial/architecture not translated

### Cover / Publish / Report
- Same as current, unchanged

## Skill Architecture

```
article-gen (orchestrator, this skill)
  |- x2md --- X -> Markdown (news type only)
  |- cover-image --- cover art (all types)
  |- feishu --- Feishu publish (all types)
  +- Claude --- enrichment + translation (built-in)
```

Changes to article-gen SKILL.md:
1. Type inference logic (new, at workflow start)
2. Body template table (6 recommended structures, inline)
3. Extension field definitions (per type, inline)
4. Category expansion mechanism (known list + propose instruction)

No new skills, no new tools, no config files.
