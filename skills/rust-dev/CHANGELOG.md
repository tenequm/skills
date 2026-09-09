# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-09-09

### Added

- references/ownership-and-types.md: the two Book-chapter-8 collections gaps the skill was silent on - `HashMap` with the `entry` API (`or_insert`, `or_insert_with`, `or_default`, and why `contains_key` + `insert` hashes twice), and the fact that a string cannot be indexed. `s[0]` does not compile because a byte offset is not a character offset; `.chars()`, `.char_indices()`, and byte-range slicing are what you actually want, and a range that lands mid-character panics.
- SKILL.md "From Python or JavaScript": integer overflow behaves differently per profile. Debug "includes checks for integer overflow that cause your program to _panic_ at runtime"; `--release` drops them and performs "_two's complement wrapping_" - so a passing test suite can still wrap in production. Plus a pointer to the string-indexing material above.
- references/async-basics.md: a "Threads First, Async Second" section. The skill sent CPU-bound work to threads (`performance.md`: "use threads or `rayon`") and then only ever showed tokio. Covers `thread::spawn` and its `'static` bound, `thread::scope` for borrowing stack data without `Arc`, `std::sync::mpsc`, and the classic hang where the original `tx` is never dropped so the receiver loop never ends.
- SKILL.md Project Structure: items are private by default, including to a parent module. `mod config;` makes a module exist without making anything in it reachable - the source of the most common early "why can't I call this" error - with `pub` vs `pub(crate)` and why `pub(crate)` is what makes the `unreachable_pub` lint useful.
- references/testing.md: what a doc comment actually looks like, since the file already told you to keep doctests for public-API examples without showing one. `///` vs `//!`, the `# ` hidden-line trick that lets an example use `?` without showing the boilerplate, and `no_run` vs `ignore`.
- references/traits-and-generics.md: a "Closures and the `Fn` Traits" section. The file taught iterator chains built entirely out of closures while naming `Fn`/`FnMut`/`FnOnce` only in a passing anti-pattern. Covers which trait a closure gets (decided by what it does with its captures, not how it is written), that the three nest, and that `move` and `FnOnce` are unrelated.
- references/crate-shortlist.md (clap): two CLI footguns that only appear once real users touch the binary. A positional argument beginning with `-` is parsed as a flag unless `--` precedes it; and Rust ignores SIGPIPE at startup - std's own comment reads "we set SIGPIPE to ignore when the program starts up in order to prevent this problem" - so `mytool | head -5` fails instead of exiting quietly. Includes the stable `libc::signal` fix and notes `-Zon-broken-pipe` is nightly-only.
- references/async-basics.md: handling SIGTERM, not just Ctrl-C. Nearly every shutdown snippet awaits `tokio::signal::ctrl_c()`, which is SIGINT only, so a service is hard-killed on every container or systemd stop while Ctrl-C keeps working locally. Plus the two follow-on traps: `with_graceful_shutdown` waits for all connections, so one long-lived stream holds shutdown open forever, and `/proc/<pid>/status` `SigCgt` tells you what the shipped binary actually catches.
- references/dev-environment.md: mold's own August 2026 benchmark now quantifies the Linux linker choice - it "links 4.9x faster than LLVM lld and 1.9x faster than wild at the median".
- references/dev-environment.md: the Cargo Book's "Optimizing Build Performance" chapter (added in Rust 1.92), which is the canonical first-party version of most of this page, along with its fuller debug-info recipe - `[profile.dev.package."*"] debug = false` plus an opt-in `[profile.debugging]` - rather than the `line-tables-only` one-liner alone.
- references/dev-environment.md: Cargo's first-party `unused_dependencies` lint, noted as covering the same ground as `cargo machete` but unusable on stable, since "Cargo's linting system is unstable and can only be used on nightly toolchains".
- references/dev-environment.md: kache 0.17/0.18 surface - `[cache.volumes]` volume-local shards (what keeps a restore zero-copy when checkout and store live on different volumes), read-only remotes for untrusted CI as a supply-chain boundary, and `explain_miss` alongside `why-miss` in the diagnosis list.
- references/error-handling.md: a "Wrap at the Boundary, Not Before It" section. `anyhow::Error` is a one-way door, and wrapping a typed error upstream of a retry loop or a status mapping silently destroys the classification that code needed - the retry loop then treats a permanent failure exactly like a retryable one.
- references/crate-shortlist.md: three reqwest 0.13 changes the notes omitted, all of which alter the dependency tree rather than the API - the rustls crypto provider "defaults to aws-lc instead of _ring_", the rustls roots features were dropped for `rustls-platform-verifier`, and native-tls now includes ALPN.
- references/crate-shortlist.md: sqlx 0.9's per-crate `sqlx.toml`, and the packaging regression that "`cargo install --locked sqlx-cli` will no longer work".
- references/crate-shortlist.md (axum): scope a tower layer to the routes it exists for. A `.layer()` on the root `Router` runs on every route, so a rate limiter meant for one expensive endpoint also throttles static assets and health checks, and the first page load exhausts the bucket.
- references/testing.md: never assert a negative wall-clock property. It is not a flaky test that a looser threshold fixes - nothing guarantees the thread is scheduled at all on a loaded runner - so assert the thing you meant (the backend was not hit, the value came from the cache) or control the clock.
- references/testing.md: `cargo nextest bench` now runs benchmark targets through the same runner.
- references/releasing.md: verify the plain `cargo install <crate>` path in a clean container. Teams that ship via Homebrew, Nix, or binstall never exercise the compile-from-crates.io path, so a packaging break can survive several releases.

