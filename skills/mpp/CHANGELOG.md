# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.2] - 2026-07-02

### Added
- Agent tool boundary note: MPP payment authority is separate from account write authority. Added TweetClaw as a public OpenClaw example where MPP is read-only and writes/private workflows require separate product credentials plus approval.

## [0.8.1] - 2026-07-01

### Added
- Request-handling gotcha: `close`/`topUp` management credentials are bodyless, so a custom request-body validator running before `mppx.session()` rejects them with a spurious 400 (mppx answers `204`). Exempt session-management credentials - gate on credential intent/action, not body presence.

## [0.8.0] - 2026-07-01

### Changed
- Sessions overhaul: `tempo.session()` is now the TIP-1034 precompile flow (Sessions v2); the escrow-contract flow the skill documented is now `tempo.sessionLegacy` (Sessions v1). Two client APIs: `tempo.session()` (Mppx registration) vs `tempo.session.manager()` (direct lifecycle control - `.sse()`/`.close()`). Documented the v1<->v2 interop cliff.
- MCP subpaths moved to `mppx/mcp/client` and `mppx/mcp/server` (`mppx/mcp-sdk/*` retained as aliases); `McpClient.wrap` unified. MCP-over-HTTP `-32042` challenges now settle in the payment-aware fetch (`Transport.http()`).
- SDK table: Go is now the official `mpp-go` (net/http, Gin, Echo, Chi); added community Swift `mpp-swift`; Python and Ruby now have MCP, Stripe, and event handling. Corrected parity sentence (session still TS/Rust only; Go has no Stripe/MCP/events).
- Solana now supports charge + session (Token-2022), not charge-only.
- Stellar (`@stellar/mpp` 0.7.0): removed the non-functional channel `open` action - Stellar is charge-only; added payer-bound `signedHash` push, `allowUnsignedPush` opt-in, `credentialTypes` advertisement.
- Refunds reframed against v2 sessions (unclaimed reserved funds refunded by default).
- CLI no longer auto-discovers config from local directories (mppx 0.8.1) - pass config explicitly.
- Peer dep: `hono` >= 4.12.25 (was 4.12.18). Subpath-export labels bumped to mppx 0.8.1.

### Added
- Payment Hooks section: server (`onChallengeCreated`/`onPaymentSuccess`/`onPaymentFailed`/`on('*')`) and client (`onChallengeReceived`/`onCredentialCreated`/`onPaymentResponse`/`onPaymentFailed`) lifecycle observability.
- Managing Agent Spend section: Tempo access keys (delegated signing keys with token limits, contract/function/recipient scopes, expiry) via `provider.getMppxParameters({ accessKey })`.
- Client chain pinning (`tempo.charge({ expectedChainId })`); `tempo.common()` charge+session bundle alias; pluggable client `channelStore` (client `authorizedSigner` override removed); proxy `anthropic()` service preset; split-payment limits (1-10, per-split memos, `expectedRecipients`).
- Services MCP discovery server (`mpp.dev/mcp/services`), docs MCP (`mpp.dev/api/mcp`), and `npx skills add tempoxyz/mpp -g` install path; IETF `draft-ryan-httpauth-payment-01`; docs monorepo `tempoxyz/mpp`.
- pympp 0.9.0: credential `source` validation + `validate_sender` callback on `ChargeIntent`; sponsored charges dry-run via `tempo_simulateV1` before broadcast; Python MCP support.
- Production gotchas (advisory): mppx/viem version coupling (arity-crash), `mppx.fetch` probe masks upstream 5xx; RedotPay `@redotpay/mpp` not-yet-on-npm caveat.

### Security
- Zero-amount proof credentials bound to the payer wallet: EIP-712 `Proof` gains an `account` field, domain version bumped to 3 (`tempo.Proof`).

Verified against: mppx@0.8.1, pympp@0.9.0, @stellar/mpp@0.7.0

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
