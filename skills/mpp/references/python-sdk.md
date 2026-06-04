# pympp Python SDK

Verified against pympp 0.8.2. Python currently supports the **charge** intent only - the session (payment-channel) intent is TypeScript/Rust-only per the official SDK capability matrix.

## Installation

```bash
# Core SDK
pip install pympp

# With Tempo payment method
pip install "pympp[tempo]"
```

**Requirements:** Python 3.10+

**Dependencies:**
- Core: `httpx`
- With `[tempo]`: `pytempo`, `eth-account`, `rlp`

---

## Server (FastAPI)

### Basic Setup

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mpp import Challenge
from mpp.server import Mpp
from mpp.methods.tempo import tempo, ChargeIntent

app = FastAPI()

# Auto-detects realm from env vars
# Auto-generates secret_key to .env if not present
mpp = Mpp.create(
    method=tempo(
        currency="<PATHUSD_TESTNET>",
        recipient="0xYourAddress",
        intents={"charge": ChargeIntent()},
    ),
)
```

### Charge Endpoint (decorator)

The current pympp API gates a route with the `@server.pay(amount=...)` decorator. On payment the handler receives an injected `Credential` and `Receipt`; the decorator emits the 402 challenge and attaches the receipt automatically:

```python
from mpp import Credential, Receipt
from mpp.server import Mpp
from mpp.methods.tempo import tempo, ChargeIntent

server = Mpp.create(
    method=tempo(
        currency="<PATHUSD_TESTNET>",
        recipient="0xYourAddress",
        intents={"charge": ChargeIntent()},
    ),
)

@app.get("/resource")
@server.pay(amount="0.50")
async def get_resource(request, credential: Credential, receipt: Receipt):
    return {"data": "paid content", "payer": credential.source}
```

### Full FastAPI Example

```python
from fastapi import FastAPI
from mpp import Credential, Receipt
from mpp.server import Mpp
from mpp.methods.tempo import tempo, ChargeIntent

app = FastAPI()
server = Mpp.create(
    method=tempo(
        currency="<PATHUSD_TESTNET>",
        recipient="0xYourAddress",
        intents={"charge": ChargeIntent()},
    ),
)

@app.get("/api/data")
@server.pay(amount="0.10")
async def get_data(request, credential: Credential, receipt: Receipt):
    return {"data": "premium content", "payer": credential.source}

@app.get("/api/free")
async def get_free():
    return {"data": "free content"}
```

---

## Client

### Async Client

The client is an async context manager that wraps `httpx.AsyncClient` with automatic 402 handling:

```python
from mpp.client import Client
from mpp.methods.tempo import tempo, TempoAccount, ChargeIntent

account = TempoAccount.from_key("0xYourPrivateKey")

async with Client(
    methods=[
        tempo(account=account, intents={"charge": ChargeIntent()}),
    ],
) as client:
    response = await client.get("https://api.example.com/data")
    print(response.json())
```

### HTTP Methods

The client exposes standard HTTP methods:

```python
async with Client(methods=[tempo(account=account, intents={"charge": ChargeIntent()})]) as client:
    # GET
    res = await client.get("https://api.example.com/data")

    # POST
    res = await client.post("https://api.example.com/submit", json={"key": "value"})

    # PUT
    res = await client.put("https://api.example.com/update", json={"key": "new_value"})

    # DELETE
    res = await client.delete("https://api.example.com/item/123")

    # Generic request
    res = await client.request("PATCH", "https://api.example.com/partial", json={"field": "val"})
```

### One-Off Request

For single requests without managing a client lifecycle:

```python
from mpp.client import get

response = await get(
    "https://api.example.com/data",
    methods=[tempo(account=account, intents={"charge": ChargeIntent()})],
)
print(response.json())
```

---

## Sessions / Streaming (not supported in Python)

The session (payment-channel) intent - off-chain vouchers, SSE/WebSocket streaming, pay-as-you-go billing - is **not implemented in pympp**. The official SDK capability matrix lists the session intent for TypeScript and Rust only. For metered/streaming billing in Python today, fall back to per-request `charge` calls, or run the session-billing tier on the TypeScript (`mppx`) or Rust (`mpp`) server. Watch [mpp.dev/sdk/python](https://mpp.dev/sdk/python) for session support.

---

## Core Types

### Challenge

```python
from mpp import Challenge

# Parse from WWW-Authenticate header
challenge = Challenge.from_www_authenticate(header_value)

# Serialize back to header
header = challenge.to_www_authenticate(realm="api.example.com")

# Access fields
challenge.id
challenge.method
challenge.intent
challenge.request
challenge.expires
```

### Credential

```python
from mpp import Credential

# Create a credential
credential = Credential(
    id=challenge.id,
    payload={"type": "hash", "hash": "0xabc123..."},
    source="did:pkh:eip155:4217:0x1234...",
)

# Serialize to Authorization header value
auth_header = credential.to_authorization()

# Parse from Authorization header
credential = Credential.from_authorization(header_value)
```

### Receipt

```python
from mpp import Receipt

# Parse from Payment-Receipt header
receipt = Receipt.from_payment_receipt(header_value)

# Serialize to header value
header = receipt.to_payment_receipt()

# Access fields
receipt.challenge_id
receipt.method
receipt.reference
receipt.settlement  # {"amount": "0.01", "currency": "USD"}
receipt.status      # "success"
receipt.timestamp
```

---

## Automatic 402 Handling

The `Client` context manager and the one-off `get` helper already intercept 402 responses and retry with payment credentials automatically. Pass timeout, connection-pool, and proxy options through to the underlying `httpx.AsyncClient` when you need fine-grained control over the HTTP client.
