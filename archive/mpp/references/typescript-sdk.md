# mppx TypeScript SDK Reference

## Installation

```bash
npm install mppx viem
```

**Peer dependencies** (install as needed, per mppx 0.8.15):
- `viem` >= 2.54.0 (required)
- `@modelcontextprotocol/sdk` >= 1.25.0 (for MCP integration)
- `hono` >= 4.12.25 (for Hono middleware)
- `express` >= 5 (for Express middleware)
- `elysia` >= 1 (for Elysia middleware)

## Package Exports

Authoritative `exports` keys from `mppx` 0.8.15:

| Subpath | Purpose |
|---|---|
| `mppx` | Main entry, core primitives |
| `mppx/client` | Client SDK (polyfill / manual fetch) |
| `mppx/client/node` | Node-only client extras: SQLite session `ChannelStore` |
| `mppx/server` | Server SDK (charge, session, compose) |
| `mppx/proxy` | Proxy server with service routing |
| `mppx/stripe`, `mppx/stripe/client`, `mppx/stripe/server` | Stripe payment method |
| `mppx/evm`, `mppx/evm/client`, `mppx/evm/server` | EVM (EIP-3009) payment method |
| `mppx/x402` | x402 interop ("exact" flow compatibility) |
| `mppx/tempo` | Tempo `Session` and `Ws` utilities (note: `tempo`/`Mppx` are NOT here - import those from `mppx/server` or `mppx/client`) |
| `mppx/html` | Payment link UI customization (Config, Text, Theme types, plus `Html.init(methodName)`, which returns the page context: `challenge`, `config`, `error`, `formattedAmount`, `label`, `root`, `submit`, `text`, `theme`, `vars`) |
| `mppx/discovery` | OpenAPI-first discovery tooling |
| `mppx/validation` | Programmatic server validation (the engine behind `mppx validate`) |
| `mppx/cli`, `mppx/cli/plugins` | CLI config + plugin authoring |
| `mppx/mcp/client` | MCP client wrapper (0.8.0+; `mppx/mcp-sdk/client` is a retained alias) |
| `mppx/mcp/server` | MCP server wrapper (0.8.0+; `mppx/mcp-sdk/server` is a retained alias) |
| `mppx/hono` | Hono framework middleware |
| `mppx/express` | Express framework middleware |
| `mppx/nextjs` | Next.js middleware |
| `mppx/elysia` | Elysia framework middleware |

Lightning, Stellar, Solana, Monad, RedotPay, and Card are **external packages** (`@buildonspark/lightning-mpp-sdk`, `@stellar/mpp`, `@solana/mpp`, `@monad-crypto/mpp`, `@redotpay/mpp`, `mpp-card`), not `mppx` subpaths.

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

