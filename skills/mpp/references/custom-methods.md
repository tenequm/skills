# Custom Payment Methods

## Overview

MPP supports dynamic extensibility through custom payment methods. Any payment rail - other blockchains, card processors, proprietary billing systems, loyalty points - can be integrated by implementing three pieces:

1. **Method definition** - schema describing the credential and request shapes
2. **Client implementation** - how to create a credential (proof of payment)
3. **Server implementation** - how to verify a credential

Custom methods plug into the same `Mppx.create()` pipeline and work across all transports (HTTP, MCP, JSON-RPC) and frameworks (Hono, Express, Next.js, etc.) without changes.

---

## Define a Method

Use `Method.from()` to define a new payment method with its name, intent, and Zod schemas:

```ts
import { Method } from 'mppx'
import { z } from 'zod'

const lightningCharge = Method.from({
  intent: 'charge',
  name: 'lightning',
  schema: {
    credential: {
      payload: z.object({
        preimage: z.string().length(64), // 32-byte hex
      }),
    },
    request: z.object({
      invoice: z.string(), // BOLT11 invoice
      paymentHash: z.string().length(64),
      network: z.enum(['mainnet', 'regtest']).default('mainnet'),
    }),
  },
})
```

`Method.from()` returns a base method definition. It has no behavior - just the type contract that both client and server implementations must satisfy.

**Parameters:**

| Field | Type | Description |
|---|---|---|
| `intent` | `string` | Payment intent (e.g. `'charge'`, `'session'`) |
| `name` | `string` | Method identifier (e.g. `'lightning'`, `'loyalty-points'`) |
| `schema.credential.payload` | `ZodType` | Zod schema for the credential payload |
| `schema.request` | `ZodType` | Zod schema for the challenge request fields |

---

## Client Implementation

Use `Method.toClient()` to add credential creation logic to a base method:

```ts
const lightningClient = Method.toClient(lightningCharge, {
  async createCredential({ challenge, context }) {
    const request = challenge.request // decoded request object
    const invoice = request.invoice

    // Pay the invoice and get the preimage
    const preimage = await payInvoice(invoice)

    return {
      payload: { preimage },
    }
  },
})
```

`createCredential` receives:
- `challenge` - the parsed challenge from the server's 402 response
- `context` - optional context passed from the application (e.g. wallet instance, user preferences)

It must return a serialized credential matching the `schema.credential.payload` Zod schema.

---

## Server Implementation

Use `Method.toServer()` to add verification logic to a base method:

```ts
import { createHash } from 'node:crypto'

const lightningServer = Method.toServer(lightningCharge, {
  async verify({ credential, challenge }) {
    const { preimage } = credential.payload
    const { paymentHash } = challenge.request

    // Verify: sha256(preimage) == paymentHash
    const hash = createHash('sha256')
      .update(Buffer.from(preimage, 'hex'))
      .digest('hex')

    if (hash !== paymentHash) {
      throw new Error('Invalid preimage: hash mismatch')
    }

    return {
      reference: paymentHash,
      settlement: {
        amount: challenge.request.amount,
        currency: 'BTC',
      },
    }
  },
})
```

`verify` receives:
- `credential` - the parsed credential from the client
- `challenge` - the original challenge

It must return a receipt object with `reference` and `settlement`, or throw an error if verification fails.

---

## Full Lightning Example

Complete custom method implementation - from definition through usage:

### Method Definition

```ts
import { Method } from 'mppx'
import { z } from 'zod'

const lightning = Method.from({
  intent: 'charge',
  name: 'lightning',
  schema: {
    credential: {
      payload: z.object({
        preimage: z.string().length(64),
      }),
    },
    request: z.object({
      invoice: z.string(),
      paymentHash: z.string().length(64),
      amount: z.number(),
      network: z.enum(['mainnet', 'regtest']).default('mainnet'),
    }),
  },
})
```

### Client

