# Tool Schema Guide

Complete Zod-to-JSON-Schema conversion rules, known breakage, outputSchema, and structuredContent patterns.

## Table of Contents
- [Zod Schema Conversion](#zod-schema-conversion)
- [What Works](#what-works)
- [What Breaks](#what-breaks)
- [outputSchema and structuredContent](#outputschema-and-structuredcontent)
- [Tool Design Patterns](#tool-design-patterns)

## Zod Schema Conversion

### v1 Path (current stable)

The SDK's `normalizeObjectSchema()` gates Zod schemas through `toJsonSchemaCompat()`. Only `z.object()` shapes pass through correctly.

**Flow**: `z.object({...})` -> `zodToJsonSchema()` -> JSON Schema object with `type: "object"` and `properties`.

Key constraint: The MCP protocol requires `Tool.inputSchema` to have `type: "object"` at the top level. Any Zod type that doesn't produce this is silently dropped or produces an empty schema.

### v2 Path (pre-alpha)

v2 uses Standard Schema interfaces (`StandardSchemaWithJSON`). The conversion delegates to the schema library's native `toJSONSchema()`. Zod v4's native `z.toJSONSchema()` produces correct JSON Schema 2020-12 output.

However, the `type: "object"` top-level requirement in the MCP protocol still applies. A `z.discriminatedUnion()` produces `{ oneOf: [...] }` without `type: "object"`, so clients that validate may reject it.

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

// FIX: Use Zod
server.tool("my-tool", "desc", {
  query: z.string().describe("Search query"),
}, handler);
```

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

**Rule today**: SDK v1.23+ accepts Zod v3 or v4. SDK v2 alpha works with any [Standard Schema](https://standardschema.dev) library (Zod v4, Valibot, ArkType) and ships a `fromJsonSchema` adapter for raw JSON Schema (e.g. TypeBox).

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
    // Structured data - clients can process programmatically
    structuredContent: weather,
    // Text fallback - backward compatibility with older clients
    content: [{ type: "text", text: JSON.stringify(weather) }],
  };
});
```

### Rules (spec normative)

- If `outputSchema` is provided, server MUST return `structuredContent` conforming to it
- Client SHOULD validate `structuredContent` against the schema
- Server SHOULD also include serialized JSON in `content` for backward compatibility
- "Soft contracts" - tools SHOULD produce schema-compliant outputs but the spec acknowledges AI-generated outputs may vary

### Token Benefits

- Clients know output shape ahead of time - better context window management
- Programmatic clients process structured data without LLM parsing
- Enables client-side field projection (only show relevant fields to LLM)

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

### No-Parameter Tools

Use explicit empty schema - not `undefined` or omission:

```typescript
// Spec recommendation (2025-11-25)
server.tool("list_models", "List available models", {
  type: "object" as const,
  additionalProperties: false,
}, handler);
```
