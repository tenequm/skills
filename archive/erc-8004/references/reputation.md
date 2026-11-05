# ERC-8004 Reputation and Feedback System

**Best Practices Source:** https://github.com/erc-8004/best-practices

## Overview

The Reputation Registry stores agent feedback as signed fixed-point numbers on-chain, with optional rich metadata off-chain (IPFS/HTTPS). Anyone can post feedback about any agent, but self-feedback is rejected (owner/operators cannot review their own agent).

## Value/ValueDecimals Encoding

Feedback uses `int128 value` + `uint8 valueDecimals` (0-18):

| tag1 | Measures | Human Example | value | valueDecimals |
|------|----------|---------------|-------|---------------|
| `starred` | Quality rating 0-100 | 87/100 | 87 | 0 |
| `reachable` | Endpoint reachable (binary) | true | 1 | 0 |
| `ownerVerified` | Endpoint owned by agent | true | 1 | 0 |
| `uptime` | Endpoint uptime % | 99.77% | 9977 | 2 |
| `successRate` | Request success rate % | 89% | 89 | 0 |
| `responseTime` | Latency in ms | 560ms | 560 | 0 |
| `blocktimeFreshness` | Avg block delay | 4 blocks | 4 | 0 |
| `revenues` | Cumulative revenues | $560 | 560 | 0 |
| `tradingYield` | Yield (tag2=day/week/month/year) | -3.2% | -32 | 1 |

### 5-Star to 0-100 Mapping (for catalogs)

| Stars | Value |
|-------|-------|
| 1 | 20 |
| 2 | 40 |
| 3 | 60 |
| 4 | 80 |
| 5 | 100 |

## On-Chain Storage

Stored in contract state (queryable by smart contracts):
- `value` (int128)
- `valueDecimals` (uint8)
- `tag1` (string)
- `tag2` (string)
- `isRevoked` (bool)
- `feedbackIndex` (uint64, 1-indexed per clientAddress per agentId)

Emitted in events but NOT stored:
- `endpoint` (string)
- `feedbackURI` (string)
- `feedbackHash` (bytes32)

## Off-Chain Feedback File

Optional file at `feedbackURI` for rich metadata:

```json
{
  "agentRegistry": "eip155:8453:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432",
  "agentId": 42,
  "clientAddress": "eip155:8453:0xReviewerAddress",
  "createdAt": "2025-09-23T12:00:00Z",
  "value": 85,
  "valueDecimals": 0,
  "tag1": "starred",
  "tag2": "finance",
  "endpoint": "https://mcp.agent.example.com",
  "mcp": {
    "tool": "financial_analyzer"
  },
  "a2a": {
    "skills": ["trading_analysis"],
    "contextId": "ctx-123",
    "taskId": "task-456"
  },
  "oasf": {
    "skills": ["analytical_skills/mathematical_reasoning"],
    "domains": ["finance_and_business"]
  },
  "proofOfPayment": {
    "fromAddress": "0xReviewer...",
    "toAddress": "0xAgent...",
    "chainId": "8453",
    "txHash": "0xPaymentTx..."
  }
}
```

IPFS is recommended for integrity (CID verifies content). For HTTPS files, `feedbackHash` (keccak256) guarantees integrity on-chain.

## SDK Usage

### Give Feedback

```typescript
// Minimal - just value
const tx = await sdk.giveFeedback('84532:42', 85);
await tx.waitConfirmed();

// With tags and endpoint
const tx = await sdk.giveFeedback(
  '84532:42',   // agentId
  85,            // value (0-100 for starred)
  'starred',     // tag1
  'finance',     // tag2
  'https://mcp.example.com',  // endpoint
);

// Full with off-chain file
const feedbackFile = await sdk.prepareFeedbackFile({
  text: 'Accurate market analysis with fast response times',
  capability: 'tools',          // MCP capability type
  name: 'financial_analyzer',   // MCP tool name
  skill: 'trading_analysis',    // A2A skill
  task: 'analyze_portfolio',    // A2A task
  context: { sessionId: 'abc', duration: 1200 },
  proofOfPayment: {
    txHash: '0x...', chainId: '8453',
    fromAddress: '0x...', toAddress: '0x...',
  },
});

const tx = await sdk.giveFeedback('84532:42', 85, 'starred', '', '', feedbackFile);
await tx.waitConfirmed();
```

### Read Feedback

