# Foundry Testing Guide

Complete guide to testing smart contracts with Forge.

## Test Structure

### File Conventions

- Test files: `ContractName.t.sol`
- Script files: `ScriptName.s.sol`
- Test contracts inherit from `Test`

### Function Prefixes

| Prefix | Purpose |
|--------|---------|
| `test_` | Unit test |
| `testFuzz_` | Fuzz test |
| `testFork_` | Fork test |
| `invariant_` | Invariant test |
| `test_RevertIf_` | Expected revert |
| `test_RevertWhen_` | Expected revert |

### Basic Test Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {Test, console} from "forge-std/Test.sol";
import {Vault} from "../src/Vault.sol";

contract VaultTest is Test {
    Vault public vault;
    address public alice;
    address public bob;

    function setUp() public {
        vault = new Vault();
        alice = makeAddr("alice");
        bob = makeAddr("bob");
        deal(alice, 100 ether);
        deal(bob, 100 ether);
    }

    function test_Deposit() public {
        vm.prank(alice);
        vault.deposit{value: 1 ether}();
        assertEq(vault.balanceOf(alice), 1 ether);
    }
}
```

## Unit Testing

### Assertions

```solidity
// Equality
assertEq(actual, expected);
assertEq(actual, expected, "custom message");
assertNotEq(actual, expected);

// Comparisons
assertGt(a, b);    // a > b
assertGe(a, b);    // a >= b
assertLt(a, b);    // a < b
assertLe(a, b);    // a <= b

// Boolean
assertTrue(condition);
assertFalse(condition);

// Approximation (for rounding)
assertApproxEqAbs(actual, expected, maxDelta);
assertApproxEqRel(actual, expected, maxPercentDelta); // 1e18 = 100%

// Arrays
assertEq(arr1, arr2);
```

### Testing Reverts

```solidity
// Expect any revert
vm.expectRevert();
vault.withdraw(1000 ether);

// Expect specific message
vm.expectRevert("Insufficient balance");
vault.withdraw(1000 ether);

// Expect custom error (selector only)
vm.expectRevert(InsufficientBalance.selector);
vault.withdraw(1000 ether);

// Expect custom error with parameters
vm.expectRevert(
    abi.encodeWithSelector(
        InsufficientBalance.selector,
        0,      // available
        1000    // required
    )
);
vault.withdraw(1000 ether);

// Partial revert (match selector only)
vm.expectPartialRevert(InsufficientBalance.selector);
vault.withdraw(1000 ether);
```

### Testing Events

```solidity
// Expect event emission
vm.expectEmit(true, true, false, true);
//            topic1, topic2, topic3, data
emit Transfer(alice, bob, 100);

// Call that should emit the event
token.transfer(bob, 100);

// Record and inspect logs
vm.recordLogs();
token.transfer(bob, 100);
Vm.Log[] memory logs = vm.getRecordedLogs();

assertEq(logs[0].topics[0], keccak256("Transfer(address,address,uint256)"));
```

### Testing Access Control

```solidity
function test_OnlyOwner() public {
    // Should succeed as owner
    vault.adminFunction();

    // Should fail as non-owner
    vm.expectRevert("Ownable: caller is not the owner");
    vm.prank(alice);
    vault.adminFunction();
}
```

## Fuzz Testing

Forge automatically generates random inputs for test parameters.

### Basic Fuzz Test

```solidity
function testFuzz_Deposit(uint256 amount) public {
    // Bound input to valid range
    amount = bound(amount, 0.01 ether, 100 ether);

    deal(alice, amount);
    vm.prank(alice);
    vault.deposit{value: amount}();

    assertEq(vault.balanceOf(alice), amount);
}
```

### Fuzz Configuration

```toml
# foundry.toml
[fuzz]
runs = 256              # Number of fuzz runs
seed = 42               # Deterministic seed (optional)
max_test_rejects = 65536
```

### Fixtures (Pre-defined Values)

```solidity
// Array fixture (must match parameter name)
uint256[] public fixtureAmount = [0, 1, 100, type(uint256).max];

