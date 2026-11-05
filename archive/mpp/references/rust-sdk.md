# mpp Rust SDK

## Installation

```bash
# Core only
cargo add mpp

# With Tempo support (client + server)
cargo add mpp --features tempo,client,server
```

---

## Feature Flags

| Feature | Description |
|---|---|
| `client` | Client providers, `Fetch` trait, credential creation |
| `evm` | Shared EVM utilities (signing, address parsing) |
| `middleware` | `reqwest-middleware` integration for automatic 402 handling |
| `server` | Verification, `ChargeMethod`, challenge generation |
| `tempo` | Tempo blockchain support (includes `evm`), Tempo-specific types |
| `tower` | `tower` service integration |
| `axum` | Axum extractors/handlers (implies `server`) |
| `ws` | WebSocket session transport (implies `server` + `client`) |
| `sqlite` | Persist and rehydrate native sessions (implies `tempo`) |
| `stripe` | Stripe payment method |
| `utils` | Shared helper utilities |

Features are additive. `tempo` implies `evm`. `middleware` implies `client`. `axum` implies `server`. `ws` implies `server` and `client`. `sqlite` implies `tempo`.

TLS backends: `reqwest-default-tls` (the default feature), `reqwest-native-tls`, `reqwest-rustls-tls`.

---

## What's New in 0.11.0

- **TIP-1034 session client primitives**: descriptor-backed channels, precompile ABI helpers, voucher signing, and fee-sponsored session opens. Rust is one of only two SDKs with the session intent.
- **`ChargeMethod::with_validate_sender`**: the Tempo hash-credential path now parses the `did:pkh:eip155` source before reserving the transaction hash and requires TIP-20 transfers to originate from the declared source address. The callback authorizes smart-account and relayer flows where the on-chain sender differs from the declared source.
- **Sponsored charge dry-run**: sponsored charges simulate the co-signed transaction via `tempo_simulateV1` before broadcasting. The check **fails closed** - if the simulation RPC is unavailable, the charge is rejected.
- **`TempoProvider::with_expected_chain_id`**: client-side chain pinning, rejecting charge challenges whose `methodDetails.chainId` conflicts with the configured chain.
- **Breaking (source-level)**: `PaymentFailedContext` gained a `reason: Option<PaymentFailureReason>` field and is now `#[non_exhaustive]`. Construct it via `PaymentFailedContext::new()` and destructure with `..` so future fields stay non-breaking.
- **Security**: oversized `WWW-Authenticate` `request` parameters are rejected before decoding.

---

## Server Quick Start

```rust
use mpp::server::{Mpp, tempo, TempoConfig};
use mpp::{parse_authorization, format_www_authenticate};

// Create server instance
let mpp = Mpp::create(tempo(TempoConfig {
    recipient: "0xYourAddress",
    currency: "<PATHUSD_TESTNET>",
    testnet: true,
    ..Default::default()
}))?;

// Generate challenge for 402 response
let challenge = mpp.charge("0.50")?;
let www_authenticate = format_www_authenticate(&challenge)?;
// Set header: WWW-Authenticate: {www_authenticate}
// Return 402

// On retry: parse and verify credential
let credential = parse_authorization(auth_header)?;
let receipt = mpp.verify_credential(&credential).await?;
let payment_receipt = receipt.to_header();
// Set header: Payment-Receipt: {payment_receipt}
// Return 200 with content
```

### Axum Example

```rust
use axum::{extract::Request, http::StatusCode, response::IntoResponse, Json};
use mpp::server::{Mpp, tempo, TempoConfig};
use mpp::{parse_authorization, format_www_authenticate};

async fn paid_handler(req: Request) -> impl IntoResponse {
    let mpp = Mpp::create(tempo(TempoConfig {
        recipient: "0xYourAddress",
        ..Default::default()
    })).unwrap();

    let auth = req.headers()
        .get("Authorization")
        .and_then(|v| v.to_str().ok());

    match auth {
        None => {
            let challenge = mpp.charge("0.10").unwrap();
            let header = format_www_authenticate(&challenge).unwrap();
            (
                StatusCode::PAYMENT_REQUIRED,
                [("WWW-Authenticate", header)],
                Json(serde_json::json!({"error": "Payment required"})),
            ).into_response()
        }
        Some(auth_header) => {
            let credential = parse_authorization(auth_header).unwrap();
            let receipt = mpp.verify_credential(&credential).await.unwrap();
            (
                StatusCode::OK,
                [("Payment-Receipt", receipt.to_header())],
                Json(serde_json::json!({"data": "paid content"})),
            ).into_response()
        }
    }
}
```

---

## Client Quick Start

```rust
use alloy::signers::local::PrivateKeySigner;
use mpp::client::{TempoProvider, send_with_payment};

let signer = PrivateKeySigner::from_bytes(&private_key)?;
let provider = TempoProvider::new(signer);

// send_with_payment handles the 402 flow automatically:
// 1. Sends the request
// 2. If 402, parses the challenge
// 3. Signs and submits payment
// 4. Retries with credential
let response = send_with_payment(
    &provider,
    reqwest::Client::new()
        .get("https://api.example.com/data"),
).await?;

println!("{}", response.text().await?);
```

### With reqwest-middleware

The `middleware` feature provides automatic 402 handling as reqwest middleware:

```rust
use mpp::middleware::PaymentMiddleware;
use reqwest_middleware::ClientBuilder;

let payment = PaymentMiddleware::new(provider);
let client = ClientBuilder::new(reqwest::Client::new())
    .with(payment)
    .build();

// All requests through this client handle 402 automatically
let res = client.get("https://api.example.com/data").send().await?;
```

---

## Common Cargo.toml Configurations

### Client Only

```toml
[dependencies]
mpp = { version = "0.11", features = ["client", "tempo"] }
```

### Server Only

```toml
[dependencies]
mpp = { version = "0.11", features = ["server", "tempo"] }
```

### Both Client and Server

```toml
[dependencies]
mpp = { version = "0.11", features = ["client", "server", "tempo"] }
```

### Client with reqwest-middleware

```toml
[dependencies]
mpp = { version = "0.11", features = ["middleware", "tempo"] }
reqwest = { version = "0.12", features = ["json"] }
reqwest-middleware = "0.4"
```

---

## Key Types

```rust
use mpp::{Challenge, Credential, Receipt};
use mpp::server::{Mpp, ChargeMethod, TempoConfig};
use mpp::client::{TempoProvider, Fetch};

// Challenge: parsed from WWW-Authenticate header
let challenge: Challenge = parse_www_authenticate(header)?;

// Credential: built from challenge + payment proof
let credential = Credential {
    challenge: challenge.clone(),
    payload: serde_json::json!({"type": "hash", "hash": "0x..."}),
    source: Some("did:pkh:eip155:4217:0x1234...".into()),
};

// Receipt: returned after verification
let receipt: Receipt = mpp.verify_credential(&credential).await?;
```
