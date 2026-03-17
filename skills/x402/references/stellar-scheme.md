# Stellar Exact Scheme Reference

The `exact` scheme on Stellar uses Soroban smart contracts with the SEP-41 token standard. Clients sign auth entries (not full transactions); facilitators rebuild and submit transactions, always sponsoring fees.

**TypeScript only** - `@x402/stellar` package. Python and Go not yet implemented.

## Protocol Flow

1. Server responds with `PaymentRequired` containing `extra.areFeesSponsored` (always true)
2. Client builds a Soroban `invokeHostFunction` operation calling `transfer(from, to, amount)` on the token contract
3. Client simulates the transaction to identify auth entry requirements
4. Client signs auth entries with ledger-based expiration (NOT the full transaction)
5. Client serializes and base64-encodes the transaction (XDR format)
6. Facilitator decodes, validates, rebuilds transaction with its own source account
7. Facilitator re-simulates, signs (optional fee bump), and submits to Stellar network

## Network Identifiers (CAIP-28)

| Network | CAIP-2 ID |
|---------|-----------|
| Stellar Mainnet | `stellar:pubnet` |
| Stellar Testnet | `stellar:testnet` |

Default facilitator (`https://x402.org/facilitator`) supports Stellar Testnet.

## Default Assets (USDC)

| Network | Contract Address | Decimals |
|---------|-----------------|----------|
| Mainnet | `CCW67TSZV3SSS2HXMBQ5JFGCKJNXKZM7UQUWUZPUTHXSTZLEO7SJMI75` | 7 |
| Testnet | `CBIELTK6YBZJU5UP2WWQEUCYKLPU6AUNZ2BQ4WWFEIE3USCIHMXQDAMA` | 7 |

## RPC Configuration

- **Testnet**: Default RPC at `https://soroban-testnet.stellar.org` (HTTP allowed)
- **Mainnet**: No default RPC - must supply custom URL (HTTPS enforced). See [Stellar RPC Providers](https://developers.stellar.org/docs/data/apis/rpc/providers#publicly-accessible-apis)
- **Horizon URLs**: Testnet `https://horizon-testnet.stellar.org`, Mainnet `https://horizon.stellar.org`

## Key Differences from EVM/SVM

| Property | EVM | SVM | Stellar |
|----------|-----|-----|---------|
| Expiration | Timestamp-based | Blockhash (~60-90s) | Ledger sequence (~5s per ledger) |
| Client signs | EIP-712 typed data | Full transaction (partial) | Auth entries only |
| Fee sponsorship | Facilitator pays gas | Facilitator is fee payer | Always sponsored |
| Token standard | ERC-20 (EIP-3009/Permit2) | SPL TransferChecked | SEP-41 Soroban |

## Fee Configuration

- Base fee: 10,000 stroops (0.001 XLM) minimum
- Default max facilitator fee: 50,000 stroops
- Ledger-based expiration: `currentLedger + ceil(maxTimeoutSeconds / estimatedLedgerCloseTime)`
- Signature expiration ledger tolerance: 2 ledgers (for RPC skew)

## PaymentRequirements

```json
{
  "scheme": "exact",
  "network": "stellar:testnet",
  "amount": "1000000",
  "asset": "CBIELTK6YBZJU5UP2WWQEUCYKLPU6AUNZ2BQ4WWFEIE3USCIHMXQDAMA",
  "payTo": "GA3D5...STELLAR_ADDRESS",
  "maxTimeoutSeconds": 60,
  "extra": {
    "areFeesSponsored": true
  }
}
```

## TypeScript Usage

### Client

```typescript
import { createEd25519Signer } from "@x402/stellar";
import { ExactStellarScheme } from "@x402/stellar/exact/client";
import { x402Client } from "@x402/core";

const signer = createEd25519Signer(privateKey, "stellar:testnet");
const client = new x402Client();
client.register("stellar:*", new ExactStellarScheme(signer));
```

### Server

```typescript
import { ExactStellarScheme } from "@x402/stellar/exact/server";
import { x402ResourceServer } from "@x402/core/server";

const server = new x402ResourceServer(facilitator)
  .register("stellar:testnet", new ExactStellarScheme());
```

### Facilitator

```typescript
import { createEd25519Signer } from "@x402/stellar";
import { ExactStellarScheme } from "@x402/stellar/exact/facilitator";

const signers = [createEd25519Signer(privateKey, "stellar:testnet")];
const scheme = new ExactStellarScheme(signers, {
  rpcConfig: { url: "https://soroban-testnet.stellar.org" },
  maxTransactionFeeStroops: 50_000,
  selectSigner: (addrs) => addrs[0], // Optional: custom signer selection
  feeBumpSigner: createEd25519Signer(feeBumpKey, "stellar:testnet"), // Optional
});
```

### Custom Token (registerMoneyParser)

```typescript
const serverScheme = new ExactStellarScheme();
serverScheme.registerMoneyParser(async (amount, network) => {
  if (network === "stellar:testnet") {
    return {
      amount: Math.round(amount * 1e7).toString(),
      asset: "CUSTOM_TOKEN_CONTRACT_ADDRESS",
      extra: { token: "CUSTOM" },
    };
  }
  return null;
});
```

## Facilitator Verification Rules (MUST)

1. Verify x402Version is 2
2. Verify scheme is "exact" and network is valid Stellar network
3. Transaction has exactly 1 `invokeHostFunction` operation
4. Facilitator addresses MUST NOT appear as transaction source, operation source, or in auth entries
5. Contract address matches `requirements.asset`
6. Function is `transfer` with 3 arguments (from, to, amount)
7. `to` equals `requirements.payTo`
8. Amount equals `requirements.amount` (as i128)
9. Re-simulation succeeds
10. Client fee within acceptable bounds (>= minResourceFee, <= maxTransactionFeeStroops)
11. Validate simulation events: exactly 1 transfer event matching expected sender/recipient/amount/asset
12. Auth entries: only `sorobanCredentialsAddress` type, no facilitator addresses, signature expiration within tolerance, no sub-invocations

## Settlement Flow

1. Re-verify payment
2. Parse transaction envelope, extract Soroban data
3. Select signer (round-robin by default, configurable)
4. Rebuild transaction with facilitator as source, facilitator-chosen fee
5. Sign inner transaction
6. Optionally wrap in FeeBumpTransaction (if `feeBumpSigner` configured)
7. Submit to network, poll for confirmation

## Address Types

- **G-address**: Standard Stellar accounts (56 chars)
- **C-address**: Soroban contract addresses (56 chars, used for token assets)
- **M-address**: Muxed accounts (69 chars, multiplexed sub-accounts)

## Utility Functions

```typescript
import {
  validateStellarDestinationAddress,  // G, C, or M address
  validateStellarAssetAddress,        // C address only (contract)
  isStellarNetwork,                   // Check valid Stellar CAIP-2
  getRpcUrl,                          // Get RPC URL with custom override
  getNetworkPassphrase,               // Get network passphrase
  convertToTokenAmount,               // Decimal to smallest units
  getEstimatedLedgerCloseTimeSeconds, // For expiration calculations
} from "@x402/stellar";
```
