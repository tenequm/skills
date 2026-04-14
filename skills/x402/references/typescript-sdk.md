# TypeScript SDK Reference

## Packages (v2.9.0)

| Package | Purpose |
|---------|---------|
| `@x402/core` | Core types, `x402Client`, `x402ResourceServer`, `x402HTTPResourceServer`, `x402Facilitator`, `HTTPFacilitatorClient` |
| `@x402/evm` | EVM exact + upto schemes (EIP-3009, Permit2). Upto: `@x402/evm/upto/client`, `@x402/evm/upto/server`, `@x402/evm/upto/facilitator` |
| `@x402/svm` | Solana scheme (SPL TransferChecked) |
| `@x402/stellar` | Stellar scheme (SEP-41 Soroban token transfers) |
| `@x402/aptos` | Aptos scheme (Fungible Asset transfers) |
| `@x402/express` | Express.js middleware |
| `@x402/fastify` | Fastify middleware (not yet published on npm) |
| `@x402/hono` | Hono edge middleware |
| `@x402/next` | Next.js middleware (`paymentProxy`, `withX402`) |
| `@x402/axios` | Axios interceptor |
| `@x402/fetch` | Fetch wrapper |
| `@x402/paywall` | Browser paywall UI (EVM + SVM) |
| `@x402/mcp` | MCP client + server |
| `@x402/extensions` | Bazaar, offer-receipt, sign-in-with-x, payment-identifier, eip2612-gas-sponsoring, erc20-approval-gas-sponsoring |

## Recent Changes

**v2.9.0** - Upto scheme (usage-based billing) with full client/server/facilitator via `@x402/evm/upto/*`. Fastify adapter. New default assets: Stable (988/2201), Polygon (137), Arbitrum One/Sepolia, Mezo testnet. Exported hook types. Settlement overrides fix for upto. Repo moved to `x402-foundation/x402`.

**v2.8.0** - `HTTPFacilitatorClient` follows 308 redirects. Randomized facilitator signer selection. MCP `structuredContent` preserved in payment wrapper. Discovery method auto-populated from adapter.

**v2.7.0** - Bazaar dynamic routing. SIWx nonce/issuedAt auto-generation for auth-only routes. `extra: null` compatibility fix between Python facilitator and TS Zod schemas.

**v2.6.0** - Stellar scheme (`@x402/stellar`). Offer-receipt extension (draft). Permit2 on-chain simulation. Express `:param` dynamic route parameters. Custom `settlementFailedResponseBody`. Solana in-flight settlement cache.

## Core Subpath Exports

`@x402/core` exports from multiple subpaths:

| Subpath | Key Exports |
|---------|-------------|
| `@x402/core` | `x402Version` |
| `@x402/core/client` | `x402Client` |
| `@x402/core/server` | `x402ResourceServer`, `x402HTTPResourceServer`, `HTTPFacilitatorClient`, `RouteConfigurationError` |
| `@x402/core/facilitator` | `x402Facilitator` |
| `@x402/core/http` | `encodePaymentSignatureHeader`, `decodePaymentSignatureHeader`, `encodePaymentRequiredHeader`, `encodePaymentResponseHeader` |
| `@x402/core/types` | `PaymentRequired`, `PaymentRequirements`, `PaymentPayload`, `Network`, `VerifyError`, `SettleError`, `FacilitatorResponseError` |

## Core Types

```typescript
type Network = `${string}:${string}`; // CAIP-2 format: "eip155:84532", "solana:EtWTRA..."
type Money = string | number; // "$0.001", 0.001
type AssetAmount = { asset: string; amount: string; extra?: Record<string, unknown> };
type Price = Money | AssetAmount;

type PaymentRequirements = {
  scheme: string; network: Network; asset: string; amount: string;
  payTo: string; maxTimeoutSeconds: number; extra: Record<string, unknown>;
};

type PaymentRequired = {
  x402Version: number; error?: string; resource: ResourceInfo;
  accepts: PaymentRequirements[]; extensions?: Record<string, unknown>;
};

type PaymentPayload = {
  x402Version: number; resource?: ResourceInfo;
  accepted: PaymentRequirements; payload: Record<string, unknown>;
  extensions?: Record<string, unknown>;
};

type ResourceInfo = { url: string; description?: string; mimeType?: string };
```

## Mechanism Subpath Exports

Each mechanism (`@x402/evm`, `@x402/svm`, `@x402/stellar`, `@x402/aptos`) exports:

| Subpath | Key Export | Role |
|---------|-----------|------|
| `/exact/client` | `ExactEvmScheme`, `registerExactEvmScheme` | Client-side signing |
| `/exact/server` | `ExactEvmScheme`, `registerExactEvmScheme` | Server-side requirements |
| `/exact/facilitator` | `ExactEvmScheme`, `registerExactEvmScheme` | Facilitator verify/settle |

Replace `Evm` with `Svm`, `Stellar`, or `Aptos` accordingly.

### Upto Subpath Exports (`@x402/evm` only)

| Subpath | Key Export | Role |
|---------|-----------|------|
| `@x402/evm/upto/client` | `UptoEvmScheme` | Client-side max-amount signing |
| `@x402/evm/upto/server` | `UptoEvmScheme` | Server-side with `setSettlementOverrides` |
| `@x402/evm/upto/facilitator` | `UptoEvmScheme` | Facilitator verify/settle (variable amount) |

## Server: Express

```typescript
import express from "express";
import { paymentMiddleware } from "@x402/express";
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { ExactSvmScheme } from "@x402/svm/exact/server";

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

### Express: Three Middleware Variants

```typescript
// 1. paymentMiddleware(routes, server, paywallConfig?, paywall?, syncFacilitatorOnStart?)
// Simplest - pass routes and a pre-configured x402ResourceServer

// 2. paymentMiddlewareFromHTTPServer(httpServer, paywallConfig?, paywall?, syncFacilitatorOnStart?)
// Use when you need HTTP-level hooks (onProtectedRequest, etc.)
import { paymentMiddlewareFromHTTPServer } from "@x402/express";
import { x402HTTPResourceServer } from "@x402/core/server";

const httpServer = new x402HTTPResourceServer(server, routes);
httpServer.onProtectedRequest(async (context, routeConfig) => {
  // Grant free access, abort, or continue to payment
  if (isFreeUser(context)) return { grantAccess: true };
});
app.use(paymentMiddlewareFromHTTPServer(httpServer));

// 3. paymentMiddlewareFromConfig(routes, facilitatorClients?, schemes?, paywallConfig?, paywall?, syncFacilitatorOnStart?)
// Quick config-based setup - creates server internally
import { paymentMiddlewareFromConfig } from "@x402/express";
app.use(paymentMiddlewareFromConfig(routes, facilitator, [
  { network: "eip155:84532", server: new ExactEvmScheme() },
]));
```

## Server: Next.js

### Middleware Proxy (for pages)

```typescript
// middleware.ts
import { paymentProxy } from "@x402/next";
import { x402ResourceServer, HTTPFacilitatorClient } from "@x402/core/server";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { createPaywall } from "@x402/paywall";
import { evmPaywall } from "@x402/paywall/evm";
import { svmPaywall } from "@x402/paywall/svm";

const facilitator = new HTTPFacilitatorClient({ url: facilitatorUrl });
const server = new x402ResourceServer(facilitator);
server.register("eip155:84532", new ExactEvmScheme());

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
    accepts: { scheme: "exact", payTo: "0x123...", price: "$0.01", network: "eip155:84532" },
    description: "Weather API",
  },
  server,
);
```

### Next.js: Three Variants

```typescript
// Proxy variants: paymentProxy, paymentProxyFromHTTPServer, paymentProxyFromConfig
// Route handler variants: withX402, withX402FromHTTPServer
// All accept (paywallConfig?, paywall?, syncFacilitatorOnStart?) optional args
```

## Server: Hono

```typescript
import { Hono } from "hono";
import { paymentMiddleware } from "@x402/hono";

const app = new Hono();
app.use("/weather", paymentMiddleware({ /* same route config */ }, server));

// Also available: paymentMiddlewareFromHTTPServer, paymentMiddlewareFromConfig
```

## Server: Fastify

```typescript
import Fastify from "fastify";
import { paymentMiddleware } from "@x402/fastify";

const app = Fastify();
app.register(paymentMiddleware({ /* same route config */ }, server));

// Also available: paymentMiddlewareFromHTTPServer, paymentMiddlewareFromConfig
```

## Route Configuration

```typescript
interface RouteConfig {
  accepts: PaymentOption | PaymentOption[]; // Single or array
  resource?: string;
  description?: string;
  mimeType?: string;
  customPaywallHtml?: string;
  unpaidResponseBody?: (context: HTTPRequestContext) => HTTPResponseBody | Promise<HTTPResponseBody>;
  settlementFailedResponseBody?: (context: HTTPRequestContext, settleResult) => HTTPResponseBody | Promise<HTTPResponseBody>;
  extensions?: Record<string, unknown>;
}

