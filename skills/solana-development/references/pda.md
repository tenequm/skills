# Program Derived Addresses (PDAs)

This reference provides comprehensive coverage of Program Derived Addresses (PDAs) for native Rust Solana program development, including derivation mechanics, security implications, and best practices.

## Table of Contents

1. [What are PDAs](#what-are-pdas)
2. [PDA Derivation Mechanics](#pda-derivation-mechanics)
3. [Canonical Bump Seeds](#canonical-bump-seeds)
4. [Creating PDA Accounts](#creating-pda-accounts)
5. [PDA Signing](#pda-signing)
6. [Common PDA Patterns](#common-pda-patterns)
7. [Security Considerations](#security-considerations)
8. [Best Practices](#best-practices)

---

## What are PDAs

**Program Derived Addresses (PDAs) are deterministic account addresses derived from a program ID and optional seeds.**

### Key Characteristics

1. **Deterministic**: Same inputs always produce the same PDA
2. **No private key**: PDAs are intentionally off the Ed25519 curve
3. **Program-signable**: The deriving program can sign for PDAs
4. **Hashmap-like**: Enable key-value storage patterns on-chain

### Why PDAs Exist

PDAs solve critical problems in Solana program development:

**Problem 1: State Storage**
- How do you store program state without tracking account addresses?
- Solution: Derive addresses from user pubkeys + seeds

**Problem 2: Program Signing**
- How can a program sign transactions without a private key?
- Solution: Runtime enables programs to sign for their PDAs

**Problem 3: Account Discovery**
- How do clients find accounts created by programs?
- Solution: Derive PDAs client-side using known seeds

### PDA vs Regular Account

| Property | Regular Account | PDA |
|----------|----------------|-----|
| Address derivation | Random (from keypair) | Deterministic (from seeds) |
| Has private key | ✅ Yes | ❌ No (off-curve) |
| Can sign transactions | ✅ Yes (with private key) | ✅ Yes (via program) |
| Who can sign | Holder of private key | Only the deriving program |
| Use case | User wallets | Program state storage |

---

## PDA Derivation Mechanics

### How PDAs are Derived

PDAs are created using a hash function that combines:
1. Program ID
2. Optional seeds (strings, numbers, pubkeys)
3. Bump seed (0-255)

The process intentionally finds an address that falls **off** the Ed25519 elliptic curve.

```
┌──────────────────────────────────────────────┐
│ Input Seeds                                  │
├──────────────────────────────────────────────┤
│ - Program ID                                 │
│ - Optional Seed 1 (e.g., "user_data")       │
│ - Optional Seed 2 (e.g., user pubkey)       │
│ - Bump seed (starts at 255)                 │
└──────────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Hash Function        │
         │ (SHA256 + checks)    │
         └──────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Is address off-curve?│
         └──────────────────────┘
              │            │
              │ No         │ Yes
              ▼            ▼
    Decrement bump    Return (PDA, bump)
```

### Native Rust API

```rust
use solana_program::pubkey::Pubkey;

// Find PDA with canonical bump
let (pda, bump_seed) = Pubkey::find_program_address(
    &[
        b"user_data",           // Seed 1: static string
        user_pubkey.as_ref(),   // Seed 2: user's public key
    ],
    program_id,
);

// pda: The derived address (off-curve)
// bump_seed: The canonical bump (first valid bump found, starting from 255)
```

### Manual PDA Creation (Advanced)

You can manually create a PDA with a specific bump using `create_program_address`:

```rust
use solana_program::pubkey::Pubkey;

// This may fail if the bump doesn't produce a valid off-curve address
let pda = Pubkey::create_program_address(
    &[
        b"user_data",
        user_pubkey.as_ref(),
        &[bump_seed],  // Specific bump
    ],
    program_id,
)?;
```

**⚠️ Warning:** Only use `create_program_address` when you're certain the bump is valid. Prefer `find_program_address` for safety.

---

## Canonical Bump Seeds

### What is a Canonical Bump?

The **canonical bump** is the first bump seed (starting from 255, decrementing) that produces a valid off-curve address.

```rust
// Example: Finding all valid bumps
for bump in (0..=255).rev() {
    if let Ok(pda) = Pubkey::create_program_address(
        &[b"data", user.as_ref(), &[bump]],
        program_id,
    ) {
        println!("Bump {}: {}", bump, pda);
    }
}

// Typical output:
// Bump 255: Error (on-curve)
// Bump 254: AValidPDAAddress...  ← CANONICAL BUMP
// Bump 253: AnotherValidPDA...
// Bump 252: AThirdValidPDA...
// ...
```

### Why Use the Canonical Bump?

**Security Reason:** Multiple bumps can derive different valid PDAs for the same seeds. Accepting arbitrary bumps enables PDA substitution attacks.

**Attack Scenario:**
```rust
// ❌ Vulnerable - accepts any bump
pub fn update_user_balance(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    bump: u8,  // User provides bump
) -> ProgramResult {
    let user = &accounts[0];
    let user_pda = &accounts[1];

    // Creates PDA with user-provided bump
    let expected_pda = Pubkey::create_program_address(
        &[b"balance", user.key.as_ref(), &[bump]],
        program_id,
    )?;

    // Attacker can provide bump 253 instead of canonical 254
    // This derives a DIFFERENT PDA the attacker controls!
    // ...
}
```

**Secure Pattern:**
```rust
// ✅ Secure - uses canonical bump only
pub fn update_user_balance(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let user = &accounts[0];
    let user_pda = &accounts[1];

    // Derive with canonical bump
    let (expected_pda, _bump) = Pubkey::find_program_address(
        &[b"balance", user.key.as_ref()],
        program_id,
    );

    // Validate
    if expected_pda != *user_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // Safe to proceed
    // ...
}
```

### Storing the Canonical Bump

**Best Practice:** Store the canonical bump in the account data:

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct UserAccount {
    pub bump: u8,           // Store canonical bump
    pub user: Pubkey,
    pub balance: u64,
}

// On creation
let (pda, bump) = Pubkey::find_program_address(&[b"user", user.key.as_ref()], program_id);
let account_data = UserAccount {
    bump,  // Save for future operations
    user: *user.key,
    balance: 0,
};
```

**Why store it?**
- Saves compute units on subsequent operations
- `find_program_address` iterates from 255, costs ~3,000 CU
- Using stored bump with `create_program_address` costs ~300 CU (10x cheaper!)

---

## Creating PDA Accounts

### Creation Process

PDAs cannot create themselves. Accounts at PDA addresses must be created by:
1. Invoking the System Program via CPI
2. Using `invoke_signed` to sign with the PDA
3. The System Program creates the account and transfers ownership

### Native Rust Pattern

```rust
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::{invoke_signed},
    program_error::ProgramError,
    pubkey::Pubkey,
    rent::Rent,
    system_instruction,
    sysvar::Sysvar,
};

pub fn create_user_account(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    user_id: u64,
) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();

    let payer = next_account_info(account_info_iter)?;           // Pays for account
    let user_pda = next_account_info(account_info_iter)?;        // PDA to create
    let system_program = next_account_info(account_info_iter)?; // System Program

    // Signer check
    if !payer.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }

    // Derive PDA
    let user_id_bytes = user_id.to_le_bytes();
    let (pda, bump_seed) = Pubkey::find_program_address(
        &[b"user", payer.key.as_ref(), user_id_bytes.as_ref()],
        program_id,
    );

    // Validate provided PDA matches derivation
    if pda != *user_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // Calculate space and rent
    let account_size: usize = 1 + 32 + 8;  // bump + pubkey + u64
    let rent = Rent::get()?;
    let rent_lamports = rent.minimum_balance(account_size);

    // Create account via CPI
    let create_account_ix = system_instruction::create_account(
        payer.key,              // Payer
        user_pda.key,           // New account address (the PDA)
        rent_lamports,          // Lamports
        account_size as u64,    // Space
        program_id,             // Owner (our program)
    );

    // Sign with PDA using bump seed
    let signer_seeds: &[&[&[u8]]] = &[&[
        b"user",
        payer.key.as_ref(),
        user_id_bytes.as_ref(),
        &[bump_seed],  // Critical: Include bump in signer seeds
    ]];

    invoke_signed(
        &create_account_ix,
        &[payer.clone(), user_pda.clone(), system_program.clone()],
        signer_seeds,  // PDA signs here
    )?;

    // Initialize account data
    let mut account_data = UserAccount::try_from_slice(&user_pda.data.borrow())?;
    account_data.bump = bump_seed;
    account_data.owner = *payer.key;
    account_data.user_id = user_id;
    account_data.serialize(&mut &mut user_pda.data.borrow_mut()[..])?;

    Ok(())
}

#[derive(BorshSerialize, BorshDeserialize)]
struct UserAccount {
    bump: u8,
    owner: Pubkey,
    user_id: u64,
}
```

### Key Points

1. **Signer Seeds Format**: `&[&[&[u8]]]` (3 levels of slicing)
   - Outer: Array of seed sets (for multiple PDAs)
   - Middle: Single seed set (one PDA)
   - Inner: Individual seed slices

2. **Bump Must Be Included**: Always append `&[bump_seed]` to signer seeds

3. **System Program Required**: Must pass System Program account for CPI

4. **Ownership Transfer**: Account starts owned by System Program, transfers to your program

---

## PDA Signing

### How Programs Sign for PDAs

When a program makes a CPI with `invoke_signed`, the runtime:
1. Receives the signer seeds
2. Derives the PDA using seeds + calling program's ID
3. Verifies the derived PDA matches an account in the instruction
4. Grants signing authority to that PDA

### invoke_signed vs invoke

```rust
// invoke: No PDA signing
pub fn invoke(
    instruction: &Instruction,
    account_infos: &[AccountInfo],
) -> ProgramResult

// invoke_signed: With PDA signing
pub fn invoke_signed(
    instruction: &Instruction,
    account_infos: &[AccountInfo],
    signers_seeds: &[&[&[u8]]],  // PDA seeds
) -> ProgramResult
```

### Practical Example: PDA Transfers SOL

```rust
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
        pda_account.key,  // From: PDA (needs signing!)
        recipient.key,    // To: recipient
        amount,
    );

    // PDA signs the transfer
    let signer_seeds: &[&[&[u8]]] = &[&[
        b"vault",
        recipient.key.as_ref(),
        &[bump_seed],
    ]];

    invoke_signed(
        &transfer_ix,
        &[pda_account.clone(), recipient.clone(), system_program.clone()],
        signer_seeds,  // Runtime verifies and grants signing authority
    )?;

    Ok(())
}
```

### Multiple PDA Signers

You can sign with multiple PDAs in a single CPI:

```rust
let signer_seeds: &[&[&[u8]]] = &[
    &[b"pda1", &[bump1]],  // First PDA
    &[b"pda2", &[bump2]],  // Second PDA
];

invoke_signed(&instruction, &accounts, signer_seeds)?;
```

---

## Common PDA Patterns

### 1. User-Specific Accounts

**Pattern:** One PDA per user for storing user data.

```rust
// Seeds: ["user_data", user_pubkey]
let (user_pda, bump) = Pubkey::find_program_address(
    &[b"user_data", user.key.as_ref()],
    program_id,
);
```

**Use case:** User profiles, balances, inventory

**Advantages:**
- Easy client-side discovery
- One account per user
- User's pubkey acts as unique identifier

### 2. Global State

**Pattern:** Single PDA for program-wide state.

```rust
// Seeds: ["global_state"]
let (global_pda, bump) = Pubkey::find_program_address(
    &[b"global_state"],
    program_id,
);
```

**Use case:** Program configuration, global counters, admin settings

**Advantages:**
- Single source of truth
- Easy to find (no variable seeds)
- Reduced account proliferation

### 3. Association Pattern

**Pattern:** PDA associates two entities.

```rust
// Seeds: ["escrow", seller_pubkey, buyer_pubkey]
let (escrow_pda, bump) = Pubkey::find_program_address(
    &[b"escrow", seller.key.as_ref(), buyer.key.as_ref()],
    program_id,
);
```

**Use case:** Escrow accounts, peer-to-peer trades, relationships

**Advantages:**
- Unique per relationship
- Deterministic discovery
- Prevents duplicate associations

### 4. Index/Counter Pattern

**Pattern:** PDA with numeric index for multiple instances.

```rust
// Seeds: ["note", author_pubkey, note_id]
let note_id: u64 = 42;
let (note_pda, bump) = Pubkey::find_program_address(
    &[b"note", author.key.as_ref(), note_id.to_le_bytes().as_ref()],
    program_id,
);
```

**Use case:** Notes, posts, items, sequential data

**Advantages:**
- Multiple accounts per user
- Enumerable (iterate by incrementing ID)
- Scalable

**Implementation:**

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct UserState {
    pub note_count: u64,  // Track next available ID
}

pub fn create_note(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    content: String,
) -> ProgramResult {
    let user = &accounts[0];
    let user_state_pda = &accounts[1];
    let note_pda = &accounts[2];

    // Load user state
    let mut user_state = UserState::try_from_slice(&user_state_pda.data.borrow())?;

    // Derive PDA for new note
    let note_id = user_state.note_count;
    let (expected_note_pda, bump) = Pubkey::find_program_address(
        &[b"note", user.key.as_ref(), note_id.to_le_bytes().as_ref()],
        program_id,
    );

    if expected_note_pda != *note_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // Create note account...
    // Initialize note data...

    // Increment counter
    user_state.note_count += 1;
    user_state.serialize(&mut &mut user_state_pda.data.borrow_mut()[..])?;

    Ok(())
}
```

### 5. Vault/Treasury Pattern

**Pattern:** PDA holds funds for the program.

```rust
// Seeds: ["vault"]
let (vault_pda, bump) = Pubkey::find_program_address(
    &[b"vault"],
    program_id,
);
```

**Use case:** Staking pools, treasuries, escrow

**Advantages:**
- Program controls funds
- No external keypair needed
- Can't lose "private key"

---

## Security Considerations

### 1. Always Validate PDAs

**❌ Vulnerable:**
```rust
pub fn update_balance(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let user_pda = &accounts[0];

    // No PDA validation!
    let mut user_data = UserData::try_from_slice(&user_pda.data.borrow())?;
    user_data.balance += 100;
    user_data.serialize(&mut &mut user_pda.data.borrow_mut()[..])?;

    Ok(())
}
```

**✅ Secure:**
```rust
pub fn update_balance(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
) -> ProgramResult {
    let user = &accounts[0];
    let user_pda = &accounts[1];

    // Derive and validate
    let (expected_pda, _) = Pubkey::find_program_address(
        &[b"user", user.key.as_ref()],
        program_id,
    );

    if expected_pda != *user_pda.key {
        return Err(ProgramError::InvalidSeeds);
    }

    // Safe to proceed
    let mut user_data = UserData::try_from_slice(&user_pda.data.borrow())?;
    user_data.balance += 100;
    user_data.serialize(&mut &mut user_pda.data.borrow_mut()[..])?;

    Ok(())
}
```

### 2. Non-Canonical Bump Attack

**Vulnerability:** Accepting user-provided bumps allows PDA substitution.

**Impact:** Attacker can manipulate which account is used.

**Prevention:**
- Always use `find_program_address` (canonical bump)
- Never accept bump as instruction parameter
- Store bump in account data after creation

### 3. Seed Confusion

**Vulnerability:** Ambiguous seed ordering can create collisions.

```rust
// ❌ Problematic - seeds can collide
let seed1 = "hello";
let seed2 = "world";

// These derive the SAME PDA:
Pubkey::find_program_address(&[b"helloworld"], program_id);
Pubkey::find_program_address(&[b"hello", b"world"], program_id);
```

**Prevention:**
```rust
// ✅ Use fixed-size types and clear separators
Pubkey::find_program_address(
    &[
        b"prefix_",        // Fixed prefix
        user.key.as_ref(), // 32 bytes (fixed)
        &id.to_le_bytes(), // 8 bytes (fixed)
    ],
    program_id,
);
```

### 4. Ownership Verification

**Always verify PDA ownership:**

```rust
// ✅ Check ownership after PDA validation
if user_pda.owner != program_id {
    return Err(ProgramError::IllegalOwner);
}
```

---

## Best Practices

### 1. Seed Design

**Good Seed Patterns:**
- Use descriptive prefixes: `b"user_profile"`, `b"escrow"`, `b"vault"`
- Include entity identifiers: user pubkeys, IDs
- Use fixed-size types: `u64.to_le_bytes()`, `Pubkey::as_ref()`
- Maintain logical ordering: most general → most specific

**Example:**
```rust
&[
    b"note",               // What type of account
    author.key.as_ref(),   // Who owns it
    note_id.to_le_bytes(), // Which instance
]
```

### 2. Always Store the Bump

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct PdaAccount {
    pub bump: u8,  // Always first field for efficiency
    // ... other fields
}
```

**Benefits:**
- Saves ~2,700 CU per operation
- Enables efficient re-derivation
- Documents canonical bump

### 3. Validate Everything

**Security Checklist:**
- ✅ Derive PDA with canonical bump
- ✅ Compare derived PDA to provided account
- ✅ Verify PDA owner is your program
- ✅ Check initialization status
- ✅ Validate signer requirements

### 4. Document Your Seed Schema

```rust
/// Derives a user profile PDA.
///
/// Seeds: ["user_profile", user_pubkey]
/// Bump: Stored in account.bump
pub fn derive_user_profile_pda(
    user: &Pubkey,
    program_id: &Pubkey,
) -> (Pubkey, u8) {
    Pubkey::find_program_address(
        &[b"user_profile", user.as_ref()],
        program_id,
    )
}
```

### 5. Use Helper Functions

```rust
pub struct PdaDerivation;

impl PdaDerivation {
    pub fn user_profile(user: &Pubkey, program_id: &Pubkey) -> (Pubkey, u8) {
        Pubkey::find_program_address(&[b"user", user.as_ref()], program_id)
    }

    pub fn note(
        author: &Pubkey,
        note_id: u64,
        program_id: &Pubkey,
    ) -> (Pubkey, u8) {
        Pubkey::find_program_address(
            &[b"note", author.as_ref(), note_id.to_le_bytes().as_ref()],
            program_id,
        )
    }
}

// Usage
let (user_pda, bump) = PdaDerivation::user_profile(user.key, program_id);
```

---

## Summary

**Key Takeaways:**

1. **PDAs are deterministic addresses** derived from program ID + seeds
2. **No private key exists** for PDAs (they're off-curve by design)
3. **Only the deriving program can sign** for its PDAs
4. **Always use canonical bump** to prevent substitution attacks
5. **Validate PDAs before use** - never trust client-provided accounts
6. **Store the bump** in account data for compute efficiency
7. **Design clear seed schemas** to prevent collisions and confusion

**Security Mantra:**
```rust
// Always follow this pattern
let (expected_pda, bump) = Pubkey::find_program_address(&seeds, program_id);
if expected_pda != *provided_pda.key {
    return Err(ProgramError::InvalidSeeds);
}
if provided_pda.owner != program_id {
    return Err(ProgramError::IllegalOwner);
}
```

PDAs are the foundation of state management in Solana programs. Master them, validate them religiously, and your programs will be secure and efficient.
