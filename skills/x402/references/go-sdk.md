# Go SDK Reference

## Installation

```bash
go get github.com/coinbase/x402/go
```

Module: `github.com/coinbase/x402/go`

## Server: Gin

```go
package main

import (
    "net/http"
    "os"
    "time"

    x402http "github.com/coinbase/x402/go/http"
    ginmw "github.com/coinbase/x402/go/http/gin"
    evm "github.com/coinbase/x402/go/mechanisms/evm/exact/server"
    svm "github.com/coinbase/x402/go/mechanisms/svm/exact/server"
    ginfw "github.com/gin-gonic/gin"
)

func main() {
    evmAddress := os.Getenv("EVM_PAYEE_ADDRESS")
    svmAddress := os.Getenv("SVM_PAYEE_ADDRESS")
    facilitatorURL := os.Getenv("FACILITATOR_URL")

    r := ginfw.Default()

    facilitator := x402http.NewHTTPFacilitatorClient(&x402http.FacilitatorConfig{
        URL: facilitatorURL,
    })

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

    r.GET("/weather", func(c *ginfw.Context) {
        c.JSON(http.StatusOK, ginfw.H{"weather": "sunny", "temperature": 70})
    })

    r.GET("/health", func(c *ginfw.Context) {
        c.JSON(http.StatusOK, ginfw.H{"status": "ok"})
    })

    r.Run(":4021")
}
```

## Client: HTTP

```go
package main

import (
    "fmt"
    "io"
    "net/http"
    "os"

    x402 "github.com/coinbase/x402/go"
    x402http "github.com/coinbase/x402/go/http"
    evm "github.com/coinbase/x402/go/mechanisms/evm/exact/client"
    svm "github.com/coinbase/x402/go/mechanisms/svm/exact/client"
    evmsigners "github.com/coinbase/x402/go/signers/evm"
    svmsigners "github.com/coinbase/x402/go/signers/svm"
)

func main() {
    evmKey := os.Getenv("EVM_PRIVATE_KEY")
    svmKey := os.Getenv("SVM_PRIVATE_KEY")

    // Create x402 client
    client := x402.Newx402Client()

    // Register EVM scheme
    evmSigner, _ := evmsigners.NewClientSignerFromPrivateKey(evmKey)
    client.Register("eip155:*", evm.NewExactEvmScheme(evmSigner))

    // Register Solana scheme (optional)
    if svmKey != "" {
        svmSigner, _ := svmsigners.NewClientSignerFromPrivateKey(svmKey)
        client.Register("solana:*", svm.NewExactSvmScheme(svmSigner))
    }

    // Wrap HTTP client with payment handling
    httpClient := x402http.Newx402HTTPClient(client)
    wrappedClient := x402http.WrapHTTPClientWithPayment(http.DefaultClient, httpClient)

    // Make request - payment handled automatically
    req, _ := http.NewRequest("GET", "http://localhost:4021/weather", nil)
    resp, _ := wrappedClient.Do(req)
    defer resp.Body.Close()

    body, _ := io.ReadAll(resp.Body)
    fmt.Println("Response:", string(body))
}
```

## MCP Server

```go
package main

import (
    "context"
    "encoding/json"

    x402 "github.com/coinbase/x402/go"
    x402http "github.com/coinbase/x402/go/http"
    x402mcp "github.com/coinbase/x402/go/mcp"
    evm "github.com/coinbase/x402/go/mechanisms/evm/exact/server"
    "github.com/modelcontextprotocol/go-sdk/mcp"
    "github.com/modelcontextprotocol/go-sdk/server"
)

func main() {
    facilitator := x402http.NewHTTPFacilitatorClient(&x402http.FacilitatorConfig{
        URL: "https://x402.org/facilitator",
    })

    resourceServer := x402.NewResourceServer(facilitator)
    resourceServer.Register("eip155:84532", evm.NewExactEvmScheme())

    requirements, _ := resourceServer.BuildPaymentRequirementsFromConfig([]x402http.PaymentOption{
        {Scheme: "exact", Price: "$0.001", Network: "eip155:84532", PayTo: payTo},
    })

    paymentWrapper := x402mcp.NewPaymentWrapper(resourceServer, requirements)

    mcpServer := server.NewMCPServer("My Paid MCP", "1.0.0")
    mcpServer.AddTool(
        mcp.NewTool("weather", mcp.WithDescription("Get weather data")),
        paymentWrapper.Wrap(func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
            data, _ := json.Marshal(map[string]interface{}{"weather": "sunny", "temperature": 70})
            return mcp.NewToolResultText(string(data)), nil
        }),
    )

    // Start SSE server
    sseServer := server.NewSSEServer(mcpServer)
    sseServer.Start(":4022")
}
```

## Advanced: Dynamic Pricing

