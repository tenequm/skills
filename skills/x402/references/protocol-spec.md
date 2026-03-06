# x402 Protocol Specification (v2)

## Protocol Version: 2

x402 is a three-layer architecture:
1. **Types** - Core data structures independent of transport and scheme
2. **Logic (Schemes)** - Payment formation/verification per network
3. **Representation (Transports)** - How payment data is transmitted

## Core Payment Flow

1. Client requests resource from server
2. Server responds with payment required signal + `PaymentRequired` data
3. Client creates `PaymentPayload` with signed authorization
4. Client retries request with payment payload attached
5. Server POSTs to facilitator `/verify`
6. Facilitator validates signature, balance, time window
7. Server POSTs to facilitator `/settle`
8. Facilitator broadcasts transaction to blockchain
9. Server responds with success + `SettlementResponse`

## Core Types

### PaymentRequired

Sent by server when payment is needed:

```json
{
  "x402Version": 2,
  "error": "PAYMENT-SIGNATURE header is required",
  "resource": {
    "url": "https://api.example.com/premium-data",
    "description": "Access to premium market data",
    "mimeType": "application/json"
  },
  "accepts": [
    {
      "scheme": "exact",
      "network": "eip155:84532",
      "amount": "10000",
      "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
      "payTo": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
      "maxTimeoutSeconds": 60,
      "extra": {
        "name": "USDC",
        "version": "2"
      }
    }
  ],
  "extensions": {}
}
```

#### PaymentRequired Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `x402Version` | number | Yes | Protocol version (must be 2) |
| `error` | string | No | Human-readable error message |
| `resource` | ResourceInfo | Yes | Protected resource metadata |
| `accepts` | PaymentRequirements[] | Yes | Acceptable payment methods |
| `extensions` | object | No | Protocol extensions data |

#### PaymentRequirements Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scheme` | string | Yes | Payment scheme (e.g., "exact") |
| `network` | string | Yes | CAIP-2 network ID (e.g., "eip155:84532") |
| `amount` | string | Yes | Amount in atomic token units |
| `asset` | string | Yes | Token contract address |
| `payTo` | string | Yes | Recipient wallet address |
| `maxTimeoutSeconds` | number | Yes | Max time for payment completion |
| `extra` | object | No | Scheme-specific data |

#### ResourceInfo Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL of the protected resource |
| `description` | string | No | Human-readable description |
| `mimeType` | string | No | MIME type of response |

### PaymentPayload

Sent by client with payment authorization:

