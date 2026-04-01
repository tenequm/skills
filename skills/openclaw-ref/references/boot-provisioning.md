# OpenClaw Boot & Provisioning

## Gateway Startup Sequence

Key files: `src/gateway/server-startup.ts`, `src/gateway/boot.ts`

### Boot Order

1. **Load config** - `loadConfig()` reads + validates config
2. **Seed control UI origins** - `maybeSeedControlUiAllowedOriginsAtStartup()` persists `gateway.controlUi.allowedOrigins` for non-loopback installs upgraded to v2026.2.26+ without required origins
3. **Record startup write hash** - if config was mutated (generated token or seeded origins), re-read snapshot and capture `startupInternalWriteHash` so the config reloader ignores this self-inflicted write
4. **Load plugins** - `loadOpenClawPlugins()` discovers and registers all plugins
5. **Clean stale locks** - remove stale session lock files (stale threshold: 30min)
6. **Start browser control** - if browser automation enabled
7. **Start Gmail watcher** - if `hooks.gmail.account` configured; validates `hooks.gmail.model` against catalog
8. **Load internal hooks** - clear previous hooks, load from config + directory discovery
9. **Start channels** - Telegram, Discord, Slack, etc. (skippable via `OPENCLAW_SKIP_CHANNELS=1`)
10. **Fire `gateway:startup` event** - delayed 250ms, plugins can hook into this (requires `hooks.internal.enabled`)
11. **Start plugin services** - `startPluginServices()` for registry lifecycle
12. **ACP identity reconcile** - if `acp.enabled`, reconcile pending session identities on startup
13. **Start memory backend** - `startGatewayMemoryBackend()` for qmd memory initialization (LanceDB runtime bootstrapped on demand at first use)
14. **Schedule restart sentinel** - wake check for updates (delayed 750ms)

### Plugin Loading During Boot

```typescript
function ensurePluginRegistryLoaded() {
  const config = loadConfig();
  const workspaceDir = resolveAgentWorkspaceDir(config, agentId);
  loadOpenClawPlugins({ config, workspaceDir, logger });
}
```

Checks during load:
- Allowlist enforcement (`plugins.allow`)
- Per-plugin enable state (`entries.<id>.enabled`)
- Manifest validation (config schema)
- Provenance tracking (warns about untracked plugins)

## BOOT.md Mechanism

Key file: `src/gateway/boot.ts`

On gateway startup:
1. Looks for `BOOT.md` in agent workspace dir
2. If exists and non-empty, runs agent with boot instructions as prompt
3. Agent executes BOOT.md tasks (send messages, configure, run setup)
4. Session state restored after boot completes (snapshots + restores main session mapping)
5. Returns discriminated union:
   - `{ status: "skipped", reason: "missing" | "empty" }`
   - `{ status: "ran" }`
   - `{ status: "failed", reason: string }`

- Boot runs in a dedicated session (`boot-<timestamp>-<uuid>`)
- Agent runs with `senderIsOwner: true`, `deliver: false`
- BOOT.md prompt instructs agent to use message tool with `action=send` and `channel` + `target` fields
- Silent reply token used to suppress unnecessary output

Use BOOT.md for one-shot initialization tasks that need agent intelligence (not just config).

## Config Reload Startup Loop Prevention

Key files: `src/gateway/config-reload.ts`, `src/gateway/server.impl.ts`

At startup, the gateway may mutate its own config file (seeding control UI origins, generating auth tokens). The config file watcher (chokidar) would see this write and trigger a reload loop.

Prevention mechanism:
1. After startup writes, the gateway re-reads the config snapshot and captures `startupInternalWriteHash`
2. `startGatewayConfigReloader()` receives `initialInternalWriteHash` and stores it as `lastAppliedWriteHash`
3. On watcher trigger, if the snapshot hash matches `lastAppliedWriteHash`, the reload is silently skipped
4. After the first non-self write, `lastAppliedWriteHash` is cleared (set to `null`) so future external changes reload normally

In-process config writes use `subscribeToWrites` listener to bypass the file watcher entirely: the listener receives the runtime config and persisted hash directly, sets `pendingInProcessConfig`, and schedules an immediate reload with `scheduleAfter(0)`.

## HTTP Request Pipeline

Key file: `src/gateway/server-http.ts`

HTTP requests are processed through `runGatewayHttpRequestStages()`, a stage-based pipeline with per-stage try/catch error isolation.

