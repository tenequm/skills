# gofumpt Reference

Latest: **v0.9.2** (October 2025). Fork of gofmt as of Go 1.25. Requires Go 1.24+ to build.

gofumpt is a **strict superset of gofmt** - any code formatted by gofumpt produces zero changes when processed by gofmt. It adds 17+ opinionated formatting rules.

## Installation

```bash
# From source (recommended)
go install mvdan.cc/gofumpt@latest

# Pre-built binaries from GitHub Releases
# Available for darwin/linux/windows on amd64/arm64

# Via gopls (no separate binary needed for editor use)
# Configure your editor to tell gopls to use gofumpt formatting
```

## CLI Usage

```bash
gofumpt -w .                  # Format all Go files recursively, in-place
gofumpt -l .                  # List files that differ from gofumpt style
gofumpt -d main.go            # Show diff without modifying (non-zero exit if diff exists)
gofumpt -w main.go            # Format single file in-place
gofumpt -extra .              # Enable all extra rules
gofumpt -extra=group_params . # Enable specific extra rule
gofumpt -lang=go1.25 .        # Specify language version
gofumpt -modpath=github.com/org/repo .  # Specify module path
gofumpt -version              # Print version
cat main.go | gofumpt         # Format from stdin
```

**Flags:**
- `-w` - write result to file (instead of stdout)
- `-l` - list files that differ
- `-d` - display diff (non-zero exit if any diff, since v0.8.0)
- `-extra` - enable extra rules (all or comma-separated: `group_params,clothe_returns`)
- `-lang` - language version (default: from go.mod)
- `-modpath` - module path (affects import grouping)
- `-s` - hidden, always enabled (simplification)

**Skipped automatically:** `vendor/`, `testdata/`, generated files (unless given as explicit args). Obeys `ignore` directives in go.mod (Go 1.25+).

## Default Rules (always applied)

These are the formatting rules gofumpt enforces beyond gofmt:

1. **No empty lines around function bodies** - removes leading/trailing blank lines inside functions

2. **No empty lines around a lone statement in a block** - `if err != nil {\n\n\treturn err\n}` removes the blank line

3. **No empty lines before a simple error check** - no blank line between `foo, err := bar()` and `if err != nil {`

4. **No empty lines following an assignment operator** - `foo :=\n"bar"` becomes `foo := "bar"`

5. **Composite literals use newlines consistently** - if any element is on a new line, braces go on their own lines

6. **Empty field lists use a single line** - `struct {\n}` becomes `struct{}`

7. **std imports in a separate group at the top** - standard library imports grouped first, separated from third-party

8. **Short case clauses on a single line** - `case 'a', 'b',\n\t'c':` becomes `case 'a', 'b', 'c':`

9. **Multiline top-level declarations separated by empty lines** - two adjacent multi-line funcs get a blank line between them

10. **Single var declarations not grouped** - `var (\n\tfoo = "bar"\n)` becomes `var foo = "bar"`

11. **Contiguous top-level declarations grouped together** - consecutive `var x = ...` grouped into `var (...)`

12. **Simple var-declarations use short assignments** - `var s = "str"` becomes `s := "str"`

13. **`-s` simplification always on** - `[][]int{[]int{1}}` becomes `[][]int{{1}}`

14. **Octal literals use `0o` prefix** - `0755` becomes `0o755` (Go 1.13+ modules)

15. **Non-directive comments start with whitespace** - `//Foo` becomes `// Foo` (but `//go:noinline` stays)

16. **Composite literals: no leading/trailing empty lines**

17. **Field lists: no leading/trailing empty lines**

18. **Multi-line func params get `) {` on its own line** - trailing comma added for readability

## Extra Rules (opt-in with `-extra`)

1. **Group adjacent parameters with the same type** - `func Foo(bar string, baz string)` becomes `func Foo(bar, baz string)`

2. **Clothe naked returns** - `return` in a function with named results becomes `return err` with explicit values (added in v0.9.0, moved to `-extra` in v0.9.2)

## Editor Integration

### VS Code

```json
{
  "go.useLanguageServer": true,
  "gopls": {
    "formatting.gofumpt": true
  }
}
```

### GoLand

File Watchers: Settings > Tools > File Watchers > Add Custom Template
- Program: path to `gofumpt`
- Arguments: `-w $FilePath$`
- Output: `$FilePath$`

### Neovim (lspconfig)

```lua
require('lspconfig').gopls.setup({
  settings = {
    gopls = {
      gofumpt = true
    }
  }
})
```

### Vim (vim-go)

```vim
let g:go_fmt_command="gopls"
let g:go_gopls_gofumpt=1
```

### Helix

```toml
# ~/.config/helix/languages.toml
[language-server.gopls.config]
"formatting.gofumpt" = true
```

### Zed

```json
{
  "lsp": {
    "gopls": {
      "initialization_options": {
        "gofumpt": true
      }
    }
  }
}
```

### Emacs (lsp-mode 8.0.0+)

```elisp
(setq lsp-go-use-gofumpt t)
```

### Emacs (eglot)

```elisp
(setq-default eglot-workspace-configuration
  '((:gopls . ((gofumpt . t)))))
```

### Sublime Text (ST4 with LSP)

```json
{
  "lsp_format_on_save": true,
  "clients": {
    "gopls": {
      "enabled": true,
      "initializationOptions": {
        "gofumpt": true
      }
    }
  }
}
```

## golangci-lint v2 Integration

In golangci-lint v2, gofumpt is a **formatter** (not a linter):

```yaml
# .golangci.yml
formatters:
  enable:
    - gofumpt
  settings:
    gofumpt:
      module-path: github.com/org/project
      extra-rules: true
```

Run: `golangci-lint fmt`

## Diagnostics

Insert `//gofumpt:diagnose` in any Go file and run gofumpt - it rewrites the comment with version and config info:

```go
//gofumpt:diagnose version: v0.9.2 flags: -lang=go1.25 -modpath=github.com/org/project
```

## Go API

```go
import "mvdan.cc/gofumpt/format"

formatted, err := format.Source(src, format.Options{
    LangVersion: "go1.25",
    ModulePath:  "github.com/org/project",
    Extra: format.Extra{
        GroupParams:    true,
        ClotheReturns: true,
    },
})
```

## Recent Changes

| Version | Date | Key Changes |
|---------|------|-------------|
| v0.9.2 | Oct 2025 | "Clothe naked returns" moved to `-extra` flag |
| v0.9.1 | Sep 2025 | Bugfix: comment directive detection |
| v0.9.0 | Sep 2025 | Based on Go 1.25's gofmt. New "clothe naked returns" rule. Obeys go.mod `ignore`. Speed-up via x/mod/modfile |
| v0.8.0 | Apr 2025 | Based on Go 1.24's gofmt. `-d` returns non-zero on diff |
