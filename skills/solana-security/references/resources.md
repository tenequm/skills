# Resources

Comprehensive collection of official documentation, security guides, audit reports, and learning materials for Solana development and security.

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

### SPL Programs
- [SPL Documentation](https://spl.solana.com/) - Solana Program Library docs
- [Token Program](https://github.com/solana-program/token) - SPL Token source
- [Token-2022](https://github.com/solana-program/token-2022) - Next-gen token program
- [Associated Token Account](https://github.com/solana-program/associated-token-account)
- [Token Metadata](https://github.com/solana-program/token-metadata)
- [Metaplex Token Metadata](https://github.com/metaplex-foundation/mpl-token-metadata)

## Security Resources

### Curated Security Lists
- [Awesome Solana Security (0xMacro)](https://github.com/0xMacro/awesome-solana-security) - **Actively maintained**, comprehensive resource list
- [Rektoff Security Roadmap](https://github.com/Rektoff/Security-Roadmap-for-Solana-applications) - Full lifecycle security strategy
- [SlowMist Best Practices](https://github.com/slowmist/solana-smart-contract-security-best-practices) - Common pitfalls with examples
- [Ackee Solana Handbook](https://ackee.xyz/solana/book/latest/) - Comprehensive development guide

### Security Guides & Articles
- [Helius Security Guide](https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security) - Common vulnerabilities explained
- [Neodyme Breakpoint Workshop](https://github.com/neodyme-labs/neodyme-breakpoint-workshop) - Hands-on security training
- [Solana Security Course](https://solana.com/developers/courses/program-security) - Official security course
- [Asymmetric Research CPI Vulnerabilities](https://blog.asymmetric.re/invocation-security-navigating-vulnerabilities-in-solana-cpis/)
- [Ottersec Lamport Transfers](https://osec.io/blog/2025-05-14-king-of-the-sol) - SOL transfer vulnerabilities
- [Infect3d Auditing Essentials](https://www.infect3d.xyz/blog/solana-quick-start)

### Vulnerability Collections
- [Urataps Audit Examples](https://github.com/urataps/solana-audit-examples) - Programs with vulnerabilities
- [ImmuneBytes Attack Vectors](https://github.com/ImmuneBytes-Security-Audit/Blockchain-Attack-Vectors/tree/main/Solana%20Attack%20Vectors)
- [Exvul Security Guide](https://exvul.com/rust-smart-contract-security-guide-in-solana/)
- [Nirlin Advanced Vulnerabilities](https://substack.com/inbox/post/164534668)

### Video Tutorials
- [Zigtur Security Walkthrough](https://www.youtube.com/watch?v=xd6qfY-GDYY)
- [M4rio Security Walkthrough](https://www.youtube.com/watch?v=q4z8tIi43lg)

### Token-2022 Security
- [Offside Token-2022 Part 1](https://blog.offside.io/p/token-2022-security-best-practices-part-1)
- [Offside Token-2022 Part 2](https://blog.offside.io/p/token-2022-security-best-practices-part-2)
- [Neodyme Token-2022 Security](https://neodyme.io/en/blog/token-2022)

### Deep Dives & Research
- [r0bre's 100 Daily Solana Tips](https://accretionxyz.substack.com/p/r0bres-100-daily-solana-tips)
- [Accretion Hidden IDL Instructions](https://accretionxyz.substack.com/p/hidden-idl-instructions-and-how-to)
- [Farouk ELALEM Under the Hood](https://ubermensch.blog/under-the-hood-of-solana-program-execution-from-rust-code-to-sbf-bytecode)
- [Lucrative_Panda Security History](https://medium.com/@lucrativepanda/a-comprehensive-analysis-of-solanas-security-history-all-incidents-impacts-and-evolution-up-to-1b1564c7ddfe)

## Essential Codebases to Study

Study these production codebases to learn security patterns:

### Framework & Core Programs
- [Anchor Framework](https://github.com/solana-foundation/anchor) - The framework itself
- [Solana System Program](https://github.com/solana-program/system)
- [SPL Token Program](https://github.com/solana-program/token)
- [Token-2022](https://github.com/solana-program/token-2022)

### Production Protocols
- [Raydium AMM](https://github.com/raydium-io/raydium-cp-swap) - DEX protocol
- [Kamino Lending](https://github.com/Kamino-Finance/klend) - Lending protocol
- [Squads Multisig](https://github.com/Squads-Protocol/v4) - Multisig protocol

## Audit Reports

Study real security audits to learn from actual vulnerabilities:

### Code4rena
- [Pump Science](https://code4rena.com/reports/2025-01-pump-science) - 2 High, 3 Medium

### Sherlock
- [Orderly](https://audits.sherlock.xyz/contests/524/report) - 2 High, 1 Medium
- [WOOFi](https://audits.sherlock.xyz/contests/535/report) - 2 High, 3 Medium

### Cantina
Contact `0xmorph` in Cantina Discord for read access:
- [Grass](https://cantina.xyz/competitions/3211ee0d-133f-43a0-837e-8dc1ecfaa424) - 13 High, 6 Medium
- [Olas](https://cantina.xyz/competitions/829164bf-7fba-4b84-a6b8-76652205bd97) - 2 High, 3 Medium
- [Tensor](https://cantina.xyz/competitions/21787352-de2c-4a77-af09-cc0a250d1f04) - 5 High, 10 Medium
- [ZetaChain](https://cantina.xyz/competitions/80a33cf0-ad69-4163-a269-d27756aacb5e) - 6 High, 27 Medium
- [Inclusive Finance](https://cantina.xyz/competitions/3eff5a8f-b73a-4cfe-8c54-546b475548f0) - 45 High, 25 Medium
- [Reserve Index](https://cantina.xyz/code/8b94becd-54e7-41cd-88e6-caae7becc76a) - 10 High, 11 Medium

## Learning Paths

### For EVM Developers
- [RareSkills Solana Course](https://www.rareskills.io/solana-tutorial) - Ethereum to Solana
- [0xkowloon Anchor for EVM](https://0xkowloon.gitbook.io/anchor-for-evm-developers)

### For Rust Learners
- [Rust Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/index.html)

### Native Rust (Non-Anchor)
- [Solana Native Rust Docs](https://solana.com/docs/programs/rust)
- [Native Development Course](https://solana.com/developers/courses/native-onchain-development)

### Blueshift Challenges
- [Blueshift Courses](https://learn.blueshift.gg/) - Anchor and Pinocchio

## Tools

### Development
- [Solana Playground](https://beta.solpg.io/) - Browser-based IDE
- [Rust Playground](https://play.rust-lang.org/) - Test Rust snippets

### Security & Analysis
- [Trident](https://github.com/Ackee-Blockchain/trident) - Fuzz testing framework (v0.12.0+: Token-2022 program support, Manually Guided Fuzzing for targeted instruction sequences, solana-sdk 2.3+ compatibility)
- [Certora Prover](https://docs.certora.com/en/latest/docs/solana/index.html) - Formal verification
- [Sec3 IDL Guesser](https://github.com/sec3-service/IDLGuesser) - Reverse engineer IDLs
- [Anchor X-ray](https://github.com/crytic/anchorx-ray) - Visualize accounts (Trail of Bits)
- [Anchor Version Detector](https://github.com/johnsaigle/anchor-version-detector) - Compatibility checker

### Testing
- [Anchor Test Framework](https://book.anchor-lang.com/anchor_in_depth/testing.html)
- [Solana Test Validator](https://docs.solana.com/developing/test-validator)

## CTFs & Practice

### Capture The Flag
- [Ackee Solana CTF](https://github.com/Ackee-Blockchain/Solana-Auditors-Bootcamp/tree/master/Capture-the-Flag)

### Bootcamps
- [Rektoff 6-Week Bootcamp](https://www.rektoff.xyz/bootcamp) - Free, Solana Foundation supported
- [Ackee Auditors Bootcamp](https://ackee.xyz/solana-auditors-bootcamp)

## Community & Support

### Q&A Platforms
- [Solana Stack Exchange](https://solana.stackexchange.com/)

### Blogs & Newsletters
- [Helius Blog](https://www.helius.dev/blog) - Frequent Solana content
- [Pine Analytics Substack](https://substack.com/@pineanalytics1) - Protocol deep dives

## Security Firms

Top firms for Solana security audits:
- [Runtime Verification](https://runtimeverification.com/)
- [OtterSec](https://osec.io/)
- [Neodyme](https://neodyme.io/en/)
- [Sec3](https://www.sec3.dev/)
- [Zellic](https://www.zellic.io/)
- [Ackee Blockchain](https://ackee.xyz/)
- [Hexens](https://hexens.io/)
- [Trail of Bits](https://www.trailofbits.com/)
- [Kudelski Security](https://kudelskisecurity.com/)
- [Cantina](https://cantina.xyz/)
- [Certora](https://www.certora.com/)
- [Sherlock](https://www.sherlock.xyz/)

## Version Information

- Latest Anchor version: 0.32.1
- Recommended Solana CLI: 2.3.0+ (Agave)
- Rust minimum version: 1.89.0+ (required for Anchor 0.32.0+)

---

**Note:** This is a curated collection from the Awesome Solana Security repository and other trusted sources. Resources are selected for their quality, maintenance status, and relevance to modern Solana development practices.
