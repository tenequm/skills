---
name: acpx-faq
description: Run coding agents (codex, claude, Antigravity/agy) headlessly through the acpx ACP CLI. Use before launching or prompting an acpx subagent, and when an acpx command fails, a session is not found, or a prompt seems lost.
metadata:
  version: "0.3.0"
  categories: "agents, operations"
  topics: "acpx, acp, agent-orchestration, troubleshooting, headless-agents"
  upstream: "acpx@0.15.1, agy@1.1.28, agy_acp_server@20260818_01_RC01"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/acpx-faq
    emoji: "🔌"
---

# acpx FAQ

Drive coding agents headlessly through [acpx](https://github.com/openclaw/acpx) (>= 0.15.1).
Command syntax: `acpx --skill show acpx` - the binary ships its own reference and is the
tiebreaker on syntax. That doc is strong on command shape and silent on failure semantics: it
has no exit-code table, no `status` state table, and does not mention `--mcp-config` at all.
This file is the other half.

Read the Invariants, then your agent's section in **Per agent** - each is a complete
launch-to-result recipe. After that: Sessions, Completion, MCP, Limits, Failures.

## Invariants

1. **Global flags precede the agent subcommand.** `--cwd`, `--model`, `--approve-all`,
   `--agent`, `--format`, `--timeout`, `--ttl`, `--mcp-config` are all global. The subcommand
   accepts only `-s`, `--no-wait`, `-f` (and `exec` also takes `--config-option`). Putting a
   global flag after the agent exits **2** with `error: unknown option '--cwd'`.
2. **`-s <name>` never creates a session.** It resolves one, walking from `--cwd` up to the
   git root. No match exits **4**. Create first with `sessions ensure --name <n>`.
3. **`status` is not a turn signal.** It reports the queue-owner process, not the turn, and
   keeps saying `running` after the turn has ended. Never gate automation on it.
4. **Permission flags only gate requests the adapter chooses to raise.** The claude adapter
   spawns its binary with `--allow-dangerously-skip-permissions --setting-sources=project,local`,
   so it never raises an ACP permission request and there is nothing for acpx to deny; codex
   writes through its terminal capability. `--deny-all` is not ignored, it is unreachable.
   Isolation comes from the `--cwd` you hand it, never from a flag.
5. **`[done] end_turn` and exit 0 are not proof of success.** A content-filter kill, an MCP
   load failure, or a truncated turn all end that way. Read the stream, or require the agent
   to write a result file you can check.

## Per agent

Each section is self-contained: flags, launch, and the quirks that bite while it runs.

### agy / Antigravity - the `--agent` escape hatch

**acpx has no Antigravity adapter and never will get one.** Issue #362 was closed as
externally blocked: Antigravity ships no supported ACP stdio mode. The built-in `gemini` agent
is the *public Gemini CLI*, a different product, and it is dead for Code Assist:

```
[error] RUNTIME: This client is no longer supported for Gemini Code Assist for individuals.
To continue using Gemini, please migrate to the Antigravity suite of products
```

The only route is Google's own signed ACP server, reached through the raw-command escape
hatch. **What the `.par` is:** installed by Antigravity under
`~/.local/lib/antigravity-acp/` and sha512-verified against Google's release manifest. Neither
acpx nor this skill downloads it - if it is missing, install Antigravity. It is a readable zip
of a Google-built Python runtime, pinned at build `agy_acp_server_20260818_01_RC01` because it
self-updates nothing. `localharness_external` ships beside it and must stay executable, or the
server starts anyway and only logs `Localharness not found`.

```bash
# macOS: --agent may point straight at the .par
D=/abs/real/dir                              # must exist: roots resolve through realpath
acpx --agent ~/.local/lib/antigravity-acp/agy_acp_server.par \
     --cwd "$D" --model gemini-3.7-flash-medium --timeout 1800 \
     exec 'Carry out $D/brief.md. Write your report to $D/report.md.'
```

**On Linux, `--agent` points at a wrapper, not at the `.par`** - the server needs `--uid=`
there (every ACP registry entry passes it for `linux-*`, none for `darwin-arm64`), and on NixOS
a CA bundle too. See Linux / NixOS below.

- **Default to `gemini-3.7-flash-medium`.** Measured on par with Opus for rubric-driven bulk
  work (99.5% verdict agreement across 213 items, and the better call on the one they disputed)
  and far faster; `gemini-3.8-flash-high` scored measurably worse on the same task despite
  being the bigger, higher-effort model. Pick another id only when a task argues for it.
- **Effort lives in the model id** - `gemini-3.7-flash-{low,medium,high}`,
  `gemini-3.8-flash-high`. This server exposes no separate effort option.
- **Auth is a settings file, not an env var.** `ACPX_AUTH_OAUTH_PERSONAL=1` is dead in build
  `20260818_01_RC01` - the `.par` carries the string *"Environment-based auth selection has
  been removed."* With no auth type configured the server does not error, it **hangs on
  `authenticate` forever**, which reads exactly like a network stall. Write the type first:

  ```bash
  mkdir -p ~/.gemini/antigravity-acp
  echo '{"auth":{"type":"oauth-personal"}}' > ~/.gemini/antigravity-acp/settings.json
  ```

  Types: `oauth-personal` (the subscription path, the one you want), `gemini-api-key`,
  `agent-platform`. Then sign in once; the token persists and later runs need nothing.
- **The OAuth browser opens silently; the URL is never printed.** Capture it with a fake
  `xdg-open` (or `open`) early on `PATH` that echoes its argument. The callback port is
  per-run: on a headless box, `curl '<callback-url>'` the redirect your browser could not
  deliver. A session created before auth finished stays broken - start a fresh one.
- **Never pass a positional agent with `--agent`** - exit **2**,
  `Do not combine positional agent with --agent override`.
- **This lane is subscription-backed. Leave the auth alone.** On the *CLI* side
  (`~/.gemini/settings.json`, a different file from the ACP server's above),
  `security.auth.selectedType: "oauth-personal"` is the Google subscription path and the
  intended default; there is no tier setting, and `agy` has no auth subcommand at all. If entitlement ever looks wrong it is a server-side lookup with no
  client-side lever - do not "fix" it by switching to `gemini-api-key` or a GCP project, which
  are separate billing arrangements rather than fixes.
- **Ask an agy verification prompt for a bare reply, and read the whole log.** agy will route
  an answer into a brain artifact file instead of the stream, so a `tail` shows you an
  `AbsolutePath` and nothing else and you cannot tell "no tools" from "answered elsewhere".
  Add "Do not create any files" and capture the full output.
- **agy hides MCP failures inside a successful-looking turn.** A failed server appears as
  inline text - `MCP load failed for <name>: ... expect initialized request, but received: ...
  "server/discover"` - in a stream that still ends `[done] end_turn` with exit 0. Grep the
  output for `MCP load failed`, do not trust the exit code.
- **The credential split is total, not just "two onboardings".** The server reads
  `~/.gemini/antigravity-acp/acp_token.json` and never looks at the CLI's
  `~/.gemini/antigravity-cli/antigravity-oauth-token`, so a fully authenticated `agy` does
  nothing for the ACP lane. Its own docstrings give the layout: `<GEMINI_HOME>/antigravity-acp/`
  holds `settings.json`, `acp_token.json`, `conversations/` and `brain/`, while
  `<GEMINI_HOME>/antigravity-cli/skills/` is shared across surfaces. Setting `GEMINI_HOME`
  relocates the whole tree - that is how you run a second isolated lane.

#### Linux / NixOS

Three differences from macOS, all silent.

1. **`--uid=` is required**, so `--agent` points at a wrapper rather than the `.par`
   (`~/.local/bin/agy-acp-server`):

   ```bash
   #!/usr/bin/env bash
   export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt   # NixOS; see 2
   exec ~/.local/lib/antigravity-acp/agy_acp_server.par --uid= "$@"
   ```

2. **Without that `SSL_CERT_FILE`, NixOS gets a 502.** The `.par` embeds a Google-built Python
   and OpenSSL whose compiled-in CA paths do not exist there, so every handshake with
   `cloudcode-pa.googleapis.com` fails. Its local proxy (`ccpa_connection/proxy_server.py`)
   swallows that and reports `502 Bad Gateway: Failed to connect to backend API`, and the turn
   still ends `[done] end_turn` with **exit 0** - invariant 5 with a concrete signature. The
   real `CERTIFICATE_VERIFY_FAILED` appears only under `--alsologtostderr`.
3. **Install `agy` by hand, not by piping the installer to a shell.** Its last step runs
   `agy install`, which appends PATH blocks to `~/.bashrc` and `~/.profile` - useless when
   `~/.local/bin` is already on PATH via home-manager, and broken when `~/.zshrc` is a
   read-only nix-store symlink. Both binaries link against `/lib64/ld-linux-x86-64.so.2`,
   which resolves through nix-ld; no patchelf needed.

Working invocation:

```bash
acpx --agent ~/.local/bin/agy-acp-server \
     --cwd "$D" --model gemini-3.7-flash-medium \
     --approve-all --timeout 1800 exec '<prompt>'
```

### codex

```bash
D=/abs/dir
acpx --cwd "$D" codex sessions ensure --name work            # idempotent; -s cannot create
acpx --cwd "$D" codex set model gpt-5.6-sol -s work          # -> model set: gpt-5.6-sol
acpx --cwd "$D" codex set reasoning_effort high -s work      # -> config set: ... (5 options)
acpx --cwd "$D" --approve-all --timeout 5400 --ttl 0 --format quiet --suppress-reads \
     codex -s work 'Carry out ./brief.md. Write your report to ./report.md.' > run.log 2>&1 &
```

For a one-shot, skip the session entirely - `exec --config-option` sets model and effort
inline (0.14.0+), applied after `--model` and before the prompt:

```bash
acpx --cwd "$D" --timeout 1800 codex exec --config-option reasoning_effort=low 'Summarize ./DESIGN.md'
```

- **The adapter floats.** `@agentclientprotocol/codex-acp@^1.1.5` is a caret on a 1.x, so it
  tracks the latest 1.x on every `npx` resolution. A codex-side change can land without you
  upgrading acpx.
- **OpenAI's content filter kills benign turns** and the turn ends looking clean
  (`[done] end_turn`, exit 0). Vocabulary like race / sweep / exploit / attack in a filename,
  comment or prompt triggers it. Read the transcript tail for the flag line before believing
  completion. Recover by re-prompting the same `-s <name>` (context survives): rename the
  artifact neutrally and list the remaining steps explicitly.
- **Queue a follow-up onto a live session** by prompting the same name again - it runs after
  the current turn rather than interrupting. This is how you course-correct a running executor
  without relaunching it.
- **Headful takeover:** `sessions show <n>` prints a `sessionId` that is the ordinary codex
  rollout id, so `codex resume <sessionId>` opens the same thread in a TUI with model and
  effort intact. **Close first** - `sessions close <n>` - or you get
  `already has an active writer (code -32600)`.
- `codex queue --thread` does **not** reach an acpx-driven session (see What acpx cannot do).

### claude

```bash
D=/abs/dir
acpx --cwd "$D" --model claude-opus-5 claude sessions ensure -s work
acpx --cwd "$D" --model claude-opus-5 --approve-all --suppress-reads --timeout 2400 \
     claude -s work -f /abs/brief.md >> run.log 2>&1 &
```

- **No effort knob.** `set reasoning_effort` returns `Internal error`. Only the model id.
- **`--model` and `set model` validate differently, and this surprises people.** The adapter
  advertises `["default","opus[1m]","claude-fable-5[1m]","sonnet","haiku"]`, and `set model`
  refuses anything outside that list:
  `Invalid value for config option model: claude-opus-5 (ACP -32603, adapter reported "Internal error")`.
  The global `--model` at session creation passes the id through to the harness instead, so
  `--model claude-opus-5` works fine. A genuinely unknown id still fails loudly:
  `RUNTIME: Internal error: There's an issue with the selected model (<id>)`.
- **Fable runs**: `--model 'claude-fable-5[1m]'` (quote it - the brackets are shell globs).
- **User-scope skills are excluded on purpose.** The adapter loads project and local settings
  but not user settings, so a user-level skill or slash command comes back
  `Unknown command: /polish`. Fix with `ACPX_CLAUDE_INCLUDE_USER_SETTINGS=1` - and settings
  bind at **session creation**, so an existing session must be recreated, not re-prompted.
- **Second account:** export `CLAUDE_CONFIG_DIR` and `CLAUDE_SECURESTORAGE_CONFIG_DIR` before
  `acpx`; the child inherits them. That is the whole mechanism for driving another lane.
- **The adapter is pinned far behind your CLI.** `claude-agent-acp@^0.60.0` resolves to exactly
  0.60.0, which pins `@anthropic-ai/claude-agent-sdk@0.3.215`, which bundles claude **2.1.215**
  - regardless of the version on your PATH. Consequences: the bundled binary predates the
  cross-session messaging socket, so these sessions are unreachable by peer messaging, and any
  newer harness feature is simply absent. Override with `--agent` pointed at a newer adapter
  build if you need one.
- A **session-creation stall** is a known adapter combination bug; acpx's own error text
  recommends `--approve-all` with `nonInteractivePermissions=deny`, upgrading both sides, or
  falling back to `claude exec` as a one-shot.

## Sessions

A session is keyed on **(agent command, absolute cwd, optional name)**. Because `cwd` is part
of the key, parallel executors each need their own directory - give every one its own git
worktree and their per-session model and effort settings cannot race.

| verb | behavior |
|---|---|
| `sessions ensure --name <n>` | returns the existing session or creates one - idempotent, safe before every prompt |
| `sessions new --name <n>` | soft-closes any current session and creates a fresh one (`(replaced <id>)`) |
| a bare prompt with `-s <n>` | never auto-creates; exits **4** with `Create one: ...` |
| `sessions show <n>` | `lastActivity`, `lastPrompt`, `historyEntries`, `sessionId`, `closed` |
| `sessions history <n> --limit N` | the actual turn content |
| `sessions close <n>` | releases the agent; required before `codex resume` and before `sessions export` |
| `sessions list --local` | local records including closed ones |
| `sessions prune` | deletes closed records - they persist indefinitely otherwise |

Resolution without `-s` walks from `--cwd` up to the git root. A session whose cwd you have
since deleted becomes an unreachable registry row: `sessions close` cannot target it without
its cwd, so prune it.

## Completion

**Never poll `status`.** It is a local `kill(pid,0)`-style check on the queue owner and never
touches the agent. Its states are `running`, `idle`, `dead`, `no-session`, where `dead` means
the owner is gone or the last exit was abnormal. A turn that finished seconds ago still reads
`running`, because the owner survives for its idle TTL (default **300s**, `--ttl <seconds>`,
`--ttl 0` to keep it forever). A loop waiting for `idle` will spin past real completion and
time out.

What is actually correct:

- the foreground stream's terminating `[done] end_turn`, plus the process exit code;
- `sessions show <n>` (`lastActivity`, `historyEntries`) and `sessions history <n>`;
- best of all, a **result file** the brief required the agent to write - poll for the file.

`--no-wait` returns as soon as the queue owner **acknowledges** the submission - `[queued]
<id>` in well under a second, even on an idle session. It is not delivery and not completion:
if a turn is already running, the prompt waits for the turn boundary. Background a normal
blocking prompt when you want the transcript; use `--no-wait` only to enqueue.

Supervising a backgrounded run: count tool lines and check mtime
(`rg -c '^\[tool\]' run.log`, `stat -f '%Sm' run.log`) rather than tailing the whole log, and
check liveness with `pgrep -fl 'acpx|codex-acp|claude-agent-acp'`.

`Ctrl+C` (and the `cancel` subcommand) sends ACP `session/cancel` first and force-kills only
if the agent does not stop in time.

## MCP

`--mcp-config <path>` **replaces** the project/global `mcpServers` for that invocation;
relative paths inside resolve from `--cwd`.

**The file shape is not the one every other tool uses.** acpx wants a JSON *array* of named
server objects. Handing it the standard object-keyed map throws an uncaught Node exception
with a stack trace, not a clean CLI error:

```
Error: Invalid mcpServers in /path/to/config.json: expected array
    at parseMcpServers (.../acpx/dist/cli.js:1393)
```

```jsonc
// WRONG - the Claude Code / standard shape
{ "mcpServers": { "example": { "command": "example", "args": ["mcp"] } } }

// RIGHT - an array, each entry carrying its own name
{ "mcpServers": [ { "name": "example", "type": "stdio", "command": "example", "args": ["mcp"] } ] }
```

### stdio is the normal case

Most MCP servers are stdio, and acpx passes them straight through - one entry, nothing to run:

```jsonc
{ "mcpServers": [ { "name": "example", "type": "stdio", "command": "example", "args": ["mcp"] } ] }
```

**If a stdio server dies only under agy, it is an MCP era mismatch, not an acpx fault.** Since
MCP 2026-07-28 (SEP-2575) the `initialize`/`initialized` handshake is retired, and a dual-era
client is told to probe stdio with `server/discover` first and fall back to `initialize` when
the answer is not a modern one. A conforming legacy server replies with an error and the
fallback happens; one that *aborts* on the unexpected request kills the pipe instead, leaving
the client nothing to fall back from:

```
MCP load failed for <name>: Error: failed to start stdio MCP server
Caused by: expect initialized request, but received: ... method: "server/discover"
: connection closed: calling "initialize": client is closing: EOF
```

agy probes; the codex and claude adapters do not, which is the only reason the same config
works for them. The fix belongs in the server (answer an error rather than exiting, or move it
to a current MCP SDK). Reaching it over HTTP also sidesteps it, since there the probe is just
one failed request rather than a dead process.

That turn still exits **0** and ends `[done] end_turn` - the failure is inline text, not an
error. Grep for `MCP load failed` before trusting any run that used MCP.

Two more traps:

- **A live queue owner refuses a config change.** The owner carries the config path and a
  SHA-256 fingerprint; switching MCP config on a persistent session requires
  `sessions close` first.
- **`--mcp-config` replaces the whole set**, so a config written for one adapter is not
  automatically right for another. Verify with a one-shot `exec` that asks the agent to name
  its own tools before dispatching real work.

`${...}` expansion inside an MCP config is evaluated in the **launcher's** environment,
because the acpx child inherits it - so a variable like a session id resolves to *your* id,
not the child's. Never let an identity flow in through the environment.

## Limits

- **Incoming ACP messages are capped at 64 MiB** since 0.15.1 (previously unlimited). Raise
  with `ACPX_MAX_ACP_MESSAGE_BYTES`, or `0` to disable. A previously-working large-payload
  script can start failing here.
- Terminal output retention is 64 KiB per call; `ACPX_TERMINAL_MAX_OUTPUT_BYTES` adjusts it.
- `--timeout <seconds>` is the wall clock for the whole prompt. Long unattended work wants
  `--timeout 5400 --ttl 0`; a wrapping shell `timeout` is a reasonable belt-and-braces.
- Output: `--format quiet` for many backgrounded executors, `text` for one you are watching,
  `json` (with `--json-strict`) when a script parses it. `--suppress-reads` keeps read-file
  contents out of the log and is worth setting on every long run.
- Pass long briefs with `-f <path>` or a path in the prompt, not inlined text: it keeps the
  content out of the shell command, where a driving harness's classifier may block on it.

## What acpx cannot do

Structural, not bugs. Do not design around them.

- **An ACP session does not wake.** An externally injected message lands in the transcript but
  starts no turn, because under ACP the turn loop belongs to the ACP client. The only inbound
  channel to an acpx session is acpx itself (`-s <name>`, optionally `--no-wait`).
- **`codex queue --thread` does not reach an acpx-driven codex session**, though it does wake a
  plain interactive codex. The ACP wrapper is not in the app-server's context.
- **acpx-spawned Claude sessions bind no IPC socket** (`entrypoint: sdk-cli`, no key file), so
  `ListAgents` / `SendMessage` cannot see or reach them.
- **acpx cannot attach to a session it did not start.** It owns the process it drives; a
  human-started headful session is out of reach.
- **Permission flags are not a sandbox.** See invariant 4: the claude adapter already passed
  `--allow-dangerously-skip-permissions` to its binary, so no permission request ever reaches
  acpx's policy layer. Verify it yourself with `ps -Ao args | grep claude-agent-sdk` during a
  turn. `--no-terminal` genuinely removes the terminal capability (an agent that calls it gets
  a hard error), but for filesystem safety the only real control is which `--cwd` you hand it.

## Failures

Exit codes, which the shipped doc does not list:

| code | meaning |
|---|---|
| 0 | success (also `cancel` with nothing to cancel) |
| 1 | agent / protocol / runtime error - the catch-all |
| 2 | usage error: bad or conflicting flags, malformed `--agent` |
| 3 | `--timeout` exceeded |
| 4 | no session found by the directory walk |
| 5 | every permission request denied or cancelled, none approved |
| 130 | interrupted (cooperative cancel first) |

**`⚠ No acpx session found (searched up to <cwd>).`** (exit 4) - invariant 2. Emitted by
`set`, by `-s` prompts, by anything that resolves a session. Fix:
`sessions ensure --name <n>` first. Confirm `--cwd` is the directory you think it is.

**`error: unknown option '--cwd'`** (exit 2) - a global flag placed after the agent
subcommand. Move it before.

**`Do not combine positional agent with --agent override`** (exit 2) - drop the positional
`claude`/`codex` when `--agent` supplies the adapter.

**`Invalid mcpServers in <path>: expected array`** (uncaught, stack trace) - the MCP config is
the standard object map; convert it to an array. See MCP.

**`Invalid value for config option model: <id> (ACP -32603, adapter reported "Internal error")`**
- `set model` with an id outside the adapter's advertised list. Use `--model` at session
creation, or pick an advertised id from `--format json ... status`.

**`RUNTIME: Internal error: There's an issue with the selected model (<id>)`** - the harness
itself rejects the id. This is a real typo or an entitlement problem, not the previous case.

**`Internal error`** from `claude set reasoning_effort` - there is no effort knob on the
claude adapter. Expected; ignore.

**`[error] RUNTIME: Authentication required`** - the agy ACP server has never been
authenticated. Write `auth.type` into `~/.gemini/antigravity-acp/settings.json`, then complete
its own sign-in; the CLI's token does not count. See agy.

**`502 Bad Gateway: Failed to connect to backend API`** (agy ACP, turn still ends
`[done] end_turn` exit 0) - the server's local proxy could not reach
`cloudcode-pa.googleapis.com`. On NixOS this is a missing `SSL_CERT_FILE`, not a network or
model problem; confirm with `--alsologtostderr` and look for `CERTIFICATE_VERIFY_FAILED`.

**`authenticate` never returns** (agy ACP, no error, no URL) - no `auth.type` in
`~/.gemini/antigravity-acp/settings.json`. `ACPX_AUTH_OAUTH_PERSONAL=1` no longer selects
anything in this build.

**`RUNTIME: This client is no longer supported for Gemini Code Assist for individuals`** - you
used the built-in `gemini` agent. It is the public Gemini CLI, not Antigravity; use `--agent`
with the `.par` server.

**`already has an active writer (code -32600)`** - `codex resume` while acpx still owns the
thread. `sessions close <n>` first.

**`Missing --skill action.`** (exit 1) - `--skill` needs `show`, `list`, `install`, `export`
or `help`.

**`error: unknown option '--one-shot'`** (exit 2, usage on **stderr**) - not a verb; `exec` is
the one-shot form.

**Timeouts** (exit 3) mean the wall clock ran out, not that the agent is stuck. Check
`sessions show` for `lastActivity` before assuming failure, and remember an adapter-side
timeout surfaces as exit 1 instead.

Silent failures worth an explicit check: a content-filter kill and an MCP load failure both
end `[done] end_turn` with exit 0; a `--no-wait` prompt that "sent" may still be queued behind
a running turn; `status` reporting `running` long after completion; and a session record whose
cwd no longer exists lingering until pruned.
