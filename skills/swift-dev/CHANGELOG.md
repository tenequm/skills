# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
