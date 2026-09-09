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

Introduced in spec 2025-03-26, replacing the HTTP+SSE transport from 2024-11-05 (now formally Deprecated). The server exposes a **single HTTP endpoint**.

> **Two eras.** Everything in this section describes the **2025-era wire** (`2024-10-07` through `2025-11-25`) - still the SDK v2 default and what deployed clients speak, so it remains the practical target. Spec **2026-07-28** removes sessions, the GET stream, DELETE termination, and SSE resumability outright; POST-only remains. Era differences are called out inline below, and the modern shape is documented in `references/spec-2026-07-28.md`.

### Request Flow (2025-era)

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

**Client MUST send on every request after initialization (2025-era):**
- `Accept: application/json, text/event-stream`
- `MCP-Protocol-Version: 2025-11-25` (added in spec 2025-06-18)
- `MCP-Session-Id: <id>` (if server assigned one)

**Server returns:**
- `Content-Type: application/json` (single response) OR `Content-Type: text/event-stream` (streaming)
- `MCP-Session-Id: <id>` on the InitializeResult response (stateful only)

**On 2026-07-28** there is no initialization and no session: client identity rides `_meta` per request, and POSTs additionally require `Mcp-Method` and `Mcp-Name` routing headers. A modern-only server receiving 2025-era traffic **SHOULD** respond: `405 Method Not Allowed` to GET or DELETE; ignore an `Mcp-Session-Id` header without minting or echoing one; ignore `Last-Event-ID` (streams are not resumable).

**The `MCP-Protocol-Version` header did not go away with `initialize`.** It is required on every modern POST *in addition to* the `_meta` field, and the two must agree:

> Every POST request to the MCP endpoint **MUST** include an `MCP-Protocol-Version` header. [...] The header value **MUST** match the `io.modelcontextprotocol/protocolVersion` field carried in the request body's `_meta`. If the values do not match, the server **MUST** reject the request with `400 Bad Request` and a `HeaderMismatch` JSON-RPC error.

The duplication is deliberate, and the spec generalizes it into a server duty for *every* mirrored header:

> Servers that process the request body **MUST** reject requests where the values specified in the headers do not match the corresponding values in the request body. This prevents potential security vulnerabilities when different components in the network rely on different sources of truth (e.g., a load balancer routing on the header value while the MCP server executes based on the body value).

So `Mcp-Method` and `Mcp-Name` need the same cross-check, after base64-sentinel decoding (see `spec-2026-07-28.md`). A header-less request is not automatically fatal: a server that supports pre-`2025-06-18` clients **MAY** treat it as `2025-03-26`; one that does not **MUST** reject it. The TS SDK closed the permissive gap on `main` - a modern POST with a valid `_meta` envelope but no header used to be classified modern, dispatched, and answered `200` with tool handlers running.

