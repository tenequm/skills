# OpenClaw GitHub Context
> Last refreshed: 2026-03-10T12:00:00Z

## Open Bugs (critical for development)

### Plugin System
- **#12854** - CJS dependencies fail with "require is not defined" under jiti loader - blocks any plugin importing CJS npm packages
- **#36377** - Mem0/sqlite3 native bindings broken under jiti (recurring: #31676, #31677) - blocks plugins with native modules
- **#36754** - Extension discovery silently skips symlinked plugin directories (`isDirectory()` returns false for symlinks)
- **#28122** - pnpm global install: bundled plugin manifests rejected as 'unsafe path' - gateway refuses to start (15 reactions)
- **#19312** - 81% bundled plugins affected by unresolved `workspace:*` dependencies in global installs
- **#25859** - Plugin `api.registerHook("message:received")` listed but never fires - hooks cleared at gateway startup
- **#37028** - Feishu duplicate registration crashes gateway (not just warning)
- **#33135** - No `dispatchAgentTurn` in plugin runtime API - webhook plugins can't trigger agent runs
- **#41229** - `plugins install` fails for local plugins when `plugins.allow` already exists
- **#39878** - `plugins uninstall` fails when channel config references the plugin being removed
- **#40232** - Plugin context engines can resolve before plugin registration (Lossless Claw / contextEngine slot)
- **#33704** - Plugin loader missing jiti alias for plugin-sdk/keyed-async-queue subpath
- **#41757** - Custom plugin tool not surfaced to sandboxed agent sessions - appears only when sandbox removed
- **#41257** - MiniMax models' tool calls are stripped instead of executed

### Config Validation
- **#24008** - Unrecognized config keys silently wipe and reset entire section on restart
- **#35957** - Stale keys from v2026.3.2 block gateway startup in v2026.3.3+
- **#36792** - Gateway promises "best-effort config" on invalid config but exits instead
- **#32583** - MCP servers config not in schema - adding to openclaw.json fails with 'Unrecognized key'
- **#28698** - `config.patch` tool dumps full config into LLM context, wasting tokens
- **#41690** - Config validation fails on `requiresOpenAiAnthropicToolPayload` unrecognized key (regression, kimi-coding models)
- **#41702** - JSON parsing syntax error on fields containing "GPT5.4" - `Expected ':' after property name`
- **#41344** - Control UI Agent form shows wrong Primary model and Save fails with `GatewayRequestError: invalid config`

### Gateway Startup
- **#36585** - TLS null dereference crash during socket reconnection under concurrent load
- **#34539** - structuredClone FATAL ERROR in orphaned subagent reconciliation after unclean exit
- **#30257** - boot-md hook misses `gateway:startup` event (race condition - hook registers after event fires)
- **#28647** - Discord channels unresolved on startup (timing issue in channel resolution)
- **#24178** - Doctor check blocks indefinitely without TTY - hangs headless/automated deployments
- **#22972** - Health check times out on slow startups
- **#36672** - HTTP 400 invalid JSON on every request - gateway bricked after initial success
- **#41804** - Gateway persistent stale processes on Windows (scheduled task runtime)
- **#41591** - `gateway stop` on Windows does not terminate running process
- **#41925** - No session is created and no runs are recorded (regression)
- **#41930** - Control UI gateway token in localStorage not reused on WebSocket reconnect - device identity prompt on every refresh
- **#41784** - WebSocket disconnected (1006) when proxying Gateway through Nginx in Docker bridge network
- **#41820** - Axios requests fail with 400 when HTTPS_PROXY is set (plain HTTP to HTTPS port)
- **#41144** - macOS LaunchAgent still points to old dist/entry.js after upgrading to 2026.3.8

### Secrets/Auth
- **#37303** - Onboarding crashes with exec secret provider - `getStatus()` eagerly resolves SecretRef tokens
- **#37142** - MiniMax 401 - anthropic-messages mode doesn't pass Bearer header
- **#37123** - Azure OpenAI not appearing during onboarding wizard
- **#36913** - Intermittent 401 "Invalid bearer token" from gateway probe
- **#12517** - [SEC] All 31 plugins share single Node.js process - lateral movement across plugins
- **#12518** - [SEC] All plugin credentials in shared `process.env` - no isolation between channels
- **#11829** - [SEC] API keys leak to LLM via tool outputs, error messages, system prompts
- **#41619** - google-gemini-cli-auth cannot complete auth even with valid access privilege (regression)
- **#41618** - Dashboard/webchat shows "authentication token invalidated" for non-token root causes
- **#41652** - v2026.2.26 continuously reports device-id-mismatch error

