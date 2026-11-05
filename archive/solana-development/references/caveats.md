# Important Caveats

Critical limitations, quirks, and gotchas in Solana and Anchor development that every security reviewer must know.

## Anchor Framework Limitations

### 1. `init_if_needed` Re-initialization Risk

```rust
// Dangerous: Can bypass initialization logic
#[account(init_if_needed, payer = user, space = ...)]
pub user_account: Account<'info, UserAccount>,
```

**Issue:** If account already exists, initialization is skipped entirely. Existing malicious or inconsistent data is not validated.

**When to use:** Only when you explicitly validate existing accounts in instruction logic.

### 2. `AccountLoader` Missing Discriminator Check

```rust
// Does NOT validate discriminator by default!
#[account(mut)]
pub user: AccountLoader<'info, User>,
```

**Issue:** `AccountLoader` is for zero-copy accounts and doesn't check the account discriminator automatically. Enables type cosplay attacks.

**Solution:** Use `Account<'info, T>` when possible, or add manual discriminator check.

### 3. `close` Constraint Ordering

```rust
// ❌ Wrong: close must be last
#[account(
    close = receiver,
    mut,
    has_one = authority
)]

// ✅ Correct: close is last
#[account(
    mut,
    has_one = authority,
    close = receiver
)]
```

**Issue:** Anchor processes constraints in order. If `close` isn't last, subsequent constraints may check zeroed account.

### 4. Space Calculation Errors Are Permanent

```rust
// If this space is wrong, account is unusable!
#[account(
    init,
    payer = user,
    space = 8 + 32  // Too small = can't deserialize later!
)]
pub user_account: Account<'info, UserAccount>,
```

**Issue:** Once initialized, account size is fixed. Too small = deserialization fails. Too large = wasted rent.

**Solution:** Always use `InitSpace` derive macro:
```rust
#[account]
#[derive(InitSpace)]
pub struct UserAccount {
    pub authority: Pubkey,
    #[max_len(100)]
    pub name: String,
}

// Then use:
space = 8 + UserAccount::INIT_SPACE
```

### 5. `constraint` Expression Limitations

```rust
// constraint expressions can't call functions that return Results!
#[account(
    constraint = some_validation(account.value)? @ ErrorCode::Invalid  // Compile error!
)]
```

**Issue:** Constraint expressions must be simple boolean checks. Cannot use `?` operator.

**Solution:** Validate in instruction body for complex checks.

## Solana Runtime Quirks

### 1. Account Data Persists After Zeroing Lamports

```rust
// Within same transaction:
**account.lamports.borrow_mut() = 0;
let data = account.try_borrow_data()?;  // Still readable!
```

**Issue:** Account data remains accessible within the transaction even after lamports are zeroed. Only garbage collected after transaction completes.

**Implication:** Always check lamports before reading account data.

### 2. Non-Canonical PDA Bumps

```rust
// Multiple PDAs possible with different bumps!
let (pda_255, bump_255) = Pubkey::find_program_address(seeds, program_id);  // bump = 255
let (pda_254, bump_254) = Pubkey::create_program_address(&[seeds, &[254]], program_id);  // Also valid!
```

**Issue:** Same seeds can derive multiple PDAs with different bumps. Creates confusion and potential exploits.

**Solution:** Always use canonical bump (255 counting down to first valid). Anchor's `bump` constraint enforces this.

### 3. Compute Budget Limits

| Network | Base Compute Units | With Optimization |
|---------|-------------------|-------------------|
| Mainnet | 200,000 | Up to 1,400,000 (with request) |
| Devnet  | 200,000 | Up to 1,400,000 |

**Issue:** Complex programs can exceed compute budget, causing transaction failure.

**Optimization strategies:**
- Minimize CPIs (each costs ~1000 CU)
- Use `AccountLoader` for large accounts
- Avoid loops with variable length
- Request higher compute budget: `ComputeBudgetProgram::set_compute_unit_limit()`

### 4. Transaction Size Limit

**Hard limit:** ~1232 bytes for transaction

**Implications:**
- Limits number of accounts (~35-40 accounts typical max)
- Large instructions need Account Compression or chunking
- Can't pass large data directly in instruction

**Solutions:**
- Use PDAs to store large data
- Break operations into multiple transactions
- Use lookup tables for frequent accounts

### 5. Account Snapshot Loading

```rust
let balance_before = ctx.accounts.vault.balance;
// CPI happens here
// balance_before is STALE - account was loaded before CPI
```

**Issue:** Accounts are loaded as snapshots at transaction start. Modifications during transaction (via CPIs) don't update the loaded data.

**Solution:** Call `.reload()` after any CPI that might modify the account.

## Token Program Gotchas

### 1. ATA Addresses Are Deterministic But Not Guaranteed

```rust
let ata = get_associated_token_address(&owner, &mint);
// ata address is deterministic but account might not exist!
```

**Issue:** ATA address can be calculated but account may not be initialized.

**Solution:** Check account exists and is initialized before use, or use `init_if_needed` with proper validation.

### 2. Delegates Don't Automatically Reset

```rust
// After transfer of ownership:
token_account.owner = new_owner;
// BUT: delegate and delegated_amount are NOT reset!
```

**Issue:** Changing owner doesn't clear delegate/close authority. Old delegate can still spend.

**Solution:** Explicitly reset authorities when changing ownership:
```rust
account.delegate = COption::None;
account.delegated_amount = 0;
if account.is_native() {
    account.close_authority = COption::None;
}
```

### 3. Token-2022 Extension Rent

**Issue:** Each extension adds rent cost. Account size varies by extensions enabled.

**Extensions and their sizes:**
- Transfer Fee: ~83 bytes
- Transfer Hook: ~107 bytes
- Permanent Delegate: ~36 bytes
- Interest Bearing: ~40 bytes

