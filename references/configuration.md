# OpenClaw Configuration

## Config File

- **Path**: `~/.openclaw/config.json` (or `config.json5`)
- **Override**: `OPENCLAW_CONFIG` env var (supports `file:///absolute/path`)
- **Format**: JSON5 (comments, trailing commas OK)
- **Key files**: `src/config/config.ts`, `src/config/io.ts`, `src/config/paths.ts`

## Config Resolution Pipeline

1. Load raw JSON5 from disk
2. Resolve `$include` directives (file composition)
3. Substitute `${ENV_VAR}` references
4. Apply environment overrides (`OPENCLAW_CONFIG_*` env vars)
5. Validate against Zod schema (including plugin schemas)
6. Apply runtime defaults
7. Return validated `OpenClawConfig`

## Full Config Structure (`OpenClawConfig`)

```typescript
type OpenClawConfig = {
  meta?: {
    version?: string;
    updatedAt?: string;
  };
  auth?: {
    profiles?: Record<string, AuthProfile>;
    active?: string;
  };
  acp?: {
    bindings?: AcpBinding[];
  };
  env?: Record<string, string>;
  secrets?: Record<string, string>;
  plugins?: PluginsConfig;       // see plugin-system.md
  skills?: SkillsConfig;
  models?: {
    mode?: "merge" | "replace";
    providers?: Record<string, ModelProviderConfig>;
    defaults?: { model?: string };
  };
  agents?: {
    defaults?: {
      model?: string;
      timeout?: number;
      compaction?: CompactionConfig;
      contextPruning?: ContextPruningConfig;
    };
    entries?: Record<string, AgentConfig>;
  };
  tools?: {
    allow?: string[];
    deny?: string[];
    loopDetection?: {             // NEW: protection against repetitive tool calls
      enabled?: boolean;
      historySize?: number;
      warningThreshold?: number;
      criticalThreshold?: number;
      globalCircuitBreakerThreshold?: number;
      // detector toggles: genericRepeat, knownPollNoProgress, pingPong
    };
  };
  channels?: {
    telegram?: TelegramChannelConfig;
    discord?: DiscordChannelConfig;
    slack?: SlackChannelConfig;
    signal?: SignalChannelConfig;
    imessage?: IMessageChannelConfig;
    whatsapp?: WhatsAppChannelConfig;
    web?: WebChannelConfig;
  };
  session?: SessionConfig;
  hooks?: HooksConfig;
  gateway?: {
    mode?: "local" | "remote";
    port?: number;
    bind?: "loopback" | "all";
    auth?: { token?: string };
    controlUi?: boolean;
    http?: {
      endpoints?: {
        responses?: {             // NEW: /v1/responses endpoint
          enabled?: boolean;
          files?: { allowlist?: string[]; maxSize?: number };
          images?: { allowlist?: string[]; maxSize?: number };
        };
      };
    };
    remote?: { host?: string; token?: string };
    talk?: {                      // RESTRUCTURED: provider-based talk config
      provider?: string;
      providers?: Record<string, TalkProviderConfig>;
      // legacy fields kept for backwards compat: voiceId, apiKey, modelId, outputFormat
    };
  };
  logging?: LoggingConfig;
  browser?: BrowserConfig;
  memory?: MemoryConfig;
  messages?: MessagesConfig;
  approvals?: ApprovalsConfig;
  cron?: CronConfig;
};
```

Key types: `src/config/types.openclaw.ts`, `src/config/types.plugins.ts`

## Telegram Config Additions

```typescript
type TelegramAccountConfig = {
  // ... existing fields ...
  threadBindings?: {              // NEW: thread-bound session lifecycle
    enabled?: boolean;
    idleHours?: number;           // default: 24
    maxAgeHours?: number;         // default: 0 (disabled)
    spawnSubagentSessions?: boolean;  // opt-in
    spawnAcpSessions?: boolean;       // opt-in
  };
  customCommands?: TelegramCustomCommand[];  // NEW: custom menu commands
  network?: {                     // NEW: IPv4/IPv6 prioritization
    autoSelectFamily?: boolean;
    dnsResultOrder?: string;
  };
  dmHistoryLimit?: number;        // NEW: separate from group historyLimit
  direct?: Record<string, DirectDmConfig>;  // NEW: per-chat-id DM config
};
```

- Thread bindings: persistent thread-session mapping with idle/max-age expiration and auto-sweep
- Custom commands: validated via `normalizeTelegramCommandName` (pattern: `/^[a-z0-9_]{1,32}$/`)
- Topics now support `agentId` for topic-specific agent routing

## Discord Config Additions

```typescript
type DiscordAccountConfig = {
  // ... existing fields ...
  threadBindings?: {              // NEW: same structure as Telegram
    enabled?: boolean;
    idleHours?: number;           // default: 24
    maxAgeHours?: number;         // default: 0
    spawnSubagentSessions?: boolean;
    spawnAcpSessions?: boolean;
  };
  inboundWorker?: {               // NEW: event processing
    runTimeoutMs?: number;        // default: 30 minutes
  };
  eventQueue?: {                  // NEW: queue controls
    listenerTimeout?: number;
    maxQueueSize?: number;
    maxConcurrency?: number;
  };
  slashCommand?: { ephemeral?: boolean };  // NEW
  autoPresence?: boolean;         // NEW: runtime/quota-based status
  activity?: string;              // NEW: bot activity settings
  activityType?: string;
  activityUrl?: string;
  status?: string;
  intents?: {                     // NEW: privileged gateway intents
    presence?: boolean;
    guildMembers?: boolean;
  };
};
```

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
"config.schema.lookup"  // NEW: Find schema for specific config path (#37266)
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

Resolved during config loading (step 3 of pipeline).

## `$include` Directive

Compose config from multiple files:
```json5
{
  "$include": "./base-config.json5",
  "gateway": { "port": 8080 }
}
```

Included file is merged, then local keys override.

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
