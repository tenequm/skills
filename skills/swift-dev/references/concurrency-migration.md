# Concurrency: Migration and Swift 6.4 Changes

Moving code to Swift 6 strict concurrency and default MainActor isolation (GCD, Combine and `ObservableObject` to async and `@Observable`), the compile errors and runtime traps that migration surfaces, per-declaration warning control, and the Swift 6.4 language changes.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: Swift blocks compiled with `swiftc -emit-sil` in Swift 6 mode with default MainActor isolation for iOS 26 and macOS 15 targets (6.4 runtime APIs at iOS 27 / macOS 27); `swift package migrate` run on a scratch package; every quoted diagnostic reproduced; upcoming-feature names checked against the compiler.

## Contents
- Order of operations
- Automated migration
- Upcoming feature flags
- GCD, Combine and ObservableObject to async
- Common errors
- Default MainActor isolation: compile errors
- Default MainActor isolation: runtime traps
- Per-declaration warning control
- Swift 6.4 language changes

## Order of operations

New targets: Swift 6 mode, default MainActor isolation and Approachable Concurrency from the start (settings in concurrency-isolation.md).

Existing code, one module at a time:
1. Swift 5 mode plus `StrictConcurrency` (SwiftPM `.enableUpcomingFeature("StrictConcurrency")`, Xcode `SWIFT_STRICT_CONCURRENCY = complete`). Everything is a warning.
2. Fix warnings bottom-up: leaf modules first, value types `Sendable`, shared mutable classes to actors or `@MainActor`.
3. Switch the module to Swift 6 mode (`.swiftLanguageMode(.v6)` / `SWIFT_VERSION = 6.0`).
4. Add `NonisolatedNonsendingByDefault` and `InferIsolatedConformances` (or Approachable Concurrency), then default MainActor isolation on UI modules.
5. Remove now-redundant `@MainActor` annotations; mark off-main work `@concurrent`.

Region-isolation errors (`sending ... risks causing data races`) are emitted by a SIL pass that only runs once type checking succeeds, and `swiftc -typecheck` never shows them. Expect a second wave of errors after the first batch is fixed.

## Automated migration

```bash
swift package migrate --to-feature NonisolatedNonsendingByDefault,ExistentialAny
swift package migrate --target AppFeature --to-feature InferIsolatedConformances
```

It builds, applies the fix-its, and adds `.enableUpcomingFeature(...)` to the manifest. For `NonisolatedNonsendingByDefault` it preserves behavior by inserting `@concurrent` on every `nonisolated async` function; remove it where running on the caller's actor is what you want. In Xcode, set an upcoming-feature setting to `MIGRATE` (for example `SWIFT_UPCOMING_FEATURE_NONISOLATED_NONSENDING_BY_DEFAULT = MIGRATE`) to get the same fix-its as warnings. Run on a clean tree, one feature at a time, and review the diff.

## Upcoming feature flags

Each is `.enableUpcomingFeature("<name>")` / `-enable-upcoming-feature <name>`:

| Flag | Effect | In Swift 6 mode |
|---|---|---|
| `StrictConcurrency` | full data-race checking in Swift 5 mode, as warnings | always on |
| `InferSendableFromCaptures` | closures and key paths infer `Sendable` from captures | always on |
| `GlobalActorIsolatedTypesUsability` | global-actor-isolated types usable in more contexts | always on |
| `DisableOutwardActorInference` | a property wrapper's `@MainActor` no longer isolates the containing type | always on |
| `NonisolatedNonsendingByDefault` | `nonisolated async` runs on the caller's actor | opt in |
| `InferIsolatedConformances` | conformances of global-actor types are isolated to that actor | opt in |
| `ExistentialAny` | `any` required on existential types | opt in |
| `InternalImportsByDefault` | imports are `internal` unless marked `public` | opt in |
| `MemberImportVisibility` | members need their module imported in this file (Xcode 27 templates enable it) | opt in |

