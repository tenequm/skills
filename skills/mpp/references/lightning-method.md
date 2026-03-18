# Lightning Payment Method

## Overview

Lightning enables Bitcoin payments over the Lightning Network using the `@buildonspark/lightning-mpp-sdk` package. Payments use **BOLT11 invoices** - the standard Lightning payment request format.

Key properties:

- **Cryptographic verification**: `sha256(preimage) == paymentHash` - verification is entirely local, no RPC or API calls needed
- **Synchronous settlement**: payment settles before the HTTP response returns
- **Global and permissionless**: no accounts, KYC, or payment processor needed
- **Self-custodial**: both client and server use Spark wallets backed by BIP-39 mnemonics

---

## Lightning Charge

One-time payment per request. Server generates a BOLT11 invoice, client pays it, server verifies the preimage.

### Server Setup

```ts
import { spark } from '@buildonspark/lightning-mpp-sdk/server'

const charge = spark.charge({
  mnemonic: process.env.MNEMONIC!, // BIP-39 mnemonic for Spark wallet
})
```

The server method handles:
1. Generating a BOLT11 invoice for the requested amount.
2. Extracting the `paymentHash` from the invoice.
3. Verifying the client's preimage: `sha256(hex_to_bytes(preimage)) == paymentHash`.

### Client Setup

```ts
import { spark } from '@buildonspark/lightning-mpp-sdk/client'

const charge = spark.charge({
  mnemonic: process.env.MNEMONIC!, // BIP-39 mnemonic for Spark wallet
})
```

The client method auto-pays the BOLT11 invoice from the challenge and returns the preimage as the credential.

### Full Charge Example

```ts
import { Mppx } from 'mppx/server'
import { spark } from '@buildonspark/lightning-mpp-sdk/server'

// Server
const mppx = Mppx.create({
  methods: [spark.charge({ mnemonic: process.env.MNEMONIC! })],
})

export async function handler(req: Request) {
  const result = await mppx.charge({ amount: '100' })(req) // 100 satoshis
  if (result.status === 402) return result.challenge
  return result.withReceipt(Response.json({ data: 'paid content' }))
}
```

```ts
import { Mppx } from 'mppx/client'
import { spark } from '@buildonspark/lightning-mpp-sdk/client'

// Client
Mppx.create({
  methods: [spark.charge({ mnemonic: process.env.MNEMONIC! })],
})

const res = await fetch('https://api.example.com/data')
// 402 -> auto-pay BOLT11 invoice -> credential with preimage -> 200
```

### Request Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `amount` | `number` | Yes | Payment amount in satoshis |
| `currency` | `string` | Yes | Always `'BTC'` |
| `methodDetails.invoice` | `string` | Yes | BOLT11 payment request string |
| `methodDetails.paymentHash` | `string` | Yes | SHA-256 hash (hex) that the preimage must satisfy |
| `methodDetails.network` | `string` | No | `'mainnet'` (default) or `'regtest'` |

### Credential Payload

| Field | Type | Required | Description |
|---|---|---|---|
| `preimage` | `string` | Yes | 32-byte hex preimage proving payment |

### Verification

Verification is a single hash operation - no network calls:

```
sha256(hex_to_bytes(preimage)) == paymentHash
```

If the hash matches, the payment is cryptographically proven. The preimage can only be obtained by paying the invoice through the Lightning Network.

### With Regtest

For local development and testing, use the regtest network:

```ts
// Server
const charge = spark.charge({
  mnemonic: process.env.MNEMONIC!,
  network: 'regtest',
})

// Client
const charge = spark.charge({
  mnemonic: process.env.MNEMONIC!,
  network: 'regtest',
})
```

---

## Lightning Session

Sessions use a deposit invoice as an upfront payment. The preimage from paying the deposit becomes a bearer token for subsequent requests.

### How It Works

1. **Open**: Server generates a deposit invoice. Client pays it. The preimage becomes the session bearer token.
2. **Per-request**: Client sends the preimage with each request. Server verifies `sha256(preimage) == paymentHash` - a single hash operation.
3. **Top-up**: If the session balance runs low, the server issues a fresh deposit invoice. Client pays it, and the new preimage extends the session.
4. **Close**: Server refunds unspent balance via the client's return invoice.

### Server Setup

```ts
import { spark } from '@buildonspark/lightning-mpp-sdk/server'

const session = spark.session({
  mnemonic: process.env.MNEMONIC!,
})
```

### Client Setup

```ts
import { spark } from '@buildonspark/lightning-mpp-sdk/client'

const session = spark.session({
  mnemonic: process.env.MNEMONIC!,
})
```

### Full Session Example

```ts
import { Mppx } from 'mppx/server'
import { spark } from '@buildonspark/lightning-mpp-sdk/server'

// Server
const mppx = Mppx.create({
  methods: [spark.session({ mnemonic: process.env.MNEMONIC! })],
})

export async function handler(req: Request) {
  const result = await mppx.session({
    amount: '10', // 10 satoshis per request
    unitType: 'request',
  })(req)
  if (result.status === 402) return result.challenge
  return result.withReceipt(Response.json({ data: 'session content' }))
}
```

```ts
import { Mppx } from 'mppx/client'
import { spark } from '@buildonspark/lightning-mpp-sdk/client'

// Client
Mppx.create({
  methods: [spark.session({ mnemonic: process.env.MNEMONIC! })],
})

// 1st request: pays deposit invoice, receives bearer token
const res1 = await fetch('https://api.example.com/data')

// 2nd+ requests: uses preimage as bearer token (no new Lightning payment)
const res2 = await fetch('https://api.example.com/data')
```

### Session Lifecycle Details

**Per-request verification** is extremely fast:

```
sha256(preimage) == paymentHash  // single CPU hash operation
```

No RPC calls, no network requests, no database lookups. This makes Lightning sessions suitable for high-frequency APIs.

**Top-up** works transparently:

1. Server detects session balance is low.
2. Server issues a fresh deposit invoice in the 402 response.
3. Client pays the new invoice.
4. New preimage extends the session.

**Close** refunds unspent balance:

1. Server calculates unspent amount from the deposit.
2. Client provides a return invoice.
3. Server pays the return invoice, refunding the client.

---

## Cleanup

Lightning methods maintain WebSocket connections to the Spark network. Always call `cleanup()` when shutting down:

```ts
const charge = spark.charge({ mnemonic: process.env.MNEMONIC! })

// ... use the method ...

// Required: close WebSocket connections
await charge.cleanup()
```

For sessions:

```ts
const session = spark.session({ mnemonic: process.env.MNEMONIC! })

// ... use the method ...

await session.cleanup()
```

Failing to call `cleanup()` will leave WebSocket connections open, potentially causing resource leaks in long-running processes.

---

## Choosing an Intent

| | Charge | Session |
|---|---|---|
| **Pattern** | One Lightning payment per request | Deposit upfront, bearer token for many requests |
| **Latency** | Lightning payment per request (~1-3s) | First request: Lightning payment; subsequent: hash check (~microseconds) |
| **Best for** | Infrequent, high-value API calls | High-frequency APIs, streaming, metered billing |
| **Verification** | `sha256(preimage) == paymentHash` | `sha256(preimage) == paymentHash` (same, but amortized) |
| **Refunds** | Not applicable (exact amount per request) | Unspent balance refunded via return invoice |
