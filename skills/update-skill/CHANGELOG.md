# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.1] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format
- metadata.openclaw block (emoji, homepage) for ClawHub display

## [0.8.0] - 2026-07-10

### Added
- Worktree lifecycle hardening from real runs: keep the worktree until the PR merges (follow-up rounds reuse it), remove the worktree before deleting its branch, `git worktree prune` for stale entries, and regenerate (never hand-merge) generated-file conflicts like README.md on rebase.
- Phase 3 line-budget planning: report the projected SKILL.md size when additive rows land and plan a references/ split when it would exceed the repo's cap.
- Phase 5 failure-attribution step: when the validation gate fails in a way unrelated to the edits, stash and re-run on a clean tree before debugging.
- Phase 3 public-vs-private scope call on usage-derived findings: private-infra learnings go to user memory/CLAUDE.md, never the public skill.
- Phase 2 research inputs: ground-truth CLI-wrapping skills against the live installed CLI, and accept user-supplied seed findings as explicit leads.
- Operating rule for duplicate/scheduled triggers firing mid-run: hold at the emitted gate, never redo research.
- Phase 4 authoring caution: never let a `!` at line start or after whitespace directly touch a backticked command in SKILL.md bodies (Claude Code executes it at load, even in code fences).
- Phase 1 pre-flight now verifies LICENSE.txt presence; Done phase reminds to propagate published updates to installed copies; Phase 7 batches multi-skill updates into one push when CI republishes per push.
- `metadata.upstream` now tracks `keep-a-changelog@2.0.0` - the spec the skill embeds a template of, whose releases invalidate content (proven this run).

### Changed
- Keep a Changelog citations and the bootstrap header template moved from 1.1.0 to 2.0.0 (six change types and dates unchanged; adds the `**Breaking:**` marker convention and version-pinned format links).
- Phase 2 notes subagents run in the background by default (Claude Code v2.1.198+): collect all completions before Phase 3.
- Phase 7 feature-branch flow now follows through merge: watch the default-branch publish CI after the PR merges (some repos have no PR CI at all), then clean up branch and worktree.

### Fixed
- Bootstrap upstream proposal no longer promotes incidentally-mentioned tools: candidates must be things whose releases would invalidate the skill's content.
- Phase 6 leak scan explicitly covers untracked new files, which `git diff` misses.

Verified against: keep-a-changelog@2.0.0

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