Validate `Origin` only when it is **present** - the spec's MUST-403 is scoped to *"present and invalid"*, and clients exist that omit it entirely.

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
  enableDnsRebindingProtection: true,          // defaults to FALSE
  allowedOrigins: ["https://app.example.com"], // unset by default
  allowedHosts: ["mcp.example.com"],           // unset by default
});
```

**The last three lines are not boilerplate.** `enableDnsRebindingProtection` defaults to `false`, and `allowedOrigins`/`allowedHosts` default to unset - so the two-option constructor everyone copies validates neither `Origin` nor `Host`, no matter what the spec says a server MUST do. The check is also all-or-nothing: with protection off the validator returns early, and with it on but a list empty, that list is skipped. The `@modelcontextprotocol/express` and `/hono` factories turn Host validation on for localhost; the raw transport does not.

### Operational Gotchas

- **Answer GET with an explicit 405 when you don't offer a stream.** Spec (2025-11-25): "The server MUST either return `Content-Type: text/event-stream` in response to this HTTP GET, or else return HTTP 405 Method Not Allowed." The official TS client special-cases 405 as the expected no-stream signal (`streamableHttp.ts`: `if (response.status === 405) { return; }` - silent, no retry); any other non-OK response, **including 406, throws**. A hand-rolled stateless server that answers GET with an empty `200` (or closes it instantly) sends official-SDK clients into a reconnect storm (hundreds of requests within minutes). The SDK transport won't do this for you: `WebStandardStreamableHTTPServerTransport` never returns 405 for GET - with a conforming `Accept` header it opens a (hanging) SSE stream even in stateless mode, and returns 406 only when the `Accept` header lacks `text/event-stream`. If your route only handles POST (the common stateless layout), return 405 for GET yourself.
- **A stateless transport instance is single-use.** Reusing it across requests throws `Stateless transport cannot be reused across requests` - create server + transport per request (the canonical pattern).
- **Only parse the body on POST.** Route GET and DELETE straight to the transport - calling `JSON.parse` (or a body-parsing middleware) on a bodyless GET/DELETE throws and 500s the request before the transport sees it.
- **Reject an unknown method loudly; never absorb it.** A modern-era client may open with a `server/discover` POST, and an intermediary that swallows the unrecognized method into an empty `2xx` bricks `connect()` outright: *"a server or intermediary (reverse proxy, API gateway, middlebox) that swallows the unrecognized `server/discover` POST into an empty 2xx bricks the connection, while one that rejects it with a 4xx degrades gracefully"* ([#2619](https://github.com/modelcontextprotocol/typescript-sdk/issues/2619)). The spec's own rule points the same way: an unimplemented RPC method **MUST** get `404 Not Found` plus a JSON-RPC `-32601`. Audit your gateway's catch-all route - a friendly `200 OK` is the failure mode here.
- **Transport-level rejections bypass your application logging.** A 406/405/415 emitted by the SDK transport never reaches app middleware, so "no errors in the logs" is not evidence the server is healthy. When a client reports a broken connection you cannot see, capture at the edge (access logs, proxy logs) rather than trusting app-level instrumentation.
- **Exclude GET from request-rate metrics.** SSE keep-alive traffic outnumbers real work by roughly two orders of magnitude - a keep-alive `GET /mcp` runs on the order of ~5 req/s per connection against ~0.01 req/s for actual tool calls. Any rate limit, autoscaling signal, or usage-billing filter on `/mcp` that counts GET is measuring noise.
- **SSE keep-alive is now built in.** Both lines write `: keepalive` comment frames to open SSE streams so idle connections survive intermediaries and idle timeouts, configurable via `keepAliveMs` (default `15000`; `0` disables). Shipped in v1.30.0 ([PR #2538](https://github.com/modelcontextprotocol/typescript-sdk/pull/2538), with per-stream timer lifecycle fixed in [PR #2547](https://github.com/modelcontextprotocol/typescript-sdk/pull/2547)) and in v2 via `createMcpHandler` ([PR #2541](https://github.com/modelcontextprotocol/typescript-sdk/pull/2541)). Don't hand-roll keep-alive on a current SDK.
- **Non-JSON POSTs are rejected with 415.** Since v1.30.0 / v2, the Content-Type is parsed as a media type rather than substring-matched, so a sloppy `Content-Type` that used to pass now fails ([PR #2444](https://github.com/modelcontextprotocol/typescript-sdk/pull/2444)). Custom transports composing `classifyInboundRequest`/`PerRequestHTTPServerTransport` must apply `isJsonContentType()` themselves.
- **Reusing a stateless transport surfaces as an opaque empty 500.** The assertion that guards single-use never reaches your error handling through the Node wrapper: *"The Node wrapper (`StreamableHTTPServerTransport` via `@hono/node-server`) converts that assertion into a bare `500` with an empty body - no `onerror`, no rejection"* ([#2704](https://github.com/modelcontextprotocol/typescript-sdk/issues/2704)). A bodyless 500 with silent logs is the signature of a transport being reused, not of a handler throwing.
- **Coming on `main`, not yet released** (`server@2.0.0` has none of it): every SDK-owned body read stops at a `maxRequestBodySize` of **4 MiB** and answers `413 Payload Too Large` before parsing, JSON-RPC batch arrays are capped at **100 messages**, and a modern POST without `MCP-Protocol-Version` is rejected rather than served. Size your own edge limits with those numbers in mind so the SDK's default is not the first thing your users discover.

### K8s Specifics

- No sticky sessions needed (`sessionIdGenerator: undefined`)
- Standard load balancer (round-robin) works
- Each pod handles any request independently
- Initialization happens per-request (spec: "initialization is required for capabilities negotiations regardless if it's stateless or stateless" - @ihrpr [#360](https://github.com/modelcontextprotocol/typescript-sdk/issues/360))

## Stateful Deployment (2025-era only)

For servers that need SSE notifications, long-running tasks, or multi-request workflows.

> **Removed in 2026-07-28.** Protocol-level sessions and `Mcp-Session-Id` are gone; list endpoints no longer vary per connection. Cross-call state moves to server-minted handles passed as ordinary tool arguments (see "Stateful Tools" in `SKILL.md`). Everything in this section applies only while you target a 2025-era wire - which is still the SDK default, so it is not dead code, but do not build *new* session infrastructure on it.

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

> **Removed in 2026-07-28**: SSE resumability is gone - `Last-Event-ID` and SSE event IDs left Streamable HTTP (SEP-2575), and clients MUST re-issue an interrupted request as a new request with a new ID. Don't invest in new persistent event stores for replay.

### Session Termination

- **Server terminates**: Responds with HTTP 404 to any request with the session ID. Client must re-initialize.
- **Client terminates**: Sends `DELETE /mcp` with `MCP-Session-Id`. Server cleans up resources.

## HTTP/2 Gotchas

### Content-Length on SSE Responses ([#1619](https://github.com/modelcontextprotocol/typescript-sdk/issues/1619))

Some HTTP adapters (e.g., `@hono/node-server`) buffer small SSE responses and add `Content-Length`. HTTP/2 forbids `Content-Length` on streaming responses, causing `PROTOCOL_ERROR` on stream close.

**Workaround**: Use `enableJsonResponse: true` for stateless servers (avoids SSE entirely). For stateful servers needing SSE, ensure your HTTP adapter doesn't add Content-Length to streaming responses, or add `Transfer-Encoding: chunked` manually.

### Transport Closure Stack Overflow ([#1699](https://github.com/modelcontextprotocol/typescript-sdk/issues/1699))

When 15-25+ transports close simultaneously (e.g., server restart, network partition), recursive promise rejection cascade causes `RangeError: Maximum call stack size exceeded`. Process stays alive but unresponsive.

**Fixed on the v2 line only** ([PR #1788](https://github.com/modelcontextprotocol/typescript-sdk/pull/1788), merged to `main` 2026-04-02, re-entrancy guard). No v1 backport was observed, so v1.30.0 is still affected - the guard below remains necessary on v1.

**Workaround (v1):**
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
