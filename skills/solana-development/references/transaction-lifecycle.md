# Transaction Lifecycle: Submission, Retry, and Confirmation

This guide covers the complete lifecycle of Solana transactions from submission to confirmation, including why transactions get dropped, retry strategies, commitment levels, and monitoring patterns for production systems.

## Transaction Journey Overview

### The Full Path

```
[1] Client                     Creates and signs transaction
    ↓
[2] RPC Node                   Validates and forwards
    ↓
[3] Leader's TPU               Transaction Processing Unit pipeline
    ├─ Fetch Stage            Receives from network
    ├─ SigVerify Stage        Verifies signatures
    ├─ Banking Stage          Executes transactions
    ├─ PoH Service            Records in Proof of History
    └─ Broadcast Stage        Shares with cluster
    ↓
[4] Cluster Validation         Validators vote on blocks
    ↓
[5] Confirmation Levels
    ├─ Processed              Included in block by leader
    ├─ Confirmed              Supermajority voted (~66% stake)
    └─ Finalized              32+ confirmed blocks after (~13 seconds)
```

### Time

line

**Normal flow:**
- Client → RPC: Instant (local network)
- RPC → Leader: 100-400ms (network latency)
- Leader processing: 400-600ms (slot time)
- Confirmed: ~1-2 slots (~800-1200ms)
- Finalized: ~32 slots (~13+ seconds)

**Total time (happy path):** ~1-15 seconds

## Blockhash Expiration

### How Blockhashes Work

Solana transactions include a `recent_blockhash` field for two purposes:
1. **Uniqueness**: Ensures each transaction is unique (prevents duplicates)
2. **Freshness**: Limits transaction validity to prevent spam

**Critical constraint:**

```rust
// Solana runtime maintains BlockhashQueue
struct BlockhashQueue {
    last_hash: Hash,
    ages: HashMap<Hash, HashAge>,
    max_age: usize,  // Currently 151
}

// Transaction validation:
fn is_valid_blockhash(blockhash: &Hash, queue: &BlockhashQueue) -> bool {
    queue.ages.contains_key(blockhash)  // Must be in last 151 blockhashes
}
```

### The 151-Block Window

**How it works:**
1. Each slot produces a new blockhash (~400-600ms per slot)
2. Runtime keeps last 151 blockhashes in `BlockhashQueue`
3. Transactions checked against this queue
4. If blockhash older than 150 blocks → **REJECTED**

**Calculation:**
```
151 blockhashes × ~600ms average slot time = ~90 seconds maximum
151 blockhashes × ~400ms minimum slot time = ~60 seconds minimum

Effective window: 60-90 seconds
```

**Critical**: Once a blockhash exits the queue (>150 blocks old), transactions using it can **never** be processed. They're permanently invalid.

### Detecting Expiration

**Using `lastValidBlockHeight`:**

```rust
use solana_client::rpc_client::RpcClient;
use solana_sdk::commitment_config::CommitmentConfig;

async fn check_transaction_expiration(
    rpc_client: &RpcClient,
    last_valid_block_height: u64,
) -> bool {
    // Get current block height
    let current_block_height = rpc_client
        .get_block_height()
        .unwrap_or(0);

    // Transaction expired if current height > last valid height
    current_block_height > last_valid_block_height
}
```

**Getting `lastValidBlockHeight`:**

```rust
let blockhash_response = rpc_client.get_latest_blockhash()?;

let blockhash = blockhash_response.value.0;
let last_valid_block_height = blockhash_response.value.1;  // Blocks until expiration

println!("Blockhash: {}", blockhash);
println!("Valid until block: {}", last_valid_block_height);
```

### Why Transactions Expire

**Design rationale:**

1. **Prevents replay attacks**: Old transactions can't be resubmitted years later
2. **Manages state bloat**: Runtime doesn't need infinite blockhash history
3. **Network spam protection**: Attackers can't flood network with ancient transactions
4. **Simplifies fee markets**: Recent activity determines current conditions

**Trade-off**: 60-90 second window requires responsive clients and reliable networking.

## How Transactions Get Dropped

### Before Processing

**1. UDP Packet Loss**

Solana uses UDP for transaction forwarding (performance over reliability):

```
Client → RPC: UDP packet
RPC → Leader: UDP packet

Packet loss rate: 0.1-5% depending on network conditions
```

**Impact**: Transaction silently dropped, never reaches leader.

