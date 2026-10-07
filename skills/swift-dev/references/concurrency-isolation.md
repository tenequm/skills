# Concurrency: Isolation, Actors, Sendable

Where code runs (default MainActor isolation, `nonisolated`, `@concurrent`, actors, custom executors), what may cross isolation boundaries (`Sendable`, `~Sendable`, `Mutex`), bridging Objective-C and third-party delegates into `@MainActor @Observable` classes, and typed throws.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every Swift block compiled with `swiftc -emit-sil` in Swift 6 mode against the iOS SDK (`arm64-apple-ios26.0`, CallKit blocks with LiveKit 2.17 modules) and the macOS SDK (`arm64-apple-macos15.0`), with and without default MainActor isolation; Xcode flag mapping confirmed with an XcodeGen project; isolated-conformance trap confirmed by running a macOS binary.

## Contents
- Project settings
- Where code runs
- Actors and reentrancy
- Custom executor: an actor on a dispatch queue
- isolated deinit
- Sendable
- Bridging delegates into a @MainActor @Observable class
- Typed throws

Verification note: `swiftc -typecheck` does NOT report region-isolation errors (`sending 'x' risks causing data races`); they come from a SIL pass. Check concurrency code with `-emit-sil -o /dev/null` or a real build.

## Project settings

App targets: Swift 6 language mode, default MainActor isolation, Approachable Concurrency. Xcode 27's app template sets `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` and `SWIFT_APPROACHABLE_CONCURRENCY = YES`.

```yaml
# XcodeGen project.yml, target settings
SWIFT_VERSION: "6.0"
SWIFT_DEFAULT_ACTOR_ISOLATION: MainActor
SWIFT_APPROACHABLE_CONCURRENCY: YES
```

In Swift 6 mode, Approachable Concurrency adds exactly two flags (the other three features it names are already part of Swift 6): `-enable-upcoming-feature InferIsolatedConformances` and `-enable-upcoming-feature NonisolatedNonsendingByDefault`. Default isolation becomes `-default-isolation=MainActor`. The SwiftPM equivalent (tools version 6.2+):

```swift
.target(
    name: "AppFeature",
    swiftSettings: [
        .defaultIsolation(MainActor.self),
        .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
        .enableUpcomingFeature("InferIsolatedConformances"),
    ]
)
```

Default isolation is per target; there is no per-file switch. Keep logic packages that run off-main (parsers, protocol clients) on the `nonisolated` default and put MainActor default on UI targets.

## Where code runs

| Declaration | Runs on |
|---|---|
| unannotated, in a MainActor-default target | main actor |
| `nonisolated func f()` (sync) | the caller's thread |
| `nonisolated func f() async` | the caller's actor with `NonisolatedNonsendingByDefault`; the global pool without it |
| `nonisolated(nonsending) func f() async` | the caller's actor, regardless of the flag |
| `@concurrent func f() async` | the global concurrent pool, always (async only) |

Use `@concurrent` for CPU-heavy or blocking work; do not use it for code that mostly awaits other async calls. Under default isolation every type is MainActor-isolated, including its conformances and computed members. A model decoded or used inside `@concurrent` code must be `nonisolated`:

```swift
import Foundation
import Observation

nonisolated struct Feed: Decodable, Sendable {
    let items: [String]
    var isEmpty: Bool { items.isEmpty }
}

@concurrent
func decodeFeed(_ data: Data) async throws -> Feed {
    try JSONDecoder().decode(Feed.self, from: data)   // off the main actor
}

@Observable
final class FeedModel {                               // MainActor by default
    var feed: Feed?

    func load(_ url: URL) async throws {
        let (data, _) = try await URLSession.shared.data(from: url)
        feed = try await decodeFeed(data)             // back on main after the await
    }
}
```

Without `nonisolated` on `Feed`: `error: main actor-isolated conformance of 'Feed' to 'Decodable' cannot be used in @concurrent context`.

