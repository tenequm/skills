# Subscription Intent (Tempo)

Recurring access on Tempo via an **authorized access key** rather than a payment per request. Activation collects the first period and authorizes a key; later requests reuse that key with no per-request payment; the server renews in the background; access is cancelled or revoked server-side.

Subscriptions are Tempo-only. The intent is `subscription`, alongside `charge` and `session`.

## Server Setup

```ts
import { Mppx, Store, tempo } from 'mppx/server'

const mppx = Mppx.create({
  methods: [
    tempo.subscription({
      currency: '<USDC_TEMPO_MAINNET>',
      recipient: '0xYourAddress',
      periodCount: '1',
      periodUnit: 'month',
      store: Store.redis(redisClient), // durable store required
    }),
  ],
  secretKey: process.env.MPP_SECRET_KEY,
})
```

A **durable store is mandatory**. Subscription state (the authorized key, period boundaries, cancellation and revocation timestamps) must survive restarts, or renewals and access checks break.

### Period Units

There is a divergence between the SDK and the docs worth knowing before you pick a value:

- The mppx type is `SubscriptionPeriodUnit = 'dev_second' | 'day' | 'week'`.
- The published request schema documents `periodUnit` as `day`, `week`, or `month`.

`dev_second` exists in the SDK for fast test cycles (a "period" of one second) but is undocumented; `month` is documented but absent from the SDK's union. Verify against the version you have pinned before relying on either edge, and prefer `day` or `week` for code that must work on both.

`periodCount` is a positive integer count of `periodUnit` values per billing period.

## Request Handling

```ts
const result = await mppx.subscription({ /* per-route overrides */ })(request)
if (result.status === 402) return result.challenge
return result.withReceipt(Response.json({ data: '...' }))
```

Two options shape how strictly access is gated:

- `requireCredential` - whether an active subscription still has to present a credential on each request, or whether server-side resolution alone suffices.
- `resolve` - a hook to map an incoming request to a subscription identity when it is not carried in the credential.

`Subscription.fromStore` reads current subscription state directly from the store, for endpoints that need to check entitlement without running the payment handler.

## Renewal

Renewal happens outside the request path. `tempo.renewSubscription` drives an overdue subscription forward from a background worker:

```ts
import { tempo } from 'mppx/server'

// in a cron job or queue consumer
await tempo.renewSubscription({ store, client, subscriptionId })
```

**Concurrency contract:** if one request is already renewing a subscription, another receives `409` with `Retry-After: 1`. Treat that as "retry shortly", not as a failure - it exists so two workers cannot double-charge a period.

## Cancellation and Revocation

Subscription records carry `canceledAt` and `revokedAt`. Cancelling stops future renewals while leaving the current period intact; revoking withdraws the authorized key immediately. Key revocation goes through the Accounts action `Actions.accessKey.revokeSync`, since the authorization lives on the payer's wallet rather than in your store.

## Relationship to Access Keys

A subscription is an access key with a spend policy attached, so the agent-spend controls documented in `SKILL.md` apply: token limits, contract/function/recipient scopes, and expiry. The subscription flow authorizes the key on activation and relies on those scopes to bound what the key can do between renewals.
