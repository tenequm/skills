---
name: go-dev
description: Opinionated Go development setup with golangci-lint v2 + gofumpt + gotestsum + golang-migrate + just. Use when creating new Go projects, setting up linting/formatting/testing, configuring CI/CD pipelines, writing Justfiles, or migrating from Makefile-only workflows. Triggers on "go project", "go mod init", "golangci-lint", "gofumpt", "gotestsum", "go test setup", "justfile go", "go migration", "go ci pipeline", "go lint setup", "go fmt", "go coverage".
metadata:
  version: "0.2.0"
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
| **Go** | 1.26+ | Language, toolchain, `go mod` | - |
| **golangci-lint** | v2.11+ | Meta-linter (100+ linters + formatters + `fmt` command) | gofmt, govet, staticcheck, errcheck run separately |
| **gofumpt** | v0.9+ | Strict formatter (superset of gofmt, 17+ extra rules) | gofmt |
| **gotestsum** | v1.13+ | Test runner with readable output, watch mode, JUnit XML | Raw `go test` |
| **just** | latest | Task runner | Makefile |
| **golang-migrate** | v4.19+ | DB migrations (CLI + library + `embed.FS`) | Manual SQL scripts |

## Quick Start: New Project

```bash
# 1. Create module
mkdir myapp && cd myapp
go mod init github.com/yourorg/myapp

# 2. Scaffold directories
mkdir -p cmd/myapp internal migrations

# 3. Install tools
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest
go install mvdan.cc/gofumpt@latest
go install gotest.tools/gotestsum@latest
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# 4. Track tools in go.mod (Go 1.24+)
go get -tool github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest
go get -tool mvdan.cc/gofumpt@latest
go get -tool gotest.tools/gotestsum@latest

# 5. Create config files (templates below)
# 6. Run: just check
```

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
go install github.com/evilmartians/lefthook/v2@latest
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
      - uses: actions/checkout@v6
      - uses: actions/setup-go@v6
        with:
          go-version: stable
      - uses: golangci/golangci-lint-action@v9
        with:
          version: v2.11

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        go-version: [stable, oldstable]
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-go@v6
        with:
          go-version: ${{ matrix.go-version }}
      - run: go install gotest.tools/gotestsum@latest
      - name: Test
        run: gotestsum --format github-actions --junitfile unit-tests.xml -- -race -coverprofile=coverage.out -covermode=atomic ./...
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-${{ matrix.go-version }}
          path: unit-tests.xml

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-go@v6
        with:
          go-version: stable
      - run: go install golang.org/x/vuln/cmd/govulncheck@latest
      - run: govulncheck ./...
```

## Existing Project Migration

```bash
# 1. Install tools
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest
go install mvdan.cc/gofumpt@latest
go install gotest.tools/gotestsum@latest

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

For incremental adoption on large codebases, use `only-new-issues: true` in the GitHub Action to only lint changed code.

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
