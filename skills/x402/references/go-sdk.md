# Go SDK Reference

Version: 2.17.0 | Module: `github.com/x402-foundation/x402/go/v2` | Go 1.24+

> **Module path:** as of v2.14.0 the module is `github.com/x402-foundation/x402/go/v2`. The old bare `.../x402/go` path no longer resolves tagged releases (it falls back to pseudo-versions). Update all imports to include `/v2`.

## Recent Additions (v2.8-v2.17)

- **Wallet compatibility (v2.17.0)** - payments verify + settle across plain EOAs, ERC-4337 / ERC-7579 smart accounts, counterfactual ERC-6492 wallets, and ERC-7702-delegated EOAs; pre-verification mirrors on-chain signature checking. ERC-6492 gated by `EIP6492AllowedFactories`.
- **`FacilitatorSupportValidator` hook (v2.17.0)** - resource server fails fast at `Initialize()` when a scheme delegates a capability (e.g. batch-settlement `receiverAuthorizer`) the facilitator does not advertise. Batch-settlement `authorizerSigner` is now optional; missing authorizer signatures error with `ErrAuthorizerNotConfigured` (`invalid_batch_settlement_evm_authorizer_not_configured`).
- **`sign-in-with-x` (v2.16.0)** - Go gains SIWX server + client (`go/v2/extensions/signinwithx`): SIWX storage, auth hooks, EVM EIP-191 sign/verify, HTTP auth retry; also covers undeployed EIP-6492 and SVM. `dynamicInfoFields` capability added.
- **Networks (v2.15.0)** - Mezo mainnet (`eip155:31612`, mUSD 18 decimals), XDC Network (`eip155:50`) and XDC Apothem (`eip155:51`) in EVM default-asset resolution.
- **builder-code (v2.15.0)** - ERC-8021 attribution with `dataSuffix` helpers (`ResolveDataSuffix`, `AppendDataSuffix`, `BuilderCodeFacilitatorExtension`) threaded through all EVM settle paths; multiple service codes (`[]string`).
- **Verify/timing (v2.15.0)** - EVM verify rejects EOA asset addresses (`asset_not_deployed_contract`); authorization `validAfter` set to 0 and default resource-server `maxTimeoutSeconds` raised from 60 to 300.
- **Go module `/v2` path** - module is now `github.com/x402-foundation/x402/go/v2` so consumers resolve tagged releases instead of pseudo-versions (v2.14.0).
- **`builder-code` extension** - Go SDK helper at `go/v2/extensions/buildercode` (ERC-8021 Schema 2 attribution; client/server/facilitator + CBOR).
- **`batch-settlement` scheme** - commit-now / settle-asynchronously EVM mechanism via `go/v2/mechanisms/evm/batch-settlement`.
- **Networks** - ADI Chain (`eip155:36900`) and HPP / HPP Sepolia (`eip155:190415` / `eip155:181228`), plus Radius (`eip155:723487` / `eip155:72344`), in EVM default-asset resolution.
- **Security (v2.13.0)** - ERC-6492 factory-injection fix (`eip6492AllowedFactories` allowlist now the sole gate; `DeployERC4337WithEIP6492` removed); SVM dedup keyed on tx message hash; facilitator HTTP-200 + `isValid:false` now a hard gate failure.
- **`EXTENSION-RESPONSES` header** - decoded and logged by the HTTP facilitator client.
- Echo and `net/http` middleware adapters (documented below) landed in v2.8.0.

## Installation

```bash
go get github.com/x402-foundation/x402/go/v2
```

## Server: Gin

```go
import (
    x402http "github.com/x402-foundation/x402/go/v2/http"
    ginmw "github.com/x402-foundation/x402/go/v2/http/gin"
    evm "github.com/x402-foundation/x402/go/v2/mechanisms/evm/exact/server"
    svm "github.com/x402-foundation/x402/go/v2/mechanisms/svm/exact/server"
)

facilitator := x402http.NewHTTPFacilitatorClient(&x402http.FacilitatorConfig{URL: facilitatorURL})

routes := x402http.RoutesConfig{
    "GET /weather": {
        Accepts: x402http.PaymentOptions{
            {Scheme: "exact", Price: "$0.001", Network: "eip155:84532", PayTo: evmAddress},
            {Scheme: "exact", Price: "$0.001", Network: "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", PayTo: svmAddress},
        },
        Description: "Weather data",
        MimeType:    "application/json",
    },
}

r.Use(ginmw.X402Payment(ginmw.Config{
    Routes:      routes,
    Facilitator: facilitator,
    Schemes: []ginmw.SchemeConfig{
        {Network: "eip155:84532", Server: evm.NewExactEvmScheme()},
        {Network: "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1", Server: svm.NewExactSvmScheme()},
    },
    Timeout: 30 * time.Second,
}))
```

