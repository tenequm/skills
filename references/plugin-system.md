# OpenClaw Plugin System

## Discovery Sources

Plugins are discovered from (in order):
1. **Bundled plugins** - built into OpenClaw core
2. **Config load paths** - `plugins.load.paths[]` array
3. **Global extensions dir** - `~/.openclaw/extensions/`
4. **Workspace extensions** - per-agent workspace dirs

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

- `kind`: optional, set `"memory"` for memory backend plugins (exclusive slot, fast-path disabled logic)
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
    api.registerTools([tool1, tool2]);
    api.registerCommand(commandDef);           // custom slash commands (bypass LLM)
    api.on("before_agent_start", handler);     // typed hook with priority
    api.registerCronJobs([cronSpec]);
    api.registerGatewayHandler("my-route", handler);
  }
};
export default plugin;
```

## Plugin API (`OpenClawPluginApi`)

```typescript
type OpenClawPluginApi = {
  runtime: PluginRuntime;
  registerChannel(opts: { plugin: ChannelPlugin }): void;
  registerTools(tools: AnyAgentTool[]): void;
  registerCommand(command: OpenClawPluginCommandDefinition): void;
  on<K extends PluginHookName>(hookName: K, handler: PluginHookHandlerMap[K], opts?: { priority?: number }): void;
  registerCronJobs(jobs: CronJobSpec[]): void;
  registerGatewayHandler(id: string, handler: GatewayRequestHandler): void;
  // provider auth, services, CLI commands...
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

24 typed hooks via `PluginHookHandlerMap`. Key prompt mutation hooks can return:
- `systemPrompt` - replace system prompt
- `prependContext` - dynamic content prepended to context
- `prependSystemContext` - static, cacheable content prepended to system prompt
- `appendSystemContext` - static, cacheable content appended to system prompt

Hook policy: `plugins.entries[pluginId].hooks.allowPromptInjection` (boolean) controls prompt mutation access. When `false`, `before_prompt_build` is blocked entirely and `before_agent_start` is constrained to non-prompt fields.

## Plugin Runtime

```typescript
type PluginRuntime = {
  config: OpenClawConfig;
  workspaceDir: string;
  channels: PluginRuntimeChannels;
  tools: PluginRuntimeTools;
  events: PluginRuntimeEvents;
  system: PluginRuntimeSystem;
  // media, whatsapp, config access...
};
```

Runtime is lazy-loaded via Proxy to avoid heavy dependencies in test/validation scenarios.

## Plugin Config Type

```typescript
type PluginsConfig = {
  enabled?: boolean;                             // master switch
  allow?: string[];                             // allowlist of trusted plugin IDs
  deny?: string[];                              // denylist (allow takes precedence)
  load?: { paths?: string[] };                  // additional search paths
  slots?: { memory?: string | null };           // exclusive slot (null/"none" disables)
  entries?: Record<string, PluginEntryConfig>;  // per-plugin config
  installs?: Record<string, PluginInstallRecord>; // install tracking
};

type PluginEntryConfig = {
  enabled?: boolean;
  hooks?: { allowPromptInjection?: boolean };   // prompt mutation policy
  config?: Record<string, unknown>;
};

type PluginInstallRecord = {
  source: "npm" | "path" | "archive";
  spec?: string;
  sourcePath?: string;
  installPath?: string;
  version?: string;
  installedAt?: string;
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

Key exports: types, config access, channel interfaces, tool builders, hook types, media pipeline, crypto/signing utilities.

Channel-specific SDK subpaths:
- `openclaw/discord` - thread binding management (`autoBindSpawnedDiscordSubagent`, `listThreadBindingsBySessionKey`, `unbindThreadBindingsBySessionKey`)
- `openclaw/slack` - account resolution, inspection, onboarding adapters
- `openclaw/telegram` - account resolution, inspection, onboarding adapters

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

Removed `api.registerHttpHandler()` - plugins using it get a clear migration error pointing to new API (#36794).
