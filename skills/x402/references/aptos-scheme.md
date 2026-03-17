# Aptos Exact Scheme Reference

The `exact` scheme on Aptos uses native Fungible Asset transfers with optional fee payer (gas) sponsorship by the facilitator.

## SDK Support

| SDK | Status |
|-----|--------|
| TypeScript (`@x402/aptos`) | Full support (client, server, facilitator) |
| Go | Not supported |
| Python | Not supported |

Install: `npm install @x402/aptos`

## Network Identifiers

| Network | CAIP-2 ID | Chain ID |
|---------|-----------|----------|
| Aptos Mainnet | `aptos:1` | 1 |
| Aptos Testnet | `aptos:2` | 2 |

## Supported Tokens

Any Aptos fungible asset. Default: USDC (6 decimals).

| Network | USDC Address |
|---------|-------------|
| Mainnet | `0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b` |
| Testnet | `0x69091fbab5f7d635ee7ac5098cf0c1efbe31d68fec0f2cd565e8d168daf52832` |

Address format: 64 hex characters with `0x` prefix (regex: `/^0x[a-fA-F0-9]{64}$/`).

## Protocol Flow

1. Client requests protected resource
2. Server returns `402` with PaymentRequirements (includes `extra.feePayer` if gas sponsored)
3. Client builds fee payer transaction using `0x1::primary_fungible_store::transfer` (or `0x1::fungible_asset::transfer`)
4. Client signs transaction (signature covers payload only, NOT fee payer address)
5. Client serializes via BCS encoding, Base64 encodes, sends in `PAYMENT-SIGNATURE` header
6. Server forwards to facilitator for verification
7. Facilitator validates structure, signature, and payment details
8. Server performs work, then requests settlement from facilitator
9. Facilitator adds fee payer signature (if sponsored) and submits to Aptos
10. Server returns response with `PAYMENT-RESPONSE` header

## PaymentRequirements

```json
{
  "scheme": "exact",
  "network": "aptos:1",
  "amount": "1000000",
  "asset": "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b",
  "payTo": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "maxTimeoutSeconds": 60,
  "extra": {
    "feePayer": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
  }
}
```

- `extra.feePayer`: If present, facilitator pays gas. If absent, client pays own gas.

## Verification Rules

Facilitator verification:
1. Verify x402Version is 2
2. Verify scheme is "exact"
3. Verify network matches (CAIP-2)
4. For sponsored tx: verify fee payer is managed by facilitator
5. Deserialize BCS-encoded transaction and verify signature
6. Verify chain ID matches expected network
7. Verify sender's public key matches derived address
8. For sponsored tx: verify max gas <= 500,000 units (prevent gas drain)
9. For sponsored tx: verify fee payer address matches
10. Verify sender != fee payer
11. Verify transaction not expired (5-second buffer)
12. Verify contains fungible asset transfer (`0x1::primary_fungible_store::transfer` or `0x1::fungible_asset::transfer`)
13. Verify transfer targets correct asset address
14. Verify transfer amount matches exactly
15. Verify transfer recipient matches exactly
16. Verify sender has sufficient balance
17. Simulate transaction

## Supported Signature Schemes

- Ed25519 (single, most common)
- MultiEd25519 (multi-signature)
- SingleKey (Ed25519, Secp256k1, Secp256r1)
- MultiKey (multiple keys)

## TypeScript Usage

### Server

```typescript
import { x402ResourceServer } from "@x402/core/server";
import { ExactAptosScheme } from "@x402/aptos/exact/server";

const server = new x402ResourceServer(facilitator)
  .register("aptos:2", new ExactAptosScheme());
```

### Client

```typescript
import { x402Client } from "@x402/core";
import { ExactAptosScheme } from "@x402/aptos/exact/client";
import { createClientSigner } from "@x402/aptos";

const signer = createClientSigner(process.env.APTOS_PRIVATE_KEY);
const client = new x402Client();
client.register("aptos:*", new ExactAptosScheme(signer));
```

### Facilitator

```typescript
import { x402Facilitator } from "@x402/core";
import { ExactAptosScheme } from "@x402/aptos/exact/facilitator";
import { toFacilitatorAptosSigner } from "@x402/aptos";

const facilitator = new x402Facilitator();
facilitator.register("aptos:2", new ExactAptosScheme(
  toFacilitatorAptosSigner(aptosAccount),
  true  // sponsorTransactions (default)
));
```

## Multi-Signer Load Balancing

The Aptos facilitator supports multiple fee payer addresses. `getExtra()` randomly selects from available signers. `getSigners()` returns all addresses.

## Non-Sponsored Transactions

If `extra.feePayer` is absent, the client pays their own gas:
1. Client constructs a regular transaction including gas payment
2. Client fully signs the transaction
3. Facilitator submits the fully-signed transaction directly via `submitTransaction()`

## Key Import Paths

| Purpose | Import |
|---------|--------|
| Client scheme | `@x402/aptos/exact/client` |
| Server scheme | `@x402/aptos/exact/server` |
| Facilitator scheme | `@x402/aptos/exact/facilitator` |
| Signer utilities | `@x402/aptos` |
| Constants | `@x402/aptos` (APTOS_MAINNET_CAIP2, APTOS_TESTNET_CAIP2, USDC_MAINNET_FA, USDC_TESTNET_FA, MAX_GAS_AMOUNT, APTOS_ADDRESS_REGEX) |