A misspelled feature name is silently ignored - no warning on Swift 6.4. Enabling one already implied by Swift 6 mode prints `upcoming feature 'X' already enabled as of the Swift 6 language mode`.

## GCD, Combine and ObservableObject to async

| Before | After |
|---|---|
| `DispatchQueue.global().async { ... DispatchQueue.main.async { } }` | `@concurrent` function, `await` it from main-actor code |
| `DispatchGroup` enter/leave/notify | `withThrowingTaskGroup` |
| private serial queue + `queue.sync` | `actor` |
| `Timer.scheduledTimer(repeats: true)` | `while !Task.isCancelled { ...; try? await Task.sleep(for:) }` in a stored task |
| completion handler | `async` function; wrap old APIs with a continuation (concurrency-tasks.md) |
| `publisher.sink` | `for await` over an `AsyncSequence` |
| `ObservableObject` + `@Published` | `@Observable` class |
| `@StateObject` / `@ObservedObject` / `@EnvironmentObject` | `@State` / plain property or `@Bindable` / `@Environment(Type.self)` |
| `.receive(on: DispatchQueue.main)` | nothing - main-actor code resumes on main after `await` |

```swift
import Foundation
import Observation

nonisolated struct Article: Decodable, Sendable { let title: String }

@concurrent
func fetchArticles(from url: URL) async throws -> [Article] {
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode([Article].self, from: data)
}

@Observable
final class ArticlesModel {                        // MainActor via default isolation
    var articles: [Article] = []
    var isLoading = false
    var error: (any Error)?

    func load(_ urls: [URL]) async {
        isLoading = true
        defer { isLoading = false }
        do {
            articles = try await withThrowingTaskGroup(of: [Article].self) { group in
                for url in urls { group.addTask { try await fetchArticles(from: url) } }
                var all: [Article] = []
                for try await batch in group { all += batch }   // not group.reduce, see below
                return all
            }
        } catch {
            self.error = error
        }
    }

    func observeLowPowerMode() async {
        for await _ in NotificationCenter.default.notifications(named: .NSProcessInfoPowerStateDidChange) {
            articles.removeAll()
        }
    }

    func poll(_ urls: [URL]) async {
        while !Task.isCancelled {
            await load(urls)
            try? await Task.sleep(for: .seconds(60))
        }
    }
}

actor TokenStore {
    private var tokens: [String: String] = [:]
    func token(for account: String) -> String? { tokens[account] }
    func set(_ token: String, for account: String) { tokens[account] = token }
}
```

`try await group.reduce(into: []) { ... }` inside actor-isolated code (any `@MainActor` or MainActor-default function) fails with `sending 'group' risks causing data races`: `AsyncSequence.reduce` is not isolation-aware. Iterate with `for try await`.

## Common errors

| Diagnostic | Fix |
|---|---|
| `sending value of non-Sendable type '() async -> ()' risks causing data races` (a `Task` capturing a non-`Sendable` object you use again afterwards) | stop using it after the hand-off, make it `Sendable` (struct, `final` + `let`, `Mutex`), or make it an actor |
| `main actor-isolated property 'x' can not be referenced from a nonisolated context` | make the caller `@MainActor`, or `async` and `await` the access |
| `var 'cache' is not concurrency-safe because it is nonisolated global shared mutable state` (also `static var`) | `let` of a `Sendable` type, `@MainActor static var`, a `Mutex`, or an actor; `nonisolated(unsafe)` only when you synchronize it yourself |
| `conformance of 'X' to protocol 'P' crosses into main actor-isolated code` | `nonisolated` members, or an isolated conformance `X: @MainActor P` (concurrency-isolation.md) |
| `main actor-isolated conformance of 'X' to 'Decodable' cannot be used in @concurrent context` | `nonisolated struct X` |
| `... can not be mutated from a Sendable closure` (a warning for many Apple completion handlers) | a real race, not noise: hop with `Task { @MainActor in }` or keep the work nonisolated |

## Default MainActor isolation: compile errors

