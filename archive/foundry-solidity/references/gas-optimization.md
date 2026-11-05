# Solidity Gas Optimization Guide

Comprehensive gas optimization techniques for Solidity 0.8.30 with Foundry profiling.

## Storage Optimization

### Variable Packing

Pack multiple variables into single 32-byte storage slots:

```solidity
// BAD: 3 storage slots (3 SSTORE operations)
contract Unoptimized {
    uint256 amount;      // slot 0
    uint8 status;        // slot 1
    address owner;       // slot 2
}

// GOOD: 2 storage slots
contract Optimized {
    uint128 amount;      // slot 0 (16 bytes)
    uint96 lockTime;     // slot 0 (12 bytes)
    uint8 status;        // slot 0 (1 byte)
    address owner;       // slot 1 (20 bytes)
}
```

**Savings:** 15,000+ gas per packed write

### Struct Packing

Pack struct fields in declaration order:

```solidity
// BAD: 3 slots
struct BadPacking {
    uint256 a;           // slot 0
    uint8 b;             // slot 1
    uint256 c;           // slot 2
}

// GOOD: 2 slots
struct GoodPacking {
    uint256 a;           // slot 0
    uint128 c;           // slot 1 (16 bytes)
    uint8 b;             // slot 1 (1 byte)
}
```

### Storage vs Memory vs Calldata

**Gas Costs:**
| Operation | Gas |
|-----------|-----|
| SLOAD (cold) | 2,100 |
| SLOAD (warm) | 100 |
| SSTORE (0→non-0) | 20,000 |
| SSTORE (non-0→non-0) | 5,000 |
| MLOAD/MSTORE | 3 per word |
| Calldata read | 3 per byte |

**Cache storage reads:**

```solidity
// BAD: 3 SLOAD operations
function process() external returns (uint256) {
    return value * 2 + value * 3 + value * 4;
}

// GOOD: 1 SLOAD + memory operations
function process() external returns (uint256) {
    uint256 v = value;
    return v * 2 + v * 3 + v * 4;
}
```

**Use calldata for external function arrays:**

```solidity
// BAD: Copies to memory
function batchProcess(uint256[] memory values) external { }

// GOOD: Reads directly from calldata
function batchProcess(uint256[] calldata values) external {
    for (uint256 i; i < values.length; ) {
        // Process values[i]
        unchecked { i++; }
    }
}
```

## Arithmetic Optimization

### Unchecked Blocks

Solidity 0.8+ adds overflow checks by default (~50-100 gas per operation):

```solidity
// BAD: Overflow check on every increment
for (uint256 i = 0; i < 100; i++) {
    result += i;
}

// GOOD: Unchecked increment (safe when bounded)
for (uint256 i = 0; i < 100; ) {
    result += i;
    unchecked { i++; }
}
```

**Savings:** 50-100 gas per iteration

### Short-Circuit Logic

Order conditions by likelihood to fail:

```solidity
// Expensive check last (short-circuits if first fails)
if (amount > 0 && expensiveValidation(amount)) {
    // ...
}
```

### Bitwise Flag Packing

Combine booleans into single uint256:

```solidity
// BAD: 4 storage slots
bool isActive;
bool isVerified;
bool isPaused;
bool isBlocked;

// GOOD: 1 storage slot, bit manipulation
uint256 flags;

function isActive() view returns (bool) {
    return (flags & (1 << 0)) != 0;
}

function setActive(bool _active) {
    if (_active) flags |= (1 << 0);
    else flags &= ~(1 << 0);
}
```

## Variable Declaration

### Immutable vs Constant vs Storage

```solidity
// Storage variable: 2,100 gas (cold read)
uint256 public maxSupply = 1_000_000;

// Constant: ~3 gas (embedded in bytecode)
uint256 public constant MAX_SUPPLY = 1_000_000;

// Immutable: ~100 gas (set once in constructor)
uint256 public immutable maxSupply;
constructor(uint256 _max) { maxSupply = _max; }
```

**Use constant for compile-time values, immutable for constructor-set values.**

### Function Visibility

```solidity
// Public creates getter (extra dispatch)
uint256 public value;

// External is cheaper for functions not called internally
function getValue() external view returns (uint256) {
    return _value;
}
```

