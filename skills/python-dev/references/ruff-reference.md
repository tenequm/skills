# ruff Reference

Extremely fast Python linter and formatter, written in Rust. Replaces flake8, black, isort, pyupgrade.

**Docs**: https://docs.astral.sh/ruff/ | **GitHub**: https://github.com/astral-sh/ruff | **Tracked line**: ruff 0.16.x

> **Heads up**: ruff **0.16 is the big one** - the default rule set went from 59 to 413 rules, 18 opinionated `E`/`F` rules were dropped from that default set, and `ruff format` now formats Python blocks inside Markdown by default. A `select` list replaces the defaults, so prefer `extend-select`/`ignore`. 0.16 also adds line-level `ruff: ignore` comments and `--add-ignore`, and `format --check` gained the linter's `--output-format github`. Earlier: 0.14 moved the default target Python to 3.14; 0.15 shipped the 2026 formatter style guide and block-level suppressions. Pinning `target-version` in `pyproject.toml` keeps formatter output reproducible across upgrades.

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
# Ruff 0.16 enables 413 rules by default (up from 59), and dropped 18 opinionated
# E/F rules from that set. Writing a `select` list REPLACES the default set, so
# `select = ["E","F","I","UP"]` now yields a weaker linter than no config at all.
# Start from the defaults and narrow with `ignore`, or widen with `extend-select`.
ignore = [
    "E501",   # line too long - formatter handles it
    "UP007",  # X | Y unions - Optional[X] is more readable
    "UP006",  # type vs Type - both valid
]

# Allow auto-fix for all enabled rules
fixable = ["ALL"]
unfixable = []
```

### Extended Rule Sets (add when needed)

Use `extend-select`, not `select` - it adds to ruff 0.16's default set instead of replacing it.
Some of these are already on by default (a mutable-default arg raises `B006` with no config at
all), while `S`, `T20` and `ERA` are not.

```toml
[tool.ruff.lint]
extend-select = [
    "B",   # flake8-bugbear - common bugs and design problems (partly default in 0.16)
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

## Git Hook Integration

```yaml
# lefthook.yml
pre-commit:
  piped: true
  jobs:
    - name: ruff-check
      glob: "*.{py,pyi,ipynb}"
      run: uv run ruff check --force-exclude --fix {staged_files}
      stage_fixed: true
    - name: ruff-format
      glob: "*.{py,pyi,ipynb}"
      run: uv run ruff format --force-exclude {staged_files}
      stage_fixed: true
```

`--force-exclude` is required whenever paths are passed explicitly, or `[tool.ruff] exclude`
is ignored for them. Lint before format: `--fix` output may need reformatting.

On pre-commit instead, the current hook ids are `ruff-check` and `ruff-format` - bare `ruff`
is a legacy alias - and `rev` must be kept in step with the ruff pin in `pyproject.toml`:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.16.6
    hooks:
      - id: ruff-check
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
