# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
