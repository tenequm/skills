---
name: go-dev
description: Opinionated Go setup with golangci-lint v2, gofumpt, gotestsum, golang-migrate, and just. Use when starting a Go project, configuring lint, format, test, coverage or CI, writing a Justfile, wiring migrations, or leaving a Makefile workflow.
metadata:
  version: "0.3.1"
  categories: "development"
  topics: "go, golangci-lint, gofumpt, testing, just"
  upstream: "go@1.27.0, golangci-lint@v2.13.1, gofumpt@v0.11.0, gotestsum@v1.13.0, golang-migrate@v4.19.1, just@1.58.0, lefthook@v2.1.11"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/go-dev
    emoji: "🐹"
    envVars:
      - name: DATABASE_URL
        required: false
        description: Connection string used by the Justfile migration recipes (golang-migrate)
---

# Go Development Stack

Opinionated, modern Go development setup. One tool per concern, zero overlap.

## When to Use

- Starting a new Go project from scratch
- Adding linting, formatting, or testing infrastructure
- Setting up CI/CD for a Go service or library
- Creating a Justfile to replace a Makefile
- Adding database migration tooling
- Migrating from scattered gofmt/govet/staticcheck invocations to a unified setup

## The Stack

| Tool | Version | Role | Replaces |
|------|---------|------|----------|
| **Go** | 1.27+ | Language, toolchain, `go mod`, `go fix` | - |
| **golangci-lint** | v2.13+ | Meta-linter (100+ linters + formatters + `fmt` command) | gofmt, govet, staticcheck, errcheck run separately |
| **gofumpt** | v0.11+ | Strict formatter (superset of gofmt, 19 default rules) | gofmt |
| **gotestsum** | v1.13+ | Test runner with readable output, watch mode, JUnit XML | Raw `go test` |
| **just** | 1.58+ | Task runner | Makefile |
| **golang-migrate** | v4.19+ | DB migrations (CLI + library + `embed.FS`) | Manual SQL scripts |
| **lefthook** | v2.1+ | Git hooks (single binary, parallel) | pre-commit (Python) |

**Version floors are load-bearing.** golangci-lint "supports Go versions lower or equal to the Go version used to compile it" - a pin older than your Go toolchain fails outright. Go 1.27 support landed in golangci-lint v2.13.0, so `v2.13` is the floor for a Go 1.27 project.

## Quick Start: New Project

```bash
# 1. Create module
mkdir myapp && cd myapp
go mod init github.com/yourorg/myapp

# 2. Scaffold directories
mkdir -p cmd/myapp internal migrations

# 3. Track tools in go.mod (Go 1.24+ tool directive). Pin versions - never @latest,
#    which recompiles the tool on every CI run and drifts between machines.
go get -tool github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1
go get -tool mvdan.cc/gofumpt@v0.11.0
go get -tool gotest.tools/gotestsum@v1.13.0

# golang-migrate needs a build tag, so install it directly
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@v4.19.1

# 4. Create config files (templates below)
# 5. Run: just check
```

**`go get -tool` tracks; `go tool` runs.** The tool directive records the dependency in `go.mod` but puts nothing on your PATH. Either invoke through the toolchain - `go tool golangci-lint run ./...`, `go tool gotestsum --format testname` - or `go install tool` once to populate `$(go env GOPATH)/bin`. The Justfile below calls the bare binaries, so it assumes the `go install tool` route (or a system install via Homebrew).

Two Go-command behaviours worth knowing before the first commit:

- `go mod init` under a 1.N toolchain writes `go 1.(N-1).0`, not `1.N` - "Running `go mod init` using a toolchain of version `1.N.X` will create a `go.mod` file specifying the Go version `go 1.(N-1).0`." Bump the directive deliberately if you want 1.N language features.
- Pin the toolchain for reproducibility with a `toolchain go1.27.0` line in `go.mod` (or `GOTOOLCHAIN=go1.27.0` in CI). This line is also what `govulncheck` compares stdlib advisories against - see Footguns below.

## .golangci.yml

```yaml
version: "2"

run:
  timeout: 5m

linters:
  default: standard
  enable:
    - bodyclose
    - copyloopvar
    - dupl
    - durationcheck
    - err113
    - errname
    - errorlint
    - exhaustive
    - exptostd
    - fatcontext
    - goconst
    - gocritic
    - gosec
    - intrange
    - misspell
    - modernize
    - musttag
    - nakedret
    - nestif
    - nilerr
    - noctx
    - nolintlint
    - nonamedreturns
    - perfsprint
    - prealloc
    - revive
    - sqlclosecheck
    - testifylint
    - thelper
    - unconvert
    - unparam
    - usestdlibvars
    - usetesting
    - wastedassign
    - whitespace
    - wrapcheck
  settings:
    govet:
      enable:
        - shadow
    gocritic:
      enabled-checks:
        - nestingReduce
    revive:
      enable-all-rules: true
    errcheck:
      check-type-assertions: true
  exclusions:
    generated: strict
    presets:
      - comments
      - std-error-handling
      - common-false-positives
    rules:
      - path: _test\.go
        linters:
          - gocyclo
          - errcheck
          - dupl
          - gosec
          - wrapcheck

formatters:
  enable:
    - gofumpt
    - goimports
  settings:
    gofumpt:
      extra-rules: true
  exclusions:
    generated: strict
    paths:
      - vendor/

output:
  formats:
    text:
      path: stdout
      print-linter-name: true
      colors: true
  sort-order:
    - linter
    - file
  show-stats: true
```