// result.status === 402 - payment required (result.challenge is the 402 response)
// otherwise paid - result.withReceipt() attaches the receipt to your response
```

Full handler example:

```ts
const handler = async (req: Request) => {
  const result = await mppx.charge({ amount: '0.01' })(req)

  if (result.status === 402) return result.challenge

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

### Credential Lifecycle: validate vs broadcast

Settlement is split into a non-mutating pre-check and a mutating settle, so a server can answer "would this credential work?" without consuming it:

```ts
// Non-mutating: does this credential satisfy the challenge?
const result = await mppx.validateCredential(authorizationHeaderValue)

// Mutating: settle the payment and produce a receipt
const receipt = await mppx.broadcastCredential(authorizationHeaderValue)
```

`mppx.verifyCredential()` is a **deprecated** alias for `broadcastCredential()`: it "maps to the same mutating operation and does not provide validation-only semantics." Use the split pair for anything that needs a safe pre-check endpoint, or that must confirm work succeeded before taking payment.

The same split exists at the method level - see `references/custom-methods.md`.

## Client SDK (`mppx/client`)

The client module exports `Mppx`, `Fetch`, `Transport`, `Expires`, and `Constants`.

### Entry Points

```ts
import { Fetch, Mppx } from 'mppx/client'

// Standalone payment-aware fetch - no global mutation
const paidFetch = Fetch.from({ methods: [tempo({ account })] })
const res = await paidFetch('https://api.example.com/data')

// Explicit global install / uninstall
Fetch.polyfill({ methods: [tempo({ account })] })
Fetch.restore()

// Undo an instance's polyfill
const mppx = Mppx.create({ methods: [tempo({ account })] })
Mppx.restore()
```

Prefer `Fetch.from()` in libraries and tests: patching `globalThis.fetch` in a shared process affects every caller, including ones that should not be paying.

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
- `acceptPaymentPolicy` - controls when the `Accept-Payment` header is injected on outgoing requests: `'always'`, `'same-origin'`, `'never'`, or `{ origins: string[] }` (supports `*.` wildcards)
- `maxPaymentRetries` - maximum payment challenge retries after the initial response, default `3`. Incremental challenges (a server re-issuing a 402 with adjusted requirements) consume retries

**Breaking change (mppx 0.6.0):** polyfilled `fetch` in browsers no longer sends `Accept-Payment` on every request - it now defaults to **same-origin** only. Non-browser environments are unaffected. Use `acceptPaymentPolicy` to opt cross-origin payment endpoints back in.

### Node SQLite Channel Store (`mppx/client/node`)

Persist session channels across processes on Node without standing up Redis:

```ts
import { createSqliteChannelStore, defaultChannelDatabasePath } from 'mppx/client/node'

const channelStore = createSqliteChannelStore({ path: defaultChannelDatabasePath() })
Mppx.create({ methods: [tempo.session({ account, maxDeposit: '1', channelStore })] })
```

`defaultChannelDatabasePath()` points at Tempo Wallet's own `channels.db`, and the store can read existing wallet-cli v2 session rows - so a CLI-opened channel is reusable from your own process, and vice versa.

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

## Proxy and Discovery

The payments proxy (`mppx/proxy`) and discovery documents (`mppx/discovery`) have their own reference: `references/discovery-and-proxy.md`. Two things worth flagging here because they are easy to get wrong:

- Free proxy routes are declared with the literal value `true` (`'GET /v1/models': true`). There is **no** `mppx.free()` helper.
- The proxy exposes both `proxy.fetch` (Fetch API runtimes) and `proxy.listener` (Node `http`).

## MCP SDK

### Server - Wrapping an MCP Server

```ts
import { McpServer } from 'mppx/mcp/server'
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
import { McpClient } from 'mppx/mcp/client'
import { Client } from '@modelcontextprotocol/sdk/client/index.js'

const baseClient = new Client({ name: 'my-client', version: '1.0.0' })

const client = McpClient.wrap(baseClient, {
  methods: [tempo()],
})
```

The MCP subpaths moved to `mppx/mcp/server` and `mppx/mcp/client` in mppx 0.8.0; the `mppx/mcp-sdk/*` specifiers remain as aliases. `McpClient.wrap` is now the single client-wrap API - the in-place `wrapClient` variant was collapsed into it. MCP-over-HTTP challenges settle in the same payment-aware fetch: `Transport.http()` extracts JSON-RPC `-32042` challenges and retries with the credential in MCP metadata, so a single client can pay both HTTP `402`s and MCP-over-HTTP challenges.

## Transports

Transports are pluggable on both client and server, exported as a `Transport` namespace from `mppx/client` and `mppx/server`:

| Export | Purpose |
|---|---|
| `Transport.http()` | HTTP header encoding; also extracts MCP-over-HTTP `-32042` challenges |
| `Transport.mcp()` | Raw JSON-RPC message handling |
| `Transport.mcpSdk()` | For use with `@modelcontextprotocol/sdk` |
| `Transport.from()` | Build a custom transport |

Use `Transport.mcp()` when handling raw JSON-RPC messages directly; with the official MCP SDK, use `Transport.mcpSdk()` instead.

## CLI

The CLI has its own reference: `references/cli.md`. Note that `mppx/cli` (config via `defineConfig`) and `mppx/cli/plugins` (plugin authoring) are module exports, not a `mppx plugins` command - no such command exists.

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

**17** error classes extend `PaymentError` and expose `.toProblemDetails()` for RFC 9457 responses.

**General errors:**
- `MalformedCredentialError` - credential cannot be parsed
- `InvalidChallengeError` - challenge is invalid or tampered
- `VerificationFailedError` - signature or HMAC verification failed
- `PaymentRequiredError` - payment is required (402)
- `PaymentActionRequiredError` - the payer must take an action before payment can complete
- `PaymentExpiredError` - challenge or credential has expired
- `PaymentInsufficientError` - payment amount too low
- `PaymentMethodUnsupportedError` - method not accepted by server
- `InvalidPayloadError` - credential payload fails its schema
- `BadRequestError` - malformed request

**Session-specific errors:**
- `InsufficientBalanceError` - session channel balance too low
- `InvalidSignatureError` - session state signature invalid
- `SignerMismatchError` - voucher signed by an unexpected signer
- `AmountExceedsDepositError` - cumulative voucher exceeds the channel deposit
- `DeltaTooSmallError` - voucher increment below the minimum
- `ChannelNotFoundError` - session channel does not exist
- `ChannelClosedError` - session channel has been closed

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

### Structured Error Metadata

`PaymentError` carries a `details` record - "safe method-specific context for diagnostics and relay responses" - alongside the human-facing `hint`. Both surface in the problem document. This is the practical way to see *why* a payment failed, since mppx otherwise re-emits internal failures as a generic 402 with a fresh challenge.

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

Client-side, pass a `channelStore` to the Tempo **session client** (`tempo.session` / `tempo.session.manager`) to persist and reuse payer session channels across processes (mppx 0.8.0) - distinct from the server-side `store` above. The client-side `authorizedSigner` override was removed in 0.8.0; voucher authority derives from the selected account.

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

### Recommended: `createViemAccount`

`@privy-io/node` version `0.20.0` or later ships a helper that builds the viem `Account` for you. It "delegates signatures to the Privy wallet, so it replaces any local viem account" - including the Tempo custom-serializer handling that previously had to be written by hand:

```ts
import { PrivyClient } from '@privy-io/node'
import { createViemAccount } from '@privy-io/node/viem'
import { Mppx, tempo } from 'mppx/client'

const privy = new PrivyClient({
  appId: process.env.PRIVY_APP_ID!,
  appSecret: process.env.PRIVY_APP_SECRET!,
})

const wallet = await privy.wallets().create({ chain_type: 'ethereum' })
const account = createViemAccount(privy, { walletId: wallet.id, address: wallet.address })

const mppx = Mppx.create({ polyfill: false, methods: [tempo({ account })] })
const response = await mppx.fetch('https://api.example.com/paid')
```

**Wallet ownership matters.** Server-side signing works with **app-owned server wallets**. User-owned embedded wallets cannot be signed for from a server without authorization keys or key quorums, and attempts fail with a 401 about missing authorization or user signing keys. Provision a server wallet for agent payment flows rather than reaching for a user's embedded wallet.

### Manual construction (background)

Before `createViemAccount`, the account was assembled by hand with `toAccount()`. It is still useful to understand what the helper does, and necessary if you are on an older `@privy-io/node`:

```ts
import { PrivyClient } from '@privy-io/node'
import { Mppx, tempo } from 'mppx/client'
import { toAccount } from 'viem/accounts'
import { keccak256 } from 'viem'

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

const account = createPrivyAccount(wallet.id, wallet.address as `0x${string}`)
```

**Key details:**
- `signTransaction` uses `signSecp256k1` (raw hash signing) because Tempo has a custom serialization format (type `0x76`). Privy's higher-level `signTransaction` doesn't support custom serializers.
- `signMessage` maps directly to Privy's `signMessage` for EIP-191 personal signatures
- `signTypedData` maps directly for EIP-712 typed data (used by zero-dollar auth proofs). As of mppx 0.8.0 the Tempo zero-amount `Proof` typed-data includes an `account` field bound to the payer wallet and its domain version is `3` (exposed as `tempo.Proof`) - a proof signed for one account no longer verifies against another
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

Conversion and input helpers also ship from the same namespace: `z.datetimeInput()` (accepts the several datetime input shapes mppx tolerates), `z.toDate()`, `z.toDatetimeString()`, and `z.unwrapOptional()`.

## Payment Hooks

Register on the object returned by `Mppx.create()`. Each registration returns an unsubscribe function.

```ts
// Server (mppx/server)
const payment = Mppx.create({ methods: [tempo.charge(), tempo.session()] })
payment.onChallengeCreated(({ challenge, method, request }) => {})
payment.onPaymentSuccess(({ method, receipt, request }) => {})
payment.onPaymentFailed(({ error, method, submittedChallenge }) => {})
payment.onSessionSettlement(({ trigger, txHash, channelId, cumulative, delta }) => {})
payment.on('*', ({ name, payload }) => {})

// Client (mppx/client)
const mppx = Mppx.create({ methods: [tempo.charge({ account })], polyfill: false })
mppx.onChallengeReceived(({ challenge }) => { /* return a credential string to override */ })
mppx.onCredentialCreated(({ challenge }) => {})
mppx.onPaymentResponse(({ challenge, response }) => {})
mppx.onPaymentFailed(({ challenge, error }) => {})
```

Server handlers are awaited inline and sequentially on the request path, so slow handlers delay the response. Every hook except client `onChallengeReceived` is a pure observer: thrown errors are swallowed and never change payment handling. Filter by intent with `method.intent` (server) or `challenge.intent` (client) - `'charge'`, `'session'`, or `'subscription'`.

`onSessionSettlement` reports on-chain session settlement with chain-agnostic context: the `trigger` that caused it (scheduled vs explicit), the transaction hash, the channel ID, and the cumulative and incremental amounts. It is the hook to wire up if you need a settlement ledger. See [mpp.dev/advanced/payment-hooks](https://mpp.dev/advanced/payment-hooks).
