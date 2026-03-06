# Development Resources

Comprehensive collection of official documentation, development tools, learning paths, and community resources for Solana program development.

## Official Documentation

### Solana Core
- [Solana Docs](https://solana.com/docs/) - Official Solana documentation
- [Solana Cookbook](https://solana.com/developers/cookbook) - Recipes for common Solana tasks
- [Solana Courses](https://solana.com/developers/courses/) - Official learning paths
- [Program Examples](https://github.com/solana-developers/program-examples) - Multi-framework examples
- [Developer Bootcamp 2024](https://github.com/solana-developers/developer-bootcamp-2024)

### Anchor Framework
- [Anchor Docs](https://www.anchor-lang.com/docs) - Official Anchor documentation
- [Anchor Book](https://book.anchor-lang.com/) - Comprehensive Anchor guide
- [Anchor by Example](https://examples.anchor-lang.com/) - Example programs
- [Anchor Lang Docs](https://docs.rs/anchor-lang) - API documentation
- [Anchor SPL Docs](https://docs.rs/anchor-spl) - SPL integration helpers
- [Anchor GitHub](https://github.com/coral-xyz/anchor) - Framework source code

### SPL Programs
- [SPL Documentation](https://spl.solana.com/) - Solana Program Library docs
- [Token Program](https://github.com/solana-program/token) - SPL Token source
- [Token-2022](https://github.com/solana-program/token-2022) - Next-gen token program
- [Associated Token Account](https://github.com/solana-program/associated-token-account)
- [Token Metadata](https://github.com/solana-program/token-metadata)
- [Metaplex Token Metadata](https://github.com/metaplex-foundation/mpl-token-metadata)

## Example Programs

### Official Examples
- [Program Examples](https://github.com/solana-developers/program-examples) - Comprehensive examples in multiple frameworks
- [Anchor Examples](https://github.com/coral-xyz/anchor/tree/master/tests) - Official Anchor test programs
- [Developer Bootcamp](https://github.com/solana-developers/developer-bootcamp-2024) - Workshop materials

### Production Protocols (for studying)
- [Anchor Framework](https://github.com/coral-xyz/anchor) - The framework source itself
- [Raydium AMM](https://github.com/raydium-io/raydium-cp-swap) - DEX protocol example
- [Kamino Lending](https://github.com/Kamino-Finance/klend) - Lending protocol
- [Squads Multisig](https://github.com/Squads-Protocol/v4) - Multisig protocol

## Development Tools

### IDEs & Playgrounds
- [Solana Playground](https://beta.solpg.io/) - Browser-based IDE for Solana programs
- [Anchor Playground](https://www.anchor-lang.com/playground) - Test Anchor programs online
- [Rust Playground](https://play.rust-lang.org/) - Test Rust snippets

### CLI & Tooling
- [Solana CLI](https://docs.solana.com/cli) - Command-line tools reference
- [Anchor CLI](https://www.anchor-lang.com/docs/cli) - Anchor command reference
- [Solana Explorer](https://explorer.solana.com/) - View transactions and accounts
- [Solana FM](https://solana.fm/) - Alternative explorer with better UX
- [Solscan](https://solscan.io/) - Popular block explorer
- [XRAY](https://xray.helius.dev/) - Transaction viewer by Helius

### Testing Frameworks
- [Mollusk](https://github.com/anza-xyz/mollusk) - Lightweight test harness for SVM programs
- [Mollusk Docs](https://solana.com/docs/programs/testing/mollusk) - Official Mollusk documentation
- [Solana Test Validator](https://docs.solana.com/developing/test-validator) - Local validator for testing
- [Anchor Testing](https://book.anchor-lang.com/anchor_in_depth/testing.html) - Anchor test framework

### Deployment & Verification
- [Solana Verify](https://github.com/Ellipsis-Labs/solana-verifiable-build) - Verifiable builds
- [Verified Builds Docs](https://solana.com/docs/programs/verified-builds) - Official guide

## Learning Paths

### Official Courses
- [Native Rust Development](https://solana.com/developers/courses/native-onchain-development) - Build with native Rust
- [Anchor Development](https://solana.com/developers/courses/onchain-development) - Build with Anchor
- [Program Security](https://solana.com/developers/courses/program-security) - Security fundamentals

### Community Tutorials
- [RareSkills Solana Course](https://www.rareskills.io/solana-tutorial) - Comprehensive course for EVM developers
- [Anchor for EVM Developers](https://0xkowloon.gitbook.io/anchor-for-evm-developers) - Quick Anchor intro
- [Ackee Solana Handbook](https://ackee.xyz/solana/book/latest/) - Development guide

### Rust Learning
- [Rust Book](https://doc.rust-lang.org/book/) - Official Rust programming language book
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/) - Learn Rust through examples

### Advanced Topics
- [Solana Architecture](https://docs.solana.com/cluster/overview) - How Solana works
- [Sealevel Runtime](https://docs.solana.com/developing/programming-model/overview) - SVM execution model
- [Account Model](https://solana.com/docs/core/accounts) - Deep dive into accounts

## Community & Support

### Q&A Platforms
- [Solana Stack Exchange](https://solana.stackexchange.com/) - Q&A for Solana development
- [Anchor Discussions](https://github.com/coral-xyz/anchor/discussions) - GitHub discussions

### Chat & Forums
- [Solana Discord](https://discord.gg/solana) - Official Solana community
- [Anchor Discord](https://discord.gg/srmqvxf) - Anchor-specific support
- [Solana Tech Discord](https://discord.gg/solana) - Technical discussions

### Blogs & Newsletters
- [Helius Blog](https://www.helius.dev/blog) - Frequent Solana developer content
- [Solana Foundation Blog](https://solana.com/news) - Official updates
- [Pine Analytics Substack](https://substack.com/@pineanalytics1) - Protocol deep dives

## Developer Tools & Libraries

### Rust Crates
- [solana-program](https://docs.rs/solana-program) - Core program library
- [anchor-lang](https://docs.rs/anchor-lang) - Anchor framework
- [anchor-spl](https://docs.rs/anchor-spl) - SPL token integration
- [borsh](https://docs.rs/borsh) - Binary serialization
- [spl-token](https://docs.rs/spl-token) - Token program library
- [spl-token-2022](https://docs.rs/spl-token-2022) - Token Extensions program

### TypeScript/JavaScript

**dApp Client (recommended for frontends):**
- [@solana/client](https://www.npmjs.com/package/@solana/client) + [@solana/react-hooks](https://www.npmjs.com/package/@solana/react-hooks) - Framework-kit: wallet connection, React hooks, SOL/SPL transfers, transaction pool ([GitHub](https://github.com/solana-foundation/framework-kit))
- [@solana/web3-compat](https://www.npmjs.com/package/@solana/web3-compat) - Drop-in bridge for migrating `@solana/web3.js` v1 code to Kit primitives

**Low-level SDK:**
- [@solana/kit](https://solanakit.org) - Solana JavaScript SDK v6 (functional, tree-shakeable). Use for server-side scripts, bots, CLIs
- [@solana/compat](https://www.npmjs.com/package/@solana/compat) - Bridge between Kit 6.x and legacy `@solana/web3.js` v1 types

**Framework-specific:**
- [@coral-xyz/anchor](https://www.npmjs.com/package/@coral-xyz/anchor) - Anchor TypeScript client (requires `@solana/web3.js` v1 as peer dependency)
- [@solana/spl-token](https://www.npmjs.com/package/@solana/spl-token) - SPL Token JS library
- [Umi Framework](https://github.com/metaplex-foundation/umi) - Modular framework by Metaplex

> **Note:** `@solana/web3.js` v1 is in maintenance mode. For new dApps, use framework-kit (`@solana/client` + `@solana/react-hooks`). For server-side/CLI code, use `@solana/kit` 6.x. The only reason to install `@solana/web3.js` is as a peer dependency required by Anchor or Light Protocol SDKs. See [client-development.md](client-development.md) for the full decision guide.

### Python
- [solana-py](https://github.com/michaelhly/solana-py) - Solana Python SDK
- [anchorpy](https://github.com/kevinheavey/anchorpy) - Anchor Python client

## RPC Providers

### Free Tier Available
- [Helius](https://www.helius.dev/) - Developer-friendly RPC with generous free tier
- [QuickNode](https://www.quicknode.com/) - Global RPC network
- [Alchemy](https://www.alchemy.com/solana) - RPC with enhanced APIs
- [Triton](https://triton.one/) - High-performance RPC
- [Public RPC Endpoints](https://docs.solana.com/cluster/rpc-endpoints) - Free public endpoints

## Developer Communities

### Learning Communities
- [Solana Developers](https://github.com/solana-developers) - Official developer org
- [Superteam](https://superteam.fun/) - Global Solana community
- [Blueshift](https://learn.blueshift.gg/) - Interactive learning platform

### Regional Communities
- [Superteam Germany](https://superteam.fun/germany)
- [Superteam India](https://superteam.fun/india)
- [Superteam Vietnam](https://superteam.fun/vietnam)
- [Superteam LatAm](https://superteam.fun/latam)

## Additional Resources

### Developer Guides
- [Solana Developer Guide](https://solana.com/developers/guides) - How-to guides
- [Solana Bootcamp](https://github.com/solana-developers/developer-bootcamp-2024) - Workshop materials
- [Anchor Examples Repo](https://github.com/coral-xyz/anchor/tree/master/tests) - Anchor test programs

### Tool Documentation
- [Cargo Build SBF](https://docs.solana.com/cli/deploy-a-program) - Building programs
- [Solana Program Deploy](https://docs.solana.com/cli/deploy-a-program) - Deployment guide
- [Solana Keygen](https://docs.solana.com/cli/wallets/paper) - Keypair management

### Ecosystem Tools
- [Metaplex](https://www.metaplex.com/) - NFT infrastructure
- [Squads](https://squads.so/) - Multisig and treasury management
- [Dialect](https://www.dialect.to/) - Messaging and notifications

## Version Information

**Current versions (as of February 2026):**
- Latest Anchor: 0.32.1
- Recommended Solana CLI: 2.3.0+ (Agave)
- Rust minimum: 1.89.0+ (required for Anchor 0.32.0+)
- @solana/client (framework-kit): 1.7.0
- @solana/react-hooks: 1.4.1
- @solana/kit: 6.1.0 (standalone) / 5.x (used internally by framework-kit)
- Solana program library: 2.0+

**Updating tools:**
```bash
# Update Solana CLI
solana-install update

# Update Anchor
avm install latest
avm use latest

# Update Rust
rustup update
```

---

**Note:** For security-specific resources, vulnerability databases, audit reports, and security tools, see the `solana-security` skill.
