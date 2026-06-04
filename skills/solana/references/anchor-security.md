# Anchor Security Reference

This document covers security patterns, vulnerabilities, and best practices specific to the Anchor framework for Solana program development.

## 1. Anchor Constraint Security

### 1.1 Account Constraint Basics

Anchor's `#[account(...)]` constraints provide declarative validation of accounts passed to instructions. Proper use is critical for security.

**Core constraint types:**
- `init` - Initialize a new account
- `mut` - Mark account as mutable
- `has_one` - Verify relationship between accounts
- `seeds` and `bump` - Validate PDA derivation
- `constraint` - Custom validation expressions
- `close` - Close account and return rent
- `realloc` - Resize account data

### 1.2 init vs init_if_needed

**VULNERABLE - Using init_if_needed:**
```rust
#[derive(Accounts)]
pub struct UpdateConfig<'info> {
    #[account(
        init_if_needed,
        payer = authority,
        space = 8 + Config::INIT_SPACE,
        seeds = [b"config"],
        bump
    )]
    pub config: Account<'info, Config>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}
```

**Issue:** `init_if_needed` allows re-initialization attacks. An attacker can close the account in a previous transaction, then re-initialize it with malicious data.

**SECURE - Separate init and update instructions:**
```rust
#[derive(Accounts)]
pub struct InitConfig<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + Config::INIT_SPACE,
        seeds = [b"config"],
        bump
    )]
    pub config: Account<'info, Config>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateConfig<'info> {
    #[account(
        mut,
        seeds = [b"config"],
        bump = config.bump
    )]
    pub config: Account<'info, Config>,
    pub authority: Signer<'info>,
}
```

**When init_if_needed is acceptable:**
- Idempotent operations where re-initialization is safe
- Accounts with no state that matters (pure PDAs used only for signing)
- Always combine with additional constraints to prevent misuse

### 1.3 has_one Constraints for Relationships

**VULNERABLE - Missing has_one check:**
```rust
#[derive(Accounts)]
pub struct WithdrawFunds<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    #[account(mut)]
    pub owner: Signer<'info>,
    #[account(mut)]
    pub destination: SystemAccount<'info>,
}

pub fn withdraw_funds(ctx: Context<WithdrawFunds>, amount: u64) -> Result<()> {
    // Missing validation: anyone can withdraw from any vault!
    transfer_lamports(&ctx.accounts.vault, &ctx.accounts.destination, amount)?;
    Ok(())
}
```

**SECURE - Using has_one:**
```rust
#[account]
pub struct Vault {
    pub owner: Pubkey,
    pub bump: u8,
}

#[derive(Accounts)]
pub struct WithdrawFunds<'info> {
    #[account(
        mut,
        has_one = owner, // Validates vault.owner == owner.key()
        seeds = [b"vault", owner.key().as_ref()],
        bump = vault.bump
    )]
    pub vault: Account<'info, Vault>,
    #[account(mut)]
    pub owner: Signer<'info>,
    #[account(mut)]
    pub destination: SystemAccount<'info>,
}
```

### 1.4 seeds and bump for PDA Validation

**VULNERABLE - Not validating PDA derivation:**
```rust
#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    pub depositor: Signer<'info>,
}
```

**Issue:** Attacker can pass any account as vault, including one they control.

**SECURE - Validate PDA with seeds and bump:**
```rust
#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(
        mut,
        seeds = [b"vault", depositor.key().as_ref()],
        bump = vault.bump
    )]
    pub vault: Account<'info, Vault>,
    pub depositor: Signer<'info>,
}
```

**CRITICAL: Always use canonical bump:**
```rust
#[account]
pub struct Vault {
    pub bump: u8, // Store canonical bump at initialization
}

// At initialization, use:
#[account(
    init,
    payer = payer,
    space = 8 + Vault::INIT_SPACE,
    seeds = [b"vault", authority.key().as_ref()],
    bump // Anchor automatically finds canonical bump
)]
pub vault: Account<'info, Vault>,

// Then store it:
vault.bump = ctx.bumps.vault; // ctx.bumps available in Anchor 0.29+
```