**Solution:** Calculate rent based on all enabled extensions.

### 4. Token-2022 Transfer Hooks Can Be Malicious

```rust
// Transfer hook can call arbitrary program!
pub struct TransferHookAccount {
    pub program_id: Pubkey,  // Could be malicious
}
```

**Issue:** Transfer hook extensions allow calling external program during transfers. Malicious hook can fail transaction or drain funds.

**Solution:**
- Validate transfer hook program if accepting specific tokens
- Consider disallowing tokens with transfer hooks
- Use Anchor's `TransferChecked` instruction

## Testing Blind Spots

### 1. Concurrent Transaction Ordering

**Issue:** Tests typically run transactions sequentially. In production, concurrent transactions can interleave in unexpected ways.

**Vulnerability example:**
```rust
// Transaction 1: Check balance = 100
// Transaction 2: Withdraw 80 (balance now 20)
// Transaction 1: Withdraw 80 (uses stale check, balance now -60!)
```

**Mitigation:**
- Use atomic operations
- Reload accounts before critical operations
- Design for idempotency

### 2. Account Rent Reclaim Attacks

**Issue:** When account rent falls below minimum, validator can reclaim the account. Tests don't simulate this.

**Solution:** Ensure all accounts are rent-exempt (2+ years of rent).

### 3. Sysvar Manipulation in Tests

```rust
// In tests, you can set arbitrary clock values
ctx.accounts.clock = Clock { unix_timestamp: attacker_value, ... };
```

**Issue:** Tests may not catch reliance on tamper-resistant sysvars.

**Solution:** In production, always load sysvars from official sysvar accounts:
```rust
pub clock: Sysvar<'info, Clock>,  // Validated address
```

### 4. Devnet vs Mainnet Differences

| Aspect | Devnet | Mainnet |
|--------|--------|---------|
| Oracle prices | Often stale/fake | Real-time |
| Program versions | May differ | Stable versions |
| Compute limits | More lenient | Strict |
| Congestion | Minimal | Can be high |
| Token availability | Test tokens | Real value |

**Issue:** Programs tested only on devnet may fail on mainnet.

**Solution:** Test on mainnet-fork or mainnet with small amounts before full deployment.

## Rust-Specific Gotchas

### 1. `unwrap()` Panics

```rust
// Panics kill the entire transaction!
let value = some_option.unwrap();  // ❌ Never do this
```

**Solution:** Always use proper error handling:
```rust
let value = some_option.ok_or(ErrorCode::MissingValue)?;
```

### 2. Integer Division Truncation

```rust
let result = 5 / 2;  // result = 2, not 2.5!
```

**Issue:** Integer division truncates, potentially causing precision loss in financial calculations.

**Solution:** Use `Decimal` type for precise calculations, or multiply before divide:
```rust
let result = (5 * PRECISION) / 2 / PRECISION;
```

### 3. Overflow in Debug vs Release

```rust
// Debug mode: panics on overflow
// Release mode: wraps silently!
let x: u8 = 255;
let y = x + 1;  // Debug: panic, Release: y = 0
```

**Solution:** Always use `checked_*` methods - they work same in debug and release.

## Cross-Program Invocation (CPI) Gotchas

### 1. CPI Success Doesn't Guarantee Correct State

```rust
// CPI returns success but state may be unexpected
invoke(&transfer_instruction, &accounts)?;
// Transfer succeeded but amount might be different due to fees!
```

**Solution:** Reload and validate account state after CPI.

### 2. Signer Seeds Must Be Exact

```rust
// Seeds for signing must match PDA derivation exactly
let seeds = &[
    b"vault",
    user.key().as_ref(),
    &[bump],  // Must be same bump used to derive PDA
];

invoke_signed(&instruction, &accounts, &[seeds])?;
```

**Issue:** Wrong seeds = "signature verification failed" error.

### 3. CPI Depth Limit

**Limit:** 4 levels of CPI depth

**Issue:** Program A → Program B → Program C → Program D → Program E (fails!)

**Solution:** Design programs to minimize CPI depth.

## Common Misunderstandings

### 1. "Anchor Prevents All Security Issues"

**False:** Anchor prevents some common issues (missing discriminators, wrong account types) but doesn't validate business logic, arithmetic, or authorization.

### 2. "Devnet Testing Is Sufficient"

**False:** Mainnet has different compute limits, real oracle data, congestion, and MEV considerations.

### 3. "One Audit Makes Code Secure"

**False:** Audits find issues in a snapshot. Code changes after audit reintroduce risk. Need continuous security review.

### 4. "`checked_*` Methods Are Slower"

**False:** Rust compiler optimizes these similarly to unchecked arithmetic. Always use checked methods.

### 5. "PDAs Can't Sign"

**True for external transactions, false for CPIs:** PDAs can sign CPIs using `invoke_signed` but can't sign transactions directly.

## Version-Specific Issues

### Anchor Version Compatibility

- **< 0.28**: No `InitSpace` derive, manual space calculation error-prone
- **< 0.29**: Different constraint syntax
- **0.30+**: Breaking changes in error handling and account initialization

**Solution:** Check `Cargo.toml` for version and consult [Anchor Changelog](https://github.com/coral-xyz/anchor/blob/master/CHANGELOG.md).

### Solana Version Differences

- **Pre-1.14**: Different fee structure
- **Pre-1.16**: No Address Lookup Tables
- **Pre-1.17**: No Token-2022

**Solution:** Verify target Solana version matches deployment network.

---

**Key Takeaway:** Many "obvious" assumptions about blockchain behavior don't hold in Solana. Always validate against actual runtime behavior, not assumptions from other chains.
