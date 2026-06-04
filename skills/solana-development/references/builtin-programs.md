# Built-in Programs

This reference provides comprehensive coverage of Solana's built-in programs for native Rust development, focusing on the System Program and Compute Budget Program.

## Table of Contents

1. [Overview of Built-in Programs](#overview-of-built-in-programs)
2. [System Program](#system-program)
3. [Compute Budget Program](#compute-budget-program)
4. [Other Built-in Programs](#other-built-in-programs)
5. [CPI Patterns](#cpi-patterns)
6. [Best Practices](#best-practices)

---

## Overview of Built-in Programs

**Built-in programs** (also called native programs) are fundamental Solana programs that provide core blockchain functionality.

### Key Built-in Programs

| Program | Program ID | Purpose |
|---------|-----------|---------|
| **System Program** | `11111111111111111111111111111111` | Account creation, transfers, allocation |
| **Compute Budget** | `ComputeBudget111111111111111111111111111111` | CU limits, heap size, priority fees |
| **BPF Loader** | Various | Loading and executing programs |
| **Config Program** | `Config1111111111111111111111111111111111111` | Validator configuration |
| **Stake Program** | `Stake11111111111111111111111111111111111111` | Staking and delegation |
| **Vote Program** | `Vote111111111111111111111111111111111111111` | Validator voting |

This reference focuses on the two most commonly used in program development: **System Program** and **Compute Budget Program**.

---

## System Program

**Program ID:** `solana_program::system_program::ID` (`11111111111111111111111111111111`)

The System Program is responsible for account creation, lamport transfers, and account management.

### Core Functionality

1. **Create accounts** (regular and PDAs)
2. **Transfer lamports** between accounts
3. **Allocate space** for account data
4. **Assign ownership** to programs
5. **Create nonce accounts** for durable transactions

### System Program Instructions

```rust
use solana_program::system_instruction;

pub enum SystemInstruction {
    CreateAccount,        // Create new account
    Assign,               // Assign account to program
    Transfer,             // Transfer lamports
    CreateAccountWithSeed,// Create account with seed
    AdvanceNonceAccount,  // Advance nonce
    WithdrawNonceAccount, // Withdraw from nonce
    InitializeNonceAccount, // Initialize nonce
    Allocate,             // Allocate account space
    AllocateWithSeed,     // Allocate with seed
    AssignWithSeed,       // Assign with seed
    TransferWithSeed,     // Transfer with seed
    UpgradeNonceAccount,  // Upgrade nonce (v4)
}
```

---

### CreateAccount

**Creates a new account with lamports and data space.**

#### Function Signature

```rust
pub fn create_account(
    from_pubkey: &Pubkey,      // Funding account (must be signer)
    to_pubkey: &Pubkey,        // New account address
    lamports: u64,             // Lamports to fund account
    space: u64,                // Bytes of data space
    owner: &Pubkey,            // Program that will own the account
) -> Instruction
```

#### Usage in Native Rust

```rust
use solana_program::{
    system_instruction,
    program::invoke,
};

pub fn create_new_account(
    payer: &AccountInfo,
    new_account: &AccountInfo,
    system_program: &AccountInfo,
    program_id: &Pubkey,
) -> ProgramResult {
    let space = 100;  // Account data size
    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(space);

    let create_account_ix = system_instruction::create_account(
        payer.key,
        new_account.key,
        lamports,
        space as u64,
        program_id,
    );

    invoke(
        &create_account_ix,
        &[
            payer.clone(),
            new_account.clone(),
            system_program.clone(),
        ],
    )?;

    msg!("Created account with {} bytes", space);
    Ok(())
}
```

#### Creating PDA Accounts

```rust
use solana_program::program::invoke_signed;

pub fn create_pda_account(
    payer: &AccountInfo,
    pda_account: &AccountInfo,
    system_program: &AccountInfo,
    program_id: &Pubkey,
    seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    // Verify PDA
    let (expected_pda, _bump) = Pubkey::find_program_address(seeds, program_id);
    if expected_pda != *pda_account.key {
        return Err(ProgramError::InvalidSeeds);
    }

    let space = 200;
    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(space);

    let create_account_ix = system_instruction::create_account(
        payer.key,
        pda_account.key,
        lamports,
        space as u64,
        program_id,
    );

    // Create full seeds with bump
    let mut full_seeds = seeds.to_vec();
    full_seeds.push(&[bump]);
    let signer_seeds: &[&[&[u8]]] = &[&full_seeds];

    invoke_signed(
        &create_account_ix,
        &[payer.clone(), pda_account.clone(), system_program.clone()],
        signer_seeds,
    )?;

    msg!("Created PDA account at {}", pda_account.key);
    Ok(())
}
```

---

### Transfer

**Transfers lamports from one account to another.**

#### Function Signature

```rust
pub fn transfer(
    from_pubkey: &Pubkey,     // Source account (must be signer)
    to_pubkey: &Pubkey,       // Destination account
    lamports: u64,            // Amount to transfer
) -> Instruction
```

#### Usage in Native Rust

```rust
pub fn transfer_lamports(
    from: &AccountInfo,
    to: &AccountInfo,
    system_program: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    let transfer_ix = system_instruction::transfer(
        from.key,
        to.key,
        amount,
    );

    invoke(
        &transfer_ix,
        &[from.clone(), to.clone(), system_program.clone()],
    )?;

    msg!("Transferred {} lamports from {} to {}",
        amount, from.key, to.key);
    Ok(())
}
```

#### Transfer from PDA

```rust
pub fn transfer_from_pda(
    pda: &AccountInfo,
    to: &AccountInfo,
    system_program: &AccountInfo,
    amount: u64,
    seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    let transfer_ix = system_instruction::transfer(
        pda.key,
        to.key,
        amount,
    );

    let mut full_seeds = seeds.to_vec();
    full_seeds.push(&[bump]);
    let signer_seeds: &[&[&[u8]]] = &[&full_seeds];

    invoke_signed(
        &transfer_ix,
        &[pda.clone(), to.clone(), system_program.clone()],
        signer_seeds,
    )?;

    Ok(())
}
```

---

### Allocate

**Allocates space for an account's data.**

#### Function Signature

```rust
pub fn allocate(
    pubkey: &Pubkey,          // Account to allocate (must be signer)
    space: u64,               // Bytes to allocate
) -> Instruction
```

#### Usage in Native Rust

```rust
pub fn allocate_account_space(
    account: &AccountInfo,
    system_program: &AccountInfo,
    space: u64,
) -> ProgramResult {
    let allocate_ix = system_instruction::allocate(
        account.key,
        space,
    );

    invoke(
        &allocate_ix,
        &[account.clone(), system_program.clone()],
    )?;

    msg!("Allocated {} bytes for account", space);
    Ok(())
}
```

**⚠️ Note:** The account must be owned by the System Program before allocating. Most programs use `create_account` instead, which combines allocation with ownership assignment.

---

### Assign

**Assigns an account to a program (changes owner).**

#### Function Signature

```rust
pub fn assign(
    pubkey: &Pubkey,          // Account to assign (must be signer)
    owner: &Pubkey,           // New owner program
) -> Instruction
```

#### Usage in Native Rust

```rust
pub fn assign_to_program(
    account: &AccountInfo,
    system_program: &AccountInfo,
    new_owner: &Pubkey,
) -> ProgramResult {
    let assign_ix = system_instruction::assign(
        account.key,
        new_owner,
    );

    invoke(
        &assign_ix,
        &[account.clone(), system_program.clone()],
    )?;

    msg!("Assigned account to program {}", new_owner);
    Ok(())
}
```

**⚠️ Note:** Most programs use `create_account` which handles assignment during creation.

---

### Complete Example: Account Lifecycle

```rust
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::invoke_signed,
    pubkey::Pubkey,
    system_instruction,
    sysvar::{rent::Rent, Sysvar},
};

#[derive(BorshSerialize, BorshDeserialize)]
pub struct UserData {
    pub user: Pubkey,
    pub balance: u64,
    pub created_at: i64,
}

pub fn create_user_account(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    user_pubkey: Pubkey,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let payer = next_account_info(account_info_iter)?;
    let user_account = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // 1. Derive PDA
    let seeds = &[b"user", user_pubkey.as_ref()];
    let (pda, bump) = Pubkey::find_program_address(seeds, program_id);

    if pda != *user_account.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // 2. Calculate space and rent
    let space = std::mem::size_of::<UserData>();
    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(space);

    // 3. Create account via System Program CPI
    let create_ix = system_instruction::create_account(
        payer.key,
        user_account.key,
        lamports,
        space as u64,
        program_id,
    );

    let signer_seeds: &[&[&[u8]]] = &[&[b"user", user_pubkey.as_ref(), &[bump]]];

    invoke_signed(
        &create_ix,
        &[payer.clone(), user_account.clone(), system_program.clone()],
        signer_seeds,
    )?;

    // 4. Initialize account data
    let clock = Clock::get()?;
    let user_data = UserData {
        user: user_pubkey,
        balance: 0,
        created_at: clock.unix_timestamp,
    };

    user_data.serialize(&mut &mut user_account.data.borrow_mut()[..])?;

    msg!("Created user account for {}", user_pubkey);
    Ok(())
}
```

---

## Compute Budget Program

**Program ID:** `solana_program::compute_budget::ID` (`ComputeBudget111111111111111111111111111111`)

The Compute Budget Program allows transactions to request specific compute unit limits, heap sizes, and priority fees.

### Core Functionality

1. **Set compute unit limit** - Maximum CUs for transaction
2. **Set compute unit price** - Priority fee per CU
3. **Request heap size** - Heap memory allocation

### Compute Budget Instructions

```rust
use solana_program::compute_budget::ComputeBudgetInstruction;

pub enum ComputeBudgetInstruction {
    RequestUnitsDeprecated,      // Deprecated
    RequestHeapFrame(u32),       // Request heap frame (bytes)
    SetComputeUnitLimit(u32),    // Set max CUs
    SetComputeUnitPrice(u64),    // Set priority fee (microlamports per CU)
    SetLoadedAccountsDataSizeLimit(u32), // Set loaded accounts data limit
}
```

---

### SetComputeUnitLimit

**Sets the maximum compute units available to the transaction.**

#### Function Signature

```rust
pub fn set_compute_unit_limit(units: u32) -> Instruction
```

#### Default Limits

- **Default per instruction:** 200,000 CUs
- **Default per transaction:** 1,400,000 CUs (with requested CU limit)
- **Maximum:** 1,400,000 CUs

#### Usage in Native Rust

**Important:** Compute Budget instructions are added to the transaction by the **client**, not inside the program.

**Client-side example (for reference):**

```rust
// This code runs CLIENT-SIDE, not in the program
use solana_sdk::{
    compute_budget::ComputeBudgetInstruction,
    transaction::Transaction,
};

let compute_budget_ix = ComputeBudgetInstruction::set_compute_unit_limit(400_000);

let transaction = Transaction::new_signed_with_payer(
    &[
        compute_budget_ix,  // Must be first
        your_program_ix,
    ],
    Some(&payer.pubkey()),
    &[&payer],
    recent_blockhash,
);
```

**⚠️ Note:** Programs cannot modify their own compute budget. These instructions must be added client-side before sending the transaction.

---

### SetComputeUnitPrice

**Sets the priority fee per compute unit (for transaction prioritization).**

#### Function Signature

```rust
pub fn set_compute_unit_price(microlamports: u64) -> Instruction
```

#### Priority Fee Calculation

```
Total Priority Fee = (CUs Used × microlamports) / 1,000,000
```

**Example:**
- CUs used: 50,000
- Price: 10,000 microlamports per CU
- Fee: (50,000 × 10,000) / 1,000,000 = 500 lamports

#### Usage (Client-side)

```rust
// Client-side code
let compute_unit_price_ix = ComputeBudgetInstruction::set_compute_unit_price(20_000);

let transaction = Transaction::new_signed_with_payer(
    &[
        compute_unit_price_ix,  // Set priority fee
        your_program_ix,
    ],
    Some(&payer.pubkey()),
    &[&payer],
    recent_blockhash,
);
```

**Use cases:**
- High-priority transactions (arbitrage, liquidations)
- Congested network periods
- Time-sensitive operations

---

### RequestHeapFrame

**Requests additional heap memory for the transaction.**

#### Function Signature

```rust
pub fn request_heap_frame(bytes: u32) -> Instruction
```

#### Default Heap

- **Default:** 32 KB
- **Maximum:** 256 KB

#### Usage (Client-side)

```rust
// Client-side code
let heap_size_ix = ComputeBudgetInstruction::request_heap_frame(256 * 1024); // 256 KB

let transaction = Transaction::new_signed_with_payer(
    &[
        heap_size_ix,       // Request more heap
        your_program_ix,
    ],
    Some(&payer.pubkey()),
    &[&payer],
    recent_blockhash,
);
```

**When to use:**
- Large data structures
- Complex deserialization
- Temporary buffers

**⚠️ Cost:** Requesting heap increases CU consumption.

---

### SetLoadedAccountsDataSizeLimit

**Sets the maximum total size of loaded account data.**

#### Function Signature

```rust
pub fn set_loaded_accounts_data_size_limit(bytes: u32) -> Instruction
```

#### Default Limit

- **Default:** 64 MB per transaction

#### Usage (Client-side)

```rust
// Client-side code
let accounts_data_limit_ix =
    ComputeBudgetInstruction::set_loaded_accounts_data_size_limit(128 * 1024 * 1024);

let transaction = Transaction::new_signed_with_payer(
    &[
        accounts_data_limit_ix,
        your_program_ix,
    ],
    Some(&payer.pubkey()),
    &[&payer],
    recent_blockhash,
);
```

**Use cases:**
- Transactions with many large accounts
- Bulk processing operations

---

### Complete Client-side Example

```rust
use solana_sdk::{
    compute_budget::ComputeBudgetInstruction,
    transaction::Transaction,
    signature::{Keypair, Signer},
    pubkey::Pubkey,
};

pub fn build_optimized_transaction(
    payer: &Keypair,
    program_id: &Pubkey,
    program_ix_data: &[u8],
    accounts: Vec<AccountMeta>,
    recent_blockhash: Hash,
) -> Transaction {
    // 1. Set compute unit limit (if default 200k is insufficient)
    let compute_limit_ix = ComputeBudgetInstruction::set_compute_unit_limit(300_000);

    // 2. Set priority fee (for faster processing)
    let compute_price_ix = ComputeBudgetInstruction::set_compute_unit_price(10_000);

    // 3. Request additional heap if needed
    let heap_size_ix = ComputeBudgetInstruction::request_heap_frame(128 * 1024); // 128 KB

    // 4. Your program instruction
    let program_ix = Instruction {
        program_id: *program_id,
        accounts,
        data: program_ix_data.to_vec(),
    };

    // 5. Build transaction (compute budget instructions FIRST)
    Transaction::new_signed_with_payer(
        &[
            compute_limit_ix,
            compute_price_ix,
            heap_size_ix,
            program_ix,
        ],
        Some(&payer.pubkey()),
        &[payer],
        recent_blockhash,
    )
}
```

---

## Other Built-in Programs

### BPF Loader

**Purpose:** Loads and executes Solana programs.

**Program IDs:**
- `BPFLoader1111111111111111111111111111111111` (deprecated)
- `BPFLoader2111111111111111111111111111111111` (upgradeable)
- `BPFLoaderUpgradeab1e11111111111111111111111` (current)

**Usage:** Primarily used by the runtime. Programs rarely interact with BPF Loader directly.

### Stake Program

**Program ID:** `Stake11111111111111111111111111111111111111`

**Purpose:** Staking SOL to validators.

**Common operations:**
- Create stake accounts
- Delegate stake
- Deactivate stake
- Withdraw stake

**Use case:** Staking pools, liquid staking protocols.

### Vote Program

**Program ID:** `Vote111111111111111111111111111111111111111`

**Purpose:** Validator voting and consensus.

**Use case:** Validator operations, rarely used by general programs.

---

## CPI Patterns

### System Program CPI Pattern

**Standard pattern for calling System Program:**

```rust
use solana_program::{
    program::invoke,
    system_instruction,
};

pub fn system_program_cpi(
    from: &AccountInfo,
    to: &AccountInfo,
    system_program: &AccountInfo,
) -> ProgramResult {
    // 1. Verify System Program
    if system_program.key != &solana_program::system_program::ID {
        return Err(ProgramError::IncorrectProgramId);
    }

    // 2. Create instruction
    let ix = system_instruction::transfer(from.key, to.key, 1_000_000);

    // 3. Invoke
    invoke(&ix, &[from.clone(), to.clone(), system_program.clone()])?;

    Ok(())
}
```

### PDA Signing Pattern

**When PDAs need to sign:**

```rust
pub fn pda_system_cpi(
    pda: &AccountInfo,
    to: &AccountInfo,
    system_program: &AccountInfo,
    program_id: &Pubkey,
    seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    // 1. Verify PDA
    let (expected_pda, _) = Pubkey::find_program_address(seeds, program_id);
    if expected_pda != *pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // 2. Create instruction
    let ix = system_instruction::transfer(pda.key, to.key, 500_000);

    // 3. Prepare signer seeds
    let mut full_seeds = seeds.to_vec();
    full_seeds.push(&[bump]);
    let signer_seeds: &[&[&[u8]]] = &[&full_seeds];

    // 4. Invoke with PDA signature
    invoke_signed(
        &ix,
        &[pda.clone(), to.clone(), system_program.clone()],
        signer_seeds,
    )?;

    Ok(())
}
```

### Validation Pattern

**Always validate accounts before CPI:**

```rust
pub fn safe_system_cpi(
    from: &AccountInfo,
    to: &AccountInfo,
    system_program: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    // ✅ Validate System Program
    if system_program.key != &solana_program::system_program::ID {
        msg!("Invalid System Program");
        return Err(ProgramError::IncorrectProgramId);
    }

    // ✅ Validate signer
    if !from.is_signer {
        msg!("From account must be signer");
        return Err(ProgramError::MissingRequiredSignature);
    }

    // ✅ Validate sufficient balance
    if from.lamports() < amount {
        msg!("Insufficient balance");
        return Err(ProgramError::InsufficientFunds);
    }

    // Execute CPI
    let ix = system_instruction::transfer(from.key, to.key, amount);
    invoke(&ix, &[from.clone(), to.clone(), system_program.clone()])?;

    Ok(())
}
```

---

## Best Practices

### 1. Always Validate Program IDs

```rust
// ✅ Validate before CPI
if system_program.key != &solana_program::system_program::ID {
    return Err(ProgramError::IncorrectProgramId);
}
```

### 2. Use Rent Exemption

```rust
// ✅ Always create accounts with rent exemption
let rent = Rent::get()?;
let lamports = rent.minimum_balance(space);

// ❌ Don't use arbitrary amounts
let lamports = 1_000_000; // May not be rent-exempt!
```

### 3. Verify PDA Before Creation

```rust
// ✅ Verify PDA derivation
let (expected_pda, bump) = Pubkey::find_program_address(seeds, program_id);
if expected_pda != *pda_account.key {
    return Err(ProgramError::InvalidSeeds);
}
```

### 4. Use invoke_signed for PDAs

```rust
// ✅ PDAs sign with invoke_signed
invoke_signed(&ix, accounts, signer_seeds)?;

// ❌ Regular invoke won't work for PDA signers
invoke(&ix, accounts)?; // Fails if PDA needs to sign
```

### 5. Set Compute Budget Client-side

```rust
// ✅ Add compute budget instructions in client
let ixs = vec![
    ComputeBudgetInstruction::set_compute_unit_limit(400_000),
    your_program_ix,
];

// ❌ Cannot set from within program
// Programs cannot modify their own compute budget
```

### 6. Order Compute Budget Instructions First

```rust
// ✅ Compute budget instructions FIRST
let ixs = vec![
    compute_limit_ix,
    compute_price_ix,
    heap_size_ix,
    program_ix,
];

// ❌ Wrong order - may not apply
let ixs = vec![
    program_ix,
    compute_limit_ix,  // Too late!
];
```

### 7. Check Account Ownership Before Transfer

```rust
// ✅ Validate ownership for security
if from_account.owner != &solana_program::system_program::ID {
    msg!("Can only transfer from System-owned accounts");
    return Err(ProgramError::IllegalOwner);
}
```

---

## Summary

**Key Takeaways:**

1. **System Program** handles account creation, transfers, and allocation
2. **Compute Budget Program** instructions are added **client-side**, not in programs
3. **Always validate** program IDs before CPI
4. **Use rent exemption** when creating accounts
5. **PDAs require invoke_signed** for signing operations

**Most Common Operations:**

| Operation | Instruction | Use Case |
|-----------|------------|----------|
| Create account | `create_account` | New program accounts |
| Transfer lamports | `transfer` | SOL transfers |
| Set CU limit | `set_compute_unit_limit` | High-CU transactions |
| Set priority fee | `set_compute_unit_price` | Fast transaction processing |
| Request heap | `request_heap_frame` | Large data operations |

**System Program CPI Template:**

```rust
// Validate
if system_program.key != &solana_program::system_program::ID {
    return Err(ProgramError::IncorrectProgramId);
}

// Create instruction
let ix = system_instruction::transfer(from.key, to.key, amount);

// Invoke (or invoke_signed for PDAs)
invoke(&ix, &[from.clone(), to.clone(), system_program.clone()])?;
```

**Compute Budget Client Template:**

```rust
// Client-side
let ixs = vec![
    ComputeBudgetInstruction::set_compute_unit_limit(300_000),
    ComputeBudgetInstruction::set_compute_unit_price(10_000),
    your_program_ix,
];
```

Master these built-in programs for efficient account management and transaction optimization in production Solana programs.
