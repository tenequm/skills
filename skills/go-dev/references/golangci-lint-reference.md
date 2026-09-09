# golangci-lint v2 Reference

Latest: **v2.13.2** (2026-08-27). Requires `version: "2"` in config.

**Go version floor:** "golangci-lint supports Go versions lower or equal to the Go version used to compile it." Go 1.27 support arrived in v2.13.0 ("🎉 go1.27 support"), so a Go 1.27 project needs v2.13 or newer - an older pin fails outright rather than degrading. `go install` of v2.13.2 itself requires Go 1.26.

## Installation

```bash
# Binary (recommended)
curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.13.2

# Homebrew
brew install golangci-lint

# Docker
docker run --rm -v $(pwd):/app -w /app golangci/golangci-lint:v2.13.2 golangci-lint run

# mise (uses the aqua backend, so it fetches the GitHub binary)
mise use -g golangci-lint@2.13.2

# go install (not recommended - dependency conflicts possible)
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.2
```

**Upstream recommends binary installation and warns against the tools pattern:** "Using `go install`/`go get`, \"tools pattern\", and `tool` command/directives installations aren't guaranteed to work. We recommend using binary installation." Seven reasons are listed, the load-bearing one for shared repos being that "the dependencies of a tool can modify the dependencies of another tool or your project". There is a blunt "We don't recommend using `go tool`" on top.

If you need it in `go.mod` anyway, isolate it behind a dedicated module file so it cannot perturb your project's graph - "the best approach is to use a dedicated module or module file to isolate golangci-lint from other tools or dependencies":

```bash
go mod init -modfile=golangci-lint.mod github.com/org/repo/golangci-lint
go get -tool -modfile=golangci-lint.mod github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.2
go tool -modfile=golangci-lint.mod golangci-lint run
go get -tool -modfile=golangci-lint.mod github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest   # update
```

## Commands

```bash
golangci-lint run              # Lint (default: ./...)
golangci-lint run --fix        # Lint and apply autofixes
golangci-lint fmt              # Format code (v2 feature)
golangci-lint fmt --diff       # Show formatting diff
golangci-lint migrate          # Migrate v1 config to v2
golangci-lint linters          # List enabled linters
golangci-lint help linters     # List all available linters
golangci-lint formatters       # List enabled formatters
golangci-lint config path      # Show which config file is used
golangci-lint cache clean      # Clear analysis cache (fixes phantom issues from stale results)
golangci-lint cache status     # Show cache directory and size
golangci-lint custom           # Build a binary with module plugins (.custom-gcl.yml)
golangci-lint version          # Print version
golangci-lint run --fast-only  # Run fast linters only (for editors)
golangci-lint run --default=none --enable=govet  # Run specific linters
```

## Config File Structure

Config file: `.golangci.yml` (searched in CWD, then parent dirs, then home).

JSON Schema: use the **versioned** URL matching your binary, e.g. `https://golangci-lint.run/jsonschema/golangci.v2.13.jsonschema.json`. The unversioned `golangci.jsonschema.json` tracks master and already contains options your released binary rejects, so validating against it produces false positives. `golangci-lint config verify` against the installed binary is the authoritative check.

`.golangci.reference.yml` in the repo lists every supported option with descriptions and defaults - "There is a `.golangci.reference.yml` file with all supported options, their descriptions, and default values."

**Cache isolation:** golangci-lint honours `GOLANGCI_LINT_CACHE`. Give each git worktree its own value so a deleted branch's cached results cannot resurface as issues in files that no longer exist. The cache does not reliably invalidate on config, tool-version, or dependency changes, so if a phantom issue keeps returning, fold those inputs into the cache path rather than clearing by hand each time.

**Cache isolation does not buy you concurrency.** The run lock is a single file in the system temp dir - `filepath.Join(os.TempDir(), "golangci-lint.lock")` - so two runs collide no matter how their caches are separated. A second run retries for five seconds and then exits with `parallel golangci-lint is running`. Two knobs change this:

```yaml
run:
  allow-parallel-runners: true   # "Allow multiple parallel golangci-lint instances running." Drops the lock.
  allow-serial-runners: true     # "Allow multiple golangci-lint instances running, but serialize them around a lock." Waits instead of failing.
```

