# TypeScript SDK Reference

## Packages

| Package | npm | Purpose |
|---------|-----|---------|
| `@x402/core` | Core types, `x402Client`, `x402ResourceServer`, `x402Facilitator` |
| `@x402/evm` | EVM scheme (EIP-3009 + Permit2) |
| `@x402/svm` | Solana scheme (SPL TransferChecked) |
| `@x402/stellar` | Stellar scheme (SEP-41 Soroban token transfers) |
| `@x402/aptos` | Aptos scheme (Fungible Asset transfers) |
| `@x402/express` | Express.js middleware |
| `@x402/hono` | Hono edge middleware |
| `@x402/next` | Next.js middleware (`paymentProxy`, `withX402`) |
| `@x402/axios` | Axios interceptor |
| `@x402/fetch` | Fetch wrapper |
| `@x402/paywall` | Browser paywall UI (EVM + SVM) |
| `@x402/mcp` | MCP client + server |
| `@x402/extensions` | Bazaar, payment-identifier, sign-in-with-x |

## Server: Express

```typescript
import express from "express";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { ExactSvmScheme } from "@x402/svm/exact/server";
import { HTTPFacilitatorClient } from "@x402/core/server";

const app = express();
const payTo = "0xYourWalletAddress";

const facilitator = new HTTPFacilitatorClient({ url: "https://x402.org/facilitator" });
const server = new x402ResourceServer(facilitator)
  .register("eip155:84532", new ExactEvmScheme())
  .register("solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", new ExactSvmScheme());

app.use(
  paymentMiddleware(
    {
      "GET /weather": {
        accepts: [
          { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo },
          { scheme: "exact", price: "$0.001", network: "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", payTo: svmAddress },
        ],
        description: "Weather data",
        mimeType: "application/json",
      },
    },
    server,
  ),
);

app.get("/weather", (req, res) => {
  res.json({ report: { weather: "sunny", temperature: 70 } });
});

app.listen(4021);
```

## Server: Next.js

### Middleware Proxy (for pages)

```typescript
// middleware.ts
import { paymentProxy } from "@x402/next";
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { registerExactEvmScheme } from "@x402/evm/exact/server";
import { createPaywall } from "@x402/paywall";
import { evmPaywall } from "@x402/paywall/evm";
import { svmPaywall } from "@x402/paywall/svm";

const facilitator = new HTTPFacilitatorClient({ url: facilitatorUrl });
const server = new x402ResourceServer(facilitator);
registerExactEvmScheme(server);

const paywall = createPaywall()
  .withNetwork(evmPaywall)
  .withNetwork(svmPaywall)
  .withConfig({ appName: "My App", testnet: true })
  .build();

export default paymentProxy(
  {
    "/protected": {
      accepts: [{ scheme: "exact", price: "$0.001", network: "eip155:84532", payTo }],
      description: "Protected content",
      mimeType: "text/html",
    },
  },
  server,
  undefined,
  paywall,
);

export const config = { matcher: ["/protected/:path*"] };
```

### Route Handler (for API routes)

```typescript
// app/api/weather/route.ts
import { withX402 } from "@x402/next";
import { NextRequest, NextResponse } from "next/server";

const handler = async (req: NextRequest) => {
  return NextResponse.json({ weather: "sunny" }, { status: 200 });
};

export const GET = withX402(
  handler,
  {
    accepts: [{ scheme: "exact", price: "$0.001", network: "eip155:84532", payTo }],
    description: "Weather API",
    mimeType: "application/json",
  },
  server,
  undefined,
  paywall,
);
```

## Server: Hono

```typescript
import { Hono } from "hono";
import { paymentMiddleware } from "@x402/hono";

const app = new Hono();
app.use("/weather", paymentMiddleware({ /* same route config */ }, server));
```

## Client: Axios

```typescript
import { x402Client, wrapAxiosWithPayment, x402HTTPClient } from "@x402/axios";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { registerExactSvmScheme } from "@x402/svm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { base58 } from "@scure/base";
import axios from "axios";

const evmSigner = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);

const client = new x402Client();
registerExactEvmScheme(client, { signer: evmSigner });

// Optional: add Solana support
const svmSigner = await createKeyPairSignerFromBytes(base58.decode(process.env.SVM_PRIVATE_KEY));
registerExactSvmScheme(client, { signer: svmSigner });

const api = wrapAxiosWithPayment(axios.create({ baseURL: "http://localhost:4021" }), client);
const response = await api.get("/weather");

// Read settlement response
const httpClient = new x402HTTPClient(client);
const settlement = httpClient.getPaymentSettleResponse(
  name => response.headers[name.toLowerCase()],
);
```

## Client: Fetch

