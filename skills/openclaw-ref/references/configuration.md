# OpenClaw Configuration

## Config File

- **Path**: `~/.openclaw/openclaw.json` (parsed as JSON5)
- **Override**: `OPENCLAW_CONFIG_PATH` env var (supports `file:///absolute/path`)
- **Format**: JSON5 (comments, trailing commas OK)
- **Key files**: `src/config/config.ts`, `src/config/io.ts`, `src/config/paths.ts`

## Config Resolution Pipeline

1. Load `.env` file if present
2. Load raw JSON5 from disk
3. Resolve `$include` directives (file composition)
4. Substitute `${ENV_VAR}` references (with `onMissing` warning mode for graceful degradation)
5. Apply environment overrides (`OPENCLAW_CONFIG_*` env vars via `env-vars.ts`)
6. Detect duplicate agent dirs (pre-validation)
7. Validate against Zod schema (including plugin schemas)
8. Apply runtime defaults chain: `applyMessageDefaults` -> `applyLoggingDefaults` -> `applySessionDefaults` -> `applyAgentDefaults` -> `applyContextPruningDefaults` -> `applyCompactionDefaults` -> `applyModelDefaults` -> `applyTalkConfigNormalization`
9. Normalize paths (`normalizeConfigPaths`) and exec safe-bin profiles (`normalizeExecSafeBinProfilesInConfig`)
10. Apply `env.vars` / `env.*` into `process.env` (skipping already-set and unresolved `${VAR}` refs)
11. Optionally load shell env fallback (`env.shellEnv.enabled`)
12. Ensure `commands.ownerDisplaySecret` exists (auto-generate + persist if missing)
13. Return validated `OpenClawConfig` (with TTL-based caching)

## Full Config Structure (`OpenClawConfig`)

```typescript
type OpenClawConfig = {
  meta?: {
    lastTouchedVersion?: string;
    lastTouchedAt?: string | number;  // ISO timestamp or Unix epoch (coerced to ISO)
  };
  auth?: AuthConfig;
  acp?: AcpConfig;
  env?: {
    shellEnv?: { enabled?: boolean; timeoutMs?: number };  // import from login shell
    vars?: Record<string, string>;                         // inline env overrides
    [key: string]: string | ... | undefined;               // sugar: direct env vars
  };
  wizard?: {                      // setup wizard state tracking
    lastRunAt?: string;
    lastRunVersion?: string;
    lastRunCommit?: string;
    lastRunCommand?: string;
    lastRunMode?: "local" | "remote";
  };
  diagnostics?: DiagnosticsConfig;
  logging?: LoggingConfig;
  cli?: CliConfig;
  update?: {                      // update channel + auto-update policy
    channel?: "stable" | "beta" | "dev";
    checkOnStart?: boolean;
    auto?: { enabled?: boolean; stableDelayHours?: number; stableJitterHours?: number; betaCheckIntervalHours?: number };
  };
  browser?: BrowserConfig;
  ui?: {
    seamColor?: string;           // accent color (hex)
    assistant?: { name?: string; avatar?: string };
  };
  secrets?: SecretsConfig;
  skills?: SkillsConfig;
  plugins?: PluginsConfig;       // see plugin-system.md
  models?: ModelsConfig;
  nodeHost?: NodeHostConfig;      // browser proxy settings for node hosts
  agents?: AgentsConfig;
  tools?: ToolsConfig;
  bindings?: AgentBinding[];      // top-level agent route/ACP bindings
  broadcast?: BroadcastConfig;
  audio?: AudioConfig;
  media?: {                       // inbound media handling
    preserveFilenames?: boolean;
    ttlHours?: number;
  };
  messages?: MessagesConfig;
  commands?: CommandsConfig;
  approvals?: ApprovalsConfig;
  session?: SessionConfig;
  web?: WebConfig;
  channels?: ChannelsConfig;
  cron?: CronConfig;
  hooks?: HooksConfig;
  discovery?: DiscoveryConfig;    // mDNS + wide-area DNS-SD
  canvasHost?: CanvasHostConfig;  // embedded canvas HTTP server
  talk?: TalkConfig;              // NOTE: top-level, not nested under gateway
  gateway?: GatewayConfig;
  memory?: MemoryConfig;
  mcp?: McpConfig;                // MCP server definitions
};
```

Key types: `src/config/types.openclaw.ts`, `src/config/types.plugins.ts`, `src/config/types.mcp.ts`

### Notable structural changes since last refresh

