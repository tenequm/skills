---
name: herdr-faq
description: Launch and drive coding agents (codex, claude, agy) through the Herdr CLI reliably. Use before starting or prompting a subagent via herdr agent/pane commands, and when any herdr command fails or an agent seems stuck, silently lost a prompt, or reports a wrong state.
metadata:
  version: "0.2.0"
  categories: "agents, operations"
  topics: "herdr, troubleshooting, agent-orchestration, terminal-multiplexer"
  upstream: "herdr@0.9.0"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/herdr-faq
    emoji: "🐑"
---

# Herdr FAQ

Launch and drive coding agents through [Herdr](https://herdr.dev) (>= 0.9.0) without losing
prompts. Command semantics: `herdr --skill` (the binary ships its own current doc and is the
tiebreaker for any dispute with this file). This file covers only what goes wrong and the
recipes that avoid it.

## Invariants

1. **Exit 0 is submission, never completion.** `agent prompt` writes text and Enter as one
   ordered submission and reports success only after both land - that still does not prove a
   turn started. `send-keys` proves nothing at all: it can return `{"type":"ok"}` for
   keystrokes that never reach the pane. Confirm by effect: state moved, or the text is
   visible in the pane.
2. **Screens no detection rule matches read as `idle`.** agy has no idle rule at all, so every
   agy `idle` is a guess. Read the screen before the first prompt, always.
3. **`agent start` timeout = the child never launched.** Bad flag, PATH, or a wrapper process.
   `pane read` has the real error; `pane process-info` and herdr's own message do not.
4. **`idle` is not "finished".** A claude turn that spawns background shells or a background
   MCP task ends and reports `idle` while that work runs on. `--wait` tracks lifecycle state,
   not turns: it can be satisfied by a turn already in flight, or by the idle an interrupted
   turn produces a second later.
5. **The driving harness is a second gate.** Dangerous passthrough flags (`--dangerously-*`,
   `danger-full-access`) get classifier-blocked, and so can ordinary brief *content* inlined
   into a shell command. `sleep N; herdr ...` polling is banned - use one backgrounded
   `prompt`, or wait on a file.

## Launch

```bash
test "${HERDR_ENV:-}" = 1                       # never drive herdr from outside a pane

P=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus | jq -r .result.pane.pane_id)
test -n "$P"                                    # empty $P => misleading downstream errors
herdr pane process-info --pane "$P"             # must be a bare shell at its prompt

herdr agent start worker --kind codex --pane "$P" --timeout 90000 -- --approve-for-me --no-alt-screen

# ALWAYS read before the first prompt (invariant 2), and branch on what it returns.
herdr agent read worker --source detection --lines 40
```

If that read shows a dialog, answer it deliberately - never blind-fire a key. **The safe key
differs per dialog**: claude's folder-trust dialog puts the cursor on `No, exit` (a bare
`enter` kills the agent), while its Bash-permission dialog puts it on `1. Yes`. Then:

```bash
herdr agent send-keys worker down enter
herdr agent wait worker --until idle done --timeout 60000   # NOT a bare wait - see Drive
```

### Never hit the claude trust dialog again

The dialog appears only when the cwd has no trusted ancestor. Trust is **inherited**: a brand
new directory under an already-trusted parent starts clean, and claude records the child
automatically. Two reliable fixes:

```bash
# (a) keep agent working dirs under a tree you have already trusted once, or
# (b) pre-seed trust for an arbitrary path, isolated from your real config:
CFG=/tmp/agentcfg; mkdir -p "$CFG"
printf '{"projects":{"%s":{"hasTrustDialogAccepted":true}}}' "$D" > "$CFG/.claude.json"
herdr pane split --current --cwd "$D" --no-focus --env CLAUDE_CONFIG_DIR="$CFG"
```

Rules: capture every ID from JSON, never predict. Names `[a-z][a-z0-9_-]{0,31}`, namespaced
(`myproj-reviewer`, never `driver`); names die with the agent - re-attach via
`agent rename <pane> <name>`. Fleets get their own workspace, `--no-focus` everywhere. After a
killed `agent start`, run `herdr agent get <name>` once to free the name reservation
(reconciliation is lazy - it can take a minute or two).

When you drive an agent under a **different `CLAUDE_CONFIG_DIR`**, it loads its own skills.
Confirm it has this skill current *before its first turn* - a running session has already
snapshotted the old text and cannot be fixed in place.

## Shapes

The facts you need while composing a command, not after it fails.

