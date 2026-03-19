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
| Matrix | `extensions/matrix/` | via plugin config | matrix-js-sdk, thread binding commands |
| Zalo | `extensions/zalo/` | via plugin config | Zalo Official Account API |
| Zalo User | `extensions/zalouser/` | via plugin config | Zalo personal account |
| Voice Call | `extensions/voice-call/` | via plugin config | Twilio/SIP voice |
| Feishu/Lark | `extensions/feishu/` | via plugin config | Feishu bot API |
| BlueBubbles | `extensions/bluebubbles/` | via plugin config | iMessage via BlueBubbles server |
| Mattermost | `extensions/mattermost/` | via plugin config | Mattermost WebSocket + slash HTTP |
| WhatsApp | `extensions/whatsapp/` | via plugin config | WhatsApp via Baileys, npm-publishable |
| ACPX | `extensions/acpx/` | via plugin config | ACP runtime backend (acpx CLI) |

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

## Thread Bindings (Telegram, Discord & Matrix)

Telegram, Discord, and Matrix support thread-bound sessions via `threadBindings` config:

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

Thread binding spawn policy defaults (`src/channels/thread-bindings-policy.ts`):
- Discord and Matrix default spawn flags to `false`
- Other channels default to `true`

Matrix thread binding commands: `/acp spawn`, `/session spawn`, `/focus`, `/unfocus` - wired through `bindings.compileConfiguredBinding`/`matchInboundConversation`.

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
- **Network fallback**: resolver-scoped dispatchers with IPv4 fallback retry on `ETIMEDOUT`/`ENETUNREACH`/`UND_ERR_CONNECT_TIMEOUT` (`src/telegram/fetch.ts`)
- **Duplicate prevention**: deduplicates messages when preview edit times out before delivery confirmation
- **Exec approvals**: per-account `execApprovals` config with `approvers` list, `target` (`"dm"`, `"channel"`, `"both"`), and inline approval buttons for OpenCode/Codex flows (`src/telegram/exec-approvals.ts`)
- **Direct delivery hooks**: bridges direct delivery to internal `message:sent` hooks (`src/telegram/bot/delivery.replies.ts`); media loader now injected via plugin-sdk path

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
- **maxLinesPerMessage**: effective value applied in live replies; resolved per-account with root/account config merge (`src/discord/accounts.ts`)
- **Account helper cycle broken**: account resolution and inspect now import from `extensions/discord/src/runtime-api.ts` cleanly
- **Strict DM allowlist auth**: enforced for DM component interactions (PR #49997)

## Discord Architecture

Inbound event processing system:
- `src/discord/monitor/inbound-worker.ts` - keyed async queue per session
- `src/discord/monitor/inbound-job.ts` - job serialization and execution
- `src/discord/monitor/timeouts.ts` - timeout normalization and abort signal management
- `src/discord/monitor/message-handler.ts` - debounce + worker integration

## Matrix Extension

New capabilities added:

- **Thread binding commands**: `/acp spawn`, `/session spawn`, `/focus`, `/unfocus` wired through binding compilation
- **Persistent sync state**: `FileBackedMatrixSyncStore` with debounced writes and `cleanShutdown` tracking
- **Startup migration**: legacy Matrix state migration wired into `openclaw doctor` and gateway startup; doctor migration previews restored
- **Poll vote alias**: `messageId` accepted as alias for `pollId` parameter in poll votes
- **Onboarding**: runtime-safe status checks (PR #49995)

## Account Inspection & Credential Status

Pattern for safe credential projection without exposing tokens:

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
- `src/channels/account-snapshot-fields.ts` - shared utilities for credential status projection (supports `tokenStatus`, `botTokenStatus`, `appTokenStatus`, `signingSecretStatus`, `userTokenStatus`)

## Channel Status

```bash
openclaw channels status            # quick status
openclaw channels status --probe    # deep probe (tests connections)
openclaw channels status --all      # all channels (read-only)
openclaw channels status --json     # JSON output
```

Falls back to config-only status when gateway unreachable. Reports "secret unavailable in this command path" for unresolvable SecretRef-backed tokens.

## Outbound Target & Action Resolution

Target display and action fallbacks moved to channel plugins:
- `messaging.formatTargetDisplay` - plugin callbacks for target display
- `messaging.inferTargetChatType` - plugin delegates for target kind inference
- `threading.resolveAutoThreadId` - auto-thread ID resolution moved to plugins
- Channel-specific message action fallbacks removed from core outbound

## Block Streaming

- Newline chunk mode no longer flushes per paragraph; `flushOnEnqueue` is opt-in only
- Envelope timestamp formatting honors timezone via `formatEnvelopeTimestamp`

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

Note: `openclaw channels remove` now installs optional plugins before removal.

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
- `src/channels/dock.ts` - channel docking with group policy resolution per channel
- `src/channels/native-command-session-targets.ts` - native command session target resolution
- `src/channels/plugins/helpers.ts` - plugin helpers (default account resolution, pairing hints, DM security policy builder)
- `src/channels/plugins/group-mentions.test.ts` - group mention handling
- `src/channels/plugins/group-policy-warnings.ts` - group policy warning collectors (open policy, allowlist provider, missing route allowlist)
- `src/channels/plugins/onboarding/` - channel-specific onboarding helpers
- `src/auto-reply/` - auto-reply logic, skill commands

Messages flow: Channel -> Routing -> Agent -> Response -> Channel

WebChat replies now stay on WebChat instead of being rerouted by persisted delivery routing (#37135).

## Extension-Specific Fixes

**MS Teams** (`extensions/msteams/`):
- Uses General channel conversation ID as team key for Bot Framework compatibility; Bot Framework sends `channelData.team.id` as the conversation ID, not the Graph API group GUID (`src/resolve-allowlist.ts`)

**Mattermost** (`extensions/mattermost/`):
- Reads `replyTo` param as fallback when `replyToId` is blank in plugin `handleAction` send paths (`src/channel.ts`)
- Fixes DM media upload for unprefixed 26-char user IDs (`src/mattermost/send.ts`)
- Sanitized `actionId` to alphanumeric-only with empty-id and collision guards (PR #49920)

**Feishu/Lark** (`extensions/feishu/`):
- Passes `mediaLocalRoots` in `sendText` local-image auto-convert shim so local path images resolve correctly (`src/outbound.ts`)
- `@_all` no longer treated as bot-specific mention (PR #50440)
- Bot-menu event keys mapped to slash commands (PR #49986)

**ACPX** (`extensions/acpx/`):
- ACP runtime backend plugin: registers via `api.registerService()`, not `registerChannel()`
- Config: `command`, `expectedVersion`, `cwd`, `permissionMode` (`approve-all`/`approve-reads`/`deny-all`), `nonInteractivePermissions` (`deny`/`fail`), `strictWindowsCmdWrapper`, `timeoutSeconds`, `queueOwnerTtlSeconds`, `mcpServers`
- MCP server injection: named MCP server definitions injected into ACPX session bootstrap via proxy agent command
- Pinned version: `0.1.15`, auto-installs plugin-local if bundled binary missing/mismatched
- Spawned processes receive `OPENCLAW_SHELL=acp` env marker

**WhatsApp** (`extensions/whatsapp/`):
- Now npm-publishable (`private: true` removed from package.json)
- Uses Baileys library for WhatsApp Web connection

## Allowlists & Pairing

- Each channel supports allowlists for authorized users
- Pairing: some channels support device/user pairing flows
- Pairing setup codes now include shared auth (bootstrap token) via `src/pairing/setup-code.ts`
- Command gating: channels can restrict which commands are available
- Onboarding: channel-specific onboarding prompts