```ts
const lightningClient = Method.toClient(lightning, {
  async createCredential({ challenge }) {
    const { invoice } = challenge.request

    // Use any Lightning wallet SDK to pay the invoice
    const preimage = await payInvoice(invoice)

    return {
      payload: { preimage },
    }
  },
})
```

### Server

```ts
import { createHash } from 'node:crypto'

const lightningServer = Method.toServer(lightning, {
  async verify({ credential, challenge }) {
    const { preimage } = credential.payload
    const { paymentHash } = challenge.request

    const hash = createHash('sha256')
      .update(Buffer.from(preimage, 'hex'))
      .digest('hex')

    if (hash !== paymentHash) {
      throw new Error('Preimage verification failed')
    }

    return {
      reference: paymentHash,
      settlement: {
        amount: String(challenge.request.amount),
        currency: 'BTC',
      },
    }
  },
})
```

### Usage

```ts
import { Mppx } from 'mppx/server'

// Server
const mppx = Mppx.create({
  methods: [lightningServer],
})

export async function handler(req: Request) {
  const result = await mppx.charge({ amount: '1000' })(req)
  if (result.status === 402) return result.challenge
  return result.withReceipt(Response.json({ data: 'paid' }))
}
```

```ts
import { Mppx } from 'mppx/client'

// Client
Mppx.create({
  methods: [lightningClient],
})

const res = await fetch('https://api.example.com/data')
```

---

## Method Architecture

The method system uses a layered architecture:

### Base Method (`Method.from`)

The base method defines the type contract:

| Property | Type | Description |
|---|---|---|
| `method` | `string` | Full method identifier (derived from name + intent) |
| `name` | `string` | Method name (e.g. `'lightning'`) |
| `schema` | `object` | Zod schemas for credential payload and request |

### Client Method (`Method.toClient`)

Extends the base method with client-side behavior:

| Property | Type | Description |
|---|---|---|
| `createCredential` | `function` | Creates a credential from a challenge. Receives `{ challenge, context }`, returns serialized credential |

### Server Method (`Method.toServer`)

Extends the base method with server-side behavior:

| Property | Type | Description |
|---|---|---|
| `verify` | `function` | Verifies a credential and returns a receipt. Receives `{ credential, challenge }` |
| `defaults` | `object` | Optional default values for challenge request fields |
| `transformRequest` | `function` | Optional transform applied to the request before challenge generation |
| `onRespond` | `function` | Optional hook called after verification, before response is sent |
| `transport` | `object` | Optional transport override for custom encoding |

### Defaults Example

```ts
const server = Method.toServer(method, {
  verify: async ({ credential }) => { /* ... */ },
  defaults: {
    currency: 'BTC',
    network: 'mainnet',
  },
})
```

### Transform Request Example

```ts
const server = Method.toServer(method, {
  verify: async ({ credential }) => { /* ... */ },
  transformRequest: (request, { amount }) => ({
    ...request,
    invoice: generateInvoice(amount),
    paymentHash: getPaymentHash(invoice),
  }),
})
```

---

## SDK References

### `Method.from(options)`

Creates a base method definition.

```ts
Method.from({
  intent: string,
  name: string,
  schema: {
    credential: { payload: ZodType },
    request: ZodType,
  },
})
```

### `Method.toClient(method, implementation)`

Adds client behavior to a base method.

```ts
Method.toClient(method, {
  createCredential: async ({ challenge, context }) => ({
    payload: { /* ... */ },
  }),
})
```

### `Method.toServer(method, implementation)`

Adds server behavior to a base method.

```ts
Method.toServer(method, {
  verify: async ({ credential, challenge }) => ({
    reference: string,
    settlement: { amount: string, currency: string },
  }),
  defaults?: object,
  transformRequest?: (request, chargeOptions) => transformedRequest,
  onRespond?: (receipt, response) => void,
  transport?: TransportOverride,
})
```
