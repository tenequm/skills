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
        amount=context.requirements.amount,
        network=context.requirements.network,
    )

server.on_after_settle(record_payment)
```

**Python (sync) - use `x402ResourceServerSync`:**
```python
from x402 import x402ResourceServerSync

server = x402ResourceServerSync(facilitator_client)

def record_payment(context):
    db.record_payment(
        payer=context.result.payer,
        transaction=context.result.transaction,
    )

server.on_after_settle(record_payment)
```

**Go:**
```go
import x402 "github.com/coinbase/x402/go"

server := x402.Newx402ResourceServer(facilitatorClient)

server.OnAfterSettle(func(ctx x402.SettleResultContext) error {
    return db.RecordPayment(Payment{
        Payer:       ctx.Result.Payer,
        Transaction: ctx.Result.Transaction,
        Amount:      ctx.Requirements.Amount,
        Network:     ctx.Requirements.Network,
    })
})
```

### x402HTTPResourceServer (HTTP-specific)

* **onProtectedRequest** - Runs on every request to a protected route.
  * Return `{ grantAccess: true }` to bypass payment (e.g., API key auth).
  * Return `{ abort: true, reason }` to return 403.
  * Return `void` to continue to payment flow.

```typescript
import { x402ResourceServer, x402HTTPResourceServer } from "@x402/core";

const server = new x402ResourceServer(facilitatorClient);
const httpServer = new x402HTTPResourceServer(server, routes);

httpServer.onProtectedRequest(async (context, routeConfig) => {
  const apiKey = context.adapter.getHeader("X-API-Key");

  if (apiKey && await isValidApiKey(apiKey)) {
    return { grantAccess: true };
  }

  // No valid API key - continue to payment flow
});
```

## Client Hooks

### x402Client (Transport-agnostic)

* **onBeforePaymentCreation** - Runs before creating a payment payload. Return `{ abort: true, reason }` to cancel.
* **onAfterPaymentCreation** - Runs after successful payload creation.
* **onPaymentCreationFailure** - Runs on failure. Return `{ recovered: true, payload }` to provide fallback.

**TypeScript:**
```typescript
import { x402Client } from "@x402/core";

const client = new x402Client();

client.onBeforePaymentCreation(async (context) => {
  const maxAmount = BigInt("10000000"); // 10 USDC
  const requestedAmount = BigInt(context.selectedRequirements.amount);

  if (requestedAmount > maxAmount) {
    return { abort: true, reason: "Payment exceeds spending limit" };
  }
});
```

**Python (async):**
```python
from x402 import x402Client
from x402.types import AbortResult

client = x402Client()

async def enforce_spending_limit(context):
    max_amount = 10_000_000  # 10 USDC
    requested_amount = int(context.selected_requirements.amount)

    if requested_amount > max_amount:
        return AbortResult(abort=True, reason="Payment exceeds spending limit")

client.on_before_payment_creation(enforce_spending_limit)
```

**Python (sync) - use `x402ClientSync`:**
```python
from x402 import x402ClientSync
from x402.types import AbortResult

client = x402ClientSync()

def enforce_spending_limit(context):
    max_amount = 10_000_000  # 10 USDC
    requested_amount = int(context.selected_requirements.amount)

    if requested_amount > max_amount:
        return AbortResult(abort=True, reason="Payment exceeds spending limit")

client.on_before_payment_creation(enforce_spending_limit)
```

**Go:**
```go
import x402 "github.com/coinbase/x402/go"

client := x402.Newx402Client()

client.OnBeforePaymentCreation(func(ctx x402.PaymentCreationContext) (*x402.BeforePaymentCreationResult, error) {
    maxAmount := big.NewInt(10_000_000) // 10 USDC
    requestedAmount := new(big.Int)
    requestedAmount.SetString(ctx.Requirements.Amount, 10)

    if requestedAmount.Cmp(maxAmount) > 0 {
        return &x402.BeforePaymentCreationResult{
            Abort:  true,
            Reason: "Payment exceeds spending limit",
        }, nil
    }
    return nil, nil
})
```

### x402HTTPClient (HTTP-specific)

* **onPaymentRequired** - Runs when a 402 response is received.
  * Return `{ headers }` to retry with alternate headers before paying (e.g., API key fallback).
  * Return `void` to proceed directly to payment.

```typescript
import { x402Client, x402HTTPClient } from "@x402/core";

const client = new x402Client();
const httpClient = new x402HTTPClient(client);

httpClient.onPaymentRequired(async ({ paymentRequired }) => {
  // Try API key authentication first
  const apiKey = process.env.API_KEY;
  if (apiKey) {
    return { headers: { "Authorization": `Bearer ${apiKey}` } };
  }
  // Return void to proceed with payment
});
```

## Facilitator Hooks

Same verify/settle pattern as server hooks. Use cases include bazaar catalog population, compliance checks, and metrics.

**TypeScript (bazaar catalog example):**
```typescript
import { x402Facilitator } from "@x402/core";
import { extractDiscoveryInfo } from "@x402/extensions/bazaar";

const facilitator = new x402Facilitator();

facilitator.onAfterVerify(async (context) => {
  const discovered = extractDiscoveryInfo(
    context.paymentPayload,
    context.requirements,
    true, // validate
  );

  if (discovered) {
    bazaarCatalog.add({
      resource: discovered.resourceUrl,
      description: discovered.description,
      mimeType: discovered.mimeType,
      x402Version: discovered.x402Version,
      accepts: [context.requirements],
      lastUpdated: new Date().toISOString(),
    });
  }
});
```

**Python (async):**
```python
from x402 import x402Facilitator

