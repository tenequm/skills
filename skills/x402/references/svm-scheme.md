# Solana (SVM) Exact Scheme Reference

The `exact` scheme on Solana uses `TransferChecked` for SPL tokens. The client creates a partially-signed versioned transaction; the facilitator adds its fee-payer signature and broadcasts.

## Canonical addresses

Well-known Solana base58 mint and program addresses referenced by placeholder elsewhere in this file. All values are public, on-chain identifiers (not secrets).

| Placeholder | Value |
|-------------|-------|
| `<USDC_SOL_MINT>` | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` (USDC mint, Solana Mainnet) |
| `<USDC_SOL_DEVNET_MINT>` | `4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU` (USDC mint, Solana Devnet/Testnet) |
| `<SPL_TOKEN_PROGRAM>` | `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA` (SPL Token program) |
| `<SPL_TOKEN_2022_PROGRAM>` | `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` (Token-2022 program) |
| `<LIGHTHOUSE_PROGRAM>` | `L2TExMFKdjpN9kozasaurPirfHy9P8sbXoAN1qA3S95` (Lighthouse instruction-guard program, injected by Phantom/Solflare) |
| `<MEMO_PROGRAM>` | `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr` (SPL Memo program) |

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
  "asset": "<USDC_SOL_MINT>",
  "payTo": "<EXAMPLE_RECIPIENT>",
  "maxTimeoutSeconds": 60,
  "extra": {
    "feePayer": "<EXAMPLE_FEE_PAYER>"
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

The decompiled transaction MUST contain 3 to 7 instructions in this order (the static-path ceiling was raised from 6 to 7 in TS v2.14.0 to accommodate wallets that inject multiple Lighthouse assertions):

1. `ComputeBudget::SetComputeUnitLimit` (discriminator `2`)
2. `ComputeBudget::SetComputeUnitPrice` (discriminator `3`)
3. `SPL Token` or `Token-2022` `TransferChecked`
4-7. (Optional) Lighthouse or Memo program instructions

- Allowed optional programs: Lighthouse (`<LIGHTHOUSE_PROGRAM>`) and Memo (`<MEMO_PROGRAM>`)
- Phantom injects 1 Lighthouse instruction; Solflare injects 2
- Memo instructions enable transaction uniqueness

#### Simulation-Based Smart-Wallet Verification (Path 2)

When `enableSmartWalletVerification` is set, transactions the static positional path rejects (smart-wallet-wrapped layouts, extra instructions) are re-verified by simulating the transaction and inspecting CPI inner instructions for a matching `TransferChecked`. This accepts payments from any allowlisted smart-wallet program (Squads, Swig, SPL Governance, Metaplex Core, Lighthouse) without a per-wallet parser, with fee-payer isolation (Address Lookup Table resolution), operator-configurable compute-budget caps, post-settlement transfer verification (TOCTOU defense), and seller-required memo enforcement.

### 2. Fee Payer Safety

- Fee payer address MUST NOT appear in any instruction's `accounts`
- Fee payer MUST NOT be the `authority` for TransferChecked
- Fee payer MUST NOT be the `source` of transferred funds

### 3. Compute Budget Validity

- Compute unit price MUST be bounded (<= 5,000,000 microlamports = 5 lamports per CU)
- Default compute unit limit: 20,000

### 4. Transfer Destination

- TransferChecked program MUST be either `spl-token` (`<SPL_TOKEN_PROGRAM>`) or `token-2022` (`<SPL_TOKEN_2022_PROGRAM>`)
- Destination MUST equal the Associated Token Account PDA for `(owner=payTo, mint=asset)` under the selected token program

### 5. Amount Exactness

- `amount` in TransferChecked MUST equal `PaymentRequirements.amount` exactly

### 6. Simulation

- Facilitator signs the transaction with the fee payer's signer, then simulates to verify it would succeed

## Footgun: Destination ATA Must Exist On-Chain

x402 Solana transactions contain only `[ComputeBudget x2, TransferChecked, optional Lighthouse/Memo]` - there is no `createAssociatedTokenAccount` instruction. If the recipient's Associated Token Account for the payment mint does not already exist on-chain, `TransferChecked` fails simulation with `InvalidAccountData`, the facilitator rejects the payment, and the buyer's wallet never prompts. Before going live, create the destination token account (the ATA for `(owner=payTo, mint=asset)`) on the target network. `payTo` is the wallet **owner** address - the facilitator derives the ATA from it.

## Duplicate Settlement Mitigation (RECOMMENDED)

Solana's transaction deduplication ensures only one transfer executes on-chain, but the RPC returns "success" for each submission of the same transaction. A malicious client can exploit this by submitting the same payment to `/settle` multiple times before the first confirms.

### In-Memory Settlement Cache

All SDKs provide a `SettlementCache` that prevents this race condition:

- **Cache key**: the transaction **message hash** (as of TS v2.14.0 / Python 2.12.0 / Go 2.13.0). Earlier versions keyed on the full Base64 signed-transaction string, which let an attacker bypass the cache by randomizing the mutable fee-payer signature slot - keying on the message hash closes that bypass.
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
import "github.com/x402-foundation/x402/go/v2/mechanisms/svm"
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
| USDC | Mainnet | `<USDC_SOL_MINT>` |
| USDC | Devnet/Testnet | `<USDC_SOL_DEVNET_MINT>` |

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
