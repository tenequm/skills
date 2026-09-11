---
name: acpx-faq
description: Run coding agents (codex, claude, agy/Antigravity) through the acpx ACP CLI - the headless lane outside a herdr pane (no HERDR_ENV). Use before launching or prompting a subagent, and when a command fails, a session is not found, or a prompt is lost.
metadata:
  version: "0.5.1"
  categories: "agents, operations"
  topics: "acpx, acp, agent-orchestration, troubleshooting, headless-agents"
  upstream: "acpx@0.15.1, agy@1.1.28, agy_acp_server@20260818_01_RC01"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/acpx-faq
    emoji: "🔌"
---

# acpx FAQ

Drive coding agents headlessly through [acpx](https://github.com/openclaw/acpx) (>= 0.15.1).

## Syntax authority

Syntax comes from the binary, not this file. `acpx --skill show acpx` is the vendor
reference (~29k chars) and the tiebreaker on command shape - do NOT dump it into the
transcript. Retrieve in this order:

1. `acpx --help` / `acpx <cmd> --help` - the flags you are about to compose.
2. One topic: `acpx --skill show acpx | rg -B2 -A12 '<term>'`, or a section:
   `acpx --skill show acpx | sed -n '/^## Sessions/,/^## /p'`.
3. Authoring something novel (a flow, an embedded runtime): dump ONCE to a scratch
   file and grep that file.

This file repeats nothing the reference covers. It carries only what the reference
lacks: exit codes, failure semantics, traps, and per-agent recipes. If a syntax
question is not answered here, it is answered there - go get it, never guess a flag.

## When this lane

acpx is the headless out-of-process executor lane. Inside a herdr pane (`HERDR_ENV=1`)
prefer herdr (herdr-faq): it gives you screen reads and dialog detection. Everywhere
else (plain terminal, ssh, cron) herdr is untargetable and acpx is the lane.
In-session fan-out stays on the harness's own subagent tool.

## Invariants

1. **Global flags precede the agent subcommand** (`--cwd`, `--model`, `--approve-all`,
   `--agent`, `--format`, `--timeout`, `--ttl`, `--mcp-config`). The subcommand accepts
   only `-s`, `--no-wait`, `-f` (and `exec` also `--config-option`). A global flag
   after the agent exits **2** with `error: unknown option`.
2. **`-s <name>` never creates a session.** It resolves one, walking from `--cwd` up
   to the git root; no match exits **4**. Create first with `sessions ensure --name <n>`.
3. **`status` is not a turn signal.** It probes the queue-owner process, never the
   agent, and keeps saying `running` after the turn has ended. Never gate automation
   on it.
4. **Permission flags are not a sandbox.** The claude adapter spawns its binary with
   `--allow-dangerously-skip-permissions --setting-sources=project,local`, so no
   permission request ever reaches acpx's policy layer (`--deny-all` is unreachable,
   not ignored); codex writes through its terminal capability. `--no-terminal`
   genuinely removes the terminal capability, but the only real filesystem control is
   which `--cwd` you hand it. Verify: `ps -Ao args | grep claude-agent-sdk` mid-turn.
5. **`[done] end_turn` and exit 0 are not proof of success.** A content-filter kill,
   an MCP load failure, or a truncated turn all end that way. Read the stream, or
   require the agent to write a result file you can check.
6. **A persistent session leaves a resident process stack until you close it.** Every
   `-s` prompt elects a queue owner holding `npm exec -> node <adapter> -> <agent>`,
   roughly 700 MB per executor. `sessions close` is the only supported teardown; the
   idle TTL (default 300s) is the backstop, and `--ttl 0` removes it. See Teardown.

## Per agent

**Default to `exec` for dispatched work.** `exec` runs a temporary session: no saved
record, not queue-aware, so it never elects a queue owner and leaves nothing to clean
up. Use `-s <name>` only to queue follow-ups onto a live run or to read
`sessions history` afterwards - and then the closing `sessions close` is part of the
recipe (invariant 6). One directory (ideally one worktree) per parallel executor:
sessions key on cwd.

### agy / Antigravity - the `--agent` escape hatch

**acpx has no Antigravity adapter**, and the built-in `gemini` agent is the *public
Gemini CLI* - a different product, dead for Code Assist. The only route is Google's
signed ACP server via `--agent`: the `.par` installed by Antigravity under
`~/.local/lib/antigravity-acp/` (if missing, install Antigravity - never download it).
`localharness_external` beside it must stay executable, or the server starts anyway
and only logs `Localharness not found`.