```typescript
import { x402Client, wrapFetchWithPayment, x402HTTPClient } from "@x402/fetch";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
registerExactEvmScheme(client, { signer });

const fetchWithPayment = wrapFetchWithPayment(fetch, client);
const response = await fetchWithPayment("http://localhost:4021/weather", { method: "GET" });
const data = await response.json();

// Read settlement response
const httpClient = new x402HTTPClient(client);
const settlement = httpClient.getPaymentSettleResponse(name => response.headers.get(name));
```

## Client: Policies

Filter payment requirements before selection:

```typescript
const client = new x402Client();
registerExactEvmScheme(client, { signer });

// Prefer cheaper options
client.registerPolicy((version, reqs) =>
  reqs.filter(r => BigInt(r.amount) < BigInt("1000000"))
);

// Prefer specific networks
client.registerPolicy((version, reqs) =>
  reqs.filter(r => r.network.startsWith("eip155:"))
);
```

## MCP Server

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createPaymentWrapper } from "@x402/mcp";
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";

const facilitator = new HTTPFacilitatorClient({ url: facilitatorUrl });
const resourceServer = new x402ResourceServer(facilitator)
  .register("eip155:84532", new ExactEvmScheme());

const requirements = await resourceServer.buildPaymentRequirements([
  { scheme: "exact", price: "$0.001", network: "eip155:84532", payTo },
]);

const paidTool = createPaymentWrapper(resourceServer, requirements);

const mcpServer = new McpServer({ name: "My Paid MCP", version: "1.0.0" });

mcpServer.tool("weather", "Get weather data", {}, paidTool(async (args) => {
  return { content: [{ type: "text", text: JSON.stringify({ weather: "sunny" }) }] };
}));
```

## MCP Client

```typescript
import { createx402MCPClient } from "@x402/mcp";
import { x402Client } from "@x402/core";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";

const paymentClient = new x402Client();
registerExactEvmScheme(paymentClient, { signer });

const x402Mcp = await createx402MCPClient({
  name: "my-client",
  transport: new SSEClientTransport(new URL("http://localhost:4022/sse")),
  paymentClient,
});

await x402Mcp.connect();
const tools = await x402Mcp.listTools();
const result = await x402Mcp.callTool("weather", { city: "SF" });
```

## Paywall (Browser UI)

```typescript
import { createPaywall } from "@x402/paywall";
import { evmPaywall } from "@x402/paywall/evm";
import { svmPaywall } from "@x402/paywall/svm";

const paywall = createPaywall()
  .withNetwork(evmPaywall)
  .withNetwork(svmPaywall)
  .withConfig({
    appName: "My App",
    appLogo: "/logo.png",
    testnet: true,
  })
  .build();

// Pass to middleware for browser-facing endpoints
paymentMiddleware(routes, server, undefined, paywall);
```

## Facilitator (Self-hosted)

```typescript
import { x402Facilitator } from "@x402/core";
import { ExactEvmFacilitator } from "@x402/evm/exact/facilitator";
import { ExactSvmFacilitator } from "@x402/svm/exact/facilitator";

const facilitator = new x402Facilitator();
facilitator.register("eip155:84532", new ExactEvmFacilitator({ privateKey: process.env.FACILITATOR_KEY }));
facilitator.register("solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", new ExactSvmFacilitator({ keypair }));

// Expose /verify, /settle, /supported endpoints
```

## Dynamic Pricing and PayTo

```typescript
app.use(
  paymentMiddleware(
    {
      "GET /weather": {
        accepts: [
          {
            scheme: "exact",
            price: (req) => calculatePrice(req), // Dynamic price function
            network: "eip155:84532",
            payTo: (req) => getPayToAddress(req), // Dynamic payTo function
          },
        ],
        description: "Weather data",
        mimeType: "application/json",
      },
    },
    server,
  ),
);
```

## Extensions: Bazaar Discovery

```typescript
import { declareDiscoveryExtension } from "@x402/extensions/bazaar";

"GET /weather": {
  accepts: [{ scheme: "exact", price: "$0.001", network: "eip155:84532", payTo }],
  description: "Weather API",
  mimeType: "application/json",
  extensions: {
    ...declareDiscoveryExtension({
      output: { example: { weather: "sunny", temperature: 72 } }
    }),
  },
}
```

## V1 to V2 Migration

| V1 | V2 |
|----|----|
| `x402` | `@x402/core` |
| `x402-express` | `@x402/express` |
| `x402-axios` | `@x402/axios` |
| `x402-fetch` | `@x402/fetch` |
| `withPaymentInterceptor` | `wrapAxiosWithPayment` |
| `X-PAYMENT` header | `PAYMENT-SIGNATURE` header |
| `X-PAYMENT-RESPONSE` header | `PAYMENT-RESPONSE` header |
| `base-sepolia` | `eip155:84532` (CAIP-2) |
| Wallet passed directly | `x402Client` + `registerExactEvmScheme` |
