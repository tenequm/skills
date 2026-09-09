# Project Shape: Past One Crate

The main skill teaches a single crate with one `Cargo.toml`. This file is what you need the day that stops being enough - a second crate, an optional dependency, a generated file, a minimum Rust version somebody actually depends on.

None of it is day-1 material. Read the section you have hit.

## Workspaces

A workspace is several crates sharing one `Cargo.lock`, one `target/` directory, and one `cargo test` invocation. The moment you have a library plus a CLI that uses it, you want one.

```toml
# Cargo.toml at the repo root - this crate has no [package] of its own
[workspace]
resolver = "3"
members = ["crates/*"]

[workspace.package]
version    = "0.1.0"
edition    = "2024"
license    = "MIT"
rust-version = "1.85"

[workspace.dependencies]
serde  = { version = "1", features = ["derive"] }
tokio  = { version = "1", features = ["rt-multi-thread", "macros"] }
anyhow = "1"
```

```toml
# crates/my-cli/Cargo.toml
[package]
name = "my-cli"
version.workspace      = true
edition.workspace      = true
rust-version.workspace = true

[dependencies]
my-lib = { path = "../my-lib" }
serde  = { workspace = true }
tokio  = { workspace = true, features = ["fs"] }   # add features, never remove them
```

Two things worth internalizing:

- **Inherited dependencies unify.** Every member resolves to one version of `serde`, which is the point - it prevents the diamond where two crates in your own repo disagree and you compile both. A member can *add* features on top of the workspace entry, but cannot subtract them.
- **`target/` is shared.** A workspace build reuses artifacts across members, which is why splitting a big crate into several rarely costs build time and often saves it.

`cargo test`, `cargo clippy`, and `cargo build` operate on the whole workspace from the root; `-p <crate>` scopes to one member.

## `[workspace.lints]` and the trap that goes with it

The main skill's `[lints]` table configures one crate. In a workspace you define it once and inherit:

```toml
# root Cargo.toml
[workspace.lints.rust]
unsafe_code     = "deny"
unreachable_pub = "warn"

[workspace.lints.clippy]
all = { level = "deny", priority = -1 }
dbg_macro = "warn"
```

```toml
# EVERY member Cargo.toml needs this - it is not automatic
[lints]
workspace = true
```

That second block is the trap. `workspace.lints` is **not** implicitly inherited, and a member that omits `[lints] workspace = true` is silently unlinted - it compiles clean while the rest of the workspace is under `-D warnings`. Cargo does have a `missing_lints_inheritance` lint for exactly this, but do not count on it: "Cargo's linting system is unstable and can only be used on nightly toolchains", so on stable nothing warns you at all. When you add a new member, this is the line you will forget, and the only thing that catches it is you.

## Feature flags

Features are named, additive sets of optional functionality. They are how a crate offers "TLS, but pick a backend" or "serde support if you want it" without forcing the dependency on everyone.

```toml
[features]
default = ["json"]
json    = ["dep:serde_json"]
tls     = ["dep:rustls"]
# Turn on a dependency's feature only if that dependency is already enabled
metrics = ["dep:prometheus", "tokio?/rt-multi-thread"]

[dependencies]
serde_json = { version = "1", optional = true }
rustls     = { version = "0.23", optional = true }
prometheus = { version = "0.14", optional = true }
```

Three pieces of syntax, all worth knowing because older guides predate them:

- **`dep:foo`** refers to the optional dependency without also creating an implicit feature named `foo`. Available since Rust 1.60. Without it, every optional dependency silently becomes part of your public feature surface.
- **`foo?/bar`** enables dependency `foo`'s `bar` feature *only if* `foo` is otherwise enabled - the `?` is what stops it from pulling `foo` in.
- **Features must be additive.** Two crates in one build can both enable features of a shared dependency, and cargo unifies them; a feature that *removes* or *changes* behavior will break somebody. If you find yourself wanting `no-std` and `std` as mutually exclusive features, that is the shape fighting you.

In code, gate with `#[cfg(feature = "json")]`. Test the combinations you actually ship - and see `dev-environment.md` on why `--all-features` in CI is a trap, and `releasing.md` on how feature unification bites across cross-compilation targets.

## Build scripts (`build.rs`)

A `build.rs` at the crate root compiles and runs *before* the crate does. Legitimate uses are narrow: compiling bundled C, generating code from a schema (protobuf, SQL), or baking in build-time facts.

```rust
// build.rs
fn main() {
    // Re-run only when this actually changes - without it, cargo re-runs
    // the script whenever any file in the package changes.
    println!("cargo::rerun-if-changed=proto/api.proto");
    println!("cargo::rustc-cfg=has_fancy_backend");
}
```

The syntax changed: directives use a **double colon** (`cargo::rerun-if-changed`) as of Rust 1.77. The old single-colon form still works but is deprecated, and tutorials are full of it.

Two costs to weigh before adding one. A build script is a compile-time dependency for everyone who builds you, including in environments you cannot see - a script that shells out to `cmake` or `protoc` makes those tools a hard install requirement, which is exactly the class of thing that breaks `cargo install` for users while working fine in your repo. And build scripts are opaque to compiler caches: files a macro or script reads are invisible to the cache key unless you declare them (see the `extra_inputs` row in `dev-environment.md`).

## `rust-version` (MSRV) and why it now matters more

`rust-version = "1.85"` in `[package]` declares your minimum supported Rust version. It used to be documentation with a build-time error attached. It is now load-bearing for dependency resolution.

Edition 2024 defaults to `resolver = "3"`, which flips `resolver.incompatible-rust-versions` from `allow` to **`fallback`**: cargo will prefer an older version of a dependency when the newest one requires a newer Rust than you declare. That is usually what you want - it stops `cargo update` from silently breaking your MSRV promise - but it means a stale `rust-version` now quietly holds your whole dependency tree back.

Set it to a version you actually test against, and raise it deliberately. If you support an MSRV, test it in CI with that toolchain, not just the latest.

## `#[non_exhaustive]`

An attribute on a struct, enum, or variant that "indicates that a type or variant may have more fields or variants added in the future". It stops downstream code from writing an exhaustive `match` or a struct literal, so adding a variant later is not a breaking change.

```rust
#[non_exhaustive]
pub enum LoadError {
    NotFound,
    Io(std::io::Error),
}
```

This is the right default for a **published library's error enum**, which is precisely the thing the main skill teaches you to build with `thiserror` - error enums grow, and without this every new variant is a semver break.

Know the cost from the consumer side, because it produces a confusing error. A downstream `match` now needs a `_ =>` arm, and a non-exhaustive *struct* cannot be built with a struct literal at all - not even with `..Default::default()`. The compiler says `error[E0639]: cannot create non-exhaustive struct using struct expression`, and the answer is always to use the crate's own constructor or builder. If you apply the attribute, ship a constructor.
