# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.11.3] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [0.11.2] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`finance, development`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [0.11.1] - 2026-08-07

### Removed

- Git-tracked `.last-refresh` provenance file (stray artifact outside the documented skill layout; now gitignored).

## [0.11.0] - 2026-07-30

### Added
- `@x402/near` (NEAR exact via NEP-366 SignedDelegate + NEP-141 `ft_transfer`, relayer-sponsored gas, `near:mainnet`/`near:testnet`) and `@x402/xrpl` (XRPL exact, `xrpl:0`/`xrpl:1`/`xrpl:2`), each with a per-chain reference doc. NEAR is published on npm; XRPL is tagged 2.20.0 but not yet published.
- Network: Igra mainnet (`eip155:38833`, USDC, Permit2 only - the token implements neither EIP-3009 nor EIP-2612).
- `extra.facilitatorAddress` - required by the upto client and embedded in the Permit2 witness as `witness.facilitator`.
- SVM `extra.recentBlockhash` / `extra.lastValidBlockHeight` transaction-construction hints (TS, Go, Python; non-binding).
- `onAfterVerify` can now abort, dispatching `onVerifiedPaymentCanceled` with reason `after_verify_aborted`.
- Wallet compatibility: ERC-6492 counterfactual wallets are **not** supported on the Permit2 path; a token whose EIP-3009 implementation only calls `ecrecover` fails every non-EOA wallet type; `payerAuthorizer` must be an EOA.
- Spec-stage schemes Starknet and Casper; draft SVM `upto` binding via the Solana payment-channels program.
- Error codes: 15 `invalid_siwx_*`, two batch-settlement codes, `invalid_exact_stellar_payload_fee_exceeds_maximum`, `invalid_exact_hedera_payload_signature_invalid`, `UnauthorizedFacilitator`.
- Bazaar catalog-visibility troubleshooting; offer-receipt signer *authorization* (`did:web`, DNS TXT `_controllers.<domain>`); `builder-code` service codes capped at 5 and silently truncated.
- Third-party SDK and facilitator directories; Slack replaced Discord as the community channel.
- Operational guidance from field use: SVM `maxTimeoutSeconds` above ~90s is unenforceable (blockhash lifetime); both payer and `payTo` ATAs must exist; `SettlementCache` rejection is client-visible and only successful settlements should be cached; browser clients must expose the un-prefixed V2 CORS headers; server-side scheme registration does not create a local verify path; a single-EOA facilitator must serialize its own settles because settle-time simulation cannot detect nonce races; set `Content-Type` explicitly on payment-wrapped fetch bodies.

### Changed
- SDK versions: TypeScript 2.17.0 -> 2.20.0, Python 2.14.0 -> 2.17.0, Go v2.17.0 -> v2.20.0.
- Default facilitator now also covers Algorand Testnet and XRPL Testnet, and advertises `upto` + `batch-settlement` on Base Sepolia alongside three extensions; upstream now documents it as dev/testnet only, not a production default.
- NEAR moved from spec-stage to a shipped TypeScript SDK; the spec-only chain list is now Cardano, Sui, Starknet, and Casper.
- Python extras: added `evm`, `tvm`, and the `clients` / `servers` / `mechanisms` bundles.

### Fixed
- **Breaking for signers:** the `upto` Permit2 witness struct was wrong - it omitted the mandatory `facilitator` field and carried a phantom `bytes extra`. The EIP-712 type list and witness type string were wrong to match. A client signing the documented struct produced a digest the contract cannot verify, so every upto payment would fail.
- Algorand CAIP-2 identifiers are the URL-safe base64 genesis hash truncated to the first 32 characters; the previous padded full-hash form no longer matches.
- The Permit2 allowance error is `permit2_allowance_required` on the wire, not `PERMIT2_ALLOWANCE_REQUIRED`.
- SIWx examples: `siwxResourceServerExtension` does not exist (it is `createSIWxResourceServerExtension`, which requires an operator-configured `origin`), and `domain` / `resourceUri` were removed from the declare options.
- Replaced the dead `x402.org/ecosystem` link (hard 404) with the docs facilitator directory.
- `builder-code` now ships Python; the support matrix said pending.
- `createAuthHeaders` must return an object keyed by facilitator path - a flat object previously dropped authentication silently and now throws.

