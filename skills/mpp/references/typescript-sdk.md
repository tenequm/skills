# mppx TypeScript SDK Reference

## Installation

```bash
npm install mppx viem
```

**Peer dependencies** (install as needed):
- `viem` >= 2.46.2 (required)
- `@modelcontextprotocol/sdk` >= 1.25.0 (for MCP integration)
- `hono` >= 4 (for Hono middleware)
- `express` >= 5 (for Express middleware)
- `elysia` >= 1 (for Elysia middleware)

## Package Exports

| Subpath | Purpose |
|---|---|
| `mppx` | Main entry, core primitives |
| `mppx/client` | Client SDK (polyfill / manual fetch) |
| `mppx/server` | Server SDK (charge, session, compose) |
| `mppx/proxy` | Proxy server with service routing |
| `mppx/stripe` | Stripe payment method |
| `mppx/tempo` | Tempo payment method |
| `mppx/html` | Payment link UI customization (Config, Text, Theme types, init()) |
| `mppx/discovery` | OpenAPI-first discovery tooling |
| `mppx/mcp-sdk/client` | MCP client wrapper |
| `mppx/mcp-sdk/server` | MCP server wrapper |
| `mppx/hono` | Hono framework middleware |
| `mppx/express` | Express framework middleware |
| `mppx/nextjs` | Next.js middleware |
| `mppx/elysia` | Elysia framework middleware |

## Server SDK (`mppx/server`)

### Creating a Server Instance

```ts
import { Mppx, tempo } from 'mppx/server'

const mppx = Mppx.create({
  methods: [tempo()],
  secretKey: process.env.MPP_SECRET_KEY, // HMAC secret for challenge binding (required)
  realm: 'My API',                       // defaults to env detection or "MPP Payment"
  transport: 'http',                      // optional, defaults to auto-detect
})
```

- `secretKey` - HMAC secret used for challenge binding. Required.
- `realm` - human-readable service name. Defaults to environment detection or `"MPP Payment"`.
- `methods` - array of payment method handlers (e.g. `tempo()`, `stripe()`).
- `transport` - protocol transport, auto-detected by default.

### Charging per Request

```ts
const result = await mppx.charge({
  amount: '0.001',
  currency: 'USD',          // optional, defaults to USD
  recipient: '0x...',       // optional, override default recipient
  description: 'API call',  // optional
  expires: Expires.minutes(5), // optional
  externalId: 'inv-123',    // optional, for idempotency/tracking
  feePayer: 'sender',       // optional, 'sender' | 'receiver'
})(request)

// result.status - 'paid' | 'unpaid'
// result.challenge - the challenge object (when unpaid)
// result.withReceipt() - attach receipt to response (when paid)
```

Full handler example:

```ts
const handler = async (req: Request) => {
  const result = await mppx.charge({ amount: '0.01' })(req)

  if (result.status === 'unpaid') {
    return Response.requirePayment(result.challenge)
  }

  const response = new Response(JSON.stringify({ data: 'paid content' }))
  return result.withReceipt(response)
}
```

### Session-Based Billing

```ts
const result = await mppx.session({
  amount: '1.00',
  unitType: 'credits',
})(request)
```

### Composing Methods

Present multiple payment methods in a single 402 response. Accepts handler function refs (0.4.0+), method objects, or `"name/intent"` string keys:

```ts
// Handler function refs (preferred, 0.4.0+)
const result = await mppx.compose(
  mppx.tempo.charge({ amount: '0.01' }),
  mppx.stripe.charge({ amount: '0.01' }),
)(request)
if (result.status === 402) return result.challenge
return result.withReceipt(Response.json({ data: '...' }))

// Tuple syntax also works
const handler = mppx.compose(
  ['tempo/charge', { amount: '0.01' }],
  ['stripe/charge', { amount: '0.01' }],
)
```

### Node.js Adapter

```ts
import http from 'node:http'
import { Mppx } from 'mppx/server'

const server = http.createServer(Mppx.toNodeListener(handler))
```

### Manual 402 Response

```ts
return Response.requirePayment(challenges)
```

## Client SDK (`mppx/client`)

### With Polyfill (Default)

