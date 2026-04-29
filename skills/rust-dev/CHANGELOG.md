# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-29

### Added
- Initial release. Practical day-1 Rust development skill.
- SKILL.md covering the Rust mental model (ownership, aliasing XOR mutability, errors as values, traits not interfaces, the borrow checker as design oracle), the 3 questions for every function signature, day-1 decision table, idioms to internalize early, "coming from X" deltas (Python/JS, Go, Java/C#, C++), the crate shortlist, top anti-patterns, what to defer, minimal Cargo.toml + lints + rustfmt.toml + rust-toolchain.toml, project structure, learning path.
- references/ownership-and-types.md: ownership, borrowing, lifetimes, `String`/`&str`/`Cow`, `Vec`/slice/array, smart pointers (`Box`/`Rc`/`Arc`/`RefCell`/`Mutex`), `MutexGuard` across `.await` pitfall, self-referential struct trap.
- references/error-handling.md: `Result`, `?`, `anyhow` for apps, `thiserror` for libraries, custom error enums, `panic!` vs `unwrap` vs `expect`, `From`-driven error conversion.
- references/traits-and-generics.md: trait definitions, generic vs `impl Trait` vs `dyn Trait`, object safety, common derives, `From`/`Into`/`TryFrom`, `Display`/`Debug`, blanket impls, the orphan rule, iterator trait, common stdlib traits, generics flavors (type/lifetime/const).
- references/async-basics.md: `tokio` runtime, `#[tokio::main]`, spawning, `Send`/`Sync`/`'static` bounds, `MutexGuard` pitfalls, `spawn_blocking`, `select!`/`join!`/`try_join!`, channels, async in traits, common pitfalls.
- references/crate-shortlist.md: minimal usage examples for `serde`/`serde_json`, `tokio`, `anyhow`, `thiserror`, `clap`, `reqwest`, `tracing`, `axum`, `sqlx`, `chrono`, plus an honorable-mentions table.

Verified against: rust@1.95.0