### 1.5 constraint Expressions and Pitfalls

**VULNERABLE - Using constraint without proper checks:**
```rust
#[derive(Accounts)]
pub struct Transfer<'info> {
    #[account(
        mut,
        constraint = from.amount >= amount @ ErrorCode::InsufficientFunds
    )]
    pub from: Account<'info, TokenAccount>,
    #[account(mut)]
    pub to: Account<'info, TokenAccount>,
    pub authority: Signer<'info>,
}
```

**Issue:** Missing check that authority actually owns the from account!

**SECURE - Combine constraints appropriately:**
```rust
#[derive(Accounts)]
pub struct Transfer<'info> {
    #[account(
        mut,
        has_one = authority, // Verify ownership
        constraint = from.amount >= amount @ ErrorCode::InsufficientFunds
    )]
    pub from: Account<'info, TokenAccount>,
    #[account(mut)]
    pub to: Account<'info, TokenAccount>,
    pub authority: Signer<'info>,
}
```

**Constraint expression tips:**
- Use `@` to specify custom error codes
- Constraints execute after account deserialization
- Complex logic should go in instruction handler, not constraints
- Prefer built-in constraints (`has_one`, `seeds`) over custom `constraint`

### 1.6 close Constraint Security

**VULNERABLE - close without proper authorization:**
```rust
#[derive(Accounts)]
pub struct CloseAccount<'info> {
    #[account(
        mut,
        close = destination
    )]
    pub account_to_close: Account<'info, MyAccount>,
    #[account(mut)]
    pub destination: SystemAccount<'info>,
}
```

**Issue:** Anyone can close the account and steal the rent!

**SECURE - Verify authorization before closing:**
```rust
#[derive(Accounts)]
pub struct CloseAccount<'info> {
    #[account(
        mut,
        has_one = authority,
        close = authority // Return rent to authorized party
    )]
    pub account_to_close: Account<'info, MyAccount>,
    #[account(mut)]
    pub authority: Signer<'info>,
}
```

**CRITICAL: close order matters:**
```rust
// WRONG - closes account before using it
#[account(
    close = authority,
    has_one = authority
)]
pub my_account: Account<'info, MyAccount>,

// CORRECT - validates before closing
#[account(
    has_one = authority,
    close = authority
)]
pub my_account: Account<'info, MyAccount>,
```

### 1.7 realloc Security Considerations

**VULNERABLE - realloc without validation:**
```rust
#[derive(Accounts)]
pub struct UpdateData<'info> {
    #[account(
        mut,
        realloc = 8 + 4 + new_data.len(),
        realloc::payer = payer,
        realloc::zero = false
    )]
    pub data_account: Account<'info, DataAccount>,
    #[account(mut)]
    pub payer: Signer<'info>,
}
```

**Issues:**
- No max size check (DoS via huge allocations)
- No authority check (anyone can realloc)
- `zero = false` might leak old data

**SECURE - Proper realloc constraints:**
```rust
#[derive(Accounts)]
pub struct UpdateData<'info> {
    #[account(
        mut,
        has_one = authority,
        realloc = 8 + 4 + new_data.len(),
        realloc::payer = authority,
        realloc::zero = true, // Zero out old data
        constraint = new_data.len() <= MAX_DATA_SIZE @ ErrorCode::DataTooLarge
    )]
    pub data_account: Account<'info, DataAccount>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}
```

## 2. Common Anchor Vulnerabilities

### 2.1 Missing Constraints Leading to Account Substitution

**VULNERABLE - No PDA validation:**
```rust
#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub pool: Account<'info, Pool>,
    #[account(mut)]
    pub user_stake: Account<'info, UserStake>,
    pub user: Signer<'info>,
}
```

**Attack:** User passes a fake `user_stake` account they control with inflated balance.

