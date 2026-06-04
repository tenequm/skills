# Solana Program Security & Validation

This reference provides comprehensive security guidance for native Rust Solana program development, covering validation patterns, common vulnerabilities, and defensive programming practices.

## Table of Contents

1. [Security Mindset](#security-mindset)
2. [Core Validation Patterns](#core-validation-patterns)
3. [Common Vulnerabilities](#common-vulnerabilities)
4. [Input Validation](#input-validation)
5. [State Management Security](#state-management-security)
6. [Arithmetic Safety](#arithmetic-safety)
7. [Re-entrancy Protection](#re-entrancy-protection)
8. [Security Checklist](#security-checklist)

---

## Security Mindset

### Think Like an Attacker

**The fundamental principle of secure programming: ask "How do I break this?"**

Presented at Breakpoint 2021 by [Neodyme](https://workshop.neodyme.io/), this mindset shift is critical:

- **Don't just test expected functionality** - explore how it can be broken
- **All programs can be exploited** - the goal is to make it as difficult as possible
- **You control nothing** - once deployed, you can't control what transactions are sent
- **Assume malicious input** - every account, every parameter, every edge case

### The Harsh Reality

```
┌─────────────────────────────────────────┐
│ Your Program (Deployed)                 │
├─────────────────────────────────────────┤
│ • No control over incoming transactions │
│ • No control over accounts passed in    │
│ • No control over instruction data      │
│ • No control over timing                │
└─────────────────────────────────────────┘
           ▲            ▲            ▲
           │            │            │
     Legitimate    Malicious     Buggy
        User        Attacker     Client
```

**Your only control:** How your program handles inputs.

### Security is Not Optional

**Example Impact:**

Without proper validation, a simple "update note" function becomes:
- ❌ Anyone can update anyone's notes
- ❌ Drain program funds
- ❌ Corrupt global state
- ❌ Brick the entire program

**With validation:**
- ✅ Only note author can update
- ✅ Funds are protected
- ✅ State remains consistent
- ✅ Program operates as intended

---

## Core Validation Patterns

### 1. Signer Checks

**Purpose:** Verify that an account signed the transaction, authorizing the operation.

**When Required:**
- Transferring funds from an account
- Modifying user-specific data
- Any privileged operation

**Pattern:**

```rust
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    program_error::ProgramError,
    msg,
};

pub fn check_signer(account: &AccountInfo) -> ProgramResult {
    if !account.is_signer {
        msg!("Missing required signature");
        return Err(ProgramError::MissingRequiredSignature);
    }
    Ok(())
}
```

**Real-World Example:**

```rust
pub fn update_user_profile(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    new_name: String,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let user = next_account_info(account_info_iter)?;
    let profile_pda = next_account_info(account_info_iter)?;

    // CRITICAL: Verify user signed the transaction
    if !user.is_signer {
        msg!("User must sign to update profile");
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Validate PDA belongs to this user
    let (expected_pda, _) = Pubkey::find_program_address(
        &[b"profile", user.key.as_ref()],
        program_id,
    );

    if expected_pda != *profile_pda.key {
        msg!("Profile PDA doesn't match user");
        return Err(ProgramError::InvalidAccountData);
    }

    // Safe to update
    let mut profile = UserProfile::try_from_slice(&profile_pda.data.borrow())?;
    profile.name = new_name;
    profile.serialize(&mut &mut profile_pda.data.borrow_mut()[..])?;

    Ok(())
}
```

### 2. Ownership Checks

**Purpose:** Verify an account is owned by the expected program.

**When Required:**
- Before reading/writing account data
- When validating PDAs
- Before performing any account-specific operations

**Pattern:**

```rust
pub fn check_ownership(
    account: &AccountInfo,
    expected_owner: &Pubkey,
) -> ProgramResult {
    if account.owner != expected_owner {
        msg!("Account owner mismatch");
        return Err(ProgramError::IllegalOwner);
    }
    Ok(())
}
```

**Common Use Cases:**

```rust
// 1. Verify program owns its PDA
if note_pda.owner != program_id {
    msg!("Note account not owned by this program");
    return Err(ProgramError::IllegalOwner);
}

// 2. Verify account owned by System Program (user wallet)
use solana_program::system_program;

if wallet.owner != &system_program::ID {
    msg!("Expected a system account (wallet)");
    return Err(ProgramError::IllegalOwner);
}

// 3. Verify account owned by Token Program
use spl_token::ID as TOKEN_PROGRAM_ID;

if token_account.owner != &TOKEN_PROGRAM_ID {
    msg!("Expected a token account");
    return Err(ProgramError::IllegalOwner);
}
```

### 3. PDA Validation

**Purpose:** Ensure a provided PDA matches the expected derivation.

**Critical for Security:** Multiple bumps can derive different PDAs. Always use canonical bump.

**Pattern:**

```rust
pub fn validate_pda(
    pda_account: &AccountInfo,
    seeds: &[&[u8]],
    program_id: &Pubkey,
) -> Result<u8, ProgramError> {
    // Derive expected PDA with canonical bump
    let (expected_pda, bump_seed) = Pubkey::find_program_address(seeds, program_id);

    // Validate match
    if expected_pda != *pda_account.key {
        msg!("Invalid PDA derivation");
        return Err(ProgramError::InvalidSeeds);
    }

    Ok(bump_seed)
}
```

**Complete Validation:**

```rust
pub fn validate_user_vault(
    program_id: &Pubkey,
    user: &AccountInfo,
    vault_pda: &AccountInfo,
) -> ProgramResult {
    // 1. Derive expected PDA
    let (expected_pda, _bump) = Pubkey::find_program_address(
        &[b"vault", user.key.as_ref()],
        program_id,
    );

    // 2. Validate address match
    if expected_pda != *vault_pda.key {
        msg!("Vault PDA seeds don't match");
        return Err(ProgramError::InvalidSeeds);
    }

    // 3. Validate ownership
    if vault_pda.owner != program_id {
        msg!("Vault not owned by program");
        return Err(ProgramError::IllegalOwner);
    }

    // 4. Validate initialization
    let vault_data = VaultAccount::try_from_slice(&vault_pda.data.borrow())?;
    if !vault_data.is_initialized {
        msg!("Vault not initialized");
        return Err(ProgramError::UninitializedAccount);
    }

    Ok(())
}
```

### 4. Initialization Checks

**Purpose:** Prevent re-initialization or use of uninitialized accounts.

**Pattern: Discriminator Field**

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct AccountData {
    pub is_initialized: bool,
    // ... other fields
}

// On creation - ensure NOT initialized
if account_data.is_initialized {
    msg!("Account already initialized");
    return Err(ProgramError::AccountAlreadyInitialized);
}

account_data.is_initialized = true;

// On update - ensure IS initialized
if !account_data.is_initialized {
    msg!("Account not initialized");
    return Err(ProgramError::UninitializedAccount);
}
```

**Advanced: Enum Discriminator**

```rust
#[derive(BorshSerialize, BorshDeserialize, PartialEq)]
pub enum AccountState {
    Uninitialized,
    Initialized,
    Frozen,
    Closed,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct GameAccount {
    pub state: AccountState,
    pub player: Pubkey,
    pub score: u64,
}

// Validation
let account = GameAccount::try_from_slice(&account_info.data.borrow())?;

match account.state {
    AccountState::Uninitialized => {
        msg!("Account not initialized");
        return Err(ProgramError::UninitializedAccount);
    }
    AccountState::Frozen => {
        msg!("Account is frozen");
        return Err(ProgramError::InvalidAccountData);
    }
    AccountState::Closed => {
        msg!("Account is closed");
        return Err(ProgramError::InvalidAccountData);
    }
    AccountState::Initialized => {
        // Proceed
    }
}
```

### 5. Account Type Validation

**Purpose:** Ensure account contains the expected data structure.

**Pattern: Type Discriminator**

```rust
#[derive(BorshSerialize, BorshDeserialize, PartialEq)]
#[repr(u8)]
pub enum AccountType {
    Uninitialized = 0,
    UserProfile = 1,
    GameState = 2,
    Leaderboard = 3,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct GenericAccount {
    pub account_type: AccountType,
    // ... rest of data varies by type
}

// Validation
pub fn validate_account_type(
    account_info: &AccountInfo,
    expected_type: AccountType,
) -> ProgramResult {
    let account = GenericAccount::try_from_slice(&account_info.data.borrow())?;

    if account.account_type != expected_type {
        msg!("Unexpected account type");
        return Err(ProgramError::InvalidAccountData);
    }

    Ok(())
}
```

### 6. Writable Validation

**Purpose:** Ensure accounts that need modification are marked writable.

**Pattern:**

```rust
pub fn check_writable(account: &AccountInfo) -> ProgramResult {
    if !account.is_writable {
        msg!("Account must be writable");
        return Err(ProgramError::InvalidAccountData);
    }
    Ok(())
}
```

**Note:** Runtime enforces this, but explicit checks improve clarity and error messages.

---

## Common Vulnerabilities

### 1. Missing Signer Check

**Vulnerability:**

```rust
// ❌ VULNERABLE - no signer check
pub fn withdraw_funds(
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let user = &accounts[0];
    let vault = &accounts[1];

    // Anyone can call this to withdraw anyone's funds!
    **user.lamports.borrow_mut() += amount;
    **vault.lamports.borrow_mut() -= amount;

    Ok(())
}
```

**Exploit:**
```
Attacker creates transaction:
- Passes victim's account as user
- Drains vault to victim's account
- Profits by intercepting the transaction or social engineering
```

**Fix:**

```rust
// ✅ SECURE - with signer check
pub fn withdraw_funds(
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let user = &accounts[0];
    let vault = &accounts[1];

    if !user.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    **user.lamports.borrow_mut() += amount;
    **vault.lamports.borrow_mut() -= amount;

    Ok(())
}
```

### 2. Missing Ownership Check

**Vulnerability:**

```rust
// ❌ VULNERABLE - no ownership check
pub fn update_score(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    new_score: u64,
) -> ProgramResult {
    let player_account = &accounts[0];

    // Could be ANY account with matching data structure!
    let mut player = PlayerData::try_from_slice(&player_account.data.borrow())?;
    player.score = new_score;
    player.serialize(&mut &mut player_account.data.borrow_mut()[..])?;

    Ok(())
}
```

**Exploit:**
```
Attacker creates a fake account:
- Owned by attacker's program
- Has same data structure
- Passes it to victim program
- Victim program modifies attacker's account!
```

**Fix:**

```rust
// ✅ SECURE - with ownership check
pub fn update_score(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    new_score: u64,
) -> ProgramResult {
    let player_account = &accounts[0];

    // Verify ownership
    if player_account.owner != program_id {
        return Err(ProgramError::IllegalOwner);
    }

    let mut player = PlayerData::try_from_slice(&player_account.data.borrow())?;
    player.score = new_score;
    player.serialize(&mut &mut player_account.data.borrow_mut()[..])?;

    Ok(())
}
```

### 3. PDA Substitution Attack

**Vulnerability:**

```rust
// ❌ VULNERABLE - accepts any PDA
pub fn claim_reward(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let user = &accounts[0];
    let reward_pda = &accounts[1];

    // No PDA validation!
    let mut reward = RewardData::try_from_slice(&reward_pda.data.borrow())?;
    reward.claimed = true;
    reward.serialize(&mut &mut reward_pda.data.borrow_mut()[..])?;

    Ok(())
}
```

**Exploit:**
```
Attacker passes someone else's reward PDA:
- Creates transaction with victim's reward PDA
- Claims victim's rewards
- Victim loses rewards
```

**Fix:**

```rust
// ✅ SECURE - validates PDA derivation
pub fn claim_reward(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let user = &accounts[0];
    let reward_pda = &accounts[1];

    // Validate PDA belongs to this user
    let (expected_pda, _) = Pubkey::find_program_address(
        &[b"reward", user.key.as_ref()],
        program_id,
    );

    if expected_pda != *reward_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    let mut reward = RewardData::try_from_slice(&reward_pda.data.borrow())?;
    reward.claimed = true;
    reward.serialize(&mut &mut reward_pda.data.borrow_mut()[..])?;

    Ok(())
}
```

### 4. Non-Canonical Bump

**Vulnerability:**

```rust
// ❌ VULNERABLE - accepts user-provided bump
pub fn update_data(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    bump: u8,  // User provides bump!
) -> ProgramResult {
    let user = &accounts[0];
    let data_pda = &accounts[1];

    // Uses user's bump - could derive DIFFERENT PDA!
    let derived_pda = Pubkey::create_program_address(
        &[b"data", user.key.as_ref(), &[bump]],
        program_id,
    )?;

    if derived_pda != *data_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // Proceeds with potentially wrong PDA
    // ...
}
```

**Exploit:**
```
Multiple bumps derive different valid PDAs:
- Canonical bump 254: User A's PDA
- Bump 253: User B's PDA (also valid!)
- Attacker uses bump 253 to access User B's data
```

**Fix:**

```rust
// ✅ SECURE - uses canonical bump only
pub fn update_data(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let user = &accounts[0];
    let data_pda = &accounts[1];

    // Always use find_program_address (canonical bump)
    let (expected_pda, _bump) = Pubkey::find_program_address(
        &[b"data", user.key.as_ref()],
        program_id,
    );

    if expected_pda != *data_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // Safe - validated with canonical bump
    // ...
}
```

### 5. Type Cosplay Attack

**Vulnerability:**

```rust
// ❌ VULNERABLE - assumes account type
pub fn admin_withdraw(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let admin_config = &accounts[0];

    // No type validation!
    let config = AdminConfig::try_from_slice(&admin_config.data.borrow())?;

    // Proceeds assuming it's actually an AdminConfig
    // ...
}
```

**Exploit:**
```
Attacker creates fake account:
- UserProfile with same memory layout as AdminConfig
- First field happens to match admin pubkey format
- Deserializes successfully as AdminConfig
- Attacker gains admin privileges!
```

**Fix:**

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct AdminConfig {
    pub discriminator: [u8; 8],  // Type identifier
    pub admin: Pubkey,
    // ... other fields
}

const ADMIN_CONFIG_DISCRIMINATOR: [u8; 8] = [1, 2, 3, 4, 5, 6, 7, 8];

// ✅ SECURE - validates type
pub fn admin_withdraw(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let admin_config = &accounts[0];

    let config = AdminConfig::try_from_slice(&admin_config.data.borrow())?;

    // Validate discriminator
    if config.discriminator != ADMIN_CONFIG_DISCRIMINATOR {
        msg!("Invalid account type");
        return Err(ProgramError::InvalidAccountData);
    }

    // Safe - type validated
    // ...
}
```

### 6. Uninitialized Account Reuse

**Vulnerability:**

```rust
// ❌ VULNERABLE - no initialization check
pub fn update_balance(
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let balance_account = &accounts[0];

    let mut balance = BalanceData::try_from_slice(&balance_account.data.borrow())?;

    // What if this account was never initialized?
    // Default values could lead to undefined behavior
    balance.amount += amount;

    balance.serialize(&mut &mut balance_account.data.borrow_mut()[..])?;
    Ok(())
}
```

**Fix:**

```rust
// ✅ SECURE - checks initialization
pub fn update_balance(
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let balance_account = &accounts[0];

    let mut balance = BalanceData::try_from_slice(&balance_account.data.borrow())?;

    if !balance.is_initialized {
        msg!("Account not initialized");
        return Err(ProgramError::UninitializedAccount);
    }

    balance.amount += amount;
    balance.serialize(&mut &mut balance_account.data.borrow_mut()[..])?;
    Ok(())
}
```

---

## Input Validation

### Validate All Input Data

**Never trust instruction data.** Always validate constraints.

```rust
pub fn allocate_stat_points(
    accounts: &[AccountInfo],
    strength: u8,
    agility: u8,
    intelligence: u8,
) -> ProgramResult {
    let character_account = &accounts[0];
    let mut character = Character::try_from_slice(&character_account.data.borrow())?;

    // 1. Validate individual stat caps
    let new_strength = character.strength.checked_add(strength)
        .ok_or(ProgramError::ArithmeticOverflow)?;

    if new_strength > 100 {
        msg!("Strength cannot exceed 100");
        return Err(ProgramError::InvalidArgument);
    }

    // 2. Validate total points spent
    let total_spent = (strength as u64)
        .checked_add(agility as u64)
        .and_then(|sum| sum.checked_add(intelligence as u64))
        .ok_or(ProgramError::ArithmeticOverflow)?;

    if total_spent > character.available_points {
        msg!("Insufficient available points");
        return Err(ProgramError::InsufficientFunds);
    }

    // 3. Safe to apply
    character.strength = new_strength;
    character.agility += agility;
    character.intelligence += intelligence;
    character.available_points -= total_spent;

    character.serialize(&mut &mut character_account.data.borrow_mut()[..])?;
    Ok(())
}
```

### String Length Validation

```rust
pub fn set_username(
    accounts: &[AccountInfo],
    username: String,
) -> ProgramResult {
    // Validate length
    if username.len() < 3 {
        msg!("Username too short (min 3 characters)");
        return Err(ProgramError::InvalidArgument);
    }

    if username.len() > 20 {
        msg!("Username too long (max 20 characters)");
        return Err(ProgramError::InvalidArgument);
    }

    // Validate characters (alphanumeric only)
    if !username.chars().all(|c| c.is_alphanumeric()) {
        msg!("Username must be alphanumeric");
        return Err(ProgramError::InvalidArgument);
    }

    // Safe to use
    // ...
}
```

### Enum Validation

```rust
#[derive(BorshDeserialize)]
#[repr(u8)]
pub enum Rarity {
    Common = 0,
    Uncommon = 1,
    Rare = 2,
    Epic = 3,
    Legendary = 4,
}

pub fn create_item(
    accounts: &[AccountInfo],
    rarity_value: u8,
) -> ProgramResult {
    // Validate enum range
    if rarity_value > 4 {
        msg!("Invalid rarity value");
        return Err(ProgramError::InvalidArgument);
    }

    let rarity: Rarity = unsafe {
        std::mem::transmute(rarity_value)
    };

    // Safe to use
    // ...
}
```

---

## State Management Security

### Avoid Race Conditions

**Problem:** Multiple transactions modifying shared state.

**Solution:** Use account-level locking and atomic operations.

```rust
pub fn claim_limited_reward(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let user = &accounts[0];
    let global_pool = &accounts[1];
    let user_claim = &accounts[2];

    // Load global state
    let mut pool = RewardPool::try_from_slice(&global_pool.data.borrow())?;

    // Check availability
    if pool.claimed >= pool.total_rewards {
        msg!("No rewards remaining");
        return Err(ProgramError::InsufficientFunds);
    }

    // Check user hasn't claimed
    let mut claim = UserClaim::try_from_slice(&user_claim.data.borrow())?;
    if claim.has_claimed {
        msg!("User already claimed");
        return Err(ProgramError::Custom(0));
    }

    // Atomically update both accounts
    pool.claimed += 1;
    claim.has_claimed = true;

    pool.serialize(&mut &mut global_pool.data.borrow_mut()[..])?;
    claim.serialize(&mut &mut user_claim.data.borrow_mut()[..])?;

    Ok(())
}
```

**Note:** Solana's account locking prevents true race conditions within a single transaction, but be aware of state assumptions across multiple transactions.

### Prevent State Corruption

**Always validate state transitions:**

```rust
#[derive(BorshSerialize, BorshDeserialize, PartialEq)]
pub enum GameState {
    NotStarted,
    InProgress,
    Finished,
}

pub fn start_game(
    accounts: &[AccountInfo],
) -> ProgramResult {
    let game_account = &accounts[0];
    let mut game = Game::try_from_slice(&game_account.data.borrow())?;

    // Validate current state
    if game.state != GameState::NotStarted {
        msg!("Game already started or finished");
        return Err(ProgramError::InvalidAccountData);
    }

    // Transition state
    game.state = GameState::InProgress;
    game.start_time = Clock::get()?.unix_timestamp;

    game.serialize(&mut &mut game_account.data.borrow_mut()[..])?;
    Ok(())
}
```

---

## Arithmetic Safety

### Always Use Checked Math

**Rust default:** Integer overflow/underflow panics in debug, wraps in release.

**Solana requirement:** Use checked operations to prevent wrapping.

```rust
// ❌ DANGEROUS - can overflow/underflow
let total = a + b;
let remaining = balance - withdrawal;

// ✅ SAFE - returns error on overflow/underflow
let total = a.checked_add(b)
    .ok_or(ProgramError::ArithmeticOverflow)?;

let remaining = balance.checked_sub(withdrawal)
    .ok_or(ProgramError::InsufficientFunds)?;
```

### Common Checked Operations

```rust
// Addition
let sum = a.checked_add(b)
    .ok_or(ProgramError::ArithmeticOverflow)?;

// Subtraction
let diff = a.checked_sub(b)
    .ok_or(ProgramError::InsufficientFunds)?;

// Multiplication
let product = a.checked_mul(b)
    .ok_or(ProgramError::ArithmeticOverflow)?;

// Division
let quotient = a.checked_div(b)
    .ok_or(ProgramError::InvalidArgument)?;  // b could be 0

// Power
let power = base.checked_pow(exponent)
    .ok_or(ProgramError::ArithmeticOverflow)?;
```

### Compound Operations

```rust
// Calculate: (a + b) * c / d
let result = a.checked_add(b)
    .and_then(|sum| sum.checked_mul(c))
    .and_then(|product| product.checked_div(d))
    .ok_or(ProgramError::ArithmeticOverflow)?;
```

### Precision Loss

**Be careful with division:**

```rust
// ❌ Loses precision
let fee = amount / 100;  // 1.5% becomes 1%

// ✅ Better - multiply first, then divide
let fee = amount.checked_mul(15)
    .and_then(|v| v.checked_div(1000))
    .ok_or(ProgramError::ArithmeticOverflow)?;
```

---

## Re-entrancy Protection

### Solana's Built-in Protection

**Good news:** Solana provides strong protection against traditional re-entrancy:

- **Account locking:** Accounts are locked during transaction execution
- **No concurrent modification:** Same account can't be modified by multiple instructions simultaneously
- **Atomic transactions:** Either all instructions succeed or all fail

### Residual Risks

**Cross-program state assumptions:**

```rust
// ❌ RISKY - state can change between checks
pub fn risky_operation(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let vault = &accounts[0];
    let mut vault_data = VaultData::try_from_slice(&vault.data.borrow())?;

    // Check balance
    let balance = **vault.lamports.borrow();
    if balance < 1000 {
        return Err(ProgramError::InsufficientFunds);
    }

    // CPI that might modify vault
    invoke(&some_instruction, accounts)?;

    // Balance might have changed!
    // Don't rely on previous check
    **vault.lamports.borrow_mut() -= 1000;  // Could underflow!

    Ok(())
}
```

**✅ Better:**

```rust
pub fn safe_operation(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let vault = &accounts[0];

    // CPI first
    invoke(&some_instruction, accounts)?;

    // Check and modify atomically
    let balance = **vault.lamports.borrow();
    let new_balance = balance.checked_sub(1000)
        .ok_or(ProgramError::InsufficientFunds)?;

    **vault.lamports.borrow_mut() = new_balance;

    Ok(())
}
```

---

## Security Checklist

### Pre-Deployment Checklist

**Account Validation:**
- ✅ All signers verified with `is_signer`
- ✅ All account owners checked
- ✅ All PDAs validated with canonical bump
- ✅ All accounts checked for initialization
- ✅ Account types validated (discriminators)
- ✅ Writable accounts verified

**Input Validation:**
- ✅ All numeric inputs range-checked
- ✅ All string inputs length-limited
- ✅ All enum values validated
- ✅ All business logic constraints enforced

**Arithmetic:**
- ✅ All additions use `checked_add`
- ✅ All subtractions use `checked_sub`
- ✅ All multiplications use `checked_mul`
- ✅ All divisions check for zero
- ✅ No unsafe casting that could overflow

**State Management:**
- ✅ State transitions validated
- ✅ Initialization flags checked
- ✅ No assumptions across CPI boundaries
- ✅ Atomicity maintained

**Error Handling:**
- ✅ All errors properly propagated
- ✅ Meaningful error messages
- ✅ No silent failures
- ✅ Proper cleanup on errors

### Testing Checklist

**Security Testing:**
- ✅ Test with missing signers
- ✅ Test with wrong account owners
- ✅ Test with wrong PDAs (non-canonical bumps)
- ✅ Test with uninitialized accounts
- ✅ Test with re-initialized accounts
- ✅ Test integer overflow/underflow
- ✅ Test boundary conditions
- ✅ Test with maximum values
- ✅ Test with malicious input

**Fuzzing:**
- ✅ Random account combinations
- ✅ Random instruction data
- ✅ Random ordering
- ✅ Edge case values

---

## Summary

**Core Security Principles:**

1. **Validate Everything** - Assume all inputs are malicious
2. **Fail Fast** - Return errors immediately when validation fails
3. **Use Checked Math** - Prevent integer overflow/underflow
4. **Think Like an Attacker** - Ask "How do I break this?"
5. **Test Malicious Cases** - Don't just test happy paths

**The Three Pillars of Account Security:**

```rust
// 1. Signer Check
if !account.is_signer {
    return Err(ProgramError::MissingRequiredSignature);
}

// 2. Ownership Check
if account.owner != expected_owner {
    return Err(ProgramError::IllegalOwner);
}

// 3. PDA Validation (if applicable)
let (expected_pda, _) = Pubkey::find_program_address(&seeds, program_id);
if expected_pda != *account.key {
    return Err(ProgramError::InvalidSeeds);
}
```

**Remember:** Once deployed, you have no control over what transactions are sent to your program. Your only defense is rigorous validation.

Security is not a feature—it's a requirement.
