# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-05-21

### Added
- Claude Code frontmatter fields `when_to_use`, `arguments`, `hooks`; substitutions
  `$name` and `${CLAUDE_EFFORT}`.
- Multi-line ` ```! ` injection block; `skillOverrides` and `disableSkillShellExecution`
  settings; skill content lifecycle / compaction re-attach budget; built-in commands
  reachable through the Skill tool.
- Evaluation-driven development; "Claude A / Claude B" iterative pattern;
  "avoid offering too many options" anti-pattern.
- API usage model (`container` parameter, `anthropic` vs `custom` Skills, up to 8
  per request, beta headers).
- Agent Skills spec `license` and `compatibility` fields; `skills-ref` validator.
- ClawHub capability tags `financial-authority` and `requires-paid-service`;
  `--clawscan-note` flag; OWASP Agentic Skills Top 10 note.
- Reference-file size guidance; checklist calibration note for project-local skills.

### Changed
- `effort` adds `xhigh`; `model` accepts `inherit` (turn-scoped override).
- `allowed-tools` clarified: pre-approves tools, does not restrict them; space-separated.
- Skill listing budget is 1% of context (was 2%); added `skillListingBudgetFraction`
  and the 1,536-character per-entry cap.
- Bundled skills list adds `/run`, `/verify`, `/run-skill-generator`.
- Inline `!command` injection recognized only at line start or after whitespace.
- Custom commands merged into skills; a skill takes precedence over a same-named command.
- `name` documented as optional in Claude Code (directory-name fallback); `description`
  falls back to the first markdown paragraph; completed the naming rules.
- Progressive-disclosure Level 2 budget framed as a recommendation.
- Cut-off skill descriptions diagnosed with `/doctor`.
- Description guidance: Claude matches semantic meaning, not keyword stuffing.
- ClawHub capability-tag derivation: purchase / transaction-signing authority now
  yields `financial-authority`, not `crypto`/`requires-wallet`.

### Removed
- ClawHub `download` install kind (no longer supported; schema is `brew`/`node`/`go`/`uv`).

### Fixed
- Clarified "one level deep" means reference-chain depth, not filesystem nesting.
- Corrected stale ClawHub doc source links and removed an unverifiable model identifier.

## [0.3.0] - 2026-04-30
- Initial CHANGELOG; tracking established.
