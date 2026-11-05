# Biome

Fast, unified linting, formatting, and import organization for JS/TS/JSX/CSS/GraphQL in a single binary. Biome **2.6** (latest `2.6.5`) does type-aware linting without the TypeScript compiler, GritQL and (developer-preview) JavaScript plugins for custom rules, and domain-based rule grouping. 2.6 also formats and lints **Markdown, SCSS, and YAML**. Zero config by default, ~97% Prettier compatibility.

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

**Before 2.6.3, `!**/dir` also matched ancestor directories.** If the project itself lived under a directory with that name - e.g. an agent worktree at `<repo>/.claude/worktrees/x/` with `"!**/.claude"` in its config - every file was excluded and Biome checked 0 files (`No files were processed`). 2.6.3 stopped applying exclusions to directories above the project root. Root-anchoring exclusions for the project's own top-level folders (`"!.claude"`, `"!dist"`) is still the clearer habit; keep `**/` for names that genuinely recur at depth. To see what a config actually resolves to, run `biome inspect config` (2.6), which follows `extends` and overrides.

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
    "rules": { "preset": "recommended" },
    "domains": { "react": "recommended" }
  },
  "javascript": { "formatter": { "quoteStyle": "double" } },
  "assist": { "enabled": true, "actions": { "source": { "organizeImports": "on" } } }
}
```

Biome 2.5 **deprecated `linter.rules.recommended`** in favor of `linter.rules.preset` (`"recommended"`, `"all"`, or `"none"`); the boolean still works but emits an info-level deprecation diagnostic - run `biome migrate --write` to convert. Groups take their own `preset` too (`"style": { "preset": "none" }`), as does `assist.actions`. The `domains` values (`"recommended"`/`"all"`/`"none"`) are unaffected.

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
pnpm biome ci --reporter=concise .                       # short one-line-per-diagnostic output
```

`--reporter=concise` (Biome 2.5) prints one `file:line:col: rule: message` line per diagnostic - the recommended reporter when an AI coding agent reads the output, since it saves tokens versus the default rich format.

`biome check` and `biome ci` exit 0 when only warnings remain, so a green run can still carry diagnostics (an unsafe fix such as removing an unused import is reported, not applied). Add the global `--error-on-warnings` flag where warnings should fail the pipeline: `pnpm biome ci --error-on-warnings .`.

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

