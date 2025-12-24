# Surfpool Local Development

Surfpool is a drop-in replacement for `solana-test-validator` built on LiteSVM. It provides instant mainnet forking, powerful cheatcodes for testing, and Infrastructure as Code for reproducible deployments.

## Installation

```bash
# macOS (Homebrew)
brew install txtx/taps/surfpool

# Update existing installation
brew tap txtx/taps
brew reinstall surfpool

# From source
git clone https://github.com/txtx/surfpool.git
cd surfpool
cargo surfpool-install

# Docker
docker run surfpool/surfpool --version

# Verify
surfpool --version
```

## Quick Start

```bash
# Start local network (in Anchor project directory)
surfpool start

# Start with custom options
surfpool start --port 8899 --slot-time 400

# Start with airdrops to specific addresses
surfpool start --airdrop <PUBKEY1> --airdrop <PUBKEY2> --airdrop-amount 100000000000
```

When run in an Anchor project, Surfpool automatically:
- Generates Infrastructure as Code runbooks
- Deploys programs to the local network
- Provides structured environment for iteration

## CLI Options

```bash
surfpool start [OPTIONS]

Options:
  -m, --manifest-file-path <PATH>   Path to manifest [default: ./Surfpool.toml]
  -p, --port <PORT>                 RPC port [default: 8899]
  -o, --host <HOST>                 Host address [default: 127.0.0.1]
  -s, --slot-time <MS>              Slot time in ms [default: 400]
  -u, --rpc-url <URL>               Mainnet RPC for forking [default: https://api.mainnet-beta.solana.com]
  --no-tui                          Disable terminal UI, show log streams
  --no-deploy                       Disable auto deployments
  --watch                           Watch programs for changes
  -r, --runbook <ID>                Runbooks to execute [default: deployment]
  -a, --airdrop <PUBKEY>            Addresses to airdrop SOL
  -q, --airdrop-amount <LAMPORTS>   Airdrop amount [default: 10000000000000]
  -k, --airdrop-keypair-path <PATH> Keypair paths to airdrop [default: ~/.config/solana/id.json]
  -g, --geyser-plugin-config <PATH> Geyser plugins to load
  --no-explorer                     Disable explorer
```

## Mainnet Forking (Just-in-Time)

Surfpool fetches mainnet accounts on-demand without downloading snapshots:

```bash
# Fork mainnet state
surfpool start --rpc-url https://api.mainnet-beta.solana.com

# Use custom RPC (recommended for rate limits)
surfpool start --rpc-url https://mainnet.helius-rpc.com?api-key=YOUR_KEY
```

**Use cases:**
- Test CPIs into Jupiter, Raydium, Meteora without manual account dumps
- Simulate swaps with real liquidity pool state
- Test oracle integrations with live price feeds

## Cheatcodes

Special RPC methods for testing. Call via any Solana RPC client:

### Account Manipulation

**`surfnet_setAccount`** - Set any account's state:
```typescript
await connection._rpcRequest('surfnet_setAccount', [
  pubkey.toBase58(),
  {
    lamports: 1_000_000_000,
    data: Buffer.from([...]).toString('hex'),
    owner: SystemProgram.programId.toBase58(),
    executable: false,
  }
]);
```

**`surfnet_setTokenAccount`** - Set token balances directly:
```typescript
await connection._rpcRequest('surfnet_setTokenAccount', [
  owner.toBase58(),
  mint.toBase58(),
  {
    amount: 1_000_000_000_000,  // Set balance without minting
    delegate: null,
    state: 'initialized',
  }
]);
```

**`surfnet_cloneProgramAccount`** - Clone programs between IDs:
```typescript
await connection._rpcRequest('surfnet_cloneProgramAccount', [
  sourceProgramId.toBase58(),
  destinationProgramId.toBase58()
]);
```

**`surfnet_setProgramAuthority`** - Modify upgrade authority:
```typescript
await connection._rpcRequest('surfnet_setProgramAuthority', [
  programId.toBase58(),
  newAuthority.toBase58()  // or null for immutable
]);
```

### Time Manipulation

**`surfnet_timeTravel`** - Jump to future epoch/slot/timestamp:
```typescript
// Move to specific slot
await connection._rpcRequest('surfnet_timeTravel', [{ slot: 300_000_000 }]);

// Move to specific epoch
await connection._rpcRequest('surfnet_timeTravel', [{ epoch: 500 }]);
```