Turning on `-default-isolation MainActor` isolates every unannotated declaration, which surfaces these (each reproduced on Xcode 27):

- Types decoded, hashed or compared off-main need `nonisolated struct`/`enum`: their conformances and computed members are otherwise main-actor-isolated.
- `KeyPathComparator(\Row.date)` fails with `type 'KeyPath<Row, Date>' does not conform to the 'Sendable' protocol` unless `Row` is `nonisolated` (affects `Table` sorting on macOS).
- Static constants in extensions become main-actor-isolated: `extension UTType { static let sketch = ... }` cannot be read from nonisolated code (`main actor-isolated static property 'sketch' can not be referenced from a nonisolated context`). Write `nonisolated static let`.
- `UIApplicationDelegate` is `@MainActor` (`NS_SWIFT_UI_ACTOR`), so conforming makes the class main-actor-isolated. `NSApplicationDelegate` is not; without default isolation an app delegate helper that touches `NSApp` warns (`main actor-isolated var 'NSApp' can not be referenced from a nonisolated context`). Mark the class `@MainActor`.
- In a module without default isolation, `@objc` target-action methods on coordinators that touch UIKit/AppKit views need `@MainActor`.
- Imported mutable C globals are errors in Swift 6 mode regardless: `kAXTrustedCheckOptionPrompt` gives `reference to var 'kAXTrustedCheckOptionPrompt' is not concurrency-safe`. Use its value: `AXIsProcessTrustedWithOptions(["AXTrustedCheckOptionPrompt": true] as CFDictionary)`.

## Default MainActor isolation: runtime traps

These compile cleanly and crash (`dispatch_assert_queue_fail` / `EXC_BREAKPOINT`) because Swift 6 checks isolation at runtime where the compiler cannot.

**Closure isolation inheritance.** A closure written in main-actor code is main-actor-isolated unless its parameter type is `@Sendable`. An Objective-C API whose block type is not `Sendable` and that calls it on another thread traps on the first call. Most Apple completion handlers are now `@Sendable` (you get a compile-time warning instead), but `AVAudioNode`'s tap block is `NS_SWIFT_NONSENDABLE`:

```swift
import AVFAudio
import Synchronization

nonisolated final class PeakMeter: Sendable {
    private let peak = Mutex<Float>(0)
    func record(_ buffer: AVAudioPCMBuffer) {
        guard let samples = buffer.floatChannelData?[0] else { return }
        let frames = Int(buffer.frameLength)
        peak.withLock { value in
            for i in 0..<frames { value = max(value, abs(samples[i])) }
        }
    }
}

final class Recorder {                             // MainActor via default isolation
    private let engine = AVAudioEngine()
    private let meter = PeakMeter()
    private var taps = 0

    func startTrapping() {
        let input = engine.inputNode
        // Compiles silently, then traps on the audio thread: the closure inherited @MainActor.
        input.installTap(onBus: 0, bufferSize: 4096, format: input.outputFormat(forBus: 0)) { buffer, _ in
            self.taps += 1
        }
    }

    func start() throws {
        let input = engine.inputNode
        let meter = meter
        // A @Sendable closure is nonisolated: no inherited actor, no runtime check.
        let tap: @Sendable (AVAudioPCMBuffer, AVAudioTime) -> Void = { buffer, _ in meter.record(buffer) }
        input.installTap(onBus: 0, bufferSize: 4096, format: input.outputFormat(forBus: 0), block: tap)
        try engine.start()
    }
}
```

`installTap(onBus:bufferSize:format:block:)` is deprecated in iOS 27 / macOS 27; the replacement is imported only as `__installTap(onBus:bufferSize:format:error:block:)`, with the same non-`Sendable` block type.

**Isolated members called from a framework thread.** `MainActor.assumeIsolated`, an isolated conformance (`X: @MainActor P`) and an actor's `assumeIsolated` all trap when entered off their executor. Each one is an assertion about the callback queue - check the framework's documented queue before relying on it.