```typescript
// Single feedback entry
const feedback = await sdk.getFeedback('84532:42', '0xClientAddr', 0);
// feedback.value, feedback.tags, feedback.text, feedback.isRevoked

// Search feedback for an agent
const results = await sdk.searchFeedback({
  agentId: '84532:42',
  tags: ['starred'],
});

// Search by reviewer (across all agents, requires subgraph)
const results = await sdk.searchFeedback({
  reviewers: ['0xReviewerAddr'],
});

// Multi-agent search
const results = await sdk.searchFeedback({
  agents: ['84532:42', '84532:43', '84532:44'],
  tags: ['starred'],
});
```

### Reputation Summary

```typescript
const summary = await sdk.getReputationSummary('84532:42');
// { count: 15, averageValue: 87.5 }

// With tag filters
const summary = await sdk.getReputationSummary('84532:42', 'starred', 'finance');
```

### Respond to Feedback

```typescript
// Agent responds to specific feedback
await sdk.appendResponse('84532:42', '0xClientAddr', 0, {
  uri: 'ipfs://QmResponseFile',
  hash: '0x...',
});
```

### Revoke Feedback

```typescript
// Only original submitter can revoke
await sdk.revokeFeedback('84532:42', 0);
```

## On-Chain Aggregation (getSummary)

The `getSummary()` function computes averages on-chain:

1. Normalizes all `value`/`valueDecimals` pairs to 18-decimal WAD
2. Sums all values
3. Finds mode (most common) `valueDecimals` across included feedbacks
4. Computes average
5. Scales back to mode precision

**Anti-Sybil requirement:** `clientAddresses` parameter MUST be non-empty. Callers must supply a trusted reviewer list. Results without filtering are vulnerable to Sybil/spam attacks.

**Tag filtering:** Empty strings for `tag1`/`tag2` act as wildcards (match all).

## Self-Feedback Prevention

The ReputationRegistry calls `isAuthorizedOrOwner()` on the IdentityRegistry before accepting feedback. If the feedback submitter is the agent owner or any approved operator, the transaction reverts.

When agent-to-agent feedback occurs, the reviewing agent SHOULD use its on-chain `agentWallet` as the `clientAddress` for reputation aggregation.

## Feedback ID Format

In the SDK: `"agentId:clientAddress:feedbackIndex"` (e.g., `"84532:42:0x742d...:0"`).

In TypeScript, `Feedback.id` is a tuple `[AgentId, Address, number]`.

The `feedbackIndex` is 0-based in the SDK (converted to 1-based when calling the contract).

## Reputation-Gated Agent Search

The SDK supports finding agents filtered by reputation thresholds:

```typescript
const agents = await sdk.searchAgents({
  active: true,
  hasMCP: true,
  feedback: {
    hasFeedback: true,
    minValue: 80,        // average value >= 80
    maxValue: 100,       // average value <= 100 (upper bound)
    minCount: 5,         // at least 5 feedbacks
    maxCount: 1000,      // at most 1000 feedbacks (upper bound)
    tag1: 'starred',     // only starred feedback
    fromReviewers: ['0xTrustedReviewer'],  // specific reviewers
  },
}, {
  sort: ['averageValue:desc'],
});
```

This uses two-phase filtering: first queries feedback subgraph for matching agentIds, then intersects with the main agent query.

## Ecosystem Patterns

### Agent-as-Rater

When the rater is itself an agent, it SHOULD submit feedback from its on-chain `agentWallet` address so `clientAddress == agentWallet`. This lets UIs resolve the wallet back to an agent identity - finding which agent has that `agentWallet`, then reading its registration file for `name` and `image` to show a profile for the rater.

### Watchtower Monitoring

Trusted third parties (infra companies, watchtowers, data providers) can routinely probe agents and publish periodic signals (e.g., once per week) so anyone can reuse them. Common reliability dimensions:

- `tag1=reachable` - Endpoint reachable (binary)
- `tag1=uptime` - Uptime over a period (percentage)
- `tag1=successRate` - Fraction of successful requests (percentage)
- `tag1=responseTime` - Average latency (milliseconds)

Consumers choose their own trusted sources by filtering feedback by `clientAddress` (e.g., "I trust this watchtower for reachability pings"). Different applications can compose the same underlying signals into dashboards, rankings, alerts, and SLAs.

### Revenue Signals

Cumulative revenue (`tag1=revenues`) helps clients assess whether an agent is battle-tested and in production use. Revenue is NOT directly computable on-chain in a clean way - smart contracts can't conveniently aggregate all payments, and indexers can't reliably distinguish between generic transfers and x402 payments.

In practice, revenue data is best known by the **facilitator** (or specialized infrastructure that interprets payment + service context). These parties publish standardized revenue signals on-chain, making them public so catalogs can filter/weight by trusted `clientAddress`.
