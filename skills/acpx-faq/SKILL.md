---
name: acpx-faq
description: Run coding agents (codex, claude, agy/Antigravity) through the acpx ACP CLI - the headless lane outside a herdr pane (no HERDR_ENV). Use before launching or prompting a subagent, and when a command fails, a session is not found, or a prompt is lost.
metadata:
  version: "0.6.1"
  categories: "agents, operations"
  topics: "acpx, acp, agent-orchestration, troubleshooting, headless-agents"
  upstream: "acpx@0.19.1, @agentclientprotocol/claude-agent-acp@0.76.0, agy@1.2.8, agy_acp_server@1.1.1"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/acpx-faq
    emoji: "🔌"
---

# acpx FAQ

Drive coding agents headlessly through [acpx](https://github.com/openclaw/acpx) (>= 0.19.1).

## Syntax authority

Syntax comes from the binary, not this file. `acpx --skill show acpx` is the vendor
reference (~39k chars) and the tiebreaker on command shape - do NOT dump it into the
transcript. Retrieve in this order:

1. `acpx --help` / `acpx <cmd> --help` - the flags you are about to compose.
2. One topic: `acpx --skill show acpx | rg -B2 -A12 '<term>'`, or a section:
   `acpx --skill show acpx | sed -n '/^## Sessions/,/^## /p'`.
3. Authoring something novel (a flow, an embedded runtime): dump ONCE to a scratch
   file and grep that file.

This file repeats nothing the reference covers. It carries only what the reference
lacks: exit codes, failure semantics, traps, and per-agent recipes. If a syntax
question is not answered here, it is answered there - go get it, never guess a flag.
The repo's `docs/` (exit-codes, session-control, config) cover some of what the
shipped reference omits.

## When this lane

acpx is the headless out-of-process executor lane. Inside a herdr pane (`HERDR_ENV=1`)
prefer herdr (herdr-faq): it gives you screen reads and dialog detection. Everywhere
else (plain terminal, ssh, cron) herdr is untargetable and acpx is the lane.
In-session fan-out stays on the harness's own subagent tool.

## Invariants

1. **Global flags precede the agent subcommand** (`--cwd`, `--model`, `--approve-all`,
   `--agent`, `--format`, `--timeout`, `--ttl`, `--mcp-config`). The subcommand accepts
   only `-s`, `--no-wait`, `-f` (and `exec` also `--config-option`). A global flag
   after the agent exits **1** with `error: unknown option`; a bad flag *before* the
   agent exits **2**.
2. **`-s <name>` never creates a session.** It resolves one, walking from `--cwd` up
   to the nearest `.git` - a directory *or file*, so each worktree and submodule is its
   own boundary; outside git only the exact `--cwd` is checked. No match exits **4**.
   Create first with `sessions ensure --name <n>` in the same directory.
3. **`status` is not a turn signal.** It probes the queue-owner process, never the
   agent, and keeps saying `running` after the turn has ended. Never gate automation
   on it.
4. **Permission flags are not a sandbox.**
   - **claude**: the adapter starts in `permissions.defaultMode` from the Claude
     settings (`acceptEdits` / `auto` approve edits without asking). Only what that
     mode escalates reaches acpx as a permission request - `--deny-all` refuses those
     (exit 5), but an auto-approved edit never asks.
   - **codex**: writes inside its workspace-write sandbox (rooted at `--cwd`, plus temp
     dirs) raise no request, so `--deny-all` still writes; outside fails with
     `Operation not permitted`. Network is off unless `config.toml` enables
     `network_access`. `--approve-all` does not change the adapter's mode
     (`INITIAL_AGENT_MODE=read-only|agent|agent-full-access` does).

   The real filesystem control is which `--cwd` you hand it.
5. **`[done] end_turn` and exit 0 are not proof of success.** A content-filter kill,
   an MCP load failure, or a truncated turn all end that way. Read the stream, or
   require the agent to write a result file you can check.
6. **A persistent session leaves a resident process stack until you close it.** Every
   `-s` prompt elects a queue owner holding `npm exec -> node <adapter> -> <agent>`
   (plus the agent's MCP servers), roughly 550-650 MB before MCP. `sessions close` is
   the supported teardown; the idle TTL (default 300s) is the backstop, and `--ttl 0`
   removes it. See Teardown.

## Per agent

**Default to `exec` for dispatched work.** `exec` runs a temporary session: no saved
record, not queue-aware, so it never elects a queue owner and leaves nothing to clean
up. Use `-s <name>` only to queue follow-ups onto a live run or to read
`sessions history` afterwards - and then the closing `sessions close` is part of the
recipe (invariant 6). One directory (ideally one worktree) per parallel executor:
sessions key on cwd.

Adapters run through `npm exec`. A fresh HOME per job re-downloads them (hundreds of
MB each); share one `npm_config_cache`. The npx cache also reuses stale builds -
pin exact adapter versions in `~/.acpx/config.json` (`agents.<name>.argv`).

### agy / Antigravity

The built-in `acpx antigravity` (0.17.1+) runs `agy_acp_server.par` **from PATH**,
and the copy Antigravity installs under `~/.local/lib/antigravity-acp/` is not on
PATH - bare `acpx antigravity` exits 1 with `Failed to spawn agent command:
agy_acp_server.par`. Prepend that directory to PATH, set `agents.antigravity.argv`,
or use `--agent <path>`. The built-in `gemini` agent is the *public Gemini CLI* - a
different product. The `.par` comes from the Antigravity install or the official ACP
registry archive; keep it beside its `localharness_external` helper from the same
release (a missing helper only logs `Localharness not found.` and carries on).

```bash
D=/abs/real/dir                              # must exist: roots resolve through realpath
acpx --agent ~/.local/lib/antigravity-acp/agy_acp_server.par \
     --cwd "$D" --model gemini-3.7-flash-medium --approve-all --timeout 1800 \
     exec "Carry out $D/brief.md. Write your report to $D/report.md."
```

- **`--approve-all` is mandatory.** Without it every write is refused: exit 5 (or a
  stall to exit 3), with `[done] end_turn` still printed and no report.
- **Fixed-choice questions fail the prompt with exit 5 even under `--approve-all`**
  (final line `Antigravity requested a user answer...`) - for `--agent` launches too.
  Write briefs that never need a user choice.
- **Default `gemini-3.7-flash-medium`** - on par with Opus for rubric-driven bulk work
  and far faster, but it misses real findings in review / bug-hunting work; use a
  stronger model there. Effort lives in the model id (`gemini-3.7-flash-{low,medium,high}`).
  Use only ids the ACP session advertises: a deliberately bad `--model` prints
  `Available models:` without starting a turn. `agy models` is a different list.
- **agy reads sibling files unprompted** - agents sharing a directory reproduce each
  other's output. One directory per agent, and checksum any rerun before believing an
  agreement number.
- **Auth: needs `auth.type` in `<GEMINI_HOME>/antigravity-acp/settings.json`** (one-time):

  ```bash
  mkdir -p ~/.gemini/antigravity-acp
  echo '{"auth":{"type":"oauth-personal"}}' > ~/.gemini/antigravity-acp/settings.json
  ```

  Without it: immediate `[error] RUNTIME: Authentication required` (exit 1). With it
  but never signed in: `session/new` blocks on a browser sign-in until `--timeout`
  (exit 3) - sign in once interactively. The server's credential is separate from the
  `agy` CLI's: the macOS Keychain (service `gemini`, account `antigravity-acp`), or
  `<GEMINI_HOME>/antigravity-acp/acp_token.json` off macOS or with
  `AGY_ACP_FORCE_FILE_STORAGE=1`. `GEMINI_HOME` alone does not isolate the macOS
  credential. An entitlement problem is server-side - do not "fix" it by switching to
  `gemini-api-key` or a GCP project (separate billing, not fixes).
- **Never pass a positional agent with `--agent`** - exit **2**.
- **Verification prompts: demand a bare reply and read the whole log.** agy routes
  answers into brain artifact files, so a `tail` cannot tell "no tools" from
  "answered elsewhere". Add "Do not create any files".
- **agy hides MCP failures inside a successful-looking turn** - exit 0, `[done]
  end_turn`, and the whole reply is `The MCP server '<name>' failed to initialize: ...`.
  Grep for `failed to initialize`.
- **Prefer `exec`.** A server death mid-checkpoint has been reported to break a saved
  conversation for good (`could not find doneCh for checkpoint`); the only reported
  recovery is deleting `~/.gemini/antigravity-acp/conversations/<id>.db`.

#### Linux / NixOS

The built-in agent adds the required `--uid=` itself. NixOS additionally needs a CA
bundle, so point `--agent` (or `agents.antigravity.argv`) at a wrapper
(`~/.local/bin/agy-acp-server`):

```bash
#!/usr/bin/env bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
exec ~/.local/lib/antigravity-acp/agy_acp_server.par --uid= "$@"
```

Without `SSL_CERT_FILE` the `.par`'s embedded OpenSSL has no valid CA paths; its local
proxy reports `502 Bad Gateway: Failed to connect to backend API` and the turn still
ends `[done] end_turn` with **exit 0** (invariant 5). The real
`CERTIFICATE_VERIFY_FAILED` appears only under `--alsologtostderr`.

### codex

```bash
D=/abs/dir
acpx --cwd "$D" codex sessions ensure --name work            # idempotent; -s cannot create
acpx --cwd "$D" codex set model gpt-5.6-sol -s work
acpx --cwd "$D" codex set reasoning_effort high -s work
acpx --cwd "$D" --approve-all --timeout 5400 --suppress-reads \
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
- **MCP servers still starting when codex builds its tool list are dropped** (1s shared
  grace). `mcp_optional_startup_grace_ms = 0` in `config.toml` waits for each server's
  own `startup_timeout_sec` instead.

### claude

```bash
D=/abs/dir
acpx --cwd "$D" --model claude-opus-5 claude sessions ensure -s work
acpx --cwd "$D" claude set effort high -s work                 # optional; after any model change
acpx --cwd "$D" --model claude-opus-5 --approve-all --suppress-reads --timeout 2400 \
     claude -s work -f /abs/brief.md >> run.log 2>&1 &
# ...after the run finishes and you have read what you need:
acpx --cwd "$D" claude sessions close work  # ALWAYS - the run is not over until this returns
```

- **Effort is `set effort <level>`**; `set reasoning_effort` is the codex name and
  returns `Internal error` on claude. A model switch resets effort - set model first.
- **Pass the model with `--model <exact id>` at session creation.** `set model`
  fuzzy-matches against the adapter's advertised list and can silently land on a
  different entry (e.g. `opus[1m]`); only an id with no match fails
  (`Invalid value for config option model`). An unknown `--model` fails with
  `RUNTIME: Model '<id>' not found`. Quote ids with brackets (`'...[1m]'`) - globs.
- **Fable runs**: `--model 'claude-fable-5[1m]'`. It is absent from the advertised
  list, but `--model` forwards it as given (adapters 0.76.0 and 0.81.0).
- **The bundled Claude Code is whatever the adapter pins.** Built-in adapter
  `^0.76.0` = Claude Code 2.1.257, and a caret on 0.x locks the minor, so upgrading
  acpx does not reach newer builds. `claude-opus-5-5` needs 2.1.280+ (`Claude Code
  2.1.257 does not support this model`) - pin a newer adapter:
  `{"agents":{"claude":{"argv":["npx","-y","@agentclientprotocol/claude-agent-acp@0.81.0"]}}}`
  in `~/.acpx/config.json`. Any command containing `claude-agent-acp` keeps acpx's
  claude handling.
- **User settings are excluded on purpose** - user skills are missing (`/polish`
  "isn't available"). Fix with `ACPX_CLAUDE_INCLUDE_USER_SETTINGS=1` - and settings
  bind at session **creation**, so recreate the session, do not re-prompt it. A
  `--cwd` under `$HOME` still loads `~/.claude/CLAUDE.md` through the ancestor
  CLAUDE.md walk.
- **Second account**: export `CLAUDE_CONFIG_DIR` and `CLAUDE_SECURESTORAGE_CONFIG_DIR`
  before `acpx`; the child inherits them.

## Sessions

- Sessions key on **(agent command, absolute cwd, optional name)** - parallel
  executors need their own directories, which also keeps per-session model and effort
  settings from racing.
- `sessions close` is the teardown verb: marks the record closed, sends ACP
  `session/close`, takes down the owner and adapter processes (see Teardown). Also
  required before `codex resume` and `sessions export`.
- `sessions list` asks the *agent* by default; `sessions list --local` lists acpx's
  own records (with their cwds).
- A session whose cwd you deleted still closes with `--cwd <old path>`.
- `sessions new|ensure --resume-session <id>` binds a record to an existing ACP
  session - take `sessionId:` from `sessions show`, not `id:` (they diverge; the wrong
  one fails `Failed to resume ACP session <id>: Internal error`). It cannot attach to
  a live process.

## Completion

`status` states (the shipped reference has no state table): `running` (JSON: `alive`
- the owner's socket answers), `idle` (no owner, including one that was killed),
`dead` (an owner lease remains but is unhealthy, or the recorded exit was abnormal),
`no-session`. `running` holds for the whole idle TTL after a turn ends - a loop
waiting for `idle` spins past real completion (invariant 3). What is actually correct:

- `acpx <agent> sessions watch -s <n>`: its `turn_result` event (`completed`,
  `cancelled`, `failed`) is the settlement signal. `WATCH_OUTCOME_UNKNOWN` means the
  owner died mid-turn - the prompt may have run; check before resubmitting;
- the foreground stream's terminating `[done] end_turn`, plus the process exit code;
- `sessions show <n>` (`lastActivity`, `historyEntries`), `sessions history <n>`, and
  `sessions read <n> --tail N` (shows in-flight tool calls);
- best: a **result file** the brief required the agent to write - poll for the file.

`--no-wait` acknowledges enqueueing (`[queued] <id>`), which is neither delivery nor
completion - behind a running turn the prompt waits for the turn boundary.

Supervise a backgrounded text-format run by counting tool lines and mtime
(`rg -c '^\[tool\]' run.log`, `stat -f '%Sm' run.log`). `--format quiet` prints only
the final text (plus an `[acpx] tokens:` line on stderr) - no `[tool]`, no `[done]` -
so those counts read 0; supervise quiet runs by exit code and result file.

## Teardown

`sessions close <n>` takes down the whole resident stack (owner -> `npm exec` ->
`node <adapter>` -> agent binary -> its MCP servers). Make it the last line of every
scripted persistent run: forgotten owners hold hundreds of MB each for hours.

Liveness and leak check - never `pgrep -l` or `ps -o args`: command lines of wrapper
shells can carry secrets, and the bracketed first letter keeps the pattern from
matching the shell that runs it (Linux `pgrep` matches its ancestors):

```bash
PAT='[a]cpx.*__queue-owner|[c]odex-acp|[c]laude-agent-acp|[a]gy_acp_server|[l]ocalharness_external'
pgrep -f "$PAT" | wc -l                                      # 0 once your runs are closed
P=$(pgrep -d, -f "$PAT") && ps -o pid,ppid,etime,rss,comm -p "$P"   # no args column
```

- `close` returns before `npm exec` / `node` exit - poll for ~10s before calling
  anything a straggler. Other people's runs count too; scope with
  `lsof -a -d cwd -Fn -p <pid>` (adapter and agent run in `--cwd`).
- **A straggler gets a plain `kill <owner pid>`**; SIGTERM takes the stack down within
  seconds. Since 0.19 even SIGKILL no longer strands the adapter (it exits on stdin
  EOF), but a mid-turn kill loses the turn: `Queue owner disconnected before prompt
  completion; outcome unknown`.
- **Owners lingering with no `--ttl 0` on the command line**: check
  `~/.acpx/config.json` - its `ttl` key sets the default idle TTL, and `"ttl": 0`
  there disables the self-reap for every invocation.
- **Close owners started by an older acpx before upgrading** - 0.19 refuses forced
  retirement of legacy owners it cannot verify (`QUEUE_SHARED_RUNTIME_UNSUPPORTED`:
  wait for idle expiry or close).
- Closed records persist indefinitely; `sessions prune --older-than 7` on a cadence.

## MCP

`--mcp-config <path>` **replaces** the project/global `mcpServers` for that invocation.
The file path resolves against `--cwd` (the last `--cwd` / `--mcp-config` wins); paths
*inside* the file are passed verbatim. The shipped reference does not mention it.

**The file shape is not the standard one.** acpx wants a JSON *array* of named server
objects; the standard object-keyed map fails with
`Invalid mcpServers in <path>: expected array` (exit 1). `env` and `headers` are
arrays of `{name, value}` too; a missing `type` means stdio.

```jsonc
// RIGHT - an array, each entry carrying its own name
{ "mcpServers": [ { "name": "example", "type": "stdio", "command": "example", "args": ["mcp"],
                    "env": [ { "name": "LOG_LEVEL", "value": "info" } ] } ] }
```

**A stdio server that dies only under agy is an MCP era mismatch, not an acpx fault.**
agy probes stdio with `server/discover` (MCP 2026-07-28 retired the `initialize`
handshake); a legacy server that *aborts* on the unexpected request kills the pipe
instead of answering an error, leaving nothing to fall back from. The codex and claude
adapters do not probe, which is the only reason the same config works for them. Fix
the server (answer an error, or move to a current MCP SDK), or reach it over HTTP.
The turn still exits **0** and ends `[done] end_turn` - grep for
`failed to initialize` before trusting any agy run that used MCP.

- **A live queue owner refuses a config change** (it carries the config path plus a
  SHA-256 fingerprint): `sessions close` first.
- **`--mcp-config` replaces the whole set** - verify a config written for one adapter
  on another with a one-shot `exec` that asks the agent to name its own tools.
- acpx does no `${...}` expansion; whatever the agent expands resolves in the
  environment it inherited from the **launcher**, so a variable like a session id
  resolves to *your* id. Never let an identity flow in through the environment.

## Limits

- **Incoming ACP messages cap at 64 MiB** since 0.15.1 (previously unlimited);
  `ACPX_MAX_ACP_MESSAGE_BYTES` raises it, `0` disables.
- Terminal output retention defaults to 64 KiB per call when the agent sets no limit;
  `ACPX_TERMINAL_MAX_OUTPUT_BYTES` is a host ceiling that can only lower it.
- Long unattended work: `--timeout 5400`, plus a wrapping shell `timeout` with a
  margin (acpx drains and cleans up past its own deadline). Exit 3 leaves partial,
  uncommitted work in the cwd - a relaunch prompt should say so. Do NOT add
  `--ttl 0` - the 300s default covers any gap within one run, and `--ttl 0` removes
  the only automatic reaper (invariant 6). Reserve it for a human-driven warm session
  you will close by hand.
- `--format quiet` for fleets you judge by exit code and result file;
  `--suppress-reads` on every long run.
- Headless permission requests nobody can answer are denied; if every request was
  denied the run exits **5**. `--non-interactive-permissions fail` stops at the first
  one instead (`Permission prompt unavailable in non-interactive mode`).
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
- **acpx cannot attach to a live process it did not start** (`--resume-session` loads
  a saved ACP session into a new adapter; see Sessions).

## Failures

Exit codes (absent from the shipped reference; repo `docs/exit-codes.md` has them):

| code | meaning |
|---|---|
| 0 | success (also `cancel` with nothing to cancel) |
| 1 | agent / protocol / runtime error - the catch-all; also a global flag after the agent |
| 2 | usage error before the agent: bad or conflicting flags, malformed `--agent` |
| 3 | `--timeout` exceeded |
| 4 | no session found by the directory walk |
| 5 | every permission request denied or cancelled; agy user-answer questions |
| 130 | interrupted - racy: a SIGINT the cooperative cancel settles first exits 0 with `[done] cancelled` |

Error catalog - string -> fix:

- `⚠ No acpx session found (searched up to <dir>)` (exit 4) - invariant 2:
  `sessions ensure --name <n>` first; confirm `--cwd` is inside the same repo boundary.
- `No named session "<n>" for cwd <cwd> and agent <agent>` (exit 1) - `sessions
  close|show` with a wrong name or cwd; `sessions list --local`.
- `error: unknown option '--cwd'` (exit 1) - global flag after the subcommand
  (invariant 1).
- `Do not combine positional agent with --agent override` (exit 2) - drop the
  positional `claude`/`codex`.
- `Agent command must not be empty` (exit 2) - an empty `--agent` (unset variable).
- `Failed to spawn agent command: agy_acp_server.par` (exit 1) - built-in
  `antigravity` with the `.par` off PATH; see agy.
- `Invalid mcpServers in <path>: expected array` (exit 1) - see MCP.
- `Invalid value for config option model: <id> (ACP -32603, adapter reported
  "Internal error")` - `set model` with no match in the advertised list; use `--model`
  at session creation (see claude).
- `RUNTIME: Model '<id>' not found` - `--model` typo or an id the harness lacks; a 404
  mid-turn reads `There's an issue with the selected model (<id>)`.
- `Claude Code 2.1.2xx does not support this model` - adapter too old; pin a newer one
  (see claude).
- `Internal error` from `claude set reasoning_effort` - claude's knob is `set effort`.
- `[error] RUNTIME: Authentication required` (agy, exit 1) - no `auth.type` in the
  server's `settings.json`; see agy.
- agy stalls at `[client] session/new (running)` until timeout (exit 3) - `auth.type`
  set but never signed in; sign in once interactively.
- `502 Bad Gateway: Failed to connect to backend API` (agy, exit 0) - missing CA
  bundle on NixOS; see Linux / NixOS.
- `Antigravity requested a user answer...` (exit 5) - agy asked a fixed-choice
  question; rewrite the brief so it never needs one.
- `The MCP server '<name>' failed to initialize` (agy, exit 0) - see MCP.
- `RUNTIME: This client is no longer supported for Gemini Code Assist`, or `Gemini CLI
  ACP startup timed out before initialize completed` - you used the built-in `gemini`
  agent; use agy.
- `already has an active writer (code -32600)` - `codex resume` while acpx still owns
  the thread; `sessions close <n>` first.
- `Failed to resume ACP session <id>: Internal error` - `--resume-session` got the
  record `id:`; use `sessionId:`.
- `Queue owner disconnected before prompt completion; outcome unknown` (exit 1) - the
  owner died mid-turn; check the cwd before resubmitting.
- `Missing --skill action.` (exit 1) - `--skill` needs
  `show|list|install|export|help`.
- `error: unknown option '--one-shot'` - not a verb (exit 1 after the agent, 2
  before); `exec` is the one-shot form.
- `Timed out after <ms>ms` (exit 3) - the wall clock ran out, not a stuck agent -
  check `sessions show` for `lastActivity`; an adapter-side timeout surfaces as exit 1
  instead.

Silent failures worth an explicit check: content-filter kills and MCP load failures
both end `[done] end_turn` with exit 0; a denied agy write ends `[done] end_turn`
with exit 5; a `--no-wait` prompt that "sent" may still be queued behind a running
turn; `status` reads `running` long after completion.
