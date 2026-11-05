# Sessions

## Why Sessions

Usage-based billing needs payment verification that keeps pace with the service. LLM inference generates hundreds of tokens - paying per-token on-chain would add seconds of latency per charge. Sessions fix this: one deposit into an on-chain escrow, then off-chain vouchers verified with CPU-only signature checks (~microseconds). The bottleneck becomes CPU, not blockchain TPS.

Key insight: a session amortizes on-chain cost across many interactions. Instead of 0.001 USD per on-chain tx per request, you pay one open tx + one close tx regardless of how many requests happen in between.

## Sessions v2 (default) vs Legacy v1

Since mppx 0.7.0, `tempo.session()` is the **v2** flow built on the TIP-1034 session precompile. The earlier contract-backed escrow implementation (the escrow-contract and channel-recovery mechanics described later in this file) is **Sessions v1**, still shipped as `tempo.sessionLegacy` on both `mppx/server` and `mppx/client` - now carrying an explicit `@deprecated` marker pointing at `tempo.session()`.

- **Default:** `tempo.session()` = v2; `tempo.sessionLegacy()` = v1, deprecated.
- **Interop cliff:** a v2-expecting client rejects a v1 session challenge (it lacks `methodDetails.sessionProtocol: "v2"`) and falls back to the charge path. A server still on old mppx serving v1 sessions silently denies newer clients their working path - keep client and server on matching flows, or advertise v2.
- **Refunds:** MPP defines no refund protocol - a charge is refunded out-of-protocol by sending funds back to the payer. For sessions, v2 reserves funds in the channel without immediately claiming them, so unclaimed reserved funds are refunded by default. v1 refunds by closing the channel (unspent escrow returned to the client).
- **Where the funds live:** v2 uses a fixed TIP-20 channel precompile (`tip20ChannelEscrow`) at the same address on mainnet (4217) and Moderato testnet (42431). v1 used a deployed `TempoStreamChannel` contract per network.

Two client entry points:
- `tempo.session({ account, maxDeposit })` - creates the method registered in `Mppx.create()`; the managed `fetch` opens and reuses the channel transparently.
- `tempo.session.manager({ account, maxDeposit })` - returns a managed client for direct lifecycle control (`.sse()`, `.close()`), used when you drive the session yourself instead of through `fetch`.

## Session Lifecycle

Four phases define a session's life:

### 1. Open

Client deposits tokens into an on-chain escrow contract, creating a payment channel. A unique `channelId` identifies the channel and holds deposited TIP-20 tokens.

### 2. Session (Vouchers)

Client signs EIP-712 typed vouchers with increasing cumulative amounts. Each voucher states "I have consumed up to X total." The server verifies each voucher with `ecrecover` - no RPC calls needed. The delta (current voucher minus previous voucher) represents the cost of the current request.

### 3. Top Up

If the channel balance runs low, the client deposits more tokens without closing. The session continues uninterrupted. When streaming, the server emits a `payment-need-voucher` SSE event to signal the client needs to top up.

### 4. Close

Either party can close the channel. The server calls `close()` on the escrow contract with the highest voucher, settling the final balance on-chain. Any unspent deposit is refunded to the client.

## Server Integration

```typescript
import { Mppx, Store, tempo } from 'mppx/server'
const mppx = Mppx.create({
  methods: [tempo({
    recipient: '0x...',
    store: Store.memory(), // or Store.cloudflare(), Store.upstash()
  })],
})

export async function handler(request: Request) {
  const result = await mppx.session({
    amount: '0.001',
    unitType: 'token',
  })(request)
  if (result.status === 402) return result.challenge
  return result.withReceipt(Response.json({ data: '...' }))
}
```

- `mppx.session()` returns a handler that manages the per-request lifecycle automatically. It does **not** settle on-chain by itself - see Settlement below.
- `result.status === 402` means the client has not yet opened a channel or the voucher is missing/invalid.
- `result.challenge` sends the 402 response with payment requirements.
- `result.withReceipt` attaches the payment receipt header to the response.
- `voucherSigner` (renamed from `authorizedSigner` in mppx 0.6.29) now exists **only on the legacy v1 path**; v2 derives voucher authority from the session descriptor. The on-chain v1 `channels()` ABI field is still named `authorizedSigner`.

## Settlement

Verifying a voucher is not the same as getting paid. The server stores the highest accepted voucher; converting that into an on-chain transfer is a separate step, and **nothing does it automatically unless you configure it**. A server that never settles accrues signed vouchers it cannot spend, while payer deposits stay reserved in open channels.

### Scheduled settlement (recommended)

`settlementSchedule` is server-owned - clients never see it and cannot influence it. Any of its three triggers can fire:

