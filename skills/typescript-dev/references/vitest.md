# Vitest

The Vite-native test runner. Vitest **5** (latest `5.1.0`; 5.0 released 2026-09-03) reuses your `vite.config.ts` - same plugins, resolve aliases, and transforms - so tests see the app exactly as the bundler builds it. It requires **Vite >= 6.4.0 and Node.js >= 22.12.0**, and `vite` is now a **required peer dependency** (install it explicitly - Yarn PnP and strict installs no longer get it transitively).

> **Security:** on v5 use **>= 5.0.5** - GHSA-p458-7748-mcp3: `@vitest/ui` and `@vitest/browser` 5.0.0-beta.6 to 5.0.4 misapply `server.fs.deny`, serving `.env`, private keys, `.git`, and the API token file when you run `--ui`, Browser Mode, or `api`. On v4 use **4.1.12**: it covers GHSA-p63j-vcc4-9vmv (critical - Browser Mode provider commands bypass the file-access gate, fixed in 4.1.10), GHSA-82fw-gwwq-j7x9 (`@vitest/mocker` redirect-mock path traversal, 4.1.11), and the follow-ups GHSA-qxg6-89mg-rqv8 (code injection via unauthenticated manual mock registration) and GHSA-xp26-3454-mjgp (Windows backslash bypass of the 4.1.11 fix). Keep every `@vitest/*` package on the same version.

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

### Mocking and hook patterns that hold up

```ts
// Partial mock: keep the real module, override one export - new real exports keep working
vi.mock('./config', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./config')>()),
  isFeatureOn: vi.fn(() => true),
}))

// Factories are hoisted above your top-level consts - share mock fns through vi.hoisted
const mocks = vi.hoisted(() => ({ send: vi.fn() }))
vi.mock('./mailer', () => ({ send: mocks.send }))
```

- A hand-written full factory drifts: every export later added to the real module is missing from the mock, and hand-copied helpers stop matching the real ones. Prefer the `importOriginal` spread. A library whose classes depend on internal wiring can break when spread - mock at your own boundary (the module that wraps it) instead.
- Give hooks a **block body**. `beforeEach(() => fn.mockReset())` returns the mock, and a function returned from `beforeEach` is treated as a cleanup hook, so Vitest calls the mock after every test. Write `beforeEach(() => { fn.mockReset() })`.
- Put a heavy one-time fixture (importing or booting the whole app) in `beforeAll`, not inside each `it()`: the first test otherwise pays the cold start inside the 5 s test timeout and flakes on a loaded machine. Raising the timeout hides the problem.
- Module-level state (caches, semaphores, singletons) persists across the tests of one file. Reset it through an exported function, or use `vi.resetModules()` plus a dynamic `import()` for a fresh instance.

## Env, time, and environments

