# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-09-09

### Fixed
- lefthook `lint` job ran `golangci-lint run --fix {staged_files}`, which fails on any commit spanning two directories (`named files must all be in one directory`, exit 7) and reports phantom `undefined:` typecheck errors when one file of a multi-file package is staged. Now derives the packages from the staged files; both shapes verified against lefthook 2.1.12 and golangci-lint 2.13.2.
- The same hook fixed formatting with standalone `gofumpt -w` while the Justfile gated with `golangci-lint fmt` - the two-formatter mismatch the skill's own footgun warns about.
- `gofumpt: extra-rules: true` is deprecated in golangci-lint and is not a neutral shorthand: it calls `Extra.Set("true")`, which also enables `balance_calls`, the rule gofumpt demoted as controversial and disabled by default.
- `revive: enable-all-rules: true` made `fmt.Println` in a hello-world `main` a lint error. Under `enable-all-rules` a rule's `arguments` are silently ignored (the rule registers twice), so only `disabled: true` suppresses it; the template now does that and runs clean on a new project.
- `piped: true` annotated as "run sequentially"; lefthook runs sequentially by default and `piped` means fail-fast.
- `jobs:` attributed to lefthook v2 and described as superseding `commands:`; it landed in 1.10.0 and `commands:` is not deprecated.
- justfile-reference gated formatting with `gofumpt -d` while its own `fmt` recipe fixed with `golangci-lint fmt`.
- golangci-lint output formats described as "one of eight"; nine are listed.

### Changed
- Stack pinned to Go 1.27.1, golangci-lint v2.13.2, gofumpt v0.12.0, golang-migrate v4.20.1, lefthook v2.1.12; govulncheck CI pin to v1.8.0.
- **Breaking (upstream):** gofumpt v0.12.0 is based on Go 1.27's gofmt and requires Go 1.26 or later; it also changes import and blank-line layout in four cases, so upgrading reformats code.
- golang-migrate: pin v4.20.1, not v4.20.0 - a release-workflow bug kept v4.20.0 off Docker and the package registries.
- Quick Start installs golangci-lint as a binary instead of `go get -tool`; upstream warns the tools pattern "aren't guaranteed to work" and that tool dependencies can perturb the project's own graph. `-modfile` isolation documented as the fallback.
- `toolchain go1.27.0` bumped to go1.27.1, per the skill's own govulncheck footgun.
- Two-formatter footgun now cites a live instance: golangci-lint v2.13.2 vendors gofumpt v0.11.0 while a standalone install is v0.12.0.

### Added
- `references/lefthook-reference.md`: job filtering (including `glob` skipping whole-project jobs), monorepo `root`, ordering and `fail_on_changes`, `stage_fixed` semantics, sharing config via `extends`/`remotes`, the CLI, env vars, and the beta `ai:` agent hooks.
- `assert_lefthook_installed: true` - a one-line fix for the skill's own "lefthook is dormant until installed" footgun.
- Footgun: the golangci-lint run lock is a single file in the system temp dir, not per-`GOLANGCI_LINT_CACHE`, so concurrent runs wait five seconds and then fail with `parallel golangci-lint is running`. Documented `run.allow-parallel-runners` / `allow-serial-runners` and the `[parallel]` recipe hazard.
- Stale-cache footgun now names its costliest symptom - nolintlint reporting a load-bearing `//nolint` as unused - with `GL_DEBUG=nolint_filter` to prove which side is stale.
- CI: `cache-dependency-path` for modules outside the repo root, setup-go's `post-if: success()` cache-save deadlock, and `golangci-lint config verify` as an explicit step.
- Justfile traps: `go tool` resolves against the cwd module, version-manager shims as a fourth install path, and `GOFLAGS=-trimpath` to share one warm cache across worktrees.
- golangci-lint: `run.allow-parallel-runners`/`allow-serial-runners`/`issues-exit-code`/`modules-download-mode`/`enable-build-vcs`, `output.path-mode`/`path-prefix`, Go plugins, mise install, `completion`, langserver, other CI systems.
- just: its own agent skill, just-lsp/just-mcp, `[cache]`, `set dotenv-command` (incompatible with `dotenv-load`), `set default-script`, remote and markdown justfiles, and further attributes.
- golang-migrate v4.20.0 fixes: S3 `ListObjects` pagination past 1000 migrations, lazy index build, `moby/moby` security swap; plus `GracefulStop`, custom loggers, and migration reversibility.
- gotestsum: the `--raw-command` contract and running a pre-compiled test binary through `test2json`.
- Go 1.27 surface: generic methods, `encoding/json/v2`, `go test -json` `OutputType`, and the four new `go fix` modernizers.
- gofumpt: `-r` removal in favour of `gofmt -r`, govim editor integration.
- mockery pin refreshed to v3.8.0.

