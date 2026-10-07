# Concurrency: Tasks, Cancellation, Streams

Creating and structuring tasks (`Task`, `async let`, task groups), cancellation including Swift 6.4 cancellation shields and `async` `defer`, timeouts, `AsyncStream`, observing `@Observable` state (`Observations`, advanced observation tracking), typed notifications, continuations including the noncopyable `Continuation`, and clocks.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every Swift block compiled with `swiftc -emit-sil` in Swift 6 mode for iOS and macOS (with and without default MainActor isolation, at the minimum OS stated next to each API); the timeout helper, `AsyncStream` bridge, cancellation shield, `Continuation` and observation-tracking examples were also run on macOS 27.2.

## Contents
- Task kinds
- async let and task groups
- Timeouts
- Cancellation, shields and async defer
- Stored tasks and debouncing
- Task-local values
- AsyncStream
- Observing @Observable state
- Typed notifications
- Continuations
- Clocks

## Task kinds

| | Inherits actor | Inherits priority and task-locals | Starts |
|---|---|---|---|
| `Task { }` | yes | yes | enqueued |
| `Task.immediate { }` (iOS 26+ / macOS 26+) | yes | yes | synchronously on the caller until its first suspension, when already on the right executor |
| `Task.detached { }` | no | no | enqueued |

`Task` inside a `@MainActor` method runs on the main actor; only the `await`ed calls leave it. `Task.detached` is rarely right: for off-main work call a `@concurrent` function from a normal `Task`. Name tasks for debugging: `Task(name: "export \(id)") { ... }` shows in LLDB (`language swift task list`, `language swift task tree`) and the Instruments Swift Tasks track. Priorities: `.userInitiated`, `.medium`, `.utility`, `.background` (`.high`/`.low` are aliases).

Prefer structured concurrency (`async let`, task groups): child tasks are cancelled and awaited when the scope exits. Use an unstructured `Task` only for work that outlives the scope (UI event handlers, stored tasks).

## async let and task groups

```swift
import Foundation

struct Profile: Sendable { let name: String }
struct Stats: Sendable { let count: Int }
struct Dashboard: Sendable { let profile: Profile; let stats: Stats }

func fetchProfile() async throws -> Profile { Profile(name: "a") }
func fetchStats() async throws -> Stats { Stats(count: 1) }

func loadDashboard() async throws -> Dashboard {
    async let profile = fetchProfile()          // both start now
    async let stats = fetchStats()
    return try await Dashboard(profile: profile, stats: stats)
}

// Ordered results with bounded concurrency.
func download(_ urls: [URL], maxConcurrent: Int = 4) async throws -> [Data] {
    try await withThrowingTaskGroup(of: (Int, Data).self) { group in
        var results = [Data?](repeating: nil, count: urls.count)
        var next = 0
        func addNext() {
            let index = next, url = urls[index]
            group.addTask { (index, try await URLSession.shared.data(from: url).0) }
            next += 1
        }
        while next < min(maxConcurrent, urls.count) { addNext() }
        for try await (index, data) in group {
            results[index] = data
            if next < urls.count { addNext() }
        }
        return results.compactMap { $0 }
    }
}

// Fire-and-forget children whose results are not needed: memory is freed as each finishes.
func warmCaches(_ keys: [String]) async {
    await withDiscardingTaskGroup { group in
        for key in keys { group.addTask { _ = key.hashValue } }
    }
}
```

- Groups yield results in completion order; carry an index to restore input order.
- When a throwing group's body throws, the remaining children are cancelled and awaited before the error propagates.
- An unawaited `async let` is cancelled and awaited when the scope exits - it never runs detached.
- A value that is not `Sendable` (for example `AVAssetWriter`) cannot be captured by `group.addTask`. Restructure so the non-`Sendable` value stays in one task.

## Timeouts

`async let _ = Task.sleep(...)` is not a timeout: nothing races it. Race the work against a sleep in a group. The standard library `withDeadline` ([SE-0526](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0526-deadline.md)) is accepted but not in the Swift 6.4 SDKs; `swift-async-algorithms` deliberately has no timeout.

