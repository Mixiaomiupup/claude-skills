---
name: ship
description: One-command workflow that chains commit → review → auto-cr. Use when user says '/ship', '一把梭', '提交并发CR', '全流程提交', or wants to commit, review, and create CR in one shot.
allowed-tools: Bash, Read, Grep, Glob
---

# Ship — Commit → Review → Auto-CR Pipeline

One command to format, commit, safety-check, push, and create CR with AI review.

## Flow

```
/ship
  │
  ├─ Step 1: Pre-commit format (from commit skill)
  │   └─ ruff/eslint/clang-format on staged files
  │
  ├─ Step 2: Commit (invoke commit skill)
  │   └─ Generate conventional message + git commit
  │
  ├─ Step 3: Safety gate (invoke review skill, Mode A)
  │   ├─ 🔴 BLOCK → Stop here, show issues, do NOT push
  │   ├─ 🟡 WARN → Show warnings, ask user to confirm
  │   └─ 🟢 PASS → Continue
  │
  ├─ Step 4: Auto-CR (invoke auto-cr skill)
  │   ├─ git push
  │   ├─ Create CR on Yunxiao
  │   ├─ AI code review on diff
  │   └─ Backfill inline + global comments
  │
  └─ Step 5: Output
      └─ CR link + summary
```

## Usage

```
/ship                    # Ship all staged changes
/ship --skip-review      # Skip safety gate (use with caution)
/ship --dry-run          # Run through steps without pushing
```

## Implementation

This skill orchestrates three existing skills. Invoke them in sequence:

### Step 1 & 2: Commit

Invoke the `commit` skill. It handles:
- Pre-commit formatting (ruff/eslint)
- Staging files
- Generating commit message
- Creating the commit

If there are no staged changes and no unstaged changes, abort with: "Nothing to ship."

### Step 3: Safety Gate

Run `review` skill in **Mode A (Pre-push Safety Gate)**:

```bash
# Get the diff of the commit just created
git diff HEAD~1..HEAD
```

Feed this diff to the review skill's safety gate checks:
1. Credential detection (passwords, API keys, tokens)
2. Large file detection (> 5MB, binary files)
3. Sensitive data (internal IPs with passwords, PII)

**Decision matrix**:

| Result | Action |
|--------|--------|
| 🔴 BLOCK | Print issues. Ask user: "Fix issues and re-run /ship, or /ship --skip-review to force" |
| 🟡 WARN | Print warnings. Ask: "Continue anyway? (y/n)" |
| 🟢 PASS | Proceed silently |

### Step 4: Auto-CR

Invoke the `auto-cr` skill. It handles:
- Push to Yunxiao
- Create Change Request
- Get diff via MCP compare
- Generate AI code review
- Backfill inline + global comments

### Step 5: Output

```
========================================
  /ship 完成
========================================

  Commit:  <hash> <message>
  Branch:  <branch> → master
  CR:      <url>
  Review:  N inline + 1 global comment
  Safety:  PASS ✓

========================================
```

## Edge Cases

| Situation | Handling |
|-----------|---------|
| On master/main branch | Abort: "Cannot ship from master. Create a feature branch first: `git checkout -b feature/xxx`" |
| No changes to commit | Abort: "Nothing to ship." |
| Safety gate blocks | Stop before push, show issues |
| Push fails | Show git error, do not create CR |
| CR creation fails | Show error, but push already succeeded — inform user to create CR manually |
| No Yunxiao MCP | Abort: "Yunxiao MCP not configured. Use /commit + /review separately." |

## Relationship to Individual Skills

```
/commit   = Step 1-2 only (format + commit)
/review   = Step 3 only (safety gate or full review)
/auto-cr  = Step 4 only (push + CR + review backfill)
/ship     = All steps chained (1 → 2 → 3 → 4)
```

Each skill works independently. /ship is the convenience wrapper.
