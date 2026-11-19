# Go Toolchain Reference

The `go` command behaviours that sit between the code and the gates: multi-module workspaces, the build and test caches, version stamping, and container builds. Verified against go1.27.4.

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

**`-trimpath` makes cache keys path-independent**, so several worktrees share build and test results - see the [Justfile Reference](justfile-reference.md). Exporting `GOFLAGS=-trimpath` only inside the Justfile leaves ad-hoc `go test` runs from a shell on a second, separate cache; export it from the shell profile or a repo `.envrc` as well if both are common.

**Build flags are part of the cache key.** `CGO_ENABLED`, `-trimpath` and `-tags` all change it, so a smoke test compiled with default flags next to `CGO_ENABLED=0 -trimpath` release binaries recompiles the whole graph. Use one flag set for builds and tests that run together, or one exported `GOFLAGS`.

**The test cache keys files by metadata.** A test that opens a file is reused only if the file's size, mode and mtime are unchanged, so fresh CI checkouts miss for every package that reads `testdata/` - see the [Go Testing Reference](go-testing-reference.md) for `GODEBUG=gocachetest=1` and the mtime workaround.

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
- **One image per codebase is often enough.** Instead of a Dockerfile stage, an image and a CI build step per command, build every `cmd/` binary once on the CI runner (with its restored `go-build` cache), `COPY` them into one runtime image, and start workers and one-off jobs from that image with a different command. The Dockerfile then copies rather than compiles.
- **Distroless has no shell, `curl` or `wget`.** Startup steps belong in Go, and a `HEALTHCHECK` has to call the binary itself (`HEALTHCHECK CMD ["/myapp", "-health"]`).
- **PID 1 needs care.** Go's default handling of `SIGTERM` exits immediately without running deferred cleanup, so install `signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)` in `main` before acquiring locks or starting servers, and bound the shutdown with a timeout that fits the orchestrator's grace period (see the [Go Correctness Reference](go-correctness-reference.md)). A Go PID 1 also does not reap orphaned grandchildren: if the binary spawns subprocesses, run it under `tini` or `docker run --init`, or zombies accumulate.
- **Runtime sizing.** Since Go 1.25 the runtime derives `GOMAXPROCS` from the container's CPU limit; an explicit `GOMAXPROCS` overrides that, so remove stale settings. `GOMEMLIMIT` is a soft limit on the Go heap and excludes non-Go memory (cgo allocations, `mmap`), so leave headroom below the container limit.
- **Cache mounts help only on persistent builders.** `RUN --mount=type=cache,target=/root/.cache/go-build` starts empty on throwaway CI runners, and `cache-to: type=gha` saves image layers, not those mounts.

## Releases (GoReleaser)

- Run `goreleaser check --config .goreleaser.yaml` in PR CI, so a tag can never be cut against a config that will not build, and rehearse locally with `goreleaser release --snapshot --clean`.
- Gitignore `dist/`: GoReleaser's output in the working tree makes VCS stamping report `+dirty`. Read the version from build info (above) rather than `-X` only, so `go install module@vX` users see it too.
- With release-please, build first and tag last: set `skip-github-release: true`, create the tag locally without pushing it, and let GoReleaser upload to a draft release and publish it, which creates the tag on GitHub. A failure before publish - a darwin notarization timeout, say - then leaves no tag, no release and no Homebrew cask update, and a re-run is safe. Guard signing and notarization with `isEnvSet` so forks and snapshots skip them.
