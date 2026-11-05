# ERC-8004 Specification

**EIP:** 8004
**Title:** Trustless Agents
**Status:** Draft
**Type:** Standards Track (ERC)
**Created:** 2025-08-13
**Requires:** EIP-155, EIP-712, ERC-721, ERC-1271
**Authors:** Marco De Rossi (@MarcoMetaMask), Davide Crapis (@dcrapis), Jordan Ellis (Google), Erik Reppel (Coinbase)
**Discussion:** https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098
**Best Practices:** https://github.com/erc-8004/best-practices

## Abstract

This protocol uses blockchains to discover, choose, and interact with agents across organizational boundaries without pre-existing trust, enabling open-ended agent economies.

Trust models are pluggable and tiered, with security proportional to value at risk. Developers choose from: reputation systems using client feedback, validation via stake-secured re-execution, zero-knowledge machine learning (zkML) proofs, or trusted execution environment (TEE) oracles.

## Motivation

MCP allows servers to list capabilities (prompts, resources, tools, completions). A2A handles agent authentication, skills advertisement via AgentCards, messaging, and task-lifecycle orchestration. However, these agent communication protocols don't cover agent discovery and trust.

This ERC addresses this through three lightweight registries deployed as per-chain singletons:

- **Identity Registry** - ERC-721 with URIStorage extension resolving to agent registration files
- **Reputation Registry** - Standard interface for posting/fetching feedback signals with on-chain and off-chain aggregation
- **Validation Registry** - Generic hooks for independent validator checks (stakers, zkML verifiers, TEE oracles)

Payments are orthogonal and not covered. Examples show how x402 payments can enrich feedback signals.

## Specification

Key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHOULD", "RECOMMENDED", "MAY", "OPTIONAL" per RFC 2119 and RFC 8174.

### Identity Registry

Uses ERC-721 with URIStorage extension. Each agent is globally identified by:

- **agentRegistry**: `{namespace}:{chainId}:{identityRegistry}` (e.g., `eip155:1:0x742...`)
  - namespace: chain family identifier (`eip155` for EVM)
  - chainId: blockchain network identifier
  - identityRegistry: deployed contract address
- **agentId**: ERC-721 tokenId (assigned incrementally)

Throughout this spec: `tokenId` = `agentId`, `tokenURI` = `agentURI`. The ERC-721 owner owns the agent and can delegate management to operators.

#### Agent URI and Registration File

The `agentURI` MUST resolve to the agent registration file. MAY use any URI scheme (`ipfs://`, `https://`). Updated via `setAgentURI()`.

Registration file MUST have this structure:

```jsonc
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "myAgentName",
  "description": "Natural language description - what it does, pricing, interaction methods",
  "image": "https://example.com/agentimage.png",
  "services": [
    { "name": "web", "endpoint": "https://web.agentxyz.com/" },
    { "name": "A2A", "endpoint": "https://agent.example/.well-known/agent-card.json", "version": "0.3.0" },
    { "name": "MCP", "endpoint": "https://mcp.agent.eth/", "version": "2025-06-18" },
    { "name": "OASF", "endpoint": "ipfs://{cid}", "version": "0.8",
      "skills": [],   // OPTIONAL
      "domains": []   // OPTIONAL
    },
    { "name": "ENS", "endpoint": "vitalik.eth", "version": "v1" },
    { "name": "DID", "endpoint": "did:method:foobar", "version": "v1" },
    { "name": "email", "endpoint": "mail@myagent.com" }
  ],
  "x402Support": false,
  "active": true,
  "registrations": [
    { "agentId": 22, "agentRegistry": "{namespace}:{chainId}:{identityRegistry}" }
  ],
  "supportedTrust": ["reputation", "crypto-economic", "tee-attestation"]
}
```

The `type`, `name`, `description`, and `image` fields SHOULD ensure ERC-721 app compatibility. Endpoint types and count are fully customizable. The `version` field is SHOULD, not MUST.

#### Endpoint Domain Verification (Optional)

An agent MAY prove control of an HTTPS endpoint-domain by publishing `https://{endpoint-domain}/.well-known/agent-registration.json` containing at least a `registrations` list. Verifiers MAY treat the domain as verified if the file includes a `registrations` entry matching the on-chain agent. If the endpoint-domain is the same domain serving the `agentURI`, this check is unnecessary.

Agents SHOULD have at least one registration. All registration fields are mandatory.

The `supportedTrust` field is OPTIONAL. If absent/empty, ERC-8004 is used only for discovery.

#### On-chain Metadata