Reach for one of them before putting `golangci-lint fmt` and `golangci-lint run` in the same `just` recipe under `[parallel]`, or in concurrent CI steps - otherwise the failure lands on green code and looks like a lint bug.

**Debugging the nolint filter.** When nolintlint claims a live `//nolint` directive is unused, `GL_DEBUG=nolint_filter` prints what the filter actually received - the fastest way to tell a stale cache from a genuinely dead suppression before you delete a real one. Other useful keys: `GL_DEBUG=exec` (the lock file), `pkgcache`, `linters_context`, `enabled_linters`.

```yaml
version: "2"  # REQUIRED

run:
  timeout: 5m             # Default: 0 (disabled in v2)
  tests: true             # Include test files
  build-tags: []
  go: ""                  # Default: from go.mod
  concurrency: 0          # 0 = auto (CPU count)
  relative-path-mode: cfg # cfg | gomod | gitroot | wd
  issues-exit-code: 1     # Exit code when issues were found
  modules-download-mode: readonly  # mod | readonly | vendor
  allow-parallel-runners: false    # Drop the global run lock
  allow-serial-runners: false      # Queue on the lock instead of failing
  enable-build-vcs: false          # Default false, which implies `-buildvcs=false`

linters:
  default: standard       # standard | all | none | fast
  enable: [...]
  disable: [...]
  settings:
    # Per-linter config (was top-level linters-settings in v1)
    govet:
      enable: [shadow]
    revive:
      enable-all-rules: true
  exclusions:
    generated: strict      # strict | lax | disable
    warn-unused: true
    presets:               # NOT enabled by default in v2
      - comments
      - std-error-handling
      - common-false-positives
    rules:
      - path: _test\.go
        linters: [gocyclo, errcheck, dupl, gosec]
    paths:
      - third_party$
      - vendor$

formatters:
  enable: [gofumpt, goimports]
  settings:
    gofumpt:
      extra-rules: true
    gci:
      sections: [standard, default, "prefix(github.com/myorg/myrepo)"]
  exclusions:
    generated: strict

issues:
  max-issues-per-linter: 50   # 0 = unlimited
  max-same-issues: 3          # 0 = unlimited
  new: false
  new-from-merge-base: ""     # e.g., "main"
  fix: false

output:
  formats:
    text:
      path: stdout
      print-linter-name: true
      colors: true
  sort-order: [linter, file]
  show-stats: true
  path-mode: ""           # "abs" shows absolute paths instead of relative ones
  path-prefix: ""         # Prepended to every reported path

severity:
  default: ""
  rules:
    - linters: [dupl]
      severity: info
```

## Default Linters (the "standard" set)

Enabled when `default: standard` (the default):

1. **errcheck** - unchecked errors
2. **govet** - suspicious constructs (like `go vet`)
3. **ineffassign** - unused assignments
4. **staticcheck** - comprehensive static analysis (includes gosimple + stylecheck in v2)
5. **unused** - unused code

## Linter Catalog by Category

### Bug Detection

| Linter | Description | Autofix |
|--------|-------------|---------|
| bodyclose | HTTP response body not closed | |
| contextcheck | Non-inherited context usage | |
| durationcheck | Two durations multiplied together | |
| errcheck | Unchecked errors (default) | |
| errchkjson | Types passed to json encoding | |
| errorlint | Go 1.13+ error wrapping issues | Yes |
| exhaustive | Enum switch exhaustiveness | |
| fatcontext | Nested contexts in loops | Yes |
| gosec | Security problems | |
| govet | Suspicious constructs (default) | Yes |
| makezero | Slices with non-zero initial length | |
| musttag | Field tags in marshaled structs | |
| nilerr | Returns nil when err is not nil | |
| nilnesserr | err != nil but returns different nil error | |
| noctx | Missing context.Context usage | |
| rowserrcheck | Rows.Err not checked | |
| sqlclosecheck | sql.Rows/Stmt not closed | |
| staticcheck | Comprehensive static analysis (default) | Yes |
| testifylint | Testify usage issues | Yes |

### Performance

| Linter | Description | Autofix |
|--------|-------------|---------|
| fatcontext | Context allocation in loops | Yes |
| perfsprint | Faster alternatives to fmt.Sprintf | Yes |
| prealloc | Slice pre-allocation opportunities | |

### Style & Code Quality

