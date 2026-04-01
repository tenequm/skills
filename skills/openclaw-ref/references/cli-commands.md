# OpenClaw CLI Commands

## Gateway

```bash
openclaw gateway run [--bind loopback|lan|auto|custom|tailnet] [--port N] [--force]
openclaw gateway run [--auth-mode none|token|password|trusted-proxy]
openclaw gateway run [--ws-log] [--dev] [--reset]
openclaw gateway run [--password-file <path>]
openclaw gateway stop
openclaw gateway status [--json]
openclaw gateway install                    # install as system service
openclaw gateway uninstall                  # remove system service
openclaw gateway start                      # start installed service
openclaw gateway restart                    # restart installed service
openclaw gateway call <method> [args]       # call gateway RPC method
openclaw gateway usage-cost                 # show usage/cost summary
openclaw gateway health                     # check gateway health
openclaw gateway probe                      # probe gateway connectivity
openclaw gateway discover                   # discover gateways on network
```

## Config

```bash
openclaw config get <key>                  # get a config value
openclaw config set <key> <value>          # set a config value
openclaw config set <key> --ref-provider <p> --ref-source <s> --ref-id <id>  # set SecretRef
openclaw config set --batch-json '<json>'  # batch set from JSON
openclaw config set --batch-file <path>    # batch set from file
openclaw config unset <key>                # remove a config key
openclaw config file                       # print config file path
openclaw config validate                   # validate current config
```

## Plugins

```bash
openclaw plugins install <spec>              # npm, clawhub, path, or archive
openclaw plugins install --link <path>       # symlink local
openclaw plugins disable <id>
openclaw plugins enable <id>
openclaw plugins list [--json] [--verbose]
openclaw plugins info <id> [--json]
openclaw plugins uninstall <id|clawhub-spec> [--keep-files] [--force]
openclaw plugins update [--all] [--dry-run]
openclaw plugins doctor
openclaw plugins install <spec> --dangerously-force-unsafe-install  # bypass security scan (NEW)
```

## Channels

```bash
openclaw channels list                       # list configured channels
openclaw channels status                     # quick status
openclaw channels status --probe             # deep probe
openclaw channels status --all               # all channels
openclaw channels status --json              # JSON output
openclaw channels status --timeout <ms>      # custom timeout
openclaw channels capabilities               # list channel capabilities
openclaw channels resolve                    # resolve channel config
openclaw channels logs                       # show channel logs
openclaw channels add                        # add a channel
openclaw channels remove                     # remove a channel (installs optional plugins first)
openclaw channels login                      # channel-specific login
openclaw channels logout                     # channel-specific logout
```

## Agents

```bash
openclaw agent --message "<text>"            # send message to agent (single turn)
openclaw agent --message "<text>" --thinking low
openclaw agents list                         # list configured agents
openclaw agents bindings                     # list agent bindings
openclaw agents bind                         # create agent binding
openclaw agents unbind                       # remove agent binding
openclaw agents add <name>                   # create agent
openclaw agents set-identity                 # set agent identity
openclaw agents delete <name>                # delete agent
```

## Skills

```bash
openclaw skills list                         # list loaded skills
openclaw skills info <name>                  # show skill details
openclaw skills check                        # check skill status
```

Note: `skills add`/`skills remove` are via `npx skills`, not `openclaw skills`.

## Models

```bash
openclaw models list [--all] [--local] [--provider <name>] [--json] [--plain]
openclaw models status                       # show model/provider status
openclaw models set <model>                  # set default model
openclaw models set-image <model>            # set default image model
openclaw models scan                         # scan for available models
openclaw models aliases list                 # list model aliases
openclaw models aliases add                  # add model alias
openclaw models aliases remove               # remove model alias
openclaw models fallbacks list               # list fallback chain
openclaw models fallbacks add                # add fallback model
openclaw models fallbacks remove             # remove fallback model
openclaw models image-fallbacks list|add|remove  # image model fallbacks
openclaw models auth add                     # interactive token provider setup
openclaw models auth login                   # OAuth/token login flow
openclaw models auth setup-token             # Anthropic setup-token paste
openclaw models auth paste-token [--expires-in <duration>]  # token paste with optional expiration
openclaw models auth login-github-copilot    # GitHub Copilot auth
openclaw models auth order get|set|clear     # auth profile order management
```

## Sessions

```bash
openclaw sessions list                       # list active sessions
openclaw sessions info <key>                 # show session details
```

## Tasks

