# OpenClaw GitHub Context
> Last refreshed: 2026-04-07T12:00:00Z

## Open Bugs (critical for development)

### Plugin System
- **#62511** - External plugins fail to load on 2026.4.5: normalizeAccountId is not a function (REGRESSION)
- **#62372** - RangeError: Maximum call stack size exceeded - google/minimax plugins fail to load on Windows (REGRESSION)
- **#62320** - CLI Stack Overflow in loadOpenClawPlugins / recordPluginError on 2026.4.5 (REGRESSION)
- **#62347** - memory-core plugin fails to load during onboard: "Unable to load plugin public-surface runtime" (REGRESSION)
- **#62277** - Feishu bundled plugin fails to load: missing register/activate export (REGRESSION)
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
- **#62472** - Context token / context window persisted incorrectly when multiple providers share the same model id
- **#62470** - google-vertex/gemini-3.1-pro-preview empty replies due to incorrect thinkingConfig disable path
- **#62405** - Control UI dropdown uses wrong value for OpenRouter models (missing openrouter/ prefix)
- **#62390** - buildQualifiedChatModelValue ignores provider when model already contains slash (REGRESSION)
- **#62388** - Comfy config path mismatch: plugins.entries.comfy.config accepted, runtime requires models.providers.comfy
- **#58932** - normalizeHyphenSlug strips all CJK characters, breaking group display names for non-Latin languages
- **#58880** - OpenRouter: "400 Reasoning is mandatory for this endpoint and cannot be disabled" (REGRESSION)
- **#58355** - Failed to set model for Ollama - model not allowed
- **#58302** - /reset and /new commands do not reset model to default
- **#58289** - Non-main agent may miss models.json and fail with "Unknown model" when provider plan is empty
- **#58087** - SecretRef-backed model provider headers sent as literal "secretref-managed" in API requests (REGRESSION)
- **#52551** - Dashboard model selector concatenates wrong provider ID
- **#49666** - Telegram proxy config wiped on gateway restart
- **#24008** - Unrecognized config keys silently wipe and reset entire section on restart
- **#36792** - Gateway promises "best-effort config" on invalid config but exits instead

### Gateway Startup
- **#62691** - `message send` crashes with `ERR_INTERNAL_ASSERTION` in v2026.4.5 (REGRESSION)
- **#62564** - ERR_UNSUPPORTED_ESM_URL_SCHEME on Windows (REGRESSION in v2026.4.5)
- **#62502** - ERR_UNSUPPORTED_ESM_URL_SCHEME on Windows non-C drives (REGRESSION)
- **#62446** - Install and first configuration fails: Cannot find module '@buape/carbon'
- **#62430** - openclaw tui crashes with Maximum call stack size exceeded during schema compilation (REGRESSION)
- **#62410** - Maximum call stack size exceeded during JSON Schema validation (REGRESSION)
- **#62408** - openclaw onboard --install-daemon ERR_UNSUPPORTED_ESM_URL_SCHEME on Windows (REGRESSION)
- **#62400** - CLI Local Commands Hang Indefinitely in OpenClaw 4.5 (REGRESSION)
- **#62356** - CLI enters CPU 100% infinite loop on unknown/unregistered subcommands (v2026.4.5)
- **#62342** - Agent listener invoked outside active run causes Gateway crash
- **#62329** - Gateway segfaults on every message when session history contains a cached PNG image (REGRESSION)
- **#62326** - openclaw devices command unresponsive (REGRESSION)
- **#62285** - openclaw command hang and gateway service not working after upgrading to 2026.4.5 (REGRESSION)
- **#62302** - RangeError: Maximum call stack size exceeded on startup due to talk-voice invoking JITI AST compilation (REGRESSION)
- **#58956** - Pre-compaction memory flush leaks into chat UI and blocks the user's active turn in 2026.3.31 (REGRESSION)
- **#58807** - falling back to HTTP: ENETUNREACH (REGRESSION)
- **#58415** - ws-stream WebSocket connect fails with 500 and always falls back to HTTP
- **#58306** - Gateway process storm: KeepAlive + ThrottleInterval=1 causes 30+ zombie processes when port not released
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
- **#62546** - Canvas returns 401 Unauthorized on Windows despite correct token (v2026.4.5) (REGRESSION)
- **#62380** - Windows Node system.run completely non-functional - exec-approvals.sock never created (REGRESSION)
- **#58768** - Incompatible security approval config
- **#58687** - Security prompt is too long to approve, clicking "Allow All" is ineffective
- **#52488** - `openclaw status --all` shows "missing scope: operator.read" even after full pairing
- **#51911** - Anthropic setup-token onboarding path has multiple failure modes
- **#49885** - google-vertex fails with "No credentials found for profile" even when ADC is valid
- **#49138** - OAuth flow missing api.responses.write scope
- **#37303** - Onboarding crashes with exec secret provider
- **#12517** - [SEC] All 31 plugins share single Node.js process - lateral movement across plugins
- **#12518** - [SEC] All plugin credentials in shared `process.env` - no isolation
- **#11829** - [SEC] API keys leak to LLM via tool outputs, error messages, system prompts

