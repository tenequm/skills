---
name: typescript-dev
description: "Build modern TypeScript frontend apps with Vite 8, React 19, Tailwind CSS v4, shadcn/ui, Biome, and Vitest. Covers the full stack - build tooling and dev server (Vite/Rolldown), type-safe React 19 components and hooks, strict TypeScript 6.0 config, utility-first styling with shadcn/ui, linting and formatting with Biome, and testing with Vitest. Use this whenever setting up or working in a TypeScript React project - configuring Vite, writing components, typing props and hooks, wiring the React Compiler, styling with Tailwind or shadcn, theming, fixing the dev server or HMR, splitting bundles, writing tests, or setting up lint/format/CI. Triggers on vite, rolldown, react, react 19, tsx, typescript, tsconfig, react compiler, tailwind, shadcn, cva, dark mode, biome, lint, format, vitest, hmr, dev server, build optimization, vite config, frontend setup."
metadata:
  version: "0.1.0"
  upstream: "vite@8.0.16, @vitejs/plugin-react@6.0.2, react@19.2.7, typescript@6.0.3, tailwindcss@4.3.0, @biomejs/biome@2.4.16, vitest@4.1.8, babel-plugin-react-compiler@1.0.0, class-variance-authority@0.7.1"
---

# TypeScript Frontend Development

One coherent stack for building type-safe React apps: **Vite 8** (build + dev server, Rolldown-powered), **React 19.2** with the React Compiler, **TypeScript 6.0** (strict), **Tailwind CSS v4.3 + shadcn/ui** for styling, **Biome 2.4** for linting and formatting, and **Vitest 4** for testing. The pieces are designed to fit together - this skill covers how they wire up and the sharp edges that span more than one of them.

The body below is the cross-cutting layer: the rules that bite when these tools meet, plus one working end-to-end setup. Each tool also has a deep-dive reference - read the one you need:

- **[references/vite.md](references/vite.md)** - Vite 8 config, dev server, proxy, HMR, Rolldown, code splitting, build optimization, deployment.
- **[references/react.md](references/react.md)** - React 19 patterns: Actions, `use()`, Activity, `useEffectEvent`, document metadata, and the React Compiler.
- **[references/typescript.md](references/typescript.md)** - Strict TypeScript 6.0 config and patterns: tsconfig defaults, generics, utility types, `import defer`, tsgo.
- **[references/tailwind.md](references/tailwind.md)** - Tailwind CSS v4 CSS-first config, OKLCH theming, dark mode, v4.3 utilities.
- **[references/shadcn.md](references/shadcn.md)** - shadcn/ui CLI, component authoring with CVA + `data-slot`, registries, Radix vs Base UI.
- **[references/biome.md](references/biome.md)** - Biome config, `biome check`, domains, type-aware linting, GritQL, ESLint/Prettier migration.
- **[references/vitest.md](references/vitest.md)** - Vitest config, Testing Library, jsdom/happy-dom, coverage, browser mode, projects.

## Version targets

| Tool | Version | Note |
|------|---------|------|
| Vite | 8.0.16 | Rolldown is the single default bundler |
| @vitejs/plugin-react | 6.0.2 | v6 removed the inline `babel` option |
| React / react-dom | 19.2.7 | React Compiler is stable (1.0) |
| babel-plugin-react-compiler | 1.0.0 | pin with `--save-exact` |
| TypeScript | 6.0.3 | last JS-based TS; bridge to tsgo/TS 7 |
| Tailwind CSS | 4.3.0 | CSS-first config, no JS config file |
| shadcn/ui CLI | 4.10.0 | `create` is an alias of `init` |
| Biome | 2.4.16 | single binary for lint + format + imports |
| Vitest | 4.1.8 | Vite-native test runner; reuses vite.config |

## Cross-cutting critical rules

These are the rules that fail in confusing ways precisely because they sit at the seam between two tools. The single-tool details live in the references.

### Vite plugin order: framework plugins first, `react()` last

When a framework plugin (TanStack Router/Start, etc.) generates routes or transforms code, it must run before `@vitejs/plugin-react` so React's Fast Refresh transform sees the final output. Wrong order causes route-generation failures and broken HMR.

```ts
plugins: [
  tanstackStart(),   // or tanstackRouter() for SPA - framework first
  tailwindcss(),
  react(),           // React plugin last among framework plugins
]
```

### React Compiler replaces manual memoization - and changes how you wire Vite

React Compiler 1.0 auto-memoizes components, computations, and callbacks at build time. Write plain components; do not reach for `useMemo`/`useCallback`/`memo`. The catch lives at the Vite seam: **`@vitejs/plugin-react` v6 removed the inline `babel` option**, so the old `react({ babel: { plugins: [...] } })` wiring no longer works. The compiler now runs through a separate Babel plugin:

```ts
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'

plugins: [react(), babel({ presets: [reactCompilerPreset()] })]
```

Install: `pnpm add -D @rolldown/plugin-babel @babel/core babel-plugin-react-compiler @types/babel__core`.

This also ripples into Biome: `useExhaustiveDependencies` can't tell the compiler is handling deps for you, so most compiler users turn it off (see [biome.md](references/biome.md)).

### Tailwind v4 is CSS-first - there is no `tailwind.config.js`

Tailwind v4 configures everything in CSS via `@theme`, `@utility`, `@plugin`, `@source`. Never create or look for `tailwind.config.js`/`.ts`. The Vite integration is the `@tailwindcss/vite` plugin (no PostCSS config either). If you find a `tailwind.config.js` in a v4 project, it is leftover - delete it and migrate the values into CSS. Full details in [tailwind.md](references/tailwind.md).

### Style with semantic tokens, never raw palette or dynamic class names

