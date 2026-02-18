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
