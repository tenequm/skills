# OpenClaw Models & Providers

## Models Config

```json
{
  "models": {
    "mode": "merge",
    "providers": {
      "provider-name": {
        "type": "openai-compatible",
        "baseUrl": "https://api.provider.com/v1",
        "apiKey": "${PROVIDER_API_KEY}",
        "models": {
          "model-id": {
            "name": "Display Name",
            "contextWindow": 128000,
            "reasoning": true,
            "costPerMillionInput": 3.0,
            "costPerMillionOutput": 15.0
          }
        }
      }
    },
    "defaults": {
      "model": "provider-name/model-id"
    }
  }
}
```

## Mode: merge vs replace

- **`merge`** (default): provider models added alongside 700+ built-in models
- **`replace`**: hides ALL built-in models, only shows configured providers

Use `replace` for controlled environments (e.g. agentbox VMs) where you want to expose only specific models.

## Provider Types

- `openai-compatible` - any OpenAI-compatible API
- `anthropic` - Anthropic API
- `google` - Google AI (Gemini)
- `google-vertex` - Google Cloud Vertex AI
- `x402` - pay-per-use via HTTP 402 micropayments

## Model APIs

Supported `api` values for model definitions:

| API | Description |
|-----|-------------|
| `openai-completions` | OpenAI Chat Completions API |
| `openai-responses` | OpenAI Responses API (/v1/responses) |
| `openai-codex-responses` | OpenAI Codex Responses API (new) |
| `anthropic-messages` | Anthropic Messages API (default for Anthropic) |
| `google-generative-ai` | Google Generative AI API |
| `github-copilot` | GitHub Copilot API |
| `bedrock-converse-stream` | AWS Bedrock Converse Stream |
| `azure-openai-responses` | Azure OpenAI Responses API |
| `ollama` | Ollama local inference |

## Model Aliases

Built-in aliases resolved in `src/config/defaults.ts`:

| Alias | Resolves to |
|-------|-------------|
| `opus` | `anthropic/claude-opus-4-6` |
| `sonnet` | `anthropic/claude-sonnet-4-6` |
| `gpt` | `openai/gpt-5.4` |
| `gpt-mini` | `openai/gpt-5.4-mini` |
| `gpt-nano` | `openai/gpt-5.4-nano` |
| `gemini` | `google/gemini-3.1-pro-preview` |
| `gemini-flash` | `google/gemini-3-flash-preview` |
| `gemini-flash-lite` | `google/gemini-3.1-flash-lite-preview` |

Anthropic within-provider aliases also supported (e.g. `opus-4.6` -> `claude-opus-4-6`, `sonnet-4.5` -> `claude-sonnet-4-5`).

## Model Compat Config

Extended `ModelCompatConfig` for provider quirks:

```typescript
type ModelCompatConfig = {
  requiresThinkingAsText?: boolean;
  requiresStringContent?: boolean;
  toolSchemaProfile?: string;
  unsupportedToolSchemaKeywords?: string[];
  nativeWebSearchTool?: boolean;
  toolCallArgumentsEncoding?: string;
  requiresMistralToolIds?: boolean;
  requiresOpenAiAnthropicToolPayload?: boolean;
  // ... other compat flags
};
```

## Model Definition Extensions

`ModelDefinitionConfig` now supports:

- `contextTokens?: number` - optional effective runtime cap for compaction/session budgeting. Keeps the provider's native `contextWindow` intact while preferring a smaller practical window.

`ModelProviderConfig` now supports:

- `request?: ConfiguredModelProviderRequest` - optional transport request overrides at the provider level.

## Discovery Toggle Config

Legacy discovery configs are deprecated but still in the type surface for migration compat:

- `bedrockDiscovery` - AWS Bedrock model discovery (existing, with region/filter/refresh options)
- `copilotDiscovery` - GitHub Copilot discovery (simple `{ enabled?: boolean }`)
- `huggingfaceDiscovery` - HuggingFace discovery (simple `{ enabled?: boolean }`)
- `ollamaDiscovery` - Ollama discovery (simple `{ enabled?: boolean }`)

## x402 Provider Pattern

Used in agentbox for pay-per-use inference:

