# Agent0 TypeScript SDK

**Package:** `agent0-sdk` (npm)
**Version:** 1.5.3+
**License:** MIT
**Node.js:** >= 22.0.0
**Repository:** https://github.com/agent0lab/agent0-ts
**Docs:** https://sdk.ag0.xyz
**Docs Source:** https://github.com/agent0lab/agent0-sdk-docs

## Installation

```bash
npm install agent0-sdk
```

**Runtime dependencies:** `viem ^2.37.5`, `graphql-request ^6.1.0`, `ipfs-http-client ^60.0.1`

## SDK Initialization

```typescript
import { SDK } from 'agent0-sdk';

const sdk = new SDK({
  chainId: number,              // Required: chain ID (1, 8453, 11155111, 84532, 137)
  rpcUrl: string,               // Required: Ethereum RPC endpoint
  privateKey?: string,          // Server-side signing
  walletProvider?: EIP1193Provider, // Browser-side (ERC-6963)
  ipfs?: 'pinata' | 'filecoinPin' | 'node',
  pinataJwt?: string,
  filecoinPrivateKey?: string,
  ipfsNodeUrl?: string,
  subgraphUrl?: string,         // Override default subgraph
  subgraphOverrides?: Record<ChainId, string>,
  registryOverrides?: Record<ChainId, Record<string, Address>>,
});
```

`sdk.isReadOnly` is `true` when no signer is configured (search/discovery still works).

## Agent Lifecycle

### Create Agent

```typescript
const agent = sdk.createAgent(
  'AgentName',
  'Description of what this agent does',
  'https://example.com/image.png'  // optional
);
```

### Configure Agent (Sync - Returns `this`)

```typescript
agent.updateInfo('NewName', 'New description', 'https://new-image.png');
agent.setActive(true);
agent.setX402Support(true);
agent.setTrust(true, false, false);  // reputation, cryptoEconomic, teeAttestation

// OASF taxonomy
agent.addSkill('natural_language_processing/summarization', true);  // validate=true
agent.addDomain('finance_and_business/investment_services', true);
agent.removeSkill('old/skill');
agent.removeDomain('old/domain');

// ENS
agent.setENS('myagent.eth', 'v1');

// Metadata
agent.setMetadata({ customKey: 'customValue' });
agent.delMetadata('customKey');

// Remove endpoints
agent.removeEndpoint('MCP');       // by type
agent.removeEndpoint(undefined, 'https://old.com');  // by value
agent.removeEndpoints();           // all
```

### Configure Agent (Async)

```typescript
// Auto-fetches tools/prompts/resources from MCP endpoint
await agent.setMCP('https://mcp.example.com', '2025-06-18', true);

// Auto-fetches skills from A2A agent card
await agent.setA2A('https://example.com/.well-known/agent-card.json', '0.3.0', true);
```

### Register on IPFS

```typescript
const tx = await agent.registerIPFS();
const { receipt, result } = await tx.waitConfirmed();
// result: RegistrationFile with agentId, agentURI (ipfs://CID), etc.
console.log(result.agentId);  // "84532:42"
```

Two transactions: (1) mint NFT via `register()`, (2) upload to IPFS + `setAgentURI()`.

### Register with HTTP URI

```typescript
// Generate and host the file yourself
const regFile = agent.getRegistrationFile();
// Host regFile JSON at your URL, then:
const tx = await agent.registerHTTP('https://example.com/agent.json');
```

### Load Existing Agent

```typescript
const agent = await sdk.loadAgent('84532:42');  // mutable Agent object
// Make changes...
agent.updateInfo(undefined, 'Updated description');
await agent.registerIPFS();  // re-uploads and updates URI
```

### Update Agent URI

```typescript
await agent.setAgentURI('ipfs://newCID');  // updates on-chain only
```

### Agent Properties (Read-Only)

```typescript
agent.agentId          // "84532:42"
agent.agentURI         // "ipfs://Qm..."
agent.name             // "AgentName"
agent.description      // "Description"
agent.image            // "https://..."
agent.mcpEndpoint      // "https://mcp..."
agent.a2aEndpoint      // "https://a2a..."
agent.ensEndpoint      // "myagent.eth"
agent.walletAddress    // "0x..."
agent.mcpTools         // ["tool1", "tool2"]
agent.mcpPrompts       // ["prompt1"]
agent.mcpResources     // ["resource1"]
agent.a2aSkills        // ["skill1"]
agent.getRegistrationFile()  // full RegistrationFile object
agent.getMetadata()    // { key: value }
```

## Wallet Management

### Set Agent Wallet (EIP-712)

```typescript
// If SDK signer IS the new wallet:
await agent.setWallet('0xNewWallet');

// If new wallet is a different key:
await agent.setWallet('0xNewWallet', {
  newWalletPrivateKey: '0x...',  // pragma: allowlist secret
  deadline: Math.floor(Date.now() / 1000) + 300,  // 5 min max
});

// Pre-computed signature (for smart contract wallets / ERC-1271):
await agent.setWallet('0xNewWallet', { signature: '0x...' });
```

