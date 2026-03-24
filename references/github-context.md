# OpenClaw GitHub Context
> Last refreshed: 2026-03-24T10:00:00Z

## Open Bugs (critical for development)

### Plugin System
- **#53046** - Missing extension runtime API entry points in package.json in extensions (v2026.3.22 regression)
- **#52938** - Non-provider registrations during snapshot loads cause duplicate warnings (fixed by PR #52938)
- **#52899** - Matrix Plugin API version mismatch after upgrade to v2026.3.22 (13 upvotes)
- **#52633** - openclaw-mem0 plugin loads but agent never calls memory_store tool, autoCapture not triggered
- **#52572** - Feishu plugin registers all tools twice
- **#52527** - 2026.3.13 breaks Slack Socket Mode - needed rollback to 2026.3.8
- **#52433** - ACPX plugin always reverts to 0.1.16, ignores npm/manual upgrade (0.3.1 never sticks)
- **#52250** - Plugin-backed channels become unknown in subagent flows when OPENCLAW_STATE_DIR is relative
- **#50441** - Slack channel crashes: "App is not a constructor" (@slack/bolt ESM interop)
- **#50382** - Duplicate plugin loading warning for installed extensions on gateway startup
- **#50323** - "failed to persist plugin auto-enable changes" warning on startup with wecom plugin
- **#50131** - Plugin tools loaded in chat/agent do not inherit gateway subagent runtime/scope - delegated plugin tools fail
- **#41757** - Custom plugin tool not surfaced to sandboxed agent sessions - appears only when sandbox removed
- **#41229** - `plugins install` fails for local plugins when `plugins.allow` already exists
- **#39878** - `plugins uninstall` fails when channel config references the plugin being removed
- **#40232** - Plugin context engines can resolve before plugin registration (Lossless Claw / contextEngine slot)
- **#36754** - Extension discovery silently skips symlinked plugin directories (`isDirectory()` returns false)
- **#28122** - pnpm global install: bundled plugin manifests rejected as 'unsafe path' - gateway refuses to start
- **#12854** - CJS dependencies fail with "require is not defined" under jiti loader - blocks plugins importing CJS npm packages
- **#36377** - Native bindings (sqlite3) broken under jiti (recurring: #31676, #31677)

### Config Validation
- **#53031** - Model switch from UI generates wrong prefix (zai/deepseek-chat instead of deepseek/deepseek-chat) (v2026.3.22 regression)
- **#52551** - Dashboard model selector concatenates wrong provider ID
- **#52482** - Control UI incorrectly handles provider prefixes (regression)
- **#52311** - OpenAI models display as anthropic/gpt-5.4-pro
- **#52233** - UI fails to update provider prefix when switching models across providers
- **#52173** - Dashboard v2 model switcher incorrectly concatenates provider prefix
- **#51824** - Control UI model selector incorrectly maps bailian models to qwen-portal provider
- **#51809** - Dashboard model picker sends anthropic/ prefix for non-Anthropic models
- **#51608** - Control UI model picker sends wrong provider prefix for all models
- **#51334** - GUI model switching error combining provider prefix
- **#51306** - Model picker in Control UI mangles provider prefix
- **#51139** - Control UI model selection uses wrong provider prefix
- **#50293** - Control UI model dropdown shows incorrect entries
- **#50197** - Control UI dropdown fails to reset provider prefix after model switch
- **#50050** - Control UI model switcher sends wrong provider prefix for cross-provider switching
- **#49686** - "model not allowed" when selecting models with custom provider prefix
- **#49666** - Telegram proxy config wiped on gateway restart
- **#24008** - Unrecognized config keys silently wipe and reset entire section on restart
- **#35957** - Stale keys from v2026.3.2 block gateway startup in v2026.3.3+
- **#36792** - Gateway promises "best-effort config" on invalid config but exits instead
- **#32583** - MCP servers config not in schema - adding to openclaw.json fails with 'Unrecognized key'

### Gateway Startup
- **#53168** - CLI commands crash gateway via WebSocket handshake timeout (v2026.3.22)
- **#53067** - CLI cannot connect to local ws (v2026.3.22 regression)
- **#52837** - `openclaw system event` CLI never completes WebSocket challenge-response handshake (macOS, 2026.3.13)
- **#52819** - Gateway heartbeat scheduler starts but never fires cycles after gateway restart (v2026.3.13)
- **#52766** - Gateway WebSocket handshake timeout on local loopback (non-systemd env) breaks all CLI RPC commands
- **#52749** - CLI can't connect to gateway
- **#52265** - CLI `openclaw cron/gateway` commands fail with "handshake timeout" on v2026.3.13
- **#52208** - macOS LaunchAgent can be removed and left not loaded after failed `openclaw gateway start`
- **#51987** - Local gateway websocket handshake times out on 127.0.0.1:18789 and closes before connect
- **#51879** - CLI gateway handshake timeout on WSL2 - 2026.3.13 regression
- **#51438** - CLI to Gateway WebSocket connections timeout in v2026.3.12+ (regression)
- **#50438** - 2026.3.13: devices commands fail with gateway closed (1000) while gateway status shows RPC probe ok
- **#50380** - CLI WebSocket handshake timeout when gateway is running (v2026.3.13, Windows)
- **#50074** - Gateway restart fails - stale process misdetection
- **#49338** - 2026.3.13 npm package missing dist/gateway.js - Gateway fails to start
- **#41804** - Gateway persistent stale processes on Windows (scheduled task runtime)
- **#41591** - `gateway stop` on Windows does not terminate running process
- **#36585** - TLS null dereference crash during socket reconnection under concurrent load
- **#34539** - structuredClone FATAL ERROR in orphaned subagent reconciliation after unclean exit
- **#24178** - Doctor check blocks indefinitely without TTY - hangs headless/automated deployments
- **#22972** - Health check times out on slow startups

