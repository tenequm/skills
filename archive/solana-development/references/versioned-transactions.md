# Versioned Transactions and Address Lookup Tables

This guide covers Solana's versioned transaction format and Address Lookup Tables (ALTs), which enable programs to work with more accounts per transaction by compressing account references.

## Introduction

### The Account Limit Problem

Solana transactions are transmitted over UDP and must fit within the IPv6 MTU size of 1280 bytes. After accounting for headers, this leaves approximately 1232 bytes for the transaction packet data.

**Legacy transaction constraints:**
- Each account address: 32 bytes
- Signatures and metadata: ~300-400 bytes overhead
- **Result**: Maximum ~35 accounts per transaction

This limitation became problematic as developers needed to compose multiple on-chain programs atomically, especially for complex DeFi operations like multi-hop swaps or protocol interactions.

### The Solution: Versioned Transactions

Versioned transactions introduce a new transaction format that supports **Address Lookup Tables (ALTs)**, allowing accounts to be referenced by 1-byte indices instead of full 32-byte addresses.

**Impact:**
- Legacy (v0 without ALTs): ~35 accounts maximum
- Versioned (v0 with ALTs): **64+ accounts** per transaction
- 31-byte savings per account referenced from an ALT

## Transaction Versions

### Version Format

Solana uses the high bit of the first byte to determine transaction version:

```rust
// Version detection (first byte of transaction)
if first_byte & 0x80 == 0 {
    // Legacy transaction (bit pattern: 0xxxxxxx)
    version = "legacy"
} else {
    // Versioned transaction (bit pattern: 1xxxxxxx)
    // Remove version bit to get actual version number
    version = first_byte & 0x7F  // Currently only version 0 exists
}
```

### Legacy Transactions

**Structure:**
```rust
pub struct LegacyMessage {
    pub header: MessageHeader,
    pub account_keys: Vec<Pubkey>,           // All 32-byte addresses
    pub recent_blockhash: Hash,
    pub instructions: Vec<CompiledInstruction>,
}
```

**Characteristics:**
- No version byte (implicitly version "legacy")
- All accounts must be fully specified (32 bytes each)
- Maximum ~35 accounts due to packet size limits
- Still supported and widely used for simple transactions

### Version 0 Transactions

**Structure:**
```rust
pub struct MessageV0 {
    pub header: MessageHeader,
    pub account_keys: Vec<Pubkey>,           // Directly specified accounts
    pub recent_blockhash: Hash,
    pub instructions: Vec<CompiledInstruction>,
    pub address_table_lookups: Vec<MessageAddressTableLookup>,  // NEW!
}

pub struct MessageAddressTableLookup {
    pub account_key: Pubkey,                 // ALT address (32 bytes)
    pub writable_indexes: Vec<u8>,           // Writable account indices
    pub readonly_indexes: Vec<u8>,           // Readonly account indices
}
```

**Characteristics:**
- Starts with version byte: `0x80` (128 in decimal, version 0)
- Includes `address_table_lookups` field
- Can reference accounts from ALTs using 1-byte indices
- Enables 64+ accounts per transaction

**Transaction size calculation:**
```
Version 0 overhead:
+ 1 byte (version)
+ 1 byte (number of lookup tables)
+ 34 bytes per lookup table (32-byte address + 2 length bytes)
+ 1 byte per account index referenced

Example with 1 ALT referencing 30 accounts:
  1 (version) + 1 (table count) + 34 (table) + 30 (indices) = 66 bytes

Equivalent legacy transaction:
  30 accounts × 32 bytes = 960 bytes

Savings: 960 - 66 = 894 bytes!
```

## Address Lookup Tables (ALTs)

### What Are ALTs?

Address Lookup Tables are **on-chain accounts** that store collections of related addresses. They act as a lookup mechanism to compress account references in transactions.

**Key properties:**
- Managed by the Address Lookup Table Program (`AddressLookupTableProgram`)
- Store up to **256 addresses** (indexed by u8: 0-255)
- Can be created, extended, deactivated, and closed
- Addresses are append-only for security

### ALT Account Structure