```typescript
type GatewayHttpRequestStage = {
  name: string;
  run: () => Promise<boolean> | boolean;
};

async function runGatewayHttpRequestStages(
  stages: readonly GatewayHttpRequestStage[],
): Promise<boolean>;
```

Each stage returns `true` if it handled the request (short-circuits remaining stages) or `false` to pass through. If a stage throws, the error is logged and the stage is skipped - subsequent stages (control-ui, gateway probes, etc.) remain reachable. This prevents a single broken plugin facade or missing optional dependency (e.g. `@slack/bolt`) from producing cascade 500s across unrelated routes.

## Node Command Policy

Key file: `src/gateway/node-command-policy.ts`

Determines which commands a connected node is allowed to execute. Decoupled from pairing state - the allowlist is resolved purely from config and platform metadata.

### Platform Defaults

Commands are grouped by platform (`ios`, `android`, `macos`, `linux`, `windows`, `unknown`). Platform is resolved from `node.platform` via prefix matching, then `node.deviceFamily` via token matching.

| Platform | Defaults |
|----------|----------|
| `ios` | canvas, camera, location, device, contacts, calendar, reminders, photos, motion, `system.notify` |
| `android` | canvas, camera, location, notifications (incl. actions), `system.notify`, device (incl. permissions/health), contacts, calendar, callLog, reminders, photos, motion |
| `macos` | canvas, camera, location, device, contacts, calendar, reminders, photos, motion, `system.run`/`system.which`/`system.notify`/`browser.proxy` |
| `linux`/`windows` | `system.run`, `system.which`, `system.notify`, `browser.proxy` |
| `unknown` | canvas, camera, location, `system.notify` |

### Dangerous Commands (opt-in)

`DEFAULT_DANGEROUS_NODE_COMMANDS`: `camera.snap`, `camera.clip`, `screen.record`, `contacts.add`, `calendar.add`, `reminders.add`, `sms.send`, `sms.search`. Not in any platform default - must be explicitly added via `gateway.nodes.allowCommands`.

### Allowlist Resolution

```typescript
resolveNodeCommandAllowlist(cfg, node): Set<string>
// = PLATFORM_DEFAULTS[platform] + cfg.gateway.nodes.allowCommands - cfg.gateway.nodes.denyCommands
```

### Command Validation

`isNodeCommandAllowed()` checks: command non-empty, in allowlist, and declared by node (node must advertise supported commands at connect time). If the node declared no commands, all invocations are rejected.

## Node Pairing Reconciliation

Key file: `src/gateway/node-connect-reconcile.ts`

`reconcileNodePairingOnConnect()` runs when a node connects via WebSocket:

1. Resolves `nodeId` from device ID or client ID
2. Resolves command allowlist via `resolveNodeCommandAllowlist()` using platform/deviceFamily from connect params
3. Filters declared commands against allowlist via `normalizeDeclaredNodeCommands()`
4. If node is not already paired, calls `requestPairing()` to create a pending pairing request
5. Returns `{ nodeId, effectiveCommands, pendingPairing? }`

## Node Catalog

Key file: `src/gateway/node-catalog.ts`

`createKnownNodeCatalog()` merges three sources into a unified node view:

- **Device pairing** - `PairedDevice` entries filtered to `role: "node"`
- **Node pairing** - `NodePairingPairedNode` approved entries with caps/commands/permissions
- **Live connections** - `NodeSession` currently connected nodes

Node IDs from all three sources are unioned. For each node, `buildEffectiveKnownNode()` resolves fields using live > nodePairing > devicePairing precedence. The `effective` field on each entry is a `NodeListNode` with merged `caps`, `commands` (sorted, deduplicated), version info, connection state, and pairing state.

`listKnownNodes()` sorts: connected first, then alphabetical by displayName/nodeId.

## Cron Busy-Wait Drift Fix

Key file: `src/cron/service/timer.ts`

Recurring main-session wake-now jobs (cron/every schedule, `sessionTarget: "main"`, `wakeMode: "now"`) previously blocked the cron lane in a busy-wait loop when the main session had requests in flight. This caused the cron job's measured duration to reflect queue wait time instead of actual bookkeeping.

Fix: when `heartbeatResult.status === "skipped"` with `reason: "requests-in-flight"` and the job is recurring (`schedule.kind !== "at"`), the cron lane now calls `requestHeartbeatNow()` (fire-and-forget nudge) and returns immediately with `{ status: "ok" }`. One-shot `at` jobs still busy-wait up to `wakeNowHeartbeatBusyMaxWaitMs` (default 2min) with 250ms retry delay before falling back to the nudge.

