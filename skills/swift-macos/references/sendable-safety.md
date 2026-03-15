# Sendable & Data Race Safety

## Table of Contents
- Sendable Protocol
- Implicit Sendable
- Making Types Sendable
- @unchecked Sendable
- @unchecked Sendable + Serial Queue Pattern
- @Sendable Closures
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

// Enums with Sendable associated values
enum Result: Sendable {
    case success(Data)
    case failure(Error) // Error is Sendable
}
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

## @preconcurrency import

Apple framework types like `AVAudioPCMBuffer`, `AVAssetWriter`, `CMSampleBuffer`, and `AVAudioFormat` lack `Sendable` conformance. Use `@preconcurrency import` to suppress warnings while Apple updates their frameworks:

```swift
@preconcurrency import AVFoundation  // Covers AVAudioPCMBuffer, AVAssetWriter, etc.
@preconcurrency import CoreMedia     // Covers CMSampleBuffer, CMTime, etc.
```

This treats the imported types as implicitly `Sendable` (matching pre-concurrency behavior). When Apple adds proper annotations, remove `@preconcurrency` to get full checking.

`KeyPath` is also not `Sendable` in Swift 6. This breaks `Table` sort with `KeyPathComparator`. Workaround: pre-sort data in the source and avoid `KeyPathComparator` entirely.

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
