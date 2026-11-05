# TypeScript 7.0 (6.0-compatible)

Strict TypeScript for React. **TS 7.0** (latest `7.0.2`, GA 2026-07-08) is the Go-native port - "a 10x faster native port of TypeScript" - and is what a plain `npm i -D typescript` installs today. Its type checker is a methodical port of 6.0, so the 6.0 defaults and deprecations below are the 7.0 rules too; 7.0 turns the 6.0 deprecations into hard errors.

## What changed in 6.0/7.0 (and why your tsconfig shrinks)

Several flags the old hand-tuned React tsconfig set manually are now **defaults**, so you delete them:

- `strict` is **on by default**.
- `noUncheckedSideEffectImports` is **on by default**.

New defaults that **break builds** if ignored:

- `types` defaults to `[]`. Ambient `@types/*` no longer leak in globally - list what you need (`"types": ["vite/client", "node"]`). `["*"]` restores the old include-everything behavior.
- Side-effect imports are checked, so `import "./styles.css"` errors (TS2882) unless something declares the module - in a Vite app that is `vite/client` in `types`.
- `module` defaults to `esnext`, and `target` to "the current stable ECMAScript version immediately preceding `esnext`" - a moving value. Pick both deliberately per project type (below).
- `rootDir` defaults to the tsconfig directory rather than being inferred from inputs - set it explicitly for non-trivial layouts.
- `lib.dom.d.ts` now includes `dom.iterable` and `dom.asynciterable` (6.0), so `"lib": ["ES2023", "DOM"]` is enough.
- 7.0 only: `libReplacement` is `false` by default and `stableTypeOrdering` is always on.

Deprecated in 6.0, **errors in 7.0**:

- `baseUrl` - use prefixed `paths` (`"@/*": ["./src/*"]`) only.
- `moduleResolution: classic` / `node` / `node10` - use `bundler` or `nodenext`.
- `esModuleInterop`, `allowSyntheticDefaultImports`, `alwaysStrict` set to `false`.
- `target: es5` (lowest is ES2015) and `downlevelIteration`.
- `--module amd|umd|systemjs|none` and `--outFile`.
- Import-assertion `assert {}` syntax - use import-attributes `with {}`.
- Legacy `module Foo {}` namespace syntax - use `namespace`.

`"ignoreDeprecations": "6.0"` silences these on 6.0 only - 7.0 removes the flags outright, so treat it as a migration window, not a fix.

## Strict tsconfig for a Vite React app

```jsonc
{
  "compilerOptions": {
    // strict, noUncheckedSideEffectImports: ON by default since 6.0
    "target": "es2023",
    "module": "preserve",
    "moduleResolution": "bundler",
    "moduleDetection": "force",
    "jsx": "react-jsx",
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "skipLibCheck": true,
    "noEmit": true,
    "types": ["vite/client"],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"]
}
```

**`bundler` vs `nodenext`.** For code a bundler consumes (a Vite app), `module: preserve` + `moduleResolution: bundler` is correct - it lets you write extensionless imports and leaves module syntax for Vite/Rolldown. For code Node runs directly (scripts, a server entry), use `module: nodenext` (which sets resolution to match) and write real `.js` extensions on relative imports.

**Solution layout.** create-vite splits this into `tsconfig.app.json` (the config above, `include: ["src"]`) and `tsconfig.node.json` (`include: ["vite.config.ts"]`, `types: ["node"]`, `module: nodenext`), both referenced from a `tsconfig.json` with `"files": []`, and builds with `tsc -b && vite build` - Vite itself never type-checks. `tsc -b` works with `noEmit` and no `composite`; set `tsBuildInfoFile` to `./node_modules/.tmp/<name>.tsbuildinfo` so incremental build info, which speeds up warm checks, stays out of the source tree.

**`exactOptionalPropertyTypes`** distinguishes "absent" from "present but `undefined`": an optional prop that may be passed `undefined` (e.g. forwarding an optional field) must be declared `prop?: T | undefined`.

**`erasableSyntaxOnly`** (since 5.8) forbids TS constructs that emit runtime code (enums, parameter properties, namespaces with values), so your `.ts` files are pure type-erasable. This is what makes **Node's native type stripping** - now stable (Node 24.12 / 25.2) - work: Node can run `.ts` directly when paired with `erasableSyntaxOnly` + `verbatimModuleSyntax`. Keep it on for portability.

## Patterns

### Component props

```tsx
type ButtonProps = React.ComponentProps<"button"> & { variant?: "primary" | "secondary"; isLoading?: boolean }

// Polymorphic "as" prop
type PolymorphicProps<E extends React.ElementType> = { as?: E } & Omit<React.ComponentProps<E>, "as">
function Text<E extends React.ElementType = "span">({ as, ...props }: PolymorphicProps<E>) {
  const Component = as || "span"
  return <Component {...props} />
}
```

### Discriminated unions over booleans

Make impossible states unrepresentable:

```tsx
type AsyncState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; error: Error }
  | { status: "success"; data: T }
```

A `switch` over `status` with a `never` default gives exhaustiveness checking.

### `satisfies` for config literals

Preserves literal types while validating shape (unlike a `Record<string, T>` annotation, which widens):

```tsx
const routes = {
  home: { path: "/" },
  about: { path: "/about" },
} satisfies Record<string, { path: string }>
routes.home // autocompletes
```

