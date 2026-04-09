# V2 Migration Guide

Comprehensive guide for migrating from `@modelcontextprotocol/sdk` v1 to v2. v2 is currently pre-alpha on the `main` branch. v1.x remains recommended for production. Stable v2 expected Q1 2026.

## Table of Contents
- [Package Split](#package-split)
- [Import Changes](#import-changes)
- [Runtime Requirements](#runtime-requirements)
- [API Changes](#api-changes)
- [Schema Changes](#schema-changes)
- [Error Model](#error-model)
- [Transport Changes](#transport-changes)
- [Middleware Packages](#middleware-packages)
- [Migration Checklist](#migration-checklist)

## Package Split

v1 ships as a single package. v2 splits into focused packages:

| v1 | v2 | Purpose |
|----|-----|---------|
| `@modelcontextprotocol/sdk` | `@modelcontextprotocol/server` | Build MCP servers |
| `@modelcontextprotocol/sdk` | `@modelcontextprotocol/client` | Build MCP clients |
| (internal) | `@modelcontextprotocol/core` | Shared protocol types, schemas |
| - | `@modelcontextprotocol/node` | Node.js HTTP transport middleware |
| - | `@modelcontextprotocol/express` | Express middleware + DNS rebinding protection |
| - | `@modelcontextprotocol/hono` | Hono middleware |

## Import Changes

### Server

```typescript
// v1
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

// v2
import { McpServer } from "@modelcontextprotocol/server";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server";
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/core";
```

### Client

```typescript
// v1
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

// v2
import { Client } from "@modelcontextprotocol/client";
```

## Runtime Requirements

| Requirement | v1 | v2 |
|-------------|----|----|
| Module system | CJS + ESM | **ESM only** |
| Node.js | 16+ | **20+** |
| Zod | v3 | **v4** (or any Standard Schema library) |

### ESM Migration

If your project uses CommonJS, you need to switch to ESM:

```json
// package.json
{
  "type": "module"
}
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "module": "nodenext",
    "moduleResolution": "nodenext"
  }
}
```

## API Changes

### Tool Registration

The biggest API change. Positional overloads replaced with config object:

```typescript
// v1 - server.tool() with positional args (deprecated)
server.tool(
  "search_docs",                                      // name
  "Search documents",                                 // description
  { query: z.string(), limit: z.number().optional() }, // schema (raw shape)
  { readOnlyHint: true, idempotentHint: true },       // annotations
  async ({ query, limit }) => { /* handler */ },       // handler
);

// v2 - registerTool() with config object
server.registerTool("search_docs", {
  title: "Document Search",
  description: "Search documents",
  inputSchema: z.object({
    query: z.string().describe("Search query"),
    limit: z.number().optional().describe("Max results"),
  }),
  outputSchema: z.object({
    results: z.array(z.object({ id: z.string(), text: z.string() })),
    has_more: z.boolean(),
  }),
  annotations: { readOnlyHint: true, idempotentHint: true },
}, async ({ query, limit }) => {
  const result = await doSearch(query, limit);
  return {
    structuredContent: result,
    content: [{ type: "text", text: JSON.stringify(result) }],
  };
});
```

Key differences:
- Config object instead of positional args (no more overload ambiguity - [#452](https://github.com/modelcontextprotocol/typescript-sdk/issues/452))
- `inputSchema` must be `z.object()` (not raw shape `{ key: z.string() }`)
- `title` field for human-readable display name
- `outputSchema` support for typed outputs

### Resource Registration

```typescript
// v1
server.resource("config", "config://app", { mimeType: "text/plain" },
  async (uri) => ({ contents: [{ uri: uri.href, text: "..." }] })
);

// v2
server.registerResource("config", "config://app", {
  title: "Application Config",
  description: "App configuration data",
  mimeType: "text/plain",
}, async (uri) => ({
  contents: [{ uri: uri.href, text: "..." }],
}));
```

### Handler Context (extra -> ctx)

```typescript
// v1 - extra parameter (unstructured)
server.tool("my-tool", schema, async (args, extra) => {
  // extra has limited, untyped fields
});

// v2 - ctx parameter (structured, typed)
server.registerTool("my-tool", config, async (args, ctx) => {
  // Logging
  await ctx.mcpReq.log("info", "Processing request");

  // Sampling (request LLM completion)
  const response = await ctx.mcpReq.requestSampling({
    messages: [{ role: "user", content: { type: "text", text: "Summarize this" } }],
    maxTokens: 100,
  });

  // Elicitation (request user input)
  const input = await ctx.mcpReq.elicitInput({
    message: "Please confirm the operation",
    requestedSchema: { type: "object", properties: { confirm: { type: "boolean" } } },
  });

  // Abort signal
  ctx.mcpReq.signal.addEventListener("abort", () => { /* cleanup */ });
});
```

## Schema Changes

### Zod v4 Required

v2 uses Zod v4 as a peer dependency. The SDK's internal schemas import `zod/v4`:

```typescript
// v2 internals
import * as z from "zod/v4";
```

**Public API uses Standard Schema interfaces** - any library implementing `StandardSchemaWithJSON` works:
- Zod v4
- ArkType
- Valibot

### inputSchema Must Be z.object()

v1 accepted raw shapes `{ key: z.string() }` and wrapped them internally. v2 requires explicit `z.object()`:

```typescript
// v1 - raw shape (implicitly wrapped)
server.tool("my-tool", "desc", {
  query: z.string(),
  limit: z.number().optional(),
}, handler);

// v2 - explicit z.object()
server.registerTool("my-tool", {
  inputSchema: z.object({
    query: z.string(),
    limit: z.number().optional(),
  }),
}, handler);
```

### JSON Schema 2020-12 Default

The spec now defaults to JSON Schema 2020-12 if no `$schema` field is present. Zod v4's `z.toJSONSchema()` produces 2020-12 output natively.

## Error Model

### McpError -> ProtocolError

```typescript
// v1
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";
throw new McpError(ErrorCode.InternalError, "Something broke");

// v2
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/core";
throw new ProtocolError(ProtocolErrorCode.InternalError, "Something broke");
```

### New SdkError (local errors)

v2 splits errors into wire errors and local errors:

```typescript
import { SdkError, SdkErrorCode } from "@modelcontextprotocol/core";

// Local SDK errors that never cross the wire
throw new SdkError(SdkErrorCode.NOT_CONNECTED, "Not connected to transport");
throw new SdkError(SdkErrorCode.REQUEST_TIMEOUT, "Request timed out");
```

## Transport Changes

### SSE Server Transport Removed

v2 removes `SSEServerTransport` from the server package. Clients can still connect to legacy SSE servers.

```typescript
// v1 - SSE transport available
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

// v2 - REMOVED. Use WebStandardStreamableHTTPServerTransport instead
```

### DNS Rebinding Protection

`createMcpExpressApp()` and `createMcpHonoApp()` include Host header validation by default for localhost servers. This prevents DNS rebinding attacks where a malicious website could access your local MCP server.

## Middleware Packages

### @modelcontextprotocol/hono

```typescript
import { createMcpHonoApp } from "@modelcontextprotocol/hono";

const mcpApp = createMcpHonoApp(
  (server) => {
    server.registerTool("my-tool", config, handler);
  },
  { name: "my-server", version: "1.0.0" },
);

const app = new Hono();
app.route("/mcp", mcpApp);
```

### @modelcontextprotocol/express

```typescript
import { createMcpExpressApp } from "@modelcontextprotocol/express";

const mcpApp = createMcpExpressApp(
  (server) => {
    server.registerTool("my-tool", config, handler);
  },
  { name: "my-server", version: "1.0.0" },
);

const app = express();
app.use("/mcp", mcpApp);
```

## Migration Checklist

### Phase 1: Prepare (do now, on v1)

- [ ] Use `.describe()` on every Zod schema field
- [ ] Use `z.object()` wrappers (not raw shapes) for tool schemas
- [ ] Set tool annotations on all tools
- [ ] Use `isError: true` for all tool-level errors (not McpError for validation)
- [ ] Bump to SDK v1.28.0 (catches plain JSON Schema errors, security fix)
- [ ] Register all tools/resources before `connect()` ([#893](https://github.com/modelcontextprotocol/typescript-sdk/issues/893))
- [ ] Ensure per-request server+transport pattern (not shared instances)

### Phase 2: Migrate (when v2 is stable)

- [ ] Switch to ESM (`"type": "module"` in package.json)
- [ ] Upgrade Node.js to 20+
- [ ] Upgrade Zod to v4
- [ ] Replace `@modelcontextprotocol/sdk` with split packages
- [ ] Replace `server.tool()` with `registerTool()`
- [ ] Replace `server.resource()` with `registerResource()`
- [ ] Replace `McpError` with `ProtocolError`
- [ ] Update handler signatures: `extra` -> `ctx`
- [ ] Remove any SSEServerTransport usage
- [ ] Add `outputSchema` + `structuredContent` to tools
- [ ] Switch to framework middleware if using Hono/Express
- [ ] Test with `MCP-Protocol-Version: 2025-11-25` header

### Phase 3: Optimize (after migration)

- [ ] Add `outputSchema` to all tools for typed outputs
- [ ] Implement dynamic tool loading for large tool sets
- [ ] Use `structuredContent` for all responses
- [ ] Review DNS rebinding protection settings
- [ ] Remove any Zod v3 compatibility shims

### Timeline

v1.x gets 6 months of support after v2 stable ships. Given v2 stable is expected Q1 2026, v1 support likely extends through Q3 2026. No rush to migrate, but write new code with v2 patterns in mind.