`nonisolated(nonsending)` appears in Apple signatures (Foundation Models, `withTaskCancellationShield`, `withContinuation`); it means "runs on whatever actor called it".

## Actors and reentrancy

An actor serializes access to its state, but it is reentrant: any `await` inside an actor method lets other calls run. Rules:

1. Never assume state is unchanged after an `await`. Re-check after every suspension, not once at the top.
2. A `Bool` "stopped" flag checked before the await does not make `start()`/`stop()` safe. Use a state enum and re-check it after each await.
3. Publish the resource to actor state before awaiting, so a concurrent `stop()` finds it. Assigning after the await orphans it.
4. In cleanup, take ownership (copy to a local, nil the field) before any await, so an interleaved call cannot double-close.

```swift
import Foundation

enum FeedError: Error { case alreadyRunning, cancelled }

actor LiveFeed {
    private enum State { case idle, starting, running }
    private var state = State.idle
    private var socket: URLSessionWebSocketTask?

    func start(_ url: URL, token: String) async throws {
        guard state == .idle else { throw FeedError.alreadyRunning }
        state = .starting
        let socket = URLSession.shared.webSocketTask(with: url)
        self.socket = socket                       // publish before awaiting
        socket.resume()
        try await socket.send(.string(token))      // stop() may run here
        guard state == .starting else { throw FeedError.cancelled }
        state = .running
    }

    func stop() {
        guard let socket else { state = .idle; return }
        self.socket = nil                          // take ownership first
        state = .idle
        socket.cancel(with: .goingAway, reason: nil)
    }
}
```

Observed failure this prevents: `stop()` landed during a 12 s suspension in `start()`, set the flag and returned; `start()` resumed and built a live recorder nobody referenced, which ran for hours dropping every buffer. Distinct errors (`.cancelled` vs `.alreadyRunning`) let tests assert the exact interleaving. Delete partial artifacts on a failed start.

`let` properties of an actor are `nonisolated`; `nonisolated` members may read only those. Custom global actors (`@globalActor actor DatabaseActor { static let shared = DatabaseActor() }`) are rarely needed - prefer a plain actor.

## Custom executor: an actor on a dispatch queue

When a framework delivers callbacks on a queue you choose (capture outputs, CoreAudio listeners, `setDelegate(_:queue:)` APIs), make that queue the actor's executor. Callbacks then already run in the actor's isolation and enter it synchronously with `assumeIsolated` - no `@unchecked Sendable`, no `nonisolated(unsafe)` bookkeeping, no extra hop. Actors cannot inherit `NSObject`, so an `NSObject` adapter receives the delegate calls:

```swift
import AVFoundation

actor FrameProcessor {
    private let queue = DispatchSerialQueue(label: "camera.frames")
    nonisolated var unownedExecutor: UnownedSerialExecutor { queue.asUnownedSerialExecutor() }

    private var frameCount = 0

    nonisolated func attach(to output: AVCaptureVideoDataOutput) -> AnyObject {
        let adapter = Adapter(self)
        output.setSampleBufferDelegate(adapter, queue: queue)
        return adapter                             // caller keeps a strong reference
    }

    private func handle(_ sampleBuffer: CMSampleBuffer) { frameCount += 1 }

    private final class Adapter: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
        unowned let processor: FrameProcessor
        init(_ processor: FrameProcessor) { self.processor = processor }

        func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer,
                           from connection: AVCaptureConnection) {
            nonisolated(unsafe) let buffer = sampleBuffer   // same isolation domain; see below
            processor.assumeIsolated { $0.handle(buffer) }
        }
    }
}
```

