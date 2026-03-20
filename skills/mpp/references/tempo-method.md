# Tempo Payment Method

## Overview

Tempo is a blockchain purpose-built for payments. Key properties:

- **No native gas token**: fees are paid in stablecoins (USDC, pathUSD), not ETH/SOL
- **TIP-20 stablecoins**: pathUSD, USDC
- **~500ms deterministic finality**
- **Sub-cent fees** with fee sponsorship support
- **2D nonces**: parallel transaction ordering (no stuck-tx bottlenecks)
- **Payment lane**: dedicated lane for channel operations (sessions)

## Gas and Fee Tokens

Tempo has **no native gas token**. Transaction fees are denominated in USD and paid in any TIP-20 stablecoin. Every transaction must know which token to use for fees. Three levels of precedence (highest first):

1. **Transaction-level `feeToken`** - explicit per-transaction:
```typescript
const prepared = await prepareTransactionRequest(client, {
  account,
  calls: [{ to, data }],
  feeToken: '0x20C000000000000000000000b9537d11c60E8b50', // USDC
} as never)
const serialized = await signTransaction(client, { ...prepared, account } as never)
await sendRawTransaction(client, { serializedTransaction: serialized })
```

2. **Account-level default via `setUserToken`** - one-time call to the FeeManager precompile:
```typescript
import { setUserToken } from 'viem/tempo'
await client.fee.setUserTokenSync({
  token: '0x20C000000000000000000000b9537d11c60E8b50',
})
```
After this, all transactions from the account use USDC for gas unless overridden at the transaction level.

3. **Validator default** - if neither is set, the validator's preferred token is used (unreliable - don't depend on this).

**If no fee token can be determined, the transaction fails with `gas_limit: 0`.**

The mppx SDK sets `feeToken` automatically for payment transactions. Direct on-chain calls (manual settle, close, custom contracts) must set it explicitly via `feeToken` in `prepareTransactionRequest` or ensure `setUserToken` was called.

