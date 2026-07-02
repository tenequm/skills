---
name: playwright-cli-cloakbrowser
description: Drive CloakBrowser Manager stealth profiles with @playwright/cli over CDP. Use for browser automation that needs a persistent logged-in session, anti-detect fingerprints, or to pass Cloudflare - attach reuses the profile's cookies and stealth where a fresh browser does not.
metadata:
  version: "0.1.0"
  upstream: "@playwright/cli@0.1.14"
allowed-tools: Bash(playwright-cli:*) Bash(curl:*) Bash(docker:*)
---

# playwright-cli on CloakBrowser stealth profiles

[CloakBrowser Manager](https://github.com/CloakHQ/CloakBrowser-Manager) runs isolated stealth Chromium profiles - unique fingerprint, optional proxy, persistent cookies, built-in noVNC live view - in a single Docker container. Every running profile exposes a CDP endpoint. `playwright-cli attach` connects to the profile's **persistent context** (`contexts[0]`), so automation inherits the profile's logins and stealth fingerprint; `playwright-cli open` would launch a plain local browser with neither. Always `attach` for this setup.

No Manager running yet? Set one up on your laptop first: [references/local-setup.md](references/local-setup.md).

For the **full command reference**, run `playwright-cli --help` and open the `Agent skill:` path it prints (the official skill bundled with `@playwright/cli`). This file only covers the CloakBrowser-specific setup and gotchas.

## Connect

```bash
# generic: attach to any CDP endpoint
playwright-cli attach --cdp=<CDP_URL>

# CloakBrowser Manager: per-profile CDP endpoint (shown via the toolbar
# code icon while a profile is running)
playwright-cli attach --cdp=http://localhost:8080/api/profiles/<profile-id>/cdp

# then drive normally
playwright-cli goto https://example.com
playwright-cli snapshot                       # a11y tree with refs (e3, e15, ...)
playwright-cli click e15
playwright-cli --raw eval "document.title"    # --raw = value only, no snapshot noise
playwright-cli detach                         # leave the browser running for next time
```

- The profile must be **running** first - click Launch in the Manager GUI, or `curl -X POST http://localhost:8080/api/profiles/<profile-id>/launch`.
- `--cdp=<url>` and `--cdp <url>` both work.
- **Never `close` / `close-all` / `kill-all`** on an attached stealth profile - that can stop the shared browser and its session. Use **`detach`** to leave it running.

## Logging into a site

The profile persists cookies, localStorage, and cache across restarts. To establish a login: open the Manager GUI at `http://localhost:8080`, view the running profile in the built-in noVNC viewer, and sign in there once. playwright-cli then drives the same session logged-in - the VNC view and the CDP connection share one browser.

## Gotchas (all observed in practice)

1. **`attach` hangs ~30 s, then times out** - the profile has a stale or heavy pre-existing tab that never finishes Playwright's `connectOverCDP` page-init handshake. Fix: close extra tabs via the noVNC view (or stop/relaunch the profile), then re-attach - drops to under a second. A clean `about:blank` profile attaches instantly.
2. **New-tab creation can be rejected** ("Failed to open a new tab") - the stealth browser may forbid `Target.createTarget` in some states. **Prefer navigating the current tab (`goto`) over `tab-new`.** If a page closes or replaces its own tab (challenge redirects, heavy detail pages), the driver desyncs - just re-`attach` and continue.
3. **JS-rendered content** (prices, dynamic cards) often is not in the a11y `snapshot` - scrape the DOM with `eval`: `playwright-cli --raw eval "[...document.querySelectorAll('[data-card]')].map(e=>e.innerText)"`.
4. **Heavy detail pages are slow through a profile proxy** and can timeout or desync. Read what you need from the list/results page when possible; treat opening detail pages as best-effort.
5. **Cookie/consent overlays** block clicks ("element covered"). Dismiss via JS: `playwright-cli eval "document.querySelector('#onetrust-accept-btn-handler')?.click()"`.
6. **Use `--raw`** whenever scraping or piping - without it every command appends page status plus a snapshot block, which mangles output.

## Minimal working pattern

```bash
CDP=http://localhost:8080/api/profiles/<profile-id>/cdp
playwright-cli attach --cdp=$CDP
playwright-cli goto "https://www.amazon.com/s?k=iphone+16+pro+max"
playwright-cli --raw eval "[...document.querySelectorAll('[data-asin]')].slice(0,5).map(e=>e.innerText.split('\n')[0]).join(' | ')"
playwright-cli detach   # leave the stealth browser running
```

## Notes

- Egress IP is whatever the profile's proxy is set to (or the Docker host's IP with no proxy). Sites see that location for geo, currency, and language - configure the profile's proxy, timezone, and locale together in the Manager.
- One profile = one persistent identity. Use separate profiles for separate accounts; that is the point of the Manager.
