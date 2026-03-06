# Durable Transaction Nonces

This guide covers Solana's durable transaction nonces, which enable transactions to remain valid indefinitely by replacing the time-limited recent blockhash mechanism. Essential for offline signing, multi-signature coordination, and scheduled transaction execution.

## Introduction

### The Expiration Problem

Solana transactions normally include a `recent_blockhash` field that serves two purposes:
1. **Double-spend prevention**: Ensures each transaction is unique and can only be processed once
2. **Transaction freshness**: Limits transaction validity to prevent spam and stale transactions

**The limitation:**
- Recent blockhashes expire after **150 blocks** (~60-90 seconds)
- Transactions with expired blockhashes are permanently rejected
- Cannot be re-validated, even with identical content

**Critical constraint:**
```
Transaction must be:
1. Signed with recent blockhash
2. Submitted to network
3. Processed by validator
4. Confirmed in block

All within ~60-90 seconds!
```

### Problems This Creates

**Hardware Wallet Users:**
- Fetch blockhash from network
- Transfer to air-gapped device
- User reviews and signs (can take minutes)
- Transfer back to online device
- Submit to network
- **Risk**: Blockhash expires during manual review

**Multi-Signature Wallets (DAOs, Squads, Realms):**
- Create transaction with blockhash
- Send to signer 1 for approval (hours/days)
- Send to signer 2 for approval (hours/days)
- Send to signer N for approval
- **Risk**: Blockhash expires while collecting signatures

**Scheduled Transactions:**
- Want to pre-sign transaction for future execution
- E.g., vesting unlock, scheduled payment, conditional trade
- **Risk**: Cannot pre-sign hours/days in advance

**Cross-Chain Bridges:**
- Wait for finality on source chain (minutes/hours)
- Sign transaction on destination chain
- **Risk**: Blockhash expires during cross-chain confirmation

### The Solution: Durable Nonces

Durable nonces replace `recent_blockhash` with a **stored on-chain value** that:
- ✅ Never expires (remains valid indefinitely)
- ✅ Changes with each use (prevents replay attacks)
- ✅ Enables offline signing without time pressure
- ✅ Supports multi-signature coordination
- ✅ Allows pre-signing transactions for future execution

**Key insight**: Instead of using the blockchain's recent history (blockhashes) to ensure uniqueness, durable nonces use a **dedicated account** that stores a nonce value and advances it after each transaction.

## How Durable Nonces Work

### Core Mechanism

1. **Nonce Account**: On-chain account (owned by System Program) storing a 32-byte nonce value
2. **Transaction Structure**: Use nonce value as `recent_blockhash` field
3. **Nonce Advancement**: First instruction MUST advance the nonce to prevent replay
4. **Authority Control**: Only nonce authority can advance nonce or authorize transactions

### Transaction Flow

```
Normal Transaction:
1. Fetch recent blockhash (expires in 90s)
2. Build transaction with blockhash
3. Sign transaction
4. Submit (must be within 90s)
5. Process and confirm

Durable Nonce Transaction:
1. Create nonce account (one-time setup)
2. Fetch current nonce value (no expiration!)
3. Build transaction with nonce as blockhash
4. Add advance_nonce instruction (MUST be first)
5. Sign transaction (no time pressure)
6. Submit anytime (minutes, hours, days later)
7. Process: advances nonce, executes instructions
```

### Double-Spend Prevention

**Without expiration, how does it prevent double-spending?**

The nonce value **changes** after each transaction:
```rust
// Transaction 1 with nonce value "ABC123..."
{
    recent_blockhash: "ABC123...",  // Current nonce value
    instructions: [
        advance_nonce_account(...),  // Changes nonce to "XYZ789..."
        transfer(...),
    ]
}

// If you try to submit Transaction 1 again:
// Runtime checks: Is "ABC123..." the current nonce?
// NO! It's now "XYZ789..."
// Transaction REJECTED (nonce mismatch)
```

**Critical**: The runtime **always** advances the nonce, even if the transaction fails after the advance instruction. This prevents replay attacks.

## Nonce Account Structure

