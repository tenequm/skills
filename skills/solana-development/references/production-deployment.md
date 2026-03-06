# Production Deployment Guide for Solana Programs

**Best practices for deploying verified, production-ready Solana programs to mainnet and serious devnet environments.**

---

## Overview

Production deployments require verified builds that prove deployed bytecode matches public source code. This guide covers the proper workflow for production deployments, particularly with Anchor framework.

**Key principle:** Transparency and verifiability build trust. Always use deterministic builds for production.

---

## Why Verified Builds Matter

**Without verified builds:**
- Users cannot verify deployed code matches GitHub source
- Audits cannot confirm they reviewed the exact deployed binary
- No transparency into what code actually runs on-chain
- Security researchers cannot validate the program

**With verified builds:**
- ✅ Provably deterministic builds (Docker-based)
- ✅ Anyone can verify deployed bytecode matches source
- ✅ Explorer verification badges (Solana Explorer, SolanaFM)
- ✅ Audit reports apply to exact deployed binary
- ✅ Standard for all serious Solana projects

**All major Solana protocols use verified builds:** Jupiter, Marinade, Orca, Metaplex, etc.

---

## The Problem with `anchor deploy`

### Anchor 0.32.1 and Earlier

**⚠️ CRITICAL: Do NOT use `anchor deploy` for production deployments**

**Why `anchor deploy` is unsuitable for production:**

1. **Non-deterministic builds**
   - Build output varies by local Rust version
   - Different on macOS vs Linux
   - Depends on installed toolchain
   - Same source → different binaries on different machines

2. **Cannot be verified**
   - No way to prove deployed code matches GitHub
   - Verification tools cannot reproduce the build
   - Breaks audit trail

3. **Lacks transparency**
   - Users must trust deployer
   - No verification badges on explorers
   - Goes against Solana ecosystem standards

**When Anchor v1 may improve this:**
- Anchor v1 is expected to have better support for verified builds
- May integrate `solana-verify` directly
- Check Anchor docs for updates when v1 releases

**For now (Anchor 0.32.1):** Use the verified deployment workflow below.

---

## Production Deployment Workflow

### Step 1: Build Verifiably

Use `solana-verify build` instead of `anchor build` for the final production build:

```bash
# Install solana-verify if not already installed
cargo install solana-verify

# Navigate to project root (where Cargo.toml with workspace is)
cd my-project

# Build verifiably in Docker (deterministic)
solana-verify build --library-name my_program

# Verify the build succeeded
ls -la target/deploy/my_program.so
```

**What this does:**
- Builds in Docker container (consistent environment)
- Uses exact dependencies from `Cargo.lock`
- Same input → same output (deterministic)
- Anyone can reproduce this exact binary

**Important:** Do NOT run `anchor build` after `solana-verify build` - it will regenerate a different binary!

### Step 2: Deploy the Verified Binary

Use `solana program deploy` directly (NOT `anchor deploy`):

**For devnet:**
```bash
solana program deploy target/deploy/my_program.so \
  --program-id target/deploy/my_program-keypair.json \
  -u devnet \
  --with-compute-unit-price 1000
```

**For mainnet:**
```bash
# Use your deployer keypair and appropriate priority fees
solana program deploy target/deploy/my_program.so \
  --program-id target/deploy/my_program-keypair.json \
  --keypair ~/.config/solana/deployer.json \
  -u mainnet-beta \
  --with-compute-unit-price 100000 \
  --max-sign-attempts 100 \
  --use-rpc
```

**Why use `solana program deploy` directly:**
- Works with verified builds
- More control over deployment parameters
- Standard across all Solana programs
- Same tool for Anchor and native Rust

### Step 3: Verify Against Repository

After deployment, verify the on-chain program matches your source:

```bash
solana-verify verify-from-repo \
  -u devnet \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/your-repo \
  --library-name my_program

# Or specify exact commit
solana-verify verify-from-repo \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/your-repo \
  --commit-hash <COMMIT_HASH> \
  --library-name my_program
```

**When prompted, upload verification data on-chain:**
```
Would you like to upload verification data on-chain? (y/n)
```

Select **yes** to enable:
- Verification badge on Solana Explorer
- OtterSec verification API listing
- SolanaFM verification display

### Step 4: Verify Hash Match (Sanity Check)

Before step 3, you can manually verify hashes match:

```bash
# Get on-chain program hash
solana-verify get-program-hash -u devnet <PROGRAM_ID>

# Get local executable hash
solana-verify get-executable-hash target/deploy/my_program.so

# These MUST match exactly
```

---

## Complete Production Deployment Checklist

### Pre-Deployment