### Channels
- **#62699** - ACP/acpx persistent sessions die with `queue owner unavailable`; Telegram topic-bound ACP issues
- **#62690** - Telegram 401 Unauthorized Error - Valid Token Not Accepted (REGRESSION)
- **#62670** - Agent listener invoked outside active run - concurrent WhatsApp + Telegram sessions
- **#62623** - v2026.4.5 regression: Slack DM file attachments no longer download to inbound (REGRESSION)
- **#62610** - Telegram channel missing from npm installs on macOS
- **#62580** - Response Contamination / Cross-Session Leakage
- **#62576** - Telegram approval/system messages broadcast to multiple authorized users (REGRESSION)
- **#62558** - QQBot channel - Framework slash commands (/new, /reset, /status) not working
- **#62551** - Agent is not being able to read files that were sent on Slack
- **#62498** - Media download failed in v2026.4.5 (re-occurrence of #32326) (REGRESSION)
- **#62324** - v2026.4.5 regression: non-main agents in Telegram multi-agent stop replying unless contextEngine=legacy (REGRESSION)
- **#62318** - Slack inbound images broken in 2026.4.5 - speech-core/runtime-api.js resolution failure (REGRESSION)
- **#62311** - Control UI completely blank on main branch: "process is not defined" (REGRESSION)
- **#58905** - Feishu(Lark) Webhook URL verification fails with 401 Invalid signature when encryptKey is set
- **#58884** - Numerous calls to statsig.anthropic.com when not using Claude/Anthropic models
- **#58781** - include_usage not auto-added to LLM calls, console stats broken (REGRESSION)
- **#58738** - ClawBot WeCom service account unresponsive after pairing (REGRESSION)
- **#58737** - Agent display name/avatar reverts to bot default on edited Slack messages (REGRESSION)
- **#58639** - Gmail to Telegram/Discord notifications stopped: /gmail-pubsub push endpoint broken
- **#58535** - Discord announce removing fields from input
- **#58523** - Slack multi-workspace: outbound works on second workspace but inbound DM replies never reach OpenClaw
- **#58514** - Google Chat: Space/Group messages silently ignored
- **#58408** - WhatsApp Inbound Works But Outbound CLI Fails With "No Active Listener"
- **#58402** - message tool "Operation aborted" + WhatsApp reconnect storm + xai-auth log spam
- **#58268** - Slack socket-mode mentions silently dropped as no-mention after stale-socket reconnect
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
- **#57731** - Discord plugin aggressively drops connections (stale-socket) causing delayed and duplicated messages (REGRESSION)
- **#57660** - Telegram polling stall detector fires too aggressively (110s), causes message delivery failures

### Agent Runtime
- **#62706** - Chrome MCP attach fails when OpenClaw passes both --browserUrl and --userDataDir
- **#62684** - Local Ollama agent pipeline times out with no provider logs on 2026.4.5
- **#62672** - Fallback chain propagates primary model's 429 error to secondary providers
- **#62614** - Retry storm can repeatedly resend oversized session context after timeouts/rate limits
- **#62604** - Control UI image paste injects massive base64 text into composer
- **#62580** - Cross-Session Leakage / Response Contamination
- **#62564** - ERR_UNSUPPORTED_ESM_URL_SCHEME on Windows (REGRESSION)
- **#62561** - Inline image attachments dropped before imageModel fallback fires
- **#62550** - browser snapshot --format ai returns role refs instead of numeric AI refs on 2026.4.5
- **#62541** - Cannot create new agent after enable dreaming config (REGRESSION)
- **#62533** - Model "Not Found" (404) errors when using a remote Ollama provider as a fallback
- **#62517** - edit tool fails with tilde paths, error broadcasts to Telegram (REGRESSION)
- **#62505** - Coding Agent never completes anything (worked in 2026.4.2) (REGRESSION)
- **#62282** - Ollama embedding broke in 2026.4.5 (REGRESSION)
- **#58962** - pdf tool / model not being used
- **#58880** - OpenRouter reasoning mandatory, cannot be disabled (REGRESSION)
- **#58842** - model hanging
- **#58631** - Haiku outputs with formatted tables/structured text crash webchat session
- **#58628** - Browser enabled and running, but browser tool is missing from agent tool list (REGRESSION)
- **#58599** - Edit tool schema mismatch: "edits" array in schema vs flat "oldText"/"newText" in implementation
- **#58553** - Long sessions (600+ messages) break with "invalid function call parameters"
- **#58442** - Model failover fails on Coding Plan quota 429 errors - infinite loop
- **#58363** - kimi web_search run error
- **#58358** - OpenClaw mishandles message_stop for KimiCodingPlan Anthropic format
- **#58235** - Gemini 3.1 Pro Preview via OpenAI-compat API missing thought_signature in tool_calls
- **#58189** - VLLM-deployed QWEN3-32B gets stuck in a loop
- **#57826** - v2026.3.28 agent systematically omits required tool parameters (REGRESSION)
- **#57821** - Cannot read properties of undefined (reading 'push') with third-party Anthropic-compatible provider
- **#57774** - Sub-agent session not properly exited, causing death loop
- **#57760** - Automatic model failover does not work when primary model hits rate limits
- **#57753** - anthropic-messages SSE state machine fails to reset between tool-use loop iterations (REGRESSION)
- **#57663** - MiniMax M2.7 persistent 408 timeouts not surfaced to user; fallback chain causes 4+ minute delays (REGRESSION)
- **#57654** - Unexpected event order: message_start before message_stop
- **#57626** - Model switch to unresponsive Ollama model cascades into infinite [object Object] loop, corrupts session
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
- **#58712** - memos-memory-guide skill shows disabled but works correctly - WSL path issue (REGRESSION)
- **#58319** - Support non-JSON SecretRef in skills entries apiKey
- **#52073** - Agent becomes completely unresponsive during Skill installation
- **#35272** - Sub-agents cannot access shared skills from `~/.openclaw/skills/`
- **#29122** - Workspace skills silently not loading
- **#21709** - `skills.allowBundled: []` allows all instead of blocking all

