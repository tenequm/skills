---
name: openclaw-ref
description: OpenClaw platform reference - plugin system, extensions, configuration, boot/provisioning, channels, models, CLI. Use when working on openclaw codebase, building openclaw plugins/extensions, configuring openclaw instances, provisioning openclaw gateways, designing agent provisioning flows (e.g. agentbox), or debugging openclaw config/plugin/channel issues. Triggers on openclaw, openclaw config, openclaw plugin, openclaw extension, openclaw channel, openclaw gateway, openclaw provisioning, openclaw onboarding, openclaw boot, openclaw skills, BOOT.md, openclaw.plugin.json, openclaw-x402, agentbox provisioning.
version: "2026.3.31"
metadata:
  last_refresh_sha: bf0f33db32c5cca2736e938b61eec49b3ca24616
---

# OpenClaw Platform Reference

Structured reference for the OpenClaw assistant platform. Source repo: `~/Projects/openclaw/`. Tracking version: **2026.3.31**.

## Quick Navigation

Load the relevant reference file based on the task:

### Plugin & Extension System
- **`references/plugin-system.md`** - Plugin discovery, loading, manifest format, registration API, installation CLI, SDK exports. Read when building/debugging plugins or understanding how extensions are loaded.

### Configuration
- **`references/configuration.md`** - Full config structure (`OpenClawConfig`), config paths, file format (JSON5), env var substitution, `$include` directives, validation (Zod), per-plugin config, programmatic read/write. Read when modifying or generating openclaw config.

### Boot & Provisioning
- **`references/boot-provisioning.md`** - Gateway startup sequence, BOOT.md mechanism, onboarding flows (interactive/non-interactive), plugin loading during boot, sidecar startup order, health checks. Read when designing automated provisioning or debugging startup.

### Channels & Extensions
- **`references/channels-extensions.md`** - All built-in channels (Telegram, Discord, Slack, Signal, iMessage, WhatsApp, Web) + extension channels (MS Teams, Matrix, Zalo, Voice Call, Feishu). Channel plugin registration, per-channel config, Telegram specifics. Read when adding/configuring channels.

### Models & Providers
- **`references/models-providers.md`** - Provider configuration, `models.mode` (merge/replace), x402 providers, model catalog structure, provider registration via plugins. Read when configuring model access or building provider plugins.

### CLI Commands
- **`references/cli-commands.md`** - Key CLI commands for config, plugins, channels, agents, onboarding, gateway, skills. Read when scripting openclaw setup or building automation.

### GitHub Context (live issues, PRs, gotchas)
- **`references/github-context.md`** - Open bugs, breaking changes, recent impactful PRs, plugin/config known issues, dev gotchas synthesized from GitHub. Refreshed via `/refresh-openclaw`. Read before starting any non-trivial openclaw work to avoid known pitfalls.

## Key File Paths (repo-root relative)

```
src/plugins/           - Plugin loader, discovery, registry, install, types
src/plugin-sdk/        - 100+ scoped exports for plugin consumption
src/config/            - Config loading, types, validation, defaults, paths
src/gateway/           - Gateway server, boot, startup, server methods
src/commands/          - CLI commands (onboard, config, etc.)
src/cli/               - CLI wiring (plugins-cli, skills-cli, etc.)
extensions/            - Extension implementations (channels, memory, etc.)
skills/                - Built-in skill definitions
docs/                  - Documentation (Mintlify)
```

## Config File Locations

- Main config: `~/.openclaw/config.json` (or `.json5`)
- Plugins: `~/.openclaw/plugins/`
- Skills: `~/.openclaw/skills/` (managed) + workspace skills
- Agents: `~/.openclaw/agents/<agent-id>/`
- Sessions: `~/.openclaw/agents/<agent-id>/sessions/`
- Credentials: `~/.openclaw/credentials/`
- Override: `OPENCLAW_CONFIG` env var

## Plugin Manifest Quick Ref

```json
{
  "id": "plugin-id",
  "name": "Display Name",
  "kind": "memory",
  "channels": ["channel-id"],
  "providers": ["provider-id"],
  "configSchema": { "type": "object" },
  "uiHints": { "field": { "label": "...", "sensitive": true } }
}
```

## Config Structure Quick Ref

Top-level keys in `OpenClawConfig`:
`meta`, `auth`, `acp`, `env`, `secrets`, `plugins`, `skills`, `models`, `agents`, `tools`, `channels`, `session`, `hooks`, `gateway`, `logging`, `browser`, `memory`, `messages`, `approvals`, `cron`