### Changed

- SKILL.md: the `.gitignore` section claimed committing `Cargo.lock` is "the recommended default for every crate type, libraries included". The Cargo FAQ no longer frames it that way - "whether you do is dependent on the needs of your package" - so the claim now cites the guide's actual wording ("When in doubt, check `Cargo.lock` into the version control system") and keeps the recommendation without overstating its source.
- references/dev-environment.md: the CI recipe now pins `actions-rust-lang/setup-rust-toolchain@v2` and drops `-- -D warnings` from the clippy step. v2.0.0 stopped exporting `RUSTFLAGS="-D warnings"` and sets cargo's `build.warnings` instead (its `build-warnings` input defaults to `deny`), because a `RUSTFLAGS` export silently overrides any `target.*.rustflags` the project set. The `@v1` form and why lint flags must follow `--` are kept for anyone still pinned there.
- references/dev-environment.md: replaced the mold quote. The current README contains no mention of macOS at all, so "mold's own source says outright that 'mold does not support macOS'" was no longer sourceable; the substance is now carried by mold's self-description as a replacement for "existing Unix linkers" plus its ELF-only architecture list.
- references/crate-shortlist.md: sqlx 0.9.0's release date corrected to 2026-05-21 (crates.io publish and release commit), not 2026-05-06.
- SKILL.md + references/crate-shortlist.md: three "as of May 2026" date stamps re-stamped to September 2026 after re-verifying the facts behind them - rustfmt's `imports_granularity` and `group_imports` are still nightly-only (tracking issues #4991 and #5083), and jiff is still 0.2.35 pre-1.0 with its 1.0 issue open.
- SKILL.md: dropped the "Rust 1.89.0" attribution on `uninlined_format_args` moving to `clippy::pedantic`. Clippy's own CHANGELOG lists the same PR under both 1.89 and 1.90, so the entry now says "the 1.89/1.90 cycle" rather than asserting a version upstream is inconsistent about.
- SKILL.md: the Reference Docs list re-describes ownership-and-types, traits-and-generics, async-basics, and error-handling to match what those files now contain, so the router still points at the right file.

### Fixed

- references/dev-environment.md: the kache quirks table said "`local_max_size` defaults to **50GiB**" and told you to raise the cap. Since 0.17.0 the default is "5% of the volume that holds the store, rounded to the nearest GiB, then clamped to 5GiB..=100GiB", with 50GiB only as a probe-failure fallback - so the old advice was wrong on a small disk and on a large one, and the fix is to check what you got rather than assume a number.
- references/project-shape.md: "Cargo ships a lint (`missing_lints_inheritance`) specifically because so many people assume otherwise" implied a safety net a stable-toolchain reader does not have. The lint exists, but Cargo's whole lint system is nightly-only, so on stable nothing warns about a member that omits `[lints] workspace = true`.

### Security

- references/dev-environment.md: the toolchain-currency argument now includes Rust 1.98.1 (2026-09-03), a one-line point release fixing "a miscompilation in generating vtables" - 1.98.0 could emit a vtable with a null pointer where a function pointer belonged, which is undefined behavior in code that compiled cleanly. No new RustSec advisory since the last refresh touches any crate this skill names.

Verified against: rust@1.98.1, reqwest@0.13.5, kache@0.18.0, release-plz-action@0.5.135

## [0.5.1] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [0.5.0] - 2026-08-26

### Added

