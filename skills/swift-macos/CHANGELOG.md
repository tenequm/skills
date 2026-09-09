# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.3] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [0.8.2] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`development`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [0.8.1] - 2026-08-20

### Fixed

- ScreenCaptureKit audio-only capture recommended `CMTime(value: 1, timescale: CMTimeScale.max)` for `minimumFrameInterval`. That reads like "infinite interval" but is ~0.5 ns - the smallest positive interval - so it requests the display's native refresh rate and burns ~15-20% of a core on WindowServer recomposites for the whole recording. Replaced with `CMTime(value: 1, timescale: 1)` (1 fps) in SKILL.md and screen-capture-audio.md, with an explicit note on the trap.
- screen-capture-audio.md called the `stream output NOT found. Dropping frame` log "cosmetic" and left the video pipeline unaddressed. The fix is to attach a `.screen` output that discards its buffers on its own queue (never the audio queue) - documented in the snippet.

## [0.8.0] - 2026-08-20

### Fixed

- SKILL.md Relationships snippet and relationships-predicates.md Cascade example did not compile: `@Model` requires an explicit initializer, which neither had. Verified against the macOS 26.5 SDK.
- models-schema.md model-inheritance snippet failed twice - `@Model` subclasses require explicit platform availability and an initializer - and the section carried no version gate at all. Subclassing is macOS 26.0+.
- `.presentedWindowStyle(.automatic) // .fullScreen` in app-lifecycle.md: `WindowStyle` has no `.fullScreen` member. The complete SDK set is `.automatic`, `.titleBar`, `.hiddenTitleBar`, `.plain`.
- `windowResizeAnchor` was documented as a Scene API taking an edge; it is a `View` modifier taking `UnitPoint?`.
- `restorationBehavior` was labelled "(macOS 26)"; it is macOS 15.0.
- `ContextOptions` is not in the macOS 26.5 SDK - it is macOS 27 beta - and was described as a trimming/retention policy; it configures prompt content. Section rewritten around `tokenCount(for:)`/`contextSize`, which do exist.
- Three stale documentation links: the Foundation Models custom-adapter article was removed by Apple, and the privacy-manifest and `SCStreamErrorCode` URLs now redirect.
- SE-0526 `withDeadline` status was "in review April 2026"; it was accepted with modifications on 2026-07-29.
- `anyAppleOS` was listed as a Swift 6.4 feature; it compiles on 6.3.3 behind `-enable-experimental-feature AnyAppleOSAvailability`.
- The App Store SDK-minimum requirement is now past tense ("Since April 28, 2026").

### Changed

- Current shipping macOS is 26.6.2 (was 26.6); Xcode 27 pinned to beta 5 (27A5237l) and macOS 27 to beta 6 (26A5416b), with Swift 6.4 noted as shipping inside the Xcode 27 beta.
- macOS 27 beta 6 deprecates both `FileDocument` and `ReferenceFileDocument` in favor of a combined `Document` protocol; the skill had quoted the superseded beta-4 note saying `ReferenceFileDocument` remained available.
- Foundation Models `GenerationError` is deprecated in macOS 27 with a hard submission deadline, and `exceededContextWindowSize` is renamed `contextSizeExceeded`.

### Added