**Detection**: No error, no confirmation - transaction just disappears.

**Solution**: Retry mechanism (RPC default behavior).

**2. RPC Node Congestion**

RPC nodes maintain transaction queues:

```rust
// RPC node queue limits
const MAX_TRANSACTIONS_QUEUE: usize = 10_000;

// When queue full:
if queue.len() >= MAX_TRANSACTIONS_QUEUE {
    return Err("Transaction queue full, try again");
}
```

**Impact**: New transactions rejected when queue full.

**Detection**: RPC returns error immediately.

**Solution**: Back off and retry, or use different RPC endpoint.

**3. RPC Node Lag**

RPC nodes can fall behind cluster:

```rust
// Check RPC health
let processed_slot = rpc_client.get_slot()?;
let max_shred_insert_slot = rpc_client.get_max_shred_insert_slot()?;

let lag = max_shred_insert_slot.saturating_sub(processed_slot);

if lag > 50 {
    println!("WARNING: RPC is {} slots behind", lag);
    // Consider using different RPC node
}
```

**Impact**: Fetches stale blockhashes that expire quickly.

**Solution**: Monitor RPC health, use multiple RPC providers.

**4. Blockhash from Minority Fork**

Clusters occasionally fork temporarily (~5% of slots):

```
Majority fork: Block A → Block B → Block C
Minority fork: Block A → Block X (abandoned)
```

If you fetch blockhash from minority fork:
- Blockhash is valid on minority fork
- Majority fork has different blockhash
- Transaction **never** valid on majority fork

**Impact**: Transaction permanently invalid (never in BlockhashQueue of majority fork).

**Detection**: Transaction never confirms, blockhash never appears in majority chain.

**Solution**: Use `confirmed` commitment level when fetching blockhashes (not `processed`).

### After Processing But Before Finalization

**5. Leader on Minority Fork**

Transaction processed by leader, but leader's block abandoned by cluster:

```
1. Leader processes transaction in slot 1000
2. Cluster votes on slot 1000
3. Supermajority votes for different fork
4. Leader's block (and transaction) discarded
```

**Impact**: Transaction processed but not confirmed. Must resubmit.

**Detection**: Transaction shows as processed but never confirmed.

**Solution**: Wait for `confirmed` level before assuming success.

**6. Transaction Expiration During Retry**

Default RPC retry behavior has limitations:

```rust
// RPC retry logic (simplified):
while !finalized && !expired {
    forward_to_leader();
    sleep(2_seconds);
}

// Problem: What if we can't determine expiration?
// RPC may stop retrying early!
```

**Impact**: RPC stops retrying before transaction actually expires.

**Solution**: Implement custom retry logic with explicit expiration tracking.

## Commitment Levels

### Understanding Commitment

Solana has three commitment levels representing stages of finality:

```
Processed
    ↓ (1-2 slots later)
Confirmed
    ↓ (32+ slots later, ~13 seconds)
Finalized
```

### Processed

**Definition**: Transaction processed by leader and included in a block.

**Characteristics:**
- Fastest (most recent)
- Least safe (~5% chance of being on abandoned fork)
- Can be rolled back if fork abandoned

**When to use:**
- Real-time UX updates (show pending state)
- Price feeds where staleness is worse than occasional rollback
- **NOT for blockhash fetching** (risk of minority fork blockhash)

**Example:**
```rust
use solana_client::rpc_config::RpcSendTransactionConfig;
use solana_sdk::commitment_config::CommitmentLevel;

let config = RpcSendTransactionConfig {
    skip_preflight: false,
    preflight_commitment: Some(CommitmentLevel::Processed),
    ..Default::default()
};

// Risky! Blockhash might be from minority fork
let signature = rpc_client.send_transaction_with_config(&transaction, config)?;
```

### Confirmed

**Definition**: Supermajority of validators voted for the block containing the transaction.

**Characteristics:**
- Fast (~1-2 slots, ~600-1200ms)
- Safe (~<0.1% chance of rollback in normal conditions)
- **RECOMMENDED for blockhash fetching**

**When to use:**
- **Default choice** for most operations
- Blockhash fetching (balance of speed and safety)
- Transaction submission (preflight commitment)
- Confirmation monitoring

