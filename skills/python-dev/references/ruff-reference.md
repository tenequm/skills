# ruff Reference

Extremely fast Python linter and formatter, written in Rust. Replaces flake8, black, isort, pyupgrade.

**Docs**: https://docs.astral.sh/ruff/ | **GitHub**: https://github.com/astral-sh/ruff | **Tracked line**: ruff 0.15.x

> **Heads up**: ruff 0.14 changed the default and latest target Python to 3.14. ruff 0.15 ships the 2026 formatter style guide and adds block-level suppression comments (`# ruff: disable[rule]` / `# ruff: enable[rule]`); a number of rules also stabilised out of preview. Pinning `target-version` in `pyproject.toml` keeps formatter output reproducible across upgrades.

## Usage

```bash
# Lint
uv run ruff check .              # Check for errors
uv run ruff check --fix .        # Auto-fix
uv run ruff check --diff .       # Show what would change

# Format
uv run ruff format .             # Format code
uv run ruff format --check .     # Check without changing

# Combined (lint + format in one go)
uv run ruff check --fix && uv run ruff format

# Info
ruff rule E501                   # Explain a rule
ruff rule --all                  # List all rules
```

## pyproject.toml Configuration

### Core Settings

```toml
[tool.ruff]
target-version = "py313"
line-length = 100
indent-width = 4

exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "*.egg-info",
]
```

### Lint Rules

```toml
[tool.ruff.lint]
# Recommended: loose, helpful rules
select = [
    "E",   # pycodestyle errors - syntax issues that break code
    "F",   # pyflakes - undefined vars, unused imports (actual bugs)
    "I",   # isort - import sorting
    "UP",  # pyupgrade - use modern Python syntax
]

ignore = [
    "E501",   # line too long - formatter handles it
    "E741",   # ambiguous variable name (l, O, I) - sometimes valid
    "UP007",  # X | Y unions - Optional[X] is more readable
    "UP006",  # type vs Type - both valid
]

# Allow auto-fix for all enabled rules
fixable = ["ALL"]
unfixable = []
```

### Extended Rule Sets (add when needed)

```toml
[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "UP",  # pyupgrade
    # Add these incrementally:
    "B",   # flake8-bugbear - common bugs and design problems
    "SIM", # flake8-simplify - simplification suggestions
    "RUF", # ruff-specific rules
    "S",   # flake8-bandit - security issues
    "PTH", # flake8-use-pathlib - prefer pathlib over os.path
    "T20", # flake8-print - no print() in production code
    "ERA", # eradicate - commented-out code detection
]
```

### Per-File Ignores

```toml
[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]          # Allow unused imports
"tests/*" = ["S101"]              # Allow assert statements
"scripts/*" = ["T20"]             # Allow print() in scripts
"conftest.py" = ["F401", "F811"]  # Allow unused imports and redefined names
```

### Import Sorting

```toml
[tool.ruff.lint.isort]
known-first-party = ["my_project"]
known-third-party = ["fastapi", "pydantic"]
force-single-line = false
lines-after-imports = 2
```

### Formatter Settings

```toml
[tool.ruff.format]
quote-style = "double"        # double (default) or single
indent-style = "space"        # space (default) or tab
line-ending = "lf"            # lf, cr-lf, cr, auto, native
skip-magic-trailing-comma = false
docstring-code-format = true  # Format code in docstrings
```

## Rule Categories Reference

| Code | Name | What It Catches |
|------|------|-----------------|
| E | pycodestyle | Syntax errors, whitespace issues |
| W | pycodestyle warnings | Whitespace warnings |
| F | Pyflakes | Undefined names, unused imports, redefined names |
| I | isort | Import order and grouping |
| UP | pyupgrade | Outdated Python syntax (dict() vs {}, old-style formatting) |
| B | flake8-bugbear | Common bugs (mutable default args, except Exception) |
| SIM | flake8-simplify | Code simplification (if/else to ternary, dict.get) |
| S | flake8-bandit | Security issues (hardcoded passwords, SQL injection) |
| RUF | Ruff-specific | Ruff's own rules (unused noqa, mutable class default) |
| T20 | flake8-print | print() statements (remove for production) |
| PTH | flake8-use-pathlib | os.path vs pathlib suggestions |
| ERA | eradicate | Commented-out code |
| N | pep8-naming | Naming conventions |
| D | pydocstyle | Docstring conventions |
| ANN | flake8-annotations | Type annotation enforcement |
| C4 | flake8-comprehensions | Unnecessary list/dict/set comprehension patterns |
| PIE | flake8-pie | Miscellaneous lints |
| RET | flake8-return | Return statement issues |

## Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.12
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## CI/CD

```yaml
# GitHub Actions
- name: Lint
  run: uv run ruff check --output-format github .

- name: Format check
  run: uv run ruff format --check .
```

The `--output-format github` flag produces annotations that show inline in PRs.

## Editor Integration

Ruff has first-party VS Code extension and LSP. With uv projects, the extension discovers ruff from the project's virtual environment automatically.

## Suppression Comments

```python
x = 1  # noqa: E741       # Suppress specific rule
x = 1  # noqa              # Suppress all rules on this line

# ruff: noqa: E741         # Suppress rule for entire file (top of file)
```

Clean up stale suppressions:
```bash
uv run ruff check --extend-select RUF100  # Flag unused noqa comments
```

## Migration from Other Tools

### From black
Ruff format is compatible with black. Remove black, add ruff format config:
```toml
[tool.ruff.format]
quote-style = "double"    # black default
```

### From flake8
Map flake8 rules to ruff equivalents. Most common: `E`, `W`, `F` codes are identical.

### From isort
Ruff `I` rules replace isort. Config maps:
- `known_first_party` -> `[tool.ruff.lint.isort] known-first-party`
- `known_third_party` -> `[tool.ruff.lint.isort] known-third-party`

## Troubleshooting

```bash
ruff clean                        # Clear cache
ruff check --show-settings        # Show resolved config
ruff check --show-files           # Show files to be checked
ruff check --statistics           # Show rule violation counts
```
