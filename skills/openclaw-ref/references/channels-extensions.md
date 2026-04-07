# OpenClaw Channels & Extensions

## Built-in Channels

| Channel | Code Path | Config Key | Notes |
|---------|-----------|------------|-------|
| Telegram | `extensions/telegram/src/` | `channels.telegram` | Long polling or webhook, bot token required |
| Discord | `extensions/discord/src/` | `channels.discord` | Bot token, guild-based |
| Slack | `extensions/slack/src/` | `channels.slack` | App token + bot token |
| Signal | `extensions/signal/src/` | `channels.signal` | signal-cli based, phone number required |
| iMessage | `extensions/imessage/src/` | `channels.imessage` | macOS only, BlueBubbles or native |
| WhatsApp | `extensions/whatsapp/` | `channels.whatsapp` | Baileys library for WhatsApp Web protocol |
| Web UI | `src/channels/web/` | `channels.web` | Built-in web chat interface |

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
| ACPX | `extensions/acpx/` | via plugin config | Embedded ACP runtime backend |
| QQ Bot | `extensions/qqbot/` | via plugin config | QQ Bot API |
| SearXNG | `extensions/searxng/` | via plugin config | Self-hosted meta-search web search provider |
| Nostr | `extensions/nostr/` | via plugin config | NIP-04 encrypted DMs via nostr-tools |
| Google Chat | `extensions/googlechat/` | via plugin config | Google Chat via google-auth-library |
| LINE | `extensions/line/` | via plugin config | LINE Messaging API |
| IRC | `extensions/irc/` | via plugin config | IRC protocol |
| Twitch | `extensions/twitch/` | via plugin config | Twitch chat via Twurple |
| Nextcloud Talk | `extensions/nextcloud-talk/` | via plugin config | Nextcloud Talk API |
| Synology Chat | `extensions/synology-chat/` | via plugin config | Synology Chat webhook/bot |
| Tlon | `extensions/tlon/` | via plugin config | Tlon/Urbit Landscape messaging |
| QA Channel | `extensions/qa-channel/` | via plugin config | Internal QA testing channel with bus-based transport (NEW) |
| Webhooks | `extensions/webhooks/` | via plugin config | Authenticated inbound webhooks binding external automation to TaskFlows (NEW) |

## Extension Plugins (Non-Channel)

| Extension | Path | Type | Notes |
|-----------|------|------|-------|
| SearXNG | `extensions/searxng/` | Web search provider | Registers via `api.registerWebSearchProvider()`; self-hosted SearXNG meta-search, no API key required; configurable categories and language |
| Memory Wiki | `extensions/memory-wiki/` | Knowledge vault | Persistent wiki compiler and Obsidian-friendly knowledge vault; supports vault modes (isolated, bridge, unsafe-local), belief-layer digests, and Obsidian CLI integration (NEW) |
| Alibaba | `extensions/alibaba/` | AI provider | Video generation provider via Alibaba Model Studio / DashScope API (NEW) |
| Amazon Bedrock Mantle | `extensions/amazon-bedrock-mantle/` | AI provider | Bedrock model discovery layer with sync runtime registration (NEW) |
| Arcee | `extensions/arcee/` | AI provider | Arcee AI provider via direct API or OpenRouter (NEW) |
| Comfy | `extensions/comfy/` | AI provider | ComfyUI image/music/video generation; local or cloud mode with workflow path config (NEW) |
| Fireworks | `extensions/fireworks/` | AI provider | Fireworks AI provider (NEW) |
| Qwen | `extensions/qwen/` | AI provider | Qwen Cloud provider with media understanding + video generation; China and Global endpoints (NEW) |
| Runway | `extensions/runway/` | AI provider | Runway video generation provider (NEW) |
| StepFun | `extensions/stepfun/` | AI provider | StepFun provider with China and Global endpoints, Step Plan support (NEW) |
| Vydra | `extensions/vydra/` | AI provider | Vydra speech, image, and video generation provider (NEW) |
| QA Lab | `extensions/qa-lab/` | Internal testing | Internal QA test harness (NEW) |

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