**Output modes.** `agent get`, `agent list`, `agent start`, `agent prompt`, `agent wait`,
`pane split`, `pane list`, `pane process-info`, `workspace *` return **JSON** - pipe to `jq`.
`agent read` and `pane read` return **raw pane text** with no wrapper; piping them to `jq`
dies with `parse error: Invalid numeric literal` and you silently lose the read. Use `tail`,
`grep -qF`.

**Positional vs flagged.** `pane close` takes its id **positionally** (`herdr pane close "$P"`)
- the one pane command that does, while `pane split|read|list|layout|process-info` all take
`--pane`. `workspace create` takes `--label`, not `--name`. `send-keys` takes key names only
(`enter`, `esc`, `down`, `ctrl+c`); text and slash commands go through `prompt`.

**Flag dependencies and caps.** `agent start --timeout` defaults to 30000 and is capped at
300000. `agent prompt --timeout` has **no cap** (1800000 is fine) but is rejected outright with
`--timeout requires --wait` when `--wait` is absent - and under a backgrounded call that
failure is invisible and the prompt is never written. Fire-and-forget sends take no flags.

**Sparse JSON.** `agent list` entries are partially populated: `name` is **absent** (not null)
for unnamed agents, `interactive_ready` is absent on many, and a pending start appears as
`{"agent_status":"unknown","launch_pending":true}` with no `agent` or `agent_session` key.
Null-guard every string op: `select((.name // "") | startswith("myproj-"))`.

**Env vars** go in `--env KEY=VALUE` at pane/tab/workspace creation, never
`pane run 'export ...'` (that sets them in a subshell the agent never sees). **Repeated flags
go inline** - building them in a shell variable fails, because zsh does not word-split
unquoted expansions and herdr receives the whole string as one argument:

```bash
E="--env A=1 --env B=2"; herdr pane split ... $E     # WRONG: unknown option: --env A=1 --env B=2
herdr pane split ... --env "A=1" --env "B=2"         # right
```

Bad flags print usage (some of it on **stdout**), so a `| jq` pipeline turns it into a
misleading parse error. Check exit status before parsing.

## Drive

```bash
# Blocking send: one call, generous timeout, backgrounded.
herdr agent prompt worker "$(cat brief.md)" --wait --timeout 1800000

# Fire-and-forget note to a working agent: no flags at all.
herdr agent prompt worker "$(cat note.md)"

# On timeout: usually false - confirm before acting, never blind-resend.
herdr agent get worker                                   # working = still on the turn

# Mid-turn dialogs: wait for blocked, inspect, surface to the human, answer via send-keys.
herdr agent wait worker --until blocked --timeout 120000
herdr agent read worker --source detection --lines 40

# Exit: confirm positively - shell back in foreground. Never regex the prompt.
herdr pane process-info --pane "$P" && herdr pane close "$P"
```

- **Wait on the artifact, not the state.** End every non-trivial brief with "write your full
  report to `<path>` and reply with only the path", and poll for the file. `idle` arrives on
  interrupted turns, on fleet parents that dispatched children and ended their turn, and for
  the entire multi-minute life of a claude background MCP task. A watcher written as
  `[ "$s" != "working" ] && echo stopped` false-alarms on every one of those.
- `--until` defaults to `idle|done|blocked`; keep it there for turn waits, because narrowing
  it is how waits hang. **One exception**: right after answering a dialog, a bare `wait`
  returns the still-`blocked` state within milliseconds - a no-op that looks like the key
  never landed. Gate on `--until idle done` there, or poll `agent get`. A wait ending
  `agent_not_running` after the agent exited or moved is the event, not an error.
- `done` and `idle` both mean ready for input; `done` is an unseen completion, and focusing the
  tab silently rewrites it to `idle`. Each TUI client tracks this independently, so its badge
  can disagree with the CLI. Gate decisions on `agent_status`, never `interactive_ready`
  (which stays true while blocked).
- Long text is safe through `agent prompt` - it uses bracketed paste, and 8 KB arrives intact.
  The 1024-byte (macOS) tty truncation is real but applies to **`pane send-text`** and
  keystrokes. Pass file paths anyway when the text is a brief: it also keeps the content out
  of the shell command, where the driving harness's classifier can block on it.
- Output: `--source recent-unwrapped` for transcript, `detection` for the last screen,
  `visible` for what is on screen now. Grey "next prompt suggestion" text in a claude composer
  reads as real unsubmitted text in a plain read - disambiguate with `--format ansi` (the
  suggestion carries the dim attribute `ESC[2m`).
- Queue follow-ups behind a working agent freely; `agent prompt` refuses blocked agents
  (`agent_blocked`) before writing anything. But do not attach `--wait` to a queued follow-up:
  it can be satisfied by the turn already running.
