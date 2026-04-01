# OpenClaw GitHub Context
> Last refreshed: 2026-03-31T23:00:00Z

## Open Bugs (critical for development)

### Plugin System
- **#58427** - Plugin subagent calls intermittently fail with "Plugin runtime subagent methods are only available during a gateway request"
- **#53046** - Missing extension runtime API entry points in package.json in extensions (v2026.3.22 regression)
- **#52633** - openclaw-mem0 plugin loads but agent never calls memory_store tool, autoCapture not triggered
- **#52433** - ACPX plugin always reverts to 0.1.16, ignores npm/manual upgrade (0.3.1 never sticks)
- **#52250** - Plugin-backed channels become unknown in subagent flows when OPENCLAW_STATE_DIR is relative
- **#50441** - Slack channel crashes: "App is not a constructor" (@slack/bolt ESM interop)
- **#50382** - Duplicate plugin loading warning for installed extensions on gateway startup
- **#50131** - Plugin tools loaded in chat/agent do not inherit gateway subagent runtime/scope
- **#41757** - Custom plugin tool not surfaced to sandboxed agent sessions
- **#41229** - `plugins install` fails for local plugins when `plugins.allow` already exists
- **#39878** - `plugins uninstall` fails when channel config references the plugin being removed
- **#40232** - Plugin context engines can resolve before plugin registration
- **#36754** - Extension discovery silently skips symlinked plugin directories
- **#28122** - pnpm global install: bundled plugin manifests rejected as 'unsafe path'
- **#12854** - CJS dependencies fail with "require is not defined" under jiti loader
- **#36377** - Native bindings (sqlite3) broken under jiti

### Config Validation
- **#58466** - Live session model switch blocks failover on overloaded_error - infinite retry loop (REGRESSION)
- **#58456** - API Key Status Display Shows "unknown" for qwen-dashscope and anthropic-openai Providers (REGRESSION)
- **#58357** - HTTP /v1/chat/completions returns 'missing scope: operator.write' with --auth none (v2026.3.28)
- **#58355** - Failed to set model for Ollama - model not allowed
- **#58087** - SecretRef-backed model provider headers sent as literal "secretref-managed" in API requests (REGRESSION)
- **#52551** - Dashboard model selector concatenates wrong provider ID
- **#49666** - Telegram proxy config wiped on gateway restart
- **#24008** - Unrecognized config keys silently wipe and reset entire section on restart
- **#36792** - Gateway promises "best-effort config" on invalid config but exits instead

### Gateway Startup
- **#58415** - ws-stream WebSocket connect fails with 500 and always falls back to HTTP
- **#58256** - browser.server not starting after upgrade to v2026.3.28 - "openclaw browser start" command not found (REGRESSION)
- **#53168** - CLI commands crash gateway via WebSocket handshake timeout (v2026.3.22)
- **#52766** - Gateway WebSocket handshake timeout on local loopback breaks all CLI RPC commands
- **#51987** - Local gateway websocket handshake times out on 127.0.0.1:18789
- **#51879** - CLI gateway handshake timeout on WSL2
- **#51438** - CLI to Gateway WebSocket connections timeout in v2026.3.12+ (regression)
- **#50074** - Gateway restart fails - stale process misdetection
- **#41804** - Gateway persistent stale processes on Windows
- **#36585** - TLS null dereference crash during socket reconnection
- **#34539** - structuredClone FATAL ERROR in orphaned subagent reconciliation
- **#24178** - Doctor check blocks indefinitely without TTY
- **#22972** - Health check times out on slow startups

### Secrets/Auth
- **#58217** - API calls get "missing scope: operator.write" (REGRESSION)
- **#52794** - Client request session.list error: scope operator.read do not have (v2026.3.22)
- **#52488** - `openclaw status --all` shows "missing scope: operator.read" even after full pairing
- **#51911** - Anthropic setup-token onboarding path has multiple failure modes
- **#49885** - google-vertex fails with "No credentials found for profile" even when ADC is valid
- **#49138** - OAuth flow missing api.responses.write scope
- **#37303** - Onboarding crashes with exec secret provider
- **#12517** - [SEC] All 31 plugins share single Node.js process - lateral movement across plugins
- **#12518** - [SEC] All plugin credentials in shared `process.env` - no isolation
- **#11829** - [SEC] API keys leak to LLM via tool outputs, error messages, system prompts

