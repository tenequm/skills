# Security Best Practices for Solana Development

Essential security principles and defensive programming patterns for building secure Solana programs with Anchor or native Rust.

> **Note:** This guide focuses on defensive programming during development. For comprehensive security audits, vulnerability analysis, and attack vectors, see the auditing references in this skill: [security-fundamentals.md](security-fundamentals.md), [vulnerability-patterns.md](vulnerability-patterns.md), [security-checklists.md](security-checklists.md), [anchor-security.md](anchor-security.md), and [native-security.md](native-security.md).

## Table of Contents

1. [Security Mindset](#security-mindset)
2. [Core Security Rules](#core-security-rules)
3. [Account Validation](#account-validation)
4. [Arithmetic Safety](#arithmetic-safety)
5. [PDA Security](#pda-security)
6. [CPI Security](#cpi-security)
7. [Common Pitfalls](#common-pitfalls)
8. [Pre-Deployment Checklist](#pre-deployment-checklist)

---

## Security Mindset

### Think Like an Attacker

**Fundamental principle:** Attackers control everything they send to your program.

- ❌ Don't assume: "Users won't do that"
- ❌ Don't assume: "The client validates this"
- ❌ Don't assume: "This account must be correct"
- ✅ Do validate: Every account, every parameter, every assumption

### You Control Nothing

Once deployed, your program:
- Cannot control which accounts are passed in
- Cannot control instruction data
- Cannot control timing or ordering
- Cannot prevent malicious clients

**Your only control:** How your program validates and handles inputs.

---

## Core Security Rules

### Rule 1: Validate Every Account

**Always verify:**

**Anchor:**
```rust
#[derive(Accounts)]
pub struct SecureInstruction<'info> {
    // ✅ Signer required
    pub authority: Signer<'info>,

    // ✅ Owner validation + relationship
    #[account(
        mut,
        has_one = authority,  // vault.authority == authority.key()
    )]
    pub vault: Account<'info, Vault>,

    // ✅ Program ID validation
    pub token_program: Program<'info, Token>,
}
```

**Native Rust:**
```rust
// ✅ Signer check
if !authority.is_signer {
    return Err(ProgramError::MissingRequiredSignature);
}

// ✅ Owner check
if vault.owner != program_id {
    return Err(ProgramError::IllegalOwner);
}

// ✅ Program ID check
if *token_program.key != spl_token::id() {
    return Err(ProgramError::IncorrectProgramId);
}
```

### Rule 2: Use Checked Arithmetic

**Never use:**
- `+`, `-`, `*`, `/` operators directly
- `saturating_*` methods (hide errors)
- `unwrap()` or `expect()` on arithmetic

**Always use:**
```rust
// ✅ Checked operations
let total = balance
    .checked_add(amount)
    .ok_or(ErrorCode::Overflow)?;

let remaining = total
    .checked_sub(withdrawal)
    .ok_or(ErrorCode::InsufficientFunds)?;

let product = price
    .checked_mul(quantity)
    .ok_or(ErrorCode::Overflow)?;

let share = total
    .checked_div(parts)
    .ok_or(ErrorCode::DivisionByZero)?;
```

### Rule 3: Validate PDAs Properly

**Anchor:**
```rust
#[derive(Accounts)]
pub struct SecurePDA<'info> {
    // ✅ Use canonical bump
    #[account(
        seeds = [b"vault", user.key().as_ref()],
        bump,  // Automatically validates canonical bump
    )]
    pub vault: Account<'info, Vault>,
}
```

**Native Rust:**
```rust
// ✅ Find canonical bump
let (expected_pda, bump) = Pubkey::find_program_address(
    &[b"vault", user.key.as_ref()],
    program_id,
);

// ✅ Validate PDA matches
if expected_pda != *vault.key {
    return Err(ProgramError::InvalidSeeds);
}

// Store bump for future use with create_program_address
```

### Rule 4: Secure Cross-Program Invocations

**Anchor:**
```rust
// ✅ Program type validation
pub token_program: Program<'info, Token>,

// ✅ Use CpiContext
let cpi_ctx = CpiContext::new(
    ctx.accounts.token_program.to_account_info(),
    transfer_accounts,
);

token::transfer(cpi_ctx, amount)?;
```

**Native Rust:**
```rust
// ✅ Validate program ID before CPI
if *token_program.key != spl_token::id() {
    return Err(ProgramError::IncorrectProgramId);
}

// ✅ Build instruction safely
let ix = spl_token::instruction::transfer(
    token_program.key,
    source.key,
    destination.key,
    authority.key,
    &[],
    amount,
)?;

invoke(&ix, &[source, destination, authority, token_program])?;
```

### Rule 5: Handle Errors Gracefully

**Never:**
```rust
// ❌ Don't panic or unwrap
let value = some_operation().unwrap();

// ❌ Don't ignore errors
some_operation();
```

**Always:**
```rust
// ✅ Propagate errors
let value = some_operation()
    .ok_or(ErrorCode::OperationFailed)?;

// ✅ Or handle explicitly
let value = match some_operation() {
    Some(v) => v,
    None => return Err(ErrorCode::OperationFailed.into()),
};
```

---

## Account Validation

### Essential Checks

For every account, verify:

1. **Signer** - Does this account need to sign?
2. **Owner** - Who owns this account? Is it our program?
3. **Writable** - Does this need `mut`?
4. **Type** - Is this the right account type?
5. **Relationships** - Do related accounts match?

### Validation Pattern

```rust
// Native Rust comprehensive validation
pub fn validate_account(
    account: &AccountInfo,
    expected_owner: &Pubkey,
    must_be_signer: bool,
    must_be_writable: bool,
) -> ProgramResult {
    // Check signer
    if must_be_signer && !account.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Check owner
    if account.owner != expected_owner {
        return Err(ProgramError::IllegalOwner);
    }

    // Check writable
    if must_be_writable && !account.is_writable {
        return Err(ProgramError::InvalidAccountData);
    }

    Ok(())
}
```

---

## Arithmetic Safety

### Common Vulnerabilities

**Overflow example:**
```rust
// ❌ VULNERABLE: Can overflow
pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    ctx.accounts.vault.balance = ctx.accounts.vault.balance + amount;
    Ok(())
}

// If vault.balance = u64::MAX - 100 and amount = 200
// Result wraps to 99, losing 18.4 quintillion tokens!
```

**Fix:**
```rust
// ✅ SECURE: Checked arithmetic
pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    ctx.accounts.vault.balance = ctx.accounts.vault.balance
        .checked_add(amount)
        .ok_or(ErrorCode::Overflow)?;
    Ok(())
}
```

### Precision Loss

**Multiply before divide:**
```rust
// ❌ WRONG: Loses precision
let fee = amount / 100;  // 1.5% becomes 1%

// ✅ CORRECT: Multiply first
let fee = amount
    .checked_mul(15)
    .and_then(|v| v.checked_div(1000))
    .ok_or(ErrorCode::Overflow)?;  // Exact 1.5%
```

---

## PDA Security

### Use Canonical Bumps

**Always find the canonical bump:**

```rust
// ✅ Find canonical bump
let (pda, bump) = Pubkey::find_program_address(
    &[b"vault", user.key.as_ref()],
    program_id,
);

// Store bump in account for later use
vault.bump = bump;
```

**Never hardcode or accept bumps from clients:**
```rust
// ❌ VULNERABLE: Accepts any bump
#[derive(Accounts)]
pub struct BadPDA<'info> {
    #[account(seeds = [b"vault"], bump = user_provided_bump)]
    pub vault: Account<'info, Vault>,
}
```

### Unique Seeds

Ensure seeds create unique PDAs:

```rust
// ✅ GOOD: Unique per user
seeds = [b"vault", user.key().as_ref()]

// ❌ BAD: Same PDA for everyone
seeds = [b"vault"]
```

---

## CPI Security

### Validate Target Programs

**Never accept arbitrary program IDs:**

```rust
// ❌ VULNERABLE
pub fn bad_cpi(ctx: Context<BadCPI>) -> Result<()> {
    // Attacker can pass any program!
    let cpi_ctx = CpiContext::new(
        ctx.accounts.any_program.to_account_info(),
        accounts,
    );
    // ... make CPI
}

// ✅ SECURE
#[derive(Accounts)]
pub struct SecureCPI<'info> {
    pub token_program: Program<'info, Token>,  // Type-checked!
}
```

### Reload Accounts After CPIs

If a CPI might modify an account you're using:

```rust
// ✅ Reload account after external call
let balance_before = token_account.amount;

// Make CPI that might change the account
token::transfer(cpi_ctx, amount)?;

// Reload to get fresh data
token_account.reload()?;

let balance_after = token_account.amount;
```

---

## Common Pitfalls

### 1. init_if_needed (Anchor)

**Dangerous pattern:**
```rust
// ❌ Can be exploited
#[account(init_if_needed, payer = user, space = 8 + 32)]
pub config: Account<'info, Config>,
```

**Problem:** Attacker creates the account first with malicious data.

**Fix:**
```rust
// ✅ Use init or check if exists
#[account(init, payer = user, space = 8 + 32)]
pub config: Account<'info, Config>,

// Or explicitly check
if config.is_initialized {
    return Err(ErrorCode::AlreadyInitialized.into());
}
```

### 2. Missing Signer Checks

```rust
// ❌ Anyone can withdraw!
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    ctx.accounts.vault.balance -= amount;
    Ok(())
}

// ✅ Authority must sign
#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut, has_one = authority)]
    pub vault: Account<'info, Vault>,
    pub authority: Signer<'info>,  // Required!
}
```

### 3. Account Confusion

```rust
// ❌ No validation - any accounts work!
pub struct Transfer<'info> {
    pub from: Account<'info, TokenAccount>,
    pub to: Account<'info, TokenAccount>,
}

// ✅ Validate relationships
pub struct Transfer<'info> {
    #[account(
        mut,
        constraint = from.owner == authority.key(),
        constraint = from.mint == to.mint,
    )]
    pub from: Account<'info, TokenAccount>,

    #[account(mut)]
    pub to: Account<'info, TokenAccount>,

    pub authority: Signer<'info>,
}
```

### 4. Unchecked Account Types

```rust
// ❌ Uses raw AccountInfo - no type safety
pub fn bad(ctx: Context<Bad>) -> Result<()> {
    let data = ctx.accounts.account.try_borrow_data()?;
    // What if attacker passes wrong account type?
}

// ✅ Use typed Account
pub fn good(ctx: Context<Good>) -> Result<()> {
    // Anchor verifies discriminator automatically
    let vault = &ctx.accounts.vault;
}
```

---

## Pre-Deployment Checklist

Before deploying to mainnet:

### Code Review

- [ ] All accounts validated (signer, owner, writable)
- [ ] All arithmetic uses `checked_*` methods
- [ ] All PDAs use canonical bumps
- [ ] All CPIs validate target programs
- [ ] No `unwrap()` or `expect()` in production code
- [ ] No `init_if_needed` without additional checks
- [ ] All error cases handled gracefully

### Testing

- [ ] Unit tests cover all instructions
- [ ] Integration tests cover instruction interactions
- [ ] Edge cases tested (zero amounts, max values, overflow)
- [ ] Error conditions tested (invalid accounts, unauthorized access)
- [ ] Fuzz testing with Trident (if possible)

### Security Audit

- [ ] Internal code review completed
- [ ] External security audit (recommended for >$100k TVL)
- [ ] Run the systematic audit workflow (see [security-checklists.md](security-checklists.md) and [vulnerability-patterns.md](vulnerability-patterns.md))
- [ ] All critical/high severity findings resolved
- [ ] Medium findings assessed and documented

### Documentation

- [ ] Account structures documented
- [ ] Instruction requirements documented
- [ ] Known limitations documented
- [ ] Upgrade strategy documented
- [ ] Emergency procedures documented

### Deployment

- [ ] Tested on devnet extensively
- [ ] Tested on mainnet-beta with small amounts
- [ ] Upgrade authority secured (multisig recommended)
- [ ] Monitoring and alerts configured
- [ ] Emergency pause mechanism (if applicable)

---

## Development vs Auditing

This guide covers **defensive programming during development** - secure coding patterns, implementation guidance, and development workflows (testing, deployment, optimization).

For **comprehensive security auditing**, use the auditing references in this skill:

- 🔍 **Systematic audits** - [security-checklists.md](security-checklists.md): category-by-category validation
- 🐛 **Vulnerability analysis** - [vulnerability-patterns.md](vulnerability-patterns.md): exploit scenarios and attack vectors
- 🛡️ **Framework-specific patterns** - [anchor-security.md](anchor-security.md) and [native-security.md](native-security.md)
- 📚 **Threat modeling and fundamentals** - [security-fundamentals.md](security-fundamentals.md)
- ⚠️ **Known gotchas** - [caveats.md](caveats.md)

---

## Quick Security Reference

### Anchor Security Checklist

```rust
#[derive(Accounts)]
pub struct Secure<'info> {
    // ✅ Signer
    pub authority: Signer<'info>,

    // ✅ Validation + relationships
    #[account(
        mut,
        has_one = authority,
        seeds = [b"vault", user.key().as_ref()],
        bump,
    )]
    pub vault: Account<'info, Vault>,

    // ✅ Program validation
    pub token_program: Program<'info, Token>,
}

pub fn secure_fn(ctx: Context<Secure>, amount: u64) -> Result<()> {
    // ✅ Checked arithmetic
    ctx.accounts.vault.balance = ctx.accounts.vault.balance
        .checked_add(amount)
        .ok_or(ErrorCode::Overflow)?;

    Ok(())
}
```

### Native Rust Security Checklist

```rust
pub fn secure_fn(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let accounts = &mut accounts.iter();
    let authority = next_account_info(accounts)?;
    let vault = next_account_info(accounts)?;

    // ✅ Signer check
    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // ✅ Owner check
    if vault.owner != program_id {
        return Err(ProgramError::IllegalOwner);
    }

    // ✅ PDA validation
    let (expected_pda, _) = Pubkey::find_program_address(
        &[b"vault", authority.key.as_ref()],
        program_id,
    );
    if *vault.key != expected_pda {
        return Err(ProgramError::InvalidSeeds);
    }

    // ✅ Deserialize
    let mut vault_data = Vault::try_from_slice(&vault.data.borrow())?;

    // ✅ Checked arithmetic
    vault_data.balance = vault_data.balance
        .checked_add(amount)
        .ok_or(ProgramError::ArithmeticOverflow)?;

    // ✅ Serialize back
    vault_data.serialize(&mut &mut vault.data.borrow_mut()[..])?;

    Ok(())
}
```

---

## Remember

**Security is not optional.** Every line of code is a potential vulnerability. Validate everything, trust nothing, and when in doubt, use the `solana-security` skill for a comprehensive audit.
