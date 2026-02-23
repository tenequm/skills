# Python SDK Reference

## Installation

```bash
# Core + async HTTP client
pip install "x402[httpx]"

# Core + sync HTTP client
pip install "x402[requests]"

# FastAPI server
pip install "x402[fastapi]"

# Flask server
pip install "x402[flask]"

# Solana support
pip install "x402[svm]"

# All EVM + SVM + FastAPI
pip install "x402[fastapi,evm,svm]"
```

## Server: FastAPI

```python
import os
from fastapi import FastAPI
from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.mechanisms.svm.exact import ExactSvmServerScheme
from x402.schemas import Network
from x402.server import x402ResourceServer

app = FastAPI()

EVM_ADDRESS = os.getenv("EVM_ADDRESS")
SVM_ADDRESS = os.getenv("SVM_ADDRESS")
EVM_NETWORK: Network = "eip155:84532"
SVM_NETWORK: Network = "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1"
FACILITATOR_URL = os.getenv("FACILITATOR_URL", "https://x402.org/facilitator")

# Create resource server
facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=FACILITATOR_URL))
server = x402ResourceServer(facilitator)
server.register(EVM_NETWORK, ExactEvmServerScheme())
server.register(SVM_NETWORK, ExactSvmServerScheme())

# Define paid routes
routes: dict[str, RouteConfig] = {
    "GET /weather": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                pay_to=EVM_ADDRESS,
                price="$0.001",
                network=EVM_NETWORK,
            ),
            PaymentOption(
                scheme="exact",
                pay_to=SVM_ADDRESS,
                price="$0.001",
                network=SVM_NETWORK,
            ),
        ],
        mime_type="application/json",
        description="Weather data",
    ),
    "GET /premium/*": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                pay_to=EVM_ADDRESS,
                price="$0.01",
                network=EVM_NETWORK,
            ),
        ],
        mime_type="application/json",
        description="Premium content",
    ),
}

app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)


@app.get("/weather")
async def get_weather():
    return {"report": {"weather": "sunny", "temperature": 70}}


@app.get("/premium/content")
async def get_premium_content():
    return {"content": "Premium data here"}
```

## Server: Flask

```python
from flask import Flask, jsonify
from x402.http import FacilitatorConfig, HTTPFacilitatorClientSync, PaymentOption
from x402.http.middleware.flask import PaymentMiddleware
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServerSync

app = Flask(__name__)

facilitator = HTTPFacilitatorClientSync(FacilitatorConfig(url="https://x402.org/facilitator"))
server = x402ResourceServerSync(facilitator)
server.register("eip155:84532", ExactEvmServerScheme())

routes = {
    "GET /weather": RouteConfig(
        accepts=[
            PaymentOption(scheme="exact", pay_to="0xYourAddress", price="$0.001", network="eip155:84532"),
        ],
        mime_type="application/json",
        description="Weather data",
    ),
}

app.wsgi_app = PaymentMiddleware(app.wsgi_app, routes=routes, server=server)


@app.get("/weather")
def get_weather():
    return jsonify({"weather": "sunny", "temperature": 70})
```

## Client: httpx (Async)

```python
import asyncio
import os
from eth_account import Account
from x402 import x402Client
from x402.http import x402HTTPClient
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client


async def main():
    client = x402Client()

    # Register EVM scheme
    account = Account.from_key(os.getenv("EVM_PRIVATE_KEY"))
    register_exact_evm_client(client, EthAccountSigner(account))

    http_client = x402HTTPClient(client)

    async with x402HttpxClient(client) as http:
        response = await http.get("http://localhost:4021/weather")
        await response.aread()

        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")

        if response.is_success:
            settle_response = http_client.get_payment_settle_response(
                lambda name: response.headers.get(name)
            )
            print(f"Settlement: {settle_response.model_dump_json(indent=2)}")


asyncio.run(main())
```

## Client: requests (Sync)

```python
import os
from eth_account import Account
from x402 import x402ClientSync
from x402.http import x402HTTPClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client_sync

client = x402ClientSync()
account = Account.from_key(os.getenv("EVM_PRIVATE_KEY"))
register_exact_evm_client_sync(client, EthAccountSigner(account))

session = x402_requests(client)
response = session.get("http://localhost:4021/weather")

print(f"Status: {response.status_code}")
print(f"Body: {response.text}")
```

## Client: Solana Support

```python
from x402 import x402Client
from x402.mechanisms.svm import KeypairSigner
from x402.mechanisms.svm.exact.register import register_exact_svm_client

client = x402Client()

# From base58 private key
svm_signer = KeypairSigner.from_base58(os.getenv("SVM_PRIVATE_KEY"))
register_exact_svm_client(client, svm_signer)

print(f"Solana address: {svm_signer.address}")
```

## MCP Server