```typescript
tempo.session({
  currency: '<PATHUSD_TESTNET>',
  recipient: '0x...',
  store,
  settlementSchedule: {
    units: 10_000,      // settle after this many additional paid units
    amount: '1.00',     // ...or this much additional settled amount
    intervalMs: 300_000, // ...or this long since the last scheduled settlement
  },
})
```

### Manual settlement

Drive settlement yourself when you want a sweep on your own cadence, or need to drain channels at shutdown:

```typescript
import { tempo } from 'mppx/server'

// Settle one channel: reads the highest stored voucher and submits it on-chain.
const txHash = await tempo.settle(store, client, channelId)

// Batch-settle precompile-backed channels.
await tempo.settleBatch(store, client, channelIds)
```

Both throw rather than silently no-op: `ChannelNotFoundError` if the channel is unknown, and a verification error if the channel is not precompile-backed or has no voucher to settle.

### Settle vs close

- **Settle** claims what has been consumed so far and leaves the channel open and reusable. This is what you want on a live channel.
- **Close** performs a final settlement and releases the payer's remaining reservation.

Settling alone is not a complete policy: a client that walks away leaves its channel open indefinitely with funds reserved. Pair a settle cadence with a close policy for channels that have been idle long enough that the session is clearly over.

### Observing settlement

The `onSessionSettlement` server hook fires for both scheduled and explicit settlements, with chain-agnostic context (`trigger`, `txHash`, `channelId`, cumulative amount, incremental delta). Use it to build the ledger that on-chain data alone will not give you, since per-request vouchers never appear as individual transactions.

## Client Integration

```typescript
import { Mppx, tempo } from 'mppx/client'
Mppx.create({
  methods: [tempo({ account, maxDeposit: '1' })], // Lock up to 1 pathUSD
})
// 1st request: opens channel on-chain, sends initial voucher
// 2nd+ requests: off-chain vouchers (no on-chain tx)
const res = await fetch('http://localhost:3000/api/resource')
```

- `maxDeposit`: maximum tokens locked in escrow. At $0.01/unit, 1 pathUSD covers 100 requests.
- If the server sets `suggestedDeposit`, the client uses `min(suggestedDeposit, maxDeposit)`.
- Channels remain open for reuse across multiple requests. Close explicitly when done.
- `channelStore`: pass a store to persist and reuse payer session channels across processes/restarts (mppx 0.8.0). On Node, `mppx/client/node` provides a SQLite store that shares Tempo Wallet's channel database. The client-side `authorizedSigner` override was removed in 0.8.0 - voucher authority now derives from the selected account.
- `topUpAmount`: preferred top-up size. The default is a bounded server suggestion and then the **exact shortfall**, which means a fine-grained stream can trigger a top-up round-trip per shortfall. Setting a `topUpAmount` batches those into fewer, larger top-ups without changing what the payer ultimately pays, since the server settles actual spend.

Client sessions rehydrate from server snapshots, reconciling the last accepted voucher against on-chain channel state before continuing cumulative payments - so a client that restarts mid-session resumes rather than opening a second channel.

## SSE Streaming

Per-token billing over Server-Sent Events enables real-time charging for streamed content.

### Server

```typescript
const mppx = Mppx.create({
  methods: [tempo({ currency: '0x20c0...', recipient: '0x...', sse: true })],
})
export const GET = mppx.session({ amount: '0.001', unitType: 'word' })(
  async () => {
    return async function* (stream) {
      yield JSON.stringify({ title: 'Example' })
      for (const word of words) {
        await stream.charge() // deducts from session balance
        yield word
      }
    }
  }
)
```

### Client

```typescript
// .sse()/.close() live on the managed client from tempo.session.manager()
const session = tempo.session.manager({ account, maxDeposit: '1' })
const stream = await session.sse('http://localhost:3000/api/poem')
for await (const word of stream) {
  process.stdout.write(word + ' ')
}
const receipt = await session.close()
```

Since mppx 0.8.12, the polyfilled/standalone client `fetch` also handles payment-aware session SSE responses, so a plain `fetch` against a streaming endpoint renews vouchers mid-stream rather than truncating when the balance runs out. `session.sse()` remains the explicit path when you want direct lifecycle control.

### Streaming Behavior

- `withReceipt` accepts an async generator - each `yield` produces one SSE event and one charge.
- If the balance is exhausted mid-stream, the server emits a `payment-need-voucher` event and pauses until the client sends a new voucher.
- The client SSE handler auto-renews vouchers transparently, so the stream resumes without application-level intervention.

## WebSocket Streaming

WebSocket transport provides bidirectional streaming payments, where voucher delivery and content streaming happen over the same persistent connection (no separate HTTP POSTs for vouchers).

