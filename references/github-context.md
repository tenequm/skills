# OpenClaw GitHub Context
> Last refreshed: 2026-03-06T14:30:00Z

## Open Bugs (critical for development)

### Plugin System
- **#36994** - Exec and tools keep breaking on Windows Pinokio - tools folder missing, local models show "unknown"
- **#36968** - v2026.3.2 can't access local files - agent says `read` tool unavailable despite workspace config

### Config Validation
- **#37309** - vLLM base URL change ignored - agent caches old URL in hidden `.openclaw/agent/main/agent/models.json`
- **#37388** - Log file doesn't rotate at midnight - stuck appending to previous day's file until restart

### Gateway Startup
- **#37340** - v2026.3.2 gateway install bug - `--install-daemon` errors on detecting missing service instead of installing
- **#37375** - Discord channel fetch failure crashes gateway - unhandled rejection in `GatewayPlugin.registerClient()` (76 crashes/day)
- **#37036** - Windows dashboard shows "Not Found" when opening via `openclaw dashboard`

### Secrets/Auth
- **#37303** - Onboarding crashes with exec secret provider - `getStatus()` eagerly resolves SecretRef tokens instead of checking config
- **#37142** - MiniMax provider 401 - anthropic-messages mode doesn't pass Bearer header correctly
- **#37123** - Azure OpenAI not appearing during onboarding wizard
- **#36913** - Intermittent 401 "Invalid bearer token" from gateway probe - self-healing but disruptive
- **#24192** - Prompt injection via `System:` message causes gateway latency (security, long-standing)

### Channels
- **#37415** - Feishu websocket fails on WSL2 due to NAT networking
- **#37357** - Telegram fake streaming - partial mode waits for full response before displaying
- **#37344** - Discord messages not sent despite proxy config - fetch fails on reply sending
- **#37307** - Cron + Mistral model timeout, then "Action send requires a target" on Telegram delivery

### Agent Runtime
- **#37322** - TUI and web return 404 with Bailian/aliyun provider models
- **#37318** - Fresh install reads non-existent memory files, triggers ENOENT then persistent 403s
- **#37040** - Agent runs complete with empty `content: []` and zero usage on custom providers
- **#37048** - v2026.3.2 sends `parallel_tool_calls: true` to models that don't support it - breaks all tools

### TUI
- **#37243** - TUI replies routed to Telegram instead of TUI after upgrade (100% repro with Telegram configured)
- **#37168** - TUI assistant replies not displayed in terminal (`--deliver` flag ignored)
- **#36897** - TUI not receiving agent messages - `messagesHandled: 0` in heartbeat

### Cron
- **#37299** - `cron list`/`cron run` throw TypeError "Cannot read properties of undefined (reading 'kind')"
- **#37198** - Cron job with "gateway restart" in message causes infinite restart loop

## Breaking Changes & Regressions