**`surfnet_pauseClock`** / **`surfnet_resumeClock`** - Control time:
```typescript
await connection._rpcRequest('surfnet_pauseClock', []);
// ... perform tests at frozen time
await connection._rpcRequest('surfnet_resumeClock', []);
```

### Transaction Profiling

**`surfnet_profileTransaction`** - Detailed CU analysis:
```typescript
const result = await connection._rpcRequest('surfnet_profileTransaction', [
  transaction.serialize().toString('base64'),
  'my-test-tag',  // optional tag for grouping
  { depth: 'instruction', encoding: 'base64' }
]);

// Result includes:
// - Total CU consumed
// - Per-instruction breakdown
// - Account changes
// - Execution logs
```

**`surfnet_getProfileResults`** - Retrieve tagged profiles:
```typescript
const profiles = await connection._rpcRequest('surfnet_getProfileResults', [
  'my-test-tag'
]);
```

**`surfnet_getTransactionProfile`** - Get profile by signature:
```typescript
const profile = await connection._rpcRequest('surfnet_getTransactionProfile', [
  { signature: txSignature }
]);
```

### IDL Management

**`surfnet_registerIdl`** - Register IDL for account parsing:
```typescript
await connection._rpcRequest('surfnet_registerIdl', [
  idlJson,  // Full IDL object
  slot      // Optional: slot when IDL becomes active
]);
```

**`surfnet_getIdl`** - Retrieve registered IDL:
```typescript
const idl = await connection._rpcRequest('surfnet_getIdl', [
  programId.toBase58()
]);
```

## Scenarios (Protocol Overrides)

Test against specific protocol states with slot-by-slot account overrides.

**Natively supported protocols (v1.0.0-rc1):**
- **Pyth v2** - Price feeds (SOL/USD, BTC/USD, ETH/BTC, ETH/USD)
- **Jupiter v6** - DEX aggregator, TokenLedger manipulation
- **Switchboard On-Demand** - Oracle quote overrides
- **Kamino** - Lending reserve liquidity, risk config, obligation health
- **Drift v2** - Perp/spot markets, user state, global state
- **Raydium AMM-v3** - AMM pool states
- **Meteora DLMM** - Dynamic liquidity market maker
- **Whirlpool** - Concentrated liquidity pools

**Register custom scenarios:**
```typescript
await connection._rpcRequest('surfnet_registerScenario', [
  {
    name: 'liquidation-test',
    description: 'Test liquidation at 80% LTV',
    overrides: [
      {
        slot: 1,
        accounts: {
          [obligationPubkey]: {
            borrowedValue: 80_000_000,
            depositedValue: 100_000_000
          }
        }
      }
    ]
  }
]);
```

**Use cases:**
- Simulate oracle price crashes
- Test liquidation scenarios
- Replay historical market conditions
- Stress test protocol edge cases

## Infrastructure as Code (IaC)

Surfpool uses `.tx` runbooks for declarative deployments:

```hcl
# deployment.tx
addon "svm" {
  network_id = input.network_id
  rpc_api_url = input.rpc_api_url
}

signer "deployer" "svm::web_wallet" {
  expected_address = input.deployer_address
}

action "deploy_program" "svm::deploy_program" {
  description = "Deploy the program"
  program = svm::get_program_from_anchor_project("my_program")
  authority = signer.deployer
  payer = signer.deployer
}

output "program_id" {
  value = action.deploy_program.program_id
}
```

**Run runbooks:**
```bash
# Supervised mode (web UI)
surfpool run deployment.tx

# Unsupervised mode (CI/CD)
surfpool run deployment.tx --unsupervised

# With environment
surfpool run deployment.tx --env mainnet
```

**Manifest file (`txtx.yml`):**
```yaml
name: my-protocol
runbooks:
  - name: Deploy Protocol
    location: ./deployment
    state:
      location: states

environments:
  devnet:
    network_id: devnet
    rpc_api_url: https://api.devnet.solana.com
  mainnet:
    network_id: mainnet
    rpc_api_url: https://api.mainnet-beta.solana.com
```

## IDL-to-SQL

Auto-generate SQL schemas from program IDLs:

```bash
# Surfpool automatically generates tables for registered IDLs
# Query account data via local SQLite or Postgres

# Example: Query all token accounts
SELECT * FROM token_accounts WHERE owner = 'YOUR_PUBKEY';
```

## MCP Integration

