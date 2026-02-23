# forge-std API Reference

Complete reference for the Forge Standard Library.

## Overview

```solidity
import {Test, console} from "forge-std/Test.sol";
import {Script} from "forge-std/Script.sol";
```

`Test` inherits: `StdAssertions`, `StdChains`, `StdCheats`, `StdInvariant`, `StdUtils`

## StdAssertions

### Boolean

```solidity
assertTrue(bool condition);
assertTrue(bool condition, string memory err);

assertFalse(bool condition);
assertFalse(bool condition, string memory err);
```

### Equality

```solidity
// Works with: bool, uint256, int256, address, bytes32, string, bytes
assertEq(T left, T right);
assertEq(T left, T right, string memory err);

assertNotEq(T left, T right);
assertNotEq(T left, T right, string memory err);

// Arrays
assertEq(T[] memory left, T[] memory right);
```

### Comparison

```solidity
// Works with: uint256, int256
assertLt(T left, T right);      // <
assertLt(T left, T right, string memory err);

assertGt(T left, T right);      // >
assertGt(T left, T right, string memory err);

assertLe(T left, T right);      // <=
assertLe(T left, T right, string memory err);

assertGe(T left, T right);      // >=
assertGe(T left, T right, string memory err);
```

### Decimal Formatting

```solidity
// Shows values with decimal places in error messages
assertEqDecimal(uint256 left, uint256 right, uint256 decimals);
assertNotEqDecimal(uint256 left, uint256 right, uint256 decimals);
assertLtDecimal(uint256 left, uint256 right, uint256 decimals);
assertGtDecimal(uint256 left, uint256 right, uint256 decimals);
assertLeDecimal(uint256 left, uint256 right, uint256 decimals);
assertGeDecimal(uint256 left, uint256 right, uint256 decimals);

// Example
assertEqDecimal(1e18, 1e18, 18); // Shows "1.0" not "1000000000000000000"
```

### Approximation

```solidity
// Absolute difference
assertApproxEqAbs(uint256 left, uint256 right, uint256 maxDelta);
assertApproxEqAbs(uint256 left, uint256 right, uint256 maxDelta, string memory err);

// Relative difference (maxPercentDelta: 1e18 = 100%)
assertApproxEqRel(uint256 left, uint256 right, uint256 maxPercentDelta);
assertApproxEqRel(uint256 left, uint256 right, uint256 maxPercentDelta, string memory err);

// Examples
assertApproxEqAbs(1000, 1005, 10);     // Pass: |1000-1005| <= 10
assertApproxEqRel(100, 101, 0.02e18);  // Pass: 1% diff <= 2%
```

### Call Comparison

```solidity
assertEqCall(address target, bytes memory callDataA, bytes memory callDataB);
assertEqCall(address targetA, bytes memory callDataA, address targetB, bytes memory callDataB);
```

### Failure

```solidity
fail();
fail(string memory err);
bool hasFailed = failed();
```

## StdCheats

### Address Creation

```solidity
// Create labeled address
address alice = makeAddr("alice");

// Create address with private key
(address bob, uint256 bobKey) = makeAddrAndKey("bob");

// Create account struct
Account memory account = makeAccount("charlie");
// account.addr, account.key
```

### Account Setup

```solidity
// ETH
deal(address to, uint256 amount);

// ERC20
deal(address token, address to, uint256 amount);
deal(address token, address to, uint256 amount, bool adjustTotalSupply);

// ERC721
dealERC721(address token, address to, uint256 tokenId);

// ERC1155
dealERC1155(address token, address to, uint256 id, uint256 amount);
dealERC1155(address token, address to, uint256 id, uint256 amount, bool adjustTotalSupply);
```

### Time Manipulation

```solidity
skip(uint256 seconds);   // Move forward
rewind(uint256 seconds); // Move backward

// Examples
skip(1 days);
skip(1 hours);
rewind(30 minutes);
```

### Prank with ETH (hoax)

```solidity
// Single call as sender with ETH
hoax(address sender);
hoax(address sender, uint256 give);
hoax(address sender, address origin);
hoax(address sender, address origin, uint256 give);

// Multiple calls
startHoax(address sender);
startHoax(address sender, uint256 give);
// ... calls ...
vm.stopPrank();

// Example
hoax(alice, 10 ether);
vault.deposit{value: 1 ether}();
```

### Code Deployment

```solidity
// Deploy from artifacts
address deployed = deployCode("ContractName.sol");
address deployed = deployCode("ContractName.sol:ContractName");
address deployed = deployCode("ContractName.sol", constructorArgs);
address deployed = deployCode("ContractName.sol", constructorArgs, value);

// Deploy to specific address
deployCodeTo("ContractName.sol", targetAddress);
deployCodeTo("ContractName.sol", constructorArgs, targetAddress);
```

