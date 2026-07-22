# Skill Card

## Description

rust-dev is a practical day-1 guide to building applications in Rust well: the ownership mental model, day-1 type and error-handling decisions, idioms and anti-patterns, a short crate shortlist, and opinionated Cargo/clippy/rustfmt configuration. It targets developers starting Rust projects or coming to Rust from Python, JavaScript, Go, Java/C#, or C++.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers starting a new Rust CLI, service, or library, or learning Rust from another language, who want decided defaults (String vs &str, anyhow vs thiserror, crate choices) instead of open-ended research. The agent uses it to answer Rust design questions, scaffold Cargo.toml/lint/format config, and guide testing, build-speed, release, and performance work via the bundled references.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Tools the skill instructs the agent to use: rustup, cargo (check/run/test/clippy/fmt), rust-analyzer; optionally bacon, kache/sccache, criterion/divan, dist, release-plz, cargo-zigbuild. None are prerequisites for reading the skill.

## Known Risks and Mitigations

Risk: The skill generates Cargo.toml, lint, toolchain, and CI configuration that can overwrite existing project files, and its setup commands install toolchains and crates (rustup, cargo install, cargo add).

Mitigation: Review generated files and commands before execution; apply configuration changes on a git branch and diff against the existing setup.

Risk: Version-pinned guidance goes stale: crate recommendations (e.g. chrono soft-deprecation vs pre-1.0 jiff), clippy lint locations, and "as of" statements are tied to the tracked upstream versions in metadata.upstream.

Mitigation: The CHANGELOG records when guidance was last verified against upstream; confirm current crate versions and stability notes (especially pre-1.0 crates) before committing to them in production code.

Risk: Opinionated defaults (unsafe_code = "forbid", deny-level clippy, edition 2024) can break builds when dropped into existing codebases that violate them.

Mitigation: The skill frames these as new-project defaults; for existing projects, introduce lints incrementally and downgrade forbid to deny where FFI exists, as the config comments describe.

## References

- The Rust Book: https://doc.rust-lang.org/book/
- Tracked upstream versions: rust@1.95.0, axum@0.8.9, reqwest@0.13.3, sqlx@0.9.0, jiff@0.2.24, kache@0.9.0, dist@0.32.0, release-plz@0.5
- blessed.rs crate guide: https://blessed.rs/crates
- Source: https://github.com/tenequm/skills/tree/main/skills/rust-dev

## Skill Output

Output type(s): Rust code and design guidance, project configuration files (Cargo.toml, rustfmt.toml, rust-toolchain.toml, CI workflows), and shell commands.

Output format: Rust and TOML code blocks in Markdown; files written into the user's project when requested.

Output parameters: Follows the project structure and configuration templates embedded in SKILL.md.

Other properties: Setup commands download toolchains and dependencies from the network; the skill itself makes no external calls.

## Skill Version

0.4.1

## Ethical Considerations

Generated code and configuration should be reviewed and compiled/tested by the user before adoption; the skill's opinionated decisions trade generality for speed and may not fit every codebase. No sensitive-data handling is involved.
