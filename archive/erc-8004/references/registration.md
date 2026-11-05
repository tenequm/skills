# Agent Registration Best Practices

**Source:** https://github.com/erc-8004/best-practices

## Registration File Format

Every agent's `agentURI` MUST resolve to a JSON file with this structure:

```json
{
  "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
  "name": "CryptoTrader Alpha",
  "description": "AI agent that analyzes crypto markets using on-chain data. Supports real-time price feeds, portfolio analysis, and trading signals. Pricing: $0.01 per request via x402. Interact via MCP tools or A2A tasks.",
  "image": "https://example.com/cryptotrader-alpha.png",
  "services": [
    {
      "name": "MCP",
      "endpoint": "https://mcp.cryptotrader.example.com",
      "version": "2025-06-18",
      "mcpTools": ["get_price", "analyze_portfolio", "trading_signal"]
    },
    {
      "name": "A2A",
      "endpoint": "https://cryptotrader.example.com/.well-known/agent-card.json",
      "version": "0.3.0",
      "a2aSkills": ["analytical_skills/mathematical_reasoning/quantitative_analysis"]
    },
    {
      "name": "OASF",
      "endpoint": "https://github.com/agntcy/oasf/",
      "version": "v0.8.0",
      "skills": [
        "analytical_skills/mathematical_reasoning/quantitative_analysis",
        "data_engineering/data_transformation_pipeline"
      ],
      "domains": [
        "finance_and_business/investment_services",
        "technology/blockchain_and_web3"
      ]
    },
    {
      "name": "ENS",
      "endpoint": "cryptotrader.eth",
      "version": "v1"
    },
    {
      "name": "agentWallet",
      "endpoint": "eip155:8453:0x1234567890abcdef1234567890abcdef12345678"
    },
    {
      "name": "web",
      "endpoint": "https://cryptotrader.example.com"
    },
    {
      "name": "email",
      "endpoint": "support@cryptotrader.example.com"
    }
  ],
  "registrations": [
    {
      "agentId": 42,
      "agentRegistry": "eip155:8453:0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
    }
  ],
  "supportedTrust": ["reputation"],
  "active": true,
  "x402Support": true
}
```

## The Four Golden Rules

### Rule 1: Name, Image, Description

- **Name**: Clear and memorable. Should convey what the agent does.
- **Image**: PNG, SVG, or WebP. High quality, distinctive. This is how the agent appears in NFT apps and catalogs.
- **Description**: Elevator pitch covering:
  - What the agent does
  - How to interact with it
  - Pricing information
  - Key capabilities

### Rule 2: Always Include a Service

At minimum, one service endpoint. Service-specific guidelines:

**MCP service:**
- Include `mcpTools` array listing tool names
- Set `version` to the MCP protocol version (e.g., `"2025-06-18"`)

**A2A service:**
- Set `endpoint` to the agent card URL (`/.well-known/agent-card.json`)
- Include `a2aSkills` using OASF slash-separated identifiers

**ENS service:**
- `endpoint` is the ENS name (e.g., `"myagent.eth"`)

**DID service:**
- `endpoint` is the full DID string (e.g., `"did:ethr:0x..."`)

**agentWallet service:**
- Format: `eip155:{chainId}:{address}`
- Can advertise wallets on chains other than where registered

### Rule 3: Declare Skills and Domains Using OASF

OASF (Open Agentic Schema Framework, Linux Foundation) provides standardized taxonomy:

- **Domains**: Fields of application (e.g., `finance_and_business/investment_services`)
- **Skills**: Specific capabilities (e.g., `natural_language_processing/natural_language_generation/summarization`)

Use the `OASF` service entry with `skills` and `domains` arrays. v0.8.0 includes 136 skills and 204 domains.

### Rule 4: Include Registrations Back-Reference

The `registrations` array creates a bidirectional cryptographic link:
- On-chain NFT -> `agentURI` -> registration file
- Registration file -> `registrations` -> on-chain NFT

Both fields are mandatory in each registration entry:
- `agentId`: The ERC-721 tokenId
- `agentRegistry`: `eip155:{chainId}:{identityRegistryAddress}`

## Nice-to-Have Extras

- `"x402Support": true` - Signals support for Coinbase x402 HTTP payment protocol
- `"active": true/false` - Set `false` until agent is tested and ready for discovery
- Set `agentWallet` on-chain via `setAgentWallet()` if payment address differs from owner

## Endpoint Domain Verification

Optional but recommended. Publish `https://{endpoint-domain}/.well-known/agent-registration.json` containing at least a `registrations` list matching the on-chain identity.

Verification logic:
1. File reachable over HTTPS
2. Contains `registrations` entry where `agentRegistry` and `agentId` match on-chain values
3. If endpoint-domain is the same as `agentURI` domain, this check is redundant

## Registration Flows

### IPFS Registration (Recommended)

```typescript
const sdk = new SDK({
  chainId: 84532,
  rpcUrl: '...',
  privateKey: '...',
  ipfs: 'pinata',       // or 'filecoinPin' (free for ERC-8004), or 'node'
  pinataJwt: '...',
});

const agent = sdk.createAgent('MyAgent', 'Description');
await agent.setMCP('https://mcp.example.com');
agent.setActive(true);

const tx = await agent.registerIPFS();
const { result } = await tx.waitConfirmed();
// result.agentId = "84532:42", result.agentURI = "ipfs://Qm..."
```

IPFS providers:
- **Filecoin Pin** (`filecoinPin`): Free for ERC-8004 agents via Protocol Labs
- **Pinata** (`pinata`): Free for ERC-8004 agents via Pinata
- **IPFS Node** (`node`): Self-hosted node

### HTTP Registration

```typescript
const agent = sdk.createAgent('MyAgent', 'Description');
await agent.setMCP('https://mcp.example.com');
const regFile = agent.getRegistrationFile();
// Host regFile JSON at your URL
const tx = await agent.registerHTTP('https://example.com/agent.json');
```

### Updating Registration

```typescript
const agent = await sdk.loadAgent('84532:42');
agent.updateInfo(undefined, 'Updated description');
await agent.setMCP('https://new-mcp.example.com');
const tx = await agent.registerIPFS();  // uploads new file, updates URI
```

## Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `type` | MUST | `"https://eips.ethereum.org/EIPS/eip-8004#registration-v1"` |
| `name` | MUST | Agent display name |
| `description` | MUST | Natural language description |
| `image` | SHOULD | Agent image URL |
| `services` | SHOULD | Array of service endpoints |
| `services[].name` | MUST | Service type (`MCP`, `A2A`, `OASF`, `ENS`, `DID`, `web`, `email`, `agentWallet`) |
| `services[].endpoint` | MUST | Service URL or identifier |
| `services[].version` | SHOULD | Protocol version |
| `registrations` | SHOULD | On-chain back-references |
| `registrations[].agentId` | MUST | ERC-721 tokenId |
| `registrations[].agentRegistry` | MUST | `eip155:{chainId}:{address}` |
| `supportedTrust` | MAY | Trust model array |
| `active` | MAY | Visibility flag |
| `x402Support` | MAY | Payment protocol flag |
