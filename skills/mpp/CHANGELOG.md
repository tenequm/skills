# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.10.2] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [0.10.1] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`finance, development`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [0.10.0] - 2026-08-07

### Changed

- Condensed SKILL.md from ~30.6k to ~23.6k chars, removing only duplication: dropped the "When to Use" section, the ASCII sequence diagram, the Tempo token-address table (placeholders now explained in one line), the `Fetch.*` / proxy-endpoint / subpath-export / `Html.init` enumerations, and the `Proxy.create` boilerplate - each fact stays in the matching reference file. Stellar `channel` and NEAR Intents caveats moved into the payment-methods table; the settlement obligation now lives only in Production Gotchas.
- Trimmed the frontmatter description to WHAT + WHEN (no trigger-keyword dump) and `metadata.openclaw.envVars` to the six genuine MPP variables (CLI-only, alias, Privy, and upstream provider keys are documented in the references instead).
- Added inline pointers to `references/stripe-method.md`, `references/lightning-method.md`, and `references/subscriptions.md` from the payment-methods and intents tables.

### Fixed

- `references/sessions.md`: added the missing `Store.redis()` row to the Store Backends table (the file's own WebSocket example uses it), and moved the general Store Backends section out of the "Escrow Contracts (Sessions v1)" block so v1-only content is properly scoped.
- `references/typescript-sdk.md`: the `mppx/html` row now documents the `Html.init(methodName)` page context fields.

## [0.9.0] - 2026-07-30

### Fixed

- Removed three APIs that do not exist in mppx: `mppx.free()` (free proxy routes are the literal value `true`), the `--inspect` CLI flag (use `mppx sign --dry-run`), and `mppx plugins add` (use `mppx skills add` / `mppx mcp add`).
- Stellar is charge **and** `channel`, not charge-only - the channel intent was never removed; it ships in `@stellar/mpp` with its wire spec still being drafted.
- `@redotpay/mpp` is published on npm (0.1.2); dropped the "not yet on public npm" caveat.
- Proof Credentials are in TypeScript, Rust, and Ruby but **not** pympp, whose Tempo method implements only `hash` and `transaction` payload types. Upstream's two capability matrices disagree, so the claim is now sourced from SDK code.
- Error classes: 14 -> 17. viem peer range `>=2.51.0` -> `>=2.54.0`. Rust feature table gained `sqlite` and the three TLS features.
- Corrected dead and moved links: `docs.tempo.finance` -> `docs.tempo.xyz`, the Stripe deposit-mode guide, and `/guides/upgrade-x402` -> `/guides/use-mpp-with-x402`. The docs MCP server exposes 8 tools, not 4.
- Stripe crypto PaymentIntents require API version `2026-03-25.preview` (was `2026-03-04.preview`).
- Access-key spend limits must be hex-encoded: `numberToHex(parseUnits(...))`, not a raw bigint.
- Replaced the hand-rolled Privy `toAccount()` + `signSecp256k1` recipe with `createViemAccount` from `@privy-io/node/viem` (requires `@privy-io/node` >= 0.20.0), keeping the manual construction as background.

### Added

- **Session settlement**: `settlementSchedule` (server-owned, triggered by units, amount, or interval), manual `tempo.settle()` / `tempo.settleBatch()`, and the `onSessionSettlement` hook. Without one of these a session server accumulates vouchers it never redeems on-chain, and channels stay open holding payer deposits.
- Server-side `bootstrap: true` same-route channel recovery; client `topUpAmount` top-up batching; `maxPaymentRetries` (default 3); payment-aware session SSE on client `fetch` responses.
- New `references/cli.md`: `mppx validate` end-to-end conformance checking, plus `init`, `sign`, `sessions`, `discover`, `services`, `mcp`, `skills`, `-M`, `--format`, and the `MPPX_*` env vars. The `mppx/validation` export runs the same checks programmatically.
- `validate`/`broadcast` credential lifecycle (`mppx.validateCredential()` vs `mppx.broadcastCredential()`), and the matching `Method.toServer` split.
- Tempo API relay via `tempo.charge({ relay })` and the two-hook relay contract.
- NEAR Intents payment method, including its non-trustless settlement disclosure via `methodDetails.settlementBackend`.
- New subpath exports `mppx/client/node` (SQLite session channel store sharing Tempo Wallet's database) and `mppx/validation`.
- `Fetch.from/polyfill/restore`, `Mppx.restore`, the `Transport.from/http/mcp/mcpSdk` namespace, `Html.init`, `BodyDigest`, `PaymentRequest`, `Challenge.meta`, and `Credential.extractPaymentScheme`.
- New `references/discovery-and-proxy.md` (proxy `Service.from`/`custom`, `rewriteRequest`, `docsLlmsUrl`, `{ pay, options }` endpoints, AI-user-agent markdown negotiation, the `discovery()` helper, `x-service-info`) and `references/subscriptions.md` (renewal worker, `409` + `Retry-After: 1` concurrency contract, cancellation vs revocation).
- New `references/production-gotchas.md` collecting the field-tested failure modes, including payment-timing (charge settles before the handler runs; 5-minute default challenge expiry), realm resolution precedence, settlement obligations, and mppscan attribution behaviour.
- Celo and Celo Sepolia EVM chains/assets; sponsored-charge budget caps `maxInFlightReservations` / `maxInFlightTotalFee`; extra Zod helpers (`datetimeInput`, `toDate`, `toDatetimeString`, `unwrapOptional`).
- Rust 0.11.0: TIP-1034 session client primitives, `ChargeMethod::with_validate_sender`, `tempo_simulateV1` sponsored dry-run, `TempoProvider::with_expected_chain_id`.

### Changed

- **Breaking:** `SKILL.md` restructured - Production Gotchas, the CLI, proxy/discovery, and subscriptions moved into `references/` to fit the repo's 500-line cap.
- `tempo.sessionLegacy` is formally `@deprecated`; `voucherSigner` now exists only on the legacy v1 path; the escrow-contract section is labelled Sessions v1, with v2 on the fixed TIP-20 channel precompile.
- `Method.toServer({ verify })` and `mppx.verifyCredential()` are deprecated in favour of the split `validate` + `broadcast` pair.
- Subscription period units: the mppx type is `'dev_second' | 'day' | 'week'` (no `month`) while the published schema says day/week/month - divergence flagged rather than silently picking one.
- x402 interop is configured on the method as `evm.charge({ x402: { facilitator } })`; client negotiation now prefers Payment-auth challenges over x402.
- `PaymentError` gained a structured `details` record, the practical way to get diagnostics out of an otherwise opaque 402.
- Session receipts documented as cumulative (`acceptedCumulative`, `spent`, `units`), so per-call amounts must be derived as deltas.

### Security

- SPT proxy endpoints must derive amount, currency, expiry, and limits server-side; forwarding client-supplied parameters delegates payment authorization to an untrusted client.
- Sponsorship rejects non-canonical fee-payer calldata and client-supplied access lists; session voucher replay checks hardened for settled vouchers and mismatched credential sources; pympp 0.9.1 rejects ABI calldata with trailing padding; the Rust SDK rejects oversized `WWW-Authenticate` `request` parameters before decoding.

Verified against: mppx@0.8.15, pympp@0.9.1, mpp@0.11.0, @stellar/mpp@0.7.1

## [0.8.3] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format

### Changed

- metadata.openclaw audited against the official ClawHub spec

## [0.8.2] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

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
