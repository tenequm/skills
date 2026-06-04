# Compressed PDAs

Build Solana programs with compressed Program Derived Addresses (PDAs) for rent-free accounts with persistent identification.

## Overview

| Aspect | Regular PDA | Compressed PDA |
|--------|-------------|----------------|
| 100-byte account | ~1,600,000 lamports | ~15,000 lamports |
| Rent | Required | None |
| Address derivation | `find_program_address` | `derive_address` |
| State updates | In-place mutation | Consume + create new |

## Prerequisites

### Required Versions

- Rust: 1.89.0+
- Solana CLI: 2.3.0+
- Anchor CLI: 0.32.1+
- ZK Compression CLI: latest (`npm install -g @lightprotocol/zk-compression-cli`)
- Node.js: 23.5.0+

### Installation

```bash
# Install ZK compression CLI
npm install -g @lightprotocol/zk-compression-cli

# Initialize new project with compression support
light init my-program
cd my-program
```

## Project Structure

```
my-program/
├── Anchor.toml
├── Cargo.toml
├── programs/
│   └── my-program/
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs
├── tests/
│   └── my-program.ts
└── package.json
```

### Cargo.toml Dependencies

```toml
[dependencies]
anchor-lang = "0.32.1"
light-sdk = "0.22"

[dev-dependencies]
light-program-test = "1.2"
light-client = "0.22"
```