```json
{
  "providers": {
    "agentbox": {
      "type": "x402",
      "baseUrl": "https://instance.agentbox.ai/v1",
      "models": {
        "claude-sonnet-4-20250514": {
          "name": "Claude Sonnet 4",
          "contextWindow": 200000,
          "reasoning": false,
          "costPerMillionInput": 3.0,
          "costPerMillionOutput": 15.0
        }
      }
    }
  }
}
```

x402 providers work with the `openclaw-x402` plugin that intercepts 402 responses and auto-signs Solana USDC payments.

## Model Studio (DashScope/Qwen) Provider

The `modelstudio` extension provides Qwen models via Alibaba Cloud Model Studio with four auth methods:

| Method | Endpoint | Type |
|--------|----------|------|
| `standard-api-key-cn` | `dashscope.aliyuncs.com/compatible-mode/v1` | Pay-as-you-go (China) |
| `standard-api-key` | `dashscope-intl.aliyuncs.com/compatible-mode/v1` | Pay-as-you-go (Global/Intl) |
| `api-key-cn` | `coding.dashscope.aliyuncs.com/v1` | Coding Plan subscription (China) |
| `api-key` | `coding-intl.dashscope.aliyuncs.com/v1` | Coding Plan subscription (Global/Intl) |

Group label: "Qwen (Alibaba Cloud Model Studio)". Default model: `modelstudio/qwen3.5-plus`. All four base URLs are registered as native Model Studio URLs (streaming usage compat applied). Env var: `MODELSTUDIO_API_KEY`. Coding Plan models include `qwen3.5-plus`, `glm-5`, `kimi-k2.5`, `MiniMax-M2.5`.

## StepFun Provider

The `stepfun` extension provides Step AI models with two surfaces:

| Surface | CN Base URL | Intl Base URL |
|---------|-------------|---------------|
| `standard` | `api.stepfun.com/v1` | `api.stepfun.ai/v1` |
| `plan` | `api.stepfun.com/step_plan/v1` | `api.stepfun.ai/step_plan/v1` |

Standard models: `step-3.5-flash`. Plan models: `step-3.5-flash`, `step-3.5-flash-2603`. Region auto-detected from API key endpoint. Env var: `STEPFUN_API_KEY`.

## Anthropic Plugin Architecture

The Anthropic provider is implemented as a bundled plugin (`extensions/anthropic/`). Stream wrappers (beta headers, service tier, fast mode) live in `extensions/anthropic/stream-wrappers.ts` and are composed via the `wrapStreamFn` provider hook.

Key stream wrappers:
- `createAnthropicBetaHeadersWrapper` - injects `anthropic-beta` header (context-1m, fine-grained-tool-streaming, interleaved-thinking, OAuth betas)
- `createAnthropicServiceTierWrapper` - sets `service_tier` (`auto`|`standard_only`) on anthropic-messages requests
- `createAnthropicFastModeWrapper` - resolves `fastMode`/`fast_mode` extra param to `service_tier`

Context-1M beta (`context-1m-2025-08-07`) is auto-added for `claude-opus-4`/`claude-sonnet-4` prefixes when `extraParams.context1m === true`. Skipped for OAuth auth (Anthropic rejects it with OAuth tokens).

Default Anthropic betas: `fine-grained-tool-streaming-2025-05-14`, `interleaved-thinking-2025-05-14`. OAuth adds: `claude-code-20250219`, `oauth-2025-04-20`.

Thinking level defaults to `"adaptive"` for Opus 4.6 and Sonnet 4.6 models when the model is explicitly configured.

## SearXNG Web Search Provider

Bundled plugin (`extensions/searxng/`) providing self-hosted meta-search via SearXNG. Registered via `api.registerWebSearchProvider()`.

Config path: `plugins.entries.searxng.config.webSearch.baseUrl`. Env var: `SEARXNG_BASE_URL`. No API key required - only a base URL to a SearXNG instance.

Tool parameters: `query` (required), `count` (1-10), `categories` (comma-separated: general, news, science, etc.), `language` (e.g. en, de, fr).

Plugin manifest declares `contracts.webSearchProviders: ["searxng"]`. Auto-detect order: 200 (low priority - prefers other configured web search providers first).