## Error Handling

### Custom Errors vs Require Strings

```solidity
// BAD: String stored in bytecode (~50+ gas)
require(msg.sender == owner, "Unauthorized access");

// GOOD: Custom error (~24 gas)
error Unauthorized();
if (msg.sender != owner) revert Unauthorized();
```

**Savings:** 20-50 gas per revert

## Events vs Storage

Store transient data in events instead of contract storage:

```solidity
// BAD: 20,000+ gas per write
uint256[] public transfers;
function recordTransfer(uint256 amount) external {
    transfers.push(amount);
}

// GOOD: ~375 gas base + 8 gas per byte
event Transfer(address indexed to, uint256 amount);
function recordTransfer(address to, uint256 amount) external {
    emit Transfer(to, amount);
}
```

## Compiler Settings

```toml
# foundry.toml
[profile.default]
optimizer = true
optimizer_runs = 200     # Balance size/runtime

[profile.production]
optimizer = true
optimizer_runs = 1000000 # Optimize for runtime
via_ir = true            # IR pipeline (slower compile, better optimization)
```

**Guidance:**
- `200` runs: Smaller deployment, higher runtime cost
- `10000+` runs: Larger deployment, lower runtime cost
- `via_ir = true`: Best optimization, slowest compilation

## EVM Opcode Reference

| Operation | Gas | Notes |
|-----------|-----|-------|
| ADD/SUB/MUL | 3 | Basic arithmetic |
| DIV/MOD | 5 | Division operations |
| SLOAD (cold) | 2,100 | First storage read |
| SLOAD (warm) | 100 | Subsequent reads |
| SSTORE (0→non-0) | 20,000 | New storage slot |
| SSTORE (non-0→non-0) | 5,000 | Update existing |
| SSTORE (→0) | 5,000 | +15,000 refund |
| CALL | 700+ | External call base |
| KECCAK256 | 30 | +6 per word |
| LOG0-LOG4 | 375-1,875 | Events |

## Foundry Gas Profiling

### Gas Reports

```bash
# Generate gas report
forge test --gas-report

# Filter by contract
forge test --match-contract MyContract --gas-report
```

### Gas Snapshots

```bash
# Create snapshot
forge snapshot

# Compare against previous
forge snapshot --diff

# Check threshold
forge snapshot --check --tolerance 5
```

### Inline Gas Measurement

```solidity
function testGasUsage() public {
    uint256 gasBefore = gasleft();

    // Code to measure
    contract.doSomething();

    uint256 gasUsed = gasBefore - gasleft();
    console.log("Gas used:", gasUsed);
}
```

### Section Snapshots

```solidity
function testOptimization() public {
    vm.startSnapshotGas("operation");

    // Code to profile
    value = 1;

    uint256 gasUsed = vm.stopSnapshotGas();
}
```

## Optimization Checklist

**Storage:**
- [ ] Pack related variables together
- [ ] Use smaller integer types when possible
- [ ] Cache frequently accessed storage variables
- [ ] Use mappings instead of arrays for lookups
- [ ] Use immutable/constant for fixed values

**Functions:**
- [ ] Mark external (not public) when not called internally
- [ ] Use calldata for array parameters
- [ ] Use unchecked blocks for safe arithmetic
- [ ] Short-circuit expensive conditions
- [ ] Use custom errors instead of require strings

**Compilation:**
- [ ] Enable optimizer
- [ ] Set appropriate optimizer_runs
- [ ] Consider via_ir for production

**Testing:**
- [ ] Use `forge test --gas-report` regularly
- [ ] Create gas snapshots for regression detection
- [ ] Profile critical functions

## Quick Wins

| Pattern | Gas Saved | Effort |
|---------|-----------|--------|
| Custom errors | 20-50/revert | Low |
| Unchecked loops | 50-100/iter | Low |
| Calldata vs memory | 5,000+ | Low |
| Variable packing | 15,000/write | Low |
| Immutable vars | 2,000/read | Low |
| Bitwise flags | 15,000 | Medium |
| Events vs storage | 19,000+ | Medium |
