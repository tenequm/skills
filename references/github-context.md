# OpenClaw GitHub Context
> Last refreshed: 2026-03-19T14:00:00Z

## Open Bugs (critical for development)

### Plugin System
- **#50441** - Slack channel crashes: "App is not a constructor" (@slack/bolt ESM interop)
- **#50382** - Duplicate plugin loading warning for installed extensions on gateway startup
- **#50323** - "failed to persist plugin auto-enable changes" warning on startup with wecom plugin
- **#50315** - Firecrawl plugin missing in openclaw@2026.3.13 npm package (not in extensions/, not listed)
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
- **#50293** - Control UI model dropdown shows incorrect entries
- **#50197** - Control UI dropdown fails to reset provider prefix after model switch
- **#50050** - Control UI model switcher sends wrong provider prefix for cross-provider switching
- **#49666** - Telegram proxy config wiped on gateway restart
- **#49686** - "model not allowed" when selecting models with custom provider prefix
- **#24008** - Unrecognized config keys silently wipe and reset entire section on restart
- **#35957** - Stale keys from v2026.3.2 block gateway startup in v2026.3.3+
- **#36792** - Gateway promises "best-effort config" on invalid config but exits instead
- **#32583** - MCP servers config not in schema - adding to openclaw.json fails with 'Unrecognized key'

### Gateway Startup
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
- **#49725** - CLI auth regression on 2026.3.13: intermittent missing scope: operator.read and websocket close
- **#49885** - google-vertex fails with "No credentials found for profile" even when ADC is valid
- **#49138** - OAuth flow missing api.responses.write scope - blocks GPT-5.4 in subagents
- **#37303** - Onboarding crashes with exec secret provider - `getStatus()` eagerly resolves SecretRef tokens
- **#37123** - Azure OpenAI not appearing during onboarding wizard
- **#12517** - [SEC] All 31 plugins share single Node.js process - lateral movement across plugins
- **#12518** - [SEC] All plugin credentials in shared `process.env` - no isolation between channels
- **#11829** - [SEC] API keys leak to LLM via tool outputs, error messages, system prompts

### Channels
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
- **#35272** - Sub-agents cannot access shared skills from `~/.openclaw/skills/` - directly impacts `npx skills add -g` (3 upvotes)
- **#29122** - Workspace skills silently not loading (no error, valid SKILL.md)
- **#21709** - `skills.allowBundled: []` allows all instead of blocking all (semantics bug)
- **#49427** - skills.entries apiKey file SecretRef passes audit but remains unresolved during embedded run startup

### Cron
- **#50303** - Cron jobs created by CLI but do not materialize from Telegram/WebChat conversation
- **#50170** - Cron reports status "error" despite successful Discord delivery (regression)
- **#50169** - `openclaw cron` command causes gateway restart failure (lock timeout)
- **#49258** - Cron job state inconsistency - lastDelivered: true but lastRunStatus: error
- **#49124** - Cron error state accumulates during host sleep/connectivity loss

### TUI
- **#49918** - TUI /new stopped emitting hook-visible new-session behavior (regression)
- **#37243** - TUI replies routed to Telegram instead of TUI (100% repro with Telegram configured)
- **#37168** - TUI assistant replies not displayed (`--deliver` flag ignored)

## Breaking Changes & Regressions