interface PaymentOption {
  scheme: string;
  payTo: string | ((context: HTTPRequestContext) => string | Promise<string>);
  price: Price | ((context: HTTPRequestContext) => Price | Promise<Price>);
  network: Network;
  maxTimeoutSeconds?: number;
  extra?: Record<string, unknown>;
}

// Routes map: "METHOD /path" => RouteConfig, supports wildcards and params
type RoutesConfig = Record<string, RouteConfig> | RouteConfig;
// Patterns: "GET /api/*", "/api/[id]", "/api/:id"
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

## Client: x402Client API

```typescript
const client = new x402Client(paymentRequirementsSelector?);

// Registration (chainable)
client.register(network, schemeNetworkClient);   // v2
client.registerV1(network, schemeNetworkClient); // v1

// Policies - filter requirements before selection
client.registerPolicy((version, reqs) => reqs.filter(r => BigInt(r.amount) < BigInt("1000000")));
client.registerPolicy((version, reqs) => reqs.filter(r => r.network.startsWith("eip155:")));

// Client extensions - enrich payment payloads
client.registerExtension({ key: "eip2612GasSponsoring", enrichPaymentPayload: async (payload, required) => payload });

// Lifecycle hooks (chainable)
client.onBeforePaymentCreation(async (ctx) => { /* return { abort: true, reason } to abort */ });
client.onAfterPaymentCreation(async (ctx) => { /* ctx.paymentPayload available */ });
client.onPaymentCreationFailure(async (ctx) => { /* return { recovered: true, payload } to recover */ });

// Create payment
const payload = await client.createPaymentPayload(paymentRequired);

// Static factory
const client = x402Client.fromConfig({ schemes: [...], policies: [...], paymentRequirementsSelector });
```

## Server: x402ResourceServer API

```typescript
const server = new x402ResourceServer(facilitatorClients?);
// facilitatorClients: FacilitatorClient | FacilitatorClient[] (defaults to HTTPFacilitatorClient)

// Registration (chainable)
server.register(network, schemeNetworkServer);

// Extensions
server.registerExtension(extension);       // ResourceServerExtension
server.hasExtension(key);
server.getExtensions();
server.enrichExtensions(declaredExtensions, transportContext);

// Lifecycle hooks (chainable)
server.onBeforeVerify(async (ctx) => { /* return { abort: true, reason, message? } */ });
server.onAfterVerify(async (ctx) => { /* ctx.result available */ });
server.onVerifyFailure(async (ctx) => { /* return { recovered: true, result } */ });
server.onBeforeSettle(async (ctx) => { /* return { abort: true, reason, message? } */ });
server.onAfterSettle(async (ctx) => { /* ctx.result, ctx.transportContext available */ });
server.onSettleFailure(async (ctx) => { /* return { recovered: true, result } */ });

// Core methods
await server.initialize();
await server.buildPaymentRequirements(resourceConfig);
await server.buildPaymentRequirementsFromOptions(paymentOptions, context);
await server.createPaymentRequiredResponse(requirements, resourceInfo, error?, extensions?, transportContext?);
await server.verifyPayment(paymentPayload, requirements);
await server.settlePayment(paymentPayload, requirements, declaredExtensions?, transportContext?);
server.findMatchingRequirements(availableRequirements, paymentPayload);
```

## Server: x402HTTPResourceServer API

```typescript
const httpServer = new x402HTTPResourceServer(resourceServer, routes);

await httpServer.initialize(); // Calls resourceServer.initialize() + validates route configs

// Paywall
httpServer.registerPaywallProvider(provider);

// Protected request hook - runs before payment processing
httpServer.onProtectedRequest(async (context, routeConfig) => {
  // return { grantAccess: true } - skip payment
  // return { abort: true, reason } - deny (403)
  // return void - continue to payment flow
});

// Core processing
const result = await httpServer.processHTTPRequest(context, paywallConfig?);
// result.type: "no-payment-required" | "payment-verified" | "payment-error"

const settleResult = await httpServer.processSettlement(paymentPayload, requirements, declaredExtensions?, transportContext?);
// settleResult.success: true => settleResult.headers
// settleResult.success: false => settleResult.response (HTTPResponseInstructions)

httpServer.requiresPayment(context); // Check if route matches
httpServer.server;  // Access underlying x402ResourceServer
httpServer.routes;  // Access RoutesConfig
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

## Self-Facilitation (In-Process)

Run the facilitator in the same process as the resource server - no external facilitator URL needed:

```typescript
import { x402Facilitator } from "@x402/core/facilitator";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { toFacilitatorEvmSigner } from "@x402/evm";
import { registerExactEvmScheme } from "@x402/evm/exact/facilitator";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { createWalletClient, http, publicActions } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { baseSepolia } from "viem/chains";

