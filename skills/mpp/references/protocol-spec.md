# MPP Core Protocol Specification

## Protocol Overview

MPP (Machine Payments Protocol) defines a Payment HTTP Authentication Scheme built on **HTTP 402 Payment Required**. It follows the structure of RFC 9110 HTTP Authentication but uses the `402` status code instead of `401` to signal that access requires payment rather than identity credentials.

MPP is submitted to the IETF as an Internet-Draft. It leverages existing HTTP semantics, making it compatible with standard web infrastructure - proxies, CDNs, and load balancers pass through the headers without modification.

The flow:
1. Client requests a protected resource.
2. Server responds with `402 Payment Required` and a `WWW-Authenticate: Payment` challenge.
3. Client fulfills payment and sends credentials in `Authorization: Payment`.
4. Server verifies payment and returns the resource with a `Payment-Receipt` header.

```http
GET /api/data HTTP/1.1
Host: api.example.com
```

```http
HTTP/1.1 402 Payment Required
WWW-Authenticate: Payment id="abc123", realm="api.example.com", method="tempo", intent="charge", ...
Content-Type: application/problem+json

{"type":"https://paymentauth.org/problems/payment-required","title":"Payment Required"}
```

---

## Challenge Structure

The server issues a challenge via the `WWW-Authenticate` header using the `Payment` scheme.

### Parameters

| Parameter     | Required | Description                                              |
|---------------|----------|----------------------------------------------------------|
| `id`          | Yes      | HMAC-derived challenge identifier (tamper-proof binding) |
| `realm`       | Yes      | Protection space (typically the host or API namespace)    |
| `method`      | Yes      | Payment method identifier (e.g., `tempo`, `stripe`, `lightning`) |
| `intent`      | Yes      | Payment intent type (e.g., `charge`, `session`)          |
| `request`     | Yes      | Base64url-encoded JSON with method-specific payment details |
| `expires`     | No       | ISO 8601 timestamp after which the challenge is invalid  |
| `description` | No       | Human-readable description of the payment                |
| `digest`      | No       | Content-Digest of the request body (for body binding)    |
| `opaque`      | No       | Server-specific opaque data echoed back by the client    |

### Request Parameter

The `request` parameter is **base64url-encoded JSON** (RFC 4648 section 5, no padding). Its contents are method-specific. Example for Tempo charge:

```json
{
  "amount": "1000",
  "currency": "0x20c0000000000000000000000000000000000000",
  "decimals": 6,
  "recipient": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
}
```

### Full Challenge Example

```http
HTTP/1.1 402 Payment Required
WWW-Authenticate: Payment id="qB3wErTyU7iOpAsD9fGhJk",
  realm="mpp.dev",
  method="tempo",
  intent="charge",
  request="eyJhbW91bnQiOiIxMDAwIiwiY3VycmVuY3kiOiIweDIwYzAuLi4ifQ",
  expires="2025-04-01T12:05:00Z",
  description="Premium API access"
Cache-Control: no-store
```

---

## Challenge ID Binding

The `id` parameter is a cryptographic binding that prevents tampering with challenge parameters without requiring server-side state storage.

### Construction

The server computes the ID as:

```
input = realm | method | intent | request | expires | digest | opaque
id    = base64url(HMAC-SHA256(server_secret, input))
```

Fields are concatenated with `|` as delimiter. Optional fields that are absent are included as empty strings (the delimiter is still present).

### Properties

- **Tamper-proof**: Any modification to challenge parameters invalidates the ID.
- **Stateless**: The server needs only its secret key to verify, no database lookup required.
- **Unique per challenge**: Different parameters always produce different IDs.

### Verification

When the client echoes the challenge back in the credential, the server recomputes the HMAC from the echoed parameters and compares it to the `id`. A mismatch means the challenge was altered.

---

## Credential Structure

After fulfilling payment, the client sends credentials via the `Authorization` header using the `Payment` scheme. The value is **base64url-encoded JSON**.

### Fields

| Field       | Required | Description                                              |
|-------------|----------|----------------------------------------------------------|
| `challenge` | Yes      | The full challenge object echoed back to the server      |
| `payload`   | Yes      | Method-specific proof of payment (tx hash, PI ID, etc.)  |
| `source`    | No       | Payer identity (e.g., `did:pkh:eip155:1:0xAbC...`)      |

