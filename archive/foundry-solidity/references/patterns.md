# Solidity Patterns and Idioms

Common patterns for modern Solidity 0.8.30 smart contract development.

## Access Control Patterns

### Ownable Pattern

Single owner - simplest but centralized:

```solidity
contract Ownable {
    address private _owner;

    error Unauthorized();

    modifier onlyOwner() {
        if (msg.sender != _owner) revert Unauthorized();
        _;
    }

    constructor() {
        _owner = msg.sender;
    }

    function owner() public view returns (address) {
        return _owner;
    }

    function transferOwnership(address newOwner) public onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        _owner = newOwner;
    }
}
```

**Use:** Simple contracts, single admin
**Pitfall:** Single point of failure

### Role-Based Access Control

Fine-grained permissions:

```solidity
contract AccessControl {
    mapping(bytes32 => mapping(address => bool)) private _roles;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    error AccessDenied(address account, bytes32 role);

    modifier onlyRole(bytes32 role) {
        if (!_roles[role][msg.sender])
            revert AccessDenied(msg.sender, role);
        _;
    }

    function grantRole(bytes32 role, address account) public onlyRole(ADMIN_ROLE) {
        _roles[role][account] = true;
    }

    function hasRole(bytes32 role, address account) public view returns (bool) {
        return _roles[role][account];
    }
}
```

**Use:** DeFi protocols, complex permissions
**Recommendation:** Use OpenZeppelin's AccessControl

### Multi-Signature Pattern

Require multiple approvals for critical operations:

```solidity
contract MultiSig {
    address[] public owners;
    uint256 public requiredSignatures;

    mapping(bytes32 => mapping(address => bool)) public confirmations;
    mapping(bytes32 => bool) public executed;

    function submitTransaction(
        address target,
        uint256 value,
        bytes calldata data
    ) external returns (bytes32) {
        bytes32 txHash = keccak256(abi.encode(target, value, data, block.timestamp));
        confirmations[txHash][msg.sender] = true;
        return txHash;
    }

    function executeTransaction(
        address target,
        uint256 value,
        bytes calldata data,
        bytes32 txHash
    ) external {
        require(!executed[txHash], "Already executed");

        uint256 count = 0;
        for (uint256 i = 0; i < owners.length; i++) {
            if (confirmations[txHash][owners[i]]) count++;
        }
        require(count >= requiredSignatures, "Not enough signatures");

        executed[txHash] = true;
        (bool success,) = target.call{value: value}(data);
        require(success, "Execution failed");
    }
}
```

**Use:** Treasury, critical upgrades, governance

## Reentrancy Protection

### Checks-Effects-Interactions (CEI)

Most important pattern - prevent state inconsistencies:

```solidity
// BAD: State update AFTER external call
function withdrawBad() external {
    uint256 amount = balances[msg.sender];
    (bool success,) = msg.sender.call{value: amount}("");
    require(success);
    balances[msg.sender] = 0; // Vulnerable!
}

// GOOD: CEI pattern
function withdrawGood() external {
    uint256 amount = balances[msg.sender];
    balances[msg.sender] = 0;              // Effects first
    (bool success,) = msg.sender.call{value: amount}("");
    require(success);                       // Interactions last
}
```

### Mutex Lock (ReentrancyGuard)

Traditional approach using storage:

```solidity
contract ReentrancyGuard {
    uint256 private constant NOT_ENTERED = 1;
    uint256 private constant ENTERED = 2;
    uint256 private _status = NOT_ENTERED;

    modifier nonReentrant() {
        require(_status != ENTERED, "ReentrancyGuard: reentrant call");
        _status = ENTERED;
        _;
        _status = NOT_ENTERED;
    }
}
```

**Cost:** ~5,000 gas (2 SSTOREs)

### Transient Storage Lock (0.8.28+)

Gas-efficient using EIP-1153:

```solidity
contract TransientReentrancyGuard {
    modifier nonReentrant() {
        assembly {
            if tload(0) { revert(0, 0) }
            tstore(0, 1)
        }
        _;
        assembly {
            tstore(0, 0)
        }
    }
}
```

**Cost:** ~200 gas (TSTORE/TLOAD) - 25x cheaper

## Factory Patterns

### Basic Factory (CREATE)

