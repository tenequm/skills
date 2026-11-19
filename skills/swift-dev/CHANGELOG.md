# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-11-19

### Added

- `references/ios-push-notifications.md`: `aps-environment` and Simulator tokens, APNs auth keys and
  `BadEnvironmentKeyInToken`, the callback-only Notification Service Extension, communication
  notifications, `simctl push` skipping service extensions, and the `dasd` restart after every boot.
- Testing: permission-gated tests fail with `#require` instead of skipping; `-collect-test-diagnostics
  never`, local build reuse, no video and no animations in UI-test launches; the `testmanagerd` launch
  stall and boot retry; reading results with `xcresulttool get test-results`; `shlock` across sessions;
  runtime probes in the Simulator; `swift test --debugger`, `swift build --build-tests`; Xcode 27.3 beta
  UI tests in Swift Testing (`XCUIAutomation`).
- Simulators: runtime selection without hard-coded identifiers, per-lane devices, status-bar overrides
  and seeding, app containers, log windows; profile and entitlement decoding.
- Builds: SDK `.swiftinterface` lookup (SwiftUICore), toolchain `swift format`, `xcodebuild -quiet`,
  `xcodegen generate --use-cache`, a public-repo xcconfig, Simulator-only code in device builds,
  Xcode 27.3 `.aea` delivery, Interface Builder `toolchain` mode fixes.
- Distribution and CI: clock-stamped build numbers, automatic TestFlight distribution,
  `REQUIRED_AGREEMENTS_MISSING_OR_EXPIRED`, tag-last releases, plist tools missing on Linux runners,
  `ubuntu-26.04` and `macos-latest-large` labels.
- Swift 6.4: the closure forward-reference break, module selectors in library-evolution interfaces,
  `anyAppleOS` from 26.0; Swift Subprocess 1.0.
- Platform: ScreenCaptureKit -3815 on display sleep, SwiftData as a disposable cache and its missing
  full-text index, saved shortcuts pinning intent identifiers, `URL` resource-value caching, logging
  errors by domain and code, imported `async` delegate variants, Secure Enclave in the Simulator, macOS 27
  installer architecture and quarantined `launchd` plists.

### Changed

- Xcode 27.2 is final (Swift 6.4.2, iOS and macOS 27.2 SDKs; there is no macOS 27.1); "27.2 RC" citations
  now point at the final notes, and `GetCodeCoverage` is noted as present in 27.2 but absent from its notes.
- XcodeGen 2.48.0: experimental `.xcproj` output, the shipped `dstPath` and synced-folder fixes, and
  `-convert-project 'Xcode Project'` on Xcode 27.2.
- LiveKit 2.19.0: Release-build crash fixes, the LiveKitFFI package rename, the data-stream source move.
- Notification permission is granted once by hand and cloned; the SpringBoard UI-test grant is no
  longer the recommended path.
- The MenuBarExtra label crash is marked as seen once with an unproven cause.
- `scenePhase` work starts on `.inactive` too, since system alerts hold the scene there.
- Mac Catalyst: the 27.2 SDK's phantom 27.1 deployment target and the 27.1 run-destination workaround.

### Fixed

- swift#92915 is closed, but the fix is not in Swift 6.4.2, and it is not limited to generic actors.
- `--explicit-target-dependency-import-check` misbehaves under Swift Build.
- `timeout` on macOS 27.2 is observed, not documented.

### Security

- LiveKit 2.19.0 removes the AAA Certificate Services root from its TURN/TLS trust anchors (compromised
  eMudhra intermediates); the XcodeGen example pins `from: 2.19.0`.

Verified against: swift@6.4.2, xcode@27.2, ios@27.2, macos@27.2, LiveKit@2.19.0, xcodegen@2.48.0

## [0.5.0] - 2026-11-18

### Added