```python
from x402 import x402ResourceServerSync
from x402.mcp import create_payment_wrapper, PaymentWrapperConfig, PaymentWrapperHooks

# Create resource server
facilitator_client = # ... HTTPFacilitatorClientSync(...)
resource_server = x402ResourceServerSync(facilitator_client)
resource_server.register("eip155:84532", evm_server_scheme)

# Build payment requirements
accepts = resource_server.build_payment_requirements_from_config({
    "scheme": "exact",
    "network": "eip155:84532",
    "pay_to": "0xYourAddress",
    "price": "$0.10",
})

# Create payment wrapper with optional hooks
paid = create_payment_wrapper(
    resource_server,
    PaymentWrapperConfig(
        accepts=accepts,
        hooks=PaymentWrapperHooks(
            on_before_execution=lambda ctx: True,   # Return False to abort
            on_after_execution=lambda ctx: None,
            on_after_settlement=lambda ctx: None,
        ),
    ),
)

# Wrap MCP tool handler
@mcp_server.tool("financial_analysis", "Financial analysis", schema)
@paid
def handler(args, context):
    return {"content": [{"type": "text", "text": "Analysis result"}]}
```

## MCP Client

```python
from x402.mcp import create_x402_mcp_client_from_config
from x402.mechanisms.evm.exact import ExactEvmClientScheme

# Create MCP client (from MCP SDK)
mcp_client = # ... create MCP client

# Create x402 MCP client with config
x402_mcp = create_x402_mcp_client_from_config(
    mcp_client,
    {
        "schemes": [
            {"network": "eip155:84532", "client": ExactEvmClientScheme(signer)},
        ],
        "auto_payment": True,
        "on_payment_requested": lambda ctx: True,  # Auto-approve
    },
)

# Call tools - payment handled automatically
result = x402_mcp.call_tool("get_weather", {"city": "NYC"})
```

### Alternative: Wrap Existing Client

```python
from x402 import x402ClientSync
from x402.mcp import wrap_mcp_client_with_payment

payment_client = x402ClientSync()
payment_client.register("eip155:84532", evm_client_scheme)

x402_mcp = wrap_mcp_client_with_payment(
    mcp_client,
    payment_client,
    auto_payment=True,
)
```

### MCP Error Utilities

```python
from x402.mcp import (
    create_payment_required_error,
    is_payment_required_error,
    extract_payment_required_from_error,
    MCP_PAYMENT_REQUIRED_CODE,      # 402
    MCP_PAYMENT_META_KEY,            # "x402/payment"
    MCP_PAYMENT_RESPONSE_META_KEY,   # "x402/payment-response"
)

# Server: raise payment required
error = create_payment_required_error(payment_required, "Payment required")
raise error

# Client: detect and extract
if is_payment_required_error(error):
    pr = extract_payment_required_from_error(json_rpc_error)
```

## Custom Pricing with AssetAmount

```python
from x402.schemas import AssetAmount

routes = {
    "GET /premium": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                pay_to="0xYourAddress",
                price=AssetAmount(
                    amount="10000",  # Atomic units (0.01 USDC)
                    asset="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
                    extra={"name": "USDC", "version": "2"},
                ),
                network="eip155:84532",
            ),
        ],
        description="Premium content",
    ),
}
```

## Key Import Paths

| Purpose | V2 Import |
|---------|-----------|
| Core client | `from x402 import x402Client` |
| Core client (sync) | `from x402 import x402ClientSync` |
| Resource server | `from x402.server import x402ResourceServer` |
| Resource server (sync) | `from x402.server import x402ResourceServerSync` |
| HTTP facilitator | `from x402.http import HTTPFacilitatorClient, FacilitatorConfig` |
| FastAPI middleware | `from x402.http.middleware.fastapi import PaymentMiddlewareASGI` |
| Flask middleware | `from x402.http.middleware.flask import PaymentMiddleware` |
| Route config | `from x402.http.types import RouteConfig` |
| Payment option | `from x402.http import PaymentOption` |
| EVM server scheme | `from x402.mechanisms.evm.exact import ExactEvmServerScheme` |
| EVM client register | `from x402.mechanisms.evm.exact.register import register_exact_evm_client` |
| EVM signer | `from x402.mechanisms.evm import EthAccountSigner` |
| SVM server scheme | `from x402.mechanisms.svm.exact import ExactSvmServerScheme` |
| SVM client register | `from x402.mechanisms.svm.exact.register import register_exact_svm_client` |
| SVM signer | `from x402.mechanisms.svm import KeypairSigner` |
| httpx client | `from x402.http.clients import x402HttpxClient` |
| requests client | `from x402.http.clients import x402_requests` |
| HTTP client wrapper | `from x402.http import x402HTTPClient` |
| HTTP client wrapper (sync) | `from x402.http import x402HTTPClientSync` |
| HTTP facilitator (sync) | `from x402.http import HTTPFacilitatorClientSync` |
| Schemas | `from x402.schemas import Network, AssetAmount` |
| MCP payment wrapper | `from x402.mcp import create_payment_wrapper, PaymentWrapperConfig` |
| MCP client factory | `from x402.mcp import create_x402_mcp_client_from_config` |
| MCP client wrap | `from x402.mcp import wrap_mcp_client_with_payment` |
| MCP error utils | `from x402.mcp import create_payment_required_error, is_payment_required_error` |