**SECURE - Validate PDAs:**
```rust
#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(
        mut,
        seeds = [b"pool"],
        bump = pool.bump
    )]
    pub pool: Account<'info, Pool>,
    #[account(
        mut,
        seeds = [b"stake", pool.key().as_ref(), user.key().as_ref()],
        bump = user_stake.bump,
        has_one = user,
        has_one = pool
    )]
    pub user_stake: Account<'info, UserStake>,
    pub user: Signer<'info>,
}
```

### 2.2 Incorrect Constraint Ordering

Anchor evaluates constraints in this order:
1. `init` / `init_if_needed` / `mut` / `close`
2. `seeds` and `bump`
3. `has_one`
4. `constraint`
5. Account deserialization

**Implications:**
- Can't use deserialized data in `seeds`
- `constraint` expressions can use deserialized data
- `close` at end ensures account data available for other checks

### 2.3 Over-Reliance on init_if_needed

Covered in section 1.2. Key takeaway: **Avoid `init_if_needed` unless absolutely necessary.**

### 2.4 Missing mut on Accounts

**VULNERABLE - Missing mut:**
```rust
#[derive(Accounts)]
pub struct Deposit<'info> {
    pub vault: Account<'info, Vault>, // Missing mut!
    pub user: Signer<'info>,
}

pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    ctx.accounts.vault.balance += amount; // Runtime error!
    Ok(())
}
```

**SECURE:**
```rust
#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    pub user: Signer<'info>,
}
```

### 2.5 PDA Bump Not Using Canonical Bump

**VULNERABLE - Using non-canonical bump:**
```rust
pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    let (pda, bump) = Pubkey::find_program_address(
        &[b"vault"],
        ctx.program_id
    );
    // Storing bump separately is fine, but must validate it
    ctx.accounts.vault.bump = bump;
    Ok(())
}

// Later, using wrong bump
#[account(
    seeds = [b"vault"],
    bump = 254 // WRONG - not canonical!
)]
pub vault: Account<'info, Vault>,
```

**SECURE - Always use canonical bump:**
```rust
#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + Vault::INIT_SPACE,
        seeds = [b"vault"],
        bump // Anchor finds canonical bump
    )]
    pub vault: Account<'info, Vault>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    ctx.accounts.vault.bump = ctx.bumps.vault; // Store canonical bump
    Ok(())
}
```

### 2.6 Account Reloading After CPI Mutations

**VULNERABLE - Stale account data after CPI:**
```rust
pub fn compound_rewards(ctx: Context<CompoundRewards>) -> Result<()> {
    // CPI to claim rewards (mutates user_rewards account)
    rewards_program::cpi::claim_rewards(
        CpiContext::new(
            ctx.accounts.rewards_program.to_account_info(),
            ClaimRewards {
                user_rewards: ctx.accounts.user_rewards.to_account_info(),
            }
        )
    )?;

    // WRONG - using stale data!
    let rewards = ctx.accounts.user_rewards.amount;

    // Reinvest...
    Ok(())
}
```

**SECURE - Reload account after CPI:**
```rust
pub fn compound_rewards(ctx: Context<CompoundRewards>) -> Result<()> {
    rewards_program::cpi::claim_rewards(
        CpiContext::new(
            ctx.accounts.rewards_program.to_account_info(),
            ClaimRewards {
                user_rewards: ctx.accounts.user_rewards.to_account_info(),
            }
        )
    )?;

    // Reload account to get fresh data
    ctx.accounts.user_rewards.reload()?;
    let rewards = ctx.accounts.user_rewards.amount;

    // Reinvest...
    Ok(())
}
```

## 3. Anchor CPI Security

### 3.1 Using Program<'info, T> for Program Validation

**VULNERABLE - Using AccountInfo for program:**
```rust
#[derive(Accounts)]
pub struct CallExternal<'info> {
    /// CHECK: This is dangerous!
    pub external_program: AccountInfo<'info>,
}
```