### Cron
- **#58927** - Cron jobs ignore payload.model and agentId, always resolving to default/main agent model
- **#58575** - --model flag on isolated cron jobs does not override session model (REGRESSION)
- **#58065** - Specified model for cron overridden by agent default (REGRESSION)
- **#57947** - Cron payload model override ignored - always resolves to agent default (REGRESSION)
- **#52975** - sessionTarget method of using custom sessionID in cron does not work
- **#52806** - Cron: Isolated sessions not executing
- **#52563** - Cron task configuration error causes Gateway crash
- **#52271** - sessions_send from cron/heartbeat deadlocks on nested lane
- **#51530** - Cron job agentTurn model override to Google/Gemini failing
- **#49258** - Cron job state inconsistency

### TUI / Control UI
- **#62604** - Control UI image paste injects massive base64 text into composer
- **#62418** - WebChat Control UI displays internal exec notifications in user-visible chat (REGRESSION)
- **#62411** - Gemma 4 thinking-off semantics broken in Control UI
- **#62371** - Control UI drag-and-drop images not attached to messages (REGRESSION)
- **#62311** - Control UI completely blank on main branch: "process is not defined" (REGRESSION)
- **#58694** - Can only chat in TUI mode
- **#58631** - Haiku outputs with formatted tables crash webchat session
- **#57964** - Repeated characters collapse when displayed in dashboard or TUI (REGRESSION)
- **#57822** - Web UI agent dropdown shows agent.id instead of identity.name
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
- **#62339** - Unknown phone number appeared in OpenClaw allowFrom without user authorization (WhatsApp)
- **#57827** - OpenClaw 2026.3.28 `config.openFile` / OPENCLAW_CONFIG_PATH command injection vulnerability
- **#58140** - Running official install command triggers Windows Defender - malicious batch file and registry keys added

### Exec Approvals (new in v2026.3.31)
- **#62380** - Windows Node system.run completely non-functional - exec-approvals.sock never created (REGRESSION)
- **#58768** - Incompatible security approval config
- **#58687** - Security prompt too long to approve, "Allow All" ineffective
- **#58479** - Approval dialog succeeds but exec never consumes it (REGRESSION)
- **#58356** - system.run.prepare broken after update to v2026.3.28

## Breaking Changes & Regressions

