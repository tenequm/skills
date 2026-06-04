# Compute Unit Optimization Guide

This guide provides comprehensive techniques for optimizing compute unit (CU) usage in Solana native Rust programs, compiled from official Solana documentation, community repositories, and expert resources.

## Understanding Compute Units

### Compute Limits

Solana enforces strict compute budgets to ensure network performance:

- **Max CU per block**: 60 million CU
- **Max CU per account per block**: 12 million CU
- **Max CU per transaction**: 1.4 million CU
- **Default soft cap per transaction**: 200,000 CU

Programs can request higher compute budgets using the Compute Budget program, up to the 1.4M hard limit.

### Transaction Fees

Transaction fees consist of two components:

1. **Base fee**: 5,000 lamports per signature (fixed, independent of CU usage)
2. **Priority fee**: Optional additional fee to prioritize transaction inclusion

Priority fees are calculated as:
```
priority_fee = microLamports_per_CU × requested_compute_units
```

### Why Optimize CU Usage?

Even though current fees don't scale with CU usage within the budget, optimization matters:

1. **Block inclusion probability**: Smaller transactions are more likely to fit in congested blocks
2. **Composability**: When your program is called via CPI, it shares the caller's CU budget
3. **Efficient resource usage**: Better utilization of limited block space
4. **Future-proofing**: Fee structures may change to account for actual CU consumption
5. **User experience**: Faster transaction execution and lower rejection rates

## Common Optimization Techniques

### 1. Logging Optimization (Highest Impact)

Logging is one of the most expensive operations in Solana programs.

**Anti-patterns:**

```rust
// EXPENSIVE: 11,962 CU
// Base58 encoding + string concatenation
msg!("A string {0}", ctx.accounts.counter.to_account_info().key());

// EXPENSIVE: 357 CU
// String concatenation
msg!("A string {0}", "5w6z5PWvtkCd4PaAV7avxE6Fy5brhZsFdbRLMt8UefRQ");
```

**Best practices:**

```rust
// EFFICIENT: 262 CU
// Use .key().log() directly
ctx.accounts.counter.to_account_info().key().log();

// BETTER: 206 CU
// Store in variable first
let pubkey = ctx.accounts.counter.to_account_info().key();
pubkey.log();

// CHEAPEST: 204 CU
// Simple string logging
msg!("Compute units");
```

**Recommendation**: Avoid logging in production unless absolutely necessary for debugging. Remove or conditionally compile logging for mainnet deployments.

### 2. Data Type Optimization

Smaller data types consume fewer compute units.

**Comparison:**

```rust
// 618 CU - u64
let mut a: Vec<u64> = Vec::new();
for _ in 0..6 {
    a.push(1);
}

// 600 CU - i32 (default integer type)
let mut a = Vec::new();
for _ in 0..6 {
    a.push(1);
}

// 459 CU - u8 (best for small values)
let mut a: Vec<u8> = Vec::new();
for _ in 0..6 {
    a.push(1);
}
```

**Initialization vs pushing:**

```rust
// 357 CU - Pushing elements one by one
let mut a: Vec<u64> = Vec::new();
for _ in 0..6 {
    a.push(1);
}

// 125 CU - Direct initialization (65% savings!)
let _a: Vec<u64> = vec![1, 1, 1, 1, 1, 1];
```

**Best practice**: Use the smallest data type that fits your requirements (u8 > u16 > u32 > u64), and prefer `vec![]` initialization over repeated `push()` calls.

### 3. Serialization: Zero-Copy vs Borsh

Zero-copy deserialization can provide massive CU savings for account operations.

**Standard Borsh serialization:**

```rust
// 6,302 CU - Standard account initialization
pub fn initialize(_ctx: Context<InitializeCounter>) -> Result<()> {
    Ok(())
}

// 2,600 CU total for increment (including serialization overhead)
pub fn increment(ctx: Context<Increment>) -> Result<()> {
    let counter = &mut ctx.accounts.counter;
    counter.count = counter.count.checked_add(1).unwrap(); // 108 CU for operation
    Ok(())
}
```

**Zero-copy optimization:**