- `references/ci-github-actions.md`: GitHub Actions CI for iOS and macOS apps and packages - runner
  labels and cost (`xcode-27`, no `macos-27`), exact Xcode pinning with `DEVELOPER_DIR`, Linux for
  platform-neutral packages, job shape with a pull-request-only exclusion paths filter and an
  `if: always()` gate (the required-check trap), build flags, Xcode's compilation cache persisted with
  `actions/cache` (one measured warm run; package targets and SDK module PCMs cached, verified on Xcode
  27.2 locally), what not to cache (DerivedData: mtimes, not inodes), cache scoping, simulators and UI
  tests on hosted runners, permission-gated macOS tests (designated-requirement blob for TCC), the
  CI-only parts of signing and notarization (keychain, `notarytool --wait` exit code), supply chain
  (lockfiles, SHA pins, actionlint labels and false reports, zizmor), and debugging a CI-only hang
  (cooperative-pool starvation on 3 cores).
- Router rows in SKILL.md and a pointer from `spm-and-builds.md`.

### Fixed

- `references/concurrency-isolation.md`: `@concurrent` is for CPU-heavy work, not blocking work - a
  blocking call inside it still holds a cooperative-pool thread; bridge it from a dispatch queue.

## [0.4.0] - 2026-11-18

### Added

- Testing: notification permission on a new Simulator has no CLI grant (`simctl privacy`,
  `XCUIProtectedResource`, `devicectl device settings`); grant it from a UI test that taps "Allow"
  through SpringBoard, or with the unofficial AppleSimulatorUtils.
- Testing: a `-only-testing:` selector that matches no tests exits 0 and prints `Test Suite 'Selected
  tests' passed`; selector forms and a guard that fails the run when nothing ran.

## [0.3.1] - 2026-11-05

### Removed

- Per-skill `LICENSE.txt`: ClawHub licenses every published skill MIT-0.

## [0.3.0] - 2026-10-24

### Added

- Bare CLI binaries: set the code-signing identifier explicitly, strip before signing, and assert the
  identity in CI (ported from `swift-macos` 0.8.5).
- iOS 27 SDK requirements and changes: mandatory launch screen, scene accessories, navigation-bar
  minimization, deprecated orientation and display-link APIs; iOS 27.1 zero default layout margins;
  On-Demand Resources deprecated for Background Assets; `PreviewProvider` deprecated.
- iPhone Duo (iOS 27.1): `ArrangementView`, `onHingeChange`, reserved regions, `CameraCaptureAccessory`,
  Simulator limits, the App Store screenshot deadline.
- Xcode 27.1/27.2 tooling: Mac Catalyst known issue, Device Hub simulation features, `devicectl device
  pasteboard`/`capture`/`simulate` (a working replacement for `simctl pbcopy`), new Xcode MCP tools and
  `mcp-server` subcommands, agent plug-ins and `lldb-mcp`.
- More 27 surface: SwiftUI modifiers (`dismissalConfirmationDialog`, `presentationPlacement`, `.crossFade`,
  `defaultTabBarPlacement`, `systemPrefersReducedResourceUsage`), AppKit (`NSRefreshController`, roles,
  `NSTextSelectionManager`), App Intents (8 schema domains, `RunSystemShortcutIntent`, `RelevantEntities`),
  SwiftData multi-store tokens and `DocumentGroup(editing:migrationPlan:)`, Swift Testing `TestScoping`
  traits, issue filters and `#_sourceLocation` helpers.
- LiveKit 2.18.0: transceivers stopped on unpublish, early data no longer dropped, in-process
  ScreenCaptureKit screen share on iOS 27.
- Developer ID Sub-CA expiry (2027-02-01); `xcrun dwarfdump --uuid` for dSYM checks; `-parse-as-library`
  for single-file probes; `MainActor.assertIsolated()` instead of `Thread.isMainThread`.

### Changed

- Verified against Xcode 27.1 (iOS 27.1 SDK); the `.xcproj` default is documented as contested between
  Apple's article and the 27.2 RC release notes, and XcodeGen 2.46.0 projects fail 27.2 conversion.
- swift#92915: needs a real suspension, still present on Xcode 27.1, and `isolation: self` is a verified
  workaround.
- On-device context size: read `contextSize` instead of hard-coding 4096.
- macOS 27 XProtect app-data restriction covers other apps' files outside containers.
- The rebuild-in-place `Code Signature Invalid` kill is observed, no longer unverified.

### Fixed

- LiveKit failed-full-reconnect watchdog is needed only before 2.18.0.
- `SpotlightSearchTool()` with the default configuration fails on the on-device model; use a focused guide.
- `HistoryObserver` takes only a container; `historyTokens` is keyed by store.
- `confirmation(expectedCount: ...5)` does not compile; the XCTest interop default depends on the tools
  version (below 6.4 a failing XCTest assertion passes); unknown `@diagnose` groups only warn.