| Linter | Description | Autofix |
|--------|-------------|---------|
| copyloopvar | Loop variable copies | Yes |
| dupl | Duplicate code fragments | |
| dupword | Duplicate words in source | Yes |
| err113 | Error handling expressions | Yes |
| errname | Sentinel error naming conventions | |
| exptostd | Replace x/exp with stdlib | Yes |
| goconst | Repeated strings that could be constants | |
| gocritic | Bugs, performance, style diagnostics | Yes |
| godot | Comments ending in period | Yes |
| intrange | Integer range in for loops | Yes |
| mirror | bytes/strings mirror patterns | Yes |
| misspell | Misspelled English words | Yes |
| modernize | Suggests modern Go language features | |
| nakedret | Naked returns | Yes |
| nestif | Deeply nested if statements | |
| nolintlint | Ill-formed nolint directives | Yes |
| nonamedreturns | Named returns | |
| predeclared | Shadowing predeclared identifiers | |
| revive | Fast, configurable meta-linter | |
| sloglint | log/slog code style | Yes |
| thelper | Missing t.Helper() in test helpers | |
| unconvert | Unnecessary type conversions | |
| unparam | Unused function parameters | |
| usestdlibvars | Use stdlib variables/constants | Yes |
| usetesting | Use testing package replacements | Yes |
| wastedassign | Wasted assignments | |
| whitespace | Unnecessary newlines | Yes |
| wrapcheck | Error wrapping from external packages | |
| wsl_v5 | Whitespace/cuddling style (replaces `wsl`) | |

### Also Available (not in the sets above)

| Linter | Description | Autofix |
|--------|-------------|---------|
| arangolint | ArangoDB query issues, incl. injection | |
| canonicalheader | Non-canonical HTTP header keys | Yes |
| clickhouselint | ClickHouse driver misuse (v2.12.0+) | |
| embeddedstructfieldcheck | Embedded-field placement in structs | |
| funcorder | Constructor/method ordering within a file | |
| gochecksumtype | Exhaustiveness for sum types | |
| godoclint | Godoc comment conventions | |
| gomodguard_v2 | Allow/blocklist direct module dependencies | |
| iface | Interface misuse, incl. unused methods | |
| iotamixing | Mixed iota and explicit values in a const block | |
| nilnil | Returning both a nil value and a nil error | |
| noinlineerr | Inline `if err := f(); err != nil` declarations | |
| protogetter | Direct proto field access instead of getters | Yes |
| recvcheck | Mixed pointer/value receivers on one type | |
| spancheck | OpenTelemetry/Census span mistakes | |
| tagalign | Struct tag alignment | Yes |
| unqueryvet | `SELECT *`, N+1 queries, SQL injection, tx leaks | |

### Deprecated Names

| Deprecated | Replacement | Since |
|-----------|-------------|-------|
| `wsl` | `wsl_v5` | v2.2.0 |
| `gomodguard` | `gomodguard_v2` | v2.12.0 |
| `exhaustruct` | `exhaustruct_v5` | v2.13.0 |

Deprecated names still resolve but will be removed; `golangci-lint help linters` marks them `[deprecated]`.

## Recommended Linter Sets

### Minimal (large existing codebases)

```yaml
linters:
  default: standard
  enable:
    - bodyclose
    - errorlint
    - gosec
    - noctx
    - sqlclosecheck
```

### Comprehensive (new projects - recommended)

```yaml
linters:
  default: standard
  enable:
    - bodyclose
    - copyloopvar
    - dupl
    - durationcheck
    - err113
    - errname
    - errorlint
    - exhaustive
    - exptostd
    - fatcontext
    - goconst
    - gocritic
    - gosec
    - intrange
    - misspell
    - modernize
    - musttag
    - nakedret
    - nestif
    - nilerr
    - noctx
    - nolintlint
    - nonamedreturns
    - perfsprint
    - prealloc
    - revive
    - sqlclosecheck
    - testifylint
    - thelper
    - unconvert
    - unparam
    - usestdlibvars
    - usetesting
    - wastedassign
    - whitespace
    - wrapcheck
```

### Maximum (enable all, disable noisy ones)