```rust
pub struct AddressLookupTable<'a> {
    pub meta: LookupTableMeta,
    pub addresses: Cow<'a, [Pubkey]>,
}

pub struct LookupTableMeta {
    pub deactivation_slot: Slot,           // Slot when deactivated (u64::MAX if active)
    pub last_extended_slot: Slot,          // Last slot when addresses were added
    pub last_extended_slot_start_index: u8, // Index where last extension started
    pub authority: Option<Pubkey>,         // Can add/deactivate (None = immutable)
}
```

**On-chain layout:**
```
Bytes 0-55:   LookupTableMeta (56 bytes)
Bytes 56+:    Raw list of Pubkey addresses (32 bytes each)
```

### Creating Address Lookup Tables

**Step 1: Create the table**

```rust
use solana_sdk::{
    address_lookup_table_account::instruction as alt_instruction,
    instruction::Instruction,
    pubkey::Pubkey,
    signer::Signer,
};

// Get recent slot for table derivation
let recent_slot = rpc_client.get_slot()?;

// Create lookup table instruction
let (create_ix, lookup_table_address) = alt_instruction::create_lookup_table(
    payer.pubkey(),      // Authority
    payer.pubkey(),      // Payer
    recent_slot,         // Recent slot for PDA derivation
);

// The lookup table address is derived deterministically:
// PDA(seeds=[authority, recent_slot], program=AddressLookupTableProgram)
```

**Transaction to create:**
```rust
let create_tx = Transaction::new_signed_with_payer(
    &[create_ix],
    Some(&payer.pubkey()),
    &[&payer],
    recent_blockhash,
);

rpc_client.send_and_confirm_transaction(&create_tx)?;
```

**Important**: Wait for the transaction to be **finalized** before extending or using the table.

**Step 2: Extend the table with addresses**

```rust
// Addresses to add to the lookup table
let addresses_to_add = vec![
    pubkey1,
    pubkey2,
    pubkey3,
    // ... up to ~20 addresses per transaction
];

let extend_ix = alt_instruction::extend_lookup_table(
    lookup_table_address,
    payer.pubkey(),        // Authority
    Some(payer.pubkey()),  // Payer (optional)
    addresses_to_add,
);

let extend_tx = Transaction::new_signed_with_payer(
    &[extend_ix],
    Some(&payer.pubkey()),
    &[&payer],
    recent_blockhash,
);

rpc_client.send_and_confirm_transaction(&extend_tx)?;
```

**Batching strategy:**
- Each extend operation can add approximately **20 addresses** before hitting transaction size limits
- For more addresses, send multiple extend transactions
- Example from TeamRaccoons repo: Batch in chunks of 20

```rust
// Batch extend for large address sets
let batch_size = 20;
for chunk in addresses.chunks(batch_size) {
    let extend_ix = alt_instruction::extend_lookup_table(
        lookup_table_address,
        authority.pubkey(),
        Some(payer.pubkey()),
        chunk.to_vec(),
    );

    // Send transaction...
    rpc_client.send_and_confirm_transaction(&tx)?;
}
```

**Warmup period:**
- Newly added addresses require **1 slot** before they can be used
- Must wait for finalization before using in v0 transactions
- Check `last_extended_slot` to ensure addresses are ready

**Step 3: Fetch the lookup table**

```rust
use solana_client::rpc_client::RpcClient;
use solana_sdk::address_lookup_table_account::AddressLookupTableAccount;

let lookup_table_account = rpc_client
    .get_account(&lookup_table_address)?;

let lookup_table = AddressLookupTableAccount::deserialize(&lookup_table_account.data)?;

// Access addresses
println!("Table contains {} addresses", lookup_table.addresses.len());
for (index, address) in lookup_table.addresses.iter().enumerate() {
    println!("Index {}: {}", index, address);
}
```

### Using ALTs in V0 Transactions

**Build a v0 transaction with ALT:**

