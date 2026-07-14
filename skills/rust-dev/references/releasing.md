# Releasing and Distribution

Getting a Rust binary from a merged commit to something a user can install. None of this matters until you have users; when you do, the difference between a good pipeline and an improvised one is measured in broken installs.

There are two viable routes. Pick by how much control you need.

## Route A: `dist` (the batteries-included default)

[`dist`](https://github.com/axodotdev/cargo-dist) (formerly `cargo-dist`) plans the release, cross-compiles the binaries, generates installers (shell, PowerShell, npm, Homebrew), and **writes its own CI workflow** - `dist init` emits a `release.yml` implementing the whole plan/build/host/publish/announce pipeline. For most projects this is the right answer, and you should try it before hand-rolling anything.

A note on its history, because a stale memory will otherwise scare you off: `dist` was built by axo, who wound down; maintenance was picked up by the community, the Astral fork's features were merged back in, and it has shipped steady releases since (0.32.0 in May 2026). It is maintained.

Reach for Route B only when you need something dist does not model - an unusual cross-compilation setup, a bespoke distribution fan-out, or strict control over the order in which things publish.

## Route B: a hand-rolled pipeline (one reference implementation)

What follows is **one pipeline that works in production**, not the only correct shape. Copy the parts that fit. The value here is less the YAML than the reasoning behind each decision - most of these were learned by breaking something.

The pieces: [`release-plz`](https://release-plz.dev) drives versioning and publishing, [`cargo-zigbuild`](https://github.com/rust-cross/cargo-zigbuild) cross-compiles every target from a single Linux runner, and a handful of plain shell steps fan the built binaries out to GitHub Releases, Homebrew, and Nix.

### release-plz drives versioning

You write [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `perf:`, …). release-plz keeps a **release PR** open that bumps the version in `Cargo.toml` and writes the `CHANGELOG.md` entry from those commits. Merging that PR is the act of releasing: release-plz then publishes to crates.io, cuts the git tag, and creates the GitHub release.

It runs as two different commands, and the split matters:

- `release-pr` - keeps the release PR current. Never publishes. Runs on every push to `main`.
- `release` - publishes to the registry and cuts the tag. Runs only when a release is actually pending.

**Two bump behaviors that surprise people.** On a `0.x` version, a `feat:` commit produces a **patch** bump, not a minor one - `0.2.7` + `feat:` is `0.2.8`. This is deliberate (Cargo treats `0.x` → `0.(x+1)` as the breaking-change channel, so features cannot claim it), and it means a `feat!:` breaking change on `0.2.3` gives you `0.3.0`, not `1.0.0`. Both are overridable (`features_always_increment_minor`, `breaking_always_increment_major`) but the defaults are the correct ones. Expect them rather than fighting them.

**Squash-merge can silently erase your release.** The version bump is computed from *commit messages*. Squash-merging a PR replaces its commits with a single commit whose message is the **PR title** - so a PR titled `ci: tidy workflow` that happens to contain the `feat:` commit produces no `feat:` in history, and therefore no release at all. The commit you cared about is gone. Either title the PR conventionally (so the squashed message carries the right type), or use a merge commit for release-worthy PRs. This is not a release-plz quirk - it bites every conventional-commit release tool.

### Build the binaries *before* you publish

The single most important ordering decision. If `cargo publish` runs first and the binary build then fails, crates.io has a version whose release has no binaries - and crates.io publishes are **irreversible**. So the publish job builds the artifacts first, and only then invokes release-plz's `release` command:

```yaml
  publish-release:
    needs: [release-prep]
    if: needs.release-prep.outputs.is_release == 'true'
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0, persist-credentials: false }

      - name: Build + package binaries      # must succeed before anything publishes
        run: ./scripts/build-dist.sh

      - uses: release-plz/action@v0.5        # NOW publish crates.io + cut the tag
        id: release-plz
        with: { command: release }
        env:
          GITHUB_TOKEN: ${{ secrets.RELEASE_TOKEN }}   # a PAT, not the workflow token - see below
          CARGO_REGISTRY_TOKEN: ${{ secrets.CARGO_REGISTRY_TOKEN }}

      - name: Upload binaries to the release
        if: ${{ steps.release-plz.outputs.releases_created }}
        run: gh release upload "v$VERSION" dist/* --clobber
```

### Detect a pending release with the tag, not with `--dry-run`

To gate the publish job you need to know "is a release pending?" - and release-plz's dry-run **cannot tell you**: in dry-run it always reports `releases_created=false` and merely logs the plan.

Check the tag instead. This mirrors release-plz's own first gate ("skip a package whose tag already exists"):

```yaml
      - id: detect
        run: |
          set -euo pipefail
          V=$(cargo metadata --no-deps --format-version 1 | jq -r '.packages[0].version')
          if git rev-parse "v$V" >/dev/null 2>&1; then
            echo "is_release=false" >> "$GITHUB_OUTPUT"
          else
            echo "is_release=true" >> "$GITHUB_OUTPUT"
          fi
```

### Set concurrency per job - never workflow-level

A workflow-level `concurrency: cancel-in-progress: true` will eventually kill a release **mid-publish**: a newer push to `main` cancels the run somewhere between release-plz cutting the tag and the artifacts finishing upload. Once the tag exists, the pending-release gate above reads `false` forever, so the interrupted release **cannot auto-recover** - you get a tagged, published version with no binaries and no retry.

Keep builds cancellable and make publishing non-cancellable:

```yaml
  build-and-test:
    concurrency: { group: "ci-build-${{ github.ref }}", cancel-in-progress: true }

  publish-release:
    # A newer push queues behind this run instead of killing it mid-publish.
    concurrency: { group: "release-${{ github.ref }}", cancel-in-progress: false }
```

### Use a PAT for the release PR, not `GITHUB_TOKEN`

A pull request opened by the default `GITHUB_TOKEN` **does not trigger workflows** - GitHub blocks that to prevent recursion. So a release PR opened with it never runs CI, and you merge a version bump nothing has tested. Give the `release-pr` step a personal access token (or a GitHub App token) instead.

### `[profile.dist]`: pay for optimization only at release

Full LTO and a single codegen unit make a meaningfully faster binary and a much slower build. You do not want that on every `cargo build --release` during development. Split the profiles:

```toml
# Iteration profile: no LTO, so local rebuilds relink in seconds.
[profile.release]

# Ship profile: used only for release artifacts.
[profile.dist]
inherits = "release"
lto = "thin"
codegen-units = 1
```

Then build artifacts with `--profile dist`. See `performance.md` for the fuller treatment of this split.

### Cross-compile every target from one runner with `cargo-zigbuild`

`cargo-zigbuild` uses Zig as the linker, which cross-links glibc (and Mach-O, given an SDK) without Docker, without QEMU, and without a per-OS CI matrix. One Linux runner produces every artifact:

```sh
rustup target add aarch64-apple-darwin x86_64-pc-windows-gnu \
                  aarch64-unknown-linux-gnu x86_64-unknown-linux-gnu

cargo zigbuild --locked --profile dist --target aarch64-apple-darwin
cargo zigbuild --locked --profile dist \
  --target aarch64-unknown-linux-gnu \
  --target x86_64-unknown-linux-gnu
cargo zigbuild --locked --profile dist --target x86_64-pc-windows-gnu
```

**The trap - and why those are three commands, not one.** Cargo resolves and **unifies features across every `--target` in a single invocation**. A dependency that a `cfg`-gated feature pulls in for one platform therefore leaks into the others: a macOS-only GPU backend gets enabled for the Windows build, or a `cfg(not(windows))` assembly feature drags a crate that `compile_error!`s on Windows into the Windows build. Grouping only the targets that share a feature set into one invocation - and giving the platform-divergent ones their own - is what avoids it. If a cross build fails with an error about a dependency that has no business being there, this is why.

One `cargo` invocation is **one feature resolution graph**. "This feature on for the macOS artifact, off for the Linux one" asks a single resolution to hold two contradictory feature sets for the same dependency; cargo deliberately refuses to model that. It is not a missing flag, so stop looking for one and split the invocation.

Worse, the leak does not have to come from *your* manifest. A crate three levels down your tree can gate a feature with `[target.'cfg(not(windows))'.dependencies]`, and if Windows shares an invocation with Linux you inherit the breakage with no feature flag of your own to turn it off - the only fixes are per-target invocations or a `[patch]`. So you cannot audit your way out of this by reading your own `Cargo.toml`.

**How to actually see the resolved features:** `cargo tree -e features` (and `cargo tree -e features -i <crate>` to ask *why* a feature is on). Do not go looking in `Cargo.lock` - **it does not record features at all**. Cargo's own lockfile decoder says so outright: "It also does not include `features`." Believing otherwise is a common and expensive detour when debugging exactly this class of bug.

If you build macOS binaries with Zig, expect to re-sign them (an ad-hoc `rcodesign sign` is enough); Zig's recorded SDK metadata can otherwise trip newer macOS loaders.

### Fan out to installers from a single build

Every channel is fed from the same artifacts, so build once and derive the rest. Compute the tarball checksums once, then template them into whatever you publish:

- **GitHub Release** - the tarballs plus a `checksums.txt`. Everything else fetches *from* this, so upload it first.
- **`cargo-binstall`** - fetches a prebuilt binary instead of compiling on `cargo install`. Declare it in `Cargo.toml`. **The gotcha:** binstall's default URL template uses the **crate** name, but release assets are usually named after the **binary**. When those differ (a crate published under a suffixed name because the good one was taken), the defaults silently miss and every install falls back to a full compile:

  ```toml
  [package.metadata.binstall]
  pkg-url = "https://github.com/myorg/my-app/releases/download/v{ version }/my-app-{ target }{ archive-suffix }"
  pkg-fmt = "txz"
  bin-dir = "{ bin }{ binary-ext }"

  [package.metadata.binstall.overrides."x86_64-pc-windows-gnu"]
  pkg-fmt = "zip"
  ```

- **Homebrew** - generate the formula in CI and push it to your tap repo, with the per-target `sha256` values from the build.
- **Nix** - render a derivation that `fetchurl`s the release tarballs. A prebuilt glibc binary needs `autoPatchelfHook` to rewrite its interpreter and RPATH to Nix store paths; Mach-O needs no patching.

**Ship shell completions pre-generated inside the tarball.** Generating them by *running* the binary at install time fails exactly where you cannot afford it - Nix cannot execute the not-yet-patched binary during its install phase, and cross-built binaries cannot run on the build host at all.

### Guard what the published crate actually contains

`exclude` in `Cargo.toml` keeps your published crate small by dropping tests, fixtures, and docs from the `.crate` file. It is also a loaded gun: **exclude a file the code embeds with `include_str!`/`include_bytes!` and `cargo install` breaks for everyone while `cargo build` in your repo keeps working perfectly.** The failure is invisible locally and can survive several releases.

The guard is cheap - assert in CI that everything the code embeds appears in the packaged file list:

```sh
# Every file the code embeds must survive into the packaged .crate.
for f in $(rg -o 'include_(str|bytes)!\("([^"]+)"\)' -r '$2' src/); do
  cargo package --list | grep -qx "$f" || { echo "embedded file not packaged: $f"; exit 1; }
done
```

### Keep the working tree clean, or publishing stops

`cargo publish` refuses to package a dirty working tree, and **untracked files count as dirty** - so a pipeline that builds artifacts into the repo (a `dist/` directory, generated completions) and then publishes will abort with "files in the working directory contain changes that were not yet committed into git." Precisely: only dirty files that intersect the set of files being packaged trigger it.

The tempting fix is `--allow-dirty`. That is the wrong lever - it disables the check that stops you publishing whatever junk is lying around. **Gitignore your build output instead**, so it is not part of the tree cargo inspects. Reach for `--allow-dirty` only when you deliberately intend to publish uncommitted content, which is almost never.

Two release-plz settings worth understanding rather than cargo-culting:

- `publish_no_verify = true` skips the verification build `cargo publish` runs by default. Legitimate **only** when CI has already compiled that exact code, and only once you have a packaging gate like the one above - it is precisely the check you are turning off. It saves a cold rebuild of the whole dependency tree at publish time.
- `semver_check = false` disables [`cargo-semver-checks`](https://github.com/obi1kenobi/cargo-semver-checks). Reasonable for a binary whose library target exists only so the binary and its tests can share code. If anyone actually depends on your library, **leave it on** - it is the thing that stops you shipping a breaking change as a patch bump.

### Why there is no task runner here

The pipeline above is plain shell and cargo invocations. A monorepo task runner (moon, Bazel, Nx) buys you remote task caching and cross-project dependency graphs - real wins in a large polyglot monorepo, and dead weight in a single-crate Rust app, where it adds a second task layer over cargo and a second toolchain-management story next to `rust-toolchain.toml`. If you want named tasks, a `Justfile` is enough. For build caching, cache at the compiler level instead (see `dev-environment.md`) - it is finer-grained and helps every build, not just the ones you routed through a task graph.
