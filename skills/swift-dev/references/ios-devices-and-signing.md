# iOS Devices and Signing

Simulator runtimes, `simctl` and `devicectl`, Developer Mode, and headless iOS code signing with `xcodebuild` and an App Store Connect API key.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: flags checked against `xcodebuild -help`, `xcrun devicectl --help` (642.16) and its subcommand help, `xcrun simctl help`; archived `hey-dan-ios` unsigned for `generic/platform=iOS`; ran a signed archive with `-allowProvisioningUpdates` against the signed-in Xcode account and recorded the errors; built, installed and launched it on an iOS 27.0 simulator with both `simctl` and `devicectl`; registered a network-paired iPhone through `-allowProvisioningDeviceRegistration` and installed and launched a development build on it with the signed-in Xcode account. No API key was used.

## Contents
- SDK vs simulator runtime
- Simulators from the command line
- devicectl: simulators and physical devices
- Developer Mode and pairing
- The iOS signing model
- Headless signing with xcodebuild
- App Store Connect API key roles
- Owner setup

## SDK vs simulator runtime

Xcode ships the iOS SDK; the simulator runtime is a separate download. A fresh Xcode can have `iphonesimulator` in `xcodebuild -showsdks` and nothing in `xcrun simctl list runtimes`. Without a runtime you can still compile:

```bash
xcodebuild -project MyApp.xcodeproj -scheme MyApp \
  -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build
```

Install a runtime (the iOS 27.0 runtime is 7.5 GB on disk):

```bash
xcodebuild -downloadPlatform iOS                       # newest runtime; iOS 27.0 (24A434) took ~3 min here
xcodebuild -downloadPlatform iOS -buildVersion 27.0 -architectureVariant arm64
xcodebuild -downloadPlatform iOS -exportPath ~/Downloads  # keep the .dmg, then:
xcodebuild -importPlatform ~/Downloads/<runtime>.dmg
```

Manage installed runtimes with `xcrun simctl runtime list`, `xcrun simctl runtime delete --outdated` (or `--unusable`, `--notUsedSinceDays N`, `--dry-run`). Known Xcode 27 issue: some deleted runtimes reappear after a reboot.

Unverified: `-destination 'generic/platform=iOS Simulator'` compiling with zero runtimes installed (a runtime was present during verification).

## Simulators from the command line

```bash
UDID=$(xcrun simctl create "Dev iPhone" com.apple.CoreSimulator.SimDeviceType.iPhone-17 \
  com.apple.CoreSimulator.SimRuntime.iOS-27-0)
xcrun simctl bootstatus "$UDID" -b          # boots if needed, waits until ready
xcodebuild -project MyApp.xcodeproj -scheme MyApp -destination "id=$UDID" \
  -derivedDataPath build build
xcrun simctl install "$UDID" build/Build/Products/Debug-iphonesimulator/MyApp.app
xcrun simctl privacy "$UDID" grant microphone com.example.MyApp
SIMCTL_CHILD_API_URL=https://staging.example.com \
  xcrun simctl launch --terminate-running-process --console "$UDID" com.example.MyApp
```

- `xcrun simctl list devicetypes` / `list runtimes` give the identifiers; omit the runtime to get the newest compatible one.
- Simulator builds are ad hoc signed ("Sign to Run Locally"): no team, certificate or profile is involved, even when the project sets `DEVELOPMENT_TEAM`.
- `SIMCTL_CHILD_<NAME>` variables reach the launched process as `<NAME>`; `--console` blocks and streams stdout/stderr.
- `xcrun simctl pbcopy` exits 0 on iOS 27 but nothing reaches the simulator's pasteboard; pass test values through `SIMCTL_CHILD_<NAME>` launch environment instead.
- `simctl privacy ... grant` skips the permission alert; `reset` brings it back. Simulators have no CallKit UI, Action Button or real audio routes - test those on hardware.
- The Simulator app is now **Device Hub** (`open "$(xcode-select -p)/../Applications/DeviceHub.app"`); it shows simulators and paired devices together.
- Xcode 27 adds `simctl reboot` / `devicectl` reboot for simulators, and runtimes ship a prebuilt dyld cache, so first boot is faster.

## devicectl: simulators and physical devices

On Xcode 27 `devicectl` lists booted simulators next to physical devices (the `Reality` column reads `simulated`), and `device install app` / `device process launch` work on both:

