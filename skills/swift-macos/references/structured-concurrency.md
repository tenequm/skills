# Structured Concurrency

## Table of Contents
- Task
- async let
- TaskGroup
- Cancellation
- Priority
- Task-Local Values
- Named Tasks
- Unstructured Tasks

## Task

```swift
// Create a new top-level task
Task {
    try await refreshData()
}

// With priority
Task(priority: .userInitiated) {
    try await importFile()
}

// Detached task (no inherited context)
Task.detached(priority: .background) {
    try await cleanupCache()
}
```

### Task vs Task.detached
| | Task | Task.detached |
|---|------|---------------|
| Inherits actor | Yes | No |
| Inherits priority | Yes | No |
| Inherits task-locals | Yes | No |
| Use when | Most cases | Independent background work |

## async let

Concurrent bindings - start multiple async operations in parallel:

```swift
func loadDashboard() async throws -> Dashboard {
    async let user = fetchUser()
    async let projects = fetchProjects()
    async let notifications = fetchNotifications()
    async let stats = fetchStats()

    // All four requests run concurrently
    // Results collected when accessed
    return try await Dashboard(
        user: user,
        projects: projects,
        notifications: notifications,
        stats: stats
    )
}
```

Child tasks are automatically cancelled if the parent scope exits early. But that cancellation alone does **not** implement a timeout — to enforce one you must *race* the work against a sleep using a task group. `async let _ = Task.sleep(...)` is a common trap: the sleep runs concurrently but nothing awaits or races it, so `try await data` still waits forever if the fetch hangs.

```swift
struct TimeoutError: Error {}

/// Race `operation` against a sleep; first to finish wins, the loser is cancelled.
/// Stdlib equivalent `withDeadline` is proposed in SE-0526 (in review April 2026).
func withTimeout<T: Sendable>(
    seconds: Double,
    operation: sending @escaping () async throws -> T
) async throws -> T {
    try await withThrowingTaskGroup(of: T.self) { group in
        group.addTask { try await operation() }
        group.addTask {
            try await Task.sleep(for: .seconds(seconds))
            throw TimeoutError()
        }
        let result = try await group.next()!
        group.cancelAll()                 // cancels the loser
        return result
    }
}

// Usage
func loadWithTimeout() async throws -> Data {
    try await withTimeout(seconds: 10) {
        try await fetchLargeDataset()
    }
}
```

`withThrowingTaskGroup` + sleep is the canonical pattern pending SE-0526 (`withDeadline`): https://github.com/swiftlang/swift-evolution/blob/main/proposals/0526-deadline.md. Do not reach for `swift-async-algorithms` — the timeout feature was explicitly pulled from that package in favor of the stdlib path.

**Caveat: the helper is cooperative.** Swift's concurrency runtime cannot forcibly stop a task that isn't observing cancellation. `group.cancelAll()` only flips the cancellation flag; if `operation` is a tight synchronous loop, a blocking C bridge, or any path without `try Task.checkCancellation()` / cancellation-aware suspension points, the TaskGroup scope still waits for it and the call hangs past `seconds`. Use this pattern for cancellation-cooperative work (`URLSession`, `Task.sleep`, most modern async APIs). For CPU-bound or C-bridged work, sprinkle `try Task.checkCancellation()` into the work at suspension-friendly granularity, or dispatch the work to a queue/thread that you can kill independently.

## TaskGroup

Dynamic number of concurrent tasks:

```swift
// Throwing task group
func fetchAllPages() async throws -> [Page] {
    try await withThrowingTaskGroup(of: Page.self) { group in
        for id in pageIDs {
            group.addTask {
                try await fetchPage(id)
            }
        }

        var pages: [Page] = []
        for try await page in group {
            pages.append(page)
        }
        return pages
    }
}

// With ordered results
func processFiles(_ urls: [URL]) async throws -> [Result] {
    try await withThrowingTaskGroup(of: (Int, Result).self) { group in
        for (index, url) in urls.enumerated() {
            group.addTask {
                let result = try await process(url)
                return (index, result)
            }
        }

        var results = [(Int, Result)]()
        for try await pair in group {
            results.append(pair)
        }
        return results.sorted(by: { $0.0 < $1.0 }).map(\.1)
    }
}

// Limiting concurrency
func downloadImages(_ urls: [URL], maxConcurrent: Int = 4) async throws -> [NSImage] {
    try await withThrowingTaskGroup(of: (Int, NSImage).self) { group in
        var results = [(Int, NSImage)]()
        var nextIndex = 0

        // Start initial batch
        for i in 0..<min(maxConcurrent, urls.count) {
            let url = urls[i]
            group.addTask { (i, try await downloadImage(url)) }
            nextIndex = i + 1
        }

        // As each completes, start next
        for try await result in group {
            results.append(result)
            if nextIndex < urls.count {
                let url = urls[nextIndex]
                let idx = nextIndex
                group.addTask { (idx, try await downloadImage(url)) }
                nextIndex += 1
            }
        }

        return results.sorted(by: { $0.0 < $1.0 }).map(\.1)
    }
}
```

## Cancellation

```swift
// Check cancellation
func processItems(_ items: [Item]) async throws -> [Result] {
    var results: [Result] = []
    for item in items {
        // Check before expensive operation
        try Task.checkCancellation()
        let result = try await process(item)
        results.append(result)
    }
    return results
}

// Non-throwing cancellation check
if Task.isCancelled {
    return partialResults // Return what we have
}

// Cancel a task
let task = Task {
    try await longRunningOperation()
}
// Later:
task.cancel()

// withTaskCancellationHandler
func download(_ url: URL) async throws -> Data {
    let session = URLSession.shared
    return try await withTaskCancellationHandler {
        try await session.data(from: url).0
    } onCancel: {
        // Clean up resources
        session.invalidateAndCancel()
    }
}
```

## Priority

```swift
// Task priorities
Task(priority: .userInitiated) { }  // User is waiting
Task(priority: .medium) { }          // Default
Task(priority: .utility) { }         // Long-running, user aware
Task(priority: .background) { }      // User not waiting
Task(priority: .low) { }             // Lowest

// TaskGroup with priority
await withTaskGroup(of: Void.self) { group in
    group.addTask(priority: .high) { await urgentWork() }
    group.addTask(priority: .low) { await backgroundWork() }
}

// Current task priority
let priority = Task.currentPriority
```

## Task-Local Values

Thread-safe context propagation:

```swift
enum RequestContext {
    @TaskLocal static var requestID: String = "unknown"
    @TaskLocal static var userID: String?
}

func handleRequest() async {
    await RequestContext.$requestID.withValue(UUID().uuidString) {
        await RequestContext.$userID.withValue("user-123") {
            // All child tasks inherit these values
            await processRequest()
        }
    }
}

func processRequest() async {
    print(RequestContext.requestID) // The inherited value
    print(RequestContext.userID)     // "user-123"
}
```

## Named Tasks (Swift 6.2)

Assign human-readable names for debugging:

```swift
Task(name: "Refresh dashboard data") {
    try await dashboard.refresh()
}

Task(name: "Export \(document.name)") {
    try await exporter.export(document)
}

// Visible in:
// - LLDB: `swift task list`
// - Instruments: Swift Concurrency instrument
// - Xcode: Debug navigator > Task column
```

## Unstructured Tasks

When you need tasks that outlive their creation scope:

```swift
class DocumentController {
    private var saveTask: Task<Void, Error>?

    func autoSave() {
        // Cancel previous save
        saveTask?.cancel()

        // Start new save with debounce
        saveTask = Task {
            try await Task.sleep(for: .seconds(2))
            try await save()
        }
    }

    deinit {
        saveTask?.cancel()
    }
}
```

**Prefer structured concurrency** (async let, TaskGroup) over unstructured Task when possible - it provides automatic cancellation and clearer lifetime management.
