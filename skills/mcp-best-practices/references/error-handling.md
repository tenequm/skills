# Error Handling

Full error taxonomy, code examples, and patterns for tool errors, protocol errors, and payment integration.

## Table of Contents
- [Error Taxonomy](#error-taxonomy)
- [Tool Execution Errors](#tool-execution-errors)
- [Protocol Errors](#protocol-errors)
- [The error.data Loss Bug](#the-errordata-loss-bug)
- [Error Helper Pattern](#error-helper-pattern)
- [Payment Error Patterns](#payment-error-patterns)

## Error Taxonomy

MCP has two distinct error reporting mechanisms. Choosing the wrong one makes the LLM blind to fixable problems.

| Type | JSON-RPC | LLM Visibility | Self-Correction | Use For |
|------|----------|----------------|-----------------|---------|
| **Tool Execution Error** | `CallToolResult` with `isError: true` | Always (clients SHOULD show) | Yes | Input validation, API failures, business logic, rate limits |
| **Protocol Error** | JSON-RPC error response (`{ error: { code, message } }`) | Maybe (clients MAY show) | No | Unknown tool, malformed request, server crash, capability mismatch |

**The rule** (SEP-1303, merged into spec 2025-11-25): If the LLM could self-correct by seeing the error message, it MUST be a Tool Execution Error. Protocol errors are for structural problems the LLM can't fix.

### SEP-2140 Extension (proposal; issue closed in favor of spec PR #2145)

Extends SEP-1303 to cover three more cases that should also be Tool Execution Errors:
1. **Tool resolution failures** - unknown tool name (currently protocol error)
2. **Tool unavailability** - disabled/policy-restricted tool
3. **Output validation failures** - structuredContent doesn't match outputSchema

Source: [modelcontextprotocol#2140](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2140), closed 2026-01-23 in favor of [PR #2145](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2145)

## Tool Execution Errors

Return `isError: true` in the `CallToolResult`. The content array carries the error message the LLM will see.

### Input Validation

```typescript
async function searchHandler({ query, since }: { query: string; since?: string }) {
  // Validate input - return tool error so LLM can correct
  if (since) {
    const date = new Date(since);
    if (isNaN(date.getTime())) {
      return {
        isError: true,
        content: [{ type: "text", text: `Invalid date format: "${since}". Use ISO format (YYYY-MM-DD).` }],
      };
    }
    if (date > new Date()) {
      return {
        isError: true,
        content: [{ type: "text", text: `Date must be in the past. Received: ${since}. Current: ${new Date().toISOString().split("T")[0]}` }],
      };
    }
  }

  const results = await doSearch(query, since);
  return { content: [{ type: "text", text: JSON.stringify(results) }] };
}
```

### Upstream API Failures

```typescript
async function fetchHandler({ url }: { url: string }) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return {
        isError: true,
        content: [{ type: "text", text: `Upstream returned ${response.status}: ${response.statusText}. Try a different URL or check if the service is available.` }],
      };
    }
    const data = await response.json();
    return { content: [{ type: "text", text: JSON.stringify(data) }] };
  } catch (err) {
    return {
      isError: true,
      content: [{ type: "text", text: `Network error fetching ${url}: ${err instanceof Error ? err.message : "unknown"}. The service may be down.` }],
    };
  }
}
```

### Rate Limits

```typescript
return {
  isError: true,
  content: [{ type: "text", text: "Rate limit exceeded. Wait 30 seconds before retrying. Current limit: 10 requests/minute." }],
};
```

### Key Principles

1. **Be specific** - include the bad value, the expected format, and a correction hint
2. **Include context** - current date, limits, valid options
3. **Be actionable** - tell the LLM what to do differently
4. **Never return stack traces** - they waste tokens and leak internals

### Forgiving Input Recovery

If an argument's intent is unambiguous, recover it instead of returning an error: accept a full URL where a bare handle is expected (and vice versa), map common aliases (`image_url`/`media_url`/`src`/`href` -> `url`), coerce obvious scalar/array mismatches. Agents routinely vary surface forms, and every avoidable `isError` costs a round-trip. Reserve errors for genuine ambiguity - and then follow the principles above with an actionable hint.

## Protocol Errors

Use JSON-RPC error responses (via `McpError` in v1, `ProtocolError` in v2) only for structural problems. Standard JSON-RPC error codes:

| Code | Name | When |
|------|------|------|
| `-32600` | Invalid Request | Malformed JSON-RPC |
| `-32601` | Method Not Found | Unknown method |
| `-32602` | Invalid Params | Schema validation failure at protocol level |
| `-32603` | Internal Error | Server crash, unrecoverable |
| `-32000` to `-32099` | Server errors | Custom server-defined errors |

```typescript
import { McpError, ErrorCode } from "@modelcontextprotocol/sdk/types.js";

// Only for structural problems the LLM can't fix
throw new McpError(ErrorCode.InternalError, "Database connection lost");
```

Inside a **tool handler** a throw does not produce a JSON-RPC error at all: the SDK converts every exception - including a thrown `McpError`/`ProtocolError` - into an `isError: true` result carrying the message, and drops the code and `data` (`UrlElicitationRequiredError` is the one exception). Protocol errors are what the SDK itself emits for unknown methods, malformed requests, and validation outside your handler.

## The error.data Loss Behavior

**Critical**: The SDK strips `error.data` when converting an `McpError` thrown from a tool handler into a `CallToolResult`. If you embed structured data in McpError's `data` field (e.g., payment challenges, retry metadata), it does not reach the client. This is observed across the x402/MPP MCP ecosystem - see Client Compatibility table below. (Historically `-32042` was the one code observed to survive with `error.data` intact - do not rely on it: as of spec 2026-07-28 that code is spec-allocated and off-limits, see [Payment Error Patterns](#payment-error-patterns).)

```typescript
// BROKEN: error.data is lost in transit
// (1002 = application-defined, outside the JSON-RPC reserved range -32768..-32000)
throw new McpError(1002, "Payment Required", {
  x402Version: 2,
  accepts: [{ scheme: "exact", network: "base", price: "5000" }],
});
// Client receives: { code: 1002, message: "Payment Required" }
// The accepts array is GONE

// FIX: Use isError tool result with structured content
return {
  isError: true,
  content: [{ type: "text", text: JSON.stringify({
    error: "Payment Required",
    x402Version: 2,
    accepts: [{ scheme: "exact", network: "base", price: "5000" }],
  })}],
  structuredContent: {
    error: "Payment Required",
    x402Version: 2,
    accepts: [{ scheme: "exact", network: "base", price: "5000" }],
  },
};
```

## Error Helper Pattern

Create a reusable helper for consistent error formatting:

```typescript
// Module-level helper
function toolError(message: string, details?: Record<string, unknown>): {
  isError: true;
  content: Array<{ type: "text"; text: string }>;
  structuredContent?: Record<string, unknown>;
} {
  const payload = details ? { error: message, ...details } : { error: message };
  return {
    isError: true,
    content: [{ type: "text", text: details ? JSON.stringify(payload) : message }],
    ...(details && { structuredContent: payload }),
  };
}

// Usage
return toolError("Rate limit exceeded", {
  retry_after_seconds: 30,
  current_limit: "10/min",
});

return toolError("Invalid date format. Use ISO (YYYY-MM-DD).");
```

## Payment Error Patterns

For MCP servers gated by payment protocols (x402, MPP), errors need to carry payment metadata that clients can act on programmatically.

> **HTTP status is always 200.** A payment/auth challenge returned as an `isError: true` tool result is a *successful* JSON-RPC response, so it rides HTTP `200` - not `401`/`402`. Clients (and anyone testing with `curl`) must parse the JSON-RPC body for the challenge; don't gate on the HTTP status code. Misreading this as "auth is broken" is a common false alarm.

### Do not use `-32042` for payments (collision with the released spec)

Some payment tooling follows the Internet-Draft [`draft-payment-transport-mcp-00`](https://paymentauth.org/draft-payment-transport-mcp-00.html) (self-published 2026-07-03; not on the IETF datatracker), which claims `-32042` for "Payment Required" and `-32043` for "payment verification failed". **Both codes collide with MCP's own allocation policy as of spec 2026-07-28.**

The released spec partitions the JSON-RPC implementation-defined range and puts `-32020..-32099` under exclusive spec control:

> **`-32020` to `-32099` - reserved for the MCP specification.** [...] Implementations **MUST NOT** emit any code from this sub-range that is not defined by this specification and **MUST** use defined codes only with their specified meanings.

`-32042` is already spec-allocated - as *"URL elicitation required (2025-11-25 only)"*, a retired code that implementations of the current revision MUST NOT emit at all. A payment challenge sent as `-32042` is therefore both spec-violating and ambiguous with a real (if retired) MCP meaning.

**What to do instead**, in order of preference:

1. **Use the `isError: true` tool-result pattern below.** It is what the x402/MPP ecosystem actually interoperates on, it survives the `error.data` loss described above, and it is unaffected by the code-allocation policy.
2. If you genuinely need a protocol-level code, **allocate outside the JSON-RPC reserved range entirely** - the spec is explicit that new codes "**SHOULD** be allocated outside the JSON-RPC reserved range (`-32768` to `-32000`)".

Do not allocate anything new in `-32000..-32019` either: that sub-range is now **legacy**, and new implementations "**SHOULD NOT** use codes from this sub-range at all".

### x402 Payment Required (isError pattern)

The bulk of the x402 MCP ecosystem uses `isError: true` tool results (not McpError) because of the `error.data` loss behavior described above. Breaking this format breaks existing x402 MCP clients.

```typescript
// Payment challenge - returned when no credential present
return {
  isError: true,
  content: [{ type: "text", text: JSON.stringify({
    x402Version: 2,
    error: "Payment required",
    accepts: [
      { scheme: "exact", network: "eip155:8453", price: "5000", payTo: "0x..." },
      { scheme: "exact", network: "solana:mainnet", price: "5000", payTo: "So1..." },
    ],
  })}],
  structuredContent: {
    x402Version: 2,
    error: "Payment required",
    accepts: [
      { scheme: "exact", network: "eip155:8453", price: "5000", payTo: "0x..." },
      { scheme: "exact", network: "solana:mainnet", price: "5000", payTo: "So1..." },
    ],
  },
};
```

### Dual-Protocol Challenges (x402 + MPP)

When supporting both x402 and MPP payment protocols on the same tool, embed both challenge types in the `isError` response. x402 clients read `accepts`, MPP clients read `org.paymentauth/challenges`. Unknown fields are ignored.

```typescript
return {
  isError: true,
  content: [{ type: "text", text: JSON.stringify(challenge) }],
  structuredContent: {
    x402Version: 2,
    error: "Payment required",
    // x402 clients read this
    accepts: [{ scheme: "exact", network: "eip155:8453", price: "5000", payTo: "0x..." }],
    // MPP clients read this
    "org.paymentauth/challenges": [
      { id: "ch_abc", method: "tempo", intent: "charge", request: { amount: "5000" } },
    ],
  },
};
```

### Credential Dispatch via _meta

When clients retry with a credential, dispatch by `_meta` key:

```typescript
async function paidToolHandler(args: unknown, extra: { _meta?: Record<string, unknown> }) {
  const meta = extra._meta ?? {};

  if (meta["x402/payment"]) {
    // x402 credential - verify and settle
    return await handleX402Payment(args, meta["x402/payment"]);
  }

  if (meta["org.paymentauth/credential"]) {
    // MPP credential - charge via tempo
    return await handleMppPayment(args, meta["org.paymentauth/credential"]);
  }

  // No credential - return payment challenge
  return paymentRequiredError(args);
}
```

### Client Compatibility

| Client | Reads `isError` challenges | Reads a JSON-RPC error code challenge (`-32042`) |
|--------|---------------------------|------------------------|
| x402MCPClient | Yes (via `structuredContent` then `content[0].text`) | No (crashes) |
| x402-proxy | Yes | No (planned) |
| agentpay-mcp | Yes | No |
| MCPay | Yes | No |
| Cloudflare agents/x402 | Yes | No |

The ecosystem is standardized on `isError: true` tool results. Do not use McpError for payment challenges.
