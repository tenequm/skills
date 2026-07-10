---
name: x402
description: "Build internet-native payments with the x402 open protocol - HTTP 402 Payment Required for on-chain micropayments with no accounts or API keys. Use when developing paid APIs, paywalled content, AI agent payment flows, or MCP tools that charge per call. Covers the TypeScript, Python, and Go SDKs across EVM, Solana, Stellar, and Aptos."
metadata:
  version: "0.10.1"
  upstream: "@x402/core@2.17.0, @x402/evm@2.17.0, x402@2.14.0, github.com/x402-foundation/x402/go/v2@v2.17.0"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/x402
    emoji: "💰"
    primaryEnv: EVM_PRIVATE_KEY
    envVars:
      - name: EVM_PRIVATE_KEY
        required: false
        description: EVM signer key for x402 client/server.
      - name: APTOS_PRIVATE_KEY
        required: false
        description: Aptos signer for x402 on Aptos.
      - name: FACILITATOR_KEY
        required: false
        description: Self-hosted facilitator signing key.
      - name: FACILITATOR_URL
        required: false
        description: Facilitator endpoint URL override.
---

# x402 Protocol Development

x402 is an open standard (Apache-2.0) that activates the HTTP `402 Payment Required` status code for programmatic, on-chain payments. Originally created by Coinbase, now maintained by the [x402 Foundation](https://github.com/x402-foundation/x402). No accounts, sessions, or API keys required - clients pay with signed crypto transactions directly over HTTP.

## When to Use

- Building a **paid API** that accepts crypto micropayments
- Adding **paywall** to web content or endpoints
- Enabling **AI agents** to autonomously pay for resources
- Integrating **MCP tools** that require payment
- Building **agent-to-agent** (A2A) payment flows
- Working with **EVM** (Base, Ethereum, MegaETH, Monad, Polygon, Stable, Arbitrum), **Solana**, **Stellar**, or **Aptos** payment settlement
- Implementing **usage-based billing** with the `upto` scheme (LLM tokens, bandwidth, compute)
- Running an **in-process facilitator** (self-facilitation) without external facilitator dependency

## Core Architecture

Three roles in every x402 payment:

1. **Resource Server** - protects endpoints, returns 402 with payment requirements
2. **Client** - signs payment authorization, retries request with payment header
3. **Facilitator** - verifies signatures, settles transactions on-chain

Payment flow (HTTP transport):
```
Client -> GET /resource -> Server returns 402 + PAYMENT-REQUIRED header
Client -> signs payment -> retries with PAYMENT-SIGNATURE header
Server -> POST /verify to Facilitator -> POST /settle to Facilitator
Server -> returns 200 + PAYMENT-RESPONSE header + resource data
```

## Quick Start: Seller (TypeScript + Express)

```typescript
import express from "express";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { HTTPFacilitatorClient } from "@x402/core/server";

const app = express();
const payTo = "0xYourWalletAddress";

const facilitator = new HTTPFacilitatorClient({ url: "https://x402.org/facilitator" });
const server = new x402ResourceServer(facilitator)
  .register("eip155:84532", new ExactEvmScheme());

app.use(
  paymentMiddleware(
    {
      "GET /weather": {
        accepts: [
          { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo },
        ],
        description: "Weather data",
        mimeType: "application/json",
      },
    },
    server,
  ),
);

app.get("/weather", (req, res) => {
  res.json({ weather: "sunny", temperature: 70 });
});

app.listen(4021);
```

Install: `npm install @x402/express @x402/core @x402/evm`

## Quick Start: Buyer (TypeScript + Axios)

```typescript
import { x402Client, wrapAxiosWithPayment } from "@x402/axios";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import axios from "axios";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
registerExactEvmScheme(client, { signer });

const api = wrapAxiosWithPayment(axios.create(), client);
const response = await api.get("http://localhost:4021/weather");
// Payment handled automatically on 402 response
```

Install: `npm install @x402/axios @x402/evm viem`

## Quick Start: Seller (Python + FastAPI)

```python
from fastapi import FastAPI
from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer

app = FastAPI()

facilitator = HTTPFacilitatorClient(FacilitatorConfig(url="https://x402.org/facilitator"))
server = x402ResourceServer(facilitator)
server.register("eip155:84532", ExactEvmServerScheme())

routes = {
    "GET /weather": RouteConfig(
        accepts=[PaymentOption(scheme="exact", pay_to="0xYourAddress", price="$0.001", network="eip155:84532")],
        mime_type="application/json",
        description="Weather data",
    ),
}
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

@app.get("/weather")
async def get_weather():
    return {"weather": "sunny", "temperature": 70}
```

Install: `pip install "x402[fastapi,evm]"`

## Quick Start: Seller (Go + Gin)

```go
import (
    x402http "github.com/x402-foundation/x402/go/v2/http"
    ginmw "github.com/x402-foundation/x402/go/v2/http/gin"
    evm "github.com/x402-foundation/x402/go/v2/mechanisms/evm/exact/server"
)

facilitator := x402http.NewHTTPFacilitatorClient(&x402http.FacilitatorConfig{URL: facilitatorURL})

routes := x402http.RoutesConfig{
    "GET /weather": {
        Accepts: x402http.PaymentOptions{
            {Scheme: "exact", Price: "$0.001", Network: "eip155:84532", PayTo: evmAddress},
        },
        Description: "Weather data",
        MimeType:    "application/json",
    },
}

r.Use(ginmw.X402Payment(ginmw.Config{
    Routes:      routes,
    Facilitator: facilitator,
    Schemes:     []ginmw.SchemeConfig{{Network: "eip155:84532", Server: evm.NewExactEvmScheme()}},
}))
```

Install: `go get github.com/x402-foundation/x402/go/v2`

## Multi-Network Support (EVM + Solana)

Servers can accept payment on multiple networks simultaneously:

```typescript
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { ExactSvmScheme } from "@x402/svm/exact/server";

const server = new x402ResourceServer(facilitator)
  .register("eip155:84532", new ExactEvmScheme())
  .register("solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", new ExactSvmScheme());

// Route config with both networks
"GET /weather": {
  accepts: [
    { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo: evmAddress },
    { scheme: "exact", price: "$0.001", network: "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", payTo: svmAddress },
  ],
}
```

Clients register both schemes and auto-select based on server requirements:

```typescript
const client = new x402Client();
registerExactEvmScheme(client, { signer: evmSigner });
registerExactSvmScheme(client, { signer: svmSigner });
```

## Supported Networks

| Network | CAIP-2 ID | Status |
|---------|-----------|--------|
| Base Mainnet | `eip155:8453` | Mainnet |
| Base Sepolia | `eip155:84532` | Testnet |
| MegaETH Mainnet | `eip155:4326` | Mainnet (MegaUSD default, 18 decimals) |
| Solana Mainnet | `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` | Mainnet |
| Solana Devnet | `solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1` | Testnet |
| Stellar Mainnet | `stellar:pubnet` | Mainnet (TypeScript SDK only) |
| Stellar Testnet | `stellar:testnet` | Testnet (TypeScript SDK only) |
| Aptos Mainnet | `aptos:1` | Mainnet (TypeScript SDK only) |
| Aptos Testnet | `aptos:2` | Testnet (TypeScript SDK only) |
| Monad Mainnet | `eip155:143` | Mainnet |
| Polygon Mainnet | `eip155:137` | Mainnet |
| Polygon Amoy | `eip155:80002` | Testnet |
| Stable Mainnet | `eip155:988` | Mainnet |
| Stable Testnet | `eip155:2201` | Testnet |
| Arbitrum One | `eip155:42161` | Mainnet |
| Arbitrum Sepolia | `eip155:421614` | Testnet |
| XDC Network Mainnet | `eip155:50` | Mainnet (USDC) |
| XDC Apothem Testnet | `eip155:51` | Testnet (USDC) |
| Mezo Mainnet | `eip155:31612` | Mainnet (mUSD, 18 decimals, Permit2 + EIP-2612) |
| Mezo Testnet | `eip155:31611` | Testnet (mUSD, Permit2 + EIP-2612) |
| Avalanche | `eip155:43114` | Runtime registration only (no default asset; community facilitators) |
| Radius Mainnet | `eip155:723487` | Mainnet (SBC default) |
| Radius Testnet | `eip155:72344` | Testnet (SBC default) |
| ADI Chain | `eip155:36900` | Mainnet (USDC.e default) |
| HPP Mainnet | `eip155:190415` | Mainnet (Bridged USDC default) |
| HPP Sepolia | `eip155:181228` | Testnet (Bridged USDC default) |
| TON Mainnet | `tvm:-239` | Mainnet (jetton transfers; Python + TypeScript SDK) |
| TON Testnet | `tvm:-3` | Testnet |
| Hedera Mainnet | `hedera:mainnet` | Mainnet (HBAR + HTS tokens) |
| Hedera Testnet | `hedera:testnet` | Testnet |
| Algorand Mainnet | `algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=` | Mainnet (USDC ASA) |
| Keeta Mainnet | `keeta:21378` | Mainnet (TypeScript SDK) |
| Keeta Testnet | `keeta:1413829460` | Testnet (TypeScript SDK) |
| Concordium Mainnet | `ccd:9dd9ca4d19e9393877d2c44b70f89acb` | Mainnet (native CCD, 6 decimals; TypeScript SDK) |
| Concordium Testnet | `ccd:4221332d34e1694168c2a0c0b3fd0f27` | Testnet (native CCD; TypeScript SDK) |

Default facilitator (`https://x402.org/facilitator`) supports Base Sepolia, Solana Devnet, Stellar Testnet, Aptos Testnet, and Hedera Testnet.

## SDK Packages

### TypeScript v2.17.0 ([npm](https://www.npmjs.com/org/x402), [GitHub](https://github.com/x402-foundation/x402/tree/main/typescript))
| Package | Purpose |
|---------|---------|
| `@x402/core` | Core types, client, server, facilitator |
| `@x402/evm` | EVM exact + upto schemes (EIP-3009, Permit2). Upto via `@x402/evm/upto/*` subpaths |
| `@x402/svm` | Solana scheme (SPL TransferChecked) |
| `@x402/stellar` | Stellar scheme (SEP-41 Soroban token transfers) |
| `@x402/aptos` | Aptos scheme (Fungible Asset transfers) |
| `@x402/avm` | Algorand (AVM) scheme |
| `@x402/hedera` | Hedera scheme (HBAR + HTS fungible-asset transfers) |
| `@x402/tvm` | TON scheme (jetton transfers) |
| `@x402/keeta` | Keeta scheme (exact) |
| `@x402/concordium` | Concordium scheme (native CCD, exact) |
| `@x402/express` | Express middleware |
| `@x402/fastify` | Fastify middleware |
| `@x402/hono` | Hono edge middleware |
| `@x402/next` | Next.js middleware |
| `@x402/axios` | Axios interceptor |
| `@x402/fetch` | Fetch wrapper |
| `@x402/paywall` | Browser paywall UI |
| `@x402/mcp` | MCP client + server |
| `@x402/extensions` | Bazaar, offer-receipt, payment-identifier, sign-in-with-x, gas sponsoring |

### Python v2.14.0 ([PyPI](https://pypi.org/project/x402/), [GitHub](https://github.com/x402-foundation/x402/tree/main/python))
```bash
pip install "x402[httpx]"      # Async HTTP client
pip install "x402[requests]"   # Sync HTTP client
pip install "x402[fastapi]"    # FastAPI server
pip install "x402[flask]"      # Flask server
pip install "x402[svm]"        # Solana support
pip install "x402[mcp]"        # MCP integration
pip install "x402[extensions]" # Extensions (bazaar, gas sponsoring, etc.)
pip install "x402[all]"        # Everything
```

### Go v2.17.0 ([GitHub](https://github.com/x402-foundation/x402/tree/main/go))

The Go module path carries a `/v2` suffix - the bare `.../x402/go` path no longer resolves tagged releases.

```bash
go get github.com/x402-foundation/x402/go/v2
```

### Java (Java 17+, [GitHub](https://github.com/x402-foundation/x402/tree/main/java))

A fourth official binding is in the repo (`PaymentFilter`, `FacilitatorClient`, `X402HttpClient`). Not published to a package registry yet - build from source.

## Key Concepts

- **Client/Server/Facilitator**: The three roles in every payment. Client signs, server enforces, facilitator settles on-chain. See `references/core-concepts.md`
- **Wallet**: Both payment mechanism and identity for buyers/sellers. See `references/core-concepts.md`
- **Networks & Tokens**: CAIP-2 identifiers, EIP-3009 tokens on EVM, SPL on Solana, custom token config. See `references/core-concepts.md`
- **Scheme**: Payment method. `exact` = transfer exact amount; `upto` = authorize max, settle actual usage (EVM Permit2 only); `batch-settlement` = commit at request time, settle asynchronously; `auth-capture` = escrow / authorize-then-capture with void, refund, reclaim. See `references/evm-scheme.md`, `references/svm-scheme.md`, `references/stellar-scheme.md`, `references/upto-scheme.md`, `references/aptos-scheme.md`, `references/protocol-spec.md`
- **Self-facilitation**: Run an in-process facilitator instead of calling an external URL. See `references/typescript-sdk.md`, `references/go-sdk.md`
- **Transport**: How payment data is transmitted (HTTP headers, MCP `_meta`, A2A metadata). See `references/transports.md`
- **Extensions**: Optional features (bazaar discovery, offer-receipt attestations, payment-identifier idempotency, sign-in-with-x auth, gas sponsoring, builder-code attribution, http-message-signatures, auth-hints). See `references/extensions.md`
- **Hooks**: Lifecycle callbacks on client/server/facilitator (TS, Python, Go). See `references/lifecycle-hooks.md`
- **Protocol types**: `PaymentRequired`, `PaymentPayload`, `SettlementResponse`. See `references/protocol-spec.md`
- **Custom tokens**: Use `registerMoneyParser` for non-USDC tokens, Permit2 for non-EIP-3009 tokens. See `references/evm-scheme.md`
- **Mainnet deployment**: Switch facilitator URL, network IDs, and wallet addresses. See `references/core-concepts.md`

## References

| File | Content |
|------|---------|
| `references/core-concepts.md` | HTTP 402 foundation, client/server/facilitator roles, wallet identity, networks, tokens, custom token config, dynamic registration, self-hosted facilitator, mainnet deployment |
| `references/protocol-spec.md` | v2 protocol types, payment flow, facilitator API, error codes |
| `references/typescript-sdk.md` | TypeScript SDK patterns for server, client, MCP, paywall, facilitator |
| `references/python-sdk.md` | Python SDK patterns for server, client, MCP (server + client), facilitator |
| `references/go-sdk.md` | Go SDK patterns for server, client, MCP, facilitator, signers, custom money parser |
| `references/evm-scheme.md` | EVM exact scheme: EIP-3009, Permit2, default asset resolution, registerMoneyParser, custom tokens |
| `references/svm-scheme.md` | Solana exact scheme: SPL TransferChecked, verification rules, duplicate settlement mitigation |
| `references/stellar-scheme.md` | Stellar exact scheme: SEP-41 Soroban token transfers, ledger-based expiration, fee sponsorship, TypeScript SDK only |
| `references/upto-scheme.md` | Upto (usage-based) scheme: authorize max amount, settle actual usage. EVM via Permit2 only |
| `references/aptos-scheme.md` | Aptos exact scheme: fungible asset transfers, fee payer sponsorship, TypeScript SDK only |
| `references/transports.md` | HTTP, MCP, A2A transport implementations |
| `references/extensions.md` | Bazaar, payment-identifier, sign-in-with-x, gas sponsoring (eip2612 + erc20) extensions |
| `references/lifecycle-hooks.md` | Client/server/facilitator hooks (TypeScript, Python, Go), hook chaining, MCP hooks |

## Official Resources

- GitHub: https://github.com/x402-foundation/x402
- Spec: https://github.com/x402-foundation/x402/tree/main/specs
- Docs: https://docs.x402.org
- Website: https://x402.org
- Ecosystem: https://x402.org/ecosystem
- Foundation Charter: https://github.com/x402-foundation/x402/tree/main/foundation