const account = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const viemClient = createWalletClient({ account, chain: baseSepolia, transport: http() }).extend(publicActions);

const evmSigner = toFacilitatorEvmSigner({
  address: account.address,
  getCode: viemClient.getCode,
  readContract: viemClient.readContract,
  verifyTypedData: viemClient.verifyTypedData,
  writeContract: viemClient.writeContract,
  sendTransaction: viemClient.sendTransaction,
  waitForTransactionReceipt: viemClient.waitForTransactionReceipt,
});

const facilitator = new x402Facilitator();
registerExactEvmScheme(facilitator, { signer: evmSigner, networks: "eip155:84532" });

const server = new x402ResourceServer({
  verify: facilitator.verify.bind(facilitator),
  settle: facilitator.settle.bind(facilitator),
  getSupported: async () => facilitator.getSupported(),
}).register("eip155:84532", new ExactEvmScheme());

app.use(paymentMiddleware(routes, server));
```

## Facilitator: HTTPFacilitatorClient

```typescript
import { HTTPFacilitatorClient } from "@x402/core/server";

const facilitator = new HTTPFacilitatorClient({
  url: "https://x402.org/facilitator", // default
  createAuthHeaders: async () => ({
    verify: { Authorization: "Bearer ..." },
    settle: { Authorization: "Bearer ..." },
    supported: { Authorization: "Bearer ..." },
  }),
});

// FacilitatorClient interface: verify(), settle(), getSupported()
// Retries getSupported() on 429 with exponential backoff (3 attempts)
```

## Facilitator (Self-hosted)

```typescript
import { x402Facilitator } from "@x402/core/facilitator";
import { ExactEvmScheme } from "@x402/evm/exact/facilitator";
import { ExactSvmScheme } from "@x402/svm/exact/facilitator";

const facilitator = new x402Facilitator();
facilitator.register("eip155:84532", new ExactEvmScheme({ privateKey: process.env.FACILITATOR_KEY }));
facilitator.register(
  ["solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", "solana:devnet"],
  new ExactSvmScheme({ keypair }),
);

// register() accepts single network or array of networks
// registerV1() for v1 protocol support

// Extensions
facilitator.registerExtension(extension); // FacilitatorExtension
facilitator.getExtensions();              // string[] of registered keys
facilitator.getExtension<T>(key);         // typed extension lookup

// Lifecycle hooks (chainable)
facilitator.onBeforeVerify(async (ctx) => { /* return { abort: true, reason } */ });
facilitator.onAfterVerify(async (ctx) => { /* only on isValid: true */ });
facilitator.onVerifyFailure(async (ctx) => { /* return { recovered: true, result } */ });
facilitator.onBeforeSettle(async (ctx) => { /* return { abort: true, reason } */ });
facilitator.onAfterSettle(async (ctx) => {});
facilitator.onSettleFailure(async (ctx) => { /* return { recovered: true, result } */ });

// Core methods
facilitator.getSupported(); // { kinds, extensions, signers }
await facilitator.verify(paymentPayload, paymentRequirements);
await facilitator.settle(paymentPayload, paymentRequirements);

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
            price: (context) => calculatePrice(context), // HTTPRequestContext
            network: "eip155:84532",
            payTo: (context) => getPayToAddress(context), // HTTPRequestContext
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

## Upto Scheme (Usage-Based Billing)

Server advertises max price with `scheme: "upto"`, then calls `setSettlementOverrides` with actual usage:

```typescript
import { paymentMiddleware, setSettlementOverrides, x402ResourceServer } from "@x402/express";
import { UptoEvmScheme } from "@x402/evm/upto/server";

const server = new x402ResourceServer(facilitatorClient)
  .register("eip155:84532", new UptoEvmScheme());

const routes = {
  "GET /api/generate": {
    accepts: { scheme: "upto", price: "$0.10", network: "eip155:84532", payTo },
    description: "AI text generation - billed by token usage",
  },
};

app.get("/api/generate", (req, res) => {
  const actualCost = computeActualCost(); // your billing logic
  setSettlementOverrides(res, { amount: String(actualCost) }); // raw units, "$0.05", or "50%"
  res.json({ result: "..." });
});
```