### Breaking in v2026.3.2
- `tools.profile` defaults to `messaging` for new installs (was broad coding/system tools)
- `parallel_tool_calls: true` sent unconditionally - breaks models that don't support it (#37048)
- TUI replies rerouted to Telegram when Telegram channel configured (#37243)
- Gateway install/onboard fails on Linux (#37340)
- Onboarding crashes with exec secret providers (#37303)

### Active Regressions (v2026.3.2)
| Issue | Summary |
|-------|---------|
| #37375 | Discord fetch failure crash-loops gateway |
| #37357 | Telegram fake streaming in partial mode |
| #37344 | Discord reply sending fails with proxy |
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

### Config Migration Hazards
- **#37309** - Changing model baseUrl has no effect due to hidden models.json cache file
- **#37340** - v2026.3.2 `--install-daemon` fails on missing service detection

## Plugin/Extension/Config Known Issues

### Plugin Loading
- **#36994** - Windows Pinokio: tools folder missing, models "unknown" after first run
- **#36968** - `read` tool unavailable despite workspace directory existing (Docker + Qwen3)
- Removed `api.registerHttpHandler()` gives clear migration error (#36794)

### Skills
- Skills installed to `~/.openclaw/skills/` still invisible to sub-agents
- Gateway does not auto-restart after skill install

### Channel Plugin Registration
- Discord `GatewayPlugin.registerClient()` has unhandled rejection that crashes gateway (#37375)
- Telegram partial streaming is fake-streaming (#37357)
- Feishu websocket broken on WSL2 (#37415)

## Recent Impactful PRs (last 30 days)

| PR | Title | Area |
|---|---|---|
| #37266 | Gateway: path-scoped config schema lookup | Gateway |
| #37247 | Skills/nano-banana-pro: support hosted input images | Skills |
| #37179 | Plugins: avoid false integrity drift prompts on unpinned updates | Plugins |
| #37135 | fix(session): keep direct WebChat replies on WebChat | Session/Routing |
| #37033 | fix(slack): record app_mention retry key before dedupe check | Slack |
| #37023 | CLI: make read-only SecretRef status flows degrade safely | CLI/Secrets |
| #36904 | Diffs: restore system prompt guidance | Diffs Plugin |
| #36835 | Memory: handle SecretRef keys in doctor embeddings | Memory |
| #36794 | Plugins: clarify registerHttpHandler migration errors | Plugins |
| #36789 | Doctor: warn on implicit heartbeat directPolicy | Doctor |
| #36783 | fix(agents): classify insufficient_quota 400s as billing | Failover |
| #36781 | fix(ui): bump dompurify to 3.3.2 | Security |
| #36746 | fix(telegram): clear DM draft after materialize | Telegram |
| #36735 | test(agents): add provider-backed failover regressions | Testing |
| #36683 | feat(telegram/acp): Topic Binding, Pin Binding Message | Telegram/ACP |
| #36656 | fix(slack): propagate mediaLocalRoots through Slack send path | Slack |
| #36646 | fix(failover): narrow service-unavailable to require overload indicator | Failover |
| #36615 | refactor(agents): share failover HTTP status classification | Failover |
| #36603 | fix(config): hash merged schema cache key to prevent RangeError | Config |

## Dev Gotchas (synthesized)

- **v2026.3.2 is highly regressive** - 17+ regressions across TUI, Telegram, Discord, onboarding, cron, tools. Test thoroughly before deploying.
- **TUI is broken in v2026.3.2** - replies go to wrong channel (#37243), not displayed (#37168), or messagesHandled:0 (#36897). Three separate TUI bugs.
- **`parallel_tool_calls: true` sent unconditionally** (#37048) - breaks all tools on non-OpenAI models. Critical for any custom provider setup.
- **Onboarding crashes with exec secret providers** (#37303) - `getStatus()` eagerly resolves tokens. Avoid exec secret providers during onboard.
- **Discord gateway crashes on network blips** (#37375) - unhandled rejection in registerClient. Can cause 76+ crashes/day.
- **Hidden models.json cache** (#37309) - changing baseUrl in config has no effect. Must manually edit `.openclaw/agent/main/agent/models.json`.
- **Telegram partial streaming is fake** (#37357) - waits for full response before displaying. Use `"block"` mode instead.
- **SecretRef handling improved** (#37023, #36835) - CLI status flows now degrade safely, doctor handles SecretRef memory keys. But onboarding still crashes (#37303).
- **Failover classification tightened** (#36646, #36615, #36783) - 400 insufficient_quota now billing, 503 requires overload indicator. Test failover after upgrade.
- **WebChat replies now stay on WebChat** (#37135) - previously leaked to other channels via persisted delivery routing.
- **Plugin update integrity drift fixed** (#37179) - unpinned version bumps no longer trigger false warnings.
- **Config schema cache hashed** (#36603) - prevents RangeError with 16+ channel accounts.