**Example:**
```rust
let commitment = CommitmentConfig::confirmed();

// Fetch blockhash at confirmed level
let recent_blockhash = rpc_client.get_latest_blockhash_with_commitment(commitment)?;

// Set preflight commitment to match
let config = RpcSendTransactionConfig {
    preflight_commitment: Some(CommitmentLevel::Confirmed),
    ..Default::default()
};
```

### Finalized

**Definition**: 32+ confirmed blocks have been built on top (mathematically impossible to rollback).

**Characteristics:**
- Slowest (~13+ seconds)
- 100% safe (impossible to rollback)
- Guaranteed by consensus algorithm

**When to use:**
- Financial settlement
- Legal/compliance requirements
- Cross-chain bridges
- Critical state changes

**Example:**
```rust
let commitment = CommitmentConfig::finalized();

// Wait for finalization
rpc_client.confirm_transaction_with_spinner(
    &signature,
    &recent_blockhash,
    commitment,
)?;
```

### Preflight Commitment Matching

**Critical rule**: Preflight commitment MUST match blockhash fetch commitment.

**Why:**

```rust
// Scenario: Mismatch
let blockhash = rpc.get_latest_blockhash_with_commitment(confirmed)?;  // confirmed

let config = RpcSendTransactionConfig {
    preflight_commitment: Some(CommitmentLevel::Processed),  // processed (WRONG!)
    ..Default::default()
};

// RPC tries to simulate at processed level
// But blockhash only exists at confirmed level
// Result: "Blockhash not found" error
```

**Correct approach:**

```rust
let commitment = CommitmentConfig::confirmed();

// Fetch blockhash
let blockhash_response = rpc.get_latest_blockhash_with_commitment(commitment)?;
let blockhash = blockhash_response.0;

// Match preflight commitment
let config = RpcSendTransactionConfig {
    preflight_commitment: Some(CommitmentLevel::Confirmed),
    ..Default::default()
};

let signature = rpc.send_transaction_with_config(&transaction, config)?;
```

## RPC Retry Behavior

### Default Retry Logic

RPC nodes automatically retry transactions:

```rust
// Simplified RPC retry algorithm:
const RETRY_INTERVAL: Duration = Duration::from_secs(2);
const MAX_QUEUE_SIZE: usize = 10_000;

loop {
    if transaction.is_finalized() {
        return Ok(signature);
    }

    if queue.len() >= MAX_QUEUE_SIZE {
        return Err("Queue full");
    }

    if can_determine_expiration() {
        if transaction.is_expired() {
            return Err("Blockhash expired");
        }
    } else {
        // Conservative: retry only once if can't determine expiration
        if retry_count > 1 {
            return Ok(signature);  // Might not actually be finalized!
        }
    }

    forward_to_current_leader();
    forward_to_next_leader();
    sleep(RETRY_INTERVAL);
    retry_count += 1;
}
```

### Leader Forwarding

RPC forwards transactions to:
1. **Current leader**: For immediate processing
2. **Next leader**: In case current leader rotation happens

**Why both?**
- Leader rotation happens every 4 slots (~1.6-2.4 seconds)
- Transaction might arrive during rotation
- Next leader can process in upcoming slots

### Queue Pressure

During congestion:

```
Queue size: 10,000 transactions
New transaction arrives:
    if queue.is_full():
        reject("Transaction queue full")
    else:
        queue.push(transaction)
        retry_until_finalized()
```

**User experience:**
- Fresh transactions rejected when queue full
- Older transactions keep retrying
- Can create priority inversion (old low-priority tx blocks new high-priority tx)

**Solution**: Use `maxRetries: 0` to take manual control during congestion.

## Custom Retry Strategies

### Manual Retry Loop

Taking full control:

```rust
use solana_client::rpc_client::RpcClient;
use solana_sdk::signature::Signature;
use std::time::Duration;
use tokio::time::sleep;

async fn send_transaction_with_retry(
    rpc_client: &RpcClient,
    transaction: &Transaction,
    last_valid_block_height: u64,
) -> Result<Signature, Box<dyn std::error::Error>> {
    let config = RpcSendTransactionConfig {
        skip_preflight: true,  // Already validated
        max_retries: Some(0),  // Manual retry control
        ..Default::default()
    };

    let signature = rpc_client.send_transaction_with_config(
        transaction,
        config,
    )?;

    // Manual retry loop
    loop {
        // Check if transaction confirmed
        match rpc_client.get_signature_status(&signature)? {
            Some(Ok(_)) => {
                println!("Transaction confirmed!");
                return Ok(signature);
            }
            Some(Err(e)) => {
                return Err(format!("Transaction failed: {:?}", e).into());
            }
            None => {
                // Not processed yet, continue
            }
        }

        // Check expiration
        let current_block_height = rpc_client.get_block_height()?;
        if current_block_height > last_valid_block_height {
            return Err("Transaction expired".into());
        }

        // Resubmit
        rpc_client.send_transaction_with_config(transaction, config)?;

        // Wait before next retry
        sleep(Duration::from_millis(500)).await;
    }
}
```