### Account Layout

Nonce accounts are owned by the System Program and have this structure:

```rust
pub struct NonceState {
    pub version: NonceVersion,
}

pub enum NonceVersion {
    Legacy(Box<NonceData>),
    Current(Box<NonceData>),
}

pub struct NonceData {
    pub authority: Pubkey,         // Who can authorize nonce operations
    pub durable_nonce: Hash,       // The actual nonce value (32 bytes)
    pub fee_calculator: FeeCalculator,  // Historic fee data
}
```

**Account requirements:**
- **Owner**: System Program (`11111111111111111111111111111111`)
- **Size**: 80 bytes
- **Rent exemption**: Required (minimum ~0.00144768 SOL)
- **Authority**: Can be any pubkey (keypair or PDA)

### Nonce Authority

The authority pubkey controls the nonce account:
- **Can**: Advance nonce, withdraw funds, authorize nonce transactions, change authority
- **Cannot**: Execute other instructions without nonce advancement (runtime enforces this)

**Authority options:**
- **Keypair**: Direct control (hot wallet, cold wallet)
- **PDA**: Program-controlled nonces (advanced use case)
- **Multisig**: Multiple signers required (DAO wallets)

## Creating Nonce Accounts

### Using Native Rust

```rust
use solana_sdk::{
    instruction::Instruction,
    pubkey::Pubkey,
    signature::{Keypair, Signer},
    system_instruction,
    sysvar::rent::Rent,
    transaction::Transaction,
};
use solana_client::rpc_client::RpcClient;

fn create_nonce_account(
    rpc_client: &RpcClient,
    payer: &Keypair,
    nonce_account: &Keypair,
    authority: &Pubkey,
) -> Result<(), Box<dyn std::error::Error>> {
    // Calculate rent-exempt balance for nonce account
    let rent = rpc_client.get_minimum_balance_for_rent_exemption(80)?;

    // Create account instruction
    let create_account_ix = system_instruction::create_account(
        &payer.pubkey(),
        &nonce_account.pubkey(),
        rent,                     // Lamports (rent-exempt minimum)
        80,                       // Space (nonce account size)
        &solana_program::system_program::id(),  // Owner (System Program)
    );

    // Initialize nonce instruction
    let initialize_nonce_ix = system_instruction::initialize_nonce_account(
        &nonce_account.pubkey(),
        authority,                // Nonce authority
    );

    // Build transaction
    let recent_blockhash = rpc_client.get_latest_blockhash()?;
    let transaction = Transaction::new_signed_with_payer(
        &[create_account_ix, initialize_nonce_ix],
        Some(&payer.pubkey()),
        &[payer, nonce_account],  // Both payer and nonce account must sign
        recent_blockhash,
    );

    // Send transaction
    let signature = rpc_client.send_and_confirm_transaction(&transaction)?;
    println!("Created nonce account: {}", signature);

    Ok(())
}
```

### Single-Step Creation

There's also a convenience function that combines both steps:

```rust
let instruction = system_instruction::create_nonce_account(
    &payer.pubkey(),
    &nonce_account.pubkey(),
    authority,
    rent_lamports,
);

// This creates a single instruction that:
// 1. Creates the account
// 2. Initializes it as a nonce account
```

### Using CLI

```bash
# Generate keypair for nonce account
solana-keygen new -o nonce-account.json

# Create nonce account
solana create-nonce-account nonce-account.json 0.0015

# Verify creation
solana nonce nonce-account.json
# Output: Current nonce value (32-byte hash)
```

## Querying Nonce Accounts

### Fetching Nonce Value

```rust
use solana_sdk::account::Account;
use solana_program::system_program;

fn get_nonce_value(
    rpc_client: &RpcClient,
    nonce_pubkey: &Pubkey,
) -> Result<Hash, Box<dyn std::error::Error>> {
    // Fetch account data
    let account = rpc_client.get_account(nonce_pubkey)?;

    // Verify it's a nonce account
    if account.owner != system_program::id() {
        return Err("Account is not owned by System Program".into());
    }

    // Deserialize nonce data
    let nonce_data = bincode::deserialize::<NonceState>(&account.data)?;

    match nonce_data {
        NonceState::Current(data) => Ok(data.durable_nonce),
        NonceState::Legacy(data) => Ok(data.durable_nonce),
    }
}
```