```swift
import Foundation

struct TimeoutError: Error {}

nonisolated func withTimeout<T: Sendable>(
    _ duration: Duration,
    operation: @escaping @Sendable () async throws -> T
) async throws -> T {
    try await withThrowingTaskGroup(of: T.self) { group in
        group.addTask { try await operation() }
        group.addTask {
            try await Task.sleep(for: duration)
            throw TimeoutError()
        }
        defer { group.cancelAll() }               // the loser is cancelled
        return try await group.next()!
    }
}

func load(_ url: URL) async throws -> Data {
    try await withTimeout(.seconds(10)) { try await URLSession.shared.data(from: url).0 }
}
```

Cancellation is cooperative: `cancelAll()` only sets a flag, and the group still awaits every child. A tight synchronous loop or a blocking C call without `try Task.checkCancellation()` keeps the call hanging past the timeout. Use it for cancellation-aware work (`URLSession`, `Task.sleep`, most async APIs).

## Cancellation, shields and async defer

```swift
import Foundation

struct Item: Sendable { let id: Int }
func process(_ item: Item) async throws -> Int { item.id }

func processAll(_ items: [Item]) async throws -> [Int] {
    var results: [Int] = []
    for item in items {
        try Task.checkCancellation()               // or `if Task.isCancelled { return results }`
        results.append(try await process(item))
    }
    return results
}

nonisolated final class Job: Sendable {
    func cancel() {}
    func run() async throws -> Data { Data() }
}

func run(_ job: Job) async throws -> Data {
    try await withTaskCancellationHandler {
        try await job.run()
    } onCancel: {
        job.cancel()                               // runs immediately, on the cancelling thread
    }
}
```

Cancellation is final and propagates to every child task. That breaks cleanup: a teardown that awaits a cancellation-aware API (`Task.sleep`, a network call, a library that checks `Task.isCancelled`) is silently skipped in a cancelled task. Swift 6.4 adds two tools that compose:

- `async` calls in `defer` (SE-0493, any OS): `defer { await close() }` is allowed in async contexts and is awaited on every exit path.
- `withTaskCancellationShield { }` (SE-0504, iOS 27+ / macOS 27+): inside it `Task.isCancelled` is `false`, `Task.checkCancellation()` does not throw, new child tasks and task groups are not cancelled, and cancellation handlers registered inside do not fire. It hides cancellation; it does not undo it. `Task.hasActiveCancellationShield` reports whether one is active; the instance `task.isCancelled` on a handle still reports the real state.

```swift
actor Recorder {
    func record() async throws { try await Task.sleep(for: .seconds(10)) }
    func finalize() async { try? await Task.sleep(for: .milliseconds(50)) }   // cancellation-aware
}

func session(_ recorder: Recorder) async throws {
    defer {
        await withTaskCancellationShield {        // finalize runs fully even if the task was cancelled
            await recorder.finalize()
        }
    }
    try await recorder.record()
}
```

Measured: with the shield, a cancelled `session` finalized; with a plain `defer { await recorder.finalize() }` it did not. Shielding `group.addTask { }` itself has no effect - shield inside the child's body. Below iOS 27 / macOS 27 the workaround is an unstructured task (`await Task { await recorder.finalize() }.value`), which escapes the cancelled tree at the cost of a scheduling hop.

## Stored tasks and debouncing

Store a `Task` you may need to cancel; cancel the previous one before starting the next. `Task` holds `self` strongly until it finishes - a long-lived loop needs `[weak self]` or an explicit cancel.

```swift
import Observation

@MainActor
@Observable
final class SearchModel {
    var query = "" { didSet { scheduleSearch() } }
    private(set) var results: [String] = []
    @ObservationIgnored private var searchTask: Task<Void, Never>?

    private func scheduleSearch() {
        searchTask?.cancel()                       // the previous search stops at its next await
        let query = query
        searchTask = Task(name: "search \(query)") {
            try? await Task.sleep(for: .milliseconds(300))
            guard !Task.isCancelled else { return }
            results = await Self.search(query)
        }
    }

    @concurrent private static func search(_ query: String) async -> [String] { [query] }

    isolated deinit { searchTask?.cancel() }
}
```