### Exponential Backoff

Reduce network load during congestion:

```rust
async fn retry_with_exponential_backoff(
    rpc_client: &RpcClient,
    transaction: &Transaction,
    last_valid_block_height: u64,
) -> Result<Signature, Box<dyn std::error::Error>> {
    let signature = rpc_client.send_transaction(transaction)?;

    let mut retry_delay = Duration::from_millis(500);
    const MAX_DELAY: Duration = Duration::from_secs(8);

    loop {
        match rpc_client.get_signature_status(&signature)? {
            Some(Ok(_)) => return Ok(signature),
            Some(Err(e)) => return Err(e.into()),
            None => {
                // Check expiration
                if rpc_client.get_block_height()? > last_valid_block_height {
                    return Err("Expired".into());
                }

                // Resubmit
                rpc_client.send_transaction(transaction)?;

                // Exponential backoff
                sleep(retry_delay).await;
                retry_delay = std::cmp::min(retry_delay * 2, MAX_DELAY);
            }
        }
    }
}
```

### Constant Interval (Mango Approach)

Aggressive resubmission:

```rust
async fn retry_constant_interval(
    rpc_client: &RpcClient,
    transaction: &Transaction,
    last_valid_block_height: u64,
) -> Result<Signature, Box<dyn std::error::Error>> {
    let signature = rpc_client.send_transaction(transaction)?;

    const RETRY_INTERVAL: Duration = Duration::from_millis(500);

    loop {
        match rpc_client.get_signature_status(&signature)? {
            Some(Ok(_)) => return Ok(signature),
            Some(Err(e)) => return Err(e.into()),
            None => {
                if rpc_client.get_block_height()? > last_valid_block_height {
                    return Err("Expired".into());
                }

                // Constant interval resubmission
                rpc_client.send_transaction(transaction)?;
                sleep(RETRY_INTERVAL).await;
            }
        }
    }
}
```

**Trade-offs:**
- **Exponential backoff**: Network-friendly, slower confirmation
- **Constant interval**: Faster confirmation, more network load
- **Choice depends on**: Application needs, RPC provider limits, congestion levels

## Confirmation Monitoring

### Polling for Confirmation

**Basic polling:**

```rust
use solana_sdk::signature::Signature;

fn wait_for_confirmation(
    rpc_client: &RpcClient,
    signature: &Signature,
    commitment: CommitmentConfig,
) -> Result<(), Box<dyn std::error::Error>> {
    loop {
        match rpc_client.get_signature_status_with_commitment(
            signature,
            commitment,
        )? {
            Some(Ok(_)) => {
                println!("Transaction confirmed at {:?}", commitment);
                return Ok(());
            }
            Some(Err(e)) => {
                return Err(format!("Transaction failed: {:?}", e).into());
            }
            None => {
                std::thread::sleep(Duration::from_millis(500));
            }
        }
    }
}
```

**With timeout:**

```rust
use std::time::{Duration, Instant};

fn wait_for_confirmation_with_timeout(
    rpc_client: &RpcClient,
    signature: &Signature,
    timeout: Duration,
) -> Result<bool, Box<dyn std::error::Error>> {
    let start = Instant::now();

    while start.elapsed() < timeout {
        match rpc_client.get_signature_status(signature)? {
            Some(Ok(_)) => return Ok(true),
            Some(Err(e)) => return Err(e.into()),
            None => std::thread::sleep(Duration::from_millis(500)),
        }
    }

    Ok(false)  // Timed out
}
```

### Using `confirm_transaction`

Built-in helper with expiration tracking:

```rust
let commitment = CommitmentConfig::confirmed();

// Method 1: With blockhash context
rpc_client.confirm_transaction_with_spinner(
    &signature,
    &recent_blockhash,
    commitment,
)?;

// Method 2: With last valid block height (recommended)
let result = rpc_client.confirm_transaction_with_commitment(
    &signature,
    commitment,
)?;

if result.value {
    println!("Transaction confirmed!");
} else {
    println!("Transaction not confirmed (might have expired)");
}
```

