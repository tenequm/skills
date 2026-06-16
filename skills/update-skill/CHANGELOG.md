# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-06-16

### Added
- Phase 0 worktree choice: the run now asks once whether to operate in a dedicated git worktree (`git worktree add ... -b chore/update-<name>`), enabling parallel updates of multiple skills without README/index/diff contention. All phases operate against a new `<workdir>` variable (the worktree if chosen, else `${CLAUDE_PROJECT_DIR}`); the existing Phase 7 branch guard handles the resulting feature-branch PR flow, and the worktree is removed after the run.

## [0.6.0] - 2026-06-05

### Added
- Restored the `argument-hint: "[skill-name]"` frontmatter field removed in 0.5.0. It is a valid, functional Claude Code field for user-invoked skills (used in Anthropic's own `skills/<name>/SKILL.md` examples) and is documented in this repo's `skills-best-practices`; it is simply outside the open Agent Skills spec, which ignores unknown fields.

### Fixed
- Aligned the repo linter (`scripts/check_skills.py`) with the optional Claude Code skill/command fields documented in `skills-best-practices` (`argument-hint`, `when_to_use`, `arguments`, `model`, `effort`, `context`, `agent`, `hooks`). The previous allowlist rejected fields the repo's own guidance endorses.

## [0.5.0] - 2026-06-05

### Added
- Apache-2.0 `LICENSE.txt` (required for publishing).
- Upstreamless-by-nature escape hatch: skills that wrap no package/spec/doc (workflow or writing skills) cleanly omit `metadata.upstream` and skip the bootstrap upstream-candidate proposal instead of being nagged.

### Changed
- Generalized for use in any skills repository. The pond usage angle is now optional with an explicit skip-and-fallback when the pond MCP is absent (https://pond.cascade.fyi/). Phase 5 reframed as a repo-agnostic validation gate, and Phase 7 defers publish/slug/release-tag specifics to the repo's own pipeline (CLAUDE.md/AGENTS.md) instead of hardcoding this repo's ClawHub scripts and release-tag naming.

### Removed
- `argument-hint` frontmatter field to pass the repo's lint allowlist (restored in 0.6.0 once the allowlist was corrected; the body already handles the no-argument case regardless).