// Function fixture
function fixtureUser() public returns (address[] memory) {
    address[] memory users = new address[](3);
    users[0] = makeAddr("alice");
    users[1] = makeAddr("bob");
    users[2] = address(0);
    return users;
}

function testFuzz_Transfer(uint256 amount, address user) public {
    // amount will be one of: 0, 1, 100, max
    // user will be one of: alice, bob, address(0)
}
```

### Using `vm.assume()`

```solidity
function testFuzz_Transfer(address recipient) public {
    // Skip invalid inputs
    vm.assume(recipient != address(0));
    vm.assume(recipient != address(token));

    // Or use helper
    assumeNotZeroAddress(recipient);
    assumeNotPrecompile(recipient);
}
```

## Invariant Testing

Test that properties hold across random function call sequences.

### Basic Invariant Test

```solidity
contract VaultInvariantTest is Test {
    Vault public vault;
    VaultHandler public handler;

    function setUp() public {
        vault = new Vault();
        handler = new VaultHandler(vault);

        // Only fuzz the handler
        targetContract(address(handler));
    }

    function invariant_SolvencyCheck() public view {
        assertGe(
            address(vault).balance,
            vault.totalDeposits(),
            "Vault is insolvent"
        );
    }

    function invariant_TotalSupplyConsistent() public view {
        assertEq(
            vault.totalSupply(),
            sumAllBalances(),
            "Supply mismatch"
        );
    }
}
```

### Handler Pattern

Wrap target contract to bound inputs and track state:

```solidity
contract VaultHandler is Test {
    Vault public vault;
    uint256 public ghost_totalDeposited;
    address[] public actors;

    constructor(Vault _vault) {
        vault = _vault;
        actors.push(makeAddr("alice"));
        actors.push(makeAddr("bob"));
        actors.push(makeAddr("charlie"));
    }

    function deposit(uint256 actorIndex, uint256 amount) external {
        // Bound inputs
        actorIndex = bound(actorIndex, 0, actors.length - 1);
        amount = bound(amount, 0.01 ether, 10 ether);

        address actor = actors[actorIndex];
        deal(actor, amount);

        vm.prank(actor);
        vault.deposit{value: amount}();

        // Track ghost variable
        ghost_totalDeposited += amount;
    }

    function withdraw(uint256 actorIndex, uint256 amount) external {
        actorIndex = bound(actorIndex, 0, actors.length - 1);
        address actor = actors[actorIndex];

        uint256 balance = vault.balanceOf(actor);
        amount = bound(amount, 0, balance);

        vm.prank(actor);
        vault.withdraw(amount);

        ghost_totalDeposited -= amount;
    }
}
```

### Target Configuration

```solidity
function setUp() public {
    // Only fuzz specific contracts
    targetContract(address(handler));

    // Exclude contracts from fuzzing
    excludeContract(address(vault));
    excludeContract(address(token));

    // Only use specific senders
    targetSender(alice);
    targetSender(bob);

    // Exclude specific senders
    excludeSender(address(0));

    // Target specific functions
    bytes4[] memory selectors = new bytes4[](2);
    selectors[0] = handler.deposit.selector;
    selectors[1] = handler.withdraw.selector;
    targetSelector(FuzzSelector({
        addr: address(handler),
        selectors: selectors
    }));
}
```

### Invariant Configuration

```toml
# foundry.toml
[invariant]
runs = 256              # Number of sequences
depth = 50              # Calls per sequence
fail_on_revert = false  # Continue on reverts
shrink_run_limit = 5000 # Shrinking iterations
```

## Fork Testing

Test against live blockchain state.

### Basic Fork Test

```solidity
contract ForkTest is Test {
    uint256 mainnetFork;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    address constant WHALE = 0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503;

    function setUp() public {
        mainnetFork = vm.createFork(vm.envString("MAINNET_RPC_URL"));
        vm.selectFork(mainnetFork);
    }

    function testFork_USDCTransfer() public {
        vm.prank(WHALE);
        IERC20(USDC).transfer(address(this), 1000e6);
        assertEq(IERC20(USDC).balanceOf(address(this)), 1000e6);
    }
}
```

### Fork Cheatcodes

```solidity
// Create fork
uint256 forkId = vm.createFork("https://eth-mainnet.alchemyapi.io/v2/...");
uint256 forkId = vm.createFork("mainnet"); // Uses foundry.toml rpc_endpoints
uint256 forkId = vm.createFork("mainnet", 18000000); // Pin to block