## Channel Plugin Type Changes

The `ChannelPlugin` type gained several new adapter slots:

- `approvalCapability?: ChannelApprovalCapability` - replaces the old `approvals?: ChannelApprovalAdapter` field; unifies auth + delivery + render + native approval surfaces into a single capability object
- `secrets?: ChannelSecretsAdapter` - channel-specific secret target registry entries and runtime config assignments
- `doctor?: ChannelDoctorAdapter` - channel-specific doctor diagnostic contracts
- `setupWizard` now accepts both `ChannelSetupWizard` and `ChannelSetupWizardAdapter`

New adapter types added:
- `ChannelSecretsAdapter` - secret target registry, unsupported SecretRef surface patterns, runtime config assignments
- `ChannelExposure` - fine-grained visibility control: `configured`, `setup`, `docs` booleans per channel (`src/channels/plugins/exposure.ts`)
- `ChannelLegacyStateMigrationPlan` - structured `copy`/`move` migration plans with source/target paths
- `ChannelConfigAdapter` gained `hasConfiguredState` and `hasPersistedAuthState` probes
- `ChannelSetupAdapter` gained `singleAccountKeysToMove`, `namedAccountPromotionKeys`, and `resolveSingleAccountPromotionTarget`

Thread and messaging adapter additions:
- `replyToMode` gained a new `"batched"` option alongside `"off"`, `"first"`, `"all"`
- `ChannelOutboundAdapter` gained `sanitizeText`, `supportsPollDurationSeconds`, `supportsAnonymousPolls`
- `ChannelMessagingAdapter` gained `transformReplyPayload`, `resolveLegacyGroupSessionKey`, `canonicalizeLegacySessionKey`, `deriveLegacySessionChatType`
- `ChannelAgentPromptAdapter` gained `inboundFormattingHints` returning `{ text_markup, rules }`
- `ChannelMessageActionAdapter` gained `resolveCliActionRequest` and `messageActionTargetAliases`

Key files: `src/channels/plugins/types.core.ts`, `src/channels/plugins/types.adapters.ts`, `src/channels/plugins/types.plugin.ts`

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

Thread binding spawn policy is now **plugin-driven** instead of hardcoded per channel. `resolveDefaultTopLevelPlacement()` reads `conversationBindings.defaultTopLevelPlacement` from the channel plugin; channels reporting `"child"` (Discord, Matrix) get thread-based spawning by default. The old hardcoded `DISCORD_THREAD_BINDING_CHANNEL`/`MATRIX_THREAD_BINDING_CHANNEL` constants are removed.

Error messages are now generic and include the channel name dynamically: `"Thread bindings are disabled for ${channel} (set channels.${channel}.threadBindings.enabled=true ...)"` instead of channel-specific strings.

Matrix thread binding commands: `/acp spawn`, `/session spawn`, `/focus`, `/unfocus` - wired through `bindings.compileConfiguredBinding`/`matchInboundConversation`.

Key files: `src/channels/thread-bindings-policy.ts`, `extensions/telegram/src/thread-bindings.ts`, Discord thread binding via plugin SDK

## Centralized Inbound Mention Policy

Group mention gating was centralized across all channels into a shared `resolveInboundMentionDecision({ facts, policy })` API (`src/channels/mention-gating.ts`). Previously each channel implemented its own mention bypass logic.

Key types:
- `InboundMentionFacts` - `canDetectMention`, `wasMentioned`, `hasAnyMention`, `implicitMentionKinds`
- `InboundMentionPolicy` - `isGroup`, `requireMention`, `allowedImplicitMentionKinds`, `allowTextCommands`, `hasControlCommand`, `commandAuthorized`
- `InboundImplicitMentionKind` - `"reply_to_bot"`, `"quoted_bot"`, `"bot_thread_participant"`, `"native"`
- `InboundMentionDecision` - `effectiveWasMentioned`, `shouldSkip`, `implicitMention`, `matchedImplicitMentionKinds`, `shouldBypassMention`