```ts
import { Mppx, tempo } from 'mppx/client'

Mppx.create({
  methods: [tempo()],
  polyfill: true,  // default - wraps globalThis.fetch
})

// All fetch calls now handle 402 automatically
const res = await fetch('https://api.example.com/data')
console.log(await res.json()) // paid content, no manual 402 handling
```

### Without Polyfill

```ts
const mppx = Mppx.create({
  methods: [tempo()],
  polyfill: false,
})

const res = await mppx.fetch('https://api.example.com/data')
```

### Manual Credential Creation

```ts
const credential = await mppx.createCredential(response402, context?)
```

### Per-Request Accounts

```ts
const res = await mppx.fetch(url, {
  context: { account: specificAccount },
})
```

### Options

- `methods` - payment method handlers
- `fetch` - custom fetch implementation (optional)
- `polyfill` - wrap `globalThis.fetch`, defaults to `true`
- `transport` - protocol transport (optional)
- `onChallenge` - callback when a 402 challenge is received (optional)

## Framework Middleware

### Hono

```ts
import { Hono } from 'hono'
import { Mppx, tempo } from 'mppx/hono'

const mppx = Mppx.create({
  methods: [tempo()],
  secretKey: process.env.MPP_SECRET_KEY,
})

const app = new Hono()

app.get('/paid', mppx.charge({ amount: '0.01' }), (c) => {
  return c.json({ data: 'paid content' })
})
```

### Express

```ts
import express from 'express'
import { Mppx, tempo } from 'mppx/express'

const mppx = Mppx.create({
  methods: [tempo()],
  secretKey: process.env.MPP_SECRET_KEY,
})

const app = express()

app.get('/paid', mppx.charge({ amount: '0.01' }), (req, res) => {
  res.json({ data: 'paid content' })
})
```

### Next.js

```ts
import { Mppx, tempo } from 'mppx/nextjs'

const mppx = Mppx.create({
  methods: [tempo()],
  secretKey: process.env.MPP_SECRET_KEY,
})

export const GET = mppx.charge({ amount: '0.01' })(async (req) => {
  return Response.json({ data: 'paid content' })
})
```

### Elysia

```ts
import { Elysia } from 'elysia'
import { Mppx, tempo } from 'mppx/elysia'

const mppx = Mppx.create({
  methods: [tempo()],
  secretKey: process.env.MPP_SECRET_KEY,
})

const app = new Elysia()
  .guard({ beforeHandle: mppx.charge({ amount: '0.01' }) })
  .get('/paid', () => ({ data: 'paid content' }))
```

## Proxy Server (`mppx/proxy`)

### Creating a Proxy

```ts
import { Proxy, openai, stripe } from 'mppx/proxy'
import { Mppx, tempo } from 'mppx/server'

const mppx = Mppx.create({
  methods: [tempo()],
  secretKey: process.env.MPP_SECRET_KEY,
})

const proxy = Proxy.create({
  title: 'My API Proxy',
  description: 'Paid access to AI APIs',
  basePath: '/api',
  services: [
    openai({
      apiKey: process.env.OPENAI_API_KEY,
      routes: {
        'POST /v1/chat/completions': mppx.charge({ amount: '0.005' }),
        'GET /v1/models': mppx.free(),
      },
    }),
    stripe({
      apiKey: process.env.STRIPE_API_KEY,
      routes: {
        'POST /v1/charges': mppx.charge({ amount: '0.01' }),
      },
    }),
  ],
})
```

### Discovery Endpoints

- `GET /discover` - service discovery metadata
- `GET /discover/all` - all routes and pricing
- `GET /llms.txt` - LLM-readable service description

### Handlers

```ts
// Fetch API (Cloudflare Workers, Bun, Deno)
export default { fetch: proxy.fetch }

// Node.js http server
import http from 'node:http'
http.createServer(proxy.listener).listen(3000)
```

## MCP SDK

### Server - Wrapping an MCP Server

```ts
import { McpServer } from 'mppx/mcp-sdk/server'
import { Server } from '@modelcontextprotocol/sdk/server/index.js'

const baseServer = new Server({ name: 'my-mcp', version: '1.0.0' })

const server = McpServer.wrap(baseServer, {
  methods: [tempo()],
  secretKey: process.env.MPP_SECRET_KEY,
})
```