### Server

```typescript
import { Ws } from 'mppx/tempo'
import { Store, tempo } from 'mppx/server'

const wsHandler = Ws.serve({
  methods: [tempo.session({ currency: '0x20c0...', recipient: '0x...', store: Store.redis(redis) })],
  secretKey: process.env.MPP_SECRET_KEY!,
  async onMessage(ws, data, stream) {
    const parsed = JSON.parse(data)
    for (const token of generateTokens(parsed.prompt)) {
      await stream.charge()
      ws.send(JSON.stringify({ mpp: 'message', data: token }))
    }
  },
})
```

### Message Types

```typescript
// Client → Server
{ mpp: 'authorization', authorization: string }     // Payment credential
{ mpp: 'payment-close-request' }                    // Request channel close

// Server → Client
{ mpp: 'message', data: string }                    // Paid content
{ mpp: 'payment-need-voucher', data: NeedVoucherEvent } // Top-up request
{ mpp: 'payment-receipt', data: SessionReceipt }    // Payment receipt
{ mpp: 'payment-close-ready', data: SessionReceipt } // Close confirmation
{ mpp: 'payment-error', status: number, message: string } // Error
```

### Key Differences from SSE

- **Bidirectional**: Both credential submission and content delivery happen over the same WebSocket connection (SSE uses separate HTTP POST for vouchers)
- **In-band close**: Channel close negotiation happens via WebSocket messages rather than HTTP requests
- **Security hardening**: Close receipts bound to signed close amount, spend committed only on actual delivery, local `maxDeposit` enforced, delivered chunks tracked for fallback close on disconnect

## Channel Recovery After Restarts

### Server bootstrap (preferred)

Set `bootstrap: true` on the session method and the server emits bootstrap hints so a returning client lazily recovers its previous channel from the same protected route before opening a new one:

```typescript
tempo.session({ currency, recipient, store, bootstrap: true })
```

Bootstrap snapshots carry the highest signed voucher, so the client reconciles against on-chain state and continues the existing cumulative sequence.

Note what bootstrap can and cannot do. Challenge generation is computed from method defaults and does not query the store, and an unpaid first request carries no payer identity - so the server has nothing to look up for a client it has never seen on that route. Client-side channel persistence (`channelStore`) remains the reliable resumption path across processes; bootstrap covers the same-route case.

### Manual `channelId` (fallback)

Pass `channelId` to `mppx.session()` so returning clients recover existing on-chain channels instead of opening new ones. The `SessionMethodDetails` type has an optional `channelId` field. When included in the 402 challenge, the client SDK's `tryRecoverChannel()` reads on-chain state and resumes the existing channel.

The server doesn't auto-populate this - it's the application's job:

```typescript
import { Credential } from 'mppx'

// Extract channelId from the credential's payload before calling mppx.session()
let channelId: string | undefined
try {
  const credential = Credential.fromRequest(request)
  if (credential.challenge.intent === 'session') {
    const payload = credential.payload as { channelId?: string }
    channelId = payload.channelId
  }
} catch {
  // No credential yet
}

// Pass channelId so the 402 challenge includes it for client-side recovery
const result = await mppx.session({
  amount: tickCost,
  unitType: 'token',
  ...(channelId && { channelId }),
})(request)
```

**Why this matters:** After a server restart, even with a persistent store, the first voucher from a returning client may fail verification (e.g., store was briefly unavailable). Without `channelId` in the re-issued 402 challenge, the client opens a new channel - locking more USDC in escrow while the old deposit sits unclaimed. With `channelId`, the client recovers the existing on-chain channel and continues using it.

## Session Receipts

Session receipts differ from charge receipts:

- `reference` contains `channelId` (a bytes32 hash), not a transaction hash.
- `acceptedCumulative` is the running total the server has accepted, `spent` the amount consumed, and `units` the metered count - a per-request receipt reports cumulative state, not the cost of that one request. Deriving a per-call price by reading the challenge amount at credential time gives blank or wrong values; compute deltas from `acceptedCumulative` instead.
- `txHash` is only populated once settlement lands on-chain, so it is absent on ordinary voucher receipts.
- Calling `close()` returns a receipt that includes the `txHash` of the settlement transaction.

## Store Backends

Sessions require state storage for channel data. Available backends:

| Backend | Usage | Notes |
|---------|-------|-------|
| `Store.memory()` | In-memory | Development only, state lost on restart |
| `Store.redis()` | Redis client | Self-hosted or managed Redis |
| `Store.cloudflare()` | Cloudflare KV | Edge-compatible |
| `Store.upstash()` | Upstash Redis | Serverless Redis |
| Custom | Implement interface | Requires async `get`, `set`, `delete` methods |

