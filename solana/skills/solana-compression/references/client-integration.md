# Client Integration

Integrate ZK Compression into TypeScript/JavaScript and Rust applications using Light Protocol SDKs and Helius/Photon RPC.

## TypeScript Setup

### Installation

```bash
npm install @lightprotocol/stateless.js @lightprotocol/compressed-token helius-sdk
```

### RPC Connection

```typescript
import { createRpc, Rpc } from '@lightprotocol/stateless.js';

// Local development (requires light test-validator)
const rpc = createRpc();

// Helius mainnet
const rpc = createRpc('https://mainnet.helius-rpc.com?api-key=YOUR_API_KEY');

// Helius devnet
const rpc = createRpc('https://devnet.helius-rpc.com?api-key=YOUR_API_KEY');

// Custom Photon endpoint
const rpc = createRpc('https://your-photon-instance.com');
```

### Using Helius SDK

```typescript
import { Helius } from 'helius-sdk';

const helius = new Helius('YOUR_API_KEY');

// All ZK compression methods available via helius.zk
const account = await helius.zk.getCompressedAccount({ address });
const accounts = await helius.zk.getCompressedAccountsByOwner(owner);
const tokenAccounts = await helius.zk.getCompressedTokenAccountsByOwner(owner);
```

## RPC Methods Reference

### Account Methods

#### getCompressedAccount

Fetch a single compressed account by address or hash.

```typescript
// By address (for accounts with persistent address)
const account = await rpc.getCompressedAccount({
    address: new PublicKey('...'),
});

// By hash
const account = await rpc.getCompressedAccount({
    hash: '...',  // Base58 encoded hash
});

// Response
interface CompressedAccount {
    hash: string;
    address?: string;
    owner: string;
    lamports: number;
    data?: {
        discriminator: number[];
        data: string;      // Base64 encoded
        dataHash: string;
    };
    leafIndex: number;
    tree: string;
    seq: number;
}
```

#### getCompressedAccountsByOwner

Fetch all compressed accounts owned by a program for a specific owner.

```typescript
const accounts = await rpc.getCompressedAccountsByOwner(
    ownerPubkey,
    {
        cursor?: string,      // Pagination cursor
        limit?: number,       // Max results (default 100)
        dataSlice?: {         // Return partial data
            offset: number,
            length: number,
        },
    }
);

// Response
interface PaginatedResult<T> {
    items: T[];
    cursor?: string;  // For next page
}
```

#### getMultipleCompressedAccounts

Batch fetch multiple accounts.

```typescript
const accounts = await rpc.getMultipleCompressedAccounts({
    addresses: [addr1, addr2],  // Or use hashes
});
```

### Token Methods

#### getCompressedTokenAccountsByOwner

```typescript
const tokenAccounts = await rpc.getCompressedTokenAccountsByOwner(
    owner,
    {
        mint?: PublicKey,  // Filter by mint
        cursor?: string,
        limit?: number,
    }
);

// Response item
interface CompressedTokenAccount {
    parsed: {
        mint: string;
        owner: string;
        amount: string;      // BigInt as string
        delegate?: string;
        state: 'initialized' | 'frozen';
    };
    hash: string;
    // ... account metadata
}
```

#### getCompressedTokenBalancesByOwner

Get aggregated balances across all token accounts.

```typescript
const balances = await rpc.getCompressedTokenBalancesByOwner(owner);

// Response
interface TokenBalance {
    mint: string;
    balance: string;  // Total across all accounts
}
```

#### getCompressedMintTokenHolders

```typescript
const holders = await rpc.getCompressedMintTokenHolders(mint, {
    cursor?: string,
    limit?: number,
});
```

### Proof Methods

#### getValidityProof

Fetch ZK proof for account inclusion.

```typescript
const proof = await rpc.getValidityProof({
    hashes: [hash1, hash2],           // Existing accounts
    newAddresses?: [address1],        // New addresses being created
    newAddressesV2?: [...],           // V2 format addresses
});

// Response
interface ValidityProof {
    compressedProof: {
        a: number[];   // 64 bytes
        b: number[];   // 128 bytes
        c: number[];   // 64 bytes
    };
    roots: string[];
    rootIndices: number[];
    leafIndices: number[];
    leaves: string[];
    merkleTrees: string[];
    nullifierQueues: string[];
    // Address proof data if newAddresses provided
}
```

#### getMultipleCompressedAccountProofs

Get Merkle proofs for multiple accounts.

```typescript
const proofs = await rpc.getMultipleCompressedAccountProofs({
    hashes: [hash1, hash2],
});
```

### Signature Methods

#### getCompressionSignaturesForAccount

```typescript
const signatures = await rpc.getCompressionSignaturesForAccount(
    accountHash,
    {
        cursor?: string,
        limit?: number,
    }
);
```

#### getCompressionSignaturesForOwner

```typescript
const signatures = await rpc.getCompressionSignaturesForOwner(owner);
```

#### getLatestCompressionSignatures

```typescript
const signatures = await rpc.getLatestCompressionSignatures({
    cursor?: string,
    limit?: number,
});
```

### Indexer Health

```typescript
// Check indexer status
const health = await rpc.getIndexerHealth();

// Get current indexed slot
const slot = await rpc.getIndexerSlot();
```

## Building Transactions

### Transaction with Compressed Accounts

