# Biome

Fast, unified linting, formatting, and import organization for JS/TS/JSX/CSS/GraphQL in a single binary. Biome **2.4** (latest `2.4.16`) does type-aware linting without the TypeScript compiler, GritQL plugins for custom rules, and domain-based rule grouping. Zero config by default, ~97% Prettier compatibility.

## Critical rules

### `files.includes` is the only file key

Biome 2.x supports only `files.includes` (with the `s`). There is **no** `files.ignore`, `files.include`, or `files.exclude` - any of them throws `Found an unknown key`. The valid `files` keys are `includes`, `maxSize`, `ignoreUnknown`. Exclude with negation patterns:

```json
{ "files": { "includes": ["**", "!**/routeTree.gen.ts", "!**/generated/**"] } }
```

For paths the scanner must skip entirely (even for assists), use the `!!` force-ignore prefix - it replaces the deprecated `experimentalScannerIgnores`:

```json
{ "files": { "includes": ["**", "!!**/legacy-vendor/**"] } }
```

### One command: `biome check`

`biome check` runs formatter + linter + import organizer in one pass. Never split into separate `biome lint` and `biome format` in CI - use `biome check` (or `biome ci` for CI mode).

```bash
biome check --write .            # apply safe fixes
biome check --write --unsafe .   # include unsafe fixes (review the diff)
```

Removing unused imports/variables is classified **unsafe** (an external caller might reference the symbol), so plain `--write` reports but doesn't delete them - use `--write --unsafe` or remove by hand. Prefer `--write` over the `--fix` alias for consistency.

### Pin versions, migrate after upgrades

```bash
pnpm add --save-dev --save-exact @biomejs/biome@latest
pnpm biome migrate --write
```

The `$schema` is version-pinned; after bumping the binary, the CLI errors with `The configuration schema version does not match the CLI version` until you run `biome migrate --write`. Do it as part of the upgrade.

### `biome.json` at the project root

One config at the root; monorepo packages use `"extends": "//"` to inherit. Never reference it with a relative path like `"../../biome.json"`.

## Quick start

```bash
pnpm add --save-dev --save-exact @biomejs/biome
pnpm biome init
```

### Recommended config (React/TypeScript)

```json
{
  "$schema": "./node_modules/@biomejs/biome/configuration_schema.json",
  "vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true },
  "files": { "includes": ["**", "!**/components/ui", "!**/routeTree.gen.ts"] },
  "formatter": { "enabled": true, "indentStyle": "space", "lineWidth": 100 },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true },
    "domains": { "react": "recommended" }
  },
  "javascript": { "formatter": { "quoteStyle": "double" } },
  "assist": { "enabled": true, "actions": { "source": { "organizeImports": "on" } } }
}
```

### IDE setup

VS Code - install `biomejs.biome`:

```json
{
  "editor.defaultFormatter": "biomejs.biome",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.biome": "explicit",
    "source.organizeImports.biome": "explicit"
  }
}
```

Zed uses the Biome extension natively. Note the spelling: Zed's inline-config key is `inline_config` (snake_case); the VS Code extension uses `inlineConfig` (camelCase).

### CI

```bash
pnpm biome ci .                                          # no writes, non-zero exit on errors
pnpm biome ci --reporter=github .                        # GitHub Actions annotations
```

## Configuration details

### Import organizer

The organizer (a Biome Assist action, not a lint rule) merges duplicates, sorts by distance, and supports custom grouping:

```json
{
  "assist": { "actions": { "source": { "organizeImports": {
    "level": "on",
    "options": { "groups": [
      { "source": "builtin" }, { "source": "external" },
      { "source": "internal", "match": "@company/*" }, { "source": "relative" }
    ] }
  } } } }
}
```

### Per-subsystem includes and overrides

Each subsystem (`linter`, `formatter`, `assist`) has its own `includes`, applied after `files.includes` (can only narrow). `overrides` apply different settings to file patterns - the field is `includes` (with `s`):

```json
{
  "overrides": [
    { "includes": ["**/components/ui/**"], "linter": { "rules": { "style": { "useComponentExportOnlyModules": "off" } } } },
    { "includes": ["**/*.test.ts"], "linter": { "rules": { "suspicious": { "noConsole": "off" } } } }
  ]
}
```

### Monorepo

