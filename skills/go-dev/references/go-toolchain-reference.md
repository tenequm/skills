# Go Toolchain Reference

The `go` command behaviours that sit between the code and the gates: multi-module workspaces, the build, test and CI caches, Go version bumps, version stamping, and container builds. Verified against go1.27.4.

## Workspaces (`go.work`)

A `go.work` file lets one checkout build several modules together without `replace` directives. It changes how patterns, tools and tidy behave, and most of the stack's commands need adjusting.

```bash
go work init ./api ./worker ./shared      # write go.work listing the modules
go work use ./tools                       # add another module
go work sync                              # push the workspace build list back into each go.mod
go list -m -f '{{.Dir}}/...'              # one package pattern per workspace module
GOWORK=off go build ./...                 # check one module as it builds on its own
```

**`./...` fails at a root that has no `go.mod`.** From the workspace root, `go build ./...`, `go test`, `go vet`, golangci-lint and govulncheck all stop with:

```
pattern ./...: directory prefix . does not contain modules listed in go.work or their selected dependencies
```

Pass the module directories instead - `go test $(go list -m -f '{{.Dir}}/...')`, and the same expansion for `golangci-lint run`. Prefer it over the `work` package pattern, which under `go work vendor` also matches vendored third-party packages.

**`go tool` sees every module's tools.** "In workspace mode, you can use `go tool` to run a tool declared in any workspace module", so a root Justfile recipe or lefthook job needs no per-module `[working-directory]` or `root:`. Without a `go.work`, `go tool` only sees the current directory's module.

**`go mod tidy` ignores the workspace.** Each module is tidied as if it were alone, so every module needs its own `require` (and `replace`, for unpublished siblings) lines. The order that converges:

```bash
go work sync                                   # workspace versions -> each go.mod
for m in $(go list -m -f '{{.Dir}}'); do (cd "$m" && GOWORK=off go mod tidy); done
go work vendor                                 # only if the workspace is vendored
go mod verify && git diff --exit-code          # CI: fail if anything moved
```

If a vendored workspace reports `inconsistent vendoring ... not marked as explicit in vendor/modules.txt` after a new cross-module require, run `go work sync` with `GOFLAGS=-mod=mod` first, then the loop above, then `go work vendor`.

More traps:

- **Tidy reads every build tag.** A test file behind `//go:build integration` that imports a sibling module adds a real `require`, and two modules whose tagged tests import each other form a module cycle. Move such tests into a leaf module.
- **Relative `replace` paths must stay inside the repo.** `replace example.com/x => ../../x` resolves in your checkout and breaks in a worktree, a temp copy, or CI.

- **`godebug` lines stop applying.** "When a workspace is in use, godebug directives in go.mod files are ignored." A GODEBUG pin made while migrating a `go` directive bump belongs in `go.work` once the module joins a workspace.
- **The test cache stops seeing sibling files.** A test that reads another workspace module's files replays cached passes after they change - see the [Go Testing Reference](go-testing-reference.md).

CI needs the workspace file too: setup-go accepts `go-version-file: go.work`, and govulncheck needs a `go.mod`, so run it once per module with `govulncheck -C <module-dir> ./...`. The same `-C` works for every `go` command - `go test -C packages/api ./...` runs in a nested module without a `cd` ("If used, this flag must be the first one in the command line").

## Tools and Dependencies

```bash
go get toolchain@patch               # bump the toolchain line to the latest patch
go get -tool gotest.tools/gotestsum@v1.13.0 && git diff go.mod   # one tool at a time
go get -tool gotest.tools/gotestsum@none   # "If -tool is used with @none, the line will be removed."
go list -m all | rg yaml             # is it already in the graph?
```