### Secrets/Auth
- **#52794** - Client request session.list error: scope operator.read do not have (v2026.3.22)
- **#52488** - `openclaw status --all` and `security audit --deep` show "missing scope: operator.read" even after full operator pairing
- **#51911** - Anthropic setup-token onboarding path has multiple failure modes (docs gap, credential propagation, multi-agent sync)
- **#51887** - gateway-client / TUI loses operator.read and breaks openclaw status --all
- **#51516** - openclaw devices/* and gateway RPC fail locally with pairing/operator scope mismatch on healthy loopback gateway (2026.3.13)
- **#51495** - CLI/operator RPC stays scope-empty on local auto-approved pairing (2026.3.13)
- **#51474** - Control UI on local loopback still requires pairing in 2026.3.13, despite docs saying local connections auto-approve
- **#51396** - clearUnboundScopes strips operator scopes unconditionally for non-local token-auth clients
- **#51008** - 2026.3.13 local loopback regression: operator.read failures and gateway closed (1000) on CLI commands
- **#49725** - CLI auth regression on 2026.3.13: intermittent missing scope: operator.read and websocket close
- **#49885** - google-vertex fails with "No credentials found for profile" even when ADC is valid
- **#49138** - OAuth flow missing api.responses.write scope - blocks GPT-5.4 in subagents
- **#37303** - Onboarding crashes with exec secret provider - `getStatus()` eagerly resolves SecretRef tokens
- **#37123** - Azure OpenAI not appearing during onboarding wizard
- **#12517** - [SEC] All 31 plugins share single Node.js process - lateral movement across plugins
- **#12518** - [SEC] All plugin credentials in shared `process.env` - no isolation between channels
- **#11829** - [SEC] API keys leak to LLM via tool outputs, error messages, system prompts

### Channels
- **#53162** - WhatsApp cron delivery always fails with "No active WhatsApp Web listener" despite channel being connected
- **#53140** - WhatsApp is taken over by OpenClaw and automatically replies to all messages
- **#52914** - WeChat QR code scan shows blank/white screen (QCLAW_USER_GUID and QCLAW_USER_ID not injected) (v2026.3.22)
- **#52876** - v2026.3.22 webui won't open, Feishu official plugin load error
- **#52778** - WeCom DM message isolation failure - different users' DMs routed to same session
- **#52773** - WhatsApp listener dies after upgrade - "No active WhatsApp Web listener" on all outbound (resolved by reverting to v2026.03.11)
- **#52763** - WhatsApp groupPolicy "allowlist" bypassed - agent replies in non-allowlisted group
- **#52729** - hooks.internal.enabled causes LINE webhook 404 (v2026.3.13)
- **#52649** - Model switch in control panel does not apply to Feishu messages for same session
- **#52626** - Multi-account Feishu tools always use accounts[0] credentials
- **#52615** - Discord `allowFrom` Web UI double-escaping IDs
- **#52603** - Telegram direct sessions return 400 "model not supported" for github-copilot models, while CLI sessions succeed
- **#52574** - gateway/ws RPC send path broken after 3.13 upgrade - "No active WhatsApp Web listener" despite healthy gateway
- **#52454** - Telegram:direct does not send thread back to telegram when you talk in the GUI
- **#52328** - Telegram extension silently fails with no guidance when OPENCLAW_EXTENSIONS=telegram is not set
- **#52286** - Message tool sends files to DM instead of staying in Telegram topic
- **#52167** - WhatsApp media sends fail on old-style group JIDs
- **#52081** - Feishu failed to load: TypeError: buildChannelConfigSchema is not a function (v2026.3.22)
- **#51815** - Telegram plugin fails to load
- **#51810** - Doctor/update fails when Telegram bot token uses file-based SecretRef (2026.3 regression)
- **#51728** - Control UI / WebChat attachments not delivered to agent in v2026.3.13
- **#51716** - Signal group messages silently dropped on Node 24 - SSE fetch fails with TypeError
- **#51558** - WhatsApp Web listener running but inaccessible to message handler
- **#51245** - Telegram slash sessions still resolve to channel=(unknown), causing elevated allowFrom checks to fail on 2026.3.13
- **#51190** - Discord channel can show running=true while connected=false, new DMs stop reaching agent until restart
- **#51158** - Matrix plugin syncs but never routes inbound messages to agent (events silently dropped)
- **#51143** - Multi-account Telegram: bot.on("message") does not fire for group messages on non-default account
- **#51111** - WhatsApp QR login appears linked briefly, then becomes disconnected with 401 / device_removed
- **#51084** - Can read Feishu documents in terminal main, but not after integrating Feishu
- **#50999** - Telegram polling enters repeated stall/restart loop on macOS in 2026.3.13
- **#50450** - Telegram duplicate message sending bug (restart causes resend)
- **#50424** - Telegram messages sent twice after channel restart (regression)
- **#50326** - Telegram `replyToMode: all` does not reply to triggering message in group/forum topics
- **#50184** - Telegram DM reply preview forced to message transport instead of draft (regression)
- **#50174** - Windows: Telegram polling stalls every ~107s (UND_ERR_CONNECT_TIMEOUT) + Discord disconnects
- **#41581** - Telegram DM partial streaming regressed from smooth sendMessageDraft to choppy editMessageText
- **#49990** - Discord proxy does not proxy REST API requests - guild resolve fails behind HTTP proxy
- **#49411** - WhatsApp Web listener Map duplicated across bundles - sends always fail
- **#50208** - No active WhatsApp Web listener on outbound despite connected status (2026.3.13)
- **#50377** - Zalo Bot API channel stops on startup with getZaloRuntime undefined in v2026.3.13
- **#50266** - Feishu channel silently fails with "replies=0" on valid Gemini API call
- **#49576** - Feishu messages crash gateway in v2026.3.13
- **#49412** - Feishu plugin duplicate id warning on startup
- **#50127** - Feishu multi-group binding routing fails under concurrency
- **#50306** - LINE channel binding lost daily
- **#49806** - iMessage channel plugin fails to load: Cannot find package 'openclaw'
- **#41576** - Channel leaks `[[reply_to:ID]]` tags into visible message text
- **#36687** - `session.dmScope` reset to "main" causes cross-channel reply leakage