```rust
use solana_sdk::{
    message::{v0, VersionedMessage},
    transaction::VersionedTransaction,
    address_lookup_table_account::AddressLookupTableAccount,
};

// 1. Create your instructions (can reference >35 accounts)
let instructions = vec![
    // Your program instructions
];

// 2. Fetch lookup table accounts
let lookup_table_account = rpc_client.get_account(&lookup_table_address)?;
let lookup_table = AddressLookupTableAccount::deserialize(&lookup_table_account.data)?;

// 3. Build v0 message
let v0_message = v0::Message::try_compile(
    &payer.pubkey(),
    &instructions,
    &[lookup_table],    // Pass lookup tables here
    recent_blockhash,
)?;

// 4. Create versioned transaction
let versioned_tx = VersionedTransaction::try_new(
    VersionedMessage::V0(v0_message),
    &[&payer],          // Signers
)?;

// 5. Send transaction
let signature = rpc_client.send_and_confirm_transaction(&versioned_tx)?;
```

**How accounts are referenced:**

When you create an instruction with accounts that exist in the ALT:
```rust
use solana_sdk::instruction::{AccountMeta, Instruction};

// These accounts are in the lookup table at indices 0, 1, 2
let account_in_alt_0 = Pubkey::new_unique();
let account_in_alt_1 = Pubkey::new_unique();
let account_in_alt_2 = Pubkey::new_unique();

let ix = Instruction::new_with_bytes(
    program_id,
    &instruction_data,
    vec![
        AccountMeta::new(account_in_alt_0, false),      // Index 0 in ALT
        AccountMeta::new_readonly(account_in_alt_1, false),  // Index 1
        AccountMeta::new(account_in_alt_2, false),      // Index 2
    ],
);

// When compiled with ALT, these become 1-byte indices instead of 32-byte addresses
```

### Deactivating and Closing ALTs

**Deactivation:**

```rust
let deactivate_ix = alt_instruction::deactivate_lookup_table(
    lookup_table_address,
    authority.pubkey(),
);

rpc_client.send_and_confirm_transaction(&tx)?;
```

**Why deactivate?**
- Prevents the table from being used in new transactions
- Required before closing
- Creates a safety cooldown period

**Cooldown period:**
- Must wait until the deactivation slot exits the slot hashes sysvar (~2.5 days on mainnet)
- Prevents same-slot recreation attacks
- Ensures no in-flight transactions reference the table

**Closing:**

```rust
let close_ix = alt_instruction::close_lookup_table(
    lookup_table_address,
    authority.pubkey(),
    recipient.pubkey(),  // Receives reclaimed rent
);

rpc_client.send_and_confirm_transaction(&tx)?;
```

**Requirements:**
- Table must be deactivated first
- Deactivation slot must have exited slot hashes sysvar
- Only authority can close
- Rent is returned to specified recipient

### Freezing ALTs (Making Immutable)

```rust
let freeze_ix = alt_instruction::freeze_lookup_table(
    lookup_table_address,
    authority.pubkey(),
);

rpc_client.send_and_confirm_transaction(&tx)?;
```

**Effect:**
- Sets authority to `None`
- Table becomes **permanently immutable**
- Cannot add more addresses
- Cannot deactivate or close
- Useful for protocol-level tables that should never change

## RPC Configuration for V0 Transactions

**Critical requirement**: When fetching transactions, you must specify support for versioned transactions:

```rust
use solana_client::rpc_config::RpcTransactionConfig;
use solana_transaction_status::UiTransactionEncoding;

let config = RpcTransactionConfig {
    encoding: Some(UiTransactionEncoding::Json),
    commitment: Some(CommitmentConfig::confirmed()),
    max_supported_transaction_version: Some(0),  // REQUIRED!
};

let tx = rpc_client.get_transaction_with_config(&signature, config)?;
```

**Without `max_supported_transaction_version: Some(0)`:**
- RPC calls will **fail** if they encounter a v0 transaction
- Error: "Transaction version is not supported"
- This affects: `getTransaction`, `getBlock`, `getSignaturesForAddress`, etc.

**For account subscriptions:**
```rust
use solana_client::rpc_config::RpcAccountInfoConfig;

let config = RpcAccountInfoConfig {
    encoding: Some(UiAccountEncoding::JsonParsed),
    commitment: Some(CommitmentConfig::confirmed()),
    // No max_supported_transaction_version needed for account queries
};
```

## Limitations and Constraints

### Hard Limits

1. **256 addresses per table** (u8 index limit)
   - Tables use 1-byte indices
   - Cannot store more than 256 addresses
   - Create multiple tables if needed