- Branded config state types: `SourceConfig`, `ResolvedSourceConfig`, `RuntimeConfig` distinguish config lifecycle stages
- `ConfigFileSnapshot` now has `sourceConfig` (pre-defaults) and `runtimeConfig` (post-defaults); `config` deprecated in favor of `runtimeConfig`
- `src/config/materialize.ts` module with profiles: `load`, `missing`, `snapshot` for config default application
- `hooks.internal.enabled` now defaults to `true` (was `false`) so bundled hooks load on fresh installs
- `exec.host` default changed from `"sandbox"` to `"auto"` (picks best available target at runtime)
- `exec.applyPatch.enabled` default changed from `false` to `true`
- Auth cooldowns: `overloadedProfileRotations` (default 1), `overloadedBackoffMs` (default 0), `rateLimitedProfileRotations` (default 1), new `authPermanentBackoffMinutes` (default 10), `authPermanentMaxMinutes` (default 60)
- MCP server config: `transport` (`"sse"` | `"streamable-http"`), `headers`, `connectionTimeoutMs` fields
- Web search config rewritten: legacy per-provider shapes (`brave`, `firecrawl`, etc.) replaced with generic `Record<string, unknown>`; `openaiCodex` and `x_search` scoped blocks
- `web.fetch.maxResponseBytes` added (default 2000000); `web.fetch.provider` added for fallback provider id
- Memory search: `provider`/`fallback` changed from union to generic `string`; `qmd.extraCollections` for cross-agent search; `store.fts.tokenizer` (`"unicode61"` | `"trigram"`) for CJK
- Auth profile: new `displayName` field
- `subagents.requireAgentId` blocks sessions_spawn without explicit agentId
- SecretRef: unsupported policies now hard-fail; gateway restart token drift fixed
- `awk` and `sed` excluded from exec safeBins fast path (injection prevention)
- Gateway: `webchat.chatHistoryMaxChars` controls max chars per text field in `chat.history` responses (default: 12000, max: 500000)
- WhatsApp: `reactionLevel` field (`"off" | "ack" | "minimal" | "extensive"`) controls agent reaction behavior per account
- Agent defaults compaction: `truncateAfterCompaction` boolean (default: false); `notifyUser` boolean (default: false); `provider` for plugin compaction providers
- Model aliases updated: `gpt-mini` -> `openai/gpt-5.4-mini`, new `gpt-nano` -> `openai/gpt-5.4-nano`
- Streaming config unified: Telegram/Discord/Slack legacy flat streaming keys replaced with structured `ChannelPreviewStreamingConfig` / `SlackChannelStreamingConfig`
- `ReplyToMode` expanded: now includes `"batched"` mode across all channels
- `ContextVisibilityMode` (`"all" | "allowlist" | "allowlist_quote"`) added to Telegram, Discord, and Slack channel configs
- `TalkProviderConfig` simplified: legacy ElevenLabs fields (`voiceId`, `voiceAliases`, `modelId`, `outputFormat`, `apiKey`) removed; providers use generic `[key: string]: unknown` extensibility
- Context pruning defaults now delegated to `applyProviderConfigDefaultsWithPlugin` (plugin-driven per-provider defaults)
- New agent defaults: `videoGenerationModel`, `musicGenerationModel`, `mediaGenerationAutoProviderFallback`, `skills`, `systemPromptOverride`, `contextInjection`, `subagents.allowAgents`
- Heartbeat: `includeSystemPromptSection` boolean; `target` type simplified to `ChannelId`
- New `ModelDefinitionConfig.contextTokens` for effective runtime cap separate from native `contextWindow`
- `ModelProviderConfig.request` added for provider-level HTTP transport overrides (auth, proxy, TLS)
- `ModelsConfig` discovery toggles: `copilotDiscovery`, `huggingfaceDiscovery`, `ollamaDiscovery` added
- Exec approvals: `enabled` field changed from `boolean` to `boolean | "auto"` (`NativeExecApprovalEnableMode`) across Discord, Telegram, and Slack
- Telegram: `errorPolicy`/`errorCooldownMs` at account, group, topic, and direct levels; `trustedLocalFileRoots`; `dangerouslyAllowPrivateNetwork`; `ingest` on topics/groups
- Slack: `thread.requireExplicitMention` for suppressing implicit thread mentions
- `tools.experimental.planTool` enables structured `update_plan` tool
- `media.tools.asyncCompletion.directSend` for direct channel sends on async media generation
- `MediaProviderRequestConfig.request` for provider HTTP transport overrides
- Config IO refactored: audit logging, write-prepare, observe-recovery, owner-display-secret, invalid-config, and runtime-snapshot extracted into separate modules
- Shell env expected keys now dynamically resolved from registered provider/channel env var lists

### MCP Config

```typescript
type McpConfig = {
  servers?: Record<string, McpServerConfig>;
};

type McpServerConfig = {
  command?: string;
  args?: string[];
  env?: Record<string, string | number | boolean>;
  cwd?: string;
  workingDirectory?: string;
  url?: string;
  transport?: "sse" | "streamable-http";
  headers?: Record<string, string | number | boolean>;
  connectionTimeoutMs?: number;
  [key: string]: unknown;          // extensible for future fields
};
```

## Gateway Config

```typescript
type GatewayConfig = {
  port?: number;                  // default: 18789
  mode?: "local" | "remote";
  bind?: "auto" | "lan" | "loopback" | "custom" | "tailnet";  // default: loopback
  customBindHost?: string;        // for bind="custom"
  controlUi?: GatewayControlUiConfig;
  auth?: GatewayAuthConfig;       // mode: "none" | "token" | "password" | "trusted-proxy"
  tailscale?: GatewayTailscaleConfig;
  remote?: GatewayRemoteConfig;   // remote.enabled field added (default: true when absent)
  reload?: GatewayReloadConfig;   // mode: "off" | "restart" | "hot" | "hybrid"
  tls?: GatewayTlsConfig;
  push?: GatewayPushConfig;       // APNs relay config (baseUrl, timeoutMs)
  http?: {
    endpoints?: {
      chatCompletions?: GatewayHttpChatCompletionsConfig;
      responses?: GatewayHttpResponsesConfig;      // /v1/responses (OpenResponses API)
    };
    securityHeaders?: GatewayHttpSecurityHeadersConfig;
  };
  nodes?: GatewayNodesConfig;     // browser routing + allowed/denied commands
  trustedProxies?: string[];
  allowRealIpFallback?: boolean;  // default: false
  tools?: GatewayToolsConfig;
  webchat?: GatewayWebchatConfig; // WebChat display/history settings
  channelHealthCheckMinutes?: number;  // default: 5, 0 to disable
  channelStaleEventThresholdMinutes?: number;  // default: 30, must be >= healthCheck interval
  channelMaxRestartsPerHour?: number;  // default: 10, rolling window cap
};
```

### Gateway WebChat Config

```typescript
type GatewayWebchatConfig = {
  /** Max characters per text field in chat.history responses before truncation (default: 12000). */
  chatHistoryMaxChars?: number;   // int, positive, max 500000
};
```

- Configurable via `gateway.webchat.chatHistoryMaxChars`
- Prevents large transcript payloads from overwhelming WebChat clients
- Validation: positive integer, capped at 500000