### Agent Runtime
- **#53233** - Anthropic rate limit cooldown propagates to independent google-vertex fallback provider
- **#52708** - ACP `mode: "run"` sessions leave orphan processes and lose completion events
- **#52677** - web_search/web_fetch tools not available to agent with built-in Gemini provider
- **#52612** - Full cacheWrite after using subagents (Anthropic)
- **#52604** - repairToolUseResultPairing misses orphaned tool IDs from MiniMax/OpenAI-compat models - underscore-stripping creates ID mismatch
- **#52559** - Agent writes do not persist to host workspace even with sandbox off
- **#52405** - exec/system.run fails with "approval requires an existing canonical cwd" even for pwd
- **#52362** - claude-cli backend: assistant responses not persisted to session .jsonl, webchat history lost on reload
- **#52317** - System prompt completely missing after /new - workspace files not injected, silent failure
- **#51774** - Google provider adapter: streaming flag causes 400 + empty required arrays rejected by schema validator
- **#51743** - Google provider: usageMetadata not mapped to usage.input/output - all Gemini calls record 0 tokens
- **#51742** - OpenClaw not passing tools definition to nemotron
- **#51669** - Web chat crashes OpenClaw after sending an image, corrupting session file
- **#51593** - HTTP 400: "tool call id exec:26 is duplicated" with moonshot/kimi-k2.5 in WhatsApp group chats
- **#51530** - Cron job agentTurn model override to Google/Gemini failing, defaulting to Anthropic/Claude
- **#51505** - Thinking stream not forwarded via WebSocket agent events during streaming
- **#51083** - ReferenceError: Cannot access 'ANTHROPIC_MODEL_ALIASES' before initialization on every CLI command
- **#51062** - Subagent failed to execute or produce output
- **#51036** - Agent completes with payloads [] and zero usage on custom OpenAI-compatible provider
- **#50401** - DeepSeek-V3 (SiliconFlow): 400 error on tool calls - "messages in request are illegal"
- **#50178** - 400 thinking enabled but reasoning_content missing in assistant tool call message
- **#50107** - NVIDIA provider sends Anthropic-style message format to OpenAI-compatible API
- **#50094** - Compactor preserves orphaned tool_use blocks, causing Anthropic 400 on model switch
- **#50017** - Automatic model fallback does not recover cleanly from invalid primary model ID
- **#49519** - openai-codex-responses provider crashes agent runtime with ReferenceError (ANTHROPIC_MODEL_ALIASES)
- **#41707** - After upgrade, tools enter infinite repeat loop (regression)
- **#41291** - Agent enters infinite retry loop when tool calls fail
- **#41335** - Session tool registry corruption - tools work once then become "not found"
- **#36520** - Runtime events mutate system prompt every turn, invalidating prompt cache (silent cost multiplier)
- **#36634** - `agents_list` tool returns only "main" despite multiple agents configured

