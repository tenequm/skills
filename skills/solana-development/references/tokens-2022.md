# SPL Token-2022 (Token Extensions Program)

Token Extensions Program (Token-2022) guide covering extension types, setup for both Anchor and Native Rust, and practical examples including transfer hooks. Includes extension configuration, space calculation, and initialization patterns.

**For related topics, see:**
- **[tokens-overview.md](tokens-overview.md)** - Token fundamentals and account structures
- **[tokens-operations.md](tokens-operations.md)** - Create, mint, transfer, burn, close operations
- **[tokens-validation.md](tokens-validation.md)** - Account validation patterns
- **[tokens-patterns.md](tokens-patterns.md)** - Common patterns and security

## Table of Contents

1. [What are Token Extensions?](#what-are-token-extensions)
2. [Available Extensions](#available-extensions)
3. [Using Token-2022 in Anchor](#using-token-2022-in-anchor)
4. [Using Token-2022 in Native Rust](#using-token-2022-in-native-rust)
5. [Transfer Hook Extension Example](#transfer-hook-extension-example-anchor)

---

## What are Token Extensions?

The Token Extensions Program (Token-2022) provides additional features through extensions. Extensions are optional functionality that can be added to a token mint or token account.

**Key Points:**
- Extensions must be enabled during account creation
- Cannot add extensions after creation
- Some extensions are incompatible with each other
- Extensions add state to the `tlv_data` field

---

## Available Extensions

```rust
pub enum ExtensionType {
    TransferFeeConfig,           // Transfer fees
    TransferFeeAmount,           // Withheld fees
    MintCloseAuthority,          // Close mint accounts
    ConfidentialTransferMint,    // Confidential transfers
    DefaultAccountState,         // Default state for new accounts
    ImmutableOwner,              // Cannot change owner
    MemoTransfer,                // Require memos
    NonTransferable,             // Cannot transfer tokens
    InterestBearingConfig,       // Tokens accrue interest
    PermanentDelegate,           // Permanent delegate authority
    TransferHook,                // Custom transfer logic
    MetadataPointer,             // Point to metadata
    TokenMetadata,               // On-chain metadata
    GroupPointer,                // Token groups
    TokenGroup,                  // Group config
    GroupMemberPointer,          // Group membership
    TokenGroupMember,            // Member config
    // ... and more
}
```

---

## Using Token-2022 in Anchor

```rust
use anchor_spl::token_2022::{self, Token2022};
use anchor_spl::token_interface::{Mint, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct CreateToken2022Mint<'info> {
    #[account(
        init,
        payer = payer,
        mint::decimals = 9,
        mint::authority = mint_authority,
        mint::token_program = token_program,
    )]
    pub mint: InterfaceAccount<'info, Mint>,

    /// CHECK: Mint authority
    pub mint_authority: UncheckedAccount<'info>,

    #[account(mut)]
    pub payer: Signer<'info>,

    pub token_program: Program<'info, Token2022>,
    pub system_program: Program<'info, System>,
}
```

**Note:** The `anchor-spl` crate includes the `token_2022_extensions` module for working with extensions, but not all extension instructions are fully implemented yet. You may need to manually implement CPI calls for some extensions.

---

## Using Token-2022 in Native Rust

```rust
use spl_token_2022::{
    extension::ExtensionType,
    instruction::initialize_mint2,
};

pub fn create_token_2022_mint(
    payer: &AccountInfo,
    mint: &AccountInfo,
    mint_authority: &Pubkey,
    decimals: u8,
    extensions: &[ExtensionType],
) -> ProgramResult {
    // Calculate space needed for extensions
    let mut space = 82; // Base mint size
    for extension in extensions {
        space += extension.get_account_len();
    }

    // Create account with proper size
    // ... (similar to regular mint creation)

    // Initialize extensions
    // Each extension has its own initialization instruction

    // Finally initialize mint
    invoke(
        &initialize_mint2(
            &spl_token_2022::ID,
            mint.key,
            mint_authority,
            None,
            decimals,
        )?,
        &[mint.clone()],
    )?;

    Ok(())
}
```

---

## Transfer Hook Extension Example (Anchor)

```rust
use anchor_lang::prelude::*;
use anchor_spl::token_interface::{TokenAccount, TokenInterface};

#[program]
pub mod transfer_hook {
    use super::*;

    #[interface(spl_transfer_hook_interface::execute)]
    pub fn execute_transfer_hook(
        ctx: Context<TransferHook>,
        amount: u64,
    ) -> Result<()> {
        msg!("Transfer hook called! Amount: {}", amount);
        // Custom transfer logic here
        Ok(())
    }
}

#[derive(Accounts)]
pub struct TransferHook<'info> {
    pub source: InterfaceAccount<'info, TokenAccount>,
    pub destination: InterfaceAccount<'info, TokenAccount>,
    /// CHECK: authority
    pub authority: UncheckedAccount<'info>,
}
```

---

## Next Steps

- **Common Patterns**: See [tokens-patterns.md](tokens-patterns.md) for escrow, staking, NFT creation patterns
- **Security**: See [tokens-patterns.md](tokens-patterns.md) for comprehensive security best practices
