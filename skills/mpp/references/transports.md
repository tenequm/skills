# Transports

## HTTP Transport

HTTP is the primary transport binding for MPP, using standard RFC 9110 HTTP Authentication headers. All JSON payloads are encoded as **base64url without padding** (RFC 4648 section 5).

### Challenge Delivery

The server signals payment requirements via `WWW-Authenticate` using the `Payment` scheme:

```http
WWW-Authenticate: Payment id="abc123", method="tempo", intent="charge", request="eyJhbW91bnQ..."
```

Parameters are key-value pairs following standard HTTP auth parameter syntax. Multiple challenges (multiple payment methods) use separate `WWW-Authenticate` headers.

### Credential Delivery

The client submits payment proof via `Authorization` using the `Payment` scheme:

```http
Authorization: Payment eyJjaGFsbGVuZ2UiOns...
```

The value after `Payment ` is a single base64url-encoded JSON object containing `challenge`, `payload`, and optional `source`.

### Receipt Delivery

The server confirms payment via the `Payment-Receipt` header:

```http
Payment-Receipt: eyJjaGFsbGVuZ2VJZCI6...
```

The value is base64url-encoded JSON containing `challengeId`, `method`, `reference`, `settlement`, `status`, and `timestamp`.

### Full HTTP Flow

```http
# Step 1: Client requests protected resource
GET /api/data HTTP/1.1
Host: api.example.com

# Step 2: Server responds with 402 + challenge
HTTP/1.1 402 Payment Required
WWW-Authenticate: Payment id="dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
  realm="api.example.com",
  method="tempo",
  intent="charge",
  request="eyJhbW91bnQiOiIwLjAxIiwiY3VycmVuY3kiOiIweC4uLiJ9",
  expires="1711929600",
  description="API access: $0.01"
Cache-Control: no-store
Content-Type: application/problem+json

{"type":"https://paymentauth.org/problems/payment-required","title":"Payment Required"}

# Step 3: Client fulfills payment and retries with credential
GET /api/data HTTP/1.1
Host: api.example.com
Authorization: Payment eyJjaGFsbGVuZ2UiOnsiaWQiOiJkQmpm...InR5cGUiOiJoYXNoIn19

# Step 4: Server verifies payment and returns resource with receipt
HTTP/1.1 200 OK
Payment-Receipt: eyJjaGFsbGVuZ2VJZCI6ImRCamZ0SmVaNENW...
Cache-Control: private
Content-Type: application/json

{"data": "protected content"}
```

---

## MCP Transport

The MCP (Model Context Protocol) transport uses JSON-RPC encoding for payment flows. This enables MCP tool calls to require payment without breaking the JSON-RPC protocol.

### Challenge Delivery

Payment challenges are returned as JSON-RPC errors with code `-32042`:

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "error": {
    "code": -32042,
    "message": "Payment Required",
    "data": {
      "challenges": [
        {
          "id": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
          "realm": "my-mcp-server",
          "method": "tempo",
          "intent": "charge",
          "request": "eyJhbW91bnQiOiIwLjAxIn0",
          "expires": "1711929600",
          "description": "Tool call: premium_analysis"
        }
      ]
    }
  }
}
```

The `challenges` array can contain multiple challenges (one per supported payment method), mirroring the multiple `WWW-Authenticate` headers in HTTP.

### Credential Delivery

Payment credentials are embedded in the tool call's `_meta` field:

```json
{
  "jsonrpc": "2.0",
  "id": "req-2",
  "method": "tools/call",
  "params": {
    "name": "premium_analysis",
    "arguments": { "query": "analyze this" },
    "_meta": {
      "org.paymentauth/credential": {
        "challenge": {
          "id": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
          "realm": "my-mcp-server",
          "method": "tempo",
          "intent": "charge",
          "request": "eyJhbW91bnQiOiIwLjAxIn0",
          "expires": "1711929600"
        },
        "payload": { "type": "hash", "hash": "0xabc123..." },
        "source": "did:pkh:eip155:4217:0x1234..."
      }
    }
  }
}
```

The credential is a JSON object (not base64url-encoded) under the namespaced key `org.paymentauth/credential`.

### Receipt Delivery

Payment receipts are embedded in the result's `_meta` field:

```json
{
  "jsonrpc": "2.0",
  "id": "req-2",
  "result": {
    "content": [
      { "type": "text", "text": "Analysis result: ..." }
    ],
    "_meta": {
      "org.paymentauth/receipt": {
        "challengeId": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        "method": "tempo",
        "reference": "0xdef456...",
        "settlement": { "amount": "0.01", "currency": "USD" },
        "status": "success",
        "timestamp": "2025-04-01T12:00:00Z"
      }
    }
  }
}
```

### Full MCP Flow

```json
// Step 1: Client calls tool
{
  "jsonrpc": "2.0", "id": "1",
  "method": "tools/call",
  "params": { "name": "premium_tool", "arguments": {} }
}

