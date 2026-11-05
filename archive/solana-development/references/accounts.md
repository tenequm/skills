# Solana Account Model & Validation

This reference provides comprehensive coverage of Solana's account model, validation patterns, and rent mechanics for native Rust program development.

## Table of Contents

1. [Account Structure](#account-structure)
2. [Account Types](#account-types)
3. [Account Ownership](#account-ownership)
4. [Rent Mechanics](#rent-mechanics)
5. [Account Validation Patterns](#account-validation-patterns)
6. [Security Best Practices](#security-best-practices)
7. [Common Vulnerabilities](#common-vulnerabilities)

---

## Account Structure

Every Solana account is a location on the blockchain that stores data. All accounts have a uniform structure defined by the [`Account`](https://github.com/anza-xyz/agave/blob/v2.1.13/sdk/account/src/lib.rs#L48-L60) struct:

```rust
pub struct Account {
    /// lamports in the account
    pub lamports: u64,
    /// data held in this account
    pub data: Vec<u8>,
    /// the program that owns this account
    pub owner: Pubkey,
    /// this account's data contains a loaded program (and is now read-only)
    pub executable: bool,
    /// the epoch at which this account will next owe rent (DEPRECATED)
    pub rent_epoch: Epoch,
}
```

### Field Details

#### `lamports` (u64)
- The account's balance in lamports (1 SOL = 1,000,000,000 lamports)
- Every account must maintain a minimum balance for rent exemption
- Rent works as a **refundable deposit** - recoverable when account is closed
- Only the account owner can deduct lamports
- Any program can **add** lamports to any account

#### `data` (Vec<u8>)
- Maximum size: **10 MiB** (10,485,760 bytes)
- Can contain any arbitrary sequence of bytes
- Structure defined by the owning program
- Common patterns:
  - **Program accounts**: Executable code or pointer to program data account
  - **Data accounts**: Serialized state (often using Borsh)

#### `owner` (Pubkey)
- The program ID that owns this account
- **Critical security property**: Only the owner can modify `data` or deduct `lamports`
- Cannot be changed after account creation (except by System Program for newly created accounts)
- Newly created accounts start owned by System Program

#### `executable` (bool)
- `true`: Account contains executable program code
- `false`: Account is a data account
- Cannot be changed after being set to `true`

#### `rent_epoch` (Epoch)
- **DEPRECATED** - no longer used
- Remains in struct for backward compatibility
- Rent is now a one-time refundable deposit, not periodic payment

---

## Account Types

### 1. Program Accounts (Executable)

Program accounts contain executable code and are owned by a [loader program](https://solana.com/docs/core/programs#loader-programs).

**Simple Program Account Structure:**
```
┌─────────────────────────────────────┐
│ Program Account                     │
├─────────────────────────────────────┤
│ lamports: 1000000                   │
│ data: [executable bytecode]         │
│ owner: BPFLoaderUpgradeab1e...      │
│ executable: true                    │
└─────────────────────────────────────┘
```

**Loader-v3 Program Structure (Upgradeable):**

Programs deployed with loader-v3 use a **two-account model**:

```
┌─────────────────────────────────────┐
│ Program Account                     │
├─────────────────────────────────────┤
│ data: [pointer to program data]    │ ──┐
│ executable: true                    │   │
└─────────────────────────────────────┘   │
                                          │
                                          ▼
                              ┌─────────────────────────────────────┐
                              │ Program Data Account                │
                              ├─────────────────────────────────────┤
                              │ data: [actual executable bytecode]  │
                              │ executable: false                   │
                              └─────────────────────────────────────┘
```

This separation enables:
- Program upgrades without changing the program address
- Buffer accounts for staging uploads
- Separate upgrade authority management

### 2. Data Accounts (Non-Executable)

Data accounts store program state and are owned by programs (or System Program).

#### a) Program State Accounts

Accounts created and owned by your program to store application state:

```rust
// Example: Note account owned by a note-taking program
pub struct NoteAccount {
    pub is_initialized: bool,
    pub author: Pubkey,
    pub note_id: u64,
    pub content: String,
}
```

**Creation Process:**
1. Invoke System Program to create account (allocate space, transfer lamports)
2. System Program transfers ownership to your program
3. Your program initializes the account data

```rust
// Step 1: Create account via System Program CPI
invoke_signed(
    &system_instruction::create_account(
        initializer.key,
        pda_account.key,
        rent_lamports,
        account_len.try_into().unwrap(),
        program_id,  // Transfer ownership to our program
    ),
    &[initializer.clone(), pda_account.clone(), system_program.clone()],
    &[&[seeds, &[bump_seed]]],
)?;

// Step 2: Initialize the account data
let mut account_data = try_from_slice_unchecked::<NoteAccount>(&pda_account.data.borrow())?;
account_data.is_initialized = true;
account_data.author = *initializer.key;
account_data.note_id = note_id;
account_data.content = content;
account_data.serialize(&mut &mut pda_account.data.borrow_mut()[..])?;
```

#### b) System Accounts (Wallet Accounts)

Accounts owned by the System Program, typically used as user wallets:

```
┌─────────────────────────────────────┐
│ Wallet Account                      │
├─────────────────────────────────────┤
│ lamports: 1000000000                │
│ data: []                            │
│ owner: 11111111111111111111...      │ ← System Program
│ executable: false                   │
└─────────────────────────────────────┘
```

**Characteristics:**
- Can sign transactions (if you have the private key)
- Can pay transaction fees
- Can transfer SOL
- Created automatically when funded with SOL

#### c) Sysvar Accounts

Special accounts at predefined addresses that provide cluster state data:

| Sysvar | Address | Purpose |
|--------|---------|---------|
| Clock | `SysvarC1ock11111111111111111111111111111111` | Current slot, epoch, timestamp |
| Rent | `SysvarRent111111111111111111111111111111111` | Rent rate calculation |
| EpochSchedule | `SysvarEpochSchedu1e111111111111111111111111` | Epoch duration info |
| SlotHashes | `SysvarS1otHashes111111111111111111111111111` | Recent slot hashes |

**Access Pattern:**
```rust
use solana_program::sysvar::{clock::Clock, Sysvar};

let clock = Clock::get()?;
let current_timestamp = clock.unix_timestamp;
```

---

## Account Ownership

### Ownership Rules

**The Golden Rule:** Only the account owner can:
1. Modify the account's `data` field
2. Deduct lamports from the account

**Critical Security Implication:**
Programs must verify account ownership to prevent unauthorized state modifications.

### Ownership in Program Context

When a program receives accounts in an instruction:

```rust
pub fn process_instruction(
    program_id: &Pubkey,      // Your program's ID
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let data_account = next_account_info(account_info_iter)?;

    // CRITICAL: Verify ownership before modifying
    if data_account.owner != program_id {
        return Err(ProgramError::IllegalOwner);
    }

    // Safe to modify - we own this account
    // ...
}
```

### AccountInfo Structure

Programs receive accounts as `AccountInfo` structs:

```rust
pub struct AccountInfo<'a> {
    pub key: &'a Pubkey,              // Account address
    pub is_signer: bool,              // Did this account sign the transaction?
    pub is_writable: bool,            // Is this account writable in this instruction?
    pub lamports: Rc<RefCell<&'a mut u64>>,  // Mutable lamport balance
    pub data: Rc<RefCell<&'a mut [u8]>>,     // Mutable data
    pub owner: &'a Pubkey,            // Owner program ID
    pub executable: bool,             // Is this executable?
    pub rent_epoch: Epoch,            // Deprecated
}
```

**Key Operations:**

```rust
// Read data
let data = data_account.data.borrow();
let account_state = MyState::try_from_slice(&data)?;

// Write data
let mut data = data_account.data.borrow_mut();
account_state.serialize(&mut *data)?;

// Modify lamports
**data_account.lamports.borrow_mut() += transfer_amount;
```

---

## Rent Mechanics

Rent is a **refundable security deposit** required to store data on-chain. Despite the name "rent", it's not a recurring fee—it's a one-time deposit fully recoverable when the account is closed.

### Rent Calculation

Rent is proportional to account size:

```rust
use solana_program::rent::Rent;
use solana_program::sysvar::Sysvar;

// Get current rent rates
let rent = Rent::get()?;

// Calculate minimum balance for rent exemption
let account_size: usize = 1000;  // bytes
let rent_lamports = rent.minimum_balance(account_size);
```

**Formula:**
Based on [agave source](https://github.com/anza-xyz/agave/blob/v2.1.13/sdk/rent/src/lib.rs#L93-L97):

```rust
minimum_balance = (LAMPORTS_PER_BYTE_YEAR * account_size) * EXEMPTION_THRESHOLD / slots_per_year
```

**Constants:**
- `LAMPORTS_PER_BYTE_YEAR`: 3,480 lamports
- `EXEMPTION_THRESHOLD`: 2.0 (200% of annual rent)
- Typical cost: ~0.00139536 SOL per 100 bytes

### Rent Exemption

**All accounts must be rent-exempt.** This means:
- Account lamport balance ≥ `rent.minimum_balance(account.data.len())`
- The Solana runtime enforces this requirement
- Non-exempt accounts cannot be created

### Practical Example

```rust
pub fn create_data_account(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    data_size: usize,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let payer = next_account_info(account_info_iter)?;
    let new_account = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Calculate rent-exempt balance
    let rent = Rent::get()?;
    let rent_lamports = rent.minimum_balance(data_size);

    // Create account with rent-exempt balance
    invoke(
        &system_instruction::create_account(
            payer.key,
            new_account.key,
            rent_lamports,           // Must be rent-exempt
            data_size as u64,
            program_id,
        ),
        &[payer.clone(), new_account.clone(), system_program.clone()],
    )?;

    Ok(())
}
```

### Closing Accounts (Recovering Rent)

To recover rent when an account is no longer needed:

```rust
pub fn close_account(
    account_to_close: &AccountInfo,
    destination: &AccountInfo,
) -> ProgramResult {
    // Transfer all lamports to destination
    let dest_lamports = destination.lamports();
    **destination.lamports.borrow_mut() = dest_lamports
        .checked_add(**account_to_close.lamports.borrow())
        .ok_or(ProgramError::ArithmeticOverflow)?;

    // Zero out lamports in closed account
    **account_to_close.lamports.borrow_mut() = 0;

    // Zero out data (security best practice)
    let mut data = account_to_close.data.borrow_mut();
    data.fill(0);

    Ok(())
}
```

**Important:** The runtime will garbage-collect accounts with 0 lamports.

---

## Account Validation Patterns

Proper account validation is **critical for security**. Programs must verify accounts before using them.

### 1. Ownership Check

**Purpose:** Ensure an account is owned by the expected program.

**When to use:**
- Before reading/writing account data
- When validating PDAs
- When ensuring proper account initialization

```rust
// Basic ownership check
if account.owner != program_id {
    msg!("Account not owned by this program");
    return Err(ProgramError::IllegalOwner);
}

// PDA ownership check (essential for security)
if note_pda.owner != program_id {
    msg!("Invalid note account - wrong owner");
    return Err(ProgramError::IllegalOwner);
}
```

**Why it matters:**
Without ownership checks, malicious actors can pass arbitrary accounts that match the expected data format but are controlled by other programs or themselves.

### 2. Signer Check

**Purpose:** Verify that an account signed the transaction.

**When to use:**
- Before transferring funds from an account
- Before modifying user-specific data
- Before any privileged operation

```rust
if !initializer.is_signer {
    msg!("Missing required signature");
    return Err(ProgramError::MissingRequiredSignature);
}

// Practical example: Only allow note author to update
pub fn update_note(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    new_content: String,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let author = next_account_info(account_info_iter)?;
    let note_pda = next_account_info(account_info_iter)?;

    // Verify author signed the transaction
    if !author.is_signer {
        msg!("Author must sign to update note");
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Deserialize and verify author matches
    let note_data = NoteAccount::try_from_slice(&note_pda.data.borrow())?;
    if note_data.author != *author.key {
        msg!("Author mismatch");
        return Err(ProgramError::IllegalOwner);
    }

    // Safe to proceed with update
    // ...
}
```

### 3. Writable Check

**Purpose:** Verify an account is marked as writable.

**When to use:**
- Before modifying account data
- Before changing lamport balances
- Enforced automatically by runtime, but explicit checks improve clarity

```rust
if !account.is_writable {
    msg!("Account must be writable");
    return Err(ProgramError::InvalidAccountData);
}
```

### 4. Initialization Check

**Purpose:** Prevent re-initialization or use of uninitialized accounts.

**Pattern: Flag-based initialization**

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct DataAccount {
    pub is_initialized: bool,
    // ... other fields
}

impl DataAccount {
    pub fn is_initialized(&self) -> bool {
        self.is_initialized
    }
}

// On creation - check NOT initialized
if account_data.is_initialized() {
    msg!("Account already initialized");
    return Err(ProgramError::AccountAlreadyInitialized);
}

// On update - check IS initialized
if !account_data.is_initialized() {
    msg!("Account not initialized");
    return Err(ProgramError::UninitializedAccount);
}
```

### 5. PDA Validation

**Purpose:** Verify a provided PDA matches expected derivation.

**Critical for security:** Always validate PDAs using canonical bump.

```rust
pub fn validate_pda(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    note_id: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let author = next_account_info(account_info_iter)?;
    let note_pda = next_account_info(account_info_iter)?;

    // Derive expected PDA
    let (expected_pda, _bump) = Pubkey::find_program_address(
        &[
            author.key.as_ref(),
            note_id.to_le_bytes().as_ref(),
        ],
        program_id,
    );

    // Validate match
    if expected_pda != *note_pda.key {
        msg!("Invalid PDA - seeds don't match");
        return Err(ProgramError::InvalidSeeds);
    }

    Ok(())
}
```

**Why use `find_program_address` instead of accepting a bump?**
- Prevents bump seed manipulation attacks
- Ensures canonical bump is used
- Eliminates category of security vulnerabilities

### 6. Account Type Validation

**Purpose:** Ensure account contains expected data type.

**Pattern: Discriminator/Type Field**

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub enum AccountType {
    Uninitialized,
    UserProfile,
    GameState,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct AccountData {
    pub account_type: AccountType,
    // ... other fields
}

// Validation
let account_data = AccountData::try_from_slice(&account.data.borrow())?;
if !matches!(account_data.account_type, AccountType::UserProfile) {
    msg!("Wrong account type");
    return Err(ProgramError::InvalidAccountData);
}
```

---

## Security Best Practices

### 1. Always Validate Before Trusting

**Never assume accounts are correct.** Always validate:

```rust
pub fn secure_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let user = next_account_info(account_info_iter)?;
    let user_data_pda = next_account_info(account_info_iter)?;

    // ✅ Signer check
    if !user.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // ✅ Ownership check
    if user_data_pda.owner != program_id {
        return Err(ProgramError::IllegalOwner);
    }

    // ✅ PDA validation
    let (expected_pda, _) = Pubkey::find_program_address(
        &[b"user_data", user.key.as_ref()],
        program_id,
    );
    if expected_pda != *user_data_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // ✅ Initialization check
    let data = UserData::try_from_slice(&user_data_pda.data.borrow())?;
    if !data.is_initialized {
        return Err(ProgramError::UninitializedAccount);
    }

    // Now safe to proceed
    // ...
}
```

### 2. Fail Fast with Meaningful Errors

Return errors immediately when validation fails:

```rust
// ✅ Good - fail fast
if !account.is_signer {
    msg!("User must sign the transaction");
    return Err(ProgramError::MissingRequiredSignature);
}

// ❌ Bad - continues with invalid state
if account.is_signer {
    // process...
}
```

### 3. Use Type Safety

Leverage Rust's type system for compile-time guarantees:

```rust
// Define a validated account type
pub struct ValidatedUserAccount<'a> {
    info: &'a AccountInfo<'a>,
    data: UserAccountData,
}

impl<'a> ValidatedUserAccount<'a> {
    pub fn validate(
        account: &'a AccountInfo<'a>,
        program_id: &Pubkey,
    ) -> Result<Self, ProgramError> {
        // Ownership check
        if account.owner != program_id {
            return Err(ProgramError::IllegalOwner);
        }

        // Deserialize and validate
        let data = UserAccountData::try_from_slice(&account.data.borrow())?;
        if !data.is_initialized {
            return Err(ProgramError::UninitializedAccount);
        }

        Ok(Self { info: account, data })
    }
}

// Usage guarantees validated account
pub fn process_with_validated_account(
    validated: ValidatedUserAccount,
) -> ProgramResult {
    // No need to re-validate!
    // ...
}
```

### 4. Check Arithmetic Operations

Always use checked math to prevent overflow/underflow:

```rust
// ❌ Dangerous - can overflow
let total = amount1 + amount2;

// ✅ Safe - returns error on overflow
let total = amount1
    .checked_add(amount2)
    .ok_or(ProgramError::ArithmeticOverflow)?;
```

### 5. Validate Data Constraints

Check business logic constraints:

```rust
pub fn allocate_points(
    character_account: &AccountInfo,
    new_strength: u8,
) -> ProgramResult {
    let mut character = Character::try_from_slice(&character_account.data.borrow())?;

    // Validate attribute cap
    if character.strength.checked_add(new_strength).ok_or(ProgramError::ArithmeticOverflow)? > 100 {
        msg!("Attribute cannot exceed 100");
        return Err(ProgramError::InvalidArgument);
    }

    // Validate allowance
    if new_strength > character.available_points {
        msg!("Insufficient available points");
        return Err(ProgramError::InsufficientFunds);
    }

    character.strength += new_strength;
    character.available_points -= new_strength;
    character.serialize(&mut &mut character_account.data.borrow_mut()[..])?;

    Ok(())
}
```

---

## Common Vulnerabilities

### 1. Missing Ownership Check

**Vulnerability:**
```rust
// ❌ No ownership validation
pub fn update_data(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    new_value: u64,
) -> ProgramResult {
    let data_account = &accounts[0];

    // Dangerous - could be any account!
    let mut data = MyData::try_from_slice(&data_account.data.borrow())?;
    data.value = new_value;
    data.serialize(&mut &mut data_account.data.borrow_mut()[..])?;

    Ok(())
}
```

**Exploit:**
Attacker passes an account they control that happens to deserialize correctly, modifying arbitrary data.

**Fix:**
```rust
// ✅ With ownership check
if data_account.owner != program_id {
    return Err(ProgramError::IllegalOwner);
}
```

### 2. Missing Signer Check

**Vulnerability:**
```rust
// ❌ No signer validation
pub fn withdraw(
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let user_account = &accounts[0];
    let vault = &accounts[1];

    // Dangerous - anyone can drain anyone's funds!
    **user_account.lamports.borrow_mut() += amount;
    **vault.lamports.borrow_mut() -= amount;

    Ok(())
}
```

**Exploit:**
Attacker calls instruction with victim's account, draining their funds without signature.

**Fix:**
```rust
// ✅ With signer check
if !user_account.is_signer {
    return Err(ProgramError::MissingRequiredSignature);
}
```

### 3. PDA Substitution Attack

**Vulnerability:**
```rust
// ❌ Accepts PDA without validation
pub fn update_user_data(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    user: &AccountInfo,
    user_pda: &AccountInfo,
) -> ProgramResult {
    // No PDA derivation check!
    let mut data = UserData::try_from_slice(&user_pda.data.borrow())?;
    data.balance += 100;
    data.serialize(&mut &mut user_pda.data.borrow_mut()[..])?;
    Ok(())
}
```

**Exploit:**
Attacker passes a different user's PDA, crediting that user's balance instead.

**Fix:**
```rust
// ✅ Validate PDA derivation
let (expected_pda, _) = Pubkey::find_program_address(
    &[b"user_data", user.key.as_ref()],
    program_id,
);
if expected_pda != *user_pda.key {
    return Err(ProgramError::InvalidSeeds);
}
```

### 4. Integer Overflow/Underflow

**Vulnerability:**
```rust
// ❌ Unchecked arithmetic
pub fn add_rewards(
    account: &AccountInfo,
    reward: u64,
) -> ProgramResult {
    let mut user = UserData::try_from_slice(&account.data.borrow())?;
    user.total_rewards = user.total_rewards + reward;  // Can overflow!
    user.serialize(&mut &mut account.data.borrow_mut()[..])?;
    Ok(())
}
```

**Exploit:**
Overflow wraps around: u64::MAX + 1 = 0, causing balance to reset.

**Fix:**
```rust
// ✅ Checked arithmetic
user.total_rewards = user.total_rewards
    .checked_add(reward)
    .ok_or(ProgramError::ArithmeticOverflow)?;
```

### 5. Unvalidated Account Reuse

**Vulnerability:**
```rust
// ❌ No initialization check
pub fn update_score(
    accounts: &[AccountInfo],
    score: u64,
) -> ProgramResult {
    let score_account = &accounts[0];
    let mut data = ScoreData::try_from_slice(&score_account.data.borrow())?;

    // What if account was never initialized?
    data.score = score;
    data.serialize(&mut &mut score_account.data.borrow_mut()[..])?;
    Ok(())
}
```

**Exploit:**
Reusing uninitialized memory can lead to undefined behavior or data corruption.

**Fix:**
```rust
// ✅ Check initialization
if !data.is_initialized {
    return Err(ProgramError::UninitializedAccount);
}
```

---

## Summary

**Critical Account Validation Checklist:**

- ✅ **Ownership check**: Verify `account.owner == expected_program_id`
- ✅ **Signer check**: Verify `account.is_signer` for privileged operations
- ✅ **PDA validation**: Use `find_program_address` with expected seeds
- ✅ **Initialization check**: Verify account is initialized before use
- ✅ **Type validation**: Ensure account contains expected data structure
- ✅ **Rent exemption**: Calculate and enforce rent-exempt balances
- ✅ **Arithmetic safety**: Use `checked_add`, `checked_sub`, etc.
- ✅ **Data constraints**: Validate business logic rules

**Think Like an Attacker:**
For every account your program receives, ask:
- "What if this is the wrong account?"
- "What if this account isn't owned by my program?"
- "What if the user didn't sign for this?"
- "What if this account is uninitialized?"
- "What if these seeds derive a different PDA?"

Validate everything. Trust nothing.
