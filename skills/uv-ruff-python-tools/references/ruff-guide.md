# Ruff: Complete Guide

Ruff is an extremely fast Python linter and code formatter written in Rust. It's 10-100x faster than existing linters and formatters, combining functionality from Flake8, Black, isort, and more into a single tool.

## Table of Contents

1. [Installation](#installation)
2. [Linting](#linting)
3. [Formatting](#formatting)
4. [Configuration](#configuration)
5. [Rule Selection](#rule-selection)
6. [Error Suppression](#error-suppression)
7. [Editor Integration](#editor-integration)
8. [CI/CD Integration](#cicd-integration)
9. [Migration Guide](#migration-guide)

## Installation

### With UV (Recommended)

```bash
# Install as a tool
uv tool install ruff

# Or add to project
uv add --dev ruff
```

### With pip

```bash
pip install ruff
```

### With Homebrew

```bash
brew install ruff
```

### With conda

```bash
conda install -c conda-forge ruff
```

### Verify Installation

```bash
ruff version
# Output: ruff 0.12.8
```

## Linting

### Basic Linting

```bash
# Check current directory
ruff check .

# Check specific files
ruff check src/main.py tests/

# Check and auto-fix
ruff check --fix .

# Preview changes without applying
ruff check --diff .

# Show fixes that would be applied
ruff check --show-fixes .
```

### Watch Mode

```bash
# Continuously check for errors
ruff check --watch .
```

### Output Formats

```bash
# Default (human-readable)
ruff check .

# JSON format
ruff check --output-format json .

# GitHub Actions format
ruff check --output-format github .

# GitLab format
ruff check --output-format gitlab .

# JUnit XML format
ruff check --output-format junit .
```

### Unsafe Fixes

```bash
# Include unsafe fixes
ruff check --fix --unsafe-fixes .

# Fix only (don't report remaining violations)
ruff check --fix-only .
```

### Statistics and Debugging

```bash
# Show statistics for each rule
ruff check --statistics .

# Show files that will be checked
ruff check --show-files .

# Show configuration being used
ruff check --show-settings .
```

## Formatting

### Basic Formatting

```bash
# Format current directory
ruff format .

# Format specific files
ruff format src/main.py

# Check formatting without changes
ruff format --check .

# Show diff of changes
ruff format --diff .
```

### Format and Lint Together

```bash
# Recommended workflow
ruff check --fix . && ruff format .
```

### Format Options

```bash
# Use preview features
ruff format --preview .

# Specific target Python version
ruff format --target-version py312 .
```

## Configuration

### Configuration Files

Ruff looks for configuration in (in order of precedence):
1. `.ruff.toml`
2. `ruff.toml`
3. `pyproject.toml`

### Basic Configuration

**pyproject.toml:**
```toml
[tool.ruff]
# Set line length
line-length = 88
indent-width = 4

# Set Python version
target-version = "py311"

# Exclude directories
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "*.egg-info",
]

[tool.ruff.lint]
# Enable specific rules
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "UP",  # pyupgrade
    "C4",  # flake8-comprehensions
]

# Ignore specific rules
ignore = [
    "E501",  # line too long (handled by formatter)
]

# Allow auto-fixing
fixable = ["ALL"]
unfixable = []

# Allow unused variables prefixed with underscore
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.format]
# Use double quotes
quote-style = "double"

# Use spaces for indentation
indent-style = "space"

# Respect magic trailing commas
skip-magic-trailing-comma = false

# Auto-detect line endings
line-ending = "auto"

# Format code in docstrings
docstring-code-format = true
docstring-code-line-length = 72
```

### Per-File Configuration

```toml
[tool.ruff.lint.per-file-ignores]
# Ignore unused imports in __init__.py
"__init__.py" = ["F401"]

# Ignore assert statements in tests
"tests/*" = ["S101"]

# Ignore print statements in scripts
"scripts/*" = ["T201"]

# Ignore import order in migrations
"migrations/*" = ["I"]
```

### Import Sorting (isort)

```toml
[tool.ruff.lint.isort]
# Known first-party packages
known-first-party = ["myproject"]

# Known third-party packages
known-third-party = ["django", "requests"]

# Section order
section-order = [
    "future",
    "standard-library",
    "third-party",
    "first-party",
    "local-folder"
]

# Combine as imports
combine-as-imports = true

# Split on trailing comma
split-on-trailing-comma = true
```

### Docstring Configuration

```toml
[tool.ruff.lint.pydocstyle]
# Use Google-style docstrings
convention = "google"  # or "numpy", "pep257"
```

## Rule Selection

### Available Rule Sets

| Code | Name | Description |
|------|------|-------------|
| E | pycodestyle errors | PEP 8 error codes |
| W | pycodestyle warnings | PEP 8 warning codes |
| F | Pyflakes | Logical errors |
| I | isort | Import sorting |
| N | pep8-naming | Naming conventions |
| D | pydocstyle | Docstring style |
| UP | pyupgrade | Modern Python syntax |
| B | flake8-bugbear | Common bugs |
| A | flake8-builtins | Builtin shadowing |
| C4 | flake8-comprehensions | List/dict/set comprehensions |
| T20 | flake8-print | Print statements |
| PT | flake8-pytest-style | Pytest style |
| S | flake8-bandit | Security issues |
| Q | flake8-quotes | Quote style |
| RUF | Ruff-specific | Ruff custom rules |

### Selecting Rules

```bash
# Enable specific rule set
ruff check --select E,W,F .

# Enable all rules
ruff check --select ALL .

# Extend default rules
ruff check --extend-select B,I .

# Ignore specific rules
ruff check --ignore E501,W503 .
```

### Configuration

```toml
[tool.ruff.lint]
# Start with Flake8 defaults and add more
select = ["E", "F"]
extend-select = ["B", "I", "N"]

# Ignore specific rules
ignore = ["E501"]
extend-ignore = ["W503"]

# Make specific rules fixable
fixable = ["I", "F401"]

# Make specific rules non-fixable
unfixable = ["B"]
```

### Popular Rule Combinations

**Minimal (Default):**
```toml
select = ["E4", "E7", "E9", "F"]
```

**Standard:**
```toml
select = ["E", "W", "F", "I"]
```

**Strict:**
```toml
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "D",   # pydocstyle
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "S",   # flake8-bandit
    "T20", # flake8-print
    "PT",  # flake8-pytest-style
]
```

## Error Suppression

### Inline Comments

```python
# Ignore specific rule on a line
import os  # noqa: F401

# Ignore multiple rules
import sys, os  # noqa: F401, E401

# Ignore all rules on a line
very_long_variable_name = "value"  # noqa

# Ignore for next line
# noqa: E501
very_long_line = "This is a very long line that exceeds the limit"
```

### File-Level Suppression

```python
# At top of file
# ruff: noqa: F401, E402

import os
import sys
```

### Auto-Add noqa Comments

```bash
# Automatically add noqa comments
ruff check --add-noqa .
```

### Type-Aware Suppression

```python
# Type checkers only
import TYPE_CHECKING  # type: ignore

# Ruff specific
from typing import Optional  # ruff: noqa: UP007
```

## Editor Integration

### VS Code

Install the [Ruff VS Code extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff):

**.vscode/settings.json:**
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "ruff.lint.args": ["--config=pyproject.toml"],
  "ruff.format.args": ["--config=pyproject.toml"]
}
```

### PyCharm/IntelliJ

1. Install Ruff via system package manager
2. Configure as external tool:
   - File → Settings → Tools → External Tools
   - Add Ruff with appropriate arguments

### Vim/Neovim

**With ALE:**
```vim
let g:ale_linters = {'python': ['ruff']}
let g:ale_fixers = {'python': ['ruff']}
```

**With nvim-lspconfig:**
```lua
require('lspconfig').ruff_lsp.setup{}
```

### Emacs

```elisp
;; With flycheck
(require 'flycheck)
(flycheck-define-checker python-ruff
  "A Python checker using ruff."
  :command ("ruff" "check" "--output-format" "text" source)
  :error-patterns
  ((error line-start (file-name) ":" line ":" column ": " (message) line-end))
  :modes python-mode)
(add-to-list 'flycheck-checkers 'python-ruff)
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Lint with Ruff

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Install dependencies
        run: uv sync

      - name: Lint with Ruff
        run: uv run ruff check .

      - name: Format check with Ruff
        run: uv run ruff format --check .
```

**Using Ruff Action:**
```yaml
- uses: chartboost/ruff-action@v1
  with:
    args: check --output-format github
```

### GitLab CI

```yaml
ruff:
  image: python:3.12
  before_script:
    - pip install ruff
  script:
    - ruff check .
    - ruff format --check .
```

### Pre-commit Hooks

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.12.8
    hooks:
      # Run the linter
      - id: ruff
        args: [--fix]
      # Run the formatter
      - id: ruff-format
```

Install:
```bash
pip install pre-commit
pre-commit install
```

### Docker

```dockerfile
FROM python:3.12-slim

# Install Ruff
RUN pip install ruff

# Copy code
COPY . /app
WORKDIR /app

# Run Ruff
RUN ruff check .
RUN ruff format --check .
```

## Migration Guide

### From Flake8

```bash
# Flake8 configuration
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
```

```toml
# Equivalent Ruff configuration
[tool.ruff]
line-length = 88

[tool.ruff.lint]
ignore = ["E203", "W503"]
exclude = [".git", "__pycache__", "build", "dist"]
```

### From Black

Ruff format is designed to be a drop-in replacement for Black:

```bash
# Replace
black .

# With
ruff format .
```

Configuration is compatible:
```toml
[tool.black]
line-length = 88
target-version = ["py311"]

# Becomes
[tool.ruff]
line-length = 88
target-version = "py311"
```

### From isort

```bash
# Replace
isort .

# With
ruff check --select I --fix .
# Or
ruff format .  # Includes import sorting
```

Configuration:
```toml
[tool.isort]
profile = "black"
known_first_party = ["myproject"]

# Becomes
[tool.ruff.lint.isort]
known-first-party = ["myproject"]
```

### From pyupgrade

```bash
# Replace
pyupgrade --py311-plus **/*.py

# With
ruff check --select UP --fix .
```

### Complete Migration

**Before:**
```bash
# Multiple tools
isort .
black .
flake8 .
pyupgrade --py311-plus **/*.py
```

**After:**
```bash
# Single command
ruff check --fix . && ruff format .
```

**Configuration consolidation:**
```toml
# pyproject.toml - All in one place
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
```

## Common Rules Explained

### E/W (pycodestyle)

```python
# E501: Line too long
very_long_line = "This line exceeds 88 characters and will be flagged by E501"

# E401: Multiple imports on one line
import os, sys  # Bad

# E402: Module level import not at top
def foo():
    pass
import os  # Bad

# W503: Line break before binary operator
result = (value
          + other_value)  # Warning in older style guides
```

### F (Pyflakes)

```python
# F401: Imported but unused
import os  # Not used anywhere

# F841: Local variable assigned but never used
def foo():
    x = 10  # Never used

# F821: Undefined name
print(undefined_var)  # NameError at runtime
```

### I (isort)

```python
# Incorrect import order
from myproject import foo
import os
import sys
from third_party import bar

# Correct
import os
import sys

from third_party import bar

from myproject import foo
```

### UP (pyupgrade)

```python
# UP006: Use list instead of List from typing
from typing import List  # Old
def foo() -> List[int]:  # Old
    pass

# New
def foo() -> list[int]:  # New (Python 3.9+)
    pass

# UP032: Use f-string instead of format
"{} {}".format(a, b)  # Old
f"{a} {b}"  # New
```

### B (flake8-bugbear)

```python
# B006: Mutable default argument
def foo(items=[]):  # Bad - mutable default
    items.append(1)
    return items

# B008: Do not perform function call in default argument
def foo(timestamp=datetime.now()):  # Bad
    pass

# B011: Do not use assert False
assert False, "This should not happen"  # Use raise instead
```

## Advanced Features

### Rule Explainer

```bash
# Get detailed explanation of a rule
ruff rule E501

# List all rules
ruff rule --all

# Search for rules
ruff rule --filter "import"
```

### Custom Configuration per Directory

```toml
# Root pyproject.toml
[tool.ruff]
line-length = 88

# tests/ can have different config
```

Create `tests/pyproject.toml`:
```toml
[tool.ruff]
extend = "../pyproject.toml"  # Inherit root config
line-length = 120  # Override for tests
```

### Preview Mode

```bash
# Enable preview features
ruff check --preview .
ruff format --preview .
```

```toml
[tool.ruff]
preview = true
```

### Unsafe Fixes

Some fixes are marked as "unsafe" because they might change semantics:

```bash
# Include unsafe fixes
ruff check --fix --unsafe-fixes .
```

### Cache Management

```bash
# Clear Ruff cache
ruff clean

# Disable cache
ruff check --no-cache .
```

## Performance Tips

1. **Use --no-cache for CI**: Ensures fresh analysis
2. **Run in parallel**: Ruff already parallelizes internally
3. **Use specific selects**: Only enable rules you need
4. **Exclude large directories**: Skip `node_modules`, `venv`, etc.
5. **Use fix in CI**: Auto-fix what you can, then check remaining

## Troubleshooting

### Ruff Not Found

```bash
# Check installation
which ruff
ruff version

# Reinstall
uv tool uninstall ruff
uv tool install ruff
```

### Configuration Not Loaded

```bash
# Show active configuration
ruff check --show-settings .

# Use specific config file
ruff check --config path/to/pyproject.toml .
```

### Rules Not Working

```bash
# Check which rules are enabled
ruff rule --all | grep E501

# Explain specific rule
ruff rule E501
```

### Performance Issues

```bash
# Profile ruff execution
time ruff check .

# Check file discovery
ruff check --show-files .

# Clear cache
ruff clean
```

## Best Practices

1. **Start with defaults**, add rules gradually
2. **Use format + lint together** in your workflow
3. **Configure in pyproject.toml** for centralized settings
4. **Use per-file-ignores** sparingly
5. **Enable auto-fix in pre-commit** hooks
6. **Run in CI/CD** to enforce standards
7. **Use --diff in CI** to show what would change
8. **Document rule exceptions** with inline comments
9. **Keep Ruff updated** for new features and fixes
10. **Use editor integration** for real-time feedback

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff GitHub](https://github.com/astral-sh/ruff)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Ruff Settings](https://docs.astral.sh/ruff/settings/)
- [Ruff VS Code Extension](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
