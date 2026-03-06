# Compressed Tokens

Compressed tokens are SPL tokens stored as compressed accounts, enabling 5000x cheaper token distribution while maintaining full SPL token compatibility.

## Overview

| Aspect | Regular SPL Token | Compressed Token |
|--------|-------------------|------------------|
| Storage | Token account (~0.002 SOL rent) | Compressed account (no rent) |
| 100 accounts | ~0.2 SOL | ~0.00004 SOL |
| Mint | Standard SPL mint | SPL mint + token pool |
| Transfers | Account-to-account | Consume input, create outputs |

## Setup

### Installation

```bash
npm install @lightprotocol/stateless.js @lightprotocol/compressed-token
```

### Create RPC Connection

```typescript
import { createRpc } from '@lightprotocol/stateless.js';

// Local development
const rpc = createRpc(); // defaults to localhost:8899

// Helius mainnet
const rpc = createRpc('https://mainnet.helius-rpc.com?api-key=YOUR_KEY');

// Helius devnet
const rpc = createRpc('https://devnet.helius-rpc.com?api-key=YOUR_KEY');
```

## Token Operations

### Create Mint with Token Pool

A token pool enables compression for an SPL mint:

```typescript
import { createMint } from '@lightprotocol/compressed-token';

// Creates SPL mint + token pool in one transaction
const { mint, transactionSignature } = await createMint(
    rpc,
    payer,           // Fee payer and mint authority
    payer.publicKey, // Mint authority
    9,               // Decimals
    // Optional: keypair for deterministic mint address
);

console.log('Mint:', mint.toBase58());
```

### Add Token Pool to Existing Mint

```typescript
import { createTokenPool } from '@lightprotocol/compressed-token';

// Add compression support to existing SPL mint
const transactionSignature = await createTokenPool(
    rpc,
    payer,
    existingMint,
);
```

> **Note**: `createTokenPool` is being renamed to `createSplInterface` in newer SDK versions. Both work currently; prefer `createSplInterface` in new code.

### Mint Compressed Tokens

```typescript
import { mintTo } from '@lightprotocol/compressed-token';

// Mint to single recipient
const sig = await mintTo(
    rpc,
    payer,
    mint,
    recipient,        // toPubkey
    mintAuthority,    // Must have mint authority
    1_000_000_000,    // Amount (with decimals)
);

// Mint to multiple recipients
const recipients = [addr1, addr2, addr3];
const amounts = [1_000_000_000, 2_000_000_000, 500_000_000];

const sig = await mintTo(
    rpc,
    payer,
    mint,
    recipients,
    mintAuthority,
    amounts,
);
```

### Transfer Compressed Tokens

```typescript
import { transfer } from '@lightprotocol/compressed-token';

// Basic transfer
const sig = await transfer(
    rpc,
    payer,
    mint,
    amount,
    owner,       // Token owner (keypair)
    recipient,   // Destination address
);
```

**How transfers work**:
1. Input compressed token accounts are consumed (nullified)
2. New output accounts created for recipient and sender (change)
3. Balances recomputed and stored in new accounts

### Query Token Accounts

```typescript
// Get all compressed token accounts for owner
const accounts = await rpc.getCompressedTokenAccountsByOwner(
    owner,
    { mint } // Optional: filter by mint
);

for (const account of accounts.items) {
    console.log('Amount:', account.parsed.amount);
    console.log('Mint:', account.parsed.mint);
    console.log('Owner:', account.parsed.owner);
}

// Get token balances summary
const balances = await rpc.getCompressedTokenBalancesByOwner(owner);
```

### Get Token Account Balance

```typescript
// Get balance for specific compressed token account
const balance = await rpc.getCompressedTokenAccountBalance(accountHash);
```

## Compress/Decompress SPL Tokens

### Compress SPL Tokens

Convert regular SPL token account to compressed:

```typescript
import { compress } from '@lightprotocol/compressed-token';

const sig = await compress(
    rpc,
    payer,
    mint,
    amount,
    owner,           // SPL token account owner
    recipient,       // Compressed token recipient (can be same)
);
```

### Decompress to SPL Tokens

Convert compressed tokens back to regular SPL:

```typescript
import { decompress } from '@lightprotocol/compressed-token';

const sig = await decompress(
    rpc,
    payer,
    mint,
    amount,
    owner,           // Compressed token owner
    recipient,       // SPL token account (or ATA created)
);
```

## Delegate Authority

### Approve Delegate

```typescript
import { approve } from '@lightprotocol/compressed-token';

const sig = await approve(
    rpc,
    payer,
    mint,
    amount,          // Delegated amount
    owner,           // Token owner
    delegate,        // Delegate pubkey
);
```

