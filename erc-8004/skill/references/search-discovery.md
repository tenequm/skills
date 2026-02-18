# Agent Search and Discovery

## Overview

ERC-8004 agents are discoverable through a subgraph (The Graph) that indexes both on-chain data and IPFS registration files. The Agent0 SDK provides a unified search API with multi-chain support, semantic search, and reputation-gated filtering.

## Search Methods

### Basic Search

```typescript
const sdk = new SDK({ chainId: 84532, rpcUrl: '...' });

// All active MCP agents
const agents = await sdk.searchAgents({ hasMCP: true, active: true });

// By name
const agents = await sdk.searchAgents({ name: 'crypto' });

// Get single agent
const agent = await sdk.getAgent('84532:42');
```

### Capability Search

```typescript
// By MCP tools (ANY semantics - matches if at least one listed tool found)
const agents = await sdk.searchAgents({
  mcpTools: ['financial_analyzer', 'price_feed'],
});

// By A2A skills
const agents = await sdk.searchAgents({
  a2aSkills: ['trading_analysis'],
});

// By OASF taxonomy
const agents = await sdk.searchAgents({
  oasfSkills: ['natural_language_processing/summarization'],
  oasfDomains: ['finance_and_business'],
});

// By trust model
const agents = await sdk.searchAgents({
  supportedTrust: ['reputation'],
});
```

### Multi-Chain Search

```typescript
// Default: queries chain 1 + SDK's chainId (de-duplicated)
const agents = await sdk.searchAgents({ active: true });

// Specific chains
const agents = await sdk.searchAgents({
  chains: [1, 8453, 137],  // Mainnet, Base, Polygon
  active: true,
});

// All indexed chains
const agents = await sdk.searchAgents({
  chains: 'all',  // 1, 8453, 137, 11155111, 84532
  active: true,
});
```

Results are merged and sorted client-side. AgentId format includes chainId prefix: `"8453:42"`.

### Semantic Search

```typescript
const agents = await sdk.searchAgents(
  { keyword: 'crypto market analysis' },
  {
    sort: ['semanticScore:desc'],
    semanticMinScore: 0.5,
    semanticTopK: 100,
  }
);
```

Uses external semantic search endpoint (`semantic-search.ag0.xyz`) for vector-based matching, then fetches agents from subgraph by ID.

### Reputation-Gated Search

```typescript
const agents = await sdk.searchAgents({
  active: true,
  feedback: {
    hasFeedback: true,
    minValue: 80,
    minCount: 5,
    tag1: 'starred',
    fromReviewers: ['0xTrustedReviewer'],
    endpoint: 'mcp',  // substring match on endpoint
    hasResponse: true,
  },
}, {
  sort: ['averageValue:desc'],
});
```

Two-phase filtering: queries feedback subgraph first for matching agentIds, then intersects with main query.

### Combined Search

```typescript
const agents = await sdk.searchAgents(
  {
    // Endpoint requirements
    hasMCP: true,
    hasOASF: true,

    // Capability requirements
    mcpTools: ['analyzer'],
    oasfDomains: ['finance_and_business'],

    // Status
    active: true,
    x402support: true,

    // Reputation
    feedback: {
      minValue: 80,
      minCount: 3,
    },

    // Time range
    updatedAtFrom: Math.floor(Date.now() / 1000) - 30 * 86400,  // last 30 days

    // Metadata
    hasMetadataKey: 'verified',
  },
  {
    sort: ['averageValue:desc', 'updatedAt:desc'],
  }
);
```

## Search Filters Reference

### Pushdown Filters (Sent to Subgraph)