## Cron Legacy Delivery Migration (Doctor)

Key files: `src/commands/doctor-cron.ts`, `src/commands/doctor-cron-legacy-delivery.ts`, `src/commands/doctor-cron-store-migration.ts`

`maybeRepairLegacyCronStore()` detects and normalizes legacy cron job storage:

**Store migration** (`normalizeStoredCronJobs`):
- `jobId` -> `id`
- Bare string schedule -> `{ kind: "cron", expr }`
- `schedule.cron` -> `schedule.expr`
- Legacy payload kind normalization (`agentturn` -> `agentTurn`, `systemevent` -> `systemEvent`)
- Top-level payload/delivery fields inlined into nested `payload`/`delivery` objects
- Missing `state`, `enabled`, `wakeMode`, `name`, `sessionTarget` fields populated with defaults
- `delivery.mode: "deliver"` -> `"announce"`
- Legacy `payload.provider` -> `delivery.channel`

**Legacy delivery migration** (`normalizeLegacyDeliveryInput`):
- Extracts `deliver`, `bestEffortDeliver`, `channel`, `provider`, `to`, `threadId` from payload
- Builds or merges into structured `delivery` object with `mode: "announce"` or `"none"`
- Strips legacy fields from payload after migration

**Notify fallback** (`migrateLegacyNotifyFallback`):
- Jobs with `notify: true` and existing webhook delivery: just removes `notify` flag
- Jobs with `notify: true` but no delivery: migrates to `delivery.mode: "webhook"` using `cron.webhook` config
- Warns if `cron.webhook` is unset and migration cannot proceed automatically

## Bundled Plugin Runtime Deps Doctor Check

Key file: `src/commands/doctor-bundled-plugin-runtime-deps.ts`

`maybeRepairBundledPluginRuntimeDeps()` scans bundled plugins for missing native dependencies.

**Scan** (`scanBundledPluginRuntimeDeps`):
- Skips source checkout roots (`.git` + `src` + `extensions` present)
- Reads `package.json` from each plugin in `dist/extensions/`
- Collects `dependencies` + `optionalDependencies` across all plugins
- Detects missing deps (sentinel: `node_modules/<name>/package.json` absent) and version conflicts across plugins

**Repair**:
- Runs `npm install --omit=dev --no-save --package-lock=false --ignore-scripts --legacy-peer-deps` with pinned versions
- Strips npm global config env vars (`npm_config_global`, `npm_config_location`, `npm_config_prefix`) to prevent nested global install

**Conflict reporting**: if multiple plugins pin different versions of the same dep, warns with per-plugin version breakdown.

## Chat-Native Task Board

Key file: `src/commands/tasks.ts`

CLI subcommands for managing background tasks:

| Subcommand | Purpose |
|------------|---------|
| `tasks list` | List tasks with optional `--runtime` / `--status` filters. Shows task ID, kind, status, delivery, run, child session, summary. |
| `tasks show <id>` | Detailed view of a single task (lookup by ID or token prefix). All fields including timestamps, labels, errors, progress. |
| `tasks notify <id> <policy>` | Update a task's notify policy (`TaskNotifyPolicy`). |
| `tasks cancel <id>` | Cancel a running task. Calls `cancelTaskById()` which coordinates with the task runtime. |
| `tasks audit` | List audit findings with `--severity` / `--code` / `--limit` filters. Shows severity, code, task ID, status, age, detail. |
| `tasks maintenance` | Reconcile, stamp cleanup, prune. Dry-run by default; `--apply` to write changes. Reports audit health before/after. |

All subcommands support `--json` for machine-readable output. Task lookup uses `reconcileTaskLookupToken()` for prefix matching on shortened IDs.

## LanceDB Runtime Bootstrap

Key file: `extensions/memory-lancedb/lancedb-runtime.ts`

The `memory-lancedb` plugin bootstraps `@lancedb/lancedb` on demand via `createLanceDbRuntimeLoader()`:

1. **Try bundled import** - direct `import("@lancedb/lancedb")` (works in dev / monorepo)
2. **Try cached runtime** - check `<stateDir>/plugin-runtimes/memory-lancedb/lancedb/` for previously installed runtime matching manifest
3. **Auto-install** - if both fail, run `npm install` into the runtime dir with the pinned version from the plugin's `package.json`