```solidity
contract TokenFactory {
    address[] public deployedTokens;

    event TokenCreated(address indexed token, address indexed creator);

    function createToken(string memory name, string memory symbol)
        external
        returns (address)
    {
        Token token = new Token(name, symbol, msg.sender);
        deployedTokens.push(address(token));
        emit TokenCreated(address(token), msg.sender);
        return address(token);
    }
}
```

**Use:** Simple deployments where address doesn't matter

### Deterministic Factory (CREATE2)

Deploy to predictable addresses across chains:

```solidity
contract DeterministicFactory {
    event Deployed(address indexed addr, bytes32 salt);

    function deploy(bytes32 salt, bytes memory bytecode)
        external
        returns (address addr)
    {
        assembly {
            addr := create2(0, add(bytecode, 0x20), mload(bytecode), salt)
            if iszero(extcodesize(addr)) { revert(0, 0) }
        }
        emit Deployed(addr, salt);
    }

    function computeAddress(bytes32 salt, bytes32 bytecodeHash)
        external
        view
        returns (address)
    {
        return address(uint160(uint256(keccak256(abi.encodePacked(
            bytes1(0xff),
            address(this),
            salt,
            bytecodeHash
        )))));
    }
}
```

**Use:** Counterfactual deployments, cross-chain consistency

### Minimal Proxy (ERC-1167 Clones)

Deploy cheap proxies (~45 bytes):

```solidity
contract CloneFactory {
    function clone(address implementation) internal returns (address instance) {
        assembly {
            mstore(0x00, or(
                shr(0xe8, shl(0x60, implementation)),
                0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000
            ))
            mstore(0x20, or(shl(0x78, implementation), 0x5af43d82803e903d91602b57fd5bf3))
            instance := create(0, 0x09, 0x37)
        }
    }
}
```

**Cost:** ~10K gas vs ~170K for full contract
**Use:** Token factories, vault templates

## Payment Patterns

### Pull Over Push

**Push (Anti-pattern):**
```solidity
// BAD: Can fail if recipient reverts
function sendRewards() external {
    for (uint256 i = 0; i < recipients.length; i++) {
        payable(recipients[i]).transfer(amounts[i]);
    }
}
```

**Pull (Recommended):**
```solidity
contract PullPayments {
    mapping(address => uint256) public pendingWithdrawals;

    function claimReward() external {
        uint256 amount = pendingWithdrawals[msg.sender];
        require(amount > 0, "Nothing to claim");

        pendingWithdrawals[msg.sender] = 0;
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }
}
```

**Why pull is safer:**
- User controls when to withdraw
- Failing transfers don't block protocol
- Prevents DoS via malicious fallbacks

## Emergency Controls

### Pausable Pattern

```solidity
contract Pausable {
    bool public paused;
    address public owner;

    error ContractPaused();

    modifier whenNotPaused() {
        if (paused) revert ContractPaused();
        _;
    }

    function pause() external onlyOwner {
        paused = true;
    }

    function unpause() external onlyOwner {
        paused = false;
    }

    function transfer(address to, uint256 amount) external whenNotPaused {
        // Transfer logic
    }
}
```

**Use:** Security response, gradual rollouts

## Proxy Patterns

### UUPS (Recommended)

Implementation controls upgrades:

```solidity
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";

contract MyContractV1 is UUPSUpgradeable {
    uint256 public value;

    function initialize(uint256 _value) public initializer {
        value = _value;
    }

    function _authorizeUpgrade(address newImplementation)
        internal
        override
        onlyOwner
    {}
}
```

### Transparent Proxy

Admin calls go to proxy, user calls go to implementation:

```solidity
// Use OpenZeppelin's TransparentUpgradeableProxy
import "@openzeppelin/contracts/proxy/transparent/TransparentUpgradeableProxy.sol";
```

**Trade-offs:**
- UUPS: Smaller proxy, upgrade logic in implementation
- Transparent: Larger proxy, clearer admin separation

## State Machine Pattern

```solidity
contract Auction {
    enum Phase { Bidding, Reveal, Finished }

    Phase public currentPhase;
    uint256 public phaseDeadline;

    error WrongPhase(Phase expected, Phase actual);

    modifier atPhase(Phase expected) {
        _checkPhaseTransition();
        if (currentPhase != expected)
            revert WrongPhase(expected, currentPhase);
        _;
    }

    function _checkPhaseTransition() internal {
        if (block.timestamp >= phaseDeadline) {
            currentPhase = Phase(uint256(currentPhase) + 1);
            phaseDeadline = block.timestamp + 1 days;
        }
    }

    function placeBid(bytes32 hashedBid) external atPhase(Phase.Bidding) {
        // Bidding logic
    }

    function revealBid(uint256 value, bytes32 secret) external atPhase(Phase.Reveal) {
        // Reveal logic
    }
}
```