**SECURE - Using Program<'info, T>:**
```rust
#[derive(Accounts)]
pub struct CallExternal<'info> {
    pub external_program: Program<'info, ExternalProgram>,
}
```

`Program<'info, T>` validates:
- Account is executable
- Account owner is BPF Loader
- Account key matches expected program ID

### 3.2 CpiContext Usage Patterns

**Basic CPI:**
```rust
use anchor_lang::prelude::*;
use anchor_spl::token::{self, Transfer};

pub fn transfer_tokens(ctx: Context<TransferTokens>, amount: u64) -> Result<()> {
    let cpi_accounts = Transfer {
        from: ctx.accounts.from.to_account_info(),
        to: ctx.accounts.to.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);

    token::transfer(cpi_ctx, amount)?;
    Ok(())
}
```

### 3.3 with_signer for PDA Signing

**SECURE - PDA signing with CPI:**
```rust
pub fn transfer_from_vault(ctx: Context<TransferFromVault>, amount: u64) -> Result<()> {
    let authority_bump = ctx.accounts.vault.authority_bump;
    let authority_seeds = &[
        b"vault-authority",
        &[authority_bump]
    ];
    let signer_seeds = &[&authority_seeds[..]];

    let cpi_accounts = Transfer {
        from: ctx.accounts.vault_token_account.to_account_info(),
        to: ctx.accounts.destination.to_account_info(),
        authority: ctx.accounts.vault_authority.to_account_info(),
    };

    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_ctx = CpiContext::new_with_signer(
        cpi_program,
        cpi_accounts,
        signer_seeds // PDA can now sign!
    );

    token::transfer(cpi_ctx, amount)?;
    Ok(())
}
```

### 3.4 Validating CPI Return Data

**SECURE - Check CPI return values:**
```rust
pub fn safe_cpi_call(ctx: Context<SafeCpiCall>) -> Result<()> {
    let result = external_program::cpi::risky_operation(
        CpiContext::new(
            ctx.accounts.external_program.to_account_info(),
            RiskyOperation { /* ... */ }
        )
    )?;

    // Validate return data
    require!(
        result.get().success,
        ErrorCode::CpiOperationFailed
    );

    Ok(())
}
```

### 3.5 Avoiding Arbitrary CPI Targets

**VULNERABLE - Arbitrary CPI target:**
```rust
#[derive(Accounts)]
pub struct ArbitraryCpi<'info> {
    /// CHECK: DANGEROUS - allows any program!
    pub target_program: AccountInfo<'info>,
}
```

**SECURE - Constrained CPI targets:**
```rust
#[derive(Accounts)]
pub struct SafeCpi<'info> {
    // Option 1: Type-safe program constraint
    pub token_program: Program<'info, Token>,

    // Option 2: Explicit allowlist
    #[account(
        constraint = allowed_programs.contains(&other_program.key())
            @ ErrorCode::UnauthorizedProgram
    )]
    pub other_program: Program<'info, OtherProgram>,
}
```

## 4. Account Type Safety

### 4.1 Account Discriminators

Anchor automatically adds an 8-byte discriminator to each account type (first 8 bytes of SHA256 hash of `"account:<AccountName>"`).

**How it protects you:**
```rust
#[account]
pub struct Vault {
    pub authority: Pubkey,
    pub balance: u64,
}

#[account]
pub struct UserAccount {
    pub authority: Pubkey,
    pub balance: u64,
}

// Anchor prevents this type confusion:
#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>, // Won't deserialize UserAccount!
}
```

**Manual discriminator handling:**
```rust
impl Vault {
    pub const DISCRIMINATOR: [u8; 8] = [/* computed at compile time */];
}

// Checking discriminator manually
let discriminator = &data[0..8];
require!(
    discriminator == Vault::DISCRIMINATOR,
    ErrorCode::InvalidAccountType
);
```

### 4.2 Account<'info, T> vs AccountInfo

**Account<'info, T>:**
- Type-safe deserialization
- Automatic discriminator check
- Automatic owner check
- Immutable/mutable access control

