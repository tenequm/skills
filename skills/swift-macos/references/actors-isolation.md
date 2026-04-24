# Actors & Isolation

## Table of Contents
- Actor Basics
- Global Actors
- @MainActor
- Custom Global Actors
- Nonisolated
- Actor Reentrancy
- Custom Executors (DispatchSerialQueue pattern)
- `assumeIsolated` Recipes
- Reentrancy & Ordering Hazards
- `isolated deinit` (SE-0371)

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

Most apps don't need custom executors. The default executor (cooperative thread pool for actors, main thread for `@MainActor`) works well. The one pattern worth knowing is using a `DispatchSerialQueue` as an actor's serial executor - the replacement for `class X: @unchecked Sendable` + `nonisolated(unsafe) var` bookkeeping that Apple's own AVCam sample uses for audio/video capture.

### `DispatchSerialQueue` as an actor's serial executor

Before - a class managing its own serial queue with roughly 28 `nonisolated(unsafe)` declarations and `@unchecked Sendable`:

```swift
final class AudioRecorder: NSObject, @unchecked Sendable, SCStreamOutput {
    private let audioQueue = DispatchQueue(label: "com.app.audio")
    nonisolated(unsafe) private var writer: AVAssetWriter?
    nonisolated(unsafe) private var audioInput: AVAssetWriterInput?
    nonisolated(unsafe) private var sessionStarted = false
    // ... and 20+ more nonisolated(unsafe) vars
}
```

After - an actor whose serial executor *is* the `DispatchSerialQueue`. No `@unchecked Sendable`, no `nonisolated(unsafe)` bookkeeping. Every `func` on the actor is serialized on the audio queue.

`SCStreamOutput` inherits `NSObjectProtocol`, so actors can't conform directly. The idiomatic workaround is a small NSObject adapter that forwards the callback into the actor via `assumeIsolated` (safe because the callback runs on `audioQueue`, which IS the actor's executor):

```swift
actor AudioRecorder {
    // The backing queue. Declared DispatchSerialQueue (not DispatchQueue) so that
    // asUnownedSerialExecutor() is available.
    private let audioQueue = DispatchSerialQueue(label: "com.app.audio")

    // Tell the runtime: run this actor's isolated code on audioQueue, not the
    // cooperative pool.
    nonisolated var unownedExecutor: UnownedSerialExecutor {
        audioQueue.asUnownedSerialExecutor()
    }

    // State. Ordinary actor-isolated properties, no nonisolated(unsafe).
    private var writer: AVAssetWriter?
    private var audioInput: AVAssetWriterInput?
    private var sessionStarted = false

    func start(url: URL) throws { /* ... */ }
    func stop() async { /* ... */ }

    // SCStream adapter. Pass audioQueue as the sampleHandlerQueue so the callback
    // runs on the actor's executor and assumeIsolated is safe.
    final class StreamOutput: NSObject, SCStreamOutput {
        unowned let recorder: AudioRecorder
        init(_ recorder: AudioRecorder) { self.recorder = recorder }
        func stream(_ stream: SCStream,
                    didOutputSampleBuffer sb: CMSampleBuffer,
                    of type: SCStreamOutputType) {
            recorder.assumeIsolated { iso in
                iso.handleSampleBuffer(sb, type: type)
            }
        }
    }

    nonisolated func makeStreamOutput() -> SCStreamOutput { StreamOutput(self) }

    private func handleSampleBuffer(_ sb: CMSampleBuffer, type: SCStreamOutputType) {
        // Actor-isolated, runs on audioQueue. Touches writer / audioInput directly.
    }
}
```

**Why not just use an actor with the default executor?** Real-time audio callbacks (CoreAudio IO procs, SCStream sample handlers) must deliver on a specific dispatch queue to meet timing. The default cooperative pool cannot guarantee that. Custom executor ties the actor's isolation to the queue the callbacks already run on, so you get data-race safety *and* preserved timing, with zero bridging code.

**IO procs stay `nonisolated`.** CoreAudio's real-time IO proc must not allocate, must not call `Task {}`, must not yield to `AsyncStream`. Keep the IO-proc closure outside the actor (or as a `nonisolated` method returning an IO block), `memcpy` into a staging buffer, dispatch to `audioQueue`, and `assumeIsolated` on the other side.

## `assumeIsolated` Recipes

`assumeIsolated` lets a `nonisolated` function synchronously access actor state *if* it can prove it's already running on the actor's executor. With a custom `DispatchSerialQueue` executor, "already on the queue" = "already isolated to the actor."

Three correct recipes, one wrong one.

### Recipe 1: CoreAudio listener registered on the actor's queue

```swift
extension AudioRecorder {
    nonisolated func installRateListener(on deviceID: AudioObjectID) {
        let listener: AudioObjectPropertyListenerBlock = { [weak self] _, _ in
            // Block runs on audioQueue because we pass it below.
            self?.assumeIsolated { iso in
                iso.handleRateChange()   // actor-isolated, zero await
            }
        }
        var addr = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyNominalSampleRate,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
        AudioObjectAddPropertyListenerBlock(deviceID, &addr, audioQueue, listener)
    }
}
```

### Recipe 2: Block dispatched to the actor's queue from outside

