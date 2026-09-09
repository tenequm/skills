# V2 Migration Guide

Comprehensive guide for migrating from `@modelcontextprotocol/sdk` v1 to v2. **v2 is stable**: `2.0.0` shipped 2026-07-27 alongside the released 2026-07-28 spec revision, with all nine packages cut simultaneously and versioned in lockstep. v1.x is now the legacy line - it "continues to receive bug fixes and security updates for at least 6 months after v2's release", with source on the long-lived [`v1.x` branch](https://github.com/modelcontextprotocol/typescript-sdk/tree/v1.x) rather than `main`. Canonical v2 docs (tutorial, troubleshooting, generated API reference): [ts.sdk.modelcontextprotocol.io/v2](https://ts.sdk.modelcontextprotocol.io/v2/).

> **Upgrading to v2 does not change your protocol revision.** v2 speaks the 2025-era wire by default; 2026-07-28 is opt-in via `versionNegotiation`. See "The Two Eras" in `SKILL.md` and `references/spec-2026-07-28.md`.

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
| - | `@modelcontextprotocol/fastify` | Fastify middleware (added 2.0.0-alpha.1, [PR #1536](https://github.com/modelcontextprotocol/typescript-sdk/pull/1536)) |
| - | `@modelcontextprotocol/server-legacy` | Frozen v1 SSE transport + OAuth Authorization Server helpers, for v1->v2 migration (added 2.0.0-alpha.3, [PR #2206](https://github.com/modelcontextprotocol/typescript-sdk/pull/2206)). Deprecated upstream ("use StreamableHTTP and a dedicated OAuth server in production"), but it did ship `2.0.0` in the GA cut |
| - | `@modelcontextprotocol/codemod` | CLI codemod for the mechanical migration: `npx @modelcontextprotocol/codemod v1-to-v2 .` |

A tenth package, `@modelcontextprotocol/core-internal`, is **private** - `server` and `client` bundle it at build time, so it never appears in your dependency tree. Never depend on it directly.

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
| Module system | CJS + ESM | **ESM-first; CJS builds restored in 2.0.0-beta.2** ([PR #2405](https://github.com/modelcontextprotocol/typescript-sdk/pull/2405): every package emits `.mjs`/`.d.mts` and `.cjs`/`.d.cts` with a `require` exports condition) |
| Node.js | 16+ | **20+** (Bun and Deno also supported) |
| Schema library | Zod v3 or v4 (since v1.23) | Any [Standard Schema](https://standardschema.dev) library (Zod v4, Valibot, ArkType) - `zod` is no longer a peer dependency ([PR #1824](https://github.com/modelcontextprotocol/typescript-sdk/pull/1824)). For raw JSON Schema, use the `fromJsonSchema` adapter. |

### ESM Migration

ESM remains the primary target; since beta.2, CommonJS consumers can `require()` the packages directly. To switch a project to ESM:

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

### Unknown / Disabled Tool Error Semantics Changed

In v2 alpha.1, unknown or disabled tool calls return JSON-RPC `-32602` (`InvalidParams`) instead of `CallToolResult` with `isError: true`. Resource-not-found is also `-32602`: [SEP-2164](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2164) (final, 2026-05-18) standardized resource-not-found on `-32602` (`InvalidParams`); `-32002` is the **legacy** code earlier protocol versions used, which clients SHOULD still accept for backwards compatibility. This is a breaking change for clients that read `isError` to detect missing tools - they must now handle JSON-RPC error responses.

### V1 Method Signatures Removed

The deprecated `.tool()`, `.prompt()`, `.resource()` method signatures are fully removed in v2 alpha.1 ([PR #1419](https://github.com/modelcontextprotocol/typescript-sdk/pull/1419)) - they error at compile time. Use `registerTool()`, `registerPrompt()`, `registerResource()` exclusively.

### V2 Client OAuth Helpers

- **`discoverOAuthServerInfo(serverUrl)`** ([PR #1527](https://github.com/modelcontextprotocol/typescript-sdk/pull/1527)) - performs RFC 9728 protected-resource-metadata discovery followed by RFC 8414 authorization-server-metadata discovery in a single call, returning a unified `OAuthDiscoveryState` cache.
- **`AuthProvider` interface** ([PR #1710](https://github.com/modelcontextprotocol/typescript-sdk/pull/1710)) - one-line bearer-token providers: `{ token(): Promise<string | undefined>; onUnauthorized?(ctx): Promise<void> }`. Transports call `token()` before each request and `onUnauthorized()` on 401.

## Transport Changes

### SSE Server Transport Removed

v2 removes `SSEServerTransport` from the server package. Clients can still connect to legacy SSE servers.

```typescript
// v1 - SSE transport available
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

// v2 - REMOVED. Use WebStandardStreamableHTTPServerTransport instead
```

### WebSocket Client Transport Removed

`WebSocketClientTransport` was non-spec and is removed in v2 alpha.1 ([PR #1783](https://github.com/modelcontextprotocol/typescript-sdk/pull/1783)). Use stdio or Streamable HTTP.

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

## Alpha -> Beta Changes (2.0.0-beta.1)

v2 entered beta on 2026-06-30. Beta signals a settling (not frozen) API with support for the upcoming `2026-07-28` spec revision. Breaking changes since the alphas, almost all from [PR #2286](https://github.com/modelcontextprotocol/typescript-sdk/pull/2286):

- **`createMcpHandler` is now web-standards-only**, returning `{ fetch, close, notify, bus }`. The duck-typed `.node(req, res)` face is gone - wrap once with `toNodeHandler(handler)` from `@modelcontextprotocol/node` for Express/Node.
- **`serveStdio(factory, options?)`** (`@modelcontextprotocol/server/stdio`) is the new stdio entry point; `ServerOptions.eraSupport` was removed (migrate `new McpServer(info, { eraSupport })` + `connect()` to `serveStdio(() => new McpServer(info))`).
- **Default JSON Schema validator is now `Ajv2020`** (true 2020-12) instead of draft-07 - `$defs`, `prefixItems`, `unevaluatedProperties`, `dependentRequired` are now enforced.
- **`CallToolResult.content` is required at the wire boundary** - a handler result without `content` is rejected with `-32602`. Softened in beta.3 ([PR #2456](https://github.com/modelcontextprotocol/typescript-sdk/pull/2456)): a legacy-era result without `content` is normalized to `content: []` instead of failing validation; 2026-era wire schemas stay strict. `CallToolResult.structuredContent` is widened to `unknown` (a deliberate source-level break for typed consumers).
- **Protocol error codes renumbered**: `HeaderMismatch -32020`, `MissingRequiredClientCapability -32021`, `UnsupportedProtocolVersion -32022`; unknown-URI `resources/read` answers `-32602` with a typed `ResourceNotFoundError` (`data.uri`).
- **TypeScript >= 6.0 consumers must set `"types": ["node"]`** in tsconfig or the `.d.mts` declarations fail under `skipLibCheck: false` ([PR #2394](https://github.com/modelcontextprotocol/typescript-sdk/pull/2394)).

## Beta.1 -> Beta.3 Changes (2026-07-02 / 2026-07-09)

beta.2 and beta.3 shipped for all v2 packages except `server-legacy` (frozen at beta.2, deprecated):

- **CommonJS builds** ([PR #2405](https://github.com/modelcontextprotocol/typescript-sdk/pull/2405), beta.2) - see Runtime Requirements above.
- **Post-dispatch `-32021` (`MissingRequiredClientCapability`) now returns HTTP 400** instead of riding HTTP 200 ([PR #2399](https://github.com/modelcontextprotocol/typescript-sdk/pull/2399), beta.2).
- **Non-JSON POSTs rejected with `415 Unsupported Media Type`** - Content-Type is parsed, not substring-matched; new exported `isJsonContentType(header)` helper. Custom transports composing `classifyInboundRequest`/`PerRequestHTTPServerTransport` must apply it themselves ([PR #2441](https://github.com/modelcontextprotocol/typescript-sdk/pull/2441), beta.3).
- **`inputRequired.elicit()` accepts a Standard Schema** (e.g. a Zod object) for `requestedSchema`; inexpressible shapes (nested objects, `.regex()`, exclusive bounds, literal unions) reject before anything is sent ([PR #2369](https://github.com/modelcontextprotocol/typescript-sdk/pull/2369), beta.3).
- **SDK error classes brand-match across separately bundled SDK copies** (`Symbol.hasInstance` + a registry symbol), plus static `X.isInstance(value)` guards; `connect()` against an auth-gated server now rejects with the original `UnauthorizedError` instead of a wrapped `SdkError` ([PR #2384](https://github.com/modelcontextprotocol/typescript-sdk/pull/2384), beta.3).
- **Streamable HTTP client session hygiene**: no session ID attached to `initialize` POSTs; `mcp-session-id` captured only from a successful initialize response; rotation only via 404 + re-initialize ([PR #2469](https://github.com/modelcontextprotocol/typescript-sdk/pull/2469), beta.3).
- **Runtime-neutral auth helpers in `@modelcontextprotocol/server`**: `requireBearerAuth` for web-standard `fetch(request)` hosts (Cloudflare Workers, Deno, Bun, Hono) and `oauthMetadataResponse` serving the RFC 9728 / RFC 8414 metadata documents; the insecure-issuer escape hatch is now an explicit `dangerouslyAllowInsecureIssuerUrl` option ([PR #2420](https://github.com/modelcontextprotocol/typescript-sdk/pull/2420), [PR #2422](https://github.com/modelcontextprotocol/typescript-sdk/pull/2422), beta.3).
- Fixes: version negotiation no longer drops pre-set transport handlers (PR #2455); CJS `validators/ajv` subpath crash fixed (PR #2431); legacy content-less `CallToolResult` tolerance (PR #2456, above).

## Beta.3 -> 2.0.0 (2026-07-13 / 07-21 / 07-27)

**If you piloted v2 on `2.0.0-beta.3`, upgrade - do not stay pinned.** beta.5 changed the 2026-07-28 wire shape, so a beta.3 build is incompatible with conforming modern peers.

### The wire realignment (beta.5, breaking)

[PR #2513](https://github.com/modelcontextprotocol/typescript-sdk/pull/2513) aligned the SDK with the *final* spec revision (spec PR #3002):

- `serverInfo` **moves out of the `DiscoverResult` body into the result `_meta`**; new exported constant `SERVER_INFO_META_KEY` (`'io.modelcontextprotocol/serverInfo'`).
- The per-request envelope's `clientInfo` **demotes from required to SHOULD** (`RequestMetaEnvelope.clientInfo` is now optional).
- Breaking types: `DiscoverResult` no longer declares `serverInfo`.

Why it matters concretely: before this, "the client hard-rejected a conforming server's `DiscoverResult` (missing body `serverInfo` failed parse, so the probe misclassified the server as legacy and attempted an `initialize` handshake against it - a hard connect failure against a modern-only server)", and "the server rejected conforming clients that omit `clientInfo`".

### Structural changes (beta.4)

- **Schema modules consolidated into `@modelcontextprotocol/core`** ([PR #2477](https://github.com/modelcontextprotocol/typescript-sdk/pull/2477)) - packages resolve them as a runtime dependency instead of bundling private copies, so an app importing more than one package "now evaluates a single shared schema graph with shared object identity". `core` gains a `./internal` subpath (SDK-internal; may change in any release), and the four core packages version together.
- **The client response cache is now string-valued** ([PR #2468](https://github.com/modelcontextprotocol/typescript-sdk/pull/2468)) - **breaking for custom `ResponseCacheStore` implementations**: `CacheEntry.value` is now `string`; persist and return it verbatim, `JSON.parse` to inspect. Entries written by an older SDK "fail decode once (reported, dropped) and are rewritten on the next fetch".
- **Startup cost moved off the hot path**: wire schemas and the Ajv engine are both built lazily on first validation ([PR #2476](https://github.com/modelcontextprotocol/typescript-sdk/pull/2476), [PR #2458](https://github.com/modelcontextprotocol/typescript-sdk/pull/2458)). For Cloudflare Workers, where lazy construction lands in the request path, call the new **`preloadSchemas()`** at module scope - the workerd export condition does it automatically ([PR #2483](https://github.com/modelcontextprotocol/typescript-sdk/pull/2483)).

### Fixes worth knowing (beta.5 / 2.0.0)

- **Auth failures are no longer treated as era evidence** ([PR #2564](https://github.com/modelcontextprotocol/typescript-sdk/pull/2564)) - a 401/403 on the `server/discover` probe now surfaces as a typed `SdkHttpError` (`ClientHttpAuthentication` / `ClientHttpForbidden`) carrying status, reason phrase, and response text, instead of triggering a legacy `initialize` fallback "which put a doomed `initialize` on the wire". If you gate your MCP endpoint behind auth, this is the fix that makes v2 clients report the real error.
- **The default validator honors declared draft-07 / 2019-09 dialects** ([PR #2534](https://github.com/modelcontextprotocol/typescript-sdk/pull/2534)) - this unblocks every `zod-to-json-schema` user, whose default output is stamped `"$schema": "http://json-schema.org/draft-07/schema#"`. Schemas with no `$schema` still validate as 2020-12; unknown dialects produce a typed error listing the supported ones.
- **stdio era probing runs on a disposable sibling process** ([PR #2514](https://github.com/modelcontextprotocol/typescript-sdk/pull/2514)) - some stdio servers exit on any pre-`initialize` request (rmcp-based servers do), which previously killed the server and hard-failed `connect()` under `mode: 'auto'`.
- **`ConnectOptions.prior`** ([PR #2511](https://github.com/modelcontextprotocol/typescript-sdk/pull/2511)) accepts a cached era verdict via the exported `PriorDiscovery` type: `{ kind: 'modern', discover }` adopts a known `DiscoverResult` with zero round trips; `{ kind: 'legacy' }` skips the probe without pinning the client to `mode: 'legacy'`.
- **`Protocol` and `mergeCapabilities` are re-exported** from the `client` and `server` package roots ([PR #2501](https://github.com/modelcontextprotocol/typescript-sdk/pull/2501)), restoring the v1 import for consumers that subclass `Protocol` (the MCP Apps SDK does). Each package bundles its own compiled copy - import from one package consistently within a process.
- **SSE keep-alive frames** ([PR #2541](https://github.com/modelcontextprotocol/typescript-sdk/pull/2541)) - `createMcpHandler`'s `keepAliveMs` now applies to every HTTP SSE stream it serves.
- The 2025-era `tasks/*` wire vocabulary is `@deprecated` and excluded from the typed method maps (`RequestMethod`, `RequestTypeMap`, `ResultTypeMap`, `NotificationTypeMap` have no `tasks/*` entries).

## Migration Checklist

### Phase 1: Prepare (do now, on v1)

- [ ] Use `.describe()` on every Zod schema field
- [ ] Use `z.object()` wrappers (not raw shapes) for tool schemas
- [ ] Set tool annotations on all tools
- [ ] Use `isError: true` for all tool-level errors (not McpError for validation)
- [ ] Bump to SDK v1.28.0 (catches plain JSON Schema errors, security fix)
- [ ] Register all tools/resources before `connect()` ([#893](https://github.com/modelcontextprotocol/typescript-sdk/issues/893))
- [ ] Ensure per-request server+transport pattern (not shared instances)

### Phase 2: Migrate (v2 is stable - you can do this now)

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
- [ ] Decide your era explicitly: leave `versionNegotiation` absent to stay on the 2025 wire (recommended unless you control both ends), or set `'auto'` / `{ pin: '2026-07-28' }`
- [ ] Test against the era you chose - `MCP-Protocol-Version: 2025-11-25` for the legacy wire, `2026-07-28` for the modern one

### Phase 3: Optimize (after migration)

- [ ] Add `outputSchema` to all tools for typed outputs
- [ ] Implement dynamic tool loading for large tool sets
- [ ] Use `structuredContent` for all responses
- [ ] Review DNS rebinding protection settings
- [ ] Remove any Zod v3 compatibility shims

### Timeline

v2 stable shipped **2026-07-27**, alongside the released 2026-07-28 spec revision. The support window is now written down in the SDK's own `ROADMAP.md`:

> The `v1.x` branch (`@modelcontextprotocol/sdk`) continues to receive bug fixes and security updates for at least six months after the v2 release (2026-07-27). It targets the 2025-11-25 spec revision; new spec revisions are implemented on `main` only.

The second sentence is the one that sets the real deadline: **v1 will never speak a revision past 2025-11-25**. Fixes for six-plus months, but no path to 2026-07-28 or anything after it, so "v1 still gets patches" is not a reason to stay if you need the modern wire. The repo also added `VERSIONING.md` and a `DEPENDENCY_POLICY.md` (including a 7-day `minimumReleaseAge` supply-chain cooldown on lockfile entries) alongside it.

In practice the ecosystem is still on v1: the official reference servers (`server-filesystem`, `server-memory`, `server-everything`) were republished 2026-08-31 still pinning `"@modelcontextprotocol/sdk": "^1.30.0"`, which is why the v1 draft-07 defect in `sdk-bugs.md` has such a wide blast radius.

New code should target v2; the `@modelcontextprotocol/codemod` `v1-to-v2` codemod handles the mechanical parts.

Two reasons to move sooner rather than later, both v1-only defects with no backport: `z.union()`/`z.discriminatedUnion()` still produce empty schemas on every released v1 including 1.30.0 ([PR #2017](https://github.com/modelcontextprotocol/typescript-sdk/pull/2017) is still open), and the concurrent-transport-closure stack overflow ([#1699](https://github.com/modelcontextprotocol/typescript-sdk/issues/1699)) was fixed on the v2 line only.