// Create and select in one call
vm.createSelectFork("mainnet");

// Switch between forks
vm.selectFork(mainnetFork);
vm.selectFork(arbitrumFork);

// Get active fork
uint256 active = vm.activeFork();

// Roll fork to different block
vm.rollFork(18500000);
vm.rollFork(arbitrumFork, 150000000);

// Make account persist across forks
vm.makePersistent(address(myContract));
vm.makePersistent(alice, bob, charlie);

// Check persistence
bool isPersistent = vm.isPersistent(address(myContract));

// Revoke persistence
vm.revokePersistent(address(myContract));
```

### Multi-Fork Testing

```solidity
function testFork_CrossChain() public {
    // Deploy on mainnet
    vm.selectFork(mainnetFork);
    address mainnetToken = address(new Token());

    // Deploy on Arbitrum
    vm.selectFork(arbitrumFork);
    address arbitrumToken = address(new Token());

    // Verify different deployments
    vm.selectFork(mainnetFork);
    assertEq(Token(mainnetToken).name(), "Token");

    vm.selectFork(arbitrumFork);
    assertEq(Token(arbitrumToken).name(), "Token");
}
```

### Fork Configuration

```toml
# foundry.toml
[rpc_endpoints]
mainnet = "${MAINNET_RPC_URL}"
sepolia = "${SEPOLIA_RPC_URL}"
arbitrum = "${ARBITRUM_RPC_URL}"
optimism = "${OPTIMISM_RPC_URL}"
```

## Differential Testing

Compare implementations against reference.

```solidity
function testDifferential_MerkleRoot(bytes32[] memory leaves) public {
    vm.assume(leaves.length > 0 && leaves.length < 100);

    // Solidity implementation
    bytes32 solidityRoot = merkle.getRoot(leaves);

    // Reference implementation (via FFI)
    string[] memory cmd = new string[](3);
    cmd[0] = "node";
    cmd[1] = "scripts/merkle.js";
    cmd[2] = vm.toString(abi.encode(leaves));

    bytes memory result = vm.ffi(cmd);
    bytes32 jsRoot = abi.decode(result, (bytes32));

    assertEq(solidityRoot, jsRoot, "Merkle root mismatch");
}
```

## Complete Cheatcode Reference

### State Manipulation

```solidity
// ETH balance
vm.deal(address, uint256);

// Code at address
vm.etch(address, bytes memory code);

// Storage
vm.store(address, bytes32 slot, bytes32 value);
bytes32 value = vm.load(address, bytes32 slot);

// Nonce
vm.setNonce(address, uint64 nonce);
vm.resetNonce(address);
uint64 nonce = vm.getNonce(address);

// Copy storage
vm.copyStorage(address from, address to);
```

### Caller Context

```solidity
// Single call
vm.prank(address sender);
vm.prank(address sender, address origin);

