# App Architecture

How to structure a SwiftUI app on iOS and macOS: one `@MainActor @Observable` controller per domain shared by views and App Intents, logic in a local Swift package for fast tests, and where SwiftData, view state and dependencies fit.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: the app/controller/intent block compiled through SIL (`swiftc -emit-sil`) for iOS 27 and macOS 27 with and without `-default-isolation MainActor`, and typechecked for iOS 26; the package layout was built and its tests run with `swift test` on macOS 27.2. The pattern is taken from a shipping iPhone app (SwiftUI + App Intents + CallKit + a local core package) whose code compiles.

## Contents
- The default: a shared controller
- Rules for controllers
- Logic in a local package
- View state and view models
- Dependencies and testing seams
- SwiftData in this shape
- When to reach for TCA
- Project layout

## The default: a shared controller

Model each app domain (calls, playback, sync, a document) as one `@MainActor @Observable final class` with a `static let shared` instance. The `App` injects it with `.environment`, views read it with `@Environment(Type.self)`, and every non-view entry point - App Intents, Shortcuts, the Action Button, system delegates (CallKit, notifications), widgets' intents running in the app process - calls the same instance. There is exactly one source of truth, and an intent that fires while the UI is on screen updates that UI.

```swift
import AppIntents
import Observation
import SwiftUI

@MainActor
@Observable
final class SessionController {
    static let shared = SessionController()

    enum Phase: Equatable {
        case idle, connecting, live, ended(String)
    }

    private(set) var phase: Phase = .idle
    private(set) var isMuted = false

    var isActive: Bool {
        switch phase {
        case .connecting, .live: true
        case .idle, .ended: false
        }
    }

    @ObservationIgnored private var connectTask: Task<Void, Never>?

    private init() {}

    func start() async {
        guard !isActive else { return }
        phase = .connecting
        connectTask = Task {
            try? await Task.sleep(for: .seconds(1))
            guard !Task.isCancelled else { return }
            phase = .live
        }
    }

    func setMuted(_ muted: Bool) { isMuted = muted }

    func stop(reason: String = "Ended.") {
        connectTask?.cancel()
        phase = .ended(reason)
    }
}

@main
struct ExampleApp: App {
    var body: some Scene {
        WindowGroup {
            SessionView()
                .environment(SessionController.shared)
        }
    }
}

struct SessionView: View {
    @Environment(SessionController.self) private var session

    var body: some View {
        VStack(spacing: 24) {
            Text(session.isActive ? "Live" : "Idle")
            if session.isActive {
                Button(session.isMuted ? "Unmute" : "Mute") { session.setMuted(!session.isMuted) }
                Button("Stop", role: .destructive) { session.stop() }
            } else {
                Button("Start") { Task { await session.start() } }
            }
        }
    }
}

struct StartSessionIntent: AppIntent {
    static let title: LocalizedStringResource = "Start session"
    static let supportedModes: IntentModes = .foreground

    @MainActor
    func perform() async throws -> some IntentResult {
        await SessionController.shared.start()
        return .result()
    }
}
```

`supportedModes: .foreground` (iOS / macOS 26+) launches the app before `perform()` runs - needed when the intent starts something user-visible like audio or a call. App Intents details live in app-intents.md.

## Rules for controllers

- `@MainActor` on the class, not on individual methods: SwiftUI reads it on the main actor, intents hop there with `@MainActor func perform()`, and the compiler then rejects off-main mutation. In a target with default `MainActor` isolation it is implied, but write it anyway - the controller may move to a package without that setting.
- `private(set)` on every observed property; mutate only through intent-named methods (`start()`, `stop(reason:)`). Views stay declarative and every state change has one code path to read.
- Model state as an enum (`Phase`) rather than several booleans; derive flags (`isActive`) as computed properties. Observation tracks computed properties through the stored ones they read.
- `@ObservationIgnored` on tasks, SDK handles, timers and caches - anything that must not trigger view updates.
- `private init()` plus `static let shared` makes the single instance structural. If a delegate needs `NSObject`, inherit and use `override private init()`.
- Long-running work is a stored `Task` you can cancel; re-check state after every `await` (another call may have changed `phase` meanwhile).
- System and SDK delegates call back on arbitrary queues: implement them `nonisolated` and hop with `MainActor.assumeIsolated` (when the SDK guarantees the main queue) or `Task { @MainActor in ... }`. See concurrency-isolation.md.
- Split by domain when a controller passes a few hundred lines; controllers may reference each other's `shared`, but keep the dependency direction one-way.

## Logic in a local package

Everything that is not UI or system glue - parsing, protocol encoding, state machines, validation, formatting, URL building - goes into a local Swift package that imports only Foundation. The app target depends on it; the controller becomes a thin adapter between the package and system frameworks.

```
MyApp/
  project.yml              # XcodeGen; or the .xcodeproj with a local package reference
  MyApp/                   # app target: App, controllers, views, intents, Info.plist
  MyAppCore/
    Package.swift
    Sources/MyAppCore/
    Tests/MyAppCoreTests/
```

