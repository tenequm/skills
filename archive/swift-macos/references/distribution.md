# macOS App Distribution

## Table of Contents
- Distribution Methods Overview
- Code Signing
- App Store Distribution
- Developer ID Distribution
- Notarization
- Notarization Gotchas
- Sandboxing
- Hardened Runtime
- Universal Binaries
- Sparkle (Auto-Update)

## Distribution Methods

| Method | Audience | Signing | Notarization | Sandbox | Review |
|--------|----------|---------|-------------|---------|--------|
| Mac App Store | Public | Apple Distribution | Automatic | Required | Yes |
| Developer ID | Public (outside store) | Developer ID | Required | Recommended | No |
| Ad-Hoc | Internal/testing | None or Dev | Not required | No | No |
| TestFlight | Testers | Apple Distribution | Automatic | Required | Beta review |

## Code Signing

### Certificates
- **Apple Development** - For running on local devices during development
- **Apple Distribution** - For App Store and TestFlight
- **Developer ID Application** - For distribution outside the App Store
- **Developer ID Installer** - For signed `.pkg` installers

### Automatic signing (recommended)
In Xcode: Signing & Capabilities > check "Automatically manage signing". Select your team.

### Manual signing
```bash
# List identities
security find-identity -v -p codesigning

# Sign app
codesign --force --options runtime \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --timestamp \
  MyApp.app

# Verify
codesign --verify --deep --strict MyApp.app
spctl --assess --type execute MyApp.app
```

### Dev-loop gotcha: `SIGKILL (Code Signature Invalid)`

If a running signed app is killed at idle right after a rebuild (e.g. a `make run` loop that replaces the `.app` under the running process), the crash is `SIGKILL` with `EXC_CRASH (Code Signature Invalid)` - not a bug in your code. macOS validates memory-mapped code pages against the on-disk signature lazily; overwriting the bundle invalidates the pages the kernel later faults in, so it terminates the process. Quit the old instance before replacing the bundle, or launch from a copied path.

### Bare CLI binaries: set the code-signing identifier explicitly

A bundle's signing identifier defaults to its `CFBundleIdentifier`. A non-bundled Mach-O (a Rust/Go/Swift CLI shipped as one file) has none, so it gets whatever the signer falls back to - and nothing fails when that fallback is unstable.

