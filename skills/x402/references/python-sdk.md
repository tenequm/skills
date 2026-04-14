# Python SDK Reference

Version: 2.6.0

## Installation

```bash
pip install "x402[httpx]"      # Async HTTP client
pip install "x402[requests]"   # Sync HTTP client
pip install "x402[fastapi]"    # FastAPI server
pip install "x402[flask]"      # Flask server
pip install "x402[svm]"        # Solana support
pip install "x402[mcp]"        # MCP integration
pip install "x402[extensions]" # Extensions (bazaar, gas sponsoring, payment-identifier, etc.)
pip install "x402[all]"        # Everything
```

## Server: FastAPI

```python
from fastapi import FastAPI
from x402.http import FacilitatorConfig, HTTPFacilitatorClient, PaymentOption
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http.types import RouteConfig
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.mechanisms.svm.exact import ExactSvmServerScheme
from x402.server import x402ResourceServer

app = FastAPI()

facilitator = HTTPFacilitatorClient(FacilitatorConfig(url="https://x402.org/facilitator"))
server = x402ResourceServer(facilitator)
server.register("eip155:84532", ExactEvmServerScheme())
server.register("solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", ExactSvmServerScheme())

routes = {
    "GET /weather": RouteConfig(
        accepts=[
            PaymentOption(scheme="exact", pay_to="0xAddr", price="$0.001", network="eip155:84532"),
            PaymentOption(scheme="exact", pay_to="SvmAddr", price="$0.001", network="solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1"),
        ],
        mime_type="application/json",
        description="Weather data",
    ),
}

app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

@app.get("/weather")
async def get_weather():
    return {"weather": "sunny", "temperature": 70}
```

Alternative function-based middleware:
```python
from x402.http.middleware.fastapi import payment_middleware

@app.middleware("http")
async def x402_middleware(request, call_next):
    handler = payment_middleware(routes, server)
    return await handler(request, call_next)
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
        accepts=[PaymentOption(scheme="exact", pay_to="0xAddr", price="$0.001", network="eip155:84532")],
        mime_type="application/json",
        description="Weather data",
    ),
}

PaymentMiddleware(app, routes=routes, server=server)

@app.get("/weather")
def get_weather():
    return jsonify({"weather": "sunny", "temperature": 70})
```

## Client: httpx (Async)

```python
from eth_account import Account
from x402 import x402Client
from x402.http import x402HTTPClient
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

client = x402Client()
account = Account.from_key(os.getenv("EVM_PRIVATE_KEY"))
register_exact_evm_client(client, EthAccountSigner(account))

http_client = x402HTTPClient(client)

async with x402HttpxClient(client) as http:
    response = await http.get("http://localhost:4021/weather")
    await response.aread()
    print(response.text)

    settle = http_client.get_payment_settle_response(lambda name: response.headers.get(name))
```

## Client: requests (Sync)

```python
from x402 import x402ClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm.exact.register import register_exact_evm_client_sync

client = x402ClientSync()
register_exact_evm_client_sync(client, EthAccountSigner(account))

session = x402_requests(client)
response = session.get("http://localhost:4021/weather")
```

## Client: Solana Support

```python
from x402.mechanisms.svm import KeypairSigner
from x402.mechanisms.svm.exact.register import register_exact_svm_client

svm_signer = KeypairSigner.from_base58(os.getenv("SVM_PRIVATE_KEY"))
register_exact_svm_client(client, svm_signer)
```

## Lifecycle Hooks

### Client Hooks

```python
client.on_before_payment_creation(lambda ctx: None)    # AbortResult to abort
client.on_after_payment_creation(lambda ctx: None)      # Observe
client.on_payment_creation_failure(lambda ctx: None)    # RecoveredPayloadResult to recover
```

### Server Hooks

```python
server.on_before_verify(lambda ctx: None)    # AbortResult to abort
server.on_after_verify(lambda ctx: None)
server.on_verify_failure(lambda ctx: None)   # RecoveredVerifyResult to recover
server.on_before_settle(lambda ctx: None)
server.on_after_settle(lambda ctx: None)
server.on_settle_failure(lambda ctx: None)   # RecoveredSettleResult to recover
```

### Policies

```python
from x402.client_base import prefer_network, prefer_scheme, max_amount

client.register_policy(prefer_network("eip155:84532"))
client.register_policy(prefer_scheme("exact"))
client.register_policy(max_amount(1000000))
```

## Dynamic Pricing and PayTo

```python
routes = {
    "GET /weather": RouteConfig(
        accepts=[PaymentOption(
            scheme="exact",
            price=lambda ctx: "$0.01" if "premium" in ctx.path else "$0.001",
            pay_to=lambda ctx: get_wallet_for_region(ctx),
            network="eip155:84532",
        )],
    ),
}
```

## Route Response Customization

