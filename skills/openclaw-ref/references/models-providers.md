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
| `ollama` | Ollama local inference |

## Model Aliases

Built-in aliases resolved in `src/config/defaults.ts`:

| Alias | Resolves to |
|-------|-------------|
| `opus` | `anthropic/claude-opus-4-6` |
| `sonnet` | `anthropic/claude-sonnet-4-6` |
| `gpt` | `openai/gpt-5.4` |
| `gpt-mini` | `openai/gpt-5-mini` |
| `gemini` | `google/gemini-3.1-pro-preview` |
| `gemini-flash` | `google/gemini-3-flash-preview` |
| `gemini-flash-lite` | `google/gemini-3.1-flash-lite-preview` |

Anthropic within-provider aliases also supported (e.g. `claude-3-haiku` -> specific model ID).

## Model Compat Config

Extended `ModelCompatConfig` for provider quirks:

```typescript
type ModelCompatConfig = {
  requiresThinkingAsText?: boolean;
  toolSchemaProfile?: string;
  nativeWebSearchTool?: boolean;
  toolCallArgumentsEncoding?: string;
  requiresMistralToolIds?: boolean;
  requiresOpenAiAnthropicToolPayload?: boolean;
  // ... other compat flags
};
```

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

### New Provider Plugin Hooks

| Hook | Purpose |
|------|---------|
| `normalizeModelId` | Provider-owned model-id alias cleanup before resolution |
| `normalizeConfig` | Transform provider config before validation |
| `normalizeTransport` | Adjust request transport options per-provider |
| `resolveConfigApiKey` | Custom API key resolution from config/env |
| `createStreamFn` | Factory for provider-specific streaming implementation |
| `createEmbeddingProvider` | Memory embeddings via provider plugin (for memory plugins) |

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

## Model Fallback & Transient Errors

Transient HTTP status codes that trigger model fallback:
`499`, `500`, `502`, `503`, `504`, `521`, `522`, `523`, `524`, `529`

HTTP 499 (Client Closed Request) is classified as `timeout` for fallback purposes (or `overloaded` if the response body contains an `overloaded_error` payload). This handles proxies/load balancers that return 499 when upstream is slow.

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

## Auth Profile Cooldowns

Failure reasons (priority order): `auth_permanent`, `auth`, `billing`, `format`, `model_not_found`, `overloaded`, `timeout`, `rate_limit`, `unknown`.

Cooldown backoff: 1min, 5min, 25min, max 1 hour (exponential). Billing/auth_permanent use separate `disabledUntil` with configurable backoff (default 5h base, 24h max, doubling).

**Cooldown expiry resets error counters.** When `cooldownUntil`/`disabledUntil` expires, `errorCount` and `failureCounts` are cleared so the profile gets a fresh backoff window. Without this, stale error counts from expired cooldowns cause the next transient failure to immediately escalate to a much longer cooldown.

**Single-provider billing probes.** When only one provider is configured (no fallback chain), billing cooldowns are probed on the standard 30s throttle so the setup can recover if the user fixes their balance - without requiring a restart. Multi-provider setups only probe near cooldown expiry so the fallback chain stays preferred.

## Default Context Windows

Claude Opus/Sonnet 4.6 default context window updated to 1M tokens (PR #49941).

## Model Selection Priority

1. Agent-specific model (in `agents.entries.<id>.model`)
2. Agent defaults (`agents.defaults.model`)
3. Session-level override (via chat command)
4. Built-in default (Claude Sonnet)