### WebSocket Subscriptions (Real-Time)

For real-time updates without polling:

```rust
use solana_client::pubsub_client::PubsubClient;
use solana_sdk::commitment_config::CommitmentConfig;

async fn subscribe_to_signature(
    ws_url: &str,
    signature: &Signature,
) -> Result<(), Box<dyn std::error::Error>> {
    let pubsub_client = PubsubClient::new(ws_url).await?;

    let (mut stream, unsubscribe) = pubsub_client
        .signature_subscribe(signature, Some(CommitmentConfig::confirmed()))
        .await?;

    // Wait for notification
    while let Some(response) = stream.next().await {
        match response.value {
            solana_client::rpc_response::RpcSignatureResult::ProcessedSignature(_) => {
                println!("Transaction confirmed!");
                break;
            }
        }
    }

    unsubscribe().await;
    Ok(())
}
```

**Advantages:**
- Real-time notification (no polling delay)
- Lower RPC load
- Immediate feedback

**Disadvantages:**
- WebSocket connection overhead
- Need to handle disconnections
- Not all RPC providers support WebSockets

## Best Practices

### 1. Fetch Fresh Blockhashes

```rust
// BAD: Fetch once and reuse
let blockhash = rpc.get_latest_blockhash()?;
for tx in transactions {
    // All use same blockhash (increases expiration risk)
    send_transaction(tx, &blockhash)?;
}

// GOOD: Fetch fresh blockhash for each transaction
for tx in transactions {
    let blockhash = rpc.get_latest_blockhash()?;
    send_transaction(tx, &blockhash)?;
}

// BETTER: Fetch fresh blockhash right before signing
fn prepare_and_send(user_action: Action) {
    // User initiates action
    let blockhash = rpc.get_latest_blockhash()?;  // Fetch now!

    // Build and sign (fast)
    let tx = build_transaction(user_action, &blockhash);
    sign_transaction(&tx);

    // Submit immediately
    send_transaction(&tx)?;
}
```

### 2. Use Confirmed Commitment

```rust
// RECOMMENDED: Confirmed commitment
let commitment = CommitmentConfig::confirmed();
let blockhash = rpc.get_latest_blockhash_with_commitment(commitment)?;

// Risks minority fork
let blockhash = rpc.get_latest_blockhash_with_commitment(
    CommitmentConfig::processed()
)?;  // Avoid!
```

### 3. Match Preflight Commitment

```rust
let commitment = CommitmentConfig::confirmed();

// Fetch blockhash
let (blockhash, last_valid_block_height) = rpc
    .get_latest_blockhash_with_commitment(commitment)?;

// Match preflight commitment
let config = RpcSendTransactionConfig {
    preflight_commitment: Some(CommitmentLevel::Confirmed),  // MATCH!
    ..Default::default()
};
```

### 4. Track Expiration Explicitly

```rust
// Get expiration info
let (blockhash, last_valid_block_height) = rpc.get_latest_blockhash()?;

// Check before retry
fn should_retry(rpc: &RpcClient, last_valid: u64) -> bool {
    rpc.get_block_height().unwrap_or(0) <= last_valid
}
```

### 5. Monitor RPC Health

```rust
async fn check_rpc_health(rpc: &RpcClient) -> bool {
    let processed = rpc.get_slot().unwrap_or(0);
    let max_shred = rpc.get_max_shred_insert_slot().unwrap_or(0);

    let lag = max_shred.saturating_sub(processed);

    if lag > 50 {
        eprintln!("RPC lagging by {} slots", lag);
        return false;
    }

    true
}
```

### 6. Implement Proper Error Handling

```rust
match rpc.send_transaction(&tx) {
    Ok(signature) => {
        println!("Submitted: {}", signature);
        // Wait for confirmation
    }
    Err(e) => {
        if e.to_string().contains("BlockhashNotFound") {
            // Blockhash expired, fetch fresh one
            let new_blockhash = rpc.get_latest_blockhash()?;
            // Re-sign transaction with new blockhash
        } else if e.to_string().contains("AlreadyProcessed") {
            // Transaction already submitted (safe to ignore)
        } else {
            // Other error, handle appropriately
            return Err(e.into());
        }
    }
}
```

