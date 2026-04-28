# ty Reference (Beta)

Astral's Python type checker - extremely fast, written in Rust.

**GitHub**: https://github.com/astral-sh/ty | **Status**: Beta (0.0.x; current line 0.0.33)

> **Heads up**: ty is still pre-1.0 and each minor bump can change inference. Notable: 0.0.30 stopped unioning `Unknown` into most inferred attribute types; 0.0.31 introduced `--fix`; 0.0.33 prefers declared annotation over inferred RHS when assignable, removing many `cast(...)` workarounds. Pin a concrete version in `[dependency-groups]` rather than tracking `@latest`.

## Installation

```bash
# As dev dependency (recommended)
uv add --dev ty
uv run ty check

# Quick run without installing
uvx ty check

# Global install
uv tool install ty@latest

# Homebrew
brew install ty
```

## Basic Usage

```bash
ty check                    # Check current project
ty check src/ tests/        # Check specific paths
ty check --watch            # Watch mode (recheck on changes)
ty server                   # Start language server (LSP)
ty version                  # Print version
```

## Configuration in pyproject.toml

All config goes in `[tool.ty.*]` sections. Alternatively, use a standalone `ty.toml` file (omits `[tool.ty]` prefix).

### Environment Settings

```toml
[tool.ty.environment]
# Python version (default: inferred from requires-python minimum, fallback 3.14)
python-version = "3.13"

# Target platform: win32, darwin, linux, android, ios, all
python-platform = "linux"

# Path to Python environment (auto-discovered via VIRTUAL_ENV from uv run)
python = ".venv"

# Additional module resolution paths
extra-paths = ["./shared/stubs"]

# First-party module roots (priority order)
root = ["./src", "./lib"]

# Custom typeshed
typeshed = "/path/to/typeshed"
```

### Source Selection

```toml
[tool.ty.src]
# Files/dirs to include
include = ["src", "tests"]

# Files/dirs to exclude (gitignore patterns)
exclude = [
    "generated",
    "*.proto",
    "tests/fixtures/**",
    "!tests/fixtures/important.py",  # negate to re-include
]

# Respect .gitignore (default: true)
respect-ignore-files = true
```

### Rule Configuration

```toml
[tool.ty.rules]
# Set all rules to a severity
all = "error"               # or "warn" or "ignore"

# Individual rule overrides
possibly-unresolved-reference = "warn"
division-by-zero = "ignore"
unused-ignore-comment = "warn"
possibly-missing-attribute = "error"
possibly-missing-import = "error"
empty-body = "error"
```

### Analysis Settings

```toml
[tool.ty.analysis]
# Suppress unresolved-import for specific modules
allowed-unresolved-imports = ["test.**", "!test.foo"]

# Whether to respect `type: ignore` comments (default: true)
# Set false to only use `ty: ignore` comments
respect-type-ignore-comments = true
```

### Output Settings

```toml
[tool.ty.terminal]
# Output format: full, concise, github, gitlab, junit
output-format = "full"

# Exit code 1 on warnings
error-on-warning = false
```

### Per-File Overrides

```toml
[[tool.ty.overrides]]
include = ["tests/**", "**/test_*.py"]

[tool.ty.overrides.rules]
possibly-unresolved-reference = "warn"
empty-body = "ignore"

[[tool.ty.overrides]]
include = ["generated/**"]

[tool.ty.overrides.rules]
all = "ignore"
```

## CLI Flags

```bash
ty check [OPTIONS] [PATH]...

# Rule severity (repeatable, use 'all' for all rules)
--error <rule>              # Treat as error
--warn <rule>               # Treat as warning
--ignore <rule>             # Disable rule

# Environment
--python-version <ver>      # 3.7 through 3.15
--python-platform <plat>    # win32, darwin, linux, all
--python <path>             # Path to environment/interpreter
--extra-search-path <path>  # Additional module path
--typeshed <path>           # Custom typeshed

# Source
--exclude <pattern>         # Gitignore-style exclude
--force-exclude             # Enforce on direct paths too

# Config
-c <key=value>              # TOML override (e.g. 'environment.python-version="3.12"')
--config-file <path>        # Path to ty.toml
--project <dir>             # Project directory

# Output
--output-format <fmt>       # full, concise, github, gitlab, junit
--error-on-warning          # Exit 1 on warnings
--exit-zero                 # Always exit 0
-q / -v                     # Quiet / verbose

# Special
--watch, -W                 # Watch mode
--fix                       # Apply auto-fixes for diagnostics that support them (ty 0.0.31+)
--add-ignore                # Auto-add ty: ignore comments for all diagnostics
```

## Suppression Comments

```python
# Suppress specific rule
x: int = "hello"  # ty: ignore[invalid-assignment]

# Suppress all ty diagnostics on a line
x: int = "hello"  # ty: ignore

# mypy-compatible (respected by default)
x: int = "hello"  # type: ignore[assignment]
x: int = "hello"  # type: ignore
```

To disable `type: ignore` support:
```toml
[tool.ty.analysis]
respect-type-ignore-comments = false
```

## Integration with uv

Always run ty through uv to ensure proper environment discovery:

```bash
uv run ty check
```

`uv run` sets the `VIRTUAL_ENV` environment variable, which ty uses to find installed packages. Without it, ty may not resolve your project's dependencies.

### Update ty

```bash
uv lock --upgrade-package ty
```

## Key Type System Features

### Intersection Types

After isinstance checks, ty narrows to intersection types:

```python
class Serializable: ...
class Versioned: ...

def process(obj: Serializable):
    if isinstance(obj, Versioned):
        # ty: type is Serializable & Versioned
        reveal_type(obj)
```

### Gradual Types

For untyped code, ty uses `Unknown` instead of `Any` to avoid false positives:

```python
max_retries = None       # ty infers: Unknown | None (not just None)
max_retries = 3          # no error - Unknown allows this
```

### Redeclarations

ty allows reusing a symbol with a different type:

```python
def split_paths(paths: str) -> list[Path]:
    paths: list[str] = paths.split(":")  # ty allows this
    return [Path(p) for p in paths]
```

## Known Limitations

1. **Beta status** - expect bugs and missing features. Version 0.0.x, targeting stable in 2026.
2. **Incomplete typing spec** - long tail of Python typing features still being added.
3. **Third-party libraries** - Pydantic, Django, SQLAlchemy support not yet complete.
4. **No plugin system** - unlike mypy, no plugin API for custom type inference.
5. **Some rules off by default** - `possibly-unresolved-reference`, `possibly-missing-import`, `division-by-zero` produce false positives.

## Recommended Setup

```toml
# Minimal, practical config
[tool.ty.environment]
python-version = "3.13"

[tool.ty.src]
include = ["src"]

# Keep default rules - they catch real issues without noise
# Add stricter rules incrementally as ty matures
```

For the Justfile:

```just
check:
    uv run ty check
    uv run ruff check --fix && uv run ruff format
```