## Provider Registration via Plugin

```typescript
// Plugin can register as auth provider
api.registerProviderAuth({
  id: "my-provider",
  authenticate: async (req) => {
    req.headers.set("Authorization", `Bearer ${apiKey}`);
    return req;
  }
});
```

Note: `registerProvider()` is auth-only. It does NOT populate the model catalog. Model metadata (names, context windows, costs) must be defined in config `models.providers`. Plugin-based missing-auth errors now include descriptive error messages.

### Provider Plugin Hooks

| Hook | Purpose |
|------|---------|
| `normalizeModelId` | Provider-owned model-id alias cleanup before resolution |
| `normalizeConfig` | Transform provider config before validation |
| `normalizeTransport` | Adjust request transport options per-provider |
| `resolveConfigApiKey` | Custom API key resolution from config/env |
| `createStreamFn` | Factory for provider-specific streaming implementation |
| `createEmbeddingProvider` | Memory embeddings via provider plugin (for memory plugins) |
| `wrapStreamFn` | Compose provider-specific stream wrappers (beta headers, service tier, etc.) |
| `buildReplayPolicy` | Provider-owned replay/compaction transcript policy |
| `sanitizeReplayHistory` | Provider-specific replay history rewrites after core cleanup |
| `validateReplayTurns` | Final replay-turn validation for strict turn ordering |
| `normalizeToolSchemas` | Rewrite tool schema keywords unsupported by provider transport |
| `inspectToolSchemas` | Inspect tool schemas without mutation |
| `resolveReasoningOutputMode` | Return `"native"` or `"tagged"` for reasoning block handling |
| `resolveTransportTurnState` | Provider transport turn state for replay |
| `resolveWebSocketSessionPolicy` | WebSocket session policy resolution |
| `matchesContextOverflowError` | Detect provider-specific context overflow errors |
| `classifyFailoverReason` | Classify errors into `FailoverReason` for fallback decisions |
| `resolveSystemPromptContribution` | Provider-owned system prompt contributions |
| `applyConfigDefaults` | Apply provider-specific config defaults (e.g. context pruning) |
| `resolveExternalAuthProfiles` | Resolve external auth profiles from provider plugins |
| `shouldDeferSyntheticProfileAuth` | Defer synthetic profile auth to env/config credentials |

### Bundled Provider Policy Surface

A new `provider-public-artifacts.ts` module provides a `BundledProviderPolicySurface` that loads `provider-policy-api.js` from bundled plugins. This surface is checked before plugin hooks for `normalizeConfig`, `applyConfigDefaults`, and `resolveConfigApiKey` - giving bundled plugins fast-path policy application without full plugin activation.

### Provider Plugin Lookup Key

`resolveProviderPluginLookupKey()` resolves the runtime plugin key used for hook dispatch. When a provider's `api` field is set to a non-generic API (anything not in `openai-completions`, `openai-responses`, `anthropic-messages`, `google-generative-ai`), the API value is used as the lookup key instead of the provider key. This lets providers using specialized APIs (like `bedrock-converse-stream` or `ollama`) route to the correct plugin.

## Plugin Auto-Enable for Provider Auth

Plugins with `autoEnableWhenConfiguredProviders` in their manifest are automatically enabled when the corresponding provider has auth configured (auth profiles, model providers, or model refs). For example, the MiniMax plugin declares `autoEnableWhenConfiguredProviders: ["minimax", "minimax-portal"]` and is auto-enabled when a MiniMax API key auth route is configured - even without an explicit `plugins.entries.minimax.enabled: true`.

Detection checks: auth profiles with matching provider, `models.providers` keys, and provider prefixes in model refs (e.g. `minimax/MiniMax-M2.7` in agent defaults).

## Plugin Model Auth API

Context-engine plugins can resolve model credentials via `runtime.modelAuth`:

```typescript
// Resolve auth for a specific model
const auth = await runtime.modelAuth.getApiKeyForModel({ model, cfg });

// Resolve auth for a provider by name
const auth = await runtime.modelAuth.resolveApiKeyForProvider({ provider: "anthropic", cfg });

// auth: { apiKey, profileId?, source, mode: "api-key"|"oauth"|"token"|"aws-sdk" }
```

