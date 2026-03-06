# Foundry Deployment Guide

Complete guide to deploying and verifying smart contracts with Foundry.

## forge create (Single Contract)

Quick deployment for single contracts.

### Basic Usage

```bash
# Deploy with constructor args
forge create src/Token.sol:Token \
    --rpc-url sepolia \
    --private-key $PRIVATE_KEY \
    --constructor-args "MyToken" "MTK" 18

# Deploy and verify
forge create src/Token.sol:Token \
    --rpc-url sepolia \
    --private-key $PRIVATE_KEY \
    --broadcast \
    --verify \
    --etherscan-api-key $ETHERSCAN_API_KEY \
    --constructor-args "MyToken" "MTK" 18

# Deploy with value (payable constructor)
forge create src/Vault.sol:Vault \
    --rpc-url sepolia \
    --private-key $PRIVATE_KEY \
    --value 1ether
```

### Using Ledger

```bash
forge create src/Token.sol:Token \
    --rpc-url mainnet \
    --ledger \
    --mnemonic-derivation-path "m/44'/60'/0'/0/0"
```

## Solidity Scripts (Recommended)

More powerful and flexible deployment method.

### Basic Deploy Script

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {Script, console} from "forge-std/Script.sol";
import {Token} from "../src/Token.sol";

contract DeployToken is Script {
    function run() external {
        // Load private key from environment
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerKey);

        console.log("Deploying from:", deployer);
        console.log("Balance:", deployer.balance);

        vm.startBroadcast(deployerKey);

        Token token = new Token("MyToken", "MTK", 18);
        console.log("Token deployed to:", address(token));

        // Initial setup
        token.mint(deployer, 1_000_000e18);

        vm.stopBroadcast();
    }
}
```

### Running Scripts

```bash
# Dry run (simulation only)
forge script script/Deploy.s.sol:DeployToken --rpc-url sepolia

# Broadcast transactions
forge script script/Deploy.s.sol:DeployToken \
    --rpc-url sepolia \
    --broadcast

# Broadcast and verify
forge script script/Deploy.s.sol:DeployToken \
    --rpc-url sepolia \
    --broadcast \
    --verify

# Resume failed deployment
forge script script/Deploy.s.sol:DeployToken \
    --rpc-url sepolia \
    --broadcast \
    --resume
```

### Script Execution Phases

1. **Local Simulation**: Run script, collect `vm.broadcast()` transactions
2. **On-chain Simulation**: (with `--rpc-url`) Simulate against chain state
3. **Broadcasting**: (with `--broadcast`) Send transactions to network
4. **Verification**: (with `--verify`) Verify contracts on Etherscan

### Complex Deployment

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {Script, console} from "forge-std/Script.sol";
import {Token} from "../src/Token.sol";
import {Staking} from "../src/Staking.sol";
import {Governance} from "../src/Governance.sol";

contract DeployProtocol is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.envAddress("ADMIN_ADDRESS");

        vm.startBroadcast(deployerKey);

        // Deploy token
        Token token = new Token("Protocol Token", "PTK", 18);
        console.log("Token:", address(token));

        // Deploy staking with token reference
        Staking staking = new Staking(address(token));
        console.log("Staking:", address(staking));

        // Deploy governance with token and staking
        Governance gov = new Governance(
            address(token),
            address(staking),
            admin
        );
        console.log("Governance:", address(gov));

        // Setup permissions
        token.grantRole(token.MINTER_ROLE(), address(staking));
        staking.setGovernance(address(gov));

        vm.stopBroadcast();
    }
}
```

### Configuration-Based Deployment

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {Script, console} from "forge-std/Script.sol";
import {Token} from "../src/Token.sol";

