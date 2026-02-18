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
  "asset": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  // pragma: allowlist secret
  "payTo": "2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",  // pragma: allowlist secret
  "maxTimeoutSeconds": 60,
  "extra": {
    "feePayer": "EwWqGE4ZFKLofuestmU4LDdK7XM1N4ALgdZccwYugwGd"  // pragma: allowlist secret
  }
}
```

- `asset`: Public key of the token mint (e.g., USDC mint)
- `extra.feePayer`: Facilitator's public key that pays transaction fees

## PaymentPayload

```json
{
  "x402Version": 2,
  "resource": { "url": "...", "description": "...", "mimeType": "..." },
  "accepted": {
    "scheme": "exact",
    "network": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
    "amount": "1000",
    "asset": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  // pragma: allowlist secret
    "payTo": "2wKupLR9q6wXYppw8Gr2NvWxKBUqm4PPJKkQfoxHDBg4",  // pragma: allowlist secret
    "maxTimeoutSeconds": 60,
    "extra": {
      "feePayer": "EwWqGE4ZFKLofuestmU4LDdK7XM1N4ALgdZccwYugwGd"  // pragma: allowlist secret
    }
  },
  "payload": {
    "transaction": "AAAAAAAAAAAAA...AAAAAAAAAAAAA="
  }
}
```

The `transaction` field contains the base64-encoded, serialized, partially-signed versioned Solana transaction.

## SettlementResponse

```json
{
  "success": true,
  "transaction": "base58 encoded transaction signature",
  "network": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
  "payer": "base58 encoded public address of the transaction fee payer"
}
```

## Facilitator Verification Rules (MUST)

### 1. Instruction Layout

The decompiled transaction MUST contain 3 to 5 instructions in this order:

1. `ComputeBudget::SetComputeUnitLimit`
2. `ComputeBudget::SetComputeUnitPrice`
3. `SPL Token` or `Token-2022` `TransferChecked`
4. (Optional) Lighthouse program instruction (Phantom wallet protection)
5. (Optional) Lighthouse program instruction (Solflare wallet protection)

- If a 4th or 5th instruction exists, its program MUST be Lighthouse (`L2TExMFKdjpN9kozasaurPirfHy9P8sbXoAN1qA3S95`)
- Phantom injects 1 Lighthouse instruction; Solflare injects 2

### 2. Fee Payer Safety

- Fee payer address MUST NOT appear in any instruction's `accounts`
- Fee payer MUST NOT be the `authority` for TransferChecked
- Fee payer MUST NOT be the `source` of transferred funds

### 3. Compute Budget Validity

- Instructions (1) and (2) MUST use `ComputeBudget` program with correct discriminators (2 = SetLimit, 3 = SetPrice)
- Compute unit price MUST be bounded (reference: <= 5 lamports per CU)

### 4. Transfer Destination

- TransferChecked program MUST be either `spl-token` or `token-2022`
- Destination MUST equal the Associated Token Account PDA for `(owner=payTo, mint=asset)` under the selected token program

### 5. Account Existence

- Source ATA MUST exist
- Destination ATA MUST exist (unless Create ATA instruction is present)

### 6. Amount Exactness

- `amount` in TransferChecked MUST equal `PaymentRequirements.amount` exactly

## Supported Solana Assets

- Any SPL token
- Token-2022 program tokens

## Common Token Mints

| Token | Mint Address |
|-------|-------------|
| USDC (Mainnet) | `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` |

## Network Identifiers

| Network | CAIP-2 ID |
|---------|-----------|
| Solana Mainnet | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` |
| Solana Devnet | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` |
