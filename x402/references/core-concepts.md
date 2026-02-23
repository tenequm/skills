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
| x402.org (default) | Base Sepolia, Solana Devnet | Testing/development, no setup needed |
| [Production facilitators](https://www.x402.org/ecosystem?category=facilitators) | Base, Solana, Polygon, Avalanche, etc. | Production use |
| Self-hosted | Any EVM chain | Full control |

**Key insight**: Facilitators support NETWORKS, not specific tokens. Any EIP-3009 token works on EVM networks, and any SPL/Token-2022 token works on Solana, as long as the facilitator supports that network.

## Wallet

In x402, a wallet is both a payment mechanism and a form of unique identity.

### For Buyers
- Store USDC/crypto
- Sign payment payloads (EIP-712 for EVM, Ed25519 for Solana)
- Authorize on-chain payments programmatically
- Wallets enable AI agents to transact without account creation

### For Sellers
- Receive USDC/crypto payments
- Define payment destination in server configuration (the `payTo` address)

### Recommended Wallet Solutions
- **CDP Wallet API** (https://docs.cdp.coinbase.com/wallet-api-v2/docs/welcome): Recommended for programmatic payments and secure key management
- **viem** / **ethers** HD wallets: For EVM
- **@solana/kit**: For Solana

Agents need wallets too. Programmatic wallets let agents sign EIP-712 payloads without exposing seed phrases.

## Networks and Token Support

### CAIP-2 Network Identifiers

x402 v2 uses CAIP-2 (Chain Agnostic Improvement Proposal) for unambiguous cross-chain support.

Format: `{namespace}:{reference}`

- **EVM**: `eip155:<chainId>` (e.g., `eip155:8453` for Base)
- **Solana**: `solana:<genesisHash>` (e.g., `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` for mainnet)

### Token Support

**EVM**: Any ERC-20 token implementing EIP-3009 (`transferWithAuthorization`). This enables:
- Gasless transfers (facilitator sponsors gas)
- One-step payments (no separate approval transactions)
- Signature-based authorization (off-chain signing)

**Solana**: Any SPL token or Token-2022 token. No EIP-712 configuration needed.

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

**Finding values on Basescan:**
- Name: Read `name()` function - e.g., https://basescan.org/token/0x833589fcd6edb6e08f4c7c32d4f71b54bda02913#readProxyContract#F16
- Version: Read `version()` function - e.g., https://basescan.org/token/0x833589fcd6edb6e08f4c7c32d4f71b54bda02913#readProxyContract#F24

```typescript
{
  extra: {
    name: "USD Coin",   // From name() function
    version: "2"        // From version() function
  }
}
```

### Adding New Networks (Dynamic Registration)

v2 uses dynamic network registration - support any EVM network without modifying source code.

**TypeScript:**
```typescript
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { registerExactEvmScheme } from "@x402/evm/exact/server";

const facilitator = new HTTPFacilitatorClient({
  url: "https://your-facilitator.com"  // Must support target network
});

const server = new x402ResourceServer(facilitator);
registerExactEvmScheme(server);  // Registers wildcard support for all EVM chains

// Use any CAIP-2 identifier in routes:
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
    {Network: x402.Network("eip155:43114"), Server: evm.NewExactEvmScheme()},  // Avalanche
}
```

**Python:**
```python
server = x402ResourceServer(facilitator)
server.register("eip155:43114", ExactEvmServerScheme())  # Avalanche mainnet
```

### Running Your Own Facilitator

If you need support for a custom network or want full control:

**Prerequisites:**
1. RPC endpoint for your target network
2. Wallet with native tokens for gas sponsorship
3. The x402 facilitator code

**TypeScript:**
```typescript
import { x402Facilitator } from "@x402/core";
import { ExactEvmFacilitator } from "@x402/evm/exact/facilitator";

const facilitator = new x402Facilitator();
facilitator.register("eip155:43114", new ExactEvmFacilitator({
  privateKey: process.env.FACILITATOR_KEY
}));

// Expose /verify, /settle, /supported endpoints via Express/Hono/etc.
```

### Quick Reference

| Network | CAIP-2 ID | Token Support | Default Facilitator |
|---------|-----------|---------------|-------------------|
| Base Mainnet | `eip155:8453` | Any EIP-3009 | Production facilitators |
| Base Sepolia | `eip155:84532` | Any EIP-3009 | x402.org (testnet) |
| Solana Mainnet | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | Any SPL/Token-2022 | Production facilitators |
| Solana Devnet | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` | Any SPL/Token-2022 | x402.org (testnet) |
| Any EVM | `eip155:<chainId>` | Any EIP-3009 | Self-hosted or community |

### Why EIP-3009?

1. **Gas abstraction**: Buyers don't need ETH/native tokens for gas
2. **One-step payments**: No separate `approve()` transaction required
3. **Universal facilitator support**: Any EIP-3009 token works with any EVM facilitator
4. **Security**: Transfers authorized by cryptographic signatures with time bounds and nonces

## Going to Production (Mainnet)

### 1. Switch Facilitator URL

Testnet uses `https://x402.org/facilitator`. For mainnet, use a production facilitator:

```typescript
// Production facilitator (e.g., Coinbase)
const facilitator = new HTTPFacilitatorClient({
  url: "https://api.cdp.coinbase.com/platform/v2/x402"
});
```

See the [x402 Ecosystem](https://www.x402.org/ecosystem?category=facilitators) for available production facilitators.

### 2. Update Network Identifiers

| Testnet | Mainnet |
|---------|---------|
| `eip155:84532` (Base Sepolia) | `eip155:8453` (Base Mainnet) |
| `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` (Devnet) | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` (Mainnet) |

### 3. Use Real Wallet Addresses

Ensure `payTo` addresses are real mainnet addresses where you want to receive USDC.

### 4. Test with Small Amounts First

Mainnet transactions involve real money. Always verify payments arrive correctly before going live.