### Unset / Read Wallet

```typescript
await agent.unsetWallet();
const wallet = await agent.getWallet();
```

## Agent Transfer

```typescript
// From a loaded Agent object
const tx = await agent.transfer('0xNewOwner');
const { result } = await tx.waitConfirmed();
// result: { txHash, from, to, agentId }

// Top-level convenience (when you only have an agentId string)
const tx = await sdk.transferAgent('84532:42', '0xNewOwner');
const { result } = await tx.waitConfirmed();

// Check ownership
const isOwner = await sdk.isAgentOwner('84532:42', '0x...');
const owner = await sdk.getAgentOwner('84532:42');
```

`sdk.transferAgent()` internally loads the agent then calls `agent.transfer()`. Use the top-level method when working with agentId strings (common when reading from subgraph); use `agent.transfer()` when you already have a loaded Agent instance.

On transfer, `agentWallet` is cleared. New owner must re-verify.

## Operator Management

`addOperator()` and `removeOperator()` are **not available** in the TypeScript SDK. Use direct contract calls via `sdk.registries()` + viem:

```typescript
import { getContract } from 'viem';

const registries = sdk.registries();
// registries.identityRegistry = "0x8004A169..."

// Use viem directly with a minimal ABI for approve/setApprovalForAll
// See the IdentityRegistry ABI for operator functions (ERC-721 approval)
```

The Python SDK has `agent.addOperator()` and `agent.removeOperator()` natively.

## Discovery and Search

### Get Single Agent

```typescript
const summary = await sdk.getAgent('84532:42');  // AgentSummary (read-only, from subgraph)
```

### Search Agents

```typescript
const agents = await sdk.searchAgents(
  {
    // Text
    name: 'crypto',              // substring match
    description: 'market',

    // Endpoints
    hasMCP: true,
    hasA2A: true,
    hasOASF: true,
    mcpContains: 'example.com',

    // Capabilities (ANY semantics - matches if at least one found)
    mcpTools: ['financial_analyzer'],
    a2aSkills: ['trading'],
    oasfSkills: ['data_engineering/data_transformation_pipeline'],
    oasfDomains: ['finance_and_business'],

    // Status
    active: true,
    x402support: true,
    supportedTrust: ['reputation'],

    // Identity
    chains: [8453, 84532],       // specific chains; 'all' for all
    agentIds: ['84532:42'],
    owners: ['0x...'],
    walletAddress: '0x...',

    // Time
    registeredAtFrom: 1700000000,
    updatedAtTo: 1800000000,

    // Metadata (two-phase prefilter)
    hasMetadataKey: 'customKey',

    // Semantic search
    keyword: 'crypto market analysis',

    // Reputation (two-phase prefilter)
    feedback: {
      hasFeedback: true,
      minValue: 80,
      minCount: 5,
      tag1: 'starred',
      fromReviewers: ['0x...'],
    },
  },
  {
    sort: ['averageValue:desc', 'updatedAt:desc'],
    semanticMinScore: 0.5,
    semanticTopK: 100,
  }
);
```

**Default chains:** chain 1 + SDK's chainId. Use `chains: 'all'` for all 5 indexed chains.

### AgentSummary Fields

```typescript
interface AgentSummary {
  chainId: number;
  agentId: string;         // "chainId:tokenId"
  name: string;
  description: string;
  image?: string;
  owners: Address[];
  operators: Address[];
  mcp?: string;            // MCP endpoint
  a2a?: string;            // A2A endpoint
  web?: string;
  email?: string;
  ens?: string;
  did?: string;
  walletAddress?: string;
  supportedTrusts: string[];
  a2aSkills: string[];
  mcpTools: string[];
  mcpPrompts: string[];
  mcpResources: string[];
  oasfSkills: string[];
  oasfDomains: string[];
  active: boolean;
  x402support: boolean;
  createdAt?: number;
  updatedAt?: number;
  lastActivity?: number;
  agentURI?: string;
  agentURIType?: string;
  feedbackCount?: number;
  averageValue?: number;
  semanticScore?: number;
  extras: Record<string, any>;
}
```

## Feedback System

### Give Feedback

```typescript
// Minimal (value only)
const tx = await sdk.giveFeedback('84532:42', 85);

// Full
const feedbackFile = await sdk.prepareFeedbackFile({
  text: 'Great analysis',
  capability: 'tools',
  name: 'financial_analyzer',
  skill: 'financial_analysis',
  task: 'analyze_portfolio',
  context: { sessionId: 'abc123' },
  proofOfPayment: {
    txHash: '0x...', chainId: '8453',
    fromAddress: '0x...', toAddress: '0x...',
  },
});

const tx = await sdk.giveFeedback(
  '84532:42',   // agentId
  85,            // value
  'starred',     // tag1
  'finance',     // tag2
  'https://mcp.example.com',  // endpoint
  feedbackFile   // off-chain file
);
const { result } = await tx.waitConfirmed();
```