```json
{
  "x402Version": 2,
  "resource": {
    "url": "https://api.example.com/premium-data",
    "description": "Access to premium market data",
    "mimeType": "application/json"
  },
  "accepted": {
    "scheme": "exact",
    "network": "eip155:84532",
    "amount": "10000",
    "asset": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
    "payTo": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
    "maxTimeoutSeconds": 60,
    "extra": { "name": "USDC", "version": "2" }
  },
  "payload": {
    "signature": "0x2d6a7588...",
    "authorization": {
      "from": "0x857b06519E91e3A54538791bDbb0E22373e36b66",
      "to": "0x209693Bc6afc0C5328bA36FaF03C514EF312287C",
      "value": "10000",
      "validAfter": "1740672089",
      "validBefore": "1740672154",
      "nonce": "0xf3746613c2d920b5fdabc0856f2aeb2d4f88ee6037b8cc5d04a71a4462f13480"
    }
  },
  "extensions": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `x402Version` | number | Yes | Protocol version |
| `resource` | ResourceInfo | No | Resource being accessed |
| `accepted` | PaymentRequirements | Yes | Chosen payment method |
| `payload` | object | Yes | Scheme-specific signed data |
| `extensions` | object | No | Protocol extensions data |

### SettlementResponse

Returned after successful settlement:

```json
{
  "success": true,
  "transaction": "0x1234567890abcdef...",
  "network": "eip155:84532",
  "payer": "0x857b06519E91e3A54538791bDbb0E22373e36b66"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | Yes | Whether settlement succeeded |
| `errorReason` | string | No | Error if failed |
| `payer` | string | No | Payer's wallet address |
| `transaction` | string | Yes | Blockchain tx hash |
| `network` | string | Yes | CAIP-2 network ID |
| `amount` | string | No | Actual settled amount (used by `upto` scheme; may differ from requested) |

### VerifyResponse

```json
{
  "isValid": true,
  "payer": "0x857b06519E91e3A54538791bDbb0E22373e36b66"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isValid` | boolean | Yes | Whether authorization is valid |
| `invalidReason` | string | No | Reason if invalid |
| `payer` | string | No | Payer's wallet address |

## TypeScript Type Definitions

```typescript
interface ResourceInfo {
  url: string;
  description: string;
  mimeType: string;
}

type PaymentRequirements = {
  scheme: string;
  network: Network;
  asset: string;
  amount: string;
  payTo: string;
  maxTimeoutSeconds: number;
  extra: Record<string, unknown>;
};

type PaymentRequired = {
  x402Version: number;
  error?: string;
  resource: ResourceInfo;
  accepts: PaymentRequirements[];
  extensions?: Record<string, unknown>;
};

type PaymentPayload = {
  x402Version: number;
  resource: ResourceInfo;
  accepted: PaymentRequirements;
  payload: Record<string, unknown>;
  extensions?: Record<string, unknown>;
};
```

## Facilitator HTTP API

### POST /verify

Verifies payment without executing on-chain.

**Request:**
```json
{
  "x402Version": 2,
  "paymentPayload": { /* PaymentPayload */ },
  "paymentRequirements": { /* PaymentRequirements */ }
}
```

The `x402Version` field is required in both `/verify` and `/settle` request bodies (added in v2 spec update, March 2026).

**Success Response:**
```json
{ "isValid": true, "payer": "0x..." }
```

**Error Response:**
```json
{ "isValid": false, "invalidReason": "insufficient_funds", "payer": "0x..." }
```

### POST /settle

Executes payment by broadcasting to blockchain.

**Request:** Same structure as `/verify` (includes `x402Version`).

**Success Response:**
```json
{
  "success": true,
  "payer": "0x...",
  "transaction": "0x...",
  "network": "eip155:84532"
}
```

### GET /supported

Lists supported schemes/networks/extensions.

**Response:**
```json
{
  "kinds": [
    { "x402Version": 2, "scheme": "exact", "network": "eip155:84532" },
    { "x402Version": 2, "scheme": "exact", "network": "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1" }
  ],
  "extensions": [],
  "signers": {
    "eip155:*": ["0x1234..."],
    "solana:*": ["CKPKJWNd..."]
  }
}
```

## Network Identifiers (CAIP-2)

Format: `{namespace}:{reference}`

| Network | CAIP-2 ID |
|---------|-----------|
| Base Mainnet | `eip155:8453` |
| Base Sepolia | `eip155:84532` |
| Ethereum Mainnet | `eip155:1` |
| Solana Mainnet | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` |
| Solana Devnet | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` |
| Avalanche Mainnet | `eip155:43114` |
| MegaETH Mainnet | `eip155:4326` |
| Stellar Mainnet | `stellar:pubnet` |
| Stellar Testnet | `stellar:testnet` |
| Aptos Mainnet | `aptos:1` |
| Aptos Testnet | `aptos:2` |
| Monad Mainnet | `eip155:143` |
| Avalanche Fuji | `eip155:43113` |

## Error Codes

| Code | Description |
|------|-------------|
| `insufficient_funds` | Client lacks enough tokens |
| `invalid_exact_evm_payload_signature` | Invalid EIP-712 signature |
| `invalid_exact_evm_payload_authorization_valid_before` | Authorization expired |
| `invalid_exact_evm_payload_authorization_valid_after` | Authorization not yet valid |
| `invalid_exact_evm_payload_authorization_value_mismatch` | Amount does not exactly match required |
| `invalid_exact_svm_payload_amount_mismatch` | Solana amount does not exactly match required |
| `permit2_amount_mismatch` | Permit2 amount does not exactly match required |
| `invalid_exact_evm_payload_recipient_mismatch` | Recipient mismatch |
| `invalid_network` | Network not supported |
| `invalid_payload` | Malformed payload |
| `invalid_scheme` | Scheme not supported |
| `invalid_x402_version` | Version not supported |
| `duplicate_settlement` | Same SVM transaction submitted to /settle multiple times |
| `unexpected_verify_error` | Unexpected verify error |
| `unexpected_settle_error` | Unexpected settle error |

## Extensions Structure

Extensions use a standardized key-value map in both `PaymentRequired` and `PaymentPayload`:

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

Clients must echo the extension from `PaymentRequired` into their `PaymentPayload`. They may append additional info but cannot delete or overwrite existing data.

## Security Considerations

- **Replay prevention**: EIP-3009 nonces + blockchain-level nonce tracking + time windows
- **Trust minimization**: Facilitators cannot modify amount or destination - they only broadcast
- **Signature verification**: All authorizations cryptographically signed by payer
- **Time constraints**: `validAfter`/`validBefore` bound authorization lifetime