- `LongRunningIntent` example now reports progress; `xcrun mcp-server` examples gained their required
  arguments; `devicectl device` has no `motion` subcommand.
- TCC keys off the code-signing identifier; `log` is a zsh builtin, so use `/usr/bin/log`.

Verified against: xcode@27.1, ios@27.1, LiveKit@2.18.0

## [0.2.0] - 2026-10-13

### Added

- Simulator test toolkit: Action Button presses, a (cosmetic) lock, out-of-process App Intents with
  `AppIntentsTesting`, the Mac's microphone through `devicectl device settings audio`, and remedies for
  `xcodebuild` UI-test stalls (`simctl diagnose`, hangs after a pass, secrets in `.xcresult` bundles).
- Starting a CallKit call or Live Activity from the background with the iOS 27 `.phone.startCall` App
  Schema, Live Activity setup with XcodeGen, and the newer App Intents protocols (26 to 27).
- TestFlight after upload: processing rejections (ITMS-90683 for WebRTC apps), polling `buildUploads`
  and `builds` until VALID, dSYM placeholders for stripped xcframeworks; device log pull with
  `devicectl device copy`; feeding call audio without a microphone.
- iOS 27 / macOS 27 / Swift 6.4 surface: SwiftUI 27 additions, Swift 6.4 language items and the `-O`
  generic-actor regression, Evaluations, `fm`, `SpotlightSearchTool`, PCC eligibility, the Xcode MCP
  server, LiveCommunicationKit and NowPlaying, SwiftData observer options, ScreenCaptureKit 27 additions.

### Changed

- App Store Connect key roles and the headless TestFlight upload are now observed (App Manager key 403
  on cloud signing, Admin key end to end), and TCC attribution for test runs is observed.
- Export-method renames are dated to Xcode 15.3; iOS 27 interruption replacements are
  `didBecomeInactive` and `resumptionRecommendation`; `BGTaskScheduler.submit` is deprecated in 27;
  `devicectl --json-output -` writes to stdout.

### Fixed

- CallKit runs in the iOS 27 Simulator with two Simulator-only stand-ins; the skill said it does not.
- A call intent is not a plain `AppIntent` when the app is resident in the background.
- LiveKit 2.17: publishing a muted mic times out; publish unmuted behind a silenced mixer instead.
- macOS async termination: no double reply on a second quit, and never `terminate` from a main-queue
  block (ported from `swift-macos` 0.8.4).
- Simulator WebRTC over a Mac VPN: deterministic, with the app-side `enableIceGatheringOnAnyAddressPorts`
  fix.
- SDK-verified corrections: SwiftData predicate errors, the `installAudioTap` Swift overlay, the
  15-second `SCClipBufferingOutput` limit, DMG signing before notarization, `NSHostingView` sizing and
  scene-bridging defaults, `ApproachableConcurrency` enabling both features, `errSecUserCanceled`.

## [0.1.0] - 2026-10-07

### Added

- Initial release: native iOS and macOS development on Swift 6.4 / Xcode 27.0 / iOS 27.0 / macOS 27.0.
  A platform-neutral core in SKILL.md (concurrency, `@Observable` controllers, SwiftData, Swift Testing,
  packages, Keychain, Foundation Models) routing to `references/ios-*`, `references/macos-*` and shared
  references.
- iOS coverage: XcodeGen projects with a local logic package, simulator runtimes and `devicectl`,
  command-line signing and device registration, TestFlight and App Store export, `AVAudioSession` and
  CallKit outgoing calls with LiveKit (room lifecycle traps, DTX across republish, mute before publish),
  App Intents and the Action Button, iOS SwiftUI (battery and accessibility in animated views), custom
  fonts with XcodeGen, simulator logs and install diagnostics, Keychain.
- macOS coverage restructured from the `swift-macos` skill and re-verified against the 27.0 SDKs, with
  the API corrections that surfaced (ScreenCaptureKit, AVAssetWriter, SwiftData predicates, document
  protocols, notarization and export methods).

Verified against: swift@6.4, xcode@27.0, ios@27.0, macos@27.0