### Security
- SIWx binds to an operator-configured `origin` instead of request-derived values; deriving the domain from the `Host` header allowed a signature made for another site to be replayed. The `uri` origin check tightened from prefix to exact match.
- Batch-settlement EVM: unauthenticated path traversal and pre-verification channel mutation fixed across all three SDKs.
- SIWx Solana rejects small-order Ed25519 public keys; Hedera facilitators must cryptographically verify the payer signed the frozen transaction body; Aptos verification must not rely on simulation; Stellar facilitators must not use the client's fee bid.
- Solana settlement is not settled until the transaction status confirms it: `skipPreflight` submission plus swallowed confirmation errors reports success for transactions that landed with `meta.err` set.

Verified against: @x402/core@2.20.0, @x402/evm@2.20.0, x402@2.17.0, github.com/x402-foundation/x402/go/v2@v2.20.0

## [0.10.2] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format

### Changed

- metadata.openclaw audited against the official ClawHub spec

## [0.10.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.10.0] - 2026-07-01

### Added
- Networks: Mezo mainnet (`eip155:31612`, mUSD, 18 decimals, Permit2 + EIP-2612), XDC Network mainnet (`eip155:50`, USDC) and XDC Apothem testnet (`eip155:51`, USDC).
- SDK bindings: `@x402/tvm` (TON exact scheme) and `@x402/keeta` (`keeta:21378`/`keeta:1413829460`) in TS 2.15.0; `@x402/concordium` (native CCD, `ccd:*`) in TS 2.17.0.
- Core APIs: transport-agnostic `parsePaymentResult` -> `HTTPResourceResponse` (2.15.0); `validateFacilitatorSupport` startup hook (Go `FacilitatorSupportValidator`) that fails fast on facilitator capability mismatch (2.17.0); `dynamicInfoFields` extension capability for per-response nonce/timestamp fields (2.16.0).
- Expanded EVM wallet compatibility: plain EOA, ERC-4337/ERC-7579 smart accounts, ERC-6492 counterfactual, and ERC-7702-delegated EOAs; ERC-6492 now covers exact + batch-settlement (2.17.0).
- Go gained sign-in-with-x server + client (`go/v2/extensions/signinwithx`, v2.16.0), closing the extensions SDK matrix.
- Error codes: `asset_not_deployed_contract` (EVM verify rejects EOA asset addresses) and `invalid_batch_settlement_evm_authorizer_not_configured` (optional batch-settlement `receiverAuthorizer`).
- Default facilitator now also supports Hedera Testnet; Hedera HBAR native token usable via asset id `0.0.0` (tinybars, 10^8).

### Changed
- SDK versions: TypeScript 2.14.0 -> 2.17.0, Python 2.12.0 -> 2.14.0, Go v2.14.0 -> v2.17.0.
- Spec-stage `exact` chains with no SDK narrowed to Cardano, NEAR, Sui (Concordium and Keeta now ship TypeScript SDKs); TON is now TypeScript + Python (was Python-only).
- Avalanche marked as runtime-registration only (no pre-configured default asset in v2).
- EVM client authorization `validAfter` now set to 0 to reduce onchain timing failures; Go raised the default resource-server `maxTimeoutSeconds` from 60 to 300.
- builder-code extension: multiple service codes (`s` as string or array) and EVM `calldataSuffix` plumbing.

Verified against: @x402/core@2.17.0, @x402/evm@2.17.0, x402@2.14.0, github.com/x402-foundation/x402/go/v2@v2.17.0

## [0.9.0] - 2026-06-09

### Added
- Networks: ADI Chain (`eip155:36900`, USDC.e), HPP mainnet (`eip155:190415`) and HPP Sepolia (`eip155:181228`), both defaulting to Bridged USDC (USDC.e).
- `@x402/hedera` TypeScript mechanism package (Hedera HBAR + HTS fungible-asset transfers).
- Note that x402 now has a fourth official SDK (Java 17+, build from source) and spec-stage `exact` schemes for Concordium, Cardano, NEAR, Sui, and Keeta (no SDK yet), plus a Cloudflare `batch-settlement` variant.
- Optimistic-settlement footgun: verify off-chain -> serve -> settle asynchronously, so settlement can fail after the buyer already received the resource.

