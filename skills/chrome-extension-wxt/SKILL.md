---
name: chrome-extension-wxt
description: Builds cross-browser extensions with WXT - entrypoints, content-script UI, storage, messaging, MV3 rules, testing, publishing. Use for Chrome or browser extension work, wxt.config.ts, Manifest V3, or WXT build and type errors.
metadata:
  version: "2.1.1"
  upstream: "wxt@0.21.5, @wxt-dev/module-react@1.2.2, chrome@157"
  categories: "development"
  topics: "chrome-extension, wxt, browser-extension, manifest-v3, typescript"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/chrome-extension-wxt
    emoji: "🧩"
---

# Browser Extensions with WXT

[WXT](https://wxt.dev) is a Vite-based framework that builds one codebase for Chrome, Firefox, Edge and Safari. It generates the manifest from files in `entrypoints/`, so there is no `manifest.json` in the source tree.

Verified against `wxt@0.21.5`. WXT 0.21 needs Node >= 22, and `vite` (`^6.3.4`, `^7` or `^8`) is a required peer dependency.

## Before you start

1. **Confirm it is a WXT project:** `wxt.config.ts` exists and `wxt` is in `package.json`. If not, do not migrate the project unasked; the WXT sections do not apply, but `references/chrome-mv3.md` still does.
2. **Check the installed `wxt` version.** This skill targets 0.21. Below 0.20 the import paths and several APIs differ: follow the [upgrade guide](https://wxt.dev/guide/resources/upgrading) before applying these patterns.

## Rules that prevent most failures

1. **WXT APIs are auto-imported globals.** `defineBackground`, `defineContentScript`, `defineUnlistedScript`, `createShadowRootUi`, `browser`, `storage`, `injectScript`, `MatchPattern` and `ContentScriptContext` need no import line. Never "fix" them as missing imports.
2. **The old import paths are gone.** `wxt/sandbox`, `wxt/client`, `wxt/storage` and `wxt/match-pattern` do not exist; using one fails with `Missing "./sandbox" specifier in "wxt" package`. For an explicit import use `import { storage } from '#imports'`. The per-utility paths are `wxt/utils/*` and `wxt/browser`.
3. **"Cannot find name defineBackground" means the generated types are missing.** Run `wxt prepare` (wired as `"postinstall": "wxt prepare"`). It regenerates `.wxt/`, which `tsconfig.json` extends. Do not add imports to silence it.
4. **`.wxt/` and `.output/` are generated.** Gitignore both, along with `web-ext.config.ts`.
5. **Runtime code goes inside `main()`.** WXT imports every entrypoint in Node at build time, so top-level `browser.*` or `document.*` calls fail the build with `document is not defined`.
6. **Nothing loose in `entrypoints/`.** Every file or folder directly inside it becomes an entrypoint. Put helper files inside the entrypoint's own folder (`popup/`, `overlay.content/`) or in `components/` and `utils/`. Entrypoints cannot nest deeper than one level, and names must be unique across types: `foo.ts` and `foo.content.ts` clash.
7. **`await createShadowRootUi(...)`.** It returns a promise. `createIntegratedUi` and `createIframeUi` are synchronous.
8. **Write the manifest in MV3 form.** WXT converts `action`, `host_permissions` and `web_accessible_resources` for MV2 targets. It does not convert runtime API calls: see [Targeting browsers](#targeting-browsers). The extension `version` comes from `package.json`.
9. **The MV3 service worker is stateless.** See [Background](#background).

## What WXT recommends

Each line restates a recommendation from WXT's or Chrome's own docs.

- **Storage:** define items with `storage.defineItem`; it is WXT's recommended way to get type safety.
- **Messaging:** use a library that wraps the raw API, such as `@webext-core/messaging`.
- **Page-context code:** inject an unlisted script with `injectScript` rather than `world: 'MAIN'`.
- **Manifest:** write every property in MV3 form; WXT converts for MV2 targets.
- **Entrypoints:** one directory per entrypoint, holding its own files.
- **Extension APIs:** use `browser`, and feature-detect APIs a browser may lack.
- **Routing in pages:** hash mode (`createHashRouter` and equivalents), because extension pages are static files.
- **Tests:** Vitest with `WxtVitest` for units; Playwright for end-to-end.
- **Translations:** the built-in `browser.i18n` API or `@wxt-dev/i18n`.

Two platform facts from Chrome's docs shape most designs:

- **Content scripts are less trustworthy than the background.** A compromised page can forge their messages. Validate every message they send, and derive the page's origin from `sender.url`, not from the payload.
- **A popup closes as soon as it loses focus** and cannot be kept open. Keep its state in storage.

## Quick start

```bash
npx wxt@latest init my-extension -t react --pm npm
cd my-extension
npm install
```

Templates are `vanilla`, `vue`, `react`, `svelte` and `solid` (all TypeScript). `--pm` takes `npm`, `pnpm`, `yarn` or `bun`. There is no `create-wxt` package, so `npm create wxt` fails. The templates do not list `vite`; npm and pnpm install the peer automatically, so nothing is needed. With Yarn, add `vite` to `devDependencies`.

For an existing project: `npm i -D wxt vite`, then add the scripts the templates use:

```json
{
  "scripts": {
    "dev": "wxt",
    "dev:firefox": "wxt -b firefox",
    "build": "wxt build",
    "build:firefox": "wxt build -b firefox",
    "zip": "wxt zip",
    "zip:firefox": "wxt zip -b firefox",
    "compile": "tsc --noEmit",
    "postinstall": "wxt prepare"
  }
}
```

`npm run dev` opens a browser with the extension loaded only when the optional `web-ext` package is installed (`npm i -D web-ext`). Without it, load `.output/chrome-mv3-dev` manually from `chrome://extensions`.

## Verify your work

Repeat until every step passes:

1. `npm run compile` - typecheck.
2. `npx wxt build`, and `npx wxt build -b firefox` if Firefox is a target. Read the warnings: WXT prints Firefox submission problems here.
3. Read `.output/chrome-mv3/manifest.json`: permissions, host permissions and content-script `matches` are exactly what you intended, nothing broader.
4. `npx vitest run` when the project has tests.
5. For runtime behaviour, a Playwright test against `.output/chrome-mv3` (see `references/testing-publishing.md`).

Do not run `npm run dev` unattended: it never exits and opens a browser window.

## Project structure

```
my-extension/
  entrypoints/        one file or folder per entrypoint
  components/         auto-imported
  hooks/              auto-imported (React, Solid)
  composables/        auto-imported (Vue)
  utils/              auto-imported
  assets/             processed by Vite
  public/             copied as-is; icons found as icon/16.png (template layout) or icon-16.png
  wxt.config.ts
  web-ext.config.ts   per-developer browser startup, gitignored
  tsconfig.json       { "extends": "./.wxt/tsconfig.json" }
```

Set `srcDir: 'src'` in the config to move everything except `public/` and the config files under `src/`. Aliases `@/` and `~/` point at `srcDir`; `@@/` and `~~/` at the project root. Add more with the `alias` config option, never with `paths` in `tsconfig.json`.

## Entrypoints

The file name decides the type. `{name}` is yours to choose.

| File in `entrypoints/` | Becomes |
|---|---|
| `background.ts` or `background/index.ts` | Service worker (MV3) or background page (MV2) |
| `popup.html` or `popup/index.html` | Toolbar popup |
| `options.html` or `options/index.html` | Options page |
| `sidepanel.html`, `{name}.sidepanel/index.html` | Side panel; WXT adds the `sidePanel` permission |
| `newtab.html`, `history.html`, `bookmarks.html`, `devtools.html`, `{name}.sandbox.html` | The matching override or page |
| `content.ts`, `{name}.content.ts(x)`, `{name}.content/index.ts(x)` | Content script, built to `content-scripts/{name}.js` |
| any other `{name}.html` or `{name}/index.html` | Unlisted page at `/{name}.html` |
| any other `{name}.ts` or `{name}/index.ts` | Unlisted script at `/{name}.js` |

### Background

```ts
// entrypoints/background.ts
export default defineBackground(() => {
  browser.runtime.onInstalled.addListener(({ reason }) => {
    console.log('Installed:', reason);
  });
});
```

The object form takes `type: 'module'` (ESM output, MV3 only), `persistent` (MV2 only), `include` and `exclude`. `main()` receives no arguments and cannot be async.

In MV3 the background is a service worker. Chrome stops it after 30 seconds without an event or extension API call, when one event takes longer than 5 minutes, or when a `fetch()` response takes more than 30 seconds. So:

- **No state in module variables.** It is lost on shutdown. Use `storage`: `local:` to persist, `session:` for in-memory state that outlives the worker but not a browser restart or extension reload.
- **Register listeners synchronously at the top of `main()`.** A listener added after an `await` can miss the event that woke the worker.
- **No DOM.** `window`, `document`, `localStorage` and `DOMParser` do not exist; use an offscreen document (`references/chrome-mv3.md`).
- **Use `browser.alarms`, not long timers.** The minimum period is 30 seconds.
- Short-lived worker processes are normal churn, not crashes. `runtime.onSuspend` is an event-page API; do not rely on it for cleanup.

### HTML pages

```html
<!-- entrypoints/popup/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>My Extension</title>
    <meta name="manifest.exclude" content="['safari']" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="./main.tsx"></script>
  </body>
</html>
```

Scripts need `type="module"`. Manifest options for a page are `<meta name="manifest.*">` tags. React, Tailwind and shadcn setup is in `references/react.md`.

## Content scripts

```ts
// entrypoints/example.content.ts
export default defineContentScript({
  matches: ['*://*.example.com/*'],
  runAt: 'document_idle',
  main(ctx) {
    ctx.addEventListener(window, 'scroll', () => {
      console.log('scrolled');
    });
  },
});
```

Options: `matches`, `excludeMatches`, `includeGlobs`, `excludeGlobs`, `allFrames`, `runAt`, `matchAboutBlank`, `matchOriginAsFallback`, `world` (`'ISOLATED'` or `'MAIN'`), `cssInjectionMode` (`'manifest'` default, `'manual'`, `'ui'`), `registration` (`'manifest'` default, `'runtime'`), `include`, `exclude`.

Content scripts are bundled as IIFE, not ESM. A dynamic `import()` inside one is inlined, so it does not split the bundle.

### Context

After the extension reloads or updates, the old content script keeps running and every extension API call throws `Extension context invalidated`. `ctx` stops work at that point. Use `ctx.addEventListener`, `ctx.setTimeout`, `ctx.setInterval` and `ctx.requestAnimationFrame` instead of the globals, `ctx.onInvalidated(cb)` for manual cleanup (for example `ctx.onInvalidated(onMessage(...))`), and check `ctx.isValid` before calling an extension API from a long-lived callback.

### UI in the page

| Helper | Style isolation | HMR | Use when |
|---|---|---|---|
| `createIntegratedUi` | no | no | The UI should inherit the page's styles |
| `createShadowRootUi` | yes | no | Default choice for injected UI |
| `createIframeUi` | yes | yes | The UI does not need the page's DOM |

```ts
// entrypoints/overlay.content/index.ts
import './style.css';

export default defineContentScript({
  matches: ['<all_urls>'],
  cssInjectionMode: 'ui',

  async main(ctx) {
    const ui = await createShadowRootUi(ctx, {
      name: 'example-overlay',
      position: 'inline',
      anchor: 'body',
      onMount(container) {
        const app = document.createElement('p');
        app.textContent = 'Hello from the extension';
        container.append(app);
      },
    });
    ui.mount();
  },
});
```

- `cssInjectionMode: 'ui'` puts the imported CSS inside the shadow root instead of the page. WXT then adds a `web_accessible_resources` entry for that CSS file on the same `matches`; it is expected, not a permission leak.
- `name` must be kebab-case. `position` is `'inline'`, `'overlay'` or `'modal'`. `anchor` is a selector, element or function; `append` is `'last'`, `'first'`, `'replace'`, `'before'` or `'after'`.
- Whatever `onMount` returns is passed to `onRemove`; use that to unmount a framework root.
- Since 0.21 the shadow root holds a `<style>` and a `<div>`, with no `<html>` or `<body>`. Base styles must target `:root, :host`.
- `rem` units follow the host page's root font size, so a Tailwind UI can change size between sites. The fix is in `references/react.md`.
- `ui.autoMount()` instead of `ui.mount()` mounts when the anchor appears and removes when it disappears.

### Single-page apps

Content scripts run on full page loads only. For client-side navigation, match the whole site and react to WXT's `wxt:locationchange` event:

```ts
// entrypoints/watch.content.ts
const watchPattern = new MatchPattern('*://*.youtube.com/watch*');

export default defineContentScript({
  matches: ['*://*.youtube.com/*'],
  main(ctx) {
    ctx.addEventListener(window, 'wxt:locationchange', ({ newUrl }) => {
      if (watchPattern.includes(newUrl)) console.log('Watch page:', newUrl.href);
    });
  },
});
```

`newUrl` and `oldUrl` are `URL` objects.

### Running in the page's JavaScript context

`world: 'MAIN'` works on Chromium MV3 only and loses access to extension APIs. WXT recommends a content script that injects an unlisted script:

```ts
// entrypoints/page-hook-main.ts
export default defineUnlistedScript(() => {
  console.log('Running in the main world', document.currentScript?.dataset['greeting']);
});
```

```ts
// entrypoints/page-hook.content.ts
export default defineContentScript({
  matches: ['*://*.example.com/*'],
  async main() {
    await injectScript('/page-hook-main.js', {
      keepInDom: true,
      modifyScript(script) {
        script.dataset['greeting'] = 'hello';
      },
    });
  },
});
```

```ts
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  manifest: {
    web_accessible_resources: [
      { resources: ['page-hook-main.js'], matches: ['*://*.example.com/*'] },
    ],
  },
});
```

The two files need different names: `page-hook.ts` next to `page-hook.content.ts` fails with "Multiple entrypoints with the same name".

To call a content script on demand, set `registration: 'runtime'` and run it with `browser.scripting.executeScript({ target: { tabId }, files: ['content-scripts/example.js'] })`. Since 0.21 the script's return value is only exposed when `globalName: true` is set.

## Storage

Keys carry their storage area as a prefix: `local:`, `session:`, `sync:` or `managed:`. Any other prefix throws `Invalid area`. The manifest needs the `storage` permission.

```ts
// utils/storage.ts
export const theme = storage.defineItem<'light' | 'dark'>('local:theme', {
  fallback: 'light',
});

export const installId = storage.defineItem<string>('local:installId', {
  init: () => crypto.randomUUID(),
});
```

```ts
const current = await theme.getValue();
await theme.setValue('dark');
const unwatch = theme.watch((newValue, oldValue) => {
  console.log('theme changed', oldValue, newValue);
});
```

`fallback` is returned when nothing is stored; `init` writes a value once. Change a stored shape with `version` and `migrations`; an unversioned item counts as version 1:

```ts
// utils/ignored-sites.ts
interface IgnoredSiteV2 {
  id: string;
  host: string;
}

export const ignoredSites = storage.defineItem<IgnoredSiteV2[]>('local:ignoredSites', {
  fallback: [],
  version: 2,
  migrations: {
    2: (hosts: string[]): IgnoredSiteV2[] =>
      hosts.map((host) => ({ id: crypto.randomUUID(), host })),
  },
});
```

For one-off keys, `storage.getItem<T>('local:key')`, `setItem`, `removeItem` and `watch` work without defining an item. `item.watch` fires for writes from any context, so the popup, background and content scripts stay in sync without messaging.

## Messaging

WXT's `browser` is the native API with no polyfill, so the cross-browser way to answer asynchronously is `sendResponse` plus a literal `return true`:

```ts
// entrypoints/background.ts
export default defineBackground(() => {
  browser.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type !== 'get-status') return;
    fetch('https://example.com')
      .then((res) => sendResponse({ status: res.status }))
      .catch(() => sendResponse({ status: 0 }));
    return true;
  });
});
```

- Returning a promise from the listener works only from Chrome 148, which rolled it out gradually. An `async` listener always returns a promise, so there it answers every message, including ones meant for another listener.
- From Chrome 146, an error thrown by a listener rejects the sender's `sendMessage()`. With several listeners, only the first to respond counts.
- Chrome serialises messages as JSON: `undefined` becomes `null`, and `Date`, `Map` and `Set` do not survive. The limit is 64 MiB.

For anything beyond one message type, WXT recommends a typed wrapper. With `@webext-core/messaging` (`npm i @webext-core/messaging`):

```ts
// utils/messaging.ts
import { defineExtensionMessaging } from '@webext-core/messaging';

interface ProtocolMap {
  getStringLength(text: string): number;
}

export const { sendMessage, onMessage } = defineExtensionMessaging<ProtocolMap>();
```

```ts
// entrypoints/background.ts
export default defineBackground(() => {
  onMessage('getStringLength', ({ data }) => data.length);
});
```

```ts
// in a popup or content script
const length = await sendMessage('getStringLength', 'hello');
```

- To message a tab from the background, pass the tab id as a third argument: `sendMessage('getStringLength', 'hello', tabId)`.
- Handlers receive `{ data, sender }`. For messages from a content script, check `data` and take the page from `sender.url` and `sender.tab?.id`.
- `onMessage` returns a remover; in a content script pass it to `ctx.onInvalidated`.

### Knowing which page a tab shows

`browser.tabs.query({ active: true, currentWindow: true })` works with no permission, but `tab.url` and `tab.title` are only filled in when the extension has the `tabs` permission, host permission for that site, or `activeTab` after the user invoked it on that tab. In a popup, `activeTab` is the minimal choice: clicking the toolbar icon grants it for that tab. When a content script already runs on the page, avoid the extra permission: the background reads `sender.url` from that script's messages, or asks it for `location.hostname` with `sendMessage(..., tabId)`.

## Configuration

```ts
// wxt.config.ts
import { defineConfig } from 'wxt';

export default defineConfig({
  modules: ['@wxt-dev/module-react'],
  manifest: ({ browser, mode }) => ({
    name: mode === 'development' ? 'My Extension (dev)' : 'My Extension',
    permissions: ['storage'],
    host_permissions: ['*://*.example.com/*'],
    ...(browser === 'firefox' && {
      browser_specific_settings: {
        gecko: {
          id: 'my-extension@example.com',
          data_collection_permissions: { required: ['none'] },
        },
      },
    }),
  }),
});
```

- `manifest` is an object or a function of `{ browser, manifestVersion, mode, command }`. Use the function form to read `.env` values; they are not loaded yet when the config file is evaluated.
- **Firefox:** set a `gecko.id` (required for MV3, recommended for MV2). Since 3 November 2025 new Firefox extensions must declare `data_collection_permissions`: `{ required: ['none'] }` when nothing leaves the browser, otherwise the data types from [Mozilla's taxonomy](https://extensionworkshop.com/documentation/develop/firefox-builtin-data-consent/). WXT warns on `wxt build -b firefox` when either is missing.
- Extension pages already get the CSP `script-src 'self' 'wasm-unsafe-eval'; object-src 'self';`. MV3 rejects `'unsafe-eval'` and remote script sources.
- Env vars need a `WXT_` or `VITE_` prefix to reach runtime code. Dotenv files can be per mode and per browser: `.env.production`, `.env.firefox`.
- `vite: () => ({ plugins: [...] })` adds Vite plugins. `hooks: { 'build:manifestGenerated': (wxt, manifest) => { ... } }` edits the final manifest.
- Framework modules: `@wxt-dev/module-react`, `module-vue`, `module-svelte`, `module-solid`. Other first-party modules: `@wxt-dev/i18n`, `@wxt-dev/auto-icons`, `@wxt-dev/analytics`, `@wxt-dev/unocss`.

### Browser startup

```ts
// web-ext.config.ts
import { defineWebExtConfig } from 'wxt';

export default defineWebExtConfig({
  binaries: { chrome: '/path/to/chrome-beta' },
  chromiumArgs: ['--user-data-dir=./.wxt/chrome-data'],
  startUrls: ['https://example.com'],
});
```

`--user-data-dir` keeps logins and devtools settings between runs (on Windows use `chromiumProfile` with an absolute path plus `keepProfileChanges: true`). `disabled: true` stops WXT opening a browser. The same options go under `webExt` in `wxt.config.ts` when they should be shared with the team.

## Targeting browsers

```bash
wxt build                 # chrome, MV3
wxt build -b firefox      # firefox, MV2 by default
wxt build -b firefox --mv3
wxt build -b edge
wxt build -b safari       # MV2 by default
```

Output goes to `.output/{browser}-mv{2|3}`. Chrome accepts only MV3; WXT still defaults Firefox and Safari to MV2, so pass `--mv3` or set `manifestVersion: 3` when that is what you want. For Firefox, keep the MV2 default unless you need MV3: Mozilla has no plans to deprecate MV2, and its MV3 runs the background as an event page, not a service worker.

```ts
if (import.meta.env.FIREFOX) {
  // firefox builds only; also CHROME, SAFARI, EDGE, OPERA, BROWSER
}
if (import.meta.env.MANIFEST_VERSION === 2) {
  // MV2 builds only
}
```

- Every entrypoint takes `include: ['firefox']` or `exclude: ['safari']`. Options such as `matches` and `runAt` also accept a per-browser object: `matches: { chrome: [...], firefox: [...] }`.
- APIs missing in a browser are `undefined` at runtime even though the types say otherwise; guard with `browser.sidePanel?.open(...)`.
- **The toolbar API differs by manifest version.** WXT converts `action` in the manifest, but at runtime an MV2 build only has `browser.browserAction`. Badge or icon code that must work in the default Firefox build uses `const action = browser.action ?? browser.browserAction;`.

## References

- `references/chrome-mv3.md` - `declarativeNetRequest`, offscreen documents, side panel, storage quotas, permission design, and a table of recent Chrome API changes. Read when deciding which permissions to request, blocking or rewriting network requests, doing DOM work from the background, building a side panel, sizing stored data, or using an API added in a recent Chrome version.
- `references/react.md` - React with WXT: popup setup, shadow-root mounting, Tailwind v4, shadcn, zustand, hooks. Read for any React UI work.
- `references/testing-publishing.md` - Vitest with `WxtVitest` and `fakeBrowser`, Playwright, zips, `wxt submit`, store requirements. Read when adding tests or shipping.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| A helper file is built as its own entrypoint, or the build errors on it | It sits directly in `entrypoints/`. Move it into the entrypoint's folder. |
| Injected UI is unstyled | Missing `cssInjectionMode: 'ui'`, the CSS import, or `:root, :host` base styles. |
| `sendMessage` resolves `undefined` | The listener did not `return true`, or the service worker was not listening at the top of `main()`. |
| Badge or icon code throws only in the Firefox build | MV2 has no `browser.action`. Use `browser.action ?? browser.browserAction`. |
| Dev browser does not open | `web-ext` is not installed, or `disabled: true` is set. |
| `Extension context invalidated` | An old content script outlived a reload. Register listeners and timers through `ctx`. |
| Type-only import errors after upgrading to 0.21 | `verbatimModuleSyntax` is on. Use `import type`. |
| `Object is possibly 'undefined'` on array indexing | WXT's tsconfig enables `noUncheckedIndexedAccess`. Guard the element or use the value you already hold. |

## Links

- [WXT docs](https://wxt.dev) and [upgrade guide](https://wxt.dev/guide/resources/upgrading)
- [WXT examples](https://github.com/wxt-dev/examples)
- [Chrome extension docs](https://developer.chrome.com/docs/extensions) and [what's new](https://developer.chrome.com/docs/extensions/whats-new)
- [MDN WebExtensions](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)