```bash
openclaw tasks [--json] [--runtime <name>] [--status <name>]  # list tasks (default action)
openclaw tasks list [--json] [--runtime <name>] [--status <name>]  # explicit list
openclaw tasks show <lookup> [--json]                         # show one task by id, run id, or session key
openclaw tasks notify <lookup> <policy>                       # set notify policy (done_only|state_changes|silent)
openclaw tasks cancel <lookup>                                # cancel a running task
openclaw tasks audit [--json] [--severity <level>] [--code <name>] [--limit <n>]  # audit findings
openclaw tasks maintenance [--json] [--apply]                 # preview or apply task ledger maintenance
```

Runtime filter values: `subagent`, `acp`, `cron`, `cli`. Status filter values: `queued`, `running`, `succeeded`, `failed`, `timed_out`, `cancelled`, `lost`. Audit severity: `warn`, `error`. Audit codes: `stale_queued`, `stale_running`, `lost`, `delivery_failed`, `missing_cleanup`, `inconsistent_timestamps`. Maintenance without `--apply` is a dry run; `--apply` runs reconciliation, cleanup stamping, and pruning.

Chat command: `/tasks` - shows task status for the current session (active + total counts, up to 5 visible tasks with timing and detail). Falls back to agent-scoped view when no session-scoped tasks exist.

## Daemon (legacy alias)

```bash
openclaw daemon install [--port N] [--runtime node|bun] [--force]
openclaw daemon uninstall
openclaw daemon start
openclaw daemon stop
openclaw daemon restart
openclaw daemon status [--json]
```

Install/manage the gateway as a system service (launchd on macOS, systemd on Linux, schtasks on Windows). Restart checks for gateway token drift (service token vs config token) before proceeding. Disabled in Nix mode.

## Onboarding

```bash
openclaw onboard                             # interactive
openclaw onboard --non-interactive --accept-risk  # automated
openclaw onboard --mode local --flow quick
openclaw onboard --reset --reset-scope full
```

Note: `onboard` avoids persisting talk fallback API key on fresh setup.

## Messages

```bash
openclaw message send "<text>"               # send to default channel
openclaw message send "<text>" --channel telegram
```

## Status

```bash
openclaw status                              # basic status
openclaw status --all                        # full status report
openclaw status --deep                       # gateway health probes
openclaw status --usage                      # provider usage snapshot
openclaw status --verbose                    # gateway connection details
openclaw status --json                       # JSON output
openclaw status --timeout <ms>               # custom timeout
openclaw status --debug                      # debug connection info
```

## Secrets

```bash
openclaw secrets reload                      # reload secret references
openclaw secrets audit                       # audit secret resolution
openclaw secrets configure                   # configure secrets provider
openclaw secrets apply                       # apply secrets to config
```

Secret resolution modes: `"strict"`, `"summary"`, `"operational_readonly"`.
Falls back to local resolution when gateway unavailable.
Target registry groups: `memory`, `qrRemote`, `channels`, `models`, `agentRuntime`, `status` (`src/cli/command-secret-targets.ts`).

## ACP

```bash
openclaw acp [--url <url>] [--token <token>] [--token-file <path>]
openclaw acp [--password <password>] [--password-file <path>]
openclaw acp [--session <key>] [--session-label <label>]
openclaw acp [--require-existing] [--reset-session]
openclaw acp [--no-prefix-cwd] [--provenance off|meta|meta+receipt]
openclaw acp [-v|--verbose]
openclaw acp client                          # run ACP client bridge
```

Runs an ACP bridge backed by the Gateway. Supports `--token-file`/`--password-file` for secret-safe credential passing (prefer over `--token`/`--password`).

## Cron

```bash
openclaw cron status [--json]                # cron scheduler status
openclaw cron list [--all] [--json]          # list jobs (--all includes disabled)
openclaw cron add|create --name <name>       # add a cron job (see full options below)
openclaw cron edit <id>                      # patch a cron job (see full options below)
openclaw cron rm|remove|delete <id> [--json] # remove a cron job
openclaw cron enable <id>                    # enable a cron job
openclaw cron disable <id>                   # disable a cron job
openclaw cron runs --id <id> [--limit <n>]   # show run history (default limit 50)
openclaw cron run <id> [--due]               # manually trigger (--due = only when due)
```

### `cron add` full options

