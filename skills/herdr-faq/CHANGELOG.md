# Changelog

All notable changes to this skill are documented in this file, following [Keep a Changelog v2.0.0](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

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