### Breaking in v2026.3.13 (current)
- CLI auth intermittent: missing scope operator.read, websocket close 1000/1006 (#49725, #50438)
- Telegram messages sent twice after channel restart (#50424)
- Feishu channel crashes gateway (#49576) and silently fails on valid API calls (#50266)
- WhatsApp Web listener Map duplicated - sends always fail (#49411)
- Gateway restart fails from stale process misdetection (#50074)
- npm package missing dist/gateway.js (#49338)
- Plugin tools not inherited by subagent runtime (#50131)
- Firecrawl plugin missing from npm package (#50315)

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
| #50450 | Telegram duplicate messages (channel restart resend) |
| #50438 | devices commands fail with gateway closed (1000) in v2026.3.13 |
| #50424 | Telegram messages sent twice after restart |
| #50401 | DeepSeek-V3 400 on tool calls |
| #50352 | acpx fails to spawn Claude CLI on Windows |
| #50332 | Automatic spaces in mixed CJK-English text cause path errors |
| #50315 | Firecrawl plugin missing from npm package |
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

### Skills
- Sub-agents cannot see globally installed skills (#35272) - impacts `~/.openclaw/skills/` approach
- Skills can silently fail to load with no error (#29122)
- `skills.allowBundled: []` semantics inverted (#21709)
- Skills entries env vars not propagated to sandbox subprocess (fixed: #50412)
- apiKey SecretRef unresolved during embedded run startup (#49427)

### Channel Plugin Registration
- Slack ESM interop crash: "App is not a constructor" (#50441)
- WhatsApp listener Map duplicated across bundles (#49411)
- Feishu duplicate registration warnings/crashes (#49412, #49576)
- Feishu multi-group binding routing fails under concurrency (#50127)
- Zalo getZaloRuntime undefined on startup (#50377)
- iMessage "Cannot find package 'openclaw'" (#49806)

## Recent Impactful PRs (last 30 days)

| PR | Title | Area |
|---|---|---|
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
| #49955 | Tests: restore deterministic plugins CLI coverage | Plugins |
| #49941 | feat: update default context window to 1M tokens for Claude Opus/Sonnet 4.6 | Models |
| #49702 | fix(security): block build-tool and glibc env injection in host exec sandbox | Security |
| #49570 | Main recovery: restore formatter and contract checks | Build |
| #49555 | Plugin SDK: restore read-only directory inspection seam | Plugin SDK |
| #49551 | Image generation: native provider migration and explicit capabilities | Agents |
| #49542 | Plugin SDK: guard package subpaths and fix Twitch setup export | Plugin SDK |
| #49533 | fix(plugins): add missing secret-input-schema build entry and Matrix runtime export | Plugins |
| #49513 | fix: add docs hint for plugin override trust error | Gateway |
| #49490 | plugins: dist node_modules symlink + config raw-toggle UI fix | Plugins |
| #49454 | Image generation: add fal provider | Agents |

## Closed Since Last Refresh (previously tracked)
- **#41925** - No session created, no runs recorded - FIXED
- **#41979** - Cron "Run Now" enqueues but never executes - FIXED
- **#37375** - Discord fetch failure crashes gateway - FIXED
- **#41798** - Cron isolated session not executing in v2026.3.8 - FIXED
- **#41930** - Control UI WebSocket reconnect loses gateway token - FIXED

## Dev Gotchas (synthesized)

- **v2026.3.13 has significant channel regressions** - Telegram duplicate messages (#50424, #50450), Feishu crashes (#49576), WhatsApp listener Map duplication (#49411), Slack ESM interop crash (#50441). Test channel connectivity thoroughly after upgrade.
- **Plugin singleton state can fragment across module graphs** - Fixed by #50418 and #50431, but any plugin relying on shared state (hook runners, registries) must be aware. Extensions duplicated across bundles get separate instances unless Symbol-based singletons are used.
- **CLI auth on v2026.3.13 is unstable** - Intermittent "missing scope: operator.read" and WebSocket close (1000/1006) errors (#49725, #50438). Multiple independent reports. May affect automated provisioning scripts that call `openclaw` CLI commands.
- **Plugin tools are invisible to sandboxed and subagent sessions** (#41757, #50131) - Tools registered by plugins do not inherit gateway subagent runtime. Must remove sandbox or ensure tools are in the gateway-level tools profile.
- **Sub-agents can't see globally installed skills** (#35272) - `~/.openclaw/skills/` skills invisible to sub-agents. Directly affects AgentBox's `npx skills add -g` approach. 3 upvotes, still no fix.
- **Config keys still silently wipe sections** (#24008) - Unknown keys cause entire config section reset on restart. Validate config carefully across version upgrades. Back up before upgrading.
- **Prompt cache invalidated every turn** (#36520) - Runtime events mutate system prompt, forcing cache miss. Silent cost multiplier on all VMs. Still open.
- **Shared process model = no plugin isolation** (#12517, #12518) - All plugins share one Node.js process. Wallet keys in x402 plugin accessible to any other plugin.
- **Headless startup pitfalls** - Doctor check hangs without TTY (#24178), health check times out on slow starts (#22972). Both relevant to cloud-init boot.
- **Plugin prompt hooks need explicit allowlist** (PR #36567) - Plugins using `before_prompt_build`/`before_agent_start` blocked unless `hooks.allowPromptInjection` is set.
- **`gateway.auth.mode` now mandatory** (PR #35094) - Startup fails if both token+password configured without explicit mode.
- **Cron delivery reporting is unreliable** - Reports error despite successful delivery (#50170), state inconsistency (#49258). Don't trust cron status as ground truth.
- **Model selector bugs across all UIs** (#50293, #50197, #50050, #49683) - Provider prefix handling broken in Control UI. Model switching may silently send wrong model ref.
- **Claude Opus/Sonnet 4.6 default context window updated to 1M** (PR #49941) - Affects default token limits in new sessions.
- **Gateway stale process detection is broken** (#50074) - Restart may fail or kill the wrong PID. Workaround: manually check process before restart.
- **Skills env vars now propagated to sandbox** (PR #50412) - `skills.entries.<skill>.env` vars are injected into sandbox subprocess environment. New capability.
- **Default reasoning config added** (PR #50405) - Gateway now has `defaultReasoning` config, defaulting to off. May affect agents expecting reasoning to be enabled by default.