### Revoke Delegate

```typescript
import { revoke } from '@lightprotocol/compressed-token';

const sig = await revoke(
    rpc,
    payer,
    mint,
    owner,
);
```

### Transfer with Delegate

```typescript
import { transfer } from '@lightprotocol/compressed-token';

// When delegate is transferring on behalf of owner
const sig = await transfer(
    rpc,
    payer,
    mint,
    amount,
    delegate,        // Delegate performing transfer
    recipient,
    owner,           // Original owner (optional, for delegate transfers)
);
```

## Merge Token Accounts

Combine multiple compressed token accounts:

```typescript
import { mergeTokenAccounts } from '@lightprotocol/compressed-token';

// Merge all token accounts for a mint into fewer accounts
const sig = await mergeTokenAccounts(
    rpc,
    payer,
    mint,
    owner,
);
```

**When to merge**:
- Owner has many small token accounts
- Reduce number of inputs needed for transfers
- Simplify account management

## Batch Operations

### Airdrop to Many Recipients

```typescript
import { mintTo } from '@lightprotocol/compressed-token';

// Prepare recipients and amounts
const recipients: PublicKey[] = [];
const amounts: number[] = [];

for (const user of users) {
    recipients.push(user.address);
    amounts.push(airdropAmount);
}

// Batch mint (limited by transaction size)
const BATCH_SIZE = 5; // Adjust based on transaction limits

for (let i = 0; i < recipients.length; i += BATCH_SIZE) {
    const batchRecipients = recipients.slice(i, i + BATCH_SIZE);
    const batchAmounts = amounts.slice(i, i + BATCH_SIZE);

    await mintTo(rpc, payer, mint, batchRecipients, mintAuthority, batchAmounts);
}
```

## Token Pool Info

```typescript
import { getTokenPoolInfos } from '@lightprotocol/compressed-token';

// Get token pool details for a mint
const poolInfo = await getTokenPoolInfos(rpc, mint);

console.log('Pool address:', poolInfo.address);
console.log('Pool token account:', poolInfo.tokenAccount);
```

## Common Errors

### TokenPool not found

```typescript
// Error: TokenPool not found for mint
// Solution: Create token pool first
import { createTokenPool } from '@lightprotocol/compressed-token';
await createTokenPool(rpc, payer, mint);
```

### Insufficient balance

```typescript
// Error: Insufficient balance for transfer
// Check balance before transfer
const accounts = await rpc.getCompressedTokenAccountsByOwner(owner, { mint });
const totalBalance = accounts.items.reduce(
    (sum, acc) => sum + BigInt(acc.parsed.amount),
    0n
);
```

### Array length mismatch

```typescript
// Error: Amount and toPubkey arrays must have same length
// Ensure arrays match
const recipients = [addr1, addr2, addr3];
const amounts = [100, 200, 300]; // Must be same length
```

## Rust SDK (On-Chain Programs)

For programs that need to interact with compressed tokens:

```rust
use light_compressed_token::{
    process_transfer,
    InputTokenDataWithContext,
    PackedTokenTransferOutputData,
};
use light_sdk::instruction::ValidityProof;

// Transfer compressed tokens in your program
pub fn transfer_compressed_tokens(
    ctx: Context<MyContext>,
    inputs: Vec<InputTokenDataWithContext>,
    outputs: Vec<PackedTokenTransferOutputData>,
    proof: ValidityProof,
) -> Result<()> {
    // ... validation logic

    // CPI to compressed token program
    process_transfer(
        ctx.accounts.into(),
        inputs,
        outputs,
        proof,
    )?;

    Ok(())
}
```

## Cost Comparison

| Operation | Regular SPL | Compressed Token |
|-----------|-------------|------------------|
| Create 1 token account | ~0.002 SOL | ~0.000001 SOL |
| Create 1000 accounts | ~2 SOL | ~0.001 SOL |
| Create 1M accounts | ~2000 SOL | ~1 SOL |
| Transfer | ~0.000005 SOL | ~0.00001 SOL |

**Note**: Compressed tokens have higher compute costs (~200k CU per transfer) but much lower state costs.

## Best Practices

1. **Use for distribution** - Ideal for airdrops, rewards, gaming items
2. **Batch mints** - Multiple recipients in one transaction
3. **Merge periodically** - Consolidate accounts for cleaner state
4. **Cache balances** - Reduce RPC calls in UI
5. **Handle multiple accounts** - Users may have multiple compressed accounts for same mint
