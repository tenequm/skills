# Build Optimization

Detailed guide for Vite 7 build configuration, chunk splitting strategies, performance tuning, and bundle analysis.

## Build Defaults

Vite 7 defaults:

| Option | Default | Description |
|--------|---------|-------------|
| `build.target` | `'baseline-widely-available'` | Chrome 107+, Edge 107+, Firefox 104+, Safari 16+ |
| `build.outDir` | `'dist'` | Output directory relative to project root |
| `build.assetsDir` | `'assets'` | Directory for generated assets inside outDir |
| `build.assetsInlineLimit` | `4096` (4 KiB) | Files smaller are inlined as base64 |
| `build.cssCodeSplit` | `true` | CSS stays with async chunks |
| `build.sourcemap` | `false` | Set `'hidden'` for production error tracking |
| `build.minify` | `'esbuild'` | `'esbuild'` for client, `false` for SSR |
| `build.chunkSizeWarningLimit` | `500` | Warning threshold in KiB |

## Chunk Splitting Strategies

### Strategy 1: Named Vendor Chunks

Best for: projects with stable dependencies that benefit from long-term caching.

```ts
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'router': ['@tanstack/react-router', '@tanstack/react-start'],
          'query': ['@tanstack/react-query'],
          'ui': ['class-variance-authority', 'clsx', 'tailwind-merge'],
        },
      },
    },
  },
})
```

Pros: predictable chunk names, great cache hit rates for unchanged deps.
Cons: manual maintenance when adding new large dependencies.

### Strategy 2: Dynamic Splitting Function

Best for: large projects with many dependencies where manual tracking is impractical.

```ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return

          // React ecosystem
          if (id.includes('react-dom') || id.includes('react/')) {
            return 'react-vendor'
          }

          // TanStack
          if (id.includes('@tanstack/')) {
            return 'tanstack'
          }

          // UI libraries
          if (
            id.includes('class-variance-authority') ||
            id.includes('tailwind-merge') ||
            id.includes('lucide-react') ||
            id.includes('@radix-ui/')
          ) {
            return 'ui'
          }

          // Everything else from node_modules
          return 'vendor'
        },
      },
    },
  },
})
```

Pros: automatic categorization, handles new deps.
Cons: less predictable chunk composition.

### Strategy 3: Route-Based Splitting

TanStack Router with `autoCodeSplitting: true` automatically code-splits per route. Combine with vendor chunks for best results:

```ts
import { defineConfig } from 'vite'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  plugins: [
    tanstackRouter({ autoCodeSplitting: true }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
        },
      },
    },
  },
})
```

Each route file becomes its own chunk. Shared code between routes is automatically extracted into common chunks.

## CSS Optimization

### CSS Code Splitting (Default)

CSS imported in async chunks is kept with those chunks. No extra configuration needed.

### Single CSS File

For projects where a single stylesheet is preferable:

```ts
build: {
  cssCodeSplit: false,
}
```

### CSS Minification

Default uses esbuild. Lightning CSS is an alternative:

```ts
build: {
  cssMinify: 'lightningcss',
}
```

```bash
pnpm add -D lightningcss
```

## Asset Handling

### Inline Threshold

Control when assets are inlined vs referenced:

```ts
build: {
  assetsInlineLimit: 0,      // never inline (all assets as files)
  assetsInlineLimit: 4096,   // default: 4 KiB
  assetsInlineLimit: 8192,   // 8 KiB (inline more small assets)
}
```

### Custom Inline Logic

```ts
build: {
  assetsInlineLimit: (filePath, content) => {
    // Always inline SVG icons
    if (filePath.endsWith('.svg') && content.byteLength < 10240) {
      return true
    }
    // Never inline fonts
    if (/\.(woff2?|ttf|eot)$/.test(filePath)) {
      return false
    }
    // Default behavior for everything else
    return undefined
  },
}
```

## Source Maps

| Value | Use Case |
|-------|----------|
| `false` | Production default, no maps |
| `true` | Separate `.map` files with reference comments |
| `'hidden'` | Separate `.map` files, no reference in bundle (upload to error tracker) |
| `'inline'` | Embedded in bundle (debugging only, increases size) |

Recommended production setup:

```ts
build: {
  sourcemap: 'hidden',
}
```

Upload `.map` files to your error tracking service (Sentry, etc.) and exclude them from deployment.

## Bundle Analysis

### rollup-plugin-visualizer

```bash
pnpm add -D rollup-plugin-visualizer
```

```ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    visualizer({
      filename: 'stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
      template: 'treemap',  // 'treemap' | 'sunburst' | 'network'
    }),
  ],
})
```

Run `pnpm vite build` and inspect `stats.html` for:
- Large dependencies that could be lazy-loaded
- Duplicate packages (different versions of same library)
- Unused code not being tree-shaken

### Compressed Size Reporting

Vite reports gzip sizes by default. Disable for faster builds on large projects:

```ts
build: {
  reportCompressedSize: false,
}
```

### Chunk Size Warnings

Adjust the warning threshold:

```ts
build: {
  chunkSizeWarningLimit: 1000,  // 1 MB threshold
}
```

## Performance Tuning

### Dependency Pre-Bundling

Vite pre-bundles dependencies on first dev server start. Force re-optimization:

```bash
pnpm vite --force
```

Include/exclude specific dependencies:

```ts
optimizeDeps: {
  include: ['some-cjs-package'],   // force pre-bundle
  exclude: ['some-esm-package'],   // skip pre-bundling
}
```

### Build Target Optimization

Lower targets increase bundle size due to syntax transforms:

```ts
// Minimum for modern features
build: { target: 'es2020' }

// Default (recommended) - smallest bundles
build: { target: 'baseline-widely-available' }

// Maximum optimization, latest syntax
build: { target: 'esnext' }
```

### Minification

esbuild (default) is 20-40x faster than Terser with only 1-2% larger output:

```ts
build: {
  minify: 'esbuild',   // default, fastest
  minify: 'terser',     // smaller output, much slower
  minify: false,         // debugging
}
```

### Module Preload

Vite injects a polyfill for `<link rel="modulepreload">`. Disable if targeting only modern browsers:

```ts
build: {
  modulePreload: { polyfill: false },
}
```

## Tree Shaking

Vite's Rollup-based bundler (or Rolldown with `rolldown-vite`) tree-shakes unused exports. Ensure effectiveness:

1. **Use ESM imports** - named imports enable tree shaking:
   ```ts
   import { Button } from '@/components/ui/button'  // tree-shakeable
   import * as UI from '@/components/ui'              // NOT tree-shakeable
   ```

2. **Mark packages as side-effect-free** in `package.json`:
   ```json
   { "sideEffects": false }
   ```

3. **Avoid barrel files** that re-export everything:
   ```ts
   // Bad: src/components/index.ts that exports every component
   // Good: import directly from the component file
   ```

4. **Check with visualizer** - look for large unused portions of libraries.

## Load Error Handling

Handle chunk loading failures after new deployments:

```ts
// src/main.tsx
window.addEventListener('vite:preloadError', (event) => {
  event.preventDefault()
  // Reload the page to get fresh asset references
  window.location.reload()
})
```

Set `Cache-Control: no-cache` on `index.html` to prevent stale references.

## rolldown-vite Performance

With `rolldown-vite` (Rust-based bundler), additional optimizations are available:

- **Unified pipeline** - single bundler for dev and prod (no esbuild + Rollup split)
- **Parallel processing** - Rust-native multithreading for transforms
- **Lower memory** - up to 100x reduction on large projects
- **Oxc minifier** - replaces esbuild for minification

Real-world results:
- GitLab: 2.5 min to 40s, 100x memory reduction
- Excalidraw: 22.9s to 1.4s (16x)
- PLAID Inc: 80s to 5s (16x)
- Appwrite: 12 min to 3 min, 4x memory reduction

No config changes needed - the performance gains come from the bundler itself.

## Complete Production Config Example

```ts
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { cloudflare } from '@cloudflare/vite-plugin'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig(({ mode }) => ({
  plugins: [
    tanstackStart(),
    tailwindcss(),
    react({
      babel: {
        plugins: [
          ['babel-plugin-react-compiler', {}],
        ],
      },
    }),
    cloudflare(),
    mode === 'analyze' && visualizer({
      filename: 'stats.html',
      open: true,
      gzipSize: true,
    }),
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': new URL('./src', import.meta.url).pathname,
    },
  },
  build: {
    sourcemap: 'hidden',
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'tanstack': [
            '@tanstack/react-query',
            '@tanstack/react-router',
          ],
        },
      },
    },
  },
  server: {
    warmup: {
      clientFiles: [
        './src/routes/__root.tsx',
        './src/components/*.tsx',
      ],
    },
  },
}))
```

Run bundle analysis: `pnpm vite build --mode analyze`
