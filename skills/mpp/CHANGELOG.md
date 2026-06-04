# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-06-04

### Fixed
- Replaced the non-existent `@anthropic-ai/mpp` package name with canonical `mppx` in tempo-method.md (mapped to the correct `mppx/server` / `mppx/client` subpaths, since `mppx/tempo` exports only `Session`).
- Corrected the proxy discovery claim: `/discover`, `/discover/all`, `/llms.txt` are all active - none return 410.
- Stripe `networkId` is a Stripe **profile** (`profile_...`) ID, not a Business Network `acct_` ID; SPT creation now uses the `@stripe/link-cli` spend-request flow, not a `shared_payment/granted_tokens` rawRequest.
- `method-unsupported` returns HTTP 400, not 402.
- pympp server/client examples updated to the current `@server.pay(...)` decorator API and `TempoAccount.from_key()`; removed the unsupported Python `StreamMethod`/`PaymentTransport` session flow (session intent is TypeScript/Rust only).
- typescript-sdk.md charge result uses numeric `=== 402` to match the rest of the skill.

### Added
- EVM (built-in `mppx/evm`, EIP-3009/x402-exact), Solana (`@solana/mpp`), Monad (`@monad-crypto/mpp`), and RedotPay (`@redotpay/mpp`) payment methods; noted Stellar's `channel` intent.
- Subscription intent (`mppx.tempo.subscription`): activation, access reuse, background renewal, cancellation, `dev_second` periods.
- New `mppx` subpaths: `mppx/evm(/client//server)`, `mppx/x402`, `mppx/cli(/plugins)`, `mppx/stripe/client//server`.
- Refunds concept (charge: out-of-protocol send-back; session: via channel close).
- Discovery documents (`x-payment-info.offers[]` OpenAPI) and registries (MPPScan, MPP Services directory).
- Ruby (`mpp-rb`, official by Stripe) and Elixir (`mpp`, community) SDK rows.
- Stripe on-chain crypto deposit method (API `2026-03-04.preview`) alongside fiat SPT.
- `opaque` challenge param semantics; MCP `-32043` error code; `acceptPaymentPolicy` option.
- Production gotchas: "fund with stablecoin fee token, not ETH" on Tempo; `MPP_SECRET_KEY` rotation with overlap; reverse-proxy `http`/`https` scheme mismatch.

### Changed
- Rust `mpp` 0.1 -> 0.10; expanded feature flags (`tower`, `axum`, `ws`, `stripe`, `utils`).
- mppx peer deps: `viem >= 2.51.0`, `hono >= 4.12.18`.
- Tempo session SDK option `authorizedSigner` -> `voucherSigner` (mppx 0.6.29).
- IETF draft now Standards Track (was Experimental).
- Established `metadata.upstream` tracking.

Verified against: mppx@0.6.30, pympp@0.8.2, mpp@0.10.4, @buildonspark/lightning-mpp-sdk@0.1.4, @stellar/mpp@0.6.0, mpp-card@0.1.8
