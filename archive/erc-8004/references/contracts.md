# ERC-8004 Smart Contracts

**Repository:** https://github.com/erc-8004/erc-8004-contracts

All contracts are UUPS-upgradeable (OpenZeppelin v5.4.0), using ERC-7201 namespaced storage. Solidity 0.8.24, Shanghai EVM, optimizer enabled (200 runs, viaIR).

## Contract Addresses

Deterministic cross-chain vanity addresses via CREATE2 (SAFE Singleton Factory at `0x914d7Fec6aaC8cd542e72Bca78B30650d45643d7`).

### Mainnet (Ethereum, Base, Polygon, Arbitrum, Optimism, Avalanche, Celo, Gnosis, Linea, Mantle, MegaETH, Scroll, Taiko, Monad, BSC)

| Contract | Address |
|----------|---------|
| IdentityRegistry | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` |
| ReputationRegistry | `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` |
| ValidationRegistry | `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` |

### Testnet (Sepolia, Base Sepolia, + corresponding testnets)

| Contract | Address |
|----------|---------|
| IdentityRegistry | `0x8004A818BFB912233c491871b3d84c89A494BD9e` |
| ReputationRegistry | `0x8004B663056A597Dffe9eCcC1965A193B7388713` |
| ValidationRegistry | `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` |

**Owner:** `0x547289319C3e6aedB179C0b8e8aF0B5ACd062603`

## IdentityRegistryUpgradeable

**Inherits:** `ERC721URIStorageUpgradeable`, `OwnableUpgradeable`, `UUPSUpgradeable`, `EIP712Upgradeable`

**Version:** 2.0.0

### Storage Layout

```solidity
// Slot 0 (shared with MinimalUUPS for upgrade persistence)
address private _identityRegistry;

// ERC-7201 namespaced storage
struct IdentityRegistryStorage {
    uint256 _lastId;
    mapping(uint256 => mapping(string => bytes)) _metadata;  // agentId => key => value
}
```

### Registration Functions

```solidity
// Mint without URI (set later via setAgentURI)
function register() external returns (uint256 agentId)

// Mint with URI
function register(string agentURI) external returns (uint256 agentId)

// Mint with URI and initial metadata
function register(string agentURI, MetadataEntry[] calldata metadata) external returns (uint256 agentId)

struct MetadataEntry {
    string metadataKey;
    bytes metadataValue;
}
```

All variants auto-set `agentWallet` metadata to `msg.sender`. The reserved `agentWallet` key is rejected in the metadata array.

### URI Management

```solidity
function setAgentURI(uint256 agentId, string calldata newURI) external
// Owner or operator only. Emits URIUpdated.
```

### Metadata Functions

```solidity
function getMetadata(uint256 agentId, string memory metadataKey) external view returns (bytes memory)
function setMetadata(uint256 agentId, string memory metadataKey, bytes memory metadataValue) external
// Owner or operator only. Reverts if metadataKey == "agentWallet".
```

### Agent Wallet (EIP-712 Verified)

```solidity
// Requires signature from newWallet (EIP-712 for EOA, ERC-1271 for smart contract wallet)
// Deadline max 5 minutes from current block.timestamp
function setAgentWallet(uint256 agentId, address newWallet, uint256 deadline, bytes calldata signature) external

function getAgentWallet(uint256 agentId) external view returns (address)

function unsetAgentWallet(uint256 agentId) external
```

EIP-712 domain: name `"ERC8004IdentityRegistry"`, version `"1"`. Typed data: `AgentWalletSet(uint256 agentId, address newWallet, address owner, uint256 deadline)`.

On NFT transfer, `agentWallet` is automatically cleared (Checks-Effects-Interactions pattern in `_update`).

### Authorization

```solidity
function isAuthorizedOrOwner(address spender, uint256 agentId) external view returns (bool)
// Used by Reputation and Validation registries to check permissions
```

### Events

```solidity
event Registered(uint256 indexed agentId, string agentURI, address indexed owner)
event MetadataSet(uint256 indexed agentId, string indexed indexedMetadataKey, string metadataKey, bytes metadataValue)
event URIUpdated(uint256 indexed agentId, string newURI, address indexed updatedBy)
```

## ReputationRegistryUpgradeable

**Inherits:** `OwnableUpgradeable`, `UUPSUpgradeable`

**Version:** 2.0.0

### Storage Layout

```solidity
struct Feedback {
    int128 value;       // signed fixed-point (max abs 1e38)
    uint8 valueDecimals; // 0-18
    bool isRevoked;
    string tag1;
    string tag2;
}

struct ReputationRegistryStorage {
    // agentId => clientAddr => feedbackIndex (1-indexed) => Feedback
    mapping(uint256 => mapping(address => mapping(uint64 => Feedback))) _feedback;
    mapping(uint256 => mapping(address => uint64)) _lastIndex;
    // Response tracking (counters only, not stored content)
    mapping(uint256 => mapping(address => mapping(uint64 => mapping(address => uint64)))) _responseCount;
    mapping(uint256 => mapping(address => mapping(uint64 => address[]))) _responders;
    mapping(uint256 => mapping(address => mapping(uint64 => mapping(address => bool)))) _responderExists;
    // Client tracking
    mapping(uint256 => address[]) _clients;
    mapping(uint256 => mapping(address => bool)) _clientExists;
}
```

### Write Functions

```solidity
function giveFeedback(
    uint256 agentId, int128 value, uint8 valueDecimals,
    string calldata tag1, string calldata tag2,
    string calldata endpoint, string calldata feedbackURI, bytes32 feedbackHash
) external
// Self-feedback rejected: calls isAuthorizedOrOwner() and reverts if true.
// endpoint, feedbackURI, feedbackHash emitted but NOT stored.