### Changed
- SDK versions: TypeScript 2.12.0 -> 2.14.0, Python 2.10.0 -> 2.12.0, Go v2.11.0 -> v2.14.0.
- Go module path now carries a `/v2` suffix (`github.com/x402-foundation/x402/go/v2/...`); all Go imports and `go get` updated - the old bare path no longer resolves tagged releases.
- `auth-capture` now ships a TypeScript client scheme (`@x402/evm/auth-capture/client`); `batch-settlement` now ships a full TypeScript SDK (`@x402/evm/batch-settlement/*`); `builder-code` now has TypeScript (`@x402/extensions/builder-code`) and Go (`go/v2/extensions/buildercode`) helpers; `sign-in-with-x` now has a Python implementation.
- SVM exact static instruction-count ceiling raised from 6 to 7; added simulation-based smart-wallet verification (`enableSmartWalletVerification`) as a fallback path for allowlisted programs (Squads, Swig, SPL Governance, Metaplex Core, Lighthouse).

### Security
- SVM exact facilitator deduplication now keys on the transaction message hash (not the full signed-tx bytes), closing a cache-bypass via fee-payer-signature randomization.
- ERC-6492 factory-call-injection hardening: the `eip6492AllowedFactories` allowlist (`eip6492_allowed_factories` in Python) is now the sole gate; an empty/omitted list disables counterfactual deployment and returns `eip6492_factory_not_allowed`. The `DeployERC4337WithEIP6492` config field was removed across all three SDKs.

Verified against: @x402/core@2.14.0, @x402/evm@2.14.0, x402@2.12.0, github.com/x402-foundation/x402/go/v2@v2.14.0

## [0.8.0] - 2026-05-22

### Added
- `batch-settlement` and `auth-capture` payment schemes (`batch-settlement` ships in the Go and Python SDKs; `auth-capture` is spec-defined, SDK support pending).
- Networks: TON/TVM (`tvm:-239`/`tvm:-3`), Hedera (`hedera:mainnet`/`testnet`), Algorand, and Radius (`eip155:723487`/`72344`). New `@x402/avm` package (Algorand TS SDK).
- Extensions: `builder-code`, `http-message-signatures`, `auth-hints` (spec-defined; no SDK helpers yet).
- Protocol fields: `ResourceInfo.serviceName`/`tags`/`iconUrl`, `VerifyResponse.extra`, `/discovery/resources` filters (`payTo`/`scheme`/`network`/`extensions`), `GET /discovery/search`, and the `PERMIT2_ALLOWANCE_REQUIRED` error code.
- Solana footgun: the destination USDC ATA must already exist on-chain (x402 SVM transactions carry no ATA-create instruction).

### Changed
- SDK versions: TypeScript 2.9.0 -> 2.12.0, Python 2.6.0 -> 2.10.0, Go 2.7.0 -> 2.11.0.
- MegaETH default token name corrected to "MegaUSD".
- Python now supports the `upto` scheme; gas-sponsoring and `payment-identifier` extensions now span TS + Go + Python.
- Default `x402.org` facilitator now also supports Aptos Testnet.
- `@x402/fastify` is published on npm (removed the "not yet published" note).
- Tightened the SKILL.md description to a concise summary; SDK version numbers are tracked in the body and `metadata.upstream` rather than inline.

### Security
- Corrected the `x402UptoPermit2Proxy` contract address to `0x4020A4f3b7b90ccA423B9fabCc0CE57C6C240002`. The previous value was a stale pre-redeployment address - a fund-loss hazard if copied into signing code.

Verified against: @x402/core@2.12.0, x402@2.10.0, github.com/x402-foundation/x402/go@v2.11.0

## [0.7.2] - 2026-04-30
- Initial CHANGELOG; upstream tracking established.
