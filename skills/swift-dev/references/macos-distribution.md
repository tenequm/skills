# macOS Distribution

Shipping a Mac app: Developer ID + notarization, Mac App Store, sandbox and hardened runtime entitlements, nested signing, Sparkle, and the `xcodebuild` signing traps.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: flags checked against `xcodebuild -help`, `notarytool --help` (1.1.3), `altool --help` (27.0.5), `stapler`, `codesign`, `spctl`; ad-hoc signed and inspected a test bundle with the `codesign` commands below; built unsigned `pkgbuild`/`productbuild` packages; reproduced the bracketed-setting parse bug; built the Sparkle snippet against Sparkle 2.10.0. Developer ID signing, notarization and uploads were not run (no credentials used). 2026-10-13: DMG signing and `find-identity` guidance re-read from Apple's packaging guide; `notarytool store-credentials --help`, `man spctl` and the Sparkle 2.10.0 release notes re-checked. 2026-10-24 (Xcode 27.1): the bare-CLI identifier commands, the `-R` requirement check and `strip` invalidating a signature run ad hoc on a scratch binary.

## Contents
- Choosing a channel
- Certificates
- Developer ID: archive, export, DMG
- Notarization
- Notarization rejections and 403s
- Mac App Store
- Sandbox and hardened runtime entitlements
- Nested code and Sparkle
- `xcodebuild` signing traps
- TCC, reinstalls and Gatekeeper
- Architectures, Enhanced Security, installers, Homebrew

## Choosing a channel

| Channel | Certificate | Notarization | Sandbox | Review |
|---|---|---|---|---|
| Developer ID (DMG, zip, Homebrew) | Developer ID Application | Required | Optional | No |
| Mac App Store / TestFlight | Apple Distribution (+ Mac Installer Distribution for the .pkg) | Not needed | Required | Yes |
| Local only | Apple Development or ad hoc (`-`) | No | No | No |

Default to Developer ID for tools that need screen capture, accessibility, Core Audio taps or other APIs the sandbox blocks. For iOS distribution see `ios-distribution.md`; a Developer ID certificate cannot sign iOS apps.

## Certificates

Per Apple's [certificate types](https://developer.apple.com/help/account/certificates/certificates-overview): **Developer ID Application** signs Mac apps distributed outside the Mac App Store, **Developer ID Installer** signs `.pkg` installers outside the store, **Apple Distribution** covers App Store/TestFlight on every platform, **Apple Development** runs your own builds on devices. Only the Account Holder can create Developer ID certificates; Account Holder or Admin create the other distribution certificates.

```bash
security find-identity -v -p codesigning   # Developer ID Application, Apple Development/Distribution
security find-identity -v                  # also lists Developer ID Installer identities
```

`-p codesigning` filters out installer identities (Apple: "Don't use the `-p codesigning` option ... Installer-signing identities are different from code-signing identities"), so use plain `-v` when looking for the `productsign` identity.