facilitator = x402Facilitator()

async def update_bazaar_catalog(context):
    discovered = extract_discovery_info(
        context.payment_payload,
        context.requirements,
        validate=True,
    )

    if discovered:
        await bazaar_catalog.add(
            resource=discovered.resource_url,
            description=discovered.description,
            mime_type=discovered.mime_type,
            accepts=[context.requirements],
        )

facilitator.on_after_verify(update_bazaar_catalog)
```

**Python (sync) - use `x402FacilitatorSync`:**
```python
from x402 import x402FacilitatorSync

facilitator = x402FacilitatorSync()

def log_verification(context):
    print(f"Verified payment from {context.result.payer}")

facilitator.on_after_verify(log_verification)
```

**Go:**
```go
import x402 "github.com/coinbase/x402/go"

facilitator := x402.Newx402Facilitator()

facilitator.OnAfterVerify(func(ctx x402.FacilitatorVerifyResultContext) error {
    discovered := extractDiscoveryInfo(ctx.PaymentPayload, ctx.Requirements)

    if discovered != nil {
        return bazaarCatalog.Add(BazaarEntry{
            Resource:    discovered.ResourceURL,
            Description: discovered.Description,
            MimeType:    discovered.MimeType,
            Accepts:     []PaymentRequirements{ctx.Requirements},
        })
    }
    return nil
})
```

## Hook Chaining

All SDKs support method chaining:

**TypeScript:**
```typescript
server
  .onBeforeVerify(validatePayment)
  .onAfterVerify(logVerification)
  .onBeforeSettle(checkBalance)
  .onAfterSettle(recordTransaction);
```

**Python:**
```python
(
    server
    .on_before_verify(validate_payment)
    .on_after_verify(log_verification)
    .on_before_settle(check_balance)
    .on_after_settle(record_transaction)
)
```

**Go:**
```go
server.
    OnBeforeVerify(validatePayment).
    OnAfterVerify(logVerification).
    OnBeforeSettle(checkBalance).
    OnAfterSettle(recordTransaction)
```

## Extension Hooks

Extensions hook into declaration and response enrichment:

```typescript
server.registerExtension({
  name: "my-extension",
  enrichDeclaration: async (requirements) => {
    return { info: { /* ... */ }, schema: { /* ... */ } };
  },
  enrichPaymentRequiredResponse: async (response) => {
    // Modify the 402 response
  },
  enrichSettlementResponse: async (response) => {
    // Add data to settlement response
  },
});
```

## MCP Hooks

MCP payment wrappers support execution and settlement hooks:

```typescript
const paidTool = createPaymentWrapper(resourceServer, requirements, {
  onBeforeExecution: async (toolName, args, paymentPayload) => {
    console.log(`Executing ${toolName} with payment`);
  },
  onAfterExecution: async (toolName, result, paymentPayload) => {
    console.log(`${toolName} completed`);
  },
  onAfterSettlement: async (toolName, settlementResponse) => {
    console.log(`${toolName} settled: ${settlementResponse.transaction}`);
  },
});
```

## Python Naming Convention

Python hooks use snake_case throughout:

| TypeScript | Python |
|------------|--------|
| `onBeforeVerify` | `on_before_verify` |
| `onAfterSettle` | `on_after_settle` |
| `onBeforePaymentCreation` | `on_before_payment_creation` |
| `onPaymentCreationFailure` | `on_payment_creation_failure` |
| `onProtectedRequest` | `on_protected_request` |

Sync variants: `x402ResourceServerSync`, `x402ClientSync`, `x402FacilitatorSync`

## Go Context Types

| Hook | Context Type | Return Type |
|------|-------------|-------------|
| `OnBeforePaymentCreation` | `x402.PaymentCreationContext` | `*x402.BeforePaymentCreationResult` |
| `OnAfterSettle` | `x402.SettleResultContext` | `error` |
| `OnAfterVerify` (facilitator) | `x402.FacilitatorVerifyResultContext` | `error` |
| `OnBeforeVerify` (server) | `context.Context` + payload + requirements | `error` (return error to abort) |

## Hook Support Matrix

| Hook | TypeScript | Go | Python |
|------|------------|-----|--------|
| Client: onBeforePaymentCreation | Yes | Yes | Yes |
| Client: onAfterPaymentCreation | Yes | Yes | Yes |
| Client: onPaymentCreationFailure | Yes | Yes | Yes |
| Client: onPaymentRequired (HTTP) | Yes | No | No |
| Server: onBeforeVerify | Yes | Yes | Yes |
| Server: onAfterVerify | Yes | Yes | Yes |
| Server: onVerifyFailure | Yes | Yes | Yes |
| Server: onBeforeSettle | Yes | Yes | Yes |
| Server: onAfterSettle | Yes | Yes | Yes |
| Server: onSettleFailure | Yes | Yes | Yes |
| Server: onProtectedRequest (HTTP) | Yes | No | No |
| Facilitator: all verify/settle hooks | Yes | Yes | Yes |
| Extension: enrichDeclaration | Yes | Yes | Yes |
| Extension: enrichPaymentRequiredResponse | Yes | No | No |
| Extension: enrichSettlementResponse | Yes | No | No |
