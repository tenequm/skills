# Compressed Account Model

Compressed accounts store state on Solana's ledger instead of in the AccountsDB, eliminating rent requirements while maintaining security through zero-knowledge proofs.

## Account Structure

### Compressed Account Layout

```rust
pub struct CompressedAccount {
    pub owner: Pubkey,           // Program that owns this account
    pub lamports: u64,           // Lamport balance
    pub address: Option<[u8; 32]>, // Optional persistent address (PDA-like)
    pub data: Option<CompressedAccountData>,
}

pub struct CompressedAccountData {
    pub discriminator: [u8; 8],  // Account type identifier
    pub data: Vec<u8>,           // Serialized account data
    pub data_hash: [u8; 32],     // Poseidon hash of data
}
```

### Comparison with Regular Accounts

| Field | Regular Account | Compressed Account |
|-------|-----------------|-------------------|
| owner | Program ID | Program ID |
| lamports | Balance | Balance |
| data | Raw bytes | Structured with discriminator + hash |
| executable | Boolean | Not applicable |
| rent_epoch | Epoch number | Not applicable |
| **address** | 32-byte pubkey (permanent) | Optional, hash changes on write |

## Account Identification

### Hash-Based Identification

Every compressed account has a unique hash computed from its contents:

```rust
// Hash computation (Poseidon)
hash = poseidon_hash([
    owner,
    lamports,
    address,
    data_hash,
])
```

**Important**: The hash changes on every write operation, so you cannot use the hash as a permanent identifier.

### Address-Based Identification (Optional)

For accounts needing persistent identification (like PDAs), set an address:

```rust
// Derive address (similar to PDA derivation)
let (address, address_seed) = derive_address(
    &[b"my_seed", user.key().as_ref()],
    &address_tree_pubkey,
    &program_id,
);
```

Addresses:
- Are permanent unique identifiers
- Cannot be reused after account closure
- Are stored in separate address trees
- Add computational overhead (use only when needed)

## State Trees

### Merkle Tree Structure

Compressed accounts are stored in concurrent Merkle trees:

```
                    Root (on-chain)
                   /              \
                Hash              Hash
               /    \            /    \
            Hash    Hash      Hash    Hash
           /  \    /  \      /  \    /  \
          A1  A2  A3  A4    A5  A6  A7  A8  (account hashes)
```

- Only the root is stored on-chain
- Leaves contain account hashes
- Trees use Poseidon hashing (ZK-friendly)
- Concurrent access supported via versioned roots

### Tree Types

| Tree Type | Purpose | Contents |
|-----------|---------|----------|
| State Tree (V1) | Store account hashes | Compressed account leaves (individual updates) |
| State Tree (V2) | Store account hashes | Compressed account leaves (batched updates, ~70% less CU) |
| Address Tree | Track unique addresses | Address leaves (indexed) |
| Nullifier Queue | Track spent accounts | Nullified account hashes |

V2 batched Merkle trees (mainnet January 2026) batch multiple insertions and verify them with ZK proofs, reducing state root update costs by ~250x. New deployments use V2 trees by default. Tree type is tracked via a `TreeType` enum in the SDK (`StateV1` or `StateV2`); tree selection is handled automatically by SDK helpers like `selectStateTreeInfo()`.

## Account Operations

### Creating Accounts

```rust
use light_sdk::account::LightAccount;

// new_init creates account with only output state (no prior state)
let mut account = LightAccount::<MyAccount>::new_init(
    &program_id,           // Owner program
    Some(address),         // Optional persistent address
    output_state_tree_index, // Which tree to store in
);

// Set initial values
account.owner = signer.key();
account.value = 0;

// Invoke Light System Program to create
LightSystemProgramCpi::new_cpi(CPI_SIGNER, proof)
    .with_light_account(account)?
    .with_new_addresses(&[new_address_params])
    .invoke(cpi_accounts)?;
```

### Reading Accounts

Accounts are read via the compression RPC API:

```typescript
// By address (if set)
const account = await rpc.getCompressedAccount({ address });

// By hash
const account = await rpc.getCompressedAccount({ hash });

// All accounts for owner
const accounts = await rpc.getCompressedAccountsByOwner(owner);
```