- **Add tools one at a time and diff `go.mod` after each.** Tools share the module graph, so one can upgrade your dependencies: in one repo govulncheck, swag and sqlc changed nothing while task upgraded eleven app dependencies. Keep the clean ones as tool directives and install the offender as a prebuilt binary. `go get tool` "is equivalent to `go get tool@upgrade`" - it floats every tool to latest, so bump tools by name with a pinned version instead.
- **`go run pkg@version` in CI compiles the tool from source on every run** (21 s warm, 106 s cold for one task runner), and its modules live outside `go.mod`, so a `go.sum`-keyed module cache never covers them. Track it as a tool or install a binary.
- **Check the graph before calling a dependency new.** `go list -m all` (and `go.sum` across workspace modules) often shows it is already there transitively - `go.yaml.in/yaml/v3`, the maintained successor of `gopkg.in/yaml.v3`, is a one-line `require`, not a new module to vet.
- **The `ignore` directive** (Go 1.25) "Specifies directory paths within the module that the `go` command should ignore when matching package patterns" - so `ignore ./web/node_modules` keeps a frontend tree out of every `./...` gate (test, lint, govulncheck).
- **Don't vendor just to pin.** `go.sum`, `-mod=readonly`, sum.golang.org and `go mod verify` already pin and check every dependency; `vendor/` only adds offline builds. A private dependency needs `GOPRIVATE` plus credentials (below) or a `replace` to an in-tree copy, not a vendored tree. If a repo does vendor, run `go mod vendor` in the same commit as every dependency change and gate it with `go mod vendor && git diff --exit-code vendor/`: a new import of an unvendored subpackage fails as `cannot find module providing package ...: import lookup disabled by -mod=vendor`, and a bump that MVS forces in fails as `inconsistent vendoring ... is explicitly required in go.mod, but not marked as explicit in vendor/modules.txt`.

## Build and Test Caches

**`GOCACHE` is shared, concurrent-safe and uncapped.** "The cache is safe for concurrent invocations of the go command." There is no size limit - "The go command periodically deletes cached data that has not been used recently" - so parallel builds across many worktrees or agent lanes can grow it to tens of GiB between trims. Share one cache rather than giving each lane its own (each new cache is a full cold rebuild), and reclaim space with `go clean -cache`. `go env GOCACHE` prints the location.

