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

## Onboarding

```bash
openclaw onboard                             # interactive
openclaw onboard --non-interactive --accept-risk  # automated
openclaw onboard --mode local --flow quick
openclaw onboard --reset --reset-scope full
```

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

## Diagnostics

```bash
openclaw doctor                              # diagnose issues
openclaw login                               # re-authenticate web provider
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
