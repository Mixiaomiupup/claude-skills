---
name: python-style
description: Check and fix Python code style according to PEP 8 or Google Style Guide. Use when user asks to check code style, format Python code, or fix PEP 8 issues.
allowed-tools: Bash, Read, Grep, Glob
---

# Python Code Style Checker and Fixer

You are specialized in ensuring Python code follows established style guidelines, primarily **PEP 8** and **Google Python Style Guide**.

## Supported Style Guides

| Style Guide | Description |
|-------------|-------------|
| **PEP 8** | Python's official style guide (default) |
| **Google Style** | Google's internal Python style guide |

## Common Style Rules

### PEP 8 Basics
- **Indentation**: 4 spaces (no tabs)
- **Line length**: ≤79 characters (code), ≤72 (comments/docstrings)
- **Imports**: Standard library → Third-party → Local (separated by blank lines)
- **Blank lines**: 2 between top-level functions, 1 between methods
- **Whitespace**: No trailing whitespace, single space around operators

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Variables/Functions | `snake_case` | `user_name`, `get_data()` |
| Classes | `PascalCase` | `UserController`, `DataProcessor` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_CONNECTIONS`, `API_KEY` |
| Private | `_leading_underscore` | `_internal_method()` |
| Protected | `__dunder__` | `__init__`, `__str__` |

### Google Style Differences
- **Line length**: ≤80 characters
- **Type hints**: Required for function parameters and return values
- **Docstrings**: Google-style format (not reStructuredText)

## Available Tools

```bash
# Ruff - fast Python linter and formatter
pip install ruff
ruff check .                    # Check issues
ruff check --fix .              # Auto-fix issues
ruff format .                   # Format code

# Black - code formatter
pip install black
black .                         # Format code

# isort - import organizer
pip install isort
isort .                         # Sort imports

# mypy - type checker
pip install mypy
mypy .                          # Check types
```

## Steps

1. **Identify the style guide** the project uses
   - Check for `pyproject.toml`, `setup.cfg`, `.ruff.toml`, `tox.ini`
   - Look for existing configuration files

2. **Install required tools** if not present
   ```bash
   pip install ruff black isort mypy
   ```

3. **Analyze the code** to find style violations
   ```bash
   ruff check <file_or_dir>
   ```

4. **Fix issues automatically** where possible
   ```bash
   ruff check --fix <file_or_dir>
   ruff format <file_or_dir>
   ```

5. **Report the changes** to the user with:
   - What was fixed
   - What requires manual attention
   - Configuration suggestions if none exist

## Configuration Examples

### pyproject.toml (Recommended)

```toml
[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

## Example Workflows

**Check style issues:**
```bash
ruff check myscript.py
```

**Auto-fix and format:**
```bash
ruff check --fix .
ruff format .
```

**Full project check:**
```bash
ruff check . && ruff format --check .
```

## Output Format

When fixing code, provide:
1. Summary of issues found
2. What was automatically fixed
3. Manual fixes needed (if any)
4. Before/After snippets for important changes

Example:
```
Found 15 style violations in app.py

✓ Fixed automatically:
  - Line too long (92 → 88 chars)
  - Missing imports sorted
  - Extra whitespace removed

⚠ Manual attention needed:
  - Line 42: Function 'process_data' missing type hints
  - Line 78: Variable 'temp' should have descriptive name
```

Always explain which style guide you're applying and why.
