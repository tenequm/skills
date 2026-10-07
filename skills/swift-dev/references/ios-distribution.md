# iOS Distribution

Getting an iOS build onto phones: development install, ad hoc, TestFlight and App Store from the command line, and why a macOS Developer ID certificate cannot sign any of it.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: archived a voice-call app unsigned for `generic/platform=iOS` and ran `-exportArchive` on it with `app-store-connect`, `release-testing`, `debugging` and `developer-id` to record the real errors; ExportOptions keys and `method` values from `xcodebuild -help`; upload flags from `xcrun altool --help` (27.0.5). Development build, install and launch on a physical iPhone with the signed-in Xcode account (sequence below); the device-selection `jq` filter run against real `devicectl list devices` JSON v5 output with the paired iPhone unreachable. Nothing was signed for distribution or uploaded (no API key used).

## Contents
- Channels
- Why Developer ID cannot sign iOS apps
- ExportOptions.plist
- Development install on your own phone
- Ad hoc
- TestFlight from the command line
- Archiving before any device is registered
- App Store release

## Channels

| Channel | Export `method` | Signed with | Who can install | Review |
|---|---|---|---|---|
| Development | `debugging` | Apple Development + development profile | Registered devices with Developer Mode on | No |
| Ad hoc | `release-testing` | Apple Distribution + ad hoc profile | Registered devices (UDIDs in the profile) | No |
| TestFlight internal | `app-store-connect` | Apple Distribution + App Store Connect profile | Up to 100 App Store Connect users | No |
| TestFlight external | `app-store-connect` | same | Up to 10,000 by email or public link | Beta App Review on the first build |
| App Store | `app-store-connect` | same | Everyone | App Review |
| In-house | `enterprise` | Enterprise distribution | Your organization (Enterprise Program only) | No |

For a personal or small-team app, TestFlight internal testing is the default: no device registration, no Developer Mode, builds install through the TestFlight app and stay testable for 90 days ([TestFlight overview](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview)). Use a development install for the inner loop.

## Why Developer ID cannot sign iOS apps

Developer ID is a macOS-only trust path: Gatekeeper accepts Developer ID-signed, notarized software from outside the Mac App Store. iOS has no equivalent. Apple's [certificate types](https://developer.apple.com/help/account/certificates/certificates-overview) scope **Developer ID Application** to "sign a Mac app before distributing it outside the Mac App Store"; iOS code runs only when signed by **Apple Development** or **Apple Distribution** (or Enterprise) and backed by a provisioning profile that matches the device or the store. `xcodebuild` rejects the attempt outright for an iOS archive:

```
error: exportArchive exportOptionsPlist error for key "method" expected one {app-store-connect, release-testing, enterprise, debugging, validation} but found developer-id
```

Having a Developer ID Application identity in the keychain therefore contributes nothing to iOS signing; the export looks for a distribution identity and fails with `No signing certificate "iOS Distribution" found` until an Apple Distribution certificate exists locally or cloud signing is allowed. For macOS Developer ID distribution see `macos-distribution.md`.

## ExportOptions.plist

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store-connect</string>
    <key>destination</key>
    <string>upload</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>testFlightInternalTestingOnly</key>
    <true/>
</dict>
</plist>
```

Keys worth knowing (full list in `xcodebuild -help`):

- `method`: `app-store-connect`, `release-testing`, `debugging`, `enterprise`, `validation` for iOS archives. `app-store`, `ad-hoc` and `development` are deprecated aliases.
- `destination`: `export` (default) writes an `.ipa` to `-exportPath`; `upload` sends the build to App Store Connect during export.
- `testFlightInternalTestingOnly`: the build can never go to external TestFlight or the App Store - use it for branch and PR builds.
- `manageAppVersionAndBuildNumber` (default YES): Xcode bumps the build number on upload, so repeated uploads of the same `CURRENT_PROJECT_VERSION` do not collide.
- `signingStyle` `automatic` on a manually signed archive creates profiles and cloud-managed certificates as needed but never registers devices or App IDs.
- `uploadSymbols` (default YES), `stripSwiftSymbols` (default YES), `thinning` for non-store exports.

## Development install on your own phone

Prerequisites: the phone is paired, unlocked and has Developer Mode on (see `ios-devices-and-signing.md`).

```bash
xcrun devicectl list devices --json-output /tmp/devices.json >/dev/null
DEVICE=$(jq -r '[.result.devices[] | select(.properties.hardware.platform == "iOS"
  and .properties.hardware.reality == "physical"
  and .properties.connection.state != "unavailable")] | first | .properties.hardware.udid // empty' /tmp/devices.json)
