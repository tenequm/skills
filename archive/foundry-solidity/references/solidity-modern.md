# Modern Solidity (0.8.30)

Complete guide to Solidity 0.8.20-0.8.30 features, gas optimization, and security patterns.

## Version Feature Summary

| Version | Key Features |
|---------|-------------|
| 0.8.30 | Prague EVM default, NatSpec for enums |
| 0.8.29 | Custom storage layout (`layout at`) |
| 0.8.28 | Transient storage for value types |
| 0.8.27 | Transient storage parser support |
| 0.8.26 | `require(bool, Error)` custom errors |
| 0.8.25 | Cancun EVM default, MCOPY opcode |
| 0.8.24 | `blobbasefee`, `blobhash()`, tload/tstore in Yul |
| 0.8.22 | File-level events |
| 0.8.21 | Relaxed immutable initialization |
| 0.8.20 | Shanghai EVM default, PUSH0 |
| 0.8.19 | Custom operators for user-defined types |
| 0.8.18 | Named mapping parameters |

## Custom Errors (0.8.4+)

Gas-efficient error handling.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

error Unauthorized(address caller, address required);
error InsufficientBalance(uint256 available, uint256 required);
error InvalidAmount();
error Expired(uint256 deadline, uint256 current);

contract Token {
    mapping(address => uint256) public balanceOf;
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function transfer(address to, uint256 amount) external {
        if (amount == 0) revert InvalidAmount();
        if (amount > balanceOf[msg.sender]) {
            revert InsufficientBalance(balanceOf[msg.sender], amount);
        }

        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
    }

    function adminFunction() external {
        if (msg.sender != owner) {
            revert Unauthorized(msg.sender, owner);
        }
        // ...
    }
}
```

### require with Custom Errors (0.8.26+)

```solidity
function transfer(address to, uint256 amount) external {
    require(amount > 0, InvalidAmount());
    require(
        amount <= balanceOf[msg.sender],
        InsufficientBalance(balanceOf[msg.sender], amount)
    );

    balanceOf[msg.sender] -= amount;
    balanceOf[to] += amount;
}
```

### Gas Comparison

```solidity
// String error: ~4 bytes selector + string data
require(x > 0, "Amount must be greater than zero");

// Custom error: ~4 bytes selector only
if (x == 0) revert InvalidAmount();

// Custom error with params: ~4 bytes + encoded params
if (x > balance) revert InsufficientBalance(balance, x);

// Savings: 50-200+ gas per error
```

## Transient Storage (0.8.28+)

Cheap temporary storage cleared after transaction.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract ReentrancyGuard {
    bool transient locked;

    modifier nonReentrant() {
        require(!locked, "Reentrancy");
        locked = true;
        _;
        locked = false; // CRITICAL: Reset for composability
    }

    function withdraw() external nonReentrant {
        // Safe from reentrancy
    }
}
```

### Flash Loan Example

```solidity
contract FlashLender {
    IERC20 public token;
    bool transient flashLoanActive;

    function flashLoan(uint256 amount, address receiver) external {
        require(!flashLoanActive, "Flash loan active");
        flashLoanActive = true;

        uint256 balanceBefore = token.balanceOf(address(this));
        token.transfer(receiver, amount);

        IFlashBorrower(receiver).onFlashLoan(amount);

        require(
            token.balanceOf(address(this)) >= balanceBefore,
            "Flash loan not repaid"
        );

        flashLoanActive = false;
    }
}
```

### Gas Comparison

| Operation | Persistent Storage | Transient Storage |
|-----------|-------------------|-------------------|
| First write | 20,000+ gas | 100 gas |
| Subsequent write | 2,900 gas | 100 gas |
| Read | 100 gas | 100 gas |

**Important**: Always reset transient storage at function exit for composability.

## Immutable Variables (Relaxed in 0.8.21+)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

contract Config {
    address public immutable owner;
    uint256 public immutable deployTime;
    bytes32 public immutable configHash;
    uint256 public immutable maxSupply;

    constructor(uint256 _maxSupply, bytes32 _configHash) {
        owner = msg.sender;
        deployTime = block.timestamp;

        // Relaxed: can read/write immutables anywhere in constructor
        if (_maxSupply == 0) {
            maxSupply = 1_000_000e18;
        } else {
            maxSupply = _maxSupply;
        }

        // Can use other immutables
        configHash = _configHash != bytes32(0)
            ? _configHash
            : keccak256(abi.encode(owner, maxSupply));
    }
}
```

### Gas Benefits

- Immutable: **3 gas** (value inlined)
- Storage: **100 gas** (SLOAD)
- Constant: **0 gas** (compile-time constant)

## User-Defined Types with Operators (0.8.19+)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

type Amount is uint256;
type Price is uint256;

using {add as +, sub as -, mul, eq as ==, lt as <} for Amount global;

function add(Amount a, Amount b) pure returns (Amount) {
    return Amount.wrap(Amount.unwrap(a) + Amount.unwrap(b));
}

function sub(Amount a, Amount b) pure returns (Amount) {
    return Amount.wrap(Amount.unwrap(a) - Amount.unwrap(b));
}

function mul(Amount a, Price p) pure returns (uint256) {
    return Amount.unwrap(a) * Price.unwrap(p);
}

function eq(Amount a, Amount b) pure returns (bool) {
    return Amount.unwrap(a) == Amount.unwrap(b);
}

function lt(Amount a, Amount b) pure returns (bool) {
    return Amount.unwrap(a) < Amount.unwrap(b);
}

contract TypeSafe {
    function calculate(Amount a, Amount b, Price p) external pure returns (uint256) {
        Amount total = a + b;
        if (total < Amount.wrap(100)) {
            return 0;
        }
        return total.mul(p);
    }
}
```

