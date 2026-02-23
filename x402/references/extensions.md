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

Enables resource discovery and cataloging. Servers declare endpoint specs so facilitators can catalog them in a discovery service.

### Server Advertises (in PaymentRequired)

```json
{
  "extensions": {
    "bazaar": {
      "info": {
        "input": {
          "type": "http",
          "method": "GET",
          "queryParams": { "city": "San Francisco" }
        },
        "output": {
          "type": "json",
          "example": { "city": "San Francisco", "weather": "foggy", "temperature": 60 }
        }
      },
      "schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
          "input": {
            "type": "object",
            "properties": {
              "type": { "type": "string", "const": "http" },
              "method": { "type": "string", "enum": ["GET", "HEAD", "DELETE"] },
              "queryParams": { "type": "object" }
            },
            "required": ["type", "method"]
          },
          "output": {
            "type": "object",
            "properties": {
              "type": { "type": "string" },
              "example": { "type": "object" }
            },
            "required": ["type"]
          }
        },
        "required": ["input"]
      }
    }
  }
}
```

### POST Endpoint Example

```json
{
  "extensions": {
    "bazaar": {
      "info": {
        "input": {
          "type": "http",
          "method": "POST",
          "bodyType": "json",
          "body": { "query": "example" }
        },
        "output": { "type": "json", "example": { "results": [] } }
      },
      "schema": { "..." : "..." }
    }
  }
}
```

### Input Types

**Query methods (GET, HEAD, DELETE):**
| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Always `"http"` |
| `method` | Yes | `"GET"`, `"HEAD"`, or `"DELETE"` |
| `queryParams` | No | Example query parameters |
| `headers` | No | Custom header examples |

**Body methods (POST, PUT, PATCH):**
| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Always `"http"` |
| `method` | Yes | `"POST"`, `"PUT"`, or `"PATCH"` |
| `bodyType` | Yes | `"json"`, `"form-data"`, or `"text"` |
| `body` | Yes | Request body example |

### SDK Usage

**TypeScript:**
```typescript
import { declareDiscoveryExtension } from "@x402/extensions/bazaar";

// In route config
extensions: {
  ...declareDiscoveryExtension({
    output: { example: { weather: "sunny", temperature: 72 } }
  }),
}
```

**Go:**
```go
import "github.com/coinbase/x402/go/extensions/bazaar"

Extensions: bazaar.DeclareDiscoveryExtension(bazaar.DiscoveryInfo{
    Output: map[string]interface{}{
        "type": "json",
        "example": map[string]interface{}{"weather": "sunny"},
    },
})
```

### Facilitator Behavior

Facilitators receiving a `PaymentPayload` with bazaar extension:
1. Validate `info` against provided `schema`
2. Extract discovery information (URL, method, input/output)
3. Catalog in their discovery service (implementation-specific)

### Discovery API

```
GET /discovery/resources?type=http&limit=10
```

Returns cataloged x402 resources with their payment requirements.

---

## Payment Identifier (Idempotency)

Enables clients to provide an `id` for request deduplication and safe retries.

### Server Advertises

```json
{
  "extensions": {
    "payment-identifier": {
      "info": { "required": false },
      "schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
          "required": { "type": "boolean" },
          "id": { "type": "string", "minLength": 16, "maxLength": 128 }
        },
        "required": ["required"]
      }
    }
  }
}
```

### Client Sends

```json
{
  "extensions": {
    "payment-identifier": {
      "schema": { "..." : "..." },
      "info": {
        "required": false,
        "id": "pay_7d5d747be160e280504c099d984bcfe0"
      }
    }
  }
}
```

### ID Format

- **Length**: 16-128 characters
- **Characters**: alphanumeric, hyphens, underscores
- **Recommendation**: UUID v4 with prefix (e.g., `pay_`)

### Idempotency Behavior

| Scenario | Server Response |
|----------|-----------------|
| New `id` | Process normally |
| Same `id`, same payload | Return cached response |
| Same `id`, different payload | 409 Conflict |
| `required: true`, no `id` | 400 Bad Request |

