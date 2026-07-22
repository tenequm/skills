# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
