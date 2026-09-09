# Changelog

All notable changes to this skill are documented in this file, following [Keep a Changelog v2.0.0](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

## [0.2.0] - 2026-09-09

### Added

- The mechanism behind the permission finding: the claude adapter spawns its binary with
  `--allow-dangerously-skip-permissions --setting-sources=project,local`, so no permission
  request ever reaches acpx's policy layer. `--deny-all` is not ignored, it is unreachable -
  and the same flag list independently explains why user-scope settings are excluded.
- agy auth guidance: `security.auth.selectedType: "oauth-personal"` is the subscription path
  and the intended default, there is no tier setting and no `agy` auth subcommand, and
  re-running with `ACPX_AUTH_OAUTH_PERSONAL=1` is non-destructive and needs no browser while
  the token is valid. Entitlement problems are server-side; do not "fix" them with an API key.
- agy verification prompts must ask for a bare reply and have their whole log read - agy
  routes answers into brain artifact files, so a `tail` cannot distinguish "no tools" from
  "answered elsewhere".

### Changed

- Rewrote the MCP section around stdio as the normal case. An era mismatch (MCP 2026-07-28
  retired the `initialize` handshake; dual-era clients probe stdio with `server/discover` and
  fall back) is now described generically: a conforming legacy server answers with an error,
  one that aborts kills the pipe. agy probes, the codex and claude adapters do not. Removed
  the transport-specific setup recipe.

## [0.1.2] - 2026-09-09

### Added

- Worked recipe for giving agy an MCP server it does not already have - the case that kept
  being re-derived from scratch. Covers serving over HTTP (and that a 406 is the normal
  handshake reply), the fact that the same server needs an OBJECT map for the plain `agy` CLI
  and an ARRAY for acpx, why the acpx config must be a dedicated file rather than the CLI's,
  the one-line verification exec, and the fan-out shape with one directory per agent.
- Note that an HTTP MCP server is unsupervised: if it dies mid-run every agent silently loses
  its tools and the turn still ends `[done] end_turn`.

## [0.1.1] - 2026-09-09

### Changed

- Shortened the frontmatter description to 219 characters (was 279) so it stays under the
  250-character budget; triggers are unchanged.

## [0.1.0] - 2026-09-09

### Added

- Launch-and-drive playbook for acpx subagents (agy/Antigravity, codex, claude), distilled
  from ~180 real invocations across eight sessions and re-verified against acpx 0.15.1. Five
  invariants, a complete recipe per agent, plus Sessions, Completion, MCP, Limits, and a
  failure catalog keyed by the exact error string.
- The Antigravity escape hatch as a first-class recipe: acpx has no agy adapter and issue #362
  is closed as externally blocked, the built-in `gemini` agent is the public Gemini CLI and is
  dead for Code Assist, so `--agent <agy_acp_server.par>` is the only route - with its one-time
  `ACPX_AUTH_OAUTH_PERSONAL=1` auth, real-cwd requirement, and effort-in-the-model-id rule.
- `--mcp-config` requires a JSON *array* of named servers; the standard object-keyed
  `mcpServers` map throws an uncaught Node exception rather than a clean error. Not mentioned
  at all in the shipped acpx reference.
- Exit-code table (0/1/2/3/4/5/130) and the `status` state semantics, both absent from the
  shipped acpx reference.
- "What acpx cannot do": ACP sessions never wake on injected messages, `codex queue --thread`
  cannot reach an acpx-driven session, acpx-spawned Claude sessions bind no IPC socket, and
  acpx cannot attach to a session it did not start.
- Limits new in 0.15.1: the 64 MiB incoming ACP message cap
  (`ACPX_MAX_ACP_MESSAGE_BYTES`) and `ACPX_TERMINAL_MAX_OUTPUT_BYTES`; and `exec
  --config-option` (0.14.0+) as the way to set model and effort without a named session.

### Fixed

- Corrects three beliefs carried in prior notes, each re-tested against 0.15.1: permission
  flags do **not** gate file writes (both adapters write under `--deny-all`, because neither
  raises a permission request); Fable **does** run through acpx (`--model
  'claude-fable-5[1m]'`); and `--model claude-opus-5` still works even though `set model`
  rejects it, because the two paths validate differently.

Verified against: acpx 0.15.1
