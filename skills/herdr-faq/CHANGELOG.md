# Changelog

All notable changes to this skill are documented in this file, following [Keep a Changelog v2.0.0](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

## [0.3.2] - 2026-09-09

### Added

- `gemini-3.7-flash-medium` named as the recommended agy default, with the measurement
  behind it.

### Fixed

- Corrected the pane-argument rule, which was wrong in a way that broke a documented command:
  `pane read` takes its id **positionally and has no `--pane` flag**, so the previous guidance
  produced `unknown option: --pane`. `pane close` is not the only positional one; `pane split`
  accepts either form; `pane layout` and `pane process-info` take `--pane`; `pane list` takes
  neither.

### Added

- An agent TARGET may be a bare pane id (`agent get|read|prompt w1K:p1`), which reaches an
  unnamed agent without renaming someone else's.

## [0.3.1] - 2026-09-09

### Changed

- Shortened the frontmatter description to 234 characters (was 266) so it stays under the
  250-character budget; triggers are unchanged.

## [0.3.0] - 2026-09-09

Restructured so each agent kind carries complete, self-contained guidance, and moved "Per kind"
ahead of the shared sections - it is now the default entry point after the invariants. Driven by
a session that lost a full comparison run to agy failures the skill named as symptoms but never
gave a recipe for.

### Added

- agy: a complete pre-flight and launch recipe. The trust dialog is unanswerable from the CLI
  side (`send-keys enter` no-ops against it, `--dangerously-skip-permissions` is
  classifier-blocked), so `~/.gemini/trustedFolders.json` must carry the exact cwd before
  `agent start`; trust is per path unless a parent holds `TRUST_PARENT`.
- agy: `not a valid artifact path` explained - `ArtifactMetadata` on a `write_to_file`
  reclassifies it as an artifact confined to `~/.gemini/antigravity-cli/brain/<session-id>/`;
  pre-create the output file so the agent takes `Edit`.
- agy: agents sharing a directory read each other's output and a prior run's results and
  reproduce them; one directory per agent, and `md5` reruns before believing an agreement.
- agy: read the startup banner, not the status - `(Google AI Pro)` means entitlement reaches
  Code Assist, while a bare address or `Eligibility check failed: UNAVAILABLE (code 503)` is an
  agent that will never run however healthy it looks.
- One tab per agent for fleets, in both the agy recipe and Launch: repeated splits starve the
  TUI of columns, which stops rendering, swallows input, and hides state from detection.
- codex and claude: runnable launch-to-first-prompt blocks in their own sections.

### Changed

- "Per kind" moved to the top, directly after the invariants; Launch, Shapes, Drive and
  Failures are now the shared reference the per-kind recipes point into.
- claude's folder-trust pre-seed, its dialog-key warning, its `idle` semantics, the grey
  composer-suggestion trap and the `CLAUDE_CONFIG_DIR` skills note all moved into its section.
- `agent_not_ready` now states explicitly that agy's trust dialog is *not* detected and reads
  as `idle`.

## [0.2.0] - 2026-09-08

Restructured from an error-code index into a composition-time reference, after forensics on
two real sessions showed that none of the failures that cost time surfaced a herdr error code
at all. New "Shapes" and "Multiple machines" sections; Launch reordered so the mandatory
detection read gates the branch that follows it.

### Added

- "Shapes" section: which commands return JSON vs raw pane text, which take ids positionally,
  flag dependencies and caps, sparse `agent list` JSON, and repeated flags in shell variables.
- Recipe to pre-empt claude's folder-trust dialog: trust is inherited from any trusted
  ancestor, or pre-seed `hasTrustDialogAccepted` under an isolated `CLAUDE_CONFIG_DIR`.
- "Multiple machines" section for 0.9.0 `herdr machine`: a TUI-only surface with no machine
  namespace in the CLI, and per-server id/name scoping.
- Invariant 4: `idle` is not "finished", and `--wait` tracks lifecycle state rather than turns.
- 0.9.0 surface: `herdr status` skew gate, `workspace close --group`,
  `workspace_group_close_required`, `tab close` `confirmation_required`, `--trust-repository`.
- Field notes: `send-keys` can return ok without delivering, grey composer suggestions read as
  real text, grok shares agy's premature-`done` bug, claude background MCP tasks hold `idle`,
  `agent focus` can no-op in 0.9.0, wrapper processes are permanently undetectable.

### Changed

- **Breaking:** claude's folder-trust dialog IS detected; `agent start` fails fast with
  `agent_not_ready` rather than succeeding and letting the first prompt type into the dialog.
- **Breaking:** `agent prompt` does not truncate long text (8 KB verified intact); the
  1024-byte macOS tty limit applies to `pane send-text` and keystrokes.
- **Breaking:** the safe recovery key is dialog-specific - claude's trust dialog defaults to
  "No, exit", so a bare `send-keys enter` kills the agent.
- After answering a dialog, a bare `agent wait` returns the stale `blocked` state within
  milliseconds; gate on `--until idle done`.
- Split `--timeout` guidance, resolving an internal contradiction: `agent start` defaults to
  30000 and caps at 300000; `agent prompt` is uncapped but rejected without `--wait`.
- Start-failure triage now reads the pane first, since a bad flag leaves only the shell and
  reports a bare `timeout`.
- `unknown option` attributed primarily to repeated flags built in a shell variable.
- Detection window is the pane's own row count; 24 is only the fallback.

### Fixed

- Removed guidance obsoleted by herdr 0.9.0: the empty-`recent` fallback for fresh panes,
  codex misclassified as blocked by stale scrollback, the Windows npm-shim `--` workaround,
  background shells hanging waits, and `server stop` after a binary update.

Verified against: herdr 0.9.0

## [0.1.0] - 2026-09-03

### Added

- Single-file launch-and-drive playbook for herdr subagents (codex, claude, agy), distilled from ~1,400 real invocations, the herdrdev/herdr issue tracker, and the v0.8.2 source: four invariants, launch recipe with per-kind specifics, drive loop, and a condensed failure catalog (triage, every error code with cause and fix, silent failures).

Verified against: herdr 0.8.2