**AccountInfo:**
- Raw account data
- No automatic validation
- Use only when necessary (non-Anchor programs, dynamic account types)

**VULNERABLE - Using AccountInfo unnecessarily:**
```rust
#[derive(Accounts)]
pub struct UpdateVault<'info> {
    /// CHECK: Missing type safety!
    pub vault: AccountInfo<'info>,
}
```

**SECURE - Use Account<'info, T>:**
```rust
#[derive(Accounts)]
pub struct UpdateVault<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
}
```

### 4.3 AccountLoader for Zero-Copy Accounts

For large accounts (>10KB), use zero-copy deserialization:

```rust
#[account(zero_copy)]
pub struct LargeAccount {
    pub data: [u8; 100000],
}

#[derive(Accounts)]
pub struct UpdateLargeAccount<'info> {
    #[account(mut)]
    pub large_account: AccountLoader<'info, LargeAccount>,
}

pub fn update(ctx: Context<UpdateLargeAccount>) -> Result<()> {
    let mut account = ctx.accounts.large_account.load_mut()?;
    account.data[0] = 42;
    Ok(())
}
```

**Security note:** Zero-copy accounts use `RefCell` internally. Must call `load()` or `load_mut()` each time you access data to ensure safety.

### 4.4 Type Cosplay Prevention

**Attack:** Creating fake accounts with correct discriminator but wrong program owner.

**Anchor's defense:**
```rust
#[account]
#[derive(Default)]
pub struct MyAccount {
    pub data: u64,
}

// Anchor checks:
// 1. Discriminator matches
// 2. Owner is this program's ID
// 3. Account is properly sized
```

**Additional validation for external accounts:**
```rust
#[derive(Accounts)]
pub struct UseExternalAccount<'info> {
    #[account(
        constraint = external_account.owner == &external_program::ID
            @ ErrorCode::InvalidAccountOwner
    )]
    pub external_account: AccountInfo<'info>,
}
```

## 5. Error Handling Security

### 5.1 Custom Error Codes

**Define clear error codes:**
```rust
#[error_code]
pub enum ErrorCode {
    #[msg("Insufficient funds for withdrawal")]
    InsufficientFunds,
    #[msg("Unauthorized access attempt")]
    Unauthorized,
    #[msg("Invalid configuration parameters")]
    InvalidConfig,
    #[msg("Arithmetic overflow occurred")]
    Overflow,
}
```

**Use with require! macro:**
```rust
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    require!(
        ctx.accounts.vault.balance >= amount,
        ErrorCode::InsufficientFunds
    );

    require!(
        ctx.accounts.vault.authority == ctx.accounts.user.key(),
        ErrorCode::Unauthorized
    );

    // Safe to proceed
    Ok(())
}
```

### 5.2 Error Propagation Patterns

**WRONG - Silencing errors:**
```rust
pub fn risky_operation(ctx: Context<RiskyOp>) -> Result<()> {
    let _ = dangerous_function(); // WRONG - error silenced!
    Ok(())
}
```

**CORRECT - Propagate errors:**
```rust
pub fn risky_operation(ctx: Context<RiskyOp>) -> Result<()> {
    dangerous_function()?; // Propagate error
    Ok(())
}
```

### 5.3 Avoiding Silent Failures

**VULNERABLE - No error on failure:**
```rust
pub fn transfer(ctx: Context<Transfer>, amount: u64) -> Result<()> {
    if ctx.accounts.from.balance >= amount {
        ctx.accounts.from.balance -= amount;
        ctx.accounts.to.balance += amount;
    }
    // Returns Ok even if transfer didn't happen!
    Ok(())
}
```

**SECURE - Explicit error:**
```rust
pub fn transfer(ctx: Context<Transfer>, amount: u64) -> Result<()> {
    require!(
        ctx.accounts.from.balance >= amount,
        ErrorCode::InsufficientFunds
    );

    ctx.accounts.from.balance -= amount;
    ctx.accounts.to.balance += amount;
    Ok(())
}
```