contract DeployConfigured is Script {
    struct Config {
        string name;
        string symbol;
        uint256 initialSupply;
        address admin;
    }

    function run() external {
        Config memory config = getConfig();

        uint256 deployerKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerKey);

        Token token = new Token(config.name, config.symbol, 18);
        token.mint(config.admin, config.initialSupply);

        if (config.admin != vm.addr(deployerKey)) {
            token.transferOwnership(config.admin);
        }

        vm.stopBroadcast();

        console.log("Deployed:", address(token));
    }

    function getConfig() internal view returns (Config memory) {
        uint256 chainId = block.chainid;

        if (chainId == 1) {
            return Config({
                name: "Production Token",
                symbol: "PROD",
                initialSupply: 100_000_000e18,
                admin: 0x1234567890123456789012345678901234567890
            });
        } else if (chainId == 11155111) {
            return Config({
                name: "Test Token",
                symbol: "TEST",
                initialSupply: 1_000_000e18,
                admin: vm.envAddress("TEST_ADMIN")
            });
        } else {
            revert("Unsupported chain");
        }
    }
}
```

### Deterministic Deployment (CREATE2)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {Script, console} from "forge-std/Script.sol";
import {Token} from "../src/Token.sol";

contract DeployDeterministic is Script {
    // Deterministic deployment factory (present on most chains)
    address constant CREATE2_FACTORY = 0x4e59b44847b379578588920cA78FbF26c0B4956C;

    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        bytes32 salt = keccak256("my-token-v1");

        // Predict address
        bytes memory bytecode = abi.encodePacked(
            type(Token).creationCode,
            abi.encode("MyToken", "MTK", 18)
        );
        address predicted = computeCreate2Address(salt, keccak256(bytecode));
        console.log("Predicted address:", predicted);

        // Check if already deployed
        if (predicted.code.length > 0) {
            console.log("Already deployed!");
            return;
        }

        vm.startBroadcast(deployerKey);

        Token token = new Token{salt: salt}("MyToken", "MTK", 18);
        require(address(token) == predicted, "Address mismatch");

        vm.stopBroadcast();

        console.log("Deployed to:", address(token));
    }

    function computeCreate2Address(bytes32 salt, bytes32 initCodeHash)
        internal
        view
        returns (address)
    {
        return address(uint160(uint256(keccak256(abi.encodePacked(
            bytes1(0xff),
            address(this),
            salt,
            initCodeHash
        )))));
    }
}
```

## Multi-Chain Deployment

### Sequential Deployment

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {Script, console} from "forge-std/Script.sol";
import {Token} from "../src/Token.sol";

contract DeployMultiChain is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");

        // Deploy to Ethereum
        vm.createSelectFork("mainnet");
        vm.startBroadcast(deployerKey);
        Token mainnetToken = new Token("Token", "TKN", 18);
        vm.stopBroadcast();
        console.log("Mainnet:", address(mainnetToken));

        // Deploy to Arbitrum
        vm.createSelectFork("arbitrum");
        vm.startBroadcast(deployerKey);
        Token arbitrumToken = new Token("Token", "TKN", 18);
        vm.stopBroadcast();
        console.log("Arbitrum:", address(arbitrumToken));

        // Deploy to Optimism
        vm.createSelectFork("optimism");
        vm.startBroadcast(deployerKey);
        Token optimismToken = new Token("Token", "TKN", 18);
        vm.stopBroadcast();
        console.log("Optimism:", address(optimismToken));
    }
}
```

Run with:

```bash
forge script script/DeployMultiChain.s.sol \
    --broadcast \
    --multi \
    --slow \
    --verify
```

## Contract Verification

### Auto-Verification

```bash
# During deployment
forge create src/Token.sol:Token \
    --rpc-url sepolia \
    --private-key $KEY \
    --verify \
    --etherscan-api-key $ETHERSCAN_KEY \
    --constructor-args "Name" "SYM" 18

# With script
forge script script/Deploy.s.sol --broadcast --verify
```

### Manual Verification

```bash
# Verify existing contract
forge verify-contract \
    --chain sepolia \
    --compiler-version 0.8.30 \
    --num-of-optimizations 200 \
    --constructor-args $(cast abi-encode "constructor(string,string,uint8)" "Name" "SYM" 18) \
    0xYourContractAddress \
    src/Token.sol:Token

# Check verification status
forge verify-check \
    --chain sepolia \
    $GUID
```

### Verification with Libraries

```bash
forge verify-contract \
    --chain mainnet \
    --libraries src/lib/Math.sol:Math:0xLibraryAddress \
    --libraries src/lib/Utils.sol:Utils:0xUtilsAddress \
    0xContractAddress \
    src/MyContract.sol:MyContract
```

### Configuration for Verification

```toml
# foundry.toml
[etherscan]
mainnet = { key = "${ETHERSCAN_API_KEY}" }
sepolia = { key = "${ETHERSCAN_API_KEY}" }
arbitrum = { key = "${ARBISCAN_API_KEY}" }
optimism = { key = "${OPTIMISTIC_ETHERSCAN_API_KEY}" }
base = { key = "${BASESCAN_API_KEY}" }
polygon = { key = "${POLYGONSCAN_API_KEY}" }
```

## Broadcast Artifacts

Scripts save transaction data to `broadcast/` directory:

```
broadcast/
└── Deploy.s.sol/
    └── 11155111/          # Chain ID
        ├── run-latest.json     # Latest run
        ├── run-1699999999.json # Timestamped runs
        └── receipts/
            └── ...
