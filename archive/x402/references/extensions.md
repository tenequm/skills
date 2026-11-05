# x402 Extensions Reference

Extensions add optional functionality beyond core payment mechanics. Servers advertise them in `PaymentRequired.extensions`, clients echo them in `PaymentPayload.extensions`. Client-echoed extension info is validated field-by-field against the server declaration; a mismatch is rejected with `extension_echo_mismatch`.

**Dynamic info fields (2.16.0):** an extension can mark certain info fields as regenerated per `PaymentRequired` response (via a `dynamicInfoFields` capability) so they are excluded from the strict client-echo comparison, while all other fields stay strictly compared. Wired into offer-receipt (`["offers"]`) and sign-in-with-x (`["nonce", "issuedAt", "expirationTime"]`).

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
import "github.com/x402-foundation/x402/go/v2/extensions/bazaar"

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

### Troubleshooting: Why a Service Is Not in the Catalog

Whether and how a resource appears in a facilitator's catalog is an implementation detail of the **facilitator operator**, not something a server controls. Two consequences catch people out:

- **A server-side declaration alone catalogs nothing.** Cataloging happens when a facilitator processes a `PaymentPayload` that includes the echoed `bazaar` extension - so a route nobody has paid for yet will not appear, no matter how it is declared.
- **A missing `EXTENSION-RESPONSES` header is not a failure signal.** Facilitators *may* return it; its absence carries no meaning.

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

### Signer Authorization (not just signature validity)

Verifiers MUST distinguish between **signature validity** and **signer authorization**. A valid signature proves a specific key signed the artifact; it does not prove that key was authorized to sign on behalf of the service identified by `resourceUrl`. Two authorization mechanisms are specified:

- `did:web` resolution against the service domain
- DNS TXT records at `_controllers.<domain>` carrying `v=1;controller=did:pkh:...`

Checking only the signature leaves a receipt forgeable by anyone who can produce a well-formed signature over the offer.

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
import "github.com/x402-foundation/x402/go/v2/extensions/paymentidentifier"
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

CAIP-122 wallet-based authentication. Clients prove wallet ownership by signing a challenge, allowing servers to skip payment for addresses that previously paid. TypeScript, Python (`x402.extensions.sign_in_with_x`, added Python v2.11.0), and Go (server + client, `go/v2/extensions/signinwithx`, added Go v2.16.0 - also covers undeployed EIP-6492 and SVM signers).

### Supported Chains

| Chain | Type | Message Format |
|-------|------|---------------|
| EVM (`eip155:*`) | `eip191` | EIP-4361 (SIWE) |
| Solana (`solana:*`) | `ed25519` | Sign-In With Solana (SIWS) |

### Server

```typescript
import { createSIWxResourceServerExtension, declareSIWxExtension } from "@x402/extensions/sign-in-with-x";

// Declare on the route - no `domain`, no `resourceUri`
extensions: { ...declareSIWxExtension({ statement: "Sign in", expirationSeconds: 300 }) }

// Register with an operator-configured public origin (required)
server.registerExtension(
  createSIWxResourceServerExtension({ origin: "https://api.example.com" }),
);
```

`DeclareSIWxOptions` now carries only `statement`, `version`, `network`, and `expirationSeconds`.

> **Security: origin binding.** `origin` is required and must be the external, browser-visible origin - not the upstream listener address behind a reverse proxy. The server validates `domain` and the `uri` origin against this configured value, **not** against request-derived values such as the `Host` header; deriving trust from request headers allowed a signature made for another site to be replayed. The `uri` origin must match exactly (scheme, host, and port) - the check was tightened from a prefix match.

Client sends `SIGN-IN-WITH-X` HTTP header (Base64-encoded JSON with signature).

### Breaking: result shapes

SIWx validation and verification results are discriminated unions across all three SDKs. The old `{ valid, error, address }` shape is gone:

```typescript
type SIWxValidationResult =
  | { isValid: true }
  | { isValid: false; invalidReason: SIWxValidationCode; invalidMessage: string };
```

Verify success carries `payer`, not `address`. Python uses `is_valid` / `invalid_reason` / `invalid_message` / `payer`. Go moved `Origin` onto `CreateResourceServerExtension()` and removed `Domain` / `ResourceURI` from `DeclareOptions`. These shipped as **minor** releases, not major.

### SIWx error codes

Validation: `invalid_siwx_domain_mismatch`, `invalid_siwx_uri_mismatch`, `invalid_siwx_issued_at`, `invalid_siwx_issued_at_too_old`, `invalid_siwx_issued_at_in_future`, `invalid_siwx_expiration_time`, `invalid_siwx_expired`, `invalid_siwx_not_before`, `invalid_siwx_not_yet_valid`, `invalid_siwx_nonce`.

Verification: `invalid_siwx_signature`, `invalid_siwx_chain_id`, `invalid_siwx_unsupported_chain`, `invalid_siwx_malformed_signature`, `invalid_siwx_verifier_error`.

Solana SIWx verification rejects small-order Ed25519 public keys (tweetnacl accepted identity-point forgeries).

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

## Builder Code (On-Chain Attribution)

The `builder-code` extension enables on-chain attribution tracking for x402 payments. Attribution is encoded as an ERC-8021 Schema 2 CBOR "builder code" appended to the settlement transaction calldata via the EVM `calldataSuffix`/`dataSuffix` plumbing, so integrators and tooling can be credited for the payments they originate (app, service, and wallet parties can each attach a code). The service-code field `s` accepts multiple codes (a string or an array / `[]string`), so layered clients (e.g. an MCP middleware) can attribute several participants on-chain. **Capped at 5** (`MAX_SERVICE_CODES`): facilitators silently truncate excess entries, so a sixth code is dropped without error. Note this cap is an implementation constant - it does not appear in `specs/extensions/builder_code.md`.

SDK helpers: TypeScript (`@x402/extensions/builder-code`), Go (`go/v2/extensions/buildercode`, `DeclareBuilderCodeExtension` + client/server/facilitator + CBOR), and Python (`x402.extensions.builder_code`). See `specs/extensions/builder_code.md`.

## HTTP Message Signatures (Agent Identity)

The `http-message-signatures` extension establishes the identity of the paying agent through cryptographic request signatures (RFC 9421). Cloudflare's `cloudflare:402` network binding uses it to bind a payment to a verifiable agent identity. Spec-defined; no SDK helper yet. See `specs/extensions/http-message-signatures.md`.

## Auth Hints (Authentication Discovery)

The `auth-hints` extension provides authentication hints for specific payment requirements. When a `402` response includes multiple `accepts[]` entries and only some require authentication, `auth-hints` lets the client discover which entries need auth - and how to obtain credentials - before committing to a payment method, avoiding an extra round trip. It is a Server-to-Client extension; the facilitator is not involved. Spec-defined; no SDK helper yet. See `specs/extensions/extension-auth-hints.md`.

---

## SDK Support Matrix

| Extension | TypeScript | Go | Python |
|-----------|------------|-----|--------|
| bazaar | Yes | Yes | Yes |
| bazaar (facilitator client - search) | Yes | Yes | Yes |
| offer-receipt | Yes | No | No |
| sign-in-with-x | Yes | Yes | Yes |
| payment-identifier | Yes | Yes | Yes |
| eip2612GasSponsoring | Yes | Yes | Yes |
| erc20ApprovalGasSponsoring | Yes | Yes | Yes |
| builder-code | Yes | Yes | Yes |

The `http-message-signatures` and `auth-hints` extensions are defined in the protocol spec but do not yet have SDK helpers in any language. `builder-code` now ships all three (Python landed as `x402.extensions.builder_code` plus `x402.mechanisms.evm.data_suffix`).
