# golangci-lint v2 Reference

Latest: **v2.11.4** (March 2026). Requires `version: "2"` in config.

## Installation

```bash
# Binary (recommended)
curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b $(go env GOPATH)/bin v2.11.4

# Homebrew
brew install golangci-lint

# Docker
docker run --rm -v $(pwd):/app -w /app golangci/golangci-lint:v2.11.4 golangci-lint run

# go install (not recommended - dependency conflicts possible)
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.11.4
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
golangci-lint cache clean      # Clear analysis cache
golangci-lint run --fast-only  # Run fast linters only (for editors)
golangci-lint run --default=none --enable=govet  # Run specific linters
```

## Config File Structure

Config file: `.golangci.yml` (searched in CWD, then parent dirs, then home).

JSON Schema: `https://golangci-lint.run/jsonschema/golangci.jsonschema.json`

```yaml
version: "2"  # REQUIRED

run:
  timeout: 5m             # Default: 0 (disabled in v2)
  tests: true             # Include test files
  build-tags: []
  go: ""                  # Default: from go.mod
  concurrency: 0          # 0 = auto (CPU count)
  relative-path-mode: cfg # cfg | gomod | gitroot | wd

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
    - exhaustruct      # Too strict for most projects
    - gochecknoglobals # Impractical for many codebases
    - gochecknoinits   # Too restrictive
    - ireturn          # Controversial
    - varnamelen       # Too opinionated
    - mnd              # Very noisy (magic numbers)
    - lll              # Line length is editor config territory
    - funlen           # Arbitrary length limits
    - godox            # FIXME/TODO are normal in active dev
    - wsl              # Deprecated, use wsl_v5
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

## Formatters Section (v2)

Formatters are separate from linters in v2. They have their own `enable`, `settings`, and `exclusions`.

Available formatters: `gci`, `gofmt`, `gofumpt`, `goimports`, `golines`

```yaml
formatters:
  enable:
    - gofumpt
    - goimports
  settings:
    gofumpt:
      extra-rules: true
    goimports:
      local-prefixes: github.com/myorg/myrepo
```

Run: `golangci-lint fmt` or `golangci-lint fmt --diff`

## GitHub Actions

Official action: `golangci/golangci-lint-action@v9`

```yaml
- uses: actions/checkout@v6
- uses: actions/setup-go@v6
  with:
    go-version: stable
- uses: golangci/golangci-lint-action@v9
  with:
    version: v2.11
    # only-new-issues: true  # For incremental adoption
```

Key options:

| Option | Default | Description |
|--------|---------|-------------|
| `version` | required | e.g. `v2.11` or `v2.11.4` |
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
| v2.11.0 | New gosec rules, revive `package-naming` |