This is the safe surface for plugins - it strips internal overrides (agentDir/store) that raw `model-auth` helpers expose. Plugins should never import `model-auth` directly.

## Local Provider Auth

`CUSTOM_LOCAL_AUTH_MARKER` for local servers (llama.cpp, vLLM, LocalAI, Ollama) that don't need authentication. These providers skip credential resolution entirely.

## Provider ID Normalization

`normalizeProviderIdForAuth` handles provider alias mappings and coding-plan variants. Provider IDs are normalized before credential lookup to handle cases like `openai-codex` -> `openai`.

Model ID normalization is split into static and runtime layers:
- `model-ref-shared.ts` - static normalization: Anthropic short aliases (`opus-4.6` -> `claude-opus-4-6`), Google preview IDs, xAI, HuggingFace prefix stripping, OpenRouter/Vercel AI Gateway prefixing
- `model-selection-normalize.ts` - runtime normalization: chains static normalization with plugin `normalizeModelId` hooks

## Provider Credential Resolution

`resolveApiKeyForProvider` now supports:
- `lockedProfile?: boolean` - treats profile as user-locked, prevents silent override by env/config credentials
- `credentialPrecedence?: "profile-first" | "env-first"` - controls whether env vars or auth profiles are tried first

Synthetic profile deferral: when a resolved key is a provider-owned synthetic profile marker and the caller hasn't locked the profile, auth resolution falls through to env/config credentials so real credentials take precedence over placeholders.

Explicit config API key preference: when `authHeader: true` is set on a provider config and the auth override resolves to `api-key`, the explicit config API key is preferred before iterating auth profiles.

`applyAuthHeaderOverride()` injects `Authorization: Bearer <apiKey>` headers for providers that set `authHeader: true`, so downstream SDKs (e.g. `@google/genai`) send credentials via standard HTTP Authorization rather than vendor-specific headers.

## Prompt Cache Stripping

`prompt_cache_key` and `prompt_cache_retention` fields are stripped from requests targeting non-OpenAI Responses API endpoints. This prevents 400 errors when models/providers don't support prompt caching metadata.

## Agent Model Defaults

```json
{
  "agents": {
    "defaults": {
      "model": "provider/model-id",
      "timeout": 120000,
      "compaction": { "enabled": true, "threshold": 0.8 },
      "contextPruning": { "enabled": true }
    }
  }
}
```

Per-agent fallback model override is supported via `agents.entries.<id>.model`.

Context pruning defaults are now applied via `applyProviderConfigDefaultsWithPlugin` dispatching to the Anthropic bundled plugin, rather than inline logic in `defaults.ts`.

## Model Selection Improvements

Model selection (`model-selection.ts`) refactored into three modules:
- `model-ref-shared.ts` - shared static `modelKey()`, `parseStaticModelRef()`, per-provider model ID normalization
- `model-selection-normalize.ts` - `parseModelRef()`, `normalizeModelRef()` with plugin hook support
- `model-selection-display.ts` - `resolveModelDisplayRef()`, `resolveModelDisplayName()` for UI rendering

Provider inference: when a model string has no provider prefix, `inferUniqueProviderFromConfiguredModels` checks the configured allowlist before defaulting to the session's current provider. This prevents provider prefix drift when switching models across providers.

Thinking default for 4.6 models: Anthropic Opus 4.6 and Sonnet 4.6 models default to `"adaptive"` thinking when the model is explicitly configured (in model config, primary selection, or per-model settings).

Synthetic catalog entries from allowlisted models now inherit `contextWindow`, `reasoning`, and `input` metadata from the provider's configured model definition, instead of using bare defaults.

## Model Fallback & Transient Errors

Transient HTTP status codes that trigger model fallback:
`499`, `500`, `502`, `503`, `504`, `521`, `522`, `523`, `524`, `529`

HTTP 499 (Client Closed Request) is classified as `timeout` for fallback purposes (or `overloaded` if the response body contains an `overloaded_error` payload). This handles proxies/load balancers that return 499 when upstream is slow.

### Plugin-Driven Failover Classification