### Skills
- **#52073** - Agent becomes completely unresponsive during Skill installation and does not report task completion
- **#35272** - Sub-agents cannot access shared skills from `~/.openclaw/skills/` - directly impacts `npx skills add -g` (3 upvotes)
- **#29122** - Workspace skills silently not loading (no error, valid SKILL.md)
- **#21709** - `skills.allowBundled: []` allows all instead of blocking all (semantics bug)
- **#49427** - skills.entries apiKey file SecretRef passes audit but remains unresolved during embedded run startup

### Cron
- **#53162** - WhatsApp cron delivery always fails with "No active WhatsApp Web listener" despite channel being connected
- **#52975** - sessionTarget method of using custom sessionID in cron scheduled task does not work
- **#52806** - Cron: Isolated sessions not executing
- **#52563** - Cron task configuration error causes Gateway crash
- **#52271** - sessions_send from cron/heartbeat context deadlocks on nested lane (maxConcurrent: 1) - regression from PR #45459
- **#51871** - Control UI: Cron jobs not displayed in dashboard (2026.3.13)
- **#51557** - Cron isolated session skill and browser compatibility issues
- **#51530** - Cron job agentTurn model override to Google/Gemini failing, defaulting to Anthropic/Claude
- **#51498** - openclaw cron list/status and openclaw health --json timeout against local gateway while scheduler still appears to run jobs
- **#50303** - Cron jobs created by CLI but do not materialize from Telegram/WebChat conversation
- **#50170** - Cron reports status "error" despite successful Discord delivery (regression)
- **#50169** - `openclaw cron` command causes gateway restart failure (lock timeout)
- **#49258** - Cron job state inconsistency - lastDelivered: true but lastRunStatus: error
- **#49124** - Cron error state accumulates during host sleep/connectivity loss

### TUI / Control UI
- **#53115** - No visual feedback when sending messages in TUI
- **#53096** - Control UI assets not found on v2026.3.22 (multiple reports: #53135, #52880, #52820)
- **#52565** - Control UI event listener registration failure in 2026.3.13 - buttons non-functional
- **#52511** - Control UI session intermittently loses browser control permission (gateway closed 1000)
- **#52494** - ui:build fails on fresh clone due to --prod removing vite
- **#52463** - Control UI session compaction incorrectly shows system internal messages in user instruction box
- **#52282** - Windows pnpm ui:build fails (path with spaces)
- **#52105** - Control UI /think command crashes
- **#52089** - Control UI slash command menu position bug
- **#51780** - UI running indicator stuck after subagent completion on remote server
- **#51685** - Control UI freezes with high CPU when switching sessions via dropdown menu
- **#51507** - WebChat/Control-UI context calculation inaccurate - shows 100% before actual limit reached
- **#49918** - TUI /new stopped emitting hook-visible new-session behavior (regression)
- **#37243** - TUI replies routed to Telegram instead of TUI (100% repro with Telegram configured)
- **#37168** - TUI assistant replies not displayed (`--deliver` flag ignored)

## Breaking Changes & Regressions

