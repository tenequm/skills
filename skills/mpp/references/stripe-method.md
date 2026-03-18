# Stripe Payment Method

## Overview

Stripe integration uses **Shared Payment Tokens (SPT)** - a Stripe Business Network feature that lets one Stripe account (client) create a token that another Stripe account (server) can use to charge. Both parties must have Stripe accounts connected to the Stripe Business Network.

Flow:
1. Server responds with 402 challenge containing Stripe payment requirements.
2. Client creates an SPT via a proxy endpoint (SPT creation requires a secret key).
3. Client sends the SPT as the credential payload.
4. Server creates a PaymentIntent using the SPT and confirms payment.

SPTs are single-use, scoped to a specific amount and currency, and bound to the Business Network profile ID.

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
  networkId: 'acct_1234567890', // Stripe Business Network profile ID
  paymentMethodTypes: ['card'],
})
```

### With Secret Key

```ts
const charge = stripe.charge({
  secretKey: process.env.STRIPE_SECRET_KEY!,
  networkId: 'acct_1234567890',
  paymentMethodTypes: ['card'],
})
```

### With Metadata

Attach metadata to the PaymentIntent for tracking, reconciliation, or plan gating:

```ts
const charge = stripe.charge({
  client: new Stripe(process.env.STRIPE_SECRET_KEY!),
  networkId: 'acct_1234567890',
  paymentMethodTypes: ['card'],
  metadata: { plan: 'pro', feature: 'api-access' },
})
```

### Multiple Payment Methods

Accept cards, Link, and other Stripe-supported methods:

```ts
const charge = stripe.charge({
  secretKey: process.env.STRIPE_SECRET_KEY!,
  networkId: 'acct_1234567890',
  paymentMethodTypes: ['card', 'link'],
})
```

### Server Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `client` | `Stripe` | One of `client` or `secretKey` | Stripe SDK instance |
| `secretKey` | `string` | One of `client` or `secretKey` | Stripe secret key (creates SDK internally) |
| `networkId` | `string` | Yes | Stripe Business Network profile ID |
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

## SPT Creation Proxy

SPT creation requires a Stripe secret key, so it cannot happen client-side. You need a server endpoint that proxies the SPT creation request to Stripe's API.

```ts
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

// POST /api/create-spt
export async function handler(req: Request) {
  const { amount, currency, payment_method, network_id } = await req.json()

  const response = await stripe.rawRequest(
    'POST',
    '/v1/shared_payment/granted_tokens',
    {
      amount: String(amount),
      currency,
      payment_method,
      network_id,
    }
  )

  return Response.json(response)
}
```

The proxy endpoint:
1. Receives SPT creation parameters from the client.
2. Calls Stripe's `shared_payment/granted_tokens` API with the server's secret key.
3. Returns the SPT to the client, which includes it in the credential payload.

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
  "spt": "spt_1abc2def3ghi4jkl5mno6pqr",
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