2. **256 unique accounts total per transaction**
   - Solana runtime limit
   - Includes both direct accounts and ALT references
   - Accounts can appear multiple times in instructions

3. **~20 addresses per extend operation**
   - Limited by transaction size
   - Must batch large address sets

4. **Transaction signers cannot be in ALTs**
   - All signers must be explicitly listed in the transaction
   - Cannot reference signer accounts from lookup tables
   - This is a security feature

5. **No recursive lookups**
   - Cannot reference another ALT from within an ALT
   - Cannot store ALT addresses in an ALT

### Security Constraints

1. **Append-only design**
   - Addresses cannot be removed or modified
   - Prevents front-running attacks
   - Once added, addresses are permanent (until table is closed)

2. **Warmup requirement**
   - New addresses need 1 slot before use
   - Prevents same-slot manipulation
   - Must wait for finalization

3. **Deactivation cooldown**
   - Tables cannot be closed immediately after deactivation
   - Must wait for slot to exit slot hashes sysvar
   - Protects in-flight transactions

4. **Authority control**
   - Only authority can extend or deactivate
   - Set to `None` to make immutable
   - Cannot change authority after freezing

### Hardware Wallet Limitations

**Issue**: Hardware wallets cannot verify accounts referenced from ALTs

**Why:**
- Hardware wallets display all transaction accounts for user verification
- They don't have access to fetch lookup table data on-chain
- Cannot show which addresses the indices reference

**Implications:**
- Users must trust that the correct lookup table is being used
- Phishing risk: Malicious apps could use attacker-controlled ALTs
- Hardware wallet UX shows: "This transaction uses address lookup tables"

**Mitigations:**
- Use well-known, immutable (frozen) ALTs when possible
- Publish ALT addresses in protocol documentation
- Verify ALT contents before use in client code
- Consider adding integrity check instructions

## Security Best Practices

### 1. Wait for Finalization

```rust
// BAD: Using immediately after creation
let (create_ix, alt_address) = alt_instruction::create_lookup_table(...);
rpc_client.send_transaction(&create_tx)?;  // Not confirmed!
let extend_ix = alt_instruction::extend_lookup_table(alt_address, ...);  // FAILS!

// GOOD: Wait for finalization
rpc_client.send_and_confirm_transaction_with_spinner(&create_tx)?;
// Now safe to extend

rpc_client.send_and_confirm_transaction_with_spinner(&extend_tx)?;
// Now safe to use in v0 transactions
```

### 2. Verify Lookup Table Contents

```rust
// Fetch and verify before use
let lookup_table = rpc_client.get_account(&alt_address)?;
let alt = AddressLookupTableAccount::deserialize(&lookup_table.data)?;

// Verify expected addresses
assert_eq!(alt.addresses.len(), expected_count);
assert_eq!(alt.addresses[0], expected_address_0);

// Check authority if relevant
if let Some(authority) = alt.meta.authority {
    assert_eq!(authority, expected_authority);
}
```

### 3. Add Integrity Check Instructions

For critical operations, add an instruction that verifies the lookup table contents:

```rust
// Your program instruction
pub fn verify_lookup_table(
    ctx: Context<VerifyLookupTable>,
    expected_addresses: Vec<Pubkey>,
) -> Result<()> {
    let lookup_table = &ctx.accounts.lookup_table;

    // Verify table contains expected addresses
    for (i, expected) in expected_addresses.iter().enumerate() {
        require_keys_eq!(
            lookup_table.addresses[i],
            *expected,
            ErrorCode::InvalidLookupTable
        );
    }

    Ok(())
}
```

### 4. Use Immutable Tables for Protocols

```rust
// After fully populating a protocol-level table
let freeze_ix = alt_instruction::freeze_lookup_table(
    protocol_alt_address,
    authority.pubkey(),
);

rpc_client.send_and_confirm_transaction(&freeze_tx)?;

// Now the table is permanently immutable
// Users can trust it won't change
```

### 5. Front-Running Prevention

**Why ALTs are append-only:**

```rust
// If removal were allowed, this attack would be possible:
// 1. User submits swap transaction using ALT at index 5
// 2. Attacker sees pending transaction
// 3. Attacker removes legitimate address, adds malicious address at index 5
// 4. User's transaction executes with malicious address

// Append-only design prevents this:
// - Addresses cannot be removed
// - Indices remain stable
// - Order cannot change
```