- `nonisolated(unsafe) let` rebind: `CMSampleBuffer`/`AVAudioPCMBuffer` are not `Sendable`, so passing them into the actor reports `sending 'buffer' risks causing data races`. When the callback runs on the actor's own queue there is no race and the rebind is correct. When the callback runs on any other queue the race is real - hop properly instead.
- Do not wrap the body in `queue.async { assumeIsolated { } }` when the callback is already on that queue. It is redundant and reorders work: a rate-change listener re-dispatched behind already-queued IO buffers let those buffers use a stale format for a cycle (pitch/length corruption).
- `assumeIsolated` traps if called off the actor's executor. That is the point: it turns a wrong-queue assumption into a crash instead of a race.
- Real-time audio IO procs stay outside the actor: no allocation, no `Task {}`, no `AsyncStream.yield`, no `assumeIsolated` on the RT thread. Copy into a staging buffer and `queue.async` to the actor.

## isolated deinit

`deinit` is nonisolated by default and cannot touch isolated state. Actors and global-actor-isolated classes can declare `isolated deinit` (SE-0371); the runtime hops to the executor (including a custom one) first:

```swift
import Foundation

@MainActor
final class Poller {
    private var pollTask: Task<Void, Never>?
    private var observer: NSObjectProtocol?

    isolated deinit {
        pollTask?.cancel()
        if let observer { NotificationCenter.default.removeObserver(observer) }
    }
}
```

Task-local values are cleared on entry; escaping `self` still traps. This replaces `nonisolated(unsafe)` mirror copies of cleanup state.

## Sendable

Implicitly `Sendable`: value types whose stored properties are `Sendable`, actors, and global-actor-isolated classes (including every `@MainActor` class). A class is `Sendable` only if `final` with immutable `Sendable` stored properties. `any Error` is not `Sendable`; an enum carrying it cannot be. Mutable shared state: an actor by default; `Mutex`/`Atomic` (`Synchronization`, iOS 18+ / macOS 15+) where you cannot `await` (realtime and C callbacks); `~Sendable` (Swift 6.4, SE-0518) to state that a type is deliberately non-`Sendable`.

```swift
import Foundation
import Synchronization

final class LevelMeter: Sendable {                // Sendable without @unchecked
    private let peak = Mutex<Float>(0)
    private let started = Atomic<Bool>(false)

    func record(_ sample: Float) {                // any thread, no await
        peak.withLock { $0 = max($0, abs(sample)) }
    }

    func drain() -> Float {
        peak.withLock { value in
            defer { value = 0 }
            return value
        }
    }

    func startOnce() -> Bool {
        started.compareExchange(expected: false, desired: true, ordering: .acquiringAndReleasing).exchanged
    }
}

nonisolated public class Connection: ~Sendable { // audited, deliberately non-Sendable
    var buffer: [UInt8] = []
}

nonisolated public final class LockedConnection: Connection, @unchecked Sendable {
    private let lock = NSLock()
    func append(_ byte: UInt8) { lock.withLock { buffer.append(byte) } }
}
```

- Never `await` inside `withLock`; keep the critical section tiny. `.relaxed` ordering only for statistics counters.
- `~Sendable` must be on the type declaration (not an extension) and, unlike `@available(*, unavailable) extension X: Sendable {}`, is not inherited: a subclass can still be `@unchecked Sendable`.
- `@unchecked Sendable` is a promise the compiler cannot check; prefer `Mutex`, an actor, or restructuring.
- Non-`Sendable` on the iOS 27 / macOS 27 SDKs: `AVAudioPCMBuffer`, `KeyPath`, and all CallKit classes; `CMSampleBuffer`, `AVAssetWriter` and `Notification` have their `Sendable` conformance explicitly unavailable. `AVAudioFormat`, `AVAudioTime`, `AVAudioSession`, `UUID` are `Sendable`.
- `@preconcurrency import Module` downgrades that module's `Sendable` errors to warnings. Use it for modules not yet audited, and remove it when the module is.
- `nonisolated(unsafe) var` on a global or stored property opts out of checking entirely; reserve it for state you protect yourself.
- `sending` parameters and results transfer a non-`Sendable` value into another region; the caller cannot use it afterwards.

## Bridging delegates into a @MainActor @Observable class

