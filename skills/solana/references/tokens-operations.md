# SPL Token Program - Operations

Complete guide to SPL Token operations including creating mints, minting tokens, transferring (with transfer_checked), burning, and closing token accounts. Shows both Anchor and Native Rust implementations side-by-side.

**For related topics, see:**
- **[tokens-overview.md](tokens-overview.md)** - Token fundamentals and account structures
- **[tokens-validation.md](tokens-validation.md)** - Account validation patterns
- **[tokens-2022.md](tokens-2022.md)** - Token Extensions Program features
- **[tokens-patterns.md](tokens-patterns.md)** - Common patterns and security

## Table of Contents

1. [Creating Tokens](#creating-tokens)
2. [Minting Tokens](#minting-tokens)
3. [Transferring Tokens](#transferring-tokens)
4. [Burning Tokens](#burning-tokens)
5. [Closing Token Accounts](#closing-token-accounts)

---

## Creating Tokens

### Initialize a New Mint

#### Using Anchor

```rust
use anchor_spl::token_interface::{Mint, TokenInterface};

#[derive(Accounts)]
pub struct CreateMint<'info> {
    #[account(
        init,
        payer = payer,
        mint::decimals = 9,
        mint::authority = mint_authority,
        mint::freeze_authority = freeze_authority,
        mint::token_program = token_program,
    )]
    pub mint: InterfaceAccount<'info, Mint>,

    /// CHECK: Can be any account
    pub mint_authority: UncheckedAccount<'info>,

    /// CHECK: Can be any account (optional)
    pub freeze_authority: UncheckedAccount<'info>,

    #[account(mut)]
    pub payer: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

pub fn create_mint(ctx: Context<CreateMint>) -> Result<()> {
    // Mint is automatically created and initialized by Anchor constraints
    msg!("Mint created: {}", ctx.accounts.mint.key());
    Ok(())
}
```

**Key Anchor Constraints:**
- `init` - Creates and initializes the account
- `mint::decimals` - Number of decimal places
- `mint::authority` - Who can mint tokens
- `mint::freeze_authority` - Who can freeze token accounts (optional)
- `mint::token_program` - Which token program to use

#### Using Native Rust

```rust
use spl_token::instruction::initialize_mint;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};

pub fn create_mint(
    payer: &AccountInfo,
    mint_account: &AccountInfo,
    mint_authority: &Pubkey,
    freeze_authority: Option<&Pubkey>,
    decimals: u8,
    system_program: &AccountInfo,
    token_program: &AccountInfo,
    rent_sysvar: &AccountInfo,
) -> ProgramResult {
    // Mint account size
    let mint_size = 82;

    // Calculate rent
    let rent = Rent::get()?;
    let rent_lamports = rent.minimum_balance(mint_size);

    // Create mint account via System Program
    invoke(
        &system_instruction::create_account(
            payer.key,
            mint_account.key,
            rent_lamports,
            mint_size as u64,
            &spl_token::ID,
        ),
        &[payer.clone(), mint_account.clone(), system_program.clone()],
    )?;

    // Initialize mint
    invoke(
        &initialize_mint(
            token_program.key,
            mint_account.key,
            mint_authority,
            freeze_authority,
            decimals,
        )?,
        &[
            mint_account.clone(),
            rent_sysvar.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}
```

### Initialize a Token Account (Non-ATA)

#### Using Anchor

```rust
use anchor_spl::token_interface::{Mint, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct CreateTokenAccount<'info> {
    #[account(
        init,
        payer = payer,
        token::mint = mint,
        token::authority = owner,
        token::token_program = token_program,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    pub mint: InterfaceAccount<'info, Mint>,

    /// CHECK: Can be any account
    pub owner: UncheckedAccount<'info>,

    #[account(mut)]
    pub payer: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
}

pub fn create_token_account(ctx: Context<CreateTokenAccount>) -> Result<()> {
    // Token account is automatically created and initialized
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_token::instruction::initialize_account3;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};

pub fn create_token_account(
    payer: &AccountInfo,
    token_account: &AccountInfo,
    mint: &AccountInfo,
    owner: &Pubkey,
    system_program: &AccountInfo,
    token_program: &AccountInfo,
) -> ProgramResult {
    // Token account size
    let token_account_size = 165;

    // Calculate rent
    let rent = Rent::get()?;
    let rent_lamports = rent.minimum_balance(token_account_size);

    // Create token account
    invoke(
        &system_instruction::create_account(
            payer.key,
            token_account.key,
            rent_lamports,
            token_account_size as u64,
            &spl_token::ID,
        ),
        &[payer.clone(), token_account.clone(), system_program.clone()],
    )?;

    // Initialize token account
    invoke(
        &initialize_account3(
            token_program.key,
            token_account.key,
            mint.key,
            owner,
        )?,
        &[token_account.clone(), mint.clone(), token_program.clone()],
    )?;

    Ok(())
}
```

---

## Minting Tokens

### Basic Minting (User Authority)

#### Using Anchor

```rust
use anchor_spl::token_interface::{self, Mint, MintTo, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct MintTokens<'info> {
    #[account(mut)]
    pub mint: InterfaceAccount<'info, Mint>,

    #[account(mut)]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    pub mint_authority: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn mint_tokens(ctx: Context<MintTokens>, amount: u64) -> Result<()> {
    let cpi_accounts = MintTo {
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.token_account.to_account_info(),
        authority: ctx.accounts.mint_authority.to_account_info(),
    };

    let cpi_program = ctx.accounts.token_program.to_account_info();
    let cpi_context = CpiContext::new(cpi_program, cpi_accounts);

    token_interface::mint_to(cpi_context, amount)?;
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_token::instruction::mint_to;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke,
    program_error::ProgramError,
};

pub fn mint_tokens(
    mint: &AccountInfo,
    destination: &AccountInfo,
    mint_authority: &AccountInfo,
    amount: u64,
    token_program: &AccountInfo,
) -> ProgramResult {
    // Mint authority must be a signer
    if !mint_authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    invoke(
        &mint_to(
            token_program.key,
            mint.key,
            destination.key,
            mint_authority.key,
            &[],  // No multisig signers
            amount,
        )?,
        &[
            mint.clone(),
            destination.clone(),
            mint_authority.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}
```

### Minting with PDA Authority

#### Using Anchor

```rust
use anchor_spl::token_interface::{self, Mint, MintTo, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct MintWithPDA<'info> {
    #[account(
        mut,
        mint::authority = mint_authority,
    )]
    pub mint: InterfaceAccount<'info, Mint>,

    #[account(mut)]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(
        seeds = [b"mint-authority"],
        bump,
    )]
    /// CHECK: PDA signer
    pub mint_authority: UncheckedAccount<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn mint_with_pda(ctx: Context<MintWithPDA>, amount: u64) -> Result<()> {
    let seeds = &[
        b"mint-authority",
        &[ctx.bumps.mint_authority],
    ];
    let signer_seeds = &[&seeds[..]];

    let cpi_accounts = MintTo {
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.token_account.to_account_info(),
        authority: ctx.accounts.mint_authority.to_account_info(),
    };

    let cpi_context = CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        cpi_accounts
    ).with_signer(signer_seeds);

    token_interface::mint_to(cpi_context, amount)?;
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_token::instruction::mint_to;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke_signed,
    program_error::ProgramError,
    pubkey::Pubkey,
};

pub fn mint_tokens_from_pda(
    program_id: &Pubkey,
    mint: &AccountInfo,
    destination: &AccountInfo,
    mint_authority_pda: &AccountInfo,
    token_program: &AccountInfo,
    amount: u64,
    pda_seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    // Validate PDA
    let (expected_pda, _) = Pubkey::find_program_address(pda_seeds, program_id);
    if expected_pda != *mint_authority_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // Prepare signer seeds
    let mut full_seeds = pda_seeds.to_vec();
    full_seeds.push(&[bump]);
    let signer_seeds: &[&[&[u8]]] = &[&full_seeds];

    invoke_signed(
        &mint_to(
            token_program.key,
            mint.key,
            destination.key,
            mint_authority_pda.key,
            &[],
            amount,
        )?,
        &[
            mint.clone(),
            destination.clone(),
            mint_authority_pda.clone(),
            token_program.clone(),
        ],
        signer_seeds,
    )?;

    Ok(())
}
```

---

## Transferring Tokens

### Basic Transfer

#### Using Anchor

```rust
use anchor_spl::token_interface::{self, TokenAccount, TokenInterface, Transfer};

#[derive(Accounts)]
pub struct TransferTokens<'info> {
    #[account(mut)]
    pub from: InterfaceAccount<'info, TokenAccount>,

    #[account(mut)]
    pub to: InterfaceAccount<'info, TokenAccount>,

    pub authority: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn transfer_tokens(ctx: Context<TransferTokens>, amount: u64) -> Result<()> {
    let cpi_accounts = Transfer {
        from: ctx.accounts.from.to_account_info(),
        to: ctx.accounts.to.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_context = CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        cpi_accounts
    );

    token_interface::transfer(cpi_context, amount)?;
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_token::instruction::transfer;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke,
    program_error::ProgramError,
};

pub fn transfer_tokens(
    source: &AccountInfo,
    destination: &AccountInfo,
    authority: &AccountInfo,
    amount: u64,
    token_program: &AccountInfo,
) -> ProgramResult {
    // Authority must be a signer
    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    invoke(
        &transfer(
            token_program.key,
            source.key,
            destination.key,
            authority.key,
            &[],  // No multisig signers
            amount,
        )?,
        &[
            source.clone(),
            destination.clone(),
            authority.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}
```

### Transfer with Checks (Recommended)

#### Using Anchor

```rust
use anchor_spl::token_interface::{self, Mint, TokenAccount, TokenInterface, TransferChecked};

#[derive(Accounts)]
pub struct TransferTokensChecked<'info> {
    #[account(mut)]
    pub from: InterfaceAccount<'info, TokenAccount>,

    #[account(mut)]
    pub to: InterfaceAccount<'info, TokenAccount>,

    pub mint: InterfaceAccount<'info, Mint>,

    pub authority: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn transfer_tokens_checked(
    ctx: Context<TransferTokensChecked>,
    amount: u64
) -> Result<()> {
    token_interface::transfer_checked(
        CpiContext::new(
            ctx.accounts.token_program.to_account_info(),
            TransferChecked {
                from: ctx.accounts.from.to_account_info(),
                mint: ctx.accounts.mint.to_account_info(),
                to: ctx.accounts.to.to_account_info(),
                authority: ctx.accounts.authority.to_account_info(),
            },
        ),
        amount,
        ctx.accounts.mint.decimals,
    )?;
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_token::instruction::transfer_checked;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke,
    program_error::ProgramError,
};

pub fn transfer_tokens_checked(
    source: &AccountInfo,
    mint: &AccountInfo,
    destination: &AccountInfo,
    authority: &AccountInfo,
    amount: u64,
    decimals: u8,
    token_program: &AccountInfo,
) -> ProgramResult {
    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

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
        &[
            source.clone(),
            mint.clone(),
            destination.clone(),
            authority.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}
```

### Transfer with PDA Signer

#### Using Anchor

```rust
use anchor_spl::token_interface::{self, TokenAccount, TokenInterface, Transfer};

#[derive(Accounts)]
pub struct TransferWithPDA<'info> {
    #[account(
        mut,
        token::authority = authority,
    )]
    pub from: InterfaceAccount<'info, TokenAccount>,

    #[account(mut)]
    pub to: InterfaceAccount<'info, TokenAccount>,

    #[account(
        seeds = [b"authority"],
        bump,
    )]
    /// CHECK: PDA signer
    pub authority: UncheckedAccount<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn transfer_with_pda(ctx: Context<TransferWithPDA>, amount: u64) -> Result<()> {
    let seeds = &[
        b"authority",
        &[ctx.bumps.authority],
    ];
    let signer_seeds = &[&seeds[..]];

    let cpi_accounts = Transfer {
        from: ctx.accounts.from.to_account_info(),
        to: ctx.accounts.to.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_context = CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        cpi_accounts
    ).with_signer(signer_seeds);

    token_interface::transfer(cpi_context, amount)?;
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_token::instruction::transfer;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke_signed,
    program_error::ProgramError,
    pubkey::Pubkey,
};

pub fn transfer_tokens_from_pda(
    program_id: &Pubkey,
    source: &AccountInfo,
    destination: &AccountInfo,
    authority_pda: &AccountInfo,
    token_program: &AccountInfo,
    amount: u64,
    pda_seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    let (expected_pda, _) = Pubkey::find_program_address(pda_seeds, program_id);
    if expected_pda != *authority_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    let mut full_seeds = pda_seeds.to_vec();
    full_seeds.push(&[bump]);
    let signer_seeds: &[&[&[u8]]] = &[&full_seeds];

    invoke_signed(
        &transfer(
            token_program.key,
            source.key,
            destination.key,
            authority_pda.key,
            &[],
            amount,
        )?,
        &[
            source.clone(),
            destination.clone(),
            authority_pda.clone(),
            token_program.clone(),
        ],
        signer_seeds,
    )?;

    Ok(())
}
```

---

## Burning Tokens

### Basic Burn

#### Using Anchor

```rust
use anchor_spl::token_interface::{self, Burn, Mint, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct BurnTokens<'info> {
    #[account(mut)]
    pub mint: InterfaceAccount<'info, Mint>,

    #[account(mut)]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    pub authority: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn burn_tokens(ctx: Context<BurnTokens>, amount: u64) -> Result<()> {
    let cpi_accounts = Burn {
        mint: ctx.accounts.mint.to_account_info(),
        from: ctx.accounts.token_account.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_context = CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        cpi_accounts
    );

    token_interface::burn(cpi_context, amount)?;
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_token::instruction::burn;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke,
    program_error::ProgramError,
};

pub fn burn_tokens(
    token_account: &AccountInfo,
    mint: &AccountInfo,
    authority: &AccountInfo,
    amount: u64,
    token_program: &AccountInfo,
) -> ProgramResult {
    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    invoke(
        &burn(
            token_program.key,
            token_account.key,
            mint.key,
            authority.key,
            &[],
            amount,
        )?,
        &[
            token_account.clone(),
            mint.clone(),
            authority.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}
```

### Burn with PDA Authority

#### Using Anchor

```rust
use anchor_spl::token_interface::{self, Burn, Mint, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct BurnWithPDA<'info> {
    #[account(mut)]
    pub mint: InterfaceAccount<'info, Mint>,

    #[account(
        mut,
        token::authority = authority,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(
        seeds = [b"burn-authority"],
        bump,
    )]
    /// CHECK: PDA signer
    pub authority: UncheckedAccount<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn burn_with_pda(ctx: Context<BurnWithPDA>, amount: u64) -> Result<()> {
    let seeds = &[
        b"burn-authority",
        &[ctx.bumps.authority],
    ];
    let signer_seeds = &[&seeds[..]];

    let cpi_accounts = Burn {
        mint: ctx.accounts.mint.to_account_info(),
        from: ctx.accounts.token_account.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_context = CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        cpi_accounts
    ).with_signer(signer_seeds);

    token_interface::burn(cpi_context, amount)?;
    Ok(())
}
```

#### Using Native Rust

```rust
pub fn burn_tokens_from_pda(
    program_id: &Pubkey,
    token_account: &AccountInfo,
    mint: &AccountInfo,
    authority_pda: &AccountInfo,
    token_program: &AccountInfo,
    amount: u64,
    pda_seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    let (expected_pda, _) = Pubkey::find_program_address(pda_seeds, program_id);
    if expected_pda != *authority_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    let mut full_seeds = pda_seeds.to_vec();
    full_seeds.push(&[bump]);
    let signer_seeds: &[&[&[u8]]] = &[&full_seeds];

    invoke_signed(
        &burn(
            token_program.key,
            token_account.key,
            mint.key,
            authority_pda.key,
            &[],
            amount,
        )?,
        &[
            token_account.clone(),
            mint.clone(),
            authority_pda.clone(),
            token_program.clone(),
        ],
        signer_seeds,
    )?;

    Ok(())
}
```

---

## Closing Token Accounts

### Close Token Account

#### Using Anchor

```rust
use anchor_spl::token_interface::{self, CloseAccount, TokenAccount, TokenInterface};

#[derive(Accounts)]
pub struct CloseTokenAccount<'info> {
    #[account(mut)]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(mut)]
    pub destination: SystemAccount<'info>,

    pub authority: Signer<'info>,

    pub token_program: Interface<'info, TokenInterface>,
}

pub fn close_token_account(ctx: Context<CloseTokenAccount>) -> Result<()> {
    let cpi_accounts = CloseAccount {
        account: ctx.accounts.token_account.to_account_info(),
        destination: ctx.accounts.destination.to_account_info(),
        authority: ctx.accounts.authority.to_account_info(),
    };

    let cpi_context = CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        cpi_accounts
    );

    token_interface::close_account(cpi_context)?;
    Ok(())
}
```

**Using Anchor Constraints (Simplified):**

```rust
#[derive(Accounts)]
pub struct CloseTokenAccount<'info> {
    #[account(
        mut,
        close = destination,
        token::authority = authority,
    )]
    pub token_account: InterfaceAccount<'info, TokenAccount>,

    #[account(mut)]
    pub destination: SystemAccount<'info>,

    pub authority: Signer<'info>,
}

pub fn close_token_account(ctx: Context<CloseTokenAccount>) -> Result<()> {
    // Account is automatically closed by Anchor constraints
    Ok(())
}
```

#### Using Native Rust

```rust
use spl_token::instruction::close_account;
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program::invoke,
    program_error::ProgramError,
};

pub fn close_token_account(
    token_account: &AccountInfo,
    destination: &AccountInfo,
    authority: &AccountInfo,
    token_program: &AccountInfo,
) -> ProgramResult {
    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    invoke(
        &close_account(
            token_program.key,
            token_account.key,
            destination.key,
            authority.key,
            &[],
        )?,
        &[
            token_account.clone(),
            destination.clone(),
            authority.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}
```

---

## Next Steps

- **Validation**: See [tokens-validation.md](tokens-validation.md) for account validation patterns
- **Token-2022**: See [tokens-2022.md](tokens-2022.md) for Token Extensions Program features
- **Patterns & Security**: See [tokens-patterns.md](tokens-patterns.md) for common patterns and security best practices
