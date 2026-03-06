# OpenClaw Channels & Extensions

## Built-in Channels

| Channel | Code Path | Config Key | Notes |
|---------|-----------|------------|-------|
| Telegram | `src/telegram/` | `channels.telegram` | Long polling or webhook, bot token required |
| Discord | `src/discord/` | `channels.discord` | Bot token, guild-based |
| Slack | `src/slack/` | `channels.slack` | App token + bot token |
| Signal | `src/signal/` | `channels.signal` | signal-cli based, phone number required |
| iMessage | `src/imessage/` | `channels.imessage` | macOS only, BlueBubbles or native |
| WhatsApp (Web) | `src/web/` | `channels.whatsapp` | Browser-based web automation |
| Web UI | `src/provider-web.ts` | `channels.web` | Built-in web chat interface |

## Extension Channels

| Extension | Path | Config Key | Notes |
|-----------|------|------------|-------|
| MS Teams | `extensions/msteams/` | via plugin config | Microsoft Graph API |
| Matrix | `extensions/matrix/` | via plugin config | matrix-js-sdk |
| Zalo | `extensions/zalo/` | via plugin config | Zalo Official Account API |
| Zalo User | `extensions/zalouser/` | via plugin config | Zalo personal account |
| Voice Call | `extensions/voice-call/` | via plugin config | Twilio/SIP voice |
| Feishu/Lark | `extensions/feishu/` | via plugin config | Feishu bot API |
| BlueBubbles | `extensions/bluebubbles/` | via plugin config | iMessage via BlueBubbles server |

## Channel Plugin Registration

```typescript
// In plugin's register() function:
api.registerChannel({
  id: "my-channel",
  protocol: "my-protocol",
  plugin: {
    start: async (runtime) => { ... },
    stop: async () => { ... },
    sendMessage: async (msg) => { ... },
    // ... event handlers
  }
});
```

## Thread Bindings (Telegram & Discord)

Both Telegram and Discord now support thread-bound sessions via `threadBindings` config:

```json
{
  "threadBindings": {
    "enabled": true,
    "idleHours": 24,
    "maxAgeHours": 0,
    "spawnSubagentSessions": false,
    "spawnAcpSessions": false
  }
}
```

- Per-account binding manager with persistent state
- Supports idle timeout and hard max age expiration
- Auto-sweep mechanism cleans expired bindings
- `spawnSubagentSessions`: auto-create + bind threads for `sessions_spawn({ thread: true })`
- `spawnAcpSessions`: auto-create + bind threads for `/acp spawn`

Key files: `src/telegram/thread-bindings.ts`, Discord thread binding via plugin SDK

## Telegram Channel Config

```json
{
  "channels": {
    "telegram": {
      "token": "123456:ABC-DEF...",
      "allowlist": ["username1", "username2"],
      "mode": "longpoll",
      "commands": { "enabled": true },
      "customCommands": [{ "name": "my_cmd", "description": "..." }],
      "threadBindings": { "enabled": true },
      "dmHistoryLimit": 50,
      "network": { "autoSelectFamily": true }
    }
  }
}
```

- **Token**: raw bot token (no `TELEGRAM_BOT_TOKEN=` prefix)
- **Allowlist**: recommended for single-user DM policy
- **Mode**: `longpoll` (default, more reliable) or `webhook`
- **Custom commands**: names must match `[a-z0-9_]{1,32}` - NO hyphens
- **Streaming modes**: `"off"`, `"partial"`, `"block"`, `"progress"`
- **Direct DMs**: `direct` config keyed by chat ID for per-user settings
- **Topics**: support `agentId` for topic-specific agent routing

## Discord Channel Config

```json
{
  "channels": {
    "discord": {
      "token": "bot-token-here",
      "guildId": "optional-specific-guild",
      "threadBindings": { "enabled": true },
      "slashCommand": { "ephemeral": true },
      "autoPresence": true,
      "intents": { "presence": false, "guildMembers": false }
    }
  }
}
```

- **Token**: raw Discord bot token
- **Inbound worker**: keyed async queue for ordered message processing per session (30min timeout)
- **Event queue**: configurable `listenerTimeout`, `maxQueueSize`, `maxConcurrency`
- **Streaming modes**: `"off"`, `"partial"`, `"block"`, `"progress"`
- **Reaction notification**: `"off"`, `"own"`, `"all"`, `"allowlist"`

## Discord Architecture

New inbound event processing system:
- `src/discord/monitor/inbound-worker.ts` - keyed async queue per session
- `src/discord/monitor/inbound-job.ts` - job serialization and execution
- `src/discord/monitor/timeouts.ts` - timeout normalization and abort signal management
- `src/discord/monitor/message-handler.ts` - debounce + worker integration

## Account Inspection & Credential Status

New pattern for safe credential projection without exposing tokens:

```typescript
type CredentialStatus = "available" | "configured_unavailable" | "missing";

// Used across Discord, Telegram, Slack for UI/status renderers
type InspectedAccount = {
  name: string;
  tokenStatus: CredentialStatus;
  // channel-specific fields...
};
```

Key files:
- `src/discord/account-inspect.ts`
- `src/telegram/account-inspect.ts`
- `src/slack/account-inspect.ts`
- `src/channels/account-snapshot-fields.ts` - shared utilities for credential status projection

## Channel Status

```bash
openclaw channels status            # quick status
openclaw channels status --probe    # deep probe (tests connections)
openclaw channels status --all      # all channels (read-only)
openclaw channels status --json     # JSON output
```

Falls back to config-only status when gateway unreachable. Reports "secret unavailable in this command path" for unresolvable SecretRef-backed tokens.

## Adding a New Channel

When adding a new channel (built-in or extension):
1. Implement channel plugin interface
2. Register via `api.registerChannel()`
3. Add config type to `src/config/types.openclaw.ts`
4. Add Zod schema to `src/config/zod-schema.providers.ts`
5. Update docs: `docs/channels/`
6. Update `.github/labeler.yml` + create matching label
7. Update all UI surfaces (macOS app, web UI, mobile if applicable)
8. Add status + configuration forms

## Extension Directory Pattern

```
extensions/my-channel/
  ├── package.json
  ├── openclaw.plugin.json
  ├── index.ts              # exports plugin with registerChannel()
  ├── src/
  │   ├── channel.ts        # channel implementation
  │   ├── types.ts          # channel-specific types
  │   └── ...
  └── skills/               # optional channel-specific skills
      └── my-channel/
          └── SKILL.md
```

## Routing & Message Flow

Key paths:
- `src/routing/` - message routing between channels
- `src/channels/` - shared channel infrastructure (dock, summary, snapshot fields)
- `src/auto-reply/` - auto-reply logic, skill commands

Messages flow: Channel -> Routing -> Agent -> Response -> Channel

WebChat replies now stay on WebChat instead of being rerouted by persisted delivery routing (#37135).

## Allowlists & Pairing

- Each channel supports allowlists for authorized users
- Pairing: some channels support device/user pairing flows
- Command gating: channels can restrict which commands are available
- Onboarding: channel-specific onboarding prompts