Key behaviors:
- Load promise is singleton-cached; reset on failure so retries are possible
- Manifest comparison gates cache validity (version bump triggers reinstall)
- `OPENCLAW_NIX_MODE=1` disables auto-install (fail-fast for Nix environments)
- Exposed via `loadLanceDbModule()` for use in the plugin index

## Skill Secrets Runtime Resolution

Key file: `src/agents/skills/runtime-config.ts`

Skill env overrides (`applySkillEnvOverrides`, `applySkillSnapshotEnvOverrides`) now prefer the runtime config snapshot over the static config:

```typescript
function resolveSkillRuntimeConfig(config?: OpenClawConfig): OpenClawConfig | undefined {
  return getRuntimeConfigSnapshot() ?? config;
}
```

This ensures SecretRef-resolved secrets (only available after secrets provider initializes at runtime) are used for skill env injection, rather than raw config values from disk.

## OpenAI Codex Proxy Bootstrap

Key file: `extensions/openai/openai-codex-provider.runtime.ts`

The Codex OAuth refresh wrapper now bootstraps the global undici proxy dispatcher before calling the upstream `getOAuthApiKey`. Without this, OAuth token refreshes behind an HTTP proxy would fail because the proxy dispatcher was only set up during initial agent run startup, not during deferred token refresh.

## Onboarding Flows

Key files: `src/commands/onboard.ts`, `src/commands/onboard-interactive.ts`, `src/commands/onboard-non-interactive.ts`

### CLI

```bash
openclaw onboard [OPTIONS]
```

### Options

| Flag | Purpose |
|------|---------|
| `--non-interactive` | No prompts (requires `--accept-risk`) |
| `--mode local\|remote` | Local vs remote execution |
| `--flow quick\|advanced\|manual` | Onboarding depth (`manual` mapped to `advanced`) |
| `--auth-choice token\|openai-codex\|...` | Auth method |
| `--reset` | Reset config/creds/sessions first |
| `--reset-scope config\|config+creds+sessions\|full` | What to reset (default: `config+creds+sessions`) |
| `--workspace PATH` | Custom agent workspace |
| `--secret-input-mode plaintext\|ref` | Secret storage mode |
| `--accept-risk` | Required for non-interactive |

### Auth Choice Deprecations

- `claude-cli` deprecated: falls back to setup-token flow with warning
- `codex-cli` deprecated: falls back to OpenAI Codex OAuth with warning
- Non-interactive mode rejects deprecated auth choices with error

### Onboard Talk Fallback Fix

- Fresh setup no longer persists talk fallback secrets into config
- Talk API key resolution (`applyTalkApiKey`) only injects env-resolved key when no provider-specific or legacy key is already configured

### Interactive Flow

1. Prompts for channels, auth, models
2. Saves config progressively
3. Creates initial workspace/sessions

### Non-Interactive Local Flow

1. Accepts env vars or flags (no prompts)
2. Validates all inputs
3. Fast automated setup
4. Use for scripted/automated provisioning

### Non-Interactive Remote Flow

1. Remote SSH/gateway setup
2. For headless/container deployments

## Exec Approval Manager

Key file: `src/gateway/exec-approval-manager.ts`

In-memory manager for exec command approvals (used by Telegram exec approvals for OpenCode/Codex).

```typescript
class ExecApprovalManager {
  create(request, timeoutMs, id?): ExecApprovalRecord;
  register(record, timeoutMs): Promise<ExecApprovalDecision | null>;  // preferred over waitForDecision
  resolve(recordId, decision, resolvedBy?): boolean;
  expire(recordId, resolvedBy?): boolean;
  consumeAllowOnce(recordId): boolean;    // atomic one-time approval consumption
  awaitDecision(recordId): Promise<...>;  // DEPRECATED: use register() instead
  lookupPendingId(input): ExecApprovalIdLookupResult;  // exact, prefix, or ambiguous match
  getSnapshot(recordId): ExecApprovalSnapshot | undefined;  // read-only snapshot of current state
}
```

- `ExecApprovalDecision`: `"allow-once"` or other decision types
- Resolved entries kept for 15s grace period for late `awaitDecision` calls
- Supports caller metadata: `requestedByConnId`, `requestedByDeviceId`, `requestedByClientId`
- `lookupPendingId` supports prefix matching for shortened approval IDs
- After approval completion, the agent session is resumed via `sendExecApprovalFollowup()` which dispatches a `callGatewayTool("agent", ...)` with the original session key and a structured prompt containing the exec result. Denied commands get a distinct prompt instructing the agent not to retry.

## Channel Health Monitor