`try? await Task.sleep` swallows the `CancellationError`, so check `Task.isCancelled` after it. A polling loop is `while !Task.isCancelled { await refresh(); try? await Task.sleep(for: .seconds(5)) }` in a stored task.

## Task-local values

```swift
import Foundation

enum RequestContext {
    @TaskLocal static var requestID = "none"
}

func handle() async {
    await RequestContext.$requestID.withValue(UUID().uuidString) {
        await log()                                // callees and child tasks see the value
    }
}

func log() async { print(RequestContext.requestID) }
```

`Task {}` inherits task-locals, `Task.detached` does not, and `isolated deinit` clears them.

## AsyncStream

Bridge a callback or delegate source with `AsyncStream.makeStream`, which returns the stream and its continuation without a closure. Always set `onTermination` to stop the source; it runs when the consumer stops iterating or its task is cancelled.

```swift
import Foundation

nonisolated func chunks(from handle: FileHandle) -> AsyncStream<Data> {
    let (stream, continuation) = AsyncStream.makeStream(of: Data.self, bufferingPolicy: .bufferingNewest(64))
    handle.readabilityHandler = { handle in
        let data = handle.availableData
        if data.isEmpty { continuation.finish() } else { continuation.yield(data) }
    }
    continuation.onTermination = { _ in
        handle.readabilityHandler = nil
    }
    return stream
}

func countBytes(_ pipe: Pipe) async -> Int {
    var total = 0
    for await chunk in chunks(from: pipe.fileHandleForReading) { total += chunk.count }
    return total
}
```

- Buffering: `.unbounded` (default), `.bufferingOldest(n)`, `.bufferingNewest(n)`. Bound it for high-rate producers.
- `AsyncStream.Continuation` is `Sendable` and `yield` is safe from any thread - but never from a real-time audio thread.
- An `AsyncStream` is single-consumer in practice: two concurrent `for await` loops split the elements between them (measured 316/684 of 1,000). Fan out with one stream per consumer.
- `AsyncThrowingStream` adds `finish(throwing:)`.
- Built-in sequences: `URL.lines`, `URLSession.bytes(from:)`, `FileHandle.bytes`, `NotificationCenter.notifications(named:)`.

## Observing @Observable state

SwiftUI observes `@Observable` automatically. Outside views, `Observations` (iOS 26+ / macOS 26+, [SE-0475](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0475-observed.md)) turns any expression over observable properties into an `AsyncSequence` of coalesced values. It takes a closure; there is no `Observations(of:)` or key-path form.

```swift
import Observation

@MainActor
@Observable
final class Transfer {
    var received = 0
    var total = 100
}

@MainActor
func watch(_ transfer: Transfer) async {
    let progress = Observations { (transfer.received, transfer.total) }
    for await (received, total) in progress {
        print("\(received)/\(total)")
        if received >= total { break }
    }
}
```

Changes made synchronously together arrive as one value (the transaction ends at the next suspension), so intermediate values can be skipped. `Observations.untilFinished { }` ends the sequence when the closure returns `.finish`.

For synchronous, uncoalesced callbacks (syncing two models, UIKit/AppKit glue), Swift 6.4 adds advanced tracking (SE-0506, iOS 27+ / macOS 27+). The shipping continuous function is named `withContinuousObservation(options:apply:)`, not the proposal's `withContinuousObservationTracking`:

```swift
import Observation

@MainActor
@Observable
final class Counter {
    var value = 0
}

@MainActor
final class CounterLogger {
    private var token: ObservationTracking.Token?

    func start(_ counter: Counter) {
        // One-shot: willSet and didSet for the first change only.
        withObservationTracking(options: [.willSet, .didSet]) {
            _ = counter.value
        } onChange: { event in
            print(event.kind == .willSet ? "will change" : "did change")
        }

        // Re-arms after every change until the token is cancelled or dropped.
        token = withContinuousObservation(options: [.didSet]) { event in
            print("value:", counter.value, event.kind == .initial ? "(initial)" : "")
        }
    }

    func stop() { token.take()?.cancel() }
}
```

