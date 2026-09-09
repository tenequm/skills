# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2026-09-09

### Added

- Review-mode state gate: a draft, closed, or merged PR - or a withdrawn ask - resolves to a
  `skip` verdict that posts nothing and names the state, while still reporting every finding.
  `skip` is reached only from PR state, never from finding severity.
- Review-mode verdict derivation. Every surviving pre-merge finding is classified SUGGESTION /
  BLOCKING QUESTION / BLOCKING FIX (SEVERE for security, data loss, irreversible changes, or a
  broken deploy path), and the verdict is the strictest match. Replaces "any correctness finding
  on changed lines -> request-changes", which could not tell a nit with a line anchor from a
  blocker. A consistency check follows: an approve means every comment can be ignored, so a
  draft comment saying "before merge" disqualifies an approve.
- Pre-merge asks vs Follow-ups split in the review-mode report. Follow-ups never enter the
  verdict; `(pre-existing)` and `(out of diff)` findings are always follow-ups.
- Phase 6 staleness re-check: on confirmation, re-fetch review state, head SHA, and
  mergeability, and re-evaluate the verdict if any moved since Phase 2 rather than posting a
  stale one.
- Phase 6 anchor pre-validation: each inline anchor is confirmed to sit inside a diff hunk
  before it is proposed, since GitHub rejects the whole review atomically on one bad anchor and
  nothing posts.
- Phase 6 thread replies via `pulls/<n>/comments -F in_reply_to=<id>` as a separate call.

### Changed

- Review-mode confirmation protocol is now explicit: `y` posts the recommendation, a named
  action is an override that must be acknowledged before posting, `n` posts nothing, and
  anything else is discussion rather than consent.
- Phase 6 review body is 1-2 sentences of judgment plus counts and unanchored items. Verification
  steps are never recited - narrating the process is an audit trail and an AI tell - and evidence
  lives inside the inline comment it supports.
- Review reports are headed with the full PR URL and title instead of a bare `#number`.
- The review JSON payload is written to the session scratchpad instead of `/tmp`.

## [3.0.0] - 2026-09-09

### Added

- PR mode. The argument now also accepts a GitHub PR - a URL, a bare number, or a description
  ("the PR for this branch") - resolved with `gh`, checked out in place or cloned to a temp dir.
  Absorbs the `review-github-pr` skill, which is removed from this repo; the review core (Phases
  2-5) is shared, so the PR path no longer lags behind polish's improvements.
- Phase 6 (review mode): posts one review through the reviews API with every anchored finding as
  an inline comment, after the user confirms a recommended action.
- Rules: convention findings must cite a specific existing example; review-mode findings are framed
  as questions, and `(pre-existing)` / `(out of diff)` findings never drive the recommended action.

### Changed

- Fix mode vs review mode is decided once in Setup, from the argument and PR authorship (your PR
  defaults to fix, someone else's to review; an explicit `fix`/`review` overrides), and is never
  re-derived from repository state later - the modes disagree on whether the tree may be edited.
- Phase 1 in review mode reads the validation command from the base branch
  (`git show origin/<baseRefName>:CLAUDE.md`) and confirms before running it, since `gh pr checkout`
  lands an untrusted tree. Check failures become findings instead of being fixed.
- Phase 3's untrusted-data framing extends to the PR title, body, and commit messages, wrapped in
  `<pr-content>` markers.

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
