# SPL Token Program - Overview and Fundamentals

Overview of SPL Token Program fundamentals including program types, account structures (Mint and Token accounts), and Associated Token Accounts (ATAs) with derivation and creation patterns.

**For additional token topics, see:**
- **[tokens-operations.md](tokens-operations.md)** - Create, mint, transfer, burn, close operations
- **[tokens-validation.md](tokens-validation.md)** - Account validation patterns
- **[tokens-2022.md](tokens-2022.md)** - Token Extensions Program features
- **[tokens-patterns.md](tokens-patterns.md)** - Common patterns and security

## Table of Contents

1. [Token Program Overview](#token-program-overview)
2. [Token Account Structures](#token-account-structures)
3. [Associated Token Accounts](#associated-token-accounts)

---

## Token Program Overview

### SPL Token vs Token-2022

**SPL Token (Original):**
- Program ID: `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`
- Production-ready, stable, widely adopted
- No new features planned
- Use for standard fungible tokens

**Token-2022 (Token Extensions Program):**
- Program ID: `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`
- Backwards-compatible with SPL Token
- Supports extensions (transfer fees, confidential transfers, metadata pointers, etc.)
- Use for advanced token features

### Key Concepts

```
┌─────────────────────────────────────────┐
│ Mint Account                             │
├─────────────────────────────────────────┤
│ - Defines a token type                  │
│ - Controls supply                       │
│ - Has mint authority (can create tokens)│
│ - Has freeze authority (can freeze accts)│
└─────────────────────────────────────────┘
           │
           │ Creates
           ▼
┌─────────────────────────────────────────┐
│ Token Account                            │
├─────────────────────────────────────────┤
│ - Holds token balance                   │
│ - Owned by a wallet or program          │
│ - Associated with specific Mint         │
│ - Can be frozen/delegated               │
└─────────────────────────────────────────┘
```

### Required Dependencies

**For Anchor:**
```toml
[dependencies]
anchor-lang = "0.32.1"
anchor-spl = "0.32.1"

[features]
idl-build = [
    "anchor-lang/idl-build",
    "anchor-spl/idl-build",
]
```

**For Native Rust:**
```toml
[dependencies]
spl-token = "6.0"
spl-associated-token-account = "6.0"
solana-program = "2.1"
```

---

## Token Account Structures

### Mint Account

**Size:** 82 bytes

```rust
pub struct Mint {
    /// Optional authority to mint new tokens (Pubkey or None)
    pub mint_authority: COption<Pubkey>,       // 36 bytes

    /// Total supply of tokens
    pub supply: u64,                           // 8 bytes

    /// Number of decimals (0 for NFTs, typically 6-9 for fungible)
    pub decimals: u8,                          // 1 byte

    /// Is initialized?
    pub is_initialized: bool,                  // 1 byte

    /// Optional authority to freeze token accounts
    pub freeze_authority: COption<Pubkey>,     // 36 bytes
}
```

**COption Format:**
```rust
pub enum COption<T> {
    None,      // Represented as [0, 0, 0, 0, ...]
    Some(T),   // Represented as [1, followed by T bytes]
}
```

### Token Account

**Size:** 165 bytes

```rust
pub struct Account {
    /// The mint associated with this account
    pub mint: Pubkey,                    // 32 bytes

    /// The owner of this account
    pub owner: Pubkey,                   // 32 bytes

    /// The amount of tokens this account holds
    pub amount: u64,                     // 8 bytes

    /// If `delegate` is `Some` then `delegated_amount` represents
    /// the amount authorized by the delegate
    pub delegate: COption<Pubkey>,       // 36 bytes

    /// The account's state
    pub state: AccountState,             // 1 byte

    /// If is_native.is_some, this is a native token, and the value logs the
    /// rent-exempt reserve
    pub is_native: COption<u64>,         // 12 bytes

    /// The amount delegated
    pub delegated_amount: u64,           // 8 bytes

    /// Optional authority to close the account
    pub close_authority: COption<Pubkey>, // 36 bytes
}

pub enum AccountState {
    Uninitialized,
    Initialized,
    Frozen,
}
```

---

## Associated Token Accounts

### What are ATAs?

**Associated Token Accounts (ATAs)** are PDAs that map a wallet address to a token account for a specific mint.

**Derivation:**
```rust
ATA = PDA(
    seeds: [wallet_address, TOKEN_PROGRAM_ID, mint_address],
    program: ASSOCIATED_TOKEN_PROGRAM_ID
)
```

**Benefits:**
- **Deterministic**: Same wallet + mint always produces same ATA
- **Discoverable**: Easy to find a user's token accounts
- **Standard**: All wallets use this convention

**Constants:**
```rust
// Token Program ID
pub const TOKEN_PROGRAM_ID: Pubkey = pubkey!("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA");

// Associated Token Program ID
pub const ASSOCIATED_TOKEN_PROGRAM_ID: Pubkey = pubkey!("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL");
```

### Finding ATA Address

#### Using Anchor

```rust
use anchor_spl::associated_token::get_associated_token_address;

// In client code or tests
let ata_address = get_associated_token_address(
    &wallet_address,
    &mint_address,
);
```

#### Using Native Rust

```rust
use spl_associated_token_account::get_associated_token_address;

// Derive ATA address
let ata_address = get_associated_token_address(
    &wallet_address,
    &mint_address,
);
```

### Creating Associated Token Accounts

#### Using Anchor

```rust
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token_interface::{Mint, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct CreateTokenAccount<'info> {
    #[account(
        init,
        payer = payer,
        associated_token::mint = mint,
        associated_token::authority = owner,
        associated_token::token_program = token_program,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    pub mint: InterfaceAccount<'info, Mint>,

    /// CHECK: Can be any account
    pub owner: UncheckedAccount<'info>,

    #[account(mut)]
    pub payer: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
}

pub fn create_ata(ctx: Context<CreateTokenAccount>) -> Result<()> {
    // ATA is automatically created by Anchor constraints
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_associated_token_account::instruction::create_associated_token_account;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke,
};

pub fn create_ata(
    payer: &AccountInfo,
    wallet: &AccountInfo,
    mint: &AccountInfo,
    ata: &AccountInfo,
    system_program: &AccountInfo,
    token_program: &AccountInfo,
    associated_token_program: &AccountInfo,
) -> ProgramResult {
    invoke(
        &create_associated_token_account(
            payer.key,
            wallet.key,
            mint.key,
            token_program.key,
        ),
        &[
            payer.clone(),
            ata.clone(),
            wallet.clone(),
            mint.clone(),
            system_program.clone(),
            token_program.clone(),
            associated_token_program.clone(),
        ],
    )?

;

    Ok(())
}
```

---

## Next Steps

- **Token Operations**: See [tokens-operations.md](tokens-operations.md) for creating mints, minting, transferring, burning, and closing accounts
- **Validation**: See [tokens-validation.md](tokens-validation.md) for account validation patterns
- **Token-2022**: See [tokens-2022.md](tokens-2022.md) for Token Extensions Program features
- **Patterns & Security**: See [tokens-patterns.md](tokens-patterns.md) for common patterns and security best practices