```tsx
<div className="bg-primary text-primary-foreground">   // respects theme + dark mode
<div className="bg-blue-500 text-white">               // breaks theming - avoid
```

And never assemble class names from fragments (`bg-${color}-500`) - Tailwind's scanner only sees complete literal strings, so dynamic names silently produce no CSS. Use a lookup map of full class strings.

### TypeScript 6.0 changed the defaults - lean on them, don't fight them

TS 6.0 bakes in much of what used to be manual: `strict` and `noUncheckedSideEffectImports` are now **on by default**, so drop them from a fresh tsconfig. But two new defaults will break builds if you ignore them: `types` now defaults to `[]` (add `"types": ["node"]` if you use Node globals) and `module`/`target` shifted (`module` defaults to `esnext`, not `nodenext`). `baseUrl` is deprecated - use prefixed `paths` instead. See [typescript.md](references/typescript.md) for the full 6.0 tsconfig and migration notes.

### One Biome command, and `files.includes` is the only include key

Run `biome check` (or `biome ci`) - it formats, lints, and organizes imports in a single pass; never split into separate `lint`+`format` calls. And in Biome 2.x the only file-selection key is `files.includes` (with the `s`); `files.ignore`/`files.include`/`files.exclude` do not exist and throw `Found an unknown key`. Exclude with negation: `"includes": ["**", "!**/routeTree.gen.ts"]`. More in [biome.md](references/biome.md).

## End-to-end setup

A minimal but complete React + TypeScript + Tailwind + Biome project. Swap the framework plugin for your router/SSR choice (see [vite.md](references/vite.md) for TanStack and Cloudflare variants).

### vite.config.ts

```ts
import { defineConfig } from 'vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
    react(),
    babel({ presets: [reactCompilerPreset()] }),
  ],
  resolve: {
    alias: { '@': new URL('./src', import.meta.url).pathname },
  },
})
```

`import.meta.url` is the ESM-correct way to resolve paths - there is no `__dirname` in an ESM config, and Vite configs are ESM-only.

### tsconfig.json (TypeScript 6.0)

```jsonc
{
  "compilerOptions": {
    // strict + noUncheckedSideEffectImports are ON by default in 6.0 - omitted on purpose
    "target": "es2023",
    "module": "preserve",
    "moduleResolution": "bundler",
    "moduleDetection": "force",
    "jsx": "react-jsx",
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "erasableSyntaxOnly": true,
    "skipLibCheck": true,
    "types": [],
    "paths": { "@/*": ["./src/*"] }
  }
}
```

`module: preserve` + `moduleResolution: bundler` is the right pairing for a Vite-bundled app; use `nodenext` instead only for Node-executed code. `types: []` keeps ambient `@types/*` from leaking in globally - add `["node"]` (or others) explicitly when needed.

### biome.json

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

### src/styles.css

```css
@import "tailwindcss";

:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --radius: 0.5rem;
}
.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
}
```

The `@import "tailwindcss";` line is load-bearing: the `@tailwindcss/vite` plugin alone produces no styles without it - a missing import is the classic "Tailwind renders nothing" footgun. Use `@theme inline` (not plain `@theme`) for tokens that reference CSS variables, so they track dark-mode changes.

### A component, the way the whole stack wants it

Plain function, `ref` as a regular prop (no `forwardRef`), native element props via `React.ComponentProps`, variants via CVA, `data-slot` for styling hooks, and no manual memoization - the compiler handles it.

```tsx
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        outline: "border border-input bg-background hover:bg-accent",
        ghost: "hover:bg-accent hover:text-accent-foreground",
      },
      size: { default: "h-9 px-4 py-2", sm: "h-8 px-3", lg: "h-10 px-8" },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
)

function Button({
  className,
  variant,
  size,
  ref,
  ...props
}: React.ComponentProps<"button"> & VariantProps<typeof buttonVariants>) {
  return (
    <button
      ref={ref}
      data-slot="button"
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
}
```

Note the `cn()` order: defaults first, consumer `className` last, so tailwind-merge's last-wins resolution lets callers override.

## Best practices

1. **Let the compiler optimize.** Write plain components and computations; reserve `useMemo`/`useCallback` for the rare case where you need a value to be a stable effect dependency.
2. **Model state as discriminated unions, not loose booleans** (`{ status: "loading" } | { status: "error"; error }`) so impossible states are unrepresentable.
3. **Extend native props with `React.ComponentProps<"el">`** instead of re-declaring HTML attributes by hand.
4. **Use `use()` over `useContext()`** - it works after early returns and inside conditionals.
5. **Semantic color tokens only**, and always pair `bg-*` with the matching `text-*-foreground`.
6. **`biome check --write`** is your one local command; `biome ci` in pipelines.
7. **Rolldown is the default bundler in Vite 8** - no opt-in needed; split stable vendor code with Rolldown's `codeSplitting` (see [vite.md](references/vite.md)).
8. **Pin exact versions for tooling that rewrites code** (`babel-plugin-react-compiler`, `@biomejs/biome`) to avoid surprise diffs between releases.
9. **Keep secrets off the client** - only `VITE_`-prefixed env vars reach browser code via `import.meta.env`.
10. **Test through `vite.config.ts`** - Vitest reuses your build config, so tests see the same aliases and transforms; `vitest run` in CI, `jsdom` for component tests.

## Resources

- Vite: https://vite.dev/guide/ - Vite 8 blog: https://vite.dev/blog/announcing-vite8
- React 19.2: https://react.dev/blog/2025/10/01/react-19-2 - Compiler: https://react.dev/learn/react-compiler
- TypeScript 6.0: https://devblogs.microsoft.com/typescript/announcing-typescript-6-0/
- Tailwind CSS: https://tailwindcss.com/docs - shadcn/ui: https://ui.shadcn.com/docs
- Biome: https://biomejs.dev/
