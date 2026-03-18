---
name: biome
description: Lint and format frontend code with Biome 2.4. Covers type-aware linting, GritQL custom rules, domains, import organizer, and migration from ESLint/Prettier. Use when configuring linting rules, formatting code, writing custom lint rules, or setting up CI checks. Triggers on biome, biome config, biome lint, biome format, biome check, biome ci, gritql, migrate from eslint, migrate from prettier, import sorting, code formatting, lint rules, type-aware linting, noFloatingPromises.
metadata:
  version: "0.2.0"
---

# Biome

Fast, unified linting, formatting, and import organization for JavaScript, TypeScript, JSX, CSS, and GraphQL. Biome 2.4 provides type-aware linting without the TypeScript compiler, GritQL plugins for custom rules, and domain-based rule grouping. Single binary, zero config by default, 97% Prettier compatibility.

## Critical Rules

### `files.ignore` DOES NOT EXIST - use `files.includes` with negation

Biome 2.x only supports `files.includes` (with an `s`). There is NO `files.ignore`, NO `files.include` (without `s`), NO `files.exclude`. Using any of these will throw `Found an unknown key` errors.

The only valid keys under `files` are: `includes`, `maxSize`, `ignoreUnknown`, `experimentalScannerIgnores`.

To exclude files (generated code, vendored files, etc.), use negation patterns in `files.includes`:

```json
{
  "files": {
    "includes": ["**", "!**/routeTree.gen.ts", "!**/generated/**"]
  }
}
```

Do NOT use `overrides` with `linter/formatter/assists: { enabled: false }` to skip generated files - that approach is fragile (easy to miss a subsystem like assists/import organizer) and unnecessarily complex. Just exclude via `files.includes`.

### Always use `biome check`, not separate lint + format

`biome check` runs formatter, linter, and import organizer in one pass. Never call `biome lint` and `biome format` separately in CI - use `biome check` (or `biome ci` for CI mode).

### biome.json lives at project root

Every project needs one `biome.json` at the root. Monorepo packages use nested configs with `"extends": "//"` to inherit from root. Never use relative paths like `"extends": ["../../biome.json"]`.

### Use `--write` to apply fixes, not `--fix`

```bash
biome check --write .            # Apply safe fixes
biome check --write --unsafe .   # Apply all fixes (review changes)
```

### Pin exact versions and migrate after upgrades

```bash
pnpm add --save-dev --save-exact @biomejs/biome@latest
pnpm biome migrate --write
```

## Quick Start

```bash
pnpm add --save-dev --save-exact @biomejs/biome
pnpm biome init    # Creates default biome.json with recommended rules
```

### IDE Setup

**VS Code** - Install `biomejs.biome` extension:

```json
{
  "editor.defaultFormatter": "biomejs.biome",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports.biome": "explicit"
  }
}
```

**Zed** - Biome extension available natively. The `inline_config` feature (v2.4) lets editors override rules without affecting `biome.json`:

```json
{
  "formatter": { "language_server": { "name": "biome" } },
  "lsp": {
    "biome": {
      "settings": {
        "inline_config": {
          "linter": { "rules": { "suspicious": { "noConsole": "off" } } }
        }
      }
    }
  }
}
```

### CI Integration

```bash
pnpm biome ci .                                  # No writes, non-zero exit on errors
pnpm biome ci --reporter=default --reporter=github .  # GitHub Actions annotations
```

## Configuration (biome.json)

### Recommended config for React/TypeScript projects

```json
{
  "$schema": "./node_modules/@biomejs/biome/configuration_schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "files": {
    "includes": [
      "src/**/*.ts", "src/**/*.tsx",
      "tests/**/*.ts", "**/*.config.ts", "**/*.json",
      "!**/generated", "!**/components/ui"
    ]
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 120
  },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true },
    "domains": { "react": "recommended" }
  },
  "javascript": {
    "formatter": { "quoteStyle": "double" }
  },
  "assist": {
    "enabled": true,
    "actions": {
      "source": { "organizeImports": "on" }
    }
  }
}
```

