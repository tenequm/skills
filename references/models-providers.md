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
- `x402` - pay-per-use via HTTP 402 micropayments

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

Note: `registerProvider()` is auth-only. It does NOT populate the model catalog. Model metadata (names, context windows, costs) must be defined in config `models.providers`.

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

## Model Fallback & Transient Errors

Transient HTTP status codes that trigger model fallback:
`499`, `500`, `502`, `503`, `504`, `521`, `522`, `523`, `524`, `529`

HTTP 499 (Client Closed Request) is classified as `timeout` for fallback purposes (or `overloaded` if the response body contains an `overloaded_error` payload). This handles proxies/load balancers that return 499 when upstream is slow.

## Auth Profile Cooldowns

Failure reasons (priority order): `auth_permanent`, `auth`, `billing`, `format`, `model_not_found`, `overloaded`, `timeout`, `rate_limit`, `unknown`.

Cooldown backoff: 1min, 5min, 25min, max 1 hour (exponential). Billing/auth_permanent use separate `disabledUntil` with configurable backoff (default 5h base, 24h max, doubling).

**Cooldown expiry resets error counters.** When `cooldownUntil`/`disabledUntil` expires, `errorCount` and `failureCounts` are cleared so the profile gets a fresh backoff window. Without this, stale error counts from expired cooldowns cause the next transient failure to immediately escalate to a much longer cooldown.

**Single-provider billing probes.** When only one provider is configured (no fallback chain), billing cooldowns are probed on the standard 30s throttle so the setup can recover if the user fixes their balance - without requiring a restart. Multi-provider setups only probe near cooldown expiry so the fallback chain stays preferred.

## Model Selection Priority

1. Agent-specific model (in `agents.entries.<id>.model`)
2. Agent defaults (`agents.defaults.model`)
3. Session-level override (via chat command)
4. Built-in default (Claude Sonnet)
