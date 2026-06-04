# Solana Program Testing Best Practices

**Common patterns, best practices, and additional testing resources**

This file provides best practices for organizing tests, testing common scenarios, and efficiently running your test suite. For framework-specific details and the testing pyramid structure, see the related files.

---

## Related Testing Documentation

- **[Testing Overview](./testing-overview.md)** - Testing pyramid structure and types of tests
- **[Testing Frameworks](./testing-frameworks.md)** - Mollusk, LiteSVM, and Anchor testing implementations

---

## Table of Contents

1. [Testing Best Practices](#testing-best-practices)
2. [Common Testing Patterns](#common-testing-patterns)
3. [Additional Resources](#additional-resources)

---

## Testing Best Practices

### Test Organization

**Organize by instruction:**
```
tests/
├── test_initialize.rs
├── test_update.rs
├── test_transfer.rs
├── test_close.rs
└── helpers/
    ├── mod.rs
    ├── accounts.rs
    └── instructions.rs
```

**Use helper modules:**
```rust
// tests/helpers/accounts.rs
use solana_sdk::{account::Account, pubkey::Pubkey};

pub fn system_account(lamports: u64) -> Account {
    Account {
        lamports,
        data: vec![],
        owner: solana_sdk::system_program::id(),
        executable: false,
        rent_epoch: 0,
    }
}

pub fn token_account(/* ... */) -> Account {
    // ...
}
```

```rust
// tests/test_initialize.rs
mod helpers;
use helpers::accounts::*;

#[test]
fn test_initialize() {
    let accounts = vec![
        (user, system_account(10_000_000)),
        // ...
    ];
}
```

### Edge Cases to Test

**Account validation:**
- Missing accounts
- Wrong account owner
- Account not writable when required
- Account not signer when required
- Uninitialized accounts
- Already initialized accounts

**Numeric boundaries:**
- Zero values
- Maximum values (u64::MAX)
- Overflow conditions
- Underflow conditions
- Negative results (when using signed integers)

**Authorization:**
- Missing signer
- Wrong signer
- Multiple signers
- PDA signer validation

**State transitions:**
- Invalid state transitions
- Idempotent operations
- Concurrent operations
- State rollback on error

**Resource limits:**
- Rent exemption
- Maximum account size
- Compute unit limits
- Stack depth limits (CPI)

### Error Condition Testing

**Test expected failures:**
```rust
#[test]
fn test_insufficient_funds_fails() {
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

    let user = Pubkey::new_unique();
    let accounts = vec![
        (user, system_account(100)),  // Not enough lamports
    ];

    let instruction = /* create transfer instruction for 1000 lamports */;

    let checks = vec![
        Check::instruction_err(InstructionError::InsufficientFunds),
    ];

    mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
}
```

**Test invalid data:**
```rust
#[test]
fn test_invalid_instruction_data() {
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

    let instruction = Instruction {
        program_id,
        accounts: /* ... */,
        data: vec![255, 255, 255],  // Invalid instruction data
    };

    let checks = vec![
        Check::instruction_err(InstructionError::InvalidInstructionData),
    ];

    mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
}
```

### Compute Unit Monitoring

**Set up continuous monitoring:**
```rust
// benches/compute_units.rs
use mollusk_svm_bencher::MolluskComputeUnitBencher;

fn main() {
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");
    let bencher = MolluskComputeUnitBencher::new(mollusk);

    // Benchmark each instruction
    bencher.bench(("initialize", &init_ix, &init_accounts));
    bencher.bench(("update", &update_ix, &update_accounts));
    bencher.bench(("close", &close_ix, &close_accounts));

    bencher
        .must_pass(true)
        .out_dir("./target/benches")
        .execute();
}
```

**Add to CI/CD:**
```yaml
# .github/workflows/test.yml
- name: Run compute unit benchmarks
  run: cargo bench

- name: Check for CU regressions
  run: |
    if git diff --exit-code target/benches/; then
      echo "No compute unit changes"
    else
      echo "Compute unit usage changed - review carefully"
      git diff target/benches/
    fi
```

### Running Tests Efficiently

**Build before testing:**
```bash
# Native Rust
cargo build-sbf && cargo test

# Anchor
anchor build && anchor test
```

**Run specific tests:**
```bash
# Native Rust
cargo test test_initialize

# Anchor
anchor test -- --test test_initialize
```

**Show program output:**
```bash
# Native Rust
cargo test -- --nocapture

# Anchor
anchor test -- --nocapture
```

**Run tests in parallel (be careful with shared state):**
```bash
cargo test -- --test-threads=4
```

---

## Common Testing Patterns

### Testing PDAs

**Anchor approach:**
```typescript
it("derives PDA correctly", async () => {
  const [pda, bump] = anchor.web3.PublicKey.findProgramAddressSync(
    [Buffer.from("seed"), user.publicKey.toBuffer()],
    program.programId
  );

  await program.methods
    .initialize(bump)
    .accounts({
      pda: pda,
      user: user.publicKey,
      systemProgram: anchor.web3.SystemProgram.programId,
    })
    .signers([user])
    .rpc();

  const accountData = await program.account.myAccount.fetch(pda);
  expect(accountData.bump).to.equal(bump);
});
```

**Native Rust approach:**
```rust
#[test]
fn test_pda_derivation() {
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

    let user = Pubkey::new_unique();
    let seeds = &[b"seed", user.as_ref()];
    let (pda, bump) = Pubkey::find_program_address(seeds, &program_id);

    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(user, true),
            AccountMeta::new(pda, false),
            AccountMeta::new_readonly(system_program::id(), false),
        ],
        data: vec![0, bump],  // Initialize instruction with bump
    };

    let accounts = vec![
        (user, system_account(10_000_000)),
        (pda, Account::default()),
    ];

    let checks = vec![
        Check::success(),
        Check::account(&pda)
            .owner(&program_id)
            .build(),
    ];

    mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
}
```

### Testing Token Operations

**Anchor with SPL Token:**
```typescript
import { TOKEN_PROGRAM_ID, createMint, createAccount, mintTo } from "@solana/spl-token";

it("transfers tokens", async () => {
  // Create mint
  const mint = await createMint(
    provider.connection,
    wallet.payer,
    wallet.publicKey,
    null,
    6
  );

  // Create token accounts
  const sourceAccount = await createAccount(
    provider.connection,
    wallet.payer,
    mint,
    user.publicKey
  );

  const destAccount = await createAccount(
    provider.connection,
    wallet.payer,
    mint,
    recipient.publicKey
  );

  // Mint tokens
  await mintTo(
    provider.connection,
    wallet.payer,
    mint,
    sourceAccount,
    wallet.publicKey,
    1_000_000
  );

  // Transfer via program
  await program.methods
    .transferTokens(new anchor.BN(500_000))
    .accounts({
      source: sourceAccount,
      destination: destAccount,
      authority: user.publicKey,
      tokenProgram: TOKEN_PROGRAM_ID,
    })
    .signers([user])
    .rpc();

  // Verify balances
  const sourceData = await getAccount(provider.connection, sourceAccount);
  const destData = await getAccount(provider.connection, destAccount);

  expect(sourceData.amount).to.equal(500_000n);
  expect(destData.amount).to.equal(500_000n);
});
```

**Native Rust with Mollusk:**
See the [Testing CPIs](./testing-frameworks.md#testing-cpis) section in Testing Frameworks for a complete token transfer example.

### Testing Associated Token Accounts

**Create ATA:**
```typescript
import { getAssociatedTokenAddress } from "@solana/spl-token";

it("creates associated token account", async () => {
  const ata = await getAssociatedTokenAddress(
    mint,
    user.publicKey
  );

  await program.methods
    .createAta()
    .accounts({
      ata: ata,
      mint: mint,
      owner: user.publicKey,
      payer: wallet.publicKey,
      tokenProgram: TOKEN_PROGRAM_ID,
      associatedTokenProgram: ASSOCIATED_TOKEN_PROGRAM_ID,
      systemProgram: SystemProgram.programId,
    })
    .rpc();

  const account = await getAccount(provider.connection, ata);
  expect(account.owner.toString()).to.equal(user.publicKey.toString());
  expect(account.mint.toString()).to.equal(mint.toString());
});
```

### Testing Account Validation

**Validate account owner:**
```rust
#[test]
fn test_wrong_owner_fails() {
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

    let account = Pubkey::new_unique();
    let wrong_owner = Pubkey::new_unique();

    let accounts = vec![
        (account, Account {
            lamports: 1_000_000,
            data: vec![0; 100],
            owner: wrong_owner,  // Wrong owner!
            executable: false,
            rent_epoch: 0,
        }),
    ];

    let instruction = /* create instruction */;

    let checks = vec![
        Check::instruction_err(InstructionError::InvalidAccountOwner),
    ];

    mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
}
```

**Validate signer:**
```rust
#[test]
fn test_missing_signer_fails() {
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

    let user = Pubkey::new_unique();

    let instruction = Instruction {
        program_id,
        accounts: vec![
            AccountMeta::new(user, false),  // Should be signer!
        ],
        data: vec![],
    };

    let accounts = vec![
        (user, system_account(1_000_000)),
    ];

    let checks = vec![
        Check::instruction_err(InstructionError::MissingRequiredSignature),
    ];

    mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
}
```

### Testing Rent Exemption

```rust
#[test]
fn test_account_is_rent_exempt() {
    let mollusk = Mollusk::new(&program_id, "target/deploy/my_program");

    let account = Pubkey::new_unique();
    let data_len = 100;
    let rent = mollusk.sysvars.rent;
    let rent_exempt_lamports = rent.minimum_balance(data_len);

    let accounts = vec![
        (account, Account {
            lamports: rent_exempt_lamports,
            data: vec![0; data_len],
            owner: program_id,
            executable: false,
            rent_epoch: 0,
        }),
    ];

    let instruction = /* create instruction */;

    let checks = vec![
        Check::success(),
        Check::account(&account)
            .rent_exempt()
            .build(),
    ];

    mollusk.process_and_validate_instruction(&instruction, &accounts, &checks);
}
```

---

## Additional Resources

### Documentation

- **Mollusk GitHub**: https://github.com/anza-xyz/mollusk
- **Mollusk Examples**: https://github.com/anza-xyz/mollusk/tree/main/harness/tests
- **Mollusk API Docs**: https://docs.rs/mollusk-svm/latest/mollusk_svm/
- **Anchor Testing Guide**: https://www.anchor-lang.com/docs/testing
- **LiteSVM**: https://github.com/amilz/litesvm
- **Solana Testing Docs**: https://solana.com/docs/programs/testing

### Key Takeaways

1. **Use Mollusk for fast, focused tests** - It's the recommended approach for both Anchor and native Rust programs
2. **Test early and often** - Catching bugs before deployment saves time and money
3. **Test error conditions** - Don't just test happy paths
4. **Monitor compute units** - Use benchmarking to catch performance regressions
5. **Organize tests logically** - Group by instruction, use helper modules
6. **Build before testing** - Always run `cargo build-sbf` or `anchor build` before tests
7. **Use validation checks** - Leverage the `Check` API for comprehensive validation
8. **Test with realistic data** - Use proper rent-exempt balances and realistic account states

### Quick Reference Commands

```bash
# Native Rust
cargo build-sbf                    # Build program
cargo test                         # Run tests
cargo test -- --nocapture         # Run tests with output
cargo test test_name              # Run specific test
cargo bench                       # Run compute unit benchmarks

# Anchor
anchor build                      # Build program
anchor test                       # Build, deploy, and test
anchor test --skip-build          # Test without rebuilding
anchor test -- --nocapture        # Test with logs
anchor test -- --test test_name   # Run specific test
```

---

## Next Steps

- For the testing strategy overview and pyramid structure, see **[Testing Overview](./testing-overview.md)**
- For framework-specific implementation details, see **[Testing Frameworks](./testing-frameworks.md)**
