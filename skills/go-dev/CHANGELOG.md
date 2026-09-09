# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
