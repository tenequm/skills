# Concurrency Migration Guide

## Table of Contents
- Migration Paths
- From No Concurrency to Swift 6.2
- From GCD to async/await
- From Combine to AsyncSequence
- From ObservableObject to @Observable
- Common Errors & Fixes
- Checklist

## Migration Paths

### Path A: New project (recommended)
1. Swift 6 language mode + default MainActor isolation from day one
2. Use `@concurrent` for explicit background work
3. Use `@Observable` for state, `@Query` for SwiftData

### Path B: Existing project, incremental
1. Start with Swift 5 mode + `StrictConcurrency` upcoming feature (warnings only)
2. Fix warnings one module at a time
3. Enable Swift 6 mode per-target as they become clean
4. Add default isolation last

## From GCD to async/await

### Dispatch queues
```swift
// Before
DispatchQueue.global().async {
    let data = loadData()
    DispatchQueue.main.async {
        self.items = parse(data)
    }
}

// After
func loadAndParse() async {
    let data = await loadData()
    items = parse(data) // Already on MainActor with default isolation
}
```

### DispatchGroup
```swift
// Before
let group = DispatchGroup()
var results: [Data] = []
for url in urls {
    group.enter()
    fetch(url) { data in
        results.append(data)
        group.leave()
    }
}
group.notify(queue: .main) {
    process(results)
}

// After
func fetchAll(_ urls: [URL]) async throws -> [Data] {
    try await withThrowingTaskGroup(of: Data.self) { group in
        for url in urls {
            group.addTask { try await fetch(url) }
        }
        return try await group.reduce(into: []) { $0.append($1) }
    }
}
```

### Serial queue (mutual exclusion)
```swift
// Before
let queue = DispatchQueue(label: "com.app.serial")
queue.sync { sharedState.update() }

// After
actor SharedState {
    func update() { /* ... */ }
}
await sharedState.update()
```

### Timer
```swift
// Before
Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { _ in
    refresh()
}

// After
func startPolling() async {
    while !Task.isCancelled {
        try? await Task.sleep(for: .seconds(5))
        await refresh()
    }
}
```

## From Combine to AsyncSequence

### Publisher to AsyncSequence
```swift
// Before (Combine)
cancellable = publisher
    .map { $0.name }
    .filter { !$0.isEmpty }
    .sink { name in
        self.displayName = name
    }

// After
for await value in stream.map(\.name).filter({ !$0.isEmpty }) {
    displayName = value
}
```

### @Published to @Observable
```swift
// Before
class ViewModel: ObservableObject {
    @Published var items: [Item] = []
    @Published var isLoading = false
    @Published var error: Error?

    private var cancellables = Set<AnyCancellable>()

    func load() {
        isLoading = true
        service.fetchItems()
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.error = error
                    }
                },
                receiveValue: { [weak self] items in
                    self?.items = items
                }
            )
            .store(in: &cancellables)
    }
}

// After
@Observable
final class ViewModel {
    var items: [Item] = []
    var isLoading = false
    var error: Error?

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            items = try await service.fetchItems()
        } catch {
            self.error = error
        }
    }
}
```

### View changes
```swift
// Before
struct ContentView: View {
    @StateObject private var viewModel = ViewModel()
    var body: some View { /* ... */ }
}

// After
struct ContentView: View {
    @State private var viewModel = ViewModel()
    var body: some View { /* ... */ }
}
```

Note: `@StateObject` -> `@State`, `@ObservedObject` -> remove or use `@Bindable`

## Common Errors & Fixes

### "Sending value of non-Sendable type"
```swift
// Error
class MyClass { var data: [String] = [] }
Task { let c = MyClass() } // MyClass not Sendable

// Fix 1: Make it Sendable
final class MyClass: Sendable { let data: [String] }

// Fix 2: Use actor
actor MyActor { var data: [String] = [] }

// Fix 3: Use struct
struct MyData: Sendable { var data: [String] = [] }
```

### "Cannot access property from non-isolated context"
```swift
// Error
@MainActor class VM { var x = 0 }
func compute(vm: VM) { print(vm.x) } // non-isolated can't access

// Fix 1: Make function MainActor
@MainActor func compute(vm: VM) { print(vm.x) }

// Fix 2: Make it async
func compute(vm: VM) async { print(await vm.x) }

// Fix 3: Use default isolation (Swift 6.2)
// With -default-isolation MainActor, both are on MainActor
```

### "Global variable must be isolated or Sendable"
```swift
// Error
var sharedConfig = Config()

// Fix 1: Make it a let with Sendable type
let sharedConfig = Config(/* immutable */) // Config must be Sendable

// Fix 2: MainActor isolate
@MainActor var sharedConfig = Config()

// Fix 3: nonisolated(unsafe) for thread-safe globals
nonisolated(unsafe) let logger = Logger()
```

## Checklist

1. [ ] Enable strict concurrency checking as warnings first
2. [ ] Make value types (structs/enums) conform to Sendable where needed
3. [ ] Convert mutable classes to actors or @Observable
4. [ ] Replace DispatchQueue.main with @MainActor
5. [ ] Replace GCD with structured concurrency (TaskGroup, async let)
6. [ ] Replace Combine publishers with AsyncSequence where possible
7. [ ] Replace @Published with @Observable properties
8. [ ] Replace completion handlers with async/await
9. [ ] Enable Swift 6 language mode
10. [ ] Enable default MainActor isolation (Swift 6.2)
11. [ ] Add @concurrent to functions needing background execution
12. [ ] Remove now-redundant @MainActor annotations

## Let the compiler do the migration: `swift package migrate`

SwiftPM ships a migration command that mechanically rewrites source for a given upcoming feature, instead of chasing diagnostics by hand:

```bash
swift package migrate --to-feature ExistentialAny
swift package migrate --to-feature InternalImportsByDefault
swift package migrate --target MyApp --to-feature NonisolatedNonsendingByDefault
```

It applies the fix-its across the target and updates `Package.swift` to enable the feature. Run it on a clean tree, one feature at a time, and review the diff - it is a mechanical rewrite, not a design review.

Full flag list: `swift package migrate --help`.

## Upcoming-feature flags worth knowing individually

Enabling `.swiftLanguageMode(.v6)` in one step is often too big a jump for an existing codebase. These dials let you land Swift 6 semantics incrementally, each as `.enableUpcomingFeature("<name>")`:

| Flag | What it turns on |
|---|---|
| `StrictConcurrency` | Full data-race checking under language mode 5 |
| `InferSendableFromCaptures` | Closures infer `Sendable` from what they capture - removes many spurious annotations |
| `GlobalActorIsolatedTypesUsability` | Makes global-actor-isolated types usable in more generic contexts |
| `NonisolatedNonsendingByDefault` | `nonisolated async` inherits the caller's isolation |
| `DisableOutwardActorInference` | Stops a global-actor-isolated property from silently isolating its containing type |
| `ExistentialAny` | Requires `any` on existential types |
| `InternalImportsByDefault` | Imports are `internal` unless marked `public` |

`DisableOutwardActorInference` is the one that most often explains a surprise: a single `@MainActor var` can otherwise pull an entire type onto the main actor without you writing that anywhere.