> **Note**: Light Protocol SDK versions change frequently. Check [crates.io](https://crates.io/crates/light-sdk) for the latest compatible versions.

## Program Structure

### Basic Anchor Program with Compression

```rust
#![allow(unexpected_cfgs)]

use anchor_lang::prelude::*;
use light_sdk::{
    account::LightAccount,
    address::v1::derive_address,
    cpi::{v1::CpiAccounts, CpiSigner},
    derive_light_cpi_signer,
    instruction::{account_meta::CompressedAccountMeta, PackedAddressTreeInfo, ValidityProof},
    LightDiscriminator, LightHasher,
};

declare_id!("YourProgramID11111111111111111111111111111");

// Derive CPI signer for Light System Program calls
pub const LIGHT_CPI_SIGNER: CpiSigner =
    derive_light_cpi_signer!("YourProgramID11111111111111111111111111111");

#[program]
pub mod my_program {
    use super::*;
    use light_sdk::cpi::{v1::LightSystemProgramCpi, InvokeLightSystemProgram};

    // Instructions here...
}

// Account context (minimal for compressed accounts)
#[derive(Accounts)]
pub struct MyAccounts<'info> {
    #[account(mut)]
    pub signer: Signer<'info>,
}

// Compressed account data structure
#[event]
#[derive(Clone, Debug, Default, LightDiscriminator, LightHasher)]
pub struct MyAccount {
    #[hash]
    pub owner: Pubkey,
    pub data: u64,
}
```

## Creating Compressed PDAs

### Create Instruction

```rust
pub fn create_account<'info>(
    ctx: Context<'_, '_, '_, 'info, MyAccounts<'info>>,
    proof: ValidityProof,
    address_tree_info: PackedAddressTreeInfo,
    output_state_tree_index: u8,
) -> Result<()> {
    // 1. Setup CPI accounts from remaining_accounts
    let light_cpi_accounts = CpiAccounts::new(
        ctx.accounts.signer.as_ref(),
        ctx.remaining_accounts,
        crate::LIGHT_CPI_SIGNER,
    );

    // 2. Derive the compressed PDA address
    let (address, address_seed) = derive_address(
        &[b"my_account", ctx.accounts.signer.key().as_ref()],
        &address_tree_info
            .get_tree_pubkey(&light_cpi_accounts)
            .map_err(|_| ErrorCode::AccountNotEnoughKeys)?,
        &crate::ID,
    );

    // 3. Prepare address params for new address creation
    let new_address_params = address_tree_info.into_new_address_params_packed(address_seed);

    // 4. Create the compressed account
    let mut account = LightAccount::<MyAccount>::new_init(
        &crate::ID,
        Some(address),
        output_state_tree_index,
    );

    // 5. Initialize account data
    account.owner = ctx.accounts.signer.key();
    account.data = 0;

    // 6. Invoke Light System Program
    LightSystemProgramCpi::new_cpi(LIGHT_CPI_SIGNER, proof)
        .with_light_account(account)?
        .with_new_addresses(&[new_address_params])
        .invoke(light_cpi_accounts)?;

    Ok(())
}
```

### Address Derivation

```rust
use light_sdk::address::v1::derive_address;

// Seeds work like regular PDAs
let (address, address_seed) = derive_address(
    &[
        b"my_prefix",           // Static seed
        user.key().as_ref(),   // Dynamic seed
        &[counter],            // Additional data
    ],
    &address_tree_pubkey,      // Address tree (from CPI accounts)
    &program_id,               // Your program ID
);
```

## Updating Compressed Accounts

### Update Instruction

```rust
pub fn update_account<'info>(
    ctx: Context<'_, '_, '_, 'info, MyAccounts<'info>>,
    proof: ValidityProof,
    // Current state must be provided (fetched from indexer)
    current_data: u64,
    account_meta: CompressedAccountMeta,
) -> Result<()> {
    // 1. Create mutable account (consumes input, creates output)
    let mut account = LightAccount::<MyAccount>::new_mut(
        &crate::ID,
        &account_meta,
        MyAccount {
            owner: ctx.accounts.signer.key(),
            data: current_data,
        },
    )?;

    // 2. Validate ownership
    require!(
        account.owner == ctx.accounts.signer.key(),
        CustomError::Unauthorized
    );

    // 3. Modify state
    account.data = account.data.checked_add(1).ok_or(CustomError::Overflow)?;

    // 4. Setup CPI and invoke
    let light_cpi_accounts = CpiAccounts::new(
        ctx.accounts.signer.as_ref(),
        ctx.remaining_accounts,
        crate::LIGHT_CPI_SIGNER,
    );

    LightSystemProgramCpi::new_cpi(LIGHT_CPI_SIGNER, proof)
        .with_light_account(account)?
        .invoke(light_cpi_accounts)?;

    Ok(())
}
```

## Closing Compressed Accounts

### Close Instruction

```rust
pub fn close_account<'info>(
    ctx: Context<'_, '_, '_, 'info, MyAccounts<'info>>,
    proof: ValidityProof,
    current_data: u64,
    account_meta: CompressedAccountMeta,
) -> Result<()> {
    // new_close only has input state (no output created)
    let account = LightAccount::<MyAccount>::new_close(
        &crate::ID,
        &account_meta,
        MyAccount {
            owner: ctx.accounts.signer.key(),
            data: current_data,
        },
    )?;

    require!(
        account.owner == ctx.accounts.signer.key(),
        CustomError::Unauthorized
    );

    let light_cpi_accounts = CpiAccounts::new(
        ctx.accounts.signer.as_ref(),
        ctx.remaining_accounts,
        crate::LIGHT_CPI_SIGNER,
    );

    LightSystemProgramCpi::new_cpi(LIGHT_CPI_SIGNER, proof)
        .with_light_account(account)?
        .invoke(light_cpi_accounts)?;

    Ok(())
}
```

**Important**: Closed account addresses can be reinitialized. Use `LightAccount::new_empty()` to reconstruct the closed account hash, then optionally chain `LightAccount::new_mut()` to set custom values in the same transaction. See [reinitialize guide](https://www.zkcompression.com/compressed-pdas/guides/how-to-reinitialize-compressed-accounts).

## Account Data Structures

### Defining Hashable Structs

```rust
use light_sdk::{LightDiscriminator, LightHasher};

#[event]  // Makes struct available in IDL
#[derive(Clone, Debug, Default, LightDiscriminator, LightHasher)]
pub struct GamePlayer {
    #[hash]
    pub wallet: Pubkey,     // Included in hash
    #[hash]
    pub game_id: [u8; 32],  // Included in hash
    pub score: u64,         // Not hashed (but serialized)
    pub level: u8,          // Not hashed (but serialized)
}
```

### Hash Attribute

- `#[hash]` marks fields for Poseidon hash computation
- All fields are Borsh serialized regardless of hash attribute
- Hash determines account identity; hashed fields should be immutable or tracked carefully

## Multiple Accounts in One Transaction

```rust
pub fn batch_create<'info>(
    ctx: Context<'_, '_, '_, 'info, MyAccounts<'info>>,
    proof: ValidityProof,
    address_tree_infos: Vec<PackedAddressTreeInfo>,
    output_state_tree_index: u8,
    count: u8,
) -> Result<()> {
    let light_cpi_accounts = CpiAccounts::new(
        ctx.accounts.signer.as_ref(),
        ctx.remaining_accounts,
        crate::LIGHT_CPI_SIGNER,
    );

    let mut accounts = Vec::new();
    let mut address_params = Vec::new();

    for i in 0..count {
        let (address, seed) = derive_address(
            &[b"batch", &[i]],
            &address_tree_infos[i as usize].get_tree_pubkey(&light_cpi_accounts)?,
            &crate::ID,
        );

        address_params.push(
            address_tree_infos[i as usize].into_new_address_params_packed(seed)
        );

        let mut account = LightAccount::<MyAccount>::new_init(
            &crate::ID,
            Some(address),
            output_state_tree_index,
        );
        account.owner = ctx.accounts.signer.key();
        account.data = i as u64;
        accounts.push(account);
    }

    let mut cpi = LightSystemProgramCpi::new_cpi(LIGHT_CPI_SIGNER, proof)
        .with_new_addresses(&address_params);

    for account in accounts {
        cpi = cpi.with_light_account(account)?;
    }

    cpi.invoke(light_cpi_accounts)?;

    Ok(())
}
```

## Testing

### Unit Tests with light-program-test

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use light_program_test::{LightProgramTest, TestRpc};

    #[tokio::test]
    async fn test_create_account() {
        let mut test = LightProgramTest::new(&[("my_program", crate::ID)]).await;
        let rpc = test.rpc();

        // Create account
        let result = test.create_compressed_account(
            &crate::ID,
            &[b"test"],
        ).await;

        assert!(result.is_ok());
    }
}
```

### Integration Tests (TypeScript)

> Light Protocol SDK uses `@solana/web3.js` v1 types. For non-Light client code, use [`@solana/kit`](https://solanakit.org).

```typescript
import { createRpc } from '@lightprotocol/stateless.js';
import { Keypair } from '@solana/web3.js'; // Required by Light SDK

describe('My Program', () => {
    const rpc = createRpc();

    it('creates compressed account', async () => {
        const payer = Keypair.generate();
        await rpc.requestAirdrop(payer.publicKey, 1000000000);

        // Build and send transaction
        // ...
    });
});
```

## Build and Deploy

```bash
# Build program
anchor build

# Run tests
cargo test-sbf

# Deploy to devnet
anchor deploy --provider.cluster devnet
```

## Common Patterns

### Read-Only Access

For instructions that only read compressed accounts without modifying:

```rust
pub fn read_account<'info>(
    ctx: Context<'_, '_, '_, 'info, MyAccounts<'info>>,
    proof: ValidityProof,
    account_data: MyAccount,
    account_meta: CompressedAccountMeta,
) -> Result<()> {
    // Validate the account exists with this data
    let account = LightAccount::<MyAccount>::new_mut(
        &crate::ID,
        &account_meta,
        account_data,
    )?;

    // Read-only logic
    msg!("Account data: {}", account.data);

    // Re-create same state (no modification)
    let light_cpi_accounts = CpiAccounts::new(
        ctx.accounts.signer.as_ref(),
        ctx.remaining_accounts,
        crate::LIGHT_CPI_SIGNER,
    );

    LightSystemProgramCpi::new_cpi(LIGHT_CPI_SIGNER, proof)
        .with_light_account(account)?
        .invoke(light_cpi_accounts)?;

    Ok(())
}
```

### CPI Between Programs

```rust
// Call another program that uses compressed accounts
pub fn cpi_example<'info>(
    ctx: Context<'_, '_, '_, 'info, CpiAccounts<'info>>,
    // ... params
) -> Result<()> {
    // Build CPI to other program
    // Include Light System Program accounts in remaining_accounts

    Ok(())
}
```

## Error Handling

```rust
#[error_code]
pub enum CustomError {
    #[msg("Unauthorized access")]
    Unauthorized,
    #[msg("Arithmetic overflow")]
    Overflow,
    #[msg("Arithmetic underflow")]
    Underflow,
    #[msg("Invalid account state")]
    InvalidState,
}
```

## Best Practices

1. **Validate ownership** - Always check account owner matches expected signer
2. **Use checked arithmetic** - Prevent overflow/underflow errors
3. **Minimize state size** - Smaller accounts = lower costs
4. **Hash immutable fields** - Fields marked `#[hash]` affect identity
5. **Handle concurrent access** - Account hashes change on every write
6. **Test with real proofs** - Use `light-program-test` for accurate testing
