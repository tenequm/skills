---
name: herdr-faq
description: Launch and drive coding agents (codex, claude, agy) through the Herdr CLI. Use before starting or prompting a subagent via herdr agent or pane commands, and when a herdr command fails or an agent seems stuck or silently lost a prompt.
metadata:
  version: "0.3.2"
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

Read the Invariants, then go straight to your agent's section in **Per kind** - each one is a
complete launch-to-first-prompt recipe. Everything after that is shared reference: Launch for
pane and name mechanics, Shapes for composing commands, Drive for the turn loop, Failures for
triage.

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

## Per kind

Each section is self-contained: flags, pre-flight, launch, dialog handling, and the quirks
that bite while the agent runs. Shared mechanics are in Launch and Shapes.

### codex

```bash
P=$(herdr pane split --current --direction right --cwd "$D" --no-focus | jq -r .result.pane.pane_id)
herdr agent start cx1 --kind codex --pane "$P" --timeout 90000 -- --approve-for-me --no-alt-screen
herdr agent read cx1 --source detection --lines 40        # ALWAYS, before the first prompt
herdr agent prompt cx1 "Carry out $D/brief.md." --wait --timeout 1800000 &
```

Never `--full-auto`: removed in 0.15x, it surfaces as a bare `timeout` and can leave the pane
wedged in startup-pending. Both the trust-directory dialog and the startup update dialog are
detected, so an untrusted dir fails fast with `agent_not_ready` rather than eating the first
prompt - answer with `send-keys`, then `wait --until idle done`. The one-time
post-`integration install` hooks-review gate is NOT detected (WONTFIX); answer it once per
machine. Session ref binds at the first prompt for a fresh start, but an explicit
`-- resume <id>` is persisted at launch.

### claude (alias `claude-code`)

```bash
# Pre-trust first - the folder-trust dialog IS detected, so an untrusted dir fails the start.
# Trust is INHERITED: a new directory under an already-trusted parent needs nothing at all.
CFG=/tmp/agentcfg; mkdir -p "$CFG"                        # isolated from your real config
printf '{"projects":{"%s":{"hasTrustDialogAccepted":true}}}' "$D" > "$CFG/.claude.json"

P=$(herdr pane split --current --cwd "$D" --no-focus --env CLAUDE_CONFIG_DIR="$CFG" \
    | jq -r .result.pane.pane_id)
herdr agent start cl1 --kind claude --pane "$P" --timeout 90000 -- --model "$M"
herdr agent read cl1 --source detection --lines 40        # ALWAYS, before the first prompt
herdr agent prompt cl1 "Carry out $D/brief.md." --wait --timeout 1800000 &
```

- **If you do hit a dialog, the safe key differs per dialog.** The folder-trust dialog puts
  the cursor on `No, exit`, so a bare `enter` kills the agent - send `down enter`. Its
  Bash-permission dialog puts the cursor on `1. Yes`.
- **`idle` lies in a specific way here.** A turn that spawns background *shells* ends and
  reports `idle` while they run; background *agents* and background *MCP tasks* keep it
  `working`, and a background MCP task can hold `idle` for its whole 3-10 minute life.
- **Grey "next prompt suggestion" text in the composer reads as real unsubmitted text** in a
  plain read - disambiguate with `--format ansi` (the suggestion carries the dim attribute
  `ESC[2m`).
- Session ref binds at launch. A Claude Code UI update can break detection
  (`herdr server update-agent-manifests`). Native-launcher installs run under a version-string
  process herdr cannot identify: launch via `HERDR_AGENT=claude exec <path>`, then
  `agent rename`.
- Under a different `CLAUDE_CONFIG_DIR` the agent loads its **own** skills. Confirm it has
  this skill current *before its first turn* - a running session has already snapshotted the
  old text and cannot be fixed in place.

### agy (aliases `antigravity`, `antigravity-cli`)

