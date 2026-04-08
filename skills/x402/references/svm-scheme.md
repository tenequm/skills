# Solana (SVM) Exact Scheme Reference

The `exact` scheme on Solana uses `TransferChecked` for SPL tokens. The client creates a partially-signed versioned transaction; the facilitator adds its fee-payer signature and broadcasts.

## Protocol Flow

1. Server responds with `PaymentRequired` containing `extra.feePayer` (facilitator's public key)
2. Client builds a Solana transaction with `TransferChecked` instruction
3. Client signs the transaction (partial signature - fee payer signature missing)
4. Client serializes and base64-encodes the partially-signed transaction
5. Client sends `PaymentPayload` with the base64 transaction
6. Facilitator decodes, verifies, and adds its fee-payer signature
7. Facilitator broadcasts the fully-signed transaction to Solana

## PaymentRequirements

```json
{
  "scheme": "exact",
  "network": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
  "amount": "1000",
  "asset": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "payTo": "2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",
  "maxTimeoutSeconds": 60,
  "extra": {
    "feePayer": "EwWqGE4ZFKLofuestmU4LDdK7XM1N4ALgdZccwYugwGd"
  }
}
```

- `asset`: Public key of the token mint (e.g., USDC mint)
- `extra.feePayer`: Facilitator's public key that pays transaction fees

## PaymentPayload

```json
{
  "x402Version": 2,
  "accepted": { "scheme": "exact", "network": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp", "..." },
  "payload": {
    "transaction": "AAAAAAAAAAAAA...AAAAAAAAAAAAA="
  }
}
```

The `transaction` field contains the base64-encoded, serialized, partially-signed versioned Solana transaction.

## Facilitator Verification Rules (MUST)

### 1. Instruction Layout

The decompiled transaction MUST contain 3 to 6 instructions in this order:

1. `ComputeBudget::SetComputeUnitLimit` (discriminator `2`)
2. `ComputeBudget::SetComputeUnitPrice` (discriminator `3`)
3. `SPL Token` or `Token-2022` `TransferChecked`
4. (Optional) Lighthouse or Memo program instruction
5. (Optional) Lighthouse or Memo program instruction
6. (Optional) Memo program instruction

- Allowed optional programs: Lighthouse (`L2TExMFKdjpN9kozasaurPirfHy9P8sbXoAN1qA3S95`) and Memo (`MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`)
- Phantom injects 1 Lighthouse instruction; Solflare injects 2
- Memo instructions enable transaction uniqueness

### 2. Fee Payer Safety

- Fee payer address MUST NOT appear in any instruction's `accounts`
- Fee payer MUST NOT be the `authority` for TransferChecked
- Fee payer MUST NOT be the `source` of transferred funds

### 3. Compute Budget Validity

- Compute unit price MUST be bounded (<= 5,000,000 microlamports = 5 lamports per CU)
- Default compute unit limit: 20,000

### 4. Transfer Destination

- TransferChecked program MUST be either `spl-token` (`TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`) or `token-2022` (`TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`)
- Destination MUST equal the Associated Token Account PDA for `(owner=payTo, mint=asset)` under the selected token program

### 5. Amount Exactness

- `amount` in TransferChecked MUST equal `PaymentRequirements.amount` exactly

### 6. Simulation

- Facilitator signs the transaction with the fee payer's signer, then simulates to verify it would succeed

## Duplicate Settlement Mitigation (RECOMMENDED)

Solana's transaction deduplication ensures only one transfer executes on-chain, but the RPC returns "success" for each submission of the same transaction. A malicious client can exploit this by submitting the same payment to `/settle` multiple times before the first confirms.

### In-Memory Settlement Cache

All SDKs provide a `SettlementCache` that prevents this race condition:

- **Cache key**: Base64-encoded transaction string
- **TTL**: 120 seconds (covers Solana blockhash lifetime of ~60-90s plus margin)
- **Behavior**: If key exists in cache, reject with `duplicate_settlement` error; otherwise insert and proceed
- **Eviction**: Entries older than 120 seconds are automatically removed
- **Thread safety**: Go uses `sync.Mutex`; Python uses `threading.Lock`; TypeScript relies on single-threaded event loop

### SDK Implementation

**TypeScript**: Built-in `SettlementCache` class. Enabled by default.

```typescript
import { SettlementCache } from "@x402/svm";
const cache = new SettlementCache();
new ExactSvmScheme(signer, cache); // optional - one is created if omitted
```

**Go**: Thread-safe `SettlementCache` with `sync.Mutex`. Must pass a shared instance to both V1 and V2 scheme registrations:

```go
import "github.com/x402-foundation/x402/go/mechanisms/svm"
cache := svm.NewSettlementCache()
```

**Python**: Thread-safe `SettlementCache` using `threading.Lock`. Same API as Go.

```python
from x402.mechanisms.svm.settlement_cache import SettlementCache
cache = SettlementCache()
```

## Multi-Signer Load Balancing

The SVM facilitator supports multiple fee payer addresses. `getExtra()` randomly selects from available signers to distribute load. `getSigners()` returns all available addresses.

## Supported Solana Assets

- Any SPL token (Token Program)
- Token-2022 program tokens

## Common Token Mints

| Token | Network | Mint Address |
|-------|---------|-------------|
| USDC | Mainnet | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |
| USDC | Devnet/Testnet | `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU` |

## Network Identifiers

| Network | CAIP-2 ID | V1 Name |
|---------|-----------|---------|
| Solana Mainnet | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | `solana` |
| Solana Devnet | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` | `solana-devnet` |
| Solana Testnet | `solana:4uhcVJyU9pJkvQyS88uRDiswHXSCkY3z` | `solana-testnet` |

## SDK Support

| SDK | Status |
|-----|--------|
| TypeScript (`@x402/svm`) | Full (client, server, facilitator) |
| Go | Full (facilitator) |
| Python | Full (facilitator) |
