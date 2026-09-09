# Changelog

All notable changes to this skill are documented in this file, following [Keep a Changelog v2.0.0](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

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