The common shape: one `@MainActor @Observable final class X: NSObject` owns a framework object and conforms to its delegate protocol. The protocol is not main-actor-isolated, so the conformance needs a decision. What decides it is the queue the framework calls you on.

### Callbacks on the main queue: nonisolated + MainActor.assumeIsolated

`CXProviderDelegate` is an unannotated Objective-C protocol, and `CXProvider.setDelegate(_:queue:)` documents "A nil queue implies that delegate callbacks should happen on the main queue". Pass `nil`, mark the methods `nonisolated`, copy `Sendable` values out of the action, and enter the main actor synchronously (pattern from a shipping CallKit + LiveKit app):

```swift
import CallKit
import LiveKit
import Observation

@MainActor
@Observable
final class CallController: NSObject {
    private(set) var isMuted = false
    private(set) var status = "idle"

    @ObservationIgnored private let provider: CXProvider
    @ObservationIgnored private var room: Room?

    override init() {
        provider = CXProvider(configuration: CXProviderConfiguration())
        super.init()
        provider.setDelegate(self, queue: nil)   // nil = main queue; the delegate methods rely on it
    }

    private func connect(_ uuid: UUID) { status = "connecting" }
    private func finish(_ reason: String) { status = reason }
    private func applyMute(_ muted: Bool) { isMuted = muted }

    /// Re-reads the room: every delegate callback lands here, so their order does not matter.
    private func refresh() {
        guard let room else { return }
        status = room.connectionState == .reconnecting ? "reconnecting" : "live"
    }
}

extension CallController: CXProviderDelegate {
    nonisolated func providerDidReset(_: CXProvider) {
        MainActor.assumeIsolated { finish("reset") }
    }

    nonisolated func provider(_ provider: CXProvider, perform action: CXStartCallAction) {
        let uuid = action.callUUID               // CXAction is not Sendable; UUID is
        provider.reportOutgoingCall(with: uuid, startedConnectingAt: nil)
        action.fulfill()
        MainActor.assumeIsolated { connect(uuid) }
    }

    nonisolated func provider(_: CXProvider, perform action: CXSetMutedCallAction) {
        let muted = action.isMuted
        action.fulfill()
        MainActor.assumeIsolated { applyMute(muted) }
    }
}
```

- `assumeIsolated` runs synchronously, so CallKit sees state updated before the callback returns, and it traps if the queue assumption is ever wrong.
- Fulfill or fail the action inside the callback. Do not capture the action in a `Task { @MainActor in action.fulfill() }`: `error: sending 'action' risks causing data races`.
- Without `nonisolated`, a plain conformance fails: `conformance of 'CallController' to protocol 'CXProviderDelegate' crosses into main actor-isolated code and can cause data races`.
- Equivalent shorter form: an isolated conformance, `extension CallController: @MainActor CXProviderDelegate { ... }` with no `nonisolated` and no `assumeIsolated` (SE-0470; inferred automatically under `InferIsolatedConformances`). The Objective-C entry point traps if called off the main actor, just like `assumeIsolated`. It works only for protocols that do not require `Sendable`.

### Callbacks on arbitrary threads: hop with Task { @MainActor in }

LiveKit declares `@objc public protocol RoomDelegate: AnyObject, Sendable` and documents that delegate calls are "not guaranteed to be the main thread" (they come from an internal serial queue). An isolated conformance is rejected (`cannot form main actor-isolated conformance of 'X' to SendableMetatype-inheriting protocol 'RoomDelegate'`), and `assumeIsolated` would trap. Hop instead (`refresh()` is in the class above); `Room` is `@unchecked Sendable`, so it can be captured:

```swift
import LiveKit

extension CallController: RoomDelegate {
    nonisolated func room(_ room: Room, didUpdateConnectionState _: ConnectionState, from _: ConnectionState) {
        Task { @MainActor in if room === self.room { refresh() } }
    }

    nonisolated func room(_ room: Room, participant _: Participant, didUpdateAttributes _: [String: String]) {
        Task { @MainActor in if room === self.room { refresh() } }
    }
}
```

