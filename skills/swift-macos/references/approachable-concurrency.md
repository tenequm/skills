# Approachable Concurrency (Swift 6.2)

## Table of Contents
- Vision & Philosophy
- Default MainActor Isolation
- @concurrent Attribute
- Nonisolated Async Changes
- Enabling in Xcode
- Migration Strategy
- Runtime Pitfalls with Default Isolation

## Vision & Philosophy

Swift 6.2 addresses feedback that Swift Concurrency was too difficult to adopt. The key insight: most app code doesn't need concurrency. The new model follows progressive disclosure:

1. **Phase 1** - Write sequential code. Default isolation keeps everything on main actor.
2. **Phase 2** - Add `async/await` for suspension without introducing parallelism.
3. **Phase 3** - Opt into parallelism with `@concurrent` when you need performance.

## Default MainActor Isolation

### Enabling

Package.swift:
```swift
.executableTarget(
    name: "MyApp",
    swiftSettings: [
        .defaultIsolation(MainActor.self),
    ]
)
```

Xcode: Build Settings > Swift Compiler - Upcoming Features > Default Isolation > MainActor

Per-file opt-out:
```swift
// At the top of a specific file
defaultIsolation(nil)
```

### What changes

With `-default-isolation MainActor`:

```swift
// Before: needed explicit annotations
@MainActor
class ViewModel {
    @MainActor
    var items: [Item] = []

    @MainActor
    func refresh() async { /* ... */ }
}

// After: everything is implicitly @MainActor
class ViewModel {
    var items: [Item] = []  // protected by MainActor

    func refresh() async {
        items = try await fetchItems() // suspends, resumes on main
    }
}
```

### What's NOT affected
- Types in libraries imported without default isolation
- Protocol conformances to protocols defined outside the module
- `@concurrent` functions (explicit opt-out)
- Types explicitly marked `nonisolated`

### Interaction with existing code

```swift
// This "just works" now
struct ContentView: View {
    @State private var items: [Item] = []

    var body: some View {
        List(items) { item in
            Text(item.name)
        }
        .task {
            // No actor-isolation errors - everything on MainActor
            items = try await loadItems()
        }
    }
}
```

## @concurrent Attribute

Explicitly request execution on the concurrent thread pool:

```swift
// Heavy computation - run off main actor
@concurrent
func compressImage(_ data: Data, quality: Double) async throws -> Data {
    // Runs on concurrent pool, keeping main actor free
    let source = CGImageSourceCreateWithData(data as CFData, nil)!
    // ... expensive processing
    return compressedData
}

// I/O-bound work
@concurrent
func loadFileContents(_ url: URL) async throws -> String {
    try String(contentsOf: url, encoding: .utf8)
}

// Call from MainActor context
func handleImport() async throws {
    // Automatically dispatched to concurrent pool
    let data = try await loadFileContents(fileURL)
    // Back on MainActor after await
    self.content = data
}
```

### When to use @concurrent
- CPU-intensive work (image processing, data parsing, compression)
- Large file I/O
- Expensive computations (sorting large datasets, cryptography)
- Any work that would cause UI jank if run on the main actor

### When NOT to use @concurrent
- Simple property access or state updates
- UI-related operations
- Short synchronous operations
- Functions that primarily call other async functions (just let them suspend)

## Nonisolated Async Changes

In Swift 6.2, `nonisolated async` functions behave differently:

```swift
// Swift 6.1: nonisolated async always ran on global pool
// Swift 6.2: nonisolated async runs in caller's context

class DataProcessor {
    nonisolated func process() async -> Data {
        // Swift 6.1: This ran on the global concurrent pool
        // Swift 6.2: This runs wherever the caller is (e.g., MainActor)
        return computeData()
    }
}

// To get the old behavior (run on concurrent pool), use @concurrent:
class DataProcessor {
    @concurrent
    func process() async -> Data {
        return computeData() // Explicitly on concurrent pool
    }
}
```

This change is enabled via the `NonisolatedNonsendingByDefault` upcoming feature flag, which is on by default in Swift 6.2 with default isolation.

## Migration Strategy

### From Swift 5 / no concurrency
1. Enable `-default-isolation MainActor` on your target
2. Build and fix errors (mostly around library boundaries)
3. Mark expensive functions with `@concurrent`
4. Test thoroughly - behavior change is mostly in async function execution context

### From Swift 6.0/6.1 with explicit @MainActor
1. Enable default isolation
2. Remove redundant `@MainActor` annotations
3. Replace `nonisolated` background work with `@concurrent`
4. Remove unnecessary `Sendable` annotations (compiler infers more)

