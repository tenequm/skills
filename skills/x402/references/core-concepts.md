# Core Concepts

## HTTP 402 - The Foundation

HTTP 402 Payment Required is a standard but historically dormant HTTP status code. x402 activates it to enable frictionless, API-native payments for:

- Machine-to-machine (M2M) payments (AI agents)
- Pay-per-use models (API calls, paywalled content)
- Micropayments without account creation or traditional payment rails

Using 402 keeps the protocol natively web-compatible and easy to integrate into any HTTP-based service. No new protocols, no special infrastructure - just HTTP.

### V2 Payment Headers

| Header | Direction | Encoding | Content |
|--------|-----------|----------|---------|
| `PAYMENT-REQUIRED` | Server to Client | Base64 JSON | PaymentRequired object |
| `PAYMENT-SIGNATURE` | Client to Server | Base64 JSON | PaymentPayload with signed authorization |
| `PAYMENT-RESPONSE` | Server to Client | Base64 JSON | SettlementResponse with tx hash |

Both headers must be valid Base64-encoded JSON strings for cross-implementation compatibility.

### V1 to V2 Header Migration

| V1 Header | V2 Header |
|-----------|-----------|
| `X-PAYMENT` | `PAYMENT-SIGNATURE` |
| `X-PAYMENT-RESPONSE` | `PAYMENT-RESPONSE` |

## Client / Server Roles

### Client (Buyer)

The entity requesting access to a paid resource. Can be:
- Human-operated applications
- Autonomous AI agents
- Programmatic services acting on behalf of users

**Responsibilities:**
1. Send HTTP request to resource server
2. Handle 402 response and extract payment details
3. Construct a valid payment payload (sign authorization)
4. Retry request with `PAYMENT-SIGNATURE` header

Clients do not need accounts, credentials, or session tokens beyond their crypto wallet. All interactions are stateless and occur over standard HTTP.

### Server (Seller)

The resource provider enforcing payment for access. Can be:
- API services
- Content providers
- Any HTTP-accessible resource requiring monetization

**Responsibilities:**
1. Define payment requirements per route
2. Respond with 402 + `PAYMENT-REQUIRED` header when no valid payment is attached
3. Verify incoming payment payloads (locally or via facilitator)
4. Settle transactions on-chain
5. Return the resource on successful payment

Servers do not need to manage client identities or maintain session state. Verification and settlement are handled per request.

#### Duplicate Settlement on Solana

If your server settles payments directly on Solana (without a facilitator), a race condition exists: the same signed payment can be submitted multiple times before on-chain confirmation. Solana's RPC returns "success" for each submission.

Mitigation: maintain a short-lived in-memory cache of transaction payloads being settled. Reject duplicates with `"duplicate_settlement"` error. Evict entries after 120 seconds. If using a facilitator, the SVM libraries include built-in `SettlementCache` protection.

## Facilitator

An optional but recommended service that simplifies payment verification and settlement.

### What It Does

- **Verifies payments**: Confirms client's payment payload meets server's requirements
- **Settles payments**: Submits validated payments to blockchain and monitors confirmation
- **Returns results**: Sends verification and settlement results back to server

### What It Does NOT Do

- Does NOT hold funds or act as a custodian
- Does NOT control the payment amount or destination (these are signed by the client)
- Cannot steal funds - tampering with the transaction fails signature checks

### Why Use One

- **Reduced complexity**: Servers don't need direct blockchain connectivity
- **Protocol consistency**: Standardized verification/settlement flows
- **Faster integration**: Start accepting payments with minimal blockchain development
- **Gas abstraction**: Facilitator sponsors gas fees, buyers don't need native tokens

### Live Facilitators

Multiple production facilitators are available. The ecosystem is permissionless - anyone can run a facilitator.