```solidity
function getMetadata(uint256 agentId, string memory metadataKey) external view returns (bytes memory)
function setMetadata(uint256 agentId, string memory metadataKey, bytes memory metadataValue) external

event MetadataSet(uint256 indexed agentId, string indexed indexedMetadataKey, string metadataKey, bytes metadataValue)
```

The key `agentWallet` is **reserved** - cannot be set via `setMetadata()` or during `register()`. It represents the payment address and defaults to the owner's address. To change it, the owner must prove control of the new wallet via EIP-712 (EOA) or ERC-1271 (smart contract wallet):

```solidity
function setAgentWallet(uint256 agentId, address newWallet, uint256 deadline, bytes calldata signature) external
function getAgentWallet(uint256 agentId) external view returns (address)
function unsetAgentWallet(uint256 agentId) external
```

On transfer, `agentWallet` is automatically cleared to zero address.

#### Registration

```solidity
struct MetadataEntry {
    string metadataKey;
    bytes metadataValue;
}

function register(string agentURI, MetadataEntry[] calldata metadata) external returns (uint256 agentId)
function register(string agentURI) external returns (uint256 agentId)
function register() external returns (uint256 agentId)  // agentURI added later via setAgentURI()
```

Emits: Transfer event, MetadataSet for `agentWallet`, MetadataSet for each additional entry, and:

```solidity
event Registered(uint256 indexed agentId, string agentURI, address indexed owner)
```

#### Update agentURI

```solidity
function setAgentURI(uint256 agentId, string calldata newURI) external
event URIUpdated(uint256 indexed agentId, string newURI, address indexed updatedBy)
```

For on-chain storage, use base64-encoded data URI: `data:application/json;base64,eyJ0eXBlIjoi...`

### Reputation Registry

Initialized with `initialize(address identityRegistry_)`. Identity registry address visible via `getIdentityRegistry()`.

Feedback consists of: signed fixed-point `value` (int128) + `valueDecimals` (uint8, 0-18), optional `tag1`/`tag2`, optional `endpoint` URI, optional feedback file URI + hash. IPFS recommended for indexing by subgraphs.

#### Value/ValueDecimals Examples

| tag1 | Measures | Example | value | valueDecimals |
|------|----------|---------|-------|---------------|
| `starred` | Quality 0-100 | 87/100 | 87 | 0 |
| `reachable` | Endpoint reachable | true | 1 | 0 |
| `ownerVerified` | Owner verified | true | 1 | 0 |
| `uptime` | Uptime % | 99.77% | 9977 | 2 |
| `successRate` | Success rate % | 89% | 89 | 0 |
| `responseTime` | Latency ms | 560ms | 560 | 0 |
| `blocktimeFreshness` | Block delay | 4 blocks | 4 | 0 |
| `revenues` | Revenue USD | $560 | 560 | 0 |
| `tradingYield` | Yield (tag2=period) | 4% | 4 | 2 |

#### Giving Feedback

```solidity
function giveFeedback(
    uint256 agentId, int128 value, uint8 valueDecimals,
    string calldata tag1, string calldata tag2,
    string calldata endpoint, string calldata feedbackURI, bytes32 feedbackHash
) external
```

Requirements: agentId must be registered, valueDecimals 0-18, submitter MUST NOT be agent owner or approved operator. tag1, tag2, endpoint, feedbackURI, feedbackHash are OPTIONAL.

```solidity
event NewFeedback(
    uint256 indexed agentId, address indexed clientAddress, uint64 feedbackIndex,
    int128 value, uint8 valueDecimals, string indexed indexedTag1,
    string tag1, string tag2, string endpoint, string feedbackURI, bytes32 feedbackHash
)
```

Stored on-chain: value, valueDecimals, tag1, tag2, isRevoked, feedbackIndex (1-indexed). Emitted only: endpoint, feedbackURI, feedbackHash.

When feedback is given by an agent, it SHOULD use the on-chain `agentWallet` as clientAddress for reputation aggregation.

#### Revoking Feedback

```solidity
function revokeFeedback(uint256 agentId, uint64 feedbackIndex) external
event FeedbackRevoked(uint256 indexed agentId, address indexed clientAddress, uint64 indexed feedbackIndex)
```

#### Appending Responses

Anyone can respond (agent showing refund, aggregator tagging spam):

```solidity
function appendResponse(
    uint256 agentId, address clientAddress, uint64 feedbackIndex,
    string calldata responseURI, bytes32 responseHash
) external

event ResponseAppended(
    uint256 indexed agentId, address indexed clientAddress, uint64 feedbackIndex,
    address indexed responder, string responseURI, bytes32 responseHash
)
```

#### Read Functions