Thinnest detection of the three: no idle rule at all, so every agy `idle` is a guess
(invariant 2). Nothing in the pre-flight is recoverable once the agent is up.

```bash
D=/abs/dir/for/this/agent                   # ONE dir per agent, holding only its brief+input
mkdir -p "$D"; : > "$D/report.md"           # pre-create the output file

python3 - "$D" <<'PY'                       # pre-trust; the dialog is unanswerable (below)
import json, pathlib, sys
p = pathlib.Path.home() / ".gemini/trustedFolders.json"
d = json.loads(p.read_text()) if p.exists() else {}
d[sys.argv[1]] = "TRUST_FOLDER"             # "TRUST_PARENT" on a parent covers its children
p.write_text(json.dumps(d, indent=2) + "\n")
PY

P=$(herdr tab create --workspace "$WS" --cwd "$D" --label ag1 --no-focus \
    | jq -r .result.root_pane.pane_id)      # one TAB per agent, never N panes in one tab
herdr agent start ag1 --kind agy --pane "$P" --timeout 120000 \
  -- --model gemini-3.7-flash-medium --effort medium --mode accept-edits
herdr agent read ag1 --source detection --lines 15   # read the banner, not the status
herdr agent prompt ag1 "Carry out $D/brief.md. Write your report to $D/report.md." \
  --wait --timeout 1800000 &                # then poll for the file, not the state
```

- **Default to `gemini-3.7-flash-medium`.** Measured on par with Opus for rubric-driven bulk
  work (99.5% verdict agreement across 213 items, and it made the better call on the one they
  disputed) and far faster; `gemini-3.8-flash-high` scored measurably worse on the same task
  despite being the bigger, higher-effort model. Pick another id only when a task argues for it.
- **The trust dialog is unanswerable from this side.** `agent start` returns `idle`, the
  screen holds `Do you trust the contents of this project?`, and `send-keys enter` no-ops
  against it - repeatedly, silently, exit 0. `--dangerously-skip-permissions` is blocked by
  the driving harness's classifier before it ever reaches herdr (invariant 5). Only the
  config entry works, and only if written *before* `agent start`. Trust is per exact path: a
  fresh subdirectory needs its own entry unless a parent carries `TRUST_PARENT`.
- **One tab per agent.** Four agy panes in one tab leaves ~29 columns: the TUI stops
  rendering, input races swallow prompts outright, and detection sees only the pane's own
  rows, so the state you read is wrong too.
- **Read the startup banner before blaming herdr.** `<account> (Google AI Pro)` means
  entitlement is reaching Code Assist. A bare address, or `Eligibility check failed:
  UNAVAILABLE (code 503)`, means the agent is dead on arrival however healthy its status
  looks - re-auth, do not re-prompt. A silent drop to free tier also changes the data terms
  on everything you send it.
- **`not a valid artifact path` is agy-internal, not your filesystem.** `ArtifactMetadata`
  attached to a `write_to_file` reclassifies the write as an artifact, confined to
  `~/.gemini/antigravity-cli/brain/<session-id>/`. It self-recovers by dropping the metadata
  and retrying as `Edit`; pre-creating the file empty skips the round trip.
- **agy reads sibling files unprompted.** Agents sharing a directory read each other's output
  and a prior run's results, then reproduce them. Own directory each, and `md5` any rerun
  before believing an agreement number - byte-identical multi-KB prose is copying, not
  consensus.
- **Premature `done`** lasts up to ~50s mid-turn while the pane visibly streams (grok shares
  this bug), so wait on the report file, never a settled state. A first prompt can be
  swallowed entirely with `agent_prompt_stalled` and no trace in the composer; re-prompt, do
  not `send-keys`. No session ref until the first prompt. Integration install target is
  `antigravity-cli`; config dir `~/.gemini/config` must exist (or
  `ANTIGRAVITY_CLI_CONFIG_DIR`).

