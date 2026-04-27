# Sendable & Data Race Safety

## Table of Contents
- Sendable Protocol
- Implicit Sendable
- Making Types Sendable
- @unchecked Sendable
- @unchecked Sendable + Serial Queue Pattern
- @Sendable Closures
- `[#SendingRisksDataRace]` Shim for Apple Non-Sendable Types
- @preconcurrency import
- Swift 6 Language Mode
- Common Patterns

## Sendable Protocol

`Sendable` marks types safe to share across concurrency domains (actors, tasks):

```swift
// Value types with Sendable stored properties are implicitly Sendable
struct Point: Sendable {
    var x: Double
    var y: Double
}

// Enums with Sendable associated values.
// Note: `any Error` is NOT Sendable by default, so an enum carrying it cannot
// claim Sendable unless the error type is concrete and Sendable.
enum NetworkResult: Sendable {
    case success(Data)
    case failure(NetworkError)   // concrete, Sendable error type
}

// If you need to carry `any Error`, drop Sendable conformance or route through
// a Sendable wrapper.
```

## Implicit Sendable

These are automatically Sendable without explicit conformance:
- Primitive types (`Int`, `String`, `Bool`, `Double`, etc.)
- Structs where all stored properties are Sendable
- Enums where all associated values are Sendable
- Tuples of Sendable types
- Metatypes (`Int.Type`)
- Actors (isolated state)

## Making Types Sendable

### Final immutable classes
```swift
final class AppConfig: Sendable {
    let apiURL: URL
    let timeout: TimeInterval
    let maxRetries: Int

    init(apiURL: URL, timeout: TimeInterval, maxRetries: Int) {
        self.apiURL = apiURL
        self.timeout = timeout
        self.maxRetries = maxRetries
    }
}
```

Requirements for class Sendable:
- Must be `final`
- All stored properties must be `let` (immutable)
- All stored properties must be `Sendable`

### Sendable through actors
```swift
// Instead of making a mutable class Sendable, use an actor
actor UserSession {
    private var token: String?
    private var refreshTask: Task<String, Error>?

    func getToken() async throws -> String {
        if let token { return token }
        if let task = refreshTask { return try await task.value }

        let task = Task { try await refreshToken() }
        refreshTask = task
        let newToken = try await task.value
        token = newToken
        refreshTask = nil
        return newToken
    }
}
```

## @unchecked Sendable

Escape hatch when you ensure thread safety yourself:

```swift
// Thread-safe via internal locking
final class ThreadSafeCache<Key: Hashable & Sendable, Value: Sendable>: @unchecked Sendable {
    private let lock = NSLock()
    private var storage: [Key: Value] = [:]

    func get(_ key: Key) -> Value? {
        lock.withLock { storage[key] }
    }

    func set(_ key: Key, value: Value) {
        lock.withLock { storage[key] = value }
    }
}
```

**Use sparingly.** Prefer actors or restructuring to avoid `@unchecked Sendable`. Common legitimate uses:
- Wrapping C/Objective-C types with internal synchronization
- Types using `os_unfair_lock` or `NSLock` internally
- Bridging legacy code during migration

## @unchecked Sendable + Serial Queue Pattern

For classes that manage their own thread safety via a serial dispatch queue (common in audio/video recording), use `@unchecked Sendable` with `nonisolated(unsafe)` properties:

```swift
class AudioRecorder: NSObject, @unchecked Sendable, SCStreamOutput {
    private let audioQueue = DispatchQueue(label: "com.app.audio")

    // State accessed from background callbacks - nonisolated(unsafe) + serial queue
    nonisolated(unsafe) private var writer: AVAssetWriter?
    nonisolated(unsafe) private var systemInput: AVAssetWriterInput?
    nonisolated(unsafe) private var micInput: AVAssetWriterInput?
    nonisolated(unsafe) private var sessionStarted = false
    nonisolated(unsafe) private var stopped = false

    // SCStreamOutput callback - runs on audioQueue (background)
    nonisolated func stream(_ stream: SCStream,
                            didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
                            of type: SCStreamOutputType) {
        // All nonisolated(unsafe) state accessed exclusively on audioQueue
        guard !stopped, let input = systemInput, input.isReadyForMoreMediaData else { return }
        input.append(sampleBuffer)
    }

    // Callbacks passed at init, not set after - avoids data races
    nonisolated let onError: (@Sendable (Error) -> Void)?

    init(onError: (@Sendable (Error) -> Void)? = nil) {
        self.onError = onError
    }
}
```

With `defaultIsolation(MainActor.self)`, pair `@ObservationIgnored` with `nonisolated(unsafe)` for internal bookkeeping properties in `@Observable` classes:

```swift
@Observable
class ResourceManager: @unchecked Sendable {
    // UI-visible state (MainActor-isolated, observed by SwiftUI)
    var isRecording = false

    // Internal state (not for UI, accessed on background queue)
    @ObservationIgnored nonisolated(unsafe) private var writer: AVAssetWriter?
    @ObservationIgnored nonisolated(unsafe) private var listenerIDs: Set<AudioObjectID> = []
}
```

## @Sendable Closures

Functions passed across concurrency boundaries must be `@Sendable`:

```swift
// @Sendable closures cannot capture mutable state
func performInBackground(_ work: @Sendable () async -> Void) {
    Task.detached { await work() }
}

// OK - captures immutable value
let name = "test"
performInBackground {
    print(name)
}

// Error - captures mutable variable
var count = 0
performInBackground {
    count += 1 // Compiler error: mutation of captured var in @Sendable closure
}
```

## `[#SendingRisksDataRace]` Shim for Apple Non-Sendable Types