Verified against: go@1.27.1, golangci-lint@v2.13.2, gofumpt@v0.12.0, gotestsum@v1.13.0, golang-migrate@v4.20.1, just@1.58.0, lefthook@v2.1.12

## [0.3.1] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [0.3.0] - 2026-08-26

### Fixed
- CI lint job pinned golangci-lint `v2.11`, which predates Go 1.27 support and fails against `go-version: stable`.
- `t.Context()` attributed to Go 1.21; it landed in Go 1.24.
- `gotestsum tool matrix` does not exist; the subcommand is `tool ci-matrix`, so the CI partitioning snippet was broken as written.
- `--jsonfile-timing-events` documented as a boolean; it takes a file path.
- Go test attributes attributed to Go 1.24; they landed in Go 1.25.
- Claim that `just` strictly enforces tab indentation; spaces work, and the skill's own templates use them.
- golangci-lint-action `version` input documented as required; `action.yml` declares it optional.
- Blanket "golang-migrate does not wrap migrations in transactions" corrected for Postgres multi-statement execution.
- `go get -tool` tracked tools while every recipe called bare binaries, with no note that `go tool <name>` or `go install tool` bridges the two.

### Changed
- Stack pinned to Go 1.27, golangci-lint v2.13.1, gofumpt v0.11.0, just 1.58.0, lefthook v2.1.11.
- **Breaking (upstream):** gofumpt `-extra` takes a comma-separated rule list since v0.10.0, no longer a boolean.
- GitHub Actions pins: `checkout` v6 to v7, `setup-go` v6 to v7, `upload-artifact` v4 to v7.
- CI and Quick Start install pinned tool versions instead of `@latest`.
- JSON Schema guidance now points at the versioned URL; the unversioned one tracks master and yields false positives.
- Maximum linter preset uses `exhaustruct_v5` and `wsl_v5` instead of their deprecated names.

### Added
- Footguns section: stale lint cache, config-file placement, formatter-gate mismatch, lefthook activation, version-floor mismatch.
- govulncheck stdlib advisories track the go.mod `toolchain` line and red-light CI on commits touching no Go code.
- Go 1.26/1.27 toolchain surface: `go fix` modernizers, default `stdversion` vet check, `go mod init` N-1 directive, `GOTOOLCHAIN` pinning.
- golangci-lint: ~18 catalog linters, `swaggo` formatter, eight output formats including SARIF, incremental-adoption flags, `path-except`, `.golangci.reference.yml`, module plugins via `golangci-lint custom`.
- gofumpt: redundant-parentheses default rule, `balance_calls` extra rule, `-e` flag, nested `extra.*` settings in golangci-lint.
- Testing: `t.Chdir`, `t.Attr`/`t.Output`, `synctest.Sleep`, `httptest.NewTestServer`, `-artifacts`/`-outputdir`, `b.Loop` inlining fix.
- Testing practice: `-count=1` defeats the test cache; goldens must not depend on `GOARCH`/`GOOS`.
- golang-migrate: `create -format`/`-tz`, `x-migrations-table-quoted`, and the `Up()` vs `Steps(1)` distinction.
- just: `[arg(...)]`, `[working-directory]`, `[env]`, `[parallel]`, `[script]`, `[timestamp]`, ten settings including `minimum-version`, `mod`, `just --fmt --check`, `--jobs`.
- lefthook: `jobs:` supersedes the `commands:`/`scripts:` split; `lefthook validate`/`dump`; `lefthook-local` override.
- Adjacent Tools table: `log/slog`, air/wgo, GoReleaser, sqlc.

### Deprecated
- `exhaustruct` replaced by `exhaustruct_v5`; `gomodguard` by `gomodguard_v2`; `wsl` by `wsl_v5`.
- mockgen reflect mode replaced by package mode; testcontainers `GenericContainer` replaced by `Run`.
- gofumpt `Options.ExtraRules` replaced by `Options.Extra`.

Verified against: go@1.27.0, golangci-lint@v2.13.1, gofumpt@v0.11.0, gotestsum@v1.13.0, golang-migrate@v4.19.1, just@1.58.0, lefthook@v2.1.11