```bash
xcrun devicectl list devices
xcrun devicectl list devices --filter "Name CONTAINS 'iPhone'" --json-output -
xcrun devicectl device install app --device <udid|name> build/Build/Products/Debug-iphoneos/MyApp.app
xcrun devicectl device process launch --device <udid|name> --terminate-existing com.example.MyApp
xcrun devicectl device process launch --device <udid|name> --console com.example.MyApp   # stream stdout, wait for exit
xcrun devicectl device info lockState --device <udid|name>
```

- `install app` takes a `.app` bundle path. Launch environment comes from `DEVICECTL_CHILD_<NAME>` or `--environment-variables '{"KEY":"value"}'` (the flag overrides the prefixed variables).
- Parse `--json-output` (versioned and stable), never the table text. In JSON v5 `hardwareProperties`, `deviceProperties` and `connectionProperties` are deprecated in favour of `properties`.
- The physical device must be unlocked for most commands. `devicectl device info details --device <udid>` reports `pairingState`, `transportType` (`localNetwork` for network pairing) and `developerModeStatus`.

## Developer Mode and pairing

- Pair first: plug in and run `xcrun devicectl manage pair --device <udid>`, or use Device Hub (+ > "Pair Nearby Device..." pairs iOS 27 devices over the network, no cable).
- Running development-signed apps (from Xcode, `devicectl`, or an ad hoc `.ipa`) requires **Developer Mode** (iOS 16+). The switch only appears in Settings > Privacy & Security after the device has been paired with a Mac; turning it on restarts the device and asks for the passcode ([Apple](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device)). TestFlight and App Store installs do not need it.
- Xcode 27 debugs on iOS 17 and later.

## The iOS signing model