| Filter | Type | Description |
|--------|------|-------------|
| `name` | string | Substring match on agent name |
| `description` | string | Substring match |
| `hasMCP` | boolean | Has MCP endpoint |
| `hasA2A` | boolean | Has A2A endpoint |
| `hasWeb` | boolean | Has web endpoint |
| `hasOASF` | boolean | Has OASF endpoint |
| `hasEndpoints` | boolean | Has any endpoints |
| `mcpContains` | string | MCP URL substring |
| `a2aContains` | string | A2A URL substring |
| `ensContains` | string | ENS name substring |
| `didContains` | string | DID substring |
| `mcpTools` | string[] | Match any listed tool |
| `mcpPrompts` | string[] | Match any listed prompt |
| `mcpResources` | string[] | Match any listed resource |
| `a2aSkills` | string[] | Match any listed skill |
| `oasfSkills` | string[] | Match any listed OASF skill |
| `oasfDomains` | string[] | Match any listed OASF domain |
| `supportedTrust` | string[] | Match any listed trust model |
| `active` | boolean | Active status |
| `x402support` | boolean | x402 payment support |
| `chains` | number[] or 'all' | Target chains |
| `agentIds` | string[] | Specific agent IDs |
| `owners` | string[] | Owner addresses |
| `operators` | string[] | Operator addresses |
| `walletAddress` | string | Agent wallet address |
| `registeredAtFrom` | number | Registration timestamp >= |
| `registeredAtTo` | number | Registration timestamp <= |
| `updatedAtFrom` | number | Update timestamp >= |
| `updatedAtTo` | number | Update timestamp <= |

### Two-Phase Prefilters (Separate Query Then Intersect)

| Filter | Type | Description |
|--------|------|-------------|
| `hasMetadataKey` | string | Agent has this metadata key |
| `metadataValue` | string | Metadata value match |
| `keyword` | string | Semantic vector search |
| `feedback.hasFeedback` | boolean | Has any feedback |
| `feedback.hasNoFeedback` | boolean | Has no feedback |
| `feedback.minValue` | number | Average value >= |
| `feedback.maxValue` | number | Average value <= |
| `feedback.minCount` | number | Feedback count >= |
| `feedback.maxCount` | number | Feedback count <= |
| `feedback.tag1` | string | Feedback tag1 filter |
| `feedback.tag2` | string | Feedback tag2 filter |
| `feedback.tag` | string | Matches tag1 OR tag2 |
| `feedback.fromReviewers` | string[] | Specific reviewer addresses |
| `feedback.endpoint` | string | Feedback endpoint substring |
| `feedback.hasResponse` | boolean | Has response from agent |
| `feedback.includeRevoked` | boolean | Include revoked feedback |

### Search Options

```typescript
interface SearchOptions {
  sort?: string[];           // e.g., ["averageValue:desc", "name:asc"]
  semanticMinScore?: number; // keyword searches only (default 0.5)
  semanticTopK?: number;     // keyword searches only
}
```

Sortable fields: `name`, `updatedAt`, `createdAt`, `averageValue`, `feedbackCount`, `semanticScore`, `lastActivity`.

## Subgraph Data Model

### Core Entities

```graphql
type Agent @entity {
  id: ID!                          # "chainId:agentId"
  chainId: Int!
  agentId: BigInt!
  agentURI: String
  agentURIType: String             # "ipfs" or "http"
  owner: Bytes!
  operators: [Bytes!]!
  createdAt: BigInt!
  updatedAt: BigInt!
  registrationFile: AgentRegistrationFile
  feedback: [Feedback!]! @derivedFrom(field: "agent")
  validations: [Validation!]! @derivedFrom(field: "agent")
  metadata: [AgentMetadata!]! @derivedFrom(field: "agent")
  totalFeedback: Int!
  lastActivity: BigInt
}

type AgentRegistrationFile @entity {
  id: ID!
  cid: String
  name: String
  description: String
  image: String
  active: Boolean
  x402Support: Boolean
  supportedTrusts: [String!]
  mcpEndpoint: String
  a2aEndpoint: String
  webEndpoint: String
  emailEndpoint: String
  ens: String
  did: String
  mcpTools: [String!]
  mcpPrompts: [String!]
  mcpResources: [String!]
  a2aSkills: [String!]
  oasfSkills: [String!]
  oasfDomains: [String!]
  hasOASF: Boolean
}

type Feedback @entity {
  id: ID!                          # "chainId:agentId:clientAddress:feedbackIndex"
  agent: Agent!
  clientAddress: Bytes!
  value: BigDecimal
  tag1: String
  tag2: String
  feedbackUri: String
  feedbackURIType: String
  feedbackHash: Bytes
  isRevoked: Boolean!
  createdAt: BigInt!
  feedbackFile: FeedbackFile
  responses: [FeedbackResponse!]! @derivedFrom(field: "feedback")
}

type AgentStats @entity {
  id: ID!                          # "chainId:agentId"
  totalFeedback: Int!
  averageValue: BigDecimal
  totalValidations: Int!
  completedValidations: Int!
  averageValidationScore: BigDecimal
  lastActivity: BigInt
}

type GlobalStats @entity {
  id: ID!                          # "global"
  totalAgents: Int!
  totalFeedback: Int!
  totalValidations: Int!
}
```

