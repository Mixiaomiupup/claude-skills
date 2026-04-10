---
name: doc-control
description: Intelligent documentation generation control - prevents unnecessary documentation while maintaining quality standards. Use before creating/updating ANY project documentation.
---

# Documentation Control Skill

## Purpose

This skill helps Claude Code make intelligent decisions about when to generate or update documentation, preventing the common problem of over-documenting simple changes while ensuring important architectural decisions are properly recorded.

## When to Use

Use this skill **BEFORE** creating or updating any project documentation when:
- You're unsure if documentation is needed for a change
- A change might be Level 2 but feels like Level 1
- You're about to create a new document file
- The user mentions "too much documentation" or "unnecessary docs"

## Workflow

### Step 1: Detect Project Documentation Mode

Read `.claude/system-instructions.txt` to check for documentation mode declaration:

```bash
# Look for: "Documentation Mode: strict|standard|comprehensive"
```

**Default**: If not found, assume `standard` mode.

### Step 2: Classify Change Level (Strict Criteria)

Use these **strict criteria** to avoid over-classification:

**Level 1** (No docs needed):
- Single file modifications
- Bug fixes affecting ≤2 files
- Adding/modifying single functions
- Refactoring within one module

**Level 2** (Selective docs):
- New feature spanning ≥3 files
- Cross-module refactoring
- New module creation
- API endpoint additions

**Level 3** (Required docs):
- System architecture changes
- Database schema migrations
- Breaking API changes
- New service/microservice additions

**When in doubt**: Default to **lower level** (Level 1 over 2, Level 2 over 3).

### Step 3: Check Existing Documentation

Use Glob to scan the project's `docs/` directory:

```bash
# Check for existing docs
ls docs/ 2>/dev/null || echo "No docs directory"
ls docs/*.md 2>/dev/null
ls docs/plans/ 2>/dev/null
```

**Identify**:
- Main architecture doc: `docs/ARCHITECTURE.md`
- Module docs: `docs/MODULE_*.md` or `docs/*_ARCHITECTURE.md`
- Planning docs: `docs/plans/YYYY-MM-DD-*.md`

### Step 4: Apply Decision Matrix

| Level | Mode | Existing Doc | Decision |
|-------|------|--------------|----------|
| 1 | Any | Any | Code comments only |
| 2 | strict | No | Skip creation |
| 2 | strict | Yes | Update existing |
| 2 | standard | No | Create if new module |
| 2 | standard | Yes | Update existing |
| 2 | comprehensive | No | Create MODULE doc |
| 2 | comprehensive | Yes | Update + expand |
| 3 | strict | No | **Ask user** |
| 3 | strict | Yes | Update |
| 3 | standard | No | Create ARCHITECTURE.md |
| 3 | standard | Yes | Update |
| 3 | comprehensive | Any | Full documentation |

### Step 5: Output Recommendation

Provide clear recommendation:

```
📋 Documentation Decision:
- Change Level: [1/2/3]
- Project Mode: [strict/standard/comprehensive]
- Existing Docs: [list files or "none"]
- Recommendation: [Update X / Create Y / Skip docs / Ask user]
- Rationale: [brief explanation]
```

## Examples

### Example 1: Bug Fix

**Input**: "Fixed authentication timeout bug in auth.py"

**Analysis**:
- Level: 1 (single file bug fix)
- Mode: standard (default)
- Existing: docs/AUTH_MODULE.md exists
- **Decision**: Code comments only, no doc update needed

### Example 2: New Feature Module

**Input**: "Added email notification system (3 files: notifier.py, templates.py, sender.py)"

**Analysis**:
- Level: 2 (multi-file new module)
- Mode: standard
- Existing: No docs/NOTIFICATION_MODULE.md
- **Decision**: Create docs/NOTIFICATION_MODULE.md with module overview

### Example 3: Architecture Change

**Input**: "Migrating from monolith to microservices"

**Analysis**:
- Level: 3 (system architecture change)
- Mode: standard
- Existing: docs/ARCHITECTURE.md exists
- **Decision**: Update docs/ARCHITECTURE.md with new microservices architecture

## Anti-Patterns to Avoid

❌ **Don't**: Create docs for every small change
❌ **Don't**: Generate docs without checking existing files first
❌ **Don't**: Escalate Level 1 changes to Level 2
❌ **Don't**: Create redundant README files

✅ **Do**: Check docs/ directory before creating new files
✅ **Do**: Update existing docs instead of creating new ones
✅ **Do**: Use code comments for Level 1 changes
✅ **Do**: Ask user when uncertain about Level 3 in strict mode

## Integration with CLAUDE.md

This skill implements the decision tree defined in CLAUDE.md Section 1.3.1. When in doubt:
1. Invoke this skill
2. Follow its recommendation
3. Document rationale in commit message if skipping docs
