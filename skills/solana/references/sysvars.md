# Sysvars (System Variables)

This reference provides comprehensive coverage of Solana System Variables (sysvars) for native Rust program development, including access patterns, use cases, and performance implications.

## Table of Contents

1. [What are Sysvars](#what-are-sysvars)
2. [Clock Sysvar](#clock-sysvar)
3. [Rent Sysvar](#rent-sysvar)
4. [EpochSchedule Sysvar](#epochschedule-sysvar)
5. [SlotHashes Sysvar](#slothashes-sysvar)
6. [Other Sysvars](#other-sysvars)
7. [Access Patterns](#access-patterns)
8. [Performance Implications](#performance-implications)
9. [Best Practices](#best-practices)

---

## What are Sysvars

**System Variables (sysvars)** are special accounts that provide programs with access to blockchain state and cluster information.

### Key Characteristics

1. **Cluster-wide state:** Same values for all programs in the same slot
2. **Updated automatically:** Runtime maintains values
3. **Predictable addresses:** Well-known pubkeys
4. **Read-only:** Programs cannot modify sysvars
5. **Low CU cost:** Cheaper than account reads

### When to Use Sysvars

**Use sysvars when you need:**
- Current timestamp or slot number
- Rent exemption calculations
- Epoch and slot timing information
- Recent block hashes (for verification)
- Stake history or epoch rewards

**Don't use sysvars for:**
- User-specific data (use accounts)
- Program state (use PDAs)
- Cross-program communication (use CPIs)

---

## Clock Sysvar

**Address:** `solana_program::sysvar::clock::ID`

The Clock sysvar provides timing information about the blockchain.

### Clock Structure

```rust
use solana_program::clock::Clock;

pub struct Clock {
    pub slot: Slot,                    // Current slot
    pub epoch_start_timestamp: i64,    // Timestamp of epoch start (approximate)
    pub epoch: Epoch,                  // Current epoch
    pub leader_schedule_epoch: Epoch,  // Epoch for which leader schedule is valid
    pub unix_timestamp: UnixTimestamp, // Estimated wall-clock Unix timestamp
}
```

### Accessing Clock

**Pattern 1: get() (Recommended)**

```rust
use solana_program::clock::Clock;
use solana_program::sysvar::Sysvar;

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    _instruction_data: &[u8],
) -> ProgramResult {
    // Get Clock directly (no account needed)
    let clock = Clock::get()?;

    msg!("Current slot: {}", clock.slot);
    msg!("Current timestamp: {}", clock.unix_timestamp);
    msg!("Current epoch: {}", clock.epoch);

    Ok(())
}
```

**Pattern 2: From account**

```rust
use solana_program::sysvar::clock;

pub fn process_with_account(
    accounts: &[AccountInfo],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let clock_account = next_account_info(account_info_iter)?;

    // Verify it's the Clock sysvar
    if clock_account.key != &clock::ID {
        return Err(ProgramError::InvalidArgument);
    }

    let clock = Clock::from_account_info(clock_account)?;
    msg!("Timestamp: {}", clock.unix_timestamp);

    Ok(())
}
```

**⚠️ Recommendation:** Use `Clock::get()` unless you specifically need the account for validation.

### Common Clock Use Cases

**1. Timestamping events:**

```rust
use solana_program::clock::Clock;
use solana_program::sysvar::Sysvar;

#[derive(BorshSerialize, BorshDeserialize)]
pub struct Event {
    pub created_at: i64,
    pub data: Vec<u8>,
}

pub fn create_event(
    event_account: &AccountInfo,
    data: Vec<u8>,
) -> ProgramResult {
    let clock = Clock::get()?;

    let event = Event {
        created_at: clock.unix_timestamp,
        data,
    };

    event.serialize(&mut &mut event_account.data.borrow_mut()[..])?;
    Ok(())
}
```

**2. Time-based logic (vesting, expiration):**

```rust
pub fn check_vesting(
    vesting_account: &AccountInfo,
) -> ProgramResult {
    let clock = Clock::get()?;
    let vesting = VestingSchedule::try_from_slice(&vesting_account.data.borrow())?;

    if clock.unix_timestamp < vesting.unlock_timestamp {
        msg!("Tokens still locked until {}", vesting.unlock_timestamp);
        return Err(ProgramError::Custom(1)); // Locked
    }

    msg!("Vesting unlocked!");
    Ok(())
}
```

**3. Slot-based mechanics:**

```rust
pub fn process_epoch_transition(
    state_account: &AccountInfo,
) -> ProgramResult {
    let clock = Clock::get()?;
    let mut state = State::try_from_slice(&state_account.data.borrow())?;

    if clock.epoch > state.last_processed_epoch {
        msg!("Processing epoch transition: {} -> {}",
            state.last_processed_epoch, clock.epoch);

        // Process epoch rewards, resets, etc.
        state.last_processed_epoch = clock.epoch;
        state.serialize(&mut &mut state_account.data.borrow_mut()[..])?;
    }

    Ok(())
}
```

### Clock Gotchas

**⚠️ unix_timestamp is approximate:**

```rust
// ❌ Don't use for precise timing
if clock.unix_timestamp == expected_timestamp {  // Risky!
    // Might miss by seconds
}

// ✅ Use ranges for time checks
if clock.unix_timestamp >= unlock_time {
    // Safe
}
```

**⚠️ Timestamps can vary across validators:**

The `unix_timestamp` is based on validator voting and may differ slightly between validators in the same slot. Don't assume exact precision.

---

## Rent Sysvar

**Address:** `solana_program::sysvar::rent::ID`

The Rent sysvar provides rent calculation parameters.

### Rent Structure

```rust
use solana_program::rent::Rent;

pub struct Rent {
    pub lamports_per_byte_year: u64,  // Base rent rate
    pub exemption_threshold: f64,      // Multiplier for exemption (2.0 = 2 years)
    pub burn_percent: u8,              // Percentage of rent burned
}
```

### Accessing Rent

**Pattern 1: get() (Recommended)**

```rust
use solana_program::rent::Rent;
use solana_program::sysvar::Sysvar;

pub fn calculate_rent_exemption(
    data_size: usize,
) -> Result<u64, ProgramError> {
    let rent = Rent::get()?;

    // Calculate minimum balance for rent exemption
    let min_balance = rent.minimum_balance(data_size);

    msg!("Minimum balance for {} bytes: {} lamports", data_size, min_balance);
    Ok(min_balance)
}
```

**Pattern 2: From account**

```rust
use solana_program::sysvar::rent;

pub fn check_rent_exemption(
    accounts: &[AccountInfo],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let data_account = next_account_info(account_info_iter)?;
    let rent_account = next_account_info(account_info_iter)?;

    if rent_account.key != &rent::ID {
        return Err(ProgramError::InvalidArgument);
    }

    let rent = Rent::from_account_info(rent_account)?;

    if !rent.is_exempt(data_account.lamports(), data_account.data_len()) {
        msg!("Account is not rent-exempt!");
        return Err(ProgramError::AccountNotRentExempt);
    }

    Ok(())
}
```

### Common Rent Use Cases

**1. Account creation with rent exemption:**

```rust
use solana_program::rent::Rent;
use solana_program::system_instruction;
use solana_program::program::invoke_signed;

pub fn create_account_rent_exempt(
    payer: &AccountInfo,
    new_account: &AccountInfo,
    system_program: &AccountInfo,
    program_id: &Pubkey,
    seeds: &[&[u8]],
    space: usize,
) -> ProgramResult {
    let rent = Rent::get()?;
    let min_balance = rent.minimum_balance(space);

    msg!("Creating account with {} lamports for {} bytes", min_balance, space);

    let create_account_ix = system_instruction::create_account(
        payer.key,
        new_account.key,
        min_balance,
        space as u64,
        program_id,
    );

    invoke_signed(
        &create_account_ix,
        &[payer.clone(), new_account.clone(), system_program.clone()],
        &[seeds],
    )?;

    Ok(())
}
```

**2. Validating account has sufficient balance:**

```rust
pub fn validate_rent_exempt_account(
    account: &AccountInfo,
) -> ProgramResult {
    let rent = Rent::get()?;

    if !rent.is_exempt(account.lamports(), account.data_len()) {
        let required = rent.minimum_balance(account.data_len());
        let current = account.lamports();

        msg!("Account not rent-exempt: has {} lamports, needs {}",
            current, required);

        return Err(ProgramError::AccountNotRentExempt);
    }

    Ok(())
}
```

**3. Calculating required lamports for reallocation:**

```rust
pub fn reallocate_account(
    account: &AccountInfo,
    new_size: usize,
) -> ProgramResult {
    let rent = Rent::get()?;

    let old_size = account.data_len();
    let current_lamports = account.lamports();

    let new_min_balance = rent.minimum_balance(new_size);

    if new_size > old_size {
        // Growing account - ensure sufficient lamports
        if current_lamports < new_min_balance {
            msg!("Need {} more lamports for reallocation",
                new_min_balance - current_lamports);
            return Err(ProgramError::InsufficientFunds);
        }
    }

    account.realloc(new_size, false)?;
    Ok(())
}
```

---

## EpochSchedule Sysvar

**Address:** `solana_program::sysvar::epoch_schedule::ID`

The EpochSchedule sysvar provides information about epoch timing and slot calculations.

### EpochSchedule Structure

```rust
use solana_program::epoch_schedule::EpochSchedule;

pub struct EpochSchedule {
    pub slots_per_epoch: u64,              // Slots per epoch after warmup
    pub leader_schedule_slot_offset: u64,  // Offset for leader schedule
    pub warmup: bool,                      // Whether in warmup period
    pub first_normal_epoch: Epoch,         // First non-warmup epoch
    pub first_normal_slot: Slot,           // First slot of first normal epoch
}
```

### Accessing EpochSchedule

```rust
use solana_program::sysvar::epoch_schedule::EpochSchedule;
use solana_program::sysvar::Sysvar;

pub fn get_epoch_info() -> ProgramResult {
    let epoch_schedule = EpochSchedule::get()?;

    msg!("Slots per epoch: {}", epoch_schedule.slots_per_epoch);
    msg!("First normal epoch: {}", epoch_schedule.first_normal_epoch);
    msg!("Warmup: {}", epoch_schedule.warmup);

    Ok(())
}
```

### Common EpochSchedule Use Cases

**1. Calculating epoch from slot:**

```rust
use solana_program::clock::Clock;
use solana_program::epoch_schedule::EpochSchedule;

pub fn calculate_epoch_from_slot(
    slot: u64,
) -> Result<u64, ProgramError> {
    let epoch_schedule = EpochSchedule::get()?;

    let epoch = epoch_schedule.get_epoch(slot);
    msg!("Slot {} is in epoch {}", slot, epoch);

    Ok(epoch)
}
```

**2. Determining slots remaining in epoch:**

```rust
pub fn slots_until_epoch_end() -> Result<u64, ProgramError> {
    let clock = Clock::get()?;
    let epoch_schedule = EpochSchedule::get()?;

    let current_slot = clock.slot;
    let current_epoch = clock.epoch;

    // Get first slot of next epoch
    let next_epoch_start = epoch_schedule.get_first_slot_in_epoch(current_epoch + 1);

    let remaining = next_epoch_start - current_slot;
    msg!("Slots remaining in epoch: {}", remaining);

    Ok(remaining)
}
```

**3. Epoch-based reward distribution:**

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct RewardState {
    pub last_distribution_epoch: u64,
    pub total_distributed: u64,
}

pub fn distribute_epoch_rewards(
    reward_state_account: &AccountInfo,
) -> ProgramResult {
    let clock = Clock::get()?;
    let mut state = RewardState::try_from_slice(&reward_state_account.data.borrow())?;

    if clock.epoch > state.last_distribution_epoch {
        let epochs_passed = clock.epoch - state.last_distribution_epoch;

        msg!("Distributing rewards for {} epochs", epochs_passed);

        // Distribute rewards
        let reward_amount = epochs_passed * 1000; // Example
        state.total_distributed += reward_amount;
        state.last_distribution_epoch = clock.epoch;

        state.serialize(&mut &mut reward_state_account.data.borrow_mut()[..])?;
    }

    Ok(())
}
```

---

## SlotHashes Sysvar

**Address:** `solana_program::sysvar::slot_hashes::ID`

The SlotHashes sysvar contains recent slot hashes for verification purposes.

### SlotHashes Structure

```rust
use solana_program::slot_hashes::SlotHashes;

// SlotHashes contains up to 512 recent (slot, hash) pairs
pub struct SlotHashes {
    // Vector of (slot, hash) tuples
    // Most recent first, up to MAX_ENTRIES (512)
}
```

### Accessing SlotHashes

```rust
use solana_program::sysvar::slot_hashes::SlotHashes;
use solana_program::sysvar::Sysvar;

pub fn verify_recent_slot(
    claimed_slot: u64,
    claimed_hash: &[u8; 32],
) -> ProgramResult {
    let slot_hashes = SlotHashes::get()?;

    // Check if slot is in recent history
    for (slot, hash) in slot_hashes.iter() {
        if *slot == claimed_slot {
            if hash.as_ref() == claimed_hash {
                msg!("Slot hash verified!");
                return Ok(());
            } else {
                msg!("Slot hash mismatch!");
                return Err(ProgramError::InvalidArgument);
            }
        }
    }

    msg!("Slot not found in recent history");
    Err(ProgramError::InvalidArgument)
}
```

### Common SlotHashes Use Cases

**1. Verifying transaction recency:**

```rust
pub fn verify_transaction_recent(
    slot_hashes_account: &AccountInfo,
    claimed_slot: u64,
) -> ProgramResult {
    let slot_hashes = SlotHashes::from_account_info(slot_hashes_account)?;

    // Check if claimed slot is in recent 512 slots
    let is_recent = slot_hashes.iter().any(|(slot, _)| *slot == claimed_slot);

    if !is_recent {
        msg!("Transaction too old or slot invalid");
        return Err(ProgramError::Custom(1));
    }

    Ok(())
}
```

**2. Preventing replay attacks:**

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct ProcessedSlot {
    pub slot: u64,
    pub hash: [u8; 32],
}

pub fn process_once_per_slot(
    state_account: &AccountInfo,
) -> ProgramResult {
    let slot_hashes = SlotHashes::get()?;
    let mut state = ProcessedSlot::try_from_slice(&state_account.data.borrow())?;

    // Get current slot and hash
    let (current_slot, current_hash) = slot_hashes.iter().next()
        .ok_or(ProgramError::InvalidArgument)?;

    if state.slot == *current_slot {
        msg!("Already processed in this slot!");
        return Err(ProgramError::Custom(2)); // Already processed
    }

    // Update state
    state.slot = *current_slot;
    state.hash = current_hash.to_bytes();
    state.serialize(&mut &mut state_account.data.borrow_mut()[..])?;

    Ok(())
}
```

**⚠️ Note:** SlotHashes only maintains the most recent 512 slots. For older verification, use a different approach.

---

## Other Sysvars

### StakeHistory

**Address:** `solana_program::sysvar::stake_history::ID`

Provides historical stake activation and deactivation information.

```rust
use solana_program::sysvar::stake_history::StakeHistory;

pub fn get_stake_history() -> ProgramResult {
    let stake_history = StakeHistory::get()?;

    // Access historical stake data by epoch
    msg!("Stake history available");
    Ok(())
}
```

**Use cases:**
- Stake pool programs
- Historical stake analysis
- Reward calculations

### EpochRewards

**Address:** `solana_program::sysvar::epoch_rewards::ID`

Provides information about epoch rewards distribution (if active).

```rust
use solana_program::sysvar::epoch_rewards::EpochRewards;

pub fn check_epoch_rewards() -> ProgramResult {
    let epoch_rewards = EpochRewards::get()?;

    msg!("Epoch rewards data available");
    Ok(())
}
```

**Use cases:**
- Stake reward programs
- Validator reward tracking

### Instructions

**Address:** `solana_program::sysvar::instructions::ID`

Provides access to instructions in the current transaction.

```rust
use solana_program::sysvar::instructions;

pub fn validate_transaction_instructions(
    instructions_account: &AccountInfo,
) -> ProgramResult {
    // Check if current instruction is not the first
    let current_index = instructions::load_current_index_checked(instructions_account)?;

    msg!("Current instruction index: {}", current_index);

    // Load a specific instruction
    if current_index > 0 {
        let prev_ix = instructions::load_instruction_at_checked(
            (current_index - 1) as usize,
            instructions_account,
        )?;

        msg!("Previous instruction program: {}", prev_ix.program_id);
    }

    Ok(())
}
```

**Use cases:**
- Cross-instruction validation
- Ensuring instruction order
- Detecting sandwich attacks

---

## Access Patterns

### Pattern 1: get() - Direct Access (Recommended)

**Advantages:**
- No account needed in instruction
- Saves account space
- Lower CU cost (~100 CU)
- Cleaner code

**Disadvantages:**
- Not supported for all sysvars
- Can't be passed to CPIs

```rust
use solana_program::sysvar::Sysvar;

pub fn use_sysvar_direct() -> ProgramResult {
    let clock = Clock::get()?;
    let rent = Rent::get()?;

    msg!("Clock: {}", clock.unix_timestamp);
    msg!("Rent: {}", rent.lamports_per_byte_year);

    Ok(())
}
```

**Supported sysvars:**
- Clock
- Rent
- EpochSchedule
- EpochRewards
- Fees (deprecated)

### Pattern 2: from_account_info - Account Access

**Advantages:**
- Works for all sysvars
- Can be validated
- Can be passed to CPIs
- Required for some sysvars (SlotHashes, Instructions)

**Disadvantages:**
- Account must be passed in instruction
- Slightly higher CU cost (~300 CU)
- More boilerplate

```rust
use solana_program::sysvar::clock;

pub fn use_sysvar_from_account(
    clock_account: &AccountInfo,
) -> ProgramResult {
    // Validate account address
    if clock_account.key != &clock::ID {
        return Err(ProgramError::InvalidArgument);
    }

    let clock = Clock::from_account_info(clock_account)?;
    msg!("Clock: {}", clock.unix_timestamp);

    Ok(())
}
```

**Required for:**
- SlotHashes
- StakeHistory
- Instructions
- Any sysvar passed to CPI

### Pattern 3: Hybrid Approach

**Use get() when possible, account when needed:**

```rust
pub fn hybrid_sysvar_access(
    accounts: &[AccountInfo],
    need_cpi: bool,
) -> ProgramResult {
    if need_cpi {
        // Need account for CPI
        let account_info_iter = &mut accounts.iter();
        let clock_account = next_account_info(account_info_iter)?;

        let clock = Clock::from_account_info(clock_account)?;

        // Can pass clock_account to CPI
        msg!("Using account access");
    } else {
        // Direct access is cheaper
        let clock = Clock::get()?;
        msg!("Using direct access");
    }

    Ok(())
}
```

---

## Performance Implications

### Compute Unit Costs

| Access Method | Approximate CU Cost |
|--------------|---------------------|
| Clock::get() | ~100 CU |
| Rent::get() | ~100 CU |
| EpochSchedule::get() | ~100 CU |
| Clock::from_account_info() | ~300 CU |
| SlotHashes::from_account_info() | ~500 CU |

### Optimization Tips

**1. Use get() when possible:**

```rust
// ✅ Efficient - 100 CU
let clock = Clock::get()?;

// ❌ Wasteful - 300 CU (unless needed for CPI)
let clock = Clock::from_account_info(clock_account)?;
```

**2. Cache sysvar values:**

```rust
// ❌ Wasteful - calls get() multiple times
for i in 0..10 {
    let clock = Clock::get()?;  // 100 CU × 10 = 1000 CU
    process_item(i, clock.unix_timestamp)?;
}

// ✅ Efficient - call once
let clock = Clock::get()?;  // 100 CU
let timestamp = clock.unix_timestamp;
for i in 0..10 {
    process_item(i, timestamp)?;
}
```

**3. Avoid unnecessary sysvar access:**

```rust
// ❌ Wasteful - reading sysvar in every call
pub fn update_balance(account: &AccountInfo, amount: u64) -> ProgramResult {
    let clock = Clock::get()?;  // Not needed!
    // ... no clock usage
    Ok(())
}

// ✅ Efficient - only access when needed
pub fn update_with_timestamp(account: &AccountInfo, amount: u64) -> ProgramResult {
    let clock = Clock::get()?;  // Used below
    let timestamp = clock.unix_timestamp;
    // ... use timestamp
    Ok(())
}
```

---

## Best Practices

### 1. Prefer get() Over from_account_info()

**Unless you need the account for CPI or validation:**

```rust
// ✅ Default choice
let clock = Clock::get()?;

// Only if needed for CPI
let clock = Clock::from_account_info(clock_account)?;
invoke(&ix, &[..., clock_account])?;
```

### 2. Validate Sysvar Accounts

**When accepting sysvar accounts, always validate:**

```rust
pub fn validate_clock_account(
    clock_account: &AccountInfo,
) -> ProgramResult {
    // ✅ Always validate sysvar address
    if clock_account.key != &solana_program::sysvar::clock::ID {
        msg!("Invalid Clock account");
        return Err(ProgramError::InvalidArgument);
    }

    Ok(())
}
```

### 3. Use Clock for Timestamps, Not Slot Hashes

**For simple time-based logic:**

```rust
// ✅ Simple and efficient
let clock = Clock::get()?;
if clock.unix_timestamp >= unlock_time {
    // unlock
}

// ❌ Overkill - SlotHashes is for verification, not timing
let slot_hashes = SlotHashes::get()?;
// Complex slot-based timing logic
```

### 4. Cache Sysvar Values

**Read once, use multiple times:**

```rust
pub fn process_multiple_accounts(
    accounts: &[AccountInfo],
) -> ProgramResult {
    // ✅ Read once
    let clock = Clock::get()?;
    let timestamp = clock.unix_timestamp;

    for account in accounts {
        update_account_timestamp(account, timestamp)?;
    }

    Ok(())
}
```

### 5. Document Sysvar Dependencies

**Be explicit about which sysvars your program uses:**

```rust
/// Processes user staking
///
/// # Sysvars
/// - Clock: for stake timestamp
/// - Rent: for account validation
///
/// # Accounts
/// - `[writable]` stake_account
/// - `[signer]` user
pub fn process_stake(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let clock = Clock::get()?;
    let rent = Rent::get()?;

    // ...
    Ok(())
}
```

### 6. Handle Clock Drift

**Don't assume unix_timestamp is perfectly accurate:**

```rust
// ❌ Risky - exact timestamp match
if clock.unix_timestamp == expected_time {
    // May never trigger
}

// ✅ Safe - use ranges
if clock.unix_timestamp >= expected_time {
    // Reliable
}

// ✅ Best - add tolerance for early/late
const TOLERANCE: i64 = 60; // 60 seconds
if clock.unix_timestamp >= expected_time - TOLERANCE {
    // Handles clock drift
}
```

---

## Summary

**Key Takeaways:**

1. **Use get() when possible** for lower CU costs and simpler code
2. **Use from_account_info()** when passing to CPIs or for sysvars without get()
3. **Always validate** sysvar account addresses when accepting them
4. **Cache sysvar values** to avoid redundant reads
5. **Understand timing limitations** - unix_timestamp is approximate

**Most Common Sysvars:**

| Sysvar | Primary Use | Access Method |
|--------|------------|---------------|
| **Clock** | Timestamps, epochs, slots | `Clock::get()` |
| **Rent** | Rent exemption calculations | `Rent::get()` |
| **EpochSchedule** | Epoch/slot calculations | `EpochSchedule::get()` |
| **SlotHashes** | Recent slot verification | `from_account_info()` only |
| **Instructions** | Transaction introspection | `from_account_info()` only |

**Common Patterns:**

```rust
// Timestamp current event
let clock = Clock::get()?;
event.created_at = clock.unix_timestamp;

// Validate rent exemption
let rent = Rent::get()?;
if !rent.is_exempt(account.lamports(), account.data_len()) {
    return Err(ProgramError::AccountNotRentExempt);
}

// Calculate rent for new account
let rent = Rent::get()?;
let min_balance = rent.minimum_balance(space);
```

Sysvars provide essential cluster state to your programs. Master their access patterns for efficient, production-ready Solana development.
