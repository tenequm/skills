# Security Checklists

Comprehensive validation checklists for Solana program security reviews.

## Account Validation Checklist

For every account in every instruction:

- [ ] **Signer validation**: Uses `Signer<'info>` or `is_signer` check when needed
- [ ] **Owner validation**: Uses `#[account(owner = ...)]` or manual owner check
- [ ] **Writable checks**: Properly marked `mut` when account data will be modified
- [ ] **Account initialization**: Checks if account is initialized before use
- [ ] **PDA validation**: Validates seeds and uses canonical bump
- [ ] **Discriminator check**: For `AccountLoader`, validates account type
- [ ] **Account relationships**: Uses `has_one` for related accounts

```rust
// Complete account validation example
#[derive(Accounts)]
pub struct SecureInstruction<'info> {
    #[account(
        mut,
        has_one = authority,  // Relationship validation
        seeds = [b"vault", authority.key().as_ref()],
        bump,  // Canonical bump
    )]
    pub vault: Account<'info, Vault>,

    pub authority: Signer<'info>,  // Signer required

    #[account(
        mut,
        constraint = token_account.owner == authority.key(),  // Custom validation
    )]
    pub token_account: Account<'info, TokenAccount>,

    pub token_program: Program<'info, Token>,  // Program validation
}
```

## Arithmetic Safety Checklist

For all mathematical operations:

- [ ] **Addition**: Uses `checked_add()` instead of `+`
- [ ] **Subtraction**: Uses `checked_sub()` instead of `-`
- [ ] **Multiplication**: Uses `checked_mul()` instead of `*`
- [ ] **Division**: Uses `checked_div()` instead of `/`
- [ ] **Division by zero**: Validates divisor is non-zero
- [ ] **Precision loss**: Uses `try_floor_u64()` instead of `try_round_u64()` to prevent arbitrage
- [ ] **Avoid saturating**: Does not use `saturating_*` methods (they hide errors)
- [ ] **Proper error handling**: All arithmetic wrapped in `ok_or(error)?`

```rust
// Secure arithmetic examples
let total = balance
    .checked_add(amount)
    .ok_or(ErrorCode::Overflow)?;

let share = total
    .checked_div(denominator)
    .ok_or(ErrorCode::DivisionByZero)?;

// For Decimal types (token amounts)
let liquidity = Decimal::from(collateral_amount)
    .try_div(rate)?
    .try_floor_u64()?;  // Not try_round_u64()!
```

## PDA and Account Security Checklist

- [ ] **Canonical bump**: PDAs use `bump` in seeds constraint (not hardcoded)
- [ ] **Unique seeds**: Seeds include unique identifier (user pubkey, mint, etc.)
- [ ] **No duplicate accounts**: Same account not used twice as mutable
- [ ] **Init vs init_if_needed**: Uses `init` with proper validation, not `init_if_needed`
- [ ] **has_one constraints**: Related accounts validated with `has_one`
- [ ] **Custom constraints**: Complex validation uses `constraint` expression
- [ ] **Seed collision**: Seeds designed to prevent collisions

```rust
// Secure PDA patterns
#[account(
    init,
    payer = authority,
    space = 8 + UserAccount::INIT_SPACE,
    seeds = [
        b"user",
        authority.key().as_ref(),  // Unique to user
        mint.key().as_ref(),        // Unique to mint
    ],
    bump
)]
pub user_account: Account<'info, UserAccount>,
```

## CPI Security Checklist

For all Cross-Program Invocations:

- [ ] **Program validation**: Target program is validated (uses `Program<'info, T>`)
- [ ] **Signer seeds**: PDA signers pass seeds correctly in `invoke_signed`
- [ ] **Return value checking**: CPI success doesn't guarantee correct state
- [ ] **Account reloading**: Reload accounts after CPI that may modify them
- [ ] **No arbitrary CPI**: Program account is not user-controlled
- [ ] **Privilege escalation**: CPI doesn't grant unexpected permissions

```rust
// Secure CPI pattern
#[derive(Accounts)]
pub struct SecureCPI<'info> {
    pub token_program: Program<'info, Token>,  // Type-validated
    // ... other accounts
}

pub fn secure_cpi(ctx: Context<SecureCPI>) -> Result<()> {
    // CPI with validated program
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

    // Reload account after CPI
    ctx.accounts.from.reload()?;

    // Validate expected state
    require!(
        ctx.accounts.from.amount == expected_amount,
        ErrorCode::InvalidState
    );

    Ok(())
}
```

## Oracle and External Data Checklist

For Pyth, Switchboard, or other oracles:

- [ ] **Oracle status**: Validates oracle is in valid state (Trading status for Pyth)
- [ ] **Price staleness**: Checks timestamp is recent enough
- [ ] **Oracle owner**: Validates oracle account owner is correct program
- [ ] **Confidence interval**: For Pyth, checks confidence is acceptable
- [ ] **Price validity**: Validates price is within reasonable bounds
- [ ] **Fallback handling**: Has strategy for oracle failure

```rust
// Pyth oracle validation
pub fn validate_pyth_price(
    pyth_account: &AccountInfo,
    clock: &Clock,
) -> Result<i64> {
    // Validate owner
    require_keys_eq!(
        *pyth_account.owner,
        PYTH_PROGRAM_ID,
        ErrorCode::InvalidOracle
    );

    let price_data = pyth_account.try_borrow_data()?;
    let price_feed = load_price_feed_from_account_info(pyth_account)?;

    // Check status
    require!(
        price_feed.agg.status == PriceStatus::Trading,
        ErrorCode::InvalidOracleStatus
    );

    // Check staleness (e.g., max 60 seconds old)
    let max_age = 60;
    require!(
        clock.unix_timestamp - price_feed.agg.publish_time <= max_age,
        ErrorCode::StalePrice
    );

    // Check confidence (example: max 1% of price)
    let confidence_threshold = price_feed.agg.price / 100;
    require!(
        price_feed.agg.conf <= confidence_threshold as u64,
        ErrorCode::OracleConfidenceTooLow
    );

    Ok(price_feed.agg.price)
}
```

## Token Program Security Checklist

### SPL Token Checks

- [ ] **ATA validation**: Associated Token Accounts validated correctly
- [ ] **Mint authority**: Proper checks on mint authority for minting operations
- [ ] **Freeze authority**: Handles frozen accounts appropriately
- [ ] **Delegate handling**: Resets delegate when needed
- [ ] **Close authority**: Resets close authority on owner change

### Token-2022 Specific Checks

- [ ] **Transfer hooks**: Handles transfer hook extensions correctly
- [ ] **Extension data**: Validates all active extensions
- [ ] **Confidential transfers**: Properly handles confidential transfer extension
- [ ] **Transfer fees**: Respects transfer fee extension
- [ ] **Permanent delegate**: Checks for permanent delegate extension
- [ ] **Additional rent**: Accounts for extension rent requirements

```rust
// Token-2022 with extensions
use spl_token_2022::extension::{
    BaseStateWithExtensions,
    StateWithExtensions,
};

pub fn safe_token_2022_transfer(
    /* accounts */
) -> Result<()> {
    // Check for transfer hook
    let mint_data = mint.try_borrow_data()?;
    let mint_with_extensions = StateWithExtensions::<Mint>::unpack(&mint_data)?;

    if let Ok(transfer_hook) = mint_with_extensions.get_extension::<TransferHook>() {
        // Handle transfer hook properly
        // ... transfer hook logic
    }

    // Check for transfer fee
    if let Ok(transfer_fee_config) = mint_with_extensions.get_extension::<TransferFeeConfig>() {
        // Calculate and handle fees
        // ... fee logic
    }

    // Proceed with transfer
    Ok(())
}
```

## Architecture Review Checklist

- [ ] **PDA design**: PDAs used appropriately vs keypair accounts
- [ ] **Account space**: Space calculation uses `InitSpace` derive
- [ ] **Error handling**: Custom errors with descriptive messages
- [ ] **Event emission**: Critical state changes emit events
- [ ] **Rent exemption**: All accounts are rent-exempt
- [ ] **Transaction size**: Stays within ~1232 byte limit
- [ ] **Compute budget**: Optimized to stay under compute limits
- [ ] **Upgradeability**: Considers upgrade path and account versioning

## Testing Checklist

- [ ] **Unit tests**: Each instruction has unit tests
- [ ] **Fuzz tests**: Arithmetic operations have fuzz tests (Trident)
- [ ] **Integration tests**: Realistic multi-instruction scenarios
- [ ] **Negative tests**: Tests for expected failures
- [ ] **PDA tests**: Tests for seed collisions
- [ ] **Edge cases**: Zero amounts, max values, overflow boundaries
- [ ] **Concurrency**: Tests for transaction ordering issues
- [ ] **Devnet testing**: Deployed and tested on devnet

```rust
// Example test structure
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normal_case() {
        // Test expected behavior
    }

    #[test]
    #[should_panic(expected = "Overflow")]
    fn test_overflow() {
        // Test arithmetic overflow protection
    }

    #[test]
    fn test_unauthorized_access() {
        // Test fails with wrong signer
    }

    #[test]
    fn test_edge_case_zero_amount() {
        // Test zero amount handling
    }
}
```
