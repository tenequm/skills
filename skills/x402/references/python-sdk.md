# Python SDK Reference

Version: 2.14.0

## Recent Additions (v2.7-v2.14)

- **Wallet compatibility (v2.14.0)** - payments verify + settle across plain EOAs, ERC-4337 / ERC-7579 smart accounts, counterfactual ERC-6492 wallets, and ERC-7702-delegated EOAs; ERC-6492 support in `exact` + `batch-settlement`, gated by `eip6492_allowed_factories`. Batch-settlement `receiver_authorizer_signer` is now optional, with a fail-fast `initialize()` check when the facilitator advertises no usable `receiverAuthorizer`.
- **Networks (v2.13.0)** - Mezo mainnet (`eip155:31612`, mUSD 18 decimals), XDC Network (`eip155:50`) and XDC Apothem (`eip155:51`) in EVM default-asset resolution.
- **Verify guard (v2.13.0)** - EVM verify rejects EOA asset addresses (no bytecode) across EIP-3009 / Permit2 exact / Permit2 upto with `asset_not_deployed_contract`; authorization `validAfter` set to 0; payment-creation failure hooks now run when after-payment hooks raise.
- **SVM client cache (v2.13.1)** - exact SVM client caches mint metadata to avoid repeated mint-account RPC fetches.
- **`upto` scheme** - usage-based EVM billing (client/server/facilitator) via `x402.mechanisms.evm.upto`, added in v2.8.0.
- **`batch-settlement` scheme** - commit-now / settle-asynchronously EVM mechanism via `x402.mechanisms.evm.batch_settlement` (cumulative vouchers, single on-chain claim; `FileChannelStorage`), in v2.11.0.
- **`siwx` (sign-in-with-x) extension** - CAIP-122 wallet auth now available in Python (v2.11.0).
- **Networks** - ADI Chain (`eip155:36900`) and HPP / HPP Sepolia (`eip155:190415` / `eip155:181228`, Bridged USDC) added to EVM default-asset resolution (v2.11.0); plus Radius and Arbitrum earlier.
- **TVM (TON) exact mechanism** - `x402.mechanisms.tvm` for TON testnet/mainnet jetton transfers (Python SDK only), added in v2.10.0.
- **Security (v2.12.0)** - ERC-6492 factory-injection fix (`eip6492_allowed_factories: list[str]` is now the sole gate; empty/omitted disables and returns `eip6492_factory_not_allowed`; `DeployERC4337WithEIP6492` removed); SVM exact dedup keyed on tx message hash (cache-bypass fix).
- **Lifecycle hooks + adapter pattern** - missing lifecycle hooks and extension/scheme-level adapter pattern added (v2.11.0); failure hooks now run after after-hook errors.
- **MCP fixes (v2.12.0)** - client-factory helpers exported from `x402.mcp`; FastMCP `CallToolResult` metadata preserved when attaching payment responses.
- **`EXTENSION-RESPONSES` header** - decoded and logged by the HTTP facilitator client.

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