Payment errors use MCP error code `-32042`.

### Client - Wrapping an MCP Client

```ts
import { McpClient } from 'mppx/mcp-sdk/client'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'

const baseClient = new Client({ name: 'my-client', version: '1.0.0' })

const client = McpClient.wrap(baseClient, {
  methods: [tempo()],
})
```

## CLI

### Account Management

```bash
# Create account (stored in system keychain, auto-funded on testnet)
mppx account create

# List accounts
mppx account list
```

### Making Requests

```bash
# Simple paid request
mppx https://api.example.com/data

# Inspect challenge without paying
mppx --inspect https://api.example.com/data

# Custom method, headers, body
mppx -X POST -H "Content-Type: application/json" -d '{"prompt":"hello"}' https://api.example.com/chat
```

### Plugins

```bash
mppx plugins add tempo/stripe
```

## Core Primitives

### Challenge

```ts
import { Challenge } from 'mppx'

const challenge = Challenge.from({
  amount: '0.01',
  recipient: '0x...',
  // ...
})

const serialized = Challenge.serialize(challenge)    // string
const parsed = Challenge.deserialize(serialized)     // Challenge
const fromRes = Challenge.fromResponse(response)     // Challenge from 402 response
const valid = Challenge.verify(challenge, secretKey)  // boolean
```

### Credential

```ts
import { Credential } from 'mppx'

const credential = Credential.from({ /* ... */ })
const serialized = Credential.serialize(credential)
const parsed = Credential.deserialize(serialized)
const fromReq = Credential.fromRequest(request)      // extract from incoming request
```

### Receipt

```ts
import { Receipt } from 'mppx'

const receipt = Receipt.from({ /* ... */ })
const serialized = Receipt.serialize(receipt)
const fromRes = Receipt.fromResponse(response)
```

### Expires Helpers

```ts
import { Expires } from 'mppx'

const fiveMin = Expires.minutes(5)
const twoHours = Expires.hours(2)
```

## Error Classes

All errors extend `PaymentError` and expose `.toProblemDetails()` for RFC 9457 responses.

**General errors:**
- `MalformedCredentialError` - credential cannot be parsed
- `InvalidChallengeError` - challenge is invalid or tampered
- `VerificationFailedError` - signature or HMAC verification failed
- `PaymentRequiredError` - payment is required (402)
- `PaymentExpiredError` - challenge or credential has expired
- `PaymentInsufficientError` - payment amount too low
- `PaymentMethodUnsupportedError` - method not accepted by server

**Session-specific errors:**
- `InsufficientBalanceError` - session channel balance too low
- `InvalidSignatureError` - session state signature invalid
- `ChannelNotFoundError` - session channel does not exist
- `ChannelClosedError` - session channel has been closed

Plus additional error types (14 total), all following the same pattern.

```ts
try {
  const result = await mppx.charge({ amount: '0.01' })(request)
} catch (e) {
  if (e instanceof PaymentExpiredError) {
    console.log(e.toProblemDetails())
    // { type: '...', title: 'Payment Expired', status: 402, detail: '...' }
  }
}
```

## Store Interface

For session channel state persistence. All built-in adapters handle BigInt serialization via `ox`'s `Json` module.

```ts
import { Store } from 'mppx/server'

// In-memory (development only)
const store = Store.memory()

// Redis / ioredis / Valkey (added in 0.4.9)
const store = Store.redis(redisClient) // client needs: get, set, del

// Cloudflare KV
const store = Store.cloudflare(env.MY_KV_NAMESPACE)

// Upstash Redis / Vercel KV
const store = Store.upstash(upstashClient)

// Custom adapter
const store = Store.from({
  get: async (key) => { /* ... */ },
  put: async (key, value) => { /* ... */ },
  delete: async (key) => { /* ... */ },
})

// Pass to session method config
tempo.session({ currency, recipient, store, sse: { poll: true } })
```

## AtomicStore

