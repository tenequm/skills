# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-04-28

### Added
- `reactNative` domain to domains table with new rules (`noReactNativeRawText`, `noReactNativeLiteralColors`, `noReactNativeDeepImports`, `useReactNativePlatformComponents`).
- Missing domains: `drizzle`, `qwik`, `turborepo`, `vue` to the domains table.
- New CLI flags `--enforce-assist`, `--suppress`, `--reason`.
- React Compiler interaction note for `useExhaustiveDependencies`.
- `package.json` indent override pattern (avoids infinite reformatting loop with pnpm).
- `--write --unsafe` guidance for unused imports/params (safe vs unsafe fixes).
- `$schema` version pin gotcha and `biome migrate` upgrade workflow.
- `inlineConfig` (VS Code) vs `inline_config` (Zed) naming note.
- VS Code `source.fixAll.biome` editor action to recommended IDE setup.
- v2.4 embedded snippets (CSS/GraphQL inside JS) note.
- v2.4 Vue/Svelte parser improvements note.
- Linux `$XDG_CONFIG_HOME` and Windows path to config discovery section.
- Highlight new type-aware nursery rules: `noMisleadingReturnType`, `useStringStartsEndsWith`, `useExplicitReturnType`, `useDisposables`.
- New test-domain rules: `noIdenticalTestTitle`, `useConsistentTestIt`.
- Initial CHANGELOG and `metadata.upstream` tracking.

### Changed
- Auto-detect criteria for `react` domain corrected to `react >= 16.0.0`; `test` domain auto-detects via `jest`/`mocha`/`ava`/`vitest`.
- `noFloatingPromises` now detects through cross-module generic wrapper functions (v2.4.12).
- Type-aware lint rules now resolve members through `Pick`, `Omit`, `Partial`, `Required`, `Readonly` utility types (v2.4.12).
- `organizeImports` now sorts imports in TypeScript modules and declaration files (v2.4.13).
- Plugin language support: clarify JS/CSS are documented; JSON support added in v2.4.

### Deprecated
- `files.experimentalScannerIgnores` is deprecated upstream; replacement is `!!` force-ignore syntax inside `files.includes`.

### Fixed
- Gotcha #6 corrected: `--fix` IS a documented alias for `--write` on `biome lint` and `biome format`.

Verified against: @biomejs/biome@2.4.13

## [0.2.0] - 2026-03-18
- Skill content prior to formal CHANGELOG tracking; see `git log -- skills/biome/` for history.