The `source` field uses the `did:pkh` format for blockchain-based methods, encoding the chain namespace, chain ID, and address.

### Example

```http
POST /api/data HTTP/1.1
Host: api.example.com
Authorization: Payment eyJjaGFsbGVuZ2UiOnsia...fQ
Content-Type: application/json

{"query": "data"}
```

Decoded credential payload:

```json
{
  "challenge": {
    "id": "qB3wErTyU7iOpAsD9fGhJk",
    "realm": "mpp.dev",
    "method": "tempo",
    "intent": "charge",
    "request": "eyJhbW91bnQiOiIxMDAwIi4uLn0",
    "expires": "2025-04-01T12:05:00Z"
  },
  "payload": {
    "type": "transaction",
    "signature": "0x1b2c3d4e5f6a7b8c9d0e..."
  },
  "source": "0x1234567890abcdef1234567890abcdef12345678"
}
```

---

## Receipt Structure

On successful payment verification, the server returns the requested resource along with a `Payment-Receipt` header. The value is **base64url-encoded JSON**.

### Fields

| Field         | Required | Description                                     |
|---------------|----------|-------------------------------------------------|
| `challengeId` | Yes      | The challenge ID this receipt corresponds to     |
| `method`      | Yes      | Payment method used                              |
| `reference`   | Yes      | Payment reference (tx hash or payment intent ID) |
| `settlement`  | Yes      | Object with `amount` and `currency`              |
| `status`      | Yes      | Always `"success"`                               |
| `timestamp`   | Yes      | ISO 8601 timestamp of settlement                 |

### Example

```http
HTTP/1.1 200 OK
Payment-Receipt: eyJjaGFsbGVuZ2VJZCI6ImRCamZ0...fQ
Cache-Control: private
Content-Type: application/json

{"data": "protected content"}
```

Decoded receipt:

```json
{
  "challengeId": "qB3wErTyU7iOpAsD9fGhJk",
  "method": "tempo",
  "reference": "0xtx789abc...",
  "settlement": {
    "amount": "1000",
    "currency": "0x20c0000000000000000000000000000000000000"
  },
  "status": "success",
  "timestamp": "2025-04-01T12:00:00Z"
}
```

---

## Status Codes

MPP departs from traditional HTTP authentication by using `402` consistently for all payment-related challenges.

| Code | Usage                                                                 |
|------|-----------------------------------------------------------------------|
| 402  | All payment challenges: initial challenge, failed credentials, expired challenges, insufficient payment. Unlike other auth schemes that use 401 for failed credentials, MPP uses 402 consistently. |
| 401  | Authentication failures **unrelated** to payment (e.g., missing API key, invalid OAuth token). |
| 403  | Payment **succeeded** but access is denied by server policy (e.g., geo-restriction, rate limit, content policy). |

This distinction is important: a `402` always means the client should attempt payment. A `401` means the issue is identity, not payment. A `403` means payment went through but access is still denied - the client should not retry payment.

---

## Error Handling

MPP uses **RFC 9457 Problem Details** (`application/problem+json`) for error responses.

### Error Type URIs

All error types are under `https://paymentauth.org/problems/`:

| Type                    | Description                                        |
|-------------------------|----------------------------------------------------|
| `payment-required`      | No payment credential provided                     |
| `payment-insufficient`  | Payment amount too low                             |
| `payment-expired`       | Challenge has expired                              |
| `verification-failed`   | Payment proof could not be verified on-chain/off-chain |
| `method-unsupported`    | Requested payment method not supported             |
| `malformed-credential`  | Credential JSON is invalid or missing fields       |
| `invalid-challenge`     | Challenge ID does not match (tampered or unknown)  |

### Example Error Response

```http
HTTP/1.1 402 Payment Required
WWW-Authenticate: Payment id="newChallenge...", method="tempo", intent="charge", ...
Retry-After: 30
Content-Type: application/problem+json

{
  "type": "https://paymentauth.org/problems/payment-expired",
  "title": "Payment Challenge Expired",
  "status": 402,
  "detail": "The challenge expired at 2025-04-01T12:00:00Z. A new challenge is provided.",
  "instance": "/api/data"
}
```