**Agent sandboxes and read-only homes.** When the default cache directory is not writable, builds fail as `FAIL <pkg> [setup failed]` with `open .../go-build/...: operation not permitted`. Set `GOCACHE` to one absolute, writable, persistent directory (gitignored if it lives in the repo). If `go` is reached through a version-manager shim, an isolated `HOME` can also break the shim, which surfaces as a child `go env` failure inside another tool (for example golangci-lint's formatter step); keep the real Go `bin` directory first on `PATH`, or set `GOROOT` explicitly.

**The module cache is read-only on purpose.** Files under `$(go env GOMODCACHE)` are written without write permission, so `rm -rf` on a module cache placed in a scratch directory fails. Use `go clean -modcache`, or build with `-modcacherw` (it "leave[s] newly-created directories in the module cache read-write instead of making them read-only") for throwaway caches.

**`-trimpath` makes cache keys path-independent**, so several worktrees share build and test results - see the [Justfile Reference](justfile-reference.md). Exporting `GOFLAGS=-trimpath` only inside the Justfile leaves ad-hoc `go test` runs from a shell on a second, separate cache; export it from the shell profile or a repo `.envrc` as well if both are common. It also rewrites the file names `runtime.Caller` reports - "the recorded file names will begin either a module path@version (when using modules), or a plain import path" - so a test helper that locates `testdata/` through `runtime.Caller(0)` builds a path that does not exist. Grep for `runtime.Caller` before exporting it, or open `testdata/` relative to the package directory, which `go test` makes the working directory.

**Build flags are part of the cache key.** `CGO_ENABLED`, `-trimpath` and `-tags` all change it, so a smoke test compiled with default flags next to `CGO_ENABLED=0 -trimpath` release binaries recompiles the whole graph. Use one flag set for builds and tests that run together, or one exported `GOFLAGS`.

**The test cache keys files by metadata.** A test that opens a file is reused only if the file's size, mode and mtime are unchanged, so fresh CI checkouts miss for every package that reads `testdata/` - see the [Go Testing Reference](go-testing-reference.md) for `GODEBUG=gocachetest=1` and the mtime workaround.

## CI Caches (setup-go)

Three `setup-go` behaviours decide whether a Go workflow is fast or pathologically slow:

- **It hashes a repo-root `go.mod`.** Caching is on by default, but a module in a subdirectory never matches, so every run logs a restore failure and cold-compiles the whole dependency tree. Point `cache-dependency-path` at the real file.
- **It restores only the exact key, and that key hashes `go.mod`.** "By default, the cache key for Go modules is based on `go.mod`. To use `go.sum`, configure the `cache-dependency-path` input." There is no `restore-keys` prefix fallback, so every change to the hashed file is a fully cold run. If that hurts, set `cache: false` and use one `actions/cache` step with a `restore-keys` prefix, keyed per job so parallel jobs do not race on save - and end the key with something unique such as `-${{ github.sha }}`: cache entries are immutable, so a key built only from `go.sum` is saved once and every later save fails with `Unable to reserve cache`. Put the Go version (or a bumpable `CACHE_VERSION` env) at the front of every key and `restore-keys` prefix: otherwise a toolchain bump restores the previous toolchain's build cache by prefix, which is useless, fills the disk, and leaves a cold lint that can blow the job timeout. Share one module cache keyed on `go.sum` across jobs, give each job its own build cache (an exact-key hit never saves, and lint, `-race` tests and image builds compile different things), save only from `main`, and restore-only on PRs with `actions/cache/restore`. Take the paths from setup-go v7.1's `GOCACHE` and `GOMODCACHE` step outputs rather than hardcoding `~/.cache/go-build`, which is wrong on macOS and Windows runners. In a vendored repo the module cache buys nothing; cache only the build cache.
- **The cache is saved in a post step declared `post-if: success()`.** A job that fails saves nothing, so a cold run that times out stays cold forever and raising the timeout never breaks the loop. Split lint and test into separate jobs so one slow gate cannot starve the other's cache.

setup-go also exports `GOTOOLCHAIN=local`, so the `go.mod` `toolchain` line is ignored unless you use `go-version-file`. Even then it reads the `toolchain` line only while `GOTOOLCHAIN` is not already `local` (`src/installer.ts`: "use version from go directive if 'GOTOOLCHAIN' has been explicitly set"), so a workflow-level `env: GOTOOLCHAIN: local`, or a second setup-go step in the same job, silently falls back to the `go` directive's older version. A `go.work` workspace takes `go-version-file: go.work`. The same rule breaks the `oldstable` matrix leg once you bump the `go` directive past it: the older `go` fails with `go.mod requires go >= ...` instead of downloading a newer toolchain. Drop `oldstable` at that point, or keep the directive one minor behind. setup-go v7.1 also accepts the toolchain spelling in `go-version`, with one trap: "`go1.21` resolves to exactly `1.21.0`, unlike `1.21`, which matches patch releases."

## Bumping the Go Version

**GODEBUG defaults flip with the `go` directive**, not only the removed settings listed below. Each setting carries the release that changed its default (`{Name: "urlstrictcolons", Package: "net/url", Changed: 26, Old: "0"}` means that once the module says `go 1.26`, "`Parse` now rejects malformed URLs containing colons in the host subcomponent" - `http://h1:80:80/` becomes a parse error; the rule covers only `http` and `https`, so a multi-host DSN such as `postgres://h1:5432,h2:5432/db` still parses). List what a bump to 1.N flips with `rg 'Changed: N,' $(go env GOROOT)/src/internal/godebugs/table.go`, and pin an old value with a `godebug` line while you migrate.

Go 1.27 changes that touch this stack directly:

- **Generic methods.** "Go 1.27 now supports generic methods: a method declaration may declare its own type parameters." Build them with go1.27.4 or later: export data from go1.27.0-1.27.3 lets analysis facts attach to the wrong methods, which crashed staticcheck ([golang/go#82106](https://github.com/golang/go/issues/82106)).
- **`encoding/json/v2`.** "The encoding/json package is now backed by the v2 implementation" - "Marshaling and unmarshaling behavior is preserved, but the exact text of error messages may differ", so tests that assert on JSON error strings break. The escape hatch is `GOEXPERIMENT=nojsonv2` at build time.
- **`go test -json` gained an `OutputType` field**, annotating `"Action":"output"` lines. gotestsum v1.13.0 does not use it yet ([gotestsum#571](https://github.com/gotestyourself/gotestsum/issues/571)).
- **`go mod tidy` reshapes `go.mod`** to "at most two require blocks". The first tidy after the bump rewrites the file, and the lefthook `mod-tidy` job stages that rewrite into whatever you commit next.
- **Removed GODEBUG settings fail the build.** The `go` command now recognizes removed settings (`asynctimerchan`, `gotypesalias`, `tls10server`, `tlsrsakex`, `tls3des`, `tlsunsafeekm`, `x509keypairleaf`) in `go.mod` `godebug` lines and `//go:debug` comments - "If they are set to an old value, the go command will fail." Delete them before bumping.
- **gofmt alignment changed.** Go 1.27 warns that "running gofmt from Go 1.27 on previously formatted code may produce minor whitespace changes", and gofumpt v0.12.0 inherits it - expect a one-time formatting diff alongside the toolchain bump.
- **`go fix` modernizers.** "The go fix command contains several new modernizers (atomictypes, embedlit, slicesbackward, and unsafefuncs)", and `fmtappendf` is gone, so a 1.27 bump is a good moment to run `go fix ./...`. "The existing `waitgroup` analyzer was renamed to `waitgroupgo`", which matters if you disable it by name.
- **New `go test` vet failures.** "`go test` now invokes the `stdversion` vet check by default. This reports the use of standard library symbols that are too new for the Go version in force in the referring file" - adjust the `go` directive or the call site rather than suppressing it. And "The printf analyzer now reports calls such as `fmt.Errorf("...: %w", p)` in which the `%w` operand `p` has type `*E`, where the type `E` itself implements `error`" - wrap the value, or make `*E` the error type.

## Version Stamping

Since Go 1.24, `go build` sets the "main module's version in the compiled binary based on the version control system tag and/or commit". Read it at runtime:

```go
import "runtime/debug"

func version() string {
    if bi, ok := debug.ReadBuildInfo(); ok {
        return bi.Main.Version
    }
    return "unknown"
}
```

| Build | `bi.Main.Version` |
|-------|-------------------|
| `go build` on a tagged commit | `v0.3.0` |
| `go build` with uncommitted changes | `v0.3.0+dirty` |
| `go build -buildvcs=false` | `(devel)` |
| `go run .` | `(devel)` |
| `go install example.com/cmd@v0.3.0` | `v0.3.0` (from the module proxy, no `.git` needed) |

Use `-ldflags -X` only for versions git cannot supply (a non-semver build ID, a build without `.git` in the Docker context). Its target must be a package-level `string` variable, named by its full import path - `-ldflags "-X example.com/app/internal/buildinfo.version=1.2.3"`. A wrong path is silently ignored, the build succeeds and the binary still says `dev`. `-X` is applied only by your own build command, so a user's `go install module@vX` never sees it; keep the `ReadBuildInfo` fallback.

Resolve the version lazily at the call site (`sync.OnceValue(version)`), not in `init()`: package-level variable initializers run before every `init()`, so a CLI root command built in `var rootCmd = newRootCmd()` reads the version before an `init()` fallback has run and reports `dev` in `--version` and help output.

**`go version -m <binary>` shows what a binary contains**: the Go version, build settings (`-trimpath`, `CGO_ENABLED`, tags, `vcs.revision`, `vcs.modified`) and every linked `dep` with its version and hash - "The -m flag causes go version to print each file's embedded module version information". Three uses keep recurring: checking which commit a deployed binary was built from, proving two builds are dependency-equivalent (build the baseline from `git archive <ref> | tar -x -C "$tmp"` and diff the `dep` lines, for example before and after dropping `vendor/`), and measuring what a library really adds (a trivial `main` that imports it).

Stamping trades against reproducibility. VCS stamping makes every commit change the binary, which triggers redeploys of unchanged code in content-addressed pipelines; `-buildvcs=false` gives byte-identical builds for the same source, at the cost of `(devel)`. Without `.git` in the build context nothing is stamped and the version is `(devel)`; with `.git` present but no `git` binary in the image (or a repo owned by another user), the build fails with `error obtaining VCS status` until you add `-buildvcs=false` or install git.

## Cross-Platform Builds

Host-only lint and tests never compile the other operating systems. Unix-only calls (`syscall.Setsid`, `syscall.Kill`, `syscall.Flock`) need build-constrained file pairs (`proc_unix.go` with `//go:build unix`, `proc_other.go` with `//go:build !unix`), and a gate that proves the other side still compiles:

```bash
GOOS=windows GOARCH=amd64 go build ./...
GOOS=windows GOARCH=amd64 go vet ./...
```

The template's `build-release` sets `CGO_ENABLED=0` while `test` and `lint` build with cgo enabled (the host default), so a dependency that compiles only with cgo breaks only the release build. Either run one `CGO_ENABLED=0 go build ./...` in CI, or keep cgo consistent across all recipes.

**go1.27.4 tightened the cgo flag allowlist.** A file with `#cgo CFLAGS: -target arm64-apple-macos13` builds on 1.27.3 and fails on 1.27.4 with `invalid flag in #cgo CFLAGS: -target (see https://go.dev/s/invalidflag)`. Allow it explicitly with `CGO_CFLAGS_ALLOW='-target|arm64-apple-macos13'`, or pass the flag through the `CGO_CFLAGS` environment variable, which is not checked.

**go1.27.4 also rejects static libraries carrying embedded LLVM bitcode** in `#cgo LDFLAGS` - every Rust `staticlib` that links std, and any object built with `clang -fembed-bitcode` - with `disallowed LTO section __LLVM,__bitcode in #cgo LDFLAGS` (`.llvmbc` on Linux). The Go team calls it "a clear regression" ([golang/go#83126](https://github.com/golang/go/issues/83126)). `CGO_LDFLAGS_ALLOW` does not help on 1.27.4, but moving the `-L`/`-l` flags from the directive into the `CGO_LDFLAGS` environment variable builds. The fix is on master, with the 1.27 backport pending ([#83136](https://github.com/golang/go/issues/83136)).

## Private Modules

`GOPRIVATE` (a comma-separated glob list such as `github.com/yourorg/*`) makes the `go` command skip the public proxy and the checksum database for matching modules - the usual fix when golangci-lint's `typecheck` or `go mod download` fails fetching a private module from `proxy.golang.org` or `sum.golang.org` (`410 Gone`, `404 Not Found`). CI then needs read credentials for those repos (a `.netrc`, `GOAUTH` - "a semicolon-separated list of authentication commands for go-import and HTTPS module mirror interactions", for example `GOAUTH="git $PWD"`, which runs `git credential fill` in that directory - or `git config url."https://x-access-token:${TOKEN}@github.com/".insteadOf`), and a Docker build needs them as a BuildKit secret (`RUN --mount=type=secret,id=netrc,target=/root/.netrc go mod download`), never as a build arg baked into a layer.

## Container Builds

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.27.4 AS build
ENV GOTOOLCHAIN=local GOFLAGS=-mod=readonly
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/myapp ./cmd/myapp

FROM gcr.io/distroless/static-debian13:nonroot
COPY --from=build /out/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]
```

- **The image tag compiles the binary, not the `toolchain` line.** Under `GOTOOLCHAIN=local` a newer `go` line fails the build (`go: go.mod requires go >= ... (running go ...; GOTOOLCHAIN=local)`) instead of downloading a toolchain inside the build, and `-mod=readonly` fails it whenever `go.mod` would need updating. But a newer `toolchain` line is silently ignored, so a repo whose `go.mod` says 1.26.6 and whose image is `golang:1.26.5` ships binaries carrying the stdlib advisories govulncheck already cleared. Bump the `FROM` tag in the same change as the toolchain line.
- **One image per codebase is often enough.** Instead of a Dockerfile stage, an image and a CI build step per command, build every `cmd/` binary once on the CI runner (with its restored `go-build` cache), `COPY` them into one runtime image, and start workers and one-off jobs from that image with a different command. The Dockerfile then copies rather than compiles. `go build -o bin/ ./cmd/...` builds them all - "If the named output is an existing directory or ends with a slash or backslash, then any resulting executables will be written to that directory" - so a new `cmd/<name>` needs no CI or Dockerfile edit. The trade-off is one shared base: a job that needs extra runtime packages (ffmpeg, say) enlarges the image every command runs from, in exchange for one image to build, scan and tag per deploy instead of one per command.
- **Distroless has no shell, `curl` or `wget`.** Startup steps belong in Go, and a `HEALTHCHECK` has to call the binary itself (`HEALTHCHECK CMD ["/myapp", "-health"]`).
- **PID 1 needs care.** Go's default handling of `SIGTERM` exits immediately without running deferred cleanup, so install `signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)` in `main` before acquiring locks or starting servers, and bound the shutdown with a timeout that fits the orchestrator's grace period (see the [Go Correctness Reference](go-correctness-reference.md)). A Go PID 1 also does not reap orphaned grandchildren: if the binary spawns subprocesses, run it under `tini` or `docker run --init`, or zombies accumulate.
- **Runtime sizing.** Since Go 1.25 the runtime derives `GOMAXPROCS` from the container's CPU limit; an explicit `GOMAXPROCS` overrides that, so remove stale settings. `GOMEMLIMIT` is a soft limit on the Go heap and excludes non-Go memory (cgo allocations, `mmap`), so leave headroom below the container limit.
- **Cache mounts help only on persistent builders.** `RUN --mount=type=cache,target=/root/.cache/go-build` starts empty on throwaway CI runners, and `cache-to: type=gha` saves image layers, not those mounts.

## Releases (GoReleaser)

- Run `goreleaser check --config .goreleaser.yaml` in PR CI, so a tag can never be cut against a config that will not build, and rehearse locally with `goreleaser release --snapshot --clean`.
- Gitignore `dist/`: GoReleaser's output in the working tree makes VCS stamping report `+dirty`. Read the version from build info (above) rather than `-X` only, so `go install module@vX` users see it too.
- With release-please, build first and tag last: set `skip-github-release: true`, create the tag locally without pushing it, and let GoReleaser upload to a draft release and publish it, which creates the tag on GitHub. A failure before publish - a darwin notarization timeout, say - then leaves no tag, no release and no Homebrew cask update, and a re-run is safe. Guard signing and notarization with `isEnvSet` so forks and snapshots skip them.
- **Tag runs restore only the default branch's caches.** "Workflow runs can restore caches created in either the current branch or the default branch", and they "cannot restore caches created for different tag names", so a tag-triggered release starts cold unless a `main` run already saved a build cache covering every `GOOS`/`GOARCH` it builds. Seed that cache from `main` whenever the release config or `go.sum` changes, and let the run finish before tagging.
- **A tag pushed with `GITHUB_TOKEN` starts no workflow** - "events triggered by the GITHUB_TOKEN will not create a new workflow run" - so a job that creates the tag for a tag-triggered release needs a GitHub App installation token or a personal access token.
