# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.4.0] - 2026-06-04

### Fixed
- Corrected ~20 doc URLs that now 404 after Privy's docs restructure (React/Node
  migration guides, custom-auth, webhooks, policies, EVM/Solana network config,
  Tempo, Solana send recipes, HD wallets, appearance, security pages).
- Server SDK user-lookup methods: `getByEmail`/`getByPhone` do not exist; use
  `getByEmailAddress({address})`, `getByPhoneNumber({number})`,
  `getByWalletAddress({address})`, and `_get(userId)` for by-ID.
- Removed reference to the nonexistent `@x402/server` package; server x402
  middleware ships per-framework (e.g. `@x402/express`).
- Fixed an undefined `alphaUsd` variable in the Tempo `transferSync` example.

### Changed
- Token verification: top-level `privy.verifyAuthToken()` is deprecated; use
  `privy.utils().auth().verifyAccessToken()`. Identity tokens parse via
  `privy.users().get({id_token})`.
- `webhooks().verify` `svix` key deprecated in favor of `headers`.
- Updated the package-version table to June 2026 and added `metadata.upstream`
  tracking plus this CHANGELOG.
- Docs index pointer: `llms.txt` now installs Privy's official agent skill; the
  real machine index is `llms-full.txt`.
- Tempo `alphaUSD` token relabeled - only PathUSD and USDC are verified names.
- Smart-wallet provider "LightAccount (Alchemy)" relabeled "Alchemy".

### Added
- New **Wallet Actions** coverage: `wallets().earn()` (DeFi yield), `wallets.swap`
  (incl. cross-chain), and `wallets().transfer()` with bridging.
- **Intents** concept (approval-gated wallet ops) and the new Node services
  `intents()` / `apps()`.
- Programmatic **fiat onramp/offramp + KYC** and **Spark/Lightning** for Bitcoin.
- Node SDK `createViemAccount` native Tempo support (tx type 118), superseding the
  hand-rolled `createPrivyAccount` signer.
- Footguns: server-side signing of user-owned wallets needs an authorization-key
  signer; filter `linkedAccounts` by `chain_type` for EVM addresses; whitelabel
  flows need Dashboard Allowed Origins; Privy smart wallets are EVM-only;
  `appearance.walletList` to scope the login modal; `@solana/kit` 6.x / memo
  peer deps; mppx `acceptPaymentPolicy` and `viem/tempo/chains`.

Verified against: @privy-io/react-auth@3.29.1, @privy-io/node@0.20.0, @privy-io/wagmi@4.0.11, mppx@0.6.30, @x402/fetch@2.14.0
