# Stripe Payment Method

## Overview

Stripe MPP supports **two payment methods**:

- **Fiat (SPT)** - **Shared Payment Tokens** let one Stripe account (client) create a token that another Stripe account (server) can use to charge cards, wallets, and other Stripe-supported methods. Requires a US legal entity. The server identifies itself via its Stripe **profile** (`profile_...`) ID as `networkId`.
- **Crypto** - direct on-chain payment using Stripe-managed crypto deposit addresses on Tempo, captured automatically when funds settle. See "Crypto (On-Chain) Method" below.

SPT flow:
1. Server responds with 402 challenge containing Stripe payment requirements.
2. Client creates an SPT (via the `@stripe/link-cli` spend-request flow, or a server-side proxy that holds the Stripe secret key).
3. Client sends the SPT as the credential payload.
4. Server creates a PaymentIntent using the SPT and confirms payment.

SPTs are single-use, scoped to a specific amount and currency, and bound to the server's Stripe profile ID.

---

## Server Setup

Import Stripe charge from `mppx/server` or `mppx/stripe`:

```ts
import Stripe from 'stripe'
import { stripe } from 'mppx/server'
```

### With Stripe SDK Instance

```ts
const charge = stripe.charge({
  client: new Stripe(process.env.STRIPE_SECRET_KEY!),
  networkId: process.env.STRIPE_PROFILE_ID!, // Stripe profile ID (profile_...)
  paymentMethodTypes: ['card'],
})
```

### With Secret Key

```ts
const charge = stripe.charge({
  secretKey: process.env.STRIPE_SECRET_KEY!,
  networkId: process.env.STRIPE_PROFILE_ID!, // profile_...
  paymentMethodTypes: ['card'],
})
```

### With Metadata

Attach metadata to the PaymentIntent for tracking, reconciliation, or plan gating:

```ts
const charge = stripe.charge({
  client: new Stripe(process.env.STRIPE_SECRET_KEY!),
  networkId: process.env.STRIPE_PROFILE_ID!, // profile_...
  paymentMethodTypes: ['card'],
  metadata: { plan: 'pro', feature: 'api-access' },
})
```

### Multiple Payment Methods

Accept cards, Link, and other Stripe-supported methods:

```ts
const charge = stripe.charge({
  secretKey: process.env.STRIPE_SECRET_KEY!,
  networkId: process.env.STRIPE_PROFILE_ID!, // profile_...
  paymentMethodTypes: ['card', 'link'],
})
```

### Server Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `client` | `Stripe` | One of `client` or `secretKey` | Stripe SDK instance |
| `secretKey` | `string` | One of `client` or `secretKey` | Stripe secret key (creates SDK internally) |
| `networkId` | `string` | Yes | Stripe profile (`profile_...`) ID from your Stripe Dashboard |
| `paymentMethodTypes` | `string[]` | Yes | Accepted payment methods (e.g. `['card']`, `['card', 'link']`) |
| `metadata` | `Record<string, string>` | No | Key-value pairs attached to the PaymentIntent |

---

## Client Setup

Import from `mppx/client` or `mppx/stripe`:

```ts
import { stripe } from 'mppx/client'
```

### Simple Setup

```ts
const charge = stripe({
  client: stripeJs, // Stripe.js instance (optional)
  createToken: async (params) => {
    const res = await fetch('/api/create-spt', {
      method: 'POST',
      body: JSON.stringify(params),
    })
    return res.json()
  },
  paymentMethod: 'pm_card_visa', // default payment method
})
```

### With Stripe Elements

Use the `onChallenge` callback to render Stripe Elements and collect the payment method interactively:

```ts
const charge = stripe({
  createToken: async (params) => {
    const res = await fetch('/api/create-spt', {
      method: 'POST',
      body: JSON.stringify(params),
    })
    return res.json()
  },
  onChallenge: async (challenge, elements) => {
    // Render Stripe Elements UI for user to enter card details
    const { paymentMethod } = await elements.submit()
    return { paymentMethod: paymentMethod.id }
  },
})
```

### Manual Flow

For full control over credential creation:

```ts
import { Challenge } from 'mppx'

const challenge = Challenge.fromResponse(response)
const credential = await charge.createCredential({
  challenge,
  context: { paymentMethod: 'pm_card_visa' },
})
```

### Client Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `client` | `StripeJs` | No | Stripe.js instance (for Elements integration) |
| `createToken` | `(params) => Promise<SPT>` | Yes | Callback to create SPT via proxy endpoint |
| `externalId` | `string` | No | External reference ID for tracking |
| `paymentMethod` | `string` | No | Default payment method ID (e.g. `pm_card_visa`) |

---

## SPT Creation

SPT creation requires a Stripe secret key, so it cannot happen in an untrusted client. The current canonical approach is the **`@stripe/link-cli`** spend-request flow:

```bash
# 1. Create a spend request (issues the SPT). Add --test in a sandbox.
npx @stripe/link-cli spend-request create \
  --payment-method-id csmrpd_xxx \
  --amount 100 \
  --credential-type shared_payment_token \
  --network-id profile_... \
  --request-approval

# 2. Pay the MPP endpoint using the spend request
npx @stripe/link-cli mpp pay https://your-endpoint.com/resource \
  --spend-request-id lsrq_xxx \
  --method POST \
  --data '{ ... }'
```

For a programmatic client, the `createToken` callback on the client method (above) calls a server-side endpoint you control that holds the Stripe secret key and returns the SPT, which the client then includes in the credential payload. The legacy `stripe.rawRequest('POST', '/v1/shared_payment/granted_tokens', ...)` endpoint is no longer documented in Stripe's canonical MPP guide - prefer the `@stripe/link-cli` flow.

## Crypto (On-Chain) Method

Stripe MPP can also accept direct on-chain payments via Tempo crypto deposit addresses. Stripe generates a deposit address per PaymentIntent and captures automatically when funds settle on-chain. Crypto PaymentIntents require API version `2026-03-04.preview` or later.

```ts
import Stripe from 'stripe'

const stripeClient = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2026-03-04.preview',
})

// Generate a Tempo deposit address backed by a Stripe PaymentIntent
const paymentIntent = await stripeClient.paymentIntents.create({
  amount: 1000,
  currency: 'usd',
  payment_method_types: ['crypto'],
  payment_method_data: { type: 'crypto' },
  payment_method_options: {
    crypto: { mode: 'deposit', deposit_options: { networks: ['tempo'] } },
  },
  confirm: true,
})
// paymentIntent.next_action.crypto_display_details.deposit_addresses.tempo.address
// -> use as the `recipient` in a tempo.charge() method
```

Present fiat (SPT) and crypto together on one endpoint with `Mppx.compose(...)`. See [docs.stripe.com/payments/machine/mpp](https://docs.stripe.com/payments/machine/mpp) for the full two-method handler.

---

## Request Fields

The challenge `request` parameter (base64url-encoded JSON) contains:

| Field | Type | Required | Description |
|---|---|---|---|
| `amount` | `string` | Yes | Payment amount in smallest currency unit |
| `currency` | `string` | Yes | ISO 4217 currency code (e.g. `usd`, `eur`) |
| `decimals` | `number` | Yes | Currency decimal places (e.g. `2` for cents) |
| `description` | `string` | No | Human-readable payment description |
| `expires` | `string` | No | ISO 8601 expiration timestamp (defaults to 5 minutes) |
| `externalId` | `string` | No | External reference for idempotency/tracking |
| `methodDetails.networkId` | `string` | Yes | Stripe Business Network profile ID |
| `methodDetails.paymentMethodTypes` | `string[]` | Yes | Accepted payment method types |
| `methodDetails.metadata` | `object` | No | Metadata key-value pairs |

Example decoded request:

```json
{
  "amount": 100,
  "currency": "usd",
  "description": "API access",
  "methodDetails": {
    "networkId": "acct_1234567890",
    "paymentMethodTypes": ["card"],
    "metadata": { "plan": "pro" }
  }
}
```

---

## Credential Payload

The credential `payload` sent by the client contains:

| Field | Type | Required | Description |
|---|---|---|---|
| `spt` | `string` | Yes | Shared Payment Token (starts with `spt_`) |
| `externalId` | `string` | No | External reference for tracking |

Example credential payload:

```json
{
  "spt": "<STRIPE_SPT_TOKEN>",
  "externalId": "order-456"
}
```

The server uses the SPT to create a PaymentIntent, confirm payment, and return a receipt with the PaymentIntent ID as the `reference`.

---

## Full Example

### Server

```ts
import Stripe from 'stripe'
import { Mppx, stripe } from 'mppx/server'

const mppx = Mppx.create({
  methods: [
    stripe.charge({
      client: new Stripe(process.env.STRIPE_SECRET_KEY!),
      networkId: process.env.STRIPE_NETWORK_ID!,
      paymentMethodTypes: ['card'],
      metadata: { service: 'my-api' },
    }),
  ],
})

export async function handler(req: Request) {
  const result = await mppx.charge({ amount: '1.00' })(req)
  if (result.status === 402) return result.challenge
  return result.withReceipt(Response.json({ data: 'paid content' }))
}
```

### Client

```ts
import { Mppx, stripe } from 'mppx/client'

Mppx.create({
  methods: [
    stripe({
      createToken: async (params) => {
        const res = await fetch('/api/create-spt', {
          method: 'POST',
          body: JSON.stringify(params),
        })
        return res.json()
      },
      paymentMethod: 'pm_card_visa',
    }),
  ],
})

const res = await fetch('https://api.example.com/paid')
// 402 -> SPT creation -> credential -> 200
```