## Escrow Contracts (Sessions v1)

Everything in this section (through Payer-Initiated Recovery) describes the **v1** contract-backed flow used by `tempo.sessionLegacy`. Sessions v2 replaces it with the TIP-20 channel precompile and does not expose these operations; the payer-initiated recovery path below still matters for channels opened under v1. The `TempoStreamChannel` on-chain escrow manages deposits, settlements, and refunds for v1.

### Deployed Addresses

- **Mainnet** (chain 4217): `<ESCROW_MAINNET>`
- **Testnet Moderato** (chain 42431): `<ESCROW_TESTNET>`

### Contract Operations

- **deposit**: Lock tokens into a channel.
- **settle**: Batch-settle vouchers, updating the channel's consumed amount.
- **close**: Final settlement plus refund of unspent tokens to the client. **Payee-only** - only the server (payee) can call this.
- **requestClose**: Payer-initiated close request. Starts a grace period during which the server can still settle outstanding vouchers.
- **withdraw**: Payer reclaims deposit after the grace period expires. Emits `ChannelExpired`.
- **CLOSE_GRACE_PERIOD**: View function returning the grace period duration (900 seconds / 15 minutes on mainnet).

### Payer-Initiated Recovery

If the server is unresponsive or fails to close a channel, the payer can recover locked funds using a two-step process:

1. **`requestClose(channelId)`** - signals intent to close. The server gets a grace period (15 min on mainnet) to settle any outstanding vouchers it holds.
2. **Wait for grace period** - `CLOSE_GRACE_PERIOD()` returns the duration. The `CloseRequested` event includes `closeGraceEnd` timestamp.
3. **`withdraw(channelId)`** - after the grace period, the payer reclaims the full unsettled deposit.

```typescript
import { createClient, encodeFunctionData, http, parseAbi, type Hex } from 'viem'
import { prepareTransactionRequest, readContract, sendRawTransaction, signTransaction } from 'viem/actions'
import { tempo } from 'viem/chains'

const ESCROW = '<ESCROW_MAINNET>' as Hex
const USDC = '<USDC_TEMPO_MAINNET>' as Hex

const abi = parseAbi([
  'function requestClose(bytes32 channelId)',
  'function withdraw(bytes32 channelId)',
  'function CLOSE_GRACE_PERIOD() view returns (uint64)',
  'function channels(bytes32) view returns (bool finalized, uint64 closeRequestedAt, address payer, address payee, address token, address authorizedSigner, uint128 deposit, uint128 settled)',
])

const client = createClient({ account, chain: tempo, transport: http('https://rpc.tempo.xyz') })

// Step 1: Request close
const data = encodeFunctionData({ abi, functionName: 'requestClose', args: [channelId] })
const prepared = await prepareTransactionRequest(client, {
  account, calls: [{ to: ESCROW, data }], feeToken: USDC,
} as never)
const serialized = await signTransaction(client, { ...prepared, account } as never) as Hex
await sendRawTransaction(client, { serializedTransaction: serialized })

// Step 2: Wait for grace period (15 min on mainnet), then withdraw
const withdrawData = encodeFunctionData({ abi, functionName: 'withdraw', args: [channelId] })
// ... same prepare + sign + send pattern
```

Key details:
- `close()` is **payee-only**. Calling it as the payer reverts with `NotPayee()`.
- During the grace period, the server can still call `close()` with the highest voucher to claim earned funds.
- If the server does nothing, `withdraw()` returns the entire unsettled deposit to the payer.
- Tempo transactions use the `calls` pattern and `feeToken` for gas payment in USDC. Use `signTransaction(client, ...)` (not `account.signTransaction`) to get Tempo's custom serializer.
- To find open channels, query `ChannelOpened` events filtered by payer address, then check each channel's state via `channels(channelId)`. Paginate event queries in chunks of 100k blocks (Tempo RPC limit).

## Security

- Voucher replay checks cover settled vouchers and mismatched credential sources (hardened in mppx 0.8.7), so a voucher cannot be re-presented after its cumulative amount has been settled, nor reused from a different declared source.
- WebSocket close receipts are bound to the signed close amount, spend is committed only when chunks are actually delivered, local `maxDeposit` is enforced on streamed voucher requests, and delivered chunks are tracked for a fallback close on disconnect.
- `maxDeposit` is the payer's hard ceiling on funds at risk in a channel. Set it deliberately: it bounds the loss if a server never closes.

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Voucher verification | ~microseconds (single `ecrecover`) |
| RPC calls during session | None (only on open/close/settle) |
| On-chain cost | Amortized: 0.001 USD total vs 0.001 USD per request for charge |
| Throughput | Hundreds of vouchers per second per channel |