```rust
// 5,020 CU - Zero-copy initialization (20% savings)
pub fn initialize_zero_copy(_ctx: Context<InitializeCounterZeroCopy>) -> Result<()> {
    Ok(())
}

// 1,254 CU total for increment (52% savings!)
pub fn increment_zero_copy(ctx: Context<IncrementZeroCopy>) -> Result<()> {
    let counter = &mut ctx.accounts.counter_zero_copy.load_mut()?;
    counter.count = counter.count.checked_add(1).unwrap(); // 151 CU for operation
    Ok(())
}
```

**Zero-copy account definition:**

```rust
#[account(zero_copy)]
#[repr(C)]
#[derive(InitSpace)]
pub struct CounterZeroCopy {
    count: u64,
    authority: Pubkey,
    big_struct: BigStruct,  // Can include large structs without stack overflow
}
```

**Benefits of zero-copy:**
- 50%+ CU savings on serialization/deserialization
- Avoids stack frame violations with large account structures
- Direct memory access without intermediate copying
- Particularly valuable for frequently updated accounts

**Trade-off**: Slightly more complex API (`load()`, `load_mut()`) and requires `#[repr(C)]` for memory layout guarantees.

### 4. Program Derived Addresses (PDAs)

PDA operations vary significantly in cost depending on the method used.

**Finding PDAs:**

```rust
// EXPENSIVE: 12,136 CU
// Iterates through nonces to find valid bump seed
let (pda, bump) = Pubkey::find_program_address(&[b"counter"], ctx.program_id);

// EFFICIENT: 1,651 CU (87% savings!)
// Uses known bump seed directly
let pda = Pubkey::create_program_address(&[b"counter", &[248_u8]], &program_id).unwrap();
```

**Optimization strategy:**

1. Use `find_program_address()` **once** during account initialization
2. Save the bump seed in the account data
3. Use `create_program_address()` with the saved bump for all subsequent operations

**Anchor implementation:**

```rust
// Account structure - save the bump
#[account]
pub struct CounterData {
    pub count: u64,
    pub bump: u8,  // Store the bump seed here
}

// EXPENSIVE: 12,136 CU - Without saved bump
#[account(
    seeds = [b"counter"],
    bump  // Anchor finds it every time
)]
pub counter_checked: Account<'info, CounterData>,

// EFFICIENT: 1,600 CU - With saved bump (87% savings!)
#[account(
    seeds = [b"counter"],
    bump = counter_checked.bump  // Use the saved bump
)]
pub counter_checked: Account<'info, CounterData>,
```

### 5. Cross-Program Invocations (CPIs)

CPIs add significant overhead compared to direct operations.

**CPI to System Program:**

```rust
// 2,215 CU - CPI for SOL transfer
let cpi_context = CpiContext::new(
    ctx.accounts.system_program.to_account_info(),
    system_program::Transfer {
        from: ctx.accounts.payer.to_account_info().clone(),
        to: ctx.accounts.counter.to_account_info().clone(),
    },
);
system_program::transfer(cpi_context, 1_000_000)?;
```

**Direct lamport manipulation:**

```rust
// 251 CU - Direct operation (90% savings!)
let counter_account_info = ctx.accounts.counter.to_account_info();
let mut counter_lamports = counter_account_info.try_borrow_mut_lamports()?;
**counter_lamports += 1_000_000;

let payer_account_info = ctx.accounts.payer.to_account_info();
let mut payer_lamports = payer_account_info.try_borrow_mut_lamports()?;
**payer_lamports -= 1_000_000;
```

**Important caveats:**

1. **Error handling overhead**: Error paths add ~1,199 CU if triggered
2. **Safety**: Direct manipulation bypasses safety checks in the System Program
3. **Ownership**: Only safe when you control both accounts
4. **Rent exemption**: You're responsible for maintaining rent exemption

**Best practice**: Use CPIs for safety and correctness by default. Only optimize to direct manipulation when:
- You have tight CU constraints
- You fully understand the safety implications
- Both accounts are controlled by your program

### 6. Pass by Reference vs Clone

Solana's bump allocator doesn't free memory, making unnecessary cloning particularly problematic.

**Comparison:**

