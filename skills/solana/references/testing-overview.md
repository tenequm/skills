# Solana Program Testing Overview

**High-level guide to testing Solana programs with the test pyramid structure**

This file provides an overview of Solana program testing, the testing pyramid structure, and the types of tests you should write. For specific implementation details and framework-specific guidance, see the related files.

---

## Related Testing Documentation

- **[Testing Frameworks](./testing-frameworks.md)** - Mollusk, LiteSVM, and Anchor testing implementations
- **[Testing Best Practices](./testing-practices.md)** - Best practices, common patterns, and additional resources

---

## Table of Contents

1. [Why Testing Matters](#why-testing-matters)
2. [Types of Tests](#types-of-tests)
3. [Testing Frameworks Available](#testing-frameworks-available)
4. [Test Structure Pyramid](#test-structure-pyramid)

---

## Why Testing Matters for Solana Programs

Solana programs are immutable after deployment and handle real financial assets. Comprehensive testing is critical to:

- **Prevent loss of funds**: Bugs in deployed programs can lead to irreversible financial losses
- **Ensure correctness**: Verify program logic works as intended under all conditions
- **Optimize performance**: Monitor compute unit usage to stay within Solana's limits (1.4M CU cap)
- **Build confidence**: Thorough testing enables safer deployments and upgrades
- **Catch edge cases**: Test boundary conditions, error handling, and attack vectors

---

## Types of Tests

**Unit Tests**
- Test individual functions and instruction handlers in isolation
- Fast, focused validation of specific logic
- Run frequently during development

**Integration Tests**
- Test complete instruction flows with realistic account setups
- Validate cross-program invocations (CPIs)
- Ensure proper state transitions

**Fuzz Tests**
- Generate random inputs to find edge cases and vulnerabilities
- Discover unexpected failure modes
- Test input validation thoroughly

**Compute Unit Benchmarks**
- Monitor compute unit consumption for each instruction
- Track performance regressions
- Ensure programs stay within CU limits

---

## Testing Frameworks Available

**Mollusk** (Recommended for both Anchor and Native Rust)
- Lightweight SVM test harness
- Exceptionally fast (no validator overhead)
- Works with both Anchor and native Rust programs
- Direct program execution via BPF loader
- Requires explicit account setup (no AccountsDB)

**LiteSVM** (Alternative for integration tests)
- In-process Solana VM for testing
- Available in Rust, TypeScript, and Python
- Faster than solana-program-test
- Supports RPC-like interactions
- Good for complex integration scenarios

**Anchor Test** (Anchor framework)
- TypeScript-based testing using @coral-xyz/anchor
- Integrates with local validator or LiteSVM
- Natural for testing Anchor programs from client perspective
- Slower but more realistic end-to-end tests

**solana-program-test** (Legacy)
- Full validator simulation
- More realistic but much slower
- Generally replaced by Mollusk and LiteSVM

**Recommendation**: Use Mollusk for fast unit and integration tests. Use LiteSVM or Anchor tests for end-to-end validation when needed.

---

## Test Structure Pyramid

### Overview

A production-grade Solana program should have a multi-level testing strategy. Each level serves a specific purpose and catches different types of bugs.

```
                    ┌─────────────────────┐
                    │  Devnet/Mainnet     │  ← Smoke tests
                    │  Smoke Tests        │    (Manual, slow)
                    └─────────────────────┘
                  ┌───────────────────────────┐
                  │   SDK Integration Tests   │  ← Full transaction flow
                  │   (LiteSVM/TypeScript)    │    (Seconds per test)
                  └───────────────────────────┘
              ┌─────────────────────────────────────┐
              │      Mollusk Program Tests          │  ← Instruction-level
              │   (Unit + Integration in Rust)      │    (~100ms per test)
              └─────────────────────────────────────┘
          ┌───────────────────────────────────────────────┐
          │        Inline Unit Tests (#[cfg(test)])       │  ← Pure functions
          │    (Math, validation, transformations)        │    (Milliseconds)
          └───────────────────────────────────────────────┘
```

### Level 1: Inline Unit Tests

**Purpose:** Test pure functions in isolation - math, validation logic, data transformations.

**Location:** Inside your program code with `#[cfg(test)]`

**Why needed:**
- Instant feedback (milliseconds)
- Runs with `cargo test` - no build artifacts needed
- Catches arithmetic edge cases before they reach the SVM
- Documents expected behavior inline with code

**What belongs here:**
- Share calculations: `1_000_000 * 5000 / 10000 = 500_000`
- Overflow detection: `u64::MAX * 10000 = None`
- Rounding behavior: `100 * 1 / 10000 = 0` (floors)
- BPS (basis points) sum validation
- Data serialization/deserialization helpers

**What doesn't belong:**
- Account validation (needs ownership checks)
- CPI logic
- Full instruction execution
- State transitions

**Example:**
```rust
// In your program code (e.g., src/math.rs)
pub fn calculate_fee(amount: u64, fee_bps: u16) -> Option<u64> {
    let fee = (amount as u128)
        .checked_mul(fee_bps as u128)?
        .checked_div(10_000)?;

    Some(fee as u64)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_fee_basic() {
        assert_eq!(calculate_fee(1_000_000, 250), Some(25_000)); // 2.5%
        assert_eq!(calculate_fee(1_000_000, 5000), Some(500_000)); // 50%
    }

    #[test]
    fn test_calculate_fee_rounding() {
        assert_eq!(calculate_fee(100, 1), Some(0)); // Rounds down
        assert_eq!(calculate_fee(10_000, 1), Some(1)); // 0.01%
    }

    #[test]
    fn test_calculate_fee_overflow() {
        assert_eq!(calculate_fee(u64::MAX, 10000), None); // Would overflow
    }
}
```

### Level 2: Mollusk Program Tests

**Purpose:** Test individual instructions with full account setup but without validator overhead.

**Location:** `tests/` directory or `#[cfg(test)]` modules

**Why needed:**
- Tests actual program binary execution
- Validates account constraints, signer checks, ownership
- ~100ms per test vs ~1s for full validator
- Catches instruction-level bugs
- Compute unit benchmarking

**What belongs here:**
- Each instruction handler (initialize, create_split, execute_split, etc.)
- Error conditions (wrong signer, invalid account owner)
- Account state transitions
- Cross-program invocations (CPIs)
- PDA derivation and signing
- Rent exemption validation

**Example:**
```rust
// tests/test_initialize.rs
use {
    mollusk_svm::Mollusk,
    my_program::{instruction::initialize, ID},
    solana_sdk::{
        account::Account,
        instruction::Instruction,
        pubkey::Pubkey,
    },
};

#[test]
fn test_initialize_success() {
    let mollusk = Mollusk::new(&ID, "target/deploy/my_program");

    let user = Pubkey::new_unique();
    let account = Pubkey::new_unique();

    let instruction = initialize(&user, &account);
    let accounts = vec![
        (user, system_account(10_000_000)),
        (account, Account::default()),
    ];

    let result = mollusk.process_instruction(&instruction, &accounts);
    assert!(result.is_ok());
}

#[test]
fn test_initialize_wrong_signer_fails() {
    let mollusk = Mollusk::new(&ID, "target/deploy/my_program");

    let user = Pubkey::new_unique();
    let wrong_signer = Pubkey::new_unique();

    let mut instruction = initialize(&user, &Pubkey::new_unique());
    instruction.accounts[0].is_signer = false; // Missing signature

    let accounts = vec![(user, system_account(10_000_000))];

    let checks = vec![Check::instruction_err(
        InstructionError::MissingRequiredSignature
    )];

    mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
}
```

### Level 3: SDK Integration Tests

**Purpose:** Test that SDK produces correct instructions that work end-to-end.

**Location:** Separate SDK package (`sdk/tests/`) or TypeScript tests

**Why needed:**
- Validates serialization matches program expectations
- Tests full transaction flow (multiple instructions)
- Catches SDK bugs before users hit them
- Client-perspective testing
- Ensures TypeScript/Rust SDK matches program

**What belongs here:**
- SDK instruction builders produce valid transactions
- Full flows: create → deposit → execute
- Multiple instructions in one transaction
- Account resolution (finding PDAs from SDK)
- Error handling from client side
- Event parsing and decoding

**Example (LiteSVM):**
```rust
// sdk/tests/integration_test.rs
use {
    litesvm::LiteSVM,
    my_program_sdk::{instructions, MyProgramClient},
    solana_sdk::{
        signature::Keypair,
        signer::Signer,
    },
};

#[test]
fn test_full_flow_create_and_execute() {
    let mut svm = LiteSVM::new();

    // Add program
    let program_bytes = include_bytes!("../../target/deploy/my_program.so");
    svm.add_program(MY_PROGRAM_ID, program_bytes);

    // Create client
    let payer = Keypair::new();
    svm.airdrop(&payer.pubkey(), 10_000_000_000).unwrap();

    let client = MyProgramClient::new(&svm, &payer);

    // Step 1: Initialize
    let tx1 = client.initialize().unwrap();
    svm.send_transaction(tx1).unwrap();

    // Step 2: Deposit
    let tx2 = client.deposit(1_000_000).unwrap();
    svm.send_transaction(tx2).unwrap();

    // Step 3: Execute
    let tx3 = client.execute().unwrap();
    let result = svm.send_transaction(tx3).unwrap();

    // Verify final state
    let account = client.get_account().unwrap();
    assert_eq!(account.balance, 1_000_000);
}
```

### Level 4: Devnet/Mainnet Smoke Tests

**Purpose:** Final validation in real environment.

**Location:** Manual testing or automated CI scripts

**Why needed:**
- Real RPC, real fees, real constraints
- Validates deployment configuration
- Tests against actual on-chain state
- Catches environment-specific issues
- Verifies upgrades work correctly

**What belongs here:**
- Post-deployment smoke tests (critical paths only)
- Upgrade validation (new version works)
- Integration with other mainnet programs
- Performance under real network conditions

**Example (Manual script):**
```bash
#!/bin/bash
# scripts/smoke-test-devnet.sh

echo "Running devnet smoke tests..."

# Test 1: Initialize
solana-keygen new --no-bpf-loader-deprecated --force -o /tmp/test-user.json
solana airdrop 2 /tmp/test-user.json --url devnet

my-program-cli initialize \
  --program-id $PROGRAM_ID \
  --payer /tmp/test-user.json \
  --url devnet

# Test 2: Execute main flow
my-program-cli execute \
  --amount 1000000 \
  --payer /tmp/test-user.json \
  --url devnet

echo "✅ Smoke tests passed"
```

### How to Use This Pyramid

**During development:**
1. Write inline tests as you implement math/validation
2. Write Mollusk tests for each instruction
3. Run frequently: `cargo test`

**Before PR/merge:**
1. Ensure all inline + Mollusk tests pass
2. Add SDK integration tests if SDK changed
3. Run compute unit benchmarks

**Before deployment:**
1. All tests pass on devnet-compatible build
2. Deploy to devnet
3. Run manual smoke tests on devnet
4. If pass, proceed to mainnet

**After deployment:**
1. Run smoke tests on mainnet
2. Monitor for errors
3. Keep tests updated as program evolves

### Benefits of This Structure

**Fast feedback loop:**
- Level 1 tests run in milliseconds
- Catch bugs early without slow iteration

**Comprehensive coverage:**
- Pure logic (Level 1)
- Program execution (Level 2)
- Client integration (Level 3)
- Real environment (Level 4)

**Efficient CI/CD:**
- Level 1-2 in every PR (fast)
- Level 3 on merge to main
- Level 4 post-deployment

**Clear responsibilities:**
- Each level tests different concerns
- No redundant tests
- Easier to maintain

---

## Next Steps

- For implementation details on Mollusk, LiteSVM, and Anchor testing, see **[Testing Frameworks](./testing-frameworks.md)**
- For best practices, common patterns, and additional resources, see **[Testing Best Practices](./testing-practices.md)**