// Step 2: Server returns -32042 error with challenges
{
  "jsonrpc": "2.0", "id": "1",
  "error": {
    "code": -32042,
    "message": "Payment Required",
    "data": {
      "challenges": [{
        "id": "abc", "method": "tempo", "intent": "charge",
        "request": "eyJhbW91bnQiOiIwLjAxIn0", "expires": "1711929600"
      }]
    }
  }
}

// Step 3: Client retries with credential in _meta
{
  "jsonrpc": "2.0", "id": "2",
  "method": "tools/call",
  "params": {
    "name": "premium_tool",
    "arguments": {},
    "_meta": {
      "org.paymentauth/credential": {
        "challenge": { "id": "abc", "method": "tempo", "intent": "charge", "request": "eyJhbW91bnQiOiIwLjAxIn0", "expires": "1711929600" },
        "payload": { "type": "hash", "hash": "0x..." }
      }
    }
  }
}

// Step 4: Server returns result with receipt in _meta
{
  "jsonrpc": "2.0", "id": "2",
  "result": {
    "content": [{ "type": "text", "text": "Premium result" }],
    "_meta": {
      "org.paymentauth/receipt": {
        "challengeId": "abc", "method": "tempo", "reference": "0x...",
        "settlement": { "amount": "0.01", "currency": "USD" },
        "status": "success", "timestamp": "2025-04-01T12:00:00Z"
      }
    }
  }
}
```

---

## Comparison Table

| Aspect | HTTP | MCP / JSON-RPC |
|---|---|---|
| **Challenge** | `WWW-Authenticate: Payment ...` header | JSON-RPC error code `-32042`, challenges in `error.data.challenges` |
| **Credential** | `Authorization: Payment <base64url>` header | `_meta.org.paymentauth/credential` in tool call params |
| **Receipt** | `Payment-Receipt: <base64url>` header | `_meta.org.paymentauth/receipt` in result._meta |
| **Encoding** | Base64url without padding (RFC 4648) | Native JSON objects |
| **Status code** | HTTP 402 | JSON-RPC error code -32042 |
| **Multiple methods** | Multiple `WWW-Authenticate` headers | Multiple entries in `challenges` array |

---

## JSON-RPC Transport

For non-MCP JSON-RPC services, the encoding is identical to the MCP transport. The same `-32042` error code, `_meta` namespacing, and JSON object encoding apply. This ensures any JSON-RPC service can adopt MPP without protocol-specific adaptations.

The only difference is the absence of MCP-specific semantics (tool names, content arrays). The credential and receipt still use the `org.paymentauth/credential` and `org.paymentauth/receipt` keys in `_meta`.

---

## Transport-Agnostic Design

The three core primitives - Challenge, Credential, and Receipt - remain identical regardless of transport. Only the encoding and delivery mechanism changes:

- **Challenge**: Same fields (`id`, `realm`, `method`, `intent`, `request`, `expires`, etc.) whether serialized into an HTTP header or a JSON-RPC error.
- **Credential**: Same structure (`challenge`, `payload`, `source`) whether base64url-encoded in `Authorization` or embedded as JSON in `_meta`.
- **Receipt**: Same fields (`challengeId`, `method`, `reference`, `settlement`, `status`, `timestamp`) whether in `Payment-Receipt` header or `_meta`.

This means payment method implementations (Tempo, Stripe, Lightning, custom) work across all transports without modification. The transport layer handles serialization; the payment method handles settlement.

```ts
// Same payment method works with both transports
const method = tempo.charge({ currency: '0x...', recipient: '0x...' })

// HTTP transport
const mppx = Mppx.create({ methods: [method], transport: 'http' })

// MCP transport
const server = McpServer.wrap(baseServer, { methods: [method] })
```