If a freshly imported Developer ID certificate does not show up as a valid identity, the Apple Developer ID G2 intermediate is missing from the keychain - install it from the [Apple PKI page](https://www.apple.com/certificateauthority/).

**The original Developer ID Sub-CA expires on February 1, 2027** ([Apple](https://developer.apple.com/news/?id=w4atic4c)). After that date, `.pkg` files signed with an affected certificate no longer install. Re-issue Developer ID certificates against the G2 Sub-CA ("When prompted for a Developer ID Certificate Intermediary, select G2 Sub-CA") and re-sign installers before then.

## Developer ID: archive, export, DMG

```bash
xcodebuild archive -scheme MyApp -destination 'generic/platform=macOS' \
  -archivePath build/MyApp.xcarchive
xcodebuild -exportArchive -archivePath build/MyApp.xcarchive \
  -exportPath build/export -exportOptionsPlist DevID.plist
hdiutil create -volname MyApp -srcfolder build/export/MyApp.app -ov -format UDZO build/MyApp.dmg
codesign -s "Developer ID Application: Your Name (TEAMID)" --timestamp -i com.example.MyApp.dmg build/MyApp.dmg
```

Sign the disk image itself, with the Developer ID Application identity and its own identifier (the bundle ID plus a unique suffix): Apple's [packaging guide](https://developer.apple.com/documentation/xcode/packaging-mac-software-for-distribution) says "Sign your code, and sign each nested container that supports signing". Without it, the `spctl --context context:primary-signature` check below has no signature to assess. With nested containers (app in a `.pkg` on a DMG), sign every layer and notarize only the outermost.

`DevID.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>developer-id</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>signingStyle</key>
    <string>automatic</string>
</dict>
</plist>
```

Xcode 27 export `method` values: `app-store-connect`, `release-testing`, `enterprise`, `debugging`, `developer-id`, `mac-application`, `validation`. The old names `app-store`, `ad-hoc` and `development` are deprecated aliases. `xcodebuild -help` prints every ExportOptions key.

Signing outside Xcode (inside-out, never `--deep` for signing - `man codesign` marks it deprecated for signing since macOS 13):

```bash
codesign --force --options runtime --timestamp \
  --entitlements MyApp.entitlements \
  --sign "Developer ID Application: Your Name (TEAMID)" MyApp.app
codesign --verify --strict --verbose=2 MyApp.app
codesign -dv --verbose=4 MyApp.app 2>&1 | grep -E 'Authority|Signature|flags|TeamIdentifier'
```

`--timestamp` (secure timestamp) and `--options runtime` (hardened runtime) are both required for notarization.

### Bare CLI binaries: set the code-signing identifier

A bundle's signing identifier defaults to its `CFBundleIdentifier`. A non-bundled Mach-O (a Swift, Rust or Go CLI shipped as one file) has none, so it gets whatever the signer falls back to, and nothing fails when that fallback moves. `codesign` without `-i` uses the file name; `rcodesign sign` without `--binary-identifier` [keeps the identifier already in the Mach-O](https://github.com/indygreg/apple-platform-rs/blob/main/apple-codesign/src/signing_settings.rs), which for cargo is the linker's ad-hoc signature over `deps/<name>-<hash>`. The designated requirement embeds the identifier (`designated => identifier "tool-34f4..." and anchor apple generic and ...`), so a new identifier per release makes every release a new program: firewall rules re-prompt and TCC grants and keychain ACLs reset, while the Developer ID, hardened-runtime and notarization checks all pass. macOS 27 also refuses to grant a process without a bundle ID access to other teams' app data containers in the Files & Folders pane (release notes, 184660124).

Apple: "If you're signing nonbundled code, add the `-i <BundleID>` option to set the code-signing identifier" ([Creating distribution-signed code for macOS](https://developer.apple.com/documentation/xcode/creating-distribution-signed-code-for-the-mac/)). Pass it on every signing path, ad hoc included, and assert it in CI - a gate that checks only Authority and flags misses a drifting identifier:

```bash
codesign --force --options runtime --timestamp -i com.example.tool \
  --sign "Developer ID Application: Your Name (TEAMID)" ./tool

rcodesign sign --binary-identifier com.example.tool \
  --code-signature-flags runtime --p12-file cert.p12 ./tool

# CI gate: fail the release if the identity drifts
codesign -dvvv ./tool 2>&1 | grep -Fqx 'Identifier=com.example.tool'
codesign --verify -R='identifier "com.example.tool" and anchor apple generic and certificate leaf[subject.OU] = "TEAMID"' ./tool
```

- **Strip before signing, never after.** Xcode's `strip` on a signed binary warns and leaves `invalid signature (code or signature have been modified)` (verified); some build systems' default strip phase (Nix's is one) re-signs the result ad hoc with the file name as identifier, silently dropping the Developer ID signature. Disable the post-build strip on Darwin or sign after it.
- Pick the identifier once: changing it costs every user one re-approval of firewall and privacy rules.

## Notarization

Store credentials once, then submit by profile name. Prefer a team App Store Connect API key over an Apple ID. The sources disagree on individual keys: Apple's [API key page](https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api) says they cannot use `notarytool`, while `notarytool store-credentials --help` (1.1.3) documents them ("Required for Team API Keys. Do not provide for Individual API Keys." for `--issuer`) - a team key avoids the question. Every program role except Finance/Marketing/Sales/Customer Support may notarize ([roles](https://developer.apple.com/help/account/access/roles)).

```bash
xcrun notarytool store-credentials notary \
  --key AuthKey_KEYID.p8 --key-id KEYID --issuer ISSUER_UUID
# or: --apple-id you@example.com --team-id TEAMID (prompts for an app-specific password)

xcrun notarytool submit build/MyApp.dmg --keychain-profile notary --wait --timeout 2h
xcrun stapler staple build/MyApp.dmg
xcrun stapler validate build/MyApp.dmg
spctl --assess --type open --context context:primary-signature -vv build/MyApp.dmg
```

For a bare app, zip it (`ditto -c -k --keepParent MyApp.app MyApp.zip`), submit the zip, then staple the `.app` - a zip cannot be stapled. `stapler` accepts disk images, signed bundles and flat installer packages.

Follow-up commands (all take `--keychain-profile`): `notarytool info <id>`, `notarytool wait <id>`, `notarytool history`, `notarytool log <id> [out.json]`. `--webhook <url>` posts status; S3 transfer acceleration is on by default.

`notarytool` is the only notarization client. The notary service stopped accepting `altool` and Xcode 13 uploads on [2023-11-01](https://developer.apple.com/news/upcoming-requirements/?id=11012023a). `altool` remains an App Store Connect upload tool, not a notarization tool.

Unverified: `-exportOptionsPlist` with `method` `developer-id` and `destination` `upload` submits the export to the notary service, after which `xcodebuild -exportNotarizedApp -archivePath ... -exportPath ...` exports the stapled app (both flags exist in `xcodebuild -help`; the round trip was not run).

## Notarization rejections and 403s

Check these first, in order:

1. **`com.apple.security.get-task-allow`** - the debug entitlement Xcode injects into Debug builds. Present in the submitted binary means rejection. Inspect what actually shipped:
   ```bash
   codesign -d --entitlements - --xml build/export/MyApp.app | plutil -p -
   ```
   `"com.apple.security.get-task-allow" => true` means you archived Debug or a custom entitlements file carries it.
2. Hardened runtime missing on any executable in the bundle (helpers, XPC services, embedded CLIs), not just the main one.
3. A nested binary unsigned, ad hoc, missing a secure timestamp, or signed by another team.
4. Plug-in entitlements: "Shared libraries, frameworks, and in-process plug-ins inherit the entitlements of their host executable" - the host must declare everything its plug-ins need. See [Resolving common notarization issues](https://developer.apple.com/documentation/security/resolving-common-notarization-issues).

**403 "A required agreement is missing or has expired"** is not a signing problem:
- The Account Holder must accept the current Apple Developer Program License Agreement at [developer.apple.com/account](https://developer.apple.com/account) - Admins cannot.
- An unanswered Digital Services Act (trader status) prompt under Business in [App Store Connect](https://appstoreconnect.apple.com) can block notarization even for apps never sold in the store. For non-store distribution, declare non-trader.
- After accepting, the 403 can persist for several minutes. Wait 5-10 minutes before resubmitting instead of retrying in a loop.

**First submissions on a new account can sit "In Progress" for days.** Bad signatures come back `Invalid` within minutes, so a long "In Progress" means the submission passed validation and is queued. Open a developer support request if it exceeds ~72 hours.

## Mac App Store

Requirements: App Store Connect app record, App Sandbox, App Review compliance, an up-to-date `PrivacyInfo.xcprivacy` (audit it against the [required-reason API list](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api)). Per Apple's [upload builds](https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds) table, Mac apps have no minimum build-Xcode requirement, while iOS/iPadOS targets (including Mac Catalyst and Designed for iPad) must be built with Xcode 26 or later. Apple also requires that [no file in a macOS upload carries `com.apple.quarantine`](https://developer.apple.com/news/upcoming-requirements/) - run `xattr -cr MyApp.app` on anything copied from a download before packaging.

```xml
<!-- AppStore.plist -->
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
```

```bash
xcodebuild -exportArchive -archivePath build/MyApp.xcarchive \
  -exportPath build/export -exportOptionsPlist AppStore.plist \
  -allowProvisioningUpdates \
  -authenticationKeyPath "$KEY_P8" -authenticationKeyID "$KEY_ID" -authenticationKeyIssuerID "$ISSUER_ID"
```

`destination` `upload` sends the build straight to App Store Connect; `export` writes the signed `.pkg` so you can upload it yourself:

```bash
xcrun altool --upload-package build/export/MyApp.pkg --api-key "$KEY_ID" --api-issuer "$ISSUER_ID" --wait
```

`altool` finds `AuthKey_<KEY_ID>.p8` in `./private_keys`, `~/private_keys`, `~/.private_keys`, `~/.appstoreconnect/private_keys` or `$API_PRIVATE_KEYS_DIR`; `--p8-file-path` points at it directly. Do not use `notarytool` for App Store uploads - it only talks to the notary service. Key roles and the TestFlight flow are the same as iOS: see `ios-devices-and-signing.md` and `ios-distribution.md`.

## Sandbox and hardened runtime entitlements

Sandbox (required for the Mac App Store, optional for Developer ID):

```xml
<key>com.apple.security.app-sandbox</key><true/>
<key>com.apple.security.files.user-selected.read-write</key><true/>
<key>com.apple.security.network.client</key><true/>
```

Common sandbox keys: `files.user-selected.read-write`, `files.downloads.read-write`, `network.client`, `network.server`, `device.camera`, `device.microphone`, `personal-information.calendars`, `personal-information.contacts` (all under `com.apple.security.`).

Hardened runtime resource entitlements: `com.apple.security.device.audio-input`, `com.apple.security.device.camera`. Runtime exceptions weaken the process - add only with a concrete reason: `com.apple.security.cs.disable-library-validation` (load plug-ins signed by another team), `cs.allow-jit`, `cs.allow-unsigned-executable-memory`.

**Capture apps:** a sandboxed app recording the mic needs both `device.microphone` (sandbox) and `device.audio-input` (hardened runtime), plus `NSMicrophoneUsageDescription`. A non-sandboxed Developer ID app needs only `device.audio-input`. Screen recording has no entitlement - it is TCC consent only (see `macos-screencapturekit.md`).

`com.apple.developer.persistent-content-capture` suppresses the recurring macOS 15+ screen-recording re-prompts. It is meant for VNC/remote-desktop apps, needs Apple approval via the entitlement request form, and a provisioning profile.

## Nested code and Sparkle

Notarization rejects any nested `.app`, `.xpc`, helper tool or framework that is not individually signed with your Developer ID, hardened runtime and a secure timestamp. Archive + export handles this; manual re-signing must go inside-out. Sparkle 2's [own recipe](https://sparkle-project.org/documentation/sandboxing/#code-signing), plus `--timestamp` for notarization:

```bash
F="MyApp.app/Contents/Frameworks/Sparkle.framework"
codesign -f -s "$SIGN_ID" -o runtime --timestamp "$F/Versions/B/XPCServices/Installer.xpc"
codesign -f -s "$SIGN_ID" -o runtime --timestamp --preserve-metadata=entitlements "$F/Versions/B/XPCServices/Downloader.xpc"
codesign -f -s "$SIGN_ID" -o runtime --timestamp "$F/Versions/B/Autoupdate"
codesign -f -s "$SIGN_ID" -o runtime --timestamp "$F/Versions/B/Updater.app"
codesign -f -s "$SIGN_ID" -o runtime --timestamp "$F"
codesign -f -s "$SIGN_ID" -o runtime --timestamp --entitlements MyApp.entitlements MyApp.app
codesign --verify --deep --strict MyApp.app
```

`--deep` is fine for `--verify`; never add it to `OTHER_CODE_SIGN_FLAGS` - it re-signs the Downloader XPC service with the wrong entitlements.

Sparkle in SwiftUI (Sparkle 2.10 via SPM):

```swift
import SwiftUI
import Sparkle

@main
struct MyApp: App {
    private let updaterController = SPUStandardUpdaterController(
        startingUpdater: true, updaterDelegate: nil, userDriverDelegate: nil
    )

    var body: some Scene {
        WindowGroup { ContentView() }
            .commands {
                CommandGroup(after: .appInfo) {
                    Button("Check for Updates...") { updaterController.updater.checkForUpdates() }
                        .disabled(!updaterController.updater.canCheckForUpdates)
                }
            }
    }
}
```

[Sparkle 2.10.0](https://github.com/sparkle-project/Sparkle/releases/tag/2.10.0) requires macOS 12 or later ("due to Xcode 27 dropping support for deploying to older OS versions") and drops CocoaPods. If you write the appcast by hand, add `<sparkle:minimumSystemVersion>12.0</sparkle:minimumSystemVersion>` to each `<item>`.

Sparkle verifies updates with its own EdDSA key, separate from Apple signing. With SPM the tools live in `.build/artifacts/sparkle/Sparkle/bin/` (`generate_keys`, `sign_update`, `generate_appcast`): run `sign_update MyApp-1.0.0.dmg` per release and put the signature into `appcast.xml`, or let `generate_appcast` do both.

## `xcodebuild` signing traps

**`BUILD SUCCEEDED` does not mean "signed as you asked."** With an SDK-conditional identity in the pbxproj (`CODE_SIGN_IDENTITY[sdk=macosx*] = "Apple Development"`), a command-line override can be logged (`note: Using codesigning identity override: <hash>`) and still produce an ad-hoc bundle. An `.xcconfig` with `CODE_SIGN_IDENTITY = -` outranks both. Defend twice:

```bash
xcodebuild -scheme MyApp CODE_SIGNING_REQUIRED=YES build
codesign -dv --verbose=4 build/MyApp.app 2>&1 | grep -E 'Authority|Signature|flags'
```

`Signature=adhoc` means no Developer ID, no notarization, no stable TCC identity.

**Bracketed settings cannot be passed on the command line.** `xcodebuild` splits `SETTING=VALUE` on the first `=`: `'CODE_SIGN_IDENTITY[sdk=iphoneos*]=Foo'` ends up as `CODE_SIGN_IDENTITY = iphoneos*]=Foo` in `-showBuildSettings` (reproduced on Xcode 27). Change conditional identities in the project or an `.xcconfig`.

**Match identities by exact name.** `security find-identity | grep "Apple Development: "` never matches a `Developer ID Application` certificate - different certificate class. Match the full keychain name, or build ad hoc and re-sign inside-out.

**Build from the resolved real path.** Building through a symlinked source directory corrupts the build database: `Stale file ... outside of the allowed root paths` and a module-emit failure, often with no `error:` line. Delete derived data and build from `"$(realpath .)"`.

**`SIGKILL (Code Signature Invalid)` at idle after a rebuild** is not your bug. The kernel validates code pages lazily against the on-disk signature; replacing the `.app` under a running process invalidates pages it later faults in. Quit the old instance before replacing the bundle.

## TCC, reinstalls and Gatekeeper

- Switching a bundle between ad hoc and Developer ID changes its code identity: expect one more round of screen-recording/microphone prompts.
- TCC keys off the code-signing identifier (the bundle ID, for a bundle; see the bare-CLI section above for non-bundled tools) + signature, not path - moving a signed `.app` keeps its grants.
- Replacing an installed app with `rm -rf` + `cp -R` can leave TCC reporting "authorized" while delivering degraded data (capture starts, buffers are silent/empty). The user-side fix is toggling the permission off and on in System Settings > Privacy & Security. Prevent it: `killall MyApp` first, then `ditto` the new bundle over the old one, then `xattr -cr`. In dev scripts, `tccutil reset ScreenCapture com.example.myapp` gives a clean prompt instead of a stale grant.
- `spctl -a -vv` reporting `rejected` / `Unnotarized Developer ID` for a local build is expected; Gatekeeper acts on the quarantine attribute, which `xattr -cr` clears.
- `sudo spctl --purge` (new in macOS 27) drops Gatekeeper's policy scan cache entries for apps on volumes that are no longer mounted ("Requires root access", `man spctl`).
- For users opening a non-notarized build: the Control-click > Open bypass is gone (since Sequoia). The only path is to try opening once, then System Settings > Privacy & Security > **Open Anyway** ([Apple Support](https://support.apple.com/en-us/102445)).

## Architectures, Enhanced Security, installers, Homebrew

**Architectures.** Xcode 27 runs only on Apple silicon. With `MACOSX_DEPLOYMENT_TARGET` 27.0 or later, `ARCHS_STANDARD` drops x86_64, so builds are arm64-only by default ([Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes)). Lower deployment targets still build universal; for a 27+ target that must run on Intel, set `ARCHS = arm64 x86_64`. Check with `lipo -archs MyApp.app/Contents/MacOS/MyApp`.

**Enhanced Security.** The Enhanced Security capability writes the `com.apple.security.hardened-process.*` entitlements (hardened heap, checked allocations, `dyld-ro`, ...). The version and platform-restriction keys exist in both a legacy and a `-string` spelling (`enhanced-security-version-string`, `platform-restrictions-string`); prefer the capability editor over a hand-maintained plist and check the [entitlements reference](https://developer.apple.com/documentation/bundleresources/security-entitlements) when changing Xcode versions. Xcode 27 known issue: apps with the Hardware-Checked Pointer Arithmetic slice (`arm64e.x1`) cannot be uploaded from macOS 26.6 with automatic signing - upload from macOS 27 or sign manually.

**Installer packages** use a different identity, **Developer ID Installer**:

```bash
pkgbuild --component build/export/MyApp.app --install-location /Applications \
  --identifier com.example.myapp --version 1.0.0 build/MyApp-component.pkg
productbuild --synthesize --package build/MyApp-component.pkg Distribution.xml  # edit, then commit it
productbuild --distribution Distribution.xml --package-path build build/MyApp.pkg
productsign --sign "Developer ID Installer: Your Name (TEAMID)" build/MyApp.pkg build/MyApp-signed.pkg
```

Notarize and staple the signed `.pkg` like a DMG.

**Homebrew cask** as a second channel for a notarized app:
- Pick a globally unique cask token - tap CI (`brew test-bot --only-tap-syntax`) fails on a collision with homebrew-core, and renaming orphans installs.
- If you must rename, ship `cask_renames.json` in the tap (`tap_migrations.json` is for cross-tap moves).
- Set `auto_updates true` when Sparkle updates the app, and add a `livecheck` block.
- `depends_on macos:` cannot express a point release; enforce exact minimums at launch.
- Reinstalling over an app already in `/Applications` needs `--force`.
- Run `brew style` and `brew audit --cask` before pushing.
