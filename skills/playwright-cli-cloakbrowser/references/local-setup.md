# Local CloakBrowser Manager setup (laptop)

Run the whole stack - stealth browser, profile manager, noVNC viewer - locally in one Docker container. No auth, no tunnels, no shims: playwright-cli connects straight to the per-profile CDP endpoint.

## Requirements

- Docker 20.10+
- ~2 GB disk (image + CloakBrowser binary, downloaded on first launch)
- ~512 MB RAM per running profile

## 1. Run the Manager

```bash
docker run -d -p 8080:8080 -v cloakprofiles:/data cloakhq/cloakbrowser-manager
```

- Binds to localhost. Profiles, cookies, and session data live in the `cloakprofiles` volume and survive container updates.
- By default there is **no authentication** - fine for local use. To protect it (e.g. on a shared machine), add `-e AUTH_TOKEN=your-secret-token`; API consumers then pass `Authorization: Bearer <token>`.

Open [http://localhost:8080](http://localhost:8080) - the Manager web GUI.

## 2. Create and launch a profile

**GUI:** click New Profile, pick platform/fingerprint options (set proxy, timezone, and locale together if you need specific geo), then click **Launch**.

**API (headless):**

```bash
# create
curl -s -X POST http://localhost:8080/api/profiles \
  -H 'Content-Type: application/json' \
  -d '{"name": "agent", "platform": "macos"}'
# -> returns {"id": "<profile-id>", ...}

# launch
curl -s -X POST http://localhost:8080/api/profiles/<profile-id>/launch

# list profiles / find the id later
curl -s http://localhost:8080/api/profiles
```

## 3. The VNC live view

The noVNC viewer is built into the Manager GUI: open `http://localhost:8080`, click the running profile, and you get a live, interactive view of the browser in your own browser tab.

Use it to:

- **Log into sites once** - cookies persist in the profile, so playwright-cli drives the session logged-in afterwards.
- **Watch automation live** - the VNC view and the CDP connection share the same browser, so you can watch playwright-cli work in real time.
- **Clear stuck tabs** - close stale/heavy tabs here when `attach` hangs (see gotcha 1 in SKILL.md).

## 4. Connect playwright-cli

The CDP URL for a running profile is shown in the Manager toolbar (code icon), and always has the shape:

```
http://localhost:8080/api/profiles/<profile-id>/cdp
```

```bash
playwright-cli attach --cdp=http://localhost:8080/api/profiles/<profile-id>/cdp
playwright-cli goto https://example.com
playwright-cli snapshot
playwright-cli detach
```

`attach` connects to the profile's persistent context, so it inherits everything the profile has: fingerprint, proxy, cookies, logins.

Playwright/Puppeteer scripts work against the same URL:

```javascript
const { chromium } = require("playwright");
const browser = await chromium.connectOverCDP(
  "http://localhost:8080/api/profiles/<profile-id>/cdp"
);
const page = browser.contexts()[0].pages()[0];
await page.goto("https://example.com");
```

## Remote Manager (optional)

Running the Manager on a home server or VPS instead? Tunnel it and everything above works unchanged:

```bash
ssh -L 8080:localhost:8080 your-server
```

If the remote Manager has `AUTH_TOKEN` set, note that `playwright-cli attach` cannot inject a Bearer header on the CDP WebSocket - either tunnel to it over SSH/VPN and drop the token, or put a small local proxy in front that injects the header.

## Updating

```bash
docker pull cloakhq/cloakbrowser-manager
docker stop <container-id>
docker run -d -p 8080:8080 -v cloakprofiles:/data cloakhq/cloakbrowser-manager
```

## Links

- [CloakBrowser Manager](https://github.com/CloakHQ/CloakBrowser-Manager) - the profile manager (MIT GUI; the CloakBrowser binary has its own license)
- [CloakBrowser](https://github.com/CloakHQ/CloakBrowser) - the stealth Chromium engine
- [cloakbrowser.dev](https://cloakbrowser.dev) - website
