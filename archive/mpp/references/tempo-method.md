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
  feeToken: '<USDC_TEMPO_MAINNET>', // USDC mainnet (see Token Addresses table below)
} as never)
const serialized = await signTransaction(client, { ...prepared, account } as never)
await sendRawTransaction(client, { serializedTransaction: serialized })
```

2. **Account-level default via `setUserToken`** - one-time call to the FeeManager precompile:
```typescript
import { setUserToken } from 'viem/tempo'
await client.fee.setUserTokenSync({
  token: '<USDC_TEMPO_MAINNET>',
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
import { tempo } from "mppx/server";
import { Expires } from "mppx";

const tempoCharge = tempo.charge({
  currency: "<PATHUSD_TESTNET>",
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
  currency: "<USDC_TEMPO_MAINNET>", // override token (USDC.e mainnet)
  recipient: "0xDifferentRecipient",
  feePayer: "https://sponsor.example.com",
  expires: Expires.minutes(10),
})(request);
```

### Client Configuration

```ts
import { tempo } from "mppx/client";
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
| `expectedChainId` | `number` | Reject charge challenges whose `methodDetails.chainId` differs - pins the client to one Tempo network (mppx 0.7.0+) |

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
  currency: "<PATHUSD_TESTNET>",
  recipient: "0xRecipient",
  feePayer: privateKeyToAccount("0xSponsorPrivateKey"),
  testnet: true,
});

// Option 2: External sponsor service
const charge = tempo.charge({
  currency: "<PATHUSD_TESTNET>",
  recipient: "0xRecipient",
  feePayer: "https://sponsor.example.com",
  testnet: true,
});
```

Fee sponsorship is ignored for push-mode clients (they broadcast themselves).

### Sponsorship Budget Caps

Sponsoring gas means paying for other people's transactions, so the sponsor path carries two in-flight budget limits:

| Parameter | Default | Purpose |
|---|---|---|
| `maxInFlightReservations` | `100` | Maximum sponsored transactions awaiting a terminal receipt |
| `maxInFlightTotalFee` | `maxTotalFee * 10` | Maximum total fee reserved across in-flight sponsorships |

Sponsorship also rejects non-canonical fee-payer calldata and client-supplied access lists before signing, so a client cannot smuggle extra state access into a transaction the server pays for.

## Relays

A relay delegates credential validation and broadcast to Tempo API or a compatible MPP relay, so your server does not need its own RPC path or broadcast wallet:

```ts
const charge = tempo.charge({
  currency: "<USDC_TEMPO_MAINNET>",
  recipient: "0xRecipient",
  relay: { apiKey: process.env.TEMPO_API_KEY, apiBaseUrl: "https://api.tempo.xyz" },
})
```

The relay contract has two hooks. `validate` (optional) checks whether a credential is valid for the underlying rail without reserving funds or making state changes; `broadcast` performs settlement. This mirrors the `validateCredential` / `broadcastCredential` split on the server. See [mpp.dev/advanced/relays](https://mpp.dev/advanced/relays).

## Optimistic Verification

Skip waiting for on-chain confirmation. Returns immediately after simulation succeeds. Use when latency matters more than guaranteed confirmation.

```ts
const charge = tempo.charge({
  currency: "<PATHUSD_TESTNET>",
  recipient: "0xRecipient",
  waitForConfirmation: false,
  testnet: true,
});
```

## Tempo Session

Since mppx 0.7.0, `tempo.session()` is the **v2** (TIP-1034 precompile) flow; the prior contract-backed flow is `tempo.sessionLegacy` (server and client). Use `tempo.session()` for `Mppx.create()` registration and `tempo.session.manager({ account, maxDeposit })` for direct lifecycle control (`.sse()`, `.close()`). `tempo.common()` registers the Tempo charge + session bundle in one call.

### Server Configuration

```ts
import { Store, tempo } from "mppx/server";

const tempoSession = tempo.session({
  currency: "<PATHUSD_TESTNET>",
  recipient: "0xYourAddress",
  store: Store.memory(),
  escrowContract: "<ESCROW_TESTNET>",
  sse: true,
});
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `currency` | `string` | TIP-20 token address |
| `recipient` | `string` | Payment recipient |
| `store` | `Store` | Session state storage |
| `escrowContract` | `string` | Escrow contract address (v1) |
| `sse` | `boolean` | Enable SSE streaming |
| `settlementSchedule` | `object` | Server-owned automatic settlement by `units`, `amount`, and/or `intervalMs` |
| `bootstrap` | `boolean` | Emit hints so returning clients recover a prior channel on the same route |
| `voucherSigner` | `Account` | **v1 only.** Account authorized to sign vouchers (renamed from `authorizedSigner` in mppx 0.6.29; the on-chain `channels()` ABI field is still `authorizedSigner`) |

Without a `settlementSchedule` or your own `tempo.settle()` sweep, the server never converts accepted vouchers into on-chain funds. See `references/sessions.md`.

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
// Direct lifecycle control (.sse()/.close()) comes from tempo.session.manager()
const session = tempo.session.manager({
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
| Testnet | pathUSD | `<PATHUSD_TESTNET>` |
| Mainnet | USDC.e (Bridged USDC) | `<USDC_TEMPO_MAINNET>` |

### Escrow Contracts

| Network | Chain ID | Address |
|---|---|---|
| Mainnet | 4217 | `<ESCROW_MAINNET>` |
| Testnet | 42431 | `<ESCROW_TESTNET>` |

### Configuration

```ts
// Testnet
const charge = tempo.charge({
  currency: "<PATHUSD_TESTNET>",
  recipient: "0xRecipient",
  testnet: true,
});

// Mainnet - use USDC.e (Bridged USDC), remove testnet flag
const charge = tempo.charge({
  currency: "<USDC_TEMPO_MAINNET>",
  recipient: "0xRecipient",
});
```

## Split Payments

Distribute a single charge across multiple recipients in one transaction (0.4.12+). The client constructs a multi-transfer transaction; the server verifies all splits match the challenge requirements.

```ts
// Server - configure split recipients
const charge = tempo.charge({
  currency: "<PATHUSD_TESTNET>",
  recipients: [
    { address: "0xPlatform", share: 0.9 },  // 90% to platform
    { address: "0xCreator", share: 0.1 },    // 10% to creator
  ],
  testnet: true,
});

// Per-request with dynamic splits
const result = await mppx.charge({
  amount: "1.00",
  recipients: [
    { address: "0xPlatform", amount: "0.90" },
    { address: "0xCreator", amount: "0.10" },
  ],
})(request);
```

Documented constraints: **1-10 splits per charge**, each split may carry its own memo, and `expectedRecipients` restricts which recipient addresses a split is allowed to target (server-side validation). The server verifies that the sum of split amounts equals the total charge amount and that each transfer targets an expected recipient. See [mpp.dev/guides/split-payments](https://mpp.dev/guides/split-payments) for the full guide.

## Stripe Integration

Create dynamic recipient addresses backed by Stripe PaymentIntents for deposit-mode crypto payments.

```ts
// Stripe PaymentIntent with Tempo network
const paymentIntent = await stripe.paymentIntents.create({
  amount: 1000,
  currency: "usd",
  payment_method_data: { type: "crypto" },
  payment_method_options: {
    crypto: { mode: "deposit", deposit_options: { networks: ["tempo"] } },
  },
  confirm: true,
});
```

Requires Stripe API version `2026-03-25.preview` or later. See the [deposit mode integration guide](https://docs.stripe.com/payments/deposit-mode-stablecoin-payments) for full PaymentIntent configuration, and `references/stripe-method.md` for the MPP-side wiring.
