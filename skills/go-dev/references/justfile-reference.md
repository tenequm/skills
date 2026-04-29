# Justfile Reference for Go Projects

`just` is a command runner (not a build system). It runs recipes defined in a `Justfile`.

## Installation

```bash
# macOS
brew install just

# Cargo
cargo install just

# Pre-built binaries
# https://github.com/casey/just/releases
```

## Core Syntax

```just
set shell := ["bash", "-euo", "pipefail", "-c"]   # Strict bash: errexit, undefined vars, pipefail
set dotenv-load := true                            # Load .env file

# Recipe with doc comment
recipe-name:
    command1
    command2

# Recipe with arguments
build target="./cmd/myapp":
    go build -o myapp {{ target }}

# Recipe with dependencies
check: fmt-check lint test
    @echo "All checks passed"
```

**Key rules:**
- Indent with **tabs** (not spaces) - unlike Makefiles, this is strictly enforced
- Each line runs in a separate shell (use `&&` or `\` to chain)
- `@` prefix suppresses command echo
- `#` comments above a recipe become its doc string

## Variables

```just
binary := "myapp"                              # Simple
version := `git describe --tags --always`      # Backtick (shell command)
export DATABASE_URL := env("DATABASE_URL", "") # Environment with default
```

## Parameters

```just
# Required parameter
migrate-create name:
    migrate create -ext sql -dir migrations -seq {{ name }}

# Default parameter
test *args="./...":
    gotestsum --format testname -- -race {{ args }}

# Variadic
run *args:
    go run ./cmd/myapp {{ args }}
```

## Dependencies

```just
# Prior dependencies (run before recipe)
coverage: test-cov
    go tool cover -html=coverage.out

# With arguments
deploy env: (build env)
    ./scripts/deploy.sh {{ env }}
```

## Recipe Attributes

```just
# Group recipes in --list output
[group('quality')]
lint:
    golangci-lint run ./...

# Hide from --list
[private]
default:
    @just --list --unsorted

# Require confirmation before running
[confirm("Drop all tables?")]
db-drop:
    migrate -path migrations -database "$DATABASE_URL" drop -f

# Platform-specific
[linux]
install:
    sudo cp myapp /usr/local/bin/

[macos]
install:
    cp myapp /usr/local/bin/

# Documented recipe (alternative to comment)
[doc("Run all tests with race detection")]
test:
    gotestsum --format testname -- -race ./...
```

## Settings

```just
set shell := ["bash", "-euo", "pipefail", "-c"]   # Shell and flags
set dotenv-load := true                            # Auto-load .env
set export := true                # Export all variables as env vars
set quiet := true                 # Suppress command echo by default
set positional-arguments := true  # Pass args as $1, $2, etc.
```

## Shebang Recipes

Run a recipe with a different interpreter:

```just
# Python script
[group('tools')]
generate-docs:
    #!/usr/bin/env python3
    import json
    with open("api.json") as f:
        spec = json.load(f)
    print(f"Found {len(spec['paths'])} endpoints")

# Bash with strict mode
[group('ci')]
release:
    #!/usr/bin/env bash
    set -euo pipefail
    VERSION=$(git describe --tags --always)
    echo "Releasing $VERSION"
    goreleaser release --clean
```

## Conditional Logic

```just
# Ternary
test-cmd := if env("CI", "") != "" { "gotestsum --format github-actions" } else { "gotestsum --format testname" }

test:
    {{ test-cmd }} -- -race ./...

# In-recipe conditionals (bash)
deploy env:
    #!/usr/bin/env bash
    if [ "{{ env }}" = "prod" ]; then
        echo "Deploying to production"
    else
        echo "Deploying to {{ env }}"
    fi
```

## Built-in Functions

| Function | Description |
|----------|-------------|
| `env("KEY", "default")` | Read environment variable |
| `home_directory()` | User home directory |
| `os()` | Operating system |
| `arch()` | CPU architecture |
| `justfile_directory()` | Directory containing the Justfile |
| `invocation_directory()` | Directory where `just` was invoked |
| `trim(s)` | Trim whitespace |
| `replace(s, from, to)` | String replacement |
| `uppercase(s)` / `lowercase(s)` | Case conversion |

## Complete Go Project Justfile

```just
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

export PATH := home_directory() + "/go/bin:" + env('PATH')

binary := "myapp"

[private]
default:
    @just --list --unsorted

# ── Code Quality ──────────────────────────────────────────

# Format all Go code
[group('quality')]
fmt:
    golangci-lint fmt ./...

# Check formatting (CI-safe, non-zero exit on diff)
[group('quality')]
fmt-check:
    gofumpt -d . 2>&1 | (! grep -q '^') || (gofumpt -l . && exit 1)

# Run linter
[group('quality')]
lint:
    golangci-lint run ./...

# Run linter with auto-fix
[group('quality')]
lint-fix:
    golangci-lint run --fix ./...

# Run vulnerability check
[group('quality')]
vuln:
    govulncheck ./...

# ── Testing ───────────────────────────────────────────────

# Run all tests with race detection
[group('test')]
test *args="./...":
    gotestsum --format testname -- -race {{ args }}

# Run tests with coverage
[group('test')]
test-cov:
    gotestsum --format testname -- -race -coverprofile=coverage.out -covermode=atomic ./...
    go tool cover -func=coverage.out

# Open coverage report in browser
[group('test')]
coverage: test-cov
    go tool cover -html=coverage.out

# Run integration tests
[group('test')]
test-integration:
    gotestsum --format testname -- -race -tags=integration ./...

# Watch tests during development
[group('test')]
test-watch:
    gotestsum --watch --watch-clear --format testname

# Run benchmarks
[group('test')]
bench:
    go test -bench=. -benchmem ./...

# ── Build ─────────────────────────────────────────────────

# Build the binary
[group('build')]
build:
    go build -o {{ binary }} ./cmd/{{ binary }}

# Build optimized release binary
[group('build')]
build-release:
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o {{ binary }} ./cmd/{{ binary }}

# ── Dependencies ──────────────────────────────────────────

# Tidy and verify modules
[group('deps')]
tidy:
    go mod tidy
    go mod verify

# Run code generators
[group('deps')]
generate:
    go generate ./...

# Update all dependencies
[group('deps')]
update-deps:
    go get -u ./...
    go mod tidy

# ── Database ──────────────────────────────────────────────

# Apply all pending migrations
[group('db')]
migrate-up:
    migrate -path migrations -database "$DATABASE_URL" up

# Revert last migration
[group('db')]
migrate-down:
    migrate -path migrations -database "$DATABASE_URL" down 1

# Create a new migration
[group('db')]
migrate-create name:
    migrate create -ext sql -dir migrations -seq {{ name }}

# Show migration version
[group('db')]
migrate-version:
    migrate -path migrations -database "$DATABASE_URL" version

# ── CI ────────────────────────────────────────────────────

# Full CI gate
[group('ci')]
check: fmt-check lint test
    @echo "All checks passed"

# CI test output with JUnit XML
[group('ci')]
test-ci:
    gotestsum --format github-actions \
      --junitfile unit-tests.xml \
      --junitfile-hide-empty-pkg \
      -- -race -count=1 ./...

# Clean build artifacts
[group('ci')]
clean:
    go clean
    rm -f {{ binary }} coverage.out unit-tests.xml
```

## Lefthook Integration

Lefthook can call `just` recipes in hooks:

```yaml
# lefthook.yml
pre-commit:
  commands:
    fmt:
      run: just fmt
    lint:
      glob: "*.go"
      run: just lint

pre-push:
  commands:
    check:
      run: just check
```

## Importing Recipes

Split large Justfiles:

```just
# Justfile
import 'just/db.just'
import 'just/docker.just'
```

```just
# just/db.just
[group('db')]
migrate-up:
    migrate -path migrations -database "$DATABASE_URL" up
```

## Running

```bash
just                   # Run default recipe (list all)
just test              # Run specific recipe
just test ./pkg/...    # Recipe with argument
just --list            # List all recipes
just --list --unsorted # List in file order
just --summary         # One-line summary of each recipe
just --evaluate        # Show all variable values
just --dry-run test    # Show what would run
just -f path/Justfile  # Use specific Justfile
```

## Tips

- Use `set shell := ["bash", "-euo", "pipefail", "-c"]` to catch command failures, undefined variables, and broken pipelines
- Group related recipes with `[group('name')]` for organized `--list` output
- Use `[private]` for helper recipes that shouldn't appear in `--list`
- `set dotenv-load := true` loads `.env` automatically - no separate tooling needed
- `export PATH` to include `$(go env GOPATH)/bin` so Go-installed tools are always available
- Prefer `just` over `make` for Go projects: no `.PHONY`, better variable handling, cross-platform, readable syntax