## Named Mapping Parameters (0.8.18+)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

contract Token {
    // Highly readable
    mapping(address account => uint256 balance) public balanceOf;
    mapping(address owner => mapping(address spender => uint256 amount)) public allowance;

    // Complex mappings
    mapping(uint256 tokenId => mapping(address operator => bool approved)) public operatorApproval;
}
```

## File-Level Events (0.8.22+)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

// File-level event
event Transfer(address indexed from, address indexed to, uint256 value);
event Approval(address indexed owner, address indexed spender, uint256 value);

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
}

contract Token is IERC20 {
    mapping(address => uint256) public balanceOf;

    function transfer(address to, uint256 amount) external returns (bool) {
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }
}
```

## Custom Storage Layout (0.8.29+)

For EIP-7702 delegate implementations:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.29;

// Delegate 1: Storage starts at 0x1000
contract DelegateA layout at 0x1000 {
    uint256 public valueA;  // Slot 0x1000

    function setA(uint256 v) external {
        valueA = v;
    }
}

// Delegate 2: Storage starts at 0x2000
contract DelegateB layout at 0x2000 {
    uint256 public valueB;  // Slot 0x2000

    function setB(uint256 v) external {
        valueB = v;
    }
}

// Both can be delegated to from same account without storage collision
```

## Checked vs Unchecked Arithmetic

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

contract Arithmetic {
    // Default: checked (reverts on overflow)
    function checkedAdd(uint256 a, uint256 b) public pure returns (uint256) {
        return a + b; // Reverts if overflow
    }

    // Explicit: unchecked (wraps on overflow)
    function uncheckedIncrement(uint256 i) public pure returns (uint256) {
        unchecked {
            return i + 1; // Does not revert
        }
    }

    // Common pattern: loop counter
    function sum(uint256[] calldata arr) public pure returns (uint256 total) {
        for (uint256 i = 0; i < arr.length;) {
            total += arr[i];
            unchecked { ++i; } // Safe: i < arr.length guarantees no overflow
        }
    }
}
```

### When to Use Unchecked

Safe scenarios:
- Loop counters bounded by array length
- Incrementing from known safe values
- Subtracting after explicit bounds check
- Timestamp/block number arithmetic

Never use unchecked:
- User-provided inputs without validation
- Token amounts in DeFi
- Any value that could overflow

## Gas Optimization Techniques

### 1. Storage Packing

```solidity
// Bad: 3 slots
contract Unpacked {
    uint256 a;  // Slot 0
    uint128 b;  // Slot 1
    uint128 c;  // Slot 2
}

// Good: 2 slots
contract Packed {
    uint256 a;  // Slot 0
    uint128 b;  // Slot 1 (first half)
    uint128 c;  // Slot 1 (second half)
}
```

### 2. Caching Storage in Memory

```solidity
// Bad: Multiple SLOADs
function bad(uint256 amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;
    emit Transfer(msg.sender, amount, balances[msg.sender]);
}

// Good: Cache storage
function good(uint256 amount) external {
    uint256 balance = balances[msg.sender];
    require(balance >= amount);
    uint256 newBalance = balance - amount;
    balances[msg.sender] = newBalance;
    emit Transfer(msg.sender, amount, newBalance);
}
```

### 3. Use calldata for Read-Only Arrays

```solidity
// Bad: Copies to memory
function bad(uint256[] memory data) external { }

// Good: Direct calldata access
function good(uint256[] calldata data) external { }
```

### 4. Short-Circuit Conditionals

```solidity
// Cheaper checks first
function check(uint256 amount, address user) external view {
    // Cheap: comparison
    // Expensive: storage read
    if (amount > 0 && balances[user] >= amount) {
        // ...
    }
}
```

### 5. Use Constants and Immutables

```solidity
// Constant: 0 gas (inlined at compile time)
uint256 constant MAX_SUPPLY = 1_000_000e18;

// Immutable: 3 gas (inlined in bytecode)
address immutable owner;

// Storage: 100 gas (SLOAD)
address _owner;
```