### Parsing Nonce Account

```rust
use solana_program::nonce::state::{Data, State};

fn parse_nonce_account(account_data: &[u8]) -> Result<Data, Box<dyn std::error::Error>> {
    let state: State = bincode::deserialize(account_data)?;

    match state {
        State::Initialized(data) => Ok(data),
        State::Uninitialized => Err("Nonce account not initialized".into()),
    }
}

// Access nonce components
fn display_nonce_info(nonce_data: &Data) {
    println!("Authority: {}", nonce_data.authority);
    println!("Nonce value: {}", nonce_data.blockhash);
    println!("Fee calculator: {:?}", nonce_data.fee_calculator);
}
```

## Building Transactions with Durable Nonces

### Transaction Structure

**Critical requirements:**
1. **First instruction** MUST be `advance_nonce_account`
2. Use nonce value as `recent_blockhash`
3. Sign with nonce authority (in addition to other required signers)

```rust
use solana_sdk::{
    hash::Hash,
    instruction::Instruction,
    message::Message,
    signature::{Keypair, Signer},
    system_instruction,
    transaction::Transaction,
};

fn build_nonce_transaction(
    nonce_pubkey: &Pubkey,
    nonce_authority: &Keypair,
    nonce_value: Hash,
    instructions: Vec<Instruction>,
    payer: &Keypair,
) -> Transaction {
    // 1. Create advance_nonce instruction (MUST BE FIRST)
    let advance_nonce_ix = system_instruction::advance_nonce_account(
        nonce_pubkey,
        &nonce_authority.pubkey(),
    );

    // 2. Combine with your instructions
    let mut all_instructions = vec![advance_nonce_ix];
    all_instructions.extend(instructions);

    // 3. Build message with nonce as blockhash
    let message = Message::new_with_blockhash(
        &all_instructions,
        Some(&payer.pubkey()),
        &nonce_value,  // Use nonce value instead of recent blockhash!
    );

    // 4. Sign with both payer and nonce authority
    let mut signers = vec![payer];
    if nonce_authority.pubkey() != payer.pubkey() {
        signers.push(nonce_authority);
    }

    Transaction::new(&signers, message, nonce_value)
}
```

### Complete Example: Transfer with Durable Nonce

```rust
fn transfer_with_nonce(
    rpc_client: &RpcClient,
    nonce_account: &Pubkey,
    nonce_authority: &Keypair,
    payer: &Keypair,
    recipient: &Pubkey,
    amount: u64,
) -> Result<(), Box<dyn std::error::Error>> {
    // 1. Fetch current nonce value
    let nonce_value = get_nonce_value(rpc_client, nonce_account)?;

    // 2. Create transfer instruction
    let transfer_ix = system_instruction::transfer(
        &payer.pubkey(),
        recipient,
        amount,
    );

    // 3. Build transaction with nonce
    let transaction = build_nonce_transaction(
        nonce_account,
        nonce_authority,
        nonce_value,
        vec![transfer_ix],
        payer,
    );

    // 4. Can now submit immediately or store for later
    // No expiration pressure!
    let signature = rpc_client.send_and_confirm_transaction(&transaction)?;
    println!("Transfer completed: {}", signature);

    Ok(())
}
```

### Serializing for Offline Signing

```rust
use base58::ToBase58;

fn serialize_for_offline_signing(transaction: &Transaction) -> String {
    // Serialize transaction to bytes
    let serialized = bincode::serialize(transaction).unwrap();

    // Encode as base58 for transport
    serialized.to_base58()
}

fn deserialize_signed_transaction(base58_tx: &str) -> Transaction {
    use base58::FromBase58;

    let bytes = base58_tx.from_base58().unwrap();
    bincode::deserialize(&bytes).unwrap()
}
```

## Managing Nonce Accounts

### Advancing Nonce