### Assumptions

```solidity
// Address type checks
assumeNotZeroAddress(address addr);
assumeNotPrecompile(address addr);
assumeNotPrecompile(address addr, uint256 chainId);
assumeNotForgeAddress(address addr);
assumePayable(address addr);
assumeNotPayable(address addr);

// Token blacklists
assumeNotBlacklisted(address token, address addr);

// Combined checks
assumeAddressIsNot(address addr, AddressType t);
assumeAddressIsNot(address addr, AddressType t1, AddressType t2);

// AddressType enum: ZeroAddress, Precompile, ForgeAddress
```

### Fork Detection

```solidity
bool forking = isFork();

// Modifiers
function testOnlyLocal() public skipWhenForking { }
function testOnlyForked() public skipWhenNotForking { }
```

### Gas Metering

```solidity
// Disable gas metering for expensive setup
modifier noGasMetering;

function testExpensiveSetup() public noGasMetering {
    // Gas not counted
}
```

### Account Destruction

```solidity
destroyAccount(address target, address beneficiary);
```

## StdStorage

Dynamic storage slot finding and manipulation.

### Setup

```solidity
using stdStorage for StdStorage;
```

### Finding Slots

```solidity
// Simple variable
uint256 slot = stdstore
    .target(address(contract))
    .sig("variableName()")
    .find();

// Mapping
uint256 slot = stdstore
    .target(address(contract))
    .sig("balances(address)")
    .with_key(user)
    .find();

// Nested mapping
uint256 slot = stdstore
    .target(address(contract))
    .sig("allowances(address,address)")
    .with_key(owner)
    .with_key(spender)
    .find();

// Struct field
uint256 slot = stdstore
    .target(address(contract))
    .sig("structVar()")
    .depth(0)  // Field index
    .find();
```

### Writing Values

```solidity
stdstore
    .target(address(contract))
    .sig("balances(address)")
    .with_key(user)
    .checked_write(1000e18);

// For int256
stdstore
    .target(address(contract))
    .sig("delta()")
    .checked_write_int(-100);
```

### Example

```solidity
function testSetBalance() public {
    // Set alice's balance to 1000 tokens
    stdstore
        .target(address(token))
        .sig("balanceOf(address)")
        .with_key(alice)
        .checked_write(1000e18);

    assertEq(token.balanceOf(alice), 1000e18);
}
```

## StdUtils

### Bounded Randomness

```solidity
// Constrain fuzz input to range
uint256 bounded = bound(uint256 x, uint256 min, uint256 max);
int256 bounded = bound(int256 x, int256 min, int256 max);

// Constrain to valid private key range
uint256 key = boundPrivateKey(uint256 pk);

// Example
function testFuzz(uint256 amount) public {
    amount = bound(amount, 1, 1000);
    // amount is now in [1, 1000]
}
```

### Address Computation

```solidity
// CREATE address
address addr = computeCreateAddress(address deployer, uint256 nonce);

// CREATE2 address
address addr = computeCreate2Address(bytes32 salt, bytes32 initCodeHash, address deployer);
address addr = computeCreate2Address(bytes32 salt, bytes32 initCodeHash); // Uses CREATE2_FACTORY

// Init code hash
bytes32 hash = hashInitCode(bytes memory creationCode);
bytes32 hash = hashInitCode(bytes memory creationCode, bytes memory args);

// Example
bytes32 initHash = hashInitCode(type(MyContract).creationCode);
address predicted = computeCreate2Address(salt, initHash, factory);
```

### Token Utilities

```solidity
// Batch balance query (uses Multicall3)
uint256[] memory balances = getTokenBalances(address token, address[] memory addresses);
```

### Byte Conversion

```solidity
uint256 value = bytesToUint(bytes memory b);
```

## StdJson

### Reading

```solidity
using stdJson for string;

string memory json = vm.readFile("data.json");

// Single values
uint256 amount = json.readUint(".amount");
int256 balance = json.readInt(".balance");
address addr = json.readAddress(".recipient");
bytes32 hash = json.readBytes32(".hash");
string memory name = json.readString(".name");
bytes memory data = json.readBytes(".data");
bool flag = json.readBool(".enabled");

// Arrays
uint256[] memory amounts = json.readUintArray(".amounts");
address[] memory addrs = json.readAddressArray(".addresses");
string[] memory names = json.readStringArray(".names");

// With defaults
uint256 amount = json.readUintOr(".amount", 100);
address addr = json.readAddressOr(".recipient", address(0));

// Check existence
bool exists = json.keyExists(".key");

// Raw bytes
bytes memory raw = json.parseRaw(".data");
```

### Writing

