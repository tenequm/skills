# OpenClaw GitHub Context
> Last refreshed: 2026-03-06T18:00:00Z

## Open Bugs (critical for development)

### Plugin System
- **#12854** - CJS dependencies fail with "require is not defined" under jiti loader - blocks any plugin importing CJS npm packages
- **#36377** - Mem0/sqlite3 native bindings broken under jiti (recurring: #31676, #31677) - blocks plugins with native modules
- **#36754** - Extension discovery silently skips symlinked plugin directories (`isDirectory()` returns false for symlinks)
- **#28122** - pnpm global install: bundled plugin manifests rejected as 'unsafe path' - gateway refuses to start (15 reactions)
- **#19312** - 81% bundled plugins affected by unresolved `workspace:*` dependencies in global installs
- **#36917** - [SEC] Plugin runtime config still exposes provider auth fields despite isolation PR
- **#25859** - Plugin `api.registerHook("message:received")` listed but never fires - hooks cleared at gateway startup
- **#37028** - Feishu duplicate registration crashes gateway (not just warning)
- **#33135** - No `dispatchAgentTurn` in plugin runtime API - webhook plugins can't trigger agent runs

### Config Validation
- **#5052** - [SEC] Config validation failure silently drops security settings to insecure defaults (returns `{}`)
- **#37309** - vLLM baseUrl change ignored - agent caches old URL in hidden `.openclaw/agent/main/agent/models.json`
- **#24008** - Unrecognized config keys silently wipe and reset entire section on restart
- **#35957** - Stale keys from v2026.3.2 block gateway startup in v2026.3.3
- **#36792** - Gateway promises "best-effort config" on invalid config but exits instead
- **#32583** - MCP servers config not in schema - adding to openclaw.json fails with 'Unrecognized key'
- **#28698** - `config.patch` tool dumps full config into LLM context, wasting tokens

### Gateway Startup
- **#36585** - TLS null dereference crash during socket reconnection under concurrent load
- **#34539** - structuredClone FATAL ERROR in orphaned subagent reconciliation after unclean exit
- **#37340** - v2026.3.2 `--install-daemon` errors on detecting missing service instead of installing
- **#30257** - boot-md hook misses `gateway:startup` event (race condition - hook registers after event fires)
- **#28647** - Discord channels unresolved on startup (timing issue in channel resolution)
- **#24178** - Doctor check blocks indefinitely without TTY - hangs headless/automated deployments
- **#22972** - Health check times out on slow startups
- **#36672** - HTTP 400 invalid JSON on every request - gateway bricked after initial success

### Secrets/Auth
- **#37303** - Onboarding crashes with exec secret provider - `getStatus()` eagerly resolves SecretRef tokens
- **#37142** - MiniMax 401 - anthropic-messages mode doesn't pass Bearer header
- **#37123** - Azure OpenAI not appearing during onboarding wizard
- **#36913** - Intermittent 401 "Invalid bearer token" from gateway probe
- **#12517** - [SEC] All 31 plugins share single Node.js process - lateral movement across plugins
- **#12518** - [SEC] All plugin credentials in shared `process.env` - no isolation between channels
- **#11829** - [SEC] API keys leak to LLM via tool outputs, error messages, system prompts

### Channels
- **#37375** - Discord channel fetch failure crashes gateway - unhandled rejection in `registerClient()` (76 crashes/day)
- **#36742** - Dual-account Telegram config crashes gateway under systemd
- **#36739/#36725** - Telegram multi-account: non-default accounts silently drop all messages
- **#36687** - `session.dmScope` reset to "main" causes cross-channel reply leakage
- **#37357** - Telegram partial streaming is fake - waits for full response
- **#36753** - `groupAllowFrom` expects user IDs not group IDs
- **#37415** - Feishu websocket fails on WSL2
- **#12534** - [SEC] Nostr plugin exposes unauthenticated `runtime.config.writeConfigFile()` - full config takeover

### Agent Runtime
- **#37048** - v2026.3.2 sends `parallel_tool_calls: true` unconditionally - breaks all tools on non-OpenAI models
- **#37466** - Unable to load exec tool (v2026.3.2 regression)
- **#36994** - Tools work on first run then break persistently - requires full reinstall
- **#36520** - Runtime events mutate system prompt every turn, invalidating prompt cache (silent cost multiplier)
- **#36634** - `agents_list` tool returns only "main" despite multiple agents configured
- **#36134** - `sessions_spawn` silently falls back to Anthropic when targeting Gemini
- **#37040** - Agent runs complete with empty `content: []` and zero usage on custom providers
- **#36968** - v2026.3.2 can't access local files even in workspace directory