### Read Feedback

```typescript
// Single feedback
const feedback = await sdk.getFeedback('84532:42', '0xClientAddr', 0);

// Search feedback
const results = await sdk.searchFeedback({
  agentId: '84532:42',
  tags: ['starred'],
  // Or multi-agent:
  agents: ['84532:42', '84532:43'],
  // Or by reviewer:
  reviewers: ['0x...'],
});

// Reputation summary
const summary = await sdk.getReputationSummary('84532:42', 'starred');
// { count: 15, averageValue: 87.5 }
```

### Manage Feedback

```typescript
// Agent responds to feedback
await sdk.appendResponse('84532:42', '0xClient', 0, {
  uri: 'ipfs://responseFile',
  hash: '0x...',
});

// Revoke your own feedback
await sdk.revokeFeedback('84532:42', 0);
```

## TransactionHandle Pattern

All write operations return a `TransactionHandle<T>`:

```typescript
const tx = await sdk.giveFeedback(...);
tx.hash;  // transaction hash (immediately available)

// Wait for mining:
const { receipt, result } = await tx.waitConfirmed();
// or with options:
const { receipt, result } = await tx.waitMined({
  timeoutMs: 60000,
  confirmations: 1,
  throwOnRevert: true,
});
```

Multiple calls to `waitConfirmed()` reuse the same promise (memoized).

## Browser Support (ERC-6963)

```typescript
import { discoverEip6963Providers, connectEip1193 } from 'agent0-sdk/eip6963';

const providers = await discoverEip6963Providers({ timeoutMs: 800 });
const { provider } = providers[0];
const walletProvider = await connectEip1193(provider);

const sdk = new SDK({
  chainId: 84532,
  rpcUrl: 'https://...',
  walletProvider,  // writes go through browser wallet
});
```

## AgentId Format

String format `"chainId:tokenId"` (e.g., `"11155111:123"`, `"84532:42"`). When no chain prefix, SDK's default chainId is used.

## Type Reference

```typescript
type AgentId = string;     // "chainId:tokenId"
type ChainId = number;
type Address = string;     // 0x-hex
type URI = string;
type Timestamp = number;

enum EndpointType { MCP, A2A, ENS, DID, WALLET = 'wallet', OASF }
enum TrustModel {
  REPUTATION = 'reputation',
  CRYPTO_ECONOMIC = 'crypto-economic',
  TEE_ATTESTATION = 'tee-attestation',
}

interface Endpoint {
  type: EndpointType;
  value: string;
  meta: Record<string, any>;
}

interface RegistrationFile {
  agentId?: string;
  agentURI?: string;
  name: string;
  description: string;
  image?: string;
  walletAddress?: string;
  walletChainId?: number;
  endpoints: Endpoint[];
  trustModels: TrustModel[];
  owners: Address[];
  operators: Address[];
  active: boolean;
  x402support: boolean;
  metadata: Record<string, any>;
  updatedAt: Timestamp;
}

interface Feedback {
  id: [AgentId, Address, number];
  agentId: string;
  reviewer: string;
  txHash?: string;
  value?: number;
  tags: string[];
  endpoint?: string;
  text?: string;
  context?: Record<string, any>;
  proofOfPayment?: Record<string, any>;
  fileURI?: string;
  createdAt: number;
  answers: any[];
  isRevoked: boolean;
  capability?: string;
  name?: string;
  skill?: string;
  task?: string;
}
```

## Supported Networks

| Network | Chain ID | Status |
|---------|----------|--------|
| Ethereum Mainnet | 1 | Indexed |
| Base Mainnet | 8453 | Indexed |
| Polygon Mainnet | 137 | Indexed |
| Ethereum Sepolia | 11155111 | Indexed |
| Base Sepolia | 84532 | Indexed |

Coming soon: BNB Chain, Monad, additional networks.

## Architecture

```
SDK
 ├── Agent (lifecycle, registration)
 │     ├── EndpointCrawler (MCP/A2A auto-fetch, soft-fail)
 │     ├── IPFSClient (Pinata / FilecoinPin / local node)
 │     └── ViemChainClient (EVM RPC -> Identity Registry)
 ├── AgentIndexer (multi-chain search)
 │     ├── SubgraphClient (The Graph GraphQL)
 │     └── SemanticSearchClient (semantic-search.ag0.xyz)
 └── FeedbackManager (reputation)
       ├── ViemChainClient (-> Reputation Registry)
       ├── IPFSClient (feedback file storage)
       └── SubgraphClient (feedback search)
```

**Key patterns:**
- **Soft-fail crawling**: MCP/A2A capability extraction never throws; registration continues without capabilities if endpoint unreachable
- **Read-only mode**: All discovery/search works without a signer
- **Two-phase feedback filtering**: Reputation-gated searches first query feedback subgraph for matching agentIds, then intersect with main query
- **Backward compatibility**: Handles old field names (`score` vs `value`, `services[]` vs `endpoints[]`, `x402support` vs `x402Support`)