```solidity
using stdJson for string;

string memory json = "obj";
json = json.serialize("amount", uint256(100));
json = json.serialize("recipient", address(0x123));
json = json.serialize("enabled", true);
json = json.serialize("amounts", amounts);

json.write("output.json");
json.write("output.json", ".config");
```

## StdToml

Identical API to StdJson:

```solidity
using stdToml for string;

string memory toml = vm.readFile("config.toml");
uint256 runs = toml.readUint(".profile.default.fuzz_runs");
```

## StdChains

Access chain configuration:

```solidity
Chain memory chain = getChain("mainnet");
// chain.name, chain.chainId, chain.rpcUrl

Chain memory chain = getChain(1); // By chain ID

// Set custom RPC
setChain("custom", ChainData({
    name: "Custom Chain",
    chainId: 12345,
    rpcUrl: "https://..."
}));
```

## StdInvariant

For invariant testing targets:

```solidity
// Target contracts for fuzzing
targetContract(address);
targetContracts(); // Returns address[]

// Exclude from fuzzing
excludeContract(address);
excludeContracts(); // Returns address[]

// Target senders
targetSender(address);
targetSenders(); // Returns address[]

// Exclude senders
excludeSender(address);
excludeSenders(); // Returns address[]

// Target specific selectors
targetSelector(FuzzSelector memory);
targetSelectors(); // Returns FuzzSelector[]

// Target artifacts (deploy and fuzz)
targetArtifact(string memory);
targetArtifacts(); // Returns string[]

// Target artifact selectors
targetArtifactSelector(FuzzArtifactSelector memory);
targetArtifactSelectors(); // Returns FuzzArtifactSelector[]
```

## StdError

Common error selectors:

```solidity
import {stdError} from "forge-std/StdError.sol";

vm.expectRevert(stdError.arithmeticError);     // Overflow/underflow
vm.expectRevert(stdError.assertionError);      // assert() failed
vm.expectRevert(stdError.divisionError);       // Division by zero
vm.expectRevert(stdError.encodeStorageError);  // Storage encoding
vm.expectRevert(stdError.enumConversionError); // Invalid enum
vm.expectRevert(stdError.indexOOBError);       // Array index out of bounds
vm.expectRevert(stdError.memOverflowError);    // Memory overflow
vm.expectRevert(stdError.popEmptyArrayError);  // Pop empty array
vm.expectRevert(stdError.zeroVarError);        // Zero-initialized function pointer
```

## StdMath

```solidity
import {stdMath} from "forge-std/StdMath.sol";

uint256 absolute = stdMath.abs(int256 x);
uint256 delta = stdMath.delta(uint256 a, uint256 b);
uint256 delta = stdMath.delta(int256 a, int256 b);
uint256 percent = stdMath.percentDelta(uint256 a, uint256 b);
```

## Console Logging

```solidity
import {console} from "forge-std/console.sol";
// or
import {console2} from "forge-std/console2.sol"; // Smaller bytecode

console.log("message");
console.log("value:", value);
console.log("a:", a, "b:", b);

// Type-specific
console.log(uint256 x);
console.log(int256 x);
console.log(address x);
console.log(bool x);
console.log(string memory x);
console.log(bytes memory x);
console.log(bytes32 x);

// Formatted
console.logBytes(bytes memory);
console.logBytes1(bytes1);
// ... up to logBytes32
```

## Script.sol

Base for deployment scripts:

```solidity
import {Script, console} from "forge-std/Script.sol";

contract DeployScript is Script {
    function setUp() public {}

    function run() public {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerKey);

        MyContract c = new MyContract();
        c.initialize();

        vm.stopBroadcast();

        console.log("Deployed:", address(c));
    }
}
```

### Script vs Test

| Feature | Test | Script |
|---------|------|--------|
| Base | `Test` | `Script` |
| Cheats | Full `StdCheats` | `StdCheatsSafe` |
| Purpose | Testing | Deployment |
| Broadcast | No | Yes |
| State changes | Local | On-chain |

## Constants

```solidity
// From CommonBase
address constant VM_ADDRESS = 0x7109709ECfa91a80626fF3989D68f67F5b1DD12D;
address constant CONSOLE = 0x000000000000000000636F6e736F6c652e6c6f67;
address constant CREATE2_FACTORY = 0x4e59b44847b379578588920cA78FbF26c0B4956C;
address constant DEFAULT_SENDER = 0x1804c8AB1F12E6bbf3894d4083f33e07309d1f38;
address constant DEFAULT_TEST_CONTRACT = 0x5615dEB798BB3E4dFa0139dFa1b3D433Cc23b72f;
address constant MULTICALL3_ADDRESS = 0xcA11bde05977b3631167028862bE2a173976CA11;
```
