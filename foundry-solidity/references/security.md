# Solidity Security & Audit Patterns

Security vulnerabilities, defensive patterns, and Foundry testing strategies for smart contract audits.

## Critical Vulnerabilities

### Reentrancy

**Risk:** External calls allow recursive entry before state updates, draining contracts.

```solidity
// VULNERABLE: State update after external call
function withdraw(uint256 amount) public {
    require(balances[msg.sender] >= amount);
    (bool sent,) = msg.sender.call{value: amount}("");
    require(sent);
    balances[msg.sender] -= amount; // Too late!
}

// SECURE: CEI pattern + reentrancy guard
function withdraw(uint256 amount) public nonReentrant {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;    // Effects first
    (bool sent,) = msg.sender.call{value: amount}("");
    require(sent);                      // Interactions last
}
```

**Foundry Test:**
```solidity
contract ReentrancyAttacker {
    Vault vault;
    uint256 count;

    receive() external payable {
        if (count++ < 5 && address(vault).balance > 0) {
            vault.withdraw(1 ether);
        }
    }

    function attack() external {
        vault.withdraw(1 ether);
    }
}

function test_reentrancy_protected() public {
    ReentrancyAttacker attacker = new ReentrancyAttacker(vault);
    deal(address(attacker), 2 ether);
    attacker.deposit{value: 1 ether}();

    vm.expectRevert("ReentrancyGuard");
    attacker.attack();
}
```

### Access Control

**Risk:** Missing permission checks allow unauthorized privileged operations.

```solidity
// VULNERABLE: No access control
function drain() public {
    payable(owner).transfer(address(this).balance);
}

// VULNERABLE: Using tx.origin
function authorize(address user) public {
    require(tx.origin == admin); // Phishing vulnerable!
}

// SECURE: Role-based access
function drain() external onlyRole(ADMIN_ROLE) {
    payable(msg.sender).transfer(address(this).balance);
}
```

**Foundry Test:**
```solidity
function test_accessControl_unauthorized() public {
    vm.prank(attacker);
    vm.expectRevert(
        abi.encodeWithSelector(
            AccessControl.AccessControlUnauthorizedAccount.selector,
            attacker,
            vault.ADMIN_ROLE()
        )
    );
    vault.drain();
}
```

### Oracle Manipulation

**Risk:** Manipulated price feeds cause unfair liquidations or loan exploits.

```solidity
// VULNERABLE: Spot price (flash-loanable)
function getPrice() public view returns (uint256) {
    return dex.spotPrice(token);
}

// SECURE: Chainlink with staleness check
function getPrice() public view returns (int256) {
    (
        uint80 roundId,
        int256 price,
        ,
        uint256 updatedAt,
        uint80 answeredInRound
    ) = priceFeed.latestRoundData();

    require(price > 0, "Invalid price");
    require(answeredInRound >= roundId, "Stale round");
    require(block.timestamp - updatedAt < 3600, "Price too old");

    return price;
}
```

**Foundry Test:**
```solidity
function test_oracle_staleness() public {
    vm.warp(block.timestamp + 4000); // Past staleness threshold

    vm.expectRevert("Price too old");
    oracle.getPrice();
}
```

### Integer Overflow/Underflow

Solidity 0.8+ has built-in checks, but watch for:

```solidity
// VULNERABLE: Unchecked block disables protection
unchecked {
    balance -= amount; // Can underflow!
}

// VULNERABLE: Type casting
uint8 small = uint8(largeNumber); // Truncates silently

// SECURE: Explicit checks
require(balance >= amount, "Insufficient balance");
unchecked { balance -= amount; }
```

### Front-Running / MEV

**Risk:** Attackers see pending transactions and extract value.

**Mitigations:**
- Commit-reveal schemes for sensitive operations
- Flashbots for transaction privacy
- Slippage protection in DEX trades
- Batch auctions instead of first-come-first-served

