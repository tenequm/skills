# Justfile Reference

`just` is a command runner for project-specific recipes. Replaces Makefile for non-build tasks.

**Manual**: https://just.systems/man/en/ | **GitHub**: https://github.com/casey/just

## Installation

```bash
brew install just       # macOS
cargo install just      # Via Rust
```

## Core Syntax

```just
# This comment shows in `just --list`
recipe-name:
    command1
    command2
```

Each line runs in a **separate shell** by default. Use `&&` to chain commands in one shell.

Suppress command echoing with `@`:

```just
@hello:
    echo "Hello"
# Output: Hello (not: echo "Hello" \n Hello)
```

## Variables

```just
# Simple assignment
version := "1.0.0"

# Backtick (evaluated at parse time)
git_hash := `git rev-parse --short HEAD`

# Environment variable with default
port := env("PORT", "8000")

# Use in recipes
build:
    @echo "Building {{version}} ({{git_hash}})"
```

## Parameters

```just
# Required
build target:
    @echo "Building {{target}}"

# With default
test suite="unit":
    @echo "Running {{suite}} tests"

# Variadic (one or more)
backup +FILES:
    scp {{FILES}} server:

# Variadic (zero or more)
commit MESSAGE *FLAGS:
    git commit {{FLAGS}} -m "{{MESSAGE}}"

# Exported as env var
serve $PORT="8000":
    python -m http.server $PORT
```

## Dependencies

```just
# Run before (prior dependency)
build:
    @echo "Building..."

test: build
    @echo "Testing..."

# Run after (subsequent dependency)
deploy: build && notify cleanup
    @echo "Deploying..."

# With arguments
default: (test "unit")

test suite:
    @echo "Running {{suite}} tests"
```

## Settings

```just
# Load .env file
set dotenv-load

# Export all variables as env vars
set export

# Suppress command echoing globally
set quiet

# Use bash
set shell := ["bash", "-uc"]
```

## Recipe Attributes

```just
# Group in `just --list`
[group('testing')]
test:
    uv run pytest

[group('quality')]
check:
    uv run ty check

# Require confirmation
[confirm("Reset database?")]
db-reset:
    dropdb myapp && createdb myapp

# Platform-specific
[linux]
install:
    sudo apt install libfoo-dev

[macos]
install:
    brew install libfoo

# Private (hidden from list)
[private]
_helper:
    echo "internal"

# Documentation override
[doc("Run type checking and linting")]
check:
    uv run ty check
    uv run ruff check --fix && uv run ruff format
```

## Shebang Recipes

For multi-line scripts in any language:

```just
analyze:
    #!/usr/bin/env python3
    import json
    with open("data.json") as f:
        data = json.load(f)
    print(f"Found {len(data)} records")

# With uv inline script deps
check-api:
    #!/usr/bin/env -S uv run --script
    # /// script
    # dependencies = ["httpx"]
    # ///
    import httpx
    r = httpx.get("https://api.example.com/health")
    print(f"Status: {r.status_code}")

# Bash with strict mode
deploy:
    #!/usr/bin/env -S bash -euo pipefail
    echo "Deploying..."
    git push origin main
```

Use `#!/usr/bin/env -S` with `-S` flag when passing arguments to the interpreter.

## Conditional Logic

```just
# Conditional assignment
os := if os() == "macos" { "darwin" } else { "linux" }

# Conditional in recipe
test:
    uv run pytest {{ if env("CI", "") != "" { "--no-header -q" } else { "-v" } }}
```

## Built-in Functions

| Function | Returns |
|----------|---------|
| `os()` | "linux", "macos", "windows" |
| `arch()` | "x86_64", "aarch64" |
| `env("VAR", "default")` | Environment variable |
| `justfile()` | Path to current Justfile |
| `justfile_directory()` | Directory of Justfile |
| `invocation_directory()` | Where `just` was called from |
| `uuid()` | Random UUID |

## Python Project Justfile Template

```just
set dotenv-load
set quiet

# Run type checking and linting
[group('quality')]
check:
    uv run ty check
    uv run ruff check --fix && uv run ruff format

# Run tests
[group('testing')]
test *ARGS:
    uv run pytest {{ARGS}}

# Run tests with coverage
[group('testing')]
test-cov:
    uv run pytest --cov=src --cov-report=term-missing

# Auto-fix and format
[group('quality')]
fix:
    uv run ruff check --fix
    uv run ruff format

# Install all dependencies
[group('dev')]
install:
    uv sync --all-groups

# Update all dependencies
[group('dev')]
update:
    uv lock --upgrade
    uv sync --all-groups

# Build the package
[group('build')]
build:
    uv build

# Clean build artifacts
[group('dev')]
clean:
    rm -rf dist/ build/ .pytest_cache/ .ruff_cache/ htmlcov/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Open Python REPL
[group('dev')]
repl:
    uv run python
```

## Running

```bash
just              # Default recipe (first one, or [default])
just test         # Named recipe
just test -x -v   # Pass args through
just --list       # List all recipes (grouped)
just -l           # Short form
just --choose     # Interactive (needs fzf)
just --summary    # One-line summary
just -n test      # Dry run (show what would run)
```
