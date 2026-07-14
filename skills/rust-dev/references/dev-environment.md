# Development Environment

Setting up a fast edit-compile-test loop, and keeping it fast as the project grows. None of this is needed on day 1 - reach for it when builds start to feel slow.

## The fast inner loop

The commands, fastest to slowest:

- `cargo check` - type-checks without code generation. This is your inner loop; run it constantly.
- `cargo clippy` - `check` plus lints. Set your editor to run this on save.
- `cargo build` / `cargo run` - full code generation.
- `cargo test` - build plus run tests.

In your editor, point rust-analyzer's check command at clippy so you get lint feedback inline (in VS Code: `"rust-analyzer.check.command": "clippy"`). rust-analyzer itself does most type-checking as you type; `cargo check` is the fallback the editor runs to populate diagnostics.

## Build speed

Two things make Rust builds slow: compiling code, and linking it. Caching compilation is the bigger win and is the same on every platform; the linker story is the part that differs.

### Build caching: use kache

[kache](https://github.com/kunobi-ninja/kache) is a content-addressed `RUSTC_WRAPPER`. It gives you a persistent, global cache of compiled **dependencies** - shared across every project on the machine, surviving `cargo clean`, branch switches, and fresh worktrees or clones at a different path. Cache hits restore zero-copy (a reflink on APFS/btrfs/XFS-with-reflink, a hardlink otherwise), so artifact bytes are not duplicated on disk. An optional S3 remote shares artifacts across machines and CI.

```sh
# Install (mise, or brew on macOS)
mise use -g github:kunobi-ninja/kache@latest
brew install kunobi-ninja/kunobi/kache

kache init      # wires RUSTC_WRAPPER into ~/.cargo/config.toml, installs + starts the daemon
kache doctor    # verify
```

`kache init` is idempotent - re-run it any time to repair the setup. To wire it by hand instead, set `rustc-wrapper = "kache"` under `[build]` in `$CARGO_HOME/config.toml`.

Sharing artifacts across machines needs a remote, in `~/.config/kache/config.toml`:

```toml
[cache.remote]
type = "s3"
bucket = "my-build-cache"
endpoint = "https://s3.example.com"   # omit for AWS S3; required for Ceph/MinIO/R2
profile = "my-aws-profile"            # an AWS profile, not env vars - see the quirks below
```

**kache disables incremental compilation while it wraps rustc.** That is deliberate: artifact caching replaces that path (and it sidesteps APFS-related incremental corruption on macOS). Do not try to turn incremental back on.

### kache quirks worth knowing before they cost you a day

| Quirk | Why it bites |
|---|---|
| `local_max_size` defaults to **50GiB** | A dependency tree with heavy native or data crates (100-300 MB artifacts each) blows past it, and LRU evicts precisely the **expensive** artifacts before anything reuses them. This looks exactly like "cross-path reuse is broken" - it is not. Raise the cap (`KACHE_MAX_SIZE`, or `cache.local_max_size`). |
| Count hit rate lies | Judge by **cost-weighted** hit rate (`kache stats`, `kache report`). Cheap leaf crates hitting while the expensive spine misses every time still reads as a healthy-looking 60% by count. |
| `cache_executables` defaults to `false` | Your `bin` and `--test` binaries relink on every build. Turn it on. (dylib/cdylib/proc-macro are always cached and unaffected.) |
| `kache sync --push` filters to **workspace members** | Seeding an existing store to S3 from your project directory silently uploads almost nothing - the push filter is `cargo metadata --no-deps`. Run it from a directory with **no** `Cargo.toml` to push everything. Push also does a full unfiltered LIST of the prefix, which is a real cost on a large bucket. |
| The service daemon does **not** inherit your shell environment | `KACHE_S3_*` credentials exported from your shell profile leave the launchd/systemd daemon with no credentials at all. Use an AWS profile (`cache.remote.profile`) or `~/.aws/credentials` instead. |
| The S3 endpoint must be the **base** endpoint | The virtual-hosted form (bucket in the hostname) fails with `NoSuchKey`. |
| Upgrading kache can orphan the service | The launchd plist or systemd unit keeps pointing at the deleted old binary. Re-run `kache init` (or `kache daemon install`) after an upgrade. |
| Keys encode **toolchain identity**, not machine identity | The key hashes the host triple and the full `rustc -vV` banner, LLVM version included. Machines can share one bucket prefix safely - objects cannot collide - but only *matching toolchains* ever hit each other. A Nix-built rustc shares a triple with rustup and still never overlaps if its bundled LLVM differs. Think **prefix per toolchain**, not per machine. |
| `key_salt` covers what the key cannot see | A glibc, linker, or Nix-store change alters compiled output while leaving every version banner unchanged, so the key does not move and a stale artifact can be restored. With `cache_executables = true` a `nix store gc` can restore a binary pointing at a garbage-collected ELF interpreter - an error no `cargo clean` fixes. Set `cache.key_salt` to something that changes with your toolchain (a closure hash, a store-path digest). |
| Macro-read files are invisible to the key | sqlx's `query!` reads `.sqlx/*.json`, migration macros read `migrations/` - rustc never reports them, so editing one does not re-key the crate and you get a **stale hit**. Declare them in a per-crate `kache.toml` (`extra_inputs = [".sqlx/**/*.json", "migrations/**/*.sql"]`). Note this is `kache.toml`, distinct from the project config `.kache.toml`. |
| Do not bind-mount the cache directory into a container | kache's SQLite index needs single-machine file locking. Shared across an OS boundary it cannot open, and kache silently builds **uncached** (the build still succeeds). Give the container its own `KACHE_CACHE_DIR`. The same applies to NFS/SMB. |

Diagnosing a cache that is not paying off: `kache stats` for the weighted hit rate, `kache list --sort size` (large entries showing `hits: 0` mean eviction thrash, not a keying problem), `kache why-miss <crate>` for a specific crate, and `KACHE_LOG=kache=warn cargo build` to run the path-leak detector, which flags any key field retaining a machine-local absolute path.

**Any `RUSTC_WRAPPER` puts your build cache in the failure path.** Once a wrapper is wired in, a broken, misconfigured, or sandboxed cache surfaces as a *compile failure* - and it will not look like a cache problem, it will look like a baffling Rust error. Before you spend an hour on a compile error that makes no sense, take the wrapper out of the picture and confirm the failure is real: `KACHE_DISABLED=1 cargo build` (kache's own bypass, which keeps it a transparent shim), or `RUSTC_WRAPPER= cargo build` for any wrapper. This applies equally to sccache.

Upgrading kache does **not** require wiping the cache. Keys only shift where the keying logic itself changed, so expect a one-time partial recompile and then a warm cache again.

### sccache: the conservative alternative

[sccache](https://github.com/mozilla/sccache) is the older, more widely deployed compilation cache, and it is a reasonable choice if you want the most boring option:

```toml
# ~/.cargo/config.toml
[build]
rustc-wrapper = "sccache"
```

It caches dependencies but cannot cache proc-macro or other linker-invoking crates, and it leaves incremental compilation on (which is what keeps your own workspace crates rebuilding fast). The trade-off against kache: sccache does not restore zero-copy, and it has no cross-machine story as direct as kache's S3 sync. The two can also be chained - set `KACHE_FALLBACK=sccache` and kache hands the compiles it declines to cache over to sccache.

### Linkers

Independent of which cache you use.

On **macOS**, do nothing. The fast third-party linkers (`mold`, `wild`) are ELF/Linux-only and cannot link Mach-O binaries, and Apple's bundled linker is already fast.

On **Linux**, you have the win for free: since Rust 1.90, `x86_64-unknown-linux-gnu` uses the bundled `rust-lld` linker by default (around 7x faster incremental linking than GNU `ld`, no setup). `mold` is faster still if you want to go further, via `.cargo/config.toml`:

```toml
[target.x86_64-unknown-linux-gnu]
linker = "clang"
rustflags = ["-C", "link-arg=-fuse-ld=mold"]
```

Profile before assuming linking is your bottleneck - often it is not.

### CI

A minimal, reproducible GitHub Actions gate is three commands behind one toolchain action:

```yaml
name: ci
on: [push, pull_request]
permissions:
  contents: read          # least-privilege GITHUB_TOKEN
jobs:
  check:
    strategy:
      fail-fast: false     # one OS failing still shows the other
      matrix:
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v6
      - uses: actions-rust-lang/setup-rust-toolchain@v1
      - run: cargo fmt --check
      - run: cargo clippy --locked -- -D warnings
      - run: cargo test --locked
```

`actions-rust-lang/setup-rust-toolchain` reads `rust-toolchain.toml` for the channel and components and bundles `Swatinem/rust-cache` - toolchain install and build cache in one step, no separate cache action. `--locked` fails CI if `Cargo.lock` is stale; `clippy -- -D warnings` turns every lint in your `[lints]` table into a CI failure.

**Think twice before adding `--all-features` to a lint or test job.** It is common advice, and it breaks the moment any optional feature needs a toolchain the runner does not have - a `cuda` feature that makes a build script shell out to `nvcc`, a feature pulling a GPU or FFI SDK. Those features exist precisely so that people who lack the toolchain can skip them, and `--all-features` removes that choice, making the job unbuildable on an ordinary machine. Lint the feature combinations you actually ship.

**Pick one cache, not two.** Stacking a compiler cache on top of the bundled `rust-cache` competes for the same Actions cache budget and usually makes things worse. When you outgrow `rust-cache` - typically once the dependency tree is big enough that restoring `target/` is itself slow, or you want runners and laptops to share compiled artifacts - swap it for [`kache-action`](https://github.com/kunobi-ninja/kache-action), which is a one-liner:

```yaml
- uses: kunobi-ninja/kache-action@v1
```

That uses the Actions cache by default; pass `s3-bucket` plus credentials to back it with S3, which is what makes reuse work across runners and across machines. Remember that cross-machine hits only land where the toolchain matches exactly, so a CI runner and a laptop on different host triples will never share artifacts no matter how the bucket is configured. If you use `sccache` in CI instead, set `CARGO_INCREMENTAL=0` so it can cache every compilation (kache handles this itself by disabling incremental).

## Optimizing dependencies in dev builds

Debug builds are slow at runtime because nothing is optimized. If a dependency does heavy computation (image processing, crypto, compression) and that dominates your dev-run time, optimize just the dependencies while keeping your own crates unoptimized for fast compiles:

```toml
[profile.dev.package."*"]
opt-level = 3
```

Your crates still compile fast; the dependencies, compiled once, then run fast.

To speed up your own crate's debug rebuilds, set `[profile.dev] debug = "line-tables-only"` - it keeps file and line numbers for panics and backtraces but drops the heavier per-variable debug info.

## File watchers

`bacon` runs `check`/`clippy`/`test` in a loop, re-running on save, with a compact summary view. Install with `cargo install bacon` and run `bacon` in the project. Optional, but a nice background companion to the editor.