### Gateway Auth

- Auth modes: `none`, `token`, `password`, `trusted-proxy`
- Token/password support `SecretInput` (plaintext string or provider ref object)
- Trusted-proxy mode: identity-aware reverse proxy (Pomerium, Caddy + OAuth) passes user via `trustedProxy.userHeader`
- Rate limiting: per-IP sliding window with lockout (`gateway.auth.rateLimit`)
- Lockout expired entries now correctly reset attempt counters (prevents infinite escalation)
- Tailscale: Whois-verified header auth for WS Control UI surface

### Gateway Reload

```typescript
type GatewayReloadConfig = {
  mode?: GatewayReloadMode;       // "off" | "restart" | "hot" | "hybrid" (default: hybrid)
  debounceMs?: number;            // default: 300
  deferralTimeoutMs?: number;     // max wait for in-flight ops before SIGUSR1 restart (default: 300000)
};
```

- Watches config file via chokidar, debounced (default 300ms)
- `hybrid` (default): hot-reload channels, restart for structural changes
- Missing config file retried up to 2 times before skip
- `diffConfigPaths` compares old/new config structurally (handles arrays via `isDeepStrictEqual`)
- `deferralTimeoutMs`: caps how long the gateway waits for in-flight operations (e.g. active subagent LLM calls) before forcing a restart; lower values risk aborting active calls

## WhatsApp Config

```typescript
type WhatsAppConfig = WhatsAppConfigCore & WhatsAppSharedConfig & {
  accounts?: Record<string, WhatsAppAccountConfig>;
  defaultAccount?: string;
  actions?: WhatsAppActionConfig;   // reactions, sendMessage, polls (default: true for all)
};

// Key shared fields (available at top-level and per-account):
type WhatsAppSharedConfig = {
  enabled?: boolean;
  dmPolicy?: DmPolicy;             // default: "pairing"
  selfChatMode?: boolean;
  allowFrom?: string[];             // E.164 allowlist
  defaultTo?: string;               // default delivery target (E.164 or group JID)
  groupAllowFrom?: string[];
  groupPolicy?: GroupPolicy;        // default: "allowlist"
  contextVisibility?: ContextVisibilityMode;
  historyLimit?: number;
  dmHistoryLimit?: number;
  dms?: Record<string, DmConfig>;
  textChunkLimit?: number;          // default: 4000
  chunkMode?: "length" | "newline";
  mediaMaxMb?: number;              // default: 50
  blockStreaming?: boolean;
  blockStreamingCoalesce?: BlockStreamingCoalesceConfig;
  groups?: Record<string, WhatsAppGroupConfig>;
  ackReaction?: WhatsAppAckReactionConfig;
  reactionLevel?: "off" | "ack" | "minimal" | "extensive";  // agent reaction guidance
  debounceMs?: number;              // batching window, default: 0
  heartbeat?: ChannelHeartbeatVisibilityConfig;
  healthMonitor?: ChannelHealthMonitorConfig;
};
```

### WhatsApp Reaction Levels

The `reactionLevel` field controls how the agent uses message reactions on WhatsApp:

- `"off"` - No reactions at all (ack and agent reactions disabled)
- `"ack"` - Only automatic ack reactions (e.g. eyes emoji on receipt); no agent-initiated reactions
- `"minimal"` (default) - Agent can react sparingly with brief guidance
- `"extensive"` - Agent can react liberally with richer guidance

Validated via `z.enum(["off", "ack", "minimal", "extensive"])`. Resolved at runtime through `resolveReactionLevel()` in `src/utils/reaction-level.ts`.

## Telegram Config

```typescript
type TelegramAccountConfig = {
  name?: string;
  capabilities?: TelegramCapabilitiesConfig;
  execApprovals?: TelegramExecApprovalConfig;  // enabled: boolean | "auto"
  markdown?: MarkdownConfig;
  commands?: ProviderCommandsConfig;
  customCommands?: TelegramCustomCommand[];  // custom menu commands
  configWrites?: boolean;
  dmPolicy?: DmPolicy;
  enabled?: boolean;
  botToken?: string;
  tokenFile?: string;               // path to token file; symlinks rejected
  replyToMode?: ReplyToMode;        // off|first|all|batched
  groups?: Record<string, TelegramGroupConfig>;
  direct?: Record<string, TelegramDirectConfig>;  // per-chat-id DM config
  allowFrom?: Array<string | number>;
  defaultTo?: string | number;
  groupAllowFrom?: Array<string | number>;
  groupPolicy?: GroupPolicy;
  contextVisibility?: ContextVisibilityMode;  // all|allowlist|allowlist_quote
  historyLimit?: number;
  dmHistoryLimit?: number;
  dms?: Record<string, DmConfig>;
  textChunkLimit?: number;          // default: 4000
  streaming?: ChannelPreviewStreamingConfig;  // unified streaming config
  mediaMaxMb?: number;
  timeoutSeconds?: number;
  retry?: OutboundRetryConfig;
  network?: TelegramNetworkConfig;  // IPv4/IPv6 prioritization + dangerouslyAllowPrivateNetwork
  proxy?: string;
  webhookUrl?: string;
  webhookSecret?: string;
  webhookPath?: string;
  webhookHost?: string;             // default: 127.0.0.1
  webhookPort?: number;             // default: 8787
  webhookCertPath?: string;
  actions?: TelegramActionConfig;
  threadBindings?: TelegramThreadBindingsConfig;
  reactionNotifications?: "off" | "own" | "all";
  reactionLevel?: "off" | "ack" | "minimal" | "extensive";  // default: ack
  heartbeat?: ChannelHeartbeatVisibilityConfig;
  healthMonitor?: ChannelHealthMonitorConfig;
  linkPreview?: boolean;            // default: true
  silentErrorReplies?: boolean;     // default: false
  errorPolicy?: "always" | "once" | "silent";
  errorCooldownMs?: number;
  responsePrefix?: string;
  ackReaction?: string;             // unicode emoji (e.g. "eyes")
  apiRoot?: string;                 // custom Bot API root URL
  trustedLocalFileRoots?: string[]; // for self-hosted Bot API file_path values
  autoTopicLabel?: AutoTopicLabelConfig;
};
```