```go
routes := x402http.RoutesConfig{
    "GET /weather": {
        Accepts: x402http.PaymentOptions{
            {
                Scheme:  "exact",
                Price:   x402http.DynamicPriceFunc(func(r *http.Request) string {
                    if r.URL.Query().Get("premium") == "true" {
                        return "$0.01"
                    }
                    return "$0.001"
                }),
                Network: "eip155:84532",
                PayTo:   evmAddress,
            },
        },
    },
}
```

## Advanced: Dynamic PayTo

```go
routes := x402http.RoutesConfig{
    "GET /weather": {
        Accepts: x402http.PaymentOptions{
            {
                Scheme:  "exact",
                Price:   "$0.001",
                Network: "eip155:84532",
                PayTo: x402http.DynamicPayToFunc(func(r *http.Request) string {
                    // Route payments to different wallets
                    return getWalletForRegion(r)
                }),
            },
        },
    },
}
```

## Advanced: Bazaar Discovery Extension

```go
import "github.com/coinbase/x402/go/extensions/bazaar"

routes := x402http.RoutesConfig{
    "GET /weather": {
        Accepts: x402http.PaymentOptions{
            {Scheme: "exact", Price: "$0.001", Network: "eip155:84532", PayTo: evmAddress},
        },
        Description: "Weather API",
        MimeType:    "application/json",
        Extensions: bazaar.DeclareDiscoveryExtension(bazaar.DiscoveryInfo{
            Output: map[string]interface{}{
                "type":    "json",
                "example": map[string]interface{}{"weather": "sunny", "temperature": 70},
            },
        }),
    },
}
```

## Facilitator (Self-hosted)

```go
package main

import (
    "github.com/gin-gonic/gin"
    x402 "github.com/coinbase/x402/go"
    evm "github.com/coinbase/x402/go/mechanisms/evm/exact/facilitator"
)

func main() {
    facilitator := x402.Newx402Facilitator()
    facilitator.Register("eip155:84532", evm.NewExactEvmScheme(evmFacilitatorSigner))

    r := gin.Default()

    r.GET("/supported", func(c *gin.Context) {
        supported, _ := facilitator.Supported(c.Request.Context())
        c.JSON(200, supported)
    })

    r.POST("/verify", func(c *gin.Context) {
        var req struct {
            PaymentPayload      json.RawMessage `json:"paymentPayload"`
            PaymentRequirements json.RawMessage `json:"paymentRequirements"`
        }
        c.BindJSON(&req)
        result, _ := facilitator.Verify(c.Request.Context(), req.PaymentPayload, req.PaymentRequirements)
        c.JSON(200, result)
    })

    r.POST("/settle", func(c *gin.Context) {
        var req struct {
            PaymentPayload      json.RawMessage `json:"paymentPayload"`
            PaymentRequirements json.RawMessage `json:"paymentRequirements"`
        }
        c.BindJSON(&req)
        result, _ := facilitator.Settle(c.Request.Context(), req.PaymentPayload, req.PaymentRequirements)
        c.JSON(200, result)
    })

    r.Run(":4022")
}
```

Facilitator signers require RPC connectivity and gas for settlement. See `e2e/facilitators/go/main.go` in the x402 repo for a complete implementation.

## Advanced: Custom Money Parser

Use alternative tokens by registering a custom money parser:

```go
evmScheme := evm.NewExactEvmScheme().RegisterMoneyParser(
    func(amount float64, network x402.Network) (*x402.AssetAmount, error) {
        if amount > 100 {
            return &x402.AssetAmount{
                Amount: fmt.Sprintf("%.0f", amount*1e18),
                Asset:  "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb", // DAI
                Extra:  map[string]interface{}{"token": "DAI"},
            }, nil
        }
        return nil, nil // Use default USDC for small amounts
    },
)
```

## Advanced: Wildcard Registration Precedence

More specific registrations override wildcards:

```go
client.
    Register("eip155:*", evm.NewExactEvmScheme(defaultSigner)).     // Fallback for all EVM
    Register("eip155:1", evm.NewExactEvmScheme(mainnetSigner))      // Override for mainnet
```

## Advanced: OnProtectedRequest Hook

Pre-payment interception hook. Called on every request to a protected route before payment processing. Use for API key bypass, rate limiting, CORS preflight, or custom access control.

