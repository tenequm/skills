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
- New `src/config/materialize.ts` module with profiles: `load`, `missing`, `snapshot` for config default application
- `hooks.internal.enabled` now defaults to `true` (was `false`) so bundled hooks load on fresh installs
- `exec.host` default changed from `"sandbox"` to `"auto"` (picks best available target at runtime)
- `exec.applyPatch.enabled` default changed from `false` to `true`
- Auth cooldowns: new `overloadedProfileRotations` (max same-provider rotations, default 1), `overloadedBackoffMs` (fixed delay, default 0), and `rateLimitedProfileRotations` (max same-provider rotations for rate-limit errors, default 1)
- MCP server config: new `transport` (`"sse"` | `"streamable-http"`), `headers`, `connectionTimeoutMs` fields
- Web search config rewritten: legacy per-provider shapes (`brave`, `firecrawl`, etc.) replaced with generic `Record<string, unknown>`; new `openaiCodex` and `x_search` scoped blocks
- `web.fetch.maxResponseBytes` added (default 2000000)
- Memory search: `provider`/`fallback` changed from union to generic `string`; new `qmd.extraCollections` for cross-agent search; new `store.fts.tokenizer` (`"unicode61"` | `"trigram"`) for CJK
- Auth profile: new `displayName` field
- `subagents.requireAgentId` blocks sessions_spawn without explicit agentId
- SecretRef: unsupported policies now hard-fail; gateway restart token drift fixed
- `awk` and `sed` excluded from exec safeBins fast path (injection prevention)
- Gateway: new `webchat.chatHistoryMaxChars` controls max chars per text field in `chat.history` responses (default: 12000, max: 500000)
- WhatsApp: new `reactionLevel` field (`"off" | "ack" | "minimal" | "extensive"`) controls agent reaction behavior per account
- Agent defaults compaction: new `truncateAfterCompaction` boolean - truncates session JSONL after compaction to prevent unbounded file growth (default: false)

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

### Config Reload

- Watches config file via chokidar, debounced (default 300ms)
- `hybrid` (default): hot-reload channels, restart for structural changes
- Missing config file retried up to 2 times before skip
- `diffConfigPaths` compares old/new config structurally (handles arrays via `isDeepStrictEqual`)

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

## Telegram Config Additions

```typescript
type TelegramAccountConfig = {
  // ... existing fields ...
  threadBindings?: {              // thread-bound session lifecycle
    enabled?: boolean;
    idleHours?: number;           // default: 24
    maxAgeHours?: number;         // default: 0 (disabled)
    spawnSubagentSessions?: boolean;  // opt-in
    spawnAcpSessions?: boolean;       // opt-in
  };
  customCommands?: TelegramCustomCommand[];  // custom menu commands
  network?: {                     // IPv4/IPv6 prioritization
    autoSelectFamily?: boolean;
    dnsResultOrder?: string;
  };
  dmHistoryLimit?: number;        // separate from group historyLimit
  direct?: Record<string, DirectDmConfig>;  // per-chat-id DM config
};
```

- Thread bindings: persistent thread-session mapping with idle/max-age expiration and auto-sweep
- Custom commands: validated via `normalizeTelegramCommandName` (pattern: `/^[a-z0-9_]{1,32}$/`)
- Topics now support `agentId` for topic-specific agent routing

## Discord Config Additions

