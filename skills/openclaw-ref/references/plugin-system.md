# OpenClaw Plugin System

## Discovery Sources

Plugins are discovered from (in order):
1. **Config load paths** - `plugins.load.paths[]` array
2. **Workspace extensions** - per-agent workspace dirs
3. **Bundled plugins** - built into OpenClaw core
4. **Global plugins dir** - `~/.openclaw/plugins/`

Key files: `src/plugins/discovery.ts`, `src/plugins/loader.ts`

## Plugin Manifest (`openclaw.plugin.json`)

```json
{
  "id": "plugin-id",
  "name": "Display Name",
  "description": "What it does",
  "kind": "memory",
  "channels": ["channel-id"],
  "providers": ["provider-id"],
  "autoEnableWhenConfiguredProviders": ["provider-id"],
  "providerAuthEnvVars": { "provider-id": ["PROVIDER_API_KEY"] },
  "skills": ["skill-id"],
  "configSchema": { "type": "object", "properties": { ... } },
  "uiHints": { "token": { "label": "API Token", "sensitive": true } },
  "contracts": {
    "webSearchProviders": ["provider-id"],
    "mediaUnderstandingProviders": ["provider-id"],
    "imageGenerationProviders": ["provider-id"],
    "speechProviders": ["provider-id"],
    "tools": ["tool-id"]
  }
}
```