: "${DEVICE:?no reachable iPhone - wake it, join the same network or plug it in}"
xcodebuild -project MyApp.xcodeproj -scheme MyApp -destination "id=$DEVICE" -derivedDataPath build \
  -allowProvisioningUpdates -allowProvisioningDeviceRegistration build
xcrun devicectl device install app --device "$DEVICE" build/Build/Products/Debug-iphoneos/MyApp.app
xcrun devicectl device process launch --device "$DEVICE" --console com.example.MyApp
```

A paired phone that is asleep or off the network stays in the list as `unavailable`; selecting it anyway makes `xcodebuild` fail with exit 70 `Unable to find a destination matching the provided destination specifier` (see ios-devices-and-signing.md), so the filter skips it and the `:?` line stops with a clear message. The filter uses the JSON v5 `properties` dictionary; `hardwareProperties` and friends are deprecated. Verified: an unreachable iPhone (`unavailable`) is skipped and the script stops; the same JSON with the state edited to `available` selects it. The first build registers the UDID and creates the development certificate and profile. `--console` streams the app's stdout until it exits; drop it to launch and return.

Verified on a physical iPhone (iOS 27.2) with the Apple Account signed into Xcode (no API key): the first build registered the device on the team and created the development profile; `install app` printed `App installed:` with the bundle ID and installation URL, and `process launch --terminate-existing` printed `Launched application with com.example.MyApp bundle identifier.` `xcodebuild [MT] IDERunDestination: Supported platforms for the buildables in the current scheme is empty.` appears on every run and is harmless.

Unverified: whether the phone shows an "Untrusted Developer" prompt on first launch (none is expected for Apple Development signing on a paid team; it was not observed directly).

## Ad hoc

Ad hoc builds run outside Xcode on up to the registered devices only. Register every tester's UDID first (the portal, or `-allowProvisioningDeviceRegistration` while the device is connected), then:

```bash
xcodebuild -exportArchive -archivePath build/MyApp.xcarchive -exportPath build/adhoc \
  -exportOptionsPlist AdHoc.plist -allowProvisioningUpdates   # AdHoc.plist: method = release-testing
```

Adding a device later means regenerating the profile and re-exporting. Testers still need Developer Mode on. Prefer TestFlight unless testers cannot use it.

## TestFlight from the command line

Prerequisites (once per app):

1. The bundle ID is registered and an app record exists in [App Store Connect](https://appstoreconnect.apple.com) (Apps > +). Uploads attach to the record by bundle ID and version.
2. Export compliance: set `ITSAppUsesNonExemptEncryption` to `NO` in Info.plist when the app only uses exempt encryption (HTTPS/TLS), or every build waits for the compliance question.
3. The app is built with Xcode 26 or later and targets iOS 13 or later ([upcoming requirements](https://developer.apple.com/news/upcoming-requirements/)).
4. An App Store Connect API key with a role that can cloud-sign and create the App Store profile - Admin for a fully headless run (see `ios-devices-and-signing.md`).

Unverified: App Store Connect rejecting an iOS build that has no app icon asset (the scratch project has none; this was not uploaded).

Archive, then export straight to App Store Connect:

```bash
AUTH=(-allowProvisioningUpdates -authenticationKeyPath "$KEY_P8" -authenticationKeyID "$KEY_ID" -authenticationKeyIssuerID "$ISSUER_ID")
xcodebuild archive -project MyApp.xcodeproj -scheme MyApp -configuration Release \
  -destination 'generic/platform=iOS' -archivePath build/MyApp.xcarchive "${AUTH[@]}"
