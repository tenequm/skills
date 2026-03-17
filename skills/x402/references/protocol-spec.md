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
| `scheme` | string | Yes | Payment scheme (e.g., "exact", "upto") |
| `network` | string | Yes | CAIP-2 network ID (e.g., "eip155:84532") |
| `amount` | string | Yes | Amount in atomic token units |
| `asset` | string | Yes | Token contract address or ISO 4217 currency code for fiat |
| `payTo` | string | Yes | Recipient wallet address or role constant (e.g., "merchant") |
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
| `extensions` | object | No | Protocol extensions data (e.g., signed receipts) |

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

The `x402Version` field is required in both `/verify` and `/settle` request bodies.

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

Note: While the request structure is identical, some schemes assign different semantics to fields at settlement time. In the `upto` scheme, `amount` in `paymentRequirements` is the maximum at verification but the actual amount to charge at settlement.

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

#### SupportedResponse Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kinds` | array | Yes | Array of SupportedKind objects |
| `extensions` | array | Yes | Extension identifiers the facilitator has implemented |
| `signers` | object | Yes | Map of CAIP-2 patterns to public signer addresses |

Each `SupportedKind` object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `x402Version` | number | Yes | Protocol version (2) |
| `scheme` | string | Yes | Payment scheme (e.g., "exact") |
| `network` | string | Yes | CAIP-2 network ID |
| `extra` | object | No | Scheme-specific configuration |

## Exact Scheme - EVM Asset Transfer Methods

The `exact` scheme on EVM supports three asset transfer methods:

| Method | Use Case | Notes |
|--------|----------|-------|
| **EIP-3009** | Tokens with native `transferWithAuthorization` (e.g., USDC) | Recommended. Simplest, truly gasless. |
| **Permit2** | Any ERC-20 token (universal fallback) | Uses `x402ExactPermit2Proxy` contract. |
| **ERC-7710** | Smart accounts with delegation support | Uses `DelegationManager.redeemDelegations()`. |

If no `assetTransferMethod` is specified in `extra`, implementations prioritize `eip3009` (if compatible) then `permit2`.

### Permit2 (Exact) Contract

Canonical `x402ExactPermit2Proxy` address: `0x402085c248EeA27D92E8b30b2C58ed07f9E20001` (same across all EVM chains via CREATE2).

### ERC-7710 Payload Structure

```json
{
  "payload": {
    "delegationManager": "0xDelegationManagerAddress",
    "permissionContext": "0x...",
    "delegator": "0x857b06519E91e3A54538791bDbb0E22373e36b66"
  }
}
```

Verification is done entirely through simulation of `delegationManager.redeemDelegations()`. No trusted list of DelegationManager implementations needed.

## Exact Scheme - SVM (Solana)

Uses `TransferChecked` for SPL tokens. Key verification requirements:
- Strict instruction layout: Compute Unit Limit, Compute Unit Price, TransferChecked (plus optional Lighthouse/Memo instructions for Phantom/Solflare wallets)
- Fee payer must NOT appear in any instruction accounts
- Compute unit price bounded (reference: <= 5 lamports/CU)
- Destination must equal ATA PDA for `(payTo, asset)`
- Transfer amount must exactly equal `PaymentRequirements.amount`

### Duplicate Settlement Mitigation (SVM)

Race condition: same tx submitted to `/settle` multiple times returns "success" each time. Mitigate with short-term in-memory cache of tx payloads, evict after 120 seconds. Error code: `duplicate_settlement`.

## Exact Scheme - Aptos

Uses `0x1::primary_fungible_store::transfer` for fungible assets. Key details:
- Network IDs: `aptos:1` (mainnet), `aptos:2` (testnet)
- `extra.feePayer`: address of facilitator account that sponsors gas (optional)
- Payload contains BCS-serialized, Base64-encoded signed transaction
- Supports sponsored (gasless) and non-sponsored transactions
- Verification: deserialize BCS transaction, verify signature, check transfer params, simulate via Aptos REST API
- Signature schemes: Ed25519, MultiEd25519, SingleKey, MultiKey

## Network Identifiers (CAIP-2)

Format: `{namespace}:{reference}`

| Network | CAIP-2 ID |
|---------|-----------|
| Base Mainnet | `eip155:8453` |
| Base Sepolia | `eip155:84532` |
| Ethereum Mainnet | `eip155:1` |
| Polygon Mainnet | `eip155:137` |
| Polygon Amoy | `eip155:80002` |
| Solana Mainnet | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` |
| Solana Devnet | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` |
| Avalanche Mainnet | `eip155:43114` |
| Avalanche Fuji | `eip155:43113` |
| MegaETH Mainnet | `eip155:4326` |
| Monad Mainnet | `eip155:143` |
| Stellar Mainnet | `stellar:pubnet` |
| Stellar Testnet | `stellar:testnet` |
| Aptos Mainnet | `aptos:1` |
| Aptos Testnet | `aptos:2` |
| Sei Mainnet | `eip155:1329` |
| Sei Testnet | `eip155:713715` |
| SKALE Mainnet | `eip155:1187947933` |
| SKALE Testnet | `eip155:324705682` |

## Discovery API (Bazaar)

### GET /discovery/resources

List discoverable x402 resources.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `type` | string | No | - | Filter by resource type ("http" or "mcp") |
| `limit` | number | No | 20 | Max results (1-100) |
| `offset` | number | No | 0 | Pagination offset |

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
| `invalid_payment_requirements` | Payment requirements invalid or malformed |
| `invalid_scheme` | Scheme not supported |
| `unsupported_scheme` | Scheme not supported by facilitator |
| `invalid_x402_version` | Version not supported |
| `invalid_transaction_state` | Blockchain transaction failed or rejected |
| `duplicate_settlement` | Same SVM transaction submitted to /settle multiple times |
| `invalid_upto_evm_payload_settlement_exceeds_amount` | Upto: settled more than authorized |
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

### Available Extensions

| Extension | Description | SDK Support |
|-----------|-------------|-------------|
| `bazaar` | Discovery layer for x402 endpoints and MCP tools | TS, Go, Python |
| `offer-receipt` | Signed offers (402 responses) and receipts (200 responses) for proof-of-interaction | TS |
| `payment-identifier` | Idempotency via unique payment IDs | TS, Go |
| `sign-in-with-x` | CAIP-122 wallet authentication for re-access without repaying | TS |
| `eip2612GasSponsoring` | Facilitator sponsors gas for EIP-2612 permit approvals | TS, Go |
| `erc20ApprovalGasSponsoring` | Facilitator sponsors gas for ERC-20 approvals | TS, Go |

## Security Considerations

- **Replay prevention**: EIP-3009 nonces + blockchain-level nonce tracking + time windows; Permit2 nonces for upto scheme; Solana blockhash expiration + duplicate settlement cache
- **Trust minimization**: Facilitators cannot modify amount or destination - they only broadcast
- **Signature verification**: All authorizations cryptographically signed by payer
- **Time constraints**: `validAfter`/`validBefore` (EIP-3009) or `validAfter`/`deadline` (Permit2) bound authorization lifetime
- **ERC-7710 race condition**: Mitigated via private mempool submission and reputation signals
