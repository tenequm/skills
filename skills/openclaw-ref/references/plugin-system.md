# OpenClaw Plugin System

## Discovery Sources

Plugins are discovered from (in order):
1. **Config load paths** - `plugins.load.paths[]` array
2. **Workspace extensions** - per-agent workspace dirs
3. **Bundled plugins** - built into OpenClaw core
4. **Global extensions dir** - `~/.openclaw/extensions/`

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
  "skills": ["skill-id"],
  "configSchema": { "type": "object", "properties": { ... } },
  "uiHints": { "token": { "label": "API Token", "sensitive": true } }
}
```

- `kind`: optional, set `"memory"` for memory backend plugins, or array `["memory", "context-engine"]` for multi-kind plugins (PR #57507)
- `channels`/`providers`: declare capabilities for UI/discovery
- `configSchema`: validated against plugin's `entries.<id>.config`
- `uiHints`: drive config UI (labels, sensitive masking)

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
6. Install to `~/.openclaw/extensions/<plugin-id>/`
7. Run `npm install --omit=dev` in plugin dir
8. Update config: install record + allowlist + enable
9. Gateway restart required

## Plugin SDK (`src/plugin-sdk/`)

100+ scoped exports. Plugins import from `openclaw/plugin-sdk` or `openclaw/<subpath>`. Runtime resolves via jiti alias.

Key exports: types, config access, channel interfaces, tool builders, hook types, media pipeline, crypto/signing utilities, `requireApiKey`/`ResolvedProviderAuth` for model auth, `ContextEngineFactory` for context engine registration.

New SDK modules:
- `src/plugin-sdk/diffs.ts` - narrow facade for diff/artifact context routing
- `src/plugin-sdk/message-tool-schema.ts` - `createMessageToolButtonsSchema()` and `createMessageToolCardSchema()` moved from core to SDK

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