```

### Reading Artifacts in Scripts

```solidity
function readDeployment() internal view returns (address) {
    string memory root = vm.projectRoot();
    string memory path = string.concat(
        root,
        "/broadcast/Deploy.s.sol/11155111/run-latest.json"
    );

    string memory json = vm.readFile(path);
    bytes memory contractAddr = json.parseRaw(".transactions[0].contractAddress");
    return abi.decode(contractAddr, (address));
}
```

## Best Practices

### 1. Use Environment Variables

```solidity
uint256 deployerKey = vm.envUint("PRIVATE_KEY");
address admin = vm.envAddress("ADMIN_ADDRESS");
string memory rpcUrl = vm.envString("RPC_URL");
```

### 2. Validate Before Broadcasting

```solidity
function run() external {
    uint256 deployerKey = vm.envUint("PRIVATE_KEY");
    address deployer = vm.addr(deployerKey);

    // Pre-flight checks
    require(deployer.balance > 0.1 ether, "Insufficient balance");
    require(block.chainid == 11155111, "Wrong network");

    vm.startBroadcast(deployerKey);
    // ...
}
```

### 3. Log Everything

```solidity
vm.startBroadcast(deployerKey);

Token token = new Token("Name", "SYM", 18);
console.log("Token deployed to:", address(token));
console.log("  - Name:", token.name());
console.log("  - Symbol:", token.symbol());
console.log("  - Owner:", token.owner());

vm.stopBroadcast();
```

### 4. Use Numbered Scripts

```
script/
├── 01_DeployToken.s.sol
├── 02_DeployStaking.s.sol
├── 03_ConfigurePermissions.s.sol
└── 04_TransferOwnership.s.sol
```

### 5. Test Scripts

```solidity
contract DeployTokenTest is Test {
    DeployToken deployer;

    function setUp() public {
        deployer = new DeployToken();
        // Set required env vars
        vm.setEnv("PRIVATE_KEY", vm.toString(uint256(1)));
    }

    function testDeploy() public {
        deployer.run();
        // Verify deployment
    }
}
```

### 6. Handle Failures Gracefully

```solidity
function run() external {
    uint256 deployerKey = vm.envUint("PRIVATE_KEY");

    vm.startBroadcast(deployerKey);

    try new Token("Name", "SYM", 18) returns (Token token) {
        console.log("Success:", address(token));
    } catch Error(string memory reason) {
        console.log("Failed:", reason);
    }

    vm.stopBroadcast();
}
```

## Upgrade Patterns

### Transparent Proxy

```solidity
import {TransparentUpgradeableProxy} from "@openzeppelin/contracts/proxy/transparent/TransparentUpgradeableProxy.sol";
import {ProxyAdmin} from "@openzeppelin/contracts/proxy/transparent/ProxyAdmin.sol";

contract DeployUpgradeable is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerKey);

        // Deploy implementation
        TokenV1 impl = new TokenV1();

        // Deploy proxy admin
        ProxyAdmin admin = new ProxyAdmin(msg.sender);

        // Deploy proxy
        bytes memory initData = abi.encodeCall(TokenV1.initialize, ("Name", "SYM"));
        TransparentUpgradeableProxy proxy = new TransparentUpgradeableProxy(
            address(impl),
            address(admin),
            initData
        );

        vm.stopBroadcast();

        console.log("Implementation:", address(impl));
        console.log("ProxyAdmin:", address(admin));
        console.log("Proxy:", address(proxy));
    }
}
```

### UUPS Proxy

```solidity
import {ERC1967Proxy} from "@openzeppelin/contracts/proxy/ERC1967/ERC1967Proxy.sol";

contract DeployUUPS is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerKey);

        // Deploy implementation
        TokenV1 impl = new TokenV1();

        // Deploy proxy
        bytes memory initData = abi.encodeCall(TokenV1.initialize, ("Name", "SYM"));
        ERC1967Proxy proxy = new ERC1967Proxy(address(impl), initData);

        vm.stopBroadcast();

        console.log("Implementation:", address(impl));
        console.log("Proxy:", address(proxy));
    }
}
```
