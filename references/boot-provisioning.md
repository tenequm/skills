# OpenClaw Boot & Provisioning

## Gateway Startup Sequence

Key files: `src/gateway/server-startup.ts`, `src/gateway/boot.ts`

### Boot Order

1. **Load config** - `loadConfig()` reads + validates config
2. **Load plugins** - `loadOpenClawPlugins()` discovers and registers all plugins
3. **Clean stale locks** - remove stale session lock files (stale threshold: 30min)
4. **Start browser control** - if browser automation enabled
5. **Start Gmail watcher** - if `hooks.gmail.account` configured; validates `hooks.gmail.model` against catalog
6. **Load internal hooks** - clear previous hooks, load from config + directory discovery
7. **Start channels** - Telegram, Discord, Slack, etc. (skippable via `OPENCLAW_SKIP_CHANNELS=1`)
8. **Fire `gateway:startup` event** - delayed 250ms, plugins can hook into this (requires `hooks.internal.enabled`)
9. **Start plugin services** - `startPluginServices()` for registry lifecycle
10. **ACP identity reconcile** - if `acp.enabled`, reconcile pending session identities on startup
11. **Start memory backend** - `startGatewayMemoryBackend()` for qmd memory initialization
12. **Schedule restart sentinel** - wake check for updates (delayed 750ms)

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