The `Retry-After` header (in seconds) indicates when the client may retry. Servers should include it for `payment-expired` and transient `verification-failed` errors.

---

## Request Body Binding

For requests with bodies (`POST`, `PUT`, `PATCH`), the server can bind the challenge to the request body using the `digest` parameter.

The digest follows **RFC 9530 Content-Digest** format:

```http
POST /api/transfer HTTP/1.1
Host: api.example.com
Content-Type: application/json
Content-Digest: sha-256=:X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE=:

{"to": "0xRecipient", "amount": 50}
```

The server includes the digest in the challenge:

```http
HTTP/1.1 402 Payment Required
WWW-Authenticate: Payment id="...",
  realm="api.example.com",
  method="tempo",
  intent="charge",
  request="...",
  expires="2025-04-01T12:05:00Z",
  digest="sha-256=:X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE=:"
```

On credential submission, the server verifies that the `Content-Digest` of the submitted body matches the `digest` in the echoed challenge. This prevents a client from paying for one operation and submitting a different request body.

---

## Multiple Challenges

A server can offer multiple payment methods by including separate `WWW-Authenticate` headers:

```http
HTTP/1.1 402 Payment Required
WWW-Authenticate: Payment id="abc", realm="api.example.com", method="tempo",
  intent="charge", request="eyJhbW91bnQ...", expires="2025-04-01T12:05:00Z"
WWW-Authenticate: Payment id="def", realm="api.example.com", method="stripe",
  intent="charge", request="eyJ0byI6Ii4...", expires="2025-04-01T12:05:00Z"
WWW-Authenticate: Payment id="ghi", realm="api.example.com", method="lightning",
  intent="charge", request="eyJyZWNpcGl...", expires="2025-04-01T12:05:00Z"
```

The client selects the method it supports and responds with the corresponding challenge. The server must accept any of the offered methods.

---

## Security Considerations

### Transport Security

TLS 1.2 or higher is **required**. Payment credentials and receipts must never be transmitted over plaintext HTTP. Servers should reject non-TLS requests with `301` or `308` redirects to HTTPS.

### Replay Protection

Payment proofs must be **single-use**. For blockchain transactions, this is inherent (a tx hash can only be mined once). For off-chain methods like Stripe, the server must track used payment intent IDs and reject duplicates.

### Idempotency

Servers must not produce side effects on unpaid requests. The `402` response must be safe to retry. For operations that create resources, servers should support the `Idempotency-Key` header:

```http
POST /api/resource HTTP/1.1
Host: api.example.com
Idempotency-Key: unique-request-id-12345
Authorization: Payment eyJjaGFsbGVuZ2...
```

This ensures that if a client retries after a network failure, the server does not double-charge or duplicate the operation.

### Amount Verification

Clients should verify that the requested payment amount is reasonable before submitting payment. Machine agents should enforce configurable spend limits and flag unusual amounts.

### Credential Handling

- Payment credentials are **bearer tokens** - possession grants access.
- Servers must not log credential values or receipt references in access logs.
- Credentials should be held in memory only for the duration of the request.

### Caching

- `402` responses: `Cache-Control: no-store` (challenges are time-bound and unique).
- Responses with receipts: `Cache-Control: private` (receipts are user-specific).
- Shared caches (CDNs) must not cache `402` responses.

---

## Extensibility

### Custom Parameters

Servers may include custom parameters in the challenge. Custom parameter names must be **lowercase** and should use a vendor prefix (e.g., `x-vendor-param`). Unknown parameters are ignored by clients.

```http
WWW-Authenticate: Payment id="...", method="tempo",
  realm="api.example.com", intent="charge", request="...",
  expires="2025-04-01T12:05:00Z", x-vendor-tier="premium"
```

### Size Considerations

Challenges should remain **under 8KB** total (including all header overhead) to ensure compatibility with common HTTP infrastructure. The `request` parameter carries the bulk of the data; if method-specific details exceed this, use a reference URL pattern instead.

### Internationalization

- Method identifiers are **ASCII-only**, lowercase, using hyphens as separators.
- The `description` parameter supports **UTF-8** for human-readable text.
- All JSON payloads (request, credential, receipt) use UTF-8 encoding.
