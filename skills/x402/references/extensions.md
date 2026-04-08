# x402 Extensions Reference

Extensions add optional functionality beyond core payment mechanics. Servers advertise them in `PaymentRequired.extensions`, clients echo them in `PaymentPayload.extensions`.

Standard extension structure:
```json
{
  "extensions": {
    "extension-name": {
      "info": { /* extension-specific data */ },
      "schema": { /* JSON Schema validating info */ }
    }
  }
}
```

## Bazaar (Resource Discovery)

Enables resource discovery and cataloging. Servers declare endpoint specs so facilitators can catalog them in a discovery service. Supports two transport types: **HTTP** and **MCP**.

### Transport Types

**HTTP** (`input.type: "http"`) - standard REST endpoints. Method is auto-inferred from route key (e.g., `"GET /weather"`) and injected by `bazaarResourceServerExtension`.

**MCP** (`input.type: "mcp"`) - Model Context Protocol tools. Identified by `toolName` field. Transport defaults to `"streamable-http"` per MCP spec, optionally `"sse"`.

### MCP Input Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Always `"mcp"` |
| `toolName` | Yes | MCP tool name |
| `description` | No | Human-readable tool description |
| `transport` | No | `"streamable-http"` (default) or `"sse"` |
| `inputSchema` | Yes | JSON Schema for tool arguments |
| `example` | No | Example tool arguments |

### SDK Usage

**TypeScript:**
```typescript
import { declareDiscoveryExtension } from "@x402/extensions/bazaar";

// HTTP endpoint - method auto-inferred from route key
extensions: {
  ...declareDiscoveryExtension({
    input: { city: "San Francisco" },
    inputSchema: { properties: { city: { type: "string" } }, required: ["city"] },
    output: { example: { weather: "sunny", temperature: 72 } },
  }),
}

// MCP tool - toolName discriminates from HTTP
extensions: {
  ...declareDiscoveryExtension({
    toolName: "financial_analysis",
    description: "Analyze financial data",
    inputSchema: { type: "object", properties: { ticker: { type: "string" } }, required: ["ticker"] },
    output: { example: { pe_ratio: 28.5 } },
  }),
}
```

**Go:**
```go
import "github.com/x402-foundation/x402/go/extensions/bazaar"

Extensions: bazaar.DeclareDiscoveryExtension(bazaar.DiscoveryInfo{
    Output: map[string]interface{}{
        "type": "json",
        "example": map[string]interface{}{"weather": "sunny"},
    },
})
```

**Python:**
```python
from x402.extensions.bazaar import declare_discovery_extension, OutputConfig

extensions = declare_discovery_extension(
    input={"city": "San Francisco"},
    input_schema={"properties": {"city": {"type": "string"}}, "required": ["city"]},
    output=OutputConfig(example={"weather": "sunny"}),
)
```

### Server Extension (Method Enrichment)

`bazaarResourceServerExtension` auto-injects the HTTP method from request context into `info.input.method`.

```typescript
import { bazaarResourceServerExtension } from "@x402/extensions/bazaar";
const resourceServer = new x402ResourceServer(facilitatorClient)
  .registerExtension(bazaarResourceServerExtension);
```

Go: `bazaar.BazaarResourceServerExtension` | Python: `bazaar_resource_server_extension`

### WithBazaar Facilitator Client

```typescript
import { withBazaar } from "@x402/extensions/bazaar";
const client = withBazaar(new HTTPFacilitatorClient({ url }));
const resources = await client.extensions.discovery.listResources({ type: "http", limit: 10 });
```

Go: `bazaar.WithBazaar(facilitatorClient)` then `facilitator.ListDiscoveryResources(ctx, params)`

### Discovery API

```
GET /discovery/resources?type=http&limit=10&offset=0
```

---

## Offer-Receipt (Signed Attestations)

Enables cryptographically signed offers and receipts for audit trails, verified reviews, and dispute resolution. TypeScript only.

### Signature Formats

| Format | Use Case |
|--------|----------|
| `jws` | Cross-chain, supports did:key/did:jwk/did:web |
| `eip712` | EVM-native, ECDSA recovery |

### Server Setup

```typescript
import {
  createOfferReceiptExtension,
  createJWSOfferReceiptIssuer,
  declareOfferReceiptExtension,
} from "@x402/extensions/offer-receipt";

const issuer = createJWSOfferReceiptIssuer(
  "did:web:api.example.com#key-1",
  { kid: "did:web:api.example.com#key-1", algorithm: "ES256", format: "jws", sign: mySignFn },
);

const resourceServer = new x402ResourceServer(facilitatorClient)
  .registerExtension(createOfferReceiptExtension(issuer));

extensions: {
  ...declareOfferReceiptExtension({ includeTxHash: false, offerValiditySeconds: 300 }),
}
```

### Client Usage