`AtomicStore` extends `Store` with a safe `update(key, fn)` method for concurrent read-modify-write operations (0.5.7+):

```ts
import { Store, type AtomicStore } from 'mppx/server'

// All built-in adapters support atomic updates
const store: AtomicStore<MyItemMap> = Store.redis(redisClient)

// Atomic read-modify-write
const result = await store.update('channel:0x123', (current) => {
  if (!current) return { value: initialState, result: 'created' }
  return { value: { ...current, settled: current.settled + amount }, result: 'updated' }
})
```

The type system uses a two-slot generic pattern:
- `Store<itemMap, extended>` - base store with optional extension slot
- `AtomicStore<itemMap>` = `Store<itemMap, AtomicActions<itemMap>>` - store with `update()` filled in
- Custom adapters via `Store.from()` get an optimistic-retry `update()` implementation automatically
- Native adapters (redis, upstash, cloudflare) use their built-in atomic primitives

Use cases: replay protection (atomic deduplication of proof credentials), channel state updates in distributed deployments, SSE session state management.

## Privy Server Wallets

Use [Privy](https://docs.privy.io) server-managed wallets as MPP signers for agentic payment flows. Install: `npm install @privy-io/node mppx viem`.

The pattern: create a custom viem `Account` that delegates signing to Privy's API, then pass it to `tempo({ account })`:

```ts
import { PrivyClient } from '@privy-io/node'
import { Mppx, tempo } from 'mppx/client'
import { toAccount } from 'viem/accounts'
import { keccak256 } from 'viem'

const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!,
})

function createPrivyAccount(walletId: string, address: `0x${string}`) {
  return toAccount({
    address,

    async signMessage({ message }) {
      const result = await privy.wallets().ethereum().signMessage(walletId, {
        message: typeof message === 'string' ? message : message.raw,
      })
      return result.signature as `0x${string}`
    },

    async signTransaction(transaction, options) {
      // Tempo uses a custom serializer - must use raw signSecp256k1
      const serializer = options?.serializer
      if (!serializer) throw new Error('Tempo serializer required')
      const unsignedSerialized = await serializer(transaction)
      const hash = keccak256(unsignedSerialized)
      const { signature } = await privy
        .wallets()
        .ethereum()
        .signSecp256k1(walletId, { params: { hash } })
      const { SignatureEnvelope } = await import('ox/tempo')
      return (await serializer(
        transaction,
        SignatureEnvelope.from(signature) as any,
      )) as `0x${string}`
    },

    async signTypedData(typedData) {
      const result = await privy
        .wallets()
        .ethereum()
        .signTypedData(walletId, { params: typedData as any })
      return result.signature as `0x${string}`
    },
  })
}

// Create wallet + MPP client
const wallet = await privy.wallets().create({ chain_type: 'ethereum' })
const account = createPrivyAccount(wallet.id, wallet.address as `0x${string}`)
const mppx = Mppx.create({ polyfill: false, methods: [tempo({ account })] })
const response = await mppx.fetch('https://api.example.com/paid')
```

**Key details:**
- `signTransaction` uses `signSecp256k1` (raw hash signing) because Tempo has a custom serialization format (type `0x76`). Privy's higher-level `signTransaction` doesn't support custom serializers.
- `signMessage` maps directly to Privy's `signMessage` for EIP-191 personal signatures
- `signTypedData` maps directly for EIP-712 typed data (used by zero-dollar auth proofs)
- For Tempo testnet (Moderato, chain 42431): use `tempo({ account, testnet: true })` in `Mppx.create`

See the [Privy MPP demo](https://github.com/privy-io/examples/tree/main/privy-next-mpp-agent-demo) for a full Next.js reference implementation including wallet creation, funding from a treasury, and executing paid API calls.

## Zod Validators

Schema validators for MPP-specific types:

```ts
import { z } from 'mppx'

const schema = z.object({
  price: z.amount(),       // valid payment amount string
  due: z.datetime(),       // ISO 8601 datetime
  wallet: z.address(),     // EVM address (0x...)
  txHash: z.hash(),        // transaction hash
  sig: z.signature(),      // cryptographic signature
  billing: z.period(),     // billing period
})
```