Client registers both exact and upto schemes:

```typescript
import { UptoEvmScheme } from "@x402/evm/upto/client";
client.register("eip155:*", new UptoEvmScheme(signer));
```

## Custom Unpaid/Settlement Failure Responses

```typescript
"GET /weather": {
  accepts: [{ scheme: "exact", price: "$0.001", network: "eip155:84532", payTo }],
  description: "Weather data",
  unpaidResponseBody: async (context) => ({
    contentType: "application/json",
    body: { preview: "Weather data available", hint: "Pay to access full report" },
  }),
  settlementFailedResponseBody: async (context, settleResult) => ({
    contentType: "application/json",
    body: { error: "Payment settlement failed", reason: settleResult.errorReason },
  }),
}
```

## Extensions: Bazaar Discovery

```typescript
import { declareDiscoveryExtension, BAZAAR } from "@x402/extensions/bazaar";

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

// MCP tool discovery
declareDiscoveryExtension({
  toolName: "financial_analysis",
  description: "Analyze financial data for a given ticker",
  inputSchema: { type: "object", properties: { ticker: { type: "string" } }, required: ["ticker"] },
});

// Bazaar auto-registers as ResourceServerExtension when declared in route extensions
// Manual: server.registerExtension(bazaarResourceServerExtension)
```

## Extensions: Offer/Receipt

```typescript
import { createOfferReceiptExtension, declareOfferReceiptExtension } from "@x402/extensions/offer-receipt";

// Server: declare on route
extensions: {
  ...declareOfferReceiptExtension({ issuerDid: "did:key:..." }),
}

// Server: register extension
const offerReceiptExt = createOfferReceiptExtension(issuer);
server.registerExtension(offerReceiptExt);

// Client: extract
import { extractOffersFromPaymentRequired, extractReceiptFromResponse } from "@x402/extensions/offer-receipt";
```

## Extensions: Sign-in-with-x

```typescript
import { declareSIWxExtension, siwxResourceServerExtension } from "@x402/extensions/sign-in-with-x";

// Server: declare on route
extensions: {
  ...declareSIWxExtension({ domain: "example.com", statement: "Sign in" }),
}

// Server: register
server.registerExtension(siwxResourceServerExtension);

// Client
import { createSIWxPayload, wrapFetchWithSIWx } from "@x402/extensions/sign-in-with-x";
```

## Extensions: Gas Sponsoring

```typescript
// EIP-2612 (for tokens with EIP-2612 permit support)
import { declareEip2612GasSponsoringExtension } from "@x402/extensions";

extensions: {
  ...declareEip2612GasSponsoringExtension(),
}

// ERC-20 Approval (for generic ERC-20 tokens without EIP-2612)
import { declareErc20ApprovalGasSponsoringExtension } from "@x402/extensions";

extensions: {
  ...declareErc20ApprovalGasSponsoringExtension(),
}
```

## Extension Interfaces

```typescript
// Client extension (enriches payment payloads)
interface ClientExtension {
  key: string;
  enrichPaymentPayload?: (payload: PaymentPayload, required: PaymentRequired) => Promise<PaymentPayload>;
}

// Resource server extension (enriches 402 response and settlement)
interface ResourceServerExtension {
  key: string;
  enrichDeclaration?: (declaration: unknown, transportContext: unknown) => unknown;
  enrichPaymentRequiredResponse?: (declaration: unknown, context: PaymentRequiredContext) => Promise<unknown>;
  enrichSettlementResponse?: (declaration: unknown, context: SettleResultContext) => Promise<unknown>;
}

// Facilitator extension (provides capabilities to mechanisms)
interface FacilitatorExtension {
  key: string;
  // Extended by specific extensions with additional properties
}
```

## Error Types

```typescript
// VerifyError - thrown when payment verification fails
class VerifyError extends Error {
  statusCode: number; invalidReason?: string; invalidMessage?: string; payer?: string;
}

// SettleError - thrown when payment settlement fails
class SettleError extends Error {
  statusCode: number; errorReason?: string; errorMessage?: string;
  payer?: string; transaction: string; network: Network;
}

// FacilitatorResponseError - thrown when facilitator returns malformed data
class FacilitatorResponseError extends Error {}

// RouteConfigurationError - thrown when route config validation fails during initialize()
class RouteConfigurationError extends Error {
  errors: RouteValidationError[];
}

// Helper: getFacilitatorResponseError(error) - walks error cause chain
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
| `ExactEvmFacilitator` | `ExactEvmScheme` (from `/exact/facilitator`) |
