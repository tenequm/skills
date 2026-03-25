# Transport Patterns

Deep dive on Streamable HTTP transport, session management, stateless deployment, and known issues.

## Table of Contents
- [Streamable HTTP Protocol](#streamable-http-protocol)
- [Stateless Deployment](#stateless-deployment)
- [Stateful Deployment](#stateful-deployment)
- [Session Management](#session-management)
- [HTTP/2 Gotchas](#http2-gotchas)
- [CORS Configuration](#cors-configuration)
- [Framework Examples](#framework-examples)

## Streamable HTTP Protocol

Introduced in spec 2025-03-26, replacing the HTTP+SSE transport from 2024-11-05. The server exposes a **single HTTP endpoint** supporting POST, GET, and DELETE.

### Request Flow

```
Client                              Server
  |                                    |
  |-- POST /mcp (initialize) -------->|
  |<-- 200 + MCP-Session-Id ----------|  (optional, stateful only)
  |                                    |
  |-- POST /mcp (tools/call) -------->|  (include Accept: application/json, text/event-stream)
  |<-- 200 application/json -----------|  (or text/event-stream for streaming)
  |                                    |
  |-- GET /mcp ---------------------->|  (optional: open SSE stream for server notifications)
  |<-- 200 text/event-stream ---------|
  |                                    |
  |-- DELETE /mcp ------------------->|  (terminate session)
  |<-- 200 ---------------------------|
```

### Required Headers

**Client MUST send on every request after initialization:**
- `Accept: application/json, text/event-stream`
- `MCP-Protocol-Version: 2025-11-25` (added in spec 2025-06-18)
- `MCP-Session-Id: <id>` (if server assigned one)

**Server returns:**
- `Content-Type: application/json` (single response) OR `Content-Type: text/event-stream` (streaming)
- `MCP-Session-Id: <id>` on the InitializeResult response (stateful only)

### Response Modes

For client notifications/responses: `202 Accepted` with no body.

For client requests, server chooses:
- **JSON response** (`enableJsonResponse: true`): Returns `application/json` with a single JSON-RPC response. Best for stateless, request/response patterns.
- **SSE stream**: Returns `text/event-stream` with JSON-RPC messages as SSE events. Required for long-running operations, progress notifications, or multi-part responses.

## Stateless Deployment

The recommended pattern for K8s, Cloudflare Workers, and any horizontally-scaled environment. Maintainer @ihrpr: "If you need a stateless server, transport (and server object) will be created on every request" ([#330](https://github.com/modelcontextprotocol/typescript-sdk/issues/330)).

### What You Give Up

- Server-initiated notifications (GET SSE stream)
- SSE resumability (`Last-Event-ID`)
- Long-running tasks with progress updates
- Session affinity

### What You Keep

- Full tool invocation (POST -> JSON response)
- Capability negotiation (initialization per request)
- Horizontal scaling without sticky sessions

### Configuration

```typescript
const transport = new WebStandardStreamableHTTPServerTransport({
  sessionIdGenerator: undefined,    // no session tracking
  enableJsonResponse: true,         // always return JSON, never SSE
});
```

### K8s Specifics

- No sticky sessions needed (`sessionIdGenerator: undefined`)
- Standard load balancer (round-robin) works
- Each pod handles any request independently
- Initialization happens per-request (spec: "initialization is required for capabilities negotiations regardless if it's stateless or stateless" - @ihrpr [#360](https://github.com/modelcontextprotocol/typescript-sdk/issues/360))

## Stateful Deployment

For servers that need SSE notifications, long-running tasks, or multi-request workflows.

### Session ID Requirements (spec 2025-11-25)

- Globally unique
- Cryptographically secure random
- Visible ASCII only (0x21-0x7E)
- Transmitted via `MCP-Session-Id` header

### Multi-Node Stateful

Requires routing by `MCP-Session-Id` header to the same node:
- Sticky sessions via load balancer header routing
- Distributed session store (but note: transport objects cannot be serialized to Redis - @ihrpr [#330](https://github.com/modelcontextprotocol/typescript-sdk/issues/330))
- Session registry mapping IDs to node addresses

### SSE Resumability (spec 2025-11-25)

Servers MAY support SSE resumability:
1. Attach globally unique event IDs to SSE events
2. Send an initial SSE event with event ID + empty data to prime reconnection
3. Client reconnects via `GET /mcp` with `Last-Event-ID` header
4. Server replays events from that ID forward

The official `everything` server uses `InMemoryEventStore` for this. Production deployments need persistent event stores.

### Session Termination

- **Server terminates**: Responds with HTTP 404 to any request with the session ID. Client must re-initialize.
- **Client terminates**: Sends `DELETE /mcp` with `MCP-Session-Id`. Server cleans up resources.

## HTTP/2 Gotchas

### Content-Length on SSE Responses ([#1619](https://github.com/modelcontextprotocol/typescript-sdk/issues/1619))

Some HTTP adapters (e.g., `@hono/node-server`) buffer small SSE responses and add `Content-Length`. HTTP/2 forbids `Content-Length` on streaming responses, causing `PROTOCOL_ERROR` on stream close.

**Workaround**: Use `enableJsonResponse: true` for stateless servers (avoids SSE entirely). For stateful servers needing SSE, ensure your HTTP adapter doesn't add Content-Length to streaming responses, or add `Transfer-Encoding: chunked` manually.

### Transport Closure Stack Overflow ([#1699](https://github.com/modelcontextprotocol/typescript-sdk/issues/1699))

When 15-25+ transports close simultaneously (e.g., server restart, network partition), recursive promise rejection cascade causes `RangeError: Maximum call stack size exceeded`. Process stays alive but unresponsive.

**Workaround**:
```typescript
process.on("uncaughtException", (err) => {
  if (err instanceof RangeError && err.message.includes("Maximum call stack")) {
    console.error("Transport closure stack overflow, restarting...");
    process.exit(1);  // Let systemd/K8s restart
  }
  throw err;
});
```

## CORS Configuration

For remote MCP servers accessed from browser-based clients, expose these headers:

```typescript
// Required CORS headers for MCP
const corsHeaders = {
  "Access-Control-Expose-Headers": "mcp-session-id, last-event-id, mcp-protocol-version",
  "Access-Control-Allow-Headers": "content-type, accept, mcp-session-id, last-event-id, mcp-protocol-version",
};
```

**Origin validation** (spec 2025-11-25): Servers MUST validate the `Origin` header on all requests. Invalid Origin MUST receive HTTP 403 Forbidden. The `@modelcontextprotocol/express` v2 middleware includes DNS rebinding protection by default for localhost servers.

## Framework Examples

### Hono (Web Standard)

```typescript
import { Hono } from "hono";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";

const app = new Hono();

app.post("/mcp", async (c) => {
  const server = new McpServer({ name: "api", version: "1.0.0" });
  registerTools(server);

  const transport = new WebStandardStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });

  try {
    await server.connect(transport);
    return transport.handleRequest(c.req.raw);
  } finally {
    await transport.close();
    await server.close();
  }
});
```

### Cloudflare Workers

Same pattern as Hono - `WebStandardStreamableHTTPServerTransport` works natively:

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    if (request.method === "POST" && new URL(request.url).pathname === "/mcp") {
      const server = new McpServer({ name: "worker-api", version: "1.0.0" });
      registerTools(server);

      const transport = new WebStandardStreamableHTTPServerTransport({
        sessionIdGenerator: undefined,
        enableJsonResponse: true,
      });

      await server.connect(transport);
      const response = await transport.handleRequest(request);
      await transport.close();
      await server.close();
      return response;
    }
    return new Response("Not Found", { status: 404 });
  },
};
```

### Express (v2 with middleware)

```typescript
import express from "express";
import { createMcpExpressApp } from "@modelcontextprotocol/express";

const mcpApp = createMcpExpressApp(
  (server) => {
    registerTools(server);
  },
  { name: "api", version: "1.0.0" },
);

const app = express();
app.use("/mcp", mcpApp);
app.listen(3000);
```

Note: `createMcpExpressApp` includes DNS rebinding protection by default for localhost.