```bash
# macOS: --agent may point straight at the .par
D=/abs/real/dir                              # must exist: roots resolve through realpath
acpx --agent ~/.local/lib/antigravity-acp/agy_acp_server.par \
     --cwd "$D" --model gemini-3.7-flash-medium --timeout 1800 \
     exec 'Carry out $D/brief.md. Write your report to $D/report.md.'
```

- **Default `gemini-3.7-flash-medium`** (measured on par with Opus for rubric-driven
  bulk work and far faster; `gemini-3.8-flash-high` measured worse on the same task).
  Effort lives in the model id (`gemini-3.7-flash-{low,medium,high}`); no separate knob.
- **agy reads sibling files unprompted** - agents sharing a directory reproduce each
  other's output. One directory per agent, and checksum any rerun before believing an
  agreement number.
- **Auth: with no auth type configured the server hangs on `authenticate` forever** -
  it reads exactly like a network stall. One-time fix:

  ```bash
  mkdir -p ~/.gemini/antigravity-acp
  echo '{"auth":{"type":"oauth-personal"}}' > ~/.gemini/antigravity-acp/settings.json
  ```

  then complete its own sign-in once; the token persists. The server reads
  `~/.gemini/antigravity-acp/acp_token.json`, never the CLI's token - a fully
  authenticated `agy` does nothing for this lane, and `GEMINI_HOME` relocates the
  whole tree (a second isolated lane). An entitlement problem is server-side with no
  client lever - do not "fix" it by switching to `gemini-api-key` or a GCP project
  (separate billing, not fixes).
- **Never pass a positional agent with `--agent`** - exit **2**.
- **Verification prompts: demand a bare reply and read the whole log.** agy routes
  answers into brain artifact files, so a `tail` cannot tell "no tools" from
  "answered elsewhere". Add "Do not create any files".
- **agy hides MCP failures inside a successful-looking turn** - grep the output for
  `MCP load failed`; the exit code stays 0.

#### Linux / NixOS

Two silent differences from macOS:

1. **`--uid=` is required**, so `--agent` points at a wrapper
   (`~/.local/bin/agy-acp-server`):

   ```bash
   #!/usr/bin/env bash
   export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt   # NixOS; see 2
   exec ~/.local/lib/antigravity-acp/agy_acp_server.par --uid= "$@"
   ```

2. **Without that `SSL_CERT_FILE`, NixOS gets a 502.** The `.par`'s embedded OpenSSL
   has no valid CA paths there; its local proxy reports
   `502 Bad Gateway: Failed to connect to backend API` and the turn still ends
   `[done] end_turn` with **exit 0** (invariant 5). The real
   `CERTIFICATE_VERIFY_FAILED` appears only under `--alsologtostderr`.

The invocation is otherwise the macOS one with
`--agent ~/.local/bin/agy-acp-server`.

### codex

```bash
D=/abs/dir
acpx --cwd "$D" codex sessions ensure --name work            # idempotent; -s cannot create
acpx --cwd "$D" codex set model gpt-5.6-sol -s work
acpx --cwd "$D" codex set reasoning_effort high -s work
acpx --cwd "$D" --approve-all --timeout 5400 --format quiet --suppress-reads \
     codex -s work 'Carry out ./brief.md. Write your report to ./report.md.' > run.log 2>&1 &
# ...after the run finishes and you have read what you need:
acpx --cwd "$D" codex sessions close work   # ALWAYS - the run is not over until this returns
```

One-shot: `exec --config-option reasoning_effort=low` sets model and effort inline
(0.14.0+), applied after `--model` and before the prompt.

- The codex adapter floats on `^1.1.5` - behavior can change without an acpx upgrade.
- **OpenAI's content filter kills benign turns** that end clean (`[done] end_turn`,
  exit 0). Vocabulary like race / sweep / exploit / attack in a filename, comment or
  prompt triggers it. Read the transcript tail before believing completion; recover by
  re-prompting the same `-s <name>` (context survives) with the artifact renamed
  neutrally and the remaining steps listed explicitly.
- **Queue a follow-up onto a live session** by prompting the same name again - it runs
  after the current turn. This is how you course-correct without relaunching.
- **Handing off to a human TUI**: `sessions close` first, then `codex resume
  <sessionId>` (id from `sessions show` - it is the ordinary codex rollout id).

### claude

```bash
D=/abs/dir
acpx --cwd "$D" --model claude-opus-5 claude sessions ensure -s work
acpx --cwd "$D" --model claude-opus-5 --approve-all --suppress-reads --timeout 2400 \
     claude -s work -f /abs/brief.md >> run.log 2>&1 &
# ...after the run finishes and you have read what you need:
acpx --cwd "$D" claude sessions close work  # ALWAYS - the run is not over until this returns
```