> Light Protocol SDK uses `@solana/web3.js` v1 types internally. These imports are required by the SDK - for non-Light client code, use [`@solana/kit`](https://solanakit.org) instead.

```typescript
import {
    createRpc,
    buildAndSignTx,
    sendAndConfirmTx,
} from '@lightprotocol/stateless.js';
import {
    TransactionInstruction,
    PublicKey,
    Keypair,
} from '@solana/web3.js'; // Required by Light SDK

async function executeCompressedTransaction(
    rpc: Rpc,
    payer: Keypair,
    programId: PublicKey,
    accounts: CompressedAccountMeta[],
) {
    // 1. Fetch validity proof
    const hashes = accounts.map(a => a.hash);
    const { compressedProof, ...proofMetadata } = await rpc.getValidityProof({
        hashes,
    });

    // 2. Build instruction with proof and account data
    const instruction = new TransactionInstruction({
        programId,
        keys: [
            { pubkey: payer.publicKey, isSigner: true, isWritable: true },
            // Add Light Protocol accounts from proofMetadata
            ...buildLightAccountMetas(proofMetadata),
        ],
        data: Buffer.from([
            // Your instruction data + serialized proof
        ]),
    });

    // 3. Build and send transaction
    const { blockhash } = await rpc.getLatestBlockhash();
    const tx = buildAndSignTx(
        [instruction],
        payer,
        blockhash,
    );

    const signature = await sendAndConfirmTx(rpc, tx);
    return signature;
}
```

### Using Anchor Client

```typescript
import { Program, AnchorProvider } from '@coral-xyz/anchor';
import { createRpc } from '@lightprotocol/stateless.js';

// Setup
const rpc = createRpc();
const provider = new AnchorProvider(rpc, wallet, {});
const program = new Program(idl, programId, provider);

// Fetch account and proof
const account = await rpc.getCompressedAccount({ address });
const proof = await rpc.getValidityProof({ hashes: [account.hash] });

// Call program instruction
await program.methods
    .updateAccount(
        proof.compressedProof,
        currentValue,
        accountMeta,
    )
    .remainingAccounts([
        // Light Protocol accounts from proof
    ])
    .rpc();
```

## Rust Client

### Setup

```toml
[dependencies]
light-client = "0.22"
solana-sdk = "2.2"
tokio = { version = "1", features = ["full"] }
```

### Usage

```rust
use light_client::{
    rpc::RpcConnection,
    indexer::Indexer,
};
use solana_sdk::pubkey::Pubkey;

#[tokio::main]
async fn main() -> Result<()> {
    // Connect to RPC
    let rpc = RpcConnection::new("https://devnet.helius-rpc.com?api-key=KEY");

    // Fetch compressed accounts
    let accounts = rpc.get_compressed_accounts_by_owner(&owner).await?;

    // Get validity proof
    let hashes: Vec<_> = accounts.iter().map(|a| a.hash).collect();
    let proof = rpc.get_validity_proof(&hashes, &[]).await?;

    // Build and send transaction
    // ...

    Ok(())
}
```

## Error Handling

### Common Errors

```typescript
try {
    const account = await rpc.getCompressedAccount({ address });
} catch (error) {
    if (error.message.includes('Account not found')) {
        // Account doesn't exist or was closed
    } else if (error.message.includes('Invalid proof')) {
        // Proof verification failed - state may have changed
    } else if (error.message.includes('Rate limit')) {
        // Too many requests - implement backoff
    }
}
```

### Retry Logic

```typescript
async function withRetry<T>(
    fn: () => Promise<T>,
    maxRetries = 3,
    delayMs = 1000,
): Promise<T> {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(r => setTimeout(r, delayMs * (i + 1)));
        }
    }
    throw new Error('Max retries exceeded');
}

// Usage
const account = await withRetry(() =>
    rpc.getCompressedAccount({ address })
);
```

## Caching Strategies

### Account Cache

```typescript
class CompressedAccountCache {
    private cache = new Map<string, { account: any; timestamp: number }>();
    private ttl = 5000; // 5 seconds

    async get(rpc: Rpc, address: PublicKey): Promise<CompressedAccount> {
        const key = address.toBase58();
        const cached = this.cache.get(key);

        if (cached && Date.now() - cached.timestamp < this.ttl) {
            return cached.account;
        }

        const account = await rpc.getCompressedAccount({ address });
        this.cache.set(key, { account, timestamp: Date.now() });
        return account;
    }

    invalidate(address: PublicKey) {
        this.cache.delete(address.toBase58());
    }
}
```

### Proof Caching

Proofs should generally NOT be cached because:
- Account state (and thus proofs) can change between transactions
- Proofs include specific Merkle roots that become stale

Instead, always fetch fresh proofs immediately before transaction submission.

## Pagination

```typescript
async function fetchAllAccounts(rpc: Rpc, owner: PublicKey) {
    const allAccounts = [];
    let cursor: string | undefined;

    do {
        const result = await rpc.getCompressedAccountsByOwner(owner, {
            cursor,
            limit: 100,
        });

        allAccounts.push(...result.items);
        cursor = result.cursor;
    } while (cursor);

    return allAccounts;
}
```

## Running Local Photon

For development without Helius:

```bash
# Install Photon
cargo install photon-indexer

# Run against local validator
photon

# Or connect to devnet
photon --rpc-url=https://api.devnet.solana.com
```

Then use `createRpc('http://localhost:8784')` to connect.

## Best Practices

1. **Batch requests** - Use `getMultipleCompressedAccounts` when fetching multiple accounts
2. **Handle state changes** - Account hashes change on write; re-fetch after transactions
3. **Fresh proofs** - Always fetch proofs immediately before transaction submission
4. **Pagination** - Use cursors for large result sets
5. **Error handling** - Implement retries for transient failures
6. **Rate limiting** - Respect RPC rate limits, implement backoff
7. **Caching** - Cache account data briefly, never cache proofs