- Thread bindings: persistent thread-session mapping with idle/max-age expiration and auto-sweep
- Custom commands: validated via `normalizeTelegramCommandName` (pattern: `/^[a-z0-9_]{1,32}$/`)
- Topics now support `agentId` for topic-specific agent routing
- `errorPolicy`/`errorCooldownMs`: per-account, per-group, per-topic, and per-direct error reporting control
- `ingest` field on `TelegramGroupConfig` and `TelegramTopicConfig`: emit internal message hooks for mention-skipped messages
- `dangerouslyAllowPrivateNetwork` on `TelegramNetworkConfig`: opt-in for trusted fake-IP/transparent-proxy environments
- `trustedLocalFileRoots`: filesystem roots for self-hosted Telegram Bot API absolute file_path values
- Exec approvals: `enabled` now accepts `boolean | "auto"` (`NativeExecApprovalEnableMode`)

## Discord Config

```typescript
type DiscordAccountConfig = {
  name?: string;
  capabilities?: string[];
  markdown?: MarkdownConfig;
  commands?: ProviderCommandsConfig;
  configWrites?: boolean;
  enabled?: boolean;
  token?: SecretInput;
  proxy?: string;
  allowBots?: boolean | "mentions";
  dangerouslyAllowNameMatching?: boolean;
  groupPolicy?: GroupPolicy;
  contextVisibility?: ContextVisibilityMode;  // all|allowlist|allowlist_quote
  textChunkLimit?: number;          // default: 2000
  streaming?: ChannelPreviewStreamingConfig;  // unified streaming config
  maxLinesPerMessage?: number;      // default: 17
  mediaMaxMb?: number;
  historyLimit?: number;
  dmHistoryLimit?: number;
  dms?: Record<string, DmConfig>;
  retry?: OutboundRetryConfig;
  actions?: DiscordActionConfig;
  replyToMode?: ReplyToMode;        // off|first|all|batched
  dmPolicy?: DmPolicy;
  allowFrom?: string[];
  defaultTo?: string;
  dm?: DiscordDmConfig;
  guilds?: Record<string, DiscordGuildEntry>;
  heartbeat?: ChannelHeartbeatVisibilityConfig;
  healthMonitor?: ChannelHealthMonitorConfig;
  execApprovals?: DiscordExecApprovalConfig;  // enabled: boolean | "auto"
  agentComponents?: DiscordAgentComponentsConfig;
  ui?: DiscordUiConfig;
  slashCommand?: DiscordSlashCommandConfig;
  threadBindings?: DiscordThreadBindingsConfig;
  intents?: DiscordIntentsConfig;
  voice?: DiscordVoiceConfig;
  pluralkit?: DiscordPluralKitConfig;
  responsePrefix?: string;
  ackReaction?: string;
  ackReactionScope?: "group-mentions" | "group-all" | "direct" | "all" | "off" | "none";
  activity?: string;
  status?: "online" | "dnd" | "idle" | "invisible";
  autoPresence?: DiscordAutoPresenceConfig;
  activityType?: 0 | 1 | 2 | 3 | 4 | 5;
  activityUrl?: string;
  inboundWorker?: { runTimeoutMs?: number };   // default: 30 minutes
  eventQueue?: { listenerTimeout?: number; maxQueueSize?: number; maxConcurrency?: number };
};
```

### Discord Auto Presence

```typescript
type DiscordAutoPresenceConfig = {
  enabled?: boolean;              // default: false
  intervalMs?: number;            // poll interval for runtime state (default: 30000)
  minUpdateIntervalMs?: number;   // min spacing between presence updates (default: 15000)
  healthyText?: string;           // custom status while healthy
  degradedText?: string;          // custom status while degraded
  exhaustedText?: string;         // custom status on quota exhaustion
};
```

### Discord Agent Components

```typescript
type DiscordAgentComponentsConfig = {
  enabled?: boolean;              // default: true - agent-controlled buttons, select menus
};

type DiscordUiConfig = {
  components?: {
    accentColor?: string;         // hex color for Discord component containers
  };
};
```

### Discord Exec Approvals

```typescript
type DiscordExecApprovalConfig = {
  enabled?: boolean | "auto";     // NativeExecApprovalEnableMode; default: auto when approvers can be resolved
  approvers?: string[];           // Discord user IDs; falls back to commands.ownerAllowFrom
  agentFilter?: string[];         // only forward for these agent IDs
  sessionFilter?: string[];       // session key patterns (substring or regex)
  cleanupAfterResolve?: boolean;  // delete approval DMs after resolution (default: false)
  target?: "dm" | "channel" | "both";  // where to send prompts (default: "dm")
};
```

## Slack Config