### Breaking in v2026.4.5 (current)
- External plugins fail to load: normalizeAccountId is not a function (#62511)
- Maximum call stack size exceeded on Windows - plugins fail to load (#62372, #62320, #62302)
- ERR_UNSUPPORTED_ESM_URL_SCHEME on Windows for all non-file:// paths (#62564, #62502, #62374, #62408)
- CLI commands hang indefinitely consuming 90%+ CPU (#62400, #62356)
- Gateway segfaults on sessions containing cached PNG images (#62329)
- `openclaw devices` command unresponsive (#62326)
- Slack DM file attachments no longer download to inbound (#62623)
- Slack inbound images broken - speech-core/runtime-api.js resolution failure (#62318)
- Coding Agent never completes anything (worked in 2026.4.2) (#62505)
- Ollama embedding broke (#62282)
- Canvas returns 401 Unauthorized on Windows (#62546)
- Cannot create new agent after enable dreaming config (#62541)
- Edit tool fails with tilde paths (#62517)
- Telegram approval messages broadcast to multiple users (#62576)
- Non-main agents in Telegram multi-agent stop replying unless contextEngine=legacy (#62324)
- memory-core plugin fails to load: "Unable to load plugin public-surface runtime" (#62347)
- Feishu bundled plugin fails to load: missing register/activate export (#62277)
- Port 18789 in use when configuring new dreaming schedule (#62276)
- Control UI completely blank: "process is not defined" (#62311)
- Media download failed (re-occurrence of #32326) (#62498)

### Breaking in v2026.3.31 (still relevant)
- Pre-compaction memory flush leaks into chat UI and blocks user turns (#58956)
- Exec approval system overhauled - excessive prompts, allow-always behaves as allow-once (fixed in #58792, #58860, #58745)

### Breaking in v2026.3.28+ (still relevant)
- Browser server removed from gateway - "openclaw browser start" not found (#58256, #58221)
- Teams webhook broken: publicUrl removed breaks JWT validation (#58249)
- Cron model override ignored (#58575, #58065, #57947, #58927)
- SecretRef-backed headers sent as literal "secretref-managed" (#58087)
- Agent systematically omits required tool parameters (#57826)

### Breaking in v2026.3.22 (still relevant)
- Control UI assets missing from npm package (#53096)
- Missing extension runtime API entries (#53046)

### Active Regressions
| Issue | Summary |
|-------|---------|
| #62691 | `message send` crashes with ERR_INTERNAL_ASSERTION in v2026.4.5 |
| #62623 | Slack DM file attachments no longer download in 2026.4.5 |
| #62564 | ERR_UNSUPPORTED_ESM_URL_SCHEME on Windows (2026.4.5) |
| #62541 | Cannot create new agent after enable dreaming config |
| #62517 | Edit tool fails with tilde paths, error broadcasts to Telegram |
| #62511 | External plugins fail to load: normalizeAccountId is not a function |
| #62505 | Coding Agent never completes (worked in 2026.4.2) |
| #62498 | Media download failed in v2026.4.5 |
| #62418 | WebChat Control UI displays internal exec notifications |
| #62410 | Maximum call stack size exceeded during JSON Schema validation |
| #62400 | CLI local commands hang indefinitely (2026.4.5) |
| #62390 | buildQualifiedChatModelValue ignores provider when model has slash |
| #62380 | Windows Node exec-approvals.sock never created |
| #62372 | RangeError: Maximum call stack size exceeded (plugin loading) |
| #62347 | memory-core plugin fails to load during onboard |
| #62329 | Gateway segfaults on cached PNG image in session history |
| #62326 | openclaw devices command unresponsive |
| #62324 | Non-main Telegram agents stop replying unless contextEngine=legacy |
| #62320 | CLI Stack Overflow in loadOpenClawPlugins |
| #62318 | Slack inbound images broken in 2026.4.5 |
| #62311 | Control UI blank: "process is not defined" |
| #62302 | RangeError: Maximum call stack on startup (talk-voice/JITI) |
| #62285 | Gateway not working after upgrading to 2026.4.5 |
| #62282 | Ollama embedding broke in 2026.4.5 |
| #62277 | Feishu bundled plugin fails to load |
| #62276 | Port 18789 in use when configuring dreaming |
| #62261 | Dev channel fails to build (preflight lint fails) |
| #58956 | Pre-compaction memory flush leaks into UI, blocks user turn |
| #58880 | OpenRouter reasoning mandatory, cannot be disabled |
| #58807 | WebSocket fallback to HTTP with ENETUNREACH |
| #58781 | include_usage not auto-added, console stats broken |
| #58738 | ClawBot WeCom unresponsive after pairing |
| #58737 | Slack agent display name/avatar reverts on edited messages |
| #58712 | Skills WSL path issue shows disabled but works |
| #58628 | Browser tool missing from agent tool list despite enabled |
| #58599 | Edit tool schema mismatch (edits[] vs flat) |
| #58575 | Cron --model flag does not override session model |
| #58560 | Browser tools AJV schema error |
| #58479 | Control UI exec approval never consumed |
| #58249 | Teams webhook broken (publicUrl removed) |
| #58256 | Browser server removed from gateway, command not found |
| #58221 | Chrome extension browser relay unavailable on macOS |
| #58107 | Multiple Feishu agents - only main reply delivered |
| #58087 | SecretRef headers sent as literal string |
| #58065 | Cron model override ignored |
| #57964 | Repeated characters collapse in dashboard/TUI |
| #57947 | Cron payload model override ignored |
| #57826 | Agent omits required tool parameters |
| #57753 | Anthropic SSE state machine fails to reset between tool-use loops |
| #57731 | Discord stale-socket drops causing delayed/duplicate messages |
| #57663 | MiniMax M2.7 408 timeouts not surfaced, 4+ min delays |

### Config Migration Hazards
- **#49666** - Telegram proxy config silently wiped on restart
- **#24008** - Unknown config keys silently wipe entire section on restart
- Browser control server removed - configs referencing `browser.server` need migration
- `hooks.internal.enabled` default changed to `true` - may affect setups relying on it being off
- `exec.host` default changed from `"sandbox"` to `"auto"`
- Exec approval system overhauled in 2026.3.31 - new approval flow can block all remote usage if not configured
- v2026.4.5 Windows ESM URL scheme handling is broadly broken - avoid upgrading Windows installs until patched

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
- v2026.4.5: External plugins fail with normalizeAccountId is not a function (#62511)
- v2026.4.5: Maximum call stack size exceeded on plugin loading (#62372, #62320, #62302)
- v2026.4.5: memory-core plugin fails to load during onboard (#62347)
- v2026.4.5: Feishu bundled plugin missing register/activate export (#62277)

### Skills
- Sub-agents cannot see globally installed skills (#35272)
- Skills can silently fail to load with no error (#29122)
- `skills.allowBundled: []` semantics inverted (#21709)
- Agent becomes unresponsive during skill installation (#52073)
- Non-JSON SecretRef not supported in skills entries apiKey (#58319)
- WSL path resolution may show skill as disabled when it works (#58712)

### Channel Plugin Registration
- Slack ESM interop crash: "App is not a constructor" (#50441)
- Slack multi-workspace inbound DM replies missing (#58523)
- Slack socket-mode mentions dropped after stale-socket reconnect (#58268)
- Slack DM file attachments no longer download in 2026.4.5 (#62623)
- Slack inbound images broken in 2026.4.5 (#62318)
- WhatsApp outbound fails despite connected status (#58408)
- WhatsApp groupPolicy "allowlist" bypassed (#52763)
- Teams webhook broken in 2026.3.24+ (#58249)
- Feishu multi-group only main reply delivered (#58107)
- Feishu webhook verification fails with encryptKey (#58905)
- Feishu bundled plugin fails to load in 2026.4.5 (#62277)
- Google Chat space/group messages silently ignored (#58514)
- Matrix plugin syncs but never routes inbound messages (#51158)
- Signal group messages silently dropped on Node 24 (#51716)
- LINE webhook 404 with hooks.internal.enabled (#52729)
- Discord channel running=true while connected=false (#51190)
- Discord stale-socket aggressive drops (#57731)
- Telegram 401 Unauthorized in 2026.4.5 (#62690)
- Telegram approval messages broadcast to multiple users (#62576)
- Telegram non-main agents stop replying in multi-agent (#62324)

## Recently Closed / Fixed (removed from previous tracking)
- **#58931** - Matrix not sending intermediate messages since 2026.3.31 - CLOSED (fixed 2026-04-01, MiniMax-specific + Matrix blockStreaming added)
- **#58934** - Validation failure exec host=node cwd omitted - CLOSED (PR #58977)
- **#58723** - dangerouslyForceUnsafeInstall param not effective - CLOSED (PR #58879, confirmed fixed in 2026.4.1)
- **#58734** - Matrix bootstrap runtime broken in 2026.3.31 - CLOSED (fixed 2026-04-01)
- **#57956** - Anthropic token auth profiles broken in 2026.3.28 - CLOSED (Anthropic ended third-party subscription support April 4, 2026)
- **#57776** - Matrix device verification fails with mismatched_sas - CLOSED (fixed 2026-04-03)
- **#57746** - Telegram long messages truncated instead of split - CLOSED (fixed 2026-04-06)
- **#57618** - Mattermost channel config rejected after upgrade - CLOSED (fixed 2026-04-04)
- **#58347** - LiveSessionModelSwitchError defeats fallback chain - CLOSED (PR #60266, regression coverage added)
- **#58337** - MiniMax toolCall pre-text block completely dropped on Telegram - CLOSED (fixed 2026-04-04)
- **#58546** - Multi-agent routing session under wrong agent - CLOSED (fixed)
- **#58466** - Model switch blocks failover on overloaded_error - CLOSED (PR #58589)
- **#58409** - CRITICAL heartbeat session reset - CLOSED (PR #58605, #58447)
- **#58357** - HTTP API missing scope with --auth none - CLOSED (PR #58653)
- **#58456** - API key status "unknown" for some providers - CLOSED (PR #58503)
- **#58494** - Browser CDP stale cdpUrl preference - CLOSED (PR #58499)
- **#58217** - Missing scope: operator.write - CLOSED (PR #58653)
- **#52899** - Matrix Plugin API version mismatch - CLOSED
- **#58662** - allow-always behaves as allow-once - CLOSED (PR #58745)
- **#58620** - Gateway writes auth.token to config, triggering restart loop - CLOSED (PR #58678)
- **#58689** - All HTTP endpoints 500 after upgrade to 2026.3.31 - CLOSED
- **#58697** - Gateway panel Internal Server Error - CLOSED

## Recent Impactful PRs (last 30 days, since 2026-03-07)

| PR | Title | Area |
|---|---|---|
| #62658 | Require re-pairing for node reconnect command upgrades | Gateway |
| #62650 | feat(ios): improve gateway connection error ux | iOS |
| #62600 | fix: compaction after tool use abortion cause agent infinite loop calls | Agents |
| #62439 | fix(exec): detect cmd wrapper carriers | Exec |
| #62411 | fix(google): preserve Gemma 4 thinking-off semantics | Agents |
| #62401 | fix(exec): align node shell allowlist wrappers | Exec |
| #62383 | fix(allowlist): gate write commands behind owner check | Security |
| #62369 | fix(feishu): enforce workspace-only localRoots in docx upload | Feishu |
| #62357 | fix(fetch-guard): drop request body on cross-origin unsafe-method redirects | Security |
| #62355 | fix(browser): harden SSRF redirect guard against non-navigation document hops | Security |
| #62350 | fix(gateway): invalidate shared-token/password WS sessions on secret rotation | Gateway |
| #62316 | fix(docker): use built bundled plugins in runtime images | Docker |
| #62312 | fix(gateway): stop SSRF guard rejecting operator-configured proxy hostnames | Gateway |
| #62291 | fix: expand host-exec env blocklist for Java, Rust, and Cargo toolchains | Security |
| #62286 | fix(channels): keep bundled dist loads off native Jiti on Windows | Channels |
| #62275 | fix(memory): respect selected slot in dreaming config | Memory |
| #62264 | Add lightContext support for spawned subagents | Agents |
| #62263 | Fix Telegram doctor migration for multi-account configs | Telegram |
| #62251 | Cron: normalize jobId to id when loading jobs.json | Cron |
| #62244 | Fix: HTTP 404 classification for model fallback chain | Agents |
| #62239 | fix(slack): prevent undici dispatcher leak to globalThis.fetch causing media download failure | Slack |
| #62237 | Mistral: send reasoning_effort for mistral-small-latest | Agents |
| #62234 | Plugins: allowlist compat for capability provider fallback | Plugins |
| #62227 | feat(memory-core): ingest session transcripts into dreaming corpus | Memory |
| #62193 | feat(ollama): detect vision capability from /api/show and set image input | Ollama |
| #62179 | feat: expose prompt-cache runtime context to context engines | Agents |
| #62168 | Matrix: prompt invite auto-join during onboarding | Matrix |
| #62148 | chore: bump bundled acpx to 0.5.1 | ACPX |
| #62146 | feat(gateway): add compaction checkpoints | Gateway |
| #62136 | fix: openclaw allows normal reply text to carry media | Security |
| #62135 | Refactor: centralize native approval lifecycle assembly | Exec |
| #62132 | ACP: harden Discord recovery and reset flow | ACP/Discord |
| #62129 | feat: Add first-class infer CLI for inference workflows | CLI |
| #62111 | fix: lower trust background runtime output injected into system events | Security |
| #62082 | fix: QQ Bot extension media URLs not guarded | QQ Bot/Security |
| #62079 | fix: Mercurial/Rust/Make env vars not sanitized in host exec | Security |
| #62078 | fix: timed-out exec approval can proceed when strictInlineEval enabled | Security |
| #62068 | feat: add Arcee AI provider plugin | Plugins |
| #62050 | stabilize media live coverage and add shared harness | Media |
| #62023 | fix(browser): guard interaction-driven navigations | Security |
| #62003 | fix(hooks): mark wake hook events untrusted | Security |
| #62001 | Protect gateway exec approval config paths | Security |
| #61985 | fix: suppress commentary history leaks | Agents |
| #61968 | fix(agents): keep phaseless OpenAI WS text buffered until phase resolves | Agents |
| #61935 | fix(gateway-status): use local TLS probe targets with fingerprint | Gateway |
| #61933 | fix(command-queue): crash on SIGUSR1 restart after upgrade from pre-4.5 | Gateway |
| #61925 | fix: lazily recreate bound ACP sessions after reset | ACP |
| #61924 | fix(memory): surface warning when sqlite-vec unavailable during index | Memory |
| #61921 | fix(browser): retry remote CDP websocket readiness before failing | Browser |
| #61909 | fix: preserve code block indentation in normalizeDirectiveWhitespace | Agents |
| #61907 | fix(matrix): compact loose list HTML for consistent Element rendering | Matrix |
| #61903 | fix(agents): prevent ReDoS in interpreter heuristic regexes | Security |
| #61892 | plugins: add bundled webhooks TaskFlow bridge | Plugins |
| #61873 | fix: approval card buttons off-screen on mobile | UI |
| #61872 | fix: prevent Canvas/Copy icons from overlapping chat bubble text | UI |
| #61871 | fix: recognize api.grok.x.ai as xAI-native endpoint | Agents |
| #61869 | fix: detect ?token= and suggest #token= fragment syntax | UI |
| #58929 | fix(ci): allow plugin npm preview without publish token | Plugins |
| #58918 | fix: hide raw provider errors from external chat replies | Agents |
| #58916 | fix: preserve anthropic thinking blocks on replay | Agents |
| #58904 | fix(agent): treat webchat exec approvals as native UI | Agents/Exec |
| #58900 | feat(gateway): make chat history max chars configurable | Gateway |
| #58896 | Security: require explicit opt-in for internal startup hooks | Security |
| #58895 | qqbot: require explicit allowlist for /bot-logs | Security |
| #58879 | fix(plugins): pass dangerouslyForceUnsafeInstall through archive | Plugins |
| #58873 | fix: preserve bundled channel plugin compat | Plugins |
| #58872 | fix(cron): avoid busy-wait drift for recurring main jobs | Cron |
| #58869 | fix(subagents): harden task-registry lifecycle writes | Tasks |
| #58860 | fix(exec): resume agent session after approval completion | Exec |
| #58846 | fix(compaction): add circuit breaker for retry loops | Agents |
| #58844 | fix(compaction): prevent splitting mid tool-call pairs | Agents |
| #58828 | feat(tasks): add chat-native task board | Tasks |
| #58825 | fix(gateway): move probe ahead of channel stages for health checks | Gateway |
| #58810 | fix(status): filter stale task rows from status cards | Tasks |
| #58799 | fix(line): resolve dist runtime contract path | LINE |
| #58792 | fix(exec): resolve remote approval regressions | Exec |
| #58782 | fix: restore bundled runtime dependency provisioning | Plugins |
| #58746 | fix: catch per-stage errors in HTTP pipeline to prevent cascade 500s | Gateway |
| #58716 | fix: re-throw LiveSessionModelSwitchError instead of swallowing in fallback | Agents |
| #58707 | fix: escalate to model fallback after rate-limit profile rotation cap | Agents |
| #58706 | feat(slack): default allowBots to true | Slack |
| #58705 | fix(plugins): repair bundled runtime deps within plugin install dirs | Plugins |
| #58688 | fix(discord): polyfill Client.registerListener for carbon >=0.14 compat | Discord |
| #58678 | fix: treat gateway.auth and gateway.controlUi as no-op in reload plan | Gateway |
| #58670 | fix(tasks): prevent synchronous task registry sweep from blocking event loop | Tasks |
| #58653 | fix: grant default operator scopes when gateway auth mode is none | Gateway |
| #58641 | Webchat: preserve rewritten stream snapshots | WebChat |
| #58625 | feat(auth): WHAM-aware Codex cooldown for multi-profile setups | Auth |
| #58614 | fix(acpx): fall back to PATH node for shebang wrappers | ACPX |
| #58610 | fix(acpx): harden codex and gemini ACP runtime flows | ACPX |
| #58609 | routing: support wildcard peer bindings (peer.id="*") for multi-agent | Routing |
| #58605 | fix(session): prevent heartbeat/cron/exec from triggering session reset | Sessions |
| #58604 | plugins: suppress provenance warning for allowlisted local plugins | Plugins |
| #58593 | fix(discord): stop media downloads from hanging | Discord |
| #58589 | fix: live session model switch no longer blocks failover | Agents |
| #58586 | fix(voice-call): clear connection timeout on successful STT connect | Voice |
| #58573 | fix(sandbox): resolve pinned fs helper python without PATH | Sandbox |
| #58562 | fix: differentiate overloaded vs rate-limit user-facing error messages | Agents |
| #58555 | fix: harden embedded text normalization | Agents |
| #58548 | feat: add agents.defaults.params for global default model params | Agents |
| #58521 | fix(tasks): make task-store writes atomic | Tasks |
| #58516 | refactor(tasks): add owner-key task access boundaries | Tasks |
| #58504 | feat(cron): add --tools flag for per-job tool allow-list | Cron |
| #58503 | fix(auth): add qwen-dashscope and anthropic-openai to known API key env vars | Auth |
| #58502 | fix(gateway): skip restart when config.patch has no actual changes | Gateway |
| #58499 | fix: CDP profiles prefer cdpPort over stale WebSocket cdpUrl | Browser |
| #58497 | feat: feishu comment event | Feishu |
| #58489 | fix: preserve Telegram topic routing in announce and delivery context | Telegram |
| #58474 | fix(session-status): infer custom runtime providers from config | Gateway |
| #58461 | fix(agents): correct model resolution priority in live-model-switch | Agents |
| #58447 | fix(core): prevent silent session reset during heartbeat runs | Sessions |
| #58446 | feat: add thinkingByChannel - per-channel thinking level overrides | Agents |
| #58403 | feat(openresponses): add per-request skills override to /v1/responses | API |
| #58400 | fix: move bootstrap session grammar into plugin-owned session-key surfaces | Plugins |
| #58382 | fix(pairing): restore qr bootstrap onboarding handoff | Pairing |
| #58379 | fix(gateway): prevent session death loop on overloaded fallback | Gateway |
| #58376 | fix(matrix): filter fetched room context by sender allowlist | Matrix |
| #58375 | Plugins: preserve prompt build system prompt precedence | Plugins |
| #58371 | Gateway: reject mixed trusted-proxy token config | Gateway |
| #58369 | Exec approvals: reject shell init-file script matches | Security |
| #58368 | fix(browser): close SSRF bypass - redirect guard and follow-up action gates | Security |
| #58362 | fix(android): resolve TLS handshake failure on Android 15 | Android |
| #58350 | fix(zalo): isolate replay dedupe across webhook paths | Zalo |
| #58346 | fix(acp): use semantic approval classes | ACP |
| #58341 | fix: skip stale-socket restart when Discord channel is still connected | Discord |
| #58336 | ClawFlow: add runtime substrate | Tasks |
| #58325 | fix(sessions): clear model override on /reset and /new | Sessions |

## Dev Gotchas (synthesized)

- **v2026.4.5 is extremely unstable on Windows** - ERR_UNSUPPORTED_ESM_URL_SCHEME (#62564, #62502, #62374, #62408), Maximum call stack size exceeded (#62372, #62320, #62302, #62410, #62430), plugins fail to load (#62511, #62347, #62277). Avoid upgrading Windows installs to 2026.4.5 until a hotfix release. Multiple critical regressions affect onboarding, CLI, and plugin loading.
- **v2026.4.5 Slack file handling broken** - Both DM file attachments (#62623) and inbound images (#62318) are broken. Root cause is likely the undici dispatcher leak fix (#62239) or speech-core runtime-api.js resolution failure. Images shared in Slack are not forwarded to the model.
- **v2026.4.5 CLI hangs and crashes** - CLI local commands hang indefinitely consuming 90%+ CPU (#62400), unknown subcommands cause infinite loops (#62356), `openclaw devices` is unresponsive (#62326). These may share a root cause with the Maximum call stack size issues.
- **v2026.4.5 memory-core / dreaming config issues** - memory-core plugin fails to load during onboard (#62347), cannot create new agent after enabling dreaming config (#62541), Ollama embedding broke (#62282). The dreaming feature appears unstable.
- **v2026.4.5 Coding Agent regression** - Coding Agent never completes anything, only produces vague status updates (#62505). Worked in 2026.4.2.
- **v2026.3.31 exec approval overhaul** - The exec approval system was significantly reworked. Expect excessive approval prompts; allow-always may behave as allow-once. Multiple hotfixes landed (PRs #58792, #58860, #58745). Remote usage on Windows may be blocked without workaround. Additionally, timed-out approvals could bypass strictInlineEval (fixed in PR #62078).
- **v2026.3.31 pre-compaction memory flush** (#58956) - Memory flush leaks into chat UI and blocks the user's active turn. Still open.
- **v2026.3.28 removes browser control server from gateway** - "openclaw browser start" is gone (#58256, #58221). Chrome extension browser relay stops working. This is a structural change, not a bug.
- **Cron model override is still broken across 4 issues** (#58575, #58065, #57947, #58927) - --model flag, payload.model, and agentTurn model override all fail; always uses agent default. PRs #58992 and #58998 were submitted but issues remain open.
- **Anthropic subscription support ended April 4, 2026** - Anthropic ended third-party harness subscription access. Users must enable pay-as-you-go "extra usage" to continue using Anthropic models through OpenClaw. One-time credit available until April 17. (#57956)
- **Model failover improvements landed but gaps remain** - PRs #58589, #58716, #58707, #60266 fixed several failover issues (overloaded_error, rate limits, LiveSessionModelSwitchError). But #58442 (Coding Plan 429 infinite loop) remains open. PR #62244 adds HTTP 404 classification to the fallback chain. Compaction abort now correctly handles tool use (#62600).
- **Compaction circuit breaker added** (PR #58846) - Prevents infinite retry loops during compaction. Also prevents splitting mid tool-call pairs (#58844). Compaction checkpoints added (PR #62146) for better recovery.
- **Plugin installs now fail closed on dangerous code** - use `--dangerously-force-unsafe-install` to override. Plugin source scan failures also block install. The param was broken in 2026.3.31 (#58723) but fixed in PR #58879 (confirmed working in 2026.4.1).
- **Massive security hardening wave** - Multiple PRs since April 1: SSRF redirect guard hardened for browser (#62355, #62023, #62312), exec env blocklist expanded for Java/Rust/Cargo/Mercurial/Make (#62291, #62079), timed-out exec approvals fixed (#62078), wake hook events marked untrusted (#62003), exec approval config paths protected (#62001), reply text media path sanitized (#62136), QQ Bot media URLs guarded (#62082), cross-origin redirect body dropped (#62357), ReDoS prevented in interpreter heuristic (#61903).
- **Teams webhook broken since 2026.3.24** (#58249) - publicUrl removal breaks JWT validation. Still open.
- **hooks.internal.enabled now defaults to true** - bundled hooks load on fresh installs. Old configs relying on false default may see new behavior. PR #58896 now requires explicit opt-in for internal startup hooks.
- **exec.host defaults to "auto" instead of "sandbox"** - may change exec routing behavior for existing setups.
- **New features: infer CLI, TaskFlow webhooks, dreaming** - `openclaw infer` CLI for provider-backed inference (PR #62129), bundled webhooks TaskFlow bridge (PR #61892), memory-core dreaming corpus ingestion (PR #62227). Dreaming is still unstable on 2026.4.5.
- **New features: compaction checkpoints, lightContext subagents** - Compaction checkpoints for recovery (PR #62146), lightContext support for spawned subagents (PR #62264).
- **Prompt cache invalidated every turn** (#36520) - still open. PR #62179 exposes prompt-cache runtime context to context engines.
- **Shared process model = no plugin isolation** (#12517, #12518) - all plugins share one Node.js process.
- **Sub-agents can't see globally installed skills** (#35272) - still no fix.
- **Config keys still silently wipe sections** (#24008) - validate config carefully across upgrades.
- **Google provider usageMetadata not mapped** (#51743) - all Gemini calls record 0 tokens. PR #62193 adds Ollama vision capability detection.
- **SecretRef-backed headers resolve to literal string** (#58087) - regression affecting model providers using SecretRef for custom headers.
- **Long sessions break model inference** (#58553) - 600+ message sessions get "invalid function call parameters".
- **Edit tool schema mismatch** (#58599) - edits[] array in schema vs flat oldText/newText in implementation.
- **CJK character handling** (#58932) - normalizeHyphenSlug strips CJK characters, breaking non-Latin group display names.
- **Security: config.openFile command injection** (#57827) - OPENCLAW_CONFIG_PATH vulnerable in 2026.3.28.
- **Wildcard peer bindings** (PR #58609) - peer.id="*" now supported for multi-agent routing.
- **agents.defaults.params** (PR #58548) - New config key for global default model params.
- **thinkingByChannel** (PR #58446) - Per-channel thinking level overrides now available.
- **Cross-session leakage reported** (#62580) - Response contamination between sessions. Needs investigation.
- **WhatsApp allowFrom security concern** (#62339) - Unknown phone number appeared in allowFrom without user authorization. Cron job sent messages to unknown number. Potential security issue.
