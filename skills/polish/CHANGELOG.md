# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.7.0] - 2026-09-09

### Added

- Rule: never reproduce a credential value in a finding, report line, or agent prompt - cite it
  by `file:line` and mask the value. Clears Snyk W007 (HIGH), which read "pass full diffs and
  exact file lines to review agents" as forced verbatim reproduction of secrets.
- Phase 3: explicit untrusted-data framing for the reviewed diff, with `<code-content>`
  boundary markers when a prompt inlines code. An instruction-shaped string inside the diff is
  a finding, not a step. Addresses the Gen audit's "Boundary markers: None".


## [2.6.2] - 2026-09-09

### Removed
- The `!` dynamic-injection block. It is a Claude Code-only body feature that reaches other
  agents as literal text, and Phase 2 already derives the same repository state; the branch
  name it uniquely supplied moved into Phase 2 step 1.
- `allowed-tools`, which existed only to keep that block from prompting.

## [2.6.1] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [2.6.0] - 2026-08-24

### Removed

- `disable-model-invocation: true` frontmatter flag. It blocked the model from honoring an earlier "run /polish before committing" instruction (the most common way the skill is requested), and the fallback was a hand-replicated or degraded review. The skill already hard-stops for approval before any fix, so model invocation is not risky.

### Changed

- Description trigger now targets an explicit or earlier user request rather than every commit, so the skill does not auto-fire unasked.

## [2.5.1] - 2026-08-21

### Fixed

- Eval 5 still required the report to stay off pre-existing code, the rule 2.5.0 replaced, and its "clean" fixture had an unchecked `fetch` boundary in the baseline that the changed file calls into - so correctly surfacing it would have failed the eval. Baseline now checks `res.ok`, and the expectation asks for no manufactured findings instead.

## [2.5.0] - 2026-08-21

### Changed

- Removed the non-blocking "Observations" report section. Everything actionable the review surfaces - including pre-existing flaws the diff touches and adjacent out-of-diff issues - is now a regular finding in its category, tagged `(pre-existing)` or `(out of diff)`, with the Recommendation line judging fix vs. skip on long-term codebase benefit (out-of-diff findings default to fix).
- Rewrote the scope rule: the diff remains the hunting scope, but real issues found along the way are findings, never parked in a side note.
- Recommendation guidance now carries a fix-vs-defer test: defer only what forces a decision or carries more risk than value; a low-risk maintenance fix is a fix, not a deferral.

## [2.4.3] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`development`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [2.4.2] - 2026-08-07

### Fixed

- Agent 4 routed out-of-scope findings to `/review`; the bundled review skill is `/code-review`.

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
