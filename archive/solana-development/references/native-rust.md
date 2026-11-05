# Native Rust Solana Programs Reference

This reference covers native Rust-specific implementation patterns and workflows for building Solana programs without the Anchor framework. For general concepts (what PDAs/CPIs are), see the other reference files.

## Table of Contents

- [Project Setup](#project-setup)
- [Entrypoint Patterns](#entrypoint-patterns)
- [Manual Account Handling](#manual-account-handling)
- [Manual Serialization](#manual-serialization)
- [Instruction Definition](#instruction-definition)
- [State Management](#state-management)
- [Manual CPI Patterns](#manual-cpi-patterns)
- [Build and Deploy Workflow](#build-and-deploy-workflow)
- [Testing with Mollusk](#testing-with-mollusk)
- [Verified Builds](#verified-builds)
- [Program Management](#program-management)
- [Common Native Patterns](#common-native-patterns)

---

## Project Setup

### Cargo.toml Configuration

Basic program configuration:

```toml
[package]
name = "my_program"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "lib"]  # cdylib for .so, lib for tests
name = "my_program"

[features]
no-entrypoint = []  # Disable entrypoint for testing/CPI

[dependencies]
solana-program = "2.1.0"
borsh = "1.5.1"
borsh-derive = "1.5.1"

[dev-dependencies]
mollusk-svm = "0.3.0"
solana-sdk = "2.1.0"

[profile.release]
overflow-checks = true
lto = "fat"
codegen-units = 1

[profile.release.build-override]
opt-level = 3
incremental = false
codegen-units = 1
```

### Dependency Versions

**Production Dependencies:**
- `solana-program = "2.1.0"` - Core program runtime APIs
- `borsh = "1.5.1"` - Serialization framework
- `borsh-derive = "1.5.1"` - Derive macros for Borsh

**Development Dependencies:**
- `mollusk-svm = "0.3.0"` - Fast testing framework
- `solana-sdk = "2.1.0"` - Client-side SDK for tests
- `mollusk-svm-bencher = "0.3.0"` - Compute unit benchmarking

**Optional Helpers:**
- `thiserror = "2.0"` - Error type definitions
- `num-derive = "0.4"` - Derive numeric traits
- `num-traits = "0.2"` - Numeric trait support
- `spl-token = "6.0"` - Token program integration
- `spl-associated-token-account = "5.0"` - ATA integration
- `bytemuck = "1.20"` - Zero-copy type conversions

### Workspace Setup Pattern

For multi-program projects:

```toml
# Workspace Cargo.toml
[workspace]
members = [
    "programs/program-one",
    "programs/program-two",
]
resolver = "2"

[workspace.dependencies]
solana-program = "2.1.0"
borsh = "1.5.1"

# Program Cargo.toml
[dependencies]
solana-program = { workspace = true }
borsh = { workspace = true }
```

### Project Structure

```
my-program/
├── Cargo.toml
├── src/
│   ├── lib.rs              # Entrypoint and routing
│   ├── instruction.rs      # Instruction definitions
│   ├── state.rs            # Account state structs
│   ├── processor.rs        # Instruction handlers
│   ├── error.rs            # Custom errors
│   └── utils.rs            # Helper functions
├── tests/
│   └── test.rs             # Mollusk tests
└── target/
    └── deploy/
        ├── program.so      # Built program binary
        └── program-keypair.json  # Program keypair
```

---

## Entrypoint Patterns

### Basic Entrypoint

The `entrypoint!` macro sets up the program entry:

```rust
use solana_program::{
    account_info::AccountInfo,
    entrypoint,
    entrypoint::ProgramResult,
    pubkey::Pubkey,
};

// Declare the entrypoint
entrypoint!(process_instruction);

// Process instruction function signature
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    // Route to handlers
    Ok(())
}
```

### Conditional Entrypoint (for testing/CPI)

Disable entrypoint when used as a dependency:

```rust
#[cfg(not(feature = "no-entrypoint"))]
use solana_program::entrypoint;

#[cfg(not(feature = "no-entrypoint"))]
entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    // Implementation
    Ok(())
}
```

### Instruction Routing Pattern

Route to different handlers based on instruction type:

```rust
use borsh::BorshDeserialize;

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    // Deserialize instruction
    let instruction = MyInstruction::try_from_slice(instruction_data)?;

    // Route to handler
    match instruction {
        MyInstruction::Initialize { data } => {
            process_initialize(program_id, accounts, data)
        }
        MyInstruction::Update { new_data } => {
            process_update(program_id, accounts, new_data)
        }
        MyInstruction::Close => {
            process_close(program_id, accounts)
        }
    }
}
```

### Multi-Module Routing

For larger programs, organize handlers in modules:

```rust
mod processor;

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = MyInstruction::try_from_slice(instruction_data)?;

    match instruction {
        MyInstruction::Initialize { data } => {
            processor::initialize::process(program_id, accounts, data)
        }
        MyInstruction::Update { new_data } => {
            processor::update::process(program_id, accounts, new_data)
        }
        MyInstruction::Close => {
            processor::close::process(program_id, accounts)
        }
    }
}
```

---

## Manual Account Handling

### Using next_account_info Iterator

The standard pattern for accessing accounts:

```rust
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
};

fn process_transfer(accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    // Get accounts in order
    let payer = next_account_info(account_info_iter)?;
    let recipient = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Use accounts...
    Ok(())
}
```

### AccountInfo Structure and Methods

Key fields and methods:

```rust
pub struct AccountInfo<'a> {
    pub key: &'a Pubkey,              // Account public key
    pub is_signer: bool,              // Signed transaction?
    pub is_writable: bool,            // Writable account?
    pub lamports: Rc<RefCell<&'a mut u64>>,  // Account balance
    pub data: Rc<RefCell<&'a mut [u8]>>,     // Account data
    pub owner: &'a Pubkey,            // Owner program
    pub executable: bool,             // Is executable?
    pub rent_epoch: Epoch,            // Rent epoch
}

// Common methods
impl<'a> AccountInfo<'a> {
    // Check if account signed the transaction
    pub fn is_signer(&self) -> bool;

    // Check if account is writable
    pub fn is_writable(&self) -> bool;

    // Borrow account data immutably
    pub fn data(&self) -> Ref<&mut [u8]>;

    // Borrow account data mutably
    pub fn data_mut(&self) -> RefMut<&mut [u8]>;

    // Borrow lamports immutably
    pub fn lamports(&self) -> Ref<&mut u64>;

    // Borrow lamports mutably
    pub fn lamports_mut(&self) -> RefMut<&mut u64>;

    // Get data length
    pub fn data_len(&self) -> usize;

    // Check if owned by program
    pub fn is_owned_by(&self, program_id: &Pubkey) -> bool;

    // Deserialize account data
    pub fn deserialize_data<T: BorshDeserialize>(&self) -> Result<T, Error>;

    // Serialize data into account
    pub fn serialize_data<T: BorshSerialize>(&self, state: &T) -> Result<(), Error>;
}
```

### Explicit Account Validation Patterns

**Signer Check:**

```rust
if !account.is_signer {
    return Err(ProgramError::MissingRequiredSignature);
}
```

**Writable Check:**

```rust
if !account.is_writable {
    return Err(ProgramError::InvalidAccountData);
}
```

**Owner Check:**

```rust
if account.owner != program_id {
    return Err(ProgramError::IncorrectProgramId);
}
```

**Specific Owner Check:**

```rust
use solana_program::system_program;

if account.owner != &system_program::ID {
    return Err(ProgramError::InvalidAccountOwner);
}
```

**Combined Validation:**

```rust
fn validate_account(
    account: &AccountInfo,
    expected_owner: &Pubkey,
    must_sign: bool,
    must_write: bool,
) -> ProgramResult {
    if must_sign && !account.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    if must_write && !account.is_writable {
        return Err(ProgramError::InvalidAccountData);
    }

    if account.owner != expected_owner {
        return Err(ProgramError::IncorrectProgramId);
    }

    Ok(())
}
```

**PDA Validation:**

```rust
fn validate_pda(
    account: &AccountInfo,
    seeds: &[&[u8]],
    program_id: &Pubkey,
) -> ProgramResult {
    let (expected_key, _bump) = Pubkey::find_program_address(seeds, program_id);

    if account.key != &expected_key {
        return Err(ProgramError::InvalidSeeds);
    }

    Ok(())
}
```

**Rent Exemption Check:**

```rust
use solana_program::sysvar::{rent::Rent, Sysvar};

fn check_rent_exempt(account: &AccountInfo) -> ProgramResult {
    let rent = Rent::get()?;

    if !rent.is_exempt(account.lamports(), account.data_len()) {
        return Err(ProgramError::AccountNotRentExempt);
    }

    Ok(())
}
```

### Account Data Access Patterns

**Immutable Borrow:**

```rust
let data = account.data.borrow();
let state = MyState::try_from_slice(&data)?;
```

**Mutable Borrow:**

```rust
let mut data = account.data.borrow_mut();
let mut state = MyState::try_from_slice(&data)?;
state.counter += 1;
state.serialize(&mut &mut data[..])?;
```

**Lamport Access:**

```rust
// Read lamports
let balance = account.lamports();
println!("Balance: {}", *balance);

// Modify lamports (for transfers)
**account.lamports.borrow_mut() = new_balance;
```

**Zero-Copy Data Access:**

```rust
use bytemuck::{Pod, Zeroable};

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
struct FastState {
    value: u64,
    flag: u8,
}

fn read_fast_state(account: &AccountInfo) -> Result<&FastState, ProgramError> {
    let data = account.try_borrow_data()?;
    bytemuck::try_from_bytes(&data[..std::mem::size_of::<FastState>()])
        .map_err(|_| ProgramError::InvalidAccountData)
}
```

---

## Manual Serialization

### Borsh Derive

Use `BorshSerialize` and `BorshDeserialize` for most cases:

```rust
use borsh::{BorshSerialize, BorshDeserialize};

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct MyState {
    pub is_initialized: bool,
    pub counter: u64,
    pub authority: Pubkey,
    pub data: Vec<u8>,
}
```

### Manual Borsh Implementation

For custom serialization logic:

```rust
use borsh::io::{Read, Write, Result as BorshResult};

#[derive(Debug)]
pub struct CustomState {
    pub flag: bool,
    pub value: u64,
}

impl BorshSerialize for CustomState {
    fn serialize<W: Write>(&self, writer: &mut W) -> BorshResult<()> {
        self.flag.serialize(writer)?;
        self.value.serialize(writer)?;
        Ok(())
    }
}

impl BorshDeserialize for CustomState {
    fn deserialize_reader<R: Read>(reader: &mut R) -> BorshResult<Self> {
        let flag = bool::deserialize_reader(reader)?;
        let value = u64::deserialize_reader(reader)?;
        Ok(Self { flag, value })
    }
}
```

### Account Data Layout Planning

Calculate and document exact byte offsets:

```rust
// Account layout documentation
// [0] is_initialized: bool (1 byte)
// [1-8] counter: u64 (8 bytes)
// [9-40] authority: Pubkey (32 bytes)
// Total: 41 bytes

#[derive(BorshSerialize, BorshDeserialize)]
pub struct Counter {
    pub is_initialized: bool,  // 1 byte
    pub counter: u64,          // 8 bytes
    pub authority: Pubkey,     // 32 bytes
}

impl Counter {
    pub const LEN: usize = 1 + 8 + 32;  // 41 bytes
}
```

### Packing and Unpacking Account Data

**Deserialize (unpack):**

```rust
use borsh::BorshDeserialize;

fn get_state(account: &AccountInfo) -> Result<MyState, ProgramError> {
    let data = account.try_borrow_data()?;
    MyState::try_from_slice(&data)
        .map_err(|_| ProgramError::InvalidAccountData)
}
```

**Serialize (pack):**

```rust
use borsh::BorshSerialize;

fn save_state(account: &AccountInfo, state: &MyState) -> ProgramResult {
    let mut data = account.try_borrow_mut_data()?;
    state.serialize(&mut &mut data[..])
        .map_err(|_| ProgramError::InvalidAccountData)?;
    Ok(())
}
```

**Combined Pattern:**

```rust
fn update_counter(account: &AccountInfo, increment: u64) -> ProgramResult {
    // Deserialize
    let mut data = account.try_borrow_mut_data()?;
    let mut state = MyState::try_from_slice(&data)?;

    // Modify
    state.counter += increment;

    // Serialize back
    state.serialize(&mut &mut data[..])?;
    Ok(())
}
```

### Zero-Copy Patterns with Bytemuck

For high-performance, use zero-copy with bytemuck:

```rust
use bytemuck::{Pod, Zeroable, from_bytes_mut, bytes_of};

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
pub struct ZeroCopyState {
    pub is_initialized: u8,  // bool as u8
    pub counter: u64,
    pub authority: [u8; 32], // Pubkey as bytes
}

impl ZeroCopyState {
    pub const LEN: usize = std::mem::size_of::<Self>();
}

// Read zero-copy
fn get_state(account: &AccountInfo) -> Result<&ZeroCopyState, ProgramError> {
    let data = account.try_borrow_data()?;
    bytemuck::try_from_bytes(&data[..ZeroCopyState::LEN])
        .map_err(|_| ProgramError::InvalidAccountData)
}

// Write zero-copy
fn update_state(account: &AccountInfo, new_counter: u64) -> ProgramResult {
    let mut data = account.try_borrow_mut_data()?;
    let state = bytemuck::try_from_bytes_mut::<ZeroCopyState>(
        &mut data[..ZeroCopyState::LEN]
    ).map_err(|_| ProgramError::InvalidAccountData)?;

    state.counter = new_counter;
    Ok(())
}
```

### Variable-Length Data

For dynamic data, use a header + data pattern:

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct VarLenState {
    pub is_initialized: bool,
    pub data_len: u32,
    // Followed by data_len bytes
}

impl VarLenState {
    pub const HEADER_LEN: usize = 1 + 4;  // bool + u32

    pub fn unpack(data: &[u8]) -> Result<(Self, &[u8]), ProgramError> {
        if data.len() < Self::HEADER_LEN {
            return Err(ProgramError::InvalidAccountData);
        }

        let header = Self::try_from_slice(&data[..Self::HEADER_LEN])?;
        let data_slice = &data[Self::HEADER_LEN..Self::HEADER_LEN + header.data_len as usize];

        Ok((header, data_slice))
    }
}
```

---

## Instruction Definition

### Borsh-Serializable Instruction Enums

Define instructions as enums:

```rust
use borsh::{BorshSerialize, BorshDeserialize};
use solana_program::pubkey::Pubkey;

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub enum MyInstruction {
    /// Initialize a new account
    ///
    /// Accounts expected:
    /// 0. `[writable, signer]` Account to initialize
    /// 1. `[signer]` Authority
    /// 2. `[]` System Program
    Initialize {
        initial_value: u64,
    },

    /// Update account data
    ///
    /// Accounts expected:
    /// 0. `[writable]` Account to update
    /// 1. `[signer]` Authority
    Update {
        new_value: u64,
    },

    /// Transfer ownership
    ///
    /// Accounts expected:
    /// 0. `[writable]` Account
    /// 1. `[signer]` Current authority
    /// 2. `[]` New authority
    TransferOwnership {
        new_authority: Pubkey,
    },

    /// Close account and reclaim rent
    ///
    /// Accounts expected:
    /// 0. `[writable]` Account to close
    /// 1. `[writable]` Rent recipient
    /// 2. `[signer]` Authority
    Close,
}
```

### Instruction Data Layout

**Fixed-Size Instructions:**

```rust
// Discriminator (1 byte) + data
// [0] = 0 -> Initialize
// [1] = 1 -> Update
// etc.

#[derive(BorshSerialize, BorshDeserialize)]
pub enum SimpleInstruction {
    Initialize = 0,
    Update = 1,
    Close = 2,
}
```

**Instructions with Parameters:**

```rust
// Manual discriminator pattern
pub enum MyInstruction {
    // Discriminator 0: [0, value_bytes[0..8]]
    Initialize { value: u64 },

    // Discriminator 1: [1, amount_bytes[0..8]]
    Transfer { amount: u64 },
}

impl MyInstruction {
    pub fn unpack(input: &[u8]) -> Result<Self, ProgramError> {
        let (&discriminator, rest) = input.split_first()
            .ok_or(ProgramError::InvalidInstructionData)?;

        Ok(match discriminator {
            0 => {
                let value = u64::from_le_bytes(rest[..8].try_into().unwrap());
                Self::Initialize { value }
            }
            1 => {
                let amount = u64::from_le_bytes(rest[..8].try_into().unwrap());
                Self::Transfer { amount }
            }
            _ => return Err(ProgramError::InvalidInstructionData),
        })
    }
}
```

### Dispatching Instructions

**Pattern 1: Direct Match**

```rust
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = MyInstruction::try_from_slice(instruction_data)?;

    match instruction {
        MyInstruction::Initialize { initial_value } => {
            msg!("Instruction: Initialize");
            process_initialize(program_id, accounts, initial_value)
        }
        MyInstruction::Update { new_value } => {
            msg!("Instruction: Update");
            process_update(program_id, accounts, new_value)
        }
        MyInstruction::Close => {
            msg!("Instruction: Close");
            process_close(program_id, accounts)
        }
    }
}
```

**Pattern 2: Handler Functions**

```rust
impl MyInstruction {
    pub fn process(
        &self,
        program_id: &Pubkey,
        accounts: &[AccountInfo],
    ) -> ProgramResult {
        match self {
            Self::Initialize { initial_value } => {
                Self::process_initialize(program_id, accounts, *initial_value)
            }
            Self::Update { new_value } => {
                Self::process_update(program_id, accounts, *new_value)
            }
            Self::Close => {
                Self::process_close(program_id, accounts)
            }
        }
    }

    fn process_initialize(
        program_id: &Pubkey,
        accounts: &[AccountInfo],
        initial_value: u64,
    ) -> ProgramResult {
        // Implementation
        Ok(())
    }
}
```

---

## State Management

### Defining Account State Structs

```rust
use borsh::{BorshSerialize, BorshDeserialize};
use solana_program::pubkey::Pubkey;

#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct UserAccount {
    pub is_initialized: bool,
    pub authority: Pubkey,
    pub balance: u64,
    pub last_updated: i64,
}

impl UserAccount {
    pub const LEN: usize = 1 + 32 + 8 + 8;  // 49 bytes
}
```

### Calculating Account Sizes

**Fixed-Size Accounts:**

```rust
impl MyState {
    // Method 1: Manual calculation
    pub const LEN: usize =
        1 +   // is_initialized: bool
        32 +  // authority: Pubkey
        8 +   // counter: u64
        4 +   // data_len: u32
        100;  // data: [u8; 100]

    // Method 2: Use size_of
    pub const LEN_ALT: usize = std::mem::size_of::<Self>();
}
```

**Variable-Size Accounts:**

```rust
impl DynamicState {
    pub const BASE_LEN: usize = 1 + 32 + 8;  // Fixed fields

    pub fn calculate_size(data_len: usize) -> usize {
        Self::BASE_LEN + 4 + data_len  // +4 for length prefix
    }
}
```

**With Borsh:**

```rust
use borsh::BorshSerialize;

let state = MyState { /* ... */ };
let serialized = state.try_to_vec()?;
let size = serialized.len();  // Actual size needed
```

### Initializing Accounts Manually with System Program CPI

**Complete Initialization Pattern:**

```rust
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::invoke,
    pubkey::Pubkey,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};

fn process_initialize(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    initial_value: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    let new_account = next_account_info(account_info_iter)?;
    let payer = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Calculate space needed
    let space = MyState::LEN;

    // Calculate rent
    let rent = Rent::get()?;
    let rent_lamports = rent.minimum_balance(space);

    // Create account via CPI to System Program
    invoke(
        &system_instruction::create_account(
            payer.key,           // Funding account
            new_account.key,     // New account
            rent_lamports,       // Lamports
            space as u64,        // Space
            program_id,          // Owner
        ),
        &[
            payer.clone(),
            new_account.clone(),
            system_program.clone(),
        ],
    )?;

    // Initialize account data
    let mut data = new_account.try_borrow_mut_data()?;
    let state = MyState {
        is_initialized: true,
        counter: initial_value,
        authority: *payer.key,
    };
    state.serialize(&mut &mut data[..])?;

    Ok(())
}
```

**Initialize PDA Pattern:**

```rust
use solana_program::program::invoke_signed;

fn initialize_pda(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    let pda = next_account_info(account_info_iter)?;
    let payer = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Verify PDA
    let (expected_pda, expected_bump) = Pubkey::find_program_address(seeds, program_id);
    if pda.key != &expected_pda || bump != expected_bump {
        return Err(ProgramError::InvalidSeeds);
    }

    // Create PDA account
    let space = MyState::LEN;
    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(space);

    let bump_seed = &[bump];
    let seeds_with_bump = &[seeds, &[bump_seed.as_slice()]].concat();

    invoke_signed(
        &system_instruction::create_account(
            payer.key,
            pda.key,
            lamports,
            space as u64,
            program_id,
        ),
        &[payer.clone(), pda.clone(), system_program.clone()],
        &[seeds_with_bump],  // Signer seeds
    )?;

    // Initialize data
    let mut data = pda.try_borrow_mut_data()?;
    let state = MyState::default();
    state.serialize(&mut &mut data[..])?;

    Ok(())
}
```

### Account Reallocation

Resize account data:

```rust
use solana_program::program::invoke;

fn reallocate_account(
    account: &AccountInfo,
    payer: &AccountInfo,
    new_size: usize,
    program_id: &Pubkey,
) -> ProgramResult {
    // Verify ownership
    if account.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }

    // Reallocate
    account.realloc(new_size, false)?;

    // Fund additional rent if needed
    let rent = Rent::get()?;
    let new_minimum_balance = rent.minimum_balance(new_size);
    let current_balance = account.lamports();

    if *current_balance < new_minimum_balance {
        let additional = new_minimum_balance - *current_balance;

        **payer.lamports.borrow_mut() -= additional;
        **account.lamports.borrow_mut() += additional;
    }

    Ok(())
}
```

---

## Manual CPI Patterns

### Using invoke

For CPIs without PDA signers:

```rust
use solana_program::{
    account_info::AccountInfo,
    instruction::{AccountMeta, Instruction},
    program::invoke,
    pubkey::Pubkey,
    system_instruction,
};

fn transfer_sol(
    from: &AccountInfo,
    to: &AccountInfo,
    system_program: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    invoke(
        &system_instruction::transfer(from.key, to.key, amount),
        &[from.clone(), to.clone(), system_program.clone()],
    )
}
```

### Using invoke_signed

For CPIs with PDA signers:

```rust
use solana_program::program::invoke_signed;

fn pda_transfer(
    pda: &AccountInfo,
    recipient: &AccountInfo,
    system_program: &AccountInfo,
    amount: u64,
    seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    let bump_seed = &[bump];
    let signer_seeds: &[&[&[u8]]] = &[
        &[seeds, &[bump_seed]].concat()
    ];

    invoke_signed(
        &system_instruction::transfer(pda.key, recipient.key, amount),
        &[pda.clone(), recipient.clone(), system_program.clone()],
        signer_seeds,
    )
}
```

### Building AccountMeta Arrays

Manually construct account metadata:

```rust
use solana_program::instruction::AccountMeta;

let account_metas = vec![
    AccountMeta::new(*writable_account.key, false),        // Writable, not signer
    AccountMeta::new(*writable_signer.key, true),          // Writable, signer
    AccountMeta::new_readonly(*readonly_account.key, false), // Read-only, not signer
    AccountMeta::new_readonly(*readonly_signer.key, true),  // Read-only, signer
];
```

### Creating Instruction Structs

Build instructions for CPI:

```rust
use solana_program::instruction::Instruction;

fn build_custom_instruction(
    program_id: &Pubkey,
    account1: &Pubkey,
    account2: &Pubkey,
    data: Vec<u8>,
) -> Instruction {
    Instruction {
        program_id: *program_id,
        accounts: vec![
            AccountMeta::new(*account1, true),
            AccountMeta::new(*account2, false),
        ],
        data,
    }
}

// Use in CPI
fn call_custom_program(
    program: &AccountInfo,
    account1: &AccountInfo,
    account2: &AccountInfo,
    data: Vec<u8>,
) -> ProgramResult {
    let instruction = build_custom_instruction(
        program.key,
        account1.key,
        account2.key,
        data,
    );

    invoke(
        &instruction,
        &[account1.clone(), account2.clone()],
    )
}
```

### SPL Token CPI Pattern

Transfer tokens via CPI:

```rust
use spl_token::instruction as token_instruction;

fn transfer_tokens(
    token_program: &AccountInfo,
    source: &AccountInfo,
    destination: &AccountInfo,
    authority: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    invoke(
        &token_instruction::transfer(
            token_program.key,
            source.key,
            destination.key,
            authority.key,
            &[],  // No multisig signers
            amount,
        )?,
        &[source.clone(), destination.clone(), authority.clone()],
    )
}

fn transfer_tokens_with_pda(
    token_program: &AccountInfo,
    source: &AccountInfo,
    destination: &AccountInfo,
    pda_authority: &AccountInfo,
    amount: u64,
    seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    let bump_seed = &[bump];
    let signer_seeds: &[&[&[u8]]] = &[
        &[seeds, &[bump_seed]].concat()
    ];

    invoke_signed(
        &token_instruction::transfer(
            token_program.key,
            source.key,
            destination.key,
            pda_authority.key,
            &[],
            amount,
        )?,
        &[source.clone(), destination.clone(), pda_authority.clone()],
        signer_seeds,
    )
}
```

---

## Build and Deploy Workflow

### cargo build-sbf Command

Build the program for Solana:

```bash
# Basic build
cargo build-sbf

# Build with specific Solana version
cargo build-sbf --solana-version 2.1.0

# Build for mainnet (with optimizations)
cargo build-sbf --release

# Specify output directory
cargo build-sbf --sbf-out-dir ./output
```

### Understanding .so and -keypair.json Files

After building:

```
target/deploy/
├── my_program.so              # Compiled program binary
└── my_program-keypair.json    # Program's keypair (address)
```

**Program ID:**

```bash
# Get program ID from keypair
solana address -k target/deploy/my_program-keypair.json
```

**Update Program ID in Code:**

```rust
// In lib.rs
declare_id!("YourProgramID11111111111111111111111111111");
```

### solana program deploy Commands

**Deploy to Devnet:**

```bash
# Set cluster
solana config set --url devnet

# Fund deployer account
solana airdrop 2

# Deploy program
solana program deploy target/deploy/my_program.so

# Deploy to specific program ID
solana program deploy \
    target/deploy/my_program.so \
    --program-id target/deploy/my_program-keypair.json

# Deploy with custom keypair
solana program deploy \
    target/deploy/my_program.so \
    --program-id custom-keypair.json \
    --upgrade-authority ~/.config/solana/id.json
```

**Deploy to Mainnet:**

```bash
solana config set --url mainnet-beta

# Deploy (costs SOL based on program size)
solana program deploy target/deploy/my_program.so
```

### Program Size and Cost Calculation

**Check Program Size:**

```bash
ls -lh target/deploy/my_program.so

# Or get detailed info
solana program show <PROGRAM_ID>
```

**Calculate Deployment Cost:**

Program cost formula: `rent_exemption(program_size)`

```bash
# Get rent for specific size
solana rent <SIZE_IN_BYTES>

# Example for 200KB program
solana rent 204800
# Output: Rent-exempt minimum: 1.42607328 SOL
```

**Typical Sizes:**
- Simple programs: 50-100 KB
- Medium programs: 100-300 KB
- Large programs: 300-500 KB
- Maximum: ~1 MB (hard limit)

**Reduce Program Size:**

```toml
# In Cargo.toml
[profile.release]
opt-level = "z"        # Optimize for size
lto = true            # Link-time optimization
codegen-units = 1     # Better optimization
strip = true          # Strip symbols
```

---

## Testing with Mollusk

### Test Structure with mollusk-svm

Basic test setup:

```rust
#[cfg(test)]
mod tests {
    use {
        mollusk_svm::Mollusk,
        solana_sdk::{
            account::Account,
            instruction::{AccountMeta, Instruction},
            pubkey::Pubkey,
        },
    };

    #[test]
    fn test_initialize() {
        // Create Mollusk instance
        let program_id = Pubkey::new_unique();
        let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

        // Test implementation...
    }
}
```

### Creating Test Accounts

**System-Owned Account:**

```rust
let user = Pubkey::new_unique();
let user_account = Account {
    lamports: 1_000_000,
    data: vec![],
    owner: solana_sdk::system_program::id(),
    executable: false,
    rent_epoch: 0,
};
```

**Program-Owned Account:**

```rust
let state_account = Pubkey::new_unique();
let state = Account {
    lamports: rent_lamports,
    data: vec![0; MyState::LEN],
    owner: program_id,
    executable: false,
    rent_epoch: 0,
};
```

**Pre-Initialized Account:**

```rust
use borsh::BorshSerialize;

let mut data = vec![0; MyState::LEN];
let initial_state = MyState {
    is_initialized: true,
    counter: 42,
    authority: user,
};
initial_state.serialize(&mut data.as_mut_slice()).unwrap();

let initialized_account = Account {
    lamports: rent_lamports,
    data,
    owner: program_id,
    executable: false,
    rent_epoch: 0,
};
```

### Process Instructions and Validate Results

**Basic Process and Check:**

```rust
use mollusk_svm::result::Check;

#[test]
fn test_instruction() {
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

    let user = Pubkey::new_unique();
    let instruction = Instruction::new_with_bytes(
        program_id,
        &[0],  // Instruction data
        vec![
            AccountMeta::new(user, true),
        ],
    );

    let accounts = vec![
        (user, Account {
            lamports: 1_000_000,
            data: vec![],
            owner: solana_sdk::system_program::id(),
            executable: false,
            rent_epoch: 0,
        }),
    ];

    let checks = vec![
        Check::success(),
        Check::account(&user)
            .lamports(1_000_000)
            .build(),
    ];

    mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
}
```

**Validate Account Data:**

```rust
let expected_data = MyState {
    is_initialized: true,
    counter: 10,
    authority: user,
}.try_to_vec().unwrap();

let checks = vec![
    Check::success(),
    Check::account(&state_account)
        .data(&expected_data)
        .lamports(rent_lamports)
        .owner(&program_id)
        .build(),
];
```

**Check Specific Data Slice:**

```rust
let checks = vec![
    Check::success(),
    Check::account(&account)
        .data_slice(0, &[1])  // Check first byte is 1 (initialized)
        .data_slice(8, &10u64.to_le_bytes())  // Check counter at offset 8
        .build(),
];
```

**Test Error Conditions:**

```rust
use solana_sdk::instruction::InstructionError;

let checks = vec![
    Check::instruction_err(InstructionError::InvalidInstructionData),
];

mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
```

### Compute Unit Benchmarking

**Basic Benchmark:**

```rust
use mollusk_svm_bencher::MolluskComputeUnitBencher;

fn main() {
    let program_id = Pubkey::new_unique();
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

    let instruction = /* build instruction */;
    let accounts = /* setup accounts */;

    MolluskComputeUnitBencher::new(mollusk)
        .bench(("my_instruction", &instruction, &accounts))
        .must_pass(true)
        .out_dir("./benches")
        .execute();
}
```

**Run Benchmark:**

```bash
# Build first
cargo build-sbf

# Run benchmark
cargo run --bin bench
```

**Benchmark Output:**

```
╭──────────────────────────────┬────────────────────╮
│ Instruction                  │ Compute Units      │
├──────────────────────────────┼────────────────────┤
│ my_instruction               │ 1,234              │
╰──────────────────────────────┴────────────────────╯

Results written to: ./benches/compute_units.json
```

---

## Verified Builds

### solana-verify Workflow

Verify programs on-chain match source code:

**Install solana-verify:**

```bash
cargo install solana-verify
```

**Verify a Program:**

```bash
# Verify remote build
solana-verify verify-from-repo \
    --program-id <PROGRAM_ID> \
    --remote https://github.com/user/repo \
    --commit-hash <COMMIT_HASH> \
    --library-name program_name

# Verify with mount path (for workspace)
solana-verify verify-from-repo \
    --program-id <PROGRAM_ID> \
    --remote https://github.com/user/repo \
    --commit-hash <COMMIT_HASH> \
    --mount-path programs/my-program \
    --library-name my_program
```

### Docker-Based Builds

Build in Docker for reproducibility:

**Dockerfile:**

```dockerfile
FROM --platform=linux/amd64 projectserum/build:v0.29.0

WORKDIR /build
COPY . .

RUN cargo build-sbf --release
```

**Build Command:**

```bash
docker build -t my-program-build .
docker create --name extract my-program-build
docker cp extract:/build/target/deploy/my_program.so ./my_program-verifiable.so
docker rm extract
```

**Verify Deterministic:**

```bash
# Compare hashes
sha256sum target/deploy/my_program.so
sha256sum my_program-verifiable.so
# Should match!
```

### Buffer Uploads for Multisig

Deploy via buffer for multisig upgrade authority:

```bash
# Write program to buffer
solana program write-buffer target/deploy/my_program.so

# Output: Buffer: <BUFFER_ADDRESS>

# Set buffer authority to multisig
solana program set-buffer-authority <BUFFER_ADDRESS> --new-buffer-authority <MULTISIG_ADDRESS>

# Later: Deploy from buffer (requires multisig)
solana program deploy --buffer <BUFFER_ADDRESS> --program-id <PROGRAM_ID>
```

**Squads Multisig Example:**

```bash
# 1. Write buffer
BUFFER=$(solana program write-buffer target/deploy/my_program.so | grep "Buffer:" | awk '{print $2}')

# 2. Transfer buffer authority to Squads
solana program set-buffer-authority $BUFFER --new-buffer-authority <SQUADS_ADDRESS>

# 3. Create proposal in Squads UI to deploy from buffer
```

---

## Program Management

### solana program show

Get program information:

```bash
# Show program details
solana program show <PROGRAM_ID>

# Output:
# Program Id: <PROGRAM_ID>
# Owner: BPFLoaderUpgradeab1e11111111111111111111111
# ProgramData Address: <DATA_ADDRESS>
# Authority: <UPGRADE_AUTHORITY>
# Last Deployed In Slot: 123456789
# Data Length: 204800 bytes
# Balance: 1.42607328 SOL
```

**Show Program Data:**

```bash
# Get upgrade authority
solana program show <PROGRAM_ID> | grep Authority

# Get program size
solana program show <PROGRAM_ID> | grep "Data Length"
```

### Authority Transfers

**Transfer Upgrade Authority:**

```bash
# Transfer to new authority
solana program set-upgrade-authority \
    <PROGRAM_ID> \
    --new-upgrade-authority <NEW_AUTHORITY>

# Transfer to multisig
solana program set-upgrade-authority \
    <PROGRAM_ID> \
    --new-upgrade-authority <MULTISIG_ADDRESS>
```

### Making Programs Immutable

Remove upgrade authority to make program immutable:

```bash
# Make immutable (IRREVERSIBLE!)
solana program set-upgrade-authority <PROGRAM_ID> --final

# Verify immutability
solana program show <PROGRAM_ID>
# Authority: none
```

**Warning:** This is permanent. The program can never be upgraded again.

### Closing Programs

Reclaim rent from closed programs:

```bash
# Close program and reclaim rent
solana program close <PROGRAM_ID>

# Close and send rent to specific recipient
solana program close <PROGRAM_ID> --recipient <RECIPIENT_ADDRESS>

# Close program buffer
solana program close --buffers
```

**Requirements:**
- Must be upgrade authority
- Program must not be marked as final
- Recipient receives all lamports from program account

---

## Common Native Patterns

### PDA Derivation and Signing

**Find PDA:**

```rust
use solana_program::pubkey::Pubkey;

fn get_user_pda(user: &Pubkey, program_id: &Pubkey) -> (Pubkey, u8) {
    Pubkey::find_program_address(
        &[
            b"user",
            user.as_ref(),
        ],
        program_id,
    )
}
```

**Verify PDA:**

```rust
fn validate_pda(
    pda: &AccountInfo,
    seeds: &[&[u8]],
    bump: u8,
    program_id: &Pubkey,
) -> ProgramResult {
    let expected_pda = Pubkey::create_program_address(
        &[seeds, &[&[bump]]].concat(),
        program_id,
    )?;

    if pda.key != &expected_pda {
        return Err(ProgramError::InvalidSeeds);
    }

    Ok(())
}
```

**Sign with PDA:**

```rust
use solana_program::program::invoke_signed;

fn pda_invoke(
    instruction: &Instruction,
    accounts: &[AccountInfo],
    user: &Pubkey,
    bump: u8,
) -> ProgramResult {
    let signer_seeds: &[&[&[u8]]] = &[
        &[b"user", user.as_ref(), &[bump]]
    ];

    invoke_signed(instruction, accounts, signer_seeds)
}
```

### Rent Calculation

**Calculate Minimum Balance:**

```rust
use solana_program::{
    rent::Rent,
    sysvar::Sysvar,
};

fn get_rent_exempt_balance(data_len: usize) -> Result<u64, ProgramError> {
    let rent = Rent::get()?;
    Ok(rent.minimum_balance(data_len))
}
```

**Check if Rent Exempt:**

```rust
fn is_rent_exempt(account: &AccountInfo) -> Result<bool, ProgramError> {
    let rent = Rent::get()?;
    Ok(rent.is_exempt(account.lamports(), account.data_len()))
}
```

### Lamport Transfers

**Direct Transfer (modify lamports):**

```rust
fn transfer_lamports(
    from: &AccountInfo,
    to: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    // Borrow and update lamports
    **from.try_borrow_mut_lamports()? -= amount;
    **to.try_borrow_mut_lamports()? += amount;

    Ok(())
}
```

**Via System Program:**

```rust
use solana_program::{
    program::invoke,
    system_instruction,
};

fn transfer_via_system_program(
    from: &AccountInfo,
    to: &AccountInfo,
    system_program: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    invoke(
        &system_instruction::transfer(from.key, to.key, amount),
        &[from.clone(), to.clone(), system_program.clone()],
    )
}
```

### Error Handling with ProgramError

**Using Built-in Errors:**

```rust
use solana_program::program_error::ProgramError;

if !account.is_signer {
    return Err(ProgramError::MissingRequiredSignature);
}

if account.owner != program_id {
    return Err(ProgramError::IncorrectProgramId);
}

if account.data_len() < MyState::LEN {
    return Err(ProgramError::AccountDataTooSmall);
}
```

**Custom Errors:**

```rust
use solana_program::program_error::ProgramError;
use thiserror::Error;

#[derive(Error, Debug, Copy, Clone)]
pub enum MyError {
    #[error("Account already initialized")]
    AlreadyInitialized,

    #[error("Invalid authority")]
    InvalidAuthority,

    #[error("Arithmetic overflow")]
    Overflow,
}

impl From<MyError> for ProgramError {
    fn from(e: MyError) -> Self {
        ProgramError::Custom(e as u32)
    }
}

// Usage
if state.is_initialized {
    return Err(MyError::AlreadyInitialized.into());
}
```

**With num_derive:**

```rust
use num_derive::FromPrimitive;
use num_traits::FromPrimitive;
use solana_program::{
    decode_error::DecodeError,
    program_error::{PrintProgramError, ProgramError},
};
use thiserror::Error;

#[derive(Clone, Debug, Eq, Error, FromPrimitive, PartialEq)]
pub enum MyError {
    #[error("Already initialized")]
    AlreadyInitialized,

    #[error("Invalid authority")]
    InvalidAuthority,
}

impl From<MyError> for ProgramError {
    fn from(e: MyError) -> Self {
        ProgramError::Custom(e as u32)
    }
}

impl<T> DecodeError<T> for MyError {
    fn type_of() -> &'static str {
        "MyError"
    }
}

impl PrintProgramError for MyError {
    fn print<E>(&self)
    where
        E: 'static + std::error::Error + DecodeError<E> + PrintProgramError + FromPrimitive,
    {
        match self {
            MyError::AlreadyInitialized => msg!("Error: Already initialized"),
            MyError::InvalidAuthority => msg!("Error: Invalid authority"),
        }
    }
}
```

### Logging and Debugging

**Basic Logging:**

```rust
use solana_program::msg;

msg!("Processing instruction");
msg!("Counter value: {}", counter);
msg!("Account: {}, balance: {}", account.key, account.lamports());
```

**Compute Units Logging:**

```rust
use solana_program::log::sol_log_compute_units;

sol_log_compute_units();  // Log current compute units used
```

**Data Logging:**

```rust
use solana_program::log::sol_log_data;

// Log data for off-chain processing
sol_log_data(&[b"event", &event_data]);
```

### Clock Access

Get current timestamp and slot:

```rust
use solana_program::{
    clock::Clock,
    sysvar::Sysvar,
};

fn get_current_time() -> Result<i64, ProgramError> {
    let clock = Clock::get()?;
    Ok(clock.unix_timestamp)
}

fn get_current_slot() -> Result<u64, ProgramError> {
    let clock = Clock::get()?;
    Ok(clock.slot)
}
```

### Account Closure Pattern

Properly close accounts and reclaim rent:

```rust
fn close_account(
    account_to_close: &AccountInfo,
    destination: &AccountInfo,
) -> ProgramResult {
    // Transfer all lamports
    let dest_starting_lamports = destination.lamports();
    **destination.lamports.borrow_mut() = dest_starting_lamports
        .checked_add(account_to_close.lamports())
        .ok_or(ProgramError::ArithmeticOverflow)?;

    **account_to_close.lamports.borrow_mut() = 0;

    // Zero out data
    let mut data = account_to_close.try_borrow_mut_data()?;
    data.fill(0);

    Ok(())
}
```

### Discriminator Pattern

Add discriminator to distinguish account types:

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub enum AccountType {
    Uninitialized,
    User,
    Config,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct UserAccount {
    pub account_type: AccountType,  // Discriminator
    pub authority: Pubkey,
    pub balance: u64,
}

impl UserAccount {
    pub const LEN: usize = 1 + 32 + 8;

    pub fn validate_type(account: &AccountInfo) -> ProgramResult {
        let data = account.try_borrow_data()?;
        let account_type = AccountType::try_from_slice(&data[..1])?;

        match account_type {
            AccountType::User => Ok(()),
            _ => Err(ProgramError::InvalidAccountData),
        }
    }
}
```

---

## Additional Resources

- **Solana Program Examples**: https://github.com/solana-developers/program-examples
- **Mollusk Testing**: https://github.com/anza-xyz/mollusk
- **solana-program Docs**: https://docs.rs/solana-program
- **Solana Cookbook**: https://solanacookbook.com/
- **SPL Token**: https://spl.solana.com/token
- **Solana Verify**: https://github.com/Ellipsis-Labs/solana-verifiable-build

---

*This reference focuses on native Rust implementation patterns. For conceptual understanding of Solana primitives (PDAs, CPIs, accounts, etc.), see the other reference files in this directory.*