Key files: `src/gateway/channel-health-monitor.ts`, `src/gateway/channel-health-policy.ts`

Periodically checks channel health and auto-restarts unhealthy channels.

### Health Evaluation Reasons

- `healthy` - normal operation
- `not-running` - channel stopped
- `disconnected` - running but not connected
- `stale-socket` - connected but no events within threshold (half-dead WebSocket)
- `stuck` - busy but no run activity within 25min
- `busy` - actively processing (healthy short-circuit)
- `startup-connect-grace` - within connect grace window after start
- `unmanaged` - disabled/unconfigured accounts (NEW)

### Restart Reasons

`ChannelRestartReason` type:
- `gave-up` - reconnectAttempts >= 10
- `stopped` - channel stopped unexpectedly
- `stale-socket` - no events within threshold
- `stuck` - busy but no progress
- `disconnected` - running but not connected

### Timing Defaults (via `ChannelHealthTimingPolicy`)

- Check interval: 5 minutes (`channelHealthCheckMinutes` config)
- Monitor startup grace: 60s
- Channel connect grace: 120s (`DEFAULT_CHANNEL_CONNECT_GRACE_MS`)
- Stale event threshold: 30 minutes (`channelStaleEventThresholdMinutes` config)
- Cooldown: 2 cycles between restarts per channel
- Max restarts: 10/hour per channel (`channelMaxRestartsPerHour` config)

### Health Check Skips

- `isHealthMonitorEnabled` - checks if monitoring is enabled
- `isManuallyStopped` - skips monitoring for manually stopped channels

### Busy Lifecycle Guard

`busyStateInitializedForLifecycle` prevents stale busy fields from previous channel lifecycle causing false healthy short-circuit.

### Stale Socket Exclusions

- Telegram (long-polling) and webhook-mode channels excluded from stale-socket checks
- Lifecycle-aware: ignores stale `lastEventAt` from previous lifecycle when channel restarted

### Restart Flow

stop -> `resetRestartAttempts` -> start -> record timestamp

## Node Pending Work

Key file: `src/gateway/server-methods/nodes-pending.ts`

Gateway methods for pending node work queue:

```typescript
"node.pending.drain"    // Drain pending work items for calling node (by device/client ID)
"node.pending.enqueue"  // Enqueue work for a specific node, with optional APNs wake + reconnect retry
```

- Enqueue supports priority and expiry
- Wake flow: APNs push -> wait for reconnect (two attempts with retry) -> nudge fallback
- Drain includes `defaultStatus` in response

## Gateway Auth

Key file: `src/gateway/auth.ts`

### Auth Modes

- `none` - no authentication
- `token` - shared secret token (config or `OPENCLAW_GATEWAY_TOKEN` env)
- `password` - shared password (config or `OPENCLAW_GATEWAY_PASSWORD` env)
- `trusted-proxy` - identity from reverse proxy headers (`trustedProxy.userHeader`)

### Auth Methods (result)

Auth resolution returns a method value: `none`, `token`, `password`, `trusted-proxy`, `device-token`, `bootstrap-token`.

### Auth Resolution

- Mode auto-detected: override > config > password presence > token presence > default (token)
- Tailscale: Whois-verified identity for WS Control UI surface only (not HTTP)
- Rate limiting: per-IP sliding window, lockout on exceeded threshold
- Missing credentials (no token/password provided) do not burn rate-limit slots
- Lockout expired entries reset attempt counters correctly (prevents infinite escalation)
- `GatewaySecretRefUnavailableError` thrown when SecretRef is used but secrets provider not initialized
- `allowRealIpFallback`: trusts X-Real-IP only when explicitly enabled (default: false)

### Trusted Proxy Auth

- `requiredHeaders`: headers that must be present from the proxy
- `allowUsers`: optional allowlist of user identities

### Credential Resolution

Key files: `src/gateway/credentials.ts`, `src/gateway/credential-planner.ts`

- Local mode: `gateway.auth.token` with `gateway.remote.token` as fallback
- Remote mode: `gateway.remote.*` with env and local config fallback chain
- Precedence: gateway service context uses `config-first`, others use `env-first`
- Unresolved `${VAR}` placeholders in credential values are rejected (`trimCredentialToUndefined`)
- `CLAWDBOT_*` legacy env vars supported as fallback
- `GatewayCredentialPlan` type for structured credential resolution
- `resolveGatewayProbeCredentialsFromConfig` - probe-specific, remote-only fallback
- `resolveGatewayDriftCheckCredentialsFromConfig` - drift check, local mode, config-first, empty env