## Justfile

```just
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

binary := "myapp"

[private]
default:
    @just --list --unsorted

# ── Code Quality ──────────────────────────────────────────

# Format all Go code
[group('quality')]
fmt:
    golangci-lint fmt ./...

# Check formatting without modifying (CI-safe)
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

# ── CI ────────────────────────────────────────────────────

# Full CI gate (format check + lint + test)
[group('ci')]
check: fmt-check lint test
    @echo "All checks passed"

# Clean build artifacts
[group('ci')]
clean:
    go clean
    rm -f {{ binary }} coverage.out
```

## Lefthook Config

Lefthook is preferred over pre-commit for Go projects - it is a single Go binary, runs hooks in parallel, and needs no Python.

```bash
go install github.com/evilmartians/lefthook/v2@v2.1.11
lefthook install
```

```yaml
# lefthook.yml
pre-commit:
  piped: true   # run sequentially: fmt -> lint -> mod-tidy (each may modify staged files)
  commands:
    fmt:
      glob: "*.go"
      run: gofumpt -w {staged_files}
      stage_fixed: true
    lint:
      glob: "*.go"
      run: golangci-lint run --fix {staged_files}
      stage_fixed: true
    mod-tidy:
      glob: "*.{go,mod,sum}"
      run: go mod tidy

pre-push:
  commands:
    test:
      run: go test -race ./...
```

`jobs:` is lefthook v2's newer primitive and supersedes the `commands:`/`scripts:` split - "Jobs provide a flexible way to define tasks, supporting both commands and scripts. Jobs can be grouped for advanced flow control." The `commands:` form above still works; reach for `jobs:` when you need grouping, nested control flow, or a mix of inline commands and scripts in one hook.

Two more worth wiring:

- `lefthook validate` in CI catches a malformed `lefthook.yml` before it silently disables hooks; `lefthook dump` prints the merged effective config when a hook does not behave as written.
- A gitignored `lefthook-local.yml` lets a developer add or skip jobs without imposing it on teammates - "This is useful when you want to use lefthook locally without imposing it on your teammates."

## Project Structure

```
myapp/
  cmd/
    myapp/
      main.go              # Wire deps, call Run(), nothing else
  internal/
    user/                  # Domain logic, one package per domain
      user.go
      user_test.go
      repository.go
    transport/             # HTTP/gRPC handlers
    storage/               # Database layer
  migrations/
    000001_create_users.up.sql
    000001_create_users.down.sql
  testdata/                # Test fixtures (ignored by go toolchain)
  .golangci.yml
  lefthook.yml
  Justfile
  go.mod
  go.sum
  Dockerfile
```

**Guidelines:**
- `cmd/` - one directory per binary, keep `main.go` thin (~50 lines max)
- `internal/` - all business logic goes here (compiler-enforced, cannot be imported externally)
- `pkg/` - only add when another repo actually imports it today, not "maybe someday"
- `testdata/` - test fixtures, golden files, fuzz corpus
- `migrations/` - SQL migration files (timestamp or sequential versioned)

## Daily Workflow

```bash
just fmt          # Format code
just lint         # Run linter
just test         # Run tests with race detection
just check        # Full CI gate (fmt-check + lint + test)
just test-watch   # Watch mode during development
just generate     # Run go generate
just tidy         # go mod tidy + verify
```

`go fix` is the toolchain-native complement to the `modernize` linter: Go 1.26 rebuilt it as a codebase modernizer - "The venerable `go fix` command has been completely revamped and is now the home of Go's *modernizers*. It provides a dependable, push-button way to update Go code bases to the latest idioms and core library APIs." Run `go fix ./...` after a toolchain bump, before the linter has to complain.

## Footguns

Six failure modes that cost real debugging time, none of which produce an obvious error message.

**Config placement is load-bearing.** `.golangci.yml` must sit at the repo root: golangci-lint searches the working dir and its parents, and editor Go plugins auto-detect only a root `.golangci.*`, so filing it under `.github/` costs in-IDE linting even if you pass `--config`. lefthook auto-discovers only the repo root or `.config/` - move `lefthook.yml` anywhere else and commits silently stop running hooks, because git invokes the hook directly and no task-runner recipe can intercept that.

**lefthook is dormant until installed.** The binary being absent from PATH, or `lefthook install` never having run, both present as "hooks just don't fire" with no warning. Pin lefthook as a repo tool and make `lefthook install` part of onboarding.

**A stale lint cache invents issues.** golangci-lint can report failures in files that no longer exist on disk - typically after a branch switch or a deleted worktree. If issue counts look impossible, run `golangci-lint cache clean` before debugging the code. When several worktrees share a checkout, give each its own cache with `GOLANGCI_LINT_CACHE=<worktree>/.golangci-cache`.

