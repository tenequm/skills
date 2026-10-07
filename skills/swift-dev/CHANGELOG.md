# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
