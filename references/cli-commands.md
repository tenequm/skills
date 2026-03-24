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
openclaw cron status                         # cron job status
openclaw cron list                           # list cron jobs
openclaw cron add                            # add a cron job
openclaw cron edit                           # edit a cron job
openclaw cron rm <id>                        # remove a cron job
openclaw cron enable <id>                    # enable a cron job
openclaw cron disable <id>                   # disable a cron job
openclaw cron runs [id]                      # show cron run history
openclaw cron run <id>                       # manually trigger cron job
```

Run `openclaw doctor --fix` to normalize legacy cron job storage.

## Diagnostics

```bash
openclaw doctor                              # diagnose issues
openclaw doctor --fix                        # auto-repair (cron, daemon, sandbox, stale plugins, etc.)
openclaw doctor --repair                     # alias for --fix
openclaw doctor --force                      # force repair without confirmation
openclaw doctor --deep                       # deep diagnostics
openclaw doctor --generate-gateway-token     # generate new gateway token
openclaw doctor --no-workspace-suggestions   # suppress workspace suggestions
openclaw dashboard                           # open web dashboard
openclaw reset                               # reset config/sessions
openclaw uninstall                           # uninstall openclaw
```

Doctor `--fix` repairs include: cron normalization, daemon/sandbox checks, stale `plugins.allow` and `plugins.entries` pruning (removes refs to plugins no longer installed). Non-interactive cron repair is properly gated (requires `--fix` flag in non-interactive mode). Uninstall accepts plugin IDs, names, installed specs, resolved specs, marketplace plugin names, and `clawhub:<package>` specs (versionless match supported).

## Exec Environment

Child commands spawned via `exec` receive `OPENCLAW_CLI=1` in their environment (`src/infra/openclaw-exec-env.ts`). Shell-like runtimes also receive `OPENCLAW_SHELL` markers:
- `exec` - commands run through the exec tool
- `acp-client` - `openclaw acp client` bridge process
- `tui-local` - local TUI `!` shell commands

Shell-wrapper positional-argv allowlist matching (`src/infra/exec-approvals-allowlist.ts`) only permits direct carrier invocations: rejects single-quoted `$0`/`$n` tokens and newline-separated exec to prevent payload smuggling, while still accepting `exec -- carrier` forms.

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
