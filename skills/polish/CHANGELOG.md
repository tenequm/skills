# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.4.1] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format
- metadata.openclaw block (emoji, homepage) for ClawHub display

## [2.4.0] - 2026-07-10

### Added
- Small-diff fast path: review all four lenses directly without agent fan-out
- Phase 4 rewritten-path rule: flaws present at HEAD are reported as
  pre-existing-carried-through; deleted test coverage is flagged
- Agent prompts now carry project constraints (CLAUDE.md) and known-intentional
  patterns to pre-empt false positives
- Report additions: per-finding fix/skip recommendation, "Dropped after
  validation" section, non-blocking "Observations" slot
- Already-committed case: scope review to the session's commits; ask
  amend-vs-new-commit after fixes
- Cleanliness: byte-aware non-ASCII punctuation scan of changed lines
- Frontmatter: allowed-tools pre-approving read-only git commands;
  argument-hint + $ARGUMENTS to pass a custom base ref

### Changed
- Diff is written to a scratchpad file and passed to agents by path
- "Correctness (0 issues)" must state what was traced, not just the count
- Clean-case report substantiates the zero and offers next actions
- Lockfiles and generated files excluded from the review diff
- Description trimmed: trigger-phrase list is dead weight under
  disable-model-invocation (description never shown to the model)

### Fixed
- Phase 2 now includes untracked files (a staged change referencing an
  untracked file previously escaped review entirely)
- evals.json eval 1 asserted three review agents; the skill launches four

## [2.3.0] - 2026-07-10
- Initial CHANGELOG; tracking established.