Ordering: tasks created with an explicit `@MainActor` closure from one serial thread start on the main actor in creation order ([SE-0431](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0431-isolated-any-functions.md); 20,000 mixed-priority tasks from one serial queue arrived in order). Nothing orders them against callbacks from other queues, an `await` inside a handler lets later ones interleave, a plain `Task {}` without the explicit `@MainActor` has no guarantee, and the callback's arguments are stale by the time the task runs. Make the handler idempotent: ignore the arguments, guard that the object is still current (`room === self.room`), and re-read the live state in one `refresh()`. Pass only `Sendable` values (IDs, `Bool`s, the `Sendable` object itself) into the task.

## Typed throws

`throws(E)` (Swift 6.0+) fits closed, caller-handled failure sets: domain errors that map to UI messages, pure decoders, embedded code. Keep `throws` (`any Error`) at framework boundaries and wherever new failure kinds may appear. Convert untyped errors at the boundary:

```swift
import Foundation

struct Grant: Decodable, Sendable { let url: String; let token: String }

enum GrantFailure: Error, Equatable {
    case unreachable
    case transport(String)
    case refused(status: Int)
    case malformed

    var message: String {
        switch self {
        case .unreachable: "Can't reach the server."
        case .transport(let detail): "Network error: \(detail)"
        case .refused(let status): "Refused (HTTP \(status))."
        case .malformed: "Unexpected response."
        }
    }
}

func decodeGrant(status: Int, body: Data) throws(GrantFailure) -> Grant {
    guard (200..<300).contains(status) else { throw .refused(status: status) }
    do { return try JSONDecoder().decode(Grant.self, from: body) } catch { throw .malformed }
}

func requestGrant(_ request: URLRequest) async throws(GrantFailure) -> Grant {
    let data: Data
    let response: URLResponse
    do {
        (data, response) = try await URLSession.shared.data(for: request)   // throws any Error
    } catch let error as URLError where error.code == .timedOut || error.code == .cannotConnectToHost {
        throw .unreachable
    } catch {
        throw .transport(error.localizedDescription)
    }
    return try decodeGrant(status: (response as? HTTPURLResponse)?.statusCode ?? 0, body: data)
}

@MainActor
final class Session {
    var status = ""
    private var task: Task<Void, Never>?

    func connect(_ request: URLRequest) {
        task = Task {
            do throws(GrantFailure) {             // in a closure, a plain `do` catches `any Error`
                let grant = try await requestGrant(request)
                status = "joined \(grant.url)"
            } catch .refused(let code) where code == 429 {
                status = "Rate limited."
            } catch {
                status = error.message            // `error` is GrantFailure
            }
        }
    }
}

func grants(_ statuses: [Int]) throws(GrantFailure) -> [Grant] {
    try statuses.map { (status) throws(GrantFailure) in try decodeGrant(status: status, body: Data()) }
}
```

Rules checked on Swift 6.4:
- `throw .case` works because the thrown type is known; `catch .case(let x)` matches enum cases directly.
- In a function body, a plain `do { try typed() } catch { }` infers `error` as the typed error. Inside any closure, including a `Task` body, it is `any Error` - write `do throws(E)`.
- An unannotated closure passed to `map` throws `any Error` (`thrown expression type 'any Error' cannot be converted to error type 'GrantFailure'`); annotate the closure `(x) throws(E) in`.
- `Task` erases typed throws: `Task { try await requestGrant(r) }.result` is `Result<Grant, any Error>`. Catch inside the task, or `catch let failure as GrantFailure` on the outside.
- A typed `throws(E)` function can be called from an untyped `throws` one; the error widens to `any Error`.
- `decodeGrant` is synchronous and pure, so `swift test` can cover every failure without a network (`#expect(throws: GrantFailure.malformed) { try decodeGrant(status: 200, body: Data("<html>".utf8)) }`).
