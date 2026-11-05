# Production Gotchas

Field-tested failure modes when running MPP servers and clients in production.

## Tempo Gas (CRITICAL)

**Tempo has no native gas token.** Unlike Ethereum (ETH for gas) or Solana (SOL for fees), Tempo charges transaction fees in stablecoins. Every transaction must specify which stablecoin pays for gas. There are two ways:

1. **Per-transaction `feeToken`** - set in the transaction itself:
```typescript
const prepared = await prepareTransactionRequest(client, {
  account,
  calls: [{ to, data }],
  feeToken: '<USDC_TEMPO_MAINNET>',
} as never)
```

2. **Account-level default via `setUserToken`** - one-time setup, applies to all future transactions:
```typescript
import { setUserToken } from 'viem/tempo'
await client.fee.setUserTokenSync({ token: '<USDC_TEMPO_MAINNET>' })
```

**Without either, transactions fail silently with `gas_limit: 0`.** The mppx SDK handles this internally for payment transactions, but any direct on-chain calls (settle, close, custom contract interactions) must set `feeToken` explicitly or ensure `setUserToken` was called for the account.

**"Fund with ETH/gas" errors are misleading on Tempo** - read them as "fund with the stablecoin fee token." The **server/recipient wallet itself** must hold the stablecoin fee token before it can broadcast `session.close()` or settle; otherwise the close silently fails and surfaces as a generic 402, leaving client deposits locked.

Asymmetry worth knowing: in charge **push** mode the payer broadcasts the transfer, so the recipient wallet needs no fee token at all for that path. It needs fee-token balance only for server-signed operations (settle, close, sponsored charges).

## Settlement Is Not Automatic

A session server verifies and stores vouchers, but **nothing redeems them on-chain unless you configure it**. Left alone, a session server accrues signed vouchers it never converts to funds, and channels stay open with payer deposits reserved.

Configure `settlementSchedule` on `tempo.session()`, or drive `tempo.settle()` / `tempo.settleBatch()` from your own sweep. See `references/sessions.md` for both. Settling claims revenue while keeping the channel reusable; closing settles and releases the payer's remaining reservation. A server that only ever settles leaves abandoned channels open indefinitely, so pair a settle cadence with a close policy for idle channels.

## Payment Timing

**Charge settles during verification, before your handler runs.** By the time route logic executes, funds have already moved - an empty result, an upstream 5xx, or a business-rule rejection is still a completed payment. There is no post-handler skip.

When you need to gate payment on the work succeeding, use the split credential lifecycle: `mppx.validateCredential()` is a non-mutating pre-check, and `mppx.broadcastCredential()` performs settlement. The older combined `verify` path is deprecated precisely because it "combines both operations and may consume payment state, so it cannot support a safe pre-check endpoint."

**Challenges expire after 5 minutes by default.** If you restructure toward "serve first, settle after the upstream call," compare your p95 upstream latency against that window - a slow upstream can expire the authorization and hand the client a 402 after a long wait. Set `expires` explicitly when the work is slow.

## Setup

**Self-payment trap**: The payer and recipient cannot be the same wallet address. When testing with the CLI, create a separate client account (`mppx account create -a client`) and fund it separately.

**Recipient wallet initialization**: TIP-20 token accounts on Tempo must be initialized before they can receive tokens (similar to Solana ATAs). Send a tiny amount (e.g. 0.01 USDC) to the recipient address first.

## Server

**Set `realm` explicitly for mppscan attribution.** The `realm` value is hashed into Tempo's attribution memo and is how mppscan correlates on-chain transactions to registered servers. Resolution order is **explicit value > env vars > request URL hostname > `"MPP Payment"`**. The env vars checked include `MPP_REALM`, `FLY_APP_NAME`, `HEROKU_APP_NAME`, `HOST`, `HOSTNAME`, `RAILWAY_PUBLIC_DOMAIN`, `RENDER_EXTERNAL_HOSTNAME`, `VERCEL_URL`, `WEBSITE_HOSTNAME`.

Two consequences:

