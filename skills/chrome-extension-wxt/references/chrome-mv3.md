# Chrome MV3 platform rules

Platform behaviour that WXT does not hide, covering Chrome up to version 157. Service worker lifecycle and messaging rules live in `SKILL.md`. All examples use WXT's auto-imported `browser`.

## Contents

- [The `browser` namespace](#the-browser-namespace)
- [Network requests: `declarativeNetRequest`](#network-requests-declarativenetrequest)
- [Offscreen documents](#offscreen-documents)
- [Side panel](#side-panel)
- [Storage quotas](#storage-quotas)
- [Permissions and security](#permissions-and-security)
- [Recent API changes](#recent-api-changes)

## The `browser` namespace

From Chrome 148 every extension API is also available as `browser.*`, identical to `chrome.*`. WXT's `browser` already resolves to whichever exists, so nothing changes in WXT code. It matters for code that runs outside WXT's bundle. For a new extension that uses `browser` directly, set `minimum_chrome_version: "148"` in the manifest.

## Network requests: `declarativeNetRequest`

Blocking `webRequest` listeners (`['blocking']`) are not available to MV3 extensions; `webRequestBlocking` is limited to policy-installed extensions. Observing requests with `webRequest` still works. To block, redirect or change headers, use rules:

```ts
// entrypoints/background.ts
export default defineBackground(() => {
  browser.runtime.onInstalled.addListener(async () => {
    await browser.declarativeNetRequest.updateDynamicRules({
      removeRuleIds: [1],
      addRules: [
        {
          id: 1,
          priority: 1,
          action: { type: 'block' },
          condition: {
            urlFilter: '||ads.example.com^',
            resourceTypes: ['script', 'image'],
          },
        },
      ],
    });
  });
});
```

- Permission: `declarativeNetRequest` gives implicit access for `block`, `allow` and `allowAllRequests` rules. `redirect` and `modifyHeaders` actions also need host permissions for the affected sites.
- `declarativeNetRequestWithHostAccess` shows no install warning but needs host permissions for every action; use it when the extension already has them.
- Static rules ship as JSON: put `rules.json` in `public/` and declare `declarative_net_request: { rule_resources: [{ id: 'main', enabled: true, path: 'rules.json' }] }` in the manifest.

## Offscreen documents

For DOM parsing, clipboard access, audio playback or other DOM-only work from the background. An extension can have one offscreen document at a time.

```ts
// utils/offscreen.ts
export async function ensureOffscreenDocument() {
  const contexts = await browser.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
  });
  if (contexts.length > 0) return;

  await browser.offscreen.createDocument({
    url: '/offscreen.html',
    reasons: ['DOM_PARSER'],
    justification: 'Parse fetched HTML',
  });
}
```

Create `entrypoints/offscreen.html` (an unlisted page) and add the `offscreen` permission. Chrome 150 added `browser.offscreen.hasDocument()` as a shorter existence check. Talk to the document with normal messaging.

## Side panel

`entrypoints/sidepanel.html` (or `sidepanel/index.html`) becomes the side panel, and WXT adds the `sidePanel` permission. Chromium uses the `side_panel` API; Firefox maps the same entrypoint to `sidebar_action`, where `browser.sidePanel` is `undefined`.

```ts
// entrypoints/background.ts
export default defineBackground(() => {
  browser.sidePanel?.setPanelBehavior({ openPanelOnActionClick: true });
});
```

- `sidePanel.open()` only works in response to a user action (a click handler, a context menu, a keyboard command).
- The API is available in extension pages and the service worker, not in content scripts.
- `getLayout()` (Chrome 140+) resolves `{ side: 'left' | 'right' }`. `close()` and `onOpened` arrived in Chrome 141, `onClosed` in 142. No event fires when the user moves the panel to the other side.

## Storage quotas

| Area | Limit | Notes |
|---|---|---|
| `local` | 10 MB | The `unlimitedStorage` permission removes the limit |
| `sync` | About 100 KB total, 8 KB per item | Synced across the user's signed-in browsers; behaves like `local` when sync is off |
| `session` | 10 MB | In memory; cleared when the extension is disabled, reloaded or updated and when the browser restarts; not exposed to content scripts by default |
| `managed` | Read-only | Set by enterprise policy |

## Permissions and security

- Request the narrowest set. Prefer `activeTab` over broad host permissions when the extension only acts on a click.
- Put rarely used permissions in `optional_permissions` and call `browser.permissions.request()` from a user gesture.
- In MV3, users can restrict host permissions per site. Check `browser.permissions.contains()` before assuming access.
- MV3 forbids remotely hosted code: every script must ship in the package. WXT 0.21 removed its `url:` import feature for the same reason.
- The extension-page CSP cannot be loosened with `'unsafe-eval'` or remote script sources; Chrome refuses to load the extension.
- Never ship secrets in the bundle. Anything in the extension is readable by the user.

## Recent API changes

| Chrome | Change |
|---|---|
| 140 | `sidePanel.getLayout()` |
| 141-142 | `sidePanel.close()`, `onOpened`, `onClosed` |
| 146 | Listener errors propagate to `sendMessage()` |
| 148 | `browser` namespace; promise-returning `onMessage` listeners; opt-in structured clone messaging ([blog post](https://developer.chrome.com/blog/structured-clone-messaging)) |
| 149 | `userScripts.execute()` validates syntax synchronously; `devtools.inspectedWindow.eval()`, `getResources()` and `network.getHAR()` return promises |
| 150 | `contextMenus` `"tab"` context for the tab strip; alarm names limited to 1024 bytes; `offscreen.hasDocument()` |
| 153 | `browser.publicSuffix`; experiment pinning new extensions' action icons to the toolbar by default |

Newer entries: [What's new in Chrome extensions](https://developer.chrome.com/docs/extensions/whats-new).

## Links

- [Service worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle)
- [Message passing](https://developer.chrome.com/docs/extensions/develop/concepts/messaging)
- [declarativeNetRequest](https://developer.chrome.com/docs/extensions/reference/api/declarativeNetRequest)
- [Offscreen documents](https://developer.chrome.com/docs/extensions/reference/api/offscreen)
- [Side panel](https://developer.chrome.com/docs/extensions/reference/api/sidePanel)
- [Transition to the browser namespace](https://developer.chrome.com/docs/extensions/develop/concepts/browser-namespace)