When an `SCStreamOutput` method, `AVAudioEngine` tap, or `AudioObjectPropertyListenerBlock` hands a `CMSampleBuffer` / `AVAudioPCMBuffer` / `AudioBufferList*` into actor-isolated code, Swift 6 flags the parameter with the `SendingRisksDataRace` diagnostic group (canonical identifier used with `-Werror` / `-Wwarning`; the compiler prints it as `[#SendingRisksDataRace]` after each error line — see https://docs.swift.org/compiler/documentation/diagnostics/sending-risks-data-race). The type isn't `Sendable` and can't cross isolation boundaries by the usual rules.

**If the callback already runs on the target executor** (e.g. SCStream's `sampleHandlerQueue` is your actor's `audioQueue`, or the `AudioObjectPropertyListenerBlock` was registered on that queue), the "data race" doesn't exist - the callback and the actor are literally the same isolation domain. The idiomatic workaround is a one-line rebind:

```swift
nonisolated func stream(_ stream: SCStream,
                        didOutputSampleBuffer sampleBuffer: CMSampleBuffer,
                        of type: SCStreamOutputType) {
    // Rebinding breaks the sending check. Safe because this callback runs on
    // audioQueue, which IS this actor's executor.
    nonisolated(unsafe) let buffer = sampleBuffer
    self.assumeIsolated { iso in
        iso.handleSampleBuffer(buffer, type: type)
    }
}
```

Reflexively adding an extra `audioQueue.async { ... }` to "fix" the warning is worse than the shim - it adds a redundant queue hop *and* can introduce the ordering bug described in `actors-isolation.md` ("Don't re-dispatch when the block already runs on the actor's executor").

**When NOT to use this shim**: if the callback fires on a queue that is *not* your actor's executor, the data race is real - you need a proper hop (`actor.method(buffer)` or `queue.async { assumeIsolated { ... } }`). The shim lies only when the callback is already running in the actor's isolation domain.

## @preconcurrency import

Apple framework types like `AVAudioPCMBuffer`, `AVAssetWriter`, `CMSampleBuffer`, and `AVAudioFormat` lack `Sendable` conformance. Use `@preconcurrency import` to suppress warnings while Apple updates their frameworks:

```swift
@preconcurrency import AVFoundation  // Covers AVAudioPCMBuffer, AVAssetWriter, etc.
@preconcurrency import CoreMedia     // Covers CMSampleBuffer, CMTime, etc.
@preconcurrency import AudioToolbox  // Covers C block types used by CoreAudio listeners
```

This treats the imported types as implicitly `Sendable` (matching pre-concurrency behavior). When Apple adds proper annotations, remove `@preconcurrency` to get full checking.

### For deinit accessing non-Sendable C block types

`deinit` that needs to remove a CoreAudio listener block (`AudioObjectPropertyListenerBlock`) or invoke AudioToolbox cleanup C APIs can fail to compile against a plain `import AudioToolbox` because the block typealias isn't `Sendable`. `@preconcurrency import AudioToolbox` unblocks this case without resorting to `@unchecked Sendable` on the whole enclosing type.

`KeyPath<Root, Value>` is not unconditionally `Sendable` in Swift 6 (SE-0418): keypath-literal captures are inferred Sendable only when the captures themselves are Sendable, and a stored `KeyPath` property needs an explicit `& Sendable` constraint. This bites `KeyPathComparator`-based `Table` sort on Swift 6.2 / Xcode 26.0-26.2 (tracked as swiftlang/swift #75852 and #84983). Most cases are resolved in Swift 6.3 / Xcode 26.3+, but verify against the toolchain you target. Workaround on affected versions: pre-sort data in the source and avoid `KeyPathComparator` entirely.

## Swift 6 Language Mode

Enable strict data race safety:

```swift
// Package.swift
.target(
    name: "MyApp",
    swiftSettings: [.swiftLanguageMode(.v6)]
)
```

What Swift 6 mode enforces:
- All `Sendable` violations are errors (not warnings)
- Global variables must be isolated or Sendable
- Closures passed across isolation boundaries must be `@Sendable`
- Protocol conformances must respect isolation

### Gradual migration
```swift
// Start with strict concurrency checking as warnings
.target(
    name: "MyApp",
    swiftSettings: [
        .swiftLanguageMode(.v5),
        .enableUpcomingFeature("StrictConcurrency"),
    ]
)
```

Then fix warnings before enabling `.v6`.

## Common Patterns

### Global state
```swift
// BAD: Mutable global
var globalCache: [String: Data] = [:] // Error in Swift 6

// GOOD: Actor-isolated
actor GlobalCache {
    static let shared = GlobalCache()
    private var storage: [String: Data] = [:]

    func get(_ key: String) -> Data? { storage[key] }
    func set(_ key: String, data: Data) { storage[key] = data }
}

// GOOD: nonisolated(unsafe) for truly thread-safe globals
nonisolated(unsafe) let logger = Logger(subsystem: "com.app", category: "main")
```

### Delegate patterns
```swift
// Protocol must be MainActor-isolated or Sendable
@MainActor
protocol DocumentDelegate: AnyObject {
    func documentDidSave(_ document: Document)
    func documentDidFail(_ document: Document, error: Error)
}
```

### Migrating ObservableObject
```swift
// Old (pre-Swift 5.9)
class ViewModel: ObservableObject {
    @Published var items: [Item] = []
}

// New
@Observable
@MainActor
final class ViewModel {
    var items: [Item] = []
}

// With default isolation (Swift 6.2), @MainActor is implicit
@Observable
final class ViewModel {
    var items: [Item] = []
}
```