- AppKit Liquid Glass interop: `NSGlassEffectView`, `NSGlassEffectContainerView`, `NSBackgroundExtensionView`, and `NSView.prefersCompactControlSizeMetrics` as the escape hatch when Liquid Glass inflates a dense AppKit layout.
- SwiftUI/AppKit bridging: `NSHostingSceneRepresentation` for hosting whole scenes, `NSHostingSizingOptions`, `NSHostingSceneBridgingOptions`, and `NSGestureRecognizerRepresentable`.
- Pasteboard privacy (macOS 15.4): `NSPasteboard.accessBehavior` and the `detect` methods that inspect the pasteboard without triggering the new read alert - the existing clipboard recipe was exactly the triggering pattern.
- App Intents beyond the single snippet: `AppEntity`/`EntityQuery`/`AppEnum`, `IndexedEntity` with `@ComputedProperty(indexingKey:)`, `SnippetIntent` and its `isDiscoverable` trap, `supportedModes` replacing the deprecated `ForegroundContinuableIntent`, and the macOS-only `NSTableViewAppIntentsDataSource`.
- WidgetKit on macOS and Control Center controls (`ControlWidget`, `ControlWidgetButton`, `ControlWidgetToggle`, `ControlConfigurationIntent`), which reached macOS in 26.0.
- Logging and diagnostics: `os.Logger`, the `.private`-by-default interpolation trap, log-level persistence, reading logs from a menu-bar-only app, and `OSSignposter`.
- `XPCSession`/`XPCListener` - the missing half of the existing `SMAppService` login-item coverage.
- `AXUIElement` accessibility API with its TCC, signature, and sandbox constraints.
- `NSLocalNetworkUsageDescription`, whose absence presents as a networking bug rather than a permission failure.
- `SpeechAnalyzer`/`SpeechTranscriber` as the on-device transcription stage of the existing capture pipeline.
- ScreenCaptureKit gaps: `streamDidBecomeActive`/`streamDidBecomeInactive` (macOS 15.2), `SCStreamConfiguration.Preset`, `SCScreenshotOutput`, and the macOS 27 beta `SCStream.isCapturing`, `SCClipBufferingOutput`, `SCRecordingEditor`.
- xcodebuild-on-.xcodeproj field notes: builds that report `BUILD SUCCEEDED` while emitting an ad-hoc-signed bundle, `codesign -dv` as the post-build gate, `CODE_SIGNING_REQUIRED=YES`, bracketed build settings being unpassable on the command line, certificate-class prefix matching, symlinked-path build-database corruption, and TCC behavior across signature changes and bundle moves.
- SPM consumer-side gates: `-skipPackagePluginValidation`/`-skipMacroValidation` for non-interactive builds, and `-downloadComponent MetalToolchain` after Xcode 26 unbundled the Metal toolchain.
- SE-0506 Advanced Observation Tracking (`withObservationTracking(options:)`, `withContinuousObservationTracking`), Implemented in Swift 6.4.
- Swift Testing pipeline: ST-0026 task-local test trait (accepted with revisions), ST-0027 and ST-0028 in active review, and the event-stream `ABI.Context` API.
- macOS 27 beta surface: SwiftData `ResultsObserver`/`HistoryObserver`/`@Query(sectionBy:)`/`Schema.Attribute.Option.codable`, Foundation Models `PrivateCloudComputeLanguageModel` with its entitlement, the `#Playground` macro, and Core AI's public API names.

Verified against: swift@6.3.3, xcode@26.6, macos@26.6.2

## [0.7.1] - 2026-08-07

### Changed

- Trimmed the frontmatter description to what-plus-when; dropped the trailing 15-item trigger-keyword list.

## [0.7.0] - 2026-07-28

### Fixed

- Foundation Models quick start assigned `Response<Content>` to the bare content type and did not compile; now reads `.content`. Verified with the compiler against the macOS 26.5 SDK.
- `.timeLimit(.seconds(30))` in testing.md is `@available(*, unavailable)` ("Time limit must be specified in minutes"); switched to `.minutes(1)`.
- `FetchDescriptor.fetchBatchSize` does not exist and the snippet mutated a `let`; replaced with `enumerate(_:batchSize:)`.
- Quick Start `@Model final class Task` shadowed `Swift.Task` in a file that then uses `Task {}` and `TaskGroup`; renamed to `ProjectTask`, matching relationships-predicates.md.

### Changed

- Current shipping macOS is 26.6 (was 26.5); noted that Xcode 26.6 still bundles the macOS 26.5 SDK.
- `weak let` corrected from a Swift 6.4 beta feature to SE-0481, shipped in Swift 6.3; 6.4 feature list rewritten against swift-evolution data.
- Xcode 27 and macOS 27 pinned to beta 4 status.
- Swift Testing version gates corrected: issue severity and all image attachments (including `CGImage`) are Swift 6.3 / Xcode 26.4, not 6.2. ST-0021 is now Implemented (Swift 6.4).
- SPM guidance modernized: `.strictMemorySafety()` over the experimental spelling, Swift Build as a 6.3 preview and 6.4 default, swift-syntax 603.0.2, swiftly 6.3.3.
- Dropped `altool --upload-app` (notary service stopped accepting it in 2023) in favor of notarytool.
- Gatekeeper Control-click bypass replaced with the Open Anyway flow - the Control-click override was removed in macOS Sequoia and is still absent in Tahoe.
- Corrected the `Schema.Attribute.Option` list; there is no `.encrypt` option.