```yaml
linters:
  default: all
  disable:
    - exhaustruct_v5   # Too strict for most projects (v2.13.0+ name; was `exhaustruct`)
    - gochecknoglobals # Impractical for many codebases
    - gochecknoinits   # Too restrictive
    - ireturn          # Controversial
    - varnamelen       # Too opinionated
    - mnd              # Very noisy (magic numbers)
    - lll              # Line length is editor config territory
    - funlen           # Arbitrary length limits
    - godox            # FIXME/TODO are normal in active dev
    - wsl_v5           # Very opinionated whitespace rules
```

## Nolint Directive Syntax

```go
// Suppress specific linters on this line:
var bad int //nolint:revive,unused

// Suppress all linters:
var bad int //nolint:all

// Suppress for a function/block:
//nolint:gocyclo
func complexFunction() { ... }

// Suppress for entire file (before package):
//nolint:unparam
package pkg

// With justification (recommended, enforced by nolintlint):
var x int //nolint:revive // legacy code, scheduled for cleanup
```

**Syntax rules** - nolint is a Go directive, not a comment:
- NO space between `//` and `nolint`
- NO space between `nolint` and `:`
- NO space between `:` and linter names

Valid: `//nolint:xxx` | Invalid: `// nolint`, `//nolint :xxx`, `//nolint: xxx`

## Exclusion Presets

```yaml
linters:
  exclusions:
    presets:
      - comments              # Suppress exported-should-have-comment checks
      - std-error-handling    # Suppress errcheck on stdout/stderr/Close/Flush
      - common-false-positives # Suppress common gosec false positives
      - legacy                # Suppress legacy govet/staticcheck patterns
```

Not enabled by default in v2 - you must opt in explicitly.

`path-except` / `paths-except` are the inverses, letting a linter run *only* on matching files - "Run some linter only for test files by excluding its issues for everything else. - path-except: `_test\.go`".

## Output Formats

`output.formats.text` is only one of nine. All can be written simultaneously, each to its own path:

```yaml
output:
  formats:
    text:
      path: stdout
      print-linter-name: true
      colors: true
    sarif:
      path: golangci-lint.sarif
    junit-xml:
      path: golangci-lint-report.xml
```

Available: `text`, `json`, `tab`, `html`, `checkstyle`, `code-climate`, `junit-xml`, `teamcity`, `sarif`.

`sarif` is the path into GitHub code scanning - upload the file with `github/codeql-action/upload-sarif` and findings appear as annotations in the Security tab. `junit-xml` and `checkstyle` cover most other CI systems.

## Incremental Adoption

Beyond the Action's `only-new-issues`, the binary can restrict reporting to changed code:

```bash
golangci-lint run --new-from-merge-base=main   # only issues absent from the merge base
golangci-lint run --new-from-rev=HEAD~1        # only issues introduced since a revision
golangci-lint run --new-from-patch=changes.patch
golangci-lint run --whole-files                # report all issues in a changed file, not just changed lines
golangci-lint run --enable-only=errcheck       # run exactly one linter, ignoring config
```

The same knobs exist in config under `issues.new`, `issues.new-from-merge-base`, and `issues.new-from-rev`.

## Module Plugins

Linters not bundled with golangci-lint can be compiled into a custom binary. Define the build in `.custom-gcl.yml`, then "Run the command `golangci-lint custom`" to produce it:

```yaml
# .custom-gcl.yml
version: v2.13.2
name: custom-golangci-lint
destination: ./bin
plugins:
  - module: github.com/example/my-linter
    version: v1.0.0
```

The resulting binary reads the same `.golangci.yml` and exposes the plugin's linters alongside the built-in set.

Module plugins are one of two plugin systems. **Go plugins** (`.so` files loaded at runtime, built with `go build -buildmode=plugin`) are the other; they avoid the rebuild step but are fragile across toolchain versions and unsupported on Windows. Prefer module plugins unless you specifically need runtime loading.

## Editor and Shell Integration

Beyond the editor settings below, two integrations are easy to miss:

- **`golangci-lint-langserver`** exposes the linter over LSP for NeoVim, Vim, and Emacs, so findings appear inline without a save-and-run cycle.
- **`golangci-lint completion`** generates shell completion: "Golangci-lint can generate Bash, fish, PowerShell, and Zsh completion files."

## Other CI Systems

The GitHub Action is the best-supported path, but upstream documents GitLab CI and Buildkite recipes as well. The portable shape is the install script plus a cached `$GOLANGCI_LINT_CACHE`; use the `junit-xml` or `checkstyle` output format to surface findings natively in those systems.