```rust
let balances = vec![10_u64; 100];

// EFFICIENT: 47,683 CU - Pass by reference
fn sum_by_reference(data: &Vec<u64>) -> u64 {
    data.iter().sum()
}

for _ in 0..39 {
    sum_reference += sum_by_reference(&balances);
}

// INEFFICIENT: 49,322 CU - Clone data (3.5% more expensive)
// WARNING: Runs out of memory at 40+ iterations!
fn sum_by_value(data: Vec<u64>) -> u64 {
    data.iter().sum()
}

for _ in 0..39 {
    sum_clone += sum_by_value(balances.clone());
}
```

**Memory concern**: Solana programs have a 32KB heap using a bump allocator that **never frees memory** during transaction execution. Excessive cloning leads to out-of-memory errors.

**Best practice**: Always pass by reference (`&T`) unless you explicitly need ownership transfer. Use `Copy` types for small data.

### 7. Checked Math vs Unchecked Operations

Checked arithmetic adds safety at the cost of compute units.

**Comparison:**

```rust
let mut count: u64 = 1;

// 97,314 CU - Checked multiplication with overflow protection
for _ in 0..12000 {
    count = count.checked_mul(2).expect("overflow");
}

// 85,113 CU - Bit shift operation (12% savings)
// Equivalent to multiply by 2, but unchecked
for _ in 0..12000 {
    count = count << 1;
}
```

**Trade-off**: Unchecked operations are faster but risk overflow bugs that can lead to serious security vulnerabilities.

**Best practice**:
- Use checked math by default for safety
- Profile your program to identify hot paths
- Only switch to unchecked math when:
  - You've proven overflow is impossible
  - CU savings are critical
  - You've added overflow tests

**Compiler configuration** (in Cargo.toml):

```toml
[profile.release]
overflow-checks = true  # Keep overflow checks even in release mode
```

## Framework Comparison

Different implementation approaches offer varying trade-offs between developer experience, safety, and performance.

| Implementation | Binary Size | Deploy Cost | Init CU | Increment CU |
|---------------|-------------|-------------|---------|--------------|
| **Anchor** | 265,677 bytes | 1.85 SOL | 6,302 | 946 |
| **Anchor Zero-Copy** | Same | 1.85 SOL | 5,020 | ~1,254 |
| **Native Rust** | 48,573 bytes | 0.34 SOL | - | 843 |
| **Unsafe Rust** | 973 bytes | 0.008 SOL | - | 5 |
| **Assembly (SBPF)** | 1,389 bytes | 0.01 SOL | - | 4 |
| **C** | 1,333 bytes | 0.01 SOL | - | 5 |

**Key insights:**

- **Anchor**: Best developer experience, automatic account validation, but highest CU and deployment costs
- **Anchor Zero-Copy**: Significant CU improvement over standard Anchor with minimal code changes
- **Native Rust**: 11% CU savings over Anchor, 82% smaller deployment size, moderate complexity
- **Unsafe Rust**: 99% CU savings, minimal size, but requires extreme care and deep expertise
- **Assembly/C**: Maximum optimization possible, but very difficult to develop and maintain

**Recommendation**: Start with Anchor or native Rust. Optimize hot paths with zero-copy. Only consider unsafe Rust or lower-level languages for critical performance bottlenecks after profiling.

## Advanced Optimization Techniques

### 1. Compiler Flags

Configure optimization in `Cargo.toml`:

```toml
[profile.release]
opt-level = 3           # Maximum optimization
lto = "fat"             # Full link-time optimization
codegen-units = 1       # Single codegen unit for better optimization
overflow-checks = true  # Keep safety checks despite performance cost
```

**Trade-offs**:
- `overflow-checks = false`: Saves CU but removes critical safety checks
- Higher `opt-level`: Better performance but slower compilation
- `lto = "fat"`: Maximum optimization but much slower builds

### 2. Function Inlining

Control function inlining to balance CU usage and stack space:

```rust
// Force inlining - saves CU by eliminating function call overhead
#[inline(always)]
fn add(a: u64, b: u64) -> u64 {
    a + b
}

// Prevent inlining - saves stack space at the cost of CU
#[inline(never)]
pub fn complex_operation() {
    // Large function body
}
```

**Trade-off**: Inlining saves CU but increases stack usage. Solana has a 4KB stack limit, so excessive inlining can cause stack overflow.