## Code Examples

### Complete Example: Multi-Swap with ALT

Based on the TeamRaccoons address-lookup-table-multi-swap example:

```rust
use solana_client::rpc_client::RpcClient;
use solana_sdk::{
    address_lookup_table_account::instruction as alt_instruction,
    address_lookup_table_account::AddressLookupTableAccount,
    commitment_config::CommitmentConfig,
    instruction::Instruction,
    message::{v0, VersionedMessage},
    pubkey::Pubkey,
    signature::{Keypair, Signer},
    transaction::{Transaction, VersionedTransaction},
};

fn create_and_use_alt_for_swaps() -> Result<()> {
    let rpc_client = RpcClient::new_with_commitment(
        "https://api.devnet.solana.com".to_string(),
        CommitmentConfig::confirmed(),
    );

    let payer = Keypair::new();
    // Fund payer...

    // Step 1: Collect all accounts needed for swap chain
    let swap_accounts = vec![
        token_program_id,
        associated_token_program_id,
        swap_program_1,
        pool_1_address,
        pool_1_authority,
        pool_1_token_a,
        pool_1_token_b,
        swap_program_2,
        pool_2_address,
        pool_2_authority,
        pool_2_token_a,
        pool_2_token_b,
        // ... many more accounts
    ];

    // Step 2: Create lookup table
    let recent_slot = rpc_client.get_slot()?;
    let (create_ix, alt_address) = alt_instruction::create_lookup_table(
        payer.pubkey(),
        payer.pubkey(),
        recent_slot,
    );

    let recent_blockhash = rpc_client.get_latest_blockhash()?;
    let create_tx = Transaction::new_signed_with_payer(
        &[create_ix],
        Some(&payer.pubkey()),
        &[&payer],
        recent_blockhash,
    );

    rpc_client.send_and_confirm_transaction_with_spinner(&create_tx)?;
    println!("Created ALT at {}", alt_address);

    // Step 3: Extend in batches of 20
    for (batch_num, chunk) in swap_accounts.chunks(20).enumerate() {
        let extend_ix = alt_instruction::extend_lookup_table(
            alt_address,
            payer.pubkey(),
            Some(payer.pubkey()),
            chunk.to_vec(),
        );

        let recent_blockhash = rpc_client.get_latest_blockhash()?;
        let extend_tx = Transaction::new_signed_with_payer(
            &[extend_ix],
            Some(&payer.pubkey()),
            &[&payer],
            recent_blockhash,
        );

        rpc_client.send_and_confirm_transaction_with_spinner(&extend_tx)?;
        println!("Extended ALT batch {}", batch_num);
    }

    // Step 4: Fetch the populated lookup table
    let alt_account = rpc_client.get_account(&alt_address)?;
    let lookup_table = AddressLookupTableAccount::deserialize(&alt_account.data)?;

    println!("ALT contains {} addresses", lookup_table.addresses.len());

    // Step 5: Build multi-swap transaction using ALT
    let swap_instructions = vec![
        create_swap_instruction(0, 1, 2, 3, 4, 5, 6),   // Indices into ALT
        create_swap_instruction(7, 8, 9, 10, 11, 12, 13),
        create_swap_instruction(14, 15, 16, 17, 18, 19, 20),
        // Many more swaps...
    ];

    let recent_blockhash = rpc_client.get_latest_blockhash()?;
    let v0_message = v0::Message::try_compile(
        &payer.pubkey(),
        &swap_instructions,
        &[lookup_table],
        recent_blockhash,
    )?;

    let versioned_tx = VersionedTransaction::try_new(
        VersionedMessage::V0(v0_message),
        &[&payer],
    )?;

    // Step 6: Send v0 transaction
    let signature = rpc_client.send_and_confirm_transaction(&versioned_tx)?;
    println!("Multi-swap completed: {}", signature);

    Ok(())
}

fn create_swap_instruction(
    swap_program: u8,
    pool: u8,
    authority: u8,
    source: u8,
    dest: u8,
    pool_token_a: u8,
    pool_token_b: u8,
) -> Instruction {
    // Create instruction with account indices
    // These will be resolved from the ALT
    Instruction {
        program_id: /* from ALT index swap_program */,
        accounts: vec![
            AccountMeta::new(/* ALT index pool */, false),
            AccountMeta::new_readonly(/* ALT index authority */, false),
            // ... etc
        ],
        data: /* swap instruction data */,
    }
}
```

