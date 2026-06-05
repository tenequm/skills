# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-06-05

### Added
- Apache-2.0 `LICENSE.txt` (required for publishing).
- Upstreamless-by-nature escape hatch: skills that wrap no package/spec/doc (workflow or writing skills) cleanly omit `metadata.upstream` and skip the bootstrap upstream-candidate proposal instead of being nagged.

### Changed
- Generalized for use in any skills repository. The pond usage angle is now optional with an explicit skip-and-fallback when the pond MCP is absent (https://pond.cascade.fyi/). Phase 5 reframed as a repo-agnostic validation gate, and Phase 7 defers publish/slug/release-tag specifics to the repo's own pipeline (CLAUDE.md/AGENTS.md) instead of hardcoding this repo's ClawHub scripts and release-tag naming.

### Removed
- `argument-hint` frontmatter field (not in the skill schema; the body already handles the no-argument case).