## 6. Token Program Integration

### 6.1 anchor_spl Security Patterns

**SECURE - Using anchor_spl helpers:**
```rust
use anchor_spl::token::{self, Token, TokenAccount, Transfer};

#[derive(Accounts)]
pub struct TransferTokens<'info> {
    #[account(mut)]
    pub from: Account<'info, TokenAccount>,
    #[account(mut)]
    pub to: Account<'info, TokenAccount>,
    pub authority: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

pub fn transfer_tokens(ctx: Context<TransferTokens>, amount: u64) -> Result<()> {
    token::transfer(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            Transfer {
                from: ctx.accounts.from.to_account_info(),
                to: ctx.accounts.to.to_account_info(),
                authority: ctx.accounts.authority.to_account_info(),
            },
        ),
        amount,
    )?;
    Ok(())
}
```

### 6.2 token_interface Usage

For Token-2022 compatibility:

```rust
use anchor_spl::token_interface::{self, TokenInterface, TokenAccount};

#[derive(Accounts)]
pub struct TransferTokens<'info> {
    #[account(mut)]
    pub from: InterfaceAccount<'info, TokenAccount>,
    #[account(mut)]
    pub to: InterfaceAccount<'info, TokenAccount>,
    pub authority: Signer<'info>,
    pub token_program: Interface<'info, TokenInterface>,
}
```

### 6.3 Associated Token Account Constraints

**VULNERABLE - Missing ATA validation:**
```rust
#[derive(Accounts)]
pub struct DepositTokens<'info> {
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    pub user: Signer<'info>,
}
```

**SECURE - Validate ATA:**
```rust
use anchor_spl::associated_token::AssociatedToken;

#[derive(Accounts)]
pub struct DepositTokens<'info> {
    #[account(
        mut,
        associated_token::mint = mint,
        associated_token::authority = user
    )]
    pub user_token_account: Account<'info, TokenAccount>,
    pub user: Signer<'info>,
    pub mint: Account<'info, Mint>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
}
```

### 6.4 Token-2022 Extension Handling

**Be aware of extensions:**
```rust
pub fn handle_transfer(ctx: Context<HandleTransfer>, amount: u64) -> Result<()> {
    // Token-2022 may have transfer fees, freeze authority, etc.
    // Always check actual amount received after transfer

    let before_balance = ctx.accounts.destination.amount;

    token_interface::transfer_checked(
        CpiContext::new(/* ... */),
        amount,
        ctx.accounts.mint.decimals,
    )?;

    ctx.accounts.destination.reload()?;
    let actual_amount = ctx.accounts.destination.amount - before_balance;

    // Use actual_amount for accounting
    Ok(())
}
```

## 7. Event Security

### 7.1 When to Emit Events

Events are critical for:
- Indexing and querying program state
- Auditing sensitive operations
- Monitoring for security incidents

**Always emit events for:**
- State changes (deposits, withdrawals, config updates)
- Authorization changes (role grants, ownership transfers)
- Critical operations (program upgrades, emergency actions)

### 7.2 Event Data Validation

**SECURE - Validate before emitting:**
```rust
#[event]
pub struct WithdrawalEvent {
    pub user: Pubkey,
    pub amount: u64,
    pub timestamp: i64,
}

pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    // Validate first
    require!(
        ctx.accounts.vault.balance >= amount,
        ErrorCode::InsufficientFunds
    );

    // Perform operation
    ctx.accounts.vault.balance -= amount;

    // Emit event AFTER successful operation
    emit!(WithdrawalEvent {
        user: ctx.accounts.user.key(),
        amount,
        timestamp: Clock::get()?.unix_timestamp,
    });

    Ok(())
}
```

### 7.3 emit! vs emit_cpi!

**emit! - Regular event:**
```rust
emit!(MyEvent {
    data: value,
});
```

**emit_cpi! - Event for CPI callers:**
```rust
// Use when program is called via CPI and event should be
// visible to the calling program
emit_cpi!(MyEvent {
    data: value,
});
```