xcodebuild -exportArchive -archivePath build/MyApp.xcarchive -exportPath build/asc \
  -exportOptionsPlist ExportOptions.plist "${AUTH[@]}"          # destination = upload
```

Escape hatch: export with `destination` `export` to get `build/asc/MyApp.ipa`, then upload separately:

```bash
xcrun altool --validate-app build/asc/MyApp.ipa --api-key "$KEY_ID" --api-issuer "$ISSUER_ID"
xcrun altool --upload-package build/asc/MyApp.ipa --api-key "$KEY_ID" --api-issuer "$ISSUER_ID" --wait
xcrun altool --build-status --delivery-id <id-from-upload> --api-key "$KEY_ID" --api-issuer "$ISSUER_ID"
```

`altool` is the current command-line uploader in Xcode 27 (version 27.0.5 lists `--upload-package` with `--wait`, `--validate-app`, `--build-status`, and still accepts `--upload-app -f`); only its notarization role was retired. It looks for `AuthKey_<KEY_ID>.p8` in `~/.appstoreconnect/private_keys` or `$API_PRIVATE_KEYS_DIR`, or takes `--p8-file-path`. Apple's [upload builds](https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds) page also lists Transporter and the App Store Connect API `buildUploads` endpoint as alternatives.

Observed once (cause unconfirmed): `-exportArchive` with `method` `app-store-connect`, `destination` `export`, automatic signing, an Apple Account signed into Xcode and no API key failed with

```
error: exportArchive Failed to Use Accounts. App Store Connect access for "<TEAM>" is required.
```

The account's App Store Connect role, a missing app record, or an export that needs an API key are all candidates; none was confirmed. Retrying with the `-authenticationKey*` flags of an Admin team key is the next thing to try.

After processing (an email arrives), the build is immediately available to internal testers in a TestFlight group; external groups trigger Beta App Review for the first build.

Unverified: the `-authenticationKey*` flags authenticating the `destination` `upload` step itself, and the live upload of any build.

## Archiving before any device is registered

Automatic signing archives with a development profile, and a team with zero registered devices cannot get one (`Your team has no devices from which to generate a provisioning profile`, see `ios-devices-and-signing.md`). Two ways out:

- Register one device (connect it and build once with `-allowProvisioningDeviceRegistration`), then archive normally. Preferred.
- Archive unsigned and let export do all signing:
  ```bash
  xcodebuild archive -project MyApp.xcodeproj -scheme MyApp -destination 'generic/platform=iOS' \
    -archivePath build/MyApp.xcarchive CODE_SIGNING_ALLOWED=NO
  xcodebuild -exportArchive -archivePath build/MyApp.xcarchive -exportPath build/asc \
    -exportOptionsPlist ExportOptions.plist "${AUTH[@]}"
  ```
  The unsigned archive succeeds (`codesign` reports "code object is not signed at all") and export proceeds to distribution signing - without credentials it stops at the missing certificate/profile errors above.

Unverified: an unsigned archive exporting successfully with an API key, and whether entitlements survive it - with `CODE_SIGNING_ALLOWED=NO` no `.xcent` entitlements file is produced, so apps using App Groups, push, iCloud or keychain sharing should archive signed and check `codesign -d --entitlements - --xml Payload/MyApp.app` in the exported `.ipa`.

## App Store release

The upload is identical to TestFlight (without `testFlightInternalTestingOnly`). Choosing the build for a version, metadata, screenshots, privacy answers and "Submit for Review" happen in App Store Connect (or its REST API); Submit for Review requires Account Holder, Admin or App Manager. Keep `PrivacyInfo.xcprivacy` current for every required-reason API the app and its SDKs use ([list](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api)).