- **No effort knob** (`set reasoning_effort` returns `Internal error`; expected).
- **`--model` and `set model` validate differently.** `set model` refuses anything
  outside the advertised list
  (`["default","opus[1m]","claude-fable-5[1m]","sonnet","haiku"]`); the global
  `--model` at session creation passes the id through to the harness, so
  `--model claude-opus-5` works. A genuinely unknown id still fails loudly:
  `RUNTIME: Internal error: There's an issue with the selected model (<id>)`.
- **Fable runs**: `--model 'claude-fable-5[1m]'` (quote it - the brackets are globs).
- **User-scope skills are excluded on purpose** -> `Unknown command: /polish`. Fix
  with `ACPX_CLAUDE_INCLUDE_USER_SETTINGS=1` - and settings bind at session
  **creation**, so recreate the session, do not re-prompt it.
- **Second account**: export `CLAUDE_CONFIG_DIR` and `CLAUDE_SECURESTORAGE_CONFIG_DIR`
  before `acpx`; the child inherits them.
- The claude adapter bundles an old claude (2.1.215) regardless of your PATH - newer
  harness features are absent; override with `--agent` at a newer adapter build.

## Sessions

- Sessions key on **(agent command, absolute cwd, optional name)** - parallel
  executors need their own directories, which also keeps per-session model and effort
  settings from racing.
- `sessions close` is the teardown verb: marks the record closed, sends ACP
  `session/close`, takes down the owner and adapter processes (see Teardown). Also
  required before `codex resume` and `sessions export`.
- A session whose cwd you have deleted becomes an unreachable registry row - `close`
  cannot target it without its cwd; prune it.

## Completion

`status` states (the vendor doc has no state table): `running`, `idle`, `dead` (owner
gone or last exit abnormal), `no-session`. It is a local `kill(pid,0)`-style check
that reads `running` for the whole idle TTL after a turn ends - a loop waiting for
`idle` spins past real completion (invariant 3). What is actually correct:

- the foreground stream's terminating `[done] end_turn`, plus the process exit code;
- `sessions show <n>` (`lastActivity`, `historyEntries`) and `sessions history <n>`;
- best: a **result file** the brief required the agent to write - poll for the file.

`--no-wait` acknowledges enqueueing (`[queued] <id>`), which is neither delivery nor
completion - behind a running turn the prompt waits for the turn boundary.

Supervise a backgrounded run by counting tool lines and mtime
(`rg -c '^\[tool\]' run.log`, `stat -f '%Sm' run.log`); liveness:
`pgrep -fl 'acpx|codex-acp|claude-agent-acp'`.

## Teardown

`sessions close <n>` takes down the whole resident stack (`acpx __queue-owner` ->
`npm exec` -> `node <adapter>` -> agent binary). Make it the last line of every
scripted persistent run: forgotten owners hold ~700 MB each for hours, heartbeating
`queueDepth: 0` lock files.

- **Verify**: `pgrep -fl 'acpx __queue-owner|claude-agent-acp|codex-acp'` should print
  nothing once your runs are closed.
- **A straggler gets a plain `kill`, never `kill -9` on an owner.** acpx (0.15.1)
  kills the adapter by PID only - there is no process-group kill in the ACP session
  path - so SIGKILL on an owner strands `npm exec -> node -> <agent>` reparented to
  PID 1. `sessions close` (or plain SIGTERM) takes the whole stack with it.
- **Owners lingering with no `--ttl 0` on the command line**: check
  `~/.acpx/config.json` - its `ttl` key sets the default idle TTL, and `"ttl": 0`
  there disables the self-reap for every invocation.
- Closed records persist indefinitely; `sessions prune --older-than 7` on a cadence.

## MCP

`--mcp-config <path>` **replaces** the project/global `mcpServers` for that invocation
(relative paths inside resolve from `--cwd`) - and it is absent from the vendor doc
entirely.

**The file shape is not the standard one.** acpx wants a JSON *array* of named server
objects; the standard object-keyed map throws an uncaught Node stack trace:
`Error: Invalid mcpServers in <path>: expected array`.

```jsonc
// RIGHT - an array, each entry carrying its own name
{ "mcpServers": [ { "name": "example", "type": "stdio", "command": "example", "args": ["mcp"] } ] }
```

**A stdio server that dies only under agy is an MCP era mismatch, not an acpx fault.**
agy probes stdio with `server/discover` (MCP 2026-07-28 retired the `initialize`
handshake); a legacy server that *aborts* on the unexpected request kills the pipe
instead of answering an error, leaving nothing to fall back from:
`MCP load failed for <name>: ... expect initialized request, but received: ...
"server/discover"`. The codex and claude adapters do not probe, which is the only
reason the same config works for them. Fix the server (answer an error, or move to a
current MCP SDK), or reach it over HTTP. The turn still exits **0** and ends
`[done] end_turn` - grep for `MCP load failed` before trusting any run that used MCP.

