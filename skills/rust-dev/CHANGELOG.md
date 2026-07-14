# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-07-14

### Added
- New reference references/releasing.md: shipping a Rust binary. Two routes, presented as alternatives rather than one blessed path - `dist` (formerly cargo-dist; community-maintained again after axo wound down, and the batteries-included default) versus a hand-rolled `release-plz` + `cargo-zigbuild` pipeline given as one worked reference implementation. Covers the design decisions that are not obvious from the YAML: build binaries before publishing (crates.io publishes are irreversible), detect a pending release via the git tag because release-plz's dry-run always reports `releases_created=false`, per-job concurrency so a cancel cannot kill a release mid-publish into an unrecoverable state, a PAT rather than `GITHUB_TOKEN` so the release PR actually triggers CI, the `[profile.dist]`/`[profile.release]` split, cross-compiling every target from one Linux runner with `cargo-zigbuild` plus the cross-target feature-unification trap, fanning out to cargo-binstall (with the crate-name-vs-binary-name URL template gotcha), Homebrew, and Nix from a single build, shipping pre-generated shell completions, and guarding `exclude` against dropping a file the code embeds via `include_str!` (an invisible `cargo install` break). Notes why no monorepo task runner appears.
- references/dev-environment.md: kache (https://github.com/kunobi-ninja/kache) is now the recommended build cache on both macOS and Linux - install and `kache init` setup, the `[cache.remote]` S3 block, and a quirks table covering the traps that actually cost time: the 50GiB default store cap (LRU-evicts the expensive artifacts first and mimics broken cross-path reuse), count vs cost-weighted hit rate, `cache_executables = false` by default, `kache sync --push` filtering to workspace members only, the service daemon not inheriting shell env (use an AWS profile for S3 credentials), the base-vs-virtual-hosted endpoint, upgrades orphaning the launchd/systemd service, keys encoding toolchain identity rather than machine identity (prefix per toolchain, not per machine), `key_salt` for toolchain changes the key cannot see, `extra_inputs` for macro-read files such as sqlx's `.sqlx/` and `migrations/` (a stale-hit hazard), and the container/NFS cache-directory rule. Plus a diagnosis recipe (`kache stats`, `kache list --sort size`, `kache why-miss`, the `KACHE_LOG=kache=warn` path-leak detector) and a note that upgrades never need a cache wipe.
- references/dev-environment.md CI section: `kunobi-ninja/kache-action@v1` as the upgrade path once `Swatinem/rust-cache` is outgrown, with the caveat that cross-machine hits require an exactly matching toolchain.

- SKILL.md anti-patterns: reading untrusted input with `.lines()`/`read_line`, which allocate without bound (std's docs warn an attacker can send bytes forever without a newline); bound with `Read::take(n)` and drain with `BufRead::skip_until` (stable 1.83).
- references/async-basics.md: the `!Send` compile error on a `std::sync::MutexGuard` held across `.await` is a different problem from the *design* question of holding a `tokio::sync::Mutex` across `.await` - which is sometimes correct, single-flight being the clearest case (N concurrent cold-start callers coalesce into one expensive load). New pitfall: `impl Stream` in a signature does not make the body stream.
- references/performance.md: `into_iter()` rather than `.iter()` when transforming an owned collection, as a peak-memory lever. New section on why high RSS is usually allocator retention rather than a leak, and why swapping the global allocator to `jemalloc`/`mimalloc` is a measure-first move rather than a free win - the real lever is the transient peak.
- references/testing.md: `cargo test` uses the `test` profile (inherits `dev`, so `debug-assertions` is on), which means a `debug_assert!` inside a *dependency* can fail the suite on input that is fine in release. `#![recursion_limit]` is a crate-root attribute and each `tests/*.rs` is its own crate root, so an E0275 trait-solving overflow in an integration binary needs it there, not in `src/lib.rs`. Env-var test pollution: isolating the test that *sets* a variable is not enough - every test that *reads* it must be isolated too.
- references/dev-environment.md: any `RUSTC_WRAPPER` puts the build cache in the failure path, so a broken wrapper surfaces as a baffling compile error - bypass it (`KACHE_DISABLED=1`, or `RUSTC_WRAPPER=`) before trusting the failure. Caveat against `--all-features` in lint/test jobs, which force-enables optional features needing toolchains the runner lacks (CUDA/`nvcc`, GPU SDKs).
- references/releasing.md: one cargo invocation is one feature-resolution graph (so per-target artifacts with different feature sets are impossible by design, not a missing flag), and the cross-target feature leak can originate in a transitive dependency you have no flag to control. `cargo tree -e features` inspects resolved features - `Cargo.lock` does not record them at all. release-plz downgrades `feat:` to a patch bump on 0.x (and `feat!:` to `0.(x+1).0`, not 1.0.0). Squash-merging a release-worthy PR under a `ci:`/`chore:` title erases the `feat:`/`fix:` commit and produces no release. `cargo publish` aborts on a dirty tree (untracked build output counts) - gitignore the output rather than reaching for `--allow-dirty`.

### Changed
- references/dev-environment.md: the "Build speed" section is reorganized around one caching recommendation instead of two platform stories. sccache is retained as the conservative alternative (and as a `KACHE_FALLBACK` chain target) rather than the macOS headline; linker guidance is now a platform note independent of the cache choice. Notes that kache disables incremental compilation while it wraps rustc - the point where its advice diverges from sccache's.
- SKILL.md: reference-list entry for dev-environment.md updated to mention kache and CI; releasing.md added to the list; releasing and distribution added to the description's triggers.

Verified against: kache@0.9.0, dist@0.32.0, release-plz@0.5

## [0.3.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.3.0] - 2026-05-21

### Added
- New reference references/testing.md: a pragmatic, anti-dogma testing guide - what to test vs what to skip, the purity-over-extent reframe, "mock resources, not your own code", reproduce-then-fix regression tests, test organization (tests with the code mirroring the source layout; `tests/` for real integration tests only; `tests/common/mod.rs`; the single-binary `#[path]` layout; fixtures in `tests/fixtures/` via `env!("CARGO_MANIFEST_DIR")` with a fixtures README), doctests, async tests, and a minimal high-value tool kit.
- New reference references/dev-environment.md: development setup and build / dev-loop speed - `cargo check` as the fast inner loop, incremental compilation, platform-aware build-speed guidance (on macOS, set up sccache as a global dependency cache and skip linker tuning; on Linux, `rust-lld` is the default linker since Rust 1.90), a minimal CI workflow recipe built on `actions-rust-lang/setup-rust-toolchain`, dev-profile tuning, and `bacon`.
- New reference references/performance.md: runtime performance of real apps - the measure-first discipline and keeping perf harnesses in a committed home (not `/tmp` or inline shell), profiling (the `profiling` build profile, samply, `dhat` for heap), benchmarking (`benches/` + `harness = false`, criterion vs divan, `std::hint::black_box`, CI regression benchmarking with CodSpeed/Bencher), the `[profile.dist]`-vs-`[profile.release]` split, and common real wins.
- references/async-basics.md: note that `tokio::fs` is backed by `spawn_blocking` (no true async file I/O on most OSes) plus batching guidance.
- SKILL.md Day-1 Setup: `cargo update`, with a note that it only moves within existing semver ranges.
- SKILL.md idioms: the compiler-as-worklist refactor trick (a mandatory no-`Default` field turns every constructor into a compile error).
- SKILL.md: formatting-discipline note in the rustfmt section; "testing", "benchmarking", and build-speed triggers added to the skill description.

### Changed
- Adopted sqlx 0.9.0 (released 2026-05-06): bumped the dependency in references/crate-shortlist.md from 0.8 to 0.9 and added a 0.9 notes callout (repo moved to the transact-rs org; MSRV raised to 1.94; runtime `query()`/`query_as()` functions now take `impl SqlSafeStr` - the `query_as!` macro is unaffected).
- Bumped tracked axum version 0.8.8 -> 0.8.9.
- SKILL.md: dropped `unwrap_used`/`expect_used` from the Minimal Cargo.toml lints - both are clippy `restriction`-group lints (a deliberate per-project opt-in, not a day-1 default), and linting `expect_used` discourages `.expect("reason")`, the recommended way to document a can't-fail invariant. Anti-pattern #4 refined accordingly; references/error-handling.md now covers `unwrap_used` as an opt-in with the companion `clippy.toml` `allow-unwrap-in-tests` setting.
- SKILL.md: reframed the `Rc<RefCell>`/`Arc<Mutex>` anti-pattern to first ask whether shared mutable state is needed at all (plain ownership or a channel is usually cleaner).

### Fixed
- references/crate-shortlist.md: axum 0.8 MSRV corrected from 1.78 to 1.80 (raised in axum 0.8.9); jiff example now imports `ToSpan` (the `1.hour()` snippet did not compile); added a reqwest 0.13 notes callout (rustls is now the default TLS backend, `query`/`form` are now opt-in features).
- references/traits-and-generics.md and async-basics.md: "object safety" updated to the current term "dyn compatibility" (renamed in Rust 1.83).
- references/async-basics.md: corrected the `tokio::task::block_in_place` description - it runs a blocking section inside the current task and panics on a `current_thread` runtime; it does not bridge async to sync.
- SKILL.md: the `?`-propagation example uses `toml::from_str` (the canonical API) instead of `toml::from_slice`; the `.gitignore` no longer teaches the retired "ignore `Cargo.lock` for libraries" rule; "Recent sugar" now names the Rust 1.95 feature `if let` guards (not let-chains); clippy `uninlined_format_args` comment corrected to Rust 1.89.0 (mid-2025).
- references/ownership-and-types.md: `Copy` types list corrected to include floats and arrays.
- references/dev-environment.md: clarified that sccache cannot cache proc-macro or other linker-invoking crates.
- references/testing.md: doctest guidance updated for the 2024 edition (compatible doctests are merged); softened two over-absolute claims.

Verified against: rust@1.95.0, axum@0.8.9, reqwest@0.13.3, sqlx@0.9.0, jiff@0.2.24

## [0.2.0] - 2026-05-07

### Changed
- Bumped axum guidance from 0.7 to 0.8 in SKILL.md and references/crate-shortlist.md (path syntax `/{id}` instead of `/:id`, `Option<T>` extractor reworked, `Host` moved to `axum-extra`, MSRV 1.78).
- Bumped reqwest guidance from 0.12 to 0.13 in references/crate-shortlist.md.
- sqlx offline-mode docs: replaced `sqlx-data.json` with `.sqlx/` directory; added notes on `--workspace`, `--check`, and `SQLX_OFFLINE=true`.
- chrono/jiff guidance rewritten: chrono soft-deprecated by maintainer (Jan 2026); jiff is recommended for new code but still pre-1.0. Updated SKILL.md crate table and references/crate-shortlist.md chrono section.
- Refreshed stale "as of April 2026" timestamp in rustfmt section.

### Added
- Brief mention of Rust 1.95 sugar (`cfg_select!` macro, let-chains in match arm guards) in the idioms section of SKILL.md.
- Comment in Cargo.toml lints noting that clippy's `uninlined_format_args` was moved to `pedantic` (allow-by-default).
- Expanded `metadata.upstream` to track volatile crates: `axum`, `reqwest`, `sqlx`, `jiff` alongside `rust`.

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