## Server: Echo

```go
import (
    x402http "github.com/x402-foundation/x402/go/v2/http"
    echomw "github.com/x402-foundation/x402/go/v2/http/echo"
    evm "github.com/x402-foundation/x402/go/v2/mechanisms/evm/exact/server"
)

e.Use(echomw.X402Payment(echomw.Config{
    Routes:      routes,
    Facilitator: facilitator,
    Schemes:     []echomw.SchemeConfig{{Network: "eip155:84532", Server: evm.NewExactEvmScheme()}},
}))
```

## Server: net/http (Standard Library)

```go
import (
    x402http "github.com/x402-foundation/x402/go/v2/http"
    nethttpmw "github.com/x402-foundation/x402/go/v2/http/nethttp"
    evm "github.com/x402-foundation/x402/go/v2/mechanisms/evm/exact/server"
)

handler := nethttpmw.X402Payment(nethttpmw.Config{
    Routes:      routes,
    Facilitator: facilitator,
    Schemes:     []nethttpmw.SchemeConfig{{Network: "eip155:84532", Server: evm.NewExactEvmScheme()}},
})(yourHandler)

http.ListenAndServe(":4021", handler)
```

## Client: HTTP

```go
import (
    x402 "github.com/x402-foundation/x402/go/v2"
    x402http "github.com/x402-foundation/x402/go/v2/http"
    evm "github.com/x402-foundation/x402/go/v2/mechanisms/evm/exact/client"
    evmsigners "github.com/x402-foundation/x402/go/v2/signers/evm"
)

client := x402.Newx402Client()
evmSigner, _ := evmsigners.NewClientSignerFromPrivateKey(evmKey)
client.Register("eip155:*", evm.NewExactEvmScheme(evmSigner))

httpClient := x402http.Newx402HTTPClient(client)
wrappedClient := x402http.WrapHTTPClientWithPayment(http.DefaultClient, httpClient)

req, _ := http.NewRequest("GET", "http://localhost:4021/weather", nil)
resp, _ := wrappedClient.Do(req)
```

## Lifecycle Hooks

### Client Hooks

```go
client.OnBeforePaymentCreation(func(ctx context.Context, pc x402.PaymentCreationContext) (*x402.AbortResult, error) {
    return nil, nil // Continue; return &x402.AbortResult{Reason: "blocked"} to abort
})
client.OnAfterPaymentCreation(func(ctx context.Context, pc x402.PaymentCreatedContext) error { return nil })
client.OnPaymentCreationFailure(func(ctx context.Context, fc x402.PaymentCreationFailureContext) (*x402.RecoveredPayloadResult, error) { return nil, nil })
```

### Server Hooks

```go
server.OnBeforeVerify(func(ctx context.Context, vc x402.VerifyContext) (*x402.AbortResult, error) { return nil, nil })
server.OnAfterVerify(func(ctx context.Context, vc x402.VerifyResultContext) error { return nil })
server.OnVerifyFailure(func(ctx context.Context, fc x402.VerifyFailureContext) (*x402.RecoveredVerifyResult, error) { return nil, nil })
server.OnBeforeSettle(func(ctx context.Context, sc x402.SettleContext) (*x402.AbortResult, error) { return nil, nil })
server.OnAfterSettle(func(ctx context.Context, sc x402.SettleResultContext) error { return nil })
server.OnSettleFailure(func(ctx context.Context, fc x402.SettleFailureContext) (*x402.RecoveredSettleResult, error) { return nil, nil })
```

### OnProtectedRequest Hook

```go
httpServer.OnProtectedRequest(func(ctx context.Context, reqCtx x402http.HTTPRequestContext, route x402http.RouteConfig) (*x402http.ProtectedRequestHookResult, error) {
    if apiKey := reqCtx.Headers.Get("X-API-Key"); isValidKey(apiKey) {
        return &x402http.ProtectedRequestHookResult{GrantAccess: true}, nil
    }
    return nil, nil // Continue to payment flow
})
```