// Multiple calls
vm.startPrank(address sender);
vm.startPrank(address sender, address origin);
vm.stopPrank();
```

### Time & Block

```solidity
vm.warp(uint256 timestamp);          // block.timestamp
vm.roll(uint256 blockNumber);        // block.number
vm.fee(uint256 gasPrice);            // tx.gasprice
vm.difficulty(uint256 difficulty);   // block.difficulty
vm.coinbase(address miner);          // block.coinbase
vm.chainId(uint256 chainId);         // block.chainid
vm.prevrandao(bytes32 prevrandao);   // block.prevrandao
```

### Expectations

```solidity
// Reverts
vm.expectRevert();
vm.expectRevert(bytes memory message);
vm.expectRevert(bytes4 selector);
vm.expectPartialRevert(bytes4 selector);

// Events
vm.expectEmit(bool topic1, bool topic2, bool topic3, bool data);
vm.expectEmit(bool topic1, bool topic2, bool topic3, bool data, address emitter);

// Calls
vm.expectCall(address target, bytes memory data);
vm.expectCall(address target, uint256 value, bytes memory data);
vm.expectCall(address target, bytes memory data, uint64 count);
```

### Snapshots

```solidity
uint256 snapshot = vm.snapshot();
vm.revertTo(snapshot);
vm.revertToAndDelete(snapshot);
```

### Environment

```solidity
// Read .env
string memory value = vm.envString("KEY");
uint256 value = vm.envUint("KEY");
address value = vm.envAddress("KEY");
bool value = vm.envBool("KEY");
bytes32 value = vm.envBytes32("KEY");

// With default
uint256 value = vm.envOr("KEY", uint256(100));

// Check existence
bool exists = vm.envExists("KEY");
```

### Cryptography

```solidity
// Sign message
(uint8 v, bytes32 r, bytes32 s) = vm.sign(privateKey, digest);
(bytes32 r, bytes32 vs) = vm.signCompact(privateKey, digest);

// Get address from private key
address addr = vm.addr(privateKey);

// Derive key from mnemonic
uint256 key = vm.deriveKey(mnemonic, index);
uint256 key = vm.deriveKey(mnemonic, path, index);

// Create wallet
Vm.Wallet memory wallet = vm.createWallet("label");
Vm.Wallet memory wallet = vm.createWallet(privateKey);
```

### Labels & Debugging

```solidity
vm.label(address, "name");
string memory name = vm.getLabel(address);

vm.breakpoint();       // Debugger breakpoint
vm.breakpoint("name"); // Named breakpoint
```

### Gas Metering

```solidity
vm.pauseGasMetering();
// ... expensive operations ...
vm.resumeGasMetering();

Vm.Gas memory gas = vm.lastCallGas();
```

### File I/O

```solidity
string memory content = vm.readFile("path/to/file");
vm.writeFile("path/to/file", "content");
bool exists = vm.exists("path/to/file");
vm.removeFile("path/to/file");
```

## Test Verbosity Levels

```bash
forge test           # Summary only
forge test -v        # + Logs
forge test -vv       # + Assertion errors
forge test -vvv      # + Stack traces (failures)
forge test -vvvv     # + Stack traces (all) + setup
forge test -vvvvv    # + All traces always
```

## Best Practices

### Test Organization

1. One test file per contract
2. Group related tests in same contract
3. Use descriptive function names
4. Include failure reason in test name

### Fuzz Testing

1. Always `bound()` numeric inputs
2. Use `vm.assume()` sparingly (reduces coverage)
3. Use fixtures for edge cases
4. Set deterministic seed in CI

### Invariant Testing

1. Use handler pattern for complex protocols
2. Track ghost variables for assertions
3. Start with simple invariants
4. Increase depth/runs gradually

### Fork Testing

1. Pin to specific block for reproducibility
2. Configure RPC endpoints in foundry.toml
3. Use `vm.makePersistent()` for deployed contracts
4. Cache responses with deterministic seed

### General

1. Test public interface, not internal state
2. Use `makeAddr()` for labeled addresses
3. Use `deal()` instead of minting
4. Label important addresses for traces
5. Test both success and failure paths