### Responsibilities

- **Server**: Request deduplication, response caching
- **Facilitator**: Verify/settle idempotency
- **Client**: Generate unique `id`, reuse on retries

---

## Sign-In With X (Wallet Authentication)

CAIP-122 wallet-based authentication. Clients prove wallet ownership by signing a challenge, allowing servers to skip payment for addresses that previously paid.

This is a **Server-Client** extension. The facilitator is not involved.

### Server Advertises

```json
{
  "extensions": {
    "sign-in-with-x": {
      "info": {
        "domain": "api.example.com",
        "uri": "https://api.example.com/premium-data",
        "version": "1",
        "nonce": "a1b2c3d4e5f67890a1b2c3d4e5f67890",  // pragma: allowlist secret
        "issuedAt": "2024-01-15T10:30:00.000Z",
        "expirationTime": "2024-01-15T10:35:00.000Z",
        "statement": "Sign in to access premium data",
        "resources": ["https://api.example.com/premium-data"]
      },
      "supportedChains": [
        { "chainId": "eip155:8453", "type": "eip191" },
        { "chainId": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp", "type": "ed25519" }
      ],
      "schema": { "..." : "..." }
    }
  }
}
```

### Client Sends (SIGN-IN-WITH-X Header)

Base64-encoded JSON in `SIGN-IN-WITH-X` HTTP header:

```json
{
  "domain": "api.example.com",
  "address": "0x857b06519E91e3A54538791bDbb0E22373e36b66",
  "uri": "https://api.example.com/premium-data",
  "version": "1",
  "chainId": "eip155:8453",
  "type": "eip191",
  "nonce": "a1b2c3d4e5f67890a1b2c3d4e5f67890",  // pragma: allowlist secret
  "issuedAt": "2024-01-15T10:30:00.000Z",
  "expirationTime": "2024-01-15T10:35:00.000Z",
  "statement": "Sign in to access premium data",
  "resources": ["https://api.example.com/premium-data"],
  "signature": "0x2d6a7588..."
}
```

### Supported Chains

| Chain | Type | Message Format |
|-------|------|---------------|
| EVM (`eip155:*`) | `eip191` | EIP-4361 (SIWE) |
| Solana (`solana:*`) | `ed25519` | Sign-In With Solana (SIWS) |

### EVM Message Format (SIWE)

```
api.example.com wants you to sign in with your Ethereum account:
0x857b06519E91e3A54538791bDbb0E22373e36b66

Sign in to access premium data

URI: https://api.example.com/premium-data
Version: 1
Chain ID: 8453
Nonce: a1b2c3d4e5f67890a1b2c3d4e5f67890
Issued At: 2024-01-15T10:30:00.000Z
Expiration Time: 2024-01-15T10:35:00.000Z
```

### Server Verification Steps

1. Parse and base64-decode the `SIGN-IN-WITH-X` header
2. Validate: `domain` matches request host, `uri` matches origin, `issuedAt` is recent, `expirationTime` is future, `nonce` is unique
3. Verify signature by chain type (`eip155:*` -> ECDSA, `solana:*` -> Ed25519)
4. Check if recovered `address` has previously paid for the resource

### Security

- **Domain binding** prevents cross-service signature reuse
- **Unique nonces** prevent replay attacks
- **Time bounds** constrain validity windows
- EVM supports smart wallets via EIP-1271/EIP-6492

### SDK Support

| Extension | TypeScript | Go | Python |
|-----------|------------|-----|--------|
| bazaar | Yes | Yes | Yes |
| sign-in-with-x | Yes | No | No |
| payment-identifier | Yes | No | No |

---

## Gas Sponsoring Extensions (EVM)

Two extensions enable gasless Permit2 approval flows for the `exact` EVM scheme. Both are Facilitator-advertised: the facilitator agrees to sponsor gas for the client's approval transaction.

### eip2612GasSponsoring

For tokens implementing **EIP-2612** (e.g., USDC). The client signs an off-chain EIP-2612 permit, and the facilitator submits it on-chain via `x402Permit2Proxy.settleWithPermit`.

