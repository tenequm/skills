# Vite 8

Build tooling and dev server. Vite 8 (stable, latest `8.1.2`) ships **Rolldown** - a Rust-based bundler from the Vite team - as its single default bundler, replacing both esbuild and Rollup. It is ESM-only and requires Node.js 20.19+ / 22.12+.

## Vite 8 essentials

- **Rolldown is the default**, no opt-in. "Vite 8 ships with Rolldown as its single, unified, Rust-based bundler." Build times drop dramatically vs the old esbuild+Rollup split.
- **ESM-only config.** `vite.config.ts` must use `import`/`export`; `require()` is not supported in config files.
- **Default browser target** is `'baseline-widely-available'`, which in Vite 8 resolves to `['chrome111', 'edge111', 'firefox114', 'safari16.4']` (bumped from Vite 7's 107/107/104/16). Override with `build.target: 'es2022'` or an explicit list.
- **Default minifiers changed:** JavaScript is minified by **Oxc** (`build.minify` default `'oxc'`), CSS by **Lightning CSS** (`build.cssMinify` default `'lightningcss'`). `build.minify: 'esbuild'` still works but is deprecated and requires installing `esbuild` yourself.
- **Install grew ~15 MB** vs Vite 7 (Lightning CSS + the Rolldown binary are now regular dependencies).

## New in Vite 8.1

- **Wasm ESM integration (stable)** - import a `.wasm` file and call its exports directly: `import { add } from './add.wasm'`. No plugin needed.
- **Experimental Bundled Dev Mode** (`experimental.bundledDev: true` or `--experimental-bundle`) - serves bundled files in dev instead of the classic unbundled server. Aimed at huge apps that suffer from module count (~15x faster startup in a 10k-component test); may not work with all third-party plugins yet.
- **Experimental Chunk Import Map** (`build.chunkImportMap`) - uses an import map so a changed chunk's hash doesn't cascade new hashes to every importer, improving long-term cache hit rates. Does not compose with `experimental.renderBuiltUrl`.
- **Lightning CSS as the future default** - Vite is working toward making Lightning CSS the default CSS transformer in the next major. Opt in early with `css: { transformer: 'lightningcss' }`.
- `import.meta.glob` gained a `caseSensitive` option; `html.additionalAssetSources` lets asset discovery see custom HTML elements/attributes.

## Configuration

### SPA with TanStack Router

```ts
import { defineConfig } from 'vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tanstackRouter({ autoCodeSplitting: true }), // framework plugin first
    tailwindcss(),
    react(),
    babel({ presets: [reactCompilerPreset()] }),
  ],
  resolve: { alias: { '@': new URL('./src', import.meta.url).pathname } },
})
```

### Full-stack with TanStack Start + Cloudflare

```ts
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { cloudflare } from '@cloudflare/vite-plugin'
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    cloudflare(),
    tanstackStart(),     // includes the router plugin internally - do NOT add both
    tailwindcss(),
    react(),
    babel({ presets: [reactCompilerPreset()] }),
  ],
})
```

`tanstackStart({ spa: { enabled: true } })` runs SPA mode; `tanstackStart({ prerender: { enabled: true, crawlLinks: true } })` enables SSG.

### Path aliases

Two options. Manual alias (works everywhere):

```ts
resolve: { alias: { '@': new URL('./src', import.meta.url).pathname } }
```

Or **new in Vite 8**, let Vite read tsconfig `paths` directly so you don't mirror them:

```ts
resolve: { tsconfigPaths: true }
```

Caveat: the native resolver does **not** follow tsconfig project references. In a solution-style setup (`tsconfig.json` -> `tsconfig.app.json` via `references`) where the `paths` live in the referenced file, `tsconfigPaths: true` silently fails to resolve `@/*` - fall back to an explicit `resolve.alias` there.

### Environment variables

Files: `.env`, `.env.local`, `.env.[mode]`, `.env.[mode].local`. Only `VITE_`-prefixed vars are exposed to client code via `import.meta.env`; everything else stays server-side. Built-in constants: `import.meta.env.MODE`, `.DEV`, `.PROD`, `.SSR`, `.BASE_URL`. Type them in `src/vite-env.d.ts`:

```ts
interface ImportMetaEnv { readonly VITE_API_URL: string }
interface ImportMeta { readonly env: ImportMetaEnv }
```

On Cloudflare, keep two channels straight: `VITE_`-prefixed `.env` values are statically injected into the **client** bundle at build time, while `.dev.vars` / Worker bindings are **runtime** server env passed to the handler - they are not available to client code, and vice versa.

## Plugin ecosystem

- **`@vitejs/plugin-react`** (v6) - Fast Refresh + JSX transform. v6 dropped Babel as a dependency (React Refresh runs through Oxc) and **removed the inline `babel` option**; run Babel-based transforms like the React Compiler through `@rolldown/plugin-babel` instead. Place last among framework plugins. v6 requires Vite 8 (use v5 if you must stay on Vite 7).
- **`@tailwindcss/vite`** - native Tailwind v4 integration, no PostCSS config. API unchanged across v4.x.
- **`@tanstack/router-plugin/vite`** - file-based routes; `tanstackRouter({ autoCodeSplitting: true })`. Must precede `react()`.
- **`@tanstack/react-start/plugin/vite`** - full-stack TanStack Start; bundles the router plugin (don't add both).
- **`@cloudflare/vite-plugin`** - runs Worker code in `workerd` during dev via the Environment API, matching production.

## Dev server

### Proxy

```ts
server: {
  proxy: {
    '/api': { target: 'http://localhost:8787', changeOrigin: true, rewrite: (p) => p.replace(/^\/api/, '') },
    '/ws': { target: 'ws://localhost:8787', ws: true },
  },
}
```

Proxy and most `server.*` changes are **not** hot-reloaded - restart the dev server after editing them.

### allowedHosts (tunnels and custom domains)

By default Vite rejects requests whose Host header it doesn't recognize, which surfaces as `Blocked request. This host (...) is not allowed.` when you hit the dev server through ngrok, a custom domain, or a fallback port. Add the host:

```ts
server: { allowedHosts: ['.ngrok-free.app', 'dev.example.com'] }
```

Setting it to `true` disables the check entirely and is a DNS-rebinding risk - scope it to known hosts.

### forwardConsole (new in Vite 8)

`server.forwardConsole` forwards browser runtime console output to the Vite server terminal. It defaults to auto - **on when an AI coding agent is detected**, off otherwise - which is handy when an agent is driving the build and can't see the browser console.

### HMR troubleshooting

| Symptom | Fix |
|---------|-----|
| Full reload instead of HMR | Ensure `@vitejs/plugin-react` is loaded and a file exports a single component |
| HMR not connecting behind a proxy | Set `server.ws.clientPort` (e.g. `443`) |
| CSS not updating | Confirm `@tailwindcss/vite` is in plugins and `@import "tailwindcss";` is in your CSS entry |
| Stale chunk after a build | Hard-refresh (`Cmd/Ctrl+Shift+R`) to bust the cached bundle |

The WebSocket knobs (`protocol`/`host`/`port`/`path`/`clientPort`/`timeout`/`server`) moved from `server.hmr.*` to `server.ws.*`. The old `server.hmr.*` keys are deprecated but auto-synced, so existing configs keep working; write new ones under `server.ws`.

### File warmup

```ts
server: { warmup: { clientFiles: ['./src/routes/__root.tsx', './src/components/*.tsx'] } }
```

### `cloudflare:workers` import errors

`Failed to resolve import "cloudflare:workers"` (or `node:*` / `buffer` "externalized for browser compatibility") means Worker-only code is reaching the client graph - common with `createServerFn` + `import { env } from "cloudflare:workers"`, or web3/Solana SDKs that pull Node built-ins. Keep server-only imports in server modules; if a dependency forces it, externalize via `build.rolldownOptions.external`. Note `vite build` validates **all** emitted chunks (even behind dynamic import), so lazy-loading a heavy server chunk alone won't exclude it from the Worker build.

## Build optimization

### Code splitting (Rolldown)

The object form of `output.manualChunks` is **removed** in Vite 8 and the function form is deprecated - both will break or warn. Use Rolldown's `codeSplitting` via `build.rolldownOptions` (note: `build.rollupOptions` is now a deprecated alias of `build.rolldownOptions`):

```ts
build: {
  rolldownOptions: {
    output: {
      // Rolldown's advanced chunking; see https://rolldown.rs/in-depth/manual-code-splitting
      advancedChunks: {
        groups: [
          { name: 'react-vendor', test: /node_modules\/(react|react-dom)\// },
          { name: 'tanstack', test: /node_modules\/@tanstack\// },
        ],
      },
    },
  },
}
```

Route-based splitting still comes for free with `tanstackRouter({ autoCodeSplitting: true })` - each route becomes its own chunk and shared code is extracted automatically.

### Build defaults

| Option | Default | Note |
|--------|---------|------|
| `build.target` | `baseline-widely-available` | chrome111/edge111/firefox114/safari16.4 |
| `build.minify` | `'oxc'` (client), `false` (SSR) | Oxc minifier, 30-90x faster than terser |
| `build.cssMinify` | `'lightningcss'` | set `'esbuild'` to revert (must install esbuild) |
| `build.sourcemap` | `false` | use `'hidden'` for error tracking without exposing source |
| `build.assetsInlineLimit` | `4096` | bytes below which assets inline as base64 |
| `build.cssCodeSplit` | `true` | CSS stays with its async chunk |
| `build.chunkSizeWarningLimit` | `500` | kB; large web3 deps routinely trip this (informational) |

### Bundle analysis

```ts
import { visualizer } from 'rollup-plugin-visualizer'
// in plugins, gated to a mode:
mode === 'analyze' && visualizer({ filename: 'stats.html', open: true, gzipSize: true })
```

Vite 8 also ships **Vite DevTools for Rolldown** (`@vitejs/devtools-rolldown`) for analyzing production builds. Run analysis with `pnpm vite build --mode analyze`.

### Tree shaking

Rolldown tree-shakes unused exports. Help it: use named ESM imports (`import { Button }`, not `import * as UI`), mark side-effect-free packages with `"sideEffects": false`, and avoid barrel files that re-export everything.

### Chunk load errors after deploy

```ts
window.addEventListener('vite:preloadError', (e) => { e.preventDefault(); window.location.reload() })
```

Serve `index.html` with `Cache-Control: no-cache` so clients don't hold stale asset references.

## Migrating Vite 7 to Vite 8

Rolldown is built in, so remove any `rolldown-vite` aliasing. If you're coming straight from stock Vite 7, the team recommends an intermediate hop to isolate Rolldown-specific issues: first alias `vite` to `rolldown-vite` on Vite 7, fix any fallout, then upgrade to Vite 8 and undo the alias.

```jsonc
// Vite 7 intermediate step, then drop this for "vite": "^8.0.0"
{ "devDependencies": { "vite": "npm:rolldown-vite@7.2.2" } }
```

`rolldown-vite` lives at `github.com/vitejs/rolldown-vite` (now **archived** - it was a technical preview, not an unrelated `nicepkg` repo). Other Vite 8 migration notes: `optimizeDeps.esbuildOptions` -> `optimizeDeps.rolldownOptions`; the `esbuild` config option -> `oxc`; `worker.rollupOptions` -> `worker.rolldownOptions`; consistent CJS interop and dropped format-sniffing resolution may surface edge cases (see https://vite.dev/guide/migration).

## Environment API

The Environment API (formalized in Vite 6, now in **Release Candidate**) gives each target - browser, Node, edge - its own module graph, plugin pipeline, and build config. Most apps never touch it directly: `@cloudflare/vite-plugin` and `@tanstack/react-start` configure environments for you. Frameworks coordinate multi-environment builds through the `buildApp` builder hook. Direct use is for framework/runtime authors.

## Deployment

### Cloudflare Workers (via TanStack Start)

```jsonc
// wrangler.jsonc
{
  "name": "my-app",
  "compatibility_date": "2025-01-01",
  "compatibility_flags": ["nodejs_compat"],
  "main": "./dist/server/index.js",
  "assets": { "directory": "./dist/client" }
}
```

```bash
pnpm vite build && pnpm wrangler deploy
```

### Static SPA / SSG

`vite build` produces `dist/` for any static host. For prerendering, enable `tanstackStart({ prerender: { enabled: true, crawlLinks: true } })`.

## Resources

- Guide: https://vite.dev/guide/ - Vite 8 blog: https://vite.dev/blog/announcing-vite8
- Migration: https://vite.dev/guide/migration - Build options: https://vite.dev/config/build-options
- Rolldown: https://rolldown.rs - Cloudflare plugin: https://developers.cloudflare.com/workers/vite-plugin/