## Commit-Reveal Scheme

Prevent front-running:

```solidity
contract CommitReveal {
    mapping(address => bytes32) public commits;
    mapping(address => uint256) public commitTimes;

    uint256 public constant REVEAL_DELAY = 1 hours;

    function commit(bytes32 hash) external {
        commits[msg.sender] = hash;
        commitTimes[msg.sender] = block.timestamp;
    }

    function reveal(uint256 value, bytes32 salt) external {
        require(block.timestamp >= commitTimes[msg.sender] + REVEAL_DELAY, "Too early");
        require(commits[msg.sender] == keccak256(abi.encode(value, salt, msg.sender)), "Invalid reveal");

        delete commits[msg.sender];
        // Process revealed value
    }
}
```

**Use:** Auctions, voting, sealed-bid protocols

## Timelock Pattern

```solidity
contract Timelock {
    uint256 public constant DELAY = 2 days;

    mapping(bytes32 => uint256) public queuedTransactions;

    function queue(address target, bytes calldata data) external returns (bytes32) {
        bytes32 txHash = keccak256(abi.encode(target, data, block.timestamp));
        queuedTransactions[txHash] = block.timestamp + DELAY;
        return txHash;
    }

    function execute(address target, bytes calldata data, bytes32 txHash) external {
        uint256 executeTime = queuedTransactions[txHash];
        require(executeTime != 0, "Not queued");
        require(block.timestamp >= executeTime, "Too early");

        delete queuedTransactions[txHash];
        (bool success,) = target.call(data);
        require(success, "Execution failed");
    }
}
```

**Use:** Governance, critical upgrades, parameter changes

## Error Handling

### Custom Errors (Preferred)

```solidity
error InsufficientBalance(uint256 available, uint256 required);
error Unauthorized(address caller);
error ZeroAddress();

function withdraw(uint256 amount) external {
    if (balances[msg.sender] < amount)
        revert InsufficientBalance(balances[msg.sender], amount);
    // ...
}
```

**Advantages:**
- ~90% gas savings vs require strings
- Structured error data for debugging
- Type-safe parameters

## Initialization Patterns

### Constructor (Non-upgradeable)

```solidity
contract Permanent {
    address public immutable owner;
    uint256 public immutable maxSupply;

    constructor(address _owner, uint256 _maxSupply) {
        owner = _owner;
        maxSupply = _maxSupply;
    }
}
```

### Initializer (Upgradeable)

```solidity
contract Upgradeable {
    bool private _initialized;
    address public owner;

    modifier initializer() {
        require(!_initialized, "Already initialized");
        _initialized = true;
        _;
    }

    function initialize(address _owner) external initializer {
        owner = _owner;
    }
}
```

**Critical:** Constructors don't run on proxies - use initializers

## Common Pitfalls

### tx.origin vs msg.sender

```solidity
// WRONG: Vulnerable to phishing
if (tx.origin == owner) { /* ... */ }

// CORRECT
if (msg.sender == owner) { /* ... */ }
```

### Storage Layout with Upgrades

```solidity
// V1
contract V1 {
    uint256 public value; // slot 0
}

// V2 - CORRECT: Append only
contract V2 is V1 {
    uint256 public newValue; // slot 1
}

// V2 - WRONG: Inserting breaks layout
contract V2Bad {
    uint256 public newValue; // slot 0 - collision!
    uint256 public value;    // slot 1
}
```

### Unbounded Loops

```solidity
// DANGEROUS: Can run out of gas
function distributeAll() external {
    for (uint256 i = 0; i < recipients.length; i++) {
        payable(recipients[i]).transfer(amounts[i]);
    }
}

// SAFE: Batch processing
function distributeBatch(uint256 start, uint256 end) external {
    require(end <= recipients.length && end - start <= 100);
    for (uint256 i = start; i < end; i++) {
        payable(recipients[i]).transfer(amounts[i]);
    }
}
```

### Unchecked External Calls

```solidity
// WRONG: Return value ignored
token.transfer(user, amount);

// CORRECT: Check return
bool success = token.transfer(user, amount);
require(success, "Transfer failed");

// BEST: Use SafeERC20
IERC20(token).safeTransfer(user, amount);
```