- SKILL.md: Rust 1.96-1.98 sugar and tooling - `assert_matches!`/`debug_assert_matches!` (1.96), plus let-chains (stable in edition 2024 since 1.88) and async closures (1.85), which the "Recent sugar" section skipped even though the skill defaults to edition 2024.
- New reference references/project-shape.md, and a pointer to it from SKILL.md's Project Structure section: the multi-crate cliff the skill never covered. Workspaces and `workspace.dependencies` (features can be added by a member, never subtracted), `[workspace.lints]` plus the trap that `[lints] workspace = true` is not implicitly inherited - a member that omits it is silently unlinted, which is why Cargo ships `missing_lints_inheritance`; feature flags including `dep:` (1.60) and the `foo?/bar` conditional form, and why features must be additive; `build.rs` with the `cargo:` -> `cargo::` directive change (1.77) and the two costs of adding one (build-time tool requirements that break `cargo install` for users, and opacity to compiler caches); what `rust-version` now controls, given edition 2024's `resolver = "3"` flips `incompatible-rust-versions` to `fallback`, so a stale MSRV silently holds the whole dependency tree back; and `#[non_exhaustive]` as the right default for a published error enum, with the `E0639` struct-literal error it produces downstream.
- references/dev-environment.md: supply-chain hygiene, previously absent entirely - `cargo audit` against the RustSec database as the first step, `cargo deny` with the warning that `cargo deny init` writes a template that fails immediately (an empty license allow-list rejects everything), and `cargo machete` with its documented static-`use`-scan false positives.
- references/dev-environment.md: `cargo build --timings` as the free diagnostic to run *before* installing a build cache, plus `cargo fix --edition` and `cargo clippy --fix`.
- references/crate-shortlist.md: `tracing_subscriber::fmt()` writes to **stdout** by default (`SubscriberBuilder`'s writer parameter is `W = fn() -> Stdout`, with no TTY detection), which silently corrupts any binary whose stdout carries data - JSON-RPC, MCP, a CLI piping records. `.with_writer(std::io::stderr)` is the documented fix, and the skill's own example inherited the default. Also the `json` feature and `tracing-appender` for production logging.
- references/crate-shortlist.md: a table for when the anyhow/thiserror split is not enough - `eyre` (customizable reports), `miette` (source-span diagnostics), `snafu` (per-`?` context selectors), `error-stack` (attachable context stack).
- references/releasing.md: crates.io Trusted Publishing - OIDC via `rust-lang/crates-io-auth-action@v1` with 30-minute tokens, removing the stored `CARGO_REGISTRY_TOKEN` secret, with the two constraints (first publish still needs an API token; there is no `cargo publish --trusted-publishing` flag).
- references/releasing.md: `dist` hard-refuses a Linux-host -> macOS cross-build via a typed `UnsupportedCrossCompile` error ("cross-compiling to macOS is a road paved with sadness - we cowardly refuse to walk it"), which is the concrete decision criterion between Route A and Route B.
- references/releasing.md: `clap_complete`'s `generate_to` named as the compile-time API the existing "ship pre-generated completions" advice requires, plus `clap_mangen`.
- references/async-basics.md: `#[tokio::test(start_paused = true)]` cannot control `std::time::Instant`, so production code must use `tokio::time::Instant` to be testable at all (behavior is identical outside a paused runtime); advance with `advance()`, not `sleep()`. Plus `tokio-console` for diagnosing a task that is not being polled, and a note that `async-std` is discontinued.
- references/testing.md: `cargo clippy --all-targets` lints `tests/` and `benches/`, so `print_stdout`/`unwrap_used`-style lints need a crate-level allow header there.

### Changed

- SKILL.md Minimal Cargo.toml: `unsafe_code` is now `"deny"` rather than `"forbid"`. `forbid` cannot be lifted by a local `#[allow]` with a SAFETY justification, and that bites on ordinary `mmap`, not only on FFI - the previous "downgrade to deny if you do FFI" comment understated when it matters.
- references/dev-environment.md: rewrote the kache quirks table against 0.16.0 (pin was 0.9.0, seven minors back). Four claims had gone stale: `cache_executables` now defaults to **`true` on Linux and macOS** (only Windows keeps `false`), so the "turn it on" advice is removed; eviction has been **cost-aware** since 0.12.0, indexing each entry's `compile_time_ms` rather than ranking by size, which retires the "LRU throws away your expensive artifacts first" failure mode (the 50GiB cap stands, now with its 10% hysteresis band); the cache key hashes the `rustc --version --verbose` banner plus the linker's `--version`, with no LLVM-version component as previously claimed; and the path-leak detector is `KACHE_LOG=warn`, not `KACHE_LOG=kache=warn`. The undocumented S3 virtual-hosted/`NoSuchKey` row is replaced with the documented endpoint requirement (kache always addresses path-style).
- references/dev-environment.md: "kache disables incremental compilation - do not turn it back on" no longer holds unconditionally; `adaptive_incremental` defaults to `true` and hands a repeatedly-missing crate an isolated incremental directory for a bounded run. Adds `cache.incremental_crates`, workspace-level `[[workspace.extra_inputs]]`, `kache sync`'s non-zero exit on partial failure (0.15.0) with `--allow-partial`, the proc-macro env-var keying fix (0.13.0), the schema v27 one-time cold miss, and the `KACHE_PRESERVE_INCREMENTAL` caveat on `KACHE_DISABLED=1`.
- references/releasing.md: `breaking_always_increment_major` was presented as a release-plz config key alongside `features_always_increment_minor`. It is not one - it exists only as a Rust API on the version updater, so readers were being sent to look for a `release-plz.toml` key that does not exist.
- references/releasing.md: "a pull request opened by `GITHUB_TOKEN` does not trigger workflows" restated - GitHub now creates those runs in an approval-required state rather than not at all. The practical failure and the PAT recommendation are unchanged.
- references/dev-environment.md: sccache's "leaves incremental compilation on (which is what keeps your own workspace crates rebuilding fast)" was misleading - sccache does not change the setting, but "Incrementally compiled crates cannot be cached" either way, which is why the skill's own CI line sets `CARGO_INCREMENTAL=0`. Its linker-crate exclusion is now quoted directly.
- references/dev-environment.md + releasing.md: `actions/checkout@v6` -> `@v7`.
- SKILL.md + references/dev-environment.md: `cargo install --locked bacon` at both occurrences, matching bacon's own documented install command.
- references/dev-environment.md: the macOS linker note now cites mold's own "mold does not support macOS" and reflects wild's move to `wild-linker/wild` (published as the `wild-linker` crate), whose Mach-O support is still listed as unsupported.
- references/performance.md: Rust 1.97 made **v0 symbol mangling the default**, which can defeat older profilers and debuggers and changes backtrace text formatting - so garbled frames after a toolchain bump are usually a stale tool, not a broken build. `cargo-flamegraph` on Linux now needs `--no-rosegment` because rust-lld is the default linker since 1.90.
- references/performance.md: `dhat` is no longer described as "native-speed" - its docs warn the slowdown "can be large" - and its maintenance caveat is noted.
- references/async-basics.md: `block_in_place` "works only on the multi-threaded runtime" was too strong; calling it outside a runtime is allowed and simply runs the closure. The `current_thread` panic is the actual constraint.
- references/error-handling.md: clippy's `unwrap_used` does not flag literally every `.unwrap()` - `allow-unwrap-in-consts` defaults to `true`.
- references/crate-shortlist.md: the jiff migration list claimed more than upstream shows - the arrow-rs and jj-vcs changes are still open PRs, while kube-rs and k8s-openapi have landed. Adds the `jiff-chrono-conversions` bridge, `jiff-sqlx` tracking sqlx 0.9, jiff's 0.2 support commitment (critical fixes for a year after 1.0), and the note that chrono's deprecation lives in an issue thread rather than its README.
- SKILL.md: the unbounded-read anti-pattern now attributes its quote to `BufRead::read_line`, where std actually carries the warning, and explains that `.lines()` inherits it by delegation.

### Deprecated

- references/crate-shortlist.md: `serde_yaml` and `bincode` were listed as plain "other formats" with no caveat. `serde_yaml` is archived at `0.9.34+deprecated` with no official successor; `bincode` 3.0.0 is a tombstone release whose entire `src/lib.rs` is `compile_error!("https://xkcd.com/2347/")`, so `bincode = "3"` fails to compile rather than failing at runtime - 2.0.1 is the last usable version.

### Security

- references/dev-environment.md: notes that Rust 1.96.0 shipped Cargo fixes for CVE-2026-5222 and CVE-2026-5223, and 1.96.1 patched CVE-2025-15661, CVE-2026-55199 and CVE-2026-55200 in vendored libssh2 - a concrete argument that a `rust-toolchain.toml` pin is for reproducibility, not for freezing.

Verified against: rust@1.98.0, reqwest@0.13.4, jiff@0.2.35, kache@0.16.0

## [0.4.3] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`development`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [0.4.2] - 2026-08-07

### Changed

- Trimmed the frontmatter description to what-plus-when; dropped the trailing trigger-keyword enumeration (semantic matching makes it redundant).

### Fixed

- `metadata.upstream` pinned the floating series `release-plz@0.5`; now tracks the concrete GitHub Action release `release-plz-action@0.5.131` (the artifact references/releasing.md actually uses).

Verified against: release-plz-action@0.5.131

## [0.4.1] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format
- metadata.openclaw block (emoji, homepage) for ClawHub display

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
