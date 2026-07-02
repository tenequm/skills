---
name: playwright-cli-cloakbrowser
description: Drive CloakBrowser Manager stealth profiles with @playwright/cli over CDP. Use for browser automation that needs a persistent logged-in session, anti-detect fingerprints, or to pass Cloudflare - attach reuses the profile's cookies and stealth where a fresh browser does not.
metadata:
  version: "0.2.0"
  upstream: "@playwright/cli@0.1.14"
allowed-tools: Bash(playwright-cli:*) Bash(curl:*) Bash(docker:*)
---

# playwright-cli on CloakBrowser stealth profiles

[CloakBrowser Manager](https://github.com/CloakHQ/CloakBrowser-Manager) runs isolated stealth Chromium profiles - unique fingerprint, optional proxy, persistent cookies, built-in noVNC live view - in a single Docker container. Every running profile exposes a CDP endpoint. `playwright-cli attach` connects to the profile's **persistent context** (`contexts[0]`), so automation inherits the profile's logins and stealth fingerprint; `playwright-cli open` would launch a plain local browser with neither. Always `attach` for this setup.

No Manager running yet? See [Setting up the Manager](#setting-up-the-manager-local-laptop) below.

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
playwright-cli --raw eval "document.title"    # --raw = return value only (JSON-serialized), no snapshot noise
playwright-cli detach                         # leave the browser running for next time
```

- The profile must be **running** first - click Launch in the Manager GUI, or `curl -X POST http://localhost:8080/api/profiles/<profile-id>/launch`.
- `--cdp=<url>` and `--cdp <url>` both work.
- `attach` creates an implicit session named `default` and prints a `--s=default` hint - that flag is only needed when juggling multiple sessions; plain commands use the default session.
- playwright-cli writes a `.playwright-cli/` scratch dir (snapshot `.yml` files, console logs) into the cwd - run from a scratch directory or gitignore it.
- **Never `close` / `close-all` / `kill-all`** on an attached stealth profile - that can stop the shared browser and its session. Use **`detach`** to leave it running.

## Logging into a site

The profile persists cookies, localStorage, and cache across restarts. To establish a login: open the Manager GUI at `http://localhost:8080`, view the running profile in the built-in noVNC viewer, and sign in there once. playwright-cli then drives the same session logged-in - the VNC view and the CDP connection share one browser.

## Gotchas (all observed in practice)

1. **`attach` hangs ~30 s, then times out** - the profile has a stale or heavy pre-existing tab that never finishes Playwright's `connectOverCDP` page-init handshake. Fix: close extra tabs via the noVNC view (or stop/relaunch the profile), then re-attach - drops to under a second. A clean `about:blank` profile attaches instantly.
2. **New-tab creation can be rejected** ("Failed to open a new tab") - the stealth browser may forbid `Target.createTarget` in some states. **Prefer navigating the current tab (`goto`) over `tab-new`.** If a page closes or replaces its own tab (challenge redirects, heavy detail pages), the driver desyncs - just re-`attach` and continue.
3. **JS-rendered content** (prices, dynamic cards) often is not in the a11y `snapshot` - scrape the DOM with `eval`: `playwright-cli --raw eval "[...document.querySelectorAll('[data-card]')].map(e=>e.innerText)"`.
4. **Heavy detail pages are slow through a profile proxy** and can timeout or desync. Read what you need from the list/results page when possible; treat opening detail pages as best-effort.
5. **Cookie/consent overlays** block clicks ("element covered"). Dismiss via JS: `playwright-cli eval "document.querySelector('#onetrust-accept-btn-handler')?.click()"`.
6. **Use `--raw`** whenever scraping or piping - without it output is wrapped in markdown header blocks (`### Result`, `### Page`, `### Snapshot` - varies by command), which mangles piping. Even with `--raw`, eval values come back JSON-serialized (strings quoted).

## Minimal working pattern

```bash
CDP=http://localhost:8080/api/profiles/<profile-id>/cdp
playwright-cli attach --cdp=$CDP
playwright-cli goto "https://www.amazon.com/s?k=iphone+16+pro+max"
playwright-cli --raw eval "[...document.querySelectorAll('[data-asin]')].slice(0,5).map(e=>e.innerText.split('\n')[0]).join(' | ')"
playwright-cli detach   # leave the stealth browser running
```

## Setting up the Manager (local laptop)

Requirements: Docker 20.10+, ~2 GB disk (the image bundles the CloakBrowser binary; the Manager is ready seconds after start), ~512 MB RAM per running profile.

```bash
docker run -d -p 8080:8080 -v cloakprofiles:/data cloakhq/cloakbrowser-manager
```

Binds to localhost. If 8080 is taken, map another host port (`-p 18080:8080`) and adjust every URL in this file accordingly. Profiles, cookies, and session data live in the `cloakprofiles` volume and survive container updates (`docker pull cloakhq/cloakbrowser-manager` + recreate). By default there is **no authentication** - fine for local use; add `-e AUTH_TOKEN=your-secret-token` to protect it, and pass `Authorization: Bearer <token>` on API calls.

Open [http://localhost:8080](http://localhost:8080) - the Manager web GUI. Create a profile (set proxy, timezone, and locale together if you need specific geo) and click **Launch**. Or headless via API:

```bash
# create -> returns {"id": "<profile-id>", ...}
curl -s -X POST http://localhost:8080/api/profiles \
  -H 'Content-Type: application/json' \
  -d '{"name": "agent", "platform": "macos"}'

# launch
curl -s -X POST http://localhost:8080/api/profiles/<profile-id>/launch

# list profiles / find the id later
curl -s http://localhost:8080/api/profiles
```

The noVNC live view is built into the GUI: click the running profile to watch and interact with the browser in a tab. Use it to log into sites once, watch automation live (VNC and CDP share the same browser), and clear stuck tabs when `attach` hangs (gotcha 1).

Playwright/Puppeteer scripts work against the same CDP URL:

```javascript
const { chromium } = require("playwright");
const browser = await chromium.connectOverCDP(
  "http://localhost:8080/api/profiles/<profile-id>/cdp"
);
const page = browser.contexts()[0].pages()[0];
await page.goto("https://example.com");
```

## Remote Manager on a Linux VM over SSH

The same setup runs on any Linux VM you can SSH into - a VPS, home server, or cloud instance. Size it at ~512 MB RAM per running profile plus ~1 GB for the Manager itself.

On the VM:

```bash
# install Docker (Ubuntu/Debian; skip if present)
curl -fsSL https://get.docker.com | sh

# run the Manager, localhost-bound so nothing is exposed publicly
docker run -d --restart unless-stopped --name cloakbrowser \
  -p 127.0.0.1:8080:8080 -v cloakprofiles:/data cloakhq/cloakbrowser-manager
```

On your laptop:

```bash
ssh -L 8080:localhost:8080 user@vm
```

Everything above now works unchanged: the GUI, the noVNC login flow, and the CDP endpoint all ride the same tunneled port, so `playwright-cli attach --cdp=http://localhost:8080/api/profiles/<id>/cdp` is identical to the local case. Binding to `127.0.0.1` on the VM makes the SSH tunnel the auth boundary, so `AUTH_TOKEN` stays unnecessary.

If you must expose the Manager directly instead (no tunnel), set `AUTH_TOKEN` and put it behind an HTTPS reverse proxy - but note that `playwright-cli attach` cannot inject a Bearer header on the CDP WebSocket, so a token-protected Manager needs a small local proxy in front that injects the header. Prefer the tunnel.

## Notes

- Egress IP is whatever the profile's proxy is set to (or the Docker host's IP with no proxy). Sites see that location for geo, currency, and language - configure the profile's proxy, timezone, and locale together in the Manager.
- One profile = one persistent identity. Use separate profiles for separate accounts; that is the point of the Manager.
- [CloakBrowser](https://github.com/CloakHQ/CloakBrowser) is the stealth Chromium engine; [cloakbrowser.dev](https://cloakbrowser.dev) is the project site. The Manager GUI is MIT; the CloakBrowser binary has its own license.
