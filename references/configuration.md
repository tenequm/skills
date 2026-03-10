# OpenClaw Configuration

## Config File

- **Path**: `~/.openclaw/config.json` (or `config.json5`)
- **Override**: `OPENCLAW_CONFIG` env var (supports `file:///absolute/path`)
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
    lastTouchedAt?: string;       // ISO timestamp
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
  browser?: BrowserConfig;
};
```

Key types: `src/config/types.openclaw.ts`, `src/config/types.plugins.ts`

### Notable structural changes since last refresh

- `talk` config is a **top-level** key (not nested under `gateway`)
- `env` is now a structured object with `shellEnv`, `vars`, and sugar for direct string keys; blocked dangerous host env vars are filtered out
- `meta` fields renamed: `lastTouchedVersion` / `lastTouchedAt`
- Added top-level keys: `wizard`, `update`, `ui`, `nodeHost`, `bindings`, `broadcast`, `audio`, `media`, `commands`, `discovery`, `canvasHost`, `web`

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
  remote?: GatewayRemoteConfig;
  reload?: GatewayReloadConfig;   // mode: "off" | "restart" | "hot" | "hybrid"
  tls?: GatewayTlsConfig;
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
  channelHealthCheckMinutes?: number;  // default: 5, 0 to disable
};
```

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
  autoPresence?: boolean;         // runtime/quota-based status
  activity?: string;              // bot activity settings
  activityType?: string;
  activityUrl?: string;
  status?: string;
  intents?: {                     // privileged gateway intents
    presence?: boolean;
    guildMembers?: boolean;
  };
};
```

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
  ├── config.json[5]           # main config
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
  // ...
};
```

- `normalizeExplicitSessionKey`: provider-aware key normalization (Discord guild+channel normalization)
- `session.mainKey` is forcefully set to `"main"` regardless of config value

## Defaults Applied at Runtime

Key file: `src/config/defaults.ts`

- **Model aliases**: `opus` -> `anthropic/claude-opus-4-6`, `sonnet` -> `anthropic/claude-sonnet-4-6`, `gpt` -> `openai/gpt-5.4`, `gemini` -> `google/gemini-3.1-pro-preview`, etc.
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
- `zod-schema.session.ts` - session/message rules
- `zod-schema.plugins.ts` - plugin config
- `zod-schema.hooks.ts` - hook definitions
- `zod-schema.ts` - main entry, composes all schemas

Malformed config breaks gateway startup. Schema cache key is hashed to prevent RangeError with many channels (#36603).

## Config CLI

```bash
openclaw config show                    # print current config
openclaw config set <key> <value>       # set a config value
openclaw config get <key>               # get a config value
openclaw config edit                    # open in editor
openclaw config path                    # print config file path
openclaw config reset                   # reset to defaults
```

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
