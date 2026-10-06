# Vitest

The Vite-native test runner. Vitest **5** (latest `5.0.3`, released 2026-09-03) reuses your `vite.config.ts` - same plugins, resolve aliases, and transforms - so tests see the app exactly as the bundler builds it. It requires **Vite >= 6.4.0 and Node.js >= 22.12.0**, and `vite` is now a **required peer dependency** (install it explicitly - Yarn PnP and strict installs no longer get it transitively).

> **Security:** Vitest 4.1.9 and below are affected by GHSA-p63j-vcc4-9vmv (critical - Browser Mode provider commands bypass the file-access gate, fixed in 4.1.10) and GHSA-82fw-gwwq-j7x9 (`@vitest/mocker` redirect-mock path traversal, fixed in 4.1.11 / 5.0.0). If you must stay on v4, pin `vitest@4.1.11` and every `@vitest/*` package to the same version.

## Configuration

Vitest reads `vite.config.ts` by default - put the `test` block there and import `defineConfig` from `vitest/config` (not `vite`) to get typed test options. A separate `vitest.config.ts` is only needed when test settings must diverge from the build config. Vitest no longer looks for a config in parent directories.

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
      include: ['src/**/*.{ts,tsx}'], // required to report uncovered files
      reporter: ['text', 'html', 'lcov'],
    },
  },
})
```

```ts
// src/test/setup.ts
import '@testing-library/jest-dom/vitest'   // registers DOM matchers with Vitest's expect
```

If `globals: true`, add `"vitest/globals"` to tsconfig `compilerOptions.types`. **jsdom vs happy-dom:** jsdom is the safer default for React component tests; happy-dom is faster but covers a smaller API surface.

Add `.vitest` to `.gitignore` - in v5 it is the single artifact root (HTML/JSON/JUnit/blob reports, attachments, failure screenshots).

Install set:

```bash
pnpm add -D vitest vite @vitejs/plugin-react jsdom \
  @testing-library/react @testing-library/dom @testing-library/jest-dom \
  @testing-library/user-event @vitest/coverage-v8