## 8. Anchor-Specific Best Practices

### 8.1 Account Space Calculation with InitSpace

**SECURE - Using InitSpace derive macro:**
```rust
use anchor_lang::prelude::*;

#[account]
#[derive(InitSpace)]
pub struct UserProfile {
    pub authority: Pubkey,      // 32 bytes
    #[max_len(50)]
    pub name: String,            // 4 + 50 bytes
    pub created_at: i64,         // 8 bytes
    pub bump: u8,                // 1 byte
}

#[derive(Accounts)]
pub struct CreateProfile<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + UserProfile::INIT_SPACE, // 8 for discriminator
        seeds = [b"profile", authority.key().as_ref()],
        bump
    )]
    pub profile: Account<'info, UserProfile>,
    pub authority: Signer<'info>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}
```

### 8.2 Remaining Accounts Handling

**SECURE - Validate remaining accounts:**
```rust
pub fn process_multiple_accounts(
    ctx: Context<ProcessAccounts>,
    count: u8,
) -> Result<()> {
    let remaining = &ctx.remaining_accounts;

    // Validate count
    require!(
        remaining.len() == count as usize,
        ErrorCode::InvalidAccountCount
    );

    // Validate each account
    for account_info in remaining.iter() {
        require!(
            account_info.is_writable,
            ErrorCode::AccountNotWritable
        );

        require!(
            account_info.owner == ctx.program_id,
            ErrorCode::InvalidAccountOwner
        );

        // Deserialize and validate type
        let account = Account::<MyAccount>::try_from(account_info)?;

        // Process account...
    }

    Ok(())
}
```

### 8.3 Instruction Data Validation

**SECURE - Validate all inputs:**
```rust
pub fn create_proposal(
    ctx: Context<CreateProposal>,
    title: String,
    description: String,
    execution_delay: i64,
) -> Result<()> {
    // Validate string lengths
    require!(
        title.len() > 0 && title.len() <= 100,
        ErrorCode::InvalidTitleLength
    );

    require!(
        description.len() <= 1000,
        ErrorCode::DescriptionTooLong
    );

    // Validate numeric ranges
    require!(
        execution_delay >= MIN_DELAY && execution_delay <= MAX_DELAY,
        ErrorCode::InvalidExecutionDelay
    );

    // Validate against overflow
    let execution_time = Clock::get()?
        .unix_timestamp
        .checked_add(execution_delay)
        .ok_or(ErrorCode::Overflow)?;

    ctx.accounts.proposal.title = title;
    ctx.accounts.proposal.description = description;
    ctx.accounts.proposal.execution_time = execution_time;

    Ok(())
}
```

### 8.4 Upgradability Considerations

**SECURE - Handle program upgrades safely:**

```rust
#[account]
#[derive(InitSpace)]
pub struct ProgramConfig {
    pub version: u8,
    pub upgrade_authority: Pubkey,
    pub paused: bool,
}

pub fn migrate(ctx: Context<Migrate>) -> Result<()> {
    let config = &mut ctx.accounts.config;

    // Check current version
    require!(
        config.version < CURRENT_VERSION,
        ErrorCode::AlreadyMigrated
    );

    // Perform version-specific migrations
    match config.version {
        0 => {
            // Migrate from v0 to v1
            // Add new fields, transform data, etc.
        }
        1 => {
            // Migrate from v1 to v2
        }
        _ => return Err(ErrorCode::UnsupportedVersion.into()),
    }

    config.version = CURRENT_VERSION;
    Ok(())
}
```

**Emergency pause pattern:**
```rust
#[derive(Accounts)]
pub struct SensitiveOperation<'info> {
    #[account(
        constraint = !config.paused @ ErrorCode::ProgramPaused
    )]
    pub config: Account<'info, ProgramConfig>,
    // ... other accounts
}
```

This ensures you can pause the program in case of emergencies during or after upgrades.