### Example: Protocol-Level Immutable ALT

```rust
// Create a permanent lookup table for protocol accounts
fn create_protocol_alt(
    authority: &Keypair,
    protocol_accounts: Vec<Pubkey>,
) -> Result<Pubkey> {
    let rpc_client = RpcClient::new("https://api.mainnet-beta.solana.com");

    // Create table
    let recent_slot = rpc_client.get_slot()?;
    let (create_ix, alt_address) = alt_instruction::create_lookup_table(
        authority.pubkey(),
        authority.pubkey(),
        recent_slot,
    );

    let create_tx = /* ... */;
    rpc_client.send_and_confirm_transaction_with_spinner(&create_tx)?;

    // Extend with all protocol accounts
    for chunk in protocol_accounts.chunks(20) {
        let extend_ix = alt_instruction::extend_lookup_table(
            alt_address,
            authority.pubkey(),
            Some(authority.pubkey()),
            chunk.to_vec(),
        );

        let extend_tx = /* ... */;
        rpc_client.send_and_confirm_transaction_with_spinner(&extend_tx)?;
    }

    // Freeze the table (make immutable)
    let freeze_ix = alt_instruction::freeze_lookup_table(
        alt_address,
        authority.pubkey(),
    );

    let freeze_tx = /* ... */;
    rpc_client.send_and_confirm_transaction_with_spinner(&freeze_tx)?;

    println!("Created immutable protocol ALT at {}", alt_address);

    // Publish this address in documentation
    // Users can trust it won't change

    Ok(alt_address)
}
```

## Troubleshooting

### Common Errors and Solutions

**Error: "Transaction version is not supported"**
```rust
// Problem: RPC not configured for v0 transactions
let tx = rpc_client.get_transaction(&signature)?;  // FAILS

// Solution: Set max_supported_transaction_version
let config = RpcTransactionConfig {
    max_supported_transaction_version: Some(0),
    ..Default::default()
};
let tx = rpc_client.get_transaction_with_config(&signature, config)?;  // Works
```

**Error: "Address lookup table not found"**
```rust
// Problem: Using table before creation is finalized
let (create_ix, alt_address) = alt_instruction::create_lookup_table(...);
rpc_client.send_transaction(&tx)?;  // Sent but not confirmed
let extend_ix = alt_instruction::extend_lookup_table(alt_address, ...);  // FAILS

// Solution: Wait for confirmation
rpc_client.send_and_confirm_transaction_with_spinner(&create_tx)?;
// Now table exists
```

**Error: "Invalid lookup table index"**
```rust
// Problem: Referencing index beyond table size
let lookup_table = /* has 10 addresses */;
let ix = Instruction {
    accounts: vec![
        AccountMeta::new(/* index 15 */, false),  // FAILS - index out of bounds
    ],
    // ...
};

// Solution: Verify table contents and use valid indices
assert!(index < lookup_table.addresses.len());
```

**Error: "Cannot deactivate lookup table"**
```rust
// Problem: Not the authority
let deactivate_ix = alt_instruction::deactivate_lookup_table(
    alt_address,
    wrong_authority.pubkey(),  // Not the actual authority
);

// Solution: Use the correct authority
let alt = AddressLookupTableAccount::deserialize(&account.data)?;
let correct_authority = alt.meta.authority.expect("Table has no authority");
let deactivate_ix = alt_instruction::deactivate_lookup_table(
    alt_address,
    correct_authority,
);
```

**Error: "Cannot close lookup table"**
```rust
// Problem 1: Table not deactivated
let close_ix = alt_instruction::close_lookup_table(...);  // FAILS

// Solution: Deactivate first, then wait
let deactivate_ix = alt_instruction::deactivate_lookup_table(...);
// ... send deactivate transaction ...
// ... wait for cooldown period (~2.5 days mainnet) ...
let close_ix = alt_instruction::close_lookup_table(...);

// Problem 2: Cooldown period not complete
// Solution: Check if deactivation slot has exited slot hashes
let slot_hashes = rpc_client.get_slot_hashes()?;
let oldest_slot = slot_hashes.last().unwrap().0;
if alt.meta.deactivation_slot < oldest_slot {
    // Safe to close
}
```