### Channels
- **#58546** - Multi-agent routing resolves correct agent but session created under default agent (REGRESSION)
- **#58535** - Discord announce removing fields from input
- **#58523** - Slack multi-workspace: outbound works on second workspace but inbound DM replies never reach OpenClaw
- **#58514** - Google Chat: Space/Group messages silently ignored
- **#58408** - WhatsApp Inbound Works But Outbound CLI Fails With "No Active Listener"
- **#58402** - message tool "Operation aborted" + WhatsApp reconnect storm + xai-auth log spam
- **#58249** - Teams webhook broken in 2026.3.24+: publicUrl removed breaks JWT validation (REGRESSION)
- **#58107** - Multiple Feishu group agents - only main reply delivered, others silently dropped (REGRESSION)
- **#52778** - WeCom DM message isolation failure
- **#52763** - WhatsApp groupPolicy "allowlist" bypassed
- **#52729** - hooks.internal.enabled causes LINE webhook 404
- **#52615** - Discord `allowFrom` Web UI double-escaping IDs
- **#52454** - Telegram:direct does not send thread back when you talk in the GUI
- **#52167** - WhatsApp media sends fail on old-style group JIDs
- **#51716** - Signal group messages silently dropped on Node 24
- **#51190** - Discord channel running=true while connected=false
- **#51158** - Matrix plugin syncs but never routes inbound messages to agent
- **#50999** - Telegram polling enters repeated stall/restart loop on macOS
- **#50450** - Telegram duplicate message sending bug (restart causes resend)
- **#50326** - Telegram `replyToMode: all` does not reply to triggering message in topics
- **#50174** - Windows: Telegram polling stalls every ~107s + Discord disconnects
- **#41581** - Telegram DM partial streaming regressed to choppy editMessageText
- **#41576** - Channel leaks `[[reply_to:ID]]` tags into visible message text
- **#36687** - `session.dmScope` reset causes cross-channel reply leakage

### Agent Runtime
- **#58599** - Edit tool schema mismatch: "edits" array in schema vs flat "oldText"/"newText" in implementation
- **#58553** - Long sessions (600+ messages) break with "invalid function call parameters"
- **#58442** - Model failover fails on Coding Plan quota 429 errors - infinite loop
- **#58363** - kimi web_search run error
- **#58358** - OpenClaw mishandles message_stop for KimiCodingPlan Anthropic format
- **#52708** - ACP `mode: "run"` sessions leave orphan processes
- **#52677** - web_search/web_fetch tools not available with built-in Gemini provider
- **#52612** - Full cacheWrite after using subagents (Anthropic)
- **#52604** - repairToolUseResultPairing misses orphaned tool IDs from MiniMax/OpenAI-compat
- **#52559** - Agent writes do not persist to host workspace even with sandbox off
- **#52317** - System prompt completely missing after /new
- **#51774** - Google provider adapter: streaming flag causes 400
- **#51743** - Google provider: usageMetadata not mapped - all Gemini calls record 0 tokens
- **#51593** - HTTP 400: "tool call id is duplicated" with moonshot/kimi-k2.5
- **#50401** - DeepSeek-V3 (SiliconFlow): 400 error on tool calls
- **#50178** - 400 thinking enabled but reasoning_content missing
- **#50094** - Compactor preserves orphaned tool_use blocks causing 400 on model switch
- **#50017** - Automatic model fallback does not recover cleanly from invalid primary model
- **#41707** - After upgrade, tools enter infinite repeat loop
- **#41291** - Agent enters infinite retry loop when tool calls fail
- **#36520** - Runtime events mutate system prompt every turn, invalidating prompt cache

### Skills
- **#52073** - Agent becomes completely unresponsive during Skill installation
- **#35272** - Sub-agents cannot access shared skills from `~/.openclaw/skills/`
- **#29122** - Workspace skills silently not loading
- **#21709** - `skills.allowBundled: []` allows all instead of blocking all

### Cron
- **#58575** - --model flag on isolated cron jobs does not override session model (REGRESSION)
- **#58065** - Specified model for cron overridden by agent default (REGRESSION)
- **#52975** - sessionTarget method of using custom sessionID in cron does not work
- **#52806** - Cron: Isolated sessions not executing
- **#52563** - Cron task configuration error causes Gateway crash
- **#52271** - sessions_send from cron/heartbeat deadlocks on nested lane
- **#51530** - Cron job agentTurn model override to Google/Gemini failing
- **#49258** - Cron job state inconsistency

### TUI / Control UI
- **#58494** - Browser CDP profiles prefer stale cdpUrl over valid cdpPort
- **#58479** - Approval dialog succeeds in Control UI, but exec never consumes the approval (REGRESSION)
- **#58560** - Browser tools fail with AJV "no schema with key or ref" 2020-12 error (REGRESSION)
- **#53096** - Control UI assets not found on v2026.3.22
- **#52565** - Control UI event listener registration failure in 2026.3.13
- **#52511** - Control UI session intermittently loses browser control permission
- **#52282** - Windows pnpm ui:build fails (path with spaces)
- **#51685** - Control UI freezes with high CPU when switching sessions
- **#51507** - WebChat/Control-UI context calculation inaccurate
- **#37243** - TUI replies routed to Telegram instead of TUI