### Skills
- **#35272** - Sub-agents cannot access shared skills from `~/.openclaw/skills/` - directly impacts `npx skills add -g`
- **#29122** - Workspace skills silently not loading (no error, valid SKILL.md)
- **#21709** - `skills.allowBundled: []` allows all instead of blocking all (semantics bug)

### TUI
- **#37243** - TUI replies routed to Telegram instead of TUI (100% repro with Telegram configured)
- **#37168** - TUI assistant replies not displayed (`--deliver` flag ignored)
- **#36897** - TUI not receiving agent messages (`messagesHandled: 0`)

### Cron
- **#37299** - `cron list`/`cron run` TypeError "Cannot read properties of undefined (reading 'kind')"
- **#37198** - Cron job with "gateway restart" in message causes infinite restart loop

## Breaking Changes & Regressions

### Breaking in v2026.3.2
- `parallel_tool_calls: true` sent unconditionally - breaks non-OpenAI models (#37048)
- TUI replies rerouted to Telegram when Telegram configured (#37243)
- Exec tool fails to load (#37466)
- Gateway install/onboard fails on Linux (#37340)
- Onboarding crashes with exec secret providers (#37303)
- File access in workspace directory broken (#36968)
- Cron commands throw TypeError (#37299)
- Telegram multi-account: secondary accounts drop messages (#36739)

### Breaking Guardrail (PR #35094)
- `gateway.auth.mode` now mandatory when both `gateway.auth.token` and `gateway.auth.password` configured - startup fails until mode is explicit

### Plugin Prompt Hook Policy (PR #36567)
- New `plugins.entries.<id>.hooks.allowPromptInjection` required for plugins using `before_prompt_build` / `before_agent_start` hooks - blocked at runtime without it

### Active Regressions
| Issue | Summary |
|-------|---------|
| #37375 | Discord fetch failure crash-loops gateway |
| #37357 | Telegram fake streaming in partial mode |
| #37340 | Gateway install broken on Linux |
| #37322 | 404 with Bailian/aliyun providers |
| #37318 | Fresh install ENOENT on memory files |
| #37303 | Onboarding crash with exec secret provider |
| #37299 | cron list/run TypeError |
| #37243 | TUI replies go to Telegram |
| #37168 | TUI doesn't display assistant replies |
| #37142 | MiniMax 401 in anthropic-messages mode |
| #37123 | Azure OpenAI missing from onboarding |
| #37048 | parallel_tool_calls breaks non-OpenAI models |
| #36994 | Windows Pinokio tools/exec breaking |
| #36968 | read tool unavailable in workspace |
| #36913 | Intermittent 401 from gateway probe |
| #36897 | TUI messagesHandled: 0 |
| #35078 | Native plugin bindings (node_sqlite3) fail under jiti |
| #32106 | Aggressive compaction loop with memoryFlush |

### Config Migration Hazards
- **#37309** - Changing model baseUrl has no effect due to hidden models.json cache
- **#35957** - Stale keys from v2026.3.2 block startup on v2026.3.3
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

### Skills
- Sub-agents cannot see globally installed skills (#35272) - impacts `~/.openclaw/skills/` approach
- Skills can silently fail to load with no error (#29122)
- Gateway does not auto-restart after skill install
- `skills.allowBundled: []` semantics inverted (#21709)

### Channel Plugin Registration
- Discord `registerClient()` unhandled rejection crashes gateway (#37375)
- Telegram partial streaming is fake (#37357)
- Feishu duplicate registration crashes gateway (#37028, #35884, #30908)
- Custom channel IDs from loaded plugins rejected by config validation (#25775)
- Outbound sendText/sendMedia ignores threadId for Discord (#33554) and Mattermost (#33561)
- Slack `groupPolicy` Zod default moved to config-level (PR #17579) - same bug remains in Discord, Telegram, Signal, IRC, iMessage, BlueBubbles account schemas

## Recent Impactful PRs (last 30 days)

| PR | Title | Area |
|---|---|---|
| #37266 | Gateway: path-scoped config schema lookup | Gateway |
| #36590 | feat(openai): add gpt-5.4 support, xhigh thinking, serviceTier | Models |
| #36567 | Enforce prompt hook policy with runtime validation | Plugins |
| #35094 | Gateway: SecretRef support for `gateway.auth.token` (+112 files) | Auth |
| #35080 | fix(subagents): deterministic announce delivery with descendant gating | Agents |
| #37179 | Plugins: avoid false integrity drift prompts on unpinned updates | Plugins |
| #37135 | fix(session): keep direct WebChat replies on WebChat | Routing |
| #37033 | fix(slack): record app_mention retry key before dedupe check | Slack |
| #36683 | feat(telegram/acp): Topic Binding, Pin Binding Message | Telegram |
| #36547 | Harden Telegram poll gating and schema consistency | Telegram |
| #35489 | feat(agents): flush reply pipeline before compaction wait | Compaction |
| #35177 | Add `prependSystemContext`/`appendSystemContext` to `before_prompt_build` | Plugins |
| #34068 | Gateway: support `image_url` in chat completions, 20MB body limit | API |
| #17579 | fix(slack): prevent Zod default groupPolicy from breaking multi-account | Slack |
| #16788 | feat(hooks): emit `before_compaction`/`after_compaction` lifecycle hooks | Hooks |
| #36794 | Plugins: clarify registerHttpHandler migration errors | Plugins |
| #36783 | fix(agents): classify insufficient_quota 400s as billing | Failover |
| #36646 | fix(failover): narrow service-unavailable to require overload indicator | Failover |
| #36603 | fix(config): hash merged schema cache key to prevent RangeError | Config |
| #36078 | fix: enforce 600 perms for cron store and run logs | Security |
| #33813 | Fix failover for zhipuai 1310 Weekly/Monthly Limit Exhausted | Failover |

## Dev Gotchas (synthesized)

- **v2026.3.2 is highly regressive** - 18+ regressions across tools, TUI, Telegram, Discord, onboarding, cron. Test thoroughly before baking into images.
- **`parallel_tool_calls: true` sent unconditionally** (#37048) - breaks ALL tools on non-OpenAI models. Critical for any custom provider setup in OPENCLAW_BASE_CONFIG.
- **Config validation failure = silent security downgrade** (#5052) - if config has any validation issue, auth/security settings silently reset to permissive defaults. Validate config carefully.
- **Hidden models.json cache** (#37309) - changing model baseUrl in served config has no effect until `.openclaw/agent/main/agent/models.json` is deleted. VMs may need cache cleanup.
- **Sub-agents can't see globally installed skills** (#35272) - `~/.openclaw/skills/` skills invisible to sub-agents. Directly affects AgentBox's `npx skills add -g` approach in multi-agent mode.
- **Skills can silently fail to load** (#29122) - valid SKILL.md files skipped with zero error. Verify with `openclaw skills list` on provisioned VMs.
- **Shared process model = no plugin isolation** (#12517, #12518) - all plugins share one Node.js process. Wallet keys in x402 plugin are accessible to any other plugin.
- **Prompt cache invalidated every turn** (#36520) - runtime events mutate system prompt, forcing cache miss. Silent cost multiplier on all VMs.
- **Headless startup pitfalls** - doctor check hangs without TTY (#24178), health check times out on slow starts (#22972). Both relevant to cloud-init boot.
- **Plugin prompt hooks need explicit allowlist** (PR #36567) - plugins using `before_prompt_build`/`before_agent_start` blocked unless `hooks.allowPromptInjection` is set.
- **`gateway.auth.mode` now mandatory** (PR #35094) - startup fails if both token+password configured without explicit mode.
- **Stale config keys block startup across versions** (#35957) - config migration between OpenClaw versions can leave blocking keys. Test OPENCLAW_BASE_CONFIG against new versions.
- **Slack groupPolicy Zod default bug exists in ALL channel schemas** (PR #17579) - Telegram, Discord, Signal, IRC, iMessage, BlueBubbles all affected. Per-account groupPolicy config may cause silent message drops.
- **20MB body limit for chat completions** (PR #34068) - if reverse proxy has lower limit, image requests fail.
- **Failover classification tightened** (PRs #36646, #36783) - 400 insufficient_quota now billing, 503 requires overload indicator. Test failover behavior after upgrade.
