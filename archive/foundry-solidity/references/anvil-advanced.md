# Anvil Advanced Usage

Advanced Anvil features for local development and testing.

## Account Impersonation

### Auto-Impersonate All Accounts

```bash
# Start with auto-impersonation
anvil --auto-impersonate
```

Now any account can send transactions without private key:

```bash
cast send $CONTRACT "transfer(address,uint256)" $TO 1000 \
  --from 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 \
  --unlocked
```

### Impersonate Specific Account

```bash
# Via RPC
cast rpc anvil_impersonateAccount 0x1234...

# Stop impersonating
cast rpc anvil_stopImpersonatingAccount 0x1234...
```

### In Foundry Tests

```solidity
address whale = 0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503;

vm.startPrank(whale);
usdc.transfer(address(this), 1_000_000e6);
vm.stopPrank();
```

## State Manipulation

### Set Balance

```bash
# Set ETH balance
cast rpc anvil_setBalance 0x1234... 0xDE0B6B3A7640000  # 1 ETH in hex

# In tests
vm.deal(address, 100 ether);
```

### Set Code

```bash
# Deploy code at address
cast rpc anvil_setCode 0x1234... 0x608060405234801...

# In tests
vm.etch(address, code);
```

### Set Storage

```bash
# Set storage slot
cast rpc anvil_setStorageAt 0x1234... 0x0 0x...

# In tests
vm.store(address, slot, value);
```

### Set Nonce

```bash
cast rpc anvil_setNonce 0x1234... 0x10  # 16 in hex
```

## Mining Modes

### Auto-Mining (Default)

```bash
anvil  # Mines block on each transaction
```

### Interval Mining

```bash
# Mine every 12 seconds
anvil --block-time 12
```

### Manual Mining

```bash
# Disable auto-mining
anvil --no-mining

# Mine manually
cast rpc evm_mine

# Mine multiple blocks
cast rpc anvil_mine 10  # Mine 10 blocks
```

### Mining Control

```bash
# Enable auto-mine
cast rpc evm_setAutomine true

# Set interval
cast rpc evm_setIntervalMining 5000  # 5 seconds in ms
```

## State Snapshots

### Dump State

```bash
# Start anvil, make changes, then dump
anvil --dump-state state.json

# Load from previous state
anvil --load-state state.json
```

### Runtime Snapshots

```bash
# Create snapshot
SNAPSHOT_ID=$(cast rpc evm_snapshot)

# Make changes...

# Revert to snapshot
cast rpc evm_revert $SNAPSHOT_ID
```

### In Tests

```solidity
uint256 snapshot = vm.snapshot();

// Make changes...

vm.revertTo(snapshot);
```

## Fork Configuration

### Basic Fork

```bash
anvil --fork-url https://eth-mainnet.g.alchemy.com/v2/KEY
```

### Pin Block

```bash
anvil --fork-url $RPC_URL --fork-block-number 18000000
```

### Fork with Caching

```bash
# Cache fork data locally
anvil --fork-url $RPC_URL --fork-retry-backoff 1000

# Disable caching
anvil --fork-url $RPC_URL --no-storage-caching
```

### Multiple Forks

```solidity
// In tests
uint256 mainnetFork = vm.createFork("mainnet");
uint256 arbitrumFork = vm.createFork("arbitrum");

vm.selectFork(mainnetFork);
// Test on mainnet...

vm.selectFork(arbitrumFork);
// Test on arbitrum...
```

## Time Manipulation

```bash
# Set timestamp
cast rpc evm_setNextBlockTimestamp 1700000000

# Increase time
cast rpc evm_increaseTime 86400  # 1 day

# In tests
vm.warp(block.timestamp + 1 days);
vm.roll(block.number + 100);
```

## RPC Methods

### Common Anvil RPC

| Method | Description |
|--------|-------------|
| `anvil_setBalance` | Set ETH balance |
| `anvil_setCode` | Set contract code |
| `anvil_setStorageAt` | Set storage slot |
| `anvil_setNonce` | Set account nonce |
| `anvil_impersonateAccount` | Impersonate address |
| `anvil_mine` | Mine blocks |
| `anvil_reset` | Reset fork |
| `anvil_dumpState` | Export state |
| `anvil_loadState` | Import state |

### EVM Methods

| Method | Description |
|--------|-------------|
| `evm_snapshot` | Create snapshot |
| `evm_revert` | Revert to snapshot |
| `evm_mine` | Mine single block |
| `evm_setAutomine` | Toggle auto-mining |
| `evm_increaseTime` | Advance time |
| `evm_setNextBlockTimestamp` | Set next timestamp |

## Configuration

### Startup Options

```bash
anvil \
  --port 8545 \
  --accounts 10 \
  --balance 10000 \
  --mnemonic "test test test..." \
  --derivation-path "m/44'/60'/0'/0/" \
  --block-time 12 \
  --gas-limit 30000000 \
  --gas-price 0 \
  --chain-id 31337 \
  --hardfork prague
```

### Hardfork Selection

```bash
anvil --hardfork shanghai
anvil --hardfork cancun
anvil --hardfork prague  # Latest
```

## Testing Patterns

### Fork Test Setup

```solidity
function setUp() public {
    vm.createSelectFork(vm.envString("MAINNET_RPC_URL"), 18000000);

    // Impersonate whale
    address whale = 0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503;
    vm.startPrank(whale);
    usdc.transfer(address(this), 1_000_000e6);
    vm.stopPrank();
}
```

### State Reset Between Tests

```solidity
uint256 snapshot;

function setUp() public {
    if (snapshot == 0) {
        // First run: setup and snapshot
        _deployContracts();
        snapshot = vm.snapshot();
    } else {
        // Subsequent runs: revert to clean state
        vm.revertTo(snapshot);
    }
}
```

### Testing Mainnet Interactions

```solidity
function test_SwapOnUniswap() public {
    vm.createSelectFork("mainnet");

    address router = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address weth = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    deal(address(this), 10 ether);

    IRouter(router).swapExactETHForTokens{value: 1 ether}(
        0, path, address(this), block.timestamp
    );
}
```
