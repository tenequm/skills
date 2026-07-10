# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.2] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.6.1] - 2026-07-10

### Fixed
- SKILL.md itself committed the footgun it documents: the troubleshooting row and Security bullet contained a live inline-injection literal (whitespace, then `!` touching a backticked placeholder command), which the Claude Code loader executed at load and errored on. Both rewritten to keep the `!` and backtick from touching.

### Changed
- Security guidance: replaced the zero-width-space suggestion (invisible, non-ASCII) with wrapping the `!` in its own code span; clarified that `references/` files are safe because they are read with the Read tool, never preprocessed.
- references/claude-code-features.md: added an explicit "documenting this syntax is itself a footgun" warning covering inline and fenced forms.

## [0.6.0] - 2026-07-01

### Added
- Claude Code: `disallowed-tools` frontmatter field; `${CLAUDE_PROJECT_DIR}` substitution (v2.1.196+) and literal-`$` backslash escape; `disableBundledSkills` setting + env var; `/reload-skills` (v2.1.152+) and SessionStart `reloadSkills: true`; frontmatter keys `display-name`/`default-enabled`/`fallback` and case-insensitive key parsing; skills-dir plugins (`.claude-plugin/plugin.json`), symlinked-dir dedup, same-name override of bundled skills; `name`-is-display-label, nested qualified invocation (`/apps/web:deploy`), and malformed-frontmatter `--debug` behavior; `/context` post-budget Skills size.
- ClawHub: per-file 10 MB cap; blocked-version triage via `clawhub scan --slug` / `scan download`; net-new `metadata.openclaw` fields (`nix`, `config`, `links`, `author`, `cliHelp`, `dependencies[]`, install `id`/`label`/`tap`); public audit status taxonomy (Pass/Review/Warn/Malicious/Pending/Error) and risk levels; more reason codes noted as a curated subset of ~26.
- API: 30 MB upload cap + common-root requirement; claude.ai-vs-API network contrast; pointers to `pause_turn`, container reuse, Files-API download, prompt-cache break, non-ZDR. Spec `compatibility` 500-char cap; `allowed-tools` marked Experimental.
- Troubleshooting footguns: over-1024-char description skipped at load; unquoted-YAML frontmatter breakage; `` !`cmd` `` executing inside doc code fences.

### Changed
- ClawHub reason codes: LLM verdict is `review.llm_review` (new `review.` tier), not `suspicious.llm_suspicious`; VirusTotal reframed as telemetry (no `vt_*` code); hard-block code `malicious.install_terminal_payload`; engine `v2.4.26`.
- ClawHub slug rules corrected (`^[a-z0-9](?:(?!--)[a-z0-9-])*[a-z0-9]$`, length 3-96, reserved/protected-affix blocklist); "never reused" -> 30-day soft-delete reservation.
- ClawHub CLI: canonical `clawhub skill publish`; removed `--clawscan-note`; "3 scanners" -> SkillSpector + VirusTotal + risk analysis, with static analysis internal-only.
- Claude Code: setting `maxSkillDescriptionChars` -> `skillListingMaxDescChars`; `disable-model-invocation` also blocks subagent preload + scheduled tasks; bundled-skills list refreshed (`/code-review`, `/design-sync`, `/fewer-permission-prompts`; `/simplify` cleanup-only since v2.1.154).
- Trimmed the SKILL.md description's keyword-dump tail (semantic matching, not keyword overlap).

### Removed
- ClawHub `download` install kind from the schema-field list (rejected by the parser; contradicted the skill's own install-specs section).

### Fixed
- Checklist validator command aligned to `uvx --from skills-ref agentskills validate`.

## [0.5.0] - 2026-06-05

### Added
- "Validate Against the Spec" testing section recommending `uvx --from skills-ref agentskills validate <skill>` before publishing.
- Publishing caveat under Frontmatter Reference: Claude Code-only fields (`argument-hint`, `when_to_use`, `model`, `context`, etc.) are rejected by the strict `agentskills validate` spec validator that ClawHub-publishing repos run, and must be stripped from the validated/published copy.

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
