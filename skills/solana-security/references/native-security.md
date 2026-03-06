# Native Rust Security Patterns for Solana Programs

This reference covers security vulnerabilities and best practices specific to Solana programs built with native Rust (without Anchor framework).

## Table of Contents

1. [Manual Account Validation](#manual-account-validation)
2. [Account Discriminator Patterns](#account-discriminator-patterns)
3. [PDA Security in Native Rust](#pda-security-in-native-rust)
4. [Manual CPI Security](#manual-cpi-security)
5. [Manual Serialization Security](#manual-serialization-security)
6. [Rent and Space Management](#rent-and-space-management)
7. [Error Handling in Native Rust](#error-handling-in-native-rust)
8. [Token Program Integration](#token-program-integration)
9. [Low-Level Security Patterns](#low-level-security-patterns)
10. [Native Rust Best Practices](#native-rust-best-practices)

---

## Manual Account Validation

In native Rust programs, ALL account validation must be performed manually. Missing any check can lead to critical vulnerabilities.

### Signer Checks

**Vulnerable:**
```rust
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    _instruction_data: &[u8],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let authority = next_account_info(account_info_iter)?;

    // Missing signer check - anyone can call this!
    // Perform privileged operation
    Ok(())
}
```

**Secure:**
```rust
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    _instruction_data: &[u8],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let authority = next_account_info(account_info_iter)?;

    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Now safe to perform privileged operation
    Ok(())
}
```

### Owner Validation

**Vulnerable:**
```rust
pub fn update_config(accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let config_account = next_account_info(account_info_iter)?;

    // Missing owner check - could be any account!
    let mut config_data = Config::try_from_slice(&config_account.data.borrow())?;
    config_data.value = 42;
    config_data.serialize(&mut *config_account.data.borrow_mut())?;

    Ok(())
}
```

**Secure:**
```rust
pub fn update_config(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let config_account = next_account_info(account_info_iter)?;

    // Verify this account is owned by our program
    if config_account.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }

    let mut config_data = Config::try_from_slice(&config_account.data.borrow())?;
    config_data.value = 42;
    config_data.serialize(&mut *config_account.data.borrow_mut())?;

    Ok(())
}
```

### Writable Checks

**Vulnerable:**
```rust
pub fn transfer_tokens(accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let source = next_account_info(account_info_iter)?;

    // Missing writable check - runtime will panic!
    let mut data = source.try_borrow_mut_data()?;
    // Modify data...
    Ok(())
}
```

**Secure:**
```rust
pub fn transfer_tokens(accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let source = next_account_info(account_info_iter)?;

    if !source.is_writable {
        return Err(ProgramError::InvalidAccountData);
    }

    let mut data = source.try_borrow_mut_data()?;
    // Safe to modify data
    Ok(())
}
```

### Comprehensive Validation Function

**Best Practice:**
```rust
pub struct AccountValidation<'a, 'info> {
    account: &'a AccountInfo<'info>,
}

impl<'a, 'info> AccountValidation<'a, 'info> {
    pub fn new(account: &'a AccountInfo<'info>) -> Self {
        Self { account }
    }

    pub fn owner(self, expected_owner: &Pubkey) -> Result<Self, ProgramError> {
        if self.account.owner != expected_owner {
            return Err(ProgramError::IncorrectProgramId);
        }
        Ok(self)
    }

    pub fn signer(self) -> Result<Self, ProgramError> {
        if !self.account.is_signer {
            return Err(ProgramError::MissingRequiredSignature);
        }
        Ok(self)
    }

    pub fn writable(self) -> Result<Self, ProgramError> {
        if !self.account.is_writable {
            return Err(ProgramError::InvalidAccountData);
        }
        Ok(self)
    }

    pub fn key(self, expected_key: &Pubkey) -> Result<Self, ProgramError> {
        if self.account.key != expected_key {
            return Err(ProgramError::InvalidAccountData);
        }
        Ok(self)
    }

    pub fn initialized(self) -> Result<Self, ProgramError> {
        if self.account.data_is_empty() {
            return Err(ProgramError::UninitializedAccount);
        }
        Ok(self)
    }
}

// Usage:
pub fn process(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let authority = next_account_info(account_info_iter)?;
    let config = next_account_info(account_info_iter)?;

    AccountValidation::new(authority)
        .signer()?;

    AccountValidation::new(config)
        .owner(program_id)?
        .writable()?
        .initialized()?;

    // All validations passed
    Ok(())
}
```

---

## Account Discriminator Patterns

Without Anchor's automatic discriminators, you must manually implement account type safety.

### Why Discriminators Matter

**Vulnerable:**
```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct ConfigAccount {
    pub admin: Pubkey,
    pub value: u64,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct UserAccount {
    pub owner: Pubkey,
    pub balance: u64,
}

pub fn update_config(accounts: &[AccountInfo]) -> ProgramResult {
    let config = next_account_info(&mut accounts.iter())?;

    // No discriminator check - UserAccount has same layout!
    let mut data = ConfigAccount::try_from_slice(&config.data.borrow())?;
    data.value = 999;
    // Could be writing to a UserAccount!

    Ok(())
}
```

### Implementing Discriminators

**Secure:**
```rust
use borsh::{BorshDeserialize, BorshSerialize};

pub const CONFIG_DISCRIMINATOR: u64 = 0x1234567890ABCDEF;
pub const USER_DISCRIMINATOR: u64 = 0xFEDCBA0987654321;

#[derive(BorshSerialize, BorshDeserialize)]
pub struct ConfigAccount {
    pub discriminator: u64,
    pub admin: Pubkey,
    pub value: u64,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct UserAccount {
    pub discriminator: u64,
    pub owner: Pubkey,
    pub balance: u64,
}

impl ConfigAccount {
    pub const LEN: usize = 8 + 32 + 8;

    pub fn new(admin: Pubkey, value: u64) -> Self {
        Self {
            discriminator: CONFIG_DISCRIMINATOR,
            admin,
            value,
        }
    }

    pub fn from_account_info(account: &AccountInfo) -> Result<Self, ProgramError> {
        let data = account.data.borrow();
        if data.len() < 8 {
            return Err(ProgramError::InvalidAccountData);
        }

        let discriminator = u64::from_le_bytes(data[0..8].try_into().unwrap());
        if discriminator != CONFIG_DISCRIMINATOR {
            return Err(ProgramError::InvalidAccountData);
        }

        Self::try_from_slice(&data).map_err(|_| ProgramError::InvalidAccountData)
    }
}

pub fn update_config(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let config_account = next_account_info(&mut accounts.iter())?;

    // Discriminator validated during deserialization
    let mut config = ConfigAccount::from_account_info(config_account)?;
    config.value = 999;
    config.serialize(&mut *config_account.data.borrow_mut())?;

    Ok(())
}
```

### Alternative: String-Based Discriminators

```rust
pub const ACCOUNT_TYPE_LEN: usize = 8;

#[derive(BorshSerialize, BorshDeserialize)]
pub struct TaggedAccount {
    pub account_type: [u8; ACCOUNT_TYPE_LEN], // "CONFIG\0\0"
    pub data: AccountData,
}

impl TaggedAccount {
    pub fn new_config(data: AccountData) -> Self {
        let mut account_type = [0u8; ACCOUNT_TYPE_LEN];
        account_type[..6].copy_from_slice(b"CONFIG");
        Self { account_type, data }
    }

    pub fn assert_config(&self) -> ProgramResult {
        let mut expected = [0u8; ACCOUNT_TYPE_LEN];
        expected[..6].copy_from_slice(b"CONFIG");

        if self.account_type != expected {
            return Err(ProgramError::InvalidAccountData);
        }
        Ok(())
    }
}
```

---

## PDA Security in Native Rust

### find_program_address vs create_program_address

**Vulnerable:**
```rust
pub fn init_pda(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    bump: u8,
) -> ProgramResult {
    let pda_account = next_account_info(&mut accounts.iter())?;

    // Using user-provided bump without validation!
    let pda = Pubkey::create_program_address(
        &[b"config", &[bump]],
        program_id,
    )?;

    if pda_account.key != &pda {
        return Err(ProgramError::InvalidAccountData);
    }

    // Attacker could find non-canonical bump
    Ok(())
}
```

**Secure:**
```rust
pub fn init_pda(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let pda_account = next_account_info(&mut accounts.iter())?;

    // Always use find_program_address to get canonical bump
    let (pda, bump) = Pubkey::find_program_address(
        &[b"config"],
        program_id,
    );

    if pda_account.key != &pda {
        return Err(ProgramError::InvalidAccountData);
    }

    // Store the canonical bump for later use
    let mut data = ConfigPda::new(bump);
    data.serialize(&mut *pda_account.data.borrow_mut())?;

    Ok(())
}
```

### Storing and Using Canonical Bumps

**Best Practice:**
```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct VaultPda {
    pub discriminator: u64,
    pub bump: u8,
    pub authority: Pubkey,
    pub balance: u64,
}

impl VaultPda {
    pub fn seeds<'a>(&'a self, authority: &'a Pubkey) -> [&'a [u8]; 3] {
        [b"vault", authority.as_ref(), &[self.bump]]
    }

    pub fn verify_pda(
        &self,
        pda_account: &AccountInfo,
        authority: &Pubkey,
        program_id: &Pubkey,
    ) -> ProgramResult {
        let expected_pda = Pubkey::create_program_address(
            &self.seeds(authority),
            program_id,
        )?;

        if pda_account.key != &expected_pda {
            return Err(ProgramError::InvalidSeeds);
        }

        Ok(())
    }
}
```

### PDA Signing with invoke_signed

**Secure Pattern:**
```rust
use solana_program::program::invoke_signed;

pub fn transfer_from_pda(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let vault_pda = next_account_info(account_info_iter)?;
    let destination = next_account_info(account_info_iter)?;
    let authority = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Load and validate PDA data
    let vault = VaultPda::from_account_info(vault_pda)?;
    vault.verify_pda(vault_pda, authority.key, program_id)?;

    // Sign with PDA's seeds
    let seeds = vault.seeds(authority.key);
    let signer_seeds = &[&seeds[..]];

    let ix = solana_program::system_instruction::transfer(
        vault_pda.key,
        destination.key,
        amount,
    );

    invoke_signed(
        &ix,
        &[vault_pda.clone(), destination.clone(), system_program.clone()],
        signer_seeds,
    )?;

    Ok(())
}
```

### Preventing PDA Substitution

**Vulnerable:**
```rust
pub fn withdraw(accounts: &[AccountInfo]) -> ProgramResult {
    let vault = next_account_info(&mut accounts.iter())?;

    // No validation that this is the CORRECT vault PDA
    let vault_data = VaultPda::from_account_info(vault)?;

    // Attacker could substitute a different vault!
    Ok(())
}
```

**Secure:**
```rust
pub fn withdraw(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let vault = next_account_info(account_info_iter)?;
    let authority = next_account_info(account_info_iter)?;

    // Derive expected PDA
    let (expected_vault, _bump) = Pubkey::find_program_address(
        &[b"vault", authority.key.as_ref()],
        program_id,
    );

    // Validate this is the correct PDA
    if vault.key != &expected_vault {
        return Err(ProgramError::InvalidAccountData);
    }

    let vault_data = VaultPda::from_account_info(vault)?;
    // Safe to proceed

    Ok(())
}
```

---

## Manual CPI Security

### Building AccountMeta Arrays Securely

**Vulnerable:**
```rust
pub fn dangerous_cpi(accounts: &[AccountInfo]) -> ProgramResult {
    let target_program = next_account_info(&mut accounts.iter())?;
    let account1 = next_account_info(&mut accounts.iter())?;

    // Missing validation - could be any program!
    let ix = Instruction {
        program_id: *target_program.key,
        accounts: vec![
            AccountMeta::new(*account1.key, false), // Wrong signer flag!
        ],
        data: vec![],
    };

    invoke(&ix, &[target_program.clone(), account1.clone()])?;
    Ok(())
}
```

**Secure:**
```rust
use solana_program::program::invoke;

pub const EXPECTED_PROGRAM_ID: Pubkey = solana_program::pubkey!("YourProgramID111111111111111111111111111111");

pub fn secure_cpi(accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let target_program = next_account_info(account_info_iter)?;
    let account1 = next_account_info(account_info_iter)?;

    // Validate target program ID
    if target_program.key != &EXPECTED_PROGRAM_ID {
        return Err(ProgramError::IncorrectProgramId);
    }

    // Correctly propagate signer/writable flags
    let account_metas = vec![
        AccountMeta {
            pubkey: *account1.key,
            is_signer: account1.is_signer,
            is_writable: account1.is_writable,
        },
    ];

    let ix = Instruction {
        program_id: *target_program.key,
        accounts: account_metas,
        data: vec![],
    };

    invoke(&ix, &[target_program.clone(), account1.clone()])?;
    Ok(())
}
```

### Checking CPI Success

**Best Practice:**
```rust
pub fn cpi_with_validation(accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let token_program = next_account_info(account_info_iter)?;
    let source = next_account_info(account_info_iter)?;
    let destination = next_account_info(account_info_iter)?;
    let authority = next_account_info(account_info_iter)?;

    // Get balances before CPI
    let source_before = source.lamports();
    let dest_before = destination.lamports();

    let ix = spl_token::instruction::transfer(
        token_program.key,
        source.key,
        destination.key,
        authority.key,
        &[],
        1000,
    )?;

    invoke(&ix, &[source.clone(), destination.clone(), authority.clone()])?;

    // Verify state changed as expected (for native SOL transfers)
    // Note: For SPL tokens, you'd need to deserialize token accounts

    Ok(())
}
```

---

## Manual Serialization Security

### Borsh Serialization Pitfalls

**Vulnerable:**
```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct Config {
    pub value: u64,
    pub items: Vec<Item>, // Variable length!
}

pub fn deserialize_config(account: &AccountInfo) -> ProgramResult {
    // No size validation - could run out of compute!
    let config = Config::try_from_slice(&account.data.borrow())?;

    // Attacker could create huge Vec causing OOM
    for item in &config.items {
        // Process item
    }

    Ok(())
}
```

**Secure:**
```rust
pub const MAX_ITEMS: usize = 100;

#[derive(BorshSerialize, BorshDeserialize)]
pub struct Config {
    pub value: u64,
    pub item_count: u32,
    pub items: Vec<Item>,
}

impl Config {
    pub fn from_account_info(account: &AccountInfo) -> Result<Self, ProgramError> {
        let data = account.data.borrow();

        // Validate minimum size
        if data.len() < 8 + 4 {
            return Err(ProgramError::InvalidAccountData);
        }

        let config = Self::try_from_slice(&data)
            .map_err(|_| ProgramError::InvalidAccountData)?;

        // Validate item count matches actual length
        if config.item_count as usize != config.items.len() {
            return Err(ProgramError::InvalidAccountData);
        }

        // Enforce maximum items
        if config.items.len() > MAX_ITEMS {
            return Err(ProgramError::InvalidAccountData);
        }

        Ok(config)
    }
}
```

### Account Data Layout Validation

**Best Practice:**
```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct UserAccount {
    pub discriminator: u64,
    pub owner: Pubkey,
    pub balance: u64,
    pub created_at: i64,
}

impl UserAccount {
    pub const LEN: usize = 8 + 32 + 8 + 8;

    pub fn from_account_info(account: &AccountInfo) -> Result<Self, ProgramError> {
        let data = account.data.borrow();

        // Exact size check prevents truncation attacks
        if data.len() != Self::LEN {
            return Err(ProgramError::InvalidAccountData);
        }

        Self::try_from_slice(&data)
            .map_err(|_| ProgramError::InvalidAccountData)
    }

    pub fn to_account_info(&self, account: &AccountInfo) -> ProgramResult {
        let mut data = account.data.borrow_mut();

        if data.len() != Self::LEN {
            return Err(ProgramError::InvalidAccountData);
        }

        self.serialize(&mut *data)
            .map_err(|_| ProgramError::InvalidAccountData)
    }
}
```

---

## Rent and Space Management

### Rent Exemption Validation

**Secure Pattern:**
```rust
use solana_program::rent::Rent;
use solana_program::sysvar::Sysvar;

pub fn create_account(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    space: usize,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let new_account = next_account_info(account_info_iter)?;
    let payer = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Get rent sysvar
    let rent = Rent::get()?;

    // Calculate required lamports for rent exemption
    let required_lamports = rent.minimum_balance(space);

    // Validate account has enough lamports
    if new_account.lamports() < required_lamports {
        return Err(ProgramError::AccountNotRentExempt);
    }

    // Additional validation: account is rent exempt
    if !rent.is_exempt(new_account.lamports(), new_account.data_len()) {
        return Err(ProgramError::AccountNotRentExempt);
    }

    Ok(())
}
```

### Account Size Calculation

**Vulnerable:**
```rust
pub fn init_account(space: usize) -> ProgramResult {
    // No validation - attacker could request huge space
    let ix = solana_program::system_instruction::create_account(
        &payer.key,
        &new_account.key,
        lamports,
        space as u64, // Could overflow!
        program_id,
    );

    Ok(())
}
```

**Secure:**
```rust
pub const MIN_ACCOUNT_SIZE: usize = 128;
pub const MAX_ACCOUNT_SIZE: usize = 10_240; // 10KB

pub fn init_account(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    requested_space: usize,
) -> ProgramResult {
    // Validate space within reasonable bounds
    if requested_space < MIN_ACCOUNT_SIZE || requested_space > MAX_ACCOUNT_SIZE {
        return Err(ProgramError::InvalidAccountData);
    }

    // Ensure space alignment
    let space = requested_space
        .checked_next_multiple_of(8)
        .ok_or(ProgramError::InvalidAccountData)?;

    let rent = Rent::get()?;
    let lamports = rent.minimum_balance(space);

    // Safe to create account
    Ok(())
}
```

---

## Error Handling in Native Rust

### Custom Error Types

**Best Practice:**
```rust
use thiserror::Error;
use solana_program::program_error::ProgramError;

#[derive(Error, Debug, Copy, Clone)]
pub enum MyProgramError {
    #[error("Invalid authority")]
    InvalidAuthority,

    #[error("Insufficient balance")]
    InsufficientBalance,

    #[error("Account already initialized")]
    AlreadyInitialized,

    #[error("Arithmetic overflow")]
    ArithmeticOverflow,
}

impl From<MyProgramError> for ProgramError {
    fn from(e: MyProgramError) -> Self {
        ProgramError::Custom(e as u32)
    }
}

pub fn process(accounts: &[AccountInfo]) -> Result<(), MyProgramError> {
    let authority = next_account_info(&mut accounts.iter())
        .map_err(|_| MyProgramError::InvalidAuthority)?;

    if !authority.is_signer {
        return Err(MyProgramError::InvalidAuthority);
    }

    Ok(())
}
```

### Avoiding unwrap() and expect()

**Vulnerable:**
```rust
pub fn process(accounts: &[AccountInfo]) -> ProgramResult {
    let account = accounts.get(0).unwrap(); // Panics if no accounts!
    let data = account.data.borrow();
    let value = u64::from_le_bytes(data[0..8].try_into().unwrap()); // Panics if not 8 bytes!

    Ok(())
}
```

**Secure:**
```rust
pub fn process(accounts: &[AccountInfo]) -> ProgramResult {
    let account = accounts
        .get(0)
        .ok_or(ProgramError::NotEnoughAccountKeys)?;

    let data = account.data.borrow();

    if data.len() < 8 {
        return Err(ProgramError::InvalidAccountData);
    }

    let value = u64::from_le_bytes(
        data[0..8]
            .try_into()
            .map_err(|_| ProgramError::InvalidAccountData)?
    );

    Ok(())
}
```

---

## Token Program Integration

### Manual Token CPI Construction

**Secure Pattern:**
```rust
use spl_token::instruction as token_instruction;

pub fn transfer_tokens(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let source_token = next_account_info(account_info_iter)?;
    let dest_token = next_account_info(account_info_iter)?;
    let authority = next_account_info(account_info_iter)?;
    let token_program = next_account_info(account_info_iter)?;

    // Validate token program
    if token_program.key != &spl_token::id() {
        return Err(ProgramError::IncorrectProgramId);
    }

    // Validate authority is signer
    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Build transfer instruction
    let transfer_ix = token_instruction::transfer(
        token_program.key,
        source_token.key,
        dest_token.key,
        authority.key,
        &[],
        amount,
    )?;

    invoke(
        &transfer_ix,
        &[
            source_token.clone(),
            dest_token.clone(),
            authority.clone(),
            token_program.clone(),
        ],
    )?;

    Ok(())
}
```

### Token Account Validation

**Secure Pattern:**
```rust
use spl_token::state::Account as TokenAccount;

pub fn validate_token_account(
    token_account_info: &AccountInfo,
    expected_owner: &Pubkey,
    expected_mint: &Pubkey,
) -> Result<TokenAccount, ProgramError> {
    // Verify owned by token program
    if token_account_info.owner != &spl_token::id() {
        return Err(ProgramError::IncorrectProgramId);
    }

    // Deserialize token account
    let token_account = TokenAccount::unpack(&token_account_info.data.borrow())?;

    // Validate owner
    if &token_account.owner != expected_owner {
        return Err(ProgramError::InvalidAccountData);
    }

    // Validate mint
    if &token_account.mint != expected_mint {
        return Err(ProgramError::InvalidAccountData);
    }

    Ok(token_account)
}
```

---

## Low-Level Security Patterns

### Account Reloading After External Calls

**Vulnerable:**
```rust
pub fn vulnerable_pattern(accounts: &[AccountInfo]) -> ProgramResult {
    let account = next_account_info(&mut accounts.iter())?;

    let balance_before = account.lamports();

    // External CPI call
    invoke(&some_instruction, &[account.clone()])?;

    // Account data not reloaded - still using stale reference!
    let balance_after = account.lamports();

    Ok(())
}
```

**Secure:**
```rust
pub fn secure_pattern(accounts: &[AccountInfo]) -> ProgramResult {
    let account = next_account_info(&mut accounts.iter())?;

    let balance_before = account.lamports();

    // External CPI call
    invoke(&some_instruction, &[account.clone()])?;

    // AccountInfo automatically reflects changes - lamports(), data, etc.
    // are fresh after CPI
    let balance_after = account.lamports();

    // But if you cached deserialized data, you must reload:
    let fresh_data = MyData::from_account_info(account)?;

    Ok(())
}
```

### Clock and Timestamp Validation

**Secure Pattern:**
```rust
use solana_program::clock::Clock;
use solana_program::sysvar::Sysvar;

pub fn time_locked_operation(
    accounts: &[AccountInfo],
    unlock_timestamp: i64,
) -> ProgramResult {
    // Get clock sysvar
    let clock = Clock::get()?;

    // Validate unlock time has passed
    if clock.unix_timestamp < unlock_timestamp {
        return Err(ProgramError::InvalidArgument);
    }

    // Proceed with operation
    Ok(())
}
```

---

## Native Rust Best Practices

### Account Iteration Patterns

**Best Practice:**
```rust
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    let authority = next_account_info(account_info_iter)?;
    let config = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Validate all expected accounts consumed
    if account_info_iter.next().is_some() {
        return Err(ProgramError::InvalidAccountData);
    }

    // Validate accounts
    AccountValidation::new(authority).signer()?;
    AccountValidation::new(config)
        .owner(program_id)?
        .writable()?;

    Ok(())
}
```

### State Management Patterns

**Best Practice:**
```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct ProgramState {
    pub version: u8,
    pub is_initialized: bool,
    pub authority: Pubkey,
    // Add new fields at the end for upgradability
    pub feature_flags: u64,
}

impl ProgramState {
    pub const CURRENT_VERSION: u8 = 1;

    pub fn initialize(authority: Pubkey) -> Self {
        Self {
            version: Self::CURRENT_VERSION,
            is_initialized: true,
            authority,
            feature_flags: 0,
        }
    }

    pub fn validate(&self) -> ProgramResult {
        if !self.is_initialized {
            return Err(ProgramError::UninitializedAccount);
        }

        if self.version != Self::CURRENT_VERSION {
            return Err(ProgramError::InvalidAccountData);
        }

        Ok(())
    }
}
```

### Security.txt Integration

**Best Practice:**
```rust
#[cfg(not(feature = "no-entrypoint"))]
solana_security_txt::security_txt! {
    name: "My Solana Program",
    project_url: "https://github.com/myorg/myprogram",
    contacts: "email:security@myorg.com,discord:myorg",
    policy: "https://github.com/myorg/myprogram/blob/main/SECURITY.md",
    preferred_languages: "en",
    source_code: "https://github.com/myorg/myprogram",
    auditors: "Auditor1, Auditor2"
}
```

---

## Summary

Native Rust Solana programs require meticulous manual validation of all security properties:

1. **Always validate**: signer, owner, writable, key equality
2. **Use discriminators** to prevent account type confusion
3. **Store canonical bumps** and validate PDA derivation
4. **Validate CPI targets** and propagate account flags correctly
5. **Validate sizes** before deserialization
6. **Check rent exemption** for all accounts
7. **Use Result types** - never unwrap or expect
8. **Validate token accounts** completely before use
9. **Reload account data** after external calls if cached
10. **Version your state** and validate initialization

For each pattern, create reusable validation functions and leverage Rust's type system to enforce security invariants at compile time where possible.
