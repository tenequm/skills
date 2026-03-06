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

Child tasks are automatically cancelled if the parent scope exits early:
```swift
func loadWithTimeout() async throws -> Data {
    async let data = fetchLargeDataset()
    async let _ = Task.sleep(for: .seconds(10)) // timeout

    return try await data
    // If function exits, pending child tasks are cancelled
}
```

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