**Callbacks assigned after init.** A `var onError: ((Error) -> Void)?` set from main-actor code and read from a background callback is a data race. Pass callbacks at init as `nonisolated let onError: (@Sendable (any Error) -> Void)?`.

**deinit.** `deinit` is nonisolated; touching main-actor state there is an error, and cleanup state copied into `nonisolated(unsafe)` mirrors drifts out of sync. Use `isolated deinit` (concurrency-isolation.md).

## Per-declaration warning control

`@diagnose(<group>, as: error | warning | ignored, reason: "...")` (SE-0522, Swift 6.4, no flag) overrides module-wide warning settings (`-warnings-as-errors`, `-Werror <group>`, SwiftPM `.treatWarning(_:as:)`) for one declaration's signature and body. Group names are the bracketed tags in diagnostics, such as `[#DeprecatedDeclaration]`.

```swift
@available(*, deprecated, message: "use newAPI()")
func oldAPI() {}

@diagnose(DeprecatedDeclaration, as: warning, reason: "legacy bridge until 2.0")
func bridgeToLegacy() {
    oldAPI()   // a warning even under -warnings-as-errors
}
```

It applies to types, extensions, functions, initializers, accessors, `import` statements and more. It changes warnings only: Swift 6 concurrency errors cannot be lowered. During a Swift 5 mode migration, `@diagnose(SendingRisksDataRace, as: ignored, reason: "...")` silences that warning for one declaration and leaves the rest of the module strict. An unknown group name is an error (`the diagnostic group identifier 'X' is unknown`).

## Swift 6.4 language changes

All compile without experimental flags on Swift 6.4. Language features work at any deployment target; the runtime APIs need iOS 27 / macOS 27.

| Proposal | Feature | Needs | Details |
|---|---|---|---|
| [SE-0522](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0522-source-warning-control.md) | `@diagnose` per-declaration warning control | - | above |
| [SE-0518](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0518-tilde-sendable.md) | `~Sendable` | - | concurrency-isolation.md |
| [SE-0493](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0493-defer-async.md) | `await` in `defer` | - | concurrency-tasks.md |
| [SE-0504](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0504-task-cancellation-shields.md) | `withTaskCancellationShield` | iOS 27 / macOS 27 | concurrency-tasks.md |
| [SE-0528](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0528-noncopyable-continuation.md) | noncopyable `Continuation`, `withContinuation(of:throwing:)` | iOS 27 / macOS 27 | concurrency-tasks.md |
| [SE-0506](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0506-advanced-observation-tracking.md) | `withObservationTracking(options:)`, `withContinuousObservation` | iOS 27 / macOS 27 | concurrency-tasks.md |
| [SE-0502](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0502-exclude-private-from-memberwise-init.md) | memberwise init skips less-visible properties that have initial values | - | below |
| [SE-0507](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0507-borrow-accessors.md) | `borrow` / `mutate` accessors | - | below |

Memberwise initializers (SE-0502): adding a `private var` with an initial value no longer makes the synthesized initializer `private`.

```swift
struct Draft {
    var title: String
    var body: String
    private var revision = 0
}

let draft = Draft(title: "Notes", body: "")   // before 6.4: initializer inaccessible due to 'private'
```

The rule caps at `internal`: a `public` struct still needs a hand-written `public init` for other modules (including test targets).

Borrow and mutate accessors (SE-0507) expose stored storage without a copy and without a coroutine; the returned value must be stored storage that outlives the access, never a local or temporary.

```swift
struct Wrapper<Element: ~Copyable>: ~Copyable {
    private var storage: Element
    init(_ element: consuming Element) { storage = element }

    var element: Element {
        borrow { storage }
        mutate { &storage }
    }
}
```

They matter for noncopyable containers and hot paths; app code rarely needs them. Also on Swift 6.4 without a flag: `@available(anyAppleOS 27.0, *)` and `#available(anyAppleOS 27.0, *)` (the SDK uses this spelling throughout). `weak let` arrived earlier, in Swift 6.3.
