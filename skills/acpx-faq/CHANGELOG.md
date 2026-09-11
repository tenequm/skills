# Changelog

All notable changes to this skill are documented in this file, following [Keep a Changelog v2.0.0](https://keepachangelog.com/en/2.0.0/).

## [Unreleased]

## [0.5.1] - 2026-09-11

### Removed

- Content agents never act on mid-run: the agy OAuth-URL capture choreography (the
  Failures catalog still routes both auth signatures to the compressed auth bullet),
  the session-creation-stall bullet (acpx prints its own remedy at failure time),
  issue/build provenance, the adapter float/pin backstories (kept as one-liners), the
  hand-install note and duplicate invocation block in Linux / NixOS. 20,097 -> 18,493
  chars.

## [0.5.0] - 2026-09-11

### Added

- Syntax authority section: `acpx --skill show acpx` is the syntax source of truth,
  retrieved tiered (`--help` first, grep/sed a topic second, dump-to-scratch-file only
  for novel authoring - never into the transcript; the reference is ~29k chars).
- When this lane section: the herdr-vs-acpx-vs-in-session routing rule, so the skill is
  self-contained instead of relying on a private harness config.
- agy: sibling-file reads warning (one directory per agent) - previously only in the
  herdr-faq sibling skill.

### Changed

- The file now carries only the vendor-reference delta: exit codes, failure semantics,
  traps, and per-agent recipes. Invariant 4 absorbed the "permission flags are not a
  sandbox" bullet; the Failures catalog is compressed to error string -> fix + section
  pointer.
- Description names the lane condition (outside a herdr pane / no HERDR_ENV).

### Removed

- Everything retrievable verbatim from `acpx --skill show acpx`: the sessions verb
  table, `Ctrl+C`/`cancel` semantics, `--format` enumeration, prune how-to, headful
  takeover walkthrough. MCP era-mismatch history, `.par` provenance, and measurement
  backstories compressed to their actionable clauses. 27,963 -> 20,128 chars.

## [0.4.0] - 2026-09-11

### Added

- Invariant 6: a persistent session leaves a resident process stack (~700 MB per executor)
  until `sessions close`; the idle TTL is the backstop and `--ttl 0` removes it. Learned
  from a real incident: seven forgotten owners from dispatched runs held ~4.9 GB RSS for
  hours, all heartbeating `queueDepth: 0` lock files.
- Teardown section: close as the last line of every scripted run, the pgrep leak check,
  plain `kill` (never `kill -9`) for stragglers - acpx 0.15.1 kills the adapter by PID only,
  so SIGKILL strands the `npm exec -> node -> agent` subtree on PID 1 - plus the
  `~/.acpx/config.json` `ttl` key and a `sessions prune --older-than 7` cadence.
- Per agent now opens with the exec-vs-session fork: `exec` is temporary, unsaved, and not
  queue-aware (nothing to leak), so it is the default for dispatched work; `-s <name>` is
  for queued follow-ups or reading `sessions history` afterwards.

### Changed

- Both launch recipes (codex, claude) now end with `sessions close` instead of stopping at
  "background it and read the log".
- Dropped `--ttl 0` from the codex recipe and from the Limits guidance; both spots now say
  what it costs and reserve it for human-driven warm sessions.
- The `sessions close` row in the Sessions table leads with teardown (per upstream
  docs/sessions.md: marks closed, sends ACP `session/close`, tears down adapter processes)
  instead of reading as a mere precondition for `codex resume` / `sessions export`.

## [0.3.0] - 2026-09-09

### Added

- agy: provenance of `agy_acp_server.par` - shipped by the Antigravity install, sha512-verified
  against Google's manifest, never downloaded by acpx or by this skill. Build
  `20260818_01_RC01` is pinned and self-updates nothing. Clears the Socket alert on unverified
  executable provenance.
- agy: Linux / NixOS section - the `--uid=` wrapper, the mandatory `SSL_CERT_FILE` export, and
  installing `agy` by hand rather than piping the installer (its `agy install` step writes to
  `~/.bashrc` / `~/.profile`).
- agy: how to capture the OAuth URL the server opens silently, and how to complete the callback
  by hand on a headless box.
- Failures: `502 Bad Gateway: Failed to connect to backend API` (a missing CA bundle on NixOS,
  surfacing as invariant 5 - exit 0 with `[done] end_turn`), and `authenticate` never returning.

### Changed

- agy: the credential split is now stated exactly - the server reads
  `~/.gemini/antigravity-acp/acp_token.json` and never the CLI's token; `GEMINI_HOME` relocates
  the whole tree.

### Removed

- `ACPX_AUTH_OAUTH_PERSONAL=1` as auth guidance. It is dead in build `20260818_01_RC01`
  ("Environment-based auth selection has been removed") and its absence makes the server hang
  on `authenticate` rather than error. Replaced by `auth.type` in
  `~/.gemini/antigravity-acp/settings.json`.

Verified against: agy 1.1.28, agy_acp_server 20260818_01_RC01, acpx 0.15.1 on NixOS.


## [0.2.1] - 2026-09-09

### Added

- `gemini-3.7-flash-medium` named as the recommended agy default, with the measurement behind
  it: on par with Opus for rubric-driven bulk work and far faster, while 3.8-flash-high scored
  worse on the same task.

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
