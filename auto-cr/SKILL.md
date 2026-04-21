---
name: auto-cr
description: Push to Yunxiao and auto-create Change Request with AI review comments. Use when user says 'auto-cr', '发CR', '提交CR', '创建合并请求', or wants to push code and create a CR on Codeup.
allowed-tools: Bash, Read, Grep, Glob
---

# Auto CR — Push + Create Change Request + AI Review Backfill

Push current branch to Yunxiao (Codeup), create a Change Request (merge request), and backfill AI code review comments via MCP.

## Prerequisites

- Current branch is NOT master/main (must be a feature/hotfix/release branch)
- There are commits ahead of target branch
- Yunxiao MCP tools are available (`mcp__yunxiao__*`)

## Organization Config

```
organizationId: 696f3f56b28d0aba0f5e4371
```

Repository IDs (lookup from remote URL if not listed):

| Repo | ID | Default Branch |
|------|----|---------------|
| calibration | 6236666 | master |
| claude-skills | 6325169 | master |
| claude-config | 6334221 | master |
| yueke-duco | 6277849 | master |
| yueke-flexiv | 6268132 | master |
| hybrid-il | 6273594 | master |
| hilserl | 6500744 | master |
| huazhi-display | 6368780 | master |
| ucal | 6391996 | master |

## Steps

### Step 1: Validate

```bash
# Must be on a feature branch, not master/main
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" == "master" || "$BRANCH" == "main" ]]; then
  echo "ERROR: Cannot create CR from $BRANCH. Create a feature branch first."
  exit 1
fi

# Must have commits ahead of target
git log master..$BRANCH --oneline
```

### Step 2: Push

```bash
# Push current branch to yunxiao (or origin)
REMOTE=$(git remote | grep -E '^(yunxiao|origin)' | head -1)
git push -u $REMOTE $BRANCH
```

### Step 3: Identify Repository

Detect repository ID from git remote URL:

```bash
REMOTE_URL=$(git remote get-url $REMOTE)
# Match against known repos to get repositoryId
```

### Step 4: Create Change Request

Use `mcp__yunxiao__create_change_request`:

- **title**: Use the last commit message subject (or summarize if multiple commits)
- **sourceBranch**: Current branch name
- **targetBranch**: `master` (or detect from repo config)
- **description**: Auto-generate from commit log:

```markdown
## Summary

<Summarize all commits in this branch>

## Commits

- <commit 1>
- <commit 2>
- ...

---
*CR created by Claude Code /auto-cr*
```

### Step 5: Get Diff via MCP

Use `mcp__yunxiao__compare`:

```
from: master (target branch)
to: <current branch>
```

This returns the full diff with file paths, line numbers, and content.

### Step 6: AI Code Review

Analyze the diff and generate review comments:

**Review checklist**:
- Code correctness and logic
- Error handling
- Performance considerations
- Naming and readability
- Test coverage (are tests included for new features?)
- Architecture alignment (does it follow project patterns?)

### Step 7: Backfill Comments to CR

First get patchset IDs via `mcp__yunxiao__list_change_request_patch_sets`.

Then post comments:

1. **INLINE_COMMENT** — For specific code issues, use `mcp__yunxiao__create_change_request_comment` with:
   - `comment_type`: `INLINE_COMMENT`
   - `file_path`: The file with the issue
   - `line_number`: Exact line
   - `from_patchset_biz_id`: Base (MERGE_TARGET) patchset
   - `to_patchset_biz_id`: Source (MERGE_SOURCE) patchset
   - `patchset_biz_id`: Source patchset

2. **GLOBAL_COMMENT** — Overall review summary, use `mcp__yunxiao__create_change_request_comment` with:
   - `comment_type`: `GLOBAL_COMMENT`
   - Summary table: commit message check, branch naming, security scan, code quality
   - Overall conclusion: PASS / WARN / NEEDS_WORK

### Step 8: Output

```
========================================
  /auto-cr 完成
========================================

分支: feature/xxx → master
CR:   https://codeup.aliyun.com/...
评论: N 条行内评论 + 1 条全局总结

[DONE]
========================================
```

## CR Description Template

```markdown
## Summary

<1-3 bullet points summarizing changes>

## Changes

| File | Change |
|------|--------|
| path/to/file.py | <brief description> |

## Commits

<list of commits>

## AI Review

<PASS/WARN/NEEDS_WORK> — See inline comments for details.

---
*CR created by Claude Code /auto-cr*
```

## Error Handling

| Error | Action |
|-------|--------|
| Not on feature branch | Abort with message |
| No commits ahead | Abort: "Nothing to CR" |
| Push fails | Show error, abort |
| CR creation fails (source commit null) | Remove `createFrom` param, retry |
| MCP not available | Abort: "Yunxiao MCP not configured" |
| Repository not in known list | Try URL-encoded full path as repositoryId |