| Facilitator | Networks | Use Case |
|-------------|----------|----------|
| x402.org (default) | Base Sepolia, Solana Devnet, Stellar Testnet | Testing/development, no setup needed |
| [Production facilitators](https://www.x402.org/ecosystem?filter=facilitators) | Base, Solana, Polygon, Avalanche, etc. | Production use |
| Self-hosted | Any EVM chain | Full control |

**Key insight**: Facilitators support NETWORKS, not specific tokens. Any EIP-3009 token works on EVM networks, any SPL/Token-2022 token works on Solana, any SEP-41 token works on Stellar, and any fungible asset works on Aptos, as long as the facilitator supports that network.

## Wallet

In x402, a wallet is both a payment mechanism and a form of unique identity.

### For Buyers
- Store USDC/crypto
- Sign payment payloads (EIP-712 for EVM, Ed25519 for Solana/Aptos, BCS signing for Aptos)
- Authorize on-chain payments programmatically
- Wallets enable AI agents to transact without account creation

### For Sellers
- Receive USDC/crypto payments
- Define payment destination in server configuration (the `payTo` address)

### Recommended Wallet Solutions
- **CDP Wallet API** (https://docs.cdp.coinbase.com/wallet-api-v2/docs/welcome): Recommended for programmatic payments and secure key management
- **viem** / **ethers** HD wallets: For EVM
- **@solana/kit**: For Solana
- **Aptos TypeScript SDK**: For Aptos

## Networks and Token Support

### CAIP-2 Network Identifiers

x402 v2 uses CAIP-2 (Chain Agnostic Improvement Proposal) for unambiguous cross-chain support.

Format: `{namespace}:{reference}`

- **EVM**: `eip155:<chainId>` (e.g., `eip155:8453` for Base)
- **Solana**: `solana:<genesisHash>` (e.g., `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` for mainnet)
- **Aptos**: `aptos:<chainId>` (e.g., `aptos:1` for mainnet)
- **Stellar**: `stellar:<network>` (e.g., `stellar:pubnet` for mainnet)

### Token Support

**EVM**: Any ERC-20 token implementing EIP-3009 (`transferWithAuthorization`). For the `exact` scheme with Permit2 fallback: Any ERC-20 token via `permitWitnessTransferFrom` (requires one-time Permit2 approval).

**Solana**: Any SPL token or Token-2022 token.

**Aptos**: Any fungible asset via `0x1::primary_fungible_store::transfer`. Supports sponsored (gasless) transactions. TypeScript SDK only.

**Stellar**: Any Soroban token implementing SEP-41. Uses `transfer(from, to, amount)`. TypeScript SDK only. Ledger-based expiration (~12 ledgers, ~60 seconds).

**USDC** is the default token, supported across all networks. When you use price strings like `"$0.001"`, the system infers USDC.

### Specifying Payment Amounts

Two options:

**1. Price String (USDC shorthand)**
```typescript
{ price: "$0.001" }  // Infers USDC
```

**2. TokenAmount / AssetAmount (custom tokens)**

TypeScript:
```typescript
{
  price: {
    amount: "10000",  // Atomic units
    asset: "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  // Token address
    extra: { name: "USDC", version: "2" }  // EIP-712 values
  }
}
```

Python:
```python
from x402.schemas import AssetAmount

PaymentOption(
    price=AssetAmount(
        amount="10000",
        asset="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        extra={"name": "USDC", "version": "2"},
    ),
)
```

### Using Custom EIP-3009 Tokens

To use a token other than USDC, you need:

1. **Token Address**: Contract address of your EIP-3009 token
2. **EIP-712 Name**: Token's name for EIP-712 signatures (read `name()` on the contract)
3. **EIP-712 Version**: Token's version for EIP-712 signatures (read `version()` on the contract)

### Adding New Networks (Dynamic Registration)

v2 uses dynamic network registration - support any EVM network without modifying source code.

**TypeScript:**
```typescript
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";

const facilitator = new HTTPFacilitatorClient({
  url: "https://your-facilitator.com"
});

const server = new x402ResourceServer(facilitator);
server.register("eip155:*", new ExactEvmScheme());

"GET /api/data": {
  accepts: [{
    scheme: "exact",
    price: "$0.001",
    network: "eip155:43114",  // Avalanche mainnet
    payTo: "0xYourAddress",
  }],
}
```

**Go:**
```go
schemes := []ginmw.SchemeConfig{
    {Network: x402.Network("eip155:43114"), Server: evm.NewExactEvmScheme()},
}
```

**Python:**
```python
server = x402ResourceServer(facilitator)
server.register("eip155:43114", ExactEvmServerScheme())
```

### Running Your Own Facilitator

**TypeScript:**
```typescript
import { x402Facilitator } from "@x402/core";
import { ExactEvmScheme } from "@x402/evm/exact/facilitator";

const facilitator = new x402Facilitator();
facilitator.register("eip155:43114", new ExactEvmScheme({
  privateKey: process.env.FACILITATOR_KEY
}));
```

### Quick Reference

| Network | CAIP-2 ID | Token Support | Default Facilitator |
|---------|-----------|---------------|-------------------|
| Base Mainnet | `eip155:8453` | Any EIP-3009 | Production facilitators |
| Base Sepolia | `eip155:84532` | Any EIP-3009 | x402.org (testnet) |
| MegaETH Mainnet | `eip155:4326` | USDM (18 decimals) | Community |
| Monad Mainnet | `eip155:143` | USDC | Community |
| Solana Mainnet | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | Any SPL/Token-2022 | Production facilitators |
| Solana Devnet | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` | Any SPL/Token-2022 | x402.org (testnet) |
| Aptos Mainnet | `aptos:1` | Any Fungible Asset | Community |
| Aptos Testnet | `aptos:2` | Any Fungible Asset | Community |
| Stellar Mainnet | `stellar:pubnet` | Any SEP-41 Soroban token | Community |
| Stellar Testnet | `stellar:testnet` | Any SEP-41 Soroban token | x402.org (testnet) |
| Polygon Mainnet | `eip155:137` | USDC | Production facilitators |
| Polygon Amoy | `eip155:80002` | USDC | Community |
| Stable Mainnet | `eip155:988` | USDT0 | Community |
| Stable Testnet | `eip155:2201` | USDT0 | Community |
| Arbitrum One | `eip155:42161` | USDC | Production facilitators |
| Arbitrum Sepolia | `eip155:421614` | USDC | Community |
| Mezo Testnet | `eip155:31611` | mUSD (Permit2 + EIP-2612) | Community |
| Any EVM | `eip155:<chainId>` | Any EIP-3009 | Self-hosted or community |

### Why EIP-3009?

1. **Gas abstraction**: Buyers don't need ETH/native tokens for gas
2. **One-step payments**: No separate `approve()` transaction required
3. **Universal facilitator support**: Any EIP-3009 token works with any EVM facilitator
4. **Security**: Transfers authorized by cryptographic signatures with time bounds and nonces

## SDK Support Matrix

| Component | TypeScript | Go | Python |
|-----------|:---:|:---:|:---:|
| Core (Server/Client/Facilitator) | Yes | Yes | Yes |
| EVM (exact/eip3009) | Yes | Yes | Yes |
| SVM (exact/spl) | Yes | Yes | Yes |
| Stellar (exact/soroban) | Yes | No | No |
| Aptos (exact/fungible) | Yes | No | No |

### HTTP Framework Integrations

| Role | TypeScript | Go | Python |
|------|------------|-----|--------|
| Server | Express, Fastify, Hono, Next.js | Gin, Echo, net/http | FastAPI, Flask |
| Client | Fetch, Axios | net/http | httpx, requests |

## Going to Production (Mainnet)

### 1. Switch Facilitator URL

```typescript
const facilitator = new HTTPFacilitatorClient({
  url: "https://api.cdp.coinbase.com/platform/v2/x402"
});
```

See the [x402 Ecosystem](https://www.x402.org/ecosystem?filter=facilitators) for available production facilitators.

### 2. Update Network Identifiers

| Testnet | Mainnet |
|---------|---------|
| `eip155:84532` (Base Sepolia) | `eip155:8453` (Base Mainnet) |
| `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` (Devnet) | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` (Mainnet) |

### 3. Use Real Wallet Addresses

Ensure `payTo` addresses are real mainnet addresses where you want to receive USDC.

### 4. Test with Small Amounts First

Mainnet transactions involve real money. Always verify payments arrive correctly before going live.