### Updating Accounts

```rust
// new_mut creates account with input state (to be consumed) and output state (new)
let mut account = LightAccount::<MyAccount>::new_mut(
    &program_id,
    &account_meta,      // Metadata about existing account
    MyAccount {         // Current state (must match on-chain)
        owner: signer.key(),
        value: current_value,
    },
)?;

// Modify the account
account.value = account.value.checked_add(1).unwrap();

// Invoke to apply changes
LightSystemProgramCpi::new_cpi(CPI_SIGNER, proof)
    .with_light_account(account)?
    .invoke(cpi_accounts)?;
```

### Closing Accounts

```rust
// new_close creates account with only input state (consumed, no output)
let account = LightAccount::<MyAccount>::new_close(
    &program_id,
    &account_meta,
    MyAccount {
        owner: signer.key(),
        value: current_value,
    },
)?;

LightSystemProgramCpi::new_cpi(CPI_SIGNER, proof)
    .with_light_account(account)?
    .invoke(cpi_accounts)?;
```

**Note**: Closed account addresses can be reinitialized. Use `LightAccount::new_empty()` to reconstruct the closed account hash, then optionally chain `LightAccount::new_mut()` to set custom values in the same transaction. See [reinitialize guide](https://www.zkcompression.com/compressed-pdas/guides/how-to-reinitialize-compressed-accounts).

## Account Metadata

When referencing existing accounts, provide metadata:

```rust
pub struct CompressedAccountMeta {
    pub merkle_context: PackedMerkleContext,
    pub leaf_index: u32,
    pub hash: [u8; 32],
}

pub struct PackedMerkleContext {
    pub merkle_tree_pubkey_index: u8,
    pub nullifier_queue_pubkey_index: u8,
    pub leaf_index: u32,
    pub queue_index: Option<QueueIndex>,
}
```

This metadata is fetched from the indexer and included in transactions.

## Hashing with LightHasher

Define hashable account structures:

```rust
use light_sdk::{LightDiscriminator, LightHasher};

#[derive(Clone, Debug, Default, LightDiscriminator, LightHasher)]
pub struct MyAccount {
    #[hash]  // Include in hash computation
    pub owner: Pubkey,
    pub value: u64,  // Not hashed (but still serialized)
}
```

- `#[hash]` marks fields included in the Poseidon hash
- All fields are serialized with Borsh
- Discriminator auto-derived from struct name

## Validity Proofs

### What Proofs Verify

- Account exists as a leaf in specified state tree
- Account hash matches provided data
- Address (if set) exists in address tree
- State transition is valid

### Proof Structure

```rust
pub struct ValidityProof {
    pub a: [u8; 64],      // Groth16 proof element A
    pub b: [u8; 128],     // Groth16 proof element B
    pub c: [u8; 64],      // Groth16 proof element C
}
// Total: 256 bytes (compressed to 128 bytes in transactions)
```

### Fetching Proofs

```typescript
// Get proof for multiple accounts
const proof = await rpc.getValidityProof({
    hashes: [accountHash1, accountHash2],
    newAddresses: [newAddress1], // If creating new addressed accounts
});
```

## Compute Units

| Operation | Approximate CU |
|-----------|---------------|
| Validity proof verification | ~100,000 |
| System program overhead | ~100,000 |
| Per account read/write | ~6,000 |
| Poseidon hash (syscall) | ~1,500 |

**Example**: Transaction with 2 accounts ≈ 212,000 CU

## Trust Assumptions

1. **Data Availability**: At least one node must store raw account data for proof generation
2. **Forester Liveness**: Nullifier queues must be emptied to prevent state tree congestion
3. **Program Upgradeability**: Light System Program is currently upgradeable (will be frozen)

## Best Practices

1. **Use addresses sparingly** - Only when persistent identification needed
2. **Batch operations** - Multiple accounts in one transaction share proof overhead
3. **Cache account state** - Reduce RPC calls by caching recent fetches
4. **Handle hash changes** - Account hashes change on every write; re-fetch after updates
5. **Plan for CU limits** - Account for ~200k CU base + 6k per account
