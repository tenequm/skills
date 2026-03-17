# Transport Implementations

x402 supports three transports: HTTP, MCP, and A2A. All use the same core types (`PaymentRequired`, `PaymentPayload`, `SettlementResponse`) but differ in how data is transmitted.

## HTTP Transport

The original and primary transport. Uses HTTP status codes and headers. Response bodies are a server implementation concern - all x402 protocol information is communicated through headers.

### Headers

| Header | Direction | Content |
|--------|-----------|---------|
| `PAYMENT-REQUIRED` | Server -> Client | Base64-encoded `PaymentRequired` JSON |
| `PAYMENT-SIGNATURE` | Client -> Server | Base64-encoded `PaymentPayload` JSON |
| `PAYMENT-RESPONSE` | Server -> Client | Base64-encoded `SettlementResponse` JSON |

### Flow

**Step 1: Client requests resource**
```http
GET /weather HTTP/1.1
Host: api.example.com
```

**Step 2: Server responds 402**
```http
HTTP/1.1 402 Payment Required
Content-Type: application/json
PAYMENT-REQUIRED: eyJ4NDAyVmVyc2lvbiI6MiwiZXJyb3IiOi...

{}
```

**Step 3: Client retries with payment**
```http
GET /weather HTTP/1.1
Host: api.example.com
PAYMENT-SIGNATURE: eyJ4NDAyVmVyc2lvbiI6MiwicmVzb3VyY2...
```

**Step 4: Server responds with data**
```http
HTTP/1.1 200 OK
Content-Type: application/json
PAYMENT-RESPONSE: eyJzdWNjZXNzIjp0cnVlLCJ0cmFuc2FjdGl...

{"weather": "sunny", "temperature": 70}
```

**Step 5 (failure): Server responds with payment failure**
```http
HTTP/1.1 402 Payment Required
Content-Type: application/json
PAYMENT-RESPONSE: eyJzdWNjZXNzIjpmYWxzZSwiZXJyb3JSZWFzb24iOi...

{}
```

On failure, the `PAYMENT-RESPONSE` header still contains the settlement result (with `success: false` and `errorReason`).

### HTTP Error Mapping

| x402 Error | HTTP Status |
|------------|-------------|
| Payment Required | 402 |
| Invalid Payment | 400 |
| Payment Failed | 402 |
| Server Error | 500 |
| Success | 200 |

## MCP Transport (Model Context Protocol)

For AI agents and MCP clients paying for tools.

### Flow

**Step 1: Client calls tool without payment**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "financial_analysis",
    "arguments": { "ticker": "AAPL" }
  }
}
```

**Step 2: Server returns payment required**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "isError": true,
    "structuredContent": {
      "x402Version": 2,
      "error": "Payment required",
      "resource": { "url": "mcp://tool/financial_analysis" },
      "accepts": [{ "scheme": "exact", "network": "eip155:84532", "..." : "..." }]
    },
    "content": [{ "type": "text", "text": "{\"x402Version\":2,...}" }]
  }
}
```

Server provides `PaymentRequired` in both `structuredContent` (preferred) and `content[0].text` (JSON string fallback).

**Step 3: Client retries with payment in `_meta`**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "financial_analysis",
    "arguments": { "ticker": "AAPL" },
    "_meta": {
      "x402/payment": {
        "x402Version": 2,
        "accepted": { "scheme": "exact", "..." : "..." },
        "payload": { "signature": "0x...", "authorization": { "..." : "..." } }
      }
    }
  }
}
```

**Step 4: Server returns result with settlement**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{ "type": "text", "text": "Analysis result..." }],
    "_meta": {
      "x402/payment-response": {
        "success": true,
        "transaction": "0x1234...",
        "network": "eip155:84532",
        "payer": "0x857b..."
      }
    }
  }
}
```

### MCP Key Fields

| Field | Location | Purpose |
|-------|----------|---------|
| `_meta["x402/payment"]` | Request params | Client sends PaymentPayload |
| `_meta["x402/payment-response"]` | Response result | Server sends SettlementResponse |
| `structuredContent` | Error response | PaymentRequired data |
| `isError: true` | Response result | Signals payment required |

## A2A Transport (Agent-to-Agent Protocol)

For agent-to-agent payments using JSON-RPC task-based state.

### Flow

**Step 1: Agent sends task, server requests payment**

Server returns `state: "input-required"` with payment metadata:

```json
{
  "result": {
    "kind": "task",
    "id": "task-123",
    "status": {
      "state": "input-required",
      "message": {
        "role": "agent",
        "parts": [{ "kind": "text", "text": "Payment is required." }],
        "metadata": {
          "x402.payment.status": "payment-required",
          "x402.payment.required": {
            "x402Version": 2,
            "resource": { "url": "...", "description": "..." },
            "accepts": [{ "scheme": "exact", "network": "eip155:8453", "..." : "..." }]
          }
        }
      }
    }
  }
}
```

**Step 2: Client submits payment**

```json
{
  "params": {
    "message": {
      "taskId": "task-123",
      "role": "user",
      "parts": [{ "kind": "text", "text": "Payment authorization." }],
      "metadata": {
        "x402.payment.status": "payment-submitted",
        "x402.payment.payload": {
          "x402Version": 2,
          "accepted": { "..." : "..." },
          "payload": { "signature": "0x...", "authorization": { "..." : "..." } }
        }
      }
    }
  }
}
```

**Step 3: Server settles and completes**

```json
{
  "result": {
    "kind": "task",
    "id": "task-123",
    "status": {
      "state": "completed",
      "message": {
        "role": "agent",
        "parts": [{ "kind": "text", "text": "Payment successful." }],
        "metadata": {
          "x402.payment.status": "payment-completed",
          "x402.payment.receipts": [{
            "success": true,
            "transaction": "0x1234...",
            "network": "eip155:8453",
            "payer": "0x857b..."
          }]
        }
      }
    }
  }
}
```

### A2A Payment Status Lifecycle

| Status | Task State | Description |
|--------|-----------|-------------|
| `payment-required` | `input-required` | Server requests payment |
| `payment-rejected` | `failed` | Client declined |
| `payment-submitted` | `working` | Payment received |
| `payment-verified` | `working` | Payment validated |
| `payment-completed` | `completed` | Settled on-chain |
| `payment-failed` | `failed` | Verification/settlement failed |

### A2A Extension Declaration

Agents declare x402 support in their AgentCard:

```json
{
  "capabilities": {
    "extensions": [{
      "uri": "https://github.com/google-a2a/a2a-x402/v0.1",
      "description": "x402 on-chain payment support",
      "required": true
    }]
  }
}
```

Clients activate via HTTP header:
```http
X-A2A-Extensions: https://github.com/google-a2a/a2a-x402/v0.1
```

### A2A Metadata Keys

| Key | Direction | Content |
|-----|-----------|---------|
| `x402.payment.status` | Both | Payment lifecycle status |
| `x402.payment.required` | Server -> Client | PaymentRequired object |
| `x402.payment.payload` | Client -> Server | PaymentPayload object |
| `x402.payment.receipts` | Server -> Client | Array of SettlementResponse |
| `x402.payment.error` | Server -> Client | Error code string |
