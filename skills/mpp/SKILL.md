---
name: mpp
description: "Build with MPP (Machine Payments Protocol) - the open protocol for machine-to-machine payments over HTTP 402. Use when developing paid APIs, payment-gated content, AI agent payment flows, MCP tool payments, pay-per-token streaming, or any service using HTTP 402 Payment Required. Covers the mppx TypeScript SDK with Hono/Express/Next.js/Elysia middleware, pympp Python SDK, and mpp Rust SDK. Supports Tempo stablecoins, Stripe cards, Lightning Bitcoin, and custom payment methods. Includes charge (one-time) and session (streaming pay-as-you-go) intents. Make sure to use this skill whenever the user mentions mpp, mppx, machine payments, HTTP 402 payments, Tempo payments, payment channels, pay-per-token, paid API endpoints, or payment-gated services."
metadata:
  version: "0.1.0"
---

# MPP - Machine Payments Protocol

MPP is an open protocol (co-authored by Tempo and Stripe) that standardizes HTTP `402 Payment Required` for machine-to-machine payments. Clients pay in the same HTTP request - no accounts, API keys, or checkout flows needed.

The core protocol spec is submitted to the IETF as the [Payment HTTP Authentication Scheme](https://datatracker.ietf.org/doc/draft-ryan-httpauth-payment/).

## When to Use

- Building a **paid API** that charges per request
- Adding a **paywall** to endpoints or content
- Enabling **AI agents** to pay for services autonomously
- **MCP tool calls** that require payment
- **Pay-per-token streaming** (LLM inference, content generation)
- **Session-based metered billing** (pay-as-you-go)
- Accepting **stablecoins** (Tempo), **cards** (Stripe), or **Bitcoin** (Lightning) for API access
- Building a **payments proxy** to gate existing APIs (OpenAI, Anthropic, etc.)

## Core Architecture

Three primitives power every MPP payment:

1. **Challenge** - server-issued payment requirement (in `WWW-Authenticate: Payment` header)
2. **Credential** - client-submitted payment proof (in `Authorization: Payment` header)
3. **Receipt** - server confirmation of successful payment (in `Payment-Receipt` header)

```
Client                                          Server
  │  (1) GET /resource                            │
  ├──────────────────────────────────────────────>│
  │         (2) 402 + WWW-Authenticate: Payment   │
  │<──────────────────────────────────────────────┤
  │  (3) Sign payment proof                       │
  │  (4) GET /resource + Authorization: Payment   │
  ├──────────────────────────────────────────────>│
  │         (5) Verify + settle                   │
  │         (6) 200 OK + Payment-Receipt          │
  │<──────────────────────────────────────────────┤
```

## Payment Methods & Intents

MPP is payment-method agnostic. Each method defines its own settlement rail:

| Method | Rail | SDK Package | Status |
|--------|------|-------------|--------|
| [Tempo](/payment-methods/tempo) | TIP-20 stablecoins on Tempo chain | `mppx` (built-in) | Production |
| [Stripe](/payment-methods/stripe) | Cards, wallets via Shared Payment Tokens | `mppx` (built-in) | Production |
| [Lightning](/payment-methods/lightning) | Bitcoin over Lightning Network | `@buildonspark/lightning-mpp-sdk` | Production |
| [Card](/payment-methods/card) | Encrypted network tokens (Visa) | `mpp-card` | Production |
| Custom | Any rail | `Method.from()` + `Method.toClient/toServer` | Extensible |

Two payment intents:

| Intent | Pattern | Best For |
|--------|---------|----------|
| **charge** | One-time payment per request | API calls, content access, fixed-price endpoints |
| **session** | Pay-as-you-go over payment channels | LLM streaming, metered billing, high-frequency APIs |

## Quick Start: Server (TypeScript)

```typescript
import { Mppx, tempo } from 'mppx/server'

const mppx = Mppx.create({
  methods: [tempo({
    currency: '0x20c0000000000000000000000000000000000000', // pathUSD
    recipient: '0xYourAddress',
  })],
})

export async function handler(request: Request) {
  const result = await mppx.charge({ amount: '0.01' })(request)
  if (result.status === 402) return result.challenge
  return result.withReceipt(Response.json({ data: '...' }))
}
```

Install: `npm install mppx viem`

## Quick Start: Client (TypeScript)

```typescript
import { privateKeyToAccount } from 'viem/accounts'
import { Mppx, tempo } from 'mppx/client'

// Polyfills globalThis.fetch to handle 402 automatically
Mppx.create({
  methods: [tempo({ account: privateKeyToAccount('0x...') })],
})

const res = await fetch('https://api.example.com/paid')
// Payment happens transparently when server returns 402
```

## Quick Start: Server (Python)

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mpp import Challenge
from mpp.server import Mpp
from mpp.methods.tempo import tempo, ChargeIntent

app = FastAPI()
mpp = Mpp.create(
    method=tempo(
        currency="0x20c0000000000000000000000000000000000000",
        recipient="0xYourAddress",
        intents={"charge": ChargeIntent()},
    ),
)

@app.get("/resource")
async def get_resource(request: Request):
    result = await mpp.charge(
        authorization=request.headers.get("Authorization"),
        amount="0.50",
    )
    if isinstance(result, Challenge):
        return JSONResponse(
            status_code=402,
            content={"error": "Payment required"},
            headers={"WWW-Authenticate": result.to_www_authenticate(mpp.realm)},
        )
    credential, receipt = result
    return {"data": "paid content"}
```

Install: `pip install "pympp[tempo]"`

## Quick Start: Server (Rust)

```rust
use mpp::server::{Mpp, tempo, TempoConfig};
use mpp::{parse_authorization, format_www_authenticate};

let mpp = Mpp::create(tempo(TempoConfig {
    recipient: "0xYourAddress",
}))?;

let challenge = mpp.charge("0.50")?;
let header = format_www_authenticate(&challenge)?;
// Respond with 402 + WWW-Authenticate header

// On retry with credential:
let credential = parse_authorization(auth_header)?;
let receipt = mpp.verify_credential(&credential).await?;
// Respond with 200 + paid content
```

Install: `cargo add mpp --features tempo,server`

## Framework Middleware (TypeScript)

Each framework has its own import for ergonomic middleware:

```typescript
// Next.js
import { Mppx, tempo } from 'mppx/nextjs'
const mppx = Mppx.create({ methods: [tempo({ currency: '0x20c0...', recipient: '0x...' })] })
export const GET = mppx.charge({ amount: '0.1' })(() => Response.json({ data: '...' }))

// Hono
import { Mppx, tempo } from 'mppx/hono'
app.get('/resource', mppx.charge({ amount: '0.1' }), (c) => c.json({ data: '...' }))

// Express
import { Mppx, tempo } from 'mppx/express'
app.get('/resource', mppx.charge({ amount: '0.1' }), (req, res) => res.json({ data: '...' }))

// Elysia
import { Mppx, tempo } from 'mppx/elysia'
app.guard({ beforeHandle: mppx.charge({ amount: '0.1' }) }, (app) =>
  app.get('/resource', () => ({ data: '...' }))
)
```

## Sessions: Pay-as-You-Go Streaming

Sessions open a payment channel once, then use off-chain vouchers for each request - no blockchain transaction per request. Sub-100ms latency, near-zero per-request fees.

```typescript
// Server - session endpoint
const result = await mppx.session({
  amount: '0.001',
  unitType: 'token',
})(request)
if (result.status === 402) return result.challenge
return result.withReceipt(Response.json({ data: '...' }))

// Server - SSE streaming with per-word billing
const mppx = Mppx.create({
  methods: [tempo({ currency: '0x20c0...', recipient: '0x...', sse: true })],
})
export const GET = mppx.session({ amount: '0.001', unitType: 'word' })(
  async () => {
    const words = ['hello', 'world']
    return async function* (stream) {
      for (const word of words) {
        await stream.charge()
        yield word
      }
    }
  }
)

// Client - session with auto-managed channel
import { Mppx, tempo } from 'mppx/client'
Mppx.create({
  methods: [tempo({ account, maxDeposit: '1' })], // Lock up to 1 pathUSD
})
const res = await fetch('http://localhost:3000/api/resource')
// 1st request: opens channel on-chain
// 2nd+ requests: off-chain vouchers (no on-chain tx)
```

See `references/sessions.md` for the full session lifecycle, escrow contracts, and SSE patterns.

## Multi-Method Support

Accept Tempo stablecoins, Stripe cards, and Lightning Bitcoin on a single endpoint:

```typescript
import Stripe from 'stripe'
import { Mppx, tempo, stripe } from 'mppx/server'
import { spark } from '@buildonspark/lightning-mpp-sdk/server'

const mppx = Mppx.create({
  methods: [
    tempo({ currency: '0x20c0...', recipient: '0x...' }),
    stripe.charge({ client: new Stripe(key), networkId: 'internal', paymentMethodTypes: ['card'] }),
    spark.charge({ mnemonic: process.env.MNEMONIC! }),
  ],
})
// 402 response advertises all methods; client picks one
```

## Payments Proxy

Gate existing APIs behind MPP payments:

```typescript
import { openai, Proxy } from 'mppx/proxy'
import { Mppx, tempo } from 'mppx/server'

const mppx = Mppx.create({ methods: [tempo()] })
const proxy = Proxy.create({
  services: [
    openai({
      apiKey: 'sk-...', // pragma: allowlist secret
      routes: {
        'POST /v1/chat/completions': mppx.charge({ amount: '0.05' }),
        'GET /v1/models': mppx.free(), // mppx.free() marks a route as free (no payment)
      },
    }),
  ],
})
```

## MCP Transport

MCP tool calls can require payment using JSON-RPC error code `-32042`:

```typescript
// Server - MCP with payment (import tempo from mppx/server, NOT mppx/tempo)
import { McpServer } from 'mppx/mcp-sdk/server'
import { tempo } from 'mppx/server'
const server = McpServer.wrap(baseServer, {
  methods: [tempo.charge({ ... })],
  secretKey: '...',
})

// Client - payment-aware MCP client (import tempo from mppx/client)
import { McpClient } from 'mppx/mcp-sdk/client'
import { tempo } from 'mppx/client'
const mcp = McpClient.wrap(client, { methods: [tempo({ account })] })
const result = await mcp.callTool({ name: 'premium_tool', arguments: {} })
```

See `references/transports.md` for the full MCP encoding (challenge in error.data.challenges, credential in _meta).

## Testing

```bash
# Create an account (stored in keychain, auto-funded on testnet)
npx mppx account create

# Make a paid request
npx mppx http://localhost:3000/resource

# Inspect challenge without paying
npx mppx --inspect http://localhost:3000/resource
```

## SDK Packages

| Language | Package | Install |
|----------|---------|---------|
| TypeScript | `mppx` | `npm install mppx` |
| Python | `pympp` | `pip install pympp` or `pip install "pympp[tempo]"` |
| Rust | `mpp` | `cargo add mpp --features tempo,client,server` |

TypeScript subpath exports (these are the only valid import paths - there is no `mppx/tempo`):
- Server: `mppx/server` (generic), `mppx/hono`, `mppx/express`, `mppx/nextjs`, `mppx/elysia` (framework middleware)
- Client: `mppx/client`
- Proxy: `mppx/proxy`
- MCP: `mppx/mcp-sdk/server`, `mppx/mcp-sdk/client`

Always import `Mppx` and `tempo` from the appropriate subpath for your context (e.g. `mppx/hono` for Hono, `mppx/server` for generic/MCP server, `mppx/client` for client).

## Key Concepts

- **Challenge/Credential/Receipt**: The three protocol primitives. Challenge IDs are HMAC-SHA256 bound to prevent tampering. See `references/protocol-spec.md`
- **Payment methods**: Tempo (stablecoins), Stripe (cards), Lightning (Bitcoin), Card (network tokens), or custom. See method-specific references
- **Intents**: `charge` (one-time) and `session` (streaming). See `references/sessions.md` for session details
- **Transports**: HTTP (headers) and MCP (JSON-RPC). See `references/transports.md`
- **Fee sponsorship**: Server pays gas fees on behalf of clients (Tempo). See `references/tempo-method.md`
- **Push/pull modes**: Client broadcasts tx (push) or server broadcasts (pull). See `references/tempo-method.md`
- **Custom methods**: Implement any payment rail with `Method.from()`. See `references/custom-methods.md`

## References

| File | Content |
|------|---------|
| `references/protocol-spec.md` | Core protocol: Challenge/Credential/Receipt structure, status codes, error handling, security, caching, extensibility |
| `references/typescript-sdk.md` | mppx TypeScript SDK: server/client/middleware patterns, proxy, MCP SDK, CLI, Mppx.create options |
| `references/tempo-method.md` | Tempo payment method: charge + session intents, fee sponsorship, push/pull modes, auto-swap, testnet/mainnet config |
| `references/stripe-method.md` | Stripe payment method: SPT flow, server/client config, Stripe Elements, createToken proxy, metadata |
| `references/sessions.md` | Session intent deep-dive: payment channels, voucher signing, SSE streaming, escrow contracts, top-up, close |
| `references/transports.md` | HTTP and MCP transport bindings: header encoding, JSON-RPC error codes, comparison |
| `references/python-sdk.md` | pympp Python SDK: FastAPI/server patterns, async client, streaming sessions |
| `references/rust-sdk.md` | mpp Rust SDK: server/client, feature flags, reqwest middleware |
| `references/lightning-method.md` | Lightning payment method: charge (BOLT11), session (bearer tokens), Spark SDK |
| `references/custom-methods.md` | Custom payment methods: Method.from, Method.toClient, Method.toServer patterns |

## Official Resources

- Website: https://mpp.dev
- GitHub: https://github.com/wevm/mppx (TypeScript SDK)
- Protocol spec: https://paymentauth.org
- Stripe docs: https://docs.stripe.com/payments/machine/mpp
- Tempo docs: https://docs.tempo.xyz
- LLM docs: https://mpp.dev/llms-full.txt