### Policies

```go
client := x402.Newx402Client(
    x402.WithPolicy(x402.PreferNetwork("eip155:84532")),
    x402.WithPaymentSelector(customSelector),
)
client.RegisterPolicy(x402.PreferScheme("exact"))
```

## Client Extensions

```go
client.RegisterExtension(myClientExtension) // implements ClientExtension { Key(), EnrichPaymentPayload() }
```

## Dynamic Pricing and PayTo

```go
routes := x402http.RoutesConfig{
    "GET /weather": {
        Accepts: x402http.PaymentOptions{
            {
                Scheme:  "exact",
                Price:   x402http.DynamicPriceFunc(func(ctx context.Context, reqCtx x402http.HTTPRequestContext) (x402.Price, error) {
                    if reqCtx.QueryParams["premium"] == "true" { return "$0.01", nil }
                    return "$0.001", nil
                }),
                Network: "eip155:84532",
                PayTo:   x402http.DynamicPayToFunc(func(ctx context.Context, reqCtx x402http.HTTPRequestContext) (string, error) {
                    return getWalletForRegion(reqCtx), nil
                }),
            },
        },
    },
}
```

## Custom Unpaid Response

```go
"GET /weather": {
    Accepts: paymentOptions,
    UnpaidResponseBody: func(ctx context.Context, reqCtx x402http.HTTPRequestContext) (*x402http.UnpaidResponse, error) {
        return &x402http.UnpaidResponse{
            ContentType: "application/json",
            Body:        map[string]interface{}{"preview": "partial data"},
        }, nil
    },
}
```

## Bazaar Discovery Extension

```go
import "github.com/x402-foundation/x402/go/v2/extensions/bazaar"

Extensions: bazaar.DeclareDiscoveryExtension(bazaar.DiscoveryInfo{
    Output: map[string]interface{}{"type": "json", "example": map[string]interface{}{"weather": "sunny"}},
})

// WithBazaar facilitator client
facilitator := bazaar.WithBazaar(x402http.NewHTTPFacilitatorClient(&x402http.FacilitatorConfig{URL: url}))
resources, _ := facilitator.ListDiscoveryResources(ctx, &bazaar.ListDiscoveryResourcesParams{Type: "http", Limit: 20})
```

## Other Extensions

```go
import "github.com/x402-foundation/x402/go/v2/extensions/paymentidentifier"   // Payment identifier
import "github.com/x402-foundation/x402/go/v2/extensions/eip2612gassponsor"    // EIP-2612 gas sponsor
import "github.com/x402-foundation/x402/go/v2/extensions/erc20approvalgassponsor" // ERC-20 approval gas sponsor
import "github.com/x402-foundation/x402/go/v2/extensions/buildercode"          // builder-code (ERC-8021 attribution)
```

The `buildercode` package exposes `DeclareBuilderCodeExtension` plus client/server/facilitator helpers and CBOR encoding for ERC-8021 Schema 2 attribution.

## Custom PaywallProvider

```go
provider := x402http.NewPaywallBuilder().
    WithNetwork(&x402http.EVMPaywallHandler{}).
    WithNetwork(&x402http.SVMPaywallHandler{}).
    WithConfig(&x402http.PaywallConfig{AppName: "My App", Testnet: false}).
    Build()
server.RegisterPaywallProvider(provider)
```

## MCP Server

```go
import x402mcp "github.com/x402-foundation/x402/go/v2/mcp"

paymentWrapper := x402mcp.NewPaymentWrapper(resourceServer, requirements)

mcpServer.AddTool(
    mcp.NewTool("weather", mcp.WithDescription("Get weather data")),
    paymentWrapper.Wrap(func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
        return mcp.NewToolResultText(`{"weather": "sunny"}`), nil
    }),
)
```

## Facilitator (Self-hosted)

```go
facilitator := x402.Newx402Facilitator()
facilitator.Register([]x402.Network{"eip155:84532"}, evm.NewExactEvmScheme(evmSigner))
facilitator.RegisterExtension(x402.NewFacilitatorExtension("myKey"))

// Verify/Settle accept []byte, auto-detect V1/V2
result, _ := facilitator.Verify(ctx, payloadBytes, requirementsBytes)
result, _ := facilitator.Settle(ctx, payloadBytes, requirementsBytes)
```