**Automatic advancement**: When you submit a transaction with a durable nonce, the runtime automatically advances the nonce as part of processing the `advance_nonce_account` instruction.

**Manual advancement** (without submitting transaction):

```rust
fn advance_nonce_manually(
    rpc_client: &RpcClient,
    nonce_account: &Pubkey,
    nonce_authority: &Keypair,
    payer: &Keypair,
) -> Result<(), Box<dyn std::error::Error>> {
    let advance_ix = system_instruction::advance_nonce_account(
        nonce_account,
        &nonce_authority.pubkey(),
    );

    let recent_blockhash = rpc_client.get_latest_blockhash()?;
    let transaction = Transaction::new_signed_with_payer(
        &[advance_ix],
        Some(&payer.pubkey()),
        &[payer, nonce_authority],
        recent_blockhash,
    );

    rpc_client.send_and_confirm_transaction(&transaction)?;
    Ok(())
}
```

**When to manually advance:**
- Before reusing nonce for a new transaction
- To invalidate a previously signed transaction
- Regular rotation for security

### Withdrawing from Nonce Account

```rust
fn withdraw_from_nonce(
    rpc_client: &RpcClient,
    nonce_account: &Pubkey,
    nonce_authority: &Keypair,
    recipient: &Pubkey,
    amount: u64,
    payer: &Keypair,
) -> Result<(), Box<dyn std::error::Error>> {
    let withdraw_ix = system_instruction::withdraw_nonce_account(
        nonce_account,
        &nonce_authority.pubkey(),
        recipient,
        amount,
    );

    let recent_blockhash = rpc_client.get_latest_blockhash()?;
    let transaction = Transaction::new_signed_with_payer(
        &[withdraw_ix],
        Some(&payer.pubkey()),
        &[payer, nonce_authority],
        recent_blockhash,
    );

    rpc_client.send_and_confirm_transaction(&transaction)?;
    Ok(())
}
```

**Important**: Must maintain rent-exempt minimum balance. Can only withdraw to zero if closing the account.

### Changing Nonce Authority

```rust
fn change_nonce_authority(
    rpc_client: &RpcClient,
    nonce_account: &Pubkey,
    current_authority: &Keypair,
    new_authority: &Pubkey,
    payer: &Keypair,
) -> Result<(), Box<dyn std::error::Error>> {
    let authorize_ix = system_instruction::authorize_nonce_account(
        nonce_account,
        &current_authority.pubkey(),
        new_authority,
    );

    let recent_blockhash = rpc_client.get_latest_blockhash()?;
    let transaction = Transaction::new_signed_with_payer(
        &[authorize_ix],
        Some(&payer.pubkey()),
        &[payer, current_authority],
        recent_blockhash,
    );

    rpc_client.send_and_confirm_transaction(&transaction)?;
    Ok(())
}
```

**Use cases:**
- Transfer control to PDA for program-managed nonces
- Rotate keys for security
- Transfer to multisig for DAO control

## Offline Signing Workflows

### Hardware Wallet Flow

**Setup (online device):**
```rust
// 1. Create nonce account (one-time)
create_nonce_account(&rpc_client, &payer, &nonce_account, &hw_wallet_pubkey)?;

// 2. Fetch nonce value
let nonce_value = get_nonce_value(&rpc_client, &nonce_account.pubkey())?;

// 3. Build unsigned transaction
let unsigned_tx = build_nonce_transaction(
    &nonce_account.pubkey(),
    &hw_wallet_keypair,  // Will be replaced with actual signature
    nonce_value,
    vec![transfer_ix],
    &payer,
);

// 4. Serialize for hardware wallet
let serialized = serialize_for_offline_signing(&unsigned_tx);

// 5. Transfer to hardware wallet (USB, QR code, etc.)
```

**Signing (air-gapped hardware wallet):**
```rust
// 1. Receive serialized transaction
let tx = deserialize_signed_transaction(&serialized);

// 2. Display to user for review (no time pressure!)
// User reviews: recipient, amount, etc.

// 3. Sign with hardware wallet private key
// (Hardware wallet handles this internally)

// 4. Export signed transaction
let signed_serialized = serialize_for_offline_signing(&signed_tx);

// 5. Transfer back to online device
```

