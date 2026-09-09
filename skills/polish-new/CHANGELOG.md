# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

## [0.1.2] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [0.1.1] - 2026-08-27

### Changed

- Reframed the conditional Adversarial lens as Control Verification: it now
  states each control's promise and hunts for a counterexample, rather than
  being told to defeat the control. Every failure mode, the exact-sequence
  citation requirement, and the "say what you tried" clause are unchanged; the
  report tag becomes `(control)`. Same reframing applied to one Side-Effect
  Gating bullet. No mechanism change - the wording reads less like offensive
  security tooling, which is what the lens was never doing.

## [0.1.0] - 2026-08-27

### Added

- Initial release: convergent rewrite of the polish skill, built from a forensic
  analysis of real review sessions. New over polish 2.6.0: run-directory ledger
  with verbatim agent reports (compaction-safe), evidence-carrying findings with
  reproduce-not-re-derive validation, diff-size-scaled sharding by lens-natural
  units, skeptic and dive escalation until a round produces nothing new,
  conditional Adversarial and Plan Conformance lenses, disposition-based
  approval (bare "go" fixes everything marked fix), class-complete fixes with
  revert-proof regression tests, working-tree-only fixes with a single commit
  offered at the end, and a fix-review loop that exits only when a round
  warrants no edits.
