# Go Toolchain Reference

The `go` command behaviours that sit between the code and the gates: multi-module workspaces, the build and test caches, version stamping, and container builds. Verified against go1.27.3.

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

Two more traps:

- **Tidy reads every build tag.** A test file behind `//go:build integration` that imports a sibling module adds a real `require`, and two modules whose tagged tests import each other form a module cycle. Move such tests into a leaf module.
- **Relative `replace` paths must stay inside the repo.** `replace example.com/x => ../../x` resolves in your checkout and breaks in a worktree, a temp copy, or CI.

CI needs the workspace file too: setup-go accepts `go-version-file: go.work`, and govulncheck needs a `go.mod`, so run it once per module with `govulncheck -C <module-dir> ./...`.

## Build and Test Caches

**`GOCACHE` is shared, concurrent-safe and uncapped.** "The cache is safe for concurrent invocations of the go command." There is no size limit - "The go command periodically deletes cached data that has not been used recently" - so parallel builds across many worktrees or agent lanes can grow it to tens of GiB between trims. Share one cache rather than giving each lane its own (each new cache is a full cold rebuild), and reclaim space with `go clean -cache`. `go env GOCACHE` prints the location.

**Agent sandboxes and read-only homes.** When the default cache directory is not writable, builds fail as `FAIL <pkg> [setup failed]` with `open .../go-build/...: operation not permitted`. Set `GOCACHE` to one absolute, writable, persistent directory (gitignored if it lives in the repo). If `go` is reached through a version-manager shim, an isolated `HOME` can also break the shim, which surfaces as a child `go env` failure inside another tool (for example golangci-lint's formatter step); keep the real Go `bin` directory first on `PATH`, or set `GOROOT` explicitly.

**The module cache is read-only on purpose.** Files under `$(go env GOMODCACHE)` are written without write permission, so `rm -rf` on a module cache placed in a scratch directory fails. Use `go clean -modcache`, or build with `-modcacherw` (it "leave[s] newly-created directories in the module cache read-write instead of making them read-only") for throwaway caches.

**`-trimpath` makes cache keys path-independent**, so several worktrees share build and test results - see the [Justfile Reference](justfile-reference.md). Exporting `GOFLAGS=-trimpath` only inside the Justfile leaves ad-hoc `go test` runs from a shell on a second, separate cache; export it from the shell profile or a repo `.envrc` as well if both are common.

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

Stamping trades against reproducibility. VCS stamping makes every commit change the binary, which triggers redeploys of unchanged code in content-addressed pipelines; `-buildvcs=false` gives byte-identical builds for the same source, at the cost of `(devel)`. Without `.git` in the build context nothing is stamped and the version is `(devel)`; with `.git` present but no `git` binary in the image (or a repo owned by another user), the build fails with `error obtaining VCS status` until you add `-buildvcs=false` or install git.

## Cross-Platform Builds

Host-only lint and tests never compile the other operating systems. Unix-only calls (`syscall.Setsid`, `syscall.Kill`, `syscall.Flock`) need build-constrained file pairs (`proc_unix.go` with `//go:build unix`, `proc_other.go` with `//go:build !unix`), and a gate that proves the other side still compiles:

```bash
GOOS=windows GOARCH=amd64 go build ./...
GOOS=windows GOARCH=amd64 go vet ./...
```

The template's `build-release` sets `CGO_ENABLED=0` while `test` and `lint` build with cgo enabled (the host default), so a dependency that compiles only with cgo breaks only the release build. Either run one `CGO_ENABLED=0 go build ./...` in CI, or keep cgo consistent across all recipes.

## Private Modules

`GOPRIVATE` (a comma-separated glob list such as `github.com/yourorg/*`) makes the `go` command skip the public proxy and the checksum database for matching modules - the usual fix when golangci-lint's `typecheck` or `go mod download` fails fetching a private module from `proxy.golang.org` or `sum.golang.org` (`410 Gone`, `404 Not Found`). CI then needs read credentials for those repos (a `.netrc` or `git config url."https://x-access-token:${TOKEN}@github.com/".insteadOf`), and a Docker build needs them as a BuildKit secret (`RUN --mount=type=secret,id=netrc,target=/root/.netrc go mod download`), never as a build arg baked into a layer.

## Container Builds

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.27.3 AS build
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

- **Distroless has no shell, `curl` or `wget`.** Startup steps belong in Go, and a `HEALTHCHECK` has to call the binary itself (`HEALTHCHECK CMD ["/myapp", "-health"]`).
- **PID 1 needs care.** Go's default handling of `SIGTERM` exits immediately without running deferred cleanup, so install `signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)` in `main` before acquiring locks or starting servers, and bound the shutdown with a timeout that fits the orchestrator's grace period (see the [Go Correctness Reference](go-correctness-reference.md)). A Go PID 1 also does not reap orphaned grandchildren: if the binary spawns subprocesses, run it under `tini` or `docker run --init`, or zombies accumulate.
- **Runtime sizing.** Since Go 1.25 the runtime derives `GOMAXPROCS` from the container's CPU limit; an explicit `GOMAXPROCS` overrides that, so remove stale settings. `GOMEMLIMIT` is a soft limit on the Go heap and excludes non-Go memory (cgo allocations, `mmap`), so leave headroom below the container limit.
- **Cache mounts help only on persistent builders.** `RUN --mount=type=cache,target=/root/.cache/go-build` starts empty on throwaway CI runners, and `cache-to: type=gha` saves image layers, not those mounts.