**Submission (online device):**
```rust
// 1. Receive signed transaction
let signed_tx = deserialize_signed_transaction(&signed_serialized);

// 2. Submit to network (can be hours/days after signing!)
let signature = rpc_client.send_and_confirm_transaction(&signed_tx)?;
```

### Multi-Signature Coordination

**DAO Proposal Execution Flow:**

```rust
// 1. Proposer creates transaction with nonce
let nonce_value = get_nonce_value(&rpc_client, &dao_nonce_account)?;
let proposal_tx = build_nonce_transaction(
    &dao_nonce_account,
    &dao_authority,  // PDA controlled by governance
    nonce_value,
    vec![execute_proposal_ix],
    &proposer,
);

// 2. Serialize and store in DAO state
let tx_data = bincode::serialize(&proposal_tx)?;
// Store tx_data in proposal account

// 3. Members vote over time (hours/days)
// Each vote increments approval count

// 4. When threshold reached, anyone can execute
let stored_tx: Transaction = bincode::deserialize(&proposal.tx_data)?;

// 5. Submit (nonce ensures it's still valid!)
rpc_client.send_and_confirm_transaction(&stored_tx)?;
```

### CLI Multi-Sig Example

**First co-signer (offline):**
```bash
solana transfer \
  --from sender.json \
  --sign-only \
  --nonce nonce-account.json \
  --nonce-authority nonce-authority.json \
  --blockhash <NONCE_VALUE> \
  --fee-payer co-sender.json \
  receiver.json 0.1

# Output:
# Pubkey=Signature
# 5nZ8nY5...=4SBv7Xp...
```

**Second co-signer (online, hours/days later):**
```bash
solana transfer \
  --from sender.json \
  --nonce nonce-account.json \
  --nonce-authority nonce-authority.json \
  --blockhash <NONCE_VALUE> \
  --fee-payer sender.json \
  --signer 5nZ8nY5...=4SBv7Xp... \
  receiver.json 0.1
```

## Security Considerations

### The Neodyme Vulnerability (2020)

**Historic issue**: Before Solana v1.3, there was a critical vulnerability in how durable nonce transactions were processed:

**The bug:**
1. Transaction with durable nonce starts processing
2. Runtime advances nonce (changes state)
3. Later instruction in transaction fails
4. Runtime rolls back ALL state changes
5. **BUG**: Nonce advancement was rolled back too!
6. Attacker could replay the transaction

**The exploit:**
```rust
// Malicious transaction:
{
    instructions: [
        advance_nonce(...),        // Advances nonce
        write_arbitrary_data(...), // Attacker's payload
        fail_intentionally(...),   // Forces transaction to fail
    ]
}

// After rollback:
// - Nonce reverted to original value
// - Arbitrary data write WAS NOT rolled back
// - Can replay transaction infinitely!
```

**Impact**: Could write arbitrary data to any account by replaying failed transactions.

**Fix** (Solana v1.3+): Nonce advancement is now **permanent** even on transaction failure. The runtime explicitly handles nonce accounts separately from normal rollback logic.

**Lesson**: This demonstrates why nonce advancement MUST happen regardless of transaction success/failure.

### Best Practices

**1. Never reuse nonce without advancing**

```rust
// BAD: Reusing nonce value
let nonce = get_nonce_value(&rpc, &nonce_account)?;
let tx1 = build_nonce_transaction(&nonce_account, &auth, nonce, vec![ix1], &payer);
let tx2 = build_nonce_transaction(&nonce_account, &auth, nonce, vec![ix2], &payer);
// If tx1 fails, tx2 might also fail with "nonce mismatch"

// GOOD: Advance between uses
let nonce1 = get_nonce_value(&rpc, &nonce_account)?;
let tx1 = build_nonce_transaction(&nonce_account, &auth, nonce1, vec![ix1], &payer);
rpc.send_and_confirm_transaction(&tx1)?;

// Fetch fresh nonce (it was advanced)
let nonce2 = get_nonce_value(&rpc, &nonce_account)?;
let tx2 = build_nonce_transaction(&nonce_account, &auth, nonce2, vec![ix2], &payer);
```

