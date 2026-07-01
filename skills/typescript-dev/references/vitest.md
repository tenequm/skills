# Vitest

The Vite-native test runner. Vitest **4** (latest `4.1.9`) reuses your `vite.config.ts` - same plugins, resolve aliases, and transforms - so tests see the app exactly as the bundler builds it. It requires **Vite >= 6.0.0 and Node >= 20.0.0**, and works with the Vite 8 / Rolldown stack (the old "Vitest 3.2+ for Vite 7" floor is superseded; use Vitest 4.x today).

## Configuration

Vitest reads `vite.config.ts` by default - put the `test` block there and import `defineConfig` from `vitest/config` (not `vite`) to get typed test options. A separate `vitest.config.ts` is only needed when test settings must diverge from the build config.

```ts
// vite.config.ts
/// <reference types="vitest/config" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,                    // optional: skip importing test/expect
    environment: 'jsdom',             // 'jsdom' | 'happy-dom' | 'node' | 'edge-runtime'
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    css: true,                        // process CSS imports per Vite rules
    coverage: {
      provider: 'v8',                 // default; or 'istanbul'
      include: ['src/**/*.{ts,tsx}'], // v4: required to report uncovered files
      reporter: ['text', 'html', 'lcov'],
    },
  },
})
```

```ts
// src/test/setup.ts
import '@testing-library/jest-dom/vitest'   // registers DOM matchers with Vitest's expect
```

If `globals: true`, add `"types": ["vitest/globals"]` to tsconfig `compilerOptions`. **jsdom vs happy-dom:** jsdom is the safer default for React component tests; happy-dom is faster but covers a smaller API surface.

Install set:

```bash
pnpm add -D vitest @vitejs/plugin-react jsdom \
  @testing-library/react @testing-library/dom @testing-library/jest-dom \
  @testing-library/user-event @vitest/coverage-v8
```

`@testing-library/react` (16.x) added React 19 support in 16.1 and requires the separate `@testing-library/dom` peer.

## Component test

```tsx
// src/components/Counter.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test } from 'vitest'   // omit if globals: true
import { Counter } from './Counter'

test('increments on click', async () => {
  const user = userEvent.setup()
  render(<Counter />)
  expect(screen.getByText('Count: 0')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: /increment/i }))
  expect(screen.getByText('Count: 1')).toBeInTheDocument()
})
```

## CLI

```bash
vitest                  # watch mode (default)
vitest run              # single run - use in CI
vitest --ui             # @vitest/ui dashboard
vitest run --coverage   # enable coverage
vitest --typecheck      # type-level test mode
vitest --project unit   # filter to a project (repeatable)
```

## Coverage

The default provider is **v8** (`@vitest/coverage-v8`); `istanbul` is the alternative. Since Vitest 3.2 the v8 provider uses AST-based remapping, so accuracy matches istanbul. **v4 breaking change:** `coverage.all` and `coverage.extensions` were removed - the default now reports only covered files, so set `coverage.include` to surface uncovered ones. When Vitest detects an AI coding agent, the `text` reporter auto-trims output (`skipFull: true` + a summary) to save tokens.

## Browser Mode

Runs tests in a real browser. In Vitest 4 the provider is an **imported factory object**, not a string, and the old `@vitest/browser` package is gone:

```ts
import { playwright } from '@vitest/browser-playwright'

test: {
  browser: {
    enabled: true,
    provider: playwright(),
    instances: [{ browser: 'chromium' }],   // at least one required
    headless: true,
  },
}
```

Set it up with `npx vitest init browser`. Providers: `@vitest/browser-playwright` (recommended, supports parallelism), `@vitest/browser-webdriverio`, and `@vitest/browser-preview` (local only - **not** for CI, it simulates events rather than driving Chrome DevTools Protocol). Render with `vitest-browser-react`; import `page`/`userEvent` from `vitest/browser`. Browser tests are not an "environment" - mix them with Node tests via `test.projects` (below).

## Projects (not workspace)

`vitest.workspace.ts` + `defineWorkspace` is **deprecated since 3.2**. Use the `test.projects` field in the root config:

```ts
export default defineConfig({
  test: {
    projects: [
      'packages/*',
      { extends: true, test: { name: 'unit', environment: 'jsdom', include: ['**/*.unit.test.ts'] } },
      { test: { name: 'node', environment: 'node', include: ['**/*.node.test.ts'] } },
    ],
  },
})
```

`extends: true` inherits root plugins/options (default is no inheritance). Use `defineProject` for standalone project files - root-only keys (`coverage`, `reporters`) error inside a project. Root-level `coverage`/`reporters` stay global.

## Notes

- **Vitest 5** is in beta: benchmarking API rewrite, `*.sequential` removed (use `concurrent: false`), stricter browser locators, no parent-dir config lookup. Stay on 4.x for production.
- Migrating from v3: `vite-node` was replaced by Vite's Module Runner; tinypool was removed (`maxThreads`/`maxForks` -> `maxWorkers`); the `workspace` -> `projects` rename is finalized.

## Resources

- Guide: https://vitest.dev/guide/ - Config: https://vitest.dev/config/
- Browser Mode: https://vitest.dev/guide/browser/ - Migration: https://vitest.dev/guide/migration
