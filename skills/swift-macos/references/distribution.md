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

## App Store Distribution

### Requirements
- Active Apple Developer Program membership ($99/year)
- App Store Connect listing with metadata, screenshots
- **Starting April 28, 2026**: uploads to App Store Connect must be built with **Xcode 26 and the iOS 26 / iPadOS 26 / tvOS 26 / visionOS 26 / watchOS 26 SDK**. Pure macOS apps are **not** in Apple's list as of 2026-04-24; Mac Catalyst and Designed-for-iPad builds inherit the iOS 26 SDK requirement. Source: https://developer.apple.com/news/?id=ueeok6yw and https://developer.apple.com/news/upcoming-requirements
- Sandbox entitlement required
- App Review compliance
- Audit `PrivacyInfo.xcprivacy` against the current required-reason APIs list (https://developer.apple.com/documentation/bundleresources/privacy_manifest_files/describing_use_of_required_reason_api) — Apple updates it periodically

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

# Or upload directly
xcrun altool --upload-app \
  -f build/export/MyApp.pkg \
  -t macos \
  --apiKey KEY_ID \
  --apiIssuer ISSUER_ID
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

TCC grants are keyed by the app's CDHash + bundle ID + Developer ID. When a release-channel app is replaced via a force-recursive delete of `/Applications/App.app` followed by `cp -R ./export/App.app /Applications/` (common in `make install` / CI workflows), TCC may remember the grant **but deliver degraded content** - permission reads as authorized, capture APIs start without error, buffers flow at zero amplitude. Direct-reading `~/Library/Application Support/com.apple.TCC/TCC.db` is blocked by SIP, so there is no programmatic recovery.

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

Developer ID-signed but non-notarized apps show Gatekeeper warnings. Users can bypass: right-click the app > Open > click "Open" in the dialog (one-time). Or: System Settings > Privacy & Security > "Open Anyway".

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