```solidity
// Commit-reveal pattern
function commit(bytes32 hash) external {
    commits[msg.sender] = hash;
    commitTime[msg.sender] = block.timestamp;
}

function reveal(uint256 value, bytes32 salt) external {
    require(block.timestamp >= commitTime[msg.sender] + 1 hours);
    require(commits[msg.sender] == keccak256(abi.encode(value, salt)));
    // Process value
}
```

### Flash Loan Attacks

**Risk:** Attackers borrow large amounts to manipulate protocol state within single transaction.

**Mitigations:**
- Use TWAP instead of spot prices
- Require multi-block operations
- Over-collateralization requirements
- Block flash loans if not needed

### Signature Malleability

**Risk:** Attackers modify signatures to replay transactions.

```solidity
// VULNERABLE: No nonce or deadline
function permit(address owner, uint256 value, bytes calldata sig) external {
    // Can be replayed!
}

// SECURE: EIP-712 with nonce and deadline
function permit(
    address owner,
    address spender,
    uint256 value,
    uint256 deadline,
    uint8 v, bytes32 r, bytes32 s
) external {
    require(block.timestamp <= deadline, "Expired");
    // Verify EIP-712 signature with nonce
    nonces[owner]++;
}
```

### Storage Collision (Proxies)

**Risk:** Proxy and implementation have different storage layouts.

```solidity
// WRONG: Storage mismatch
contract Proxy {
    address implementation; // slot 0
    address owner;          // slot 1
}
contract Implementation {
    address owner;          // slot 0 - COLLISION!
}

// CORRECT: Use EIP-1967 storage slots
bytes32 constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
```

### Denial of Service

**Patterns:**
- Unbounded loops exhausting gas
- External calls that always revert
- Block gas limit exceeded

```solidity
// VULNERABLE: Unbounded loop
function distributeAll() external {
    for (uint256 i = 0; i < users.length; i++) {
        payable(users[i]).transfer(rewards[i]);
    }
}

// SECURE: Paginated distribution
function distributeBatch(uint256 start, uint256 count) external {
    require(count <= 100, "Batch too large");
    uint256 end = start + count;
    if (end > users.length) end = users.length;

    for (uint256 i = start; i < end; i++) {
        payable(users[i]).transfer(rewards[i]);
    }
}
```

## Foundry Security Testing

### Fuzz Testing

Generate random inputs to find edge cases:

```solidity
function testFuzz_transfer(address to, uint256 amount) public {
    vm.assume(to != address(0));
    vm.assume(to != address(token));
    amount = bound(amount, 0, token.balanceOf(address(this)));

    uint256 balanceBefore = token.balanceOf(to);
    token.transfer(to, amount);

    assertEq(token.balanceOf(to), balanceBefore + amount);
}
```

**Configuration:**
```toml
[fuzz]
runs = 10000
seed = "0x1234"
max_test_rejects = 65536
```

### Invariant Testing

Test properties that must always hold:

```solidity
contract VaultInvariant is Test {
    Vault vault;
    VaultHandler handler;

    function setUp() public {
        vault = new Vault();
        handler = new VaultHandler(vault);
        targetContract(address(handler));
    }

    // Total deposits must equal total shares value
    function invariant_solvency() public view {
        assertGe(
            vault.totalAssets(),
            vault.totalSupply(),
            "Vault insolvent"
        );
    }

    // Sum of balances equals total supply
    function invariant_balanceSum() public view {
        uint256 sum = 0;
        address[] memory users = handler.getUsers();
        for (uint256 i = 0; i < users.length; i++) {
            sum += vault.balanceOf(users[i]);
        }
        assertEq(sum, vault.totalSupply());
    }
}
```

### Handler Pattern

Control fuzz inputs and track state:

```solidity
contract VaultHandler is Test {
    Vault vault;
    address[] public users;
    uint256 public ghost_totalDeposited;

    constructor(Vault _vault) {
        vault = _vault;
        users.push(makeAddr("alice"));
        users.push(makeAddr("bob"));
    }

    function deposit(uint256 userSeed, uint256 amount) external {
        address user = users[bound(userSeed, 0, users.length - 1)];
        amount = bound(amount, 1, 1e24);

        deal(address(vault.asset()), user, amount);

        vm.startPrank(user);
        vault.asset().approve(address(vault), amount);
        vault.deposit(amount, user);
        vm.stopPrank();

        ghost_totalDeposited += amount;
    }

    function withdraw(uint256 userSeed, uint256 shares) external {
        address user = users[bound(userSeed, 0, users.length - 1)];
        shares = bound(shares, 0, vault.balanceOf(user));
        if (shares == 0) return;

        vm.prank(user);
        uint256 assets = vault.redeem(shares, user, user);

        ghost_totalDeposited -= assets;
    }
}
```