```typescript
type DiscordAccountConfig = {
  // ... existing fields ...
  threadBindings?: {              // same structure as Telegram
    enabled?: boolean;
    idleHours?: number;           // default: 24
    maxAgeHours?: number;         // default: 0
    spawnSubagentSessions?: boolean;
    spawnAcpSessions?: boolean;
  };
  inboundWorker?: {               // event processing
    runTimeoutMs?: number;        // default: 30 minutes
  };
  eventQueue?: {                  // queue controls
    listenerTimeout?: number;
    maxQueueSize?: number;
    maxConcurrency?: number;
  };
  slashCommand?: { ephemeral?: boolean };
  autoPresence?: DiscordAutoPresenceConfig;  // runtime/quota-based status
  activity?: string;              // bot activity settings
  activityType?: 0 | 1 | 2 | 3 | 4 | 5;
  activityUrl?: string;
  status?: "online" | "dnd" | "idle" | "invisible";
  intents?: {                     // privileged gateway intents
    presence?: boolean;
    guildMembers?: boolean;
  };
  agentComponents?: DiscordAgentComponentsConfig;  // agent-controlled interactive components
  ui?: DiscordUiConfig;           // UI customization (component accent color)
  execApprovals?: DiscordExecApprovalConfig;  // exec approval forwarding to DMs/channels
  voice?: DiscordVoiceConfig;     // voice channel conversations
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
  enabled?: boolean;              // default: false
  approvers?: string[];           // Discord user IDs; falls back to commands.ownerAllowFrom
  agentFilter?: string[];         // only forward for these agent IDs
  sessionFilter?: string[];       // session key patterns (substring or regex)
  cleanupAfterResolve?: boolean;  // delete approval DMs after resolution (default: false)
  target?: "dm" | "channel" | "both";  // where to send prompts (default: "dm")
};
```

## Slack Config Additions

```typescript
type SlackAccountConfig = {
  // ... existing fields ...
  mode?: "socket" | "http";       // connection mode (default: socket)
  signingSecret?: string;         // required for HTTP mode
  webhookPath?: string;           // default: /slack/events
  nativeStreaming?: boolean;      // Slack chat.startStream/appendStream/stopStream (default: true)
  execApprovals?: SlackExecApprovalConfig;
  slashCommand?: SlackSlashCommandConfig;
  thread?: SlackThreadConfig;     // thread session behavior
  replyToModeByChatType?: Partial<Record<"direct" | "group" | "channel", ReplyToMode>>;
  typingReaction?: string;        // reaction emoji while processing (e.g. "hourglass_flowing_sand")
};
```

- `typingReaction`: emoji shortcode added while processing a reply, removed when done. Useful as a typing indicator fallback when assistant mode is not enabled.

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
  truncateAfterCompaction?: boolean;   // truncate session JSONL after compaction (default: false)
  memoryFlush?: AgentCompactionMemoryFlushConfig;
};
```

- `truncateAfterCompaction`: When enabled, removes summarized entries from the session JSONL file after compaction to prevent unbounded file growth in long-running sessions. Default: false (preserves existing behavior).

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
| `enabled` | `boolean` | `false` | Cache chunk embeddings in SQLite |
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

## Config Paths

```
~/.openclaw/
  ├── openclaw.json             # main config
  ├── extensions/              # global plugin installs
  ├── skills/                  # managed skills
  ├── credentials/             # web provider creds
  ├── agents/
  │   └── <agent-id>/
  │       ├── workspace/       # agent workspace
  │       └── sessions/        # session storage
  └── agentbox/                # agentbox-specific data (if applicable)
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

- **Model aliases**: `opus` -> `anthropic/claude-opus-4-6`, `sonnet` -> `anthropic/claude-sonnet-4-6`, `gpt` -> `openai/gpt-5.4`, `gpt-mini` -> `openai/gpt-5-mini`, `gemini` -> `google/gemini-3.1-pro-preview`, `gemini-flash` -> `google/gemini-3-flash-preview`, `gemini-flash-lite` -> `google/gemini-3.1-flash-lite-preview`
- **Agent defaults**: `maxConcurrent` (from `DEFAULT_AGENT_MAX_CONCURRENT`), `subagents.maxConcurrent` (from `DEFAULT_SUBAGENT_MAX_CONCURRENT`)
- **Context pruning**: auto-enabled with `mode: "cache-ttl"` when Anthropic auth is configured; heartbeat interval set to `1h` (OAuth) or `30m` (API key)
- **Anthropic cache retention**: `cacheRetention: "short"` auto-applied for Anthropic/Bedrock models when using API key auth
- **Compaction**: defaults to `mode: "safeguard"`
- **Logging**: defaults `redactSensitive: "tools"`
- **Messages**: defaults `ackReactionScope: "group-mentions"`
- **Talk**: normalized via `normalizeTalkConfig`; fallback API key resolved from env

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
