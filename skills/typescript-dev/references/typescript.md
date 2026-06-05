# TypeScript 6.0

Strict TypeScript for React. **TS 6.0** (latest `6.0.3`) is a deliberate bridge release: "the last release based on the current JavaScript codebase," pre-staging the breaking changes that the Go-native rewrite (tsgo / TS 7.0) will enforce. Target 6.0 today - it is stable and shippable, and most of its new defaults bake in settings you used to set by hand.

## What changed in 6.0 (and why your tsconfig shrinks)

Several flags the old hand-tuned React tsconfig set manually are now **defaults**, so you delete them:

- `strict` is **on by default**.
- `noUncheckedSideEffectImports` is **on by default**.

Two new defaults will **break builds** if ignored:

- `types` now defaults to `[]`. Ambient `@types/*` no longer leak in globally - add what you need explicitly (`"types": ["node"]`).
- `module` defaults to `esnext` and `target` to a floating current-year ES version (currently `es2025`); they no longer default to `nodenext`. Pick deliberately per project type (below).
- `rootDir` now defaults to the tsconfig directory rather than being inferred from inputs - set it explicitly for non-trivial layouts.

Deprecations and removals to migrate off:

- `baseUrl` is **deprecated** - use prefixed `paths` (`"@/*": ["./src/*"]`) only.
- `moduleResolution: classic` is **removed**; `node`/`node10` is deprecated. Use `bundler` or `nodenext`.
- `esModuleInterop` and `allowSyntheticDefaultImports` can no longer be set to `false` (safe interop is always on).
- `target: es5` is deprecated (lowest target is now ES2015); `downlevelIteration` errors.
- `--module amd|umd|systemjs|none` and `--outFile` are removed.
- Import-assertion `assert {}` syntax errors - use import-attributes `with {}`.
- Legacy `module Foo {}` namespace syntax is a hard error - use `namespace`.

You can silence 6.0 deprecation errors temporarily with `"ignoreDeprecations": "6.0"`, but TS 7.0 removes the flags outright - treat it as a migration window, not a fix.

## Strict tsconfig for a Vite React app

```jsonc
{
  "compilerOptions": {
    // strict, noUncheckedSideEffectImports: ON by default in 6.0
    "target": "es2023",
    "module": "preserve",
    "moduleResolution": "bundler",
    "moduleDetection": "force",
    "jsx": "react-jsx",
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "erasableSyntaxOnly": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "skipLibCheck": true,
    "types": [],
    "paths": { "@/*": ["./src/*"] }
  }
}
```

**`bundler` vs `nodenext`.** For code a bundler consumes (a Vite app), `module: preserve` + `moduleResolution: bundler` is correct - it lets you write extensionless imports and leaves module syntax for Vite/Rolldown. For code Node runs directly (scripts, a server entry), use `module: nodenext` (which sets resolution to match) and write real `.js` extensions on relative imports.

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

## tsgo / TypeScript 7

The native (Go) compiler ships as a preview: `npm i -D @typescript/native-preview`, run `npx tsgo` as a `tsc` drop-in (~10x faster type-checking). It is **not GA** - type-checking is near-complete but the language service and public API are still in progress. Don't target it for production builds yet; do try it for fast CI type-checks. TS 6.0's deprecations exist precisely to smooth this migration.

## Resources

- TS 6.0 announcement: https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/
- tsgo / TS 7: https://github.com/microsoft/typescript-go
- Release notes: https://www.typescriptlang.org/docs/handbook/release-notes/