Channels updated to use the shared API: Discord, Slack, Telegram, Signal, iMessage, WhatsApp, Google Chat, MS Teams, LINE, Nextcloud Talk, Zalo User. The legacy flat-params overload is deprecated but still accepted.

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
- **Network fallback**: resolver-scoped dispatchers with IPv4 fallback retry on `ETIMEDOUT`/`ENETUNREACH`/`UND_ERR_CONNECT_TIMEOUT` (`extensions/telegram/src/fetch.ts`)
- **Duplicate prevention**: deduplicates messages when preview edit times out before delivery confirmation
- **Exec approvals**: per-account `execApprovals` config with `approvers` list, `target` (`"dm"`, `"channel"`, `"both"`), and inline approval buttons for OpenCode/Codex flows (`extensions/telegram/src/exec-approvals.ts`). Now uses shared `createChannelExecApprovalProfile()` from plugin-sdk for client enablement, approver checks, request filtering, and local prompt suppression
- **Direct delivery hooks**: bridges direct delivery to internal `message:sent` hooks (`extensions/telegram/src/bot/delivery.replies.ts`); media loader now injected via plugin-sdk path
- **Safe send retry**: `isSafeToRetrySendError()` only retries pre-connect errors (`ECONNREFUSED`, `ENOTFOUND`, `EAI_AGAIN`, `ENETUNREACH`, `EHOSTUNREACH`) to prevent duplicate messages; post-connect errors like `ECONNRESET`/`ETIMEDOUT` are not retried for non-idempotent sends (`extensions/telegram/src/network-errors.ts`)
- **Topic delivery routing preserved**: DM topic `threadId` propagated correctly in announce/delivery contexts so replies land in the correct topic thread
- **Media retry with file-too-big guard**: `resolveTelegramFileWithRetry()` retries `getFile` up to 3 attempts with 1-4s jitter delay; permanently skips Telegram Bot API >20MB `file is too big` errors instead of retrying (`extensions/telegram/src/bot/delivery.resolve-media.ts`)
- **Lazy send runtime loading**: Telegram send runtime is now lazily loaded from entrypoints instead of eagerly imported, reducing startup cost (NEW)

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
      "autoArchiveDuration": 1440,
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
- **maxLinesPerMessage**: effective value applied in live replies; resolved per-account with root/account config merge (`extensions/discord/src/accounts.ts`)
- **Account helper cycle broken**: account resolution and inspect now import from `extensions/discord/src/runtime-api.ts` cleanly
- **Strict DM allowlist auth**: enforced for DM component interactions
- **Native command auth replies**: privileged native slash commands (e.g. `/config show`, `/plugins list`) now return explicit "You are not authorized" reply on auth failure instead of falling through to Discord's generic empty-interaction fallback; gated on `CommandSource === "native"` in `rejectUnauthorizedCommand()`/`rejectNonOwnerCommand()` gates
- **Bounded inbound media downloads**: attachment and sticker fetches use `DISCORD_ATTACHMENT_IDLE_TIMEOUT_MS` (60s idle) and `DISCORD_ATTACHMENT_TOTAL_TIMEOUT_MS` (120s total) timeouts per individual download; the inbound worker abort signal remains the outer bound for the full message (`extensions/discord/src/monitor/timeouts.ts`)
- **Cover image support for event create**: `guild-admin` action handler now accepts an `image` param for event cover art; trusted media roots passed to loader (PR #60883) (NEW)
- **DM ACP binding identity stabilized**: fixes identity resolution for ACP bindings in Discord DM contexts (NEW)

## Discord Architecture

Inbound event processing system:
- `extensions/discord/src/monitor/inbound-worker.ts` - keyed async queue per session
- `extensions/discord/src/monitor/inbound-job.ts` - job serialization and execution
- `extensions/discord/src/monitor/timeouts.ts` - timeout normalization and abort signal management
- `extensions/discord/src/monitor/message-handler.ts` - debounce + worker integration

Voice subsystem additions:
- `extensions/discord/src/voice/capture-state.ts` - per-speaker voice capture state with generation tracking (NEW)
- `extensions/discord/src/voice/receive-recovery.ts` - DAVE encryption failure recovery with `DecryptionFailed` pattern detection, passthrough fallback (initial 30s / rearm 15s expiry), and reconnect threshold (3 failures in 30s window) (NEW)
- `extensions/discord/src/voice/sanitize.ts` - voice input text sanitization (NEW)

Approval handler runtime:
- `extensions/discord/src/approval-handler.runtime.ts` - centralized Discord-specific approval rendering and delivery (626 lines); implements `ChannelApprovalNativeRuntimeAdapter` with pending/resolved/expired view rendering via Carbon UI components; replaces bulk of old `exec-approvals.ts` logic (NEW)

## Approval Architecture (Plugin-SDK Split)

The approval system underwent a major structural split in the plugin-sdk. The old monolithic `approval-runtime` module was decomposed into purpose-specific modules:

| Module | Runtime export | Purpose |
|--------|---------------|---------|
| `approval-auth-helpers.ts` | `approval-auth-runtime` | Approver resolution, sender auth |
| `approval-client-helpers.ts` | `approval-client-runtime` | Client enablement, target recipient matching, profile factory, request filter matching, local prompt suppression |
| `approval-delivery-helpers.ts` | `approval-delivery-runtime` | Delivery suppression, DM route detection, native delivery mode resolution |
| `approval-native-helpers.ts` | `approval-native-runtime` | Origin target resolution, approver DM target resolution, session-conversation binding |
| `approval-handler-runtime.ts` | `approval-handler-runtime` | Native runtime adapter factory (`createChannelApprovalNativeRuntimeAdapter`) |
| `approval-handler-adapter-runtime.ts` | `approval-handler-adapter-runtime` | Lazy adapter factory (`createLazyChannelApprovalNativeRuntimeAdapter`) |
| `approval-gateway-runtime.ts` | `approval-gateway-runtime` | Gateway-mediated approval resolution |
| `approval-reply-runtime.ts` | `approval-reply-runtime` | Reply metadata and payload helpers |
| `approval-renderers.ts` | - | Shared approval UI renderers |

Key shared factories:
- `createApproverRestrictedNativeApprovalCapability()` - builds a full `ChannelApprovalCapability` from per-channel adapter params (approver list, delivery mode, auth checks, origin/DM target resolvers)
- `splitChannelApprovalCapability()` - splits a capability into `{ auth, delivery, nativeRuntime, render, native, describeExecApprovalSetup }` facets
- `createChannelExecApprovalProfile()` - builds a reusable profile with `isClientEnabled`, `isApprover`, `isAuthorizedSender`, `resolveTarget`, `shouldHandleRequest`, `shouldSuppressLocalPrompt`
- `createChannelNativeOriginTargetResolver()` - generic origin target resolver using turn-source + session-target + fallback chain
- `createChannelApproverDmTargetResolver()` - generic approver DM target resolver

The `ChannelPlugin.approvals` field is replaced by `ChannelPlugin.approvalCapability` which merges auth (actor action authorization, availability state) with delivery/native/render surfaces.

**Centralized native approval lifecycle** (PR #62135): approval handler bootstrap, runtime, route coordination, and view models extracted to `src/infra/approval-handler-bootstrap.ts`, `src/infra/approval-handler-runtime.ts`, `src/infra/approval-native-route-coordinator.ts`, and `src/infra/approval-view-model.ts`. Discord's `exec-approvals.ts` reduced from ~800 to ~50 lines; rendering moved to `approval-handler.runtime.ts`.

Per-channel impact:
- **Discord**: approval rendering and delivery moved to `approval-handler.runtime.ts`; `exec-approvals.ts` now thin re-export + button interaction handler using `resolveApprovalOverGateway()`
- **Slack**: `shouldHandleSlackExecApprovalRequest()` and inline auth replaced with `createChannelExecApprovalProfile()`; imports from split modules
- **Telegram**: exec approval config now gates on `account.enabled && tokenSource !== "none"`; uses shared `createChannelExecApprovalProfile()` and `isChannelExecApprovalTargetRecipient()`

## Matrix Extension

Capabilities:

- **Thread binding commands**: `/acp spawn`, `/session spawn`, `/focus`, `/unfocus` wired through binding compilation
- **Persistent sync state**: `FileBackedMatrixSyncStore` with debounced writes and `cleanShutdown` tracking
- **Startup migration**: legacy Matrix state migration wired into `openclaw doctor` and gateway startup; doctor migration previews restored
- **Poll vote alias**: `messageId` accepted as alias for `pollId` parameter in poll votes
- **Onboarding**: runtime-safe status checks
- **Thread-isolated sessions**: per-chat-type `threadReplies` config for thread-based session isolation
- **Group chat history context**: agent triggers include room history context
- **Draft streaming**: edit-in-place partial replies via message edits
- **Explicit proxy config**: `channels.matrix.proxy` for HTTP proxy support
- **Sender allowlist filtering**: fetched room context filtered by sender allowlist

## Slack Channel

- **Delivery-mirror guard**: embedded Pi session subscriber now filters `provider: "openclaw"` + `model: "delivery-mirror"` synthetic transcript entries via `isDeliveryMirrorAssistantMessage()`, preventing duplicate re-delivery to Slack ~3.6s after original
- **Chunk limit raised**: `SLACK_TEXT_LIMIT` raised from 4000 to 8000 (`extensions/slack/src/limits.ts`); passed as `fallbackLimit` to `resolveTextChunkLimit()`; config override via `textChunkLimit` still works
- **Thread explicit mention config**: `channels.slack.thread.requireExplicitMention` (default: `false`) - when `true`, suppresses implicit thread-participant mention detection so the bot only responds in threads when explicitly @mentioned (PR #58276) (NEW)
- **Guarded media transport**: fixes dispatcher leak to `globalThis.fetch` that caused media download failures in Slack (PR #62239) (NEW)

## Diagnostics

- **Cache-trace credential redaction**: credentials are now redacted from cache-trace diagnostic output to prevent accidental token exposure in diagnostic dumps

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
- `extensions/discord/src/account-inspect.ts`
- `extensions/telegram/src/account-inspect.ts`
- `extensions/slack/src/account-inspect.ts`
- `src/channels/account-snapshot-fields.ts` - shared utilities for credential status projection (supports `tokenStatus`, `botTokenStatus`, `appTokenStatus`, `signingSecretStatus`, `userTokenStatus`)

Read-only account inspect modules (`src/channels/read-only-account-inspect.discord.runtime.ts`, `slack.runtime.ts`, `telegram.ts`) have been removed; inspection is now handled through the plugin adapter `config.describeAccount` and the bundled plugin bootstrap registry.

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
  ├── tsconfig.json          # package boundary tsconfig (now required)
  ├── src/
  │   ├── channel.ts        # channel implementation
  │   ├── types.ts          # channel-specific types
  │   └── ...
  └── skills/               # optional channel-specific skills
      └── my-channel/
          └── SKILL.md
```

Package boundary `tsconfig.json` files are now added to all extensions via bulk rollout for consistent type-checking isolation.

## Channel Plugin Bootstrap Registry

New `src/channels/plugins/bootstrap-registry.ts` provides a cached bootstrap plugin registry that merges runtime and setup plugin sections. Used for early startup operations (config presence detection, secret resolution) before the full plugin runtime is available. Merges `getBundledChannelPlugin` + `getBundledChannelSetupPlugin` entries, caching sorted IDs and resolved secrets.

## Channel Plugin Module Loader

New `src/channels/plugins/module-loader.ts` provides a centralized Jiti-based module loader for channel plugins. Caches loader instances per config key, handles native TypeScript loading with proper alias maps, and centralizes Windows-compatible Jiti dist loading policy.

## Config Presence Detection

Channel config presence detection (`src/channels/config-presence.ts`) was refactored:
- Hardcoded `CHANNEL_ENV_PREFIXES` array removed; env var prefixes now resolved from plugin manifests via `listBundledChannelPluginIds()`
- Auth state detection delegates to `hasBundledChannelPersistedAuthState()` from `src/channels/plugins/persisted-auth-state.ts` instead of per-channel filesystem probes
- `ChannelPresenceOptions.includePersistedAuthState` controls whether persisted auth state contributes to channel presence

## Config Write Policy

New shared config write policy (`src/channels/plugins/config-write-policy-shared.ts`) provides reusable authorization logic for channel config writes:
- `ConfigWriteTargetLike` - global, channel-scoped, account-scoped, or ambiguous targets
- `ConfigWriteAuthorizationResultLike` - allowed or blocked with reason (`ambiguous-target`, `origin-disabled`, `target-disabled`)
- Reusable across all channels that support chat-driven config writes

## Routing & Message Flow

Key paths:
- `src/routing/` - message routing between channels
- `src/channels/` - shared channel infrastructure (summary, snapshot fields)
- `src/channels/native-command-session-targets.ts` - native command session target resolution
- `src/channels/plugins/helpers.ts` - plugin helpers (default account resolution, pairing hints, DM security policy builder)
- `src/channels/plugins/group-policy-warnings.ts` - group policy warning collectors (open policy, allowlist provider, missing route allowlist)
- `src/channels/plugins/session-conversation.ts` - session conversation resolution; resolves thread IDs, base conversation IDs, and parent conversation candidates per channel via plugin messaging hooks or bundled fallback modules
- `src/channels/model-overrides.ts` - per-channel model overrides via `channels.modelByChannel` config; resolves group/channel/thread candidates with wildcard fallback
- `src/channels/chat-meta-shared.ts` - channel metadata factory that builds `ChatChannelMeta` from plugin catalog entries instead of hardcoded maps (NEW)
- `src/auto-reply/` - auto-reply logic, skill commands

Messages flow: Channel -> Routing -> Agent -> Response -> Channel

WebChat replies now stay on WebChat instead of being rerouted by persisted delivery routing.

## Extension-Specific Fixes

**MS Teams** (`extensions/msteams/`):
- Uses General channel conversation ID as team key for Bot Framework compatibility; Bot Framework sends `channelData.team.id` as the conversation ID, not the Graph API group GUID (`src/resolve-allowlist.ts`)

**Mattermost** (`extensions/mattermost/`):
- Reads `replyTo` param as fallback when `replyToId` is blank in plugin `handleAction` send paths (`src/channel.ts`)
- Fixes DM media upload for unprefixed 26-char user IDs (`extensions/mattermost/src/send.ts`)
- Sanitized `actionId` to alphanumeric-only with empty-id and collision guards

**Feishu/Lark** (`extensions/feishu/`):
- Passes `mediaLocalRoots` in `sendText` local-image auto-convert shim so local path images resolve correctly (`src/outbound.ts`)
- `@_all` no longer treated as bot-specific mention
- Bot-menu event keys mapped to slash commands
- Config schema uses `name` (not `botName`) for account display name
- **Drive comment event handling**: new `comment-handler.ts` / `comment-dispatcher.ts` flow processes Feishu Drive comment notice events; resolves comment turn, applies allowlist/pairing policy, dispatches to agent with `Surface: "feishu-comment"` context; supports dynamic agent creation for comment flows
- **Drive tool expanded with comment CRUD**: `feishu_drive` tool now supports `list_comments`, `list_comment_replies`, `add_comment`, and `reply_comment` actions alongside existing file operations (`extensions/feishu/src/drive.ts`)
- **Workspace-only localRoots in docx upload**: `docx-upload` action enforces workspace-scoped `localRoots` to prevent path traversal (NEW)

**ACPX** (`extensions/acpx/`):
- Embedded ACP runtime backend plugin: registers via `api.registerService()`, not `registerChannel()`
- Major runtime rewrite: `runtime.ts` reduced from ~1100 to ~150 lines; subprocess management, JSON-RPC, event parsing, and process spawning extracted or removed
- Config: `cwd`, `stateDir` (NEW), `permissionMode` (`approve-all`/`approve-reads`/`deny-all`), `nonInteractivePermissions` (`deny`/`fail`), `strictWindowsCmdWrapper`, `timeoutSeconds`, `queueOwnerTtlSeconds` (now compat-only, logged as ignored), `mcpServers`
- `agents` config: per-agent `command` overrides via `agents.<name>.command` (NEW)
- `command` and `expectedVersion` removed from top-level config; the plugin uses its bundled runtime
- MCP server injection: named MCP server definitions injected into ACP session bootstrap; `mcp-command-line.mjs` replaces old `mcp-agent-command.ts`
- Pinned version: bumped from `0.1.15` to **`0.5.1`**
- Spawned processes receive `OPENCLAW_SHELL=acp` env marker
- `pluginToolsMcpBridge` config option - when enabled, injects the built-in OpenClaw plugin-tools MCP server into ACP sessions so ACP agents can call plugin-registered tools
- Config schema now requires `minLength: 1` for `cwd` field
- `configContracts.dangerousFlags` added for `permissionMode: approve-all`; `secretInputs` scoped to `mcpServers.*.env.*`
- ACP Discord recovery and reset flow hardened (PR #62132) (NEW)

**WhatsApp** (`extensions/whatsapp/`):
- Now npm-publishable (`private: true` removed from package.json)
- Uses Baileys library for WhatsApp Web connection
- Test harness stabilized: session exports preserved in login coverage and shared workers, media test module exports preserved, CI extension checks stabilized
- **Reaction guidance levels**: `resolveWhatsAppReactionLevel()` resolves per-account reaction level from config with `defaultLevel: "minimal"` and `invalidFallback: "minimal"`; levels control ack reaction behavior (`extensions/whatsapp/src/reaction-level.ts`)

**BlueBubbles** (`extensions/bluebubbles/`):
- **Localhost probe respects private-network opt-out**: `allowPrivateNetwork` config is now honored during localhost health probes; account-level overrides preserved (PR #59373) (NEW)

**QQ Bot** (`extensions/qqbot/`):
- `/bot-logs` requires explicit allowlist: `hasExplicitCommandAllowlist()` checks that `allowFrom` contains non-wildcard entries before permitting log export; keeps `/bot-logs` closed when setup leaves allowFrom in permissive mode (`extensions/qqbot/src/slash-commands.ts`)

**Webhooks** (`extensions/webhooks/`) (NEW):
- Authenticated inbound webhooks that bind external automation to OpenClaw TaskFlows
- Config: named `routes` with `sessionKey`, `secret` (string or SecretRef), optional `path`, `controllerId`, `description`, `enabled`
- HTTP handler: `createTaskFlowWebhookRequestHandler()` with per-route auth validation
- Registers via `definePluginEntry()` with resolved route config

**QA Channel** (`extensions/qa-channel/`) (NEW):
- Internal testing channel using bus-based transport protocol
- Registers as a full channel plugin via `createChatChannelPlugin()`
- Supports accounts, config schema, setup wizard, status, and channel actions

## SearXNG Extension

Bundled self-hosted web search provider plugin (`extensions/searxng/`):
- Registers via `api.registerWebSearchProvider()` using `definePluginEntry()` (`extensions/searxng/index.ts`)
- **No API key required** - only needs a SearXNG base URL (`SEARXNG_BASE_URL` env var or `plugins.entries.searxng.config.webSearch.baseUrl` config)
- Configurable `categories` (comma-separated: general, news, science, etc.) and `language` (en, de, fr, etc.) via config or per-query tool parameters
- Auto-detect order: 200 (lower priority than commercial providers)
- Web search provider contract: `webSearchProviders: ["searxng"]` in `openclaw.plugin.json`
- Tool: `searxng_search` - search query with optional `count` (1-10), `categories`, `language` parameters
- Config resolution: `resolveSearxngBaseUrl()` checks plugin config, inline env SecretRef, then `SEARXNG_BASE_URL` env var (`extensions/searxng/src/config.ts`)

## Allowlists & Pairing

- Each channel supports allowlists for authorized users
- Pairing: some channels support device/user pairing flows
- Pairing setup codes now include shared auth (bootstrap token) via `src/pairing/setup-code.ts`
- Command gating: channels can restrict which commands are available
- Onboarding: channel-specific onboarding prompts
