# Fall 2026 Releases (WWDC 2026)

Announced at WWDC 2026 (June 8, 2026), shipping fall 2026. As of 2026-08-20, Xcode 27 is at **beta 5** and macOS 27 at **beta 6**. Build against the shipping stack (Swift 6.3.3 / Xcode 26.6 / macOS 26.6.2 Tahoe) unless you specifically target these betas.

Sources: [Apple Newsroom, 2026-06-08](https://www.apple.com/newsroom/2026/06/apple-aids-app-development-with-new-intelligence-frameworks-and-advanced-tools/); [WWDC26 "What's new in Swift"](https://developer.apple.com/videos/play/wwdc2026/262); [Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes); [macOS 27 release notes](https://developer.apple.com/documentation/macos-release-notes/macos-27-release-notes).

## OS and toolchain

- **macOS 27 Golden Gate** (beta 6, build 26A5416b, 2026-08-17) - next macOS; Apple-silicon only. macOS 26.6.2 Tahoe is the current shipping release until fall.
- **Xcode 27** (beta 5, build 27A5237l, 2026-08-10) - agentic coding with Anthropic/Google/OpenAI models plus MCP plug-ins and the Agent Client Protocol; Apple-silicon only, ~30% smaller. Requires macOS Tahoe 26.4 or later. Gemini also landed in stable Xcode 26.6. Beta 5 previews an MCP server that runs without an open Xcode workspace and can grant code-signed agents long-lived permission over a directory tree; enable it with `sudo xcrun mcp-server enable`.
- **Swift 6.4** (beta; shipping toolchain is still 6.3.3) - ships inside the Xcode 27 beta ("Xcode 27 beta 5 includes Swift 6.4 and SDKs for iOS 27, iPadOS 27, tvOS 27, watchOS 27, macOS 27, and visionOS 27"), and the `release/6.4.x` branch is cut with daily snapshots on swift.org. Features: targeted warning suppression (SE-0522), `~Sendable` to explicitly mark a type non-Sendable (SE-0518), Task Cancellation Shields (SE-0504), `Continuation` (SE-0528), `async` calls in `defer` bodies (SE-0493), borrow/mutate accessors (SE-0507), a memberwise initializer that excludes private initialized properties (SE-0502), and Advanced Observation Tracking (SE-0506).

Two version-gate corrections worth carrying:

- `weak let` (SE-0481) is **not** a 6.4 feature - it shipped in Swift 6.3 and is already available in the pinned toolchain.
- `anyAppleOS` is **not** gated on 6.4 either - it compiles on 6.3.3 behind `-enable-experimental-feature AnyAppleOSAvailability`. Without the flag the compiler names it for you: `error: any Apple OS requires '-enable-experimental-feature AnyAppleOSAvailability'`.

## Xcode 27 build-breakers

These bite when you first open a project in Xcode 27, before any new API is adopted. Check them ahead of the beta.

- **The ld64 linker is gone.** "The ld64 linker has been removed and the `-ld_classic` option is no longer supported. (165165518)" Any project still carrying `-ld_classic` in `OTHER_LDFLAGS` - a flag Apple itself prescribed as a workaround in Xcode 15 - fails to link. Remove it.
- **Clang module names must be globally unique per dependency scan.** The optimized Swift dependency scanner now requires that "every Clang module reachable from a single Swift dependency-scan action must have a unique module name. If two module maps visible to the same scan declare a Clang module with the same name, the scan may report an error." The common cause is vendored third-party sources shipping a `module.modulemap` that redeclares an SDK module.
- **Universal binaries are no longer the default at deployment target 27.0+.** "The `ARCHS_STANDARD` build setting will no longer include x86_64 when `MACOSX_DEPLOYMENT_TARGET` or `DRIVERKIT_DEPLOYMENT_TARGET` >= 27.0." Add x86_64 to `ARCHS` explicitly if you still ship Intel. Xcode 27 itself installs only on Apple silicon.
- **SE-0508 source break.** "A computed property with both an `init` accessor and an array/dictionary literal initial value will no longer compile if the getter is declared before the `init` accessor." Workaround: declare the `init` accessor first.
- **libc++ floor raised.** The minimum supported C++ deployment target on macOS moves to 11.0, and `multimap`/`multiset::find` no longer necessarily returns an iterator to the first equal element.

## Document apps: concurrency and new protocols

macOS 27 adds `ReadableDocument` / `WritableDocument`, plus a combined `Document` protocol for the common read-and-write case. As of beta 6 the older protocols are formally deprecated - not merely superseded:

> You can now use the `Document` protocol for representing documents in `DocumentGroup`. This protocol combines `ReadableDocument` and `WritableDocument` for common read-and-write cases. Use `Document` instead of `ReferenceFileDocument` and `FileDocument`, which are now deprecated.

New `DocumentGroup` initializers adopting them expose an `Observable` `URLDocumentConfiguration`, let you disable document creation for editing-only apps, and present custom UI before any document is opened.

The isolation contract changed in a way that silently defeats off-main I/O if you carry old annotations forward:

> The `read(from:progress:)` and `write(content:to:previous:progress:)` requirements of `DocumentReader` and `DocumentWriter` are declared with `@concurrent` instead of `nonisolated`. With approachable-concurrency defaults that infer `MainActor` isolation, an unannotated `nonisolated` async method runs on the main actor, defeating the intent of off-main reading and writing. Conforming types that previously used `nonisolated` should switch to `@concurrent` to match.

`makeDocument:` and `makeReadableDocument:` closures passed to `DocumentGroup` initializers are now `@MainActor`-isolated.

## Frameworks

- **Foundation Models next-gen** - the single native Swift API now accepts image input and adds server models running on Private Cloud Compute via `PrivateCloudComputeLanguageModel`, which Apple frames as a one-line swap for `SystemLanguageModel` and which requires the `com.apple.developer.private-cloud-compute` entitlement. `DynamicProfile` (with `LanguageModelSession.Profile` and `DynamicInstructions`) swaps model/tools/instructions mid-session. A new `LanguageModel` protocol makes third-party models (Claude, Gemini) pluggable behind the same API. `ContextOptions` arrives here too - despite the name it configures what appears in the prompt, not a trimming policy. `LanguageModelSession.GenerationError` is **deprecated** as of 27.0 in favour of `LanguageModelError` / `SystemLanguageModel.Error` / `LanguageModelSession.Error`, with `exceededContextWindowSize` renamed `contextSizeExceeded`; Apple states you must update to Xcode 27 to catch the new types before submitting. It remains correct under the macOS 26.5 SDK you build against today.
- **Core AI** - a brand-new framework, distinct from Foundation Models, for loading and running full-scale LLMs on device, optimized for the Neural Engine and unified memory. Public surface includes `AIModel`, `AIModelAsset`, `AIModelCache`, `InferenceFunction`, `NDArray`, `ComputeUnitKind`, and `SpecializationOptions`, plus a background-inference entitlement `com.apple.developer.background-tasks.continued-processing.inference`. No `updates/coreai` change log exists yet (404), so the framework index is the only source.
- **SwiftData** - a new data-store observation surface: `ResultsObserver` delivers real-time updates for models matching fetch criteria, and `HistoryObserver` observes remote model changes. `@Query(...sectionBy:)` returns `SectionedResults`/`ResultsSection` for grouped queries, and `Schema.Attribute.Option.codable` lets `Codable` types - including ones you do not control - be stored directly in a model.
- **SwiftUI** - reorderable list/grid containers, faster layout, and lazier `@State` initialization (back-deployed). In apps built with the macOS 27 SDK, `List` accepts drops in two cases that previously did not work: drags with compatible transfer representations into reorderable content even without `.reorderableItem`, and `.dropDestination(...)` declared on a list item. SwiftUI also now hides menu item symbol images in most contexts by default - use `.labelStyle(.titleAndIcon)` to opt a menu item back in. New **Spatial Preview** framework streams 3D content from a Mac to Apple Vision Pro.
- **Previews** - code inside `#Preview` now explicitly runs on the main actor, so it can call main-actor-isolated APIs without concurrency warnings or runtime check failures.

## Liquid Glass becomes mandatory

Apps rebuilt with the Xcode 27 SDK can no longer opt out of Liquid Glass - the `UIDesignRequiresCompatibility` key is ignored. Under Xcode 26 the key still works as a temporary migration aid. A new system transparency slider lets users tune the effect.