## Formatters Section (v2)

Formatters are separate from linters in v2. They have their own `enable`, `settings`, and `exclusions`.

Available formatters: `gci`, `gofmt`, `gofumpt`, `goimports`, `golines`, `swaggo` (added v2.2.0)

```yaml
formatters:
  enable:
    - gofumpt
    - goimports
  settings:
    gofumpt:
      extra-rules: true          # all extra rules
      # or select individually (v2.13.0+, gofumpt 0.11.0):
      # extra:
      #   group-params: true
      #   clothe-returns: true
      #   balance-calls: false
    goimports:
      local-prefixes: github.com/myorg/myrepo
```

Run: `golangci-lint fmt`, `golangci-lint fmt --diff`, or `golangci-lint fmt --diff-colored`.

Do not pair `golangci-lint fmt` as the CI gate with a standalone `gofumpt -w` as the fixer - they can disagree on the same file, so the gate fails on code the fixer just formatted. Pick one for both roles.

## GitHub Actions

Official action: `golangci/golangci-lint-action@v9`

```yaml
- uses: actions/checkout@v7
- uses: actions/setup-go@v7
  with:
    go-version: stable
- uses: golangci/golangci-lint-action@v9
  with:
    version: v2.13
    # only-new-issues: true  # For incremental adoption
```

Keep `version:` at or above the Go version `setup-go` resolves. With `go-version: stable` that is the newest Go release, so a pin left behind after a Go major bump breaks the job.

Key options:

| Option | Default | Description |
|--------|---------|-------------|
| `version` | *(optional)* | e.g. `v2.13`, `v2.13.2`, or `latest`. Declared `required: false` in `action.yml` - omit it and the action resolves a default |
| `version-file` | - | Read the version from `.golangci-lint-version` or `.tool-versions` |
| `install-only` | false | Install the binary without running it |
| `only-new-issues` | false | Show only new issues on PRs |
| `verify` | true | Validate config against JSON Schema |
| `cache-invalidation-interval` | 7 | Days before cache refresh |
| `skip-save-cache` | false | Restore but don't save cache |

## Editor Integration

**VS Code:**
```json
{
  "go.lintTool": "golangci-lint",
  "go.lintFlags": ["--path-mode=abs", "--fast-only"]
}
```

**GoLand:** Built-in support since 2025.1 for both v1 and v2.

## v2 Migration from v1

Key breaking changes in v2.0.0 (March 2025):

- `version: "2"` required in config
- `staticcheck`, `gosimple`, `stylecheck` merged into `staticcheck`
- `linters-settings:` moved under `linters.settings:`
- `issues.exclude-rules` moved to `linters.exclusions.rules`
- Formatters moved to `formatters:` section
- `disable-all: true` replaced by `default: none`
- No exclusions by default (must use `presets:`)
- Many deprecated linters removed (`deadcode`, `golint`, `varcheck`, etc.)

Run `golangci-lint migrate` to auto-convert v1 configs.

## Notable v2.x Additions

| Version | Key Additions |
|---------|--------------|
| v2.1.0 | `funcorder` linter, colored diff for `fmt` |
| v2.2.0 | `noinlineerr` linter, `wsl_v5` replaces deprecated `wsl` |
| v2.4.0 | Go 1.25 support |
| v2.5.0 | `godoclint`, `unqueryvet`, `iotamixing` linters |
| v2.6.0 | `modernize` analyzer suite |
| v2.9.0 | Go 1.26 support |
| v2.11.0 | New gosec rules, revive `package-naming` (⚠️ breaking: package checks moved out of `var-naming`) |
| v2.12.0 | `clickhouselint` linter, `gomodguard_v2` major bump, JSON schema embedded in the binary |
| v2.13.0 | **Go 1.27 support**; `exhaustruct` deprecated in favour of `exhaustruct_v5`; gofumpt 0.11.0 with granular `extra.*` options; `govet-modernize` 0.49.0 |
| v2.13.1 | Linter bug fixes |
| v2.13.2 | Cache-entropy fix; linter deps bumped (`staticcheck` 0.8.1, `iface` 1.5.1, `unparam`); `canonicalheader` moved to a temporary fork. No config-schema change (current release) |