```python
from x402.http.types import HTTPResponseBody

routes = {
    "GET /weather": RouteConfig(
        accepts=[...],
        unpaid_response_body=lambda ctx: HTTPResponseBody(
            content_type="application/json",
            body={"error": "Payment required", "preview": {"temp": 70}},
        ),
        settlement_failed_response_body=lambda ctx, result: HTTPResponseBody(
            content_type="application/json",
            body={"error": "Settlement failed", "reason": result.error_reason},
        ),
        custom_paywall_html="<html>Custom paywall</html>",
    ),
}
```

## Extensions

### Bazaar Discovery

```python
from x402.extensions.bazaar import bazaar_resource_server_extension

server.register_extension(bazaar_resource_server_extension)

routes = {
    "GET /weather": RouteConfig(
        accepts=[...],
        extensions={"bazaar": {"output": {"type": "json", "example": {"weather": "sunny"}}}},
    ),
}
```

## Extensions: Gas Sponsoring

```python
from x402.extensions.eip2612_gas_sponsoring import declare_eip2612_gas_sponsoring_extension
from x402.extensions.erc20_approval_gas_sponsoring import declare_erc20_approval_gas_sponsoring_extension

# EIP-2612 gas sponsoring
extensions = declare_eip2612_gas_sponsoring_extension()

# ERC-20 approval gas sponsoring
extensions = declare_erc20_approval_gas_sponsoring_extension()
```

## Extensions: Payment Identifier

```python
from x402.extensions.payment_identifier import declare_payment_identifier_extension

extensions = declare_payment_identifier_extension(required=False)
```

## MCP Server

```python
from x402.mcp import create_payment_wrapper, PaymentWrapperConfig

paid = create_payment_wrapper(resource_server, PaymentWrapperConfig(accepts=accepts))

@mcp_server.tool("financial_analysis", "Financial analysis", schema)
@paid
def handler(args, context):
    return {"content": [{"type": "text", "text": "Analysis result"}]}
```

Async variant: `from x402.mcp.server_async import create_payment_wrapper`

## MCP Client

```python
from x402.mcp import create_x402_mcp_client_from_config

x402_mcp = create_x402_mcp_client_from_config(mcp_client, {
    "schemes": [{"network": "eip155:84532", "client": ExactEvmClientScheme(signer)}],
    "auto_payment": True,
})
result = x402_mcp.call_tool("get_weather", {"city": "NYC"})
```

Async: `from x402.mcp.client_async import x402MCPClient`

## Facilitator (Self-hosted)

```python
from x402.facilitator import x402Facilitator, x402FacilitatorSync
from x402.mechanisms.evm.exact.facilitator import ExactEvmFacilitatorScheme

facilitator = x402Facilitator()
facilitator.register(["eip155:84532"], ExactEvmFacilitatorScheme(signer))
facilitator.register_extension(my_extension)

result = await facilitator.verify(payload_bytes, requirements_bytes)
result = await facilitator.settle(payload_bytes, requirements_bytes)
```

## Facilitator Client Auth

```python
from x402.http.facilitator_client_base import AuthProvider, AuthHeaders, FacilitatorConfig

class MyAuth:
    def get_auth_headers(self) -> AuthHeaders:
        return AuthHeaders(
            verify={"Authorization": "Bearer ..."},
            settle={"Authorization": "Bearer ..."},
            supported={"Authorization": "Bearer ..."},
        )

facilitator = HTTPFacilitatorClient(FacilitatorConfig(url="...", auth_provider=MyAuth()))
```

## Custom Pricing with AssetAmount

```python
from x402.schemas import AssetAmount

PaymentOption(
    scheme="exact",
    pay_to="0xAddr",
    price=AssetAmount(amount="10000", asset="0x036CbD...", extra={"name": "USDC", "version": "2"}),
    network="eip155:84532",
)
```

## Async/Sync Duality

| Async | Sync |
|-------|------|
| `x402Client` | `x402ClientSync` |
| `x402ResourceServer` | `x402ResourceServerSync` |
| `x402Facilitator` | `x402FacilitatorSync` |
| `HTTPFacilitatorClient` | `HTTPFacilitatorClientSync` |
| `x402HTTPClient` | `x402HTTPClientSync` |
| `x402HTTPResourceServer` | `x402HTTPResourceServerSync` |

FastAPI middleware uses async variants. Flask middleware uses sync variants.

## Key Import Paths

| Purpose | Import |
|---------|--------|
| Core client | `from x402 import x402Client` |
| Core client (sync) | `from x402 import x402ClientSync` |
| Resource server | `from x402.server import x402ResourceServer` |
| Resource server (sync) | `from x402.server import x402ResourceServerSync` |
| Facilitator | `from x402.facilitator import x402Facilitator` |
| HTTP facilitator client | `from x402.http import HTTPFacilitatorClient, FacilitatorConfig` |
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
| MCP payment wrapper | `from x402.mcp import create_payment_wrapper, PaymentWrapperConfig` |
| MCP client factory | `from x402.mcp import create_x402_mcp_client_from_config` |
| Bazaar extension | `from x402.extensions.bazaar import bazaar_resource_server_extension` |
| Schemas | `from x402.schemas import Network, AssetAmount` |
| Policies | `from x402.client_base import prefer_network, prefer_scheme, max_amount` |