function revokeFeedback(uint256 agentId, uint64 feedbackIndex) external
// Only the original clientAddress can revoke.

function appendResponse(
    uint256 agentId, address clientAddress, uint64 feedbackIndex,
    string calldata responseURI, bytes32 responseHash
) external
// Anyone can respond. Only counters tracked, not content.
```

### Read Functions

```solidity
function readFeedback(uint256 agentId, address clientAddress, uint64 feedbackIndex)
    external view returns (int128 value, uint8 valueDecimals, string tag1, string tag2, bool isRevoked)
// feedbackIndex is 1-indexed

function getSummary(uint256 agentId, address[] calldata clientAddresses, string tag1, string tag2)
    external view returns (uint64 count, int128 summaryValue, uint8 summaryValueDecimals)
// clientAddresses MUST be non-empty - REVERTS if empty (Sybil protection).
// Callers must supply a trusted reviewer list.
// Empty strings for tag1/tag2 act as wildcards.
// Aggregation: normalizes to 18-decimal WAD, averages, scales to mode precision.

function readAllFeedback(uint256 agentId, address[] calldata clientAddresses,
    string tag1, string tag2, bool includeRevoked) external view returns (...)
// If clientAddresses is empty, uses all tracked clients.

function getResponseCount(uint256 agentId, address clientAddress,
    uint64 feedbackIndex, address[] responders) external view returns (uint64)
// address(0) = all clients; feedbackIndex 0 = all feedbacks.

function getClients(uint256 agentId) external view returns (address[] memory)
function getLastIndex(uint256 agentId, address clientAddress) external view returns (uint64)
```

### Events

```solidity
event NewFeedback(uint256 indexed agentId, address indexed clientAddress, uint64 feedbackIndex,
    int128 value, uint8 valueDecimals, string indexed indexedTag1,
    string tag1, string tag2, string endpoint, string feedbackURI, bytes32 feedbackHash)
event FeedbackRevoked(uint256 indexed agentId, address indexed clientAddress, uint64 indexed feedbackIndex)
event ResponseAppended(uint256 indexed agentId, address indexed clientAddress,
    uint64 feedbackIndex, address indexed responder, string responseURI, bytes32 responseHash)
```

## ValidationRegistryUpgradeable

**Inherits:** `OwnableUpgradeable`, `UUPSUpgradeable`

**Version:** 2.0.0

### Storage Layout

```solidity
struct ValidationStatus {
    address validatorAddress;
    uint256 agentId;
    uint8 response;        // 0-100
    bytes32 responseHash;
    string tag;
    uint256 lastUpdate;
    bool hasResponse;
}

struct ValidationRegistryStorage {
    mapping(bytes32 => ValidationStatus) validations;        // requestHash => status
    mapping(uint256 => bytes32[]) _agentValidations;         // agentId => requestHashes
    mapping(address => bytes32[]) _validatorRequests;        // validatorAddress => requestHashes
}
```

### Functions

```solidity
function validationRequest(
    address validatorAddress, uint256 agentId,
    string requestURI, bytes32 requestHash
) external
// Must be called by owner/operator. Duplicate requestHash rejected.

function validationResponse(
    bytes32 requestHash, uint8 response,
    string responseURI, bytes32 responseHash, string tag
) external
// Must be called by the validatorAddress from the request.
// response: 0=failed, 100=passed, intermediate for spectrum.
// Can be called multiple times (progressive finality via tag).

function getValidationStatus(bytes32 requestHash)
    external view returns (address, uint256, uint8, bytes32, string, uint256)

function getSummary(uint256 agentId, address[] calldata validatorAddresses, string tag)
    external view returns (uint64 count, uint8 avgResponse)
// ACCEPTS empty validatorAddresses (includes ALL validators - no filter).
// This differs from ReputationRegistry.getSummary() which REVERTS on empty.
// Only counts requests with hasResponse == true.

function getAgentValidations(uint256 agentId) external view returns (bytes32[] memory)
function getValidatorRequests(address validatorAddress) external view returns (bytes32[] memory)
```

### Events

```solidity
event ValidationRequest(address indexed validatorAddress, uint256 indexed agentId,
    string requestURI, bytes32 indexed requestHash)
event ValidationResponse(address indexed validatorAddress, uint256 indexed agentId,
    bytes32 indexed requestHash, uint8 response,
    string responseURI, bytes32 responseHash, string tag)
```

## Deployment Architecture

### Two-Phase Vanity Deployment

1. Deploy `MinimalUUPS` via CREATE2 (stores `_identityRegistry` at slot 0)
2. Deploy three vanity proxies via CREATE2 pointing to MinimalUUPS
3. Deploy three real implementations via CREATE2
4. Upgrade proxies to real implementations (slot 0 data persists)

This enables deterministic vanity addresses across all EVM chains.

### Dependencies

- OpenZeppelin Contracts Upgradeable v5.4.0
- SAFE Singleton Factory (`0x914d7Fec6aaC8cd542e72Bca78B30650d45643d7`)
- Hardhat v3 with viem v2.38 for testing/deployment

### ABI Files

Pre-built ABI JSON files available in the contracts repository:
- `abis/IdentityRegistry.json`
- `abis/ReputationRegistry.json`
- `abis/ValidationRegistry.json`