- Code that reads `process.env` at import time can't be primed from the test body - static imports run first. Set values in `test.env` in the config, or per test with `vi.stubEnv('KEY', 'value')`, then `vi.resetModules()` and `await import('./module')`.
- Vite's env loading applies to tests: `.env.local` is "loaded in all cases", so a developer's local `VITE_*` flags leak into Vitest. Pin the values tests depend on in `.env.test` or `test.env`.
- Loggers that write straight to the file descriptor (pino) bypass `console`, so Vitest can't capture or silence them. Give the logger an explicit level and set it to silent through `test.env`.
- Pin the clock for anything date-relative - `vi.useFakeTimers()` then `vi.setSystemTime(new Date('2026-01-15T12:00:00Z'))`. A seed like "30 minutes ago" lands in "yesterday" when the suite runs just after UTC midnight. Since 5.1, `setSystemTime` also accepts `Temporal` values and `fakeTimers.fakeNodeBuiltins` fakes `node:timers` too ("We plan to enable it by default in the next major version").
- Run server-side modules in `environment: 'node'`, ideally as their own project. Under jsdom, crypto libraries trip on cross-realm values (jsdom's `TextEncoder` output is not `instanceof` the test realm's `Uint8Array`), and jsdom has no `Blob.text()`. A per-file `// @vitest-environment node` comment works, but then a jsdom-only `setupFiles` runs in node and can crash.
- "All tests passed, run failed" with an unhandled error after a jsdom file tore down (e.g. `window is not defined` from react-dom's scheduler) means async UI work outlived the test: await it with `findBy*`/`waitFor`, and clear pending timers in `afterEach`.

## CLI

```bash
vitest                  # watch mode (default)
vitest run              # single run - use in CI
vitest run --changed main  # only tests affected by changes vs a git ref (follows the import graph)
vitest run --since-last-run  # 5.1: only tests whose files changed since their last run (no git needed)
vitest run --last-failed     # 5.1: rerun only the failures
vitest --ui             # @vitest/ui dashboard (v5: token-authenticated)
vitest run --coverage   # enable coverage
vitest --typecheck      # type-level test mode
vitest -p unit          # filter to a project (--project, repeatable)
vitest doctor           # re-runs the suite with alternative configs, recommends faster options
```

## Coverage

The default provider is **v8** (`@vitest/coverage-v8`); `istanbul` is the alternative. The default reports only covered files, so set `coverage.include` to surface uncovered ones. In v5, `include`/`exclude` patterns match each file's path relative to the project root (no implicit "contains" matching), and a pattern without wildcards is a directory: `['src']` means `src/**`, not every path containing `src`. Re-check the reported file set after upgrading. When Vitest detects an AI coding agent, the `text` reporter auto-trims output (`skipFull: true` + a summary) to save tokens. Since 5.1, `coverage.ignoreNode` (v8) excludes AST nodes from coverage - written for cases "like the cache branches that the React Compiler adds to every component", which otherwise drag branch coverage down.

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

Set it up with `npx vitest init browser`. Providers: `@vitest/browser-playwright` (recommended, supports parallelism), `@vitest/browser-preview` (local only - **not** for CI, it simulates events), and `@vitest/browser-webdriverio` (moved to the vitest-community org in v5). Render with `vitest-browser-react`; import `page`/`userEvent` from `vitest/browser`. v5 locators match text **exactly** by default, and browser `toHaveTextContent` is strict equality - partial/RegExp matching moved to `toMatchTextContent`. Trace view (stable since 5.1) records each interaction as a DOM snapshot you can step through in the UI or HTML report; it is on by default for failures (`browser.traceView.mode` defaults to `'failure-only'`, and `browser.traceView.enabled` is deprecated in favor of `mode`). Since 5.1 the browser server's default port is 23315.

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
- Split a module whose top level loads a heavy SDK when a test only needs one of its functions - moving that function out beats any config knob.
- Measure pool and cache tweaks before adopting them - on many suites they land within noise of the defaults. `test.deps.optimizer` pre-bundling can leave tests holding two copies of a library, silently breaking `instanceof` checks against its error classes.
- The `threads` pool can't use `process.chdir()` (and changing `process.env.TZ` has no effect in a worker): pass directories in, or keep those files on `forks`, the default.
- `fsModuleCache` lives in `node_modules/.vitest-cache` at the workspace root; CI only benefits if that directory (or a custom `fsModuleCachePath`) is restored between runs.

## Suite hygiene

- **Fast pre-commit gate:** `vitest run --changed <ref> --passWithNoTests` (or `--since-last-run`) instead of the full suite; keep the full run in CI.
- **Skipped suites look green.** Suites gated with `skipIf`/`runIf` on an env var or database URL never run in the default gate but still read as passing. Move them out of the default `include` into their own script or project so "not run" is visible.
- **Assert scaling, not wall-clock time.** A ReDoS or performance guard with a fixed millisecond budget flakes under load; compare the time for input size n against 2n instead.
- **Prove a regression test red first:** put the bug back, watch the test fail, then restore the fix.
- **Delete tests that only exercise a library** - a test that builds its own Hono app with hand-written middleware tests Hono, not your code. Test your decision logic and mock at your boundary.

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