### 6. Increment Patterns

```solidity
// Most efficient
unchecked { ++i; }

// Less efficient
unchecked { i++; }

// Least efficient (checked)
i++;
```

### Gas Costs Reference

| Operation | Gas Cost |
|-----------|----------|
| SLOAD (warm) | 100 |
| SLOAD (cold) | 2,100 |
| SSTORE (zero to non-zero) | 20,000 |
| SSTORE (non-zero to non-zero) | 2,900 |
| SSTORE (non-zero to zero) | Refund 4,800 |
| TLOAD | 100 |
| TSTORE | 100 |
| Memory read/write | 3 |
| Calldata read | 3 |

## Security Best Practices

### 1. Checks-Effects-Interactions

```solidity
function withdraw(uint256 amount) external {
    // CHECKS
    require(amount <= balances[msg.sender], "Insufficient");

    // EFFECTS
    balances[msg.sender] -= amount;

    // INTERACTIONS
    (bool success,) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
```

### 2. Reentrancy Protection

```solidity
// Using transient storage (0.8.28+)
bool transient locked;

modifier nonReentrant() {
    require(!locked);
    locked = true;
    _;
    locked = false;
}

// Or OpenZeppelin ReentrancyGuard
```

### 3. Access Control

```solidity
error Unauthorized();

modifier onlyOwner() {
    if (msg.sender != owner) revert Unauthorized();
    _;
}

// Use OpenZeppelin AccessControl for complex permissions
```

### 4. Safe External Calls

```solidity
// Check return value
(bool success, bytes memory data) = target.call(payload);
require(success, "Call failed");

// Or use SafeCall pattern
function safeTransferETH(address to, uint256 amount) internal {
    (bool success,) = to.call{value: amount}("");
    if (!success) revert TransferFailed();
}
```

### 5. Input Validation

```solidity
function deposit(uint256 amount) external {
    if (amount == 0) revert InvalidAmount();
    if (amount > MAX_DEPOSIT) revert ExceedsMax(amount, MAX_DEPOSIT);

    // Proceed
}
```

### 6. Integer Overflow Protection

```solidity
// Built-in since 0.8.0, but be careful with unchecked
function safeAdd(uint256 a, uint256 b) internal pure returns (uint256) {
    // This reverts on overflow (default behavior)
    return a + b;
}
```

### 7. Timestamp Dependence

```solidity
// Don't use for randomness
// Small manipulations possible by miners

// OK for time-based logic with tolerance
require(block.timestamp >= deadline, "Not yet");

// Bad: exact timing
require(block.timestamp == exactTime, "Wrong time");
```

## EVM Version Features

### Prague (0.8.30 default)

- All Cancun features
- EIP-7702 preparation

### Cancun (0.8.25 default)

- Transient storage (TLOAD, TSTORE)
- MCOPY for memory copying
- BLOBHASH, BLOBBASEFEE

### Shanghai (0.8.20 default)

- PUSH0 opcode

### Block Properties by Version

```solidity
// Always available
block.number
block.timestamp
block.chainid
block.coinbase
block.gaslimit

// Paris+
block.prevrandao  // Replaces block.difficulty

// Cancun+
block.blobbasefee
blobhash(index)
```

## Common Patterns

### Factory Pattern

```solidity
contract Factory {
    event Created(address indexed instance);

    function create(bytes32 salt, bytes calldata initData) external returns (address) {
        address instance = address(new Contract{salt: salt}(initData));
        emit Created(instance);
        return instance;
    }

    function predictAddress(bytes32 salt, bytes calldata initData) external view returns (address) {
        bytes32 hash = keccak256(abi.encodePacked(
            bytes1(0xff),
            address(this),
            salt,
            keccak256(abi.encodePacked(
                type(Contract).creationCode,
                abi.encode(initData)
            ))
        ));
        return address(uint160(uint256(hash)));
    }
}
```

### Minimal Proxy (EIP-1167)

```solidity
function clone(address implementation) internal returns (address instance) {
    assembly {
        let ptr := mload(0x40)
        mstore(ptr, 0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000)
        mstore(add(ptr, 0x14), shl(0x60, implementation))
        mstore(add(ptr, 0x28), 0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000)
        instance := create(0, ptr, 0x37)
    }
    require(instance != address(0), "Clone failed");
}
```

### Merkle Proof Verification

```solidity
function verify(
    bytes32[] calldata proof,
    bytes32 root,
    bytes32 leaf
) public pure returns (bool) {
    bytes32 computedHash = leaf;
    for (uint256 i = 0; i < proof.length;) {
        bytes32 proofElement = proof[i];
        if (computedHash <= proofElement) {
            computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
        } else {
            computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
        }
        unchecked { ++i; }
    }
    return computedHash == root;
}
```