### Gradual adoption
```swift
// Keep per-file control
// File: NetworkLayer.swift
defaultIsolation(nil) // This file opts out of default isolation

actor NetworkClient {
    // Explicitly managed isolation
}
```

## Runtime Pitfalls with Default Isolation

These issues compile cleanly but crash at runtime. The compiler does not always catch them.

### Closure isolation inheritance (most dangerous)

Closures defined inside MainActor-isolated methods inherit MainActor isolation. When passed to APIs that call them on background threads, Swift 6 runtime checks the executor and crashes with `dispatch_assert_queue_fail` / SIGTRAP.

Affected APIs include `AVAudioEngine.installTap`, `NotificationCenter.addObserver` with `queue: nil`, `DispatchSource.setEventHandler`, and `NSSetUncaughtExceptionHandler`.

```swift
// CRASHES at runtime - closure inherits MainActor isolation but runs on audio thread:
func startCapture() {
    engine.inputNode.installTap(onBus: 0, bufferSize: 1024, format: fmt) { buffer, time in
        self.process(buffer) // dispatch_assert_queue_fail
    }
}

// FIX - extract to @Sendable typed variable to break isolation inheritance:
func startCapture() {
    let handler: @Sendable (AVAudioPCMBuffer, AVAudioTime) -> Void = { [weak self] buffer, time in
        self?.process(buffer) // nonisolated, safe on any thread
    }
    engine.inputNode.installTap(onBus: 0, bufferSize: 1024, format: fmt, block: handler)
}
```

Same fix needed for NotificationCenter observers:
```swift
// CRASHES - observer closure inherits MainActor, but CoreAudio fires on I/O thread:
NotificationCenter.default.addObserver(
    forName: .AVAudioEngineConfigurationChange, object: engine, queue: nil
) { [weak self] _ in self?.handleConfigChange() }

// FIX - either use queue: .main or extract to @Sendable:
NotificationCenter.default.addObserver(
    forName: .AVAudioEngineConfigurationChange, object: engine, queue: .main
) { [weak self] _ in self?.handleConfigChange() }
```

### deinit is always nonisolated

`deinit` cannot access MainActor-isolated properties or call MainActor-isolated methods. Properties needed for cleanup must be `nonisolated(unsafe)`:

```swift
@Observable
class ResourceManager: @unchecked Sendable {
    // Pair @ObservationIgnored with nonisolated(unsafe) for internal state
    @ObservationIgnored nonisolated(unsafe) private var listenerID: AudioObjectID?

    deinit {
        // Can access nonisolated(unsafe) properties directly
        if let id = listenerID {
            AudioObjectRemovePropertyListener(id, &address, callback, nil)
        }
    }
}
```

### Types and enums need explicit nonisolated for cross-isolation use

With default isolation, all types are MainActor. Value types and enums used in background callbacks or `Task.detached` need explicit opt-out:

```swift
// Without this, using LevelSource in a nonisolated SCStreamOutput callback errors:
nonisolated enum LevelSource: Sendable {
    case mic, system, both
}

// Codable structs used across isolation boundaries:
nonisolated struct TranscriptSegment: Codable, Sendable {
    let timestamp: Double
    let text: String
}
```

### Non-Sendable Apple framework types

Several Apple types lack Sendable conformance. Use `@preconcurrency import` to suppress warnings:

```swift
@preconcurrency import AVFoundation // Suppresses AVAudioPCMBuffer, AVAssetWriter Sendable warnings

// KeyPath is not Sendable - Table sort with KeyPathComparator breaks:
// Instead of: @State var sortOrder = [KeyPathComparator(\Item.date)]
// Pre-sort data in the source and avoid KeyPathComparator entirely.

// AVAssetWriter can't cross TaskGroup boundary (sending parameter).
// Use a simple Task instead of TaskGroup for timeout patterns.
```

### Methods called from nonisolated contexts

Functions called from background callbacks must be explicitly `nonisolated`:

```swift
class AudioProcessor: @unchecked Sendable {
    // Called from audioQueue (background) - must be explicit nonisolated
    nonisolated private func handleConfigChange(engine: AVAudioEngine) {
        // Only access nonisolated(unsafe) state or dispatch to queue
    }

    // Log utilities must also be nonisolated to work from any thread
    nonisolated static func log(_ message: String) { ... }
}
```

### Callbacks set after init create data races

Mutable closure properties set after initialization are read from background callbacks:

```swift
// BAD - data race between MainActor set and background read:
class Recorder {
    var onError: ((Error) -> Void)?
}

// GOOD - immutable, passed at init:
class Recorder {
    nonisolated let onError: (@Sendable (Error) -> Void)?
    init(onError: (@Sendable (Error) -> Void)? = nil) {
        self.onError = onError
    }
}
```
