# Lifecycle Hooks Reference

All three x402 roles (client, server, facilitator) support lifecycle hooks for logging, spending limits, access control, and custom behavior. All SDKs support method chaining.

## Server Hooks

### x402ResourceServer (Transport-agnostic)

* **onBeforeVerify** - Runs before payment verification. Return `{ abort: true, reason }` to reject.
* **onAfterVerify** - Runs after successful verification.
* **onVerifyFailure** - Runs on verification failure. Return `{ recovered: true, result }` to override.
* **onBeforeSettle** - Runs before settlement. Return `{ abort: true, reason }` to reject.
* **onAfterSettle** - Runs after successful settlement.
* **onSettleFailure** - Runs on settlement failure. Return `{ recovered: true, result }` to override.

**TypeScript:**
```typescript
import { x402ResourceServer } from "@x402/core";

const server = new x402ResourceServer(facilitatorClient);

server.onAfterSettle(async (context) => {
  await recordPayment({
    payer: context.result.payer,
    transaction: context.result.transaction,
    amount: context.requirements.amount,
    network: context.requirements.network,
  });
});
```

**Python (async):**
```python
from x402 import x402ResourceServer

server = x402ResourceServer(facilitator_client)

async def record_payment(context):
    await db.record_payment(
        payer=context.result.payer,
        transaction=context.result.transaction,
    )

server.on_after_settle(record_payment)
```

**Python (sync):** Use `x402ResourceServerSync` with sync callables.

**Go:**
```go
server := x402.Newx402ResourceServer(facilitatorClient)

server.OnAfterSettle(func(ctx x402.SettleResultContext) error {
    return db.RecordPayment(Payment{
        Payer:       ctx.Result.Payer,
        Transaction: ctx.Result.Transaction,
    })
})
```

### x402HTTPResourceServer (HTTP-specific)

* **onProtectedRequest** - Runs on every request to a protected route.
  * Return `{ grantAccess: true }` to bypass payment (e.g., API key auth).
  * Return `{ abort: true, reason }` to return 403.
  * Return `void`/`nil` to continue to payment flow.

**TypeScript:**
```typescript
const httpServer = new x402HTTPResourceServer(server, routes);

httpServer.onProtectedRequest(async (context, routeConfig) => {
  const apiKey = context.adapter.getHeader("X-API-Key");
  if (apiKey && await isValidApiKey(apiKey)) {
    return { grantAccess: true };
  }
});
```

**Go:**
```go
httpServer.OnProtectedRequest(func(ctx context.Context, reqCtx x402http.HTTPRequestContext, route x402http.RouteConfig) (*x402http.ProtectedRequestHookResult, error) {
    apiKey := reqCtx.Adapter.GetHeader("X-API-Key")
    if apiKey != "" && isValidAPIKey(apiKey) {
        return &x402http.ProtectedRequestHookResult{GrantAccess: true}, nil
    }
    return nil, nil
})
```

## Client Hooks

### x402Client (Transport-agnostic)

* **onBeforePaymentCreation** - Runs before creating a payment payload. Return `{ abort: true, reason }` to cancel.
* **onAfterPaymentCreation** - Runs after successful payload creation.
* **onPaymentCreationFailure** - Runs on failure. Return `{ recovered: true, payload }` to provide fallback.

**TypeScript:**
```typescript
client.onBeforePaymentCreation(async (context) => {
  const maxAmount = BigInt("10000000"); // 10 USDC
  const requestedAmount = BigInt(context.selectedRequirements.amount);
  if (requestedAmount > maxAmount) {
    return { abort: true, reason: "Payment exceeds spending limit" };
  }
});
```

**Go:**
```go
client.OnBeforePaymentCreation(func(ctx context.Context, pc x402.PaymentCreationContext) (*x402.AbortResult, error) {
    maxAmount := big.NewInt(10_000_000)
    requestedAmount := new(big.Int)
    requestedAmount.SetString(pc.Requirements.Amount, 10)
    if requestedAmount.Cmp(maxAmount) > 0 {
        return &x402.AbortResult{Reason: "Payment exceeds spending limit"}, nil
    }
    return nil, nil
})
```