```
Schedule (exactly one required):
  --at <when>              One-shot time (ISO with offset, or +duration; use --tz for offset-less)
  --every <duration>       Interval (e.g. 10m, 1h)
  --cron <expr>            5-field or 6-field cron expression
  --tz <iana>              Timezone for cron/offset-less --at (IANA)
  --stagger <duration>     Cron stagger window (e.g. 30s, 5m)
  --exact                  Disable cron staggering (stagger=0)

Identity:
  --name <name>            Job name (required)
  --description <text>     Optional description
  --disabled               Create job disabled
  --agent <id>             Agent id
  --session <target>       Session target (main|isolated|current|session:<id>)
  --session-key <key>      Session key for routing
  --wake <mode>            Wake mode (now|next-heartbeat, default: now)

Lifecycle:
  --delete-after-run       Delete one-shot job after success
  --keep-after-run         Keep one-shot job after success

Payload (exactly one required):
  --system-event <text>    systemEvent payload (main session)
  --message <text>         agentTurn payload (isolated/current/custom session)
  --thinking <level>       Thinking level (off|minimal|low|medium|high|xhigh)
  --model <model>          Model override (provider/model or alias)
  --timeout-seconds <n>    Timeout seconds for agent jobs
  --light-context          Lightweight bootstrap context
  --tools <csv>            Tool allow-list (comma-separated, e.g. exec,read,write)

Delivery:
  --announce               Announce summary to a chat (subagent-style)
  --deliver                Deprecated alias for --announce
  --no-deliver             Disable announce delivery and skip main-session summary
  --channel <channel>      Delivery channel (default: last)
  --to <dest>              Destination (E.164, Telegram chatId, Discord channel/user)
  --account <id>           Channel account id (multi-account setups)
  --best-effort-deliver    Do not fail job if delivery fails
```

### `cron edit` full options

Accepts all `cron add` options as patch fields, plus:

```
  --enable / --disable              Toggle job enabled state
  --clear-agent                     Unset agent (use default)
  --clear-session-key               Unset session key
  --no-light-context                Disable lightweight bootstrap
  --clear-tools                     Remove tool allow-list (use all tools)
  --no-best-effort-deliver          Fail job when delivery fails

Failure alerts:
  --failure-alert / --no-failure-alert           Enable/disable failure alerts
  --failure-alert-after <n>                      Alert after N consecutive errors
  --failure-alert-channel <channel>              Alert channel
  --failure-alert-to <dest>                      Alert destination
  --failure-alert-cooldown <duration>            Min time between alerts (e.g. 1h, 30m)
  --failure-alert-mode <mode>                    Alert mode (announce|webhook)
  --failure-alert-account-id <id>                Account ID for alert channel
```

Run `openclaw doctor --fix` to normalize legacy cron job storage.

## Diagnostics

```bash
openclaw doctor                              # diagnose issues
openclaw doctor --fix                        # auto-repair (see repair list below)
openclaw doctor --repair                     # alias for --fix
openclaw doctor --force                      # force repair without confirmation
openclaw doctor --deep                       # deep diagnostics (scan extra gateway services)
openclaw doctor --yes                        # accept defaults without prompting
openclaw doctor --non-interactive            # run without prompts (safe migrations only)
openclaw doctor --generate-gateway-token     # generate new gateway token
openclaw doctor --no-workspace-suggestions   # suppress workspace suggestions
openclaw dashboard                           # open web dashboard
openclaw reset                               # reset config/sessions
openclaw uninstall                           # uninstall openclaw
```

### Doctor `--fix` repairs

Repair contributions run in order:

1. **Gateway config** - checks gateway.mode and auth.mode ambiguity
2. **Auth profiles** - repairs legacy OAuth profile IDs, removes deprecated CLI auth profiles
3. **Gateway auth** - generates gateway token when missing (unless SecretRef-managed)
4. **Legacy state** - migrates legacy sessions/agent/WhatsApp auth state
5. **Legacy plugin manifests** - repairs legacy plugin manifest contracts
6. **Bundled plugin runtime deps** - installs missing npm dependencies required by bundled plugins (`npm install --omit=dev --no-save`)
7. **State integrity** - checks state directory structure
8. **Session locks** - checks for stale session locks
9. **Legacy cron normalization** - normalizes cron store: `jobId` to `id`, bare-string schedules to `{kind,expr}`, `schedule.cron` to `schedule.expr`, payload kind casing, legacy top-level payload/delivery fields, `deliver` mode to `announce`, legacy `notify: true` webhook fallback migration, stagger defaults, sessionTarget inference
10. **Sandbox** - repairs sandbox images, warns about scope
11. **Gateway services** - scans extra gateway installs, repairs service config, checks launchd overrides
12. **Startup matrix** - runs startup matrix migration on `--fix`
13. **Security** - notes security warnings
14. **Browser** - checks Chrome MCP browser readiness
15. **OAuth TLS** - checks OpenAI OAuth TLS prerequisites (deep mode)

