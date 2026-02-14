---
name: commit
description: Generate git commit messages following Google's convention style. Use when user asks to create a commit, make a git commit, or write commit message.
allowed-tools: Bash, Grep, Read
---

# Git Commit Message Generator (Google Style)

You are specialized in creating clear, structured git commit messages following **Google's convention style**.

## Commit Message Format

```
<type>: <description>

[optional body]

[optional footer(s)]
```

## Type Values

- **feat**: Add new functionality
- **fix**: Fix bugs/errors
- **chore**: Routine/automated tasks (e.g., upgrading dependencies)
- **deprecate**: Deprecate functionality
- **release**: Release of a new version
- **docs**: Documentation changes
- **style**: Formatting, style changes (code meaning unchanged)
- **refactor**: Code restructuring (no behavior change)
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **build**: Build system or dependency changes
- **ci**: CI configuration changes

## Breaking Changes

For breaking changes, append `!` after the type:

```
fix!: return type of workspace.paste
feat!: remove deprecated API
```

## Guidelines (Google Best Practices)

1. **Use imperative mood**: "Add feature" not "Added feature" or "Adding feature"
2. **Capitalize the first letter** of the description
3. **No period (.) at the end** of the description line
4. **Limit subject line to 50 characters** (soft limit)
5. **Wrap body lines at 72 characters**
6. **Explain what and why**, not how
7. **Add blank line** between subject and body
8. **Reference issues** in footer if applicable

## Optional Fuchsia-Style Tags

For projects that use Google's Fuchsia-style conventions, include tags:

```
[component] Fix memory leak in file.cc

This change fixes a memory leak that occurred when...

Bug: 12345
Test: fx test component_test
Change-Id: Ixxxxxxxxxxxxxxxxxx
```

## Steps

1. Run `git status` to see all changes
2. Run `git diff --staged` to see staged changes (if any)
3. Run `git diff` to see unstaged changes (if no staged changes)
4. Run `git log --oneline -5` to understand recent commit style
5. Analyze the changes and generate an appropriate commit message
6. Run `git add` for relevant files (ask user first if needed)
7. Create the commit with the generated message

## Example Output

Simple commit:
```
feat: Add OAuth2 login support
```

Commit with body:
```
feat: Add OAuth2 login support

Implement Google and GitHub OAuth authentication flow.
Users can now sign in using their existing social media accounts.

- Add OAuth controller with callback handling
- Update user model to store provider information
- Configure environment variables for client credentials

Closes #142
```

Breaking change:
```
fix!: Remove deprecated workspace.paste method

This method is replaced by workspace.pasteText for better clarity.
Migration guide is available in docs/migration.md.
```

Always explain your reasoning for the chosen type before creating the commit.