### Breaking in v2026.3.22 (current)
- Control UI assets missing from npm package - dozens of reports (#53096, #53135, #52880, #52820, #52848 - many now fixed by PR #52839, #53081)
- WhatsApp plugin missing on clean install (#53138 - fixed by PR #53060)
- Matrix Plugin API version mismatch (#52899 - 13 upvotes, still open)
- Feishu plugin buildChannelConfigSchema not a function (#52081)
- Missing extension runtime API entry points in package.json (#53046)
- Model switch from UI generates wrong prefix (#53031)
- WeChat QR code scan blank screen (#52914)

### Breaking in v2026.3.13 (still relevant in many installs)
- CLI auth intermittent: missing scope operator.read, websocket close 1000/1006 (#49725, #50438, #52488, #52794)
- WebSocket handshake timeout breaks all CLI commands (#51438, #51987, #52766, #53168)
- Telegram messages sent twice after channel restart (#50424, #50450)
- Feishu channel crashes gateway (#49576) and silently fails on valid API calls (#50266)
- WhatsApp Web listener Map duplicated - sends always fail (#49411)
- Gateway restart fails from stale process misdetection (#50074)
- npm package missing dist/gateway.js (#49338)
- Plugin tools not inherited by subagent runtime (#50131)
- Slack Socket Mode broken (#52527)

### Breaking in v2026.3.8 (still relevant in some installs)
- Google model provider prefix not stripped - 404 on all Google API calls (#41249)
- Tool validation errors - file read/write broken (#41209)
- Telegram DM streaming regressed to choppy editMessageText (#41581)

### Breaking Guardrails (still in effect)
- **PR #35094** - `gateway.auth.mode` mandatory when both `gateway.auth.token` and `gateway.auth.password` configured
- **PR #36567** - `plugins.entries.<id>.hooks.allowPromptInjection` required for plugins using prompt mutation hooks

### Active Regressions
| Issue | Summary |
|-------|---------|
| #53233 | Anthropic rate limit cooldown propagates to google-vertex fallback |
| #53226 | Windows exec launcher broken - all commands quoted as PS string literals |
| #53169 | Dashboard upgrade fails silently - gateway entrypoint renamed without service migration |
| #53168 | CLI commands crash gateway via WebSocket handshake timeout |
| #53096 | Control UI assets not found (v2026.3.22) |
| #53067 | CLI cannot connect to local ws (v2026.3.22) |
| #53046 | Missing extension runtime API entries in package.json (v2026.3.22) |
| #53031 | Model switch from UI generates wrong prefix (v2026.3.22) |
| #52899 | Matrix Plugin API version mismatch (v2026.3.22, 13 upvotes) |
| #52876 | v2026.3.22 webui won't open, Feishu plugin load error |
| #52794 | Client scope operator.read missing (v2026.3.22) |
| #52773 | WhatsApp listener dies after upgrade |
| #52729 | hooks.internal.enabled causes LINE webhook 404 |
| #52677 | web_search/web_fetch tools not available with Gemini provider |
| #52604 | repairToolUseResultPairing misses orphaned tool IDs |
| #52574 | WhatsApp WS RPC send path broken after 3.13 upgrade |
| #52527 | 2026.3.13 breaks Slack Socket Mode |
| #52488 | operator.read missing even after full pairing |
| #52482 | Control UI provider prefix handling wrong |
| #52433 | ACPX plugin version pinning broken |
| #52405 | exec/system.run "approval requires canonical cwd" even for pwd |
| #52271 | sessions_send from cron deadlocks on nested lane |
| #52081 | Feishu buildChannelConfigSchema not a function |
| #51879 | CLI gateway handshake timeout on WSL2 |
| #51871 | Control UI cron jobs not displayed |
| #51810 | Doctor/update fails with file-based SecretRef Telegram tokens |
| #51780 | UI running indicator stuck after subagent completion |
| #51716 | Signal group messages dropped on Node 24 |
| #50450 | Telegram duplicate messages (channel restart resend) |
| #50438 | devices commands fail with gateway closed (1000) in v2026.3.13 |
| #50424 | Telegram messages sent twice after restart |
| #50401 | DeepSeek-V3 400 on tool calls |
| #50352 | acpx fails to spawn Claude CLI on Windows |
| #50332 | Automatic spaces in mixed CJK-English text cause path errors |
| #50266 | Feishu silent failure on valid Gemini calls |
| #50211 | Shared CI regressions failing unrelated PRs |
| #50197 | Control UI model dropdown prefix reset failure |
| #50184 | Telegram DM reply forced to message transport |
| #50178 | reasoning_content missing causes 400 |
| #50170 | Cron reports error despite successful delivery |
| #50131 | Plugin tools don't inherit subagent runtime |
| #50074 | Gateway restart stale process misdetection |
| #49990 | Discord proxy doesn't proxy REST API calls |
| #49952 | WhatsApp session not restored |
| #49725 | CLI auth intermittent scope/websocket issues |
| #49666 | Telegram proxy config wiped on gateway restart |
| #49519 | openai-codex-responses crashes with ReferenceError |
| #49411 | WhatsApp listener Map duplicated across bundles |
| #41707 | Tools infinite repeat loop after upgrade |
| #41581 | Telegram DM streaming regression (choppy edits) |
| #41335 | Session tool registry corruption |
| #41291 | Agent infinite retry loop on tool failure |
| #41249 | Google model prefix not stripped (404s) |
| #41209 | Tool validation errors in v2026.3.8 |

### Config Migration Hazards
- **#49666** - Telegram proxy config silently wiped on restart
- **#24008** - Unknown config keys silently wipe entire section on restart
- **#35957** - Stale keys from older versions block startup on newer
- **#51453** - config_guard falsely flags models.providers.zai.models token refresh as breaking change every hour
- **PR #35094** - Must set `gateway.auth.mode` explicitly if both token+password present
- **PR #36567** - Must set `hooks.allowPromptInjection` for plugins with prompt hooks

## Plugin/Extension/Config Known Issues

### Plugin Loading
- CJS dependencies fail under jiti ESM loader (#12854) - fundamental limitation
- Native bindings (sqlite3) broken under jiti (#36377)
- Symlinked plugin dirs silently skipped (#36754)
- pnpm global install rejects bundled plugin manifest paths (#28122)
- Split-load singleton state duplication across module graphs (fixed: #50418, #50431)
- Plugin tools not inherited by subagent runtime scope (#50131)
- Custom plugin tools invisible to sandboxed sessions (#41757)
- Plugin auto-enable changes fail to persist on startup (#50323)
- Duplicate plugin loading warnings with installed extensions (#50382)
- Missing extension runtime API entries in npm package (#53046 - v2026.3.22)
- ACPX version pinning broken - always reverts to 0.1.16 (#52433)
- Non-provider registrations during snapshot loads causing issues (fixed: PR #52938)

### Skills
- Sub-agents cannot see globally installed skills (#35272) - impacts `~/.openclaw/skills/` approach
- Skills can silently fail to load with no error (#29122)
- `skills.allowBundled: []` semantics inverted (#21709)
- Skills entries env vars not propagated to sandbox subprocess (fixed: #50412)
- apiKey SecretRef unresolved during embedded run startup (#49427)
- Agent becomes unresponsive during skill installation (#52073)

### Channel Plugin Registration
- Slack ESM interop crash: "App is not a constructor" (#50441)
- Slack Socket Mode broken on v2026.3.13 (#52527)
- WhatsApp listener Map duplicated across bundles (#49411)
- WhatsApp listener dies after upgrade - reverted to v2026.3.11 works (#52773)
- WhatsApp groupPolicy "allowlist" bypassed (#52763)
- Feishu duplicate registration warnings/crashes (#49412, #49576)
- Feishu multi-group binding routing fails under concurrency (#50127)
- Feishu registers all tools twice (#52572)
- Feishu buildChannelConfigSchema not a function in v2026.3.22 (#52081)
- Multi-account Feishu tools always use accounts[0] (#52626)
- Matrix Plugin API version mismatch after v2026.3.22 upgrade (#52899)
- Matrix plugin syncs but never routes inbound messages (#51158)
- Zalo getZaloRuntime undefined on startup (#50377)
- iMessage "Cannot find package 'openclaw'" (#49806)
- Signal group messages silently dropped on Node 24 (#51716)
- LINE webhook 404 with hooks.internal.enabled (#52729)
- LINE channel binding lost daily (#50306)
- Telegram plugin fails to load (#51815)
- Discord channel running=true while connected=false (#51190)

## Recent Impactful PRs (last 30 days)

| PR | Title | Area |
|---|---|---|
| #53212 | fix(anthropic): split system prompt into static/dynamic blocks for stable cache prefix | Agents |
| #53211 | fix(auth): stop live auth store writes from reverting fresh tokens | Auth |
| #53187 | Doctor: prune stale plugin allowlist and entry refs | Plugins |
| #53182 | feat: add adaptive policy feedback subsystem with gateway integration | Gateway |
| #53165 | Fix workspace skill grouping in Control Panel | UI |
| #53146 | fix(hooks): resolve session key fallback for message:sent in group deliveries | Hooks |
| #53127 | fix(subagents): recheck timed-out announce waits | Agents |
| #53111 | fix(memory): bootstrap lancedb runtime on demand | Memory |
| #53110 | Fix Control UI operator.read scope handling | Auth/UI |
| #53081 | Fix packaged Control UI asset lookup | Packaging |
| #53078 | fix(openai-codex): bootstrap proxy on oauth refresh | Agents |
| #53072 | fix(discord): return explicit auth replies for native commands | Discord |
| #53065 | fix: relay ACP parent completions reliably | Agents |
| #53060 | fix: keep whatsapp bundled in default npm builds | Packaging |
| #53055 | fix(gateway): guard openrouter auto pricing recursion | Gateway |
| #53054 | fix(mistral): repair max-token defaults and doctor migration | Config |
| #53020 | Agents: fix runtime web_search provider selection | Agents |
| #53017 | fix(clawhub): resolve auth token for skill browsing | Skills |
| #53001 | fix(reply): preserve debounced followup ordering | Telegram |
| #52998 | fix(telegram): preserve inbound debounce order | Telegram |
| #52991 | fix(plugins): unblock Discord/Slack message tool sends and Feishu media | Plugins |
| #52988 | fix(channels): preserve external catalog overrides | Channels |
| #52979 | feat(plugins): subagent enhancements - abort, structured output, dispatch fixes | Plugins |
| #52978 | feat(whatsapp): support native @mentions in outbound group replies | WhatsApp |
| #52969 | Packaging: include optional bundled plugins in npm packs | Packaging |
| #52964 | fix(config): keep built-in channels out of plugin allowlists | Config |
| #52961 | fix(agents): preserve anthropic thinking block order | Agents |
| #52918 | fix: add Telegram polling watchdog; reduce gateway startup memory | Telegram |
| #52917 | fix: null-guard Vertex AI ADC init; fix tool call mismatch for local LLMs | Agents |
| #52916 | fix: skip repeated workspace file injection after first turn | Agents |
| #52913 | fix(release): preserve shipped channel surfaces in npm tar | Packaging |
| #52862 | fix: ensure cron isolated sessions are truly independent | Cron |
| #52839 | fix(packaging): add Control UI build verification to prevent broken releases | Packaging |
| #52629 | feat(web-search): add DuckDuckGo bundled plugin | Plugins |
| #52617 | feat(web-search): add Exa as bundled web search plugin | Plugins |
| #52552 | fix(image): deprecate legacy skill and clarify auth | Agents |
| #52513 | fix(gateway): pass process.env in status command probe auth | Gateway |
| #52508 | fix(exec): return plain-text tool result on failure instead of raw JSON | Exec |
| #52489 | Reply: fix generated image delivery to Discord | Discord |
| #52461 | feat(telegram): add asDocument param to message tool | Telegram |
| #52428 | fix: sweep stale chatRunState buffers for stuck runs | Gateway |
| #52387 | fix(gateway): harden first-turn startup readiness | Gateway |
| #52326 | fix(gateway): trim startup plugin imports | Gateway |
| #52228 | fix: ensure env proxy dispatcher before MiniMax and OpenAI Codex OAuth flows | Agents |
| #52171 | fix: pass clientTools to runEmbeddedAttempt in /v1/responses agent path | Gateway |
| #52082 | perf(inbound): trim cold startup import graph | Gateway |
| #51951 | feat(usage): improve usage overview styling and localization | UI |
| #51924 | feat(ui): add multi-session selection and deletion | UI |
| #51795 | fix(status): recompute fallback context window | Agents |
| #51502 | feat(telegram): auto-rename DM topics on first message | Telegram |
| #51324 | feat(gateway): persist webchat inbound images to disk | Gateway |
| #51191 | feat: add context engine transcript maintenance | Agents |
| #50688 | fix(sessions): update sessionFile after compaction rotates sessionId | Gateway |
| #50431 | fix(plugins): share command registry across module graphs | Plugins |
| #50418 | fix(plugins): share split-load singleton state | Plugins |
| #50412 | fix(exec): propagate skills.entries.env vars into sandbox subprocess | Exec |
| #50405 | feat(gateway): add default reasoning config, defaulting to off | Gateway |
| #50386 | fix(macos): align exec command parity | macOS |
| #50212 | fix: isolate CLI startup imports | CLI |
| #50167 | Channels: stabilize lane harness and monitor tests | Channels |
| #50155 | Telegram: stabilize pairing/session/forum routing and reply formatting tests | Telegram |
| #50124 | fix(exec): only kill PTY on forced exit to avoid PID-recycle hazard | Exec |
| #50097 | fix: avoid killing current gateway pid in stale-restart retry path | CLI |
| #50092 | fix: persist outbound sends and skip stale cron deliveries | Cron |
| #50062 | fix(plugins): preserve singletons in source runtime shims | Plugins |
| #50058 | Stabilize plugin loader and Docker extension smoke | Plugins |
| #49997 | Discord: enforce strict DM component allowlist auth | Discord |
| #49995 | Matrix: make onboarding status runtime-safe | Matrix |
| #49941 | feat: update default context window to 1M tokens for Claude Opus/Sonnet 4.6 | Models |
| #49702 | fix(security): block build-tool and glibc env injection in host exec sandbox | Security |
| #49611 | fix: generalize api_error detection for fallback model triggering | Agents |
| #49555 | Plugin SDK: restore read-only directory inspection seam | Plugin SDK |
| #49551 | Image generation: native provider migration and explicit capabilities | Agents |
| #49542 | Plugin SDK: guard package subpaths and fix Twitch setup export | Plugin SDK |
| #49533 | fix(plugins): add missing secret-input-schema build entry and Matrix runtime export | Plugins |
| #49513 | fix: add docs hint for plugin override trust error | Gateway |
| #49490 | plugins: dist node_modules symlink + config raw-toggle UI fix | Plugins |
| #49454 | Image generation: add fal provider | Agents |
| #49200 | feat: add Tavily as a bundled web search plugin | Plugins |
| #48842 | feat(telegram): support custom apiRoot for alternative API endpoints | Telegram |
| #48762 | feat: add deepseek as builtin provider | Agents |
| #45489 | fix: prevent delivery-mirror re-delivery and raise Slack chunk limit | Slack |
| #43356 | feat: add anthropic-vertex provider for Claude via GCP Vertex AI | Agents |
| #43215 | Usage: include reset and deleted session archives | Gateway |
| #41021 | feat(compaction): truncate session JSONL after compaction to prevent unbounded growth | Agents |
| #40700 | fix(subagent): include partial progress when subagent times out | Agents |
| #40126 | feat(memory): pluggable system prompt section for memory plugins | Memory |
| #38805 | feat: notify user when context compaction starts and completes | UX |

## Closed Since Last Refresh (previously tracked)
- **#50315** - Firecrawl plugin missing in openclaw@2026.3.13 npm package - FIXED (now included via packaging fixes)
- **#41925** - No session created, no runs recorded - FIXED
- **#41979** - Cron "Run Now" enqueues but never executes - FIXED
- **#37375** - Discord fetch failure crashes gateway - FIXED
- **#41798** - Cron isolated session not executing in v2026.3.8 - FIXED
- **#41930** - Control UI WebSocket reconnect loses gateway token - FIXED

## Dev Gotchas (synthesized)

- **v2026.3.22 has major packaging regressions** - Control UI assets missing from npm package (dozens of reports), WhatsApp plugin missing on clean install (fixed by PR #53060), Matrix Plugin API version mismatch (#52899, 13 upvotes), Feishu buildChannelConfigSchema not a function (#52081). Extension runtime API entry points missing (#53046). Test carefully after upgrade.
- **v2026.3.13 has significant channel regressions** - Telegram duplicate messages (#50424, #50450), Feishu crashes (#49576), WhatsApp listener Map duplication (#49411), Slack ESM interop crash (#50441), Slack Socket Mode broken (#52527). Test channel connectivity thoroughly after upgrade.
- **WebSocket handshake timeout is a pervasive regression** - CLI-to-gateway WebSocket connections timeout across v2026.3.12+ on macOS, Windows, WSL2, and Linux (#51438, #51879, #51987, #52265, #52766, #53067, #53168). Multiple independent reports. Affects `openclaw status`, `openclaw cron`, `openclaw devices/*`, and all RPC commands. No definitive fix yet.
- **Model selector prefix bug is widespread** - At least 12 independent reports of Control UI model picker sending wrong provider prefix when switching models (#53031, #52551, #52482, #52311, #52233, #52173, #51824, #51809, #51608, #51334, #51306, #51139, #50293, #50197, #50050). Affects all UIs. Model switching may silently send wrong model ref.
- **operator.read scope regression is systemic** - CLI and Control UI lose operator.read scope on local loopback connections despite auto-approve being documented (#52794, #52488, #51887, #51516, #51495, #51474, #51396, #51008, #49725). Fixed partially by PR #53110 and #53211 but not fully resolved.
- **Plugin singleton state can fragment across module graphs** - Fixed by #50418 and #50431, but any plugin relying on shared state (hook runners, registries) must be aware. Extensions duplicated across bundles get separate instances unless Symbol-based singletons are used.
- **Plugin tools are invisible to sandboxed and subagent sessions** (#41757, #50131) - Tools registered by plugins do not inherit gateway subagent runtime. Must remove sandbox or ensure tools are in the gateway-level tools profile.
- **Sub-agents can't see globally installed skills** (#35272) - `~/.openclaw/skills/` skills invisible to sub-agents. Directly affects AgentBox's `npx skills add -g` approach. 3 upvotes, still no fix.
- **Config keys still silently wipe sections** (#24008) - Unknown keys cause entire config section reset on restart. Validate config carefully across version upgrades. Back up before upgrading.
- **config_guard false positives** (#51453) - zai provider token refresh falsely flagged as breaking change every hour.
- **Prompt cache invalidated every turn** (#36520) - Runtime events mutate system prompt, forcing cache miss. Silent cost multiplier on all VMs. Still open. PR #53212 (split static/dynamic blocks) may help for Anthropic.
- **Shared process model = no plugin isolation** (#12517, #12518) - All plugins share one Node.js process. Wallet keys in x402 plugin accessible to any other plugin.
- **Headless startup pitfalls** - Doctor check hangs without TTY (#24178), health check times out on slow starts (#22972). Both relevant to cloud-init boot.
- **Plugin prompt hooks need explicit allowlist** (PR #36567) - Plugins using `before_prompt_build`/`before_agent_start` blocked unless `hooks.allowPromptInjection` is set.
- **`gateway.auth.mode` now mandatory** (PR #35094) - Startup fails if both token+password configured without explicit mode.
- **Cron delivery reporting is unreliable** - Reports error despite successful delivery (#50170), state inconsistency (#49258), isolated sessions not executing (#52806), model override not respected (#51530). Don't trust cron status as ground truth.
- **Claude Opus/Sonnet 4.6 default context window updated to 1M** (PR #49941) - Affects default token limits in new sessions.
- **Gateway stale process detection is broken** (#50074) - Restart may fail or kill the wrong PID. Workaround: manually check process before restart.
- **Skills env vars now propagated to sandbox** (PR #50412) - `skills.entries.<skill>.env` vars are injected into sandbox subprocess environment. New capability.
- **Default reasoning config added** (PR #50405) - Gateway now has `defaultReasoning` config, defaulting to off. May affect agents expecting reasoning to be enabled by default.
- **DeepSeek now a builtin provider** (PR #48762) - No longer requires custom provider config. Directly supported.
- **DuckDuckGo and Exa added as bundled web search plugins** (PRs #52629, #52617) - Tavily also added (#49200). Three new web search options.
- **Subagent enhancements shipped** (PR #52979) - Abort support, structured output, dispatch fixes. New `api.runtime.agent.abort` API.
- **Anthropic thinking block order preserved** (PR #52961) - Fixes out-of-order thinking blocks that could cause API errors.
- **Auth token store race condition fixed** (PR #53211) - Live auth store writes were reverting fresh tokens.
- **Telegram debounce order fixed** (PRs #53001, #52998) - Followup messages now preserve ordering.
- **Ollama oversized context window** (#52206) - v2026.3.13 still sends 262k context to Ollama ignoring configured lower limits.
- **Google provider usageMetadata not mapped** (#51743) - All Gemini calls record 0 tokens. No usage tracking for Google models.