```go
import x402http "github.com/coinbase/x402/go/http"

// Grant free access based on custom logic (e.g., API key, CORS preflight)
server.OnProtectedRequest(func(
    ctx context.Context,
    reqCtx x402http.HTTPRequestContext,
    routeConfig x402http.RouteConfig,
) (*x402http.ProtectedRequestHookResult, error) {
    // Bypass payment for OPTIONS requests
    if reqCtx.Method == "OPTIONS" {
        return &x402http.ProtectedRequestHookResult{GrantAccess: true}, nil
    }
    // Bypass payment for valid API keys
    if apiKey := reqCtx.Headers.Get("X-API-Key"); isValidKey(apiKey) {
        return &x402http.ProtectedRequestHookResult{GrantAccess: true}, nil
    }
    return nil, nil // Continue to payment flow
})

// Deny access
server.OnProtectedRequest(func(
    ctx context.Context,
    reqCtx x402http.HTTPRequestContext,
    routeConfig x402http.RouteConfig,
) (*x402http.ProtectedRequestHookResult, error) {
    if isBlocked(reqCtx) {
        return &x402http.ProtectedRequestHookResult{
            Abort: true, Reason: "Access denied",
        }, nil
    }
    return nil, nil
})
```

Hook result semantics:
- Return `nil` - no opinion, continue to next hook or payment flow
- `GrantAccess: true` - bypass payment, grant free access
- `Abort: true` - return 403 Forbidden with `Reason`
- Multiple hooks execute in registration order; first non-nil result wins

## Advanced: WithBazaar Facilitator Client

Wraps `HTTPFacilitatorClient` to add bazaar discovery queries. Preserves all original capabilities (Verify, Settle, GetSupported).

```go
import (
    x402http "github.com/coinbase/x402/go/http"
    "github.com/coinbase/x402/go/extensions/bazaar"
)

// Create bazaar-enabled facilitator client
facilitator := bazaar.WithBazaar(
    x402http.NewHTTPFacilitatorClient(&x402http.FacilitatorConfig{URL: facilitatorURL}),
)

// List all discovered resources
resources, err := facilitator.ListDiscoveryResources(ctx, nil)

// List with filtering and pagination
resources, err := facilitator.ListDiscoveryResources(ctx, &bazaar.ListDiscoveryResourcesParams{
    Type:   "http",
    Limit:  20,
    Offset: 0,
})

for _, r := range resources.Items {
    fmt.Printf("Resource: %s (Type: %s, Version: %d)\n", r.Resource, r.Type, r.X402Version)
}
fmt.Printf("Total: %d\n", resources.Pagination.Total)
```

## Advanced: Custom PaywallProvider

Pluggable HTML generation for browser-facing 402 responses. Three priority levels:
1. Per-route `CustomPaywallHTML` in RouteConfig (highest)
2. Registered `PaywallProvider` (via `RegisterPaywallProvider`)
3. Built-in EVM/SVM templates (default fallback)

```go
import x402http "github.com/coinbase/x402/go/http"

// Option 1: Custom provider implementation
type MyPaywall struct{}

func (p *MyPaywall) GenerateHTML(
    paymentRequired types.PaymentRequired,
    config *x402http.PaywallConfig,
) string {
    return "<html>Custom paywall for " + config.AppName + "</html>"
}

server.RegisterPaywallProvider(&MyPaywall{})

// Option 2: Compose network-specific handlers with PaywallBuilder
provider := x402http.NewPaywallBuilder().
    WithNetwork(&x402http.EVMPaywallHandler{}).
    WithNetwork(&x402http.SVMPaywallHandler{}).
    WithConfig(&x402http.PaywallConfig{
        AppName: "My App",
        AppLogo: "https://example.com/logo.png",
        Testnet: false,
    }).
    Build()

server.RegisterPaywallProvider(provider)

// Option 3: Per-route custom HTML (overrides provider)
routes := x402http.RoutesConfig{
    "GET /api": {
        Accepts:          paymentOptions,
        CustomPaywallHTML: "<html>Custom for this route</html>",
    },
}
```

Built-in handlers: `EVMPaywallHandler` (matches `eip155:*`) and `SVMPaywallHandler` (matches `solana:*`). Use `x402http.DefaultPaywallProvider()` for both.

## Key Import Paths

| Purpose | Import |
|---------|--------|
| Core types | `github.com/coinbase/x402/go` |
| HTTP utilities | `github.com/coinbase/x402/go/http` |
| Gin middleware | `github.com/coinbase/x402/go/http/gin` |
| EVM server scheme | `github.com/coinbase/x402/go/mechanisms/evm/exact/server` |
| EVM client scheme | `github.com/coinbase/x402/go/mechanisms/evm/exact/client` |
| SVM server scheme | `github.com/coinbase/x402/go/mechanisms/svm/exact/server` |
| SVM client scheme | `github.com/coinbase/x402/go/mechanisms/svm/exact/client` |
| EVM signers | `github.com/coinbase/x402/go/signers/evm` |
| SVM signers | `github.com/coinbase/x402/go/signers/svm` |
| MCP support | `github.com/coinbase/x402/go/mcp` |
| Bazaar extension | `github.com/coinbase/x402/go/extensions/bazaar` |
| Bazaar facilitator client | `github.com/coinbase/x402/go/extensions/bazaar` (use `bazaar.WithBazaar()`) |
