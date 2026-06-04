# Cross-Program Invocation (CPI)

This reference provides comprehensive coverage of Cross-Program Invocation (CPI) for native Rust Solana program development, including invoke patterns, account privilege propagation, and security considerations.

## Table of Contents

1. [What is CPI](#what-is-cpi)
2. [CPI Fundamentals](#cpi-fundamentals)
3. [invoke vs invoke_signed](#invoke-vs-invoke_signed)
4. [Account Privilege Propagation](#account-privilege-propagation)
5. [Common CPI Patterns](#common-cpi-patterns)
6. [CPI Limits and Constraints](#cpi-limits-and-constraints)
7. [Security Considerations](#security-considerations)
8. [Best Practices](#best-practices)

---

## What is CPI

**Cross-Program Invocation (CPI) is when one Solana program directly calls instructions on another program.**

### Conceptual Model

If you think of a Solana instruction as an API endpoint, a CPI is like one API endpoint internally calling another.

```
User Transaction
     │
     ▼
┌────────────────────┐
│   Your Program     │
│                    │
│   ┌──────────────┐ │
│   │ Instruction  │ │
│   │   Handler    │ │
│   └──────┬───────┘ │
│          │ CPI     │
└──────────┼─────────┘
           │
           ▼
┌────────────────────┐
│ System Program     │
│  create_account    │
└────────────────────┘
```

### Why CPI is Essential

**Composability**: Programs can leverage functionality from other programs without reimplementing it.

**Common Use Cases:**
- Create accounts (System Program CPI)
- Transfer tokens (Token Program CPI)
- Interact with DeFi protocols
- Call custom program logic
- Complex multi-step operations

### CPI vs Direct Instruction

| Aspect | Direct Instruction | CPI |
|--------|-------------------|-----|
| Who initiates | User wallet | Another program |
| Signer source | User's private key | Program or PDA |
| Call depth | 1 (top-level) | 2-5 (nested) |
| Use case | Entry point | Program-to-program |

---

## CPI Fundamentals

### The Two CPI Functions

Solana provides two functions for making CPIs:

```rust
use solana_program::program::{invoke, invoke_signed};

// 1. invoke: For regular account signers
pub fn invoke(
    instruction: &Instruction,
    account_infos: &[AccountInfo],
) -> ProgramResult

// 2. invoke_signed: For PDA signers
pub fn invoke_signed(
    instruction: &Instruction,
    account_infos: &[AccountInfo],
    signers_seeds: &[&[&[u8]]],
) -> ProgramResult
```

### Required Imports

```rust
use solana_program::{
    account_info::AccountInfo,
    entrypoint::ProgramResult,
    instruction::{AccountMeta, Instruction},
    program::{invoke, invoke_signed},
    pubkey::Pubkey,
};
```

### Instruction Structure

Before making a CPI, you must construct an `Instruction`:

```rust
pub struct Instruction {
    /// Program ID of the program being invoked
    pub program_id: Pubkey,

    /// Accounts required by the instruction
    pub accounts: Vec<AccountMeta>,

    /// Serialized instruction data
    pub data: Vec<u8>,
}

pub struct AccountMeta {
    /// Account public key
    pub pubkey: Pubkey,

    /// Is this account a signer?
    pub is_signer: bool,

    /// Is this account writable?
    pub is_writable: bool,
}
```

---

## invoke vs invoke_signed

### invoke: Regular Signers

Use `invoke` when all required signers are regular accounts (not PDAs).

**Example: User transfers SOL**

```rust
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::invoke,
    program_error::ProgramError,
    pubkey::Pubkey,
    system_instruction,
};

pub fn user_transfer_sol(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    let sender = next_account_info(account_info_iter)?;
    let recipient = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Verify sender signed the transaction
    if !sender.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Create transfer instruction
    let transfer_ix = system_instruction::transfer(
        sender.key,
        recipient.key,
        amount,
    );

    // Execute CPI (sender already signed the transaction)
    invoke(
        &transfer_ix,
        &[
            sender.clone(),
            recipient.clone(),
            system_program.clone(),
        ],
    )?;

    Ok(())
}
```

**Key Points:**
- `sender.is_signer` must be true (verified at transaction level)
- No `signers_seeds` needed
- `invoke` internally calls `invoke_signed` with empty seeds

### invoke_signed: PDA Signers

Use `invoke_signed` when a PDA needs to sign the instruction.

**Example: PDA transfers SOL**

```rust
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::invoke_signed,
    program_error::ProgramError,
    pubkey::Pubkey,
    system_instruction,
};

pub fn pda_transfer_sol(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    let pda_account = next_account_info(account_info_iter)?;
    let recipient = next_account_info(account_info_iter)?;
    let system_program = next_account_info(account_info_iter)?;

    // Derive PDA and verify
    let (pda, bump_seed) = Pubkey::find_program_address(
        &[b"vault", recipient.key.as_ref()],
        program_id,
    );

    if pda != *pda_account.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // Create transfer instruction
    let transfer_ix = system_instruction::transfer(
        pda_account.key,  // From PDA (needs signing!)
        recipient.key,
        amount,
    );

    // PDA signing seeds (must match derivation)
    let signer_seeds: &[&[&[u8]]] = &[&[
        b"vault",
        recipient.key.as_ref(),
        &[bump_seed],  // Critical: bump must be included
    ]];

    // Execute CPI with PDA signature
    invoke_signed(
        &transfer_ix,
        &[
            pda_account.clone(),
            recipient.clone(),
            system_program.clone(),
        ],
        signer_seeds,  // Runtime verifies and grants signing authority
    )?;

    Ok(())
}
```

**How Runtime Handles PDA Signing:**

1. Runtime receives `signers_seeds`
2. Calls `create_program_address(signers_seeds, calling_program_id)`
3. Verifies derived PDA matches an account in the instruction
4. Grants signing authority for that account
5. Executes the CPI

**Critical:** Seeds must exactly match the PDA derivation, including the bump.

---

## Account Privilege Propagation

### Privilege Extension

When making a CPI, account privileges **extend** from the caller to the callee.

```
User Transaction
     │ (provides: signer=true, writable=true)
     ▼
┌─────────────────────┐
│  Program A          │
│  Receives accounts: │
│  - user (signer)    │──┐ Privileges
│  - vault (writable) │  │ propagate
└─────────────────────┘  │
                         ▼
                    ┌─────────────────────┐
                    │  Program B (via CPI)│
                    │  Can use:           │
                    │  - user (signer)    │
                    │  - vault (writable) │
                    └─────────────────────┘
```

### Propagation Rules

**Rule 1:** If an account is a signer in Program A, it remains a signer in Program B (via CPI)

**Rule 2:** If an account is writable in Program A, it remains writable in Program B (via CPI)

**Rule 3:** Programs can add PDA signers via `invoke_signed`

**Rule 4:** Programs cannot escalate privileges (can't make non-signer a signer without PDA derivation)

### Example: Privilege Propagation Chain

```rust
// User calls Program A
// Accounts: [user (signer, writable), vault (writable), data_account]

// Program A → CPI to Program B
invoke(
    &instruction_for_program_b,
    &[user.clone(), vault.clone()],  // Both retain privileges
)?;

// Program B → CPI to Program C
invoke(
    &instruction_for_program_c,
    &[user.clone()],  // user still a signer!
)?;
```

**Depth**: Up to 4 levels of CPI (5 total stack height including initial transaction)

---

## Common CPI Patterns

### 1. System Program: Create Account

**Most common CPI**: Creating new accounts.

```rust
use solana_program::{
    program::invoke_signed,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};

pub fn create_pda_account(
    program_id: &Pubkey,
    payer: &AccountInfo,
    pda_account: &AccountInfo,
    system_program: &AccountInfo,
    space: usize,
    seeds: &[&[u8]],
    bump: u8,
) -> ProgramResult {
    // Calculate rent
    let rent = Rent::get()?;
    let rent_lamports = rent.minimum_balance(space);

    // Create account instruction
    let create_account_ix = system_instruction::create_account(
        payer.key,
        pda_account.key,
        rent_lamports,
        space as u64,
        program_id,
    );

    // Prepare signer seeds
    let mut full_seeds = seeds.to_vec();
    full_seeds.push(&[bump]);
    let signer_seeds: &[&[&[u8]]] = &[&full_seeds];

    // Execute CPI
    invoke_signed(
        &create_account_ix,
        &[payer.clone(), pda_account.clone(), system_program.clone()],
        signer_seeds,
    )?;

    Ok(())
}
```

### 2. System Program: Transfer SOL

```rust
use solana_program::system_instruction;

// From regular account
let transfer_ix = system_instruction::transfer(from_key, to_key, lamports);
invoke(&transfer_ix, &[from_account, to_account, system_program])?;

// From PDA
let transfer_ix = system_instruction::transfer(pda_key, to_key, lamports);
let signer_seeds: &[&[&[u8]]] = &[&[seeds, &[bump]]];
invoke_signed(&transfer_ix, &[pda_account, to_account, system_program], signer_seeds)?;
```

### 3. Custom Program CPI

**Calling another custom program:**

```rust
use borsh::BorshSerialize;

#[derive(BorshSerialize)]
struct CustomInstructionData {
    amount: u64,
    memo: String,
}

pub fn call_custom_program(
    custom_program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let user = next_account_info(account_info_iter)?;
    let target_account = next_account_info(account_info_iter)?;
    let custom_program = next_account_info(account_info_iter)?;

    // Serialize instruction data
    let instruction_data = CustomInstructionData {
        amount,
        memo: "Hello from CPI".to_string(),
    };
    let data = instruction_data.try_to_vec()?;

    // Build instruction
    let instruction = Instruction {
        program_id: *custom_program_id,
        accounts: vec![
            AccountMeta::new(*user.key, true),           // signer, writable
            AccountMeta::new(*target_account.key, false), // writable
        ],
        data,
    };

    // Execute CPI
    invoke(
        &instruction,
        &[user.clone(), target_account.clone(), custom_program.clone()],
    )?;

    Ok(())
}
```

### 4. Multiple PDAs Signing

```rust
pub fn multi_pda_cpi(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let pda1_seeds = &[b"pda1", &[bump1]];
    let pda2_seeds = &[b"pda2", &[bump2]];

    // Multiple PDA signers
    let signer_seeds: &[&[&[u8]]] = &[
        pda1_seeds,  // First PDA
        pda2_seeds,  // Second PDA
    ];

    invoke_signed(&instruction, &accounts, signer_seeds)?;

    Ok(())
}
```

### 5. Chained CPIs

**Program A calls Program B, which calls Program C:**

```rust
// In Program A
pub fn program_a_handler(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    // Call Program B
    let instruction_for_b = build_program_b_instruction();
    invoke(&instruction_for_b, accounts)?;

    Ok(())
}

// In Program B
pub fn program_b_handler(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    // Call Program C
    let instruction_for_c = build_program_c_instruction();
    invoke(&instruction_for_c, accounts)?;

    Ok(())
}
```

**Depth tracking**: User→A→B→C = stack depth 4 (within limit)

---

## CPI Limits and Constraints

### Stack Depth Limit

**Maximum call depth:** 5 (including initial transaction)

```
Depth 1: User Transaction
Depth 2: Program A (first CPI)
Depth 3: Program B (second CPI)
Depth 4: Program C (third CPI)
Depth 5: Program D (fourth CPI)
Depth 6: ❌ ERROR - MAX_INSTRUCTION_STACK_DEPTH exceeded
```

**Constant:**
```rust
// From agave source
pub const MAX_INSTRUCTION_STACK_DEPTH: usize = 5;
```

**Error when exceeded:**
```
Error: CallDepth(5)
```

### Account Limits

- **Max accounts per instruction:** 256 (practical limit ~64 without ALTs)
- **Max writable accounts:** Limited by transaction size
- **Duplicate accounts:** Allowed but share state (mutations visible to all references)

### Compute Unit Costs

CPI operations consume compute units:

| Operation | Approximate CU Cost |
|-----------|---------------------|
| `invoke` base cost | ~1,000 CU |
| `invoke_signed` base cost | ~1,000 CU |
| Per account passed | ~50-100 CU |
| PDA derivation in runtime | ~1,500 CU |
| Actual callee logic | Variable |

**Tip:** Pre-derive PDAs and store bumps to save CU.

### Data Size Limits

- **Instruction data:** No hard limit, but affects transaction size (1232 bytes max for non-ALT transactions)
- **Account data modification:** Accounts can be resized via `realloc` (up to 10 MiB)

---

## Security Considerations

### 1. Validate PDA Derivation Before CPI

**❌ Vulnerable:**
```rust
pub fn vulnerable_cpi(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let pda_account = &accounts[0];

    // No validation!
    let signer_seeds: &[&[&[u8]]] = &[&[b"vault", &[bump]]];

    invoke_signed(&instruction, &[pda_account.clone()], signer_seeds)?;
    Ok(())
}
```

**✅ Secure:**
```rust
pub fn secure_cpi(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    bump: u8,
) -> ProgramResult {
    let pda_account = &accounts[0];

    // Validate PDA before CPI
    let (expected_pda, _) = Pubkey::find_program_address(&[b"vault"], program_id);
    if expected_pda != *pda_account.key {
        return Err(ProgramError::InvalidSeeds);
    }

    let signer_seeds: &[&[&[u8]]] = &[&[b"vault", &[bump]]];
    invoke_signed(&instruction, &[pda_account.clone()], signer_seeds)?;
    Ok(())
}
```

### 2. Verify Signer Requirements

**Always check `is_signer` before making CPIs that transfer value:**

```rust
if !user.is_signer {
    return Err(ProgramError::MissingRequiredSignature);
}

let transfer_ix = system_instruction::transfer(user.key, vault.key, amount);
invoke(&transfer_ix, &[user.clone(), vault.clone(), system_program.clone()])?;
```

### 3. Program ID Verification

**Verify the program being called is the expected program:**

```rust
const EXPECTED_PROGRAM: &str = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";

if token_program.key.to_string() != EXPECTED_PROGRAM {
    return Err(ProgramError::IncorrectProgramId);
}
```

### 4. Privilege Leakage

**Be careful about which accounts you pass in CPIs:**

```rust
// ❌ Dangerous - passes admin with signer privilege
invoke(
    &untrusted_program_instruction,
    &[admin.clone(), user_data.clone()],  // Admin is a signer!
)?;

// ✅ Safe - only pass necessary accounts
invoke(
    &untrusted_program_instruction,
    &[user_data.clone()],  // Admin not included
)?;
```

### 5. Reent rancy Considerations

**Solana programs are generally safe from reentrancy** because:
- Accounts are locked during instruction execution
- Runtime prevents concurrent modifications

**However, be cautious with:**
- State assumptions across CPI boundaries
- Read-modify-write patterns split across CPIs

### 6. Error Handling

**CPI errors propagate to the caller:**

```rust
// If CPI fails, entire transaction reverts
match invoke(&instruction, &accounts) {
    Ok(()) => msg!("CPI succeeded"),
    Err(e) => {
        msg!("CPI failed: {:?}", e);
        return Err(e);  // Propagate error
    }
}
```

**All state changes are atomic** - if CPI fails, all changes rollback.

---

## Best Practices

### 1. Derive PDAs Once

```rust
// ❌ Wasteful - derives multiple times
pub fn wasteful(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let (pda, bump) = Pubkey::find_program_address(&[b"data"], program_id);
    // ... use pda

    let (pda_again, bump_again) = Pubkey::find_program_address(&[b"data"], program_id);
    // ... use pda_again (same as pda!)
}

// ✅ Efficient - derive once, reuse
pub fn efficient(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let (pda, bump) = Pubkey::find_program_address(&[b"data"], program_id);
    // Reuse pda and bump
}
```

### 2. Store and Reuse Bumps

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct VaultData {
    pub bump: u8,  // Store on creation
    // ... other fields
}

// On CPI: use stored bump
let vault_data = VaultData::try_from_slice(&vault_pda.data.borrow())?;
let signer_seeds: &[&[&[u8]]] = &[&[b"vault", &[vault_data.bump]]];
```

**Benefit:** Saves ~2,700 CU per operation.

### 3. Helper Functions for Common CPIs

```rust
pub mod cpi_helpers {
    use super::*;

    pub fn transfer_sol(
        from: &AccountInfo,
        to: &AccountInfo,
        system_program: &AccountInfo,
        amount: u64,
    ) -> ProgramResult {
        let ix = system_instruction::transfer(from.key, to.key, amount);
        invoke(&ix, &[from.clone(), to.clone(), system_program.clone()])
    }

    pub fn transfer_sol_from_pda(
        from_pda: &AccountInfo,
        to: &AccountInfo,
        system_program: &AccountInfo,
        amount: u64,
        signer_seeds: &[&[&[u8]]],
    ) -> ProgramResult {
        let ix = system_instruction::transfer(from_pda.key, to.key, amount);
        invoke_signed(&ix, &[from_pda.clone(), to.clone(), system_program.clone()], signer_seeds)
    }
}
```

### 4. Validate All CPI Inputs

**Checklist before CPI:**
- ✅ Verify signer requirements (`is_signer`)
- ✅ Validate PDA derivation
- ✅ Check program IDs match expectations
- ✅ Verify account ownership
- ✅ Validate data integrity

### 5. Document CPI Dependencies

```rust
/// Transfers SOL from program vault to recipient.
///
/// # Accounts
/// 0. `[writable]` vault_pda - Program vault (PDA, signer)
/// 1. `[writable]` recipient - Receives SOL
/// 2. `[]` system_program - System Program (11111...)
///
/// # CPIs Made
/// - System Program: transfer (from vault to recipient)
pub fn withdraw_from_vault(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    amount: u64,
) -> ProgramResult {
    // ...
}
```

### 6. Error Context

```rust
invoke(&instruction, &accounts).map_err(|e| {
    msg!("CPI to System Program failed");
    e
})?;
```

### 7. Minimize CPI Depth

**Keep call chains shallow:**
- Reduces compute units
- Easier to debug
- Lower risk of hitting stack limit
- Better user experience (simpler transactions)

---

## Summary

**Key Takeaways:**

1. **CPI enables composability** - programs call other programs
2. **Use `invoke` for regular signers**, `invoke_signed` for PDAs
3. **Privileges propagate** - signers and writable flags extend through CPIs
4. **Maximum depth is 5** - including initial transaction
5. **Always validate PDAs** before using in `invoke_signed`
6. **Verify signer requirements** to prevent unauthorized operations
7. **Store bumps** in account data to save compute units
8. **CPIs are atomic** - failures rollback all changes

**Security Checklist:**
- ✅ Validate PDA derivation with canonical bump
- ✅ Verify `is_signer` for value transfers
- ✅ Check program IDs match expectations
- ✅ Only pass necessary accounts (avoid privilege leakage)
- ✅ Handle CPI errors appropriately

**Common Pattern:**
```rust
// 1. Validate inputs
if !user.is_signer {
    return Err(ProgramError::MissingRequiredSignature);
}

// 2. Derive and validate PDA if needed
let (pda, bump) = Pubkey::find_program_address(&seeds, program_id);
if pda != *pda_account.key {
    return Err(ProgramError::InvalidSeeds);
}

// 3. Build instruction
let ix = build_instruction();

// 4. Execute CPI
invoke_signed(&ix, &accounts, &[&[seeds, &[bump]]])?;
```

CPI is the foundation of program composability on Solana. Master it to build powerful, modular programs that leverage the entire ecosystem.