**2. Protect nonce authority**

```rust
// Use cold storage for nonce authority
// OR use PDA with program logic to restrict usage
let authority_pda = Pubkey::find_program_address(
    &[b"nonce_authority", dao.key().as_ref()],
    program_id,
);
```

**3. Maintain rent exemption**

```rust
// Check before withdrawal
let nonce_account = rpc.get_account(&nonce_pubkey)?;
let rent = rpc.get_minimum_balance_for_rent_exemption(80)?;

if nonce_account.lamports - withdraw_amount < rent {
    return Err("Would violate rent exemption".into());
}
```

**4. Verify nonce advancement in transaction**

```rust
// In your program that uses nonce transactions:
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    // First account should be nonce account
    let nonce_account = &accounts[0];

    // Verify it's a valid nonce account
    if nonce_account.owner != &system_program::id() {
        return Err(ProgramError::InvalidAccountData);
    }

    // Verify advance_nonce was called
    // (Runtime enforces this, but you can add checks)

    Ok(())
}
```

**5. Monitor nonce account balance**

```rust
// Periodic check (e.g., daily job)
fn check_nonce_health(rpc: &RpcClient, nonce: &Pubkey) -> Result<(), String> {
    let account = rpc.get_account(nonce)
        .map_err(|_| "Nonce account not found")?;

    let rent = rpc.get_minimum_balance_for_rent_exemption(80)
        .map_err(|_| "Failed to fetch rent")?;

    if account.lamports < rent {
        return Err(format!(
            "Nonce account below rent exemption: {} < {}",
            account.lamports, rent
        ));
    }

    Ok(())
}
```

## Use Cases

### 1. Scheduled Payments (Vesting)

```rust
// Pre-sign monthly vesting releases
fn create_vesting_schedule(
    rpc: &RpcClient,
    nonce_account: &Pubkey,
    nonce_authority: &Keypair,
    recipient: &Pubkey,
    amount_per_month: u64,
    months: usize,
) -> Result<Vec<Transaction>, Box<dyn std::error::Error>> {
    let mut transactions = Vec::new();

    for month in 0..months {
        // Fetch current nonce
        let nonce = get_nonce_value(rpc, nonce_account)?;

        // Create transfer
        let transfer_ix = system_instruction::transfer(
            &nonce_authority.pubkey(),
            recipient,
            amount_per_month,
        );

        // Build nonce transaction
        let tx = build_nonce_transaction(
            nonce_account,
            nonce_authority,
            nonce,
            vec![transfer_ix],
            nonce_authority,
        );

        transactions.push(tx);

        // Advance nonce for next month's transaction
        advance_nonce_manually(rpc, nonce_account, nonce_authority, nonce_authority)?;
    }

    Ok(transactions)
}

// Executor submits each month
fn execute_vesting_payment(
    rpc: &RpcClient,
    pre_signed_tx: &Transaction,
) -> Result<(), Box<dyn std::error::Error>> {
    // No time pressure - can submit anytime!
    rpc.send_and_confirm_transaction(pre_signed_tx)?;
    Ok(())
}
```

### 2. Conditional Trades (Limit Orders)

```rust
// Pre-sign trade execution at specific price
fn create_limit_order(
    nonce: &Pubkey,
    authority: &Keypair,
    swap_instruction: Instruction,  // Execute when price reached
) -> Transaction {
    let nonce_value = /* fetch nonce */;

    build_nonce_transaction(
        nonce,
        authority,
        nonce_value,
        vec![swap_instruction],
        authority,
    )
}

// Bot monitors price and submits when condition met
fn execute_limit_order(rpc: &RpcClient, current_price: f64, limit_tx: &Transaction) {
    if current_price >= target_price {
        rpc.send_transaction(limit_tx).ok();  // Submit pre-signed transaction
    }
}
```

### 3. Cross-Chain Bridges