### Formatter options

Key options: `indentStyle` (`"space"`/`"tab"`), `indentWidth`, `lineWidth`, `lineEnding` (`"lf"`/`"crlf"`), `trailingNewline`. JS-specific: `quoteStyle`, `trailingCommas`, `semicolons`, `arrowParentheses`, `bracketSpacing`.

### Linter rule configuration

Rules use severity levels `"error"`, `"warn"`, `"info"`, or `"off"`. Some accept options:

```json
{
  "linter": {
    "rules": {
      "recommended": true,
      "style": {
        "noRestrictedGlobals": {
          "level": "error",
          "options": {
            "deniedGlobals": {
              "Buffer": "Use Uint8Array for browser compatibility."
            }
          }
        },
        "useComponentExportOnlyModules": "off"
      }
    }
  }
}
```

### Import organizer

The import organizer (Biome Assist) merges duplicates, sorts by distance, and supports custom grouping:

```json
{
  "assist": {
    "enabled": true,
    "actions": {
      "source": {
        "organizeImports": {
          "level": "on",
          "options": {
            "groups": [
              { "source": "builtin" },
              { "source": "external" },
              { "source": "internal", "match": "@company/*" },
              { "source": "relative" }
            ]
          }
        }
      }
    }
  }
}
```

### Per-subsystem includes

Each subsystem (`linter`, `formatter`, `assist`) has its own `includes` for fine-grained scoping. Applied after `files.includes` - can only narrow, not widen.

```json
{
  "files": {
    "includes": ["**", "!**/dist"]
  },
  "linter": {
    "includes": ["**", "!**/components/ui"]
  },
  "formatter": {
    "includes": ["**", "!**/components/ui"]
  }
}
```

This lints and formats everything except `dist/` and `components/ui`, while assists (import organizer) still run on `components/ui`.

### Overrides

Overrides apply different settings to specific file patterns. Use for per-file rule tweaks (e.g., relaxing rules for vendored/shadcn components). The field is `includes` (with `s`).

```json
{
  "overrides": [
    {
      "includes": ["**/components/ui/**"],
      "linter": {
        "rules": {
          "suspicious": { "noDocumentCookie": "off" },
          "style": { "useComponentExportOnlyModules": "off" }
        }
      }
    },
    {
      "includes": ["**/*.test.ts"],
      "linter": {
        "rules": {
          "suspicious": { "noConsole": "off" }
        }
      }
    }
  ]
}
```

### Monorepo configuration

Root `biome.json` holds shared config. Package configs inherit with `"extends": "//"`:

```json
{
  "$schema": "../../node_modules/@biomejs/biome/configuration_schema.json",
  "extends": "//"
}
```

Override specific rules per package by adding a `linter.rules` section alongside `"extends": "//"`.

### Configuration file discovery (v2.4)

Search order: `biome.json` -> `biome.jsonc` -> `.biome.json` -> `.biome.jsonc` -> platform config home (`~/.config/biome` on Linux, `~/Library/Application Support/biome` on macOS).

## Domains

Domains group lint rules by technology. Enable only what your stack needs:

```json
{
  "linter": {
    "domains": {
      "react": "recommended",
      "next": "recommended",
      "test": "recommended",
      "types": "all"
    }
  }
}
```

| Domain | Purpose | Auto-detected |
|--------|---------|---------------|
| `react` | React hooks, JSX patterns | `react` dependency |
| `next` | Next.js-specific rules | `next >= 14.0.0` |
| `solid` | Solid.js rules | `solid-js` dependency |
| `test` | Testing best practices (any framework) | - |
| `playwright` | Playwright test rules | `@playwright/test` |
| `project` | Cross-file analysis (noImportCycles, noUnresolvedImports) | - |
| `types` | Type inference rules (noFloatingPromises, noMisusedPromises) | - |

**Activation levels:** `"recommended"` (stable rules only), `"all"` (includes nursery), `"none"` (disable).

