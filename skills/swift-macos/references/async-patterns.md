# Async Patterns

## Table of Contents
- AsyncSequence
- AsyncStream
- Observations (Swift 6.2)
- Continuations
- Clock & Duration
- Debouncing & Throttling
- Error Handling

## AsyncSequence

Protocol for asynchronous iteration:

```swift
// Consuming
for await line in fileURL.lines {
    process(line)
}

// With transformations
let validItems = items
    .compactMap { try? parse($0) }
    .filter { $0.isActive }

for try await item in validItems {
    display(item)
}

// First element
let first = await stream.first(where: { $0.isImportant })

// Collect into array
let all = try await stream.reduce(into: []) { $0.append($1) }
```

### Built-in AsyncSequences
- `URL.lines` - Lines from a file
- `URLSession.bytes(from:)` - Bytes from network
- `NotificationCenter.notifications(named:)` - Notifications
- `FileHandle.bytes` - Bytes from file handle

## AsyncStream

Create custom async sequences:

```swift
// Yield-based
func priceUpdates(for symbol: String) -> AsyncStream<Price> {
    AsyncStream { continuation in
        let connection = WebSocket(url: priceURL(for: symbol))

        connection.onMessage = { data in
            if let price = try? JSONDecoder().decode(Price.self, from: data) {
                continuation.yield(price)
            }
        }

        connection.onClose = {
            continuation.finish()
        }

        continuation.onTermination = { _ in
            connection.close()
        }

        connection.connect()
    }
}

// Usage
for await price in priceUpdates(for: "AAPL") {
    updateChart(price)
}
```

### Throwing variant
```swift
func monitorSystem() -> AsyncThrowingStream<SystemEvent, Error> {
    AsyncThrowingStream { continuation in
        let monitor = SystemMonitor()

        monitor.onEvent = { event in
            continuation.yield(event)
        }

        monitor.onError = { error in
            continuation.finish(throwing: error)
        }

        monitor.onComplete = {
            continuation.finish()
        }

        continuation.onTermination = { _ in
            monitor.stop()
        }

        monitor.start()
    }
}
```

### Buffering policy
```swift
AsyncStream(bufferingPolicy: .bufferingNewest(10)) { continuation in
    // Only keeps latest 10 values if consumer is slow
}

// Options:
// .unbounded - No limit (default)
// .bufferingOldest(N) - Keep first N, drop new
// .bufferingNewest(N) - Keep latest N, drop old
```

## Observations (Swift 6.2)

Stream transactional state changes from `@Observable` types:

```swift
import Observation

@Observable
class DownloadState {
    var bytesReceived: Int = 0
    var totalBytes: Int = 0
    var isComplete = false

    var progress: Double {
        totalBytes > 0 ? Double(bytesReceived) / Double(totalBytes) : 0
    }
}

// Stream as AsyncSequence. `Observations` uses a closure initializer;
// there is NO `Observations(of:)` factory and NO variadic-keypath tracking
// form. SE-0475 rejected both. Apple platforms: macOS 26+ / iOS 26+.
let state = DownloadState()
let progressStream = Observations { state.progress }
for await value in progressStream {
    progressBar.value = value
    if state.isComplete { break }
}
```

Key behavior:
- Groups synchronous changes into transactions
- Transaction ends at next `await` that suspends
- Avoids redundant updates (if you change 3 properties synchronously, one update fires)
- Works with any `@Observable` type

### Observing multiple properties
```swift
// Project the values you want into a tuple inside the closure.
let progress = Observations { (state.bytesReceived, state.totalBytes) }
for await (bytes, total) in progress {
    updateProgress(bytes: bytes, total: total)
}
```

Source: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0475-observed.md. Docs: https://developer.apple.com/documentation/observation/observations

## Continuations

Bridge callback-based APIs to async/await:

```swift
// Checked continuation (with runtime checks for misuse)
func fetchLocation() async throws -> CLLocation {
    try await withCheckedThrowingContinuation { continuation in
        locationManager.requestLocation { result in
            switch result {
            case .success(let location):
                continuation.resume(returning: location)
            case .failure(let error):
                continuation.resume(throwing: error)
            }
            // WARNING: Must resume exactly once. Double-resume crashes.
        }
    }
}

// Unsafe continuation (no runtime checks, slightly faster)
func readSensor() async -> SensorData {
    await withUnsafeContinuation { continuation in
        sensor.read { data in
            continuation.resume(returning: data)
        }
    }
}
```

**Rules:**
- Must resume exactly once
- `withCheckedContinuation` catches double-resume at runtime
- `withUnsafeContinuation` for performance-critical paths

## Clock & Duration

```swift
// Sleep
try await Task.sleep(for: .seconds(2))
try await Task.sleep(for: .milliseconds(500))
try await Task.sleep(until: .now + .seconds(5), clock: .continuous)

// Measure
let clock = ContinuousClock()
let elapsed = try await clock.measure {
    try await performWork()
}
print("Took \(elapsed)") // e.g., "1.234 seconds"

// Timeout pattern
func withTimeout<T>(
    _ duration: Duration,
    operation: @Sendable () async throws -> T
) async throws -> T {
    try await withThrowingTaskGroup(of: T.self) { group in
        group.addTask { try await operation() }
        group.addTask {
            try await Task.sleep(for: duration)
            throw TimeoutError()
        }

        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}
```

## Debouncing & Throttling

```swift
// Debounce search input
actor SearchDebouncer {
    private var currentTask: Task<Void, Never>?

    func debounce(delay: Duration = .milliseconds(300), action: @Sendable @escaping () async -> Void) {
        currentTask?.cancel()
        currentTask = Task {
            try? await Task.sleep(for: delay)
            guard !Task.isCancelled else { return }
            await action()
        }
    }
}

// Usage in SwiftUI
struct SearchView: View {
    @State private var query = ""
    @State private var results: [Item] = []
    private let debouncer = SearchDebouncer()

    var body: some View {
        TextField("Search", text: $query)
            .onChange(of: query) { _, newValue in
                Task {
                    await debouncer.debounce {
                        let items = try? await search(newValue)
                        await MainActor.run { results = items ?? [] }
                    }
                }
            }
    }
}
```

## Error Handling

```swift
// Typed throws (Swift 6.0+)
func parse(_ input: String) throws(ParseError) -> AST {
    guard !input.isEmpty else {
        throw .emptyInput
    }
    // ...
}

// Catch specific typed errors
do throws(ParseError) {
    let ast = try parse(input)
} catch .emptyInput {
    showEmptyMessage()
} catch .invalidSyntax(let line) {
    highlightError(at: line)
}

// In async context
func fetchAndParse() async throws(AppError) -> Model {
    let data = try await fetch()
    return try parse(data)
}
```