Domains group lint rules by technology - enable what your stack uses. Levels: `"recommended"` (the domain's recommended stable rules), `"all"` (every stable rule in the domain), `"none"`. **Domains never enable nursery rules** - not even at `"all"` - so a nursery rule listed under a domain must be turned on individually under `linter.rules.nursery`.

```json
{ "linter": { "domains": { "react": "recommended", "test": "recommended", "types": "all" } } }
```

Common domains: `react` (auto-detected at `react >= 16`), `next`, `solid`, `vue`, `test` (jest/vitest/mocha/ava), `playwright`, `drizzle`, `tailwind` (auto-detected at `tailwindcss >= 4.0.0`; all its rules are nursery), `project` (cross-file: `noImportCycles`, `noUnresolvedImports`), `types` (type inference). The `project` and `types` domains trigger a file scan with small overhead.

## Type-aware linting

Biome has its own Rust type-inference engine - no `typescript` dependency needed. The headline promise rules are still **nursery**, so the `types` domain alone does not turn them on - enable them explicitly:

```json
{
  "linter": {
    "domains": { "types": "all" },
    "rules": {
      "nursery": {
        "noFloatingPromises": "error",
        "noMisusedPromises": "error",
        "useAwaitThenable": "error"
      }
    }
  }
}
```

| Rule | Group | Catches |
|------|-------|---------|
| `noFloatingPromises` | nursery | unhandled promises (missing await/return/void) |
| `noMisusedPromises` | nursery | promises in conditionals or array callbacks |
| `useAwaitThenable` | nursery | awaiting non-thenables |
| `noUnnecessaryConditions` | stable (`types` domain) | always-true/false conditions |
| `useStrictBooleanExpressions` | nursery (2.5.15) | ambiguous truthiness like `if (count)` on `number \| undefined` |
| `noUnsafeTypeAssertion` | nursery | `as` assertions (const assertions allowed) |

```ts
async function loadData() { fetch("/api") }        // ERROR: floating promise
async function loadData() { void fetch("/api") }   // OK: explicit fire-and-forget
```

### React Compiler interaction

If you use the React Compiler, `useExhaustiveDependencies` can't tell the compiler is handling memoization, so most compiler users turn it off:

```json
{ "linter": { "rules": { "correctness": { "useExhaustiveDependencies": "off" } } } }
```

The nursery rule `useReactCompiler` (2.5.8+, React domain) reports React Compiler lint-mode diagnostics - code the compiler will bail out on - without ESLint. Enable it with `"nursery": { "useReactCompiler": "error" }`.

### Tailwind v4 CSS

Point Biome at your Tailwind entry with the top-level `tailwind.stylesheet` option (2.6). It turns on `css.parser.tailwindDirectives`, so `@theme`, `@utility`, and `@apply` parse instead of erroring, and makes the Tailwind rules read your own `@theme` - without it they "recognize only Tailwind CSS's default configuration". `tailwind.mergeFunctions`, `variantFunctions`, and `attributes` tune where class strings are detected.

```json
{ "tailwind": { "stylesheet": "./src/styles.css" } }
```

The `tailwind` domain's nursery rules lint class strings in JSX - enable them individually:

```json
{ "linter": { "rules": { "nursery": {
  "noTailwindRawColors": "error",
  "useTailwindStaticClassStrings": "error",
  "noTailwindRestyledComponents": "warn",
  "useTailwindSortedClasses": "warn",
  "useTailwindShorthandClasses": "warn",
  "noTailwindArbitraryValue": "warn"
} } } }
```

`noTailwindRawColors` enforces this skill's semantic-token rule, flagging palette classes like `bg-pink-500` in favor of tokens like `bg-primary`; its `allowBlackAndWhite` option defaults to `true`, so `text-white`/`bg-black` pass unless you set it to `false`. Two 2.6 rules back up the rest of the styling rules: `useTailwindStaticClassStrings` flags dynamically built class strings (the "never assemble class names" rule), and `noTailwindRestyledComponents` reports call-site utilities that change a component's color, typography, spacing, shape, effects, or motion - add a variant instead. `useTailwindShorthandClasses` suggests `size-4` for `w-4 h-4`; `noTailwindArbitraryValue` now allows arbitrary modifiers (`bg-black/[0.5]`) and takes `allowedCategories`/`allowedClasses`. The sorting rule is now `useTailwindSortedClasses` (renamed from `useSortedClasses`, with Tailwind v4 ordering) - `biome migrate --write` renames it in your config.

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

Target languages: JavaScript (default), CSS, and JSON. Biome 2.6 also adds **JavaScript plugins** as a developer preview, distributable as packages with a `biome-manifest.json`.

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
biome lint --only=types .        # run just type-aware rules (nursery ones report at info - won't fail CI)
biome lint --enforce-assist .    # fail CI when assist actions remain unapplied
biome check --watch .            # re-run on file changes (2.5; read-only, no --write/--fix)
biome explain noFloatingPromises # explain a rule
biome migrate --write            # after a version bump
biome upgrade                    # 2.5: self-upgrade standalone (Homebrew/binary) installs
biome inspect config             # 2.6: print the resolved config (extends, overrides)
biome migrate stylelint --write  # 2.6: import a Stylelint config
```

Standalone install without npm: `curl -fsSL https://biomejs.dev/install | bash` (2.6). 2.5.15 also restricts the daemon's Unix socket to the current user (`0600`, in a private `biome-daemon` cache dir) - another reason to stay on the latest patch. Biome 2.5 also adds `formatter.delimiterSpacing` (pads `[ 1, 2 ]` / `{ a }` / `( x )` - an accessibility aid for dyslexia; behavior varies per language) and can now format/lint `.svg` files.

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
- Domains: https://biomejs.dev/linter/domains/ - Migrate: https://biomejs.dev/installation/migrate-from-other-tools/ - v2.6: https://biomejs.dev/blog/biome-v2-6