Integrations for all three are session-restore only - they never improve state detection - and
their hooks silently no-op without `python3` on PATH. `integration status` cannot see a
codex-side disabled hook (WONTFIX); verify `agent_session` is present after the first codex
turn instead.

## Launch

Shared mechanics; kind-specific flags and pre-flight are in Per kind.

```bash
test "${HERDR_ENV:-}" = 1                       # never drive herdr from outside a pane

P=$(herdr pane split --current --direction right --cwd "$PWD" --no-focus | jq -r .result.pane.pane_id)
test -n "$P"                                    # empty $P => misleading downstream errors
herdr pane process-info --pane "$P"             # must be a bare shell at its prompt
```

For a fleet, give each agent its own **tab** instead (`herdr tab create --workspace "$WS"
--cwd "$D" --no-focus | jq -r .result.root_pane.pane_id`): repeated splits leave each pane
narrow, and a TUI below its minimum width stops rendering, swallows input, and hides its own
state from detection.

Always `agent read --source detection` before the first prompt (invariant 2) and branch on
what it returns - never blind-fire a key at a dialog. After answering one:

```bash
herdr agent wait worker --until idle done --timeout 60000   # NOT a bare wait - see Drive
```

Rules: capture every ID from JSON, never predict. Names `[a-z][a-z0-9_-]{0,31}`, namespaced
(`myproj-reviewer`, never `driver`); names die with the agent - re-attach via
`agent rename <pane> <name>`. Fleets get their own workspace, `--no-focus` everywhere. After a
killed `agent start`, run `herdr agent get <name>` once to free the name reservation
(reconciliation is lazy - it can take a minute or two).

## Shapes

The facts you need while composing a command, not after it fails.

**Output modes.** `agent get`, `agent list`, `agent start`, `agent prompt`, `agent wait`,
`pane split`, `pane list`, `pane process-info`, `workspace *` return **JSON** - pipe to `jq`.
`agent read` and `pane read` return **raw pane text** with no wrapper; piping them to `jq`
dies with `parse error: Invalid numeric literal` and you silently lose the read. Use `tail`,
`grep -qF`.

**Positional vs flagged**, and it differs per command. `pane close <id>` and
`pane read <id>` take the pane **positionally** - `pane read` has no `--pane` at all, so
`herdr pane read --pane "$P"` dies with `unknown option: --pane`. `pane split` accepts either
form. `pane layout` and `pane process-info` take `--pane`; `pane list` takes neither. When in
doubt read the `Usage:` line, which names positionals in angle brackets.

**An agent TARGET can be a bare pane id**, not just a name: `agent get w1K:p1`,
`agent read w1K:p1`, `agent prompt w1K:p1 '<text>'` all work. That is how you reach an agent
that was never named, without renaming someone else's. `workspace create` takes `--label`, not `--name`. `send-keys` takes key names only
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
  `visible` for what is on screen now.
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
trust-directory dialog and its startup update dialog are detected, and claude's folder-trust
dialog is caught by the generic blocked-form rule - **agy's trust dialog is not**, and reads
as `idle` instead. Codex's one-time post-`integration install` hooks-review gate is NOT
detected (WONTFIX) - answer it once per machine.

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

## Multiple machines (0.9.0)

`herdr machine` manages saved SSH endpoints, but it is a **TUI-only** surface: there is no
machine namespace in the CLI or socket API. IDs and live agent names are scoped to one server,
two machines can both hold `w1:p1` or an agent named `reviewer`, and selecting a machine in the
TUI does **not** retarget CLI commands run in your pane - they still use the inherited socket.
For automation, run the herdr CLI on the intended host over ssh and rediscover IDs there. Only
add, remove, enable, or disable profiles when the user asks; setup asks before stopping an
incompatible remote server and defaults to No - do not approve replacement without consent.
`--trust-repository` on `worktree` grants per-request Git trust and is not a routine retry.