The `project` domain enables rules needing the module graph. The `types` domain (v2.4) enables rules requiring type inference. Both trigger a file scan that adds a small overhead.

## Type-Aware Linting

Biome 2.0 introduced type-aware linting without the TypeScript compiler. Biome has its own type inference engine in Rust - no `typescript` dependency needed.

### How it works

Enable the `types` domain to activate file scanning and type inference. Performance impact is minimal compared to typescript-eslint because inference runs natively.

### Key rules

| Rule | What it catches |
|------|----------------|
| `noFloatingPromises` | Unhandled promises (missing await/return/void) |
| `noMisusedPromises` | Promises in conditionals, array callbacks |
| `useAwaitThenable` | Awaiting non-thenable values |
| `noUnnecessaryConditions` | Conditions that are always true/false |
| `useRegexpExec` | `string.match()` where `regexp.exec()` is better |
| `useFind` | `array.filter()[0]` instead of `array.find()` |
| `useArraySortCompare` | `Array.sort()` without compare function |

### noFloatingPromises

The most impactful type-aware rule. Detects unhandled promises:

```ts
// ERROR: floating promise
async function loadData() {
  fetch("/api/data");
}

// VALID: awaited
async function loadData() {
  await fetch("/api/data");
}

// VALID: explicitly voided (fire-and-forget)
async function loadData() {
  void fetch("/api/data");
}
```

Detects ~75% of cases compared to typescript-eslint, improving each release.

### Limitations vs typescript-eslint

- Complex generic type inference may miss some cases
- Not a full type checker - handles common patterns, not every edge case
- Rules still in nursery - expect improvements with each release
- Major performance advantage: fraction of tsc-based linting time

## GritQL Custom Rules

GritQL is a declarative pattern-matching language for custom lint rules. Create `.grit` files and register them as plugins.

```json
{ "plugins": ["./lint-rules/no-object-assign.grit"] }
```

### Examples

**Ban `Object.assign`:**

```grit
`$fn($args)` where {
    $fn <: `Object.assign`,
    register_diagnostic(
        span = $fn,
        message = "Prefer object spread instead of `Object.assign()`"
    )
}
```

**CSS - enforce color classes:**

```grit
language css;
`$selector { $props }` where {
    $props <: contains `color: $color` as $rule,
    not $selector <: r"\.color-.*",
    register_diagnostic(
        span = $rule,
        message = "Don't set explicit colors. Use `.color-*` classes instead."
    )
}
```

### Plugin API

`register_diagnostic()` arguments:
- `severity` - `"hint"`, `"info"`, `"warn"`, `"error"` (default: `"error"`)
- `message` (required) - diagnostic message
- `span` (required) - syntax node to highlight

Supported target languages: JavaScript (default), CSS, JSON (v2.4). Profile with `biome lint --profile-rules .`.

## Suppression Patterns

### Single-line

```ts
// biome-ignore lint/suspicious/noConsole: needed for debugging
console.log("debug info");
```

### File-level

```ts
// biome-ignore-all lint/suspicious/noConsole: logger module
```

### Range

```ts
// biome-ignore-start lint/style/useConst: legacy code
let x = 1;
let y = 2;
// biome-ignore-end lint/style/useConst
const a = 4; // this line IS checked
```

`biome-ignore-end` is optional - omit to suppress until end of file. Biome requires explanation text after the colon.

## Migration

### From ESLint

```bash
pnpm biome migrate eslint --write
pnpm biome migrate eslint --write --include-inspired  # Include non-identical rules
```

Supports legacy and flat configs, `extends` resolution, plugins (typescript-eslint, react, jsx-a11y, unicorn), `.eslintignore`.

### From Prettier

```bash
pnpm biome migrate prettier --write
```

Maps `tabWidth` -> `indentWidth`, `useTabs` -> `indentStyle`, `singleQuote` -> `quoteStyle`, `trailingComma` -> `trailingCommas`.

### From ESLint + Prettier combo

