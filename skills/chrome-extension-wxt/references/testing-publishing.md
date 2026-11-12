# Testing and publishing

Verified against `wxt@0.21.5`.

## Contents

- [Unit tests with Vitest](#unit-tests-with-vitest)
- [End-to-end tests with Playwright](#end-to-end-tests-with-playwright)
- [Building zips](#building-zips)
- [Submitting to stores](#submitting-to-stores)
- [Before submitting](#before-submitting)

## Unit tests with Vitest

```bash
npm i -D vitest
```

```ts
// vitest.config.ts
import { configDefaults, defineConfig } from 'vitest/config';
import { WxtVitest } from 'wxt/testing/vitest-plugin';

export default defineConfig({
  plugins: [WxtVitest()],
  test: {
    exclude: [...configDefaults.exclude, 'e2e/**'],
  },
});
```

The `exclude` keeps Vitest from picking up Playwright's `*.spec.ts` files. The plugin replaces `browser` with an in-memory fake, applies the Vite config from `wxt.config.ts`, and sets up auto-imports, aliases and `import.meta.env.BROWSER`. Do not hand-mock `globalThis.browser`.

```ts
// utils/__tests__/theme.test.ts
import { beforeEach, describe, expect, it } from 'vitest';
import { fakeBrowser } from 'wxt/testing/fake-browser';

const theme = storage.defineItem<'light' | 'dark'>('local:theme', {
  fallback: 'light',
});

describe('theme', () => {
  beforeEach(() => {
    fakeBrowser.reset();
  });

  it('returns the fallback when nothing is stored', async () => {
    expect(await theme.getValue()).toBe('light');
  });

  it('persists a new value', async () => {
    await theme.setValue('dark');
    expect(await theme.getValue()).toBe('dark');
  });
});
```

- The `wxt/testing` barrel export was removed in 0.21. Import from `wxt/testing/fake-browser` and `wxt/testing/vitest-plugin`.
- To mock a WXT API, mock its real module, not `#imports`: `vi.mock('wxt/utils/inject-script', ...)`. The real paths are listed in `.wxt/types/imports-module.d.ts`.
- A faked `runtime.onMessage` listener cannot answer by returning a promise. Use `sendResponse` and `return true`, the same as production code.
- `@webext-core/messaging` works under `WxtVitest`: register a handler with `onMessage` and call `sendMessage` in the same test to exercise it.
- For component tests add `@testing-library/react` and a DOM environment (`environment: 'happy-dom'` or `'jsdom'` under `test` in the Vitest config).

## End-to-end tests with Playwright

Extensions load only in Chromium with a persistent context. Build first (`wxt build`), then point Playwright at the output directory.

```bash
npm i -D @playwright/test
npx playwright install chromium
```

```ts
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({ testDir: 'e2e' });
```

```ts
// e2e/fixtures.ts
import { test as base, chromium, type BrowserContext } from '@playwright/test';
import path from 'node:path';

const pathToExtension = path.resolve('.output/chrome-mv3');

export const test = base.extend<{
  context: BrowserContext;
  extensionId: string;
}>({
  context: async ({}, use) => {
    const context = await chromium.launchPersistentContext('', {
      channel: 'chromium',
      args: [
        `--disable-extensions-except=${pathToExtension}`,
        `--load-extension=${pathToExtension}`,
      ],
    });
    await use(context);
    await context.close();
  },
  extensionId: async ({ context }, use) => {
    let [serviceWorker] = context.serviceWorkers();
    if (!serviceWorker) serviceWorker = await context.waitForEvent('serviceworker');
    await use(serviceWorker.url().split('/')[2]!);
  },
});

export const expect = test.expect;
```

```ts
// e2e/popup.spec.ts
import { expect, test } from './fixtures';

test('popup renders', async ({ page, extensionId }) => {
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  await expect(page.locator('#root')).not.toBeEmpty();
});
```

Use Playwright's bundled Chromium (`channel: 'chromium'`); branded Chrome and Edge removed the side-loading flags. The `extensionId` fixture needs a background entrypoint, because it reads the id from the service worker URL.

## Building zips

```bash
wxt zip              # .output/{name}-{version}-chrome.zip
wxt zip -b firefox   # also writes .output/{name}-{version}-sources.zip
```

- `{name}` and `{version}` come from `package.json`. Bump `version` there; do not set it in the manifest.
- The default file name template is `{{name}}-{{packageVersion}}-{{browser}}{{modeSuffix}}.zip`; change it with `zip.artifactTemplate`.
- Firefox review needs the sources zip and a `README.md` or `SOURCE_CODE_REVIEW.md` with build steps. Extract the zip and confirm `npm i && npm run zip:firefox` reproduces the same output.
- `zip.includeSources`, `zip.excludeSources` and `zip.dotSources` control what goes in the sources zip. `.env` files change chunk hashes: remove them before zipping, or include them only if they hold no secrets.
- Safari: `wxt build -b safari`, then `xcrun safari-web-extension-packager .output/safari-mv2`. Safari needs a native app wrapper from Xcode; WXT does not automate it.

## Submitting to stores

The first submission to each store is manual: create the listing, upload a zip and fill in the forms. After that, WXT automates updates.

```bash
wxt submit init
```

This walks through each store and writes the credentials to `.env.submit`. Keep that file out of git.

**Chrome Web Store API v1 stopped working on 15 October 2026.** When `wxt submit init` asks, choose the v2 API, which authenticates with a service account instead of a refresh token. A CI job that still passes `CHROME_REFRESH_TOKEN` is using v1 and fails.

```bash
wxt zip
wxt zip -b firefox

wxt submit --dry-run \
  --chrome-zip .output/my-extension-1.2.0-chrome.zip \
  --firefox-zip .output/my-extension-1.2.0-firefox.zip \
  --firefox-sources-zip .output/my-extension-1.2.0-sources.zip \
  --edge-zip .output/my-extension-1.2.0-chrome.zip
```

Drop `--dry-run` once it passes. The Edge store takes the Chrome zip.

### GitHub Actions

```yaml
# .github/workflows/release.yml
name: Release

on:
  workflow_dispatch:

jobs:
  submit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: 22
          cache: npm
      - run: npm ci
      - run: npm run zip
      - run: npm run zip:firefox
      - name: Submit to stores
        run: |
          npx wxt submit \
            --chrome-zip .output/*-chrome.zip \
            --firefox-zip .output/*-firefox.zip \
            --firefox-sources-zip .output/*-sources.zip
        env:
          FIREFOX_EXTENSION_ID: ${{ secrets.FIREFOX_EXTENSION_ID }}
          FIREFOX_JWT_ISSUER: ${{ secrets.FIREFOX_JWT_ISSUER }}
          FIREFOX_JWT_SECRET: ${{ secrets.FIREFOX_JWT_SECRET }}
```

Add one `env` line and one repository secret for every Chrome and Edge variable that `wxt submit init` wrote to `.env.submit`; the Chrome names depend on the API version chosen. WXT needs Node 22 or newer in CI.

## Before submitting

- Icons at 16, 32, 48 and 128 px in `public/`.
- Every permission and host permission is used and explained in the listing; unused ones are a common rejection reason.
- A privacy policy URL when the extension handles user data.
- Firefox: a `gecko.id` and `data_collection_permissions` in `browser_specific_settings` (see Configuration in `SKILL.md`). `wxt build -b firefox` prints no Firefox warnings.
- No remotely hosted code and no secrets in the bundle.
- Tested from the production build (`wxt build`), loaded unpacked, in each target browser.
- To test an update path with changed permissions, use Google's [extension update testing tool](https://github.com/GoogleChromeLabs/extension-update-testing-tool).

## Links

- [WXT unit testing](https://wxt.dev/guide/essentials/unit-testing)
- [WXT E2E testing](https://wxt.dev/guide/essentials/e2e-testing)
- [WXT publishing](https://wxt.dev/guide/essentials/publishing)
- [Playwright Chrome extensions](https://playwright.dev/docs/chrome-extensions)
- [Chrome Web Store publishing](https://developer.chrome.com/docs/webstore/publish/)
- [Firefox source code submission](https://extensionworkshop.com/documentation/publish/source-code-submission/)
