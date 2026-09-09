---
name: mcp-best-practices
description: Build, harden, and debug production MCP servers with the TypeScript SDK. Use when writing or reviewing an MCP server - transports, tool schemas, errors, OAuth, token bloat, SDK migrations, MCP Apps, Registry. Assumes a server already exists.
metadata:
  version: "1.2.1"
  categories: "development, integrations"
  topics: "mcp, typescript-sdk, tool-design, transports, server-hardening"
  upstream: "@modelcontextprotocol/sdk@1.30.0, @modelcontextprotocol/server@2.0.0, @modelcontextprotocol/ext-apps@2.0.0, modelcontextprotocol-spec@2026-07-28"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/mcp-best-practices
    emoji: "🔌"
    envVars:
      - name: MAX_MCP_OUTPUT_TOKENS
        required: false
        description: Claude Code client-side cap on MCP tool result size, referenced in the result-size budget guidance
---

# MCP Best Practices

Decision reference for building production MCP servers with the TypeScript SDK. Not a tutorial - assumes you already have a working server and need to make it correct, fast, and secure.

## Quick Reference

| Component | Current | Notes |
|-----------|---------|-------|
| Spec (released) | **2026-07-28** ([specification](https://modelcontextprotocol.io/specification/latest)) | Stateless/sessionless overhaul - see "Spec 2026-07-28" below and `references/spec-2026-07-28.md` |
| Spec (still deployed) | **2025-11-25** | What most shipped clients and servers actually speak today; the v2 SDK's default |
| TS SDK (current) | **v2.0.0** (2026-07-27), nine packages in lockstep: `/server`, `/client`, `/core`, `/hono`, `/express`, `/node`, `/fastify`, `/codemod`, `/server-legacy` | Speaks 2025-era by default; 2026-07-28 is opt-in |
| TS SDK (legacy) | **v1.30.0** (`@modelcontextprotocol/sdk`) | Bug + security fixes for >=6 months after v2 GA; source on the [`v1.x` branch](https://github.com/modelcontextprotocol/typescript-sdk/tree/v1.x) |
| JSON Schema | **2020-12** default (2019-09 / draft-07 accepted since v2.0.0) | - |
| Transport | **Streamable HTTP** (remote), **stdio** (local) | SSE + WebSocket removed in v2 |
| Extensions | **MCP Apps** (Stable, SEP-1865), **Auth Extensions** (official), **Tasks** ([ext-tasks](https://github.com/modelcontextprotocol/ext-tasks)) | Domain-specific WGs |
| Registry | **Preview** with v0.1 API freeze since 2025-10-24 ([registry](https://modelcontextprotocol.io/registry/about)) | GA pending |

**v2 imports** (current):
```typescript
import { McpServer } from "@modelcontextprotocol/server";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/server";
import { ProtocolError, ProtocolErrorCode } from "@modelcontextprotocol/core";
```

**v1 imports** (legacy line, still widely deployed):
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
```

### The Two Eras

The most decision-relevant fact after the 2026-07-28 release: **upgrading to SDK v2.0.0 does not move you to the new spec.** A hand-constructed `Client`/`Server`/`McpServer` keeps speaking the 2025-era protocol it was written for.

Every revision from `2024-10-07` through `2025-11-25` opens with `initialize` and shares one wire behavior - the SDK calls that family **legacy**. `2026-07-28` starts the **modern** era: no `initialize`, a `server/discover` advertisement instead, a `_meta` envelope on every request. Selection is explicit:

| `versionNegotiation.mode` | Behavior |
|---|---|
| absent / `'legacy'` | The 2025 `initialize` handshake, byte for byte. No probe. **This is the default.** |
| `'auto'` | Probe with `server/discover`; fall back to `initialize` against a 2025-only server |
| `{ pin: '2026-07-28' }` | That revision or nothing - a pin never falls back |

Build new servers on the 2025-era wire unless you control both ends. The stateless design guidance throughout this skill is what makes the eventual era switch cheap.

Tooling: [SDK docs](https://ts.sdk.modelcontextprotocol.io) ([v2](https://ts.sdk.modelcontextprotocol.io/v2/)); [MCP Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector), which **connects as `legacy` by default** (see "Testing Against Each Era" in `references/spec-2026-07-28.md`); the [conformance suite](https://github.com/modelcontextprotocol/conformance); and the [`mcp-server-dev` plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/mcp-server-dev) for scaffolding.

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
    // Origin/Host checking is OFF unless you turn it on: the SDK defaults
    // enableDnsRebindingProtection to false and leaves both lists unset.
    enableDnsRebindingProtection: true,
    allowedOrigins: ["https://app.example.com"],
    allowedHosts: ["mcp.example.com"],
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

The `McpServer` must be per-request, but its constant inputs must not be. **Hoist to module level**: Zod schemas, annotation objects (`{ readOnlyHint: true, ... }`), tool description strings, payment configs, upstream API clients.

**If you only route POST** (the common stateless layout), answer `GET /mcp` with an explicit **405 Method Not Allowed** - the spec requires it when no SSE stream is offered, and the official TS client reads 405 as the benign no-stream signal, while an empty `200` sends it into a reconnect storm.

> For transports, sessions, HTTP/2 gotchas, and K8s deployment: see `references/transport-patterns.md`

### Framework Integration

The transport is web-standard, so Hono and the Workers runtime need no adapter; v2 also ships `@modelcontextprotocol/hono` (`createMcpHonoApp()`) and `@modelcontextprotocol/express` (wrapping `NodeStreamableHTTPServerTransport` for `IncomingMessage`/`ServerResponse`). On Cloudflare Workers call `preloadSchemas()` at module scope - v2's workerd build does it automatically. Examples: `references/transport-patterns.md`.

## Tool Design

### Registration API

**v1 (legacy line)** - `server.tool(name, description, zodShape, annotations, handler)`. Positional overloads are ambiguous; same fields as v2 below minus `outputSchema`. Removed entirely in v2.

**v2 (current)** - `registerTool()` with config object:
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
    // Both channels carry IDENTICAL bytes. Divergent payloads = the text block
    // silently vanishes on Claude Code/Codex/Copilot. See "Tool Result Delivery" below.
    structuredContent: result,
    content: [{ type: "text", text: JSON.stringify(result) }],
  };
});
```

### Naming

Spec 2025-11-25 (SHOULD, not MUST): 1-128 chars, case-sensitive, `A-Za-z0-9_-.` only. **DO**: `search_docs`, `get_user_profile`, `admin.tools.list`. **DON'T**: `search` (generic names collide across servers), `Search Docs` (spaces disallowed). Service-prefix (`github_*`, `jira_*`) when multiple servers are active - LLMs confuse generic names. Bake the prefix into the tool name itself: the spec is explicit that *"The server `name` (from `serverInfo`) is not guaranteed to be unique across servers and **SHOULD NOT** be relied upon for disambiguation"*, so an aggregator cannot derive a safe prefix for you.

### Schema Rules

`.describe()` on every field - this is what LLMs use for argument generation. Three constructs break silently (`z.union()`, raw JSON Schema, `z.transform()`), as does client-side AJV strict validation - see "Known SDK Bugs" below.

**Pagination** is the primitive most servers hit first: a `tools/list` or `resources/list` with 50+ entries should paginate. The protocol `cursor` is **opaque** - never parse or synthesize it; loop until `nextCursor` is absent. It is distinct from in-tool `offset`/`limit` args.

> Zod-to-JSON-Schema conversion rules, outputSchema/structuredContent patterns, non-text content types, the other tool-definition fields (`icons`, `listChanged`, `execution.taskSupport`), and the remaining primitives (prompts, resources, resource templates, completions, cancellation): see `references/tool-schema-guide.md`

### Annotations

All are optional hints (untrusted from untrusted servers per spec):

| Annotation | Default | Meaning |
|------------|---------|---------|
| `readOnlyHint` | `false` | Tool doesn't modify its environment |
| `destructiveHint` | `true` | May perform destructive updates (only when readOnly=false) |
| `idempotentHint` | `false` | Repeated calls with same args have no additional effect |
| `openWorldHint` | `true` | Interacts with external entities (APIs, web) |

Set them accurately - clients use them for consent prompts and auto-approval decisions.

**The "Lethal Trifecta"**: private-data access + exposure to untrusted content + external communication in one agent creates data-theft conditions (demonstrated with a malicious calendar event, an MCP calendar server, and a code-execution tool). Design tool sets so no single agent holds all three.

### Stateful Tools

With no protocol-level session on 2026-07-28, cross-call state uses **server-minted handles passed as ordinary tool arguments**: a creation tool returns `{ basket_id: "bsk_a1b2c3" }`, later tools take `basket_id` as an argument, and the model carries it forward. A handle is a name, not a capability - validate the caller against it on *every* call, keep it opaque with real entropy, and state its retention policy in the *creation tool's description*. Expired or unknown handles return a tool execution error so the model can recover by creating new state. Full rules: `references/spec-2026-07-28.md`.

## Tool Result Delivery: `content` vs `structuredContent`

**The footgun:** when a tool returns BOTH a text `content` block and `structuredContent`, several major clients (Claude Code, Codex CLI, VS Code Copilot, Goose) silently drop the text block and forward only `structuredContent` to the model. If the two payloads differ, the human-readable one vanishes. This is **client behavior the spec does not constrain** - not an SDK transform. Don't return both channels expecting both to reach the model.

### Empirically tested - Claude Code 2.1.165 (MCP 2025-11-25)

Measured with `claude -p --output-format=stream-json`, reading the exact `tool_result` the model received:

| Tool returns | What the model receives |
|--------------|-------------------------|
| One text block, no `structuredContent` | text verbatim |
| `content: []` + `structuredContent` | `JSON.stringify(structuredContent)` as a string in the content slot - works |
| text block + `structuredContent` | **text block silently dropped**; `structuredContent` wins |
| text + `structuredContent` + `outputSchema` | same - **`outputSchema` makes zero difference** |
| two text blocks, no `structuredContent` | both preserved verbatim |

`structuredContent` is **not a separate typed channel to the model** on Claude Code - it is stringified into the standard `tool_result` content slot, so it costs the **same tokens** as the equivalent JSON-as-text. It does not buy cheaper or out-of-band structured data.

Intentional, per Anthropic maintainer ([anthropics/claude-code#9962](https://github.com/anthropics/claude-code/issues/9962)): structuredContent support landed in Claude Code v2.0.21 and "we made `structuredContent` the default when both formats are present... optimizing for agent performance." Reproduced across unrelated servers (Laravel, Roblox Studio, YouTube) - host-side precedence, not a server bug.

### What the spec actually says (2025-11-25)

**There is no precedence rule** - the spec never says which field a client should prefer when both are present ([Discussion #1563](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/1563)), and that gap is the documented root cause of client divergence. The only relevant normative line is a backwards-compat SHOULD: *"a tool that returns structured content SHOULD also return the serialized JSON in a TextContent block."* The official TypeScript SDK passes both fields through **verbatim**; any stringify-into-content you observe is the host harness, not the SDK.

### Cross-client behavior (the matrix above is Claude Code only)

| Client | When both `content` + `structuredContent` present |
|--------|---------------------------------------------------|
| Claude Code CLI, OpenAI Codex CLI, VS Code Copilot, Goose | **shadow** - only `structuredContent` reaches the model (text dropped) |
| Cursor, Claude.ai web, ChatGPT MCP connector | prefer `content` / surface both to the model |
| Google ADK (framework) | forwards both by default; content-only is opt-in |

(Non-Claude-Code rows come from issue trackers and maintainer statements, not the stream-json harness - treat exact delivery as client-version-dependent.)

### The rule for server authors

- **DON'T** return divergent `content` and `structuredContent` (e.g. a rendered ASCII table as text + different JSON as structured). On shadowing clients the text silently disappears and only the JSON reaches the model.
- **DO**, if you emit `structuredContent`, mirror the **same bytes** into a text block: `content: [{ type: "text", text: JSON.stringify(payload) }]`. This is the spec's backwards-compat SHOULD. Shadowing clients use the structured copy; others fall back to the identical text - either way the model gets the data. Mirroring does not double tokens on shadowing clients (they drop the text).
- **PREFER one channel per tool / per mode.** For a human-readable rendering (table, summary) to reach the model, return it as **text only, no `structuredContent`** - or expose a `format: "table" | "json"` arg (`table` -> text-only; `json` -> JSON mirrored into both channels). Both are empirically valid on Claude Code and keep one channel per call.
- `outputSchema` gates client-side validation only; it does **not** make the text block survive on shadowing clients.

`content` blocks are not text-only - `image`, `audio`, `resource_link`, and embedded `resource` blocks all exist, with annotations (`audience`, `priority`, `lastModified`); for those and the image preview + URL pattern see `references/tool-schema-guide.md`.

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

**Known SDK behavior**: converting an `McpError` thrown from a tool handler into a `CallToolResult` drops the `error.data` field, so structured data embedded there may never reach the client. The x402/MPP ecosystem standardized on `isError: true` results with `structuredContent` for this reason.

> For full error taxonomy, code examples, payment error patterns, and why `-32042` is not available as a "Payment Required" code: see `references/error-handling.md`

## Resources and Instructions

Set `instructions` in the server constructor - a system-level hint to the LLM about how to use your server:

```typescript
const server = new McpServer({
  name: "docs-api",
  version: "1.0.0",
  instructions: "Knowledge base API. Use search_docs for full-text search, get_doc for retrieval by ID. All tools are read-only.",
});
```

Ship guides and structured data as resources under a `docs://` URI scheme (`server.resource(...)`) - see "Other Server Primitives" in `references/tool-schema-guide.md`.

## Performance

### Token Bloat Mitigation

Tool definitions consume context window before any conversation starts. GitHub MCP: 20,444 tokens for 80 tools (SEP-1576).

**Strategies**:
1. **5-15 tools per server** - community sweet spot. Split beyond that.
2. **Outcome-oriented tools** - bundle multi-step operations into single tools (e.g., `track_order(email)` not `get_user` + `list_orders` + `get_status`).
3. **Response granularity** - return curated results, not raw API dumps. 800-token user object vs 20-token summary.
4. **`outputSchema` + `structuredContent`** - typed output for programmatic/PTC clients. Caveat: on shadowing clients `structuredContent` is stringified into the model's context at the **same token cost as text** - not a free out-of-band channel (see "Tool Result Delivery").
5. **Dynamic tool loading** - register only relevant tool subsets per request context (e.g. a `?tools=search,fetch` query param). Pair with `listChanged` if the set changes mid-session. **Vary the set per connection, not mid-conversation**: tool definitions sit in the prompt prefix, and *"Adding or removing tool definitions mid-conversation invalidates that cache, and the resulting miss can cost more tokens than the definitions you removed."* A client must also treat a cached list as stale the moment `list_changed` arrives, even before the `ttlMs` you advertised.
6. **Progressive tool discovery / code mode** - large-catalog clients increasingly use a `search_tools` meta-tool and programmatic tool calling, where `structuredContent` is consumed outside the model context ([client best practices](https://modelcontextprotocol.io/docs/develop/clients/client-best-practices)). Curated, well-described tools make these flows work.

### Result-Size Budgets (per-client caps)

Clients silently truncate large tool results. Budget for the strictest client you target:

| Client | Default cap | Configurable |
|--------|------------|--------------|
| Claude Code | 25,000 tokens (warning at 10k) | `MAX_MCP_OUTPUT_TOKENS` env; per-tool `_meta["anthropic/maxResultSizeChars"]` up to 500,000 chars, which **replaces** the token cap for text rather than being bounded by it |
| OpenAI Codex CLI | **10,000 tokens** on every current model (~40KB); `bytes`-mode 10,000 survives only on legacy `gpt-5.2` and as the unknown-model fallback | `tool_output_token_limit` config |
| Gemini CLI | 40,000 chars (head 20% / tail 80% trim; full output saved to a file) | settings; 0 or negative disables |

Enforce your own cap server-side - see "Result-Size Budgets and Truncation" in `references/tool-schema-guide.md`. Two rules worth stating here: **never truncate `isError` results** (payment/auth challenges must survive intact), and treat client budgets as **per-connection properties** - accept them as URL query params (`?max_chars=`, alongside `?tools=`) rather than growing every tool schema with override args.

### Long-Running Tools

**A client timeout is a wall clock, not an idle timer.** Claude Code's per-server tool-call timeout is documented as a *"Hard wall-clock limit per call; progress notifications do not extend it"* - so the common instinct (emit `notifications/progress` to keep a slow call alive) does not work there. Progress is for the human watching, not for buying time.

Design past the cap instead: return quickly with a server-minted handle and let the caller poll (see "Stateful Tools"), or adopt the `io.modelcontextprotocol/tasks` extension, which is built for exactly this and returns a `CreateTaskResult` the client polls via `tasks/get`. Tasks is per-request opt-in - a server that cannot service a call synchronously for a client that did **not** declare the tasks capability **MUST** return `-32021` (Missing Required Client Capability) naming the extension, not silently block.

### No-Parameter Tools

For tools with no inputs, use an explicit empty schema - not `undefined` or omission:
```typescript
inputSchema: { type: "object" as const, additionalProperties: false }
```

## Security

### Top Threats (real-world incidents, 2025-2026)

| Attack | Example | Mitigation |
|--------|---------|------------|
| **Tool poisoning** | Hidden instructions in descriptions (WhatsApp MCP, Apr 2025) | Review tool descriptions; clients should display them |
| **Supply chain** | Malicious npm packages (Smithery breach, Oct 2025) | Pin versions, audit dependencies |
| **Stdio config injection** | User-controlled input reaches `StdioServerParameters` unsanitized (OX Security, 2026-04-15) | Sanitize stdio config in client code; prefer first-party servers. Treated as "by design" - not patched in the SDK |
| **Cross-server shadowing** | Malicious server overrides legitimate tool names | Service-prefix tool names; validate tool sources |
| **Token theft** | Over-privileged PATs with broad scopes | Minimal scopes; OAuth 2.1 Resource Indicators (RFC 8707) |
| **Token passthrough** | Server accepts/forwards tokens not issued for it | Validate audience claim; never transit client tokens to upstream APIs |
| **Confused deputy** | Proxy server consent cookies exploited via DCR | Per-client consent before forwarding to third-party auth |
| **Session hijacking** | Stolen/guessed session IDs for impersonation | Cryptographically random IDs, bind to user identity, never use for auth |
| **Cross-client response leak** | Shared `McpServer`/transport reused across clients ([CVE-2026-25536](https://nvd.nist.gov/vuln/detail/cve-2026-25536), affects v1.10.0-1.25.3) | **Require SDK >= v1.26.0**; per-request server+transport |
| **UriTemplate ReDoS** | Malicious URI patterns ([CVE-2026-0621](https://github.com/modelcontextprotocol/typescript-sdk/pull/1365)) | Upgrade to v1.25.2+ / v2.0.0-alpha.1+ |

Generic hygiene still applies: validate inputs at tool boundaries, enforce per-user access control, rate limit, never interpolate tool input into shell commands, block private IPs on outbound fetches, bind local servers to `127.0.0.1`.

### Server-Side Requirements (spec normative)

- **Validate the `Origin` header** - but only reject when it is **present and invalid**: *"If the `Origin` header is present and invalid, servers MUST respond"* with 403. Shipping clients exist that send no `Origin` at all; a blanket 403-on-missing locks them out.
- **Turn the checks on.** `WebStandardStreamableHTTPServerTransport` defaults `enableDnsRebindingProtection` to `false` and leaves `allowedOrigins`/`allowedHosts` unset, so the stock stateless constructor validates nothing. The `@modelcontextprotocol/express` and `/hono` factories enable Host validation for localhost by default; the raw transport does not.
- **`MCP-Protocol-Version` is not optional on a modern wire.** The header survived the sessionless overhaul: *"Every POST request to the MCP endpoint **MUST** include an `MCP-Protocol-Version` header"*, and its value **MUST** match `io.modelcontextprotocol/protocolVersion` in the body's `_meta` or the server **MUST** answer `400 Bad Request` with a `HeaderMismatch` error. The version rides `_meta` *and* the header, redundantly and on purpose - intermediaries route on the header while the server executes on the body, so both must agree.
- **Be lenient about *which* version, not about whether it is declared.** On 2025-era wires accept a range of declared versions rather than enforcing one - clients advertising `2024-11-05` are still in the wild, and a server supporting pre-`2025-06-18` clients **MAY** treat a header-less request as `2025-03-26`. A server that does not support those clients **MUST** reject a header-less request.

### Auth (OAuth 2.1)

MCP normatively requires **OAuth 2.1** ([draft-ietf-oauth-v2-1-13](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-13)), not 2.0 - PKCE mandatory, implicit flow removed. Servers are Resource Servers; clients MUST send Resource Indicators (RFC 8707) binding tokens to your server.

- **Validate audience** - reject tokens not issued for your server (passthrough is forbidden). **PKCE `S256`**, **short-lived tokens**, **minimal scopes** (elevate via `WWW-Authenticate` challenges).
- Use a tested validation library (Keycloak, Auth0, ...) - don't roll your own; never log Authorization headers/tokens/secrets.
- **RFC 9207 `iss` interop footgun**: advertising `authorization_response_iss_parameter_supported: true` makes strict clients MUST-validate a callback `iss` that some of them drop. Advertise the flag as `false` while still sending `iss` - see `references/security-auth.md`.

> For full security attack/mitigation patterns and auth implementation details: see `references/security-auth.md`

## Known SDK Bugs

Must-know as of `sdk@1.30.0` / `server@2.0.0`:

- **`z.union()`/`z.discriminatedUnion()` silently produce empty schemas on every released v1**, v1.30.0 included ([#1643](https://github.com/modelcontextprotocol/typescript-sdk/issues/1643), backport still open) - use flat `z.object()` + `z.enum()`.
- **Require SDK >= v1.26.0** - shared instances leaked cross-client data below that ([CVE-2026-25536](https://nvd.nist.gov/vuln/detail/cve-2026-25536)).
- **Register everything before `connect()`** - later registration throws; open on both `main` and `v1.x` ([#893](https://github.com/modelcontextprotocol/typescript-sdk/issues/893)).
- **Client AJV strict rejects unstripped `structuredContent` extras** - `.parse()` upstream data first, or `.passthrough()` for intentional extras.
- **v1.30.0 stamps every tool schema `"$schema": "http://json-schema.org/draft-07/schema#"`**, and a strict 2020-12 client rejects the whole tool: *"JSON Schema declares an unsupported dialect ... The default validator supports JSON Schema 2020-12 only."* One bad schema can take the server's other tools down with it in clients that drop the whole `tools/list`. v2 emits 2020-12. Open ([#2721](https://github.com/modelcontextprotocol/typescript-sdk/issues/2721), [#2677](https://github.com/modelcontextprotocol/typescript-sdk/issues/2677)); `@modelcontextprotocol/inspector` >= 2.4.0 flags it for you.
- **Don't reuse one `McpServer` across `createMcpHandler` requests on v2.** Each request wraps `onclose`, the chain grows unbounded, and it dies with `RangeError: Maximum call stack size exceeded` at roughly 19-25k accumulated sessions - affects released `server@2.0.0` ([#2607](https://github.com/modelcontextprotocol/typescript-sdk/issues/2607)). The per-request pattern above is the fix.

> Full table (statuses, zod 3->4 dropping `additionalProperties`, `refine`/`superRefine` never running, transport-closure stack overflow, HTTP/2, raw JSON Schema, `z.transform()`, ReDoS): see `references/sdk-bugs.md`

## V2 Migration

> For comprehensive migration guide with all breaking changes and before/after code: see `references/v2-migration.md`

**Key breaking changes**:
1. Package split: `@modelcontextprotocol/sdk` -> `@modelcontextprotocol/server` + `/client` + `/core`
2. ESM-first (CJS builds restored in beta.2), Node.js 20+ (Bun/Deno supported)
3. Zod v4 required (or any Standard Schema library)
4. `McpError` -> `ProtocolError` (from `@modelcontextprotocol/core`)
5. `extra` parameter -> structured `ctx` with `ctx.mcpReq`
6. `server.tool()` -> `registerTool()` (config object, not positional args)
7. SSE server transport removed (clients can still connect to legacy SSE servers)
8. `@modelcontextprotocol/hono` and `@modelcontextprotocol/express` middleware packages
9. DNS rebinding protection enabled by default for localhost servers

v1.x gets 6 more months of support after v2 stable ships. No rush, but write new code with v2 patterns in mind.

## Spec 2026-07-28 (released)

Published 2026-07-28 ([release announcement](https://blog.modelcontextprotocol.io/posts/2026-07-28/), [changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)) - now the latest revision. Remember it is **opt-in on the SDK** (see "The Two Eras"): 2025-11-25 remains what most deployed software speaks.

Four shifts that change a decision you make today:

- **MCP is stateless and sessionless.** The `initialize` handshake and `Mcp-Session-Id` are gone ([SEP-2575](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2575), [SEP-2567](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2567)); every request carries its protocol version, client identity, and capabilities in `_meta`, and cross-call state uses handles (see "Stateful Tools"). Do not build new servers on session affinity.
- **`server/discover` is a server MUST** - it advertises versions/capabilities/identity; clients MAY skip it and handle `UnsupportedProtocolVersionError` inline.
- **Roots, Sampling, Logging, and the HTTP+SSE transport are Deprecated** under a formal feature lifecycle (12-month minimum window, SEP-2577/SEP-2596). They still work; design new servers without them.
- **Allocate application-defined error codes outside `-32768..-32000`** - `-32020..-32099` is reserved for the spec and `-32000..-32019` is legacy that new implementations SHOULD NOT use at all ([PR #2907](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2907)).

The `content` vs `structuredContent` dual-delivery footgun is **unchanged** - no precedence rule landed, so the guidance above still holds.

> Everything else - MRTR, `subscriptions/listen`, `_meta` identity keys, `requestState`, `Mcp-Method`/`Mcp-Name`, cacheable results, per-request log level, auth changes, the removals (SSE resumability, `ping`, `execution.taskSupport`), era testing, working groups: see `references/spec-2026-07-28.md`

## Extensions

Optional, strictly additive capabilities named `{vendor-prefix}/{extension-name}` (official: `io.modelcontextprotocol/*`; third-party: reversed domain). Negotiated in `initialize` capabilities on 2025-era wires; on 2026-07-28 clients advertise support **per request** in `_meta["io.modelcontextprotocol/clientCapabilities"]`. Official ones: **MCP Apps** (`/ui`, interactive HTML UIs, Stable, widely supported; `ext-apps` **2.0.0** since 2026-09-08 - breaking on the TypeScript side only, the wire protocol is unchanged), **OAuth Client Credentials** (Draft), **Enterprise-Managed Authorization** (Stable 2026-06-18), **Tasks** (official since 2026-08-19) - [client matrix](https://modelcontextprotocol.io/extensions/client-matrix).

Server capabilities beyond tools, all 2025-era APIs (the SDK default):

| Capability | Purpose | v2 API |
|-----------|---------|--------|
| **Elicitation** | Request structured user input mid-tool | `ctx.mcpReq.elicitInput()` |
| **Sampling** | Request LLM completion from client | `ctx.mcpReq.requestSampling()` |
| **Tasks** | Long-running ops with lifecycle management | Official extension (SEP-2663) |
| **Progress** | Incremental progress on requests | `ctx.mcpReq.sendProgress()` |

On 2026-07-28 servers cannot send requests to clients at all: elicitation and sampling go through MRTR (return an `InputRequiredResult`, read `inputResponses` on the retry). Tasks moved out of core into the polled `io.modelcontextprotocol/tasks` extension ([ext-tasks](https://github.com/modelcontextprotocol/ext-tasks)).

> For MCP Apps architecture, ext-apps SDK, and build patterns: see `references/mcp-apps.md`
> For the extensions system, auth extensions, elicitation/sampling/tasks detail, and the MCP Registry: see `references/extensions-registry.md`