```solidity
// clientAddresses MUST be non-empty (Sybil protection). tag1/tag2 optional filters.
function getSummary(uint256 agentId, address[] calldata clientAddresses, string tag1, string tag2)
    external view returns (uint64 count, int128 summaryValue, uint8 summaryValueDecimals)

function readFeedback(uint256 agentId, address clientAddress, uint64 feedbackIndex)
    external view returns (int128 value, uint8 valueDecimals, string tag1, string tag2, bool isRevoked)

function readAllFeedback(uint256 agentId, address[] calldata clientAddresses,
    string tag1, string tag2, bool includeRevoked)
    external view returns (address[] memory, uint64[] memory, int128[] memory,
    uint8[] memory, string[] memory, string[] memory, bool[] memory)

function getResponseCount(uint256 agentId, address clientAddress,
    uint64 feedbackIndex, address[] responders) external view returns (uint64 count)

function getClients(uint256 agentId) external view returns (address[] memory)
function getLastIndex(uint256 agentId, address clientAddress) external view returns (uint64)
```

#### Off-Chain Feedback File Structure

```jsonc
{
  "agentRegistry": "eip155:1:{identityRegistry}",
  "agentId": 22,
  "clientAddress": "eip155:1:{clientAddress}",
  "createdAt": "2025-09-23T12:00:00Z",
  "value": 100,
  "valueDecimals": 0,
  // ALL OPTIONAL:
  "tag1": "foo",
  "tag2": "bar",
  "endpoint": "https://agent.example.com/GetPrice",
  "mcp": { "tool": "ToolName" },
  "a2a": { "skills": [], "contextId": "...", "taskId": "..." },
  "oasf": { "skills": [], "domains": [] },
  "proofOfPayment": {
    "fromAddress": "0x...", "toAddress": "0x...",
    "chainId": "1", "txHash": "0x..."
  }
}
```

### Validation Registry

Enables agents to request third-party verification. Validators can use stake-secured re-execution, zkML verifiers, or TEE oracles.

#### Validation Request

```solidity
function validationRequest(
    address validatorAddress, uint256 agentId,
    string requestURI, bytes32 requestHash
) external

event ValidationRequest(
    address indexed validatorAddress, uint256 indexed agentId,
    string requestURI, bytes32 indexed requestHash
)
```

MUST be called by owner/operator of agentId. requestHash = keccak256 of request payload, identifies the request.

#### Validation Response

```solidity
function validationResponse(
    bytes32 requestHash, uint8 response,
    string responseURI, bytes32 responseHash, string tag
) external

event ValidationResponse(
    address indexed validatorAddress, uint256 indexed agentId,
    bytes32 indexed requestHash, uint8 response,
    string responseURI, bytes32 responseHash, string tag
)
```

Only requestHash and response are mandatory. MUST be called by the validatorAddress from the original request. Response: 0-100 (0=failed, 100=passed, intermediate for spectrum outcomes). Can be called multiple times per requestHash for progressive finality (e.g., "soft_finality"/"hard_finality" via tag).

#### Read Functions

```solidity
function getValidationStatus(bytes32 requestHash)
    external view returns (address, uint256, uint8, bytes32, string, uint256)

function getSummary(uint256 agentId, address[] calldata validatorAddresses, string tag)
    external view returns (uint64 count, uint8 averageResponse)

function getAgentValidations(uint256 agentId) external view returns (bytes32[] memory)
function getValidatorRequests(address validatorAddress) external view returns (bytes32[] memory)
```

Incentives and slashing are managed by specific validation protocols, outside this registry's scope.

## Rationale

- **Agent communication protocols**: MCP and A2A are popular but more could emerge. The flexible registration file with open-ended endpoint lists combines AI primitives (MCP, A2A) with Web3 primitives (wallets, DIDs, ENS).
- **Feedback**: Leverages A2A nomenclature (tasks, skills) and MCP (tools, prompts) with complete flexibility in signal structure.
- **Gas Sponsorship**: Clients don't need registration; any app can implement frictionless feedback via EIP-7702.
- **Indexing**: On-chain data + IPFS makes subgraph indexing straightforward.
- **Deployment**: Singleton per chain. An agent registered on chain A can operate on other chains. Multi-chain registration is supported.

## Security Considerations

- **Sybil attacks**: Possible via fake feedback. Mitigated by reputation systems around reviewers and filtering by clientAddress (already protocol-enabled).
- **Audit trail**: On-chain pointers and hashes cannot be deleted.
- **Validator incentives**: Managed by specific validation protocols.
- **Capability guarantees**: ERC-8004 cannot cryptographically guarantee advertised capabilities are functional/non-malicious. The three trust models (reputation, validation, TEE) address this.