**Don't run two formatters against one gate.** Standalone `gofumpt -w` and `golangci-lint fmt` do not always agree on the same file, so a repo that fixes with one and gates with the other fails CI on code it just formatted. Pick one as both fixer and gate - the Justfile above uses `golangci-lint fmt` for both.

**A pinned linter older than your Go toolchain fails outright.** This is the same trap as the version floor above, and it usually surfaces first as a config-schema rejection: a config authored against a newer golangci-lint hits `additional properties ... not allowed` under the pinned CI version. Bump the CI pin and the local install together.

**`govulncheck` fails on stdlib advisories, not just your code.** Advisories are matched against the `toolchain` line in `go.mod`, so a lagging toolchain red-lights CI on commits that touch zero Go code - and a failed test-and-lint job typically skips the release job downstream. When `govulncheck` reports vulnerabilities "in the Go standard library" all marked fixed in a patch you don't have, the fix is bumping the toolchain, not editing code.

## CI/CD Pipeline (GitHub Actions)

```yaml
name: Go CI
on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-go@v7
        with:
          go-version: stable
      - uses: golangci/golangci-lint-action@v9
        with:
          version: v2.13

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        go-version: [stable, oldstable]
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-go@v7
        with:
          go-version: ${{ matrix.go-version }}
      - run: go install gotest.tools/gotestsum@v1.13.0
      - name: Test
        run: gotestsum --format github-actions --junitfile unit-tests.xml -- -race -coverprofile=coverage.out -covermode=atomic ./...
      - uses: actions/upload-artifact@v7
        if: always()
        with:
          name: test-results-${{ matrix.go-version }}
          path: unit-tests.xml

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-go@v7
        with:
          go-version: stable
      - run: go install golang.org/x/vuln/cmd/govulncheck@v1.7.0
      - run: govulncheck ./...
```

## Existing Project Migration

```bash
# 1. Install tools
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.1
go install mvdan.cc/gofumpt@v0.11.0
go install gotest.tools/gotestsum@v1.13.0

# 2. Migrate existing golangci-lint v1 config
golangci-lint migrate

# 3. Format codebase
gofumpt -w .

# 4. Run linter (fix what you can, nolint the rest)
golangci-lint run --fix ./...

# 5. Replace go test with gotestsum in scripts/CI
# Before: go test -v ./...
# After:  gotestsum --format testname -- -race ./...

# 6. Copy Justfile and lefthook.yml templates above
# 7. Run: just check
```

For incremental adoption on large codebases, use `only-new-issues: true` in the GitHub Action to only lint changed code. Outside the Action, `--new-from-merge-base=main` and `--new-from-rev=<rev>` do the same locally - see the [golangci-lint Reference](references/golangci-lint-reference.md) for the full set.

Expect new findings after a toolchain bump: since Go 1.27, "`go test` now invokes the `stdversion` vet check by default. This reports the use of standard library symbols that are too new for the Go version in force in the referring file". Adjust the `go` directive or the call site rather than suppressing it.

## Adjacent Tools

Not part of the core stack, but the gaps most projects fill next:

| Need | Tool | Why |
|------|------|-----|
| Structured logging | `log/slog` (stdlib) | The default since Go 1.21; the `sloglint` linter enforces a consistent call style |
| Hot reload for a running service | [air](https://github.com/air-verse/air) or [wgo](https://github.com/bokwoon95/wgo) | `just test-watch` covers tests; neither `go run` nor gotestsum restarts a server on save |
| Release binaries + changelog | [GoReleaser](https://goreleaser.com/) | Cross-compile, checksum, sign, and publish from one config |
| Type-safe SQL from schema | [sqlc](https://sqlc.dev/) | Generates Go from the same SQL your migrations define, so `storage/` stays hand-written-free |

## Reference Docs

- [golangci-lint Reference](references/golangci-lint-reference.md) - v2 config, linter catalog, recommended sets, nolint syntax
- [gofumpt Reference](references/gofumpt-reference.md) - formatting rules, editor integration, golangci-lint integration
- [gotestsum Reference](references/gotestsum-reference.md) - output formats, watch mode, JUnit XML, CI recipes
- [Go Testing Reference](references/go-testing-reference.md) - table-driven tests, mocking, benchmarks, coverage, fuzz testing
- [golang-migrate Reference](references/go-migrate-reference.md) - CLI, library, embed.FS, transactions, pitfalls
- [Justfile Reference](references/justfile-reference.md) - Go-specific recipes, task groups, lefthook integration

## Resources

- [Go Official Docs](https://go.dev/doc/)
- [golangci-lint Docs](https://golangci-lint.run/)
- [gofumpt](https://github.com/mvdan/gofumpt)
- [gotestsum](https://github.com/gotestyourself/gotestsum)
- [golang-migrate](https://github.com/golang-migrate/migrate)
- [Lefthook](https://github.com/evilmartians/lefthook)
- [just](https://github.com/casey/just)
- [govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck)
- [Go 1.27 Release Notes](https://go.dev/doc/go1.27)
- [Go Release History](https://go.dev/doc/devel/release)