### Example GraphQL Queries

**Find all active MCP agents:**

```graphql
{
  agents(
    where: {
      registrationFile_: {
        mcpEndpoint_not: null,
        active: true
      }
    }
    orderBy: updatedAt
    orderDirection: desc
    first: 20
  ) {
    id
    agentId
    owner
    registrationFile {
      name
      description
      mcpEndpoint
      mcpTools
      active
      x402Support
    }
  }
}
```

**Find high-rated agents:**

```graphql
{
  agentStats(
    where: { averageValue_gte: "80.0", totalFeedback_gte: 5 }
    orderBy: averageValue
    orderDirection: desc
  ) {
    id
    totalFeedback
    averageValue
  }
}
```

**Search by capability:**

```graphql
{
  agents(where: { registrationFile_: { mcpTools_contains: ["financial_analyzer"] } }) {
    id
    registrationFile {
      name
      mcpTools
      oasfSkills
      oasfDomains
    }
  }
}
```

**Agent with feedback details:**

```graphql
{
  agent(id: "84532:42") {
    id
    agentId
    owner
    registrationFile { name description mcpEndpoint a2aEndpoint }
    feedback(where: { isRevoked: false }) {
      clientAddress
      value
      tag1
      tag2
      createdAt
      responses { responder createdAt }
    }
  }
}
```

**Global statistics:**

```graphql
{
  globalStats(id: "global") {
    totalAgents
    totalFeedback
    totalValidations
  }
}
```

## Indexed Networks

URL pattern: `https://gateway.thegraph.com/api/<API_KEY>/subgraphs/id/<SUBGRAPH_ID>`

| Network | Chain ID | Subgraph ID |
|---------|----------|-------------|
| Ethereum Mainnet | 1 | `FV6RR6y13rsnCxBAicKuQEwDp8ioEGiNaWaZUmvr1F8k` |
| Base Mainnet | 8453 | `43s9hQRurMGjuYnC1r2ZwS6xSQktbFyXMPMqGKUFJojb` |
| Polygon Mainnet | 137 | `9q16PZv1JudvtnCAf44cBoxg82yK9SSsFvrjCY9xnneF` |
| Ethereum Sepolia | 11155111 | `6wQRC7geo9XYAhckfmfo8kbMRLeWU8KQd3XsJqFKmZLT` |
| Base Sepolia | 84532 | `4yYAvQLFjBhBtdRCY7eUWo181VNoTSLLFd5M7FXQAi6u` |

The SDK embeds sponsored API keys per chain. Override with `subgraphOverrides` per chain in SDK config.

## Architecture Notes

- Subgraph indexes both on-chain events and IPFS registration files
- SDK auto-uses default subgraph URL per chain
- Search returns ALL matching results (no pagination needed)
- Multi-chain results merged and sorted client-side
- Semantic search hits `semantic-search.ag0.xyz`, then subgraph for full data
- Two-phase prefilters (metadata, feedback, keyword) run separate queries then intersect IDs
