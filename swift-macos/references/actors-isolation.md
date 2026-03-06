# Actors & Isolation

## Table of Contents
- Actor Basics
- Global Actors
- @MainActor
- Custom Global Actors
- Nonisolated
- Actor Reentrancy
- Custom Executors

## Actor Basics

Actors protect mutable state from data races via serialized access:

```swift
actor BankAccount {
    let id: UUID
    private(set) var balance: Decimal

    init(id: UUID, initialBalance: Decimal) {
        self.id = id
        self.balance = initialBalance
    }

    func deposit(_ amount: Decimal) {
        precondition(amount > 0)
        balance += amount
    }

    func withdraw(_ amount: Decimal) throws {
        guard balance >= amount else {
            throw BankError.insufficientFunds
        }
        balance -= amount
    }

    // Cross-actor operations
    func transfer(amount: Decimal, to other: BankAccount) async throws {
        try withdraw(amount)
        await other.deposit(amount)
    }
}

// All access from outside requires await
let account = BankAccount(id: UUID(), initialBalance: 1000)
await account.deposit(500)
let balance = await account.balance
```

### Actor properties
- Actor-isolated properties/methods require `await` from outside
- `let` properties are `nonisolated` by default (immutable = safe)
- Actors are reference types (like classes)
- Actors implicitly conform to `Sendable`

## Global Actors

Annotate types/functions to isolate them to a shared actor:

```swift
@MainActor
class ViewModel {
    var items: [Item] = [] // protected by MainActor

    func refresh() async throws {
        let data = try await api.fetch() // suspends, but resumes on MainActor
        items = data
    }
}
```

### @MainActor specifics
```swift
// On a function
@MainActor
func updateUI() {
    // Guaranteed to run on main thread
}

// On a property
@MainActor var currentTitle: String = ""

// On a closure
let callback: @MainActor () -> Void = {
    // Runs on MainActor
}

// Opt out within MainActor type
@MainActor
class ViewModel {
    nonisolated var description: String {
        "ViewModel" // No actor isolation needed
    }

    @concurrent
    func heavyComputation() async -> Data {
        // Runs off MainActor
    }
}
```

## Custom Global Actors

```swift
@globalActor
actor DatabaseActor {
    static let shared = DatabaseActor()
}

@DatabaseActor
class DatabaseManager {
    private var connection: Connection?

    func query(_ sql: String) throws -> [Row] {
        guard let conn = connection else { throw DBError.notConnected }
        return try conn.execute(sql)
    }
}

// Usage
@DatabaseActor
func fetchUsers() throws -> [User] {
    let rows = try DatabaseManager.shared.query("SELECT * FROM users")
    return rows.map(User.init)
}
```

## Nonisolated

Opt specific members out of actor isolation:

```swift
actor Cache {
    let name: String // implicitly nonisolated (let)

    nonisolated var debugDescription: String {
        "Cache(\(name))" // OK - only accesses nonisolated data
    }

    nonisolated func hash(into hasher: inout Hasher) {
        hasher.combine(name)
    }

    private var store: [String: Data] = []

    func get(_ key: String) -> Data? {
        store[key]
    }
}
```

### nonisolated(unsafe)
Escape hatch for when you know something is safe but compiler disagrees:

```swift
// Use sparingly - bypasses safety checks
nonisolated(unsafe) var legacyCallback: (() -> Void)?
```

## Actor Reentrancy

Actors don't prevent reentrancy - state can change across await points:

```swift
actor ImageLoader {
    private var cache: [URL: NSImage] = [:]

    func load(_ url: URL) async throws -> NSImage {
        // Check cache
        if let cached = cache[url] {
            return cached
        }

        // DANGER: Another call to load() can execute here during await
        let image = try await downloadImage(url)

        // State may have changed! Check again.
        if let cached = cache[url] {
            return cached // Another task already loaded it
        }

        cache[url] = image
        return image
    }
}
```

**Rule**: Never assume state is unchanged after an `await` inside an actor.

## Custom Executors

Control where actor code runs (advanced):

```swift
actor SpecificThreadActor {
    let executor: SpecificThreadExecutor

    nonisolated var unownedExecutor: UnownedSerialExecutor {
        executor.asUnownedSerialExecutor()
    }

    init(thread: Thread) {
        self.executor = SpecificThreadExecutor(thread: thread)
    }
}
```

Most apps don't need custom executors. The default executor (cooperative thread pool for actors, main thread for @MainActor) works well.
