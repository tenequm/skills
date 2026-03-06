# Stellar Exact Scheme Reference

The `exact` scheme on Stellar uses Soroban smart contracts with the SEP-41 token standard. Clients sign auth entries (not full transactions); facilitators rebuild and submit transactions, always sponsoring fees.

**TypeScript only** - `@x402/stellar` package. Python and Go not yet implemented.

## Protocol Flow

1. Server responds with `PaymentRequired` containing `extra.feePayer` (facilitator's public key)
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
- Ledger-based expiration: `currentLedger + ceil(maxTimeoutSeconds / ~5s)`

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
    "feePayer": "GC2F5...FACILITATOR_KEY"
  }
}
```

## PaymentPayload

```json
{
  "x402Version": 2,
  "accepted": {
    "scheme": "exact",
    "network": "stellar:testnet",
    "amount": "1000000",
    "asset": "CBIELTK6YBZJU5UP2WWQEUCYKLPU6AUNZ2BQ4WWFEIE3USCIHMXQDAMA",
    "payTo": "GA3D5...STELLAR_ADDRESS",
    "maxTimeoutSeconds": 60,
    "extra": { "feePayer": "GC2F5...FACILITATOR_KEY" }
  },
  "payload": {
    "transaction": "AAAAAAAAAA...base64_XDR...AAAAAAA="
  }
}
```

The `transaction` field contains the base64-encoded XDR Soroban transaction with signed auth entries.

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

const server = new x402ResourceServer(facilitator);
server.register("stellar:testnet", new ExactStellarScheme());
```

### Facilitator

```typescript
import { createEd25519Signer } from "@x402/stellar";
import { ExactStellarScheme } from "@x402/stellar/exact/facilitator";

const signers = [createEd25519Signer(privateKey, "stellar:testnet")];
const scheme = new ExactStellarScheme(signers, {
  rpcConfig: { url: "https://soroban-testnet.stellar.org" },
  maxTransactionFeeStroops: 50_000,
});
```

### Custom RPC

```typescript
const scheme = new ExactStellarScheme(signer, {
  url: "https://custom-rpc-provider.example.com",
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

1. Transaction has exactly 1 `invokeHostFunction` operation
2. Contract address matches `requirements.asset`
3. Function is `transfer` with 3 arguments (from, to, amount)
4. `to` equals `requirements.payTo`
5. Amount equals `requirements.amount` (as i128)
6. Facilitator is NOT the payer, operation source, or in auth entries
7. Auth entry signatures valid and not expired
8. Re-simulation succeeds with expected balance changes only
9. Client fee within acceptable bounds

## Address Types

- **G-address**: Standard Stellar accounts
- **C-address**: Soroban contract addresses (used for token assets)
- **M-address**: Muxed accounts (multiplexed sub-accounts)

## Utility Functions

```typescript
import {
  validateStellarDestinationAddress,  // G, C, or M address
  validateStellarAssetAddress,        // C address only (contract)
  isStellarNetwork,                   // Check valid Stellar CAIP-2
  getRpcUrl,                          // Get RPC URL with custom override
  getNetworkPassphrase,               // Get network passphrase
  convertToTokenAmount,               // Decimal to smallest units
} from "@x402/stellar";
```
