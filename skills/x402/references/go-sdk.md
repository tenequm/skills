# Go SDK Reference

Version: 2.7.0 | Module: `github.com/x402-foundation/x402/go` | Go 1.24+

## Installation

```bash
go get github.com/x402-foundation/x402/go
```

## Server: Gin

```go
import (
    x402http "github.com/x402-foundation/x402/go/http"
    ginmw "github.com/x402-foundation/x402/go/http/gin"
    evm "github.com/x402-foundation/x402/go/mechanisms/evm/exact/server"
    svm "github.com/x402-foundation/x402/go/mechanisms/svm/exact/server"
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
    x402http "github.com/x402-foundation/x402/go/http"
    echomw "github.com/x402-foundation/x402/go/http/echo"
    evm "github.com/x402-foundation/x402/go/mechanisms/evm/exact/server"
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
    x402http "github.com/x402-foundation/x402/go/http"
    nethttpmw "github.com/x402-foundation/x402/go/http/nethttp"
    evm "github.com/x402-foundation/x402/go/mechanisms/evm/exact/server"
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
    x402 "github.com/x402-foundation/x402/go"
    x402http "github.com/x402-foundation/x402/go/http"
    evm "github.com/x402-foundation/x402/go/mechanisms/evm/exact/client"
    evmsigners "github.com/x402-foundation/x402/go/signers/evm"
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
import "github.com/x402-foundation/x402/go/extensions/bazaar"

Extensions: bazaar.DeclareDiscoveryExtension(bazaar.DiscoveryInfo{
    Output: map[string]interface{}{"type": "json", "example": map[string]interface{}{"weather": "sunny"}},
})

// WithBazaar facilitator client
facilitator := bazaar.WithBazaar(x402http.NewHTTPFacilitatorClient(&x402http.FacilitatorConfig{URL: url}))
resources, _ := facilitator.ListDiscoveryResources(ctx, &bazaar.ListDiscoveryResourcesParams{Type: "http", Limit: 20})
```

## Other Extensions

```go
import "github.com/x402-foundation/x402/go/extensions/paymentidentifier"   // Payment identifier
import "github.com/x402-foundation/x402/go/extensions/eip2612gassponsor"    // EIP-2612 gas sponsor
import "github.com/x402-foundation/x402/go/extensions/erc20approvalgassponsor" // ERC-20 approval gas sponsor
```

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
import x402mcp "github.com/x402-foundation/x402/go/mcp"

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
    uptoclient "github.com/x402-foundation/x402/go/mechanisms/evm/upto/client"
    uptoserver "github.com/x402-foundation/x402/go/mechanisms/evm/upto/server"
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
| Core types | `github.com/x402-foundation/x402/go` |
| HTTP utilities | `github.com/x402-foundation/x402/go/http` |
| Gin middleware | `github.com/x402-foundation/x402/go/http/gin` |
| Echo middleware | `github.com/x402-foundation/x402/go/http/echo` |
| net/http middleware | `github.com/x402-foundation/x402/go/http/nethttp` |
| EVM exact server | `github.com/x402-foundation/x402/go/mechanisms/evm/exact/server` |
| EVM exact client | `github.com/x402-foundation/x402/go/mechanisms/evm/exact/client` |
| EVM exact facilitator | `github.com/x402-foundation/x402/go/mechanisms/evm/exact/facilitator` |
| EVM upto server | `github.com/x402-foundation/x402/go/mechanisms/evm/upto/server` |
| EVM upto client | `github.com/x402-foundation/x402/go/mechanisms/evm/upto/client` |
| EVM upto facilitator | `github.com/x402-foundation/x402/go/mechanisms/evm/upto/facilitator` |
| SVM exact server | `github.com/x402-foundation/x402/go/mechanisms/svm/exact/server` |
| SVM exact client | `github.com/x402-foundation/x402/go/mechanisms/svm/exact/client` |
| EVM signers | `github.com/x402-foundation/x402/go/signers/evm` |
| SVM signers | `github.com/x402-foundation/x402/go/signers/svm` |
| MCP support | `github.com/x402-foundation/x402/go/mcp` |
| Bazaar extension | `github.com/x402-foundation/x402/go/extensions/bazaar` |
| Payment identifier | `github.com/x402-foundation/x402/go/extensions/paymentidentifier` |
| EIP-2612 gas sponsor | `github.com/x402-foundation/x402/go/extensions/eip2612gassponsor` |
| ERC-20 approval sponsor | `github.com/x402-foundation/x402/go/extensions/erc20approvalgassponsor` |
