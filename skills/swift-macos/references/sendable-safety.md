# Sendable & Data Race Safety

## Table of Contents
- Sendable Protocol
- Implicit Sendable
- Making Types Sendable
- @unchecked Sendable
- @Sendable Closures
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
