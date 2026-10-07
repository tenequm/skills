# iOS Project Setup with XcodeGen

How to stand up an iOS app from the command line: an XcodeGen `project.yml`, a local Swift package for logic and fast tests, the Info.plist keys and build settings that matter, and the build/test commands.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: generated the project below with XcodeGen 2.46.0, built it unsigned for `generic/platform=iOS` and `generic/platform=iOS Simulator`, ran its app-target tests on an iOS 27.0 simulator and `swift test` in the local package, and read the compiler flags Xcode passed from the build log; added two OFL fonts (one static, one variable) to a copy, built it for the simulator, inspected the `.app` and checked `UIFont(name:)` at launch, and reproduced the build error without `excludes`.

## Contents
- Why a generator
- Layout
- project.yml
- Build settings that are not obvious
- Info.plist keys
- Custom fonts
- The local package
- Commands and timings
- justfile
- .gitignore
- Opening in Xcode
- Failure modes

## Why a generator

SwiftPM cannot produce an iOS `.app` (no app bundle, Info.plist, entitlements, asset catalog or signing), and a hand-maintained `.xcodeproj` is unreviewable XML that merges badly. Generate it instead: **[XcodeGen](https://github.com/yonaskolb/XcodeGen)** reads one `project.yml` and writes the `.xcodeproj`, which stays out of git. Install with `mise use -g xcodegen@2.46.0` (or `brew install xcodegen`).

[Tuist](https://tuist.dev) is the alternative (Swift `Project.swift` manifests, `tuist generate`). XcodeGen is the default here because it is a single YAML file with no manifest-compilation step or extra toolchain, and the generated project is disposable.

## Layout

```
VoiceApp/
  project.yml          the source of truth for the Xcode project
  justfile
  VoiceApp/            app target: SwiftUI, UIKit, CallKit, LiveKit glue
  VoiceAppTests/       app-target tests (need a simulator)
  VoiceCore/           local package: logic + tests, no UIKit
    Package.swift
    Sources/VoiceCore/
    Tests/VoiceCoreTests/
```

## project.yml

```yaml
name: VoiceApp
options:
  bundleIdPrefix: com.example
  deploymentTarget:
    iOS: "26.0"
settings:
  base:
    DEVELOPMENT_TEAM: ABCDE12345   # replace with your 10-character Team ID
    CODE_SIGN_STYLE: Automatic
    SWIFT_VERSION: "6.0"
    SWIFT_APPROACHABLE_CONCURRENCY: YES
    SWIFT_UPCOMING_FEATURE_MEMBER_IMPORT_VISIBILITY: YES
    MARKETING_VERSION: "0.1.0"
    CURRENT_PROJECT_VERSION: "1"
packages:
  LiveKit:
    url: https://github.com/livekit/client-sdk-swift
    from: 2.17.0
  VoiceCore:
    path: VoiceCore
targets:
  VoiceApp:
    type: application
    platform: iOS
    sources: [VoiceApp]
    dependencies:
      - package: LiveKit
      - package: VoiceCore
    info:
      path: VoiceApp/Info.plist
      properties:
        CFBundleDisplayName: Voice
        CFBundleShortVersionString: $(MARKETING_VERSION)
        CFBundleVersion: $(CURRENT_PROJECT_VERSION)
        NSMicrophoneUsageDescription: Voice sends your microphone audio to the agent during a call.
        UIBackgroundModes: [audio, voip]
        UILaunchScreen: {}
        UISupportedInterfaceOrientations: [UIInterfaceOrientationPortrait]
        ITSAppUsesNonExemptEncryption: false
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: com.example.VoiceApp
        TARGETED_DEVICE_FAMILY: "1"
        SWIFT_DEFAULT_ACTOR_ISOLATION: MainActor
    scheme:
      testTargets: [VoiceAppTests]
  VoiceAppTests:
    type: bundle.unit-test
    platform: iOS
    sources: [VoiceAppTests]
    dependencies:
      - target: VoiceApp
    settings:
      base:
        GENERATE_INFOPLIST_FILE: YES
```

Key reference: [XcodeGen ProjectSpec](https://github.com/yonaskolb/XcodeGen/blob/2.46.0/Docs/ProjectSpec.md). Remote packages take `from:` / `majorVersion:`, `minorVersion:`, `exactVersion:`, `branch:` or `revision:`; local ones take `path:`. A `package:` dependency names the key under `packages`; add `product:` when the library product name differs from the package key. `bundleIdPrefix` names targets without an explicit `PRODUCT_BUNDLE_IDENTIFIER` (here the test bundle becomes `com.example.VoiceAppTests`).

## Build settings that are not obvious

XcodeGen applies its own presets (`share/xcodegen/SettingPresets` in the install), not Xcode 27's new-project template, so the defaults differ from a project made in Xcode:

| Setting | XcodeGen preset | Xcode 27 app template | Set to |
|---|---|---|---|
| `SWIFT_VERSION` | `5.0` | `5.0` | `"6.0"` |
| `SWIFT_APPROACHABLE_CONCURRENCY` | unset | `YES` | `YES` |
| `SWIFT_DEFAULT_ACTOR_ISOLATION` | unset (`nonisolated`) | `MainActor` (app target) | `MainActor` on the app target |
| `SWIFT_UPCOMING_FEATURE_MEMBER_IMPORT_VISIBILITY` | unset | `YES` | `YES` |
| `TARGETED_DEVICE_FAMILY` | `"1,2"` (iPhone + iPad) | per template | `"1"` for iPhone-only |

- **`SWIFT_STRICT_CONCURRENCY` is redundant in Swift 6 mode - leave it out.** Its xcspec definition only applies when the effective Swift version is 4, 4.2 or 5 ("This is always 'complete' when in the Swift 6 language mode and produces errors instead of warnings"). Setting it to `complete` on a Swift 6 target adds no flag and does not even trigger a recompile.
- **`SWIFT_APPROACHABLE_CONCURRENCY: YES` still matters in Swift 6 mode.** Three of its five features are already part of Swift 6, but the build log shows it adds `-enable-upcoming-feature InferIsolatedConformances` and `-enable-upcoming-feature NonisolatedNonsendingByDefault` (nonisolated async functions run on the caller's actor unless marked `@concurrent`). See concurrency-isolation.md.
- **`SWIFT_DEFAULT_ACTOR_ISOLATION: MainActor`** passes `-default-isolation=MainActor`: unannotated code in the app target is main-actor isolated. Keep it on the app target, not project-wide, so test bundles and other targets opt in deliberately. Project build settings never reach SwiftPM packages - a package that wants it declares `swiftSettings: [.defaultIsolation(MainActor.self)]` itself. Escape hatch: leave default isolation off and mark controllers `@MainActor` explicitly - also fine under Swift 6; pick one per target.
- **`MemberImportVisibility`** makes each file import the modules whose members it uses. A view that reads a property of a `VoiceCore` type without `import VoiceCore` fails with `property 'origin' is not available due to missing import of defining module 'VoiceCore' [#MemberImportVisibility]`, even though another file in the target imports it.

## Info.plist keys

XcodeGen writes `info.path` on every `xcodegen generate` from `info.properties`, so the plist is a build artifact: gitignore it and edit `project.yml`. It adds `CFBundleIdentifier`, `CFBundleExecutable`, `CFBundleName`, `CFBundlePackageType` and friends itself.

- **Versions:** without the two `$(...)` lines above, the generated plist hard-codes `CFBundleShortVersionString` to `1.0` and `CFBundleVersion` to `1`, silently ignoring `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION`. Every TestFlight upload then carries the same build number. With the mapping, the built app's plist reads `0.1.0` / `1`; bump `CURRENT_PROJECT_VERSION` per upload (see ios-distribution.md).
- **`NSMicrophoneUsageDescription`** is the text of the microphone permission prompt; accessing the mic without it terminates the app. Every protected resource has its own `NS...UsageDescription` key.
- **`UIBackgroundModes: [audio, voip]`** keeps a call running with the screen locked (with an active CallKit call and audio session - see ios-audio-and-callkit.md). Add `fetch` only for `BGAppRefreshTask` (see ios-swiftui.md).
- **`UILaunchScreen: {}`** gives a system launch screen without a storyboard.
- **`ITSAppUsesNonExemptEncryption: false`** declares the app (including linked libraries) uses no encryption, or only encryption exempt from export compliance. With the key present, App Store Connect skips the export-compliance questionnaire on every upload; set `true` (plus `ITSEncryptionExportComplianceCode`) if you ship non-exempt crypto ([Apple](https://developer.apple.com/documentation/bundleresources/information-property-list/itsappusesnonexemptencryption)).
- **`UIDesignRequiresCompatibility`** (the Liquid Glass opt-out) is ignored when building against the iOS 27 SDK - do not add it.
- `TARGETED_DEVICE_FAMILY` is a build setting, not a plist key: `"1"` iPhone, `"2"` iPad, `"1,2"` both. The built plist's `UIDeviceFamily` follows it; `"1,2"` commits you to iPad layouts and screenshots.

## Custom fonts

Keep fonts in their own folder, one subfolder per family with its license file, and add that folder as a folder reference:

```yaml
targets:
  VoiceApp:
    sources:
      - path: VoiceApp
        excludes: [Fonts]
      - path: VoiceApp/Fonts       # folder reference: keeps subfolders and each OFL.txt
        type: folder
        buildPhase: resources
    info:
      properties:
        UIAppFonts:
          - Fonts/IBMPlexMono/IBMPlexMono-Regular.ttf
          - Fonts/HankenGrotesk/HankenGrotesk[wght].ttf
```

- **The `excludes` is required.** Without it the main group also adds every file in `Fonts/` as a flat resource, and two families shipping an `OFL.txt` collide: `error: Multiple commands produce '.../VoiceApp.app/OFL.txt'`.
- `UIAppFonts` paths are relative to the bundle root, so they include the `Fonts/` folder. The built `.app` contains `Fonts/<Family>/*.ttf` plus each `OFL.txt`.
- Reference a font by its PostScript name, not the file name: `Font.custom("IBMPlexMono-Regular", size: 15, relativeTo: .body)` (`relativeTo:` keeps it scaling with Dynamic Type). `fc-scan --format "%{postscriptname} | %{style[0]}\n" <file>.ttf` (Homebrew `fontconfig`) prints the names, including a variable font's named instances.
- A variable font registers only its default instance by name: `UIFont(name: "HankenGrotesk-Regular", size: 12)` resolved, `UIFont(name: "HankenGrotesk-Bold", size: 12)` returned `nil` although `fc-scan` lists that instance (observed on the iOS 27.0 simulator). Unverified: whether `.weight(.bold)` on the custom font selects the variable instance.

## The local package

Keep protocol, parsing and state-machine logic in a local package with no UIKit, CallKit or LiveKit imports. `swift test` then runs it on the Mac in seconds with no simulator, while the app target only does UI and framework glue.

```swift
// swift-tools-version:6.2
import PackageDescription

let package = Package(
    name: "VoiceCore",
    platforms: [.iOS(.v26), .macOS(.v15)],
    products: [.library(name: "VoiceCore", targets: ["VoiceCore"])],
    targets: [
        .target(name: "VoiceCore"),
        .testTarget(name: "VoiceCoreTests", dependencies: ["VoiceCore"]),
    ]
)
```

`.iOS(.v26)` needs tools version 6.2+. The `.macOS` entry is what lets `swift test` run on the host. Types the app uses must be `public`, and a synthesized memberwise init is internal - give public structs an explicit `public init` (see testing.md for the misleading diagnostic this causes in `#expect`).

## Commands and timings

Measured on an Apple-silicon Mac, Xcode 27.0, LiveKit 2.17.0:

| Command | Time |
|---|---|
| `xcodegen generate` | 0.04 s |
| `swift test` in `VoiceCore` (cold / warm) | 8 s / 3 s |
| `xcodebuild ... -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build`, clean | 28 s |
| same, `generic/platform=iOS Simulator`, clean | 97 s (builds arm64 and x86_64) |
| `xcodebuild ... -destination 'platform=iOS Simulator,id=<udid>' test` (incl. simulator boot) | 35-70 s |

```bash
xcodegen generate
xcodebuild -project VoiceApp.xcodeproj -scheme VoiceApp \
  -destination 'generic/platform=iOS' -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO build
```

`generic/platform=iOS` compile-checks for devices with no device attached, no simulator runtime installed and no signing. A generic Simulator destination builds every simulator architecture; to compile-check faster, name a concrete simulator (`platform=iOS Simulator,name=iPhone 17`), which builds only the active one. App-target tests need an installed iOS simulator runtime; installing runtimes, running on a device and signing are in ios-devices-and-signing.md, TestFlight in ios-distribution.md.

## justfile

```just
# VoiceApp.xcodeproj is generated from project.yml and not committed.
gen:
    xcodegen generate

open: gen
    open VoiceApp.xcodeproj

# Logic tests on the Mac, no simulator.
test:
    cd VoiceCore && swift test

# App-target tests; needs an installed iOS simulator runtime.
test-app sim="iPhone 17": gen
    xcodebuild -project VoiceApp.xcodeproj -scheme VoiceApp -destination 'platform=iOS Simulator,name={{sim}}' -derivedDataPath build test

# Compile-check for a device without signing.
build: gen
    xcodebuild -project VoiceApp.xcodeproj -scheme VoiceApp -destination 'generic/platform=iOS' -derivedDataPath build CODE_SIGNING_ALLOWED=NO build
```

`build` and `test-app` depend on `gen` on purpose - see the first failure mode below.

## .gitignore

```gitignore
# Generated by xcodegen; keep only the SwiftPM pins.
*.xcodeproj/*
!*.xcodeproj/project.xcworkspace/
*.xcodeproj/project.xcworkspace/*
!*.xcodeproj/project.xcworkspace/xcshareddata/
*.xcodeproj/project.xcworkspace/xcshareddata/*
!*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/
*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/*
!*.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved
VoiceApp/Info.plist
.build/
build/
xcuserdata/
.DS_Store
```

Xcode writes the SwiftPM pins to `VoiceApp.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved`. Ignoring the whole `*.xcodeproj/` drops them, so every fresh clone resolves the newest versions allowed by `from:` - including transitive packages like `webrtc-xcframework`. The negation chain above commits only that file; `xcodegen generate` leaves an existing `Package.resolved` untouched, so a fresh clone builds the pinned versions.

## Opening in Xcode

`just open` (or `open VoiceApp.xcodeproj`, or `xed .`). Treat Xcode's project editor as read-only: build-setting, capability or Info changes made in Xcode's UI are overwritten by the next `xcodegen generate` - put them in `project.yml`. The iOS simulator UI app is `DeviceHub.app` in Xcode 27 (formerly Simulator.app).

## Failure modes

- **New files silently missing from the build.** XcodeGen lists source files at generate time. A file created on disk afterwards (by an agent, a script, `git pull`) is not compiled - a file containing a syntax error still gave `BUILD SUCCEEDED` until the next `xcodegen generate`. Regenerate before every build (the justfile does). Escape hatch: `sources: [{path: VoiceApp, type: syncedFolder}]` makes an Xcode 16+ synchronized folder that picks up new files without regenerating (verified; XcodeGen adds the Info.plist membership exception itself).
- **Test bundle won't sign:** `Cannot code sign because the target does not have an Info.plist file and one is not being generated automatically` - add `GENERATE_INFOPLIST_FILE: YES` to the test target.
- **`... is not available due to missing import of defining module`** - `MemberImportVisibility`; add the `import` to that file.
- **Build-setting overrides on the `xcodebuild` command line hit every target, packages included.** `xcodebuild ... SWIFT_STRICT_CONCURRENCY=complete` recompiled LiveKit's Swift 5 modules with `-enable-upcoming-feature StrictConcurrency`. Put settings in `project.yml`, which only reaches project targets.
- **Version stuck at 1.0 (1)** - map `CFBundleShortVersionString` / `CFBundleVersion` to the build settings (see Info.plist keys).
- **Unpinned dependencies on CI** - commit `Package.resolved` (see .gitignore).