Provider plugins can now contribute to failover classification via two new hooks:
- `matchesContextOverflowError` - detect provider-specific context overflow errors (checked across all plugins)
- `classifyFailoverReason` - classify errors into `FailoverReason` values (first plugin match wins)

These are consulted in addition to the built-in classifier.

### Rate-Limit Profile Rotation Cap

When a model hits rate-limit errors, the runner rotates through auth profiles. After exceeding `rateLimitProfileRotationLimit` rotations (configurable), the runner escalates to **cross-provider model fallback** instead of spinning forever across profiles that share the same model quota. This mirrors the existing overload rotation cap behavior.

Without this, per-model quota exhaustion (e.g. Anthropic Sonnet-only rate limits) causes infinite profile rotation when all profiles share the same underlying quota. The escalation throws a `FailoverError` with reason `rate_limit`, triggering the standard model fallback chain.

### Fallback Classifier Priority Order

`classifyFailoverReason()` evaluates in this order (first match wins):

1. `overloaded` - explicit overload signals
2. `timeout` - transient HTTP status codes (5xx), 529 -> `overloaded`
3. `billing` - billing/payment errors
4. `auth_permanent` - permanent auth failures
5. `auth` - transient auth errors
6. `timeout` - JSON `api_error` with transient signal (see below)
7. `format` - Cloud Code Assist format errors
8. `timeout` - generic timeout patterns

### Generalized `api_error` Detection

JSON `api_error` payloads (`"type":"api_error"`) are only classified as transient (`timeout`) when the message matches a transient signal pattern. This handles non-standard providers (e.g. MiniMax returning `"unknown error, 520 (1000)"`).

Transient signals: `internal server error`, `overload`, `temporarily unavailable`, `service unavailable`, `unknown error`, `server error`, `bad gateway`, `gateway timeout`, `upstream error`, `backend error`, `try again later`, `temporarily.*unable`.

Billing/auth errors inside `api_error` payloads are excluded from transient classification - they fall through to their specific classifiers.

### Failover Reasons

Full `FailoverReason` union: `auth`, `auth_permanent`, `format`, `rate_limit`, `overloaded`, `billing`, `timeout`, `model_not_found`, `session_expired`, `unknown`.

`session_expired` (HTTP 410 Gone) handles expired/deleted upstream sessions - not retried via profile rotation.

## Auth Profile Cooldowns

Failure reasons (priority order): `auth_permanent`, `auth`, `billing`, `format`, `model_not_found`, `overloaded`, `timeout`, `rate_limit`, `unknown`.

Cooldown backoff: 1min, 5min, 25min, max 1 hour (exponential). Billing/auth_permanent use separate `disabledUntil` with configurable backoff (default 5h base, 24h max, doubling).

**Cooldown expiry resets error counters.** When `cooldownUntil`/`disabledUntil` expires, `errorCount` and `failureCounts` are cleared so the profile gets a fresh backoff window. Without this, stale error counts from expired cooldowns cause the next transient failure to immediately escalate to a much longer cooldown.

**Single-provider billing probes.** When only one provider is configured (no fallback chain), billing cooldowns are probed on the standard 30s throttle so the setup can recover if the user fixes their balance - without requiring a restart. Multi-provider setups only probe near cooldown expiry so the fallback chain stays preferred.

### Cooldown Probe Policy by Reason

| Reason | Allow cooldown probe | Use transient probe slot | Preserve transient probe slot |
|--------|---------------------|--------------------------|-------------------------------|
| `rate_limit` | yes | yes | no |
| `overloaded` | yes | yes | no |
| `billing` | yes | no | no |
| `unknown` | yes | yes | no |
| `model_not_found` | no | no | yes |
| `format` | no | no | yes |
| `auth` / `auth_permanent` | no | no | yes |
| `session_expired` | no | no | yes |

## Error Sanitization for Chat Replies

Raw provider error payloads are never shown directly to users. `formatAssistantErrorText()` rewrites errors into safe user-facing messages:

- Context overflow -> suggests `/reset` or larger-context model
- Reasoning constraint -> suggests `/think minimal`
- Invalid streaming order -> generic retry message
- Role ordering conflicts -> retry + `/new` suggestion
- Rate-limit/overload -> transient retry message
- Transport errors (ECONNRESET, ETIMEDOUT, etc.) -> connectivity message
- Billing errors -> provider-specific billing message
- Raw HTTP/JSON API payloads -> `formatRawAssistantErrorForUi()` extracts status + message
- Long unhandled errors -> truncated to 600 chars

`sanitizeUserFacingText()` also catches provider error payloads that leak into non-error stream chunks (e.g. Codex error prefixes) and rewrites them.

## Provider Replay Policy

Provider plugins now own replay/compaction transcript policy via `buildReplayPolicy` hook. The `ProviderReplayPolicy` type controls:

- `sanitizeMode` - `"full"` or `"images-only"`
- `sanitizeToolCallIds` / `toolCallIdMode` - strict tool-call ID regeneration (`"strict"` or `"strict9"`)
- `preserveSignatures` - preserve byte-for-byte thinking block signatures
- `dropThinkingBlocks` - strip thinking blocks from prior turns
- `repairToolUseResultPairing` - fix orphaned tool use/result blocks
- `applyAssistantFirstOrderingFix` / `validateGeminiTurns` / `validateAnthropicTurns` - turn ordering fixes
- `allowSyntheticToolResults` - permit synthetic tool results in replay

Helper builders in `provider-replay-helpers.ts`:
- `buildOpenAICompatibleReplayPolicy()` - builds policy for OpenAI-compatible APIs (completions/responses/codex)
- `buildStrictAnthropicReplayPolicy()` - strict Anthropic replay with signature preservation
- `buildAnthropicReplayPolicyForModel()` - model-aware Anthropic policy (preserves thinking blocks for 4.5+ models)
- `shouldPreserveThinkingBlocks()` - returns true for Claude 4.5+ models (Opus 4.5+, Sonnet 4.5+, Haiku 4.5+) where dropping thinking blocks breaks prompt cache prefix matching

Additional replay hooks: `sanitizeReplayHistory` (post-core cleanup rewrites), `validateReplayTurns` (strict turn ordering validation).

## Anthropic Thinking Replay Preservation

Anthropic Claude endpoints can reject replayed `thinking` blocks unless original signatures are preserved byte-for-byte. The replay policy handles this per-provider:

- `preserveSignatures` in replay policy determines whether the provider preserves thinking block signatures
- `dropThinkingBlocks` policy strips thinking blocks at send-time for providers where replay would fail
- Claude 4.5+ models (Opus 4.5/4.6, Sonnet 4.5/4.6, Haiku 4.5) preserve thinking blocks natively - dropping them breaks prompt cache prefix matching
- Pre-4.5 models (claude-3-7-sonnet, claude-3-5-sonnet) require dropping thinking blocks

## Default Context Windows

Claude Opus/Sonnet 4.6 default context window updated to 1M tokens (PR #49941).

## Model Selection Priority

1. Agent-specific model (in `agents.entries.<id>.model`)
2. Agent defaults (`agents.defaults.model`)
3. Session-level override (via chat command)
4. Built-in default (Claude Sonnet)

## Plugin Activation State

Plugin enablement uses `resolveEffectivePluginActivationState()` (renamed from `resolveEffectiveEnableState()`), returning `.activated` (previously `.enabled`). The `enabledByDefault` flag from plugin manifests is now passed through to the activation resolver. Provider discovery uses `resolveDiscoveredProviderPluginIds()` which returns all plugins with registered providers (regardless of activation state), while `resolveEnabledProviderPluginIds()` filters to only activated plugins.

## Provider Plugin Loading

Provider plugin loading (`providers.runtime.ts`) refactored with a two-mode architecture:
- **runtime mode** (default): uses `resolveRuntimePluginRegistry()` with the shared plugin registry, returns `[]` if a registry load is already in-flight (prevents re-entrant plugin activation)
- **setup mode**: uses `loadOpenClawPlugins()` directly with `resolveDiscoveredProviderPluginIds()` for initial setup/discovery flows

Plugin resolution now supports `providerRefs` and `modelRefs` parameters for targeted plugin loading - only the plugins that own the specified providers/models are loaded, with their IDs auto-activated in the runtime config.