### 7. Use Skip Preflight Judiciously

```rust
// When to skip preflight:
// - During congestion (preflight adds latency)
// - When retrying (already validated once)
// - When you're confident about transaction validity

let config = RpcSendTransactionConfig {
    skip_preflight: true,  // Skip simulation
    preflight_commitment: Some(CommitmentLevel::Confirmed),
    max_retries: Some(0),
    ..Default::default()
};

// Still recommended: Simulate ONCE before skip_preflight
rpc.simulate_transaction(&tx)?;  // Catch errors
// Then submit with skip_preflight for speed
```

## Production Patterns

### High-Throughput System

```rust
struct TransactionSubmitter {
    rpc_client: Arc<RpcClient>,
    retry_queue: Arc<Mutex<VecDeque<RetryableTransaction>>>,
}

struct RetryableTransaction {
    transaction: Transaction,
    signature: Signature,
    last_valid_block_height: u64,
    submitted_at: Instant,
    retry_count: usize,
}

impl TransactionSubmitter {
    async fn submit_transaction(&self, tx: Transaction) -> Result<Signature, Error> {
        let (blockhash, last_valid) = self.rpc_client.get_latest_blockhash()?;

        // Submit initial
        let signature = self.rpc_client.send_transaction(&tx)?;

        // Add to retry queue
        let retryable = RetryableTransaction {
            transaction: tx,
            signature,
            last_valid_block_height: last_valid,
            submitted_at: Instant::now(),
            retry_count: 0,
        };

        self.retry_queue.lock().unwrap().push_back(retryable);

        Ok(signature)
    }

    async fn retry_worker(&self) {
        loop {
            sleep(Duration::from_millis(500)).await;

            let mut queue = self.retry_queue.lock().unwrap();

            for tx in queue.iter_mut() {
                // Check if confirmed
                match self.rpc_client.get_signature_status(&tx.signature) {
                    Ok(Some(Ok(_))) => {
                        // Confirmed, remove from queue (handle in cleanup pass)
                        continue;
                    }
                    Ok(Some(Err(_))) => {
                        // Failed, remove from queue
                        continue;
                    }
                    _ => {
                        // Not confirmed, check expiration
                        let current_height = self.rpc_client.get_block_height().unwrap_or(0);

                        if current_height > tx.last_valid_block_height {
                            // Expired, remove from queue
                            continue;
                        }

                        // Retry
                        let _ = self.rpc_client.send_transaction(&tx.transaction);
                        tx.retry_count += 1;
                    }
                }
            }

            // Cleanup confirmed/failed/expired
            queue.retain(|tx| {
                matches!(
                    self.rpc_client.get_signature_status(&tx.signature),
                    Ok(None)  // Still pending
                )
            });
        }
    }
}
```

### Wallet Integration

```rust
async fn wallet_send_transaction(
    rpc: &RpcClient,
    unsigned_tx: Transaction,
    signer: &dyn Signer,
) -> Result<Signature, Error> {
    // Fetch blockhash immediately before signing
    let (blockhash, last_valid) = rpc.get_latest_blockhash()?;

    // Update transaction with fresh blockhash
    let mut tx = unsigned_tx.clone();
    tx.message.recent_blockhash = blockhash;

    // Sign
    tx.sign(&[signer], blockhash);

    // Simulate first
    rpc.simulate_transaction(&tx)?;

    // Submit with retry
    let signature = tx.signatures[0];

    send_with_retry(rpc, &tx, last_valid).await?;

    Ok(signature)
}
```

## Resources

### Official Documentation
- [Transaction Retry Guide](https://solana.com/developers/guides/advanced/retry)
- [Transaction Confirmation Guide](https://solana.com/developers/guides/advanced/confirmation)

### Technical References
- [RpcClient Source](https://github.com/solana-labs/solana/blob/master/client/src/rpc_client.rs)
- [Transaction Source](https://github.com/solana-labs/solana/blob/master/sdk/src/transaction/mod.rs)
- [BlockhashQueue Source](https://github.com/solana-labs/solana/blob/master/runtime/src/blockhash_queue.rs)

### Community Resources
- [Solana Cookbook - Transactions](https://solanacookbook.com/references/basic-transactions.html)
- [Solana Stack Exchange - Transaction Questions](https://solana.stackexchange.com/questions/tagged/transaction)