Observed behavior: the `.initial` event and later events are delivered asynchronously on the closure's isolation (here the main actor), and several changes between deliveries coalesce into one event. `event.matches(\Counter.value)` identifies the changed property, but the `onChange` closure is `@Sendable`, so a key path to a main-actor-isolated property cannot be formed there (`cannot form key path to main actor-isolated property`); it works for nonisolated models. Plain `withObservationTracking(_:onChange:)` without options remains fire-once.

## Typed notifications

iOS 26+ / macOS 26+ `NotificationCenter` messages carry typed payloads and declare their isolation. `MainActorMessage` observers run on the main actor; `AsyncMessage` is the off-main counterpart.

```swift
import Foundation

@MainActor
final class Document {
    let id = UUID()
}

struct DocumentSaved: NotificationCenter.MainActorMessage {
    typealias Subject = Document
    static var name: Notification.Name { .init("DocumentSaved") }
    let id: UUID
}

@MainActor
final class Sidebar {
    private var token: NotificationCenter.ObservationToken?
    private(set) var lastSaved: UUID?

    func watch(_ document: Document) {
        token = NotificationCenter.default.addObserver(of: document, for: DocumentSaved.self) { [weak self] message in
            self?.lastSaved = message.id           // already on the main actor
        }
    }
}

@MainActor
func save(_ document: Document) {
    NotificationCenter.default.post(DocumentSaved(id: document.id), subject: document)
}
```

## Continuations

A continuation bridges a completion-handler API to `async`. It must be resumed exactly once.

```swift
import Foundation

enum LookupError: Error { case notFound }

// Calls `completion` exactly once, on a background queue.
nonisolated func legacyLookup(_ key: String, completion: @escaping @Sendable (Result<Int, LookupError>) -> Void) {
    DispatchQueue.global().async { completion(key == "a" ? .success(1) : .failure(.notFound)) }
}

func lookup(_ key: String) async throws -> Int {
    try await withCheckedThrowingContinuation { continuation in
        legacyLookup(key) { continuation.resume(with: $0) }
    }
}
```

`CheckedContinuation` traps on a double resume and logs a leaked (never resumed) one; `withUnsafeContinuation` drops both checks. On iOS 27+ / macOS 27+, `Continuation` (SE-0528) is noncopyable: a second `resume` is a compile error, dropping it unresumed traps (`Continuation was deinitialized without being resumed.`), and `withContinuation(of:throwing:)` is one function for non-throwing, typed and untyped failure:

```swift
import Foundation

enum LookupError: Error { case notFound }
nonisolated func legacyLookup(_ key: String, completion: @escaping @Sendable (Result<Int, LookupError>) -> Void) {
    DispatchQueue.global().async { completion(key == "a" ? .success(1) : .failure(.notFound)) }
}

func lookup(_ key: String) async throws(LookupError) -> Int {
    try await withContinuation(of: Int.self, throwing: LookupError.self) { continuation in
        let checked = CheckedContinuation(continuation)   // escaping closures cannot capture the noncopyable one
        legacyLookup(key) { checked.resume(with: $0) }
    }
}

actor Gate {
    private var waiter: Continuation<Void, Never>?

    func wait() async {
        await withContinuation(of: Void.self) { continuation in
            waiter = consume continuation          // stored, not captured
        }
    }

    func open() {
        waiter.take()?.resume()
    }
}
```

Capturing the `Continuation` itself in a callback fails: `noncopyable 'continuation' cannot be consumed when captured by an escaping closure`. So the compile-time guarantee applies when you store the continuation (actor-held waiters, registries); for callback APIs, convert with `CheckedContinuation(_:)` or `UnsafeContinuation(_:)`, which are not deprecated.

## Clocks

```swift
func step() async throws {}

func clocks() async throws {
    try await Task.sleep(for: .milliseconds(500))
    try await Task.sleep(until: .now + .seconds(5), clock: .continuous)   // keeps counting during system sleep
    let elapsed = try await ContinuousClock().measure { try await step() }
    print(elapsed)
}
```

`ContinuousClock` keeps advancing while the device sleeps; `SuspendingClock` does not. Use `Duration` everywhere instead of `TimeInterval` in async code.