```typescript
type SlackAccountConfig = {
  name?: string;
  mode?: "socket" | "http";       // connection mode (default: socket)
  signingSecret?: string;         // required for HTTP mode
  webhookPath?: string;           // default: /slack/events
  capabilities?: SlackCapabilitiesConfig;
  execApprovals?: SlackExecApprovalConfig;  // enabled: boolean | "auto"
  markdown?: MarkdownConfig;
  commands?: ProviderCommandsConfig;
  configWrites?: boolean;
  enabled?: boolean;
  botToken?: string;
  appToken?: string;
  userToken?: string;
  userTokenReadOnly?: boolean;    // default: true
  allowBots?: boolean;
  dangerouslyAllowNameMatching?: boolean;
  requireMention?: boolean;       // default: true
  groupPolicy?: GroupPolicy;
  contextVisibility?: ContextVisibilityMode;  // all|allowlist|allowlist_quote
  historyLimit?: number;
  dmHistoryLimit?: number;
  dms?: Record<string, DmConfig>;
  textChunkLimit?: number;
  streaming?: SlackChannelStreamingConfig;  // mode, chunkMode, preview, block, nativeTransport
  mediaMaxMb?: number;
  reactionNotifications?: SlackReactionNotificationMode;
  reactionAllowlist?: Array<string | number>;
  replyToMode?: ReplyToMode;      // off|first|all|batched
  replyToModeByChatType?: Partial<Record<"direct" | "group" | "channel", ReplyToMode>>;
  thread?: SlackThreadConfig;     // thread session behavior
  actions?: SlackActionConfig;
  slashCommand?: SlackSlashCommandConfig;
  dmPolicy?: DmPolicy;
  allowFrom?: Array<string | number>;
  defaultTo?: string;
  dm?: SlackDmConfig;
  channels?: Record<string, SlackChannelConfig>;
  heartbeat?: ChannelHeartbeatVisibilityConfig;
  healthMonitor?: ChannelHealthMonitorConfig;
  responsePrefix?: string;
  ackReaction?: string;           // shortcodes (e.g. "eyes")
  typingReaction?: string;        // reaction emoji while processing (e.g. "hourglass_flowing_sand")
};
```

- `typingReaction`: emoji shortcode added while processing a reply, removed when done. Useful as a typing indicator fallback when assistant mode is not enabled.
- `thread.requireExplicitMention`: when true, suppresses implicit thread mentions - only explicit @bot mentions trigger replies in threads where the bot has previously participated.
- Slack streaming unified into `SlackChannelStreamingConfig` (includes `nativeTransport` toggle for `chat.startStream`/`appendStream`/`stopStream`)

## Session Config

```typescript
type SessionConfig = {
  scope?: "per-sender" | "global";
  dmScope?: "main" | "per-peer" | "per-channel-peer" | "per-account-channel-peer";
  identityLinks?: Record<string, string[]>;
  mainKey?: string;               // always normalized to "main" (custom values ignored with warning)
  threadBindings?: SessionThreadBindingsConfig;  // shared defaults for thread routing
  reset?: SessionResetConfig;
  resetByType?: SessionResetByTypeConfig;
  resetByChannel?: Record<string, SessionResetConfig>;
  sendPolicy?: SessionSendPolicyConfig;
  maintenance?: SessionMaintenanceConfig;  // pruning, capping, file rotation
  parentForkMaxTokens?: number;            // max parent transcript tokens for thread/session forking (0 = disable guard)
  agentToAgent?: {
    maxPingPongTurns?: number;             // cap on requester/target agent turns (0-5, default: 5)
  };
  // ...
};
```

- `normalizeExplicitSessionKey`: provider-aware key normalization (Discord guild+channel normalization)
- `session.mainKey` is forcefully set to `"main"` regardless of config value

## Auth Config

```typescript
type AuthConfig = {
  profiles?: Record<string, AuthProfileConfig>;
  order?: Record<string, string[]>;
  cooldowns?: {
    billingBackoffHours?: number;          // default: 5
    billingBackoffHoursByProvider?: Record<string, number>;
    billingMaxHours?: number;              // default: 24
    authPermanentBackoffMinutes?: number;  // base backoff for permanent-auth failures (default: 10)
    authPermanentMaxMinutes?: number;      // cap for permanent-auth backoff (default: 60)
    failureWindowHours?: number;           // default: 24
    overloadedProfileRotations?: number;   // max same-provider rotations for overloaded errors (default: 1)
    overloadedBackoffMs?: number;          // fixed delay before retry (default: 0)
    rateLimitedProfileRotations?: number;  // max same-provider rotations for rate-limit errors (default: 1)
  };
};

type AuthProfileConfig = {
  provider: string;
  mode: "api_key" | "oauth" | "token";
  email?: string;
  displayName?: string;
};
```

## Agent Defaults - Compaction Config

```typescript
type AgentCompactionConfig = {
  mode?: "default" | "safeguard";
  reserveTokens?: number;
  keepRecentTokens?: number;
  reserveTokensFloor?: number;         // 0 disables the floor
  maxHistoryShare?: number;            // 0.1-0.9, default 0.5
  customInstructions?: string;
  recentTurnsPreserve?: number;
  identifierPolicy?: "strict" | "off" | "custom";
  identifierInstructions?: string;
  qualityGuard?: { enabled?: boolean; maxRetries?: number };
  postIndexSync?: "off" | "async" | "await";
  postCompactionSections?: string[];   // defaults to ["Session Startup", "Red Lines"]
  model?: string;                      // override compaction model
  timeoutSeconds?: number;             // default: 900
  provider?: string;                   // plugin compaction provider id
  truncateAfterCompaction?: boolean;   // truncate session JSONL after compaction (default: false)
  notifyUser?: boolean;                // send compaction notice to user (default: false)
  memoryFlush?: AgentCompactionMemoryFlushConfig;
};
```

- `truncateAfterCompaction`: When enabled, removes summarized entries from the session JSONL file after compaction to prevent unbounded file growth in long-running sessions. Default: false (preserves existing behavior).
- `notifyUser`: When enabled, sends a compaction notice to the user when compaction starts. Default: false (silent).
- `provider`: When set, delegates compaction summarization to a registered plugin provider instead of the built-in `summarizeInStages()`. Falls back to built-in on failure.

## Agent Defaults - New Fields

