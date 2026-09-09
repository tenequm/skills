# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.0] - 2026-09-09

### Added
- A `Length` subsection under Writing the Description - target 250 chars, with the compression
  order that actually pays (cut restated stack enumerations and selling points, collapse trigger
  lists, keep exclusions and disambiguations).
- Guidance to prefer prose over an `!` block in a published skill: dynamic injection is
  host-specific, arrives elsewhere as literal text, and drags `allowed-tools` along to suppress
  its own prompts.

### Changed
- Level 1 metadata cost was a flat "~100 tokens"; it is a function of description length,
  roughly `chars / 4 + 25`.
- `disable-model-invocation` now carries a "don't reach for it by default" warning - it blocks
  the prose invocation path users actually use, plus subagent preload and scheduled tasks.
- The frontmatter parse-failure row generalized from `Triggers:` to any colon-space in a plain
  YAML scalar, with ` - ` given as the rewrite.
- The four generic workflow templates condensed to a four-bullet list, and the Be Concise
  example shortened (it also nested a fence inside a fence of the same type).

## [0.8.2] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [0.8.1] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`agents, knowledge`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [0.8.0] - 2026-08-07

### Changed

- Consolidated references into SKILL.md following the skill's own single-file-first stance: description-guide.md, patterns.md, and checklist.md folded in (negative triggers, manually-invoked-skills note, CLI-embedded pattern, MCP/subagent guidance, Claude A/B loop, compact pre-publish checklist); redundant examples and generic workflow patterns dropped.
- claude-code-features.md merged into a new "Claude Code Specifics" section after verifying every claim against official docs (Claude Code v2.1.224): ~85% is now covered verbatim by the expanded official skills docs and collapsed to links; kept the injection footgun, undocumented frontmatter keys (display-name, default-enabled, fallback, case-insensitive parsing), and behavior deltas (fork background-by-default since v2.1.218, per-turn allowed-tools grant, directory-derived command names, compaction re-attach budgets, listing budget mechanics, skill stacking, additionalDirectories not loading skills).
- clawhub-publishing.md rewritten quirks-only (~5.5k chars, was 16.7k) and kept as the sole reference (conditional-loading test: needed only when publishing). Doc-covered material replaced with links to ClawHub's five docs; verified against clawhub CLI v0.23.3 and moderation engine v2.4.26.
- Size guidance is now chars-only: 25k recommended / 50k hard ceiling via `wc -c`; line counts dropped as a metric (identical content varies 2x in lines depending on formatting).
- Frontmatter table completed with `background` and `shell` fields.

### Removed

- Stale ClawHub facts: the capability-tags system (retired upstream 2026-06-17), the "5 new skills/hour" rate limit (now 200 new skills per 24 hours), the "text-based files only" upload rule (binaries now accepted), and the claim that `--slug`/`--name`/`--changelog`/`--tags` left the CLI (all alive in v0.23.3, plus new `--categories`/`--topics`).
- Stale Claude Code facts: outdated bundled-skills table (roster churns; linked to the commands reference instead), unconditional PowerShell env-var requirement, `/review` listed as a Skill-tool built-in (now an alias of `/code-review`).

### Fixed

- `allowed-tools` documented as a per-turn grant (was "while the skill is active").

## [0.7.0] - 2026-08-07

### Changed

- Repositioned the skill as opinionated guidance for any agent, distilled from the spec, official docs, and production experience (was "following Anthropic's official guidelines"); deviations from official guidance are now marked where they occur.
- Replaced "Progressive Disclosure (Most Important)" with "Single File vs. references/ (Most Important)": single-file SKILL.md is the default; split only when content is conditionally loaded (big chunks needed by only some invocations) AND size pressure exists. Distribution is a veto - skills that must travel as one file (CLI-embedded, pasted, printed by a command) stay single-file and get condensed carefully, never lossily trimmed.
- Size guidance is now two-tier: 500 lines / 25k chars recommended, 1000 lines / 50k chars hard ceiling, checked with `wc -c` (chars are easier for models to verify than tokens).
- Troubleshooting row and quality checklist reworded to match the new stance.

### Added

- references/patterns.md: "Single-File Skill Embedded in a CLI" pattern (compile SKILL.md into the binary, print via a `<tool> skill` subcommand - the shape playwright-cli, browser-use, and agent-browser converge on).

## [0.6.3] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format

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