### Critical / Data Loss
- **#58409** - [CRITICAL] Heartbeat System Causes Silent Session Reset - User Data Loss (REGRESSION)
- **#58234** - Heartbeat trigger anomaly - does not fire in target session (REGRESSION)

## Breaking Changes & Regressions

### Breaking in v2026.3.28+ (current)
- Browser server removed from gateway - "openclaw browser start" not found (#58256, #58221)
- HTTP API returns 'missing scope: operator.write' with --auth none (#58357, #58217)
- Teams webhook broken: publicUrl removed breaks JWT validation (#58249)
- Heartbeat system causes silent session reset (#58409, #58234)
- Model failover infinite retry on overloaded_error (#58466)
- Cron model override ignored (#58575, #58065)
- Multi-agent routing creates session under wrong agent (#58546)
- SecretRef-backed headers sent as literal "secretref-managed" (#58087)
- API key status shows "unknown" for some providers (#58456)

### Breaking in v2026.3.22 (still relevant)
- Control UI assets missing from npm package (#53096)
- Matrix Plugin API version mismatch (#52899)
- Missing extension runtime API entries (#53046)

### Active Regressions
| Issue | Summary |
|-------|---------|
| #58599 | Edit tool schema mismatch (edits[] vs flat) |
| #58595 | esbuild binary incompatible with macOS 10.15 since ~2026.3.8 |
| #58575 | Cron --model flag does not override session model |
| #58560 | Browser tools AJV schema error |
| #58546 | Multi-agent routing session under wrong agent |
| #58544 | openclaw update fails with preflight-no-good-commit |
| #58479 | Control UI exec approval never consumed |
| #58466 | Model switch blocks failover on overloaded - infinite loop |
| #58456 | API key status "unknown" for some providers |
| #58409 | CRITICAL: Heartbeat causes silent session reset |
| #58256 | Browser server removed from gateway, command not found |
| #58249 | Teams webhook broken (publicUrl removed) |
| #58234 | Heartbeat trigger anomaly |
| #58221 | Chrome extension browser relay unavailable on macOS |
| #58217 | API calls get "missing scope: operator.write" |
| #58107 | Multiple Feishu agents - only main reply delivered |
| #58087 | SecretRef headers sent as literal string |
| #58065 | Cron model override ignored |

### Config Migration Hazards
- **#49666** - Telegram proxy config silently wiped on restart
- **#24008** - Unknown config keys silently wipe entire section on restart
- Browser control server removed - configs referencing `browser.server` need migration
- `hooks.internal.enabled` default changed to `true` - may affect setups relying on it being off
- `exec.host` default changed from `"sandbox"` to `"auto"`

## Plugin/Extension/Config Known Issues

### Plugin Loading
- CJS dependencies fail under jiti ESM loader (#12854) - fundamental limitation
- Native bindings (sqlite3) broken under jiti (#36377)
- Symlinked plugin dirs silently skipped (#36754)
- pnpm global install rejects bundled plugin manifest paths (#28122)
- Plugin tools not inherited by subagent runtime scope (#50131)
- Custom plugin tools invisible to sandboxed sessions (#41757)
- Plugin subagent methods fail outside gateway request context (#58427)
- ACPX version pinning broken - always reverts to 0.1.16 (#52433)
- Dangerous installs now fail closed by default - use `--dangerously-force-unsafe-install` to override

### Skills
- Sub-agents cannot see globally installed skills (#35272)
- Skills can silently fail to load with no error (#29122)
- `skills.allowBundled: []` semantics inverted (#21709)
- Agent becomes unresponsive during skill installation (#52073)

### Channel Plugin Registration
- Slack ESM interop crash: "App is not a constructor" (#50441)
- Slack multi-workspace inbound DM replies missing (#58523)
- WhatsApp outbound fails despite connected status (#58408)
- WhatsApp groupPolicy "allowlist" bypassed (#52763)
- Teams webhook broken in 2026.3.24+ (#58249)
- Feishu multi-group only main reply delivered (#58107)
- Google Chat space/group messages silently ignored (#58514)
- Matrix plugin syncs but never routes inbound messages (#51158)
- Signal group messages silently dropped on Node 24 (#51716)
- LINE webhook 404 with hooks.internal.enabled (#52729)
- Discord channel running=true while connected=false (#51190)

## Recent Impactful PRs (last 30 days, since 2026-03-01)

| PR | Title | Area |
|---|---|---|
| #58554 | test: dedupe extension-owned coverage | Tests/Extensions |
| #58521 | fix(tasks): make task-store writes atomic | Tasks |
| #58516 | refactor(tasks): add owner-key task access boundaries | Tasks |
| #58382 | fix(pairing): restore qr bootstrap onboarding handoff | Pairing |
| #58379 | fix(gateway): prevent session death loop on overloaded fallback | Gateway |
| #58376 | fix(matrix): filter fetched room context by sender allowlist | Matrix |
| #58375 | Plugins: preserve prompt build system prompt precedence | Plugins |
| #58371 | Gateway: reject mixed trusted-proxy token config | Gateway |
| #58369 | Exec approvals: reject shell init-file script matches | Security |
| #58299 | fix: normalize MCP tool schemas missing properties field for OpenAI Responses API | Agents |
| #58253 | fix(qqbot): align speech schema and setup validation | QQ Bot |
| #58245 | fix(discord): gate voice ingress by allowlists | Discord |
| #58236 | fix(nostr): verify inbound dm signatures before pairing replies | Nostr |
| #58226 | fix(media): reject oversized image inputs before decode | Media |
| #58225 | fix(hooks): rebind hook agent session keys to the target agent | Hooks |
| #58208 | fix: omit disabled OpenAI reasoning payloads | Agents |
| #58175 | fix(exec): keep awk and sed out of safeBins fast path | Security |
| #58167 | fix(gateway): narrow plugin route runtime scopes | Gateway |
| #58141 | Secrets: hard-fail unsupported SecretRef policy and fix gateway restart token drift | Secrets |
| #58100 | Sessions: parse thread suffixes by channel | Sessions |
| #58025 | Sandbox: relabel managed workspace mounts for SELinux | Sandbox |
| #57995 | feat(matrix): thread-isolated sessions and per-chat-type threadReplies | Matrix |
| #57848 | Sandbox: sanitize SSH subprocess env | Security |
| #57729 | Plugins: block install when source scan fails | Security |
| #57507 | fix: support multi-kind plugins for dual slot ownership | Plugins |
| #56930 | feat(matrix): add explicit channels.matrix.proxy config | Matrix |
| #56710 | fix(compaction): resolve model override in runtime context for all context engines | Agents |
| #56387 | feat(matrix): add draft streaming (edit-in-place partial replies) | Matrix |
| #56060 | fix(telegram): forum topic replies route to root chat + ACP spawn fails from forum topics | Telegram |
| #52986 | Feature/add qq channel | Channels |

## Dev Gotchas (synthesized)

- **v2026.3.28 removes browser control server from gateway** - "openclaw browser start" is gone (#58256, #58221). Chrome extension browser relay stops working. This is a structural change, not a bug.
- **Heartbeat system can silently reset sessions** (#58409, #58234) - CRITICAL data loss bug. Heartbeat triggers may fire in wrong session or cause unexpected resets.
- **Model failover infinite loop on overloaded_error** (#58466) - live session model switch blocks fallback, causing infinite retry. Affects production setups with overloaded providers.
- **Cron model override is broken** (#58575, #58065) - --model flag and agentTurn model override both fail; always uses agent default. Two independent reports.
- **Exec approval consumption broken in Control UI** (#58479) - approval dialog succeeds but exec never consumes it, generates new approval ID. Regression.
- **HTTP API scope regression** (#58357, #58217) - /v1/chat/completions returns "missing scope: operator.write" even with --auth none. Affects v2026.3.28.
- **Teams webhook broken since 2026.3.24** (#58249) - publicUrl removal breaks JWT validation.
- **hooks.internal.enabled now defaults to true** - bundled hooks load on fresh installs. Old configs relying on false default may see new behavior.
- **exec.host defaults to "auto" instead of "sandbox"** - may change exec routing behavior for existing setups.
- **Plugin installs now fail closed on dangerous code** - use `--dangerously-force-unsafe-install` to override. Plugin source scan failures also block install.
- **Multi-kind plugins supported** (PR #57507) - `kind` field can be an array `["memory", "context-engine"]`. New `slots.ts` module handles slot resolution.
- **Prompt cache invalidated every turn** (#36520) - still open. PR #53212 (split static/dynamic blocks) helps for Anthropic but doesn't fully fix.
- **Shared process model = no plugin isolation** (#12517, #12518) - all plugins share one Node.js process.
- **Sub-agents can't see globally installed skills** (#35272) - still no fix.
- **Config keys still silently wipe sections** (#24008) - validate config carefully across upgrades.
- **Plugin prompt hooks need explicit allowlist** (PR #36567) - `hooks.allowPromptInjection` required.
- **`gateway.auth.mode` now mandatory** (PR #35094) - fails if both token+password without explicit mode.
- **Google provider usageMetadata not mapped** (#51743) - all Gemini calls record 0 tokens.
- **SecretRef-backed headers resolve to literal string** (#58087) - regression affecting model providers using SecretRef for custom headers.
- **Long sessions break model inference** (#58553) - 600+ message sessions get "invalid function call parameters".
- **Edit tool schema mismatch** (#58599) - edits[] array in schema vs flat oldText/newText in implementation.