### x402HTTPClient (HTTP-specific)

* **onPaymentRequired** - Runs when a 402 response is received.
  * Return `{ headers }` to retry with alternate headers before paying (e.g., API key fallback).
  * Return `void` to proceed directly to payment.

```typescript
httpClient.onPaymentRequired(async ({ paymentRequired }) => {
  const apiKey = process.env.API_KEY;
  if (apiKey) {
    return { headers: { "Authorization": `Bearer ${apiKey}` } };
  }
});
```

## Facilitator Hooks

Same verify/settle pattern as server hooks.

**TypeScript:**
```typescript
facilitator.onAfterVerify(async (context) => {
  const discovered = extractDiscoveryInfo(context.paymentPayload, context.requirements, true);
  if (discovered) {
    bazaarCatalog.add({ resource: discovered.resourceUrl, accepts: [context.requirements] });
  }
});
```

**Go:**
```go
facilitator.OnAfterVerify(func(ctx x402.FacilitatorVerifyResultContext) error {
    // Bazaar catalog population, compliance checks, metrics
    return nil
})
```

## Hook Chaining

All SDKs support method chaining:

```typescript
server
  .onBeforeVerify(validatePayment)
  .onAfterVerify(logVerification)
  .onBeforeSettle(checkBalance)
  .onAfterSettle(recordTransaction);
```

```go
server.OnBeforeVerify(validate).OnAfterVerify(log).OnBeforeSettle(check).OnAfterSettle(record)
```

## Extension Hooks

### Server Extensions (ResourceServerExtension)

```typescript
server.registerExtension({
  key: "my-extension",
  enrichDeclaration: async (declaration, transportContext) => enrichedDeclaration,
  enrichPaymentRequiredResponse: async (declaration, context) => ({ info: {}, schema: {} }),
  enrichSettlementResponse: async (declaration, context) => ({ info: {}, schema: {} }),
});
```

### Client Extensions (ClientExtension)

```typescript
client.registerExtension({
  key: "eip2612GasSponsoring",
  enrichPaymentPayload: async (paymentPayload, paymentRequired) => enrichedPayload,
});
```

Go: `client.RegisterExtension(myExtension)` - implements `ClientExtension` interface with `Key()` and `EnrichPaymentPayload()`.

## MCP Hooks

```typescript
const paidTool = createPaymentWrapper(resourceServer, requirements, {
  onBeforeExecution: async (toolName, args, paymentPayload) => {},
  onAfterExecution: async (toolName, result, paymentPayload) => {},
  onAfterSettlement: async (toolName, settlementResponse) => {},
});
```

## Python Naming Convention

| TypeScript | Python |
|------------|--------|
| `onBeforeVerify` | `on_before_verify` |
| `onAfterSettle` | `on_after_settle` |
| `onBeforePaymentCreation` | `on_before_payment_creation` |
| `onProtectedRequest` | `on_protected_request` |

Sync variants: `x402ResourceServerSync`, `x402ClientSync`, `x402FacilitatorSync`

## Hook Support Matrix

| Hook | TypeScript | Go | Python |
|------|------------|-----|--------|
| Client: onBeforePaymentCreation | Yes | Yes | Yes |
| Client: onAfterPaymentCreation | Yes | Yes | Yes |
| Client: onPaymentCreationFailure | Yes | Yes | Yes |
| Client: onPaymentRequired (HTTP) | Yes | No | No |
| Client: registerExtension | Yes | Yes | No |
| Server: onBeforeVerify | Yes | Yes | Yes |
| Server: onAfterVerify | Yes | Yes | Yes |
| Server: onVerifyFailure | Yes | Yes | Yes |
| Server: onBeforeSettle | Yes | Yes | Yes |
| Server: onAfterSettle | Yes | Yes | Yes |
| Server: onSettleFailure | Yes | Yes | Yes |
| Server: onProtectedRequest (HTTP) | Yes | Yes | No |
| Facilitator: all verify/settle hooks | Yes | Yes | Yes |
| Extension: enrichDeclaration | Yes | Yes | Yes |
| Extension: enrichPaymentRequiredResponse | Yes | No | No |
| Extension: enrichSettlementResponse | Yes | No | No |
