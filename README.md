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
| `acpx-faq` | 0.5.1 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/acpx-faq.zip) | [page](https://clawhub.ai/tenequm/skills/acpx-faq) | Run coding agents (codex, claude, agy/Antigravity) through the acpx ACP CLI - the headless lane outside a herdr pane (no HERDR_ENV). Use before launching or prompting a subagent, and when a command fails, a session is not found, or a prompt is lost. |
| `chrome-extension-wxt` | 1.1.5 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/chrome-extension-wxt.zip) | [page](https://clawhub.ai/tenequm/skills/chrome-extension-wxt) | Build Chrome extensions with the WXT framework and TypeScript, React, Vue, or Svelte. Use when creating browser extensions or cross-browser add-ons. Triggers on "chrome extension", "browser extension", WXT, manifest v3, or wxt.config.ts. |
| `effect-ts` | 0.6.5 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/effect-ts.zip) | [page](https://clawhub.ai/tenequm/skills/effect-ts) | Effect-TS guide for TypeScript, v4 default with v3 support. Use when writing, debugging, or reviewing Effect code across errors, concurrency, services, streams, and schema, or when code imports from 'effect' or any '@effect/*' package. |
| `erc-8004` | 0.2.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/erc-8004.zip) | [page](https://clawhub.ai/tenequm/skills/erc-8004-development) | Build with ERC-8004 Trustless Agents - on-chain agent identity, reputation, validation, and discovery on EVM chains. Use when registering agents on-chain, building agent reputation, or using the Agent0 SDK. Triggers on ERC-8004 and Agent0. |
| `founder-playbook` | 0.1.6 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/founder-playbook.zip) | [page](https://clawhub.ai/tenequm/skills/founder-playbook-web3) | Decision validation and thinking frameworks for founders. Use to pressure-test a decision, validate next steps, or sanity-check an approach - "should I", "help me think through", "what am I missing". Covers fundraising, customers, runway. |
| `foundry-solidity` | 0.2.5 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/foundry-solidity.zip) | [page](https://clawhub.ai/tenequm/skills/foundry-solidity) | Build and test Solidity contracts with Foundry. Use when developing Ethereum contracts, writing Forge tests, deploying with scripts, or debugging with Cast/Anvil. Triggers on forge, cast, anvil, foundry.toml, *.t.sol, or *.s.sol. |
| `gh-cli` | 1.3.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/gh-cli.zip) | [page](https://clawhub.ai/tenequm/skills/gh-cli) | GitHub CLI for remote repository analysis, file fetching, codebase comparison, and discovering trending code/repos. Use when analyzing repos without cloning, comparing codebases, or searching for popular GitHub projects. |
| `ghostwriter` | 0.1.2 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/ghostwriter.zip) | [page](https://clawhub.ai/tenequm/skills/ghostwriter) | Write content by interviewing the user instead of drafting - extract their material through questions, then assemble the piece from their own words. Use when the user needs to write something for an audience or mentions "ghostwriter". |
| `go-dev` | 0.4.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/go-dev.zip) | [page](https://clawhub.ai/tenequm/skills/go-dev) | Opinionated Go setup with golangci-lint v2, gofumpt, gotestsum, golang-migrate, and just. Use when starting a Go project, configuring lint, format, test, coverage or CI, writing a Justfile, wiring migrations, or leaving a Makefile workflow. |
| `grill-me` | 0.1.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/grill-me.zip) | [page](https://clawhub.ai/tenequm/skills/grill-me) | Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me". |
| `herdr-faq` | 0.4.1 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/herdr-faq.zip) | [page](https://clawhub.ai/tenequm/skills/herdr-faq) | Launch and drive coding agents (codex, claude, agy) through the Herdr CLI; requires a herdr pane (HERDR_ENV=1). Use before starting or prompting a herdr subagent, and when a herdr command fails or an agent seems stuck or silently lost a prompt. |
| `impactful-writing` | 0.1.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/impactful-writing.zip) | [page](https://clawhub.ai/tenequm/skills/impactful-writing) | Write clear, emotionally resonant, and well-structured content that readers remember and act upon. Use when writing or editing any text - Twitter posts, articles, documentation, emails, comments, updates - for maximum clarity, engagement, and impact. |
| `lance-format` | 0.19.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/lance-format.zip) | [page](https://clawhub.ai/tenequm/skills/lance-format) | Deep reference for Lance v12 columnar format, its Rust crates, and pylance - file encodings, table format, indexes, schema evolution, time travel. Use when building on the Lance crates or reading .lance datasets, not the LanceDB product. |
| `mcp-best-practices` | 1.2.1 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/mcp-best-practices.zip) | [page](https://clawhub.ai/tenequm/skills/mcp-best-practices) | Build, harden, and debug production MCP servers with the TypeScript SDK. Use when writing or reviewing an MCP server - transports, tool schemas, errors, OAuth, token bloat, SDK migrations, MCP Apps, Registry. Assumes a server already exists. |
| `mpp` | 0.10.2 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/mpp.zip) | [page](https://clawhub.ai/tenequm/skills/mpp) | Build with MPP (Machine Payments Protocol), open machine-to-machine payments over HTTP 402. Use for paid APIs, payment-gated endpoints, agent payment flows, MCP tool payments, or metered billing. Covers mppx (TS), pympp, and mpp Rust SDKs. |
| `okf-project-knowledge-base` | 0.2.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/okf-project-knowledge-base.zip) | [page](https://clawhub.ai/tenequm/skills/okf-project-knowledge-base) | Durable project knowledge as Git-native OKF bundles (docs/knowledge/, one concept per file, with provenance and trust tiers). Use to record a decision, finding, or rule that must outlive the session. Not session state or agent instructions. |
| `polish` | 3.1.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/polish.zip) | [page](https://clawhub.ai/tenequm/skills/code-polish) | Pre-release code review - lint and type checks, parallel review agents (cleanliness, design, efficiency, side-effect gating), findings validated, fixes on approval. Reviews a GitHub PR when given one. Run before committing, pushing, or on a PR. |
| `polish-new` | 0.1.2 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/polish-new.zip) | [page](https://clawhub.ai/tenequm/skills/polish-new) | Pre-release code review that converges - parallel review agents sized to the diff, findings validated against evidence in a run ledger, fixes on approval, then re-reviews its own fixes until a round warrants no edits. Run on /polish-new. |
| `pre-compact` | 0.1.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/pre-compact.zip) | [page](https://clawhub.ai/tenequm/skills/pre-compact) | Prepare the session for context compaction - write a handoff file a fresh session can continue from, propose updates to the project's durable docs, apply them on approval or with `auto`. Use before compacting or clearing context, or on "pre-compact". |
| `python-dev` | 0.3.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/python-dev.zip) | [page](https://clawhub.ai/tenequm/skills/python-dev) | Opinionated Python development setup with uv, ty, ruff, pytest, lefthook, and just. Use when creating a new Python project, writing or fixing pyproject.toml, or configuring linting, formatting, type checking, testing, git hooks, or CI. |
| `reset-context-contamination` | 0.1.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/reset-context-contamination.zip) | [page](https://clawhub.ai/tenequm/skills/reset-context-contamination) | Discards this thread's accumulated drafts and framings and re-derives the task from a clean problem statement. Use when the user says the thread is contaminated, the conversation is going in circles, or that they want a fresh take. |
| `rust-dev` | 0.6.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/rust-dev.zip) | [page](https://clawhub.ai/tenequm/skills/rust-dev) | Day-1 guide to building well in Rust - ownership, errors as values, String vs &str, Box/Rc/Arc, anyhow vs thiserror, and a crate shortlist (tokio, serde, axum, sqlx). Use when starting a Rust project, fighting the borrow checker, or picking crates. |
| `skills-best-practices` | 0.9.0 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/skills-best-practices.zip) | [page](https://clawhub.ai/tenequm/skills/skills-best-practices) | Opinionated best practices for building Agent Skills - SKILL.md structure, frontmatter, description writing, progressive disclosure, testing, distribution. Use when creating or reviewing a skill, or debugging why one will not trigger. |
| `solana-development` | 0.7.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/solana-development.zip) | [page](https://clawhub.ai/tenequm/skills/solana-development) | Build, test, deploy, and audit Solana programs with Anchor or native Rust, plus ZK Compression (Light Protocol). Use for Solana contracts, token operations, compute optimization, deployment, program audits, or compressed tokens and PDAs. |
| `standard-readme` | 0.1.5 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/standard-readme.zip) | [page](https://clawhub.ai/tenequm/skills/standard-readme) | Writes or audits READMEs against the Standard Readme spec. Use whenever the user asks to create, rewrite, improve, audit, or fix a README, or asks about README quality or structure - even if they never mention "standard readme". |
| `swift-macos` | 0.8.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/swift-macos.zip) | [page](https://clawhub.ai/tenequm/skills/swift-macos) | macOS apps with Swift 6.3, SwiftUI, SwiftData, Swift Concurrency, Foundation Models, Swift Testing, and ScreenCaptureKit. Use when building native Mac apps - windows, menus, SwiftData, on-device AI, capture, AppKit bridges, notarization. |
| `tanstack` | 0.4.5 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/tanstack.zip) | [page](https://clawhub.ai/tenequm/skills/tanstack) | Type-safe React with TanStack Query (fetching, caching, mutations), Router (file-based routing, search params, loaders), and Start (SSR, server functions). Use for react-query, server state, typed search params, route loaders, or SSR. |
| `typescript-dev` | 0.3.5 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/typescript-dev.zip) | [page](https://clawhub.ai/tenequm/skills/typescript-dev) | Full-stack TypeScript with Vite 8, React 19, Tailwind v4, shadcn/ui, Biome, Vitest, and Hono 4. Use when setting up or working in a TypeScript project - components, styling, build and HMR, tests, lint/CI, or a Hono API with type-safe RPC. |
| `update-skill` | 0.8.4 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/update-skill.zip) | [page](https://clawhub.ai/tenequm/skills/update-skill) | Thorough on-demand refresh of one skill in a skills repo - researches usage, upstream, and docs in parallel, gates twice for approval, bumps version, updates CHANGELOG, validates, commits, watches CI. Use to check a skill's freshness. |
| `x402` | 0.11.3 | [zip](https://github.com/tenequm/skills/releases/download/skills-latest/x402.zip) | [page](https://clawhub.ai/tenequm/skills/x402-development) | Build internet-native payments with x402 - HTTP 402 for on-chain micropayments, no accounts or API keys. Use for paid APIs, paywalled content, agent payment flows, or per-call MCP tools. TypeScript, Python, and Go SDKs across EVM and Solana. |
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