- [ ] All tests pass (`cargo test`, `anchor test`)
- [ ] Security audit completed (for mainnet)
- [ ] `Cargo.lock` committed to git
- [ ] Git tag created for release (e.g., `v1.0.0`)
- [ ] Sufficient SOL in deployer wallet
- [ ] Multisig or governance ready (mainnet)

### Build

- [ ] Run `solana-verify build --library-name my_program`
- [ ] Verify `.so` file exists in `target/deploy/`
- [ ] Do NOT run `anchor build` after this
- [ ] Get hash: `solana-verify get-executable-hash target/deploy/my_program.so`

### Deploy

- [ ] Use `solana program deploy` (NOT `anchor deploy`)
- [ ] Specify correct program ID keypair
- [ ] Use appropriate priority fees
- [ ] Verify deployment: `solana program show <PROGRAM_ID>`

### Verify

- [ ] Run `solana-verify verify-from-repo` with your GitHub URL
- [ ] Upload verification data on-chain when prompted
- [ ] Check verification appears on explorer
- [ ] Optional: Submit remote verification job

### Post-Deployment

- [ ] Transfer upgrade authority to multisig (mainnet)
- [ ] Smoke test critical instructions on-chain
- [ ] Set up monitoring
- [ ] Announce deployment with verification link

---

## Example: Complete Mainnet Deployment

```bash
# 1. Prepare
git tag v1.0.0
git push origin v1.0.0

# 2. Build verifiably
solana-verify build --library-name cascade_splits

# 3. Check hash
solana-verify get-executable-hash target/deploy/cascade_splits.so
# Output: abc123def456...

# 4. Deploy to mainnet
solana program deploy target/deploy/cascade_splits.so \
  --program-id target/deploy/cascade_splits-keypair.json \
  --keypair ~/.config/solana/mainnet-deployer.json \
  -u mainnet-beta \
  --with-compute-unit-price 100000 \
  --max-sign-attempts 100 \
  --use-rpc

# Output: Program Id: SPL1T3rERcu6P6dyBiG7K8LUr21CssZqDAszwANzNMB

# 5. Verify on-chain hash matches
solana-verify get-program-hash -u mainnet-beta SPL1T3rERcu6P6dyBiG7K8LUr21CssZqDAszwANzNMB
# Output: abc123def456... (must match step 3!)

# 6. Verify against repository
solana-verify verify-from-repo \
  -u mainnet-beta \
  --program-id SPL1T3rERcu6P6dyBiG7K8LUr21CssZqDAszwANzNMB \
  https://github.com/cascade-protocol/splits \
  --commit-hash v1.0.0 \
  --library-name cascade_splits

# When prompted: Upload verification data on-chain? → YES

# 7. Transfer authority to multisig
SQUADS_VAULT="YourSquadsVaultAddress"
solana program set-upgrade-authority SPL1T3rERcu6P6dyBiG7K8LUr21CssZqDAszwANzNMB \
  --new-upgrade-authority $SQUADS_VAULT

# 8. Verify on explorer
# Visit: https://explorer.solana.com/address/SPL1T3rERcu6P6dyBiG7K8LUr21CssZqDAszwANzNMB
# Should show verification badge

# 9. Check OtterSec verification
# Visit: https://verify.osec.io/status/SPL1T3rERcu6P6dyBiG7K8LUr21CssZqDAszwANzNMB
```

---

## Program Upgrades with Verified Builds

### Upgrade Workflow

```bash
# 1. Make changes, test, commit
git add .
git commit -m "feat: add new feature"
git tag v1.1.0
git push origin main v1.1.0

# 2. Build verifiably
solana-verify build --library-name my_program

# 3. Check if program size increased
OLD_SIZE=$(solana program show <PROGRAM_ID> | grep "Data Length" | awk '{print $3}')
NEW_SIZE=$(wc -c < target/deploy/my_program.so)

# 4. Extend if needed
if [ $NEW_SIZE -gt $OLD_SIZE ]; then
  DIFF=$((NEW_SIZE - OLD_SIZE))
  solana program extend <PROGRAM_ID> $DIFF
fi

# 5. Deploy upgrade
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID> \
  --upgrade-authority ~/.config/solana/deployer.json \
  -u mainnet-beta \
  --with-compute-unit-price 100000

# 6. Verify new version
solana-verify verify-from-repo \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/your-repo \
  --commit-hash v1.1.0 \
  --library-name my_program
```

### Upgrades via Multisig

If upgrade authority is a Squads multisig:

```bash
# 1. Build verifiably
solana-verify build --library-name my_program

# 2. Create buffer (not direct upgrade)
solana program write-buffer target/deploy/my_program.so
# Output: Buffer: <BUFFER_ADDRESS>

# 3. Transfer buffer to multisig
solana program set-buffer-authority <BUFFER_ADDRESS> \
  --new-buffer-authority <SQUADS_VAULT>

# 4. Create upgrade proposal in Squads UI
# - Navigate to https://v4.squads.so/
# - Create transaction for BPF Upgradeable Loader upgrade
# - Reference buffer address
# - Get approval from multisig members
# - Execute

# 5. After execution, verify
solana-verify verify-from-repo \
  -u mainnet-beta \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/your-repo \
  --commit-hash v1.1.0 \
  --library-name my_program
```

---

## Troubleshooting

### Hash Mismatch After Deployment

**Problem:** On-chain hash doesn't match local hash

**Causes:**
1. Ran `anchor build` or `cargo build-sbf` after `solana-verify build`
2. Deployed wrong file
3. `Cargo.lock` not committed or out of sync

**Solution:**
```bash
# 1. Clean everything
cargo clean

# 2. Ensure Cargo.lock is committed
git add Cargo.lock
git commit -m "Add Cargo.lock"

# 3. Rebuild verifiably
solana-verify build --library-name my_program

# 4. Redeploy
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID>

# 5. Verify again
solana-verify verify-from-repo ...
```

### Verification Fails: "Could not build from repository"

**Problem:** `solana-verify verify-from-repo` cannot build

**Causes:**
1. Missing `Cargo.lock` in repository
2. Wrong commit hash
3. Workspace configuration issue
4. Missing dependencies in Docker build

**Solution:**
```bash
# 1. Verify Cargo.lock exists in git
git ls-files | grep Cargo.lock

# 2. Check commit hash is correct
git log --oneline

# 3. Ensure workspace Cargo.toml exists at root
cat Cargo.toml  # Should have [workspace]

# 4. Try local verification first
solana-verify verify-from-repo \
  --program-id <PROGRAM_ID> \
  file://$(pwd) \
  --library-name my_program
```

### "anchor deploy" Used by Accident

**Problem:** Deployed with `anchor deploy` instead of verified build

**Solution:** Redeploy properly:
```bash
# 1. Build verifiably
solana-verify build --library-name my_program

# 2. Redeploy (upgrade) with verified binary
solana program deploy target/deploy/my_program.so \
  --program-id <PROGRAM_ID>

# 3. Verify
solana-verify verify-from-repo \
  -u <NETWORK> \
  --program-id <PROGRAM_ID> \
  https://github.com/your-org/your-repo
```

---

## Version-Specific Notes

### Anchor 0.32.1

- **Status:** Current stable version as of November 2024
- **Issue:** `anchor deploy` does not produce verifiable builds
- **Workaround:** Use workflow in this guide (solana-verify + solana program deploy)
- **Uses:** Solana SDK 2.2.x

### Anchor 0.30.x

- **Status:** Older stable version
- **Issue:** Same as 0.32.1
- **Workaround:** Same workflow applies
- **Uses:** Solana SDK 2.1.x

### Future: Anchor 1.0.0

- **Expected:** Better integration with verified builds
- **Possible:** `anchor deploy --verifiable` flag
- **Check:** Official Anchor docs when v1 releases
- **Until then:** Use this guide

---

## Best Practices Summary

### Always ✅

- Use `solana-verify build` for production builds
- Commit `Cargo.lock` to git
- Tag releases with git tags
- Deploy with `solana program deploy` directly
- Verify against repository after deployment
- Upload verification data on-chain
- Transfer mainnet authority to multisig
- Test entire flow on devnet first

### Never ❌

- Use `anchor deploy` for production/mainnet
- Run `anchor build` or `cargo build-sbf` after `solana-verify build`
- Deploy without verifying
- Deploy mainnet without devnet testing first
- Deploy mainnet without security audit
- Keep upgrade authority as individual wallet (mainnet)
- Skip uploading verification data

### Development Only

`anchor deploy` is fine for:
- Local validator testing
- Rapid iteration during development
- Devnet experiments
- Non-production testing

---

## Additional Resources

- **Solana Verify CLI**: https://github.com/Ellipsis-Labs/solana-verifiable-build
- **Verified Programs List**: https://verify.osec.io/verified-programs
- **Solana Explorer**: https://explorer.solana.com
- **Squads Protocol**: https://squads.so
- **Anchor Documentation**: https://www.anchor-lang.com/docs

---

## Summary

**For production Solana program deployments:**

1. Use `solana-verify build` (NOT `anchor deploy`)
2. Deploy with `solana program deploy` directly
3. Verify with `solana-verify verify-from-repo`
4. Upload verification data on-chain

This ensures transparency, verifiability, and trust in your deployed programs.
