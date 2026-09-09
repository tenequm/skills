# Tool Schema Guide

Complete Zod-to-JSON-Schema conversion rules, known breakage, outputSchema, and structuredContent patterns.

## Table of Contents
- [Zod Schema Conversion](#zod-schema-conversion)
- [What Works](#what-works)
- [What Breaks](#what-breaks)
- [outputSchema and structuredContent](#outputschema-and-structuredcontent)
- [Non-Text Content Types](#non-text-content-types)
- [Other Tool-Definition Fields](#other-tool-definition-fields)
- [Tool Design Patterns](#tool-design-patterns)
- [Other Server Primitives](#other-server-primitives)

## Zod Schema Conversion

### v1 Path (current stable)

The SDK's `normalizeObjectSchema()` gates Zod schemas through `toJsonSchemaCompat()`. Only `z.object()` shapes pass through correctly.

**Flow**: `z.object({...})` -> `zodToJsonSchema()` -> JSON Schema object with `type: "object"` and `properties`.

Key constraint: The MCP protocol requires `Tool.inputSchema` to have `type: "object"` at the top level. Any Zod type that doesn't produce this is silently dropped or produces an empty schema.

### v2 Path (current, 2.0.0)

v2 uses Standard Schema interfaces (`StandardSchemaWithJSON`). The conversion delegates to the schema library's native `toJSONSchema()`. Zod v4's native `z.toJSONSchema()` produces correct JSON Schema 2020-12 output.

The `type: "object"` top-level requirement still applies, but v2's converter handles the union case rather than silently emptying it: Zod's discriminated unions "emit `{oneOf: [...]}` without a top-level `type`, so for `io: 'input'` this function defaults `type` to `\"object\"` when absent and throws on an explicit non-object `type`". A `z.string()` at the top level is a hard error, not a silent empty schema.

**Zod version guardrails in v2** - both surface at registration, not at call time:

- A Zod 3 schema is a hard error: *"Schema appears to be from zod 3, which the SDK cannot convert to JSON Schema. Upgrade to zod >=4.2.0, or wrap your JSON Schema with fromJsonSchema()."*
- Below zod 4.2.0 you get a warning and a slower path: *"[mcp-sdk] Your zod version does not implement `~standard.jsonSchema` (added in zod 4.2.0). Falling back to z.toJSONSchema()."*

**Raw JSON Schema in v2**: use the exported `fromJsonSchema()` wrapper - `fromJsonSchema<T>(schema, validator?): StandardSchemaWithJSON<T, T>`. This is v2's answer to the v1 registration throw (#1596), and it is how you use TypeBox or a hand-written schema.

Since 2.0.0 the default validator also honors **declared draft-07 and 2019-09 dialects**, so `zod-to-json-schema` output (stamped draft-07 by default) validates instead of being rejected. Schemas with no `$schema` are still treated as 2020-12.

## What Works

### Primitives and Simple Types

```typescript
z.string()                          // { "type": "string" }
z.number()                          // { "type": "number" }
z.boolean()                         // { "type": "boolean" }
z.literal("active")                 // { "const": "active" }
z.enum(["asc", "desc"])             // { "enum": ["asc", "desc"] }
z.string().optional()               // adds to JSON Schema without "required"
z.string().default("hello")         // { "type": "string", "default": "hello" }
z.string().describe("Search query") // { "type": "string", "description": "Search query" }
```

### Objects and Arrays

```typescript
// Top-level object - the only safe top-level type
z.object({
  query: z.string().describe("Search query"),
  limit: z.number().optional().describe("Max results"),
})

// Nested objects
z.object({
  user: z.object({
    name: z.string(),
    age: z.number(),
  }),
})

// Arrays
z.object({
  ids: z.array(z.string()).describe("List of IDs"),
})

// Enum discriminator (safe alternative to discriminatedUnion)
z.object({
  type: z.enum(["user", "org"]).describe("Entity type"),
  name: z.string().describe("Entity name"),
})
```

### Descriptions (.describe())

**Always use `.describe()` on every field.** This is the primary mechanism LLMs use for argument generation. The SDK converts `.describe()` to JSON Schema `description` fields.

```typescript
// DO: Every field described
z.object({
  query: z.string().describe("Search query - supports boolean operators (AND, OR, NOT)"),
  since: z.string().optional().describe("ISO date string, e.g. 2026-01-01"),
  max_results: z.number().optional().describe("1-100, default 20"),
})

// DON'T: Missing descriptions
z.object({
  query: z.string(),
  since: z.string().optional(),
  max_results: z.number().optional(),
})
```

## What Breaks

### z.union() and z.discriminatedUnion() - Silently Dropped ([#1643](https://github.com/modelcontextprotocol/typescript-sdk/issues/1643))

**Severity**: High. The schema silently becomes `{ type: "object", properties: {} }` - the tool accepts any input.

**Fix status**: Resolved in the v2 line ([PR #1796](https://github.com/modelcontextprotocol/typescript-sdk/pull/1796), merged 2026-03-30). The v1.x backport ([PR #2017](https://github.com/modelcontextprotocol/typescript-sdk/pull/2017)) is **still open**, so the bug is present on every released v1 - **including v1.30.0**, which still routes tool schemas through `normalizeObjectSchema()`. The flat-object workaround below remains required on v1; migrating to v2 is the real fix.

```typescript
// BROKEN: Produces empty schema in v1
z.discriminatedUnion("type", [
  z.object({ type: z.literal("search"), query: z.string() }),
  z.object({ type: z.literal("fetch"), id: z.string() }),
])

// FIX: Flatten to single object with enum discriminator
z.object({
  type: z.enum(["search", "fetch"]).describe("Operation type"),
  query: z.string().optional().describe("Required for type=search"),
  id: z.string().optional().describe("Required for type=fetch"),
})
```

### z.transform() - Stripped During Conversion ([#702](https://github.com/modelcontextprotocol/typescript-sdk/issues/702))

JSON Schema cannot represent runtime transformations. The transform is silently removed.

```typescript
// BROKEN: Transform lost - union resolves incorrectly
z.union([z.array(z.string()), z.string()])
  .transform((val) => Array.isArray(val) ? val : [val])

// FIX: Accept the final type directly
z.array(z.string()).describe("List of values")
```

### Plain JSON Schema Objects - Silent Drop Before v1.28 ([#1596](https://github.com/modelcontextprotocol/typescript-sdk/issues/1596))

Before v1.28.0, passing a raw JSON Schema object (not a Zod schema) was silently accepted but produced `{ type: "object", properties: {} }`. Fixed in v1.28 - now throws at registration time.

```typescript
// BROKEN in v1.27 (silently empty), ERROR in v1.28+ (throws)
server.tool("my-tool", "desc", {
  type: "object",
  properties: { query: { type: "string" } },
}, handler);

// FIX (v1): Use Zod
server.tool("my-tool", "desc", {
  query: z.string().describe("Search query"),
}, handler);
```

**On v2**, raw JSON Schema is supported again via the `fromJsonSchema()` wrapper - see "v2 Path" above.

A related v1 trap that does *not* throw: passing raw JSON Schema `properties` to `McpServer.tool()` on an older v1 makes **every argument arrive as `undefined`** at the handler rather than erroring - the SDK tries to validate incoming args against the raw JSON objects, fails, and hands you nothing. For pass-through proxies that must forward schemas verbatim, use the lower-level `Server` class with raw request handlers instead of `McpServer`.

### A Raw Shape Skips refine/superRefine/transform ([#2705](https://github.com/modelcontextprotocol/typescript-sdk/issues/2705))

**Severity: High, and fail-open.** Passing a raw shape where a `z.object()` is expected validates against the shape only:

> `registerTool(name, { inputSchema: <zod object> })` validates against the **raw shape only**; `refine` / `superRefine` / `transform` constraints never run. A payload rejected by `schema.safeParse` passes the server gate - a fail-open validation gap for tools whose security-critical constraints are expressed via refine/superRefine.

Cross-field rules (`.refine(d => d.start < d.end)`), conditional requirements, and custom `superRefine` issues are exactly where authorization and safety logic tends to live, so this is not a cosmetic gap.

```typescript
// RISKY: the refine never runs at the server boundary
const schema = z.object({ start: z.string(), end: z.string() })
  .refine((d) => d.start < d.end, "start must precede end");

// FIX: re-validate inside the handler for anything security-critical
async ({ start, end }) => {
  const parsed = schema.safeParse({ start, end });
  if (!parsed.success) {
    return { isError: true, content: [{ type: "text", text: parsed.error.issues[0].message }] };
  }
  // ...
}
```

### zod 3 -> 4 Silently Drops `additionalProperties: false` ([#2636](https://github.com/modelcontextprotocol/typescript-sdk/issues/2636))

Upgrading Zod under an unchanged SDK changes what your server publishes:

> We upgraded zod from v3 to v4. After the upgrade, all input schemas are missing `additionalProperties: false` in the `tools/list` response.

Nothing errors; your strict input schemas quietly become open ones, and the LLM can start passing unmodeled arguments. **Assert on the published `tools/list` JSON, not on the Zod source** - a Zod-level test cannot see this. Open as of `sdk@1.30.0`; reproduced against zod 3.25.76 (emits it) versus zod 4.5.4 (does not).

### z.passthrough() - Allows Arbitrary Properties

`z.passthrough()` on object schemas produces JSON Schema without `additionalProperties: false`, allowing the LLM to send any extra fields. This can cause unexpected behavior.

```typescript
// RISKY: Accepts any extra fields
z.object({ query: z.string() }).passthrough()

// SAFE: Strict schema
z.object({ query: z.string() }).strict()
// or just don't add passthrough (default is strip)
z.object({ query: z.string() })
```

### Zod v4 Compatibility ([#925](https://github.com/modelcontextprotocol/typescript-sdk/issues/925) - resolved)

Earlier v1 releases (≤ v1.22.x) required Zod v3 internally and broke with Zod v4 (`w._parse is not a function`). Backwards-compatible Zod v4 support shipped in **v1.23.0-beta.0** and is now in stable v1; issue #925 closed 2025-11-21.

**Rule today**: SDK v1.23+ accepts Zod v3 or v4. SDK v2.0.0 requires a [Standard Schema](https://standardschema.dev) library (Zod >=4.2.0 recommended, Valibot, ArkType) and ships the `fromJsonSchema` adapter for raw JSON Schema (e.g. TypeBox). Zod 3 is a hard error on v2.

### Duplicate SDK Installs from a Zod Peer Split

A zod v3/v4 split across sibling packages installs **two copies of the SDK**, producing two structurally identical but nominally incompatible `Client`/`Server` types:

> `@modelcontextprotocol/sdk` gets installed twice because [one dep] peers on zod@3 while [another] peers on zod@4. Two copies of `Client` with identical structure but different private field types.

The symptom is a type error that reads like nonsense ("`Client` is not assignable to `Client`"). Check for duplicate resolutions (`npm ls @modelcontextprotocol/sdk`) **before** debugging the types. v2 mitigates the related runtime hazard - SDK error classes now brand-match across separately bundled copies via `Symbol.hasInstance`, with static `X.isInstance(value)` guards - but duplicate *type* identities are still a resolution problem you fix in the lockfile.

## outputSchema and structuredContent

Added in spec 2025-06-18. Enables typed, machine-readable tool outputs.

### How They Work Together

1. **Tool definition** includes `outputSchema` (JSON Schema or Zod schema)
2. **Tool result** returns `structuredContent` (matching the schema) AND `content` (text fallback)
3. **Client** validates `structuredContent` against `outputSchema`

### Pattern

```typescript
server.registerTool("get_weather", {
  title: "Weather",
  description: "Get current weather for a city",
  inputSchema: z.object({
    city: z.string().describe("City name"),
  }),
  outputSchema: z.object({
    temperature: z.number().describe("Temperature in Celsius"),
    conditions: z.string().describe("Weather description"),
    humidity: z.number().describe("Humidity percentage"),
  }),
}, async ({ city }) => {
  const weather = await fetchWeather(city);
  return {
    // structuredContent and content MUST carry identical bytes. Several clients
    // (Claude Code, Codex CLI, VS Code Copilot, Goose) drop the text block when
    // structuredContent is present, so a divergent text payload silently vanishes.
    structuredContent: weather,
    content: [{ type: "text", text: JSON.stringify(weather) }],
  };
});
```

### Rules (spec normative)

- If `outputSchema` is provided, server MUST return `structuredContent` conforming to it
- Client SHOULD validate `structuredContent` against the schema
- Server SHOULD also include serialized JSON in `content` for backward compatibility
- "Soft contracts" - tools SHOULD produce schema-compliant outputs but the spec acknowledges AI-generated outputs may vary
- **No precedence rule.** The spec never defines which field a client prefers when both `content` and `structuredContent` are present - left client-defined, which is why clients diverge; a clarification is in flight via SEP-1624 -> SEP-2200 (see SKILL.md "Tool Result Delivery: content vs structuredContent" for the empirical Claude Code 2.1.165 matrix, the cross-client table, and the maintainer confirmation). VS Code's maintainers frame `structuredContent` as PTC-only and not model-facing ([microsoft/vscode#290063](https://github.com/microsoft/vscode/issues/290063)); other clients disagree, so a portable server cannot rely on it either way.

### Token Reality (not a free channel)

- Clients know output shape ahead of time - better context window management.
- **But `structuredContent` is NOT a separate, cheaper channel to the model.** On shadowing clients (Claude Code, Codex CLI, VS Code Copilot, Goose) it is stringified into the model's `tool_result` content slot at the same token cost as the equivalent JSON-as-text, and the `content` text block is dropped. "Programmatic processing without LLM parsing" only holds for clients/flows (PTC, code-mode) that consume `structuredContent` outside the model context - not the default model-facing path.
- Client-side field projection (showing only relevant fields to the LLM) is a client capability, not guaranteed by emitting `outputSchema`. Curate response size on the server; don't assume the client trims it.

### AJV Strict-Mode Rejects Unstripped Extras (high-impact gotcha)

**Symptom**: Tool returns `structuredContent` built from upstream API data; the server logs nothing wrong; the SDK client throws "data must NOT have additional properties" or "has an output schema but did not return structured content."

**Root cause**: Zod v4 `z.object()` produces JSON Schema with `additionalProperties: false`. The SDK's client (and some inspector tools) validate `structuredContent` against `outputSchema` using AJV in strict mode and reject any extra fields. Server-side, calling `outputSchema.parse(data)` strips extras silently and returns a clean object - but if you assign the original raw upstream data to `structuredContent` without parsing it through the schema, the server happily sends the unstripped object across the wire and the client rejects it.

```typescript
// BROKEN: server.parse() result is computed but discarded
const outputSchema = z.object({ id: z.string(), name: z.string() });
const upstream = await fetchUser();  // returns { id, name, email, role, createdAt }
outputSchema.parse(upstream);         // strips extras, but result is thrown away
return {
  structuredContent: upstream,        // contains email/role/createdAt - client AJV rejects
  content: [{ type: "text", text: JSON.stringify(upstream) }],
};

// FIX 1: Use the parsed value
const cleaned = outputSchema.parse(upstream);
return {
  structuredContent: cleaned,
  content: [{ type: "text", text: JSON.stringify(cleaned) }],
};

// FIX 2: Mark the schema as passthrough if extras are intentional
const outputSchema = z.object({ id: z.string(), name: z.string() }).passthrough();
```

**Operational note**: Clients cache `outputSchema` from the `tools/list` response. If you change a tool's schema (or remove `outputSchema` entirely), already-connected sessions keep validating against the cached schema. Reconnecting the client clears the cache.

**Client-side typing note**: `CallToolResult` carries an open `[x: string]: unknown` index signature, which defeats normal narrowing on `result.content` - e.g. `result.content.find(c => c.type === "text")` types the element as `unknown`. Consumers iterating tool results need an explicit cast or type guard rather than relying on inference.

**Default rule for upstream pass-through**: When an `outputSchema` (or a nested response object) forwards data straight from an upstream API, default it to `.passthrough()`. Upstream payloads routinely carry fields you didn't model, and a strict outer schema turns every one into a client-side AJV rejection. Reserve the `.parse()`-strip path (FIX 1) for response schemas where you deliberately want to drop upstream fields before they reach the client. `inputSchema` is the opposite - keep it strict so the LLM can't pass unmodeled arguments.

### Proxies and Aggregators: Strip `outputSchema` When Re-Listing

If you re-expose another server's tools to a downstream client, **drop `outputSchema` from the tool definitions you list**. You cannot control which SDK version the end client runs, and a stricter client AJV-rejects `structuredContent` that the upstream server considers perfectly valid - a failure you cannot fix from the middle.

> strip `outputSchema` from tool definitions when the proxy lists them to the downstream client. No `outputSchema` = no validation attempted. `structuredContent` still flows through untouched.

The data still reaches the model; only the client-side validation step is skipped. That is the right trade for a component that doesn't own either end.

**Diagnostic**: a doubled error prefix - `MCP error -32602: MCP error -32602:` - means a client or proxy in the chain re-wrapped a validation error it produced itself. The failure is client-side, not in your server.

### Middleware Must Spread the Whole Result

Any wrapper around a tool handler (auth gates, payment wrappers, logging, telemetry) must return `{...result}`, never a reconstructed object:

```typescript
// BROKEN: silently drops structuredContent and any future result field
return { content: result.content, isError: result.isError, _meta: result._meta };

// CORRECT: preserve everything, override only what you mean to
return { ...result, _meta: { ...result._meta, "my/annotation": value } };
```

This exact bug shipped in a published payment-wrapper package. Reconstruction is a silent data-loss bug that only shows up for tools using the fields you forgot - and it breaks again every time the spec adds a result field.

**Testing note**: the MCP Inspector is not ground truth for result and schema fields. It omits `outputSchema` in its display and does not surface `structuredContent` (it doesn't advertise the capability). Verify with a raw JSON-RPC `tools/list` / `tools/call` before concluding a field is missing.

## Non-Text Content Types

`content` blocks are not text-only. Spec 2025-11-25 defines `text`, `image`, `audio`, `resource_link`, and embedded `resource` blocks; all support optional annotations (`audience`, `priority`, `lastModified`). Resource links returned by tools are not guaranteed to appear in `resources/list`.

```typescript
return {
  content: [
    { type: "image", data: base64Jpeg, mimeType: "image/jpeg" },
    { type: "text", text: JSON.stringify({ width, height, url }) },
    { type: "resource_link", uri: "docs://guide", name: "Guide", mimeType: "text/markdown" },
  ],
};
```

### Image-Returning Tools

Don't inline full-resolution base64 by default - it blows client result caps (see SKILL.md "Result-Size Budgets"). But don't return only a bare URL either: pure-MCP clients without a shell have no primitive that turns an arbitrary image URL into vision. The pattern that serves both:

1. **`ImageContent` block with a server-downscaled preview** (~1024px JPEG) - vision-capable clients see the image directly.
2. **Text block with metadata plus a URL to the untouched original** - the universal deliverable for clients whose size caps drop the image block.

## Other Tool-Definition Fields

- **`icons`** ([SEP-973](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)): tools, resources, prompts, and implementations can carry `icons: [{ src, mimeType, sizes }]` for client UI display.
- **`listChanged` capability + `notifications/tools/list_changed`**: declare `tools: { listChanged: true }` and emit the notification when the tool set changes at runtime - required plumbing if you adopt the dynamic tool loading strategy from SKILL.md "Token Bloat Mitigation". On 2026-07-28 the client opts into delivery via the `subscriptions/listen` filter.
- **`execution.taskSupport`** (**2025-11-25 only**): per-tool negotiation of task-augmented execution - `"forbidden"` (default), `"optional"`, `"required"`. **Removed in 2026-07-28** along with core tasks; the field is absent from that revision's schema. Tasks now live in the `io.modelcontextprotocol/tasks` extension.

## Tool Design Patterns

### Outcome-Oriented Tools

Bundle multi-step operations into single tools. This reduces round-trips and token overhead.

```typescript
// DON'T: Three separate tools requiring LLM orchestration
server.tool("get_user", ...);
server.tool("list_orders", ...);
server.tool("get_shipping_status", ...);

// DO: One outcome-oriented tool
server.tool("track_order", "Track order status by customer email",
  { email: z.string().email().describe("Customer email") },
  async ({ email }) => {
    const user = await getUser(email);
    const orders = await listOrders(user.id);
    const latest = orders[0];
    const status = await getShippingStatus(latest.id);
    return {
      content: [{
        type: "text",
        text: `Order #${latest.id} shipped via ${status.carrier}, arriving ${status.eta}`,
      }],
    };
  },
);
```

### Flat Arguments

Prefer top-level primitives over nested objects. LLMs hallucinate less with flat schemas.

```typescript
// DON'T: Nested objects
z.object({
  filter: z.object({
    query: z.string(),
    options: z.object({
      limit: z.number(),
      sort: z.enum(["asc", "desc"]),
    }),
  }),
})

// DO: Flat arguments
z.object({
  query: z.string().describe("Search query"),
  limit: z.number().optional().describe("Max results (default 20)"),
  sort: z.enum(["asc", "desc"]).optional().describe("Sort order (default desc)"),
})
```

### Pagination

Return pagination metadata with default limits:

```typescript
z.object({
  query: z.string().describe("Search query"),
  offset: z.number().optional().describe("Skip N results (default 0)"),
  limit: z.number().optional().describe("Max results, 1-100 (default 20)"),
})
// Response includes:
// { results: [...], has_more: true, next_offset: 20, total_count: 142 }
```

### Result-Size Budgets and Truncation

Clients silently truncate large results (SKILL.md "Result-Size Budgets" has the per-client caps). Enforce your own cap server-side:

- **One backstop wrapper at the tool-registration chokepoint** guarantees the invariant even when an individual renderer overruns; keep the cap values in one constants module.
- **Two-tier trimming**: prefer smart trims at item boundaries with an explicit "N omitted - pass cursor=..." hint; hard-truncate with a uniform footer (link to the full output) only as a fallback.
- **Never cut JSON mid-body**: on overflow return a `{truncated: true, download_url, size_chars}` envelope instead of invalid JSON.
- **Skip `isError` results entirely** - truncation must never mangle payment/auth challenges or error payloads clients parse programmatically.
- **Budgets are per-connection, not per-call**: accept them as connection query params (`?max_chars=`, alongside `?tools=` filtering) instead of adding override args to every tool schema.

#### Mechanics of the per-tool cap

- **`_meta["anthropic/maxResultSizeChars"]` is a wire-level `tools/list` field, not an SDK feature.** It is a flat JSON field at the protocol level, so a Rust (`rmcp`), Python, or Go server can emit it exactly as a TypeScript one does - the TS SDK has no special privilege here. The key is literal, including the forward slash. Values above 500,000 are clamped, and clients that don't know the key ignore it harmlessly, so it is strictly additive.
- **It replaces the env cap for text; it is not bounded by it.** Per the client docs: *"the environment variable applies to tools that don't declare their own limit. Tools that set `anthropic/maxResultSizeChars` use that value instead for text content, regardless of what `MAX_MCP_OUTPUT_TOKENS` is set to."* So a per-tool value can raise **or lower** the effective cap independently of the user's env setting - declaring a small one is a legitimate way to enforce your own budget client-side.
- **It covers text content only.** Image or binary bytes in a `CallToolResult` remain bound by the client's global env cap (*"Tools that return image data are still subject to `MAX_MCP_OUTPUT_TOKENS`"*) with no per-tool override. Don't size an image-returning tool against the raised number.
- **Budget in bytes, not code points.** A char-count budget under-measures CJK and emoji payloads: a response that "fits" by character count can still blow the client cap once JSON-serialized.

#### Prefer paging over truncation

Let the *server* stop early rather than letting the client cut the tail off:

- An agent that asks for `limit=200` and gets 73 hits with `has_more=true` knows more exists and can fetch it. The same agent handed a client-side `[OUTPUT TRUNCATED]` banner cannot tell what it lost.
- Some clients don't truncate at all - they **spill the oversized result to a file** and hand the agent a small preview, forcing a multi-call round-trip through disk. That is strictly worse than paginating.
- **Reject knowably-oversized requests at the input boundary** with an error naming the corrective action; that is faster feedback than truncating the output.
- When you do truncate, **name the drill-in call in the marker**. `[truncated]` teaches the agent nothing; "showing 20 of 340 - call `get_detail(id)` for full text" teaches it the workflow.

#### Response-shape economy

- Rough targets: ~5-10KB total per search-style call, ~200 bytes/item for summaries, ~5KB/item for detail views.
- **Auto-truncate with good defaults rather than exposing a knob** - agents don't set knobs they weren't told about.
- Truncate on sentence or word boundaries, not mid-token.
- **Hoist row-invariant metadata into a top-level lookup map keyed by id** instead of repeating it per row. Repeating two ~35-character fields across 200 rows that only span 20 distinct parents is ~14KB of literally duplicated text.

### No-Parameter Tools

Use explicit empty schema - not `undefined` or omission:

```typescript
// Spec recommendation (2025-11-25)
server.tool("list_models", "List available models", {
  type: "object" as const,
  additionalProperties: false,
}, handler);
```

## Other Server Primitives

Beyond tools, the spec (2025-11-25) defines primitives a production server often needs. All are optional capabilities negotiated at initialization; a server that omits them still conforms.

| Primitive | Methods | When you need it |
|-----------|---------|------------------|
| **Prompts** | `prompts/list`, `prompts/get` (`registerPrompt`) | Reusable, parameterized prompt templates users invoke by name (slash-commands, canned workflows). Args are completable. |
| **Resources** | `resources/list`, `resources/read` (`server.resource(name, uri, config, readCallback)`) | Documentation or structured data exposed by URI - a `docs://` scheme is the common convention for guides shipped alongside tools. |
| **Resource Templates** | `resources/templates/list` (RFC 6570 URI templates) | Parameterized resources - `docs://{id}` instead of enumerating every static URI. Template variables are completable. |
| **Pagination** | opaque `cursor` param + `nextCursor` in result, on every `*/list` | Large tool/resource/prompt catalogs. The cursor is opaque - never parse or synthesize it; loop until `nextCursor` is absent. Distinct from in-tool `offset`/`limit` args. |
| **Completions** | `completion/complete` | Argument autocomplete for prompt args and resource-template variables. Return ranked candidates with `hasMore`/`total` hints. |
| **Cancellation** | `notifications/cancelled` | Client aborts an in-flight long request by id. Honor it via the handler's abort signal (`extra.signal` v1 / `ctx.mcpReq.signal` v2) - stop work, release resources. |

```typescript
server.resource("search-operators", "docs://search-operators", {
  title: "Search Operators Guide",
  description: "Supported search operators and syntax",
  mimeType: "text/markdown",
}, async () => ({
  contents: [{ uri: "docs://search-operators", text: operatorsMarkdown }],
}));
```