## Use Cases and Patterns

### 1. DEX Aggregators

**Problem**: Multi-hop swaps require many accounts (pools, authorities, token accounts)

**Solution**: Create ALT with all pool accounts

```rust
// ALT contains:
// [0-19]: Pool 1 accounts (program, pool, authority, tokens, mint, etc.)
// [20-39]: Pool 2 accounts
// [40-59]: Pool 3 accounts
// [60-79]: Common accounts (token program, associated token program, etc.)

// Transaction can now execute 3+ swaps atomically
```

### 2. Complex Protocol Interactions

**Problem**: DeFi protocols compose multiple programs (lending, swapping, staking)

**Solution**: Protocol-specific ALT with all contract addresses

```rust
// Protocol ALT:
// [0]: Program ID
// [1]: Global config account
// [2-10]: Pool addresses
// [11-20]: Oracle addresses
// [21-30]: Treasury accounts
// etc.
```

### 3. NFT Minting/Trading

**Problem**: Minting or trading multiple NFTs requires many metadata accounts

**Solution**: Collection-specific ALT with all related accounts

```rust
// Collection ALT:
// [0]: Candy machine
// [1]: Collection mint
// [2]: Collection metadata
// [3]: Collection master edition
// [4-100]: Individual NFT addresses
```

### 4. Transaction Builder Programs

**Problem**: Building very large transactions (>64 accounts)

**Solution**: Multi-transaction pattern with ALTs

```rust
// Transaction 1: Create and populate ALT
// Transaction 2: Execute main operation using ALT
// Transaction 3: Clean up and close ALT
```

## Best Practices Summary

1. **Always wait for finalization** before using newly created or extended tables
2. **Batch extend operations** in chunks of ~20 addresses
3. **Verify table contents** before use in production
4. **Use immutable tables** for protocol-level accounts
5. **Set max_supported_transaction_version** in all RPC calls
6. **Document ALT addresses** for protocol integrators
7. **Consider hardware wallet UX** - frozen tables are more trustworthy
8. **Add integrity checks** for critical operations
9. **Plan for cooldown** when closing tables
10. **Keep signers explicit** - never try to put signers in ALTs

## Program Compatibility

**Important**: Programs are **completely unaware** of whether they were called via legacy or v0 transactions.

From the program's perspective:
- Account references work identically
- No code changes needed
- Same `AccountInfo` structures
- Same validation logic

The transaction version only affects:
- How accounts are referenced in the transaction
- Transaction size limits
- Client-side transaction construction

**This means:**
- Existing programs work with v0 transactions without modification
- New programs don't need version-specific logic
- ALTs are purely a client-side optimization

## Resources

### Official Documentation
- [Versioned Transactions Guide](https://solana.com/developers/guides/advanced/versions)
- [Address Lookup Tables Guide](https://solana.com/developers/guides/advanced/lookup-tables)
- [Versioned Transactions Proposal](https://docs.anza.xyz/proposals/versioned-transactions)

### Code Examples
- [TeamRaccoons Multi-Swap Example](https://github.com/TeamRaccoons/address-lookup-table-multi-swap)
- [Solana Program Library - Address Lookup Table](https://github.com/solana-labs/solana-program-library/tree/master/address-lookup-table)

### Technical References
- [AddressLookupTableProgram Source](https://github.com/solana-labs/solana/blob/master/sdk/program/src/address_lookup_table/instruction.rs)
- [solana-sdk VersionedTransaction](https://docs.rs/solana-sdk/latest/solana_sdk/transaction/struct.VersionedTransaction.html)
- [solana-sdk Message v0](https://docs.rs/solana-sdk/latest/solana_sdk/message/v0/struct.Message.html)

### Community Resources
- [Solana Cookbook - Versioned Transactions](https://solanacookbook.com/references/basic-transactions.html#versioned-transactions)
- [Solana Stack Exchange - ALT Questions](https://solana.stackexchange.com/questions/tagged/address-lookup-table)
