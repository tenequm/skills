# Serialization and Data Handling

This reference provides comprehensive coverage of data serialization and deserialization patterns for native Rust Solana program development, focusing on Borsh and account data layout best practices.

## Table of Contents

1. [Why Borsh for Solana](#why-borsh-for-solana)
2. [Basic Borsh Usage](#basic-borsh-usage)
3. [Account Data Layout Design](#account-data-layout-design)
4. [Serialization Patterns](#serialization-patterns)
5. [Zero-Copy Deserialization](#zero-copy-deserialization)
6. [Data Versioning](#data-versioning)
7. [Performance Considerations](#performance-considerations)
8. [Common Pitfalls](#common-pitfalls)

---

## Why Borsh for Solana

**Borsh (Binary Object Representation Serializer for Hashing)** is the recommended serialization format for Solana programs.

### Advantages

1. **Deterministic:** Same data always produces same bytes
2. **Compact:** Efficient binary encoding
3. **Fast:** Lower compute unit cost than alternatives
4. **Strict Schema:** Type-safe serialization/deserialization
5. **No Metadata:** Unlike JSON, no field names in output

### vs Alternatives

| Format | CU Cost | Size | Type Safety | Deterministic |
|--------|---------|------|-------------|---------------|
| **Borsh** | ✅ Low | ✅ Compact | ✅ Yes | ✅ Yes |
| bincode | ❌ High | ✅ Compact | ✅ Yes | ⚠️ Config-dependent |
| JSON | ❌ Very High | ❌ Large | ❌ No | ❌ No |
| MessagePack | ⚠️ Medium | ✅ Compact | ⚠️ Partial | ⚠️ Mostly |

**Recommendation:** Use Borsh for all program account data.

---

## Basic Borsh Usage

### Dependencies

```toml
[dependencies]
borsh = { version = "1.5", features = ["derive"] }
```

### Deriving Borsh Traits

```rust
use borsh::{BorshDeserialize, BorshSerialize};

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub struct UserAccount {
    pub user: Pubkey,
    pub balance: u64,
    pub created_at: i64,
}
```

### Serialization

**To bytes:**

```rust
let account_data = UserAccount {
    user: Pubkey::new_unique(),
    balance: 1000,
    created_at: 1234567890,
};

// Serialize to Vec<u8>
let bytes = account_data.try_to_vec()?;

// Serialize to existing buffer
let mut buffer = vec![0u8; 100];
account_data.serialize(&mut buffer.as_mut_slice())?;
```

### Deserialization

**From bytes:**

```rust
// Deserialize from slice
let account_data = UserAccount::try_from_slice(&bytes)?;

// Deserialize with BorshDeserialize
let mut cursor = &bytes[..];
let account_data = UserAccount::deserialize(&mut cursor)?;
```

---

## Account Data Layout Design

### Basic Structure

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct AccountData {
    // 1. Discriminator / Type Field (1 byte)
    pub account_type: u8,

    // 2. Flags / State (1 byte)
    pub is_initialized: bool,

    // 3. Fixed-size fields (predictable layout)
    pub owner: Pubkey,           // 32 bytes
    pub created_at: i64,         // 8 bytes
    pub counter: u64,            // 8 bytes

    // 4. Variable-size fields (at end)
    pub name: String,            // 4 + length
    pub metadata: Vec<u8>,       // 4 + length
}
```

**Size calculation:**
```
1 (type) + 1 (flag) + 32 (pubkey) + 8 (i64) + 8 (u64) + 4 (string len) + N (string) + 4 (vec len) + M (vec)
= 58 + N + M bytes
```

### Size Calculation Helper

```rust
impl AccountData {
    pub const FIXED_SIZE: usize = 58;  // All fixed fields

    pub fn calculate_size(name_len: usize, metadata_len: usize) -> usize {
        Self::FIXED_SIZE + name_len + metadata_len
    }

    pub fn max_size(max_name: usize, max_metadata: usize) -> usize {
        Self::calculate_size(max_name, max_metadata)
    }
}

// Usage
let account_size = AccountData::max_size(32, 256);  // 346 bytes
```

### Fixed-Size Accounts

**Best for performance:**

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct FixedAccount {
    pub is_initialized: bool,
    pub owner: Pubkey,
    pub balance: u64,
    pub last_updated: i64,
    // Fixed-size array instead of Vec
    pub data: [u8; 256],
}

impl FixedAccount {
    pub const SIZE: usize = 1 + 32 + 8 + 8 + 256;  // 305 bytes
}
```

---

## Serialization Patterns

### Pattern 1: try_from_slice (Recommended)

**Most common pattern for account deserialization:**

```rust
use borsh::BorshDeserialize;

pub fn load_account_data(
    account_info: &AccountInfo,
) -> Result<UserAccount, ProgramError> {
    let data = UserAccount::try_from_slice(&account_info.data.borrow())?;
    Ok(data)
}
```

**Error handling:**
```rust
let data = UserAccount::try_from_slice(&account_info.data.borrow())
    .map_err(|e| {
        msg!("Failed to deserialize account: {}", e);
        ProgramError::InvalidAccountData
    })?;
```

### Pattern 2: Unchecked Deserialization

**Use when you've already validated the account:**

```rust
use borsh::try_from_slice_unchecked;

// After validation checks
let mut data = try_from_slice_unchecked::<UserAccount>(&account_info.data.borrow())
    .unwrap();  // Safe because we validated
```

**⚠️ Warning:** Only use after thorough validation. Skips some safety checks.

### Pattern 3: Partial Deserialization

**Read only what you need:**

```rust
#[derive(BorshDeserialize)]
pub struct AccountHeader {
    pub account_type: u8,
    pub is_initialized: bool,
    pub owner: Pubkey,
}

// Deserialize just the header
let header = AccountHeader::try_from_slice(&account_info.data.borrow()[..42])?;

if !header.is_initialized {
    return Err(ProgramError::UninitializedAccount);
}
```

### Pattern 4: In-Place Modification

**Efficient for large accounts:**

```rust
pub fn update_balance(
    account_info: &AccountInfo,
    new_balance: u64,
) -> ProgramResult {
    let mut data = account_info.data.borrow_mut();

    // Deserialize
    let mut account = UserAccount::try_from_slice(&data)?;

    // Modify
    account.balance = new_balance;
    account.last_updated = Clock::get()?.unix_timestamp;

    // Serialize back
    account.serialize(&mut &mut data[..])?;

    Ok(())
}
```

### Pattern 5: Bulk Operations

**Processing multiple accounts:**

```rust
pub fn process_accounts(
    accounts: &[AccountInfo],
) -> ProgramResult {
    let account_data: Vec<UserAccount> = accounts
        .iter()
        .map(|acc| UserAccount::try_from_slice(&acc.data.borrow()))
        .collect::<Result<Vec<_>, _>>()?;

    // Process all accounts
    for (i, data) in account_data.iter().enumerate() {
        msg!("Account {}: balance = {}", i, data.balance);
    }

    Ok(())
}
```

---

## Zero-Copy Deserialization

### When to Use Zero-Copy

**Benefits:**
- Avoids memory allocation
- Reduces compute units (50%+ savings for large structs)
- Direct access to account data

**Use when:**
- Account data is large (> 100 bytes)
- Frequent reads
- Performance-critical paths

### Bytemuck Pattern

```toml
[dependencies]
bytemuck = { version = "1.14", features = ["derive"] }
```

```rust
use bytemuck::{Pod, Zeroable};

#[repr(C)]
#[derive(Copy, Clone, Pod, Zeroable)]
pub struct ZeroCopyAccount {
    pub is_initialized: u8,      // bool as u8
    pub owner: [u8; 32],         // Pubkey as bytes
    pub balance: u64,
    pub counter: u64,
}

impl ZeroCopyAccount {
    pub const SIZE: usize = std::mem::size_of::<Self>();

    pub fn from_account_info(account_info: &AccountInfo) -> Result<&Self, ProgramError> {
        let data = account_info.data.borrow();
        bytemuck::try_from_bytes(&data)
            .map_err(|_| ProgramError::InvalidAccountData)
    }

    pub fn from_account_info_mut(
        account_info: &AccountInfo,
    ) -> Result<&mut Self, ProgramError> {
        let data = account_info.data.borrow_mut();
        bytemuck::try_from_bytes_mut(&mut data)
            .map_err(|_| ProgramError::InvalidAccountData)
    }
}

// Usage
let account = ZeroCopyAccount::from_account_info(account_info)?;
msg!("Balance: {}", account.balance);

// Mutable access
let account = ZeroCopyAccount::from_account_info_mut(account_info)?;
account.balance += 100;
```

**⚠️ Limitations:**
- Only works with types that are `Pod` (Plain Old Data)
- No `String`, `Vec`, or other heap-allocated types
- Must be `#[repr(C)]` for stable layout

---

## Data Versioning

### Pattern 1: Version Field

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct VersionedAccount {
    pub version: u8,
    pub data: AccountDataEnum,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub enum AccountDataEnum {
    V1(AccountDataV1),
    V2(AccountDataV2),
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct AccountDataV1 {
    pub balance: u64,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct AccountDataV2 {
    pub balance: u64,
    pub last_updated: i64,  // New field
}

// Deserialization with version handling
pub fn load_versioned_account(
    account_info: &AccountInfo,
) -> ProgramResult {
    let versioned = VersionedAccount::try_from_slice(&account_info.data.borrow())?;

    match versioned.data {
        AccountDataEnum::V1(data_v1) => {
            msg!("V1 account: balance = {}", data_v1.balance);
        }
        AccountDataEnum::V2(data_v2) => {
            msg!("V2 account: balance = {}, updated = {}",
                data_v2.balance, data_v2.last_updated);
        }
    }

    Ok(())
}
```

### Pattern 2: Optional Fields

```rust
#[derive(BorshSerialize, BorshDeserialize)]
pub struct Account {
    pub balance: u64,

    // V2: Added optional field
    pub metadata: Option<Metadata>,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct Metadata {
    pub name: String,
    pub url: String,
}

// Old accounts: metadata = None
// New accounts: metadata = Some(Metadata { ... })
```

### Pattern 3: Migration Function

```rust
pub fn migrate_account_v1_to_v2(
    account_info: &AccountInfo,
) -> ProgramResult {
    // Load V1
    let data_v1 = AccountDataV1::try_from_slice(&account_info.data.borrow())?;

    // Convert to V2
    let data_v2 = AccountDataV2 {
        balance: data_v1.balance,
        last_updated: Clock::get()?.unix_timestamp,
    };

    // Reallocate if needed
    let new_size = data_v2.try_to_vec()?.len();
    account_info.realloc(new_size, false)?;

    // Serialize V2
    data_v2.serialize(&mut &mut account_info.data.borrow_mut()[..])?;

    Ok(())
}
```

---

## Performance Considerations

### Compute Unit Costs

**Serialization costs (approximate):**

| Operation | CU Cost |
|-----------|---------|
| Serialize small struct (< 100 bytes) | ~500 CU |
| Serialize large struct (> 1KB) | ~2,000 CU |
| Deserialize small struct | ~800 CU |
| Deserialize large struct | ~3,000 CU |
| Zero-copy access | ~100 CU |

### Optimization Tips

**1. Minimize serialization frequency:**

```rust
// ❌ Wasteful - serializes twice
let mut data = load_data(account)?;
data.field1 = value1;
save_data(account, &data)?;

data.field2 = value2;
save_data(account, &data)?;  // Serialize again!

// ✅ Efficient - serialize once
let mut data = load_data(account)?;
data.field1 = value1;
data.field2 = value2;
save_data(account, &data)?;
```

**2. Use fixed-size fields:**

```rust
// ❌ Variable size - more expensive
pub struct Account {
    pub name: String,        // 4 + N bytes
}

// ✅ Fixed size - cheaper
pub struct Account {
    pub name: [u8; 32],      // Exactly 32 bytes
}
```

**3. Order fields by size:**

```rust
// ✅ Optimized layout (largest first)
#[derive(BorshSerialize, BorshDeserialize)]
#[repr(C)]
pub struct OptimizedAccount {
    pub pubkey1: Pubkey,     // 32 bytes
    pub pubkey2: Pubkey,     // 32 bytes
    pub amount: u64,         // 8 bytes
    pub timestamp: i64,      // 8 bytes
    pub flags: u8,           // 1 byte
}
```

---

## Common Pitfalls

### 1. Buffer Too Small

```rust
// ❌ Error: buffer too small
let mut buffer = vec![0u8; 10];
large_struct.serialize(&mut buffer.as_mut_slice())?;  // Fails!

// ✅ Correct: proper size
let size = large_struct.try_to_vec()?.len();
let mut buffer = vec![0u8; size];
large_struct.serialize(&mut buffer.as_mut_slice())?;
```

### 2. Forgetting to Borrow

```rust
// ❌ Error: data moved
let data = account_info.data;
UserAccount::try_from_slice(&data)?;  // Fails!

// ✅ Correct: borrow data
let data = account_info.data.borrow();
UserAccount::try_from_slice(&data)?;
```

### 3. Mismatched Schema

```rust
// Account created with V1
#[derive(BorshSerialize)]
pub struct AccountV1 {
    pub balance: u64,
}

// Later, trying to deserialize as V2
#[derive(BorshDeserialize)]
pub struct AccountV2 {
    pub balance: u64,
    pub timestamp: i64,  // New field!
}

// ❌ Fails: not enough bytes
let data = AccountV2::try_from_slice(&bytes)?;  // Error!
```

**Solution:** Use versioning or optional fields.

### 4. String/Vec Limits

```rust
// ❌ No validation
#[derive(BorshSerialize, BorshDeserialize)]
pub struct Account {
    pub name: String,  // Could be 10MB!
}

// ✅ Validate before deserializing
pub fn validate_name(name: &str) -> ProgramResult {
    if name.len() > 32 {
        return Err(ProgramError::InvalidArgument);
    }
    Ok(())
}
```

### 5. Incorrect Size Calculation

```rust
// ❌ Wrong: ignores vector length prefix
let size = my_vec.len();

// ✅ Correct: includes 4-byte length prefix
let size = 4 + my_vec.len();
```

---

## Summary

**Key Takeaways:**

1. **Use Borsh** for all Solana program serialization
2. **Design fixed-size layouts** when possible for predictability
3. **Validate before deserializing** to prevent errors
4. **Use zero-copy** for large, frequently-accessed data
5. **Plan for versioning** from the start
6. **Minimize serialization frequency** to save compute units

**Common Patterns:**
```rust
// Deserialize
let data = AccountData::try_from_slice(&account_info.data.borrow())?;

// Modify
let mut data = data;
data.field = new_value;

// Serialize
data.serialize(&mut &mut account_info.data.borrow_mut()[..])?;
```

**Size Calculation:**
```rust
// Fixed fields
const FIXED_SIZE: usize = 1 + 32 + 8;

// Variable fields
let total_size = FIXED_SIZE + 4 + string.len() + 4 + vec.len();
```

Proper serialization patterns are fundamental to efficient and correct Solana programs. Master Borsh for production-ready data handling.