- `kind`: optional, set `"memory"` for memory backend plugins, or array `["memory", "context-engine"]` for multi-kind plugins (PR #57507)
- `channels`/`providers`: declare capabilities for UI/discovery
- `autoEnableWhenConfiguredProviders`: provider ids that trigger auto-enable when referenced in auth profiles, provider config, or model refs (see "Auto-Enable for API Key Auth" below)
- `providerAuthEnvVars`: cheap env-var lookup for provider auth without booting plugin runtime. Map of provider id to env var names (e.g. minimax manifest maps `"minimax" -> ["MINIMAX_API_KEY"]`)
- `contracts`: static capability ownership snapshot (`PluginManifestContracts`) for manifest-driven discovery and compat wiring without importing plugin runtime. Optional arrays: `speechProviders`, `mediaUnderstandingProviders`, `imageGenerationProviders`, `webSearchProviders`, `tools`
- `providerAuthChoices`: array of auth choice objects for provider onboarding UI. Fields: `provider`, `method`, `choiceId`, `choiceLabel`, `groupId`, `groupLabel`, `optionKey`, `cliFlag`, `cliOption`, `cliDescription`, `onboardingScopes`
- `configSchema`: validated against plugin's `entries.<id>.config`
- `uiHints`: drive config UI (labels, sensitive masking)

> **Deprecated**: top-level `speechProviders`, `mediaUnderstandingProviders`, `imageGenerationProviders` in the manifest are deprecated. Move them under `contracts`. Run `openclaw doctor --fix` to auto-migrate.

## Package.json Convention

```json
{
  "name": "@openclaw/plugin-name",
  "type": "module",
  "openclaw": {
    "extensions": ["./index.ts", "./other-entry.ts"]
  }
}
```

The `openclaw.extensions` array lists entry points. Each must export a default plugin definition.

## Plugin Registration Pattern

```typescript
import type { OpenClawPluginApi, OpenClawPluginDefinition } from "openclaw/plugin-sdk";

const plugin: OpenClawPluginDefinition = {
  id: "my-plugin",
  name: "My Plugin",
  configSchema: myZodSchema,
  register(api: OpenClawPluginApi) {
    api.registerChannel({ plugin: channelImpl });
    api.registerTool(toolDef);                 // singular, supports factory pattern
    api.registerCommand(commandDef);           // custom slash commands (bypass LLM)
    api.on("before_agent_start", handler);     // typed hook with priority
    api.registerHttpRoute(routeDef);           // HTTP endpoint
    api.registerGatewayMethod("method", handler); // gateway protocol method
    api.registerContextEngine("id", factory);  // exclusive slot for context engine
    api.registerSpeechProvider(speechImpl);    // TTS/STT provider
    api.registerMediaUnderstandingProvider(muImpl);  // media understanding
    api.registerImageGenerationProvider(igImpl);     // image generation
    api.registerWebSearchProvider(wsImpl);           // web search
    api.registerInteractiveHandler(handler);         // interactive message handler
    api.onConversationBindingResolved(handler);      // binding lifecycle hook
  }
};
export default plugin;
```

## Plugin API (`OpenClawPluginApi`)

```typescript
type OpenClawPluginApi = {
  id: string;                                  // plugin id
  name: string;                                // plugin display name
  version: string;                             // plugin version
  description: string;                         // plugin description
  source: string;                              // install source
  rootDir: string;                             // plugin root directory
  registrationMode: "full" | "setup-only" | "setup-runtime" | "cli-metadata";  // cli-metadata NEW
  runtime: PluginRuntime;
  pluginConfig: Record<string, unknown>;       // resolved plugin config
  registerChannel(opts: { plugin: ChannelPlugin }): void;
  registerTool(tool: AnyAgentTool | ToolFactory): void;  // singular, supports factory
  registerCommand(command: OpenClawPluginCommandDefinition): void;
  on<K extends PluginHookName>(hookName: K, handler: PluginHookHandlerMap[K], opts?: { priority?: number }): void;
  registerHook(hookName: string, handler: Function, opts?: { priority?: number }): void;  // alias for on()
  registerHttpRoute(route: HttpRouteDefinition): void;    // replaces old registerHttpHandler
  registerGatewayMethod(method: string, handler: GatewayMethodHandler): void;
  registerProvider(provider: ProviderDefinition): void;   // auth-only, no model catalog
  registerService(service: ServiceDefinition): void;
  registerCli(cli: CliDefinition): void;
  registerContextEngine(id: string, factory: ContextEngineFactory): void;  // exclusive slot
  registerSpeechProvider(provider: SpeechProviderDef): void;
  registerMediaUnderstandingProvider(provider: MediaUnderstandingProviderDef): void;
  registerImageGenerationProvider(provider: ImageGenerationProviderDef): void;
  registerWebSearchProvider(provider: WebSearchProviderDef): void;
  registerInteractiveHandler(handler: InteractiveHandlerDef): void;
  onConversationBindingResolved(handler: BindingResolvedHandler): void;
  resolvePath(...segments: string[]): string;
};
```

## Plugin Commands

```typescript
type OpenClawPluginCommandDefinition = {
  name: string;
  description: string;
  acceptsArgs?: boolean;
  requireAuth?: boolean;
  handler: PluginCommandHandler;
};

type PluginCommandContext = {
  senderId: string;
  channel: string;
  isAuthorizedSender: boolean;
  commandBody: string;
  // ...
};

type PluginCommandResult = ReplyPayload;
```

Plugin commands are processed before built-in commands and before agent invocation - they bypass LLM reasoning entirely.

## Plugin Hooks

26 typed hooks via `PluginHookHandlerMap`. Key prompt mutation hooks can return:
- `systemPrompt` - replace system prompt
- `prependContext` - dynamic content prepended to context
- `prependSystemContext` - static, cacheable content prepended to system prompt
- `appendSystemContext` - static, cacheable content appended to system prompt

Notable hooks:
- `subagent_delivery_target` - controls subagent message delivery routing
- `before_dispatch` - intercept inbound messages before agent dispatch (NEW). Returns `{ handled: boolean; text?: string }` to skip default dispatch and optionally reply directly.

New hook context fields:
- `PluginHookAgentContext.runId` - unique identifier for the agent run (NEW)
- `PluginHookBeforeToolCallResult.requireApproval` - plugin-driven approval gates on tool calls (NEW), with severity levels, timeout behavior, and `onResolution` callback
- `PluginCommandContext.threadParentId` - parent conversation id for thread-capable channels (NEW)

Approval resolution types: `allow-once`, `allow-always`, `deny`, `timeout`, `cancelled` (via `PluginApprovalResolutions` const).

Sync-only hooks: `before_message_write` and `tool_result_persist` reject async handlers at registration time.

Hook policy: `plugins.entries[pluginId].hooks.allowPromptInjection` (boolean) controls prompt mutation access. When `false`, `before_prompt_build` is blocked entirely and `before_agent_start` is constrained to non-prompt fields.

## Plugin Runtime

```typescript
type PluginRuntime = PluginRuntimeCore & {
  subagent: PluginRuntimeSubagent;             // gateway subagent (late-bound via Symbol)
  channel: PluginRuntimeChannels;
};

type PluginRuntimeCore = {
  version: string;
  config: OpenClawConfig;
  workspaceDir: string;
  channels: PluginRuntimeChannels;
  tools: PluginRuntimeTools;
  events: PluginRuntimeEvents;
  system: PluginRuntimeSystem;
  modelAuth: {                                 // #41090: safe model auth access
    getApiKeyForModel(modelId: string): Promise<string | undefined>;
    resolveApiKeyForProvider(providerId: string): Promise<string | undefined>;
  };
  mediaUnderstanding: PluginRuntimeMediaUnderstanding;
  imageGeneration: PluginRuntimeImageGeneration;
  webSearch: PluginRuntimeWebSearch;
  stt: PluginRuntimeStt;
  // media, whatsapp, config access...
};
```

Runtime is lazy-loaded via Proxy to avoid heavy dependencies in test/validation scenarios.

`modelAuth` safety wrappers strip `agentDir`/`store`/`profileId`/`preferredProfile` to prevent credential steering by plugins.

Gateway subagent runtime uses `Symbol.for("openclaw.plugin.gatewaySubagentRuntime")` for late binding.

### Local Runtime Module Loading

Key file: `src/plugins/runtime/local-runtime-module.ts`

`loadSiblingRuntimeModuleSync<T>()` loads a sibling module relative to a caller's `import.meta.url` using jiti. Resolution logic:

1. Compute `baseDir` from `fileURLToPath(moduleUrl)`
2. Search candidate directories: `[baseDir, baseDir/plugins/runtime]`
3. Try extensions in order: `.js`, `.ts`, `.mjs`, `.mts`, `.cjs`, `.cts`
4. First existing file wins; throws if none found

Jiti instances are cached by a composite key of `{ tryNative, aliasMap, moduleUrl }` to avoid re-creating loaders for the same configuration. Uses `buildPluginLoaderAliasMap()` and `buildPluginLoaderJitiOptions()` from `src/plugins/sdk-alias.ts`.

```typescript
function loadSiblingRuntimeModuleSync<T>(params: {
  moduleUrl: string;      // caller's import.meta.url
  relativeBase: string;   // e.g. "./my-module" (extension auto-resolved)
}): T;
```

### Bundled Plugin Runtime Dependencies

Key file: `src/plugins/bundled-dir.ts`

`resolveBundledPluginsDir()` locates the bundled extensions directory with this resolution priority:

1. `OPENCLAW_BUNDLED_PLUGINS_DIR` env override (falls back to argv-based package root for stale overrides in packaged installs)
2. Source checkout: `<packageRoot>/extensions/` (preferred when `.git` + `src/` + `extensions/` exist, or in VITEST)
3. Runtime staging: `<packageRoot>/dist-runtime/extensions/` - only used when the paired `dist/extensions/` also exists (prevents wrapper drift after partial builds, fix from #58782)
4. Built distribution: `<packageRoot>/dist/extensions/`
5. Bun `--compile` sibling: `<execDir>/dist/extensions/` or `<execDir>/extensions/`
6. Walk-up from module: traverse up to 6 parent dirs looking for `extensions/`

Package roots are resolved from three sources (deduplicated): `argv[1]`, `process.cwd()`, `import.meta.url`.

## Plugin Config Type

```typescript
type PluginsConfig = {
  enabled?: boolean;                             // master switch
  allow?: string[];                             // allowlist of trusted plugin IDs
  deny?: string[];                              // denylist (allow takes precedence)
  load?: { paths?: string[] };                  // additional search paths
  slots?: {
    memory?: string | null;                     // exclusive memory slot (null/"none" disables)
    contextEngine?: string;                     // exclusive context engine slot
  };
  entries?: Record<string, PluginEntryConfig>;  // per-plugin config
  installs?: Record<string, PluginInstallRecord>; // install tracking
};

type PluginEntryConfig = {
  enabled?: boolean;
  hooks?: { allowPromptInjection?: boolean };   // prompt mutation policy
  subagent?: {                                  // subagent policy
    allowModelOverride?: boolean;
    allowedModels?: string[];
  };
  config?: Record<string, unknown>;
};

type PluginInstallRecord = InstallRecordBase & {
  source: "npm" | "path" | "archive" | "marketplace" | "clawhub";
  spec?: string;
  sourcePath?: string;
  installPath?: string;
  version?: string;
  installedAt?: string;
  resolvedName?: string;
  resolvedVersion?: string;
  resolvedSpec?: string;
  integrity?: string;
  shasum?: string;
  resolvedAt?: string;
  marketplaceName?: string;                     // marketplace install metadata
  marketplaceSource?: string;
  marketplacePlugin?: string;
  clawhubUrl?: string;                          // clawhub install metadata
  clawhubPackage?: string;
  clawhubFamily?: string;
  clawhubChannel?: string;
};
```

## Plugin Loading Flow

1. `loadOpenClawPlugins()` entry point (from gateway/CLI)
2. Discovery: scan all sources for manifests
3. Config validation: each plugin's config checked against its schema
4. Module import via jiti (handles TS/JS, ESM/CJS)
5. Plugin SDK aliases resolved (100+ `openclaw/*` import paths)
6. Provenance tracking: validates plugins are from known/trusted install paths
7. Registry created with status tracking (loaded/disabled/error)
8. Global hook runner initialized

Options: `mode: "validate"` validates without executing plugins.
Untracked plugins (no provenance) generate diagnostics warnings.

Key file: `src/plugins/loader.ts`

### Bundled Channel Plugin Enable Resolution

Key file: `src/plugins/config-state.ts`

`resolveEffectiveEnableState()` wraps the base `resolveEnableState()` with an additional override for bundled channel plugins. When a bundled plugin is disabled by default (reason `"bundled (disabled by default)"` or `"not in allowlist"`), it calls `isBundledChannelEnabledByChannelConfig()` which checks if `channels.<channelId>.enabled === true` exists in the root config (#58873).

```typescript
function resolveEffectiveEnableState(params: {
  id: string;
  origin: PluginRecord["origin"];
  config: NormalizedPluginsConfig;
  rootConfig?: OpenClawConfig;
  enabledByDefault?: boolean;
}): { enabled: boolean; reason?: string };
```

The channel id is resolved via `normalizeChatChannelId(pluginId)`. If the root config has `channels.<id>.enabled === true`, the plugin is force-enabled regardless of allowlist or default-disabled state. This allows `applyPluginAutoEnable()` to set `channels.<id>.enabled: true` and have it take effect during loading.

### Auto-Enable for API Key Auth

Key file: `src/config/plugin-auto-enable.ts`

`applyPluginAutoEnable()` supports `mode: "api_key"` auth profiles (not just OAuth) for triggering auto-enable via `autoEnableWhenConfiguredProviders` (#57127). The `isProviderConfigured()` function checks three sources:

1. `auth.profiles` - matches `profile.provider` against the target provider id (works for both OAuth and API key mode profiles)
2. `models.providers` - matches keys in the provider config map
3. Model refs - extracts provider prefix from `agents.defaults.model`, `agents.list[].model`, and model fallbacks

`resolveAutoEnableProviderPluginIds()` merges the built-in `BUNDLED_AUTO_ENABLE_PROVIDER_PLUGIN_IDS` map with manifest-declared `autoEnableWhenConfiguredProviders` from the `PluginManifestRegistry`. Plugins that are explicitly disabled or denied are skipped. The `preferOver` mechanism prevents enabling superseded plugins when a preferred alternative is also configured.

### Uninstall Resolution

`resolvePluginUninstallId()` (`src/cli/plugins-cli.ts`) uses a multi-step fallback chain:
1. Match by plugin `id`/`name` in registry
2. Match by `spec`/`resolvedSpec`/`resolvedName`/`marketplacePlugin` in install records
3. Parse as ClawHub spec (`clawhub:<name>`) and match `clawhubPackage` (versionless)
4. Fall back to raw id

### Doctor: Stale Plugin Config Pruning

Key file: `src/commands/doctor/shared/stale-plugin-config.ts` (PR #53187)

`scanStalePluginConfig()` finds orphaned `plugins.allow` and `plugins.entries` refs pointing to plugins no longer installed. `maybeRepairStalePluginConfig()` auto-removes them via `openclaw doctor --fix`. Auto-repair is blocked when manifest discovery has errors (`isStalePluginAutoRepairBlocked()`).

`normalizePluginId()` (`src/plugins/config-state.ts`) is now exported for use by the doctor scanner.

## Process-Global Singleton Pattern

Six Symbol-based singletons ensure shared state across duplicated dist chunks:

| Symbol | Purpose |
|--------|---------|
| `openclaw.plugins.hook-runner-global-state` | Global hook runner (#40184) |
| `openclaw.contextEngineRegistryState` | Context engine registry |
| `openclaw.pluginRegistryState` | Plugin registry state (#50418) |
| `openclaw.pluginCommandsState` | Command registry across module graphs (#50431) |
| `openclaw.plugins.binding.global-state` | Conversation binding state |
| `openclaw.plugin.gatewaySubagentRuntime` | Gateway subagent late binding |

## Plugin Update

```typescript
type PluginUpdateStatus = "updated" | "unchanged" | "skipped" | "error";
type PluginUpdateOutcome = {
  pluginId: string;
  status: PluginUpdateStatus;
  message: string;
  currentVersion?: string;
  nextVersion?: string;
};
```

- `updateNpmInstalledPlugins()` - update npm-installed plugins with dry-run support
- `syncPluginsForUpdateChannel()` - sync plugins between bundled/npm based on update channel
- Unpinned version bumps no longer trigger false integrity-mismatch warnings (#37179)

## Plugin Installation

### CLI Commands

```bash
openclaw plugins install <npm-spec>       # from npm
openclaw plugins install <path>           # from local dir
openclaw plugins install --link <path>    # symlink local dir
openclaw plugins disable <id>
openclaw plugins enable <id>
openclaw plugins list [--json] [--verbose]
openclaw plugins info <id> [--json]
openclaw plugins uninstall <id> [--keep-files] [--force]
openclaw plugins update [--all] [--dry-run]
openclaw plugins doctor                   # diagnostics
```

### Install Flow (npm)

1. Validate npm spec
2. Download + extract tarball
3. Inspect `package.json` + `openclaw.plugin.json`
4. Validate `openclaw.extensions` array
5. Security scan for dangerous patterns
6. Install to `~/.openclaw/plugins/<plugin-id>/`
7. Run `npm install --omit=dev` in plugin dir
8. Update config: install record + allowlist + enable
9. Gateway restart required

## Plugin SDK (`src/plugin-sdk/`)

100+ scoped exports. Plugins import from `openclaw/plugin-sdk` or `openclaw/<subpath>`. Runtime resolves via jiti alias.

Key exports: types, config access, channel interfaces, tool builders, hook types, media pipeline, crypto/signing utilities, `requireApiKey`/`ResolvedProviderAuth` for model auth, `ContextEngineFactory` for context engine registration.

New SDK modules:
- `src/plugin-sdk/diffs.ts` - narrow facade for diff/artifact context routing
- `src/plugin-sdk/channel-actions.ts` - `createMessageToolButtonsSchema()` and `createMessageToolCardSchema()` moved from core to SDK
- `src/plugin-sdk/approval-delivery-helpers.ts` - `createApproverRestrictedNativeApprovalAdapter()` factory for channel-specific approval delivery. Produces an adapter with `auth` (authorize actor, availability state), `delivery` (DM route detection, forwarding suppression), and optional `native` (origin/approver-DM target resolution, delivery capabilities) sections. Used by discord, slack, and telegram extensions.

Channel-specific SDK subpaths:
- `openclaw/discord` - thread binding management (`autoBindSpawnedDiscordSubagent`, `listThreadBindingsBySessionKey`, `unbindThreadBindingsBySessionKey`)
- `openclaw/slack` - account resolution, inspection, onboarding adapters
- `openclaw/telegram` - account resolution, inspection, onboarding adapters

## Extension Shared Helpers

`extensions/shared/` directory with extracted modules from `src/plugin-sdk/extension-shared.ts` (boundary debt removal). Provides common utilities for channel extensions without coupling to core plugin-sdk internals.

## Extension Directory Structure

```
extensions/my-plugin/
  ├── package.json            # name, openclaw.extensions
  ├── openclaw.plugin.json    # manifest
  ├── index.ts                # default export: plugin definition
  ├── src/                    # implementation
  └── node_modules/           # runtime deps (npm install --omit=dev)
```

Keep plugin deps in the extension `package.json`, not root. Use `devDependencies` or `peerDependencies` for `openclaw` (resolved at runtime via jiti alias).

Removed `api.registerHttpHandler()` - plugins using it get a clear migration error pointing to `api.registerHttpRoute()` (#36794).

## Bundled Web Search Provider: SearXNG (#57317)

Key files: `extensions/searxng/`

Self-hosted meta-search provider with no API key required. Registered as a bundled web search provider plugin.

### Manifest

```json
{
  "id": "searxng",
  "contracts": { "webSearchProviders": ["searxng"] },
  "configSchema": {
    "type": "object",
    "properties": {
      "webSearch": {
        "type": "object",
        "properties": {
          "baseUrl": { "type": ["string", "object"] },
          "categories": { "type": "string" },
          "language": { "type": "string" }
        }
      }
    }
  }
}
```

### Registration

Uses `definePluginEntry()` + `api.registerWebSearchProvider()` with the `WebSearchProviderPlugin` interface:

```typescript
const provider: WebSearchProviderPlugin = {
  id: "searxng",
  label: "SearXNG Search",
  hint: "Self-hosted meta-search with no API key required",
  requiresCredential: true,            // base URL acts as credential
  credentialLabel: "SearXNG Base URL",
  envVars: ["SEARXNG_BASE_URL"],
  autoDetectOrder: 200,
  credentialPath: "plugins.entries.searxng.config.webSearch.baseUrl",
  // ...credential get/set helpers, tool factory
};
```

### Runtime Client (`src/searxng-client.ts`)

`runSearxngSearch()` performs the search:
1. Resolve config: `baseUrl` from plugin config, inline env secret ref, or `SEARXNG_BASE_URL` env var
2. SSRF validation: `validateSearxngBaseUrl()` uses `assertHttpUrlTargetsPrivateNetwork()` - HTTP URLs must target private/loopback network; HTTPS allowed for public hosts
3. Cache check via `normalizeCacheKey()` / `readCache()` with `DEFAULT_CACHE_TTL_MINUTES`
4. Build URL: `<baseUrl>/search?q=...&format=json&categories=...&language=...`
5. Fetch via `withTrustedWebSearchEndpoint()` with configurable timeout (default 20s) and 1MB response limit
6. Parse results: normalize each `SearxngResult` (`url`, `title`, `content`), cap at `count`
7. Wrap results with `wrapWebContent()` (untrusted external content markers) and `writeCache()`

### Config Resolution Chain (`src/config.ts`)

Base URL resolution order:
1. `plugins.entries.searxng.config.webSearch.baseUrl` (string or secret-input object)
2. Inline env secret ref (`{ source: "env", id: "VAR_NAME" }`)
3. `SEARXNG_BASE_URL` environment variable

Categories and language from `plugins.entries.searxng.config.webSearch.categories`/`language`.

## New Provider Plugin Types

Provider plugins gained several new hook contexts for decoupling provider-specific logic from core:

```typescript
// Provider-owned model-id normalization (plugin-side alias cleanup)
type ProviderNormalizeModelIdContext = { provider: string; modelId: string };

// Provider-owned config normalization for models.providers.<id> entries
type ProviderNormalizeConfigContext = { provider: string; providerConfig: ModelProviderConfig };

// Provider-owned transport normalization (API/baseUrl-based, not provider-id-based)
type ProviderNormalizeTransportContext = { provider: string; api?: string | null; baseUrl?: string };

// Provider-owned env/config auth marker resolution
type ProviderResolveConfigApiKeyContext = { provider: string; env: NodeJS.ProcessEnv };

// Provider-owned transport creation (custom StreamFn replacing pi-ai default)
type ProviderCreateStreamFnContext = { config?; agentDir?; workspaceDir?; provider; modelId; model };

// Provider-owned embedding transport creation (memory embeddings via provider plugin)
type ProviderCreateEmbeddingProviderContext = {
  config; agentDir?; workspaceDir?; provider; model;
  remote?: { baseUrl?; apiKey?; headers? };
  providerApiKey?; outputDimensionality?; taskType?;
};
```

`ProviderWrapStreamFnContext` now includes optional `model?: ProviderRuntimeModel`.

`ProviderAuthContext` now includes optional `env?: NodeJS.ProcessEnv`.

## Plugin Tool Context Additions

`OpenClawPluginToolContext` gained new fields:
- `runtimeConfig?: OpenClawConfig` - active runtime-resolved config snapshot
- `browser?: { sandboxBridgeUrl?; allowHostControl? }` - browser sandbox bridge info
- `deliveryContext?: DeliveryContext` - trusted ambient delivery route for active session

## Speech Provider Plugin Additions

`SpeechProviderPlugin` gained new hooks:
- `autoSelectOrder?: number` - priority for auto-selection
- `resolveConfig?` - provider-owned config resolution
- `parseDirectiveToken?` - provider-owned directive token parsing
- `resolveTalkConfig?` / `resolveTalkOverrides?` - talk config resolution

## Web Search Provider Additions

`WebSearchProviderPlugin` gained `runSetup?` hook for interactive provider setup.

## Memory Plugin State (`src/plugins/memory-state.ts` - NEW)

Centralized module for memory plugin exclusive slots:

```typescript
type MemoryPromptSectionBuilder = (params: { availableTools: Set<string>; citationsMode? }) => string[];
type MemoryFlushPlanResolver = (params: { cfg?; nowMs? }) => MemoryFlushPlan | null;
type MemoryPluginRuntime = {
  getMemorySearchManager(params: { cfg; agentId; purpose? }): Promise<{ manager; error? }>;
  resolveMemoryBackendConfig(params: { cfg; agentId }): MemoryRuntimeBackendConfig;
  closeAllMemorySearchManagers?(): Promise<void>;
};
```

Three exclusive slots: prompt section builder, flush plan resolver, and runtime adapter.

## Memory Embedding Providers (`src/plugins/memory-embedding-providers.ts` - NEW)

Multiple adapters can coexist (unlike other exclusive slots):

```typescript
type MemoryEmbeddingProviderAdapter = {
  id: string;
  model: string;
  maxInputTokens?: number;
  embedQuery: (text: string) => Promise<number[]>;
  embedBatch: (texts: string[]) => Promise<number[][]>;
};
```

## Plugin Kind Slots (`src/plugins/slots.ts` - NEW)

Multi-kind plugin support. `kind` field can now be a single `PluginKind` or an array:

```typescript
type PluginKind = "memory" | "context-engine";
function hasKind(kind: PluginKind | PluginKind[] | undefined, target: PluginKind): boolean;
function normalizeKinds(kind?: PluginKind | PluginKind[]): PluginKind[];
```

## CLI Backend Plugin Type (NEW)

```typescript
type CliBackendPlugin = {
  id: string;                          // provider id (e.g. "claude-cli/opus")
  config: CliBackendConfig;            // default backend config
  bundleMcp?: boolean;                 // inject bundle MCP config file
  normalizeConfig?: (config: CliBackendConfig) => CliBackendConfig;
};
```

## CLI Command Descriptors (NEW)

```typescript
type OpenClawPluginCliCommandDescriptor = {
  name: string;
  description: string;
  hasSubcommands: boolean;
};
```

Used for lazy root CLI registration - when descriptors cover every top-level command, the plugin registrar stays lazy-loaded.

## Plugin Install Security

- `before_install` hook removed (commit `fcb802e`)
- Dangerous skill installs now fail closed by default (commit `0d7f1e2`)
- New override: `--dangerously-force-unsafe-install` bypasses built-in blocking
- `dangerouslyForceUnsafeInstall` is now threaded through all install paths including archive extraction (#58879), via `InstallSafetyOverrides` type in `PackageInstallCommonParams` and `FileInstallCommonParams` (`src/plugins/install.ts`). `FileInstallCommonParams` picks `dangerouslyForceUnsafeInstall` from `PackageInstallCommonParams`. All scan functions (`scanBundleInstallSource`, `scanPackageInstallSource`, `scanFileInstallSource`) accept `InstallSafetyOverrides`. Also threaded through marketplace (`src/plugins/marketplace.ts`), ClawHub (`src/plugins/clawhub.ts`), and CLI install command (`src/cli/plugins-install-command.ts`).
- Marketplace and Ollama network requests are guarded (commit `8deb952`)
- Plugin install blocked when source scan fails (commit `7a953a5`)

## Plugin Shapes

OpenClaw classifies every loaded plugin into a shape:

| Shape | Meaning |
|-------|---------|
| `plain-capability` | One capability type (e.g. provider-only like `mistral`) |
| `hybrid-capability` | Multiple capability types (e.g. `openai` owns text, speech, media, images) |
| `hook-only` | Only hooks, no capabilities/tools/commands/services |
| `non-capability` | Tools/commands/services but no capabilities |

Use `openclaw plugins inspect <id>` to see shape.

## Bundle Compatibility

OpenClaw can install plugins from three external ecosystems: Codex, Claude, Cursor. These are content packs mapped into native features.

- Bundle formats: `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`
- Auto-detected during install from local paths and archives
- Mapped features: skill roots, command roots (Claude/Cursor), hook packs (Codex), MCP tools, Claude `settings.json` defaults
- Show up as `Format: bundle` with subtype in `plugins list` / `plugins inspect`
- Bundles are NOT in-process native plugins - narrower trust boundary

## ClawHub Install Flow

- `openclaw plugins install <spec>` checks ClawHub first, falls back to npm
- Explicit: `openclaw plugins install clawhub:<package>`
- ClawHub downloads archive, checks plugin API / min gateway compat
- Marketplace support: `<plugin>@<marketplace>` shorthand, `--marketplace` flag
- Marketplace sources: known-marketplace name, local path, GitHub repo shorthand, git URL

## Community Plugins

Community plugins are available on ClawHub and npm. Notable ones: Codex App Server Bridge, DingTalk, Lossless Claw (LCM), Opik, QQbot, WeCom.

## ExecApprovalManager Generics

`ExecApprovalManager` is now generic: `ExecApprovalManager<TPayload = ExecApprovalRequestPayload>`. All methods (`create`, `register`, `getSnapshot`) use the generic `TPayload` type.