```

`@testing-library/react` (16.x) supports React 19 and requires the separate `@testing-library/dom` peer. Keep every `@vitest/*` package on the exact same version as `vitest` - they are exact-version peers.

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

## Mocking

```ts
import { afterEach, expect, test, vi } from 'vitest'
import { fetchUser } from './api'
import { greet } from './greet'

vi.mock('./api', () => ({ fetchUser: vi.fn() }))   // hoisted to the top of the file

afterEach(() => vi.useRealTimers())

test('greets the fetched user', async () => {
  vi.mocked(fetchUser).mockResolvedValue({ name: 'Ada' })
  await expect(greet('1')).resolves.toBe('Hello, Ada')   // async assertions must be awaited
})

test('spies and fake timers', () => {
  const log = vi.spyOn(console, 'log').mockImplementation(() => {})
  vi.useFakeTimers()
  setTimeout(() => console.log('tick'), 1000)
  vi.advanceTimersByTime(1000)
  expect(log).toHaveBeenCalledWith('tick')
})
```

`vi.mock`/`vi.hoisted` must sit at module top level - in v5 calling them inside a function, block, or test **throws** (use `vi.doMock` for dynamic, non-hoisted mocks). New in v5, `vi.when` gives per-argument behavior without hand-written implementations:

```ts
const getFlag = vi.fn<(key: string) => boolean>()
vi.when(getFlag).calledWith('beta').thenReturn(true).calledWith('legacy').thenReturn(false)
```

## CLI

```bash
vitest                  # watch mode (default)
vitest run              # single run - use in CI
vitest --ui             # @vitest/ui dashboard (v5: token-authenticated)
vitest run --coverage   # enable coverage
vitest --typecheck      # type-level test mode
vitest -p unit          # filter to a project (--project, repeatable)
vitest doctor           # re-runs the suite with alternative configs, recommends faster options
```

## Coverage

The default provider is **v8** (`@vitest/coverage-v8`); `istanbul` is the alternative. The default reports only covered files, so set `coverage.include` to surface uncovered ones. In v5, `include`/`exclude` patterns match each file's path relative to the project root (no implicit "contains" matching), and a pattern without wildcards is a directory: `['src']` means `src/**`, not every path containing `src`. Re-check the reported file set after upgrading. When Vitest detects an AI coding agent, the `text` reporter auto-trims output (`skipFull: true` + a summary) to save tokens.

## Browser Mode

Runs tests in a real browser. The provider is an **imported factory object**, not a string:

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

Set it up with `npx vitest init browser`. Providers: `@vitest/browser-playwright` (recommended, supports parallelism), `@vitest/browser-preview` (local only - **not** for CI, it simulates events), and `@vitest/browser-webdriverio` (moved to the vitest-community org in v5). Render with `vitest-browser-react`; import `page`/`userEvent` from `vitest/browser`. v5 locators match text **exactly** by default, and browser `toHaveTextContent` is strict equality - partial/RegExp matching moved to `toMatchTextContent`. `browser.traceView: true` (experimental) records each interaction as a DOM snapshot you can step through in the UI or HTML report.

## Projects

Use `test.projects` in the root config (not the old `vitest.workspace.ts`):

```ts
export default defineConfig({
  test: {
    projects: [
      'packages/*',
      { test: { name: 'unit', environment: 'jsdom', include: ['**/*.unit.test.ts'] } },
      { extends: false, test: { name: 'node', environment: 'node', include: ['**/*.node.test.ts'] } },
    ],
  },
})
```

**v5 change:** inline projects now **inherit the root config by default** (`extends` defaults to `true`), including `plugins`, `resolve.alias`, and `setupFiles` - arrays are merged, not replaced. Set `extends: false` for a project that must not see root plugins or setup files. Inline projects that don't change the Vite config share one Vite server (`sharedViteServer`), and a referenced project config may declare its own nested `projects`. Use `defineProject` for standalone project files - root-only keys (`coverage`, `reporters`) error inside a project.

## Test speed

Vitest 5 is faster out of the box (shared Vite server, vm-pool reuse, `fsModuleCache` on by default - transformed modules persist on disk across runs; clear with `vitest --clearCache`). The duration breakdown (`environment 79%, import 13%, ...`) tells you where time goes; `vitest doctor` tries alternative configs for you. Beyond that, **the module graph dominates**:

- Import the unit under test, not the app entry or a barrel file - a single barrel import can pull in hundreds of modules per test file.
- `isolate: false` (or a project with it) for pure-function suites that touch no shared global state can cut runtime substantially; keep isolation for DOM and stateful tests.
- Measure pool and cache tweaks before adopting them - on many suites they land within noise of the defaults.

## Migrating from v4

- **`clearMocks` defaults to `true`** - mock call history is cleared before every test; set `clearMocks: false` to keep v4 behavior.
- **Unawaited async assertions fail** - `expect(p).resolves`/`.rejects`/`toMatchFileSnapshot` must be `await`ed.
- **Inline projects inherit root config** (see Projects).
- **Reporters write files**: `json`/`junit` go to `.vitest/` instead of stdout; HTML moved to `.vitest/index.html` and its option is `outputDir` (was `outputFile`).
- **Removed entrypoints**: `vitest/coverage` -> `vitest/node`, `vitest/environments` -> `vitest/runtime`.
- **Benchmarks rewritten**: `bench` is a test-context fixture, no longer a top-level import.
- Coming from v3: `vite-node` was replaced by Vite's Module Runner, and `maxThreads`/`maxForks` became `maxWorkers`.

## Resources

- Guide: https://vitest.dev/guide/ - Config: https://vitest.dev/config/
- Vitest 5 announcement: https://vitest.dev/blog/vitest-5 - Migration: https://vitest.dev/guide/migration
- Mocking: https://vitest.dev/guide/mocking - Browser Mode: https://vitest.dev/guide/browser/
