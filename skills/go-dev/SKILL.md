---
name: go-dev
description: Opinionated Go setup with golangci-lint v2, gofumpt, gotestsum, golang-migrate, and just. Use when starting a Go project, configuring lint, format, test, coverage or CI, writing a Justfile, wiring migrations, or leaving a Makefile workflow.
metadata:
  version: "0.4.0"
  categories: "development"
  topics: "go, golangci-lint, gofumpt, testing, just"
  upstream: "go@1.27.1, golangci-lint@v2.13.2, gofumpt@v0.12.0, gotestsum@v1.13.0, golang-migrate@v4.20.1, just@1.58.0, lefthook@v2.1.12"
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
| **gofumpt** | v0.12+ | Strict formatter (superset of gofmt, 19 default rules) | gofmt |
| **gotestsum** | v1.13+ | Test runner with readable output, watch mode, JUnit XML | Raw `go test` |
| **just** | 1.58+ | Task runner | Makefile |
| **golang-migrate** | v4.20+ | DB migrations (CLI + library + `embed.FS`) | Manual SQL scripts |
| **lefthook** | v2.1+ | Git hooks (single binary, parallel) | pre-commit (Python) |

**Version floors are load-bearing.** golangci-lint "supports Go versions lower or equal to the Go version used to compile it" - a pin older than your Go toolchain fails outright. Go 1.27 support landed in golangci-lint v2.13.0, so `v2.13` is the floor for a Go 1.27 project. Two more floors moved recently: gofumpt v0.12.0 "is based on Go 1.27's gofmt, and requires Go 1.26 or later", and lefthook's `go install` path now asks for Go 1.26+.

## Quick Start: New Project

```bash
# 1. Create module
mkdir myapp && cd myapp
go mod init github.com/yourorg/myapp

# 2. Scaffold directories
mkdir -p cmd/myapp internal migrations

# 3. Install golangci-lint as a binary, not as a module tool (see note below)
curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.13.2

# 4. Track the rest in go.mod (Go 1.24+ tool directive). Pin versions - never @latest,
#    which recompiles the tool on every CI run and drifts between machines.
go get -tool mvdan.cc/gofumpt@v0.12.0
go get -tool gotest.tools/gotestsum@v1.13.0

# golang-migrate needs a build tag, so install it directly
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@v4.20.1

# 5. Create config files (templates below)
# 6. Run: just check
```

**Do not install golangci-lint through the tools pattern.** Upstream is explicit: "Using `go install`/`go get`, \"tools pattern\", and `tool` command/directives installations aren't guaranteed to work. We recommend using binary installation." The reason that matters in a shared repo is dependency bleed - "the dependencies of a tool can modify the dependencies of another tool or your project". If you must have it in `go.mod`, isolate it behind its own `-modfile` - see the [golangci-lint Reference](references/golangci-lint-reference.md).

**`go get -tool` tracks; `go tool` runs.** The tool directive records the dependency in `go.mod` but puts nothing on your PATH. Either invoke through the toolchain - `go tool gofumpt -l .`, `go tool gotestsum --format testname` - or `go install tool` once to populate `$(go env GOPATH)/bin`. The Justfile below calls the bare binaries, so it assumes the `go install tool` route (or a system install via Homebrew). Note that `go tool` resolves against the module in the current directory - "additional tools may be defined in the go.mod of the current module" - so in a monorepo it fails with `go: no such tool "..."` unless the recipe sets `[working-directory(...)]`.

Two Go-command behaviours worth knowing before the first commit:

- `go mod init` under a 1.N toolchain writes `go 1.(N-1).0`, not `1.N` - "Running `go mod init` using a toolchain of version `1.N.X` will create a `go.mod` file specifying the Go version `go 1.(N-1).0`." Bump the directive deliberately if you want 1.N language features.
- Pin the toolchain for reproducibility with a `toolchain go1.27.1` line in `go.mod` (or `GOTOOLCHAIN=go1.27.1` in CI). Pin the current patch, not the `.0`: this line is what `govulncheck` compares stdlib advisories against, so a stale patch red-lights CI on its own - see Footguns below.

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
      rules:
        # enable-all-rules turns on `unhandled-error`, which flags `fmt.Println` in main.
        # Under enable-all-rules a rule's `arguments` are ignored (the rule registers
        # twice), so an allowlist does not work here - only `disabled` takes effect.
        - name: unhandled-error
          disabled: true
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
      # Select rules individually. `extra-rules: true` is deprecated, and it also
      # switches on `balance_calls`, which gofumpt itself demoted as controversial.
      extra:
        group-params: true
        clothe-returns: true
        balance-calls: false
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
go install github.com/evilmartians/lefthook/v2@v2.1.12   # needs Go 1.26+
lefthook install
```

```yaml
# lefthook.yml
assert_lefthook_installed: true   # fail loudly instead of skipping every rule

pre-commit:
  piped: true   # fail fast - stop at the first failing job
  commands:
    fmt:
      glob: "*.go"
      run: golangci-lint fmt {staged_files}
      stage_fixed: true
    lint:
      glob: "*.go"
      # Never pass a bare file list to `golangci-lint run`: a list spanning two
      # directories is rejected outright, and one file of a multi-file package
      # reports phantom `undefined:` typecheck errors. Lint the packages instead.
      run: printf '%s\n' {staged_files} | xargs -n1 dirname | sort -u | xargs golangci-lint run --fix
      stage_fixed: true
    mod-tidy:
      glob: "*.{go,mod,sum}"
      run: go mod tidy

pre-push:
  commands:
    test:
      run: go test -race ./...
```

`piped: true` is fail-fast, not ordering - lefthook "runs commands and scripts **sequentially** by default", and `piped` adds "Stop running commands and scripts if one of them fail." It cannot be combined with `parallel: true`.

`jobs:` (added in lefthook 1.10.0) is the newer primitive alongside the `commands:`/`scripts:` split - "Jobs provide a flexible way to define tasks, supporting both commands and scripts. Jobs can be grouped for advanced flow control." `commands:` is not deprecated and stays fully documented; reach for `jobs:` when you need grouping, nested control flow, or a mix of inline commands and scripts in one hook.

Four more worth wiring:

- `assert_lefthook_installed: true`, above, is the antidote to the dormancy footgun below: "fail (with exit status 1) if `lefthook` executable can't be found in $PATH".
- `lefthook validate` in CI catches a malformed `lefthook.yml` before it silently disables hooks; `lefthook dump` prints the merged effective config when a hook does not behave as written.
- A gitignored `lefthook-local.yml` lets a developer add or skip jobs without imposing it on teammates - "This is useful when you want to use lefthook locally without imposing it on your teammates."
- In a monorepo, give each job a `root:` pointing at its module directory; without it `go mod tidy` and `go tool` run against the repo root and fail.

Beta, but worth knowing: `ai:` declares LLM agent hooks in the same file - "During `lefthook install`, lefthook generates the provider-specific settings file so that the agent calls `lefthook run <hook>` when the event fires", for `claude`, `codex`, `cursor`, and `copilot`. See the [Lefthook Reference](references/lefthook-reference.md) for the wider config surface.

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

`go fix` is the toolchain-native complement to the `modernize` linter: Go 1.26 rebuilt it as a codebase modernizer - "The venerable `go fix` command has been completely revamped and is now the home of Go's *modernizers*. It provides a dependable, push-button way to update Go code bases to the latest idioms and core library APIs." Run `go fix ./...` after a toolchain bump, before the linter has to complain. Go 1.27 added four more modernizers - "The go fix command contains several new modernizers (atomictypes, embedlit, slicesbackward, and unsafefuncs)" - and removed `fmtappendf`, so a 1.27 bump is a good moment to run it.

Three other Go 1.27 changes touch this stack directly:

- **Generic methods.** "Go 1.27 now supports generic methods: a method declaration may declare its own type parameters."
- **`encoding/json/v2`.** "The encoding/json package is now backed by the v2 implementation" - behaviour-compatible by default, but worth knowing before you debug a marshalling difference.
- **`go test -json` gained an `OutputType` field**, annotating `"Action":"output"` lines. This is the stream gotestsum consumes, so it lands in your test tooling whether or not you use it directly.

## Footguns

Seven failure modes that cost real debugging time, none of which produce an obvious error message.

**Config placement is load-bearing.** `.golangci.yml` must sit at the repo root: golangci-lint searches the working dir and its parents, and editor Go plugins auto-detect only a root `.golangci.*`, so filing it under `.github/` costs in-IDE linting even if you pass `--config`. lefthook auto-discovers only the repo root or `.config/` - move `lefthook.yml` anywhere else and commits silently stop running hooks, because git invokes the hook directly and no task-runner recipe can intercept that.

**lefthook is dormant until installed.** The binary being absent from PATH, or `lefthook install` never having run, both present as "hooks just don't fire" with no warning. Set `assert_lefthook_installed: true` so this fails loudly, pin lefthook as a repo tool, and make `lefthook install` part of onboarding.

**A stale lint cache invents issues.** golangci-lint can report failures in files that no longer exist on disk - typically after a branch switch or a deleted worktree. The costlier variant is nolintlint reporting a load-bearing `//nolint` directive as unused, which tempts you to delete a real suppression. Prove which side is lying with `GL_DEBUG=nolint_filter` before touching the code, and run `golangci-lint cache clean` if issue counts look impossible. When several worktrees share a checkout, give each its own cache with `GOLANGCI_LINT_CACHE=<worktree>/.golangci-cache` - and note the cache does not reliably invalidate on config, tool, or dependency changes, so fold those into the cache key if a phantom keeps returning.

