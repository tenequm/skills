# Solana Program Deployment Reference

This reference covers deployment workflows, best practices, and troubleshooting for both Anchor and native Rust Solana programs.

## Table of Contents

- [Deployment Overview](#deployment-overview)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Building Programs](#building-programs)
- [Deploying to Networks](#deploying-to-networks)
- [Program Upgrades](#program-upgrades)
- [Verified Builds](#verified-builds)
- [Program Authority Management](#program-authority-management)
- [Multisig Deployments](#multisig-deployments)
- [Network-Specific Considerations](#network-specific-considerations)
- [Post-Deployment](#post-deployment)
- [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
- [Best Practices](#best-practices)

---

## Deployment Overview

### Solana Networks

Solana has three primary networks:

**Localhost (127.0.0.1:8899)**
- Local test validator running on your machine
- Fastest iteration, no cost
- Full control over network state
- Use for rapid development and debugging

**Devnet**
- Public development network
- Free SOL via airdrops
- Resets periodically
- Use for integration testing

**Mainnet-beta**
- Production network with real economic value
- Requires real SOL for deployment and transactions
- Immutable deployed programs (unless upgradeable)
- Use for production deployments

### Network Configuration

**Anchor** - Edit `Anchor.toml`:

```toml
[toolchain]

[features]
seeds = false
skip-lint = false

[programs.localnet]
my_program = "11111111111111111111111111111111"

[programs.devnet]
my_program = "YourDevnetProgramID"

[programs.mainnet]
my_program = "YourMainnetProgramID"

[registry]
url = "https://api.apr.dev"

[provider]
cluster = "Localnet"  # Change to "Devnet" or "Mainnet"
wallet = "~/.config/solana/id.json"

[scripts]
test = "yarn run ts-mocha -p ./tsconfig.json -t 1000000 tests/**/*.ts"
```

**Native Rust** - Use Solana CLI:

```bash
# View current config
solana config get

# Set network
solana config set --url https://api.devnet.solana.com  # Devnet
solana config set --url https://api.mainnet-beta.solana.com  # Mainnet
solana config set --url http://localhost:8899  # Localnet

# Set wallet
solana config set --keypair ~/.config/solana/id.json
```

### Cost Considerations

Program deployment requires rent-exempt balance for:

1. **Program Account** - Stores program metadata (small cost)
2. **Program Data Account** - Stores the executable bytecode (major cost)

**Calculate deployment cost:**

```bash
# Get program size
ls -l target/deploy/my_program.so
# Example: 363960 bytes

# Check rent for program data account (1x program size in newer versions)
solana rent 363960
# Output:
# Rent-exempt minimum: ~2.5 SOL

# Add transaction fees (~0.002 SOL) for deployment transactions
```

**Cost breakdown:**
- **363KB program** ≈ 2.5 SOL rent + 0.002 SOL tx fees = **~2.502 SOL**
- **800KB program** ≈ 5.5 SOL rent + 0.002 SOL tx fees = **~5.502 SOL**

**Important:** Since Solana CLI v1.18+, program accounts are sized to 1x the .so file (previously 2x), reducing costs by approximately 50%.

---

## Pre-Deployment Checklist

### 1. Build Verification

**Anchor:**
```bash
# Clean build
anchor clean
anchor build

# Verify build succeeded
ls -la target/deploy/
# Should see: my_program.so and my_program-keypair.json
```

**Native Rust:**
```bash
# Clean build
cargo clean
cargo build-sbf

# Verify build
ls -la target/deploy/
# Should see: my_program.so
```

### 2. Testing Completeness

**Anchor:**
```bash
# Run all tests on local validator
anchor test

# Run tests without redeploying
anchor test --skip-deploy

# Run specific test file
anchor test tests/my-test.ts
```

**Native Rust:**
```bash
# Run Mollusk unit tests
cargo test

# Run integration tests
cargo test-sbf
```

### 3. Security Review

- [ ] All account validations implemented (owner checks, signer checks)
- [ ] No missing arithmetic overflow checks
- [ ] PDA seeds properly validated
- [ ] No uninitialized account usage
- [ ] Authority checks on privileged operations
- [ ] CPI security (check target program IDs)
- [ ] Consider professional audit for mainnet

### 4. Program Size Optimization

**Check current size:**
```bash
ls -lh target/deploy/my_program.so
```

**Optimization techniques:**

```toml
# Cargo.toml - Release profile optimization
[profile.release]
overflow-checks = true
lto = "fat"              # Link-time optimization
codegen-units = 1        # Single codegen unit
opt-level = "z"          # Optimize for size (use "3" for speed)
strip = true             # Strip symbols

[profile.release.build-override]
opt-level = 3
incremental = false
codegen-units = 1
```

**Remove unused dependencies:**
```bash
# Check dependency tree
cargo tree

# Remove unused features
# Instead of:
# solana-program = "2.1.0"
# Use:
solana-program = { version = "2.1.0", default-features = false }
```

**Current size limits:**
- Maximum program size: ~1 MB (actual limit varies by compute budget)
- Recommended: Keep under 500KB for reliable deployment

### 5. Rent Calculation

```bash
# Calculate exact rent needed
PROGRAM_SIZE=$(wc -c < target/deploy/my_program.so)
solana rent $PROGRAM_SIZE

# Fund deployment wallet
solana balance
# If insufficient, request airdrop (devnet) or transfer SOL
```

---

## Building Programs

### Anchor Programs

**Standard build:**
```bash
anchor build
```

**What it produces:**
- `target/deploy/my_program.so` - Executable binary
- `target/deploy/my_program-keypair.json` - Program ID keypair
- `target/idl/my_program.json` - Interface definition
- `target/types/my_program.ts` - TypeScript types

**Build specific program in workspace:**
```bash
anchor build --program-name my_program
```

**Verifiable build (Docker-based):**
```bash
# Install solana-verify CLI
cargo install solana-verify

# Build verifiably
solana-verify build

# Build specific program
solana-verify build --library-name my_program
```

**Sync program IDs:**
```bash
# After first build, sync declared IDs with keypair
anchor keys sync
```

### Native Rust Programs

**Standard build:**
```bash
cargo build-sbf
```

**What it produces:**
- `target/deploy/my_program.so` - Executable binary
- No automatic keypair generation (must provide or use deployed ID)

**Verifiable build:**
```bash
solana-verify build --library-name my_program
```

**Build with specific Solana version:**
```bash
# Set platform tools version
cargo build-sbf --sbf-sdk ~/.local/share/solana/install/releases/2.1.0/solana-release/bin/sdk/sbf
```

### Understanding Build Outputs

**.so file:**
- Compiled BPF bytecode
- This is what gets deployed on-chain
- Hash determines if program matches source

**Program ID keypair (Anchor):**
- Generated on first build
- Defines program's on-chain address
- **CRITICAL:** Back this up before deploying

**IDL (Anchor only):**
- JSON describing program interface
- Used by clients to interact with program
- Can be uploaded on-chain for discovery

---

## Deploying to Networks

### Anchor Deployment

**Deploy to configured network:**
```bash
# Deploy to network specified in Anchor.toml [provider] cluster
anchor deploy

# Specify network explicitly
anchor deploy --provider.cluster devnet
anchor deploy --provider.cluster mainnet
```

**Deploy with specific program ID:**
```bash
# First deployment - uses keypair from target/deploy/
anchor deploy

# Redeploy to same address (upgrade)
anchor deploy
```

**Deploy with priority fees (congested networks):**
```bash
# Set priority fee in micro-lamports per compute unit
anchor deploy --provider.cluster mainnet \
  --program-name my_program \
  -- --with-compute-unit-price 50000
```

**What `anchor deploy` does:**
1. Reads program from `target/deploy/my_program.so`
2. Creates or uses existing program account
3. Uploads program data via multiple write transactions
4. Sets executable flag on program account
5. Optionally uploads IDL to on-chain account

### Native Rust Deployment

**Deploy new program:**
```bash
# Deploy with auto-generated program ID
solana program deploy target/deploy/my_program.so

# Deploy to specific program ID (first time)
solana program deploy target/deploy/my_program.so \
  --program-id my_program-keypair.json
```

**Deploy with priority fees:**
```bash
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  --with-compute-unit-price 50000 \
  --max-sign-attempts 100 \
  --use-rpc
```

**Flags explained:**
- `--with-compute-unit-price` - Priority fee (micro-lamports per CU)
- `--max-sign-attempts` - Retries for recent blockhash expiration
- `--use-rpc` - Send transactions individually vs in batches
- `-u <URL>` - Specify RPC endpoint

**Check deployment cost before deploying:**
```bash
# Dry run to estimate cost
solana program deploy target/deploy/my_program.so --dry-run
```

### Deploying with Specific Program ID

**Generate deterministic program ID:**
```bash
# Create new keypair
solana-keygen new -o my-program-keypair.json

# View address
solana-keygen pubkey my-program-keypair.json
```

**For Anchor:**
```bash
# Update lib.rs with new program ID
declare_id!("YourNewProgramID");

# Update Anchor.toml
[programs.devnet]
my_program = "YourNewProgramID"

# Rebuild and deploy
anchor build
anchor keys sync  # Verify IDs match
anchor deploy
```

**For Native Rust:**
```bash
# Deploy using keypair
solana program deploy target/deploy/my_program.so \
  --program-id my-program-keypair.json
```

### Deployment Costs and Funding

**Check balance before deployment:**
```bash
solana balance
```

**Fund wallet for devnet:**
```bash
# Request airdrop (2 SOL max per request)
solana airdrop 2

# For larger programs, request multiple times
solana airdrop 2 && solana airdrop 2
```

**Fund wallet for mainnet:**
```bash
# Transfer SOL from exchange or another wallet
# No airdrops available on mainnet
```

**Cost estimation:**
```bash
# Program size
PROGRAM_SIZE=$(wc -c < target/deploy/my_program.so)

# Rent cost
solana rent $PROGRAM_SIZE

# Add ~0.002-0.01 SOL for transaction fees
# Add priority fees if network is congested
```

---

## Program Upgrades

### How Upgrades Work

Solana programs deployed via `solana program deploy` or `anchor deploy` are **upgradeable by default**.

**Upgrade mechanism:**
1. Program data lives in separate account from program account
2. Upgrade authority (wallet) can replace program data
3. Program address stays the same
4. All accounts/PDAs remain valid

**Check if program is upgradeable:**
```bash
solana program show <PROGRAM_ID>

# Output shows:
# Program Id: <PROGRAM_ID>
# Owner: BPFLoaderUpgradeable1111111111111111111111111
# ProgramData Address: <DATA_ACCOUNT>
# Authority: <UPGRADE_AUTHORITY>  # If upgradeable
# Last Deployed In Slot: ...
# Data Length: ...
```

### Anchor Upgrades

**Upgrade deployed program:**
```bash
anchor upgrade target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  --provider.cluster devnet
```

**Note:** In newer Anchor versions, `anchor deploy` automatically upgrades if program exists.

**Upgrade with priority fees:**
```bash
anchor upgrade target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  --provider.cluster mainnet \
  -- --with-compute-unit-price 50000
```

### Native Rust Upgrades

**Upgrade using same deploy command:**
```bash
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  --upgrade-authority ~/.config/solana/id.json
```

### Extending Program Accounts

**Problem:** If new program is larger than allocated space:
```
Error: account data too small for instruction
```

**Solution:** Extend program account before upgrading:

```bash
# Check current program size
solana program show <PROGRAM_ID>
# Shows: Data Length: 363960 bytes

# New build is larger
NEW_SIZE=$(wc -c < target/deploy/my_program.so)
echo $NEW_SIZE
# Shows: 380000 bytes

# Calculate additional bytes needed
ADDITIONAL_BYTES=$((NEW_SIZE - 363960))
echo $ADDITIONAL_BYTES
# Shows: 16040 bytes

# Extend program account
solana program extend <PROGRAM_ID> $ADDITIONAL_BYTES

# Check rent cost for extension
solana rent $ADDITIONAL_BYTES
# Example: 0.2 SOL

# Now upgrade works
solana program deploy target/deploy/my_program.so --program-id <PROGRAM_ID>
```

**Note:** Program extension support added in Solana CLI v1.18+

### Data Migration Strategies

**Account structure changes:**

When upgrading programs that change account layouts:

**Option 1: Version field**
```rust
#[account]
pub struct MyAccount {
    pub version: u8,  // Add version field
    pub data: u64,
    // New fields in v2
    pub new_field: Option<String>,
}

// In instruction handler
if account.version == 1 {
    // Migrate from v1 to v2
    account.new_field = Some("default".to_string());
    account.version = 2;
}
```

**Option 2: Separate migration instruction**
```rust
pub fn migrate_account_v1_to_v2(ctx: Context<MigrateAccount>) -> Result<()> {
    let account = &mut ctx.accounts.account;

    // Perform migration logic
    account.new_field = compute_new_field(&account.data);
    account.version = 2;

    Ok(())
}
```

**Option 3: New program version with migration path**
- Deploy new program ID
- Create migration instructions that move data
- Deprecate old program gradually

---

## Verified Builds

Verified builds prove deployed bytecode matches public source code.

### Why Verify?

- **Transparency:** Users can audit your program's source
- **Trust:** Proves deployed program matches GitHub repository
- **Security:** Enables community security reviews
- **Ecosystem:** Explorers display verified status
- **Wallets:** May whitelist verified programs

### Tools for Verification

**Solana Verify CLI:**
```bash
cargo install solana-verify
```

**Docker (required for deterministic builds):**
- Install Docker: https://docs.docker.com/engine/install/
- Ensure Docker daemon is running

### Building Verifiable Programs

**Verifiable build process:**
```bash
# Navigate to project root (with Cargo.toml)
cd my-project

# Build in Docker container for deterministic output
solana-verify build

# For workspace with specific program
solana-verify build --library-name my_program

# Get hash of built executable
solana-verify get-executable-hash target/deploy/my_program.so
```

**What makes builds verifiable:**
1. **Docker environment:** Ensures consistent build environment
2. **Locked dependencies:** `Cargo.lock` pins exact versions
3. **Same toolchain:** Uses specific Rust/Solana version
4. **Deterministic compilation:** Same input → same output

**Project structure requirements:**

```
my-project/
├── Cargo.toml          # Workspace manifest
├── Cargo.lock          # Locked dependencies (required!)
├── programs/
│   └── my_program/
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs
```

**Workspace Cargo.toml example:**
```toml
[workspace]
members = ["programs/*"]
resolver = "2"

[workspace.dependencies]
solana-program = "2.1.0"

[profile.release]
overflow-checks = true
lto = "fat"
codegen-units = 1

[profile.release.build-override]
opt-level = 3
incremental = false
codegen-units = 1
```

### Deploying Verifiable Programs

**Deploy verified build:**
```bash
# IMPORTANT: Use the binary from solana-verify build
# DO NOT run `anchor build` or `cargo build-sbf` after verification build

# Deploy with priority fees for reliability
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  -u https://api.mainnet-beta.solana.com \
  --with-compute-unit-price 50000 \
  --max-sign-attempts 100 \
  --use-rpc
```

**Verify deployed program matches built executable:**
```bash
# Get on-chain program hash
solana-verify get-program-hash -u mainnet-beta <PROGRAM_ID>

# Get local executable hash
solana-verify get-executable-hash target/deploy/my_program.so

# Hashes must match!
```

### Verifying Against Repository

**Verify from GitHub repository:**
```bash
solana-verify verify-from-repo \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/your-repo \
  --commit-hash <COMMIT_HASH> \
  --library-name my_program \
  --mount-path programs/my_program
```

**Parameters explained:**
- `--program-id`: On-chain program address
- `--commit-hash`: Git commit to build from (optional, uses latest if omitted)
- `--library-name`: Crate name from Cargo.toml `[lib]` section
- `--mount-path`: Path to program directory in repo (for workspaces)

**Upload verification data on-chain:**

When prompted during verification:
```
Would you like to upload verification data on-chain? (y/n)
```

Select **yes** to write verification PDA. This enables:
- Solana Explorer verification badge
- OtterSec API verification
- SolanaFM verification display

### Remote Verification with OtterSec API

**Submit verification job:**
```bash
solana-verify verify-from-repo \
  --remote \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/your-repo
```

**Manual job submission:**
```bash
solana-verify remote submit-job \
  --program-id <PROGRAM_ID> \
  --uploader <UPGRADE_AUTHORITY>
```

**Check verification status:**
```bash
solana-verify remote get-job-status --job-id <JOB_ID>
```

**Verification API endpoint:**
```
https://verify.osec.io/status/<PROGRAM_ID>
```

**Where verified status appears:**
- [Solana Explorer](https://explorer.solana.com)
- [SolanaFM](https://solana.fm)
- [SolScan](https://solscan.io)
- [SolanaVerify.org](https://solanaverify.org)
- [OtterSec API](https://verify.osec.io/verified-programs)

### security.txt Integration

**Add security contact info:**

```rust
#[cfg(not(feature = "no-entrypoint"))]
solana_security_txt::security_txt! {
    name: "My Program",
    project_url: "https://myproject.com",
    contacts: "email:security@myproject.com,discord:myproject",
    policy: "https://github.com/myproject/security/blob/main/SECURITY.md",
    preferred_languages: "en",
    source_code: "https://github.com/myproject/program",
    source_release: "v1.0.0",
    auditors: "Audit Firm Name"
}
```

**Benefits:**
- Security researchers know how to contact you
- Shows commitment to security
- Standard across Solana ecosystem

---

## Program Authority Management

### Viewing Program Information

**Check program authority:**
```bash
solana program show <PROGRAM_ID>

# Output:
# Program Id: YourProgramId
# Owner: BPFLoaderUpgradeable1111111111111111111111111
# ProgramData Address: <DATA_ACCOUNT_ADDRESS>
# Authority: <CURRENT_AUTHORITY>  # Current upgrade authority
# Last Deployed In Slot: 123456789
# Data Length: 363960 bytes (0x58e38 bytes)
```

**View all your deployed programs:**
```bash
solana program show --programs

# Shows all programs where your wallet is authority
```

### Transferring Upgrade Authority

**Transfer to new authority:**
```bash
solana program set-upgrade-authority <PROGRAM_ID> \
  --new-upgrade-authority <NEW_AUTHORITY_PUBKEY>
```

**Common use cases:**
- Transfer to multisig (Squads Protocol)
- Transfer to governance program
- Transfer to team member
- Transfer to DAO

**Transfer to multisig (Squads):**
```bash
# Get Squads vault address from https://v4.squads.so/
SQUADS_VAULT="YourSquadsVaultAddress"

solana program set-upgrade-authority <PROGRAM_ID> \
  --new-upgrade-authority $SQUADS_VAULT
```

### Making Programs Immutable

**WARNING:** This is irreversible!

```bash
solana program set-upgrade-authority <PROGRAM_ID> --final

# Confirms immutability - program can NEVER be upgraded
```

**Use cases for immutability:**
- DeFi protocols requiring immutable guarantees
- After extensive auditing, lock the program
- Community trust through code permanence

**Considerations:**
- Cannot fix bugs after making immutable
- Cannot add features
- Ensure thorough testing and auditing first
- Consider governance/multisig instead

### Buffer Accounts for Deployment

**Understanding buffers:**

When deploying, the Solana CLI creates temporary buffer accounts:

1. Creates buffer account
2. Writes program data to buffer
3. Deploys buffer to program account
4. Closes buffer (if successful)

**View your buffer accounts:**
```bash
solana program show --buffers

# Output:
# Buffer Address                                | Authority                                      | Balance
# Abc123...                                     | YourWallet...                                  | 2.5 SOL
```

**Close buffer manually (failed deployment):**
```bash
solana program close <BUFFER_ADDRESS>

# Recovers rent SOL back to wallet
```

**Common scenarios:**
- Deployment failed mid-process
- Want to cancel deployment
- Need to reclaim SOL from old buffers

---

## Multisig Deployments

Deploying with multisig (Squads Protocol) provides security for production programs.

### Why Use Multisig?

- **Security:** No single point of failure
- **Governance:** Team/DAO approval for upgrades
- **Transparency:** On-chain approval trail
- **Best practice:** Standard for serious projects

### Workflow Overview

1. Build verifiable program
2. Deploy with temporary authority
3. Verify against repository
4. Transfer authority to multisig
5. Export PDA transaction for verification upload
6. Submit through Squads UI
7. Remote verification

### Detailed Multisig Deployment

**1. Build verifiable program:**
```bash
solana-verify build --library-name my_program
```

**2. Deploy with your wallet as initial authority:**
```bash
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  -u mainnet-beta \
  --with-compute-unit-price 50000
```

**3. Verify locally:**
```bash
solana-verify verify-from-repo \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/repo \
  --commit-hash <COMMIT>
```

**4. Transfer authority to Squads multisig:**

Get Squads vault address from https://v4.squads.so/

```bash
SQUADS_VAULT="YourSquadsVaultAddress"

solana program set-upgrade-authority <PROGRAM_ID> \
  --new-upgrade-authority $SQUADS_VAULT
```

**5. Export verification PDA transaction:**

```bash
solana-verify verify-from-repo \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/repo \
  --export-pda-tx verification_tx.json
```

**6. Submit transaction in Squads:**

- Go to https://v4.squads.so/
- Navigate to your multisig
- Create new transaction
- Import `verification_tx.json`
- Get approval from multisig members
- Execute transaction

**7. Submit remote verification:**

After Squads transaction executes:

```bash
solana-verify remote submit-job \
  --program-id <PROGRAM_ID> \
  --uploader <SQUADS_VAULT>
```

**8. Monitor verification:**

```bash
# Check job status
solana-verify remote get-job-status --job-id <JOB_ID>

# Or visit
https://verify.osec.io/status/<PROGRAM_ID>
```

### Upgrading via Multisig

**Create upgrade buffer:**
```bash
# Build new version
solana-verify build --library-name my_program

# Write to buffer (not direct upgrade)
solana program write-buffer target/deploy/my_program.so

# Output: Buffer address: <BUFFER_ADDRESS>
```

**Transfer buffer authority to multisig:**
```bash
solana program set-buffer-authority <BUFFER_ADDRESS> \
  --new-buffer-authority <SQUADS_VAULT>
```

**Create Squads transaction for upgrade:**

Use Squads CLI or UI to propose:
```bash
# Using Squads SDK/CLI
npx ts-node scripts/program-upgrade.ts \
  --rpc "https://api.mainnet-beta.solana.com" \
  --program "<PROGRAM_ID>" \
  --buffer "<BUFFER_ADDRESS>" \
  --multisig "<MULTISIG_ADDRESS>" \
  --member "<YOUR_PUBKEY>" \
  --name "Upgrade my_program v2"
```

**Close buffer via Squads (if needed):**
```bash
npx ts-node scripts/squad-closebuffer.ts \
  --rpc "https://api.mainnet-beta.solana.com" \
  --multisig "<MULTISIG_ADDRESS>" \
  --buffer "<BUFFER_ADDRESS>" \
  --program "<PROGRAM_ID>"
```

---

## Network-Specific Considerations

### Localhost Development

**Start test validator:**
```bash
# Basic
solana-test-validator

# With program pre-deployed
solana-test-validator --bpf-program <PROGRAM_ID> target/deploy/my_program.so

# With cloned mainnet accounts
solana-test-validator \
  --clone <ACCOUNT_ADDRESS> \
  --url mainnet-beta

# Reset ledger on restart
solana-test-validator --reset
```

**Deploy to local validator:**
```bash
# Anchor
anchor localnet  # Starts validator and deploys
# Or
anchor deploy --provider.cluster localnet

# Native Rust
solana program deploy target/deploy/my_program.so -ul
```

**Benefits:**
- Instant transaction confirmation
- Unlimited free SOL
- Full control over clock and state
- Fast iteration

**Limitations:**
- No network effects
- Single validator (no consensus)
- State doesn't persist (unless configured)

### Devnet Deployment

**Configure network:**
```bash
solana config set --url devnet
```

**Fund wallet:**
```bash
solana airdrop 2
# Repeat as needed, max 2 SOL per request
```

**Deploy:**
```bash
# Anchor
anchor deploy --provider.cluster devnet

# Native Rust
solana program deploy target/deploy/my_program.so \
  -u devnet \
  --with-compute-unit-price 1000
```

**Benefits:**
- Real network conditions
- Free SOL via airdrops
- Test integrations with other programs
- Longer-lived state than localnet

**Limitations:**
- Network resets occasionally
- Potential rate limiting
- Slower than localnet
- Public network (anyone can interact)

**Best practices:**
- Test all upgrade paths on devnet first
- Monitor transaction success rates
- Test with realistic compute budgets
- Validate against cloned mainnet accounts

### Testnet Deployment

Testnet is less commonly used but available for staging:

```bash
solana config set --url testnet
solana airdrop 2  # If available
```

**Use cases:**
- Staging environment before mainnet
- Testing between devnet and mainnet
- Longer-term testing without mainnet costs

### Mainnet Deployment

**Pre-deployment checklist:**
- [ ] Thoroughly tested on devnet
- [ ] Security audit completed (for DeFi/high-value programs)
- [ ] Verified build prepared
- [ ] Upgrade authority configured (multisig recommended)
- [ ] Sufficient SOL for deployment (check `solana rent`)
- [ ] Monitoring/alerting setup
- [ ] Rollback plan documented
- [ ] Team coordination for deployment time

**Configure mainnet:**
```bash
solana config set --url mainnet-beta

# Use paid RPC for reliability (recommended)
solana config set --url https://your-rpc-provider.com
```

**Fund wallet:**
```bash
# Transfer from exchange or another wallet
# Calculate needed SOL:
PROGRAM_SIZE=$(wc -c < target/deploy/my_program.so)
solana rent $PROGRAM_SIZE
# Add ~0.5 SOL buffer for transaction fees and priority fees
```

**Deploy with appropriate priority fees:**

Check current priority fee recommendations:
- https://www.quicknode.com/gas-tracker/solana
- https://solanacompass.com/gas-fees

```bash
# Typical priority fee: 50,000-300,000 micro-lamports per CU
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  -u mainnet-beta \
  --with-compute-unit-price 100000 \
  --max-sign-attempts 100 \
  --use-rpc
```

**Post-deployment verification:**
```bash
# Verify deployment
solana program show <PROGRAM_ID> -u mainnet-beta

# Verify hash matches
solana-verify get-program-hash -u mainnet-beta <PROGRAM_ID>

# Submit verification job
solana-verify verify-from-repo \
  --remote \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/repo
```

**Cost considerations:**
- 200KB program: ~1.5 SOL
- 500KB program: ~3.5 SOL
- 800KB program: ~5.5 SOL
- Plus transaction fees: ~0.01-0.05 SOL
- Priority fees during congestion: +0.1-1 SOL

---

## Post-Deployment

### Verifying Deployment Success

**Check program was deployed:**
```bash
solana program show <PROGRAM_ID>

# Verify output shows:
# - Correct ProgramData address
# - Your authority
# - Expected data length
# - Recent slot number
```

**Compare program hash:**
```bash
# On-chain hash
solana-verify get-program-hash -u <NETWORK> <PROGRAM_ID>

# Local build hash
solana-verify get-executable-hash target/deploy/my_program.so

# Must match exactly
```

### Testing On-Chain

**Anchor:**
```bash
# Run tests against deployed program
anchor test --skip-deploy --provider.cluster devnet

# Or run specific test
anchor run test-on-devnet
```

**Native Rust / TypeScript client (Anchor - requires legacy `@solana/web3.js` v1):**
```typescript
import { Connection, PublicKey } from '@solana/web3.js';

const connection = new Connection('https://api.devnet.solana.com');
const programId = new PublicKey('YourProgramId');

// Send test transaction
const tx = await program.methods
  .yourInstruction()
  .accounts({ /* ... */ })
  .rpc();

console.log('Transaction:', tx);
```

**Smoke tests:**
- Call each instruction with valid inputs
- Verify account state changes
- Check events are emitted correctly
- Test error cases return expected errors

### Monitoring Program Usage

**View recent transactions:**
```bash
# Get recent transactions for program
solana transaction-history <PROGRAM_ID> --limit 10

# Or use explorers:
# https://explorer.solana.com/address/<PROGRAM_ID>
# https://solscan.io/account/<PROGRAM_ID>
```

**Set up monitoring:**

Use services like:
- [Helius webhooks](https://www.helius.dev/)
- [QuickNode functions](https://www.quicknode.com/)
- [SolanaFM API](https://solana.fm/)

**Monitor for:**
- Transaction success rate
- Compute unit usage
- Error frequency
- Unusual activity patterns

### Publishing IDL (Anchor)

**Upload IDL to on-chain account:**
```bash
anchor idl init <PROGRAM_ID> \
  --filepath target/idl/my_program.json \
  --provider.cluster devnet
```

**Upgrade IDL after program upgrade:**
```bash
anchor idl upgrade <PROGRAM_ID> \
  --filepath target/idl/my_program.json \
  --provider.cluster devnet
```

**Fetch published IDL:**
```bash
anchor idl fetch <PROGRAM_ID> \
  --provider.cluster devnet \
  --out fetched_idl.json
```

**Benefits of publishing IDL:**
- Clients can auto-discover your interface
- Explorers can decode instructions
- Reduces integration friction
- Standard for Anchor programs

### Closing Programs and Reclaiming SOL

**Close buffer accounts:**
```bash
# View all buffers
solana program show --buffers

# Close specific buffer
solana program close <BUFFER_ADDRESS>

# Reclaims rent SOL to wallet
```

**Close entire program (irreversible!):**
```bash
solana program close <PROGRAM_ID>

# WARNING: This deletes the program permanently
# Cannot be undone
# Only do this for test programs
```

**When to close:**
- Failed test deployments on devnet
- Obsolete test programs
- Reclaim SOL from old projects

**When NOT to close:**
- Any program with active users
- Programs other contracts depend on
- Mainnet programs (almost never)

---

## Common Issues and Troubleshooting

### Insufficient Balance

**Error:**
```
Error: Account <WALLET> has insufficient funds for spend (1.5 SOL) + fee (0.002 SOL)
```

**Solution:**
```bash
# Check current balance
solana balance

# Devnet - request airdrop
solana airdrop 2

# Mainnet - transfer SOL
# Calculate needed amount:
PROGRAM_SIZE=$(wc -c < target/deploy/my_program.so)
solana rent $PROGRAM_SIZE
# Add 0.5 SOL buffer
```

### Program Too Large

**Error:**
```
Error: Program too large. Maximum size: 1048576 bytes
```

**Solutions:**

**1. Optimize build:**
```toml
[profile.release]
lto = "fat"
codegen-units = 1
opt-level = "z"  # Optimize for size
strip = true
```

**2. Remove unused dependencies:**
```bash
cargo tree  # Identify large dependencies
```

**3. Use feature flags to exclude optional code:**
```toml
[dependencies]
solana-program = { version = "2.1.0", default-features = false }
```

**4. Split program into multiple programs:**
- Separate complex logic into multiple programs
- Use CPI to communicate between them

### Account Data Too Small for Instruction

**Error:**
```
Error: account data too small for instruction
```

**Cause:** Upgrade would exceed allocated program size.

**Solution:**
```bash
# Check current size
solana program show <PROGRAM_ID>
# Data Length: 363960 bytes

# Check new size
NEW_SIZE=$(wc -c < target/deploy/my_program.so)
echo $NEW_SIZE
# 380000 bytes

# Calculate difference
DIFF=$((NEW_SIZE - 363960))

# Extend program
solana program extend <PROGRAM_ID> $DIFF

# Check rent for extension
solana rent $DIFF

# Now deploy upgrade
solana program deploy target/deploy/my_program.so --program-id <PROGRAM_ID>
```

### Network Congestion / Blockhash Expiration

**Error:**
```
Error: Transaction simulation failed: Blockhash not found
```

**Cause:** High network congestion or large program deployment.

**Solutions:**

**1. Increase priority fees:**
```bash
solana program deploy target/deploy/my_program.so \
  --with-compute-unit-price 300000 \  # Higher priority
  --max-sign-attempts 100 \
  --use-rpc
```

**2. Use paid RPC endpoint:**
```bash
solana config set --url https://your-premium-rpc.com

# Paid RPCs often have:
# - Higher rate limits
# - Better transaction success rates
# - Priority queue access
```

**3. Deploy during low traffic:**
- Avoid peak hours (US/Europe daytime)
- Early morning UTC often less congested

**4. Break into smaller chunks:**

For very large programs, manually create buffer and write in batches.

### Keypair Issues

**Error:**
```
Error: Dynamic program error: Invalid keypair file
```

**Solutions:**

**1. Verify keypair format:**
```bash
# Should be JSON array of numbers
cat program-keypair.json
# [123, 45, 67, ...]

# Or base58 string
```

**2. Regenerate if corrupted:**
```bash
solana-keygen new -o program-keypair.json --force
```

**3. Check file permissions:**
```bash
chmod 600 program-keypair.json
```

### Anchor Build vs Deploy Mismatch

**Error:**
```
Error: Program <ID> does not match declared program id in lib.rs
```

**Solution:**
```bash
# Sync program IDs
anchor keys sync

# Rebuilds and updates declare_id! to match keypair
```

### Native Rust: Missing Program ID

**Error:**
```
Error: No program keypair found
```

**Solution:**

Native Rust doesn't auto-generate keypairs. Either:

**Option 1: Create keypair:**
```bash
solana-keygen new -o target/deploy/my_program-keypair.json
solana program deploy target/deploy/my_program.so \
  --program-id target/deploy/my_program-keypair.json
```

**Option 2: Use existing program ID:**
```bash
solana program deploy target/deploy/my_program.so \
  --program-id <EXISTING_PROGRAM_ID>
```

### Verification Failures

**Error:**
```
Verification failed: Hash mismatch
On-chain: abc123...
Local: def456...
```

**Causes and solutions:**

**1. Built outside Docker:**
```bash
# Must use solana-verify build for deterministic build
solana-verify build
```

**2. Cargo.lock mismatch:**
```bash
# Ensure Cargo.lock committed to git
git add Cargo.lock
git commit -m "Add Cargo.lock for verifiable builds"
```

**3. Rebuild after verification:**
```bash
# Don't run `anchor build` or `cargo build-sbf` after solana-verify build
# This regenerates binary with different hash

# If you did, rebuild verifiably:
solana-verify build
solana program deploy target/deploy/my_program.so --program-id <PROGRAM_ID>
```

**4. Wrong commit hash:**
```bash
# Ensure you're verifying against correct commit
git log  # Find exact commit used for deployment
solana-verify verify-from-repo \
  --commit-hash <EXACT_COMMIT> \
  ...
```

---

## Best Practices

### Deployment Workflow

**Recommended deployment process:**

1. **Local development**
   - Develop on localnet
   - Unit test with Mollusk (native) or Bankrun/Anchor tests
   - Iterate quickly

2. **Devnet testing**
   - Deploy to devnet
   - Integration testing
   - Test upgrade paths
   - Load testing if applicable

3. **Devnet verification**
   - Build verifiable
   - Deploy and verify on devnet
   - Ensure verification succeeds

4. **Security review**
   - Internal code review
   - Automated analysis (Soteria, Sec3, etc.)
   - Professional audit (for mainnet)

5. **Mainnet staging**
   - Build final verifiable version
   - Generate program ID
   - Set up multisig/governance

6. **Mainnet deployment**
   - Deploy during low-traffic period
   - Use paid RPC
   - Set appropriate priority fees
   - Monitor closely

7. **Post-deployment**
   - Submit verification
   - Smoke test critical functions
   - Set up monitoring
   - Transfer authority to multisig

### Version Control

**Always commit:**
- `Cargo.lock` (required for verified builds)
- Program keypairs (for test programs only)
- IDL files
- Migration scripts

**Never commit:**
- Mainnet keypairs (use environment variables)
- Wallet private keys
- RPC API keys

**Tag deployments:**
```bash
git tag -a v1.0.0-mainnet -m "Mainnet deployment v1.0.0"
git push origin v1.0.0-mainnet
```

**Link verification to tags:**
```bash
solana-verify verify-from-repo \
  --commit-hash v1.0.0-mainnet \
  ...
```

### Backup Strategies

**Critical to back up:**

1. **Program keypairs**
   ```bash
   # Mainnet program keypairs
   cp target/deploy/my_program-keypair.json ~/secure-backup/

   # Encrypted backup
   gpg -c target/deploy/my_program-keypair.json
   ```

2. **Upgrade authority keypairs**
   ```bash
   # If not using multisig
   cp ~/.config/solana/id.json ~/secure-backup/upgrade-authority.json
   ```

3. **Buffer accounts during deployment**
   ```bash
   # Save buffer address immediately after creating
   echo "Buffer: <ADDRESS>" >> deployment-log.txt
   ```

4. **Deployment artifacts**
   - Built .so files
   - IDL files
   - Verification data
   - Transaction signatures

**Backup locations:**
- Encrypted cloud storage (Google Drive, Dropbox)
- Hardware wallet (for keypairs)
- Offline USB drives (encrypted)
- Team password manager (1Password, Bitwarden)

**Test backup restoration:**
```bash
# Periodically verify backups work
cp ~/secure-backup/my_program-keypair.json /tmp/test-restore.json
solana-keygen pubkey /tmp/test-restore.json
# Should output expected program ID
```

### Framework-Specific Best Practices

**Anchor:**
- Always run `anchor keys sync` after first build
- Keep `Anchor.toml` in source control
- Use workspace for multi-program projects
- Upload IDL on-chain for discoverability
- Version your IDL files alongside code

**Native Rust:**
- Use `no-entrypoint` feature for testing
- Implement security.txt for contact info
- Document your instruction format
- Provide client SDK (TypeScript/Rust) for integrations
- Include example transaction builders

### Testing Before Deployment

**Progressive testing strategy:**

```bash
# 1. Unit tests (Mollusk for native, Anchor tests)
cargo test

# 2. Integration tests on localnet
anchor test  # or cargo test-sbf

# 3. Devnet deployment test
anchor deploy --provider.cluster devnet
# Test all functions on devnet

# 4. Upgrade test on devnet
# Make small change, rebuild, upgrade
anchor build
anchor upgrade <PROGRAM_ID> target/deploy/program.so --provider.cluster devnet
# Verify upgrade worked

# 5. Verified build test
solana-verify build
solana-verify verify-from-repo --program-id <DEVNET_ID> https://github.com/...

# 6. Final smoke tests on devnet
# Run critical user flows

# 7. Mainnet deployment
# Only after all above pass
```

### Documentation

**Document your deployment:**

Create `DEPLOYMENT.md` in your repo:

```markdown
# Deployment Guide

## Program IDs

- Devnet: ABC123...
- Mainnet: DEF456...

## Build

```bash
solana-verify build --library-name my_program
```

## Deploy

### Devnet
```bash
anchor deploy --provider.cluster devnet
```

### Mainnet
```bash
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  -u mainnet-beta \
  --with-compute-unit-price 100000
```

## Verify

```bash
solana-verify verify-from-repo \
  --remote \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/repo \
  --commit-hash v1.0.0
```

## Upgrade Authority

Mainnet: Squads Multisig `GHI789...`

## Last Deployment

- Date: 2025-01-15
- Version: v1.0.0
- Commit: abc123def456
- Deployed by: @deployer
- Verification: https://verify.osec.io/status/<PROGRAM_ID>
```

---

## Summary

**Key takeaways:**

1. **Always test on devnet first** - Never deploy untested code to mainnet
2. **Use verified builds for mainnet** - Transparency builds trust
3. **Calculate costs before deploying** - Use `solana rent` to estimate
4. **Set up multisig for mainnet** - Prevents single points of failure
5. **Monitor after deployment** - Watch for errors and unusual activity
6. **Back up keypairs** - Lose keypair = lose upgrade authority
7. **Document your deployments** - Future you will thank you
8. **Use priority fees on mainnet** - Ensures reliable deployment
9. **Test upgrade paths** - Practice on devnet first
10. **Never make programs immutable hastily** - Irreversible decision

**Resources:**
- Solana CLI docs: https://docs.solana.com/cli
- Anchor docs: https://www.anchor-lang.com/
- Solana Verify: https://github.com/Ellipsis-Labs/solana-verifiable-build
- OtterSec Verify API: https://verify.osec.io/
- Squads Protocol: https://squads.so/
- Security.txt: https://github.com/neodyme-labs/solana-security-txt

Deploy with confidence!