### Channels
- **#37375** - Discord channel fetch failure crashes gateway - unhandled rejection in `registerClient()` (76 crashes/day)
- **#36742** - Dual-account Telegram config crashes gateway under systemd
- **#36687** - `session.dmScope` reset to "main" causes cross-channel reply leakage
- **#37357** - Telegram partial streaming is fake - waits for full response
- **#37415** - Feishu websocket fails on WSL2
- **#12534** - [SEC] Nostr plugin exposes unauthenticated `runtime.config.writeConfigFile()` - full config takeover
- **#41753** - Intermittent inbound Telegram DM delivery failure persists in v2026.3.x
- **#41739** - Telegram replies routed to Web UI session instead of source channel (regression)
- **#41708** - Telegram fails on Sonnet 4.6 related to thinking blocks (regression)
- **#41581** - Telegram DM partial streaming regressed from smooth sendMessageDraft to choppy editMessageText after 2026.3.8
- **#41569** - Telegram media download intermittently fails behind proxy
- **#41576** - Channel leaks `[[reply_to:ID]]` tags into visible message text
- **#41844** - Discord leaks raw `to=cron` tool-call text instead of executing cron scheduling
- **#41860** - Feishu: links with underscores cannot display full hyperlink
- **#41458** - TTS voice message fails on Feishu channel
- **#41163** - Feishu multi-bot cannot send/receive messages

### Agent Runtime
- **#36520** - Runtime events mutate system prompt every turn, invalidating prompt cache (silent cost multiplier)
- **#36634** - `agents_list` tool returns only "main" despite multiple agents configured
- **#36134** - `sessions_spawn` silently falls back to Anthropic when targeting Gemini
- **#37040** - Agent runs complete with empty `content: []` and zero usage on custom providers
- **#41707** - After upgrade, tools enter infinite repeat loop (regression)
- **#41291** - Agent enters infinite retry loop when tool calls fail
- **#41335** - Session tool registry corruption - tools work once then become "not found"
- **#41282** - openai-codex still times out on GPT-5.4 after #38736 due to remaining non-codex transport path
- **#41249** - Google model provider prefix not stripped in 2026.3.8 - causes 404 on all Google model API calls (regression)
- **#41209** - Tool validation errors after upgrading to 2026.3.8 - file read/write broken
- **#41673** - Embedded run agent end: `isError=true error=LLM request timed out`
- **#41283** - `tools.catalog` errorCode=INVALID_REQUEST errorMessage=unknown agent id
- **#41720** - exec and web_fetch hang indefinitely on macOS
- **#41679** - `read` tool failed: ENOENT
- **#41644** - Returns "400 Model do not support image input" even for text-only messages

### Skills
- **#35272** - Sub-agents cannot access shared skills from `~/.openclaw/skills/` - directly impacts `npx skills add -g`
- **#29122** - Workspace skills silently not loading (no error, valid SKILL.md)
- **#21709** - `skills.allowBundled: []` allows all instead of blocking all (semantics bug)
- **#41722** - skills.install fails on macOS 26 - CLT not supported (regression)
- **#41605** - Control UI Skills panel: clicking anywhere triggers filter and hides all skills

### TUI
- **#37243** - TUI replies routed to Telegram instead of TUI (100% repro with Telegram configured)
- **#37168** - TUI assistant replies not displayed (`--deliver` flag ignored)
- **#36897** - TUI not receiving agent messages (`messagesHandled: 0`)
- **#41971** - Chat hangs forever on Linux (works fine on macOS with identical config)

### Cron
- **#37299** - `cron list`/`cron run` TypeError "Cannot read properties of undefined (reading 'kind')"
- **#37198** - Cron job with "gateway restart" in message causes infinite restart loop
- **#41979** - Cron "Run Now" button doesn't work - task enqueued but never executes (regression)
- **#41798** - Cron isolated session not executing in v2026.3.8 (regression)
- **#41558** - Recurring cron jobs with isolated agentTurn + LLM time out on force-run
- **#41507** - Cron: manual job triggers via API/dashboard enqueue but never execute
- **#41843** - `crontab set` overwrites existing entries without warning

