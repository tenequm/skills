# Sessions

## Why Sessions

Usage-based billing needs payment verification that keeps pace with the service. LLM inference generates hundreds of tokens - paying per-token on-chain would add seconds of latency per charge. Sessions fix this: one deposit into an on-chain escrow, then off-chain vouchers verified with CPU-only signature checks (~microseconds). The bottleneck becomes CPU, not blockchain TPS.

Key insight: a session amortizes on-chain cost across many interactions. Instead of 0.001 USD per on-chain tx per request, you pay one open tx + one close tx regardless of how many requests happen in between.

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

- `mppx.session()` returns a handler that manages the full lifecycle automatically.
- `result.status === 402` means the client has not yet opened a channel or the voucher is missing/invalid.
- `result.challenge` sends the 402 response with payment requirements.
- `result.withReceipt` attaches the payment receipt header to the response.

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
const session = tempo.session({ account, maxDeposit: '1' })
const stream = await session.sse('http://localhost:3000/api/poem')
for await (const word of stream) {
  process.stdout.write(word + ' ')
}
const receipt = await session.close()
```

### Streaming Behavior

- `withReceipt` accepts an async generator - each `yield` produces one SSE event and one charge.
- If the balance is exhausted mid-stream, the server emits a `payment-need-voucher` event and pauses until the client sends a new voucher.
- The client SSE handler auto-renews vouchers transparently, so the stream resumes without application-level intervention.

## Session Receipts

Session receipts differ from charge receipts:

- `reference` contains `channelId` (a bytes32 hash), not a transaction hash.
- The on-chain settlement transaction hash is only available after the channel closes.
- Calling `close()` returns a receipt that includes the `txHash` of the settlement transaction.

## Store Backends

Sessions require state storage for channel data. Available backends:

| Backend | Usage | Notes |
|---------|-------|-------|
| `Store.memory()` | In-memory | Development only, state lost on restart |
| `Store.cloudflare()` | Cloudflare KV | Edge-compatible |
| `Store.upstash()` | Upstash Redis | Serverless Redis |
| Custom | Implement interface | Requires async `get`, `set`, `delete` methods |

## Escrow Contract

The `TempoStreamChannel` on-chain escrow manages deposits, settlements, and refunds.

### Deployed Addresses

- **Mainnet** (chain 4217): `0x33b901018174DDabE4841042ab76ba85D4e24f25`
- **Testnet Moderato** (chain 42431): `0xe1c4d3dce17bc111181ddf716f75bae49e61a336`

### Contract Operations

- **deposit**: Lock tokens into a channel.
- **settle**: Batch-settle vouchers, updating the channel's consumed amount.
- **close**: Final settlement plus refund of unspent tokens to the client.

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Voucher verification | ~microseconds (single `ecrecover`) |
| RPC calls during session | None (only on open/close/settle) |
| On-chain cost | Amortized: 0.001 USD total vs 0.001 USD per request for charge |
| Throughput | Hundreds of vouchers per second per channel |
