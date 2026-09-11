---
name: herdr-faq
description: Launch and drive coding agents (codex, claude, agy) through the Herdr CLI; requires a herdr pane (HERDR_ENV=1). Use before starting or prompting a herdr subagent, and when a herdr command fails or an agent seems stuck or silently lost a prompt.
metadata:
  version: "0.4.0"
  categories: "agents, operations"
  topics: "herdr, troubleshooting, agent-orchestration, terminal-multiplexer"
  upstream: "herdr@0.9.0"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/herdr-faq
    emoji: "🐑"
---

# Herdr FAQ

Launch and drive coding agents through [Herdr](https://herdr.dev) (>= 0.9.0) without
losing prompts.

## Syntax authority

`herdr --skill` (~13k chars) is the vendor reference: command model, IDs, lifecycle
states, prompt and wait mechanics, read sources, safety rules. Read it once per session
before your first herdr command - this file assumes it and repeats none of it. For
flags, run the command group bare (`herdr agent`, `herdr pane`) or `--help`; never bare
`herdr` (it launches the TUI). If a syntax question is not answered here, it is
answered there - go get it, never guess a flag.

## When this lane

```bash
test "${HERDR_ENV:-}" = 1     # never drive herdr from outside a pane
```

Unset means this shell is not herdr-managed: no `$HERDR_PANE_ID`, no `--current`, and
an untargeted command lands on whatever pane the USER has focused. Use acpx instead
(acpx-faq). In-session fan-out stays on the harness's own subagent tool.

## Invariants

1. **Exit 0 is submission, never completion** - and `send-keys` can return
   `{"type":"ok"}` for keystrokes that never reach the pane. Confirm by effect: state
   moved, or the text is visible in the pane.
2. **Screens no detection rule matches read as `idle`.** agy has no idle rule at all,
   so every agy `idle` is a guess. Read the screen before the first prompt, always.
3. **`agent start` timeout = the child never launched** (bad flag, PATH, or a wrapper
   process). `pane read` has the real error; `pane process-info` and herdr's own
   message do not.
4. **`idle` is not "finished".** A claude turn that spawned background shells or a
   background MCP task ends and reports `idle` while that work runs on; `--wait`
   tracks lifecycle state, not turns.
5. **The driving harness is a second gate.** Dangerous passthrough flags
   (`--dangerously-*`, `danger-full-access`) get classifier-blocked, and so can
   ordinary brief *content* inlined into a shell command. `sleep N; herdr ...` polling
   is banned - use one backgrounded `prompt`, or wait on a file.

## Per kind

Model defaults unless the task argues otherwise: codex `gpt-5.6-sol` at
`reasoning_effort high` (set via codex's own flags/config - check `codex --help`),
claude `claude-opus-5`, agy `gemini-3.7-flash-medium` (measured on par with Opus for
rubric-driven bulk work and far faster; `gemini-3.8-flash-high` measured worse on the
same task). One directory per agent, always.

### codex

```bash
P=$(herdr pane split --current --direction right --cwd "$D" --no-focus | jq -r .result.pane.pane_id)
herdr agent start cx1 --kind codex --pane "$P" --timeout 90000 -- --approve-for-me --no-alt-screen
herdr agent read cx1 --source detection --lines 40        # ALWAYS, before the first prompt
herdr agent prompt cx1 "Carry out $D/brief.md." --wait --timeout 1800000 &
```

Never `--full-auto`: removed in 0.15x, it surfaces as a bare `timeout` and can wedge
the pane in startup-pending. The trust-directory and startup-update dialogs are
detected, so an untrusted dir fails fast with `agent_not_ready` rather than eating the
first prompt. The one-time post-`integration install` hooks-review gate is NOT
detected (WONTFIX) - answer it once per machine. Session ref binds at the first prompt
for a fresh start; an explicit `-- resume <id>` is persisted at launch.

### claude (alias `claude-code`)

```bash
# Pre-trust first - the folder-trust dialog IS detected, so an untrusted dir fails the
# start. Trust is INHERITED: a new dir under an already-trusted parent needs nothing.
CFG=/tmp/agentcfg; mkdir -p "$CFG"                        # isolated from your real config
printf '{"projects":{"%s":{"hasTrustDialogAccepted":true}}}' "$D" > "$CFG/.claude.json"

P=$(herdr pane split --current --cwd "$D" --no-focus --env CLAUDE_CONFIG_DIR="$CFG" \
    | jq -r .result.pane.pane_id)
herdr agent start cl1 --kind claude --pane "$P" --timeout 90000 -- --model claude-opus-5
herdr agent read cl1 --source detection --lines 40        # ALWAYS, before the first prompt
herdr agent prompt cl1 "Carry out $D/brief.md." --wait --timeout 1800000 &
```

- **The safe key differs per dialog.** The folder-trust dialog puts the cursor on
  `No, exit`, so a bare `enter` kills the agent - send `down enter`. The
  Bash-permission dialog puts the cursor on `1. Yes`.
- **`idle` lies in a specific way here.** Background *shells* end the turn and report
  `idle` while they run; background *agents* and *MCP tasks* keep it `working`, and a
  background MCP task can hold `idle` for its whole 3-10 minute life.
- **Grey next-prompt-suggestion text reads as real unsubmitted text** in a plain
  read - disambiguate with `--format ansi` (the suggestion carries the dim attribute
  `ESC[2m`).
- Session ref binds at launch. A Claude Code UI update can break detection
  (`herdr server update-agent-manifests`). Native-launcher installs run under a
  version-string process herdr cannot identify: launch via
  `HERDR_AGENT=claude exec <path>`, then `agent rename`.
- Under a different `CLAUDE_CONFIG_DIR` the agent loads its **own** skills. Confirm
  they are current *before its first turn* - a running session has already snapshotted
  the old text.

### agy (aliases `antigravity`, `antigravity-cli`)

Thinnest detection of the three: no idle rule at all (invariant 2), and nothing in the
pre-flight is recoverable once the agent is up.

```bash
D=/abs/dir/for/this/agent                   # ONE dir per agent - agy reads sibling files
mkdir -p "$D"; : > "$D/report.md"           # pre-create the output file

python3 - "$D" <<'PY'                       # pre-trust; the dialog is unanswerable (below)
import json, pathlib, sys
p = pathlib.Path.home() / ".gemini/antigravity-cli/settings.json"
d = json.loads(p.read_text()) if p.exists() else {}
tw = d.setdefault("trustedWorkspaces", [])  # a list of exact paths, not a map
if sys.argv[1] not in tw: tw.append(sys.argv[1])
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

- **The trust dialog is unanswerable from this side.** `agent start` returns `idle`,
  the screen holds `Do you trust the contents of this project?`, and `send-keys enter`
  no-ops against it - repeatedly, silently, exit 0. `--dangerously-skip-permissions`
  is classifier-blocked before it reaches herdr (invariant 5). Only a config entry
  written *before* `agent start` pre-empts it.
- **Trust lives in `trustedWorkspaces`** in `~/.gemini/antigravity-cli/settings.json`,
  NOT `~/.gemini/trustedFolders.json` (the Gemini CLI's file - observed ignored on agy
  1.2.0). Pre-writing it is not confirmed end to end, and a harness classifier may
  refuse the edit as a trust-config change - when it does, drive agy through acpx
  instead (acpx-faq): its ACP server has no folder-trust dialog.
- **One tab per agent.** Four agy panes in one tab leaves ~29 columns: the TUI stops
  rendering, input races swallow prompts, and detection sees only the pane's own rows,
  so the state you read is wrong too.
- **Read the startup banner before blaming herdr.** `<account> (Google AI Pro)` means
  entitlement is reaching Code Assist. A bare address, or `Eligibility check failed:
  UNAVAILABLE (code 503)`, means dead on arrival however healthy the status looks -
  re-auth, do not re-prompt. A silent drop to free tier also changes the data terms.
- **`not a valid artifact path` is agy-internal, not your filesystem.**
  `ArtifactMetadata` on a `write_to_file` confines the write to
  `~/.gemini/antigravity-cli/brain/<session-id>/`. It self-recovers by retrying as
  `Edit`; pre-creating the file empty skips the round trip.
- **agy reads sibling files unprompted** - agents sharing a directory reproduce each
  other's output. Own directory each, and `md5` any rerun before believing an
  agreement number: byte-identical multi-KB prose is copying, not consensus.
- **Premature `done`** lasts up to ~50s mid-turn while the pane visibly streams (grok
  shares this bug) - wait on the report file, never a settled state. A first prompt
  can be swallowed entirely with `agent_prompt_stalled` and no trace in the composer;
  re-prompt, never `send-keys`. No session ref until the first prompt. Integration
  install target is `antigravity-cli`; `~/.gemini/config` must exist (or
  `ANTIGRAVITY_CLI_CONFIG_DIR`).

Integrations for all three are session-restore only - they never improve state
detection - and their hooks silently no-op without `python3` on PATH.
`integration status` cannot see a codex-side disabled hook (WONTFIX); verify
`agent_session` is present after the first codex turn instead.

## Launch and fleets

- Fleets: one **tab** per agent (`herdr tab create --workspace "$WS" --cwd "$D"
  --no-focus`), own workspace, `--no-focus` everywhere. Repeated splits leave panes
  narrow, and a TUI below its minimum width stops rendering, swallows input, and hides
  its state from detection (which sees only the pane's own rows; fallback 24).
- Always `agent read --source detection` before the first prompt (invariant 2) and
  branch on it - never blind-fire a key at a dialog. After answering one, gate on
  `agent wait <n> --until idle done --timeout 60000`: a bare `wait` returns the
  still-`blocked` state within milliseconds, a no-op that looks like the key never
  landed.
- Names die with the agent and freed names get recycled - namespace them
  (`myproj-reviewer`, never `driver`). After a killed `agent start`, one
  `herdr agent get <name>` frees the reservation (reconciliation is lazy). An agent
  TARGET can be a bare pane id (`agent prompt w1K:p1 '<text>'`) - how you reach an
  unnamed agent without renaming someone else's.
- Test `-n "$P"` after capturing a pane id: an empty one makes later parsers blame the
  wrong token.

## Composing traps

- `agent read` and `pane read` return **raw pane text**; the other agent/pane/workspace
  commands return JSON. Piping raw text to `jq` dies with
  `parse error: Invalid numeric literal` and you silently lose the read - use `tail`,
  `grep -qF`.
- `pane read <id>` takes the pane **positionally** and has no `--pane` at all
  (`unknown option: --pane`); `pane close` likewise. When in doubt read the `Usage:`
  line - it names positionals in angle brackets.
- `agent start --timeout` defaults to 30000 and caps at 300000. `agent prompt
  --timeout` has **no cap** (1800000 is fine) but is rejected with
  `--timeout requires --wait` when `--wait` is absent - and backgrounded, that failure
  is invisible and the prompt is never written. Fire-and-forget sends take no flags.
- `agent list` JSON is sparse: `name` is **absent** (not null) for unnamed agents, and
  a pending start is `{"agent_status":"unknown","launch_pending":true}`. Null-guard
  every string op: `select((.name // "") | startswith("myproj-"))`.
- Env vars go in `--env KEY=VALUE` at pane/tab/workspace creation, never
  `pane run 'export ...'` (a subshell the agent never sees). Repeated flags go
  inline - zsh does not word-split an unquoted `$E`, so `E="--env A=1 --env B=2"`
  arrives as one bogus argument.
- Bad flags print usage partly on **stdout**, so a `| jq` pipeline turns it into a
  misleading parse error - check exit status before parsing.

## Drive

- **Wait on the artifact, not the state.** End every non-trivial brief with "write
  your full report to `<path>` and reply with only the path", and poll for the file.
  `idle` arrives on interrupted turns, on fleet parents that dispatched children, and
  for the whole life of a claude background MCP task (invariant 4) - a watcher on
  `!= working` false-alarms on every one of those.
- Gate decisions on `agent_status`, never `interactive_ready` (it stays true while
  blocked).
- Long text is safe through `agent prompt` (bracketed paste; 8 KB arrives intact); the
  1024-byte macOS tty truncation applies to `pane send-text` and keystrokes. Pass file
  paths anyway - it also keeps brief content out of the shell command (invariant 5).
- Queue follow-ups behind a working agent freely (`prompt` refuses blocked agents
  before writing anything) - but no `--wait` on a queued follow-up: it can be
  satisfied by the turn already running.
- Slash commands that open dialogs trip the fixed 5s stall gate - verify those by
  screen read, not `--wait`.
- Exit: confirm positively - `pane process-info` shows the shell back in the
  foreground - then `pane close`. Never regex the prompt.

## Failures

Triage first:

- **Any start failure** -> `herdr pane read <pane> --source visible` FIRST. Most
  common: the child launched, printed `error: unknown option ...`, and exited -
  `process-info` looks innocent and herdr reports a bare `timeout`. Then
  `process-info`: a foreign foreground process = busy/race; an agent under a wrapper
  (`node`, a bare version string) = relaunch via `HERDR_AGENT=<kind> exec <cmd>`, then
  `agent rename`; under `docker exec`, `podman exec`, or `ssh -t` = permanently
  undetectable (WONTFIX).
- **Any wrong state** -> `agent explain <target> --verbose` + `agent read --source
  detection`. Matched rule null + `default_known_agent_idle_fallback` = herdr is
  guessing. Stale manifest -> `herdr server update-agent-manifests` (no restart).
  Local rule patch: `~/.config/herdr/agent-detection/<kind>.toml`. Logs:
  `~/.config/herdr/herdr-server.log`, `HERDR_LOG=herdr=debug`.
- **After a binary update, do NOT reflexively `server stop`** - it kills every pane
  process and in-flight turn, unresumably. 0.9.0 leaves a compatible server and its
  agents untouched; trust `herdr status` (`endpoint_compatible`, `restart_needed`,
  `server_binary_stale`). A stale CLIENT inverts the picture: it calls the server
  "old" while `pane list` correctly says `client protocol N is older than server`.
- **"herdr is stuck"** is often the terminal emulator, not herdr - a wedged surface
  takes no input while panes and agents are fine in the server. Open a fresh tab
  before touching the server.

Catalog:

- `agent_not_ready` (start) - a dialog is on screen; exit 1 but the agent is running
  and the name is bound. Read, answer via `send-keys` (safe keys in Per kind), gate
  `--until idle done`, prompt. A blocked launch never times out: `launch_pending`
  stays true and `rename` returns `agent_launch_pending` until answered. agy's trust
  dialog is NOT detected and reads as `idle` instead - see agy.
- `timeout` (start) - invariant 3; read the pane. `command not found` in a non-login
  shell: set `[terminal] shell_mode = "login"`, recreate the pane. Under `--remote`,
  panes inherit the SERVER's PATH, so a `~/.local/bin` agent CLI gives a bare timeout.
- `agent_name_taken` / `agent_launch_pending` - reservations reconcile lazily: one
  `herdr agent get <name>` frees an expired one. Still wedged: burn both - fresh pane,
  fresh name.
- `agent_pane_busy` - "available shell" = the shell itself, alone, in the foreground.
  (a) racy rc files (`starship`, `direnv`): herdr retries only 2s and `pane get` looks
  identical ready vs not - retry with backoff, clean up orphaned tabs; (b) genuine
  occupant: split a new pane, never reclaim (killing the occupant cascades into
  `pane_not_found`); (c) Windows profiles that chain-launch pwsh nest shells
  invisibly: `[terminal] default_shell = "pwsh.exe"`.
- `agent_not_found` - downstream symptom: failed start, exited agent, or a bad name
  earlier in the loop. A live pane can rarely lose registration while the TUI runs
  fine - `agent rename <pane> <same-name>` restores it.
- `timeout` (prompt --wait / wait) - usually the turn outlasted the timeout:
  `agent get` shows `working`. Use 1800000+, background it, never resend on timeout
  alone.
- `agent_prompt_stalled` - **not proof of non-delivery**; the text may have landed and
  been consumed. Causes in observed order: stale manifest; a dialog-opening prompt; a
  target-side paste modal swallowing Enter (omp's Large Paste Menu triggers on *line
  count*, not bytes - disable it in omp `/settings`); Windows input races on long
  prompts. Never blind-resend and never recover with a lone `send-keys enter`. Read
  the pane, then re-send with a fresh `agent prompt`:

  ```bash
  for i in 1 2 3; do
    herdr agent prompt "$A" "$TEXT" --wait --timeout 60000 && break
    herdr agent read "$A" --source recent-unwrapped --lines 200 | grep -qF "${TEXT:0:80}" && break
  done
  ```

- `agent_blocked` (prompt) - refused before anything is written. Read detection,
  surface the dialog, answer via send-keys.
- `invalid_agent_name` - `[a-z][a-z0-9_-]{0,31}`; shell loops producing uppercase are
  the classic cause, and one bad name cascades into a wall of `agent_not_found`s.
- `pane_not_found` / `workspace_not_found` / `unknown option: <valid-looking value>` -
  IDs are runtime-only, never reused: re-list at session start, recreate only what is
  missing. `unknown option` on a whole flag string is the zsh variable trap (see
  Composing traps); on a lone token it is usually an empty `$P`.
- `workspace_group_close_required` - closing a primary workspace with open worktree
  workspaces needs `workspace close --group`; `tab close` can likewise return
  `confirmation_required` for a worktree group.
- Harness blocks - classifier denial on dangerous passthrough flags: put
  permissiveness in the child agent's own config ("Stage 2 classifier error" is
  transient - retry once). Allowlist the read-only commands
  (`agent get/read/list/wait/explain`, `pane read/list/process-info`,
  `workspace list`) or every call prompts.

Silent failures (exit 0, no error): fallback-idle prompt swallowing (invariant 2);
`send-keys` returning ok without delivering; a bare `agent prompt` leaving text
unsubmitted in an out-of-view pane; a first turn going straight
`unknown -> working -> idle` skips `done` and its notification; a tall dialog partly
invisible in a short pane (detection sees only the pane's own rows);
`pane wait-output` matching the echoed command itself - never use it for readiness;
`agent focus` returning ok without moving the viewport in 0.9.0 - use `tab focus`.