## Breaking Changes & Regressions

### Breaking in latest version (v2026.3.8)
- Google model provider prefix not stripped - 404 on all Google API calls (#41249)
- Tool validation errors - file read/write broken (#41209)
- Cron isolated sessions not executing (#41798)
- Telegram DM streaming regressed to choppy editMessageText (#41581)
- macOS LaunchAgent points to old dist/entry.js after upgrade (#41144)
- skills.install fails on macOS 26 CLT (#41722)
- Browser node routing prevents local Chrome relay from starting (#41214)

### Breaking in v2026.3.2 (still relevant)
- TUI replies rerouted to Telegram when Telegram configured (#37243)
- Onboarding crashes with exec secret providers (#37303)
- Cron commands throw TypeError (#37299)

### Breaking Guardrail (PR #35094)
- `gateway.auth.mode` now mandatory when both `gateway.auth.token` and `gateway.auth.password` configured - startup fails until mode is explicit

### Plugin Prompt Hook Policy (PR #36567)
- New `plugins.entries.<id>.hooks.allowPromptInjection` required for plugins using `before_prompt_build` / `before_agent_start` hooks - blocked at runtime without it

### Active Regressions
| Issue | Summary |
|-------|---------|
| #41979 | Cron "Run Now" enqueues but never executes |
| #41930 | Control UI WebSocket reconnect loses gateway token |
| #41925 | No session created, no runs recorded |
| #41798 | Cron isolated session not executing in v2026.3.8 |
| #41753 | Intermittent Telegram DM delivery failure in v2026.3.x |
| #41739 | Telegram replies routed to Web UI instead of source channel |
| #41722 | skills.install fails on macOS 26 CLT |
| #41708 | Telegram fails on Sonnet 4.6 (thinking blocks) |
| #41707 | Tools enter infinite repeat loop after upgrade |
| #41702 | JSON parse error on "GPT5.4" fields |
| #41690 | Config validation rejects `requiresOpenAiAnthropicToolPayload` key |
| #41619 | google-gemini-cli-auth cannot complete auth |
| #41591 | `gateway stop` on Windows does not terminate process |
| #41581 | Telegram DM streaming regressed (choppy edits) |
| #41558 | Recurring cron jobs time out on force-run |
| #41519 | kimi-k2.5:cloud tool routing fails |
| #41507 | Cron manual triggers enqueue but never execute |
| #41462 | Tool dispatching regression between 2026.3.1 and 2026.3.2 |
| #41335 | Session tool registry corruption - tools work once then break |
| #41291 | Agent infinite retry loop on tool call failure |
| #41282 | openai-codex still times out on GPT-5.4 |
| #41249 | Google model prefix not stripped in 2026.3.8 - 404s |
| #41209 | Tool validation errors - file read/write broken in 2026.3.8 |
| #37375 | Discord fetch failure crash-loops gateway |
| #37357 | Telegram fake streaming in partial mode |
| #37322 | 404 with Bailian/aliyun providers |
| #37303 | Onboarding crash with exec secret provider |
| #37299 | cron list/run TypeError |
| #37243 | TUI replies go to Telegram |
| #37168 | TUI doesn't display assistant replies |
| #37142 | MiniMax 401 in anthropic-messages mode |
| #37123 | Azure OpenAI missing from onboarding |
| #36913 | Intermittent 401 from gateway probe |
| #36897 | TUI messagesHandled: 0 |
| #35078 | Native plugin bindings (node_sqlite3) fail under jiti |
| #32106 | Aggressive compaction loop with memoryFlush |

### Config Migration Hazards
- **#41690** - `requiresOpenAiAnthropicToolPayload` key rejected by config validation in newer versions
- **#41702** - Model names with "GPT5.4" cause JSON parse errors
- **#35957** - Stale keys from v2026.3.2 block startup on v2026.3.3+
- **#24008** - Unknown config keys silently wipe entire section on restart
- **PR #35094** - Must set `gateway.auth.mode` explicitly if both token+password present
- **PR #36567** - Must set `hooks.allowPromptInjection` for plugins with prompt hooks

## Plugin/Extension/Config Known Issues

### Plugin Loading
- CJS dependencies fail under jiti ESM loader (#12854) - fundamental limitation
- Native bindings (sqlite3) broken under jiti (#36377, #35078)
- Symlinked plugin dirs silently skipped (#36754)
- pnpm global install rejects bundled plugin manifest paths (#28122)
- `workspace:*` deps unresolved in 81% of bundled plugins (#19312)
- `api.registerHttpHandler()` removed - must use `api.registerHttpRoute()` (#36794)
- Plugin-registered hooks cleared at gateway startup (#25859)
- Plugin loader missing jiti alias for plugin-sdk/keyed-async-queue (#33704)
- Local plugin install fails when `plugins.allow` already exists (#41229)
- Plugin uninstall fails when channel config still references plugin (#39878)
- Context engine plugins can resolve before registration (#40232)
- Custom plugin tools invisible to sandboxed sessions (#41757)

### Skills
- Sub-agents cannot see globally installed skills (#35272) - impacts `~/.openclaw/skills/` approach
- Skills can silently fail to load with no error (#29122)
- Gateway does not auto-restart after skill install
- `skills.allowBundled: []` semantics inverted (#21709)
- skills.install fails on macOS 26 due to CLT incompatibility (#41722)
- Control UI Skills panel filter hides all skills on click (#41605)

### Channel Plugin Registration
- Discord `registerClient()` unhandled rejection crashes gateway (#37375)
- Telegram partial streaming is fake (#37357), regressed further in 2026.3.8 (#41581)
- Feishu duplicate registration crashes gateway (#37028, #35884, #30908)
- Feishu multi-bot cannot send/receive messages (#41163)
- Custom channel IDs from loaded plugins rejected by config validation (#25775)
- Outbound sendText/sendMedia ignores threadId for Discord (#33554) and Mattermost (#33561)
- Slack `groupPolicy` Zod default moved to config-level (PR #17579) - same bug remains in Discord, Telegram, Signal, IRC, iMessage, BlueBubbles account schemas

## Recent Impactful PRs (last 30 days)

| PR | Title | Area |
|---|---|---|
| #41838 | fix(msteams): use General channel conversation ID as team key for Bot Framework | Channels |
| #41761 | fix(agents): forward memory flush write path | Agents |
| #41662 | fix(telegram): prevent duplicate messages when preview edit times out | Telegram |
| #41599 | fix(secrets): resolve web tool SecretRefs atomically at runtime | Secrets |
| #41468 | Add HTTP 499 to transient error codes for model fallback | Failover |
| #41464 | acp: harden follow-up reliability and attachments | ACP |
| #41442 | acp: enrich streaming updates for IDE clients | ACP |
| #41439 | Sandbox: avoid config barrel mock crashes in constants | Sandbox |
| #41429 | Gateway: tighten node pending drain semantics | Gateway |
| #41427 | acp: forward attachments into ACP runtime sessions | ACP |
| #41422 | fix(agents): probe single-provider billing cooldowns | Failover |
| #41411 | feat(exec): mark child command env with OPENCLAW_CLI | Exec |
| #41401 | fix(cron): do not misclassify empty/NO_REPLY as interim acknowledgement | Cron |
| #41387 | fix(agents): fix Brave llm-context empty snippets | Agents |
| #41338 | Logging: harden probe suppression for observations | Logging |
| #41337 | Agents: add fallback error observations | Agents |
| #41242 | fix(swiftformat): sync GatewayModels exclusions with OpenClawProtocol | iOS |
| #41187 | fix(acp): map error states to end_turn instead of unconditional refusal | ACP |
| #41176 | fix(mattermost): read replyTo param in plugin handleAction send | Mattermost |
| #41090 | fix(plugins): expose model auth API to context-engine plugins | Plugins |
| #41028 | fix(auth): reset cooldown error counters on expiry to prevent infinite escalation | Auth |
| #40998 | Cron: enforce cron-owned delivery contract | Cron |
| #40892 | fix(ui): preserve control-ui auth across refresh | UI |
| #40881 | fix(web-search): recover OpenRouter Perplexity citations from message annotations | Search |
| #40757 | fix(sandbox): pass real workspace to sessions_spawn when workspaceAccess is ro | Sandbox |
| #40740 | fix(telegram): move network fallback to resolver-scoped dispatchers | Telegram |
| #40623 | fix(feishu): pass mediaLocalRoots in sendText local-image auto-convert shim | Feishu |
| #40575 | Fix cron text announce delivery for Telegram targets | Cron |
| #40543 | fix(agents): re-expose configured tools and memory plugins | Agents |
| #40519 | fix: dedupe inbound Telegram DM replies per agent | Telegram |
| #40460 | test(context-engine): add bundle chunk isolation tests for registry | Plugins |
| #40389 | Fix one-shot exit hangs by tearing down cached memory managers | Agents |
| #40385 | gateway: fix global Control UI 404s for symlinked wrappers and bundled package roots | Gateway |
| #40380 | fix(gateway): exit non-zero on restart shutdown timeout | Gateway |
| #37266 | Gateway: path-scoped config schema lookup | Gateway |
| #36590 | feat(openai): add gpt-5.4 support, xhigh thinking, serviceTier | Models |
| #36567 | Enforce prompt hook policy with runtime validation | Plugins |
| #35094 | Gateway: SecretRef support for `gateway.auth.token` (+112 files) | Auth |
| #35080 | fix(subagents): deterministic announce delivery with descendant gating | Agents |

## Dev Gotchas (synthesized)

- **v2026.3.8 introduces new regressions** - Google model 404s (#41249), file tool validation errors (#41209), cron isolated sessions broken (#41798), Telegram streaming regression (#41581). Test before deploying.
- **Cron subsystem is broadly broken** - "Run Now" doesn't execute (#41979), isolated sessions fail (#41798), manual triggers enqueue but never run (#41507), recurring jobs time out (#41558). Avoid cron-dependent workflows until fixed.
- **Tool dispatch instability** - Tools enter infinite repeat loops (#41707), session registry corruption makes tools work once then break (#41335), infinite retry on tool failure (#41291). Multiple independent reports suggest a systemic regression in tool dispatch.
- **Telegram channel is the most regressive area** - DM delivery failures (#41753), replies routed to wrong channel (#41739), streaming regression (#41581), thinking block failures (#41708), media download failures behind proxy (#41569). Six distinct regressions in the latest version.
- **Config validation failure = data loss risk** - unknown config keys silently wipe entire section (#24008), stale keys block startup across versions (#35957), GPT5.4 model names cause JSON parse errors (#41702), new compat keys rejected (#41690). Validate config carefully across version upgrades.
- **Sub-agents can't see globally installed skills** (#35272) - `~/.openclaw/skills/` skills invisible to sub-agents. Directly affects AgentBox's `npx skills add -g` approach in multi-agent mode.
- **Skills can silently fail to load** (#29122) - valid SKILL.md files skipped with zero error. Verify with `openclaw skills list` on provisioned VMs.
- **Shared process model = no plugin isolation** (#12517, #12518) - all plugins share one Node.js process. Wallet keys in x402 plugin are accessible to any other plugin.
- **Prompt cache invalidated every turn** (#36520) - runtime events mutate system prompt, forcing cache miss. Silent cost multiplier on all VMs.
- **Headless startup pitfalls** - doctor check hangs without TTY (#24178), health check times out on slow starts (#22972). Both relevant to cloud-init boot.
- **Plugin prompt hooks need explicit allowlist** (PR #36567) - plugins using `before_prompt_build`/`before_agent_start` blocked unless `hooks.allowPromptInjection` is set.
- **`gateway.auth.mode` now mandatory** (PR #35094) - startup fails if both token+password configured without explicit mode.
- **Custom plugin tools invisible in sandboxed sessions** (#41757) - tools registered by plugins don't surface to sandboxed agents. Must remove sandbox to see them.
- **Gateway stale processes on Windows** (#41804) - `gateway stop` doesn't terminate (#41591). Windows scheduled task runtime leaves orphan processes.
- **ACP has seen heavy stabilization work** - PRs #41464, #41442, #41427, #41425, #41424, #41187 all landed in the last 30 days. ACP error handling, attachments, streaming, and session context all reworked.
- **Failover classification tightened** - HTTP 499 now transient (#41468), billing cooldowns probed per-provider (#41422), cooldown counters reset on expiry (#41028). Test failover behavior after upgrade.
- **Slack groupPolicy Zod default bug exists in ALL channel schemas** (PR #17579) - Telegram, Discord, Signal, IRC, iMessage, BlueBubbles all affected. Per-account groupPolicy config may cause silent message drops.