- Slash commands that open dialogs trip the fixed 5s `agent_prompt_stalled` gate - verify
  those by screen read, not `--wait`.

## Failures

Triage first:

- **Any start failure** -> `herdr pane read <pane> --source visible` FIRST. The most common
  cause is a bad flag: the child launched, printed `error: unknown option ...`, and exited,
  leaving only the shell - so `process-info` looks innocent and herdr reports a bare
  `timeout`. Then `pane process-info --pane <id>`: a foreign foreground process = busy/race;
  an agent under a wrapper (`node`, a bare version string) = herdr cannot identify it ->
  relaunch via `HERDR_AGENT=<kind> exec <cmd>`, then `agent rename`. An agent under
  `docker exec`, `podman exec`, or `ssh -t` is permanently undetectable (WONTFIX).
- **Any wrong state** -> `herdr agent explain <target> --verbose` + `agent read --source
  detection`. Matched rule null + `default_known_agent_idle_fallback` = herdr is guessing.
  Stale manifest -> `herdr server update-agent-manifests` (no restart; named servers now pick
  up each other's downloads). Local rule patch: `~/.config/herdr/agent-detection/<kind>.toml`.
- **Logs**: `~/.config/herdr/herdr-server.log`, `HERDR_LOG=herdr=debug`.
- **After a binary update**, do NOT reflexively `server stop`. 0.9.0 leaves a compatible server
  and its running agents untouched; check `herdr status` (`endpoint_compatible`,
  `restart_needed`, `server_binary_stale`) and stop only for server-side changes - stopping
  kills every pane process and in-flight turn, unresumably. A **stale client** inverts the
  advice: it reports the running server as "old" while `pane list` correctly says
  `client protocol N is older than server`. Trust `herdr status`.
- **"herdr is stuck"** is often the terminal emulator, not herdr. A wedged surface takes no
  input while panes and agents are fine in the server. Open a fresh tab before touching the
  server.

**`agent_not_ready` (start)** - a dialog is on screen. Exit 1 but the agent is running and the
name is bound (documented contract). Read, answer via send-keys, wait on `--until idle done`,
prompt. A blocked launch never times out: `launch_pending` stays true and `rename` returns
`agent_launch_pending` until the dialog is answered or the process exits. Both codex's
trust-directory dialog and its startup update dialog are detected; claude's folder-trust
dialog is caught too, by the generic blocked-form rule. Codex's one-time post-`integration
install` hooks-review gate is NOT detected (WONTFIX) - answer it once per machine.

**`timeout` (start)** - invariant 3; read the pane. `command not found` in a non-login shell:
set `[terminal] shell_mode = "login"`, recreate the pane. Under `--remote`, panes inherit the
*server's* PATH, so a `~/.local/bin` agent CLI is not found and you get a bare timeout.

**`agent_name_taken` / `agent_launch_pending`** - reservations are made before launch and
reconciled lazily: `herdr agent get <name>` once frees an expired one. Still wedged (rename ->
pending, get -> not_found, restart -> pane_busy): burn both - fresh pane, fresh name. Names are
cross-workspace and freed names get recycled - namespace them.

**`agent_pane_busy`** - "available shell" = the shell itself, alone, in the foreground. Three
cases: (a) racy - shell still running its rc files (`starship`, `direnv`); herdr retries only
2s (never on Windows) and `pane get` looks identical ready vs not, so retry with backoff and
clean up any orphaned tab; (b) genuine occupant - split a new pane, do not reclaim (killing the
occupant cascades into `pane_not_found`); (c) permanent on Windows - a profile that
chain-launches pwsh nests shells invisibly: `[terminal] default_shell = "pwsh.exe"`.

**`agent_not_found`** - downstream symptom: failed start, exited agent, or a bad name earlier
in the loop. A pane holding only a shell also returns it. A live pane can rarely lose
registration while the TUI runs fine - `agent rename <pane> <same-name>` restores it.

**`timeout` (prompt --wait / wait)** - usually the turn outlasted the timeout: `agent get`
shows `working`. Use 1800000+, background it, never resend on timeout alone.

**`agent_prompt_stalled`** - the 5s gate is fixed and now starts *after* submission, accepting
only observed `working` or `blocked`; the caller timeout includes submission time, and expiring
first returns `timeout` instead. **It is not proof of non-delivery** - the text may have landed
and been consumed. Causes in observed order: stale manifest; dialog-opening prompt; a
target-side paste modal swallowing Enter (omp's Large Paste Menu, which triggers on *line
count*, not bytes - disable it in omp `/settings`); Windows input races on long prompts. Never
blind-resend and never recover with a lone `send-keys enter` (it can silently no-op). Read the
pane, then re-send with a fresh `agent prompt` - not a keystroke:

```bash
for i in 1 2 3; do
  herdr agent prompt "$A" "$TEXT" --wait --timeout 60000 && break
  herdr agent read "$A" --source recent-unwrapped --lines 200 | grep -qF "${TEXT:0:80}" && break
done
```

**`agent_blocked` (prompt)** - refused before anything is written. Read detection, surface the
dialog, answer via send-keys.

**`invalid_agent_name`** - grammar above; shell loops producing uppercase are the classic
cause, and one bad name cascades into a wall of `agent_not_found`s.

**`pane_not_found` / `workspace_not_found` / `unknown option: <valid-looking value>`** - IDs are
runtime-only, never reused: re-list at session start, recreate only what is missing.
`unknown option` on a whole flag string is the shell-variable trap (see Shapes); on a lone
token it is usually an empty `$P` making the parser blame the wrong thing.

**`workspace_group_close_required`** - closing a primary workspace with open worktree
workspaces needs `workspace close --group`. Closing the last tab closes its workspace. `tab close` can likewise return
`confirmation_required` when it would close a whole worktree group.

**Harness blocks** - classifier denial on dangerous passthrough flags: put permissiveness in
the child agent's own config ("Stage 2 classifier error" is transient - retry once). Allowlist
read-only commands (`agent get/read/list/wait/explain`, `pane read/list/process-info`,
`workspace list`) or every call prompts.

Silent failures (exit 0, no error): fallback-idle prompt swallowing (invariant 2); `send-keys`
returning ok without delivering; bare `agent prompt` leaving text unsubmitted in an
out-of-view pane; tty truncation of long `send-text`; a first turn going straight
`unknown -> working -> idle` skips `done` and its notification; detection sees only the pane's
own rows (fallback 24), so a tall dialog in a short pane is partly invisible;
`pane wait-output` matches the echoed command itself - never use it for readiness;
`agent focus` can return ok without moving the viewport in 0.9.0 - use `tab focus` instead.

## Per kind

**codex** - `-- --approve-for-me --no-alt-screen` (never `--full-auto`: removed in 0.15x,
surfaces as a bare timeout and can leave the pane wedged in startup-pending). Trust dialog and
startup update dialog are both detected; an untrusted dir fails fast with `agent_not_ready`.
Session ref binds at the first prompt for a fresh start, but an explicit `-- resume <id>` is
persisted at launch.

**claude** (alias `claude-code`) - `-- --model <m>`. The folder-trust dialog **is** detected
(`agent_not_ready`), so pre-trust the dir (see Launch) rather than recovering. Session ref
binds at launch. A turn with background shells ends and reports `idle` while they run;
background *agents* and background *MCP tasks* keep it `working`, and a background MCP task can
hold `idle` for its whole 3-10 minute life. A Claude Code UI update can still break detection
(`herdr server update-agent-manifests`). Native-launcher installs run under a version-string
process herdr cannot identify: launch via `HERDR_AGENT=claude exec <path>`, then rename.

**agy** (aliases `antigravity`, `antigravity-cli`) - thinnest detection: no idle rule at all,
the trust dialog reads idle, and premature `done` mid-turn lasts up to ~50s while the pane
visibly streams (grok shares this bug). Never trust a single settled state - verify by screen
read or sentinel. A first prompt can be swallowed entirely with `agent_prompt_stalled` and no
trace in the composer; re-prompting works. No session ref until the first prompt. Integration
install target is `antigravity-cli`; config dir `~/.gemini/config` must exist (or
`ANTIGRAVITY_CLI_CONFIG_DIR`).

Integrations for all three are session-restore only - they never improve state detection - and
their hooks silently no-op without `python3` on PATH. `integration status` cannot see a
codex-side disabled hook (WONTFIX); verify `agent_session` is present after the first codex
turn instead.

## Multiple machines (0.9.0)

`herdr machine` manages saved SSH endpoints, but it is a **TUI-only** surface: there is no
machine namespace in the CLI or socket API. IDs and live agent names are scoped to one server,
two machines can both hold `w1:p1` or an agent named `reviewer`, and selecting a machine in the
TUI does **not** retarget CLI commands run in your pane - they still use the inherited socket.
For automation, run the herdr CLI on the intended host over ssh and rediscover IDs there. Only
add, remove, enable, or disable profiles when the user asks; setup asks before stopping an
incompatible remote server and defaults to No - do not approve replacement without consent.
`--trust-repository` on `worktree` grants per-request Git trust and is not a routine retry.