```rust
// Sign Solana transaction while waiting for Ethereum finality
async fn bridge_from_ethereum_to_solana(
    eth_tx_hash: H256,
    solana_mint_ix: Instruction,
    nonce_account: &Pubkey,
    nonce_authority: &Keypair,
) -> Result<(), Box<dyn std::error::Error>> {
    // 1. Pre-sign Solana mint transaction
    let nonce = get_nonce_value(&solana_rpc, nonce_account)?;
    let mint_tx = build_nonce_transaction(
        nonce_account,
        nonce_authority,
        nonce,
        vec![solana_mint_ix],
        nonce_authority,
    );

    // 2. Wait for Ethereum finality (12+ minutes)
    wait_for_ethereum_finality(eth_tx_hash).await?;

    // 3. Submit Solana transaction (still valid!)
    solana_rpc.send_and_confirm_transaction(&mint_tx)?;

    Ok(())
}
```

### 4. DAO Governance Execution

Already covered in multi-sig example above - proposals can be voted on over days/weeks, then executed with pre-signed transaction.

## CLI Reference

**Create nonce account:**
```bash
solana create-nonce-account <KEYPAIR_PATH> <AMOUNT>
```

**Get current nonce:**
```bash
solana nonce <NONCE_ACCOUNT>
```

**Manually advance nonce:**
```bash
solana new-nonce <NONCE_ACCOUNT>
```

**Get nonce account info:**
```bash
solana nonce-account <NONCE_ACCOUNT>
```

**Withdraw from nonce:**
```bash
solana withdraw-from-nonce-account <NONCE_ACCOUNT> <DESTINATION> <AMOUNT>
```

**Change nonce authority:**
```bash
solana authorize-nonce-account <NONCE_ACCOUNT> <NEW_AUTHORITY>
```

**Sign transaction offline:**
```bash
solana <COMMAND> \
  --sign-only \
  --nonce <NONCE_ACCOUNT> \
  --nonce-authority <AUTHORITY_KEYPAIR> \
  --blockhash <NONCE_VALUE>
```

**Submit pre-signed transaction:**
```bash
solana <COMMAND> \
  --nonce <NONCE_ACCOUNT> \
  --nonce-authority <AUTHORITY_KEYPAIR> \
  --blockhash <NONCE_VALUE> \
  --signer <PUBKEY=SIGNATURE>
```

## Limitations and Considerations

**Transaction size:**
- Adding `advance_nonce_account` instruction adds ~40 bytes
- May push transaction over size limit if already near maximum

**Extra signature requirement:**
- Nonce authority must sign (if different from fee payer)
- Increases transaction complexity

**Rent cost:**
- Each nonce account requires ~0.0015 SOL rent-exempt minimum
- For many scheduled transactions, can become expensive

**Nonce advancement overhead:**
- Compute units to advance nonce (~few hundred CU)
- Minimal but worth considering for CU-constrained transactions

**Cannot mix recent blockhashes and nonces:**
- Transaction uses either recent blockhash OR durable nonce
- Cannot use both in the same transaction

## Resources

### Official Documentation
- [Introduction to Durable Nonces](https://solana.com/developers/guides/advanced/introduction-to-durable-nonces)
- [Durable Transaction Nonces Proposal](https://docs.anza.xyz/implemented-proposals/durable-tx-nonces)
- [CLI Nonce Examples](https://docs.anza.xyz/cli/examples/durable-nonce)

### Code Examples
- [Durable Nonces Repository](https://github.com/0xproflupin/solana-durable-nonces)
- [System Program Source](https://github.com/solana-labs/solana/blob/master/sdk/program/src/system_instruction.rs)

### Security Analysis
- [Neodyme: Nonce Upon a Time](https://neodyme.io/en/blog/nonce-upon-a-time/) - Historic vulnerability analysis

### Technical References
- [solana-sdk NonceState](https://docs.rs/solana-sdk/latest/solana_sdk/nonce/state/enum.State.html)
- [System Program Instructions](https://docs.rs/solana-sdk/latest/solana_sdk/system_instruction/)
