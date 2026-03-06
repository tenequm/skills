# Error Handling in Solana Programs

This reference provides comprehensive coverage of error handling patterns for native Rust Solana program development, including custom error types, error propagation, and best practices.

## Table of Contents

1. [Error Handling Fundamentals](#error-handling-fundamentals)
2. [ProgramError](#programerror)
3. [Custom Error Types](#custom-error-types)
4. [Error Propagation](#error-propagation)
5. [Error Context and Logging](#error-context-and-logging)
6. [Client-Side Error Handling](#client-side-error-handling)
7. [Best Practices](#best-practices)

---

## Error Handling Fundamentals

### Why Error Handling Matters

**In Solana programs, errors serve multiple purposes:**

1. **Security:** Prevent invalid state transitions
2. **User Experience:** Provide meaningful feedback
3. **Debugging:** Identify issues quickly
4. **Transaction Validation:** Fail fast when invariants are violated

**Key Principle:** Errors should cause the entire transaction to fail and rollback, maintaining atomicity.

### The Result Type

All Solana program instructions return `ProgramResult`:

```rust
use solana_program::{
    entrypoint::ProgramResult,
    program_error::ProgramError,
};

pub type ProgramResult = Result<(), ProgramError>;

// Success
pub fn successful_operation() -> ProgramResult {
    Ok(())
}

// Failure
pub fn failed_operation() -> ProgramResult {
    Err(ProgramError::Custom(42))
}
```

**When an instruction returns `Err`:**
- Transaction fails immediately
- All state changes rollback
- Error code returned to client
- Transaction fee still charged (for processing cost)

---

## ProgramError

### The Built-in Error Type

Solana provides `ProgramError` enum with common error variants:

```rust
use solana_program::program_error::ProgramError;

pub enum ProgramError {
    // Common errors
    Custom(u32),                           // Custom error code
    InvalidArgument,                       // Invalid instruction argument
    InvalidInstructionData,                // Failed to deserialize instruction data
    InvalidAccountData,                    // Invalid account data
    AccountDataTooSmall,                   // Account data too small
    InsufficientFunds,                     // Not enough lamports
    IncorrectProgramId,                    // Wrong program ID
    MissingRequiredSignature,              // Required signer missing
    AccountAlreadyInitialized,             // Account already initialized
    UninitializedAccount,                  // Account not initialized
    NotEnoughAccountKeys,                  // Not enough accounts provided
    AccountBorrowFailed,                   // Failed to borrow account data
    MaxSeedLengthExceeded,                 // PDA seed too long
    InvalidSeeds,                          // Invalid PDA derivation
    BorshIoError(String),                  // Borsh serialization error
    AccountNotRentExempt,                  // Account not rent-exempt
    IllegalOwner,                          // Wrong account owner
    ArithmeticOverflow,                    // Arithmetic overflow
    // ... and more
}
```

### Common ProgramError Usage

```rust
use solana_program::program_error::ProgramError;

pub fn validate_inputs(
    amount: u64,
    max_amount: u64,
) -> ProgramResult {
    // InvalidArgument: Input doesn't meet requirements
    if amount == 0 {
        return Err(ProgramError::InvalidArgument);
    }

    // InsufficientFunds: Not enough balance
    if amount > max_amount {
        return Err(ProgramError::InsufficientFunds);
    }

    // ArithmeticOverflow: Math operation failed
    let _result = amount.checked_mul(2)
        .ok_or(ProgramError::ArithmeticOverflow)?;

    Ok(())
}
```

---

## Custom Error Types

### Why Custom Errors?

**Built-in `ProgramError` is generic.** Custom errors provide:

- **Specific error codes** for different failure modes
- **Better debugging** with descriptive messages
- **Client clarity** - clients know exactly what went wrong
- **Documentation** - errors serve as API documentation

### Defining Custom Errors

Use the `thiserror` crate to define custom error enums:

```rust
use solana_program::program_error::ProgramError;
use thiserror::Error;

#[derive(Error, Debug, Copy, Clone)]
pub enum NoteError {
    #[error("You do not own this note")]
    Forbidden,

    #[error("Note text is too long")]
    InvalidLength,

    #[error("Rating must be between 1 and 5")]
    InvalidRating,

    #[error("Note title cannot be empty")]
    EmptyTitle,

    #[error("Maximum notes limit reached")]
    MaxNotesExceeded,
}
```

**Attributes explained:**
- `#[derive(Error)]` - Implements `std::error::Error` trait
- `#[derive(Debug)]` - Allows `{:?}` formatting
- `#[derive(Copy, Clone)]` - Makes errors copyable (recommended)
- `#[error("...")]` - Error message string

### Converting to ProgramError

Implement `From<CustomError> for ProgramError`:

```rust
impl From<NoteError> for ProgramError {
    fn from(e: NoteError) -> Self {
        ProgramError::Custom(e as u32)
    }
}
```

**How it works:**
1. Custom error is converted to `u32` (using `as u32` cast)
2. Wrapped in `ProgramError::Custom(u32)`
3. Returned to client as error code

**Error code mapping:**
```rust
NoteError::Forbidden      → ProgramError::Custom(0)
NoteError::InvalidLength  → ProgramError::Custom(1)
NoteError::InvalidRating  → ProgramError::Custom(2)
NoteError::EmptyTitle     → ProgramError::Custom(3)
NoteError::MaxNotesExceeded → ProgramError::Custom(4)
```

### Using Custom Errors

```rust
pub fn create_note(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    title: String,
    content: String,
    rating: u8,
) -> ProgramResult {
    // Validation with custom errors
    if title.is_empty() {
        return Err(NoteError::EmptyTitle.into());
    }

    if content.len() > 1000 {
        return Err(NoteError::InvalidLength.into());
    }

    if rating < 1 || rating > 5 {
        return Err(NoteError::InvalidRating.into());
    }

    // Continue processing...
    Ok(())
}
```

**The `.into()` method** automatically converts `NoteError` to `ProgramError`.

### Advanced Custom Error Types

**With additional context:**

```rust
#[derive(Error, Debug)]
pub enum GameError {
    #[error("Insufficient mana: have {current}, need {required}")]
    InsufficientMana { current: u32, required: u32 },

    #[error("Invalid move: {0}")]
    InvalidMove(String),

    #[error("Player not found: {0}")]
    PlayerNotFound(String),
}
```

**Note:** Errors with fields cannot derive `Copy`, only `Clone`.

---

## Error Propagation

### The `?` Operator

The `?` operator is Rust's error propagation mechanism:

```rust
pub fn complex_operation(
    accounts: &[AccountInfo],
) -> ProgramResult {
    // If validation fails, error is returned immediately
    validate_accounts(accounts)?;

    // If deserialization fails, error is propagated
    let data = AccountData::try_from_slice(&accounts[0].data.borrow())?;

    // If checked math fails, ArithmeticOverflow is returned
    let result = data.value.checked_add(100)
        .ok_or(ProgramError::ArithmeticOverflow)?;

    Ok(())
}
```

**What `?` does:**
1. If `Result` is `Ok(value)`, unwraps to `value`
2. If `Result` is `Err(e)`, converts `e` and returns early
3. Conversion happens via `From` trait

### Error Conversion Chain

```rust
// Step 1: Borsh deserialization fails
let data = MyData::try_from_slice(bytes)?;
// Returns: Err(std::io::Error)

// Step 2: ? operator converts via From trait
// std::io::Error → ProgramError::BorshIoError

// Step 3: Custom error conversion
return Err(MyError::InvalidData.into());
// MyError → ProgramError::Custom(n)
```

### Manual Error Handling

```rust
// Without ?
pub fn manual_error_handling(
    account: &AccountInfo,
) -> ProgramResult {
    match validate_account(account) {
        Ok(()) => {
            // Continue processing
        }
        Err(e) => {
            msg!("Validation failed: {:?}", e);
            return Err(e);
        }
    }

    Ok(())
}

// With ? (equivalent)
pub fn automatic_error_handling(
    account: &AccountInfo,
) -> ProgramResult {
    validate_account(account)?;
    Ok(())
}
```

### Mapping Errors

Transform one error type to another:

```rust
pub fn map_errors(
    account: &AccountInfo,
) -> ProgramResult {
    // Map generic error to custom error
    let data = AccountData::try_from_slice(&account.data.borrow())
        .map_err(|_| NoteError::InvalidLength)?;

    // Map to different ProgramError variant
    let value = data.amount.checked_add(100)
        .ok_or(ProgramError::ArithmeticOverflow)?;

    Ok(())
}
```

### Combining Multiple Operations

```rust
pub fn chain_operations(
    accounts: &[AccountInfo],
) -> ProgramResult {
    // All operations must succeed or transaction fails
    let account1 = validate_and_load_account(&accounts[0])?;
    let account2 = validate_and_load_account(&accounts[1])?;

    let combined = account1.value
        .checked_add(account2.value)
        .ok_or(ProgramError::ArithmeticOverflow)?;

    update_account(&accounts[2], combined)?;

    Ok(())
}
```

---

## Error Context and Logging

### Adding Context with `msg!`

Use `msg!` macro to log context before returning errors:

```rust
use solana_program::msg;

pub fn transfer_tokens(
    from: &AccountInfo,
    to: &AccountInfo,
    amount: u64,
) -> ProgramResult {
    if amount == 0 {
        msg!("Transfer amount cannot be zero");
        return Err(ProgramError::InvalidArgument);
    }

    let from_balance = get_balance(from)?;

    if from_balance < amount {
        msg!("Insufficient balance: have {}, need {}", from_balance, amount);
        return Err(ProgramError::InsufficientFunds);
    }

    // Perform transfer...
    Ok(())
}
```

### Logging Best Practices

**✅ Good logging:**
```rust
msg!("Invalid rating: got {}, expected 1-5", rating);
msg!("PDA derivation failed: expected {}, got {}", expected, actual);
msg!("Account {} not owned by program {}", account.key, program_id);
```

**❌ Poor logging:**
```rust
msg!("Error");  // Not helpful
msg!("Failed");  // What failed?
// (no logging)  // Can't debug issues
```

### Conditional Logging

```rust
pub fn debug_operation(
    account: &AccountInfo,
    debug_mode: bool,
) -> ProgramResult {
    if debug_mode {
        msg!("Processing account: {}", account.key);
        msg!("Owner: {}", account.owner);
        msg!("Lamports: {}", account.lamports());
    }

    // Process...
    Ok(())
}
```

### Error with Recovery

```rust
pub fn try_with_fallback(
    accounts: &[AccountInfo],
) -> ProgramResult {
    // Try primary method
    match process_primary(accounts) {
        Ok(()) => {
            msg!("Primary method succeeded");
            Ok(())
        }
        Err(e) => {
            msg!("Primary method failed: {:?}, trying fallback", e);

            // Try fallback
            process_fallback(accounts).map_err(|fallback_err| {
                msg!("Fallback also failed: {:?}", fallback_err);
                fallback_err
            })
        }
    }
}
```

---

## Client-Side Error Handling

### Error Code Interpretation

**Client receives:**
```json
{
  "error": {
    "InstructionError": [
      0,
      {
        "Custom": 2
      }
    ]
  }
}
```

**Decoding:**
- Instruction index: `0` (first instruction)
- Error type: `Custom`
- Error code: `2`

### TypeScript Error Mapping

```typescript
// Define error codes matching Rust enum
enum NoteError {
    Forbidden = 0,
    InvalidLength = 1,
    InvalidRating = 2,
    EmptyTitle = 3,
    MaxNotesExceeded = 4,
}

// Error messages
const NOTE_ERROR_MESSAGES = {
    [NoteError.Forbidden]: "You do not own this note",
    [NoteError.InvalidLength]: "Note text is too long",
    [NoteError.InvalidRating]: "Rating must be between 1 and 5",
    [NoteError.EmptyTitle]: "Note title cannot be empty",
    [NoteError.MaxNotesExceeded]: "Maximum notes limit reached",
};

// Parse error
function parseNoteError(error: any): string {
    if (error?.InstructionError) {
        const [_, instructionError] = error.InstructionError;

        if (instructionError?.Custom !== undefined) {
            const errorCode = instructionError.Custom;
            return NOTE_ERROR_MESSAGES[errorCode] || `Unknown error: ${errorCode}`;
        }
    }

    return "Transaction failed";
}

// Usage
try {
    await program.methods.createNote(title, content, rating).rpc();
} catch (error) {
    const message = parseNoteError(error);
    console.error(message);
}
```

### Anchor Error Handling

**With Anchor framework:**

```typescript
import { AnchorError } from "@coral-xyz/anchor";

try {
    await program.methods.createNote(title, content, rating).rpc();
} catch (error) {
    if (error instanceof AnchorError) {
        console.error("Error code:", error.error.errorCode.code);
        console.error("Error message:", error.error.errorMessage);
        console.error("Error number:", error.error.errorCode.number);
    }
}
```

---

## Best Practices

### 1. Fail Fast

**Return errors immediately when validation fails:**

```rust
// ✅ Good - fails fast
pub fn validate_input(rating: u8) -> ProgramResult {
    if rating < 1 || rating > 5 {
        return Err(NoteError::InvalidRating.into());
    }

    // Continue only if valid
    Ok(())
}

// ❌ Bad - continues with invalid state
pub fn validate_input_bad(rating: u8) -> ProgramResult {
    if rating >= 1 && rating <= 5 {
        // Valid branch
    }
    // Continues regardless!
    Ok(())
}
```

### 2. Meaningful Error Messages

```rust
// ✅ Good - specific and actionable
#[error("Username must be 3-20 characters, got {0}")]
InvalidUsernameLength(usize),

#[error("Insufficient mana: need {required}, have {current}")]
InsufficientMana { required: u32, current: u32 },

// ❌ Bad - vague
#[error("Invalid input")]
InvalidInput,

#[error("Error")]
GenericError,
```

### 3. Organize Errors by Category

```rust
#[derive(Error, Debug, Copy, Clone)]
pub enum GameError {
    // Validation errors (0-99)
    #[error("Invalid player name")]
    InvalidPlayerName,

    #[error("Invalid move")]
    InvalidMove,

    // State errors (100-199)
    #[error("Game not started")]
    GameNotStarted,

    #[error("Game already finished")]
    GameFinished,

    // Resource errors (200-299)
    #[error("Insufficient gold")]
    InsufficientGold,

    #[error("Inventory full")]
    InventoryFull,
}
```

### 4. Consistent Error Handling Pattern

```rust
pub fn standard_operation_pattern(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    params: Params,
) -> ProgramResult {
    // 1. Parse accounts
    let account_info_iter = &mut accounts.iter();
    let user = next_account_info(account_info_iter)?;
    let data_account = next_account_info(account_info_iter)?;

    // 2. Validate signers
    if !user.is_signer {
        msg!("User must sign the transaction");
        return Err(ProgramError::MissingRequiredSignature);
    }

    // 3. Validate ownership
    if data_account.owner != program_id {
        msg!("Data account not owned by program");
        return Err(ProgramError::IllegalOwner);
    }

    // 4. Validate input parameters
    if params.amount == 0 {
        msg!("Amount cannot be zero");
        return Err(ProgramError::InvalidArgument);
    }

    // 5. Load and validate account data
    let mut data = AccountData::try_from_slice(&data_account.data.borrow())?;

    if !data.is_initialized {
        msg!("Account not initialized");
        return Err(ProgramError::UninitializedAccount);
    }

    // 6. Perform operation
    // ...

    Ok(())
}
```

### 5. Document Error Codes

```rust
/// Error codes for the Note program.
///
/// | Code | Error | Description |
/// |------|-------|-------------|
/// | 0 | Forbidden | Caller does not own the note |
/// | 1 | InvalidLength | Note text exceeds maximum length |
/// | 2 | InvalidRating | Rating not in range 1-5 |
/// | 3 | EmptyTitle | Note title is empty |
/// | 4 | MaxNotesExceeded | User has reached note limit |
#[derive(Error, Debug, Copy, Clone)]
#[repr(u32)]
pub enum NoteError {
    #[error("You do not own this note")]
    Forbidden = 0,

    #[error("Note text is too long")]
    InvalidLength = 1,

    #[error("Rating must be between 1 and 5")]
    InvalidRating = 2,

    #[error("Note title cannot be empty")]
    EmptyTitle = 3,

    #[error("Maximum notes limit reached")]
    MaxNotesExceeded = 4,
}
```

### 6. Error Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_invalid_rating() {
        let result = validate_rating(0);
        assert_eq!(
            result.unwrap_err(),
            NoteError::InvalidRating.into()
        );

        let result = validate_rating(6);
        assert_eq!(
            result.unwrap_err(),
            NoteError::InvalidRating.into()
        );
    }

    #[test]
    fn test_valid_rating() {
        for rating in 1..=5 {
            assert!(validate_rating(rating).is_ok());
        }
    }
}
```

### 7. Avoid Silent Failures

```rust
// ❌ Bad - errors ignored
pub fn bad_error_handling(accounts: &[AccountInfo]) -> ProgramResult {
    let _ = validate_accounts(accounts);  // Ignores error!

    if let Ok(data) = load_data(accounts) {
        process(data);  // What if load_data failed?
    }

    Ok(())  // Returns success even if operations failed!
}

// ✅ Good - errors propagated
pub fn good_error_handling(accounts: &[AccountInfo]) -> ProgramResult {
    validate_accounts(accounts)?;

    let data = load_data(accounts)?;
    process(data)?;

    Ok(())
}
```

---

## Summary

**Key Takeaways:**

1. **Always return `ProgramResult`** from instruction handlers
2. **Use custom errors** for specific failure modes
3. **Implement `From` trait** to convert custom errors to `ProgramError`
4. **Use `?` operator** for clean error propagation
5. **Add context with `msg!`** for better debugging
6. **Fail fast** - return errors immediately
7. **Document error codes** for client developers
8. **Test error cases** as thoroughly as success cases

**Error Handling Pattern:**

```rust
use solana_program::{
    entrypoint::ProgramResult,
    program_error::ProgramError,
    msg,
};
use thiserror::Error;

// 1. Define custom errors
#[derive(Error, Debug, Copy, Clone)]
pub enum MyError {
    #[error("Descriptive error message")]
    SpecificError,
}

// 2. Implement From conversion
impl From<MyError> for ProgramError {
    fn from(e: MyError) -> Self {
        ProgramError::Custom(e as u32)
    }
}

// 3. Use in program
pub fn my_instruction(accounts: &[AccountInfo]) -> ProgramResult {
    // Validate
    if invalid_condition {
        msg!("Detailed error context");
        return Err(MyError::SpecificError.into());
    }

    // Propagate errors with ?
    let data = load_data(accounts)?;

    Ok(())
}
```

**Remember:** Good error handling is not optional—it's essential for security, debugging, and user experience.
