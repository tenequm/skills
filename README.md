# Skills

Claude Code skills for founders, developers, and web3 builders.

This repository publishes reusable skill folders under `skills/<slug>/`, ships stable bundle downloads through GitHub Releases, and publishes changed skills to ClawHub.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Skill Catalog](#skill-catalog)
- [Release Automation](#release-automation)
- [Contributing](#contributing)
- [License](#license)

## Background

Each skill is a directory with a `SKILL.md` file plus optional references, scripts, evals, or assets. The repository is designed to support three consumption paths:

- ClawHub for normal installation and discovery
- GitHub Releases for raw portable zip bundles and release history
- GitHub source for review and contribution

## Install

```bash
npx skills add tenequm/skills@<skill-name>
```

## Usage

```bash
# Install a skill from this repository
npx skills add tenequm/skills@typescript-dev

# Or download the latest raw bundle from GitHub Releases
curl -LO https://github.com/tenequm/skills/releases/download/skills-latest/typescript-dev.zip
```

Use the catalog below to pick a skill. Prefer ClawHub for normal installs. Use the zip bundles when you want a portable artifact or need to inspect the packaged files directly.

## Skill Catalog

Each skill has a stable latest bundle link and a ClawHub page:

<!-- GENERATED_SKILLS_TABLE_START -->
| Skill | Version | Bundle | ClawHub | Description |
|-------|---------|--------|---------|-------------|
| `audio-quality-check` | 0.1.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/audio-quality-check.zip) | [page](https://clawhub.ai/tenequm/skills/audio-quality-check) | Analyzes audio recording quality - echo detection, loudness, speech intelligibility, SNR, and spectral analysis. Use when the user wants to check a recording's quality, detect echo or duplication, measure speech clarity, compare original vs processed audio, or diagnose why a recording sounds bad, including tracks from Blackbox or any call recording app. |
| `chrome-extension-wxt` | 1.1.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/chrome-extension-wxt.zip) | [page](https://clawhub.ai/tenequm/skills/chrome-extension-wxt) | Build Chrome extensions using WXT framework with TypeScript, React, Vue, or Svelte. Use when creating browser extensions, developing cross-browser add-ons, or working with Chrome Web Store projects. Triggers on phrases like "chrome extension", "browser extension", "WXT framework", "manifest v3", or file patterns like wxt.config.ts. |
| `cloudflare-workers` | 3.1.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/cloudflare-workers.zip) | [page](https://clawhub.ai/tenequm/skills/cloudflare-workers) | Rapid development with Cloudflare Workers - build and deploy serverless applications on Cloudflare's global network. Use when building APIs, full-stack web apps, edge functions, background jobs, or real-time applications. Triggers on phrases like "cloudflare workers", "wrangler", "edge computing", "serverless cloudflare", "workers bindings", or files like wrangler.toml, worker.ts, worker.js. |
| `effect-ts` | 0.6.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/effect-ts.zip) | [page](https://clawhub.ai/tenequm/skills/effect-ts) | Effect-TS development guide for TypeScript, focused on Effect v4 (the recommended default) with full v3 (stable) support for existing codebases. Use when building, debugging, reviewing, or generating Effect code across its error, concurrency, service, streaming, schema, and platform layers, or whenever code imports from 'effect', '@effect/platform', '@effect/ai', or '@effect/sql'. Includes exhaustive wrong-vs-correct API tables to prevent hallucinated Effect code. |
| `erc-8004` | 0.2.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/erc-8004.zip) | [page](https://clawhub.ai/tenequm/skills/erc-8004-development) | Build with ERC-8004 Trustless Agents - on-chain agent identity, reputation, validation, and discovery on EVM chains. Use when registering AI agents on-chain, building agent reputation systems, searching/discovering agents, working with the Agent0 SDK (agent0-sdk), or implementing the ERC-8004 standard. Triggers on ERC-8004, Agent0, agent identity, agent registry, agent reputation, trustless agents, agent discovery. |
| `founder-playbook` | 0.1.5 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/founder-playbook.zip) | [page](https://clawhub.ai/tenequm/skills/founder-playbook-web3) | Decision validation and thinking frameworks for startup founders. Use when you need to pressure-test a decision, validate your next steps, think through strategic options, or sanity-check your approach. Triggers on phrases like "should I", "help me think through", "is this the right move", "validate my thinking", "what am I missing". Covers fundraising, customer development, runway management, prioritization, and crypto/web3 founder challenges. |
| `foundry-solidity` | 0.2.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/foundry-solidity.zip) | [page](https://clawhub.ai/tenequm/skills/foundry-solidity) | Build and test Solidity smart contracts with Foundry toolkit. Use when developing Ethereum contracts, writing Forge tests, deploying with scripts, or debugging with Cast/Anvil. Triggers on Foundry commands (forge, cast, anvil), Solidity testing, smart contract development, or files like foundry.toml, *.t.sol, *.s.sol. |
| `gh-cli` | 1.3.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/gh-cli.zip) | [page](https://clawhub.ai/tenequm/skills/gh-cli) | GitHub CLI for remote repository analysis, file fetching, codebase comparison, and discovering trending code/repos. Use when analyzing repos without cloning, comparing codebases, or searching for popular GitHub projects. |
| `ghostwriter` | 0.1.1 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/ghostwriter.zip) | [page](https://clawhub.ai/tenequm/skills/ghostwriter) | Write content by interviewing the user instead of drafting - extract their material through questions, then assemble the piece from their own words. Use when the user needs to write something for an audience or mentions "ghostwriter". |
| `go-dev` | 0.3.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/go-dev.zip) | [page](https://clawhub.ai/tenequm/skills/go-dev) | Opinionated Go development setup with golangci-lint v2, gofumpt, gotestsum, golang-migrate, and just. Use when creating a new Go project, setting up linting, formatting, testing, or coverage, configuring a Go CI pipeline, writing a Justfile, wiring database migrations, or migrating from a Makefile-only workflow. |
| `grafana-foundation-sdk` | 0.2.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/grafana-foundation-sdk.zip) | [page](https://clawhub.ai/tenequm/skills/grafana-foundation-sdk) | Build Grafana dashboards as code with the grafana-foundation-sdk typed builders (TypeScript or Go). Use when creating, modifying, or generating Grafana dashboard JSON programmatically, converting hand-written dashboard JSON to typed code, building monitoring dashboards, or working with Prometheus/Loki queries in dashboards. |
| `grill-me` | 0.1.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/grill-me.zip) | [page](https://clawhub.ai/tenequm/skills/grill-me) | Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me". |
| `herdr-faq` | 0.1.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/herdr-faq.zip) | [page](https://clawhub.ai/tenequm/skills/herdr-faq) | Launch and drive coding agents (codex, claude, agy) through the Herdr CLI reliably. Use before starting or prompting a subagent via herdr agent/pane commands, and when any herdr command fails or an agent seems stuck, silently lost a prompt, or reports a wrong state. |
| `impactful-writing` | 0.1.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/impactful-writing.zip) | [page](https://clawhub.ai/tenequm/skills/impactful-writing) | Write clear, emotionally resonant, and well-structured content that readers remember and act upon. Use when writing or editing any text - Twitter posts, articles, documentation, emails, comments, updates - for maximum clarity, engagement, and impact. |
| `lance-format` | 0.18.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/lance-format.zip) | [page](https://clawhub.ai/tenequm/skills/lance-format) | Deep reference for Lance v12 - the open columnar lakehouse format for multimodal AI - and its Rust crate workspace plus pylance. Covers the 2.x file format and structural encodings, the table format (manifests, fragments, transactions, OCC), vector / scalar / full-text indexes, MemWAL, schema evolution, time travel, namespaces, and object-store config. Use when building directly on the Lance crates or reading `.lance` datasets; this is the Lance format and engine (`lance-format/lance`), not the LanceDB product built on top of it. |
| `mcp-best-practices` | 1.1.1 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/mcp-best-practices.zip) | [page](https://clawhub.ai/tenequm/skills/mcp-best-practices) | Build, harden, and debug production MCP servers with the TypeScript SDK. Use when writing or reviewing an MCP server or its tools - picking a transport, designing tool schemas and results, handling errors, adding OAuth, cutting token bloat, or migrating SDK versions. Also covers MCP Apps, extensions, and the Registry. Assumes a working server already exists rather than scaffolding one from scratch. |
| `mpp` | 0.10.1 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/mpp.zip) | [page](https://clawhub.ai/tenequm/skills/mpp) | Build with MPP (Machine Payments Protocol) - the open protocol for machine-to-machine payments over HTTP 402. Use when building paid APIs, payment-gated content or endpoints, AI agent payment flows, MCP tool payments, pay-per-token streaming, or metered pay-as-you-go billing. Covers the mppx TypeScript SDK (Hono/Express/Next.js/Elysia middleware), pympp Python SDK, and mpp Rust SDK, with Tempo stablecoins, Stripe cards, Lightning Bitcoin, and custom payment rails. |
| `okf-project-knowledge-base` | 0.1.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/okf-project-knowledge-base.zip) | [page](https://clawhub.ai/tenequm/skills/okf-project-knowledge-base) | Maintain durable project knowledge as Git-native OKF v0.2 bundles - one Markdown concept per file with YAML frontmatter, provenance sources, trust tiers, and a progressive-disclosure index. Use when recording a decision, finding, or rule that must outlive the session ("document this decision", "add this to the knowledge base", "why did we choose X"), when a repo contains a bundle (a directory whose index.md declares okf_version, canonically docs/knowledge/), when setting up durable knowledge capture in a project, or when reviewing completed work for knowledge worth preserving. Not for session state, scratchpads, or agent operating instructions. |
| `polish` | 2.6.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/polish.zip) | [page](https://clawhub.ai/tenequm/skills/code-polish) | Pre-release code review - runs lint/type checks, launches parallel review agents (cleanliness, design, efficiency, side-effect gating) on the diff, validates findings, and fixes with approval. Run when the user asks for a polish or pre-release review, or told you earlier to polish before committing or pushing. |
| `polish-new` | 0.1.1 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/polish-new.zip) | [page](https://clawhub.ai/tenequm/skills/polish-new) | Pre-release code review that converges - runs checks, launches parallel review agents (cleanliness, design, efficiency, side-effect gating) sized to the diff, validates findings against reproducible evidence in a run ledger, fixes on approval, then reviews its own fixes until a round warrants no edits. Run on /polish-new, or when asked for a polish or pre-release review before committing or pushing. |
| `pre-compact` | 0.1.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/pre-compact.zip) | [page](https://clawhub.ai/tenequm/skills/pre-compact) | Prepare the session for context compaction - write a handoff file a fresh session can continue from, propose updates to the project's durable docs, apply them on approval or with `auto`. Use before compacting or clearing context, or on "pre-compact". |
| `privy-integration` | 0.4.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/privy-integration.zip) | [page](https://clawhub.ai/tenequm/skills/privy-integration) | Integrates Privy authentication, embedded wallets, and agent payment protocols into web and agentic apps. Covers React SDK (PrivyProvider, hooks, wagmi), Node.js SDK, smart wallets (ERC-4337), x402 and MPP machine payments, Tempo chain, and agentic wallets with policies. Use when setting up Privy auth, creating embedded or agentic wallets, adding x402 or MPP payments, integrating with Tempo, configuring wallet policies, or connecting Privy to MCP/Agent Auth flows. |
| `python-dev` | 0.2.5 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/python-dev.zip) | [page](https://clawhub.ai/tenequm/skills/python-dev) | Opinionated Python development setup with uv, ty, ruff, pytest, and just. Use when creating a new Python project, writing or fixing pyproject.toml, or configuring linting, formatting, type checking, testing, pre-commit hooks, or build and CI tooling. |
| `reset-context-contamination` | 0.1.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/reset-context-contamination.zip) | [page](https://clawhub.ai/tenequm/skills/reset-context-contamination) | Discards the accumulated drafts and framings from this thread and re-derives the task from a clean problem statement. Use when the user says the thread is contaminated, that the conversation is going in circles, or that they want a fresh take, or when they invoke /reset-context-contamination. |
| `review-github-pr` | 0.4.2 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/review-github-pr.zip) | [page](https://clawhub.ai/tenequm/skills/review-github-pr) | Reviews a GitHub pull request end to end. Fetches the diff, runs automated checks, analyzes the changes with three parallel review agents (correctness, convention compliance, efficiency), validates every finding against the actual code, and drafts a GitHub review that posts findings as inline diff comments with a recommended action of approve, request changes, or comment only. |
| `rust-dev` | 0.5.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/rust-dev.zip) | [page](https://clawhub.ai/tenequm/skills/rust-dev) | Practical day-1 guide to building applications in Rust well. Covers the mental model (ownership, errors as values, traits-not-interfaces), day-1 decisions (String vs &str, Box vs Rc vs Arc, dyn vs impl Trait, anyhow vs thiserror), idioms, anti-patterns, and a tight crate shortlist (tokio, serde, anyhow, clap, reqwest, tracing, axum, sqlx). Use when starting a Rust project, learning Rust from another language, wrestling with the borrow checker, choosing crates, structuring modules, configuring Cargo.toml/clippy/rustfmt, testing, profiling, or releasing a binary. |
| `skills-best-practices` | 0.8.1 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/skills-best-practices.zip) | [page](https://clawhub.ai/tenequm/skills/skills-best-practices) | Build high-quality Agent Skills for any agent - opinionated best practices distilled from the Agent Skills spec, official Anthropic guidance, and production experience. Covers SKILL.md structure, frontmatter, description writing, single-file vs references/ layout, progressive disclosure, testing, patterns, troubleshooting, and distribution across all surfaces (Claude.ai, Claude Code, API, Agent SDK). Use when creating a skill, reviewing skill quality, debugging why a skill won't trigger, structuring skill directories, or writing skill descriptions. |
| `solana-development` | 0.7.2 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/solana-development.zip) | [page](https://clawhub.ai/tenequm/skills/solana-development) | Build, test, deploy, and audit Solana programs with Anchor or native Rust, and build with ZK Compression (Light Protocol). Use when developing Solana smart contracts, implementing token operations, optimizing compute, deploying to networks, auditing programs for vulnerabilities, or creating compressed tokens/PDAs. |
| `standard-readme` | 0.1.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/standard-readme.zip) | [page](https://clawhub.ai/tenequm/skills/standard-readme) | Writes or audits README files following the Standard Readme specification (github.com/RichardLitt/standard-readme). Use whenever the user asks to create, write, rewrite, improve, audit, or fix a README, or asks about README quality or structure - even if they never mention "standard readme" explicitly. |
| `swift-macos` | 0.8.2 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/swift-macos.zip) | [page](https://clawhub.ai/tenequm/skills/swift-macos) | Covers macOS app development with Swift 6.3, SwiftUI, SwiftData, Swift Concurrency, Foundation Models, Swift Testing, ScreenCaptureKit, and app distribution. Use when building native Mac apps - windows, scenes, navigation, menus and toolbars, SwiftData models and queries, modern concurrency, on-device AI, testing, screen and audio capture, MenuBarExtra apps, AppKit bridges, login items, process monitoring, or App Store and Developer ID notarization. |
| `tanstack` | 0.4.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/tanstack.zip) | [page](https://clawhub.ai/tenequm/skills/tanstack) | Builds type-safe React apps with TanStack Query (data fetching, caching, mutations), Router (file-based routing, search params, loaders), and Start (SSR, server functions, middleware). Use when working with react-query, server state, file-based routing, typed search params, route loaders, SSR, or server functions in a full-stack React app. |
| `typescript-dev` | 0.3.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/typescript-dev.zip) | [page](https://clawhub.ai/tenequm/skills/typescript-dev) | Builds full-stack TypeScript apps with Vite 8, React 19, Tailwind CSS v4, shadcn/ui, Biome, Vitest, and Hono. Covers the frontend (Vite/Rolldown build and dev server, type-safe React 19, strict TypeScript 6.0, Tailwind/shadcn styling, Biome lint/format, Vitest) and the Hono 4 backend/edge layer (routing, middleware, Zod validation, end-to-end type-safe RPC, OpenAPI, multi-runtime deploy). Use when setting up or working in a TypeScript project: configuring Vite, writing components, the React Compiler, Tailwind/shadcn, dev server and HMR, bundles, tests, lint/format/CI, or building a Hono API and wiring its RPC client to React. |
| `update-skill` | 0.8.2 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/update-skill.zip) | [page](https://clawhub.ai/tenequm/skills/update-skill) | Thorough on-demand refresh of one skill in a skills repository: researches usage/upstream/docs in parallel, gates twice for approval, bumps version, updates CHANGELOG, runs the repo's validation, then commits and watches CI. Install the pond MCP (https://pond.cascade.fyi/) for the prior-session usage angle; without it that angle is skipped. Use to update, refresh, or check the freshness of a specific skill. |
| `web3-protocol-gtm` | 0.2.6 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/web3-protocol-gtm.zip) | [page](https://clawhub.ai/tenequm/skills/web3-protocol-gtm) | Go-to-market strategy for web3 builders - protocols, products, services, and solo founders. Use when planning growth for a crypto protocol, building developer community, crafting CT narrative, planning ecosystem partnerships, preparing grant applications, launching tokens, pricing crypto-native products, or growing as a solo founder in web3. |
| `x402` | 0.11.2 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/x402.zip) | [page](https://clawhub.ai/tenequm/skills/x402-development) | Build internet-native payments with the x402 open protocol - HTTP 402 Payment Required for on-chain micropayments with no accounts or API keys. Use when developing paid APIs, paywalled content, AI agent payment flows, or MCP tools that charge per call. Covers the TypeScript, Python, and Go SDKs across EVM, Solana, Stellar, Aptos, NEAR, and XRPL. |
<!-- GENERATED_SKILLS_TABLE_END -->

## Release Automation

Pushes to `main` use a skill-aware release workflow that:

- runs `pre-commit`
- detects which `skills/<slug>/` directories changed
- requires a version bump in each changed skill
- publishes changed skills to ClawHub
- creates an immutable GitHub Release for that push
- refreshes the rolling `skills-latest` release used by the README bundle links

Setup details live in [docs/release-automation.md](docs/release-automation.md).

## Contributing

Issues and pull requests are welcome.

Before opening a PR:

- run the repository checks with `just check`
- update `README.md` with `just readme` if skill metadata changed
- bump the skill version when editing files inside `skills/<slug>/`

```bash
just check
```

## License

[MIT](LICENSE)