- **A live queue owner refuses a config change** (it carries the config path plus a
  SHA-256 fingerprint): `sessions close` first.
- **`--mcp-config` replaces the whole set** - verify a config written for one adapter
  on another with a one-shot `exec` that asks the agent to name its own tools.
- `${...}` in an MCP config expands in the **launcher's** environment (the child
  inherits it), so a variable like a session id resolves to *your* id. Never let an
  identity flow in through the environment.

## Limits

- **Incoming ACP messages cap at 64 MiB** since 0.15.1 (previously unlimited);
  `ACPX_MAX_ACP_MESSAGE_BYTES` raises it, `0` disables.
- Terminal output retention is 64 KiB per call (`ACPX_TERMINAL_MAX_OUTPUT_BYTES`).
- Long unattended work: `--timeout 5400`, plus a wrapping shell `timeout` as
  belt-and-braces. Do NOT add `--ttl 0` - the 300s default covers any gap within one
  run, and `--ttl 0` removes the only automatic reaper (invariant 6). Reserve it for a
  human-driven warm session you will close by hand.
- `--format quiet` for fleets; `--suppress-reads` on every long run.
- Pass long briefs as `-f <path>` or a path in the prompt, never inlined - inlined
  content in a shell command is what a driving harness's classifier blocks on.

## What acpx cannot do

Structural, not bugs. Do not design around them.

- **An ACP session does not wake.** An externally injected message lands in the
  transcript but starts no turn; the only inbound channel is acpx itself
  (`-s <name>`, optionally `--no-wait`).
- **`codex queue --thread` does not reach an acpx-driven codex session** (it does wake
  a plain interactive codex).
- **acpx-spawned Claude sessions bind no IPC socket**, so `ListAgents` /
  `SendMessage` cannot see or reach them.
- **acpx cannot attach to a session it did not start.**

## Failures

Exit codes (absent from the vendor doc):

| code | meaning |
|---|---|
| 0 | success (also `cancel` with nothing to cancel) |
| 1 | agent / protocol / runtime error - the catch-all |
| 2 | usage error: bad or conflicting flags, malformed `--agent` |
| 3 | `--timeout` exceeded |
| 4 | no session found by the directory walk |
| 5 | every permission request denied or cancelled |
| 130 | interrupted (cooperative cancel first) |

Error catalog - string -> fix:

- `No acpx session found (searched up to <cwd>)` (exit 4) - invariant 2:
  `sessions ensure --name <n>` first; confirm `--cwd`.
- `error: unknown option '--cwd'` (exit 2) - global flag after the subcommand
  (invariant 1).
- `Do not combine positional agent with --agent override` (exit 2) - drop the
  positional `claude`/`codex`.
- `Invalid mcpServers in <path>: expected array` (uncaught stack trace) - see MCP.
- `Invalid value for config option model: <id> (ACP -32603, adapter reported
  "Internal error")` - `set model` outside the advertised list; use `--model` at
  session creation (see claude).
- `RUNTIME: Internal error: There's an issue with the selected model (<id>)` - the
  harness itself rejects the id: a real typo or an entitlement problem.
- `Internal error` from `claude set reasoning_effort` - no effort knob; expected.
- `[error] RUNTIME: Authentication required` - the agy ACP server was never
  authenticated; see agy.
- `502 Bad Gateway: Failed to connect to backend API` (agy, exit 0) - missing CA
  bundle on NixOS; see Linux / NixOS.
- `authenticate` never returns (agy, no error, no URL) - no `auth.type` in
  `~/.gemini/antigravity-acp/settings.json`; see agy.
- `RUNTIME: This client is no longer supported for Gemini Code Assist` - you used the
  built-in `gemini` agent; use `--agent` with the `.par`.
- `already has an active writer (code -32600)` - `codex resume` while acpx still owns
  the thread; `sessions close <n>` first.
- `Missing --skill action.` (exit 1) - `--skill` needs
  `show|list|install|export|help`.
- `error: unknown option '--one-shot'` (exit 2) - not a verb; `exec` is the one-shot
  form.
- Exit 3 = the wall clock ran out, not a stuck agent - check `sessions show` for
  `lastActivity`; an adapter-side timeout surfaces as exit 1 instead.

Silent failures worth an explicit check: content-filter kills and MCP load failures
both end `[done] end_turn` with exit 0; a `--no-wait` prompt that "sent" may still be
queued behind a running turn; `status` reads `running` long after completion; a
session whose cwd no longer exists lingers until pruned.