Every binary that runs on an iOS device must be signed with an Apple-issued **Apple Development** or **Apple Distribution** certificate and carry a provisioning profile that matches the bundle ID, team, entitlements and - for development and ad hoc - the device UDID. There is no Gatekeeper-style "identified developer" path on iOS, which is why a **Developer ID Application** certificate (Mac-only: "sign a Mac app before distributing it outside the Mac App Store", per [Apple's certificate types](https://developer.apple.com/help/account/certificates/certificates-overview)) and self-signed identities cannot sign iOS apps. More in `ios-distribution.md`.

| Purpose | Certificate | Profile | Device list |
|---|---|---|---|
| Run from Xcode / `devicectl` | Apple Development | iOS App Development | Registered UDIDs |
| Ad hoc (`release-testing`) | Apple Distribution | Ad Hoc | Registered UDIDs |
| TestFlight / App Store | Apple Distribution | App Store Connect | None |

With automatic signing (`CODE_SIGN_STYLE: Automatic` + `DEVELOPMENT_TEAM`) Xcode creates all of these. Distribution certificates can be **cloud-managed**: Apple holds the private key and signs during export, so CI machines need no `.p12` ([cloud-managed certificates](https://developer.apple.com/help/account/certificates/cloud-managed-certificates)).

## Headless signing with xcodebuild

| Flag | Effect |
|---|---|
| `-allowProvisioningUpdates` | Lets xcodebuild talk to the developer portal: create/update App IDs, profiles and certificates for automatic signing, download profiles for manual signing |
| `-allowProvisioningDeviceRegistration` | Also registers the destination device's UDID; only effective with `-allowProvisioningUpdates` |
| `-authenticationKeyPath`, `-authenticationKeyID`, `-authenticationKeyIssuerID` | Authenticate with an App Store Connect API key instead of an Apple Account in Xcode > Settings > Apple Accounts; all three are required together |

Build and install on a connected device, registering it on first use:

```bash
xcodebuild -project MyApp.xcodeproj -scheme MyApp -destination "id=$DEVICE_UDID" \
  -derivedDataPath build \
  -allowProvisioningUpdates -allowProvisioningDeviceRegistration \
  -authenticationKeyPath "$KEY_P8" -authenticationKeyID "$KEY_ID" -authenticationKeyIssuerID "$ISSUER_ID" \
  build
xcrun devicectl device install app --device "$DEVICE_UDID" build/Build/Products/Debug-iphoneos/MyApp.app
xcrun devicectl device process launch --device "$DEVICE_UDID" com.example.MyApp
```

Drop the three key flags to use the Apple Account signed into Xcode instead. Pass the same signing flags to every `xcodebuild` step that signs (`build`, `archive`, `-exportArchive`).

Errors observed on this Mac (signed-in Xcode account, team with no registered devices, no local profiles):

- `xcodebuild archive -destination 'generic/platform=iOS' -allowProvisioningUpdates` - automatic signing archives with a **development** profile, which needs at least one device:
  ```
  error: Communication with Apple failed: Your team has no devices from which to generate a provisioning profile. Connect a device to use or manually add device IDs in Certificates, Identifiers & Profiles.
  error: No profiles for 'com.tenequm.HeyDan' were found: Xcode couldn't find any iOS App Development provisioning profiles matching 'com.tenequm.HeyDan'.
  ```
  Fix: connect a device and add `-allowProvisioningDeviceRegistration`, register a UDID in the portal, or archive unsigned and let export sign (see `ios-distribution.md`).
- `xcodebuild -exportArchive` without `-allowProvisioningUpdates` never creates anything:
  ```
  error: exportArchive No signing certificate "iOS Distribution" found
  error: exportArchive No profiles for 'com.tenequm.HeyDan' were found
    ... Automatic signing is disabled and unable to generate a profile. To enable automatic signing, pass -allowProvisioningUpdates to xcodebuild.
  ```

## App Store Connect API key roles

Keys are created in App Store Connect > Users and Access > Integrations > App Store Connect API. Only Account Holder/Admin can create **team** keys. The `.p8` downloads exactly once; the key's role is fixed at creation - to change it, create a new key ([Apple](https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api)). **Individual** keys cannot use provisioning endpoints or `notarytool`, so headless signing needs a **team** key.

What each operation needs, from Apple's [program roles](https://developer.apple.com/help/account/access/roles) table:

| Operation | Account Holder | Admin | App Manager | Developer |
|---|---|---|---|---|
| Register devices (Add UDIDs) | yes | yes | with CI&P access | only via Xcode automatic signing |
| Register App IDs | yes | yes | with CI&P access | only via Xcode automatic signing |
| Create development profiles | yes | yes | with CI&P access | only via Xcode automatic signing |
| Create distribution profiles | yes | yes | with CI&P access | no |
| Create distribution certificates | yes | yes | with CI&P access | no |
| Cloud-managed Apple Distribution signing | yes | yes | separate permission | separate permission |
| Upload builds | yes | yes | with CI&P access | with CI&P access |
| Notarize | yes | yes | yes | yes |

CI&P = Certificates, Identifiers & Profiles access, a per-user grant in Users and Access. For a headless pipeline that registers devices, creates profiles and cloud-signs distribution builds, use an **Admin** team key. Community reports ([rxliuli](https://rxliuli.com/blog/two-pitfalls-of-safari-cloud-signing-in-github-actions), [SlyLED CI](https://github.com/SlyWombat/SlyLED/commit/2b790e62f167ad31225b25bf39fd341382fe4a1c)) show App Manager and Developer keys authenticating fine and then failing export with `Cloud signing permission error`; the escape hatch for a lower-role key is manual signing with a pre-created App Store profile and a local Apple Distribution certificate.

Unverified: whether a Developer or App Manager **team key** can upload builds or register devices - the per-user "CI&P access" grant has no visible equivalent for keys.

Handle the `.p8` like a password: keep it out of the repo, write it to a `0600` temp file from your secret store right before the build, and delete it afterwards. `altool` instead looks for `AuthKey_<KEY_ID>.p8` in `~/.appstoreconnect/private_keys` (and a few other directories, see `altool --help`).

## Owner setup

- Team: `4L9YA7S99L` (paid Apple Developer Program).
- Code-signing identity types in the login keychain (`security find-identity -v -p codesigning`): Apple Development, Developer ID Application, and one local self-signed identity (not Apple-issued). There is no Apple Distribution certificate locally; distribution signing would be cloud-managed or created on first export.
- Physical device: an iPhone 15 Pro Max on iOS 27.2 beta (24B5099f), paired over the local network with Developer Mode enabled; registered on the team on 2026-10-07 by the first `-allowProvisioningDeviceRegistration` build (hey-dan installed and launched). Before that the team had no registered devices, which produced the archive errors above.
- An Apple Account is signed into Xcode and handles development signing; the API key is only needed for headless distribution.
- ASC API key: 1Password item `pond-apple-ci-signing`. Unverified: its role (Admin vs App Manager/Developer) - this decides whether device registration, profile creation and cloud signing work headless.
- To verify the role: App Store Connect > Users and Access > Integrations > App Store Connect API > Team Keys shows each key's Access column. The functional check is an `-exportArchive` with `method` `app-store-connect`, `destination` `export` and `-allowProvisioningUpdates` plus the key flags: success means the key can create the App Store profile and cloud-sign; `Cloud signing permission error` means the role is too low.
