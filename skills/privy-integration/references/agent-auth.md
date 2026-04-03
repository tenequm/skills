# Agent Auth & Agentic Wallets Reference

Privy's agentic wallet infrastructure, the Agent Auth Protocol for per-agent identity, MCP authorization patterns, and Better Auth integration bridges.

## Table of Contents

- [Agentic Wallets](#agentic-wallets)
- [Agent Auth Protocol](#agent-auth-protocol)
- [MCP Authorization](#mcp-authorization)
- [Better Auth Integration](#better-auth-integration)

## Agentic Wallets

Privy server wallets can be configured as autonomous agent wallets with policy-based controls. Two control models cover different trust levels.

Docs: https://docs.privy.io/recipes/agent-integrations/agentic-wallets

### Model 1: Agent-Controlled, Developer-Owned

The application backend controls the wallet via authorization keys. Fully autonomous agents execute transactions within policy constraints without user approval.

- Use when: agents need full autonomy (trading bots, automated payments, infrastructure provisioning)
- Risk: developer bears full responsibility for agent behavior

### Model 2: User-Owned with Agent Signers

Users maintain wallet ownership and grant limited permissions to agents. The agent operates as an additional signer with scoped policies. Users retain ultimate control and can revoke agent access.

- Use when: users delegate specific tasks (portfolio rebalancing, scheduled payments)
- Risk: lower - user retains revocation authority

### Setup Steps

1. **Create authorization keys** in Privy Dashboard (optionally in a key quorum for multi-party approval)
2. **Define agent policies** (spending limits, chain restrictions, contract allowlists)
3. **Create agent wallet** with `owner_id` set to authorization key ID and `policy_ids` array
4. **Execute transactions** via Privy's API (validated against attached policies)
5. **Monitor** via webhooks (transaction events, balance changes)

### Policy Examples

**Spending limit** (max value per transaction):
```json
{
  "name": "Max 0.1 ETH per tx",
  "method": "eth_sendTransaction",
  "conditions": [
    {
      "field_source": "ethereum_transaction",
      "field": "value",
      "operator": "lte",
      "value": "100000000000000000"
    }
  ],
  "action": "ALLOW"
}
```

**Chain restriction**:
```json
{
  "name": "Base mainnet only",
  "method": "eth_sendTransaction",
  "conditions": [
    {
      "field_source": "ethereum_transaction",
      "field": "chain_id",
      "operator": "eq",
      "value": "8453"
    }
  ],
  "action": "ALLOW"
}
```

**Contract allowlist**:
```json
{
  "name": "Only Uniswap Router",
  "method": "eth_sendTransaction",
  "conditions": [
    {
      "field_source": "ethereum_transaction",
      "field": "to",
      "operator": "in",
      "value": ["0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD"]
    }
  ],
  "action": "ALLOW"
}
```

### Policy Condition Operators

| Operator | Description |
|----------|-------------|
| `eq` | Equals |
| `neq` | Not equals |
| `gt` | Greater than |
| `gte` | Greater than or equal |
| `lt` | Less than |
| `lte` | Less than or equal |
| `in` | Value in array |
| `not_in` | Value not in array |

### Supported Chains for Agentic Wallets

| Chain | chain_type | CAIP-2 |
|-------|-----------|--------|
| Ethereum | `ethereum` | `eip155:1` |
| Base | `ethereum` | `eip155:8453` |
| Polygon | `ethereum` | `eip155:137` |
| Arbitrum | `ethereum` | `eip155:42161` |
| Optimism | `ethereum` | `eip155:10` |
| Solana | `solana` | `solana:mainnet` |
| Cosmos, Stellar, Sui, Tron, Bitcoin (SegWit), NEAR, TON, Starknet | varies | varies |

### OpenClaw Integration

OpenClaw is an open-source framework for running AI agents with tool access. Combined with Privy, agents control wallets via natural language.

**Install via ClawHub:**
```bash
clawhub install privy
```

**Install via GitHub:**
```bash
git clone https://github.com/privy-io/privy-agentic-wallets-skill.git ~/.openclaw/workspace/skills/privy
```

**Configure** in `~/.openclaw/openclaw.json`:
```json
{
  "env": {
    "vars": {
      "PRIVY_APP_ID": "your-app-id",
      "PRIVY_APP_SECRET": "your-app-secret"
    }
  }
}
```

**Natural language usage examples:**
- "Create an Ethereum wallet for yourself using Privy"
- "Create a policy that limits transactions to 0.1 ETH max, only on Base mainnet"
- "Attach the spending limit policy to my wallet"
- "Send 0.01 ETH to 0x1234... on Base"

**Note**: OpenClaw is experimental, third-party, not officially supported by Privy. Only fund wallets with amounts you're comfortable losing.

### Security Best Practices

- Start with restrictive policies, loosen over time
- Require human approval for high-value transactions
- Monitor agent activity via webhooks
- On compromise: rotate App Secret, rotate authorization keys, review transactions, transfer funds

## Agent Auth Protocol

An open protocol (v1.0-draft) for giving AI agents their own cryptographic identity, capability-based authorization, and service discovery. Created by the Better Auth team.

Site: https://agentauthprotocol.com
Spec: https://agentauthprotocol.com/specification/v1.0-draft
GitHub: https://github.com/better-auth/agent-auth-protocol

### Core Concepts

**Three runtime participants:**
- **Agent** - the runtime AI actor (conversation, task, or session) that calls external services
- **Client** - the process holding a host identity, exposing protocol tools (MCP server, CLI, SDK)
- **Server** - the service's authorization server managing discovery, registrations, approvals, capability grants

**Two identity types:**
- **Host** - persistent identity of the client environment (e.g., a Claude Code session). Carries default capabilities and optionally a linked user
- **Agent** - per-agent identity created at registration time, used for authenticated capability execution

### Protocol Flow

```
1. Client -> Server:  GET /.well-known/agent-configuration (discovery)
2. Client -> Server:  POST /agent/register (Host JWT + agent pubkey + requested capabilities)
3. Server -> Client:  agent_id + pending/active capabilities
4. (If delegated) User approves via device authorization (RFC 8628) or CIBA
5. Client -> Server:  POST /capability/execute (Agent JWT signed with Ed25519)
6. Server validates JWT, checks grants, enforces constraints, executes
```

### Agent Modes

- **Delegated** (default): acts on behalf of a user, capabilities approved through device flow. Example: email assistant reading inbox
- **Autonomous**: operates without user in the loop, capabilities granted by server policy. Example: deployment agent provisioning infrastructure

### Capabilities System

Capabilities are named actions with JSON Schema input/output definitions and constraints:

```json
{
  "capability": "transfer_funds",
  "constraints": {
    "to": {"const": "acc_456"},
    "amount": {"maximum": 1000},
    "currency": {"in": ["USD", "EUR"]}
  }
}
```

Constraint operators: `max`, `min`, `in`, `not_in`. The tightest constraint from agent-proposed or server-imposed wins. Agents can escalate (request additional capabilities) at runtime via `POST /agent/request-capability`, always triggering a new approval flow.

### Authentication

- **Ed25519 keypairs** (EdDSA, RFC 8037/8032) in JWK format
- **Host JWT** (`typ: host+jwt`): used for registration, management. Claims: `iss` (JWK thumbprint), `aud` (server issuer URL), `iat`, `exp`, `jti`
- **Agent JWT** (`typ: agent+jwt`): used for capability execution. 60-second lifetime, no refresh tokens - fresh JWT signed for every request. Claims: `iss` (host ID), `sub` (agent ID), `aud` (execution URL), `iat`, `exp`, `jti`
- **Replay protection**: unique `jti` per JWT, server rejects duplicates within 90s window

### Agent Lifecycle

States: `pending` -> `active` -> `expired` -> `revoked` (terminal). Also: `rejected`, `claimed`.

Three configurable lifetime clocks:
- **Session TTL** - from last request (protects against abandoned agents)
- **Max lifetime** - from last activation (caps continuous use)
- **Absolute lifetime** - from creation (hard limit, permanent revocation)

### MCP Integration

Agent Auth ships with an MCP server exposing all protocol operations as 15 MCP tools:

```bash
claude mcp add auth-agent -- npx @auth/agent-cli mcp --url https://api.example.com
```

Available tools: `list_providers`, `search_providers`, `discover_provider`, `list_capabilities`, `describe_capability`, `connect_agent`, `agent_status`, `request_capability`, `disconnect_agent`, `reactivate_agent`, `execute_capability`, `sign_jwt`, `rotate_agent_key`, `rotate_host_key`, `enroll_host`

### SDKs

| Package | Purpose |
|---------|---------|
| `@better-auth/agent-auth` | Server plugin for Better Auth (4 DB tables) |
| `@auth/agent` | Client SDK - keypair management, JWT signing, registration |
| `@auth/agent-cli` | CLI commands + MCP server mode |

The client SDK ships with tool adapters for Vercel AI SDK, OpenAI function calling, and Anthropic Claude.

**OpenAPI adapter**: `createFromOpenAPI(spec)` auto-derives capabilities from OpenAPI operations - each `operationId` becomes a capability.

### Server Configuration

```ts
import {agentAuth} from '@better-auth/agent-auth';

agentAuth({
  providerName: 'my-service',
  capabilities: [/* capability definitions */],
  onExecute: async (capability, input, agent) => {/* handler */},
  modes: ['delegated', 'autonomous'],
  agentSessionTTL: 3600,      // seconds
  agentMaxLifetime: 86400,     // seconds
  maxAgentsPerUser: 25,
  approvalStrength: 'session', // 'none' | 'session' | 'webauthn'
})
```

### Connection to Privy

Agent Auth provides the **identity and authorization layer** while Privy provides the **wallet infrastructure**:

- Better Auth's JWT plugin bridges to Privy's `customAuth` (proven pattern from community, see Better Auth section below)
- An agent with Agent Auth identity can use a Privy server wallet for on-chain actions
- Agent Auth's capability constraints (amount caps, recipient allowlists) map to Privy's wallet policies
- Agent Auth's `autonomous` mode enables fully autonomous agent wallets

## MCP Authorization

The MCP specification (2025-11-25) defines OAuth 2.1-based authorization for HTTP-based MCP servers. This is relevant for agents that access Privy-protected resources via MCP tools.

### Core Architecture

- **MCP server** = OAuth 2.1 resource server (accepts Bearer tokens)
- **MCP client** = OAuth 2.1 client (makes protected requests)
- **Authorization server** = issues access tokens (may be co-located or separate)

### Discovery Flow

1. Server returns `401 Unauthorized` with `WWW-Authenticate: Bearer resource_metadata="<url>"`
2. Client fetches Protected Resource Metadata (RFC 9728) to find authorization server
3. Client fetches Authorization Server Metadata (RFC 8414) for endpoints
4. Client registers dynamically (RFC 7591) or uses pre-registered credentials
5. Client obtains token via authorization code + PKCE (S256 required)

### Client Credentials (Machine-to-Machine)

Extension `io.modelcontextprotocol/oauth-client-credentials` enables agents to authenticate without user interaction:

**JWT Bearer Assertions (recommended):**
```
POST /token
grant_type=client_credentials
client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
client_assertion=<signed JWT>
```

The JWT contains: `iss` (client ID), `sub` (client ID), `aud` (AS token endpoint), `exp`, `iat`.

**SDK support:**
- TypeScript: `ClientCredentialsProvider` from `@modelcontextprotocol/client`
- Python: `ClientCredentialsOAuthProvider` from `mcp.client.auth.extensions.client_credentials`

### Enterprise-Managed Authorization

Extension for centralized access control via enterprise IdP (Okta, Azure AD, corporate SSO):

1. User authenticates via SSO (OpenID Connect / SAML)
2. Client exchanges ID Token for an ID-JAG (Identity Assertion JWT Authorization Grant) via RFC 8693 Token Exchange
3. Client sends ID-JAG to MCP AS via RFC 7523 JWT Bearer Grant
4. AS returns scoped Bearer access token

This eliminates per-server authorization prompts for employees and enables central policy enforcement.

### MCP Apps

MCP Apps are interactive HTML UIs that render inside MCP hosts (Claude Desktop, VS Code, etc.) within the conversation. Tools return rich interactive UIs instead of just text/images.

- Tools include `_meta.ui.resourceUri` pointing to a `ui://` resource
- Host renders HTML in a sandboxed iframe
- Bidirectional communication via JSON-RPC over `postMessage`
- Package: `@modelcontextprotocol/ext-apps`

### Privy as MCP Authorization Server

Privy's auth system can serve as the OAuth AS for MCP servers:

- Privy already supports OAuth flows and JWT tokens
- MCP clients could use Privy's token endpoint for access to MCP-protected resources
- Privy server wallets + Client Credentials flow enables autonomous agent auth to MCP servers
- The same key infrastructure that signs blockchain transactions also authenticates to MCP services

### Ecosystem Integration Pattern

```
MCP Protocol Layer     -> tool discovery, execution, communication
Agent Auth Protocol    -> per-agent identity, capability-based authorization
Privy                  -> wallet infrastructure (create, sign, transact)
x402 / MPP             -> payment settlement for paid capabilities
Better Auth            -> OAuth provider for MCP, JWT bridge to Privy
```

An agent can: discover a service via MCP -> authenticate with Agent Auth -> execute capabilities where x402/MPP handles payment settlement, all with per-agent audit trail and constraint enforcement.

## Better Auth Integration

Better Auth is an open-source auth framework with plugins relevant to the Privy + agent ecosystem.

### JWT Bridge to Privy

Community-proven pattern (GitHub issue #5907) connecting Better Auth to Privy's `customAuth`:

**Server setup:**
```ts
import {betterAuth} from 'better-auth';
import {jwt} from 'better-auth/plugins';

const auth = betterAuth({
  plugins: [
    jwt({
      jwks: {keyPairConfig: {alg: 'RS256'}},
      jwt: {
        definePayload: ({user}) => ({
          sub: user.id,
          iat: Math.floor(Date.now() / 1000),
          exp: Math.floor(Date.now() / 1000) + 3600
        })
      }
    })
  ]
});
```

Configure the JWKS endpoint in Privy Dashboard under custom auth provider settings.

**Client setup:**
```tsx
<PrivyProvider
  appId="your-app-id"
  config={{
    customAuth: {
      getCustomAccessToken: async () => {
        // Get JWT from Better Auth
        return authClient.token();
      }
    }
  }}
>
```

**Note**: Privy's custom JWT authentication requires the Scale or Enterprise plan (not available on Free/Pro).

### OAuth Provider Plugin (MCP Support)

`@better-auth/oauth-provider` turns Better Auth into a full OAuth 2.1 provider with OIDC, supporting MCP authentication:

```ts
import {oauthProvider} from '@better-auth/oauth-provider';

oauthProvider({
  loginPage: '/sign-in',
  consentPage: '/consent',
  allowDynamicClientRegistration: true,
  allowUnauthenticatedClientRegistration: true, // for MCP public clients
  scopes: ['openid', 'profile', 'email', 'offline_access']
})
```

Key endpoints: `POST /oauth2/authorize`, `POST /oauth2/token`, `GET /oauth2/userinfo`, `POST /oauth2/introspect`, `POST /oauth2/revoke`

Well-known endpoints for MCP discovery: `/.well-known/openid-configuration`, `/.well-known/oauth-authorization-server`

### API Key Plugin

`@better-auth/api-key` provides usage-based access control with patterns useful for agent services:

```ts
import {apiKey} from '@better-auth/api-key';

// Create key with rate limits and usage caps
const key = await auth.api.createApiKey({
  body: {
    name: 'agent-key',
    remaining: 100,           // usage cap
    refillAmount: 100,        // refill count
    refillInterval: 86400000, // refill every 24h (ms)
    rateLimitMax: 60,         // max requests per window
    rateLimitTimeWindow: 60000, // 1 minute window (ms)
    permissions: {projects: ['read']},
    metadata: {agentId: 'agent-123'}
  }
});

// Verify with permission check
const {valid, error, key} = await auth.api.verifyApiKey({
  body: {key: 'the_api_key', permissions: {projects: ['read']}}
});
```

## Official Links

| Topic | URL |
|-------|-----|
| Agentic wallets (Privy) | https://docs.privy.io/recipes/agent-integrations/agentic-wallets |
| OpenClaw integration | https://docs.privy.io/recipes/agent-integrations/openclaw-agentic-wallets |
| Wallet policies | https://docs.privy.io/wallets/policies/overview |
| Wallet signers | https://docs.privy.io/wallets/using-wallets/signers/overview |
| Agent Auth Protocol | https://agentauthprotocol.com |
| Agent Auth spec | https://agentauthprotocol.com/specification/v1.0-draft |
| Agent Auth GitHub | https://github.com/better-auth/agent-auth-protocol |
| MCP auth spec | https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization |
| MCP Apps | https://modelcontextprotocol.io/extensions/apps/overview |
| MCP ext-auth repo | https://github.com/modelcontextprotocol/ext-auth |
| Better Auth OAuth provider | https://better-auth.com/docs/plugins/oauth-provider |
| Better Auth API key | https://better-auth.com/docs/plugins/api-key |
| Better Auth Privy issue | https://github.com/better-auth/better-auth/issues/5907 |
| Privy auth overview | https://docs.privy.io/authentication/user-authentication/privy-auth |