Config repair sequence (runs during config flow when `--fix` active):

- **Telegram allowFrom usernames** - normalizes username entries in allowFrom lists
- **Discord numeric IDs** - fixes string/number type mismatches in Discord IDs
- **Open-policy allowFrom normalization** - adds missing `"*"` wildcard to `allowFrom` when `dmPolicy="open"` (top-level or nested `dm.allowFrom` depending on channel)
- **Bundled plugin load path migration** - rewrites legacy `dist/extensions/` or `dist-runtime/extensions/` paths to current `extensions/` paths in `plugins.load.paths`
- **Stale plugin config** - prunes `plugins.allow` and `plugins.entries` refs to plugins no longer installed; removes legacy web search config migration paths
- **Allowlist policy allowFrom** - repairs allowlist policy allowFrom entries
- **Channel plugin blockers** - warns when configured channels have their backing plugin disabled (`plugins.entries.<id>.enabled=false` or `plugins.enabled=false`)
- **Legacy tools-by-sender migration** - migrates untyped `toolsBySender` keys to typed `id:` prefix entries (deprecated bare keys become `id:<key>`)
- **Exec safe-bin coverage** - scaffolds missing `safeBinProfiles` entries for custom safeBins, warns about interpreter/runtime bins without profiles and risky semantics entries
- **Expanded cron normalization** - `delivery.mode` normalization, `sessionTarget` inference/normalization, legacy delivery input hoisting from payload to delivery object, stagger defaults for cron-type schedules, `schedule.anchorMs` coercion for every-type schedules

Non-interactive cron repair is properly gated (requires `--fix` flag in non-interactive mode). Uninstall accepts plugin IDs, names, installed specs, resolved specs, marketplace plugin names, and `clawhub:<package>` specs (versionless match supported).

## Exec Environment

Child commands spawned via `exec` receive `OPENCLAW_CLI=1` in their environment (`src/infra/openclaw-exec-env.ts`). Shell-like runtimes also receive `OPENCLAW_SHELL` markers:
- `exec` - commands run through the exec tool
- `acp-client` - `openclaw acp client` bridge process
- `tui-local` - local TUI `!` shell commands
- `acp` - ACPX runtime backend child processes (`extensions/acpx/src/runtime-internals/process.ts`)

Shell-wrapper positional-argv allowlist matching (`src/infra/exec-approvals-allowlist.ts`) only permits direct carrier invocations: rejects single-quoted `$0`/`$n` tokens and newline-separated exec to prevent payload smuggling, while still accepting `exec -- carrier` forms.

`exec.host` default changed from `"sandbox"` to `"auto"` - picks the best available exec target at runtime.

`awk` and `sed` are excluded from the safeBins fast path to prevent injection via their expression arguments.

## Chat-Native Plugin Commands

When `commands.plugins: true` is enabled in config, plugin management is available directly in chat. Uses the same resolver as the CLI.

```
/plugin install clawhub:<pkg>    # install from ClawHub
/plugin install <spec>           # install (ClawHub first, npm fallback)
/plugin show <id>                # inspect plugin details
/plugin enable <id>              # enable a plugin
/plugin disable <id>             # disable a plugin
/plugin list                     # list loaded plugins
```

## Sub-CLIs (additional)

```bash
openclaw tui                                 # terminal UI
openclaw logs                                # view logs
openclaw system                              # system info
openclaw approvals                           # manage approvals
openclaw nodes                               # manage browser nodes
openclaw devices                             # manage paired devices
openclaw node                                # node management
openclaw sandbox                             # sandbox configuration
openclaw dns                                 # DNS-SD discovery
openclaw docs                                # open documentation
openclaw hooks                               # manage hooks
openclaw webhooks                            # manage webhooks
openclaw qr                                  # QR code pairing
openclaw pairing                             # device pairing
openclaw directory                           # agent directory
openclaw security                            # security audit
openclaw update                              # check for updates
openclaw completion                          # shell completions
```

## Dev Commands

```bash
pnpm install                                 # install deps
pnpm build                                   # type-check + build
pnpm tsgo                                    # TypeScript checks only
pnpm check                                   # lint + format check
pnpm format:fix                              # auto-format
pnpm test                                    # vitest
pnpm test:coverage                           # with coverage
pnpm openclaw ...                            # run CLI in dev mode
```
