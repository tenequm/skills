# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
