# SPL Token Program - Validation Patterns

Validation patterns for SPL Token accounts including ownership verification, mint validation, ATA address derivation checks, and balance verification. Covers both Anchor constraint-based and Native Rust manual validation approaches.

**For related topics, see:**
- **[tokens-overview.md](tokens-overview.md)** - Token fundamentals and account structures
- **[tokens-operations.md](tokens-operations.md)** - Create, mint, transfer, burn, close operations
- **[tokens-2022.md](tokens-2022.md)** - Token Extensions Program features
- **[tokens-patterns.md](tokens-patterns.md)** - Common patterns and security

## Table of Contents

1. [Validate Token Account Ownership and Mint](#validate-token-account-ownership-and-mint)
2. [Validate ATA Address](#validate-ata-address)
3. [Check Token Balance](#check-token-balance)

---

## Validate Token Account Ownership and Mint

### Using Anchor

```rust
use anchor_spl::token_interface::{TokenAccount, Mint};

#[derive(Accounts)]
pub struct ValidateTokenAccount<'info> {
    #[account(
        constraint = token_account.owner == owner.key() @ ErrorCode::InvalidOwner,
        constraint = token_account.mint == mint.key() @ ErrorCode::InvalidMint,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    pub mint: InterfaceAccount<'info, Mint>,

    /// CHECK: Any account
    pub owner: UncheckedAccount<'info>,
}

pub fn validate_token_account(ctx: Context<ValidateTokenAccount>) -> Result<()> {
    // Validation is automatic via constraints

    // Additional checks if needed
    require!(
        ctx.accounts.token_account.amount >= 100,
        ErrorCode::InsufficientBalance
    );

    Ok(())
}
```

### Using Native Rust

```rust
use spl_token::state::Account as TokenAccount;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    program_pack::Pack,
    pubkey::Pubkey,
};

pub fn validate_token_account(
    token_account_info: &AccountInfo,
    expected_owner: &Pubkey,
    expected_mint: &Pubkey,
) -> ProgramResult {
    // 1. Verify owned by Token Program
    if token_account_info.owner != &spl_token::ID {
        msg!("Account not owned by Token Program");
        return Err(ProgramError::IllegalOwner);
    }

    // 2. Deserialize token account
    let token_account = TokenAccount::unpack(&token_account_info.data.borrow())?;

    // 3. Verify owner
    if token_account.owner != *expected_owner {
        msg!("Token account owner mismatch");
        return Err(ProgramError::IllegalOwner);
    }

    // 4. Verify mint
    if token_account.mint != *expected_mint {
        msg!("Token account mint mismatch");
        return Err(ProgramError::InvalidAccountData);
    }

    // 5. Verify not frozen
    if token_account.state != spl_token::state::AccountState::Initialized {
        msg!("Token account is frozen or uninitialized");
        return Err(ProgramError::InvalidAccountData);
    }

    Ok(())
}
```

---

## Validate ATA Address

### Using Anchor

```rust
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token_interface::{Mint, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct ValidateATA<'info> {
    #[account(
        associated_token::mint = mint,
        associated_token::authority = owner,
        associated_token::token_program = token_program,
    )]
    pub ata: InterfaceAccount<'info, TokenAccount>,

    pub mint: InterfaceAccount<'info, Mint>,

    /// CHECK: Any account
    pub owner: UncheckedAccount<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn validate_ata(ctx: Context<ValidateATA>) -> Result<()> {
    // ATA address is automatically validated by Anchor constraints
    Ok(())
}
```

### Using Native Rust

```rust
use spl_associated_token_account::get_associated_token_address;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
};

pub fn validate_ata(
    ata_info: &AccountInfo,
    wallet: &Pubkey,
    mint: &Pubkey,
) -> ProgramResult {
    // Derive expected ATA address
    let expected_ata = get_associated_token_address(wallet, mint);

    // Validate match
    if expected_ata != *ata_info.key {
        msg!("Invalid ATA address");
        return Err(ProgramError::InvalidAccountData);
    }

    Ok(())
}
```

---

## Check Token Balance

### Using Anchor

```rust
use anchor_spl::token_interface::TokenAccount;

pub fn check_balance(
    ctx: Context<SomeContext>,
    minimum_amount: u64
) -> Result<()> {
    let token_account = &ctx.accounts.token_account;

    require!(
        token_account.amount >= minimum_amount,
        ErrorCode::InsufficientBalance
    );

    Ok(())
}
```

### Using Native Rust

```rust
use spl_token::state::Account as TokenAccount;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    program_pack::Pack,
};

pub fn check_token_balance(
    token_account_info: &AccountInfo,
    minimum_amount: u64,
) -> ProgramResult {
    let token_account = TokenAccount::unpack(&token_account_info.data.borrow())?;

    if token_account.amount < minimum_amount {
        msg!("Insufficient token balance: {} < {}", token_account.amount, minimum_amount);
        return Err(ProgramError::InsufficientFunds);
    }

    Ok(())
}
```

---

## Next Steps

- **Token-2022**: See [tokens-2022.md](tokens-2022.md) for Token Extensions Program features
- **Patterns & Security**: See [tokens-patterns.md](tokens-patterns.md) for common patterns and comprehensive security best practices