Note: Tempo transactions use a custom serialization format (type 0x76). Always use `signTransaction(client, ...)` from viem/actions (which uses the chain's serializer), NOT `account.signTransaction()` (which uses the default legacy serializer).

## Tempo Charge

### Server Configuration

```ts
import { tempo } from "@anthropic-ai/mpp/tempo";
import { Expires } from "@anthropic-ai/mpp";

const tempoCharge = tempo.charge({
  currency: "0x20c0000000000000000000000000000000000000", // pathUSD testnet
  recipient: "0xYourAddress",
  decimals: 6,
  description: "API access",
  externalId: "order-123",
  feePayer: privateKeyToAccount("0xSponsorPrivateKey"), // optional
  testnet: true,
  waitForConfirmation: true,
});
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `currency` | `string` | TIP-20 token address (required) |
| `recipient` | `string` | Payment recipient address (required) |
| `decimals` | `number` | Token decimals (default: 18) |
| `description` | `string` | Human-readable payment description |
| `externalId` | `string` | External reference ID |
| `feePayer` | `Account \| string` | Fee sponsor account or URL |
| `testnet` | `boolean` | Use Tempo testnet |
| `waitForConfirmation` | `boolean` | Wait for on-chain confirmation |

**Per-call overrides:**

```ts
const handler = mppx.charge({
  amount: "1.00",
  currency: "0x20c000000000000000000000b9537d11c60e8b50", // override token
  recipient: "0xDifferentRecipient",
  feePayer: "https://sponsor.example.com",
  expires: Expires.minutes(10),
})(request);
```

### Client Configuration

```ts
import { tempo } from "@anthropic-ai/mpp/tempo";
import { privateKeyToAccount } from "viem/accounts";

const tempoClient = tempo.charge({
  account: privateKeyToAccount("0xYourPrivateKey"),
  autoSwap: true,
  clientId: "my-app",
  mode: "pull",
});
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `account` | `Account` | viem account (privateKey, Passkey, or WebCrypto) |
| `autoSwap` | `boolean \| object` | Auto-swap from fallback stablecoin |
| `clientId` | `string` | Client identifier |
| `mode` | `'push' \| 'pull'` | Transaction broadcast mode (default: `'pull'`) |
| `getClient` | `function` | Custom viem client factory |

**autoSwap options:**

```ts
// Simple - use defaults
autoSwap: true

// Advanced - configure slippage and allowed input tokens
autoSwap: {
  slippage: 2, // percent
  tokenIn: ["0xFallbackTokenAddress"],
}
```

## Push vs Pull Modes

### Pull Mode (Default)

1. Client signs the transaction
2. Client sends serialized signed tx to server
3. Server broadcasts (enables fee sponsorship)
4. Credential payload: `{ type: 'transaction', signature }`

```ts
// Client - pull mode (default)
const client = tempo.charge({
  account: privateKeyToAccount("0x..."),
  mode: "pull",
});
```

### Push Mode

1. Client builds, signs, and broadcasts the transaction itself
2. Client sends tx hash to server for verification
3. Credential payload: `{ type: 'hash', hash }`

```ts
// Client - push mode (e.g. browser wallet)
const client = tempo.charge({
  account: privateKeyToAccount("0x..."),
  mode: "push",
});
```

The server handles both modes automatically - no server-side changes needed.

## Fee Sponsorship

Available in pull mode only. The server co-signs the transaction with the fee payer account before broadcasting, so the client never needs gas tokens.

```ts
// Option 1: Direct account
const charge = tempo.charge({
  currency: "0x20c0000000000000000000000000000000000000",
  recipient: "0xRecipient",
  feePayer: privateKeyToAccount("0xSponsorPrivateKey"),
  testnet: true,
});

// Option 2: External sponsor service
const charge = tempo.charge({
  currency: "0x20c0000000000000000000000000000000000000",
  recipient: "0xRecipient",
  feePayer: "https://sponsor.example.com",
  testnet: true,
});
```

Fee sponsorship is ignored for push-mode clients (they broadcast themselves).

## Optimistic Verification

Skip waiting for on-chain confirmation. Returns immediately after simulation succeeds. Use when latency matters more than guaranteed confirmation.

```ts
const charge = tempo.charge({
  currency: "0x20c0000000000000000000000000000000000000",
  recipient: "0xRecipient",
  waitForConfirmation: false,
  testnet: true,
});
```

## Tempo Session

### Server Configuration

```ts
import { tempo } from "@anthropic-ai/mpp/tempo";
import { Store } from "@anthropic-ai/mpp";

const tempoSession = tempo.session({
  currency: "0x20c0000000000000000000000000000000000000",
  recipient: "0xYourAddress",
  store: Store.memory(),
  escrowContract: "0xe1c4d3dce17bc111181ddf716f75bae49e61a336", // testnet
  sse: true,
});
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `currency` | `string` | TIP-20 token address |
| `recipient` | `string` | Payment recipient |
| `store` | `Store` | Session state storage |
| `escrowContract` | `string` | Escrow contract address |
| `sse` | `boolean` | Enable SSE streaming |

**Store options:**

```ts
Store.memory()       // In-memory (development)
Store.cloudflare()   // Cloudflare KV
Store.upstash()      // Upstash Redis
```

**Per-call configuration:**

```ts
const handler = mppx.session({
  amount: "0.001",
  unitType: "token", // billing unit name: 'token', 'photo', 'word', etc.
})(request);
```

### Client Configuration

```ts
const session = tempo.session({
  account: privateKeyToAccount("0x..."),
  maxDeposit: "5.00", // max tokens locked in escrow
});
```

The session lifecycle is auto-managed:
- First request: opens a payment channel (escrow deposit)
- Subsequent requests: signs vouchers (off-chain, instant)
- `session.close()`: settles on-chain, reclaims unspent deposit

**SSE streaming:**

```ts
const stream = session.sse("https://api.example.com/stream");
// Returns async iterable
for await (const event of stream) {
  console.log(event);
}
```

## Request Schema (Charge)

| Field | Type | Required | Description |
|---|---|---|---|
| `amount` | `string` | Yes | Payment amount |
| `currency` | `address` | Yes | TIP-20 token address |
| `decimals` | `number` | No | Token decimals |
| `recipient` | `address` | No | Override recipient |
| `chainId` | `number` | No | Chain ID |
| `externalId` | `string` | No | External reference |
| `memo` | `hex` | No | On-chain memo |
| `feePayer` | `boolean` | No | Request fee sponsorship |
| `description` | `string` | No | Payment description |

## Testnet vs Mainnet

### Token Addresses

| Network | Token | Address |
|---|---|---|
| Testnet | pathUSD | `0x20c0000000000000000000000000000000000000` |
| Mainnet | USDC | `0x20c000000000000000000000b9537d11c60e8b50` |

### Escrow Contracts

| Network | Chain ID | Address |
|---|---|---|
| Mainnet | 4217 | `0x33b901018174DDabE4841042ab76ba85D4e24f25` |
| Testnet | 42431 | `0xe1c4d3dce17bc111181ddf716f75bae49e61a336` |

### Configuration

```ts
// Testnet
const charge = tempo.charge({
  currency: "0x20c0000000000000000000000000000000000000",
  recipient: "0xRecipient",
  testnet: true,
});

// Mainnet - use USDC, remove testnet flag
const charge = tempo.charge({
  currency: "0x20c000000000000000000000b9537d11c60e8b50",
  recipient: "0xRecipient",
});
```

## Stripe Integration

Create dynamic recipient addresses backed by Stripe PaymentIntents for deposit-mode crypto payments.

```ts
// Stripe PaymentIntent with Tempo network
const paymentIntent = await stripe.paymentIntents.create({
  amount: 1000,
  currency: "usd",
  payment_method_types: ["crypto"],
  deposit_options: {
    networks: ["tempo"],
  },
});
```

See [Stripe crypto deposits documentation](https://docs.stripe.com/crypto/deposit-mode) for full PaymentIntent configuration.
