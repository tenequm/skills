# gofumpt Reference

Latest: **v0.12.0** (2026-09-07). Based on Go 1.27's gofmt - "This release is based on Go 1.27's gofmt, and requires Go 1.26 or later."

gofumpt is a **strict superset of gofmt** - any code formatted by gofumpt produces zero changes when processed by gofmt. It adds 19 opinionated formatting rules on top, plus 3 opt-in extra rules.

**Upgrading to v0.12.0 reformats imports.** Four fixes change output on real code, so expect a one-time diff: a std import carrying a comment is "no longer moved into the top import group, as the comment stayed behind and ended up detached at the bottom of the group"; moving a std import up "no longer leaves an empty line where it used to be"; a copyright header or package doc "no longer makes gofumpt treat a single-line first declaration as multi-line"; and an assignment whose right-hand side is split by a comment "is now left alone".

**golangci-lint lags gofumpt.** golangci-lint v2.13.2 vendors `mvdan.cc/gofumpt v0.11.0`, so `golangci-lint fmt` and a standalone v0.12.0 binary disagree on exactly the cases above. Do not use one as fixer and the other as gate.

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
gofumpt -extra=group_params,clothe_returns .  # Enable specific extra rules
gofumpt -lang=go1.27 .        # Specify language version
gofumpt -modpath=github.com/org/repo .  # Specify module path
gofumpt -version              # Print version
cat main.go | gofumpt         # Format from stdin
```

**Flags:**
- `-w` - write result to file (instead of stdout)
- `-l` - list files that differ
- `-d` - display diff (non-zero exit if any diff, since v0.8.0)
- `-extra` - enable extra rules. **Changed in v0.10.0:** "The `-extra` flag now accepts a comma-separated list of rule names to enable individual extra rules, rather than enabling all of them at once." Bare `-extra` still enables all of them; `-extra=group_params,clothe_returns,balance_calls` selects individually
- `-e` - report all errors (not just the first 10 on different lines)
- `-lang` - language version (default: from go.mod)
- `-modpath` - module path (affects import grouping)
- `-s` - hidden, always enabled (simplification). Note "the `-r` rewrite flag is removed in favor of `gofmt -r`, and the `-s` flag is hidden as it is always enabled"

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

19. **Redundant parentheses dropped** (v0.10.0) - "A new rule is introduced to drop unnecessary parentheses around expressions where the inner expression is unambiguous on its own, such as `f((3))`." Parentheses are kept where they carry meaning, such as on binary expressions, and around an expression starting with a composite literal like `(s{}.Foo())`, which needs them in an `if`/`for`/`switch` clause

## Extra Rules (opt-in with `-extra`)

1. **Group adjacent parameters with the same type** - `func Foo(bar string, baz string)` becomes `func Foo(bar, baz string)`

2. **Clothe naked returns** (`clothe_returns`) - `return` in a function with named results becomes `return err` with explicit values (added in v0.9.0, moved to `-extra` in v0.9.2)

3. **Balance multi-line calls** (`balance_calls`, v0.11.0) - matches the opening and closing parenthesis of a multi-line call in their use of newlines. Introduced as a default rule in v0.10.0 and walked back: "The multi-line function call rule introduced in v0.10.0 proved controversial, so it is now the extra rule `balance_calls`, disabled by default." It only moves the closing parenthesis to its own line when the opening parenthesis ends a line

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

### govim

```vim
call govim#config#Set("Gofumpt", 1)
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
      extra:
        group-params: true
        clothe-returns: true
        balance-calls: false
```

Run: `golangci-lint fmt`

Since golangci-lint v2.13.0 (which bundles gofumpt 0.11.0) the extra rules are selected individually - "`gofumpt`: from 0.9.2 to 0.11.0 (new options: `extra.group-params`, `extra.clothe-returns`, `extra.balance-calls`)".

**`extra-rules: true` is deprecated, and it is not a neutral shorthand.** golangci-lint marks it `# Deprecated: use `extra` instead.` and warns on every run: `` `extra-rules` is deprecated, please use `extra.group-params` instead ``. More importantly it enables *all three* rules, `balance_calls` included - in gofumpt's own code `ExtraRules` calls `Extra.Set("true")`, whose branch sets `GroupParams`, `ClotheReturns` **and** `BalanceCalls`. Since `balance_calls` is the rule gofumpt deliberately demoted as controversial and disabled by default, `extra-rules: true` silently opts you back into it. Use the `extra:` map.

## Diagnostics

Insert `//gofumpt:diagnose` in any Go file and run gofumpt - it rewrites the comment with version and config info:

```go
//gofumpt:diagnose version: v0.12.0 flags: -lang=go1.27 -modpath=github.com/org/project
```

## Go API

```go
import "mvdan.cc/gofumpt/format"

formatted, err := format.Source(src, format.Options{
    LangVersion: "go1.26",
    ModulePath:  "github.com/org/project",
    Extra: format.Extra{
        GroupParams:   true,
        ClotheReturns: true,
        BalanceCalls:  false,
    },
})
```

`Options.ExtraRules` is deprecated in favour of `Options.Extra`. To stay source-compatible across releases that add new extra rules, set them by name instead of by field - "Go API users who wish to avoid build errors in such cases can use the string API in [Extra.Set]".

## Recent Changes

| Version | Date | Key Changes |
|---------|------|-------------|
| v0.12.0 | Sep 2026 | Based on Go 1.27's gofmt; **requires Go 1.26+**. Four import/blank-line fixes: std imports with comments stay put, no orphan empty line when a std import moves up, copyright headers no longer force a blank line after the first declaration, comment-split assignments left alone |
| v0.11.0 | Jul 2026 | Multi-line call rule demoted to the `balance_calls` extra rule (disabled by default); stable single-pass output for a lone var next to a single-element var group |
| v0.10.0 | May 2026 | Based on Go 1.26's gofmt; requires Go 1.25+. **Breaking:** `-extra` takes a comma-separated rule list instead of a boolean. New default rule dropping redundant parentheses |
| v0.9.2 | Oct 2025 | "Clothe naked returns" moved to `-extra` flag |
| v0.9.1 | Sep 2025 | Bugfix: comment directive detection |
| v0.9.0 | Sep 2025 | Based on Go 1.25's gofmt. New "clothe naked returns" rule. Obeys go.mod `ignore`. Speed-up via x/mod/modfile |
| v0.8.0 | Apr 2025 | Based on Go 1.24's gofmt. `-d` returns non-zero on diff |