```bash
pnpm biome migrate eslint --write
pnpm biome migrate prettier --write
pnpm remove eslint prettier eslint-config-prettier eslint-plugin-prettier \
  @typescript-eslint/parser @typescript-eslint/eslint-plugin
rm .eslintrc* .prettierrc* .eslintignore .prettierignore
```

Enable VCS integration since ESLint respects gitignore by default:

```json
{ "vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true } }
```

## CLI Reference

### biome check (primary command)

```bash
biome check .                    # Check all files
biome check --write .            # Apply safe fixes
biome check --write --unsafe .   # Apply all fixes
biome check --changed .          # Only VCS-changed files
biome check --staged .           # Only staged files
```

### biome ci (CI mode)

```bash
biome ci .                                           # No writes, exit code on errors
biome ci --reporter=github .                         # GitHub annotations
biome ci --reporter=sarif --reporter-file=report.sarif .  # SARIF output
```

### biome lint

```bash
biome lint --only=suspicious/noDebugger .    # Single rule
biome lint --skip=project .                  # Skip domain
biome lint --only=types .                    # Only type-aware rules
biome lint --error-on-warnings .             # Warnings become errors
```

### Other commands

```bash
biome format --write .                       # Format only
biome search '`console.$method($args)`' .    # GritQL pattern search
biome rage                                   # Debug info for bug reports
biome explain noFloatingPromises             # Explain a rule
```

## Best Practices

1. **Use `biome check` as your single command** - combines format, lint, and import organization
2. **Start with `recommended: true`** - disable individual rules as needed
3. **Enable relevant domains** - `react`, `next`, `test`, `types` based on your stack
4. **Enable VCS integration** - respects `.gitignore`, enables `--changed`/`--staged`
5. **Use `biome ci` in pipelines** - never writes files, clear exit codes
6. **Pin exact versions** - avoid surprise rule changes between releases
7. **Run `biome migrate --write` after every upgrade**
8. **Use `--staged` in pre-commit hooks**: `biome check --staged --write --no-errors-on-unmatched .`
9. **Profile slow rules** with `biome lint --profile-rules` (v2.4)
10. **Use GritQL plugins** for project-specific patterns instead of disabling rules globally

## Gotchas

These are real mistakes that have caused broken configs, dirty working trees, and wasted debugging time. Read before writing any Biome config.

1. **`files.ignore`, `files.include`, `files.exclude` do not exist.** Only `files.includes` (with `s`). Biome will throw `Found an unknown key` for anything else. See the first critical rule above.

2. **`organizeImports` is NOT a top-level config key.** In Biome 2.x it moved under `assist.actions.source.organizeImports`. Using it at the top level is a config error.

3. **`overrides` that disable `linter` + `formatter` still run `assist`.** If you use overrides to skip a generated file, the import organizer (an assist action) will still rewrite it. This silently dirties your working tree. Use `files.includes` negation to fully exclude a file instead.

4. **`overrides` field is `includes` (with `s`), not `include`.** Same naming as `files.includes`.

5. **`biome check --write` runs formatter + linter + assists in one pass.** Any of these three can modify files. If a generated file keeps getting dirtied after `check --write`, check which subsystem is touching it - it's often the import organizer (assist), not the formatter or linter.

6. **`--fix` does not exist.** The flag is `--write`. `--fix` will silently do nothing or error.

## Resources

- **Biome Docs**: https://biomejs.dev/
- **Biome GitHub**: https://github.com/biomejs/biome
- **GritQL Docs**: https://docs.grit.io/
- **Biome v2 Blog**: https://biomejs.dev/blog/biome-v2/
- **Biome v2.4 Blog**: https://biomejs.dev/blog/biome-v2-4/
- **Migration Guide**: https://biomejs.dev/guides/migrate-eslint-prettier/
- **Rules Reference**: https://biomejs.dev/linter/javascript/rules/
- **Domains**: https://biomejs.dev/linter/domains/
- **Plugins**: https://biomejs.dev/linter/plugins/

For detailed lint rules by category with code examples, see [rules-reference.md](references/rules-reference.md).