**Concurrent golangci-lint runs fail rather than queue.** The lock is a single file in the system temp dir, *not* per-`GOLANGCI_LINT_CACHE`, so per-worktree cache isolation does not prevent it. A second run waits five seconds, then exits with `parallel golangci-lint is running`. This bites hardest in a `just` recipe with `[parallel]` that runs `fmt` and `run` together, on green code. Set `run.allow-serial-runners: true` to wait indefinitely instead of failing, or `run.allow-parallel-runners: true` to drop the lock entirely.

**Don't run two formatters against one gate.** Standalone `gofumpt -w` and `golangci-lint fmt` do not always agree on the same file, so a repo that fixes with one and gates with the other fails CI on code it just formatted. This is currently live rather than theoretical: golangci-lint v2.13.2 vendors gofumpt v0.11.0, while a standalone install is v0.12.0, and v0.12.0 changed how imports carrying comments and blank lines are laid out. Pick one as both fixer and gate - the Justfile and the hook above both use `golangci-lint fmt`.

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
      - name: Verify lint config against the pinned binary
        run: golangci-lint config verify

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
      - run: go install golang.org/x/vuln/cmd/govulncheck@v1.8.0
      - run: govulncheck ./...
```

Two `setup-go` behaviours decide whether this workflow is fast or pathologically slow:

- **It hashes a repo-root `go.mod`.** Caching is on by default, but a module in a subdirectory never matches, so every run logs a restore failure and cold-compiles the whole dependency tree. Point `cache-dependency-path` at the real file.
- **The cache is saved in a post step declared `post-if: success()`.** A job that fails saves nothing, so a cold run that times out stays cold forever and raising the timeout never breaks the loop. Split lint and test into separate jobs so one slow gate cannot starve the other's cache.

`golangci-lint config verify` earns its place as an explicit step: a config authored against a newer binary is accepted locally and rejected by the pinned CI version, and without this step that surfaces as a confusing lint failure much later in the job.

## Existing Project Migration

```bash
# 1. Install tools (golangci-lint as a binary - see Quick Start)
curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.13.2
go install mvdan.cc/gofumpt@v0.12.0
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
- [Lefthook Reference](references/lefthook-reference.md) - job filtering, monorepo roots, remote configs, CLI, env vars

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