**Symptom:** the binary is Developer ID signed, hardened, and notarized, every check passes, yet each release shows up as a new program: firewall rules (Little Snitch keys on [team + identifier](https://help.obdev.at/littlesnitch6/adv-code-identity)) re-prompt, and TCC grants and keychain ACLs likely reset. `codesign -dvvv` shows `Identifier=` changing between releases (`pond-0299b429ffb51fd1` -> `pond-34f43d0cd245ce1c`), and the designated requirement embeds it: `designated => identifier "pond-34f4..." and anchor apple generic and ...`.

**Cause:** `codesign` without `-i` derives the identifier from the file name. `rcodesign sign` without `--binary-identifier` [keeps the identifier already in the Mach-O](https://github.com/indygreg/apple-platform-rs/blob/main/apple-codesign/src/signing_settings.rs) - and the linker's automatic ad-hoc signature took cargo's intermediate filename `deps/<name>-<metadata hash>`, whose hash moves with the version and dependencies.

**Fix:** pass the identifier on every signing path, ad-hoc included. Apple: "If you're signing nonbundled code, add the `-i <BundleID>` option to set the code-signing identifier, where `<BundleID>` is the bundle ID the code would have if it had a bundle ID" ([Creating distribution-signed code for macOS](https://developer.apple.com/documentation/xcode/creating-distribution-signed-code-for-the-mac/)).

```bash
codesign --force --options runtime --timestamp -i com.example.tool \
  --sign "Developer ID Application: Your Name (TEAM_ID)" ./tool

rcodesign sign --binary-identifier com.example.tool \
  --code-signature-flags runtime --p12-file cert.p12 ./tool

# CI signature gate: fail the release if the identifier drifts
codesign -dvvv ./tool 2>&1 | grep -qx 'Identifier=com.example.tool'
```

Pick the identifier once and never change it: the switch itself costs every user one re-approval of firewall and privacy rules.

## Building an existing `.xcodeproj` from the command line

Signing an `.xcodeproj` via `xcodebuild` fails in ways that still report `BUILD SUCCEEDED`. These are the traps that cost the most time.

**`BUILD SUCCEEDED` does not mean "signed as you asked."** When the pbxproj declares an SDK-conditional identity - `CODE_SIGN_IDENTITY[sdk=macosx*] = "Apple Development"` - a command-line override can be *accepted, logged, and then ignored*. The log prints `note: Using codesigning identity override: <hash>` and the build still emits an ad-hoc-signed bundle. An `.xcconfig` setting `CODE_SIGN_IDENTITY = -` outranks both the pbxproj conditional and the command line. Two defences:

```bash
# 1. Refuse to silently fall back to ad-hoc
xcodebuild -scheme MyApp CODE_SIGNING_REQUIRED=YES ...

# 2. Never trust the build log - verify the artifact
codesign -dv --verbose=4 build/MyApp.app 2>&1 | grep -E 'Authority|Signature|flags'
```

`Signature=adhoc` in that output means unsigned for every practical purpose: no Developer ID, no notarization, no stable TCC identity.

**Bracketed build settings cannot be passed on the command line at all.** `xcodebuild` splits each `SETTING=VALUE` argument on the *first* `=`, so `CODE_SIGN_IDENTITY[sdk=macosx*]=X` parses as the setting name `CODE_SIGN_IDENTITY[sdk` with the value `macosx*]=X`. To change a conditional identity, edit the pbxproj or supply an `.xcconfig` - there is no CLI form.

**Match the identity by name, not by prefix.** Scripts that auto-detect a certificate with `security find-identity | grep "Apple Development: "` can never match a `Developer ID Application` certificate - different certificate class, and no environment variable or rename fixes it. Match on the exact keychain name you intend to use, or build ad-hoc and re-sign the bundle inside-out (frameworks -> dylibs -> XPC services -> app).

**Build from the resolved real path.** Building through a symlinked source directory corrupts Xcode's build database: you get `Stale file ... outside of the allowed root paths` and a module-emit failure, often with **no `error:` line anywhere in the log**. Delete the derived-data directory and rebuild from the fully resolved path (`cd "$(realpath .)"`).

**Signature-class changes cost one round of TCC re-prompts.** Switching a bundle between ad-hoc and Developer ID changes its code identity, so the system asks for screen-recording and microphone consent once more. That is expected. Also expected: `spctl -a -vv` reporting `rejected / Unnotarized Developer ID` for a locally signed build - Gatekeeper acts on the quarantine attribute, which `xattr -cr MyApp.app` clears.

**Moving a signed `.app` preserves its TCC grants and preferences.** TCC keys off code-signing identifier (the bundle ID, for a bundle) plus signature, not path, so relocating a bundle does not reset permissions. The safe replace idiom is quit the app, `ditto` the new bundle into place, then `xattr -cr` it.

## App Store Distribution

### Requirements
- Active Apple Developer Program membership ($99/year)
- App Store Connect listing with metadata, screenshots
- **Since April 28, 2026**: uploads to App Store Connect must be built with **Xcode 26 and the iOS 26 / iPadOS 26 / tvOS 26 / visionOS 26 / watchOS 26 SDK**. Pure macOS apps are **not** in Apple's list as of 2026-04-24; Mac Catalyst and Designed-for-iPad builds inherit the iOS 26 SDK requirement. Source: https://developer.apple.com/news/?id=ueeok6yw and https://developer.apple.com/news/upcoming-requirements
- Sandbox entitlement required
- App Review compliance
- Audit `PrivacyInfo.xcprivacy` against the current required-reason APIs list (https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api) — Apple updates it periodically

### Workflow
1. Archive: Product > Archive in Xcode
2. Validate: Window > Organizer > Validate App
3. Upload: Distribute App > App Store Connect
4. Submit for review in App Store Connect

### ExportOptions.plist (for CI)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store-connect</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>destination</key>
    <string>upload</string>
    <key>signingStyle</key>
    <string>automatic</string>
</dict>
</plist>
```

### CI build & upload
```bash
# Build archive
xcodebuild archive \
  -project MyApp.xcodeproj \
  -scheme MyApp \
  -archivePath build/MyApp.xcarchive \
  -destination "generic/platform=macOS"

# Export and upload
xcodebuild -exportArchive \
  -archivePath build/MyApp.xcarchive \
  -exportPath build/export \
  -exportOptionsPlist ExportOptions.plist

# Or upload directly. Use notarytool - NOT `altool --upload-app`:
# the notary service stopped accepting altool uploads on 2023-11-01,
# and the flag is absent from Xcode 26.6's altool --help.
xcrun notarytool submit build/export/MyApp.pkg \
  --key AuthKey_KEYID.p8 \
  --key-id KEY_ID \
  --issuer ISSUER_ID \
  --wait
```

### Notarize-then-export in one archive flow

`xcodebuild` can export an already-notarized archive directly, which avoids re-signing between notarization and distribution:

```bash
xcodebuild -exportNotarizedApp \
  -archivePath build/MyApp.xcarchive \
  -exportPath build/notarized
```

## Developer ID Distribution

For distributing outside the Mac App Store:

### Build and sign
```bash
xcodebuild archive \
  -scheme MyApp \
  -archivePath MyApp.xcarchive

xcodebuild -exportArchive \
  -archivePath MyApp.xcarchive \
  -exportPath ./export \
  -exportOptionsPlist DevIDExport.plist
```

DevIDExport.plist:
```xml
<dict>
    <key>method</key>
    <string>developer-id</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>signingStyle</key>
    <string>automatic</string>
</dict>
```

### Create DMG
```bash
# Create DMG with hdiutil
hdiutil create -volname "MyApp" -srcfolder ./export/MyApp.app \
  -ov -format UDZO MyApp.dmg

# Or use create-dmg for pretty DMGs
# brew install create-dmg
create-dmg \
  --volname "MyApp" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "MyApp.app" 175 120 \
  --hide-extension "MyApp.app" \
  --app-drop-link 425 120 \
  MyApp.dmg ./export/MyApp.app
```

## Notarization

Required for all Developer ID-signed apps (since macOS 10.15):

```bash
# Submit for notarization
xcrun notarytool submit MyApp.dmg \
  --apple-id your@email.com \
  --team-id TEAM_ID \
  --password @keychain:AC_PASSWORD \
  --wait

# Check status
xcrun notarytool info SUBMISSION_ID \
  --apple-id your@email.com \
  --team-id TEAM_ID \
  --password @keychain:AC_PASSWORD

# View log on failure
xcrun notarytool log SUBMISSION_ID \
  --apple-id your@email.com \
  --team-id TEAM_ID \
  --password @keychain:AC_PASSWORD

# Staple ticket to app/DMG
xcrun stapler staple MyApp.dmg

# Verify
xcrun stapler validate MyApp.dmg
spctl --assess --type open --context context:primary-signature MyApp.dmg
```

### Store credentials in keychain
```bash
xcrun notarytool store-credentials "AC_PASSWORD" \
  --apple-id your@email.com \
  --team-id TEAM_ID \
  --password "app-specific-password"

# Then use:
xcrun notarytool submit MyApp.dmg \
  --keychain-profile "AC_PASSWORD" --wait
```

### Using API keys (recommended for CI)
```bash
xcrun notarytool submit MyApp.dmg \
  --key AuthKey_KEYID.p8 \
  --key-id KEY_ID \
  --issuer ISSUER_UUID \
  --wait
```

## Notarization Gotchas

### notarytool 403 "A required agreement is missing or has expired"

A 403 from `xcrun notarytool submit` is almost never a code-signing problem - it's an Apple agreement that needs acceptance. Two flavors, both easy to miss:

**(a) Apple Developer Program License Agreement.** Must be accepted by the **Account Holder** (not team admin, not developer). Log in at `developer.apple.com/account` with the Account Holder's Apple ID; a banner prompts acceptance.

**(b) Digital Services Act (DSA) banner on App Store Connect.** Even when distributing via Developer ID + GitHub Releases (nothing on the App Store), an unanswered DSA compliance banner at `appstoreconnect.apple.com` can hold the account in incomplete state and cause notarytool to 403. Click "Business → Agreements, Tax, and Banking" and complete any outstanding prompts. For non-App-Store distribution, "I'm not a trader under the DSA or I don't plan to distribute in the EU" is the appropriate answer.

**Propagation lag**: after accepting, notarytool may still 403 for several minutes. Don't retry in a tight loop - check both `developer.apple.com/account` and the "Agreements, Tax, and Banking" page for any remaining unsigned items, then wait 5-10 minutes before resubmitting.

### TCC is keyed by code-signature CDHash - reinstalls can degrade without error

TCC grants are keyed by the app's CDHash + code-signing identifier (bundle ID for an app; see the bare-CLI section above for non-bundled tools) + Developer ID. When a release-channel app is replaced via a force-recursive delete of `/Applications/App.app` followed by `cp -R ./export/App.app /Applications/` (common in `make install` / CI workflows), TCC may remember the grant **but deliver degraded content** - permission reads as authorized, capture APIs start without error, buffers flow at zero amplitude. Direct-reading `~/Library/Application Support/com.apple.TCC/TCC.db` is blocked by SIP, so there is no programmatic recovery.

The user-visible remediation: System Settings → Privacy & Security → toggle the permission off, then on again. To prevent the issue:
- Prefer in-place overwrite (let the OS handle inode swap) over force-recursive replace (rm&#8209;rf + cp&#8209;R).
- `killall App` before replacing the bundle - otherwise the still-running process keeps executing from its unlinked inode and `open -a` activates the stale instance instead of launching the new one.
- For dev scripts, consider `tccutil reset ScreenCapture $BUNDLE_ID` after install so the user gets a fresh prompt rather than a degraded cached grant.

### Nested framework bundles must be deep-signed

Frameworks like Sparkle contain nested bundles (`Updater.app`, `Installer.xpc`, `Downloader.xpc`). Notarization rejects if these aren't individually signed with Developer ID + secure timestamp. Sign from inside out:

```bash
# Sign all nested bundles inside Sparkle
find "MyApp.app/Contents/Frameworks/Sparkle.framework" \
    -type d \( -name "*.app" -o -name "*.xpc" \) | while read f; do
    codesign --force --options runtime --sign "$SIGN_ID" --timestamp "$f"
done
# Then the framework itself
codesign --force --options runtime --sign "$SIGN_ID" --timestamp \
    "MyApp.app/Contents/Frameworks/Sparkle.framework"
# Then the main app
codesign --force --options runtime --sign "$SIGN_ID" --timestamp \
    --entitlements entitlements.plist "MyApp.app"

# Verify before submitting
codesign --verify --deep --strict MyApp.app
```

### Missing intermediate certificate

After importing a Developer ID Application certificate, `security find-identity -v -p codesigning` may show no valid identity. Apple's G2 intermediate certificate must be downloaded and installed separately into the keychain.

### First-time Developer ID accounts may stall

First notarization submissions from a new Developer ID can sit "In Progress" for 72+ hours. If signing were wrong, Apple rejects within minutes as `Invalid`. "In Progress" for days means the submission passed validation and is in Apple's review queue. File a Technical Support Incident (TSI) if this happens.

### Gatekeeper bypass for non-notarized builds

Developer ID-signed but non-notarized apps show Gatekeeper warnings. **The Control-click (right-click) > Open override was removed in macOS Sequoia and is still gone in Tahoe 26** - do not tell users to use it.

The only supported path now: try to open the app once (so the block is registered), then System Settings > Privacy & Security > scroll down > **Open Anyway** > confirm. Apple's [current documentation](https://support.apple.com/en-us/102445) describes this flow exclusively. The app is then saved as an exception and opens by double-click thereafter.

### Sparkle EdDSA signing

Sparkle uses its own EdDSA key pair (separate from Apple code signing) to verify update integrity. Sign DMGs with Sparkle's `sign_update` tool:

```bash
.build/artifacts/sparkle/Sparkle/bin/sign_update MyApp-1.0.0.dmg
```

The appcast.xml contains the EdDSA signature and is generated per-release.

## Sandboxing

Required for Mac App Store. Configured via entitlements:

```xml
<!-- MyApp.entitlements -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <false/>
</dict>
</plist>
```

Common sandbox entitlements:
- `files.user-selected.read-write` - Access user-selected files
- `files.downloads.read-write` - Access Downloads folder
- `network.client` - Outbound network connections
- `network.server` - Incoming connections (server)
- `device.camera` - Camera access
- `device.microphone` - Microphone access (sandbox side)
- `personal-information.calendars` - Calendar access
- `personal-information.contacts` - Contacts access

## Hardened Runtime

Required for notarization. Enable in Xcode: Signing & Capabilities > + Capability > Hardened Runtime.

Resource access entitlements (only enable if needed):
- `com.apple.security.device.audio-input` - Microphone and audio input via Core Audio
- `com.apple.security.device.camera` - Camera access

Runtime exception entitlements (weaken security - use sparingly):
- `cs.disable-library-validation` - Load third-party frameworks/plugins with different Team ID
- `cs.allow-unsigned-executable-memory` - Allow unsigned executable memory
- `cs.allow-jit` - Allow JIT compilation

**For capture apps**: microphone access needs BOTH sandbox (`device.microphone`) AND hardened runtime (`device.audio-input`) entitlements if sandboxed. Screen recording needs NO entitlement - it's governed by TCC runtime permission only.

### Capture app entitlements

Non-sandboxed (Developer ID):

```xml
<dict>
    <key>com.apple.security.device.audio-input</key>
    <true/>
</dict>
```

Sandboxed (App Store):

```xml
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.device.microphone</key>
    <true/>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
```

Info.plist (required for microphone):

```xml
<key>NSMicrophoneUsageDescription</key>
<string>Record audio alongside screen capture.</string>
```

### Persistent Content Capture

`com.apple.developer.persistent-content-capture` bypasses macOS 15+ recurring screen recording prompts. Intended for VNC/remote desktop apps. Requires Apple approval and provisioning profile - request through Apple Developer entitlement request form.

## Universal Binaries

Support both Apple Silicon and Intel:

```bash
# Build universal
xcodebuild -scheme MyApp \
  -destination "generic/platform=macOS" \
  ARCHS="arm64 x86_64" \
  ONLY_ACTIVE_ARCH=NO

# Verify architectures
lipo -info MyApp.app/Contents/MacOS/MyApp
# Output: Architectures in the fat file: arm64 x86_64

# Create universal from two builds
lipo -create MyApp-arm64 MyApp-x86_64 -output MyApp-universal
```

In Xcode: Build Settings > Architectures > Standard Architectures (Apple Silicon, Intel)

## Sparkle (Auto-Update)

For Developer ID apps, use Sparkle for auto-updates:

```swift
// Package.swift dependency
.package(url: "https://github.com/sparkle-project/Sparkle", from: "2.0.0")

// In App
import Sparkle

@main
struct MyApp: App {
    private let updaterController = SPUStandardUpdaterController(
        startingUpdater: true,
        updaterDelegate: nil,
        userDriverDelegate: nil
    )

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .commands {
            CommandGroup(after: .appInfo) {
                CheckForUpdatesView(updater: updaterController.updater)
            }
        }
    }
}
```

## Notarization rejections: check these first

`com.apple.security.get-task-allow` is the single most common cause. It is the debug entitlement Xcode injects into Debug builds; if it survives into the archive you submit, the notary service rejects the upload. Verify before submitting:

```bash
codesign -d --entitlements - --xml build/export/MyApp.app | plutil -p -
```

If `get-task-allow` appears with value `true`, you archived a Debug configuration or a custom entitlements file carries it. Strip it from the Release entitlements.

Other frequent blockers:

- Hardened Runtime not enabled on every executable in the bundle (not just the main one).
- A nested binary signed with a different Team ID, or left unsigned.
- **Plug-in entitlement inheritance**: "Shared libraries, frameworks, and in-process plug-ins inherit the entitlements of their host executable." The host app must declare every entitlement its plug-ins need - a plug-in cannot add its own.

Reference: [Resolving common notarization issues](https://developer.apple.com/documentation/security/resolving-common-notarization-issues).

## Enhanced Security capability (Xcode 26+)

Xcode 26 added an **Enhanced Security** capability enabling additional runtime and compile-time protections - pointer authentication, hardened heap, memory tagging - via the `com.apple.security.hardened-process.*` entitlement family.

The entitlement schema changed again in Xcode 26.4: `-version` became `-version-string` and `-platform-restrictions` became `-platform-restrictions-string`. If you hand-maintain an entitlements plist rather than using the capability UI, re-check the key spellings against the [Security entitlements reference](https://developer.apple.com/documentation/bundleresources/security-entitlements) when moving between Xcode versions.

## Installer packages

For apps that need an installer rather than a drag-to-Applications DMG:

```bash
pkgbuild --root build/export/MyApp.app \
  --identifier com.example.myapp \
  --version 1.0.0 \
  --install-location /Applications/MyApp.app \
  build/MyApp-component.pkg

productbuild --distribution Distribution.xml \
  --package-path build \
  build/MyApp.pkg

productsign --sign "Developer ID Installer: Your Name (TEAMID)" \
  build/MyApp.pkg build/MyApp-signed.pkg
```

Note the identity is **Developer ID Installer**, a different certificate from the **Developer ID Application** identity used for the app itself.

Useful `notarytool` subcommands beyond `submit`:

```bash
xcrun notarytool history --key ... --key-id ... --issuer ...
xcrun notarytool log <submission-id> --key ... --key-id ... --issuer ...
xcrun notarytool info <submission-id> -f json --key ... --key-id ... --issuer ...
```

`--s3-acceleration` speeds up large uploads. `stapler validate <path>` verifies a stapled ticket.

## Homebrew cask as a second install channel

A signed, notarized Mac app can ship through a Homebrew tap alongside the DMG. Practical constraints, in the order they usually bite:

- **Pick a globally unique cask token.** Tap CI (`brew test-bot --only-tap-syntax`) fails if your token collides with one in homebrew-core, and renaming later orphans every existing install.
- **If you must rename, ship `cask_renames.json`** in the tap so `brew update` migrates existing installs. `tap_migrations.json` is for cross-tap moves and will not do this.
- **Set `auto_updates true`** when the app self-updates via Sparkle, so Homebrew does not fight the in-app updater. Add a `livecheck` block so version bumps are detectable.
- **`depends_on macos:` cannot express a point release** (e.g. 26.1). Enforce a precise minimum in the app at launch and treat the cask constraint as approximate.
- **Reinstalling over an app already in `/Applications` fails** without `--force`.
- Run `brew style` and `brew audit --cask` before pushing; generated casks commonly trip on a redundant `version` line.