```swift
someBackgroundWork { result in
    self.audioQueue.async {
        self.assumeIsolated { iso in
            iso.writeFrames(result)
        }
    }
}
```

### Recipe 3: Real-time IO proc - do NOT assumeIsolated on the RT thread

```swift
nonisolated func makeIOProc() -> AudioDeviceIOBlock {
    return { [weak self] _, inputData, _, _, _ in
        guard let self else { return }
        // RT thread. No allocation, no Task, no AsyncStream, no assumeIsolated.
        let frames = stageIntoRingBuffer(inputData)
        // Hop to audioQueue for everything else.
        self.audioQueue.async {
            self.assumeIsolated { iso in iso.writeFrames(frames) }
        }
    }
}
```

## Reentrancy & Ordering Hazards

### Don't re-dispatch when the block already runs on the actor's executor

When a CoreAudio property listener is registered with the actor's `audioQueue`, the block fires *on that queue* - so the block is already isolated to the actor. Wrapping its body in an extra `audioQueue.async { assumeIsolated { ... } }` is not just redundant; it creates an **ordering bug**.

Consider: `AudioObjectAddPropertyListenerBlock(deviceID, &rateAddr, audioQueue, listener)`. An `AudioObjectPropertyListenerBlock` rate-change fires on `audioQueue`. The queue already has IO-proc buffers ahead of it. If the listener does:

```swift
// WRONG: re-dispatches rate change behind already-queued IO-proc work.
let listener: AudioObjectPropertyListenerBlock = { [weak self] _, _ in
    self?.audioQueue.async {
        self?.assumeIsolated { iso in iso.handleRateChange() }
    }
}
```

...then `handleRateChange` runs *after* the IO-proc buffers queued before it. Those buffers read the stale `tapFormat` for one cycle, producing pitch/length corruption.

Correct pattern: call `assumeIsolated` directly, no inner `async`:

```swift
let listener: AudioObjectPropertyListenerBlock = { [weak self] _, _ in
    self?.assumeIsolated { iso in iso.handleRateChange() }
}
```

### State can change across every `await`

Standard actor reentrancy rule - restated because it bites concrete patterns:

```swift
actor ImageLoader {
    private var cache: [URL: NSImage] = [:]

    func load(_ url: URL) async throws -> NSImage {
        if let cached = cache[url] { return cached }
        let image = try await downloadImage(url)
        // Another load() may have populated cache during the await.
        if let cached = cache[url] { return cached }
        cache[url] = image
        return image
    }
}
```

### Don't assign the reference before awaiting a suspension that can race `stop()`

```swift
// FRAGILE: assignment happens after the await. A concurrent stop() during
// startCapture's suspension calls stopCapture() on a nil stream; cleanup
// silently no-ops, and the SCStream that eventually starts is orphaned.
func start() async throws {
    let s = SCStream(...)
    try await s.startCapture()    // <-- suspension
    self.stream = s
}

// ROBUST: assignment first, so stop() during the suspension drives cleanup.
func start() async throws {
    let s = SCStream(...)
    self.stream = s
    try await s.startCapture()
}
```

SCStream tolerates `stopCapture()` on an unstarted stream; not all APIs do. Test the "stop during start" path explicitly.

## `isolated deinit` (SE-0371, Swift 6.2+)

`deinit` is `nonisolated` by default — it cannot touch actor-isolated state. SE-0371 (shipped in Swift 6.2) lets actors and global-actor-isolated classes mark `deinit` as `isolated`; the runtime hops to the relevant executor (including a custom `unownedExecutor` like `DispatchSerialQueue`) before running the body, so cleanup can access isolated properties directly. No `nonisolated(unsafe)` mirrors needed for observer tokens, listener IDs, or `beginActivity` handles.

Caveat: task-local values set outside are **not** visible inside an isolated deinit — SE-0371 clears them on entry. Escaping `self` from an isolated deinit still traps. Source: https://github.com/swiftlang/swift-evolution/blob/main/proposals/0371-isolated-synchronous-deinit.md

```swift
actor AudioRecorder {
    private let audioQueue = DispatchSerialQueue(label: "audio")
    nonisolated var unownedExecutor: UnownedSerialExecutor {
        audioQueue.asUnownedSerialExecutor()
    }

    // Cached at start() time so deinit can tear them down.
    private var listenerIDs: Set<AudioObjectID> = []
    private let rateListener: AudioObjectPropertyListenerBlock
    private var observerTokens: [NSObjectProtocol] = []
    private var activityToken: NSObjectProtocol?

    init() {
        self.rateListener = { _, _ in /* handle rate change */ }
    }

    private func rateAddr() -> AudioObjectPropertyAddress {
        AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyNominalSampleRate,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
    }

    isolated deinit {
        // Runs on audioQueue, can touch actor-isolated state directly.
        var addr = rateAddr()
        for id in listenerIDs {
            AudioObjectRemovePropertyListenerBlock(id, &addr, audioQueue, rateListener)
        }
        observerTokens.forEach { NotificationCenter.default.removeObserver($0) }
        if let t = activityToken { ProcessInfo.processInfo.endActivity(t) }
    }
}
```

The "before" equivalent required `nonisolated(unsafe) var` copies of every piece of cleanup state, kept in sync with the actor-isolated originals.
