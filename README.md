# Claude Code Skills

> 15 first-party skills | 1 third-party | 6 categories

Personal skill collection for Claude Code, synced to GitHub and Yunxiao via `cc-sync`.

## Quick Reference

| Skill | Category | Trigger | Description |
|-------|----------|---------|-------------|
| [ucal](ucal/SKILL.md) | Content & Knowledge | XHS/Zhihu/X link, "调研XX" | Cross-platform content analysis and research |
| [kb](kb/SKILL.md) | Content & Knowledge | "记下来", "搜知识库", "总结" | Obsidian knowledge base manager |
| [x2md](x2md/SKILL.md) | Content & Knowledge | X/Twitter link + "保存" | Tweet/thread to Obsidian Markdown converter |
| [gemini-image](gemini-image/SKILL.md) | Image & Media | "画一张", "generate image" | Gemini AI image generation, editing, understanding |
| [review](review/SKILL.md) | Code Quality | "review", "审查代码" | Six-dimension code review |
| [python-style](python-style/SKILL.md) | Code Quality | "check style", "PEP 8" | Python code style checker |
| [refactor](refactor/SKILL.md) | Code Quality | "重构", "improve code" | Code smell detection and refactoring |
| [debug](debug/SKILL.md) | Code Quality | Bug, error, unexpected behavior | Systematic debugging methodology |
| [test](test/SKILL.md) | Code Quality | "写测试", "test this" | Unit/integration test generator |
| [commit](commit/SKILL.md) | Dev Workflow | "提交", "commit" | Google convention commit generator |
| [remote-repos](remote-repos/SKILL.md) | Dev Workflow | Git push/pull, PR, CI/CD | GitHub + Yunxiao operations |
| [explain](explain/SKILL.md) | Dev Workflow | "怎么工作的", "explain this" | Code explanation with diagrams and analogies |
| [server](server/SKILL.md) | Infrastructure | SSH, deploy, server status | Aliyun server management |
| [sync-config](sync-config/SKILL.md) | Infrastructure | "sync", "backup config" | Config & skills sync to remotes |
| [doc-control](doc-control/SKILL.md) | Documentation | Before creating/updating docs | Documentation generation gatekeeper |

---

## Content & Knowledge

Skills for consuming, analyzing, and storing information.

### [ucal](ucal/SKILL.md)

Cross-platform content analyzer for XHS, Zhihu, X/Twitter, and generic web. Two modes: **read** (single link analysis) and **research** (multi-source investigation with hypothesis-driven evidence tracking and narrative reporting).

### [kb](kb/SKILL.md)

Obsidian vault manager (`~/Documents/obsidian/mixiaomi`). Five modes: write (notes/ideas), search (find content), synthesize (cross-note analysis), insight (personal reflections), browse (vault listing). Uses 9-category tag taxonomy.

### [x2md](x2md/SKILL.md)

X/Twitter content clipper. Converts tweets, threads, and long-form articles to clean Markdown with YAML frontmatter. Saves to Obsidian vault (`X收藏/`) with AI-generated categorization and summaries.

**Usage examples**: "帮我看看这个链接", "调研XX话题", "记下来: ...", "保存这条推文"

---

## Image & Media

Skills for generating, editing, and understanding images.

### [gemini-image](gemini-image/SKILL.md)

Generate, edit, and understand images using Gemini on Vertex AI. Three modes: **generate** (text-to-image), **edit** (modify existing images), **understand** (analyze image content). Supports photorealistic, watercolor, illustration, and other styles.

**Usage examples**: "画一张日落的图", "这张图里是什么", "给照片加一道彩虹", "generate a logo"

---

## Code Quality

Skills for reviewing, testing, debugging, and improving code.

### [review](review/SKILL.md)

Six-dimension code reviewer: security, correctness, performance, readability, maintainability, best practices. Priority system: critical / important / optional.

### [python-style](python-style/SKILL.md)

Python style enforcer using `ruff`, `black`, `isort`, `mypy`. Auto-fixes PEP 8 violations, reports issues with before/after examples.

### [refactor](refactor/SKILL.md)

Code refactoring advisor. Identifies code smells, checks SOLID principles, prioritizes improvements by impact, and provides concrete before/after examples with step-by-step plans.

### [debug](debug/SKILL.md)

Systematic debugging expert: understand problem -> reproduce -> hypothesize -> isolate -> verify fix. Provides diagnostic commands, common bug patterns, and structured debugging session output.

### [test](test/SKILL.md)

Test generator following Arrange-Act-Assert pattern. Supports Python, JavaScript/TypeScript, Go. Focuses on behavior testing, edge cases, and meaningful coverage targets.

**Usage examples**: "review PR", "check style", "重构这段代码", "帮我 debug", "写测试"

---

## Development Workflow

Skills for commits, repo operations, and code comprehension.

### [commit](commit/SKILL.md)

Git commit message generator following Google's convention style. Supports multiple commit types (`feat`, `fix`, `chore`, `docs`, `test`, etc.), breaking changes with `!` notation, and optional Fuchsia-style scope tags.

### [remote-repos](remote-repos/SKILL.md)

Dual-platform remote repo operations. GitHub via `gh` CLI, Yunxiao via MCP tools. Covers repos, branches, PRs/MRs, CI/CD pipelines, work items, and deployments.

### [explain](explain/SKILL.md)

Code explainer using big picture overviews, ASCII diagrams, step-by-step breakdowns, and analogies. Adapts depth to user level (beginner/intermediate/advanced).

**Usage examples**: "提交", "create PR", "explain this function"

---

## Infrastructure

Skills for server management and configuration sync.

### [server](server/SKILL.md)

Aliyun Ubuntu server manager (China East 2, 2 vCPU / 2 GiB). Hosts shige-h5 and csfilter projects. Provides SSH commands, deployment procedures, nginx routing config, and service management.

### [sync-config](sync-config/SKILL.md)

Unified CLI (`cc-sync`) for syncing Claude Code config and skills to GitHub + Yunxiao. Supports `push`/`pull` with `--dry-run` preview, `--yes` auto-confirm, and automatic credential sanitization.

**Usage examples**: "部署项目", "sync 配置", "backup config"

---

## Documentation

Skills for controlling documentation generation.

### [doc-control](doc-control/SKILL.md)

Documentation generation gatekeeper that prevents over-documentation. Classifies changes into Level 1-3, checks project documentation mode (`strict`/`standard`/`comprehensive`), and decides whether to create, update, or skip docs.

---

## Third-party

| Skill | Source | Notes |
|-------|--------|-------|
| baoyu-skills | [baoyu/claude-code-skills](https://github.com/baoyu/claude-code-skills) | Has its own git repo, tracked in `component-manifest.json` |

## Sync

```bash
# Preview changes
cc-sync push --target skills --dry-run

# Push to both remotes
cc-sync push --target skills --yes

# Check status
cc-sync status
```
