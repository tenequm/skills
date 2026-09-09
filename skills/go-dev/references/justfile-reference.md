# Justfile Reference for Go Projects

`just` is a command runner (not a build system). It runs recipes defined in a `Justfile`. Latest: **1.58.0** (2026-08-03).

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
- Indent recipe bodies consistently - **either** tabs or spaces works (unlike Makefiles, which demand tabs), but the indentation must be uniform within a recipe. `set indentation` makes the project's choice explicit. The templates in this reference use spaces
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

# Run the recipe from a fixed directory, whatever the invocation dir
[working-directory('backend')]
migrate-up:
    migrate -path migrations -database "$DATABASE_URL" up

# Set an env var for this recipe only
[env('CGO_ENABLED', '0')]
build-static:
    go build -o myapp ./cmd/myapp

# Run this recipe's dependencies concurrently
[parallel]
check-all: lint test vuln

# Print a timestamp before each command
[timestamp]
slow-task:
    go test -run TestBigIntegration ./...

# Treat the body as a script for one interpreter (no per-line shells)
[script('bash', '-euo', 'pipefail', '-c')]
release:
    VERSION=$(git describe --tags --always)
    goreleaser release --clean
```

### Recipe flags with `[arg(...)]`

Turns positional parameters into real command-line options - "Require values of argument `ARG` to be passed as `--LONG` option."

```just
[arg('env', long='environment', short='e')]
deploy env='staging':
    ./scripts/deploy.sh {{ env }}
```

Invoke as `just deploy --environment prod` instead of `just deploy prod`.

## Settings

```just
set shell := ["bash", "-euo", "pipefail", "-c"]   # Shell and flags
set dotenv-load := true                            # Auto-load .env
set export := true                # Export all variables as env vars
set quiet := true                 # Suppress command echo by default
set positional-arguments := true  # Pass args as $1, $2, etc.

set dotenv-path := ".env.local"   # Load a specific env file
set dotenv-required := true       # Fail if the env file is missing
set dotenv-override := true       # .env wins over the ambient environment
set working-directory := "backend"  # Default dir for every recipe
set indentation := "    "         # Make the tabs-vs-spaces choice explicit
set minimum-version := "1.58.0"   # Error if `just` is older than this
set script-interpreter := ["bash", "-euo", "pipefail"]  # Default for [script] recipes
set fallback := true              # Search parent directories for a recipe
set no-exit-message := true       # Suppress just's own error line on failure
set dotenv-command := 'sops -d .enc.env'  # Run a command, load its output as the env file
set default-script := true        # Recipes default to script mode instead of shell mode
```

This is a catalog, not a copy-pasteable header - `dotenv-command` and `dotenv-load` are mutually exclusive, and `just` rejects a file setting both.

`set minimum-version` is worth adding to any Justfile that uses recent attributes: without it, an older `just` fails with a confusing parse error instead of a version message.

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
# Gate with the same tool that fixes - see the two-formatter footgun in SKILL.md
[group('quality')]
fmt-check:
    golangci-lint fmt --diff ./...

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

Note the direction of the dependency: git invokes the hook binary directly, so lefthook must be installed and its config must sit at the repo root or in `.config/` for any of this to fire. A `just` recipe cannot rescue a misplaced `lefthook.yml`.

Useful in a `check` recipe:

```just
[group('ci')]
hooks-check:
    lefthook validate     # config is well-formed
    lefthook dump         # print the merged effective config
```

## Importing Recipes

Split large Justfiles:

```just
# Justfile
import 'just/db.just'
import 'just/docker.just'
```

`import` splices recipes into the current namespace; `mod` keeps them namespaced, so recipes are invoked as `just db migrate-up`:

```just
mod db 'just/db.just'
mod docker
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
just --fmt             # Format the Justfile in place
just --fmt --check     # Exit non-zero if the Justfile is not formatted (CI gate)
just --jobs 4          # Cap parallelism for [parallel] dependencies
```

`just --fmt --check` is a natural addition to the `check` recipe - "Run `--fmt` in 'check' mode. Exits with 0 if justfile is formatted correctly."

## Go Tooling Traps in Recipes

Three ways a recipe that reads correctly still fails:

**`go tool` is scoped to the current directory's module.** Per `go help tool`, "additional tools may be defined in the go.mod of the current module" - so in a monorepo, a recipe invoked from the repo root fails with `go: no such tool "golangci-lint"` even though the tool is tracked in the submodule. Pin the directory on the recipe:

```just
[group('quality')]
[working-directory('services/api')]
lint:
    go tool golangci-lint run ./...
```

**A version-manager shim is a fourth install path**, alongside binary, Homebrew, and `go install`. If a tool is on PATH via mise, asdf, or similar and no version is pinned for the project, the recipe fails inside the shim rather than in the tool - `mise ERROR No version is set for shim: golangci-lint` - which reads like a Justfile bug. Pin the tool version in the version manager's config, or call an absolute path.

**`GOFLAGS=-trimpath` lets worktrees share one warm cache.** `-trimpath` "remove[s] all file system paths from the resulting executable", which also makes the build and test cache keys path-independent. Without it, every git worktree recompiles the whole dependency tree (with `-race`, expensively) because its absolute paths differ:

```just
export GOFLAGS := "-trimpath"
```

Set it at the top of the Justfile so `build`, `test`, and the linter's own package loading all share cache entries across worktrees.

## Tips

- Use `set shell := ["bash", "-euo", "pipefail", "-c"]` to catch command failures, undefined variables, and broken pipelines
- Group related recipes with `[group('name')]` for organized `--list` output
- Use `[private]` for helper recipes that shouldn't appear in `--list`
- `set dotenv-load := true` loads `.env` automatically - no separate tooling needed
- `export PATH` to include `$(go env GOPATH)/bin` so Go-installed tools are always available
- Prefer `just` over `make` for Go projects: no `.PHONY`, better variable handling, cross-platform, readable syntax

## Beyond the Basics

Surface worth knowing about, none of it needed for the Justfile above:

| Feature | What it does |
|---------|--------------|
| Agent skill | just ships its own: "A skill for agents is available in [skills/just] and may be installed manually or with `npx skills add casey/just --global`" |
| `just-lsp` / `just-mcp` | An LSP server, and an MCP adapter - "just-mcp provides a model context protocol adapter to allow LLMs to query the contents of justfiles and run recipes" |
| `[cache]` (1.54.0) | "Skip recipe invocations when a matching entry exists in the cache." Currently unstable |
| `set lists` / `set guards` / `set lazy` | Unstable settings: list-valued variables, the `?` guard sigil, lazy evaluation |
| Remote and markdown justfiles | Run recipes from a URL, or keep them in fenced code blocks inside a Markdown file |
| Global / user justfiles | A personal recipe set available from any directory |
| `--choose` / `--man` / `--dump` | Interactive recipe picker, a generated man page, and a machine-readable dump |
| `[continue(SIGNALS)]` | "Continue execution normally if a command is interrupted by any of `SIGNALS` and exits successfully. Defaults to `SIGINT`" |
| User-defined functions (1.47+) | Reusable expression-level helpers, distinct from recipes |
| `[metadata]`, `[extension]`, `[no-cd]`, `[exit-message]`, `[default]` | Further recipe attributes |