```typescript
type AgentDefaultsConfig = {
  // ... existing fields ...
  videoGenerationModel?: AgentModelConfig;
  musicGenerationModel?: AgentModelConfig;
  mediaGenerationAutoProviderFallback?: boolean;  // default: true; auto-append cross-provider fallbacks
  skills?: string[];                  // default skill allowlist for agents without explicit agents.list[].skills
  systemPromptOverride?: string;      // full system prompt replacement (debugging/experiments)
  contextInjection?: "always" | "continuation-skip";  // bootstrap file injection policy (default: always)
  subagents?: {
    allowAgents?: string[];           // default allowlist for sessions_spawn target agent ids
    // ... existing subagent fields ...
  };
  heartbeat?: {
    // ... existing heartbeat fields ...
    includeSystemPromptSection?: boolean;  // include ## Heartbeats section for default agent (default: true)
    target?: ChannelId;               // simplified from "last" | "none" | ChannelId
  };
  cliBackends?: Record<string, CliBackendConfig>;  // includes new imagePathScope: "temp" | "workspace"
};
```

## Memory Search Configuration

All settings live under `agents.defaults.memorySearch` in `openclaw.json` unless noted otherwise.

### Provider selection

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `provider` | `string` | auto-detected | `openai`, `gemini`, `voyage`, `mistral`, `ollama`, `local` |
| `model` | `string` | provider default | Embedding model name |
| `fallback` | `string` | `"none"` | Fallback adapter when primary fails |
| `enabled` | `boolean` | `true` | Enable/disable memory search |

Auto-detection order (first available wins): `local` -> `openai` -> `gemini` -> `voyage` -> `mistral`. `ollama` must be set explicitly.

### Remote endpoint - `memorySearch.remote`

| Key | Type | Description |
| --- | --- | --- |
| `baseUrl` | `string` | Custom API base URL |
| `apiKey` | `string` | Override API key |
| `headers` | `object` | Extra HTTP headers |
| `batch.enabled` | `boolean` | Enable batch API for embedding indexing (OpenAI/Gemini; default: true) |
| `batch.wait` | `boolean` | Wait for batch completion (default: true) |
| `batch.concurrency` | `number` | Max concurrent batch jobs (default: 2) |
| `batch.pollIntervalMs` | `number` | Poll interval in ms (default: 5000) |
| `batch.timeoutMinutes` | `number` | Timeout in minutes (default: 60) |

### Hybrid search - `memorySearch.query.hybrid`

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `boolean` | `true` | Enable hybrid BM25 + vector search |
| `vectorWeight` | `number` | `0.7` | Vector score weight (0-1) |
| `textWeight` | `number` | `0.3` | BM25 score weight (0-1) |
| `candidateMultiplier` | `number` | `4` | Candidate pool size multiplier |
| `mmr.enabled` | `boolean` | `false` | Enable MMR diversity re-ranking |
| `mmr.lambda` | `number` | `0.7` | 0 = max diversity, 1 = max relevance |
| `temporalDecay.enabled` | `boolean` | `false` | Enable recency boost |
| `temporalDecay.halfLifeDays` | `number` | `30` | Score halves every N days |

### Local embedding - `memorySearch.local`

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `modelPath` | `string` | auto-downloaded | Path to GGUF model file |
| `modelCacheDir` | `string` | node-llama-cpp default | Cache dir for downloaded models |

Default model: `embeddinggemma-300m-qat-Q8_0.gguf` (~0.6 GB, auto-downloaded).

### Multimodal memory (Gemini) - `memorySearch.multimodal`

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `boolean` | `false` | Enable multimodal indexing |
| `modalities` | `string[]` | - | `["image"]`, `["audio"]`, or `["all"]` |
| `maxFileBytes` | `number` | `10000000` | Max file size for indexing |

Requires `gemini-embedding-2-preview`. Only applies to files in `extraPaths`.

### Extra paths - `memorySearch.extraPaths`

`string[]` of additional directories or files to index. Paths can be absolute or workspace-relative; directories are scanned recursively for `.md` files.

### Embedding cache - `memorySearch.cache`

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `boolean` | `true` | Cache chunk embeddings in SQLite |
| `maxEntries` | `number` | `50000` | Max cached embeddings |

### Session memory (experimental)

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `experimental.sessionMemory` | `boolean` | `false` | Enable session indexing |
| `sources` | `string[]` | `["memory"]` | Add `"sessions"` to include transcripts |

### SQLite vector - `memorySearch.store.vector`

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `boolean` | `true` | Use sqlite-vec for vector queries |
| `extensionPath` | `string` | bundled | Override sqlite-vec path |

Falls back to in-process cosine similarity when sqlite-vec is unavailable.

### QMD backend - `memory.backend = "qmd"`, `memory.qmd.*`

Set `memory.backend` to `"qmd"` to enable. Settings live under `memory.qmd`:

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `command` | `string` | `qmd` | QMD executable path |
| `searchMode` | `string` | `search` | `search`, `vsearch`, or `query` |
| `includeDefaultMemory` | `boolean` | `true` | Auto-index `MEMORY.md` + `memory/**/*.md` |
| `paths[]` | `array` | - | Extra paths: `{ name, path, pattern? }` |
| `sessions.enabled` | `boolean` | `false` | Index session transcripts |

**Update schedule** (`memory.qmd.update`): `interval` (default `"5m"`), `debounceMs` (default `15000`), `onBoot` (default `true`), `waitForBootSync`, `embedInterval`, `commandTimeoutMs`.

**Limits** (`memory.qmd.limits`): `maxResults` (default `6`), `maxSnippetChars`, `maxInjectedChars`, `timeoutMs` (default `4000`).

**Scope** (`memory.qmd.scope`): Same schema as `session.sendPolicy` - controls which sessions receive QMD results. Default is DM-only.

**Citations** (`memory.citations`): `"auto"` (default), `"on"`, `"off"` - controls `Source: <path#line>` footer in snippets.

## Env Variable Handling

### `env-vars.ts` - Config env var application

- `env.vars` and direct `env.*` string values are collected and applied to `process.env`
- Only applied when the key is not already set in `process.env`
- Dangerous host env vars blocked via `isDangerousHostEnvVarName` / `isDangerousHostEnvOverrideVarName`
- Values containing unresolved `${VAR}` references are skipped to prevent literal placeholders from being accepted as valid credentials
- Key normalization: `normalizeEnvVarKey(key, { portable: true })`

