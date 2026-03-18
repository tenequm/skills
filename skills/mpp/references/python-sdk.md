# pympp Python SDK

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
- With `[tempo]`: `eth-account`, `web3`

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
        currency="0x20c0000000000000000000000000000000000000",
        recipient="0xYourAddress",
        intents={"charge": ChargeIntent()},
    ),
)
```

### Charge Endpoint

`mpp.charge()` returns either a `Challenge` (payment needed) or a `(credential, receipt)` tuple (payment verified):

```python
@app.get("/resource")
async def get_resource(request: Request):
    result = await mpp.charge(
        authorization=request.headers.get("Authorization"),
        amount="0.50",
    )

    if isinstance(result, Challenge):
        return JSONResponse(
            status_code=402,
            content={"error": "Payment required"},
            headers={
                "WWW-Authenticate": result.to_www_authenticate(mpp.realm),
            },
        )

    credential, receipt = result
    return JSONResponse(
        content={"data": "paid content"},
        headers={
            "Payment-Receipt": receipt.to_payment_receipt(),
        },
    )
```

### Full FastAPI Example

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mpp import Challenge
from mpp.server import Mpp
from mpp.methods.tempo import tempo, ChargeIntent

app = FastAPI()
mpp = Mpp.create(
    method=tempo(
        currency="0x20c0000000000000000000000000000000000000",
        recipient="0xYourAddress",
        intents={"charge": ChargeIntent()},
    ),
)

@app.get("/api/data")
async def get_data(request: Request):
    result = await mpp.charge(
        authorization=request.headers.get("Authorization"),
        amount="0.10",
    )
    if isinstance(result, Challenge):
        return JSONResponse(
            status_code=402,
            content={"error": "Payment required"},
            headers={"WWW-Authenticate": result.to_www_authenticate(mpp.realm)},
        )
    credential, receipt = result
    return JSONResponse(
        content={"data": "premium content", "payer": credential.source},
        headers={"Payment-Receipt": receipt.to_payment_receipt()},
    )

@app.get("/api/free")
async def get_free():
    return {"data": "free content"}
```

---

## Client

### Async Client

The client is an async context manager that wraps `httpx.AsyncClient` with automatic 402 handling:

```python
from eth_account import Account
from mpp.client import Client
from mpp.methods.tempo import tempo, ChargeIntent

account = Account.from_key("0xYourPrivateKey")

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

## Payment Sessions (Streaming)

### StreamMethod

Use `StreamMethod` for session-based payment channels that support streaming:

```python
from mpp.methods.tempo import StreamMethod

method = StreamMethod(
    account=account,
    currency="0x20c0000000000000000000000000000000000000",
    deposit="1.00",  # max tokens locked in escrow
)
```

### PaymentTransport

`PaymentTransport` wraps any `httpx.AsyncBaseTransport` to inject payment credentials:

```python
import httpx
from mpp.transport import PaymentTransport

transport = PaymentTransport(methods=[method])

async with httpx.AsyncClient(transport=transport) as client:
    async with client.stream("GET", "https://api.example.com/stream") as response:
        async for line in response.aiter_lines():
            print(line)
```

### Full Streaming Example

```python
import httpx
from eth_account import Account
from mpp.methods.tempo import StreamMethod
from mpp.transport import PaymentTransport

account = Account.from_key("0xYourPrivateKey")

method = StreamMethod(
    account=account,
    currency="0x20c0000000000000000000000000000000000000",
    deposit="1.00",
)

transport = PaymentTransport(methods=[method])

async with httpx.AsyncClient(transport=transport) as client:
    # First request opens the payment channel on-chain
    async with client.stream("GET", "https://api.example.com/stream") as response:
        async for line in response.aiter_lines():
            # Each line is charged against the session balance
            print(line)

    # Subsequent requests use off-chain vouchers
    async with client.stream("GET", "https://api.example.com/stream") as response:
        async for line in response.aiter_lines():
            print(line)

    # Close the channel when done
    await method.close()
```

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

## Custom httpx Transport

`PaymentTransport` wraps any `httpx.AsyncBaseTransport`, intercepting 402 responses and automatically retrying with payment credentials:

```python
import httpx
from mpp.transport import PaymentTransport
from mpp.methods.tempo import tempo, ChargeIntent

# Wrap the default transport
transport = PaymentTransport(
    methods=[tempo(account=account, intents={"charge": ChargeIntent()})],
)

# Use with any httpx.AsyncClient
async with httpx.AsyncClient(transport=transport, base_url="https://api.example.com") as client:
    res = await client.get("/data")
    print(res.json())
```

This is useful when you need fine-grained control over the HTTP client (timeouts, connection pooling, proxies) while still getting automatic payment handling.