## Custom Money Parser

```go
evmScheme := evm.NewExactEvmScheme().RegisterMoneyParser(
    func(amount float64, network x402.Network) (*x402.AssetAmount, error) {
        return &x402.AssetAmount{
            Amount: fmt.Sprintf("%.0f", amount*1e18),
            Asset:  "0xYourTokenAddress",
            Extra:  map[string]interface{}{"assetTransferMethod": "permit2"},
        }, nil
    },
)
```

## Upto Scheme (Usage-Based Billing)

```go
import (
    uptoclient "github.com/x402-foundation/x402/go/v2/mechanisms/evm/upto/client"
    uptoserver "github.com/x402-foundation/x402/go/v2/mechanisms/evm/upto/server"
)

// Server: register upto scheme
server.Register("eip155:84532", uptoserver.NewUptoEvmScheme())

// Route config with scheme "upto" and max price
routes := x402http.RoutesConfig{
    "GET /api/generate": {
        Accepts: x402http.PaymentOptions{
            {Scheme: "upto", Price: "$0.10", Network: "eip155:84532", PayTo: address},
        },
    },
}

// In handler: set actual settlement amount
x402http.SetSettlementOverrides(w, x402http.SettlementOverrides{Amount: "50000"}) // raw atomic units

// Client: register upto scheme
client.Register("eip155:*", uptoclient.NewUptoEvmScheme(evmSigner))
```

## Wildcard Registration

```go
client.
    Register("eip155:*", evm.NewExactEvmScheme(defaultSigner)).     // Fallback for all EVM
    Register("eip155:1", evm.NewExactEvmScheme(mainnetSigner))      // Override for mainnet
```

## Key Import Paths

| Purpose | Import |
|---------|--------|
| Core types | `github.com/x402-foundation/x402/go/v2` |
| HTTP utilities | `github.com/x402-foundation/x402/go/v2/http` |
| Gin middleware | `github.com/x402-foundation/x402/go/v2/http/gin` |
| Echo middleware | `github.com/x402-foundation/x402/go/v2/http/echo` |
| net/http middleware | `github.com/x402-foundation/x402/go/v2/http/nethttp` |
| EVM exact server | `github.com/x402-foundation/x402/go/v2/mechanisms/evm/exact/server` |
| EVM exact client | `github.com/x402-foundation/x402/go/v2/mechanisms/evm/exact/client` |
| EVM exact facilitator | `github.com/x402-foundation/x402/go/v2/mechanisms/evm/exact/facilitator` |
| EVM upto server | `github.com/x402-foundation/x402/go/v2/mechanisms/evm/upto/server` |
| EVM upto client | `github.com/x402-foundation/x402/go/v2/mechanisms/evm/upto/client` |
| EVM upto facilitator | `github.com/x402-foundation/x402/go/v2/mechanisms/evm/upto/facilitator` |
| SVM exact server | `github.com/x402-foundation/x402/go/v2/mechanisms/svm/exact/server` |
| SVM exact client | `github.com/x402-foundation/x402/go/v2/mechanisms/svm/exact/client` |
| EVM signers | `github.com/x402-foundation/x402/go/v2/signers/evm` |
| SVM signers | `github.com/x402-foundation/x402/go/v2/signers/svm` |
| MCP support | `github.com/x402-foundation/x402/go/v2/mcp` |
| Bazaar extension | `github.com/x402-foundation/x402/go/v2/extensions/bazaar` |
| Payment identifier | `github.com/x402-foundation/x402/go/v2/extensions/paymentidentifier` |
| EIP-2612 gas sponsor | `github.com/x402-foundation/x402/go/v2/extensions/eip2612gassponsor` |
| ERC-20 approval sponsor | `github.com/x402-foundation/x402/go/v2/extensions/erc20approvalgassponsor` |
| Builder-code extension | `github.com/x402-foundation/x402/go/v2/extensions/buildercode` |
| Sign-in-with-x extension | `github.com/x402-foundation/x402/go/v2/extensions/signinwithx` |
| Batch-settlement (EVM) | `github.com/x402-foundation/x402/go/v2/mechanisms/evm/batch-settlement` |