### Added

- Xcode 27 build-breakers: ld64 and `-ld_classic` removal, unique Clang module-name requirement, `ARCHS_STANDARD` dropping x86_64 at deployment target 27.0+, the SE-0508 source break, and the `DocumentReader`/`DocumentWriter` `@concurrent` isolation change alongside the new `ReadableDocument`/`WritableDocument` protocols.
- SwiftData: `#Unique` and `#Index` macros, model inheritance with `includeSubclasses`, `.ephemeral`, history tracking (`HistoryDescriptor`/`HistoryToken`/tombstones), custom `DataStore`, fetch shaping (`propertiesToFetch`, `relationshipKeyPathsForPrefetching`), relationship cardinality.
- Swift Testing: `confirmation` for callback- and delegate-driven code, `withKnownIssue`, the `swift test` CLI surface, and the trap where Command Line Tools alone silently run no tests.
- Concurrency: the `Synchronization` module (`Mutex`, `Atomic`) for realtime and C-callback contexts, the `nonisolated(nonsending)` spelling, isolated conformances (SE-0470), `swift package migrate --to-feature`, and the individual upcoming-feature flags.
- ScreenCaptureKit: `synchronizationClock`, `SCScreenshotConfiguration`, Presenter Overlay delegate callbacks, and the omitted `SCStreamConfiguration` properties.
- SwiftUI: `@Entry`, native `WebView`/`WebPage`, rich-text `TextEditor`, and the `UtilityWindow`/`SettingsLink`/`defaultLaunchBehavior` scene surface.
- Distribution: `get-task-allow` as the top notarization blocker, plug-in entitlement inheritance, the Enhanced Security capability, `-exportNotarizedApp`, installer packaging, and Homebrew cask as a second channel.
- SPM: package traits, `--build-system swiftbuild`, `.binaryTarget`/`.systemLibrary`, plugin permissions, and the unwritable-`$HOME`-cache build failure.
- Foundation Models: `@PromptBuilder`/`@InstructionsBuilder`, `DynamicGenerationSchema`, `ContextOptions`.
- Field-hardening notes: actor reentrancy across awaits, the interleaved-vs-planar downmix trap, stale TCC rows after a signing-identity change, mic taps dying on output-device switches, third-party Voice Processing reshaping your input, mic-activity latching, MenuBarExtra label-update crashes, and crash visibility for menu-bar-only apps.

Verified against: swift@6.3.3, xcode@26.6, macos@26.6

## [0.6.3] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format

### Changed

- metadata.openclaw audited against the official ClawHub spec

## [0.6.2] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.6.1] - 2026-07-01
### Changed
- Moved the "Fall 2026 Releases (WWDC 2026)" section out of SKILL.md into `references/fall-2026-releases.md` (progressive disclosure), keeping SKILL.md under the 500-line policy limit. Content unchanged, expanded slightly with sources.

## [0.6.0] - 2026-07-01
### Changed
- Current toolchain updated to Swift 6.3.3 / Xcode 26.6 (macOS 26.5 Tahoe SDK); dropped the stale "Swift 6.2.4, Feb 2026 latest" framing.
- Liquid Glass section notes the `UIDesignRequiresCompatibility` opt-out is removed for apps built with Xcode 27.

### Added
- Forward-looking "Fall 2026 Releases (WWDC 2026, beta)" section: macOS 27 Golden Gate, Xcode 27, Swift 6.4, Foundation Models next-gen (image input, server models, Dynamic Profiles, pluggable models), Core AI, Spatial Preview.
- CoreAudio CFString Create-Rule trap (`takeRetainedValue`) in core-audio-tap.md.
- `SIGKILL (Code Signature Invalid)` dev-loop gotcha in distribution.md.
- CHANGELOG and upstream tracking established.

Verified against: swift@6.3.3, xcode@26.6