```typescript
import {
  extractOffersFromPaymentRequired,
  decodeSignedOffers,
  findAcceptsObjectFromSignedOffer,
  extractReceiptFromResponse,
  verifyReceiptMatchesOffer,
} from "@x402/extensions/offer-receipt";

const offers = extractOffersFromPaymentRequired(paymentRequired);
const decoded = decodeSignedOffers(offers);
const requirements = findAcceptsObjectFromSignedOffer(decoded[0], paymentRequired.accepts);
const receipt = extractReceiptFromResponse(response);
const valid = verifyReceiptMatchesOffer(receipt, decoded[0], [myWalletAddress]);
```

### DID Key Resolution

`extractPublicKeyFromKid(kid)` supports `did:key` (Ed25519, secp256k1, P-256), `did:jwk`, and `did:web` (fetches `/.well-known/did.json`).

---

## Payment Identifier (Idempotency)

Enables clients to provide an `id` for request deduplication and safe retries.

### SDK Usage

**TypeScript (server):**
```typescript
import { declarePaymentIdentifierExtension, paymentIdentifierResourceServerExtension } from "@x402/extensions/payment-identifier";

extensions: { [PAYMENT_IDENTIFIER]: declarePaymentIdentifierExtension(false) }
resourceServer.registerExtension(paymentIdentifierResourceServerExtension);
```

**TypeScript (client):**
```typescript
import { appendPaymentIdentifierToExtensions } from "@x402/extensions/payment-identifier";
appendPaymentIdentifierToExtensions(extensions); // Adds ID only if server declared extension
```

**Go (client):**
```go
import "github.com/x402-foundation/x402/go/extensions/paymentidentifier"
err := paymentidentifier.AppendPaymentIdentifierToExtensions(extensions, "")
```

**Go (facilitator):**
```go
id, err := paymentidentifier.ExtractPaymentIdentifier(payload, true) // validate=true
```

### ID Format

- **Length**: 16-128 characters
- **Characters**: alphanumeric, hyphens, underscores (`^[a-zA-Z0-9_-]+$`)

### Idempotency Behavior

| Scenario | Server Response |
|----------|-----------------|
| New `id` | Process normally |
| Same `id`, same payload | Return cached response |
| Same `id`, different payload | 409 Conflict |
| `required: true`, no `id` | 400 Bad Request |

---

## Sign-In With X (Wallet Authentication)

CAIP-122 wallet-based authentication. Clients prove wallet ownership by signing a challenge, allowing servers to skip payment for addresses that previously paid. TypeScript only.

### Supported Chains

| Chain | Type | Message Format |
|-------|------|---------------|
| EVM (`eip155:*`) | `eip191` | EIP-4361 (SIWE) |
| Solana (`solana:*`) | `ed25519` | Sign-In With Solana (SIWS) |

### Server

```typescript
import { declareSIWxExtension, siwxResourceServerExtension } from "@x402/extensions/sign-in-with-x";

extensions: { ...declareSIWxExtension({ domain: "example.com", statement: "Sign in" }) }
server.registerExtension(siwxResourceServerExtension);
```

Client sends `SIGN-IN-WITH-X` HTTP header (Base64-encoded JSON with signature).

---

## Gas Sponsoring Extensions (EVM)

Two extensions enable gasless Permit2 approval flows.

### eip2612GasSponsoring

For tokens implementing **EIP-2612**. Client signs off-chain permit; facilitator calls `settleWithPermit()`.

```typescript
import { declareEip2612GasSponsoringExtension } from "@x402/extensions";
extensions: { ...declareEip2612GasSponsoringExtension() }
```

Go: `eip2612gassponsor.DeclareEip2612GasSponsoringExtension()`

### erc20ApprovalGasSponsoring

For tokens **without** EIP-2612. Client signs a raw `approve()` transaction; facilitator broadcasts atomically before settling.

```typescript
import { declareErc20ApprovalGasSponsoringExtension } from "@x402/extensions";
extensions: { ...declareErc20ApprovalGasSponsoringExtension() }
```

Go: `erc20approvalgassponsor.DeclareExtension()`

### Gas Sponsoring Comparison

| Feature | eip2612GasSponsoring | erc20ApprovalGasSponsoring |
|---------|---------------------|---------------------------|
| Token requirement | Must implement EIP-2612 | Any ERC-20 |
| Client signs | Off-chain EIP-2612 permit | Full EVM transaction |
| Gas funding needed | No (off-chain signature) | Yes (if client lacks gas) |
| Settlement method | `settleWithPermit` | Atomic batch (fund + approve + settle) |

---

## SDK Support Matrix

| Extension | TypeScript | Go | Python |
|-----------|------------|-----|--------|
| bazaar | Yes | Yes | Yes |
| offer-receipt | Yes | No | No |
| sign-in-with-x | Yes | No | No |
| payment-identifier | Yes | Yes | Yes |
| eip2612GasSponsoring | Yes | Yes | Yes |
| erc20ApprovalGasSponsoring | Yes | Yes | Yes |
