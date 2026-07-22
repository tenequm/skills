---
name: solana-development
description: Build, test, deploy, and audit Solana programs with Anchor or native Rust, and build with ZK Compression (Light Protocol). Use when developing Solana smart contracts, implementing token operations, optimizing compute, deploying to networks, auditing programs for vulnerabilities, or creating compressed tokens/PDAs.
metadata:
  version: "0.7.1"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/solana-development
    emoji: "☀️"
    envVars:
      - name: SURFPOOL_DATASOURCE_RPC_URL
        required: false
        description: Dedicated mainnet RPC endpoint for surfpool's datasource (avoids public RPC rate limits when forking mainnet locally).
---

# Solana

Everything for building on Solana: developing programs (Anchor or native Rust), auditing them for security, and building with ZK Compression. All three share the same core model - accounts, PDAs, CPIs, tokens - and differ only in abstraction level and goal.

## What this skill covers

| Area | Use when | Jump to |
|------|----------|---------|
| **Development** | Writing programs, tokens, tests, deployments | [Development](#development) |
| **Security & Auditing** | Reviewing for vulnerabilities, writing exploits, audit reports | [Security and Auditing](#security-and-auditing) |
| **ZK Compression** | Rent-free tokens/PDAs at scale via Light Protocol | [ZK Compression](#zk-compression) |

---

# Development

Build Solana programs with Anchor (recommended) or native Rust. Both share accounts, PDAs, CPIs, and tokens; they differ in syntax and abstraction.

## Quick Start

### Recommended: Anchor Framework

Macros and tooling that cut boilerplate and generate TypeScript clients:

```rust
use anchor_lang::prelude::*;

declare_id!("YourProgramID");

#[program]
pub mod my_program {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, data: u64) -> Result<()> {
        ctx.accounts.account.data = data;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = user, space = 8 + 8)]
    pub account: Account<'info, MyAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct MyAccount {
    pub data: u64,
}
```

```bash
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install latest && avm use latest
anchor init my_project && cd my_project && anchor build && anchor test
```

**→ See [references/anchor.md](references/anchor.md) for the complete Anchor guide**

### Advanced: Native Rust

Maximum control, optimization potential, and deeper runtime understanding:

```rust
use solana_program::{
    account_info::AccountInfo, entrypoint, entrypoint::ProgramResult,
    pubkey::Pubkey, msg,
};

entrypoint!(process_instruction);

pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    msg!("Processing instruction");
    // Manual account parsing, validation, and instruction routing
    Ok(())
}
```

```bash
cargo new my_program --lib
cd my_program   # configure Cargo.toml (see native-rust.md)
cargo build-sbf
```

**→ See [references/native-rust.md](references/native-rust.md) for the complete native Rust guide**

## When to use which

| Your need | Approach | Reason |
|-----------|----------|--------|
| Standard DeFi/NFT program | Anchor | Faster, proven patterns |
| TypeScript client needed | Anchor | Auto-generates IDL + types |
| New to Solana | Anchor | Gentler learning curve |
| Compute optimization critical | Native Rust | Direct control, no overhead |
| Smallest program size | Native Rust | No abstraction layer |
| Learning fundamentals | Native Rust | Understand the platform deeply |

You can also start with Anchor for speed, then optimize hot paths with native patterns. Both can coexist in one workspace.

## Reference map

**Foundations**
- [accounts.md](references/accounts.md) - Account model, ownership, rent, validation
- [pda.md](references/pda.md) - Program Derived Addresses: derivation, canonical bumps, signing
- [cpi.md](references/cpi.md) - Cross-Program Invocations safely

**Tokens**
- [tokens-overview.md](references/tokens-overview.md) - Token accounts and ATAs
- [tokens-operations.md](references/tokens-operations.md) - Create, mint, transfer, burn, close
- [tokens-validation.md](references/tokens-validation.md) - Account validation patterns
- [tokens-2022.md](references/tokens-2022.md) - Token Extensions Program
- [tokens-patterns.md](references/tokens-patterns.md) - Common patterns and security

**Testing**
- [testing-overview.md](references/testing-overview.md) - Test pyramid and strategy
- [testing-frameworks.md](references/testing-frameworks.md) - Mollusk, Anchor test, native Rust
- [testing-practices.md](references/testing-practices.md) - Best practices and patterns
- [surfpool.md](references/surfpool.md) - Local dev with mainnet forking, cheatcodes, IaC

**Deployment**
- [deployment.md](references/deployment.md) - Deploy, upgrade, verify, manage programs
- [production-deployment.md](references/production-deployment.md) - Verified builds (Anchor 0.32.1)

**Client**
- [client-development.md](references/client-development.md) - dApp client: wallet connections, React hooks, SOL/SPL transfers, transaction management (framework-kit and @solana/kit 6.x)

**Implementation details**
- [serialization.md](references/serialization.md) - Data layout, Borsh, zero-copy
- [error-handling.md](references/error-handling.md) - Custom errors, propagation, client handling
- [security.md](references/security.md) - Defensive programming patterns during development

**Advanced**
- [compute-optimization.md](references/compute-optimization.md) - CU optimization and benchmarking
- [versioned-transactions.md](references/versioned-transactions.md) - Address Lookup Tables for 256+ accounts
- [durable-nonces.md](references/durable-nonces.md) - Offline signing with durable nonces
- [transaction-lifecycle.md](references/transaction-lifecycle.md) - Submission, retries, confirmations

**Low-level**
- [sysvars.md](references/sysvars.md) - Clock, Rent, EpochSchedule, SlotHashes
- [builtin-programs.md](references/builtin-programs.md) - System Program, Compute Budget Program

## Common tasks

| Task | Pointer |
|------|---------|
| New program | Anchor: `anchor init` / Native: `cargo new --lib` → [anchor.md](references/anchor.md), [native-rust.md](references/native-rust.md) |
| Initialize a PDA | [pda.md](references/pda.md) |
| Transfer SPL tokens | [tokens-operations.md](references/tokens-operations.md) |
| Fast unit tests | Mollusk → [testing-frameworks.md](references/testing-frameworks.md) |
| Local mainnet fork | `surfpool start` → [surfpool.md](references/surfpool.md) |
| Deploy to devnet | [deployment.md](references/deployment.md) |
| Production verified build | `solana-verify build` → [production-deployment.md](references/production-deployment.md) |
| Optimize compute | [compute-optimization.md](references/compute-optimization.md) |
| Handle 40+ accounts | Address Lookup Tables → [versioned-transactions.md](references/versioned-transactions.md) |
| Offline signing | Durable nonces → [durable-nonces.md](references/durable-nonces.md) |

---

# Security and Auditing

Systematic security review for Solana programs (Anchor or native Rust). The core principle: **attackers can pass arbitrary accounts to any instruction**, so there are no implicit guarantees - validate everything, trust nothing.

## Review process

1. **Initial assessment** - Framework (Anchor vs native), Anchor version, dependencies (oracles, external programs), instruction count, account types, program purpose.
2. **Systematic review** - For each instruction, check in order: account validation (signer/owner/writable/init), arithmetic safety (`checked_*`), PDA security (canonical bumps, seed uniqueness), CPI security (validated targets), oracle/external data (staleness, status). → [security-checklists.md](references/security-checklists.md)
3. **Vulnerability pattern detection** - Type cosplay, account reloading, improper closing, missing lamports/ownership checks, PDA substitution, arbitrary CPI, overflow/underflow. → [vulnerability-patterns.md](references/vulnerability-patterns.md)
4. **Architecture and testing review** - PDA design, space/rent, error handling, event emission, compute budget, test coverage (unit/integration/fuzz), upgrade and authority management.
5. **Generate report** - Findings by severity, critical first, quick wins, testing recommendations.

## Essential checks (every instruction)

**Anchor:**
```rust
#[derive(Accounts)]
pub struct SecureInstruction<'info> {
    #[account(
        mut,
        has_one = authority,                          // relationship check
        seeds = [b"vault", user.key().as_ref()], bump // canonical bump
    )]
    pub vault: Account<'info, Vault>,
    pub authority: Signer<'info>,                     // signer required
    pub token_program: Program<'info, Token>,         // program validation
}

let total = balance.checked_add(amount).ok_or(ErrorCode::Overflow)?;
```

**Native Rust:**
```rust
if !authority.is_signer { return Err(ProgramError::MissingRequiredSignature); }
if vault.owner != program_id { return Err(ProgramError::IllegalOwner); }
let total = balance.checked_add(amount).ok_or(ProgramError::ArithmeticOverflow)?;
```

## Critical anti-patterns

❌ **Never:** `saturating_*` arithmetic (hides errors), `unwrap()`/`expect()` in production, `init_if_needed` without extra checks, skipped signer validation, unchecked arithmetic, arbitrary CPI targets, forgetting to reload accounts after mutations.

✅ **Always:** `checked_*` arithmetic, `ok_or(error)?` on Options, explicit `init` with validation, `Signer`/`is_signer` checks, `Program<'info, T>` for CPI targets, reload after external mutations, validate ownership + discriminator + relationships.

## Severity and finding format

- 🔴 **Critical** - Funds stolen/lost, protocol broken
- 🟠 **High** - Disruption, partial fund loss possible
- 🟡 **Medium** - Edge cases, griefing, suboptimal behavior
- 🔵 **Low** - Code quality, gas, best practices
- 💡 **Informational** - Recommendations, documentation

```markdown
## 🔴 [CRITICAL] Title
**Location:** `programs/vault/src/lib.rs:45-52`
**Issue:** Brief description.
**Vulnerable Code:** ```rust ... ```
**Exploit Scenario:** How it's exploited, step by step.
**Recommendation:** ```rust ... ```
**References:** Links to docs or similar exploits.
```

## Reference map

- [security-fundamentals.md](references/security-fundamentals.md) - Security mindset, threat modeling, core validation, input/state/arithmetic safety, re-entrancy
- [vulnerability-patterns.md](references/vulnerability-patterns.md) - Each vuln with vulnerable code, exploit scenario, secure fix, references
- [security-checklists.md](references/security-checklists.md) - Account, arithmetic, PDA, CPI, oracle, token checklists
- [anchor-security.md](references/anchor-security.md) - Anchor constraints, CpiContext, events, custom errors
- [native-security.md](references/native-security.md) - Manual validation, secure PDA signing, discriminators, rent exemption
- [caveats.md](references/caveats.md) - Solana quirks, Anchor limitations, testing blind spots, version issues

## Key questions for every audit

1. Can an attacker substitute accounts? (PDA validation, program IDs, `has_one`)
2. Can arithmetic overflow/underflow? (checked ops, division by zero)
3. Are all accounts validated? (owner, signer, writable, initialized)
4. Can the program be drained? (authorization, reentrancy, account confusion)
5. What happens in edge cases? (zero amounts, max values, closed accounts, expired data)
6. Are external dependencies safe? (oracle staleness/status, CPI targets, token program)

## Modern practices (2025)

Anchor 0.30+ • Token-2022 with proper extension handling • `InitSpace` derive • emit events for critical state changes • fuzz tests with Trident • document invariants • roadmap: Dev → Audit → Testnet → Audit → Mainnet.

---

# ZK Compression

ZK Compression enables rent-free tokens and PDAs by storing state on the ledger (not in accounts), using zero-knowledge proofs to validate state transitions. Built by Light Protocol, indexed by Helius Photon.

## When to use

**Use when:** creating millions of token accounts (~5000x cheaper), airdrops/loyalty/gaming mints to many recipients, many infrequently-updated user accounts, low-update-frequency PDAs.

**Use regular accounts when:** updated frequently (>1000 lifetime writes), large data accessed on-chain, or compute budget is critical (compression adds ~100k CU).

## Quick Start

```bash
# TypeScript client
npm install @lightprotocol/stateless.js @lightprotocol/compressed-token
# Rust SDK for programs
cargo add light-sdk
# CLI + local validator
npm install -g @lightprotocol/zk-compression-cli
light test-validator      # local validator with compression
light init my-program     # new Anchor project with compression
```

### Mint compressed tokens (TypeScript)

```typescript
import { createRpc } from '@lightprotocol/stateless.js';
import { createMint, mintTo, transfer } from '@lightprotocol/compressed-token';

const rpc = createRpc(); // or createRpc('https://mainnet.helius-rpc.com?api-key=YOUR_KEY')

const { mint } = await createMint(rpc, payer, payer.publicKey, 9);
await mintTo(rpc, payer, mint, recipient, payer, 1_000_000_000);
await transfer(rpc, payer, mint, 500_000_000, owner, recipient);
const accounts = await rpc.getCompressedTokenAccountsByOwner(owner, { mint });
```

**→ See [references/compressed-pdas.md](references/compressed-pdas.md) for the full Anchor program with compressed PDAs (LightAccount, validity proofs, CPI).**

## Core concepts

**Compressed account model** - Like regular accounts but stored on the ledger instead of AccountsDB. No rent. Identified by content hash (changes on every write) or an optional persistent address (PDA-like). State validated by ZK proofs.

**State trees** - Concurrent Merkle trees (Poseidon hashing); only the root is on-chain. **V2 batched trees** (mainnet, Jan 2026): ~250x cheaper state-root updates and ~70% less CU vs V1. New deployments use V2 automatically; V1 still supported.

**Validity proofs** - Groth16 ZK proofs, constant 128 bytes regardless of account count, ~100k CU to verify.

**LightAccount operations:**
```rust
LightAccount::<T>::new_init(&program_id, Some(address), tree_index);     // create
LightAccount::<T>::new_mut(&program_id, &account_meta, current_state)?;  // modify
LightAccount::<T>::new_close(&program_id, &account_meta, current_state)?; // close
```

## RPC and infrastructure

Query compressed state via Helius RPC or self-hosted Photon. Key methods: `getCompressedAccount`, `getCompressedAccountsByOwner`, `getCompressedTokenAccountsByOwner`, `getCompressedTokenBalancesByOwner`, `getValidityProof`, `getMultipleCompressedAccounts`, `getCompressionSignaturesForAccount`.

Node types: **Photon RPC** (indexes state, serves queries - Helius or self-host), **Prover** (generates proofs), **Forester** (maintains trees, empties nullifier queues).

```bash
cargo install photon-indexer
photon --rpc-url=https://api.devnet.solana.com
```

## Trade-offs

Larger transactions (+128 byte proof + account data) • higher CU (~100k proof + ~6k per account) • each write nullifies old state and appends new • requires a Photon indexer for queries. With V2 batched trees, break-even shifts well past V1's ~1000-write threshold.

## Reference map

- [compressed-accounts.md](references/compressed-accounts.md) - Account model, hashing, addresses
- [compressed-tokens.md](references/compressed-tokens.md) - Token operations, pools, batch operations
- [compressed-pdas.md](references/compressed-pdas.md) - Building programs with compressed PDAs
- [client-integration.md](references/client-integration.md) - TypeScript/Rust client setup, RPC methods

External: [ZK Compression Docs](https://www.zkcompression.com/) • [Light Protocol](https://github.com/Lightprotocol/light-protocol) • [Helius SDK](https://github.com/helius-labs/helius-sdk) • [Photon Indexer](https://github.com/helius-labs/photon) • [Program Examples](https://github.com/Lightprotocol/program-examples)

---

# Resources

Official docs, tools, learning paths, security guides, audit reports, security firms, and community links:

**→ See [references/resources.md](references/resources.md)**

## General best practices

✅ Validate every account (ownership, signers, mutability) • use `checked_*` arithmetic • test extensively (unit, integration, edge cases) • use PDAs for program-owned accounts • minimize and profile compute • add `security.txt` so researchers can reach you.

**Anchor-specific:** `InitSpace` derive for space • `has_one` constraints • `Program<'info, T>` for CPI validation • `emit!` events • group related constraints.

**Native-specific:** `next_account_info` for safe iteration • cache PDA bumps • zero-copy for large structs (50%+ CU savings) • minimize logging (pubkey formatting is expensive) • `solana-verify build` for production.

## Getting help

- Anchor: [Discord](https://discord.gg/srmqvxf) • [Docs](https://www.anchor-lang.com/docs)
- Solana: [Stack Exchange](https://solana.stackexchange.com/) • [Discord](https://discord.gg/solana)