## AgentBox Provisioning Flow

How agentbox provisions openclaw instances (reference pattern for automated provisioning):

```
1. VM created (Hetzner) with cloud-init
2. Boot script runs (agentbox-init.sh):
   a. Wait for user systemd readiness
   b. Fetch config from backend API: GET /instances/config?serverId=X&secret=Y
   c. Configure reverse proxy (Caddy HTTPS)
   d. Write ~/.openclaw/openclaw.json (merged config via jq)
   e. Generate wallet (openclaw-x402 CLI)
   f. Set gateway token in systemd drop-in
   g. Start gateway service (systemd user unit)
   h. Wait for health check (up to 120s, gateway cold start ~72s)
3. VM calls back to backend with wallet + gatewayToken
4. Backend funds wallet + mints SATI NFT
5. Instance state: provisioning -> minting -> running
```

### Config Merge Pattern (jq)

```bash
# Fetch base config from API
curl -s "$BACKEND_URL/instances/config?serverId=$SERVER_ID&secret=$SECRET" | \
  jq --arg rpc "$RPC_URL" \
     --arg token "$TELEGRAM_TOKEN" \
     '.plugins.entries["openclaw-x402"].config.rpcUrl = $rpc |
      if $token != "" then .channels.telegram.token = $token else . end' \
  > ~/.openclaw/openclaw.json
```

### Gateway Auth

- Token-based: `OPENCLAW_GATEWAY_TOKEN` env var
- Systemd drop-in: `~/.config/systemd/user/openclaw-gateway.service.d/token.conf`
- Config: `gateway.auth.token` and `gateway.remote.token` must match
- API access: `Bearer <gatewayToken>` for `/v1/chat/completions`

## Health Check

After starting gateway, verify:
```bash
# Check port
ss -ltnp | grep 18789

# Check gateway health
curl -s http://localhost:18789/health

# Check channel status
openclaw channels status --probe
```

## Key Provisioning Gotchas

1. **Gateway cold start is slow** (~72s on small VMs) - plan for timeout
2. **Plugin fetch interceptor needs gateway token** - token must be in both systemd env AND config file
3. **Skills auto-discovered** from `~/.openclaw/skills/` - no explicit config needed
4. **Config strictly validated** - malformed JSON breaks startup entirely
5. **Channels require explicit config** - Telegram is opt-in, not auto-discovered
6. **`models.mode: "replace"`** hides all 700+ builtins - only providers in config appear
7. **Plugin `registerProvider()`** is auth-only, does NOT populate model catalog - metadata must be defined in config
8. **Bootstrap secrets** (gateway.auth.password) must be plaintext strings or env vars - secrets provider system is not initialized at gateway startup
9. **Exec child commands** marked with `OPENCLAW_CLI` env var
10. **Memory flush** protects bootstrap files during flush operations
11. **One-shot mode** tears down cached memory managers to prevent exit hangs
12. **Default reasoning config** now defaults to off (PR #50405) - agents expecting reasoning must enable it explicitly
13. **LanceDB runtime auto-installs** on packaged/global installs where bundled import fails - requires `npm` on PATH; disable with `OPENCLAW_NIX_MODE=1`
14. **Skill SecretRef secrets** only available after secrets provider initializes - skill env overrides now prefer `getRuntimeConfigSnapshot()` over static config so resolved secrets propagate
15. **Codex OAuth behind proxy** - proxy dispatcher must be bootstrapped before OAuth refresh; now handled automatically by the `getOAuthApiKey` wrapper
16. **Startup config reload loop** - gateway records `startupInternalWriteHash` after self-mutations (token generation, origin seeding); config reloader skips watcher triggers matching this hash
17. **HTTP stage cascade 500s** - `runGatewayHttpRequestStages()` isolates each stage in try/catch; a broken plugin facade or missing optional dep no longer takes down unrelated HTTP routes
18. **Node command policy is config-only** - allowlist resolution is decoupled from pairing state; determined by platform defaults + `gateway.nodes.allowCommands` - `gateway.nodes.denyCommands`
19. **Cron recurring wake-now drift** - recurring main-session cron jobs no longer busy-wait when the main lane is busy; they fire a `requestHeartbeatNow` nudge and release the cron lane immediately
20. **Bundled plugin runtime deps** - packaged installs may be missing native deps from bundled plugins; `openclaw doctor --fix` runs `npm install` with pinned versions into the package root