### 3. Alternative Entry Points

The standard Solana entry point adds overhead. Alternatives:

**Standard entry point:**
```rust
use solana_program::entrypoint;
entrypoint!(process_instruction);
```

**Minimal entry points:**
- [solana-nostd-entrypoint](https://github.com/cavemanloverboy/solana-nostd-entrypoint): Ultra-minimal entry using unsafe Rust
- [eisodos](https://github.com/anza-xyz/eisodos): Alternative minimal entry point

**Warning**: These require deep understanding of Solana internals and unsafe Rust. Only use for extreme optimization needs.

### 4. Custom Heap Allocators

Solana's default bump allocator never frees memory during transaction execution.

**Problem:**
```rust
// This will eventually run out of heap space (32KB limit)
for _ in 0..1000 {
    let v = vec![0u8; 1024];  // Each iteration uses more heap
    // Memory is never freed!
}
```

**Solution - Custom allocators:**

- **smalloc**: Used by Metaplex programs, provides better memory management
- Prevents out-of-memory errors in memory-intensive operations

**Implementation** (advanced):
```rust
#[global_allocator]
static ALLOCATOR: custom_allocator::CustomAllocator = custom_allocator::CustomAllocator;
```

### 5. Boxing and Heap Allocation

Heap operations cost more CU than stack operations.

```rust
// Stack allocation - faster
let data = [0u8; 100];

// Heap allocation - slower, uses more CU
let data = Box::new([0u8; 100]);
```

**Best practice**: Avoid `Box`, `Vec`, and other heap allocations when stack allocation is possible and doesn't risk overflow.

## Measuring Compute Units

### Using sol_log_compute_units()

Built-in logging function to track CU consumption:

```rust
use solana_program::log::sol_log_compute_units;

pub fn my_instruction(ctx: Context<MyContext>) -> Result<()> {
    sol_log_compute_units(); // Log remaining CU

    // ... do some work ...

    sol_log_compute_units(); // Log remaining CU again
    Ok(())
}
```

**Output in transaction logs:**
```
Program consumption: 200000 units remaining
Program consumption: 195432 units remaining
```

**CU used = 200000 - 195432 = 4,568 CU**

### compute_fn! Macro

Convenient macro for measuring specific code blocks (costs 409 CU overhead):

```rust
#[macro_export]
macro_rules! compute_fn {
    ($msg:expr=> $($tt:tt)*) => {
        ::solana_program::msg!(concat!($msg, " {"));
        ::solana_program::log::sol_log_compute_units();
        let res = { $($tt)* };
        ::solana_program::log::sol_log_compute_units();
        ::solana_program::msg!(concat!(" } // ", $msg));
        res
    };
}
```

**Usage:**

```rust
let result = compute_fn! { "My expensive operation" =>
    expensive_computation()
};
```

**Output:**
```
Program log: My expensive operation {
Program consumption: 195432 units remaining
Program consumption: 180123 units remaining
Program log: } // My expensive operation
```

**Actual CU = (195432 - 180123) - 409 (macro overhead) = 14,900 CU**

### Using Mollusk Bencher

For native Rust programs, use Mollusk's built-in benchmarking (see main SKILL.md for details).

## Anti-Patterns to Avoid

### 1. Excessive Logging

```rust
// BAD: Logging in production
msg!("Processing user {}", user_pubkey);
msg!("Amount: {}", amount);
msg!("Timestamp: {}", Clock::get()?.unix_timestamp);
```

**Solution**: Remove logging or use conditional compilation:

```rust
#[cfg(feature = "debug")]
msg!("Processing user {}", user_pubkey);
```

### 2. Large Data Types for Small Values

```rust
// BAD: Using u64 when u8 suffices
pub struct Config {
    pub fee_percentage: u64,  // Only 0-100
    pub max_items: u64,       // Only 0-255
}

// GOOD: Use smallest type
pub struct Config {
    pub fee_percentage: u8,   // 0-100
    pub max_items: u8,        // 0-255
}
```

### 3. Cloning Large Structures

```rust
// BAD: Unnecessary clone
fn process_data(data: Vec<u8>) -> Result<()> {
    let copy = data.clone();  // Wastes CU and heap
    // ...
}

// GOOD: Pass by reference
fn process_data(data: &[u8]) -> Result<()> {
    // Work directly with reference
}
```

### 4. Repeated PDA Derivation

```rust
// BAD: Finding bump every time
#[account(
    seeds = [b"vault"],
    bump  // Finds bump on every call!
)]
pub vault: Account<'info, Vault>,

// GOOD: Use saved bump
#[account(
    seeds = [b"vault"],
    bump = vault.bump  // Uses saved bump
)]
pub vault: Account<'info, Vault>,
```

### 5. Unnecessary Boxing

```rust
// BAD: Boxing adds heap overhead
let value = Box::new(calculate_value());

// GOOD: Keep on stack
let value = calculate_value();
```

### 6. String Operations

```rust
// BAD: String concatenation and formatting
let message = format!("User {} sent {} tokens", user, amount);
msg!(&message);

// GOOD: Use separate logs or remove entirely
user.log();
amount.log();
```

### 7. Deep CPI Chains

Each CPI adds significant overhead. Avoid unnecessary indirection:

```rust
// BAD: Unnecessary CPI
invoke(
    &my_helper_program::process(),
    &accounts,
)?;

// GOOD: Direct implementation
process_directly(&accounts)?;
```

### 8. Not Using Zero-Copy for Large Accounts

```rust
// BAD: Large account with standard serialization
#[account]
pub struct LargeData {
    pub items: [u64; 1000],  // Expensive to serialize/deserialize
}

// GOOD: Use zero-copy
#[account(zero_copy)]
#[repr(C)]
pub struct LargeData {
    pub items: [u64; 1000],  // Direct memory access
}
```

## Best Practices Summary

1. **Minimize or eliminate logging** in production code
2. **Use zero-copy** for accounts with large data structures
3. **Cache PDA bumps** - derive once, store in account, reuse
4. **Choose smallest data types** that meet your requirements
5. **Pass by reference** instead of cloning data
6. **Profile before optimizing** - measure CU usage to identify bottlenecks
7. **Consider native Rust** over Anchor for performance-critical programs
8. **Use `vec![]` initialization** instead of repeated `push()` calls
9. **Avoid unnecessary CPIs** - use direct operations when safe
10. **Balance safety vs performance** - don't sacrifice security without careful analysis
11. **Test CU usage** regularly - include benchmarks in your test suite
12. **Use checked math by default** - only optimize to unchecked when proven safe
13. **Minimize heap allocations** - prefer stack when possible
14. **Remove or conditionally compile debug code** for production builds
15. **Consider zero-copy for frequently updated accounts** - 50%+ CU savings

## Additional Resources

### Official Documentation
- [How to Optimize Compute](https://solana.com/developers/guides/advanced/how-to-optimize-compute)
- [Solana Compute Budget Documentation](https://github.com/solana-labs/solana/blob/090e11210aa7222d8295610a6ccac4acda711bb9/program-runtime/src/compute_budget.rs#L26-L87)

### Code Examples and Tools
- [solana-developers/cu_optimizations](https://github.com/solana-developers/cu_optimizations) - Official examples with benchmarks
- [hetdagli234/optimising-solana-programs](https://github.com/hetdagli234/optimising-solana-programs) - Community optimization examples

### Video Guides
- [How to optimize CU in programs](https://www.youtube.com/watch?v=7CbAK7Oq_o4)
- [Program optimization Part 1](https://www.youtube.com/watch?v=xoJ-3NkYXfY)
- [Program optimization Part 2 - Advanced](https://www.youtube.com/watch?v=Pwly1cOa2hg)
- [Writing Solana programs in Assembly](https://www.youtube.com/watch?v=eacDC0VgyxI)

### Technical Articles
- [RareSkills: Solana Compute Unit Price](https://rareskills.io/post/solana-compute-unit-price)
- [Understanding Solana Compute Units](https://www.helius.dev/blog/priority-fees-understanding-solanas-transaction-fee-mechanics)

### Advanced Tools
- [solana-nostd-entrypoint](https://github.com/cavemanloverboy/solana-nostd-entrypoint) - Minimal entry point
- [Mollusk](https://github.com/anza-xyz/mollusk) - Fast testing with CU benchmarking