- **In Kubernetes, `HOSTNAME` is the pod name** (e.g. `web-69d986c8d8-6dtdx`) which rotates on every deploy, giving a new server fingerprint each time. Set `MPP_REALM` to your stable public domain.
- **Env vars outrank the per-request hostname.** A server fronting several hostnames resolves every request to the same env-derived realm, so multi-host or multi-brand deployments must pass `realm` explicitly - typically one `Mppx.create()` instance per realm, selected by the incoming host.

```typescript
Mppx.create({
  methods: [tempo({ ... })],
  realm: 'api.example.com', // or process.env.MPP_REALM
  secretKey,
})
```

**`tempo()` vs explicit registration**: `tempo({ ... })` registers both `charge` and `session` intents with shared config. When you need different config per intent (e.g. session needs `store` and `sse: { poll: true }` but charge doesn't), register them explicitly:

```typescript
import { Mppx, Store, tempo } from 'mppx/server'
Mppx.create({
  methods: [
    tempo.charge({ currency, recipient }),
    tempo.session({ currency, recipient, store: Store.memory(), sse: { poll: true } }),
  ],
  secretKey,
})
```

**Hono multiple headers**: `c.header(name, value)` replaces by default. When emitting multiple `WWW-Authenticate` values (e.g. charge + session intents), the second call silently overwrites the first. Prefer `Mppx.compose()`, which handles multi-header emission correctly. If composing manually, use `{ append: true }`:

```typescript
c.header('WWW-Authenticate', chargeWwwAuth)
c.header('WWW-Authenticate', sessionWwwAuth, { append: true })
```

Apply the same branch at both the challenge site and the verification site. If you compose several methods when verifying but emit a single-method challenge, the 402 advertises fewer options than the server actually accepts.

**CORS headers**: `WWW-Authenticate` and `Payment-Receipt` must be listed in `access-control-expose-headers` or browsers/clients won't see them.

**Rotate `MPP_SECRET_KEY` with overlap**: challenge IDs are HMAC-bound to the secret, so a hard swap invalidates every in-flight challenge. Staged rollout: start issuing new challenges with the new key, keep verifying the previous key during a short overlap window, then drop the old key after outstanding challenges have expired. If your deployment can't verify current-and-previous keys, do a coordinated cutover and wait out the old challenge TTL.

**SSE utilities import path**: `Session.Sse.iterateData` is exported from `mppx/tempo`, NOT `mppx/server`:

```typescript
import { Mppx, Store, tempo } from 'mppx/server'
import { Session } from 'mppx/tempo'
const iterateSseData = Session.Sse.iterateData
```

## Diagnostics

mppx catches verification failures internally and re-emits them as a plain 402 with a fresh challenge, so a bad RPC endpoint, a failed broadcast, and a missing signer all look identical from outside. Three ways to see through it:

- `PaymentError` carries a structured `details` record (alongside `hint`) surfaced in the RFC 9457 problem document - read it rather than inferring from the status code.
- Register `onPaymentFailed` server-side; the handler receives the underlying error.
- From the client, `mppx -v` (details) and `-vv` (headers) show the negotiation.

## Stores

**Never use `Store.memory()` in production.** It loses all channel state on restart/redeploy. When state is lost, the server can't close channels or settle funds - client deposits stay reserved indefinitely. Use a persistent store.

Built-in store adapters (all handle BigInt serialization via `ox`'s `Json` module):

```typescript
import { Store } from 'mppx/server'

Store.memory()               // development only
Store.redis(redisClient)     // ioredis, node-redis, Valkey (added in 0.4.9)
Store.upstash(upstashClient) // Upstash Redis / Vercel KV
Store.cloudflare(kvNamespace) // Cloudflare KV
Store.from({ get, put, delete }) // custom adapter
```

**AtomicStore** (0.5.7+): Extends `Store` with an `update(key, fn)` method for safe concurrent read-modify-write. Used internally for replay protection and channel state. All built-in adapters support atomic updates. Custom adapters via `Store.from()` get an optimistic-retry implementation automatically.

**Polling mode**: If your store doesn't implement the optional `waitForUpdate()` method (e.g. custom adapters via `Store.from()`), pass `sse: { poll: true }` to `tempo.session()`. Otherwise SSE streams hang waiting for event-driven wakeups that never come.

## Request Handling

**Session voucher POSTs have no body.** Mid-stream voucher POSTs carry only `Authorization: Payment` - no JSON body. If your middleware decides charge vs session based on `body.stream`, vouchers hit the charge path. Check the **credential's intent** instead. As of mppx 0.4.9 the SDK skips route amount/currency/recipient validation for topUp and voucher credentials, so body-derived pricing mismatches no longer cause spurious 402 rejections.

**`close`/`topUp` management credentials are also bodyless.** They arrive as POSTs with only `Authorization: Payment`. If you run your own request-body validation (e.g. a Zod schema on the tool payload) before handing the request to `mppx.session()`, it rejects these with a spurious **400** before mppx can answer them (mppx replies `204 No Content`). Exempt session-management credentials from your body validator - gate on the credential's intent/action, not on body presence.

**Clone the request before reading the body.** `request.json()` consumes the Request body. If you parse the body first and then pass the original request to `mppx.session()` or `mppx.charge()`, the mppx handler gets an empty body and returns 402. Clone before reading.

## Pricing & Streaming

**Cheap model zero-charge floor**: Tempo USDC has 6-decimal precision. For very cheap models, per-token cost like `(0.10 / 1_000_000) * 1.3 = 0.00000013` rounds to `"0.000000"` via `toFixed(6)` - effectively zero. Add a minimum tick cost floor:

```typescript
const MIN_TICK_COST = 0.000001 // smallest Tempo USDC unit (6 decimals)
const tickCost = Math.max((outputRate / 1_000_000) * margin, MIN_TICK_COST)
```

**SSE chunks != tokens**: Per-SSE-event `stream.charge()` is an acceptable approximation. `stream.charge()` is serial (store read + write per call, per-channelId mutex) - no bulk API exists yet.

**Add upstream timeouts**: Always use `AbortSignal.timeout()` on upstream fetches. A stalled upstream holds the payment channel open, reserving client funds.

## Observability and Accounting

mppscan indexes MPP **payments by realm**, not raw chain transactions, so looking up a transaction hash there will not find it - use Tempo's own explorer for that. Session traffic compounds this: per-request vouchers are off-chain, so a busy streaming service reads as near-zero volume until settle and close transactions land.

For per-request accounting, keep your own ledger keyed by channel ID. Background-sweep settlements carry no request context, so attribution has to come from your side.

## Infrastructure

**Nginx proxy buffer overflow**: Large 402 headers can exceed nginx's default 4k `proxy_buffer_size`, causing **502 Bad Gateway**. Fix: `nginx.ingress.kubernetes.io/proxy-buffer-size: "16k"`. Debug by port-forwarding directly to the pod - if you get 402 there, the issue is in the ingress layer.

**Reverse-proxy scheme mismatch**: Behind a TLS-terminating proxy (Caddy/nginx/CDN), the request the server sees can be `http://` while the public origin is `https://`. If the challenge binds the resource URL, the signed payment then fails re-verification - a double-402 loop. Trust the forwarded-proto header or configure the public resource URL explicitly.

## Client / Tempo CLI

**Network selection**: the CLI defaults to Tempo mainnet. Use `--network testnet`, `--rpc-url`, or the `MPPX_RPC_URL` / `RPC_URL` env vars for testnet.

**Stale sessions after redeploy**: When the server redeploys and loses in-memory session state, clients get `"Session invalidation claim for channel 0x... was not confirmed on-chain"`. Fix with `mppx sessions close` (or `tempo wallet sessions close` / `sync`). Dispute window is 4-15 min.

## Client SDK Versioning (advisory)

These are field reports, not documented guarantees - verify against your own versions.

**Pin mppx and viem together.** Bumping `viem` independently of `mppx` has crashed the Tempo charge path with `TypeError: Cannot destructure property 'from' of 'parameters'` - a call-signature mismatch between the mppx build and a newer viem. Treat mppx + viem as a coupled pair. mppx 0.8.15 requires `viem >= 2.54.0`.

**A fast non-402 response is not a payment failure.** `mppx.fetch` sends an initial probe; if the response is not a 402 (e.g. an upstream 500) it returns it as-is immediately (hundreds of ms). Opening a real session channel takes seconds, so a quick failure means the upstream errored before any payment - disambiguate on latency plus status, and don't retry as if payment failed.