### `env-substitution.ts` - `${VAR}` resolution

- Pattern: `[A-Z_][A-Z0-9_]*` (uppercase only)
- Escape: `$${VAR}` outputs literal `${VAR}`
- `onMissing` callback mode: preserves placeholder + emits warning instead of throwing
- `containsEnvVarReference(value)`: check without substituting

### `shell-env-expected-keys.ts` - Dynamic key resolution

Shell env expected keys are now dynamically resolved from registered provider/channel env var lists via `resolveShellEnvExpectedKeys()` instead of a hardcoded list. Core keys always included: `OPENCLAW_GATEWAY_TOKEN`, `OPENCLAW_GATEWAY_PASSWORD`.

## Config Paths

```
~/.openclaw/
  +-  openclaw.json             # main config
  +-  extensions/              # global plugin installs
  +-  skills/                  # managed skills
  +-  credentials/             # web provider creds
  +-  agents/
  |   +-- <agent-id>/
  |       +-  workspace/       # agent workspace
  |       +-- sessions/        # session storage
  +-- agentbox/                # agentbox-specific data (if applicable)
```

Key file: `src/config/config-paths.ts`

## Config Gateway Methods

```typescript
// Available via gateway protocol
"config.get"       // Get current config with redaction
"config.schema"    // Get schema with plugin integration
"config.schema.lookup"  // Find schema for specific config path (#37266)
"config.set"       // Full config replacement (requires base hash)
"config.patch"     // Merge patch application (requires base hash)
"config.apply"     // Apply full config with restart coordination
```

- `config.schema.lookup` returns only the relevant schema subset for a given config path
- Config mutations include audit logging (actor, device ID, client IP, changed paths)
- Restart sentinel support for post-restart notifications

## Programmatic Config Operations

```typescript
import { loadConfig, writeConfigFile } from "openclaw/config";

// Read
const config = loadConfig();

// Modify
config.channels = {
  ...config.channels,
  telegram: { token: "123:ABC" }
};

// Write (with backup rotation + audit log)
await writeConfigFile(config);
```

## Environment Variable Substitution

Config values can reference env vars:
```json5
{
  "gateway": {
    "auth": { "token": "${OPENCLAW_GATEWAY_TOKEN}" }
  }
}
```

Resolved during config loading (step 4 of pipeline).

## `$include` Directive

Compose config from multiple files:
```json5
{
  "$include": "./base-config.json5",
  "gateway": { "port": 8080 }
}
```

Included file is merged, then local keys override.

## Defaults Applied at Runtime

Key file: `src/config/defaults.ts`

- **Model aliases**: `opus` -> `anthropic/claude-opus-4-6`, `sonnet` -> `anthropic/claude-sonnet-4-6`, `gpt` -> `openai/gpt-5.4`, `gpt-mini` -> `openai/gpt-5.4-mini`, `gpt-nano` -> `openai/gpt-5.4-nano`, `gemini` -> `google/gemini-3.1-pro-preview`, `gemini-flash` -> `google/gemini-3-flash-preview`, `gemini-flash-lite` -> `google/gemini-3.1-flash-lite-preview`
- **Agent defaults**: `maxConcurrent` (from `DEFAULT_AGENT_MAX_CONCURRENT`), `subagents.maxConcurrent` (from `DEFAULT_SUBAGENT_MAX_CONCURRENT`)
- **Context pruning**: delegated to `applyProviderConfigDefaultsWithPlugin` for plugin-driven per-provider defaults (Anthropic cache-ttl + heartbeat interval auto-applied when auth is configured)
- **Anthropic cache retention**: `cacheRetention: "short"` auto-applied for Anthropic/Bedrock models when using API key auth
- **Compaction**: defaults to `mode: "safeguard"`
- **Logging**: defaults `redactSensitive: "tools"`
- **Messages**: defaults `ackReactionScope: "group-mentions"`
- **Talk**: normalized via `normalizeTalkConfig`; legacy ElevenLabs fields removed; provider-specific config via `providers` map
- **Model defaults**: provider-specific normalization via `normalizeProviderSpecificConfig`; Mistral safe max tokens per model; cost/input/contextWindow/maxTokens defaults applied per model

## Models Config

```typescript
type ModelsConfig = {
  mode?: "merge" | "replace";
  providers?: Record<string, ModelProviderConfig>;
  bedrockDiscovery?: BedrockDiscoveryConfig;
  copilotDiscovery?: DiscoveryToggleConfig;    // new
  huggingfaceDiscovery?: DiscoveryToggleConfig; // new
  ollamaDiscovery?: DiscoveryToggleConfig;      // new
};

type ModelProviderConfig = {
  baseUrl: string;
  apiKey?: SecretInput;
  auth?: "api-key" | "aws-sdk" | "oauth" | "token";
  api?: ModelApi;
  injectNumCtxForOpenAICompat?: boolean;
  headers?: Record<string, SecretInput>;
  authHeader?: boolean;
  request?: ConfiguredModelProviderRequest;  // new: provider-level HTTP transport overrides
  models: ModelDefinitionConfig[];
};

type ModelDefinitionConfig = {
  id: string;
  name: string;
  api?: ModelApi;
  reasoning: boolean;
  input: Array<"text" | "image">;
  cost: { input: number; output: number; cacheRead: number; cacheWrite: number };
  contextWindow: number;
  contextTokens?: number;          // new: effective runtime cap separate from native contextWindow
  maxTokens: number;
  headers?: Record<string, string>;
  compat?: ModelCompatConfig;      // includes new requiresStringContent field
};
```

