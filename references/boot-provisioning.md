# OpenClaw Boot & Provisioning

## Gateway Startup Sequence

Key files: `src/gateway/server-startup.ts`, `src/gateway/boot.ts`

### Boot Order

1. **Load config** - `loadConfig()` reads + validates config
2. **Load plugins** - `loadOpenClawPlugins()` discovers and registers all plugins
3. **Clean stale locks** - remove stale session lock files
4. **Start browser control** - if browser automation enabled
5. **Start watchers** - Gmail watcher, other hook-based watchers
6. **Load internal hooks** - from config + discovery
7. **Fire `gateway:startup` event** - plugins can hook into this
8. **Start channels** - Telegram, Discord, Slack, etc. (each with own connection lifecycle)
9. **Schedule restart sentinel** - wake check for updates

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
4. Session state restored after boot completes
5. Returns: `"skipped" | "ran" | "failed"`

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
| `--flow quick\|advanced\|manual` | Onboarding depth |
| `--auth-choice token\|openai-codex\|...` | Auth method |
| `--reset` | Reset config/creds/sessions first |
| `--reset-scope config\|config+creds+sessions\|full` | What to reset |
| `--workspace PATH` | Custom agent workspace |
| `--secret-input-mode plaintext\|ref` | Secret storage mode |
| `--accept-risk` | Required for non-interactive |

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
