# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format
- metadata.openclaw block (emoji, homepage) for ClawHub display

## [0.2.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.2.0] - 2026-06-05

### Fixed
- Go install string corrected to `go get github.com/grafana/grafana-foundation-sdk/go@v0.0.16` (the canonical tag form per the official docs), replacing the stale `@next+cog-v0.0.x` branch ref.
- PieChart legend example now uses `PieChartLegendOptionsBuilder` (from the `piechart` package) instead of `common.VizLegendOptionsBuilder`, which is a type error for piechart panels.

### Added
- `metadata.upstream` tracking established (pinned to v0.0.16).
- Known gotcha on dashboard schema v1 vs v2: the skill targets v1; `dashboardv2beta1` (k8s apiVersion `dashboard.grafana.app/v2beta1`) exists and is still stabilizing.
- Known gotchas on the type-checking gap (builders only checked when wired into a tsconfig; use project-local `npx tsc` for the SDK's ES2024/bundler output) and the regenerate-JSON-after-every-edit discipline.
- `units` typed-constants module, `expr` server-side/SQL expressions, `testdata` datasource, and the broader set of core datasource query builders (elasticsearch, cloudwatch, azuremonitor, googlecloudmonitoring, bigquery, athena, parca, grafanapyroscope) in the TypeScript reference.
- Additional panel types in the import reference: canvas, datagrid, annotationslist, dashboardlist, news; plus `librarypanel`.

### Changed
- Version pins updated to 0.0.16 across SKILL.md (install commands) and references/patterns.md (`package.json` example).

Verified against: @grafana/grafana-foundation-sdk@0.0.16, github.com/grafana/grafana-foundation-sdk/go@0.0.16

## [0.1.0] - 2026-06-05

### Added
- Initial release: building Grafana dashboards as code with the grafana-foundation-sdk typed builders (TypeScript or Go). Covers installation, core architecture, a TypeScript quick start, key patterns (helper functions, template variables, panel sizing, thresholds, field overrides, rows, Loki queries, transformations), output generation, and known gotchas, with `references/typescript-api.md` and `references/patterns.md` for depth.
