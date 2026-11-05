# SPL Token Program - Common Patterns and Security

Common SPL Token patterns including escrow, staking, NFT creation, and account freezing. Comprehensive security considerations covering validation, authority checks, and defensive programming. Includes quick reference tables and security checklist.

**For related topics, see:**
- **[tokens-overview.md](tokens-overview.md)** - Token fundamentals and account structures
- **[tokens-operations.md](tokens-operations.md)** - Create, mint, transfer, burn, close operations
- **[tokens-validation.md](tokens-validation.md)** - Account validation patterns
- **[tokens-2022.md](tokens-2022.md)** - Token Extensions Program features

## Table of Contents

1. [Pattern 1: Token Escrow](#pattern-1-token-escrow)
2. [Pattern 2: Token Staking](#pattern-2-token-staking)
3. [Pattern 3: NFT Creation](#pattern-3-nft-creation)
4. [Pattern 4: Freezing and Thawing Accounts](#pattern-4-freezing-and-thawing-accounts)
5. [Security Considerations](#security-considerations)
6. [Summary](#summary)

---

## Pattern 1: Token Escrow

Program holds tokens temporarily on behalf of users.

### Using Anchor

```rust
use anchor_spl::token_interface::{self, TokenAccount, TokenInterface, Transfer};

#[derive(Accounts)]
pub struct InitializeEscrow<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 1,
        seeds = [b"escrow", user.key().as_ref()],
        bump,
    )]
    pub escrow_state: Account<'info, EscrowState>,

    #[account(
        init,
        payer = user,
        token::mint = mint,
        token::authority = escrow_state,
        token::token_program = token_program,
    )]
    pub escrow_token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(mut)]
    pub user_token_account: InterfaceAccount<'info, TokenAccount>,

    pub mint: InterfaceAccount<'info, Mint>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct EscrowState {
    pub user: Pubkey,
    pub amount: u64,
    pub bump: u8,
}

pub fn initialize_escrow(ctx: Context<InitializeEscrow>, amount: u64) -> Result<()> {
    // Transfer tokens to escrow
    token_interface::transfer(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            Transfer {
                from: ctx.accounts.user_token_account.to_account_info(),
                to: ctx.accounts.escrow_token_account.to_account_info(),
                authority: ctx.accounts.user.to_account_info(),
            },
        ),
        amount,
    )?;

    // Save state
    ctx.accounts.escrow_state.user = ctx.accounts.user.key();
    ctx.accounts.escrow_state.amount = amount;
    ctx.accounts.escrow_state.bump = ctx.bumps.escrow_state;

    Ok(())
}

#[derive(Accounts)]
pub struct ReleaseEscrow<'info> {
    #[account(
        mut,
        seeds = [b"escrow", escrow_state.user.as_ref()],
        bump = escrow_state.bump,
        has_one = user,
        close = user,
    )]
    pub escrow_state: Account<'info, EscrowState>,

    #[account(mut)]
    pub escrow_token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(mut)]
    pub recipient_token_account: InterfaceAccount<'info, TokenAccount>,

    pub user: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn release_escrow(ctx: Context<ReleaseEscrow>) -> Result<()> {
    let seeds = &[
        b"escrow",
        ctx.accounts.user.key().as_ref(),
        &[ctx.accounts.escrow_state.bump],
    ];
    let signer_seeds = &[&seeds[..]];

    token_interface::transfer(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            Transfer {
                from: ctx.accounts.escrow_token_account.to_account_info(),
                to: ctx.accounts.recipient_token_account.to_account_info(),
                authority: ctx.accounts.escrow_state.to_account_info(),
            },
        ).with_signer(signer_seeds),
        ctx.accounts.escrow_state.amount,
    )?;

    Ok(())
}
```

### Using Native Rust

```rust
use borsh::{BorshDeserialize, BorshSerialize};
use spl_token::instruction::transfer;

#[derive(BorshSerialize, BorshDeserialize)]
pub struct EscrowState {
    pub user: Pubkey,
    pub amount: u64,
    pub bump: u8,
}

pub fn initialize_escrow(
    program_id: &Pubkey,
    user: &AccountInfo,
    user_token_account: &AccountInfo,
    escrow_token_account: &AccountInfo,
    escrow_state: &AccountInfo,
    amount: u64,
    token_program: &AccountInfo,
) -> ProgramResult {
    // Transfer tokens to escrow
    invoke(
        &transfer(
            &spl_token::ID,
            user_token_account.key,
            escrow_token_account.key,
            user.key,
            &[],
            amount,
        )?,
        &[user_token_account.clone(), escrow_token_account.clone(), user.clone()],
    )?;

    // Save escrow state
    let (pda, bump) = Pubkey::find_program_address(&[b"escrow", user.key.as_ref()], program_id);
    let escrow = EscrowState {
        user: *user.key,
        amount,
        bump,
    };
    escrow.serialize(&mut &mut escrow_state.data.borrow_mut()[..])?;

    Ok(())
}

pub fn release_escrow(
    program_id: &Pubkey,
    escrow_state: &AccountInfo,
    escrow_token_account: &AccountInfo,
    recipient_token_account: &AccountInfo,
    escrow_pda: &AccountInfo,
    amount: u64,
    bump: u8,
    user: &Pubkey,
) -> ProgramResult {
    let signer_seeds: &[&[&[u8]]] = &[&[b"escrow", user.as_ref(), &[bump]]];

    invoke_signed(
        &transfer(
            &spl_token::ID,
            escrow_token_account.key,
            recipient_token_account.key,
            escrow_pda.key,
            &[],
            amount,
        )?,
        &[escrow_token_account.clone(), recipient_token_account.clone(), escrow_pda.clone()],
        signer_seeds,
    )?;

    Ok(())
}
```

---

## Pattern 2: Token Staking

Users lock tokens to earn rewards.

### Using Anchor

```rust
use anchor_spl::token_interface::{self, Mint, TokenAccount, TokenInterface, Transfer};

#[derive(Accounts)]
pub struct StakeTokens<'info> {
    #[account(
        init_if_needed,
        payer = user,
        space = 8 + 32 + 8 + 8 + 1,
        seeds = [b"stake", user.key().as_ref()],
        bump,
    )]
    pub stake_account: Account<'info, StakeAccount>,

    #[account(mut)]
    pub user_token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(
        mut,
        seeds = [b"vault"],
        bump,
    )]
    pub vault_token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct StakeAccount {
    pub user: Pubkey,
    pub amount_staked: u64,
    pub stake_timestamp: i64,
    pub bump: u8,
}

pub fn stake_tokens(ctx: Context<StakeTokens>, amount: u64) -> Result<()> {
    // Transfer tokens to vault
    token_interface::transfer(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            Transfer {
                from: ctx.accounts.user_token_account.to_account_info(),
                to: ctx.accounts.vault_token_account.to_account_info(),
                authority: ctx.accounts.user.to_account_info(),
            },
        ),
        amount,
    )?;

    // Update stake account
    let clock = Clock::get()?;
    ctx.accounts.stake_account.user = ctx.accounts.user.key();
    ctx.accounts.stake_account.amount_staked += amount;
    ctx.accounts.stake_account.stake_timestamp = clock.unix_timestamp;
    ctx.accounts.stake_account.bump = ctx.bumps.stake_account;

    Ok(())
}

#[derive(Accounts)]
pub struct UnstakeTokens<'info> {
    #[account(
        mut,
        seeds = [b"stake", user.key().as_ref()],
        bump = stake_account.bump,
        has_one = user,
    )]
    pub stake_account: Account<'info, StakeAccount>,

    #[account(mut)]
    pub user_token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(
        mut,
        seeds = [b"vault"],
        bump,
    )]
    pub vault_token_account: InterfaceAccount<'info, TokenAccount>,

    /// CHECK: Vault authority PDA
    #[account(
        seeds = [b"vault-authority"],
        bump,
    )]
    pub vault_authority: UncheckedAccount<'info>,

    pub user: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn unstake_tokens(ctx: Context<UnstakeTokens>, amount: u64) -> Result<()> {
    require!(
        ctx.accounts.stake_account.amount_staked >= amount,
        ErrorCode::InsufficientStake
    );

    let seeds = &[
        b"vault-authority",
        &[ctx.bumps.vault_authority],
    ];
    let signer_seeds = &[&seeds[..]];

    // Transfer tokens back to user
    token_interface::transfer(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            Transfer {
                from: ctx.accounts.vault_token_account.to_account_info(),
                to: ctx.accounts.user_token_account.to_account_info(),
                authority: ctx.accounts.vault_authority.to_account_info(),
            },
        ).with_signer(signer_seeds),
        amount,
    )?;

    // Update stake account
    ctx.accounts.stake_account.amount_staked -= amount;

    Ok(())
}
```

---

## Pattern 3: NFT Creation

Minting a non-fungible token (supply = 1, decimals = 0).

### Using Anchor

```rust
use anchor_spl::token_interface::{self, Mint, MintTo, SetAuthority, TokenAccount, TokenInterface};
use anchor_spl::token_interface::spl_token_2022::instruction::AuthorityType;

#[derive(Accounts)]
pub struct CreateNFT<'info> {
    #[account(
        init,
        payer = payer,
        mint::decimals = 0,
        mint::authority = mint_authority,
        mint::token_program = token_program,
    )]
    pub mint: InterfaceAccount<'info, Mint>,

    #[account(
        init,
        payer = payer,
        associated_token::mint = mint,
        associated_token::authority = owner,
        associated_token::token_program = token_program,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    /// CHECK: Owner of the NFT
    pub owner: UncheckedAccount<'info>,

    pub mint_authority: Signer<'info>,

    #[account(mut)]
    pub payer: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
}

pub fn create_nft(ctx: Context<CreateNFT>) -> Result<()> {
    // Mint exactly 1 token
    token_interface::mint_to(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.mint.to_account_info(),
                to: ctx.accounts.token_account.to_account_info(),
                authority: ctx.accounts.mint_authority.to_account_info(),
            },
        ),
        1,
    )?;

    // Remove mint authority to freeze supply
    token_interface::set_authority(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            SetAuthority {
                account_or_mint: ctx.accounts.mint.to_account_info(),
                current_authority: ctx.accounts.mint_authority.to_account_info(),
            },
        ),
        AuthorityType::MintTokens,
        None,
    )?;

    msg!("NFT created: {}", ctx.accounts.mint.key());
    Ok(())
}
```

### Using Native Rust

```rust
use spl_token::instruction::{mint_to, set_authority, AuthorityType};

pub fn create_nft(
    mint: &AccountInfo,
    token_account: &AccountInfo,
    mint_authority: &AccountInfo,
    token_program: &AccountInfo,
) -> ProgramResult {
    // 1. Mint exactly 1 token
    invoke(
        &mint_to(
            &spl_token::ID,
            mint.key,
            token_account.key,
            mint_authority.key,
            &[],
            1,  // Exactly 1 token
        )?,
        &[mint.clone(), token_account.clone(), mint_authority.clone()],
    )?;

    // 2. Remove mint authority (make supply fixed)
    invoke(
        &set_authority(
            &spl_token::ID,
            mint.key,
            None,  // Set to None
            AuthorityType::MintTokens,
            mint_authority.key,
            &[],
        )?,
        &[mint.clone(), mint_authority.clone()],
    )?;

    Ok(())
}
```

---

## Pattern 4: Freezing and Thawing Accounts

### Using Anchor

```rust
use anchor_spl::token_interface::{self, FreezeAccount, Mint, ThawAccount, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct FreezeTokenAccount<'info> {
    #[account(
        mint::freeze_authority = freeze_authority,
    )]
    pub mint: InterfaceAccount<'info, Mint>,

    #[account(mut)]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    pub freeze_authority: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn freeze_account(ctx: Context<FreezeTokenAccount>) -> Result<()> {
    token_interface::freeze_account(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            FreezeAccount {
                account: ctx.accounts.token_account.to_account_info(),
                mint: ctx.accounts.mint.to_account_info(),
                authority: ctx.accounts.freeze_authority.to_account_info(),
            },
        ),
    )?;
    Ok(())
}

pub fn thaw_account(ctx: Context<FreezeTokenAccount>) -> Result<()> {
    token_interface::thaw_account(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            ThawAccount {
                account: ctx.accounts.token_account.to_account_info(),
                mint: ctx.accounts.mint.to_account_info(),
                authority: ctx.accounts.freeze_authority.to_account_info(),
            },
        ),
    )?;
    Ok(())
}
```

### Using Native Rust

```rust
use spl_token::instruction::{freeze_account, thaw_account};

pub fn freeze_token_account(
    token_account: &AccountInfo,
    mint: &AccountInfo,
    freeze_authority: &AccountInfo,
    token_program: &AccountInfo,
) -> ProgramResult {
    invoke(
        &freeze_account(
            token_program.key,
            token_account.key,
            mint.key,
            freeze_authority.key,
            &[],
        )?,
        &[
            token_account.clone(),
            mint.clone(),
            freeze_authority.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}

pub fn thaw_token_account(
    token_account: &AccountInfo,
    mint: &AccountInfo,
    freeze_authority: &AccountInfo,
    token_program: &AccountInfo,
) -> ProgramResult {
    invoke(
        &thaw_account(
            token_program.key,
            token_account.key,
            mint.key,
            freeze_authority.key,
            &[],
        )?,
        &[
            token_account.clone(),
            mint.clone(),
            freeze_authority.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}
```

---

## Security Considerations

### 1. Always Validate Token Accounts

#### Anchor Approach

```rust
#[derive(Accounts)]
pub struct SafeTransfer<'info> {
    #[account(
        mut,
        constraint = source.mint == mint.key() @ ErrorCode::InvalidMint,
        constraint = source.owner == authority.key() @ ErrorCode::InvalidOwner,
    )]
    pub source: InterfaceAccount<'info, TokenAccount>,

    #[account(
        mut,
        constraint = destination.mint == mint.key() @ ErrorCode::InvalidMint,
    )]
    pub destination: InterfaceAccount<'info, TokenAccount>,

    pub mint: InterfaceAccount<'info, Mint>,

    pub authority: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}
```

#### Native Rust Approach

```rust
// ❌ Dangerous - no validation
pub fn unsafe_transfer(
    source: &AccountInfo,
    destination: &AccountInfo,
    authority: &AccountInfo,
) -> ProgramResult {
    // No checks! Attacker can pass any accounts
    invoke(&transfer_instruction, &accounts)?;
    Ok(())
}

// ✅ Safe - validates everything
pub fn safe_transfer(
    source: &AccountInfo,
    destination: &AccountInfo,
    authority: &AccountInfo,
    expected_mint: &Pubkey,
) -> ProgramResult {
    // Validate source
    validate_token_account(source, authority.key, expected_mint)?;

    // Validate destination
    let dest_token = TokenAccount::unpack(&destination.data.borrow())?;
    if dest_token.mint != *expected_mint {
        return Err(ProgramError::InvalidAccountData);
    }

    invoke(&transfer_instruction, &accounts)?;
    Ok(())
}
```

### 2. Check Token Program ID

#### Anchor Approach

```rust
// Anchor automatically validates via Interface type
pub token_program: Interface<'info, TokenInterface>,
```

#### Native Rust Approach

```rust
pub fn validate_token_program(token_program: &AccountInfo) -> ProgramResult {
    if token_program.key != &spl_token::ID && token_program.key != &spl_token_2022::ID {
        msg!("Invalid Token Program");
        return Err(ProgramError::IncorrectProgramId);
    }
    Ok(())
}
```

### 3. Verify Mint Matches

**Attack scenario:** Attacker passes token account for wrong mint.

#### Anchor Approach

```rust
#[account(
    constraint = token_account.mint == expected_mint.key() @ ErrorCode::InvalidMint,
)]
pub token_account: InterfaceAccount<'info, TokenAccount>,
```

#### Native Rust Approach

```rust
// Always verify mint
let source_token = TokenAccount::unpack(&source.data.borrow())?;
let dest_token = TokenAccount::unpack(&dest.data.borrow())?;

if source_token.mint != dest_token.mint {
    msg!("Mint mismatch between source and destination");
    return Err(ProgramError::InvalidAccountData);
}
```

### 4. Authority Checks

#### Anchor Approach

```rust
#[account(
    constraint = token_account.owner == authority.key() @ ErrorCode::Unauthorized,
)]
pub token_account: InterfaceAccount<'info, TokenAccount>,

pub authority: Signer<'info>,  // Automatically validates is_signer
```

#### Native Rust Approach

```rust
// Verify authority matches token account owner
let token_account = TokenAccount::unpack(&token_account_info.data.borrow())?;

if token_account.owner != *authority.key {
    msg!("Authority doesn't own token account");
    return Err(ProgramError::IllegalOwner);
}

// Verify authority signed
if !authority.is_signer {
    msg!("Authority must sign");
    return Err(ProgramError::MissingRequiredSignature);
}
```

### 5. Account State Checks

#### Anchor Approach

```rust
use spl_token::state::AccountState;

pub fn check_not_frozen(ctx: Context<SomeContext>) -> Result<()> {
    let token_account = &ctx.accounts.token_account;

    require!(
        token_account.state == AccountState::Initialized,
        ErrorCode::AccountFrozen
    );

    Ok(())
}
```

#### Native Rust Approach

```rust
let token_account = TokenAccount::unpack(&token_account_info.data.borrow())?;

// Check not frozen
if token_account.state == spl_token::state::AccountState::Frozen {
    msg!("Token account is frozen");
    return Err(ProgramError::InvalidAccountData);
}

// Check initialized
if token_account.state == spl_token::state::AccountState::Uninitialized {
    msg!("Token account not initialized");
    return Err(ProgramError::UninitializedAccount);
}
```

### 6. Use TransferChecked Over Transfer

**Why:** `transfer_checked` validates the mint and decimals, preventing certain attack vectors.

#### Anchor Approach

```rust
// ✅ Preferred - validates mint and decimals
token_interface::transfer_checked(
    cpi_context,
    amount,
    decimals,
)?;

// ❌ Less secure - no mint/decimal validation
token_interface::transfer(
    cpi_context,
    amount,
)?;
```

#### Native Rust Approach

```rust
// ✅ Preferred
invoke(
    &transfer_checked(
        token_program.key,
        source.key,
        mint.key,
        destination.key,
        authority.key,
        &[],
        amount,
        decimals,
    )?,
    &accounts,
)?;

// ❌ Less secure
invoke(
    &transfer(
        token_program.key,
        source.key,
        destination.key,
        authority.key,
        &[],
        amount,
    )?,
    &accounts,
)?;
```

---

## Summary

### Key Takeaways

**Anchor Advantages:**
- Automatic account validation through constraints
- Cleaner, more concise code
- Built-in safety checks
- Type-safe account structures
- Simplified CPI with `CpiContext`

**Native Rust Advantages:**
- Full control over all operations
- No framework overhead
- Explicit validation (can be more transparent)
- Useful for understanding low-level mechanics

### Common Operations Quick Reference

| Operation | Anchor Module | Native Rust Crate |
|-----------|---------------|-------------------|
| Mint tokens | `token_interface::mint_to` | `spl_token::instruction::mint_to` |
| Transfer tokens | `token_interface::transfer` | `spl_token::instruction::transfer` |
| Transfer checked | `token_interface::transfer_checked` | `spl_token::instruction::transfer_checked` |
| Burn tokens | `token_interface::burn` | `spl_token::instruction::burn` |
| Create ATA | `associated_token` constraint | `spl_associated_token_account` |
| Close account | `token_interface::close_account` | `spl_token::instruction::close_account` |
| Freeze account | `token_interface::freeze_account` | `spl_token::instruction::freeze_account` |

### Security Checklist

- ✅ Validate token program ID
- ✅ Verify token account ownership
- ✅ Check mint matches expected
- ✅ Confirm authority is signer
- ✅ Ensure account not frozen
- ✅ Validate ATA derivation if applicable
- ✅ Use `transfer_checked` instead of `transfer`
- ✅ Validate account state (initialized/frozen)
- ✅ Check sufficient balance before operations

### Token Account Sizes

- **Mint account:** 82 bytes
- **Token account:** 165 bytes
- **Token-2022 with extensions:** 82/165 + extension sizes

Token integration is fundamental for DeFi, NFT, and gaming programs on Solana. Whether using Anchor or native Rust, understanding both approaches provides the flexibility to choose the right tool for your use case.