Root holds shared config; packages inherit with `"extends": "//"` and add their own `linter.rules` as needed.

## Domains

Domains group lint rules by technology - enable what your stack uses. Levels: `"recommended"` (stable only), `"all"` (includes nursery), `"none"`.

```json
{ "linter": { "domains": { "react": "recommended", "test": "recommended", "types": "all" } } }
```

Common domains: `react` (auto-detected at `react >= 16`), `next`, `solid`, `vue`, `test` (jest/vitest/mocha/ava), `playwright`, `drizzle`, `project` (cross-file: `noImportCycles`, `noUnresolvedImports`), `types` (type inference: `noFloatingPromises`, `noMisusedPromises`). The `project` and `types` domains trigger a file scan with small overhead.

## Type-aware linting

Biome has its own Rust type-inference engine - no `typescript` dependency needed. Enable the `types` domain.

| Rule | Catches |
|------|---------|
| `noFloatingPromises` | unhandled promises (missing await/return/void) |
| `noMisusedPromises` | promises in conditionals or array callbacks |
| `useAwaitThenable` | awaiting non-thenables |
| `noUnnecessaryConditions` | always-true/false conditions |

```ts
async function loadData() { fetch("/api") }        // ERROR: floating promise
async function loadData() { void fetch("/api") }   // OK: explicit fire-and-forget
```

### React Compiler interaction

If you use the React Compiler, `useExhaustiveDependencies` can't tell the compiler is handling memoization, so most compiler users turn it off:

```json
{ "linter": { "rules": { "correctness": { "useExhaustiveDependencies": "off" } } } }
```

### Tailwind v4 CSS

To lint CSS that uses Tailwind at-rules, enable `css.parser.tailwindDirectives` so Biome parses `@theme`, `@utility`, and `@apply` instead of erroring on them.

## GritQL custom rules

Declarative pattern-matching for project-specific rules. Register `.grit` files as plugins:

```json
{ "plugins": ["./lint-rules/no-object-assign.grit"] }
```

```grit
`$fn($args)` where {
  $fn <: `Object.assign`,
  register_diagnostic(span = $fn, message = "Prefer object spread over Object.assign()")
}
```

Target languages: JavaScript (default), CSS, and JSON.

## Suppression

```ts
// biome-ignore lint/suspicious/noConsole: needed for debugging
console.log("debug")
// biome-ignore-all lint/suspicious/noConsole: logger module      (file-level)
// biome-ignore-start lint/style/useConst: legacy ... biome-ignore-end  (range)
```

Biome requires explanation text after the colon.

## Migration from ESLint/Prettier

```bash
pnpm biome migrate eslint --write     # legacy + flat configs, plugin mapping, .eslintignore
pnpm biome migrate prettier --write   # maps tabWidth/useTabs/singleQuote/trailingComma
```

After removing ESLint (which respected `.gitignore`), enable VCS integration so Biome ignores the same files:

```json
{ "vcs": { "enabled": true, "clientKind": "git", "useIgnoreFile": true } }
```

## CLI reference

```bash
biome check --write .            # primary command
biome check --changed .          # only VCS-changed files
biome check --staged .           # only staged (good for pre-commit)
biome lint --only=types .        # run just type-aware rules
biome lint --enforce-assist .    # fail CI when assist actions remain unapplied
biome explain noFloatingPromises # explain a rule
biome migrate --write            # after a version bump
```

## Gotchas

1. **Only `files.includes` exists** - not `ignore`/`include`/`exclude`.
2. **`organizeImports` is under `assist.actions.source`**, not a top-level key.
3. **`overrides` disabling linter+formatter still run assists** - the import organizer will still rewrite a "skipped" file, silently dirtying your tree. Use `files.includes` negation to fully exclude.
4. **`package.json` reformatting loop:** Biome's default JSON formatter uses tabs; pnpm writes 2-space `package.json`, so each install/check fight. Either exclude it (`"!**/package.json"`) or override JSON to spaces:

```json
{ "overrides": [{ "includes": ["**/package.json"], "json": { "formatter": { "indentStyle": "space", "indentWidth": 2 } } }] }
```

## Resources

- Docs: https://biomejs.dev/ - Config reference: https://biomejs.dev/reference/configuration/
- Domains: https://biomejs.dev/linter/domains/ - Migrate: https://biomejs.dev/guides/migrate-eslint-prettier/