```swift
// swift-tools-version:6.2
import PackageDescription

let package = Package(
    name: "MyAppCore",
    platforms: [.iOS(.v26), .macOS(.v15)],
    products: [.library(name: "MyAppCore", targets: ["MyAppCore"])],
    targets: [
        .target(name: "MyAppCore"),
        .testTarget(name: "MyAppCoreTests", dependencies: ["MyAppCore"]),
    ]
)
```

```swift
import Foundation

public struct InviteLink: Sendable, Equatable {
    public let host: String
    public let token: String

    public init?(_ text: String) {
        guard let url = URLComponents(string: text.trimmingCharacters(in: .whitespacesAndNewlines)),
              url.scheme == "https", let host = url.host, !host.isEmpty,
              let token = url.queryItems?.first(where: { $0.name == "t" })?.value, !token.isEmpty
        else { return nil }
        self.host = host
        self.token = token
    }
}
```

```swift
import MyAppCore
import Testing

struct InviteLinkTests {
    @Test func parsesHostAndToken() throws {
        let link = try #require(InviteLink(" https://example.com/join?t=abc\n"))
        #expect(link.host == "example.com")
        #expect(link.token == "abc")
    }

    @Test(arguments: ["http://example.com/join?t=abc", "https://example.com/join", ""])
    func rejectsInvalid(_ text: String) {
        #expect(InviteLink(text) == nil)
    }
}
```

- Why: `swift test` in `MyAppCore/` builds and runs on the Mac in seconds, with no simulator, no signing and no app launch. The iOS simulator runtime is a multi-GB download and app-hosted tests are slow; keep that path for UI and integration tests only (testing.md).
- `.macOS(...)` in `platforms` is what lets an iOS-only app's package test on the Mac. Keep UIKit, SwiftUI, AVFoundation sessions, CallKit and third-party SDKs out of the package; if a type needs them, it belongs in the app target.
- Mark package types `public` and `Sendable` value types; the app imports them across the module boundary.
- XcodeGen wiring (`packages: { MyAppCore: { path: MyAppCore } }` and a `- package: MyAppCore` dependency) is in ios-project-setup.md; package mechanics are in spm-and-builds.md.

## View state and view models

- Ephemeral UI state (sheet shown, text field draft, selection) is `@State` in the view.
- Shared domain state lives in a controller from `@Environment`.
- Add a per-screen view model only when a screen has real logic of its own (validation, paging, a multi-step form). Make it an `@Observable` class owned by `@State private var model = FormModel()`, created in the view, holding a reference to the controller if needed. Do not create one per view by default; it duplicates state the controller already owns.
- Pass `@Bindable var item: Item` to child views that edit an `@Observable` or `@Model` object.

## Dependencies and testing seams

Inject what crosses a process or hardware boundary (network, Keychain, clock, audio), not everything. A protocol with a live default keeps call sites simple and gives tests a seam; no DI container is needed.

```swift
import Foundation
import Observation

protocol InviteService: Sendable {
    func redeem(token: String) async throws -> String
}

struct LiveInviteService: InviteService {
    func redeem(token: String) async throws -> String {
        var request = URLRequest(url: URL(string: "https://example.com/redeem")!)
        request.httpMethod = "POST"
        request.httpBody = Data(token.utf8)
        let (data, _) = try await URLSession.shared.data(for: request)
        return String(decoding: data, as: UTF8.self)
    }
}

@MainActor
@Observable
final class InviteController {
    static let shared = InviteController()

    private(set) var roomName: String?
    @ObservationIgnored private let service: any InviteService

    init(service: any InviteService = LiveInviteService()) {
        self.service = service
    }

    func redeem(_ token: String) async throws {
        roomName = try await service.redeem(token: token)
    }
}
```

Tests construct `InviteController(service: StubService())` directly; the app only ever uses `shared`. Keep the `init` internal (not `private`) when you want this seam.

## SwiftData in this shape

- The `ModelContainer` is created once (an `enum Store { static let shared }` or a property of the `App`) so the app scene, App Intents and controllers share one store; see swiftdata-store.md.
- Views read with `@Query`; controllers that must react to data outside views use `ResultsObserver` (iOS / macOS 27).
- Writes go through `container.mainContext` in controllers, and heavy imports through a `@ModelActor` started from a `@concurrent` function.
- Never pass `@Model` objects between actors; pass `PersistentIdentifier`.

## When to reach for TCA

The Composable Architecture (Point-Free) gives reducer-based state, exhaustive `TestStore` tests and built-in dependency management at the cost of a large dependency, more boilerplate and a learning curve. Consider it only for big teams that want every state transition expressed as a reducer and tested exhaustively. Mixing it into an app built on the controller pattern doubles the concepts; pick one per app.

## Project layout

```
MyApp/
  project.yml
  MyApp/
    MyAppApp.swift          # @main, scenes, environment injection
    Controllers/            # @MainActor @Observable domain controllers (.shared)
    Views/                  # SwiftUI views, grouped by feature when it grows
    Intents/                # AppIntent types and AppShortcutsProvider
    Info.plist
  MyAppCore/                # local package: Foundation-only logic + Swift Testing tests
  MyAppUITests/             # optional: XCUITest flows on a simulator or device
```

Group by feature (`Views/Settings/`, `Views/Session/`) once a folder passes a dozen files. Split additional local packages only for a functional reason - a module shared with a widget or app extension, or code with a different dependency set - not for tidiness.