### Hook and event types

```tsx
const [user, setUser] = useState<User | null>(null)          // explicit for null init
const inputRef = useRef<HTMLInputElement>(null)               // React 19: RefObject<T | null>
const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => e.preventDefault()
```

Reducers use a discriminated-union action type; `useReducer(reducer, initial)` infers the rest.

### Generic components

```tsx
function Select<T>({ items, value, onChange, getKey, getLabel }: {
  items: T[]; value: T; onChange: (item: T) => void; getKey: (item: T) => string; getLabel: (item: T) => string
}) {
  return (
    <select value={getKey(value)} onChange={(e) => {
      const item = items.find((i) => getKey(i) === e.target.value)
      if (item) onChange(item)
    }}>
      {items.map((item) => <option key={getKey(item)} value={getKey(item)}>{getLabel(item)}</option>)}
    </select>
  )
}
```

### `import defer` (TS 5.9+)

Defers module evaluation until first property access - useful for heavy, conditionally-used modules. Namespace imports only, and it is not downleveled, so it requires `module: preserve | esnext` and a runtime/bundler that supports it:

```tsx
import defer * as heavy from "./heavy-feature.js"
// heavy.* not evaluated until first access
```

### Zod v4 validation

```tsx
import { z } from "zod"
const UserSchema = z.object({ name: z.string().min(1), email: z.email() })
type User = z.infer<typeof UserSchema>

const result = UserSchema.safeParse(Object.fromEntries(formData))
if (!result.success) {
  const flat = z.flattenError(result.error) // Zod v4 field-level errors
  return flat.fieldErrors
}
```

**`z.union` strips the losing variant's fields.** For object schemas it returns the first member that parses, and `z.object` strips unknown keys, so `z.union([Base, Extended])` hands back an `Extended` value without its extra fields - and reordering only moves the loss to the other variant. Tag the variants and use `z.discriminatedUnion("kind", [...])`, or parse with the schema you already know applies:

```tsx
const Pr = z.object({ kind: z.literal("pr"), title: z.string(), merged: z.boolean() })
const Discussion = z.object({ kind: z.literal("discussion"), title: z.string(), repo: z.string() })
const Result = z.discriminatedUnion("kind", [Pr, Discussion])   // keeps each variant's fields
```

## TypeScript 7 in practice

**No JS API in 7.0.** The `typescript@7` package exposes only `version` plus `unstable/*` subpaths - "it does not ship with an API. We expect TypeScript 7.1 to ship with a new (and different) API." Tools that `import ts from "typescript"` break on 7.0. In this stack, Biome, `@vitejs/plugin-react`, and the shadcn CLI (bundles its own TS via ts-morph) are unaffected; **typescript-eslint** (peer `typescript <6.1.0`, still true in 8.72), and Volar-based checkers for **Vue, Astro, Svelte, and MDX** still need 6.0.

**Side-by-side with 6.0** - the official alias pair keeps the 6.0 API for tools while `tsc` is 7.0:

```json
{
  "devDependencies": {
    "@typescript/native": "npm:typescript@^7.0.2",
    "typescript": "npm:@typescript/typescript6@^6.0.2"
  }
}
```

`tsc` then runs 7.0 and `tsc6` runs 6.0; `require("typescript")` resolves to the 6.0 API for typescript-eslint and friends. If a framework checker (`astro check`, `vue-tsc`) needs 6.0, keep it as the library and run 7.0 `tsc --noEmit` as a separate step for plain `.ts`.

**Migrating:** "Practically any TypeScript code that compiles cleanly with TypeScript 6.0 (with the `stableTypeOrdering` flag on, and without any `ignoreDeprecations` flag set) should compile identically in TypeScript 7.0." Get 6.0 clean under those two conditions first, then switch.

**7.0-only behavior changes:**

- `tsc file.ts` in a directory with a `tsconfig.json` errors (TS5112) unless you pass `--ignoreConfig`.
- `/// <reference no-default-lib />` is no longer respected under `skipDefaultLibCheck`.
- Template-literal inference treats Unicode code points as single characters.

**Parallelism:** `--checkers` (default 4 type-check workers), `--builders` (parallel project-reference builds), `--singleThreaded`. On small CI runners lower `--checkers`, and fix the number across environments for reproducible results.

**Nightlies** resume under the `typescript` package's `next` tag (`typescript@next`); `@typescript/native-preview` is frozen.

**TS 7.1** (beta 2026-10-20, RC expected about a month later) brings the API back with new entry points - `typescript/sync`, `typescript/async`, plus `typescript/fs` and `typescript/ast`: "TypeScript 7.1 ships a new API that allows building powerful tools". That is what typescript-eslint and other API consumers will move to. It also adds **content mappers** (`contentMappers` in tsconfig, run with `tsc --runExternalCode`), the plugin point for checking `.vue`/`.astro`/`.svelte`/MDX on 7.x; an `es2026` target; import attributes in ambient module declarations; and stricter checks on distributive type parameters (new errors like "'B' is only assignable to the non-distributed 'A'"). Until 7.1 is GA, keep the 6.0 alias pair above for API consumers.

## Resources

- TS 7.0 announcement: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/ - TS 7.1 beta: https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/
- TS 6.0 announcement: https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/
- Source and issues: https://github.com/microsoft/TypeScript - Release notes: https://www.typescriptlang.org/docs/handbook/release-notes/