Add Surfpool as an MCP server for AI-assisted development:

**Claude Code / Cursor configuration:**
```json
{
  "mcpServers": {
    "surfpool": {
      "command": "surfpool",
      "args": ["mcp"]
    }
  }
}
```

**Available MCP tools:**
- `start_surfnet` - Start a local network
- `set_token_account` - Set token balances for testing

**Example prompt:**
> "Start a local network with 10 users loaded with SOL, USDC, JUP and TRUMP tokens"

## Integration with Anchor

Surfpool works seamlessly with existing Anchor workflows:

```bash
# In Anchor project directory
cd my-anchor-project

# Start Surfpool (auto-deploys programs)
surfpool start

# Run Anchor tests against Surfpool
anchor test --skip-local-validator

# Watch for program changes
surfpool start --watch
```

**anchor.toml configuration:**
```toml
[provider]
cluster = "localnet"  # Points to Surfpool on 8899

[programs.localnet]
my_program = "YourProgramID"
```

## Integration with Native Rust

```bash
# Build program
cargo build-sbf

# Start Surfpool
surfpool start --no-deploy

# Deploy manually
solana program deploy target/deploy/my_program.so

# Or use runbook
surfpool run deploy.tx
```

## Surfpool Studio

Local web dashboard for visualization:

```bash
# Start with Studio enabled (default)
surfpool start

# Access at http://localhost:8899/studio
```

**Features:**
- Real-time transaction monitoring
- Account state inspection
- Scenario builder (drag-and-drop protocol overrides)
- IDL-parsed account views
- Transaction profiling results

## Best Practices

### Testing with Cheatcodes

```typescript
describe('Liquidation Tests', () => {
  beforeEach(async () => {
    // Set up specific account states
    await connection._rpcRequest('surfnet_setTokenAccount', [
      userWallet.toBase58(),
      usdcMint.toBase58(),
      { amount: 1_000_000_000 }
    ]);

    // Pause clock for deterministic tests
    await connection._rpcRequest('surfnet_pauseClock', []);
  });

  it('should liquidate at 80% LTV', async () => {
    // Time travel to simulate price change
    await connection._rpcRequest('surfnet_timeTravel', [{ slot: currentSlot + 1000 }]);

    // Test liquidation logic
    // ...
  });

  afterEach(async () => {
    await connection._rpcRequest('surfnet_resumeClock', []);
  });
});
```

### CU Optimization Workflow

1. **Profile baseline:**
   ```typescript
   const baseline = await connection._rpcRequest('surfnet_profileTransaction', [
     tx.serialize().toString('base64'),
     'optimization-baseline'
   ]);
   ```

2. **Make optimizations** (see [compute-optimization.md](compute-optimization.md))

3. **Profile again and compare:**
   ```typescript
   const optimized = await connection._rpcRequest('surfnet_profileTransaction', [
     optimizedTx.serialize().toString('base64'),
     'optimization-v1'
   ]);
   ```

4. **Review in Studio** for per-instruction breakdown

### CI/CD Integration

```yaml
# GitHub Actions example
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Surfpool
        run: cargo install --git https://github.com/txtx/surfpool surfpool-cli

      - name: Start Surfpool
        run: surfpool start --no-tui &

      - name: Wait for Surfpool
        run: sleep 5

      - name: Run tests
        run: anchor test --skip-local-validator
```

## Troubleshooting

**Port already in use:**
```bash
surfpool start --port 8900
```

**Mainnet RPC rate limits:**
```bash
# Use dedicated RPC
surfpool start --rpc-url https://mainnet.helius-rpc.com?api-key=YOUR_KEY

# Or set environment variable
export SURFPOOL_DATASOURCE_RPC_URL=https://your-rpc.com
```

**Program not deploying:**
```bash
# Check deployment logs
surfpool start --debug

# Manually deploy
surfpool start --no-deploy
solana program deploy target/deploy/program.so
```

## Resources

- [Surfpool Documentation](https://docs.surfpool.run)
- [GitHub Repository](https://github.com/txtx/surfpool)
- [Surfpool 101 Video Series](https://www.youtube.com/playlist?list=PL0FMgRjJMRzO1FdunpMS-aUS4GNkgyr3T)
- [Discord Community](https://discord.gg/rqXmWsn2ja)
- [Solana Docs: Surfpool CLI Basics](https://solana.com/docs/intro/installation/surfpool-cli-basics)
