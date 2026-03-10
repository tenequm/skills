# OpenClaw CLI Commands

## Gateway

```bash
openclaw gateway run [--bind loopback|all] [--port N] [--force]
openclaw gateway stop
openclaw gateway status
```

## Config

```bash
openclaw config show
openclaw config set <key> <value>
openclaw config get <key>
openclaw config edit
openclaw config path
openclaw config reset
```

## Plugins

```bash
openclaw plugins install <spec>              # npm, path, or archive
openclaw plugins install --link <path>       # symlink local
openclaw plugins disable <id>
openclaw plugins enable <id>
openclaw plugins list [--json] [--verbose]
openclaw plugins info <id> [--json]
openclaw plugins uninstall <id> [--keep-files] [--force]
openclaw plugins update [--all] [--dry-run]
openclaw plugins doctor
```

## Channels

```bash
openclaw channels status                     # quick status
openclaw channels status --probe             # deep probe
openclaw channels status --all               # all channels
openclaw channels status --json              # JSON output
openclaw channels status --timeout <ms>      # custom timeout
```

Falls back to config-only status when gateway unreachable.

## Agents

```bash
openclaw agent --message "<text>"            # send message to agent
openclaw agent --message "<text>" --thinking low
openclaw agent list
openclaw agent create <name>
```

## Skills

```bash
openclaw skills list
openclaw skills add <spec>                   # install skill
openclaw skills add -g <spec>               # install globally
openclaw skills remove <name>
openclaw skills info <name>
```

## Models

```bash
openclaw models list [--all] [--local] [--provider <name>] [--json] [--plain]
openclaw models auth add                     # interactive token provider setup
openclaw models auth login                   # OAuth/token login flow
openclaw models auth setup-token             # Anthropic setup-token paste
openclaw models auth paste-token [--expires-in <duration>]  # token paste with optional expiration
```

## Daemon

```bash
openclaw daemon install [--port N] [--runtime node|bun] [--force]
openclaw daemon start
openclaw daemon stop
openclaw daemon restart
openclaw daemon status [--json]
```

Install/manage the gateway as a system service (launchd on macOS, systemd on Linux). Restart checks for gateway token drift (service token vs config token) before proceeding. Disabled in Nix mode.

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
openclaw status --latest                     # device approval recovery flow
```

## Secrets

```bash
openclaw secrets resolve                     # resolve secret references
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
openclaw acp serve                           # serve ACP gateway
```

Runs an ACP bridge backed by the Gateway. Supports `--token-file`/`--password-file` for secret-safe credential passing (prefer over `--token`/`--password`).

## Cron

```bash
openclaw cron status                         # cron job status
openclaw cron list                           # list cron jobs
openclaw cron add                            # add a cron job
openclaw cron edit                           # edit a cron job
```

Run `openclaw doctor --fix` to normalize legacy cron job storage.

## Diagnostics

```bash
openclaw doctor                              # diagnose issues
openclaw doctor --fix                        # auto-repair (cron, daemon, sandbox, etc.)
openclaw login                               # re-authenticate web provider
```

Doctor non-interactive cron repair is now properly gated (requires `--fix` flag in non-interactive mode).

## Exec Environment

Child commands spawned via `exec` receive `OPENCLAW_CLI=1` in their environment (`src/infra/openclaw-exec-env.ts`). Shell-like runtimes also receive `OPENCLAW_SHELL` markers:
- `exec` - commands run through the exec tool
- `acp` - ACP runtime backend process spawns (acpx)
- `acp-client` - `openclaw acp client` bridge process
- `tui-local` - local TUI `!` shell commands

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