**Facilitator advertises in PaymentRequired:**
```json
{
  "extensions": {
    "eip2612GasSponsoring": {
      "info": {
        "description": "The facilitator accepts EIP-2612 gasless Permit to Permit2 canonical contract.",
        "version": "1"
      },
      "schema": {
        "type": "object",
        "properties": {
          "from": { "type": "string", "description": "Sender address" },
          "asset": { "type": "string", "description": "ERC-20 token contract" },
          "spender": { "type": "string", "description": "Canonical Permit2 address" },
          "amount": { "type": "string", "description": "Approval amount (typically MaxUint)" },
          "nonce": { "type": "string", "description": "Current nonce of sender" },
          "deadline": { "type": "string", "description": "Signature expiry timestamp" },
          "signature": { "type": "string", "description": "65-byte EIP-2612 signature (r,s,v)" },
          "version": { "type": "string", "description": "Schema version" }
        },
        "required": ["from", "asset", "spender", "amount", "nonce", "deadline", "signature", "version"]
      }
    }
  }
}
```

**Client sends in PaymentPayload:**
```json
{
  "extensions": {
    "eip2612GasSponsoring": {
      "info": {
        "from": "0x857b...36b66",
        "asset": "0x036C...CF7e",
        "spender": "0xCanonicalPermit2",
        "amount": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
        "nonce": "0",
        "deadline": "1740672154",
        "signature": "0x2d6a7588...",
        "version": "1"
      }
    }
  }
}
```

**Facilitator verification:**
1. Verify `asset` implements `IERC20Permit`
2. Verify `signature` was signed for `spender` and recovers to `from`
3. Verify `spender` matches Canonical Permit2
4. Simulate `x402Permit2Proxy.settleWithPermit`

**Settlement:** Calls `x402Permit2Proxy.settleWithPermit` (atomic permit + settle).

### erc20ApprovalGasSponsoring

For tokens **without** EIP-2612 support. The client signs a raw EVM transaction calling `token.approve(Permit2, amount)`, and the facilitator broadcasts it with gas funding.

**Key difference from eip2612:** The client signs a full EVM transaction (not just a permit signature), and the facilitator must fund gas if the client lacks native tokens.

**Client sends in PaymentPayload:**
```json
{
  "extensions": {
    "erc20ApprovalGasSponsoring": {
      "info": {
        "from": "0x857b...36b66",
        "asset": "0x036C...CF7e",
        "spender": "0xCanonicalPermit2",
        "amount": "115792089237316195423570985008687907853269984665640564039457584007913129639935",
        "signedTransaction": "0x505cbf0d...",
        "version": "1"
      }
    }
  }
}
```

**Client requirements:**
- `maxFee` and `maxPriorityFee` must align with current network gas prices
- `nonce` must match the client's current on-chain nonce

**Facilitator verification:**
1. RLP-decode the signed transaction
2. Verify signer matches `from`
3. Verify `to` equals the `asset` contract
4. Verify calldata matches `approve(spender, amount)`
5. Verify `spender` matches Canonical Permit2
6. Verify nonce matches client's on-chain nonce
7. Verify gas fees match current network prices
8. Check if client has enough native gas; calculate deficit if not

**Settlement (atomic batch):**
1. **Gas funding** - send native tokens to client if needed
2. **Approval relay** - broadcast client's signed `approve()` transaction
3. **Settlement** - call `x402Permit2Proxy.settle()`

All three steps execute as an atomic batch to prevent front-running between the funding and settlement steps.

### Gas Sponsoring Comparison

| Feature | eip2612GasSponsoring | erc20ApprovalGasSponsoring |
|---------|---------------------|---------------------------|
| Token requirement | Must implement EIP-2612 | Any ERC-20 |
| Client signs | Off-chain EIP-2612 permit | Full EVM transaction |
| Gas funding needed | No (off-chain signature) | Yes (if client lacks gas) |
| Settlement method | `settleWithPermit` | Atomic batch (fund + approve + settle) |
| Front-run protection | Inherent (off-chain) | Atomic batch required |
