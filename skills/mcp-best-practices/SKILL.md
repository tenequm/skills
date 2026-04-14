---
name: mcp-best-practices
description: Build production MCP servers with the TypeScript SDK. Covers spec 2025-11-25, SDK v1.28+/v2, transport selection, tool design, error handling, security, performance, known bugs with workarounds, MCP extensions, MCP Apps (interactive UIs), authorization extensions, and the MCP Registry. Use this skill whenever building MCP servers, designing MCP tools, choosing MCP transports, handling MCP errors, migrating to MCP v2, reviewing MCP security, optimizing MCP token usage, building MCP Apps, using MCP extensions, publishing to the MCP Registry, or working with registerTool, McpServer, streamable HTTP, outputSchema, structuredContent, tool annotations, ext-apps, or ext-auth.
metadata:
  version: "0.2.1"
---

# MCP Best Practices

Decision reference for building production MCP servers with the TypeScript SDK. Not a tutorial - assumes you already have a working server and need to make it correct, fast, and secure.

## Quick Reference

| Component | Current | Next |
|-----------|---------|------|
| Spec | **2025-11-25** ([spec.modelcontextprotocol.io](https://spec.modelcontextprotocol.io)) | - |
| TS SDK (stable) | **v1.28.0** (`@modelcontextprotocol/sdk`) | v2 pre-alpha on `main` |
| TS SDK (v2) | Pre-alpha (`@modelcontextprotocol/server`, `/client`, `/core`) | Q1 2026 stable |
| JSON Schema | **2020-12** default (explicit `$schema` supported) | - |
| Transport | **Streamable HTTP** (remote), **stdio** (local) | SSE removed in v2 |
| Extensions | **MCP Apps** (GA), **Auth Extensions** (official) | Domain-specific WGs |
| Registry | **Preview** ([registry](https://modelcontextprotocol.io/registry/about)) | GA pending |

**v1 imports** (production today):
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
```

**v2 imports** (when stable):
```typescript
import { McpServer } from "@modelcontextprotocol/server";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";
```

## Server Setup

### Transport Decision

| Scenario | Transport | Key Config |
|----------|-----------|------------|
| Remote, stateless (K8s, CF Workers) | `WebStandardStreamableHTTPServerTransport` | `sessionIdGenerator: undefined`, `enableJsonResponse: true` |
| Remote, stateful (long tasks, SSE) | `WebStandardStreamableHTTPServerTransport` | `sessionIdGenerator: () => randomUUID()` |
| Local CLI / Claude Desktop | `StdioServerTransport` | Default |
| Legacy SSE clients | SSE removed in v2 - migrate to Streamable HTTP | - |

### Stateless Pattern (recommended for remote deployment)

Per-request server+transport creation is the canonical pattern. Maintainer @ihrpr confirms: "each transport should have an instance of MCPServer" ([#343](https://github.com/modelcontextprotocol/typescript-sdk/issues/343)). Sharing instances leaks cross-client data (GHSA-345p-7cg4-v4c7).

```typescript
app.post("/mcp", async (c) => {
  const server = new McpServer({ name: "my-server", version: "1.0.0" });
  // Register tools, resources, prompts...
  registerTools(server);

  const transport = new WebStandardStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,   // stateless - no session tracking
    enableJsonResponse: true,        // JSON responses, no SSE streaming
  });

  // All tools/resources must be registered before connect() (#893)
  try {
    await server.connect(transport);
    return transport.handleRequest(c.req.raw);
  } finally {
    await transport.close();
    await server.close();
  }
});
```

**What to hoist to module level** (don't recreate per request):
- Zod schemas (they never change)
- Annotation objects (`{ readOnlyHint: true, ... }`)
- Tool description strings
- Payment configs, upstream API clients

The McpServer itself must be per-request, but its constant inputs should not be.

> For deep dive on transports, sessions, HTTP/2 gotchas, and K8s deployment: see `references/transport-patterns.md`

### Framework Integration

**Hono** (web-standard):
```typescript
import { Hono } from "hono";
const app = new Hono();
app.post("/mcp", handleMcpRequest);  // WebStandardStreamableHTTPServerTransport
app.get("/mcp", handleMcpSse);       // Optional: SSE for server notifications
app.delete("/mcp", handleMcpDelete); // Optional: session termination
```

**Cloudflare Workers**: Same pattern - `WebStandardStreamableHTTPServerTransport` works natively in Workers runtime.

**Express/Node** (v2): Use `@modelcontextprotocol/express` middleware with `NodeStreamableHTTPServerTransport` (wraps the Web Standard transport for `IncomingMessage`/`ServerResponse`).

## Tool Design

### Registration API

**v1 (current stable)** - `server.tool()` works but has ambiguous overloads. Prefer the config-object form when possible:
```typescript
server.tool("search_docs", "Search documents", {
  query: z.string().describe("Search query"),
  max_results: z.number().optional().describe("Max results (default 20)"),
}, { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
  async ({ query, max_results }) => { /* handler */ }
);
```

**v2 (migration target)** - `registerTool()` with config object:
```typescript
server.registerTool("search_docs", {
  title: "Document Search",
  description: "Search documents by keyword or phrase",
  inputSchema: z.object({
    query: z.string().describe("Search query"),
    max_results: z.number().optional().describe("Max results (default 20)"),
  }),
  outputSchema: z.object({
    results: z.array(z.object({ id: z.string(), text: z.string() })),
    has_more: z.boolean(),
  }),
  annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
}, async ({ query, max_results }) => {
  const result = await fetchDocs(query, max_results);
  return {
    structuredContent: result,
    content: [{ type: "text", text: JSON.stringify(result) }],
  };
});
```

### Naming

Spec (2025-11-25): 1-128 chars, case-sensitive. Allowed: `A-Za-z0-9_-.`

**DO**: `search_docs`, `get_user_profile`, `admin.tools.list`
**DON'T**: `search` (too generic, collides across servers), `Search Docs` (spaces not allowed)

Service-prefix your tools (`github_*`, `jira_*`) when multiple servers are active - LLMs confuse generic names across servers.

### Schema Rules

`.describe()` on every field - this is what LLMs use for argument generation.

> For complete Zod-to-JSON-Schema conversion rules, what breaks silently, outputSchema/structuredContent patterns: see `references/tool-schema-guide.md`

**Critical bugs**:
- `z.union()` / `z.discriminatedUnion()` silently produce empty schemas ([#1643](https://github.com/modelcontextprotocol/typescript-sdk/issues/1643)). Use flat `z.object()` with `z.enum()` discriminator field instead.
- Plain JSON Schema objects silently dropped before v1.28.0. Fixed in v1.28 - now throws at registration ([#1596](https://github.com/modelcontextprotocol/typescript-sdk/issues/1596)).
- `z.transform()` stripped during conversion - JSON Schema can't represent transforms ([#702](https://github.com/modelcontextprotocol/typescript-sdk/issues/702)).

### Annotations

All are optional hints (untrusted from untrusted servers per spec):

| Annotation | Default | Meaning |
|------------|---------|---------|
| `readOnlyHint` | `false` | Tool doesn't modify its environment |
| `destructiveHint` | `true` | May perform destructive updates (only when readOnly=false) |
| `idempotentHint` | `false` | Repeated calls with same args have no additional effect |
| `openWorldHint` | `true` | Interacts with external entities (APIs, web) |

Set them accurately - clients use them for consent prompts and auto-approval decisions.

**Open SEPs expanding annotations**:
- `#1913` Trust and Sensitivity - data classification hints
- `#1984` Comprehensive annotations for governance/UX
- `#1561` `unsafeOutputHint` - output may contain untrusted content
- `#1560` `secretHint` - tool handles secrets/credentials
- `#1487` `trustedHint` - server attestation of tool trustworthiness

**The "Lethal Trifecta"**: Combining (1) access to private data + (2) exposure to untrusted content + (3) external communication ability creates data theft conditions. Researchers demonstrated this with a malicious calendar event, an MCP calendar server, and a code execution tool. Design tool sets to avoid granting all three simultaneously.

**Evaluation framework for new annotation proposals**:
1. What client behavior changes? (No concrete action = don't add it)
2. Does it require trust to be useful? (If yes, doesn't help against untrusted servers)
3. Could `_meta` handle it? (Namespaced metadata better for single-deployment needs)
4. Does it help reason about tool combinations?
5. Is it a hint or contract? (Contracts belong in auth/transport/runtime layer)

## Error Handling

Two distinct mechanisms with different LLM visibility:

| Type | LLM Sees It? | Use For |
|------|--------------|---------|
| **Tool error** (`isError: true` in CallToolResult) | Yes - enables self-correction | Input validation, API failures, business logic errors |
| **Protocol error** (JSON-RPC error response) | Maybe - clients MAY expose | Unknown tool, malformed request, server crash |

Per SEP-1303 (merged into spec 2025-11-25): input validation errors MUST be tool execution errors, not protocol errors. The LLM needs to see "date must be in the future" to self-correct.

```typescript
// DO: Tool execution error - LLM can self-correct
return {
  isError: true,
  content: [{ type: "text", text: "Date must be in the future. Current date: 2026-03-25" }],
};

// DON'T: Protocol error for validation - LLM can't see this
throw new McpError(ErrorCode.InvalidParams, "Invalid date");
```

**Known bug**: The SDK loses `error.data` when converting `McpError` to tool results ([PR #1075](https://github.com/modelcontextprotocol/typescript-sdk/pull/1075)). If you embed structured data in McpError's data field, it may not reach the client. Use `isError: true` tool results with structured content instead.

> For full error taxonomy, code examples, and payment error patterns: see `references/error-handling.md`

## Resources and Instructions

### Server Instructions

Set in the initialization response - acts as a system-level hint to the LLM about how to use your server:

```typescript
const server = new McpServer({
  name: "docs-api",
  version: "1.0.0",
  instructions: "Knowledge base API. Use search_docs for full-text search, get_doc for retrieval by ID. All tools are read-only.",
});
```

### Resource Registration

Expose documentation or structured data via `docs://` URI scheme:

```typescript
server.resource("search-operators", "docs://search-operators", {
  title: "Search Operators Guide",
  description: "Supported search operators and syntax",
  mimeType: "text/markdown",
}, async () => ({
  contents: [{ uri: "docs://search-operators", text: operatorsMarkdown }],
}));
```

## Performance

### Module-Level Caching

The McpServer must be per-request, but everything else can be shared:

```typescript
// Module-level (created once)
const SCHEMAS = {
  search: z.object({ query: z.string().describe("Search query") }),
  fetch: z.object({ id: z.string().describe("Resource ID") }),
};
const READ_ONLY_ANNOTATIONS = {
  readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true,
} as const;

// Per-request (created each time)
function createMcpServer(ctx: Context) {
  const server = new McpServer({ name: "my-server", version: "1.0.0" });
  server.tool("search", "Search", SCHEMAS.search, READ_ONLY_ANNOTATIONS, handler);
  return server;
}
```

### Token Bloat Mitigation

Tool definitions consume context window before any conversation starts. GitHub MCP: 20,444 tokens for 80 tools (SEP-1576).

**Strategies**:
1. **5-15 tools per server** - community sweet spot. Split beyond that.
2. **Outcome-oriented tools** - bundle multi-step operations into single tools (e.g., `track_order(email)` not `get_user` + `list_orders` + `get_status`).
3. **Response granularity** - return curated results, not raw API dumps. 800-token user object vs 20-token summary.
4. **`outputSchema` + `structuredContent`** - lets clients process data programmatically without LLM parsing overhead.
5. **Dynamic tool loading** - register only relevant tool subsets based on request context (e.g., `?tools=search,fetch` query parameter).

### No-Parameter Tools

For tools with no inputs, use explicit empty schema:
```typescript
inputSchema: { type: "object" as const, additionalProperties: false }
```

## Security

### Top Threats (real-world incidents, 2025)

| Attack | Example | Mitigation |
|--------|---------|------------|
| **Tool poisoning** | Hidden instructions in descriptions (WhatsApp MCP, Apr 2025) | Review tool descriptions; clients should display them |
| **Supply chain** | Malicious npm packages (Smithery breach, Oct 2025) | Pin versions, audit dependencies |
| **Command injection** | `child_process.exec` with unsanitized input (CVE-2025-53967) | Never interpolate user input into shell commands |
| **Cross-server shadowing** | Malicious server overrides legitimate tool names | Service-prefix tool names; validate tool sources |
| **Token theft** | Over-privileged PATs with broad scopes | Minimal scopes; OAuth 2.1 Resource Indicators (RFC 8707) |
| **Token passthrough** | Server accepts/forwards tokens not issued for it | Validate audience claim; never transit client tokens to upstream APIs |
| **SSRF** | Malicious OAuth metadata URLs targeting internal services | HTTPS enforcement, block private IPs, validate redirect targets |
| **Confused deputy** | Proxy server consent cookies exploited via DCR | Per-client consent before forwarding to third-party auth |
| **Session hijacking** | Stolen/guessed session IDs for impersonation | Cryptographically random IDs, bind to user identity, never use for auth |

### Server-Side Requirements (spec normative)

- **Validate all inputs** at tool boundaries
- **Implement access controls** per user/session
- **Rate limit** tool invocations
- **Sanitize outputs** before returning to client
- **Validate `Origin` header** - respond 403 for invalid origins (2025-11-25 requirement)
- **Require `MCP-Protocol-Version` header** on all requests after initialization (spec 2025-06-18+)
- **Bind local servers to localhost** (127.0.0.1) only

### Auth (OAuth 2.1)

MCP normatively requires **OAuth 2.1** ([draft-ietf-oauth-v2-1-13](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-13)). The spec states: "Authorization servers MUST implement OAuth 2.1." PKCE is mandatory, implicit flow is removed. Always build against OAuth 2.1 - not 2.0.

MCP servers are OAuth 2.1 Resource Servers. Clients MUST include Resource Indicators (RFC 8707) binding tokens to specific servers. Key requirements:

- **Validate audience** - reject tokens not issued for your server (token passthrough is explicitly forbidden)
- **PKCE mandatory** - use `S256` code challenge method
- **Short-lived tokens** - reduce blast radius of leaked credentials
- **Scope minimization** - start with minimal scopes, elevate incrementally via `WWW-Authenticate` challenges
- **Don't implement token validation yourself** - use tested libraries (Keycloak, Auth0, etc.)
- **Don't log credentials** - never log Authorization headers, tokens, or secrets

> For full security attack/mitigation patterns and auth implementation details: see `references/security-auth.md`

## Known SDK Bugs

| Issue | Severity | Status | Workaround |
|-------|----------|--------|------------|
| [#1643](https://github.com/modelcontextprotocol/typescript-sdk/issues/1643) - `z.union()`/`z.discriminatedUnion()` silently dropped | High | Open | Use flat `z.object()` + `z.enum()` |
| [#1699](https://github.com/modelcontextprotocol/typescript-sdk/issues/1699) - Transport closure stack overflow (15-25+ concurrent) | High | Open | `uncaughtException` handler + process restart |
| [#1619](https://github.com/modelcontextprotocol/typescript-sdk/issues/1619) - HTTP/2 + SSE Content-Length error | Medium | Open | Use `enableJsonResponse: true` or avoid HTTP/2 upstream |
| [#893](https://github.com/modelcontextprotocol/typescript-sdk/issues/893) - Dynamic registration after connect blocked | Medium | Open | Register all tools/resources before `connect()` |
| [#1596](https://github.com/modelcontextprotocol/typescript-sdk/issues/1596) - Plain JSON Schema silently dropped | Fixed | v1.28.0 | Upgrade to v1.28+ |
| GHSA-345p-7cg4-v4c7 - Shared instances leak cross-client data | Critical | v1.26.0 | Per-request server+transport (the canonical pattern) |

## V2 Migration

> For comprehensive migration guide with all breaking changes and before/after code: see `references/v2-migration.md`

**Key breaking changes**:
1. Package split: `@modelcontextprotocol/sdk` -> `@modelcontextprotocol/server` + `/client` + `/core`
2. ESM only, Node.js 20+
3. Zod v4 required (or any Standard Schema library)
4. `McpError` -> `ProtocolError` (from `@modelcontextprotocol/core`)
5. `extra` parameter -> structured `ctx` with `ctx.mcpReq`
6. `server.tool()` -> `registerTool()` (config object, not positional args)
7. SSE server transport removed (clients can still connect to legacy SSE servers)
8. `@modelcontextprotocol/hono` and `@modelcontextprotocol/express` middleware packages
9. DNS rebinding protection enabled by default for localhost servers

v1.x gets 6 more months of support after v2 stable ships. No rush, but write new code with v2 patterns in mind.

## Extensions

MCP extensions are optional, strictly additive capabilities on top of the core protocol. Both sides negotiate support during initialization via `extensions` in capabilities.

**Identifiers**: `{vendor-prefix}/{extension-name}`. Official: `io.modelcontextprotocol/*`. Third-party: reversed domain (e.g., `com.example/my-ext`).

### Official Extensions

| Extension | Identifier | Purpose |
|-----------|-----------|---------|
| **MCP Apps** | `io.modelcontextprotocol/ui` | Interactive HTML UIs in chat (charts, forms, dashboards) |
| **OAuth Client Credentials** | `io.modelcontextprotocol/oauth-client-credentials` | Machine-to-machine auth (CI/CD, daemons, server-to-server) |
| **Enterprise-Managed Auth** | `io.modelcontextprotocol/enterprise-managed-authorization` | Centralized access control via enterprise IdP |

**Client support**: Claude (web + Desktop), ChatGPT, VS Code Copilot, Goose, Postman, MCPJam all support MCP Apps. Auth extensions not yet widely adopted.

> For MCP Apps architecture, ext-apps SDK, and build patterns: see `references/mcp-apps.md`
> For extensions system, auth extensions, and MCP Registry: see `references/extensions-registry.md`

### Server Capabilities Beyond Tools

| Capability | Purpose | v2 API |
|-----------|---------|--------|
| **Elicitation** | Request structured user input mid-tool | `ctx.mcpReq.elicitInput()` |
| **Sampling** | Request LLM completion from client | `ctx.mcpReq.requestSampling()` |
| **Tasks** (SEP-1686) | Long-running ops with lifecycle management | Pending |
| **Progress** | Incremental progress on requests | `ctx.mcpReq.sendProgress()` |