- `ModelApi` values: `"openai-completions"`, `"openai-responses"`, `"openai-codex-responses"`, `"anthropic-messages"`, `"google-generative-ai"`, `"github-copilot"`, `"bedrock-converse-stream"`, `"ollama"`, `"azure-openai-responses"`
- `contextTokens`: optional effective runtime cap used for compaction/session budgeting, keeps native `contextWindow` intact
- `ModelProviderConfig.request`: `ConfiguredProviderRequest` with auth (bearer/header), proxy (env/explicit), and TLS overrides

## Validation

Zod schemas in `src/config/zod-schema*.ts`:
- `zod-schema.core.ts` - shared primitives
- `zod-schema.agents.ts` - agent definitions
- `zod-schema.providers.ts` - channel configs
- `zod-schema.providers-core.ts` - core provider type schemas
- `zod-schema.providers-whatsapp.ts` - WhatsApp-specific validation (reactionLevel, dmPolicy/allowFrom cross-checks)
- `zod-schema.session.ts` - session/message rules
- `zod-schema.hooks.ts` - hook definitions
- `zod-schema.installs.ts` - plugin install records
- `zod-schema.sensitive.ts` - sensitive field schemas
- `zod-schema.agent-runtime.ts` - agent runtime schemas
- `zod-schema.agent-defaults.ts` - agent defaults with compaction/heartbeat/subagents
- `zod-schema.ts` - main entry, composes all schemas

Malformed config breaks gateway startup. Schema cache key is hashed to prevent RangeError with many channels (#36603).

## Config CLI

```bash
openclaw config get <key>                  # get a config value
openclaw config set <key> <value>          # set a config value (also supports SecretRef builder)
openclaw config unset <key>                # remove a config key
openclaw config file                       # print config file path
openclaw config validate                   # validate current config
```

`config set` supports three modes: direct value, SecretRef builder (`--ref-provider`/`--ref-source`/`--ref-id`), and batch (`--batch-json`/`--batch-file`).

## Tools Config - Notable Changes

```typescript
type ToolsConfig = {
  // ... standard allow/deny/profile ...
  web?: {
    search?: {
      enabled?: boolean;
      provider?: string;
      apiKey?: SecretInput;
      maxResults?: number;
      timeoutSeconds?: number;
      cacheTtlMinutes?: number;
      openaiCodex?: {              // native Codex web search
        enabled?: boolean;
        mode?: "cached" | "live";
        allowedDomains?: string[];
        contextSize?: "low" | "medium" | "high";
        userLocation?: { country?: string; region?: string; city?: string; timezone?: string };
      };
    } & Record<string, unknown>;   // generic extensible search config
    x_search?: {                   // xAI Grok X search (apiKey removed - uses plugin config or XAI_API_KEY)
      enabled?: boolean;
      model?: string;
      inlineCitations?: boolean;
      maxTurns?: number;
      timeoutSeconds?: number;
      cacheTtlMinutes?: number;
    };
    fetch?: {
      enabled?: boolean;
      provider?: string;           // new: fallback provider id
      maxChars?: number;
      maxCharsCap?: number;        // default: 50000
      maxResponseBytes?: number;   // default: 2000000
      timeoutSeconds?: number;
      cacheTtlMinutes?: number;
      maxRedirects?: number;       // default: 3
      userAgent?: string;
      readability?: boolean;       // default: true
    };
  };
  media?: MediaToolsConfig;        // includes asyncCompletion.directSend
  experimental?: {
    planTool?: boolean;            // structured update_plan tool
  };
};
```

- Legacy Firecrawl-specific fetch config removed; replaced by generic `provider` field
- `x_search.apiKey` removed; auth resolved via plugin config or `XAI_API_KEY` env var
- `tools.experimental.planTool`: enables the structured `update_plan` tool for all providers (OpenAI-family runs auto-enable it)

## Streaming Config (Unified)

Legacy per-channel flat streaming keys (`streaming`, `blockStreaming`, `blockStreamingCoalesce`, `streamMode`, `draftChunk`) replaced with structured types:

```typescript
type ChannelPreviewStreamingConfig = {
  mode?: "off" | "partial" | "block" | "progress";
  chunkMode?: "length" | "newline";
  preview?: { chunk?: BlockStreamingChunkConfig };
  block?: { enabled?: boolean; coalesce?: BlockStreamingCoalesceConfig };
};

// Slack extends with nativeTransport
type SlackChannelStreamingConfig = ChannelPreviewStreamingConfig & {
  nativeTransport?: boolean;      // Slack chat.startStream/appendStream/stopStream
};
```

Used by Telegram, Discord, and Slack account configs via `streaming` field.

## AgentBox Config Pattern

AgentBox serves a base config via API and merges per-instance values at boot:

```typescript
// Backend: OPENCLAW_BASE_CONFIG (constants.ts)
{
  gateway: { mode: "local", port: 18789, bind: "loopback" },
  models: { mode: "replace", providers: { agentbox: {...}, blockrun: {...} } },
  plugins: { entries: { "openclaw-x402": { enabled: true }, telegram: { enabled: true } } },
  agents: { defaults: { model: "...", compaction: {...} } }
}

// Init script merges per-instance:
// - rpcUrl, telegramBotToken, dashboardUrl
// - Written to ~/.openclaw/openclaw.json via jq
```

## Config IO Architecture

The config IO module (`src/config/io.ts`) has been refactored with functionality extracted into focused submodules:

- `io.audit.ts` - Config write/observe audit logging (JSONL records with file metadata, suspicious change detection)
- `io.write-prepare.ts` - Config write preparation (merge patch creation, env ref restoration, validation formatting, path collection)
- `io.observe-recovery.ts` - Suspicious config read detection and backup recovery
- `io.owner-display-secret.ts` - Auto-generation and persistence of `commands.ownerDisplaySecret`
- `io.invalid-config.ts` - Structured invalid config error handling
- `runtime-snapshot.ts` - Runtime config snapshot state management (get/set/clear/refresh/write-notification listeners)