**Configuration:**
```toml
[invariant]
runs = 256
depth = 100
fail_on_revert = false
```

### Fork Testing

Test against real mainnet state:

```solidity
function setUp() public {
    vm.createSelectFork(vm.envString("MAINNET_RPC_URL"), 18000000);
}

function testFork_usdcIntegration() public {
    IERC20 usdc = IERC20(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
    address whale = 0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503;

    uint256 balanceBefore = usdc.balanceOf(address(this));

    vm.prank(whale);
    usdc.transfer(address(this), 1_000_000e6);

    assertEq(usdc.balanceOf(address(this)), balanceBefore + 1_000_000e6);
}
```

### Symbolic Execution (Halmos)

Prove properties mathematically:

```solidity
function check_transferPreservesSupply(address from, address to, uint256 amount) public {
    uint256 supplyBefore = token.totalSupply();

    token.transfer(from, to, amount);

    assert(token.totalSupply() == supplyBefore);
}
```

Run with: `halmos --contract MyTest`

## Pre-Audit Checklist

### Code Quality
- [ ] NatSpec documentation on all public functions
- [ ] No console.log or debug statements
- [ ] All TODO/FIXME resolved
- [ ] Consistent naming conventions

### Security Patterns
- [ ] Reentrancy guards on external-calling functions
- [ ] CEI pattern followed
- [ ] Access control on privileged functions
- [ ] No tx.origin for authentication
- [ ] SafeERC20 for token transfers
- [ ] Input validation on all parameters

### Testing
- [ ] >95% code coverage
- [ ] Fuzz tests with 10,000+ runs
- [ ] Invariant tests for core properties
- [ ] Edge case tests (zero, max values)
- [ ] Fork tests for integrations

### Static Analysis
- [ ] Slither: no HIGH/CRITICAL issues
- [ ] Manual review of MEDIUM issues

### Documentation
- [ ] README with security assumptions
- [ ] Threat model documented
- [ ] Known limitations listed
- [ ] Admin functions documented

## Common Audit Findings

### Missing Return Value Check

```solidity
// BAD
token.transfer(user, amount);

// GOOD
require(token.transfer(user, amount), "Transfer failed");

// BEST
IERC20(token).safeTransfer(user, amount);
```

### Uninitialized Proxy

```solidity
// BAD: Anyone can initialize
function initialize(address _owner) external {
    owner = _owner;
}

// GOOD: Use initializer modifier
function initialize(address _owner) external initializer {
    owner = _owner;
}
```

### Precision Loss

```solidity
// BAD: Division before multiplication
uint256 share = (amount / total) * balance; // Rounds to 0

// GOOD: Multiplication before division
uint256 share = (amount * balance) / total;
```

### Unchecked Array Access

```solidity
// BAD
return users[index]; // Can revert

// GOOD
require(index < users.length, "Out of bounds");
return users[index];
```

## Security Tools

**Static Analysis:**
- Slither: `slither . --json report.json`
- Mythril: `myth analyze contracts/Vault.sol`

**Fuzzing:**
- Forge fuzz: Built-in
- Echidna: Property-based fuzzing

**Formal Verification:**
- Certora Prover
- Halmos

## Foundry Security Commands

```bash
# Run all tests with coverage
forge coverage --report lcov

# Fuzz with high iterations
forge test --fuzz-runs 50000

# Invariant testing
forge test --match-contract Invariant -vv

# Fork testing
forge test --fork-url $RPC_URL

# Gas analysis
forge test --gas-report

# Debug failing test
forge test --match-test testName -vvvv
```
