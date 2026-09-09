---
name: swift-macos
description: macOS apps with Swift 6.3, SwiftUI, SwiftData, Swift Concurrency, Foundation Models, Swift Testing, and ScreenCaptureKit. Use when building native Mac apps - windows, menus, SwiftData, on-device AI, capture, AppKit bridges, notarization.
metadata:
  version: "0.8.3"
  categories: "development"
  topics: "swift, swiftui, macos, swiftdata, screencapturekit"
  upstream: "swift@6.3.3, xcode@26.6, macos@26.6.2"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/swift-macos
    emoji: "🍎"
    os:
      - macos
---

# macOS App Development - Swift 6.3

Build native macOS apps with Swift 6.3 (latest: 6.3.3, bundled in Xcode 26.6, Jun 2026), SwiftUI, SwiftData, and macOS 26 Tahoe (26.6.2 current). Target macOS 14+ for SwiftData/@Observable, macOS 15+ for latest SwiftUI, macOS 26 for Liquid Glass and Foundation Models. Note Xcode 26.6 still bundles the macOS **26.5** SDK, so 26.6-only API is not yet buildable. For the WWDC 2026 beta stack (macOS 27, Xcode 27, Swift 6.4, shipping fall 2026), see `references/fall-2026-releases.md`.

## Quick Start

```swift
import SwiftUI
import SwiftData

@Model
final class Project {
    var name: String
    var createdAt: Date
    // Named ProjectTask, not Task - `Task` would shadow `Swift.Task`
    @Relationship(deleteRule: .cascade) var tasks: [ProjectTask] = []

    init(name: String) {
        self.name = name
        self.createdAt = .now
    }
}

@Model
final class ProjectTask {
    var title: String
    var isComplete: Bool
    var project: Project?

    init(title: String) {
        self.title = title
        self.isComplete = false
    }
}

@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup("Projects") {
            ContentView()
        }
        .modelContainer(for: [Project.self, ProjectTask.self])
        .defaultSize(width: 900, height: 600)

        #if os(macOS)
        Settings { SettingsView() }

        MenuBarExtra("Status", systemImage: "circle.fill") {
            MenuBarView()
        }
        .menuBarExtraStyle(.window)
        #endif
    }
}

struct ContentView: View {
    @Query(sort: \Project.createdAt, order: .reverse)
    private var projects: [Project]

    @Environment(\.modelContext) private var context
    @State private var selected: Project?

    var body: some View {
        NavigationSplitView {
            List(projects, selection: $selected) { project in
                NavigationLink(value: project) {
                    Text(project.name)
                }
            }
            .navigationSplitViewColumnWidth(min: 200, ideal: 250)
        } detail: {
            if let selected {
                DetailView(project: selected)
            } else {
                ContentUnavailableView("Select a Project",
                    systemImage: "sidebar.left")
            }
        }
    }
}
```

## Scenes & Windows

| Scene | Purpose |
|-------|---------|
| `WindowGroup` | Resizable windows (multiple instances) |
| `Window` | Single-instance utility window |
| `Settings` | Preferences (Cmd+,) |
| `MenuBarExtra` | Menu bar with `.menu` or `.window` style |
| `DocumentGroup` | Document-based apps |

Open windows: `@Environment(\.openWindow) var openWindow; openWindow(id: "about")`

For complete scene lifecycle, see `references/app-lifecycle.md`.

## Menus & Commands

```swift
.commands {
    CommandGroup(replacing: .newItem) {
        Button("New Project") { /* ... */ }
            .keyboardShortcut("n", modifiers: .command)
    }
    CommandMenu("Tools") {
        Button("Run Analysis") { /* ... */ }
            .keyboardShortcut("r", modifiers: [.command, .shift])
    }
}
```

## Table (macOS-native)

```swift
Table(items, selection: $selectedIDs, sortOrder: $sortOrder) {
    TableColumn("Name", value: \.name)
    TableColumn("Date") { Text($0.date, format: .dateTime) }
        .width(min: 100, ideal: 150)
}
.contextMenu(forSelectionType: Item.ID.self) { ids in
    Button("Delete", role: .destructive) { delete(ids) }
}
```

For forms, popovers, sheets, inspector, and macOS modifiers, see `references/swiftui-macos.md`.

## @Observable

```swift
@Observable
final class AppState {
    var projects: [Project] = []
    var isLoading = false

    func load() async throws {
        isLoading = true
        defer { isLoading = false }
        projects = try await ProjectService.fetchAll()
    }
}

// Use: @State var state = AppState()          (owner)
// Pass: .environment(state)                    (inject)
// Read: @Environment(AppState.self) var state  (child)
```

## SwiftData

### @Query & #Predicate

```swift
@Query(filter: #Predicate<Project> { !$0.isArchived }, sort: \Project.name)
private var active: [Project]

// Dynamic predicate
func search(_ term: String) -> Predicate<Project> {
    #Predicate { $0.name.localizedStandardContains(term) }
}

// FetchDescriptor (outside views)
var desc = FetchDescriptor<Project>(predicate: #Predicate { $0.isArchived })
desc.fetchLimit = 50
let results = try context.fetch(desc)
let count = try context.fetchCount(desc)
```

### Relationships

```swift
@Model final class Author {
    var name: String
    @Relationship(deleteRule: .cascade, inverse: \Book.author)
    var books: [Book] = []

    init(name: String) { self.name = name }
}

@Model final class Book {
    var title: String
    var author: Author?
    @Relationship var tags: [Tag] = []  // many-to-many

    init(title: String) { self.title = title }
}
```

Delete rules: `.cascade`, `.nullify` (default), `.deny`, `.noAction`.

Every `@Model` class needs an explicit initializer - the macro does not synthesize one, and omitting it fails with `@Model requires an initializer be provided for '<Type>'`.

### Schema Migration

```swift
enum SchemaV1: VersionedSchema { /* ... */ }
enum SchemaV2: VersionedSchema { /* ... */ }

enum MigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] { [SchemaV1.self, SchemaV2.self] }
    static var stages: [MigrationStage] {
        [.lightweight(fromVersion: SchemaV1.self, toVersion: SchemaV2.self)]
    }
}

// Apply: .modelContainer(for: Model.self, migrationPlan: MigrationPlan.self)
```

### CloudKit Sync

Enable iCloud capability, then `.modelContainer(for: Model.self)` auto-syncs. Constraints: all properties need defaults/optional, no unique constraints, optional relationships.

For model attributes, background contexts, batch ops, undo/redo, and testing, see SwiftData references below.

## Concurrency (Swift 6.2+)

### Default MainActor Isolation

Opt entire module into main actor - all code runs on main actor by default:

```swift
// Package.swift
.executableTarget(name: "MyApp", swiftSettings: [
    .defaultIsolation(MainActor.self),
])
```

Or Xcode: Build Settings > Swift Compiler > Default Isolation > MainActor.

### @concurrent

Mark functions for background execution:

```swift
@concurrent
func processFile(_ url: URL) async throws -> Data {
    let data = try Data(contentsOf: url)
    return try compress(data) // runs off main actor
}
// After await, automatically back on main actor
let result = try await processFile(fileURL)
```

Use for CPU-intensive work, I/O, anything not touching UI.

### Actors

```swift
actor DocumentStore {
    private var docs: [UUID: Document] = [:]
    func add(_ doc: Document) { docs[doc.id] = doc }
    func get(_ id: UUID) -> Document? { docs[id] }
    nonisolated let name: String
}
// Requires await: let doc = await store.get(id)
```

### Structured Concurrency

```swift
// Parallel with async let
func loadDashboard() async throws -> Dashboard {
    async let profile = fetchProfile()
    async let stats = fetchStats()
    return try await Dashboard(profile: profile, stats: stats)
}

// Dynamic with TaskGroup
func processImages(_ urls: [URL]) async throws -> [NSImage] {
    try await withThrowingTaskGroup(of: (Int, NSImage).self) { group in
        for (i, url) in urls.enumerated() {
            group.addTask { (i, try await loadImage(url)) }
        }
        var results = [(Int, NSImage)]()
        for try await r in group { results.append(r) }
        return results.sorted { $0.0 < $1.0 }.map(\.1)
    }
}
```

### Sendable

```swift
struct Point: Sendable { var x, y: Double }              // value types: implicit
final class Config: Sendable { let apiURL: URL }          // final + immutable
actor SharedState { var count = 0 }                       // mutable: use actors
// Enable strict mode: .swiftLanguageMode(.v6) in Package.swift
```

### AsyncSequence & Observations

```swift
// Stream @Observable changes (macOS 26+ / iOS 26+, SE-0475)
// Observations uses a closure init, not Observations(of:).
let progresses = Observations { manager.progress }
for await p in progresses { print(p) }

// Typed NotificationCenter (macOS 26+)
struct DocSaved: NotificationCenter.MainActorMessage {
    typealias Subject = Document
    static var name: Notification.Name { .init("DocSaved") }
    let id: UUID
}
NotificationCenter.default.post(DocSaved(id: document.id), subject: document)
let token = NotificationCenter.default.addObserver(of: document, for: DocSaved.self) { msg in
    refresh(msg.id)
}
```

For concurrency deep dives, see concurrency references below.

## Foundation Models (macOS 26+)

On-device ~3B LLM. Free, offline, private:

```swift
import FoundationModels

let session = LanguageModelSession()
let response = try await session.respond(to: "Summarize: \(text)")
print(response.content)  // respond() returns Response<Content>, not Content

// Structured output
@Generable struct Summary { var title: String; var points: [String] }
let result = try await session.respond(to: prompt, generating: Summary.self)
let summary: Summary = result.content
```

For tool calling, streaming, and sessions, see `references/foundation-models.md`.

## Testing

```swift
import Testing

@Suite("Project Tests")
struct ProjectTests {
    @Test("creates with defaults")
    func create() {
        let p = Project(name: "Test")
        #expect(p.name == "Test")
    }

    @Test("formats sizes", arguments: [(1024, "1 KB"), (0, "0 KB")])
    func format(bytes: Int, expected: String) {
        #expect(formatSize(bytes) == expected)
    }
}

// SwiftData testing
let container = try ModelContainer(
    for: Project.self,
    configurations: ModelConfiguration(isStoredInMemoryOnly: true)
)
let ctx = ModelContext(container)
ctx.insert(Project(name: "Test"))
try ctx.save()
```

For exit tests, attachments, UI testing, see `references/testing.md`.

## Distribution

| Method | Sandbox | Notarization | Review |
|--------|---------|--------------|--------|
| App Store | Required | Automatic | Yes |
| Developer ID | Recommended | Required | No |
| Ad-Hoc | No | No | Local only |

```bash
xcodebuild archive -scheme MyApp -archivePath MyApp.xcarchive
xcodebuild -exportArchive -archivePath MyApp.xcarchive \
  -exportPath ./export -exportOptionsPlist ExportOptions.plist
xcrun notarytool submit ./export/MyApp.dmg \
  --apple-id you@example.com --team-id TEAM_ID \
  --password @keychain:AC_PASSWORD --wait
xcrun stapler staple ./export/MyApp.dmg
```

For complete distribution guide, see `references/distribution.md`.

## SPM

```swift
// swift-tools-version: 6.3
let package = Package(
    name: "MyApp",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(name: "MyApp", swiftSettings: [
            .swiftLanguageMode(.v6),
            .defaultIsolation(MainActor.self),
        ]),
        .testTarget(name: "MyAppTests", dependencies: ["MyApp"]),
    ]
)
```

For build plugins, macros, and Swift Build, see `references/spm-build.md`.

## Liquid Glass (macOS 26)

Apps rebuilt with Xcode 26 SDK get automatic Liquid Glass styling. Use `.glassEffect()` for custom glass surfaces, `GlassEffectContainer` for custom hierarchies. Opt out (Xcode 26 only): `UIDesignRequiresCompatibility = YES` in Info.plist keeps the legacy visual style - a temporary migration aid. Apps rebuilt with Xcode 27 (beta) can no longer opt out; the key is ignored and Liquid Glass is mandatory (see `references/fall-2026-releases.md`).

## ScreenCaptureKit

Capture screen content, app audio, and microphone (macOS 12.3+):

```swift
import ScreenCaptureKit

let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
guard let display = content.displays.first else { return }

// Filter: specific apps only
let filter = SCContentFilter(display: display, including: [targetApp], exceptingWindows: [])

// Configure
let config = SCStreamConfiguration()
config.capturesAudio = true
config.sampleRate = 48000
config.channelCount = 2
config.excludesCurrentProcessAudio = true

// Audio-only: throttle the video pipeline (it always runs). minimumFrameInterval is a
// MINIMUM gap between frames - 1/Int32.max is ~0s, i.e. native refresh rate (60+ fps
// of discarded frames and a full-screen recomposite each). Use 1 fps.
config.width = 2; config.height = 2
config.minimumFrameInterval = CMTime(value: 1, timescale: 1)

let stream = SCStream(filter: filter, configuration: config, delegate: self)
try stream.addStreamOutput(self, type: .screen, sampleHandlerQueue: nil)
try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: audioQueue)
try await stream.startCapture()
```

macOS 15+: `SCRecordingOutput` for simplified file recording, `config.captureMicrophone` for mic capture. macOS 14+: `SCContentSharingPicker` for system picker UI, `SCScreenshotManager` for single-frame capture.

For complete API reference, audio writing (AVAssetWriter/AVAudioFile), permissions, and examples, see `references/screen-capture-audio.md`.

## AppKit Interop

```swift
struct WebViewWrapper: NSViewRepresentable {
    let url: URL
    func makeNSView(context: Context) -> WKWebView { WKWebView() }
    func updateNSView(_ v: WKWebView, context: Context) {
        v.load(URLRequest(url: url))
    }
}
```

For hosting SwiftUI in AppKit and advanced bridging, see `references/appkit-interop.md`.

## Architecture

| Pattern | Best For | Complexity |
|---------|----------|------------|
| SwiftUI + @Observable | Small-medium, solo | Low |
| MVVM + @Observable | Medium, teams | Medium |
| TCA | Large, strict testing | High |

See `references/architecture.md` for all patterns with examples.

## References

| File | When to read |
|------|-------------|
| `references/fall-2026-releases.md` | WWDC 2026 beta stack: macOS 27, Xcode 27, Swift 6.4, Foundation Models next-gen, Core AI, Spatial Preview, mandatory Liquid Glass |
| **SwiftUI & macOS** | |
| `references/app-lifecycle.md` | Window management, scenes, DocumentGroup, MenuBarExtra gotchas, async termination, LSUIElement issues |
| `references/swiftui-macos.md` | Sidebar, Inspector, Table, forms, popovers, sheets, search |
| `references/appkit-interop.md` | NSViewRepresentable, hosting controllers, NSHostingSceneRepresentation, sizing/scene-bridging options, AppKit Liquid Glass (NSGlassEffectView), pasteboard privacy, NSPanel/floating HUD |
| `references/screen-capture-audio.md` | ScreenCaptureKit, SCStream gotchas, SCStream teardown hazards, AVAudioEngine dual pipeline, AVAssetWriter crash safety, non-interleaved stereo trap, TCC gotchas, CDHash degraded-state after reinstall, SpeechAnalyzer transcription |
| `references/core-audio-tap.md` | CATap for per-process audio: tap-only aggregate (HFP-safe), drift compensation, rate-change anti-pattern, interleaved-stereo frame-count trap, IO proc isolation |
| `references/system-integration.md` | Keyboard shortcuts, drag & drop, file access, App Intents (entities, Spotlight, snippets), widgets & Control Center, process monitoring, AXUIElement, CoreAudio per-process APIs, login items, XPC, LSUIElement, os.Logger & signposts, privacy usage descriptions |
| `references/foundation-models.md` | On-device AI: guided generation, tool calling, streaming |
| `references/architecture.md` | MVVM, TCA, dependency injection, project structure |
| `references/testing.md` | Swift Testing, exit tests, attachments, UI testing, XCTest migration |
| `references/distribution.md` | App Store, Developer ID, notarization gotchas, nested bundle signing, xcodebuild signing traps (silent ad-hoc builds), sandboxing, universal binaries |
| `references/spm-build.md` | Package.swift, Swift Build, plugins, macros, plugin/macro validation gates, Metal toolchain download, manual .app bundle assembly, mixed ObjC targets, CLT testing |
| **Concurrency** | |
| `references/approachable-concurrency.md` | Default MainActor isolation, @concurrent, nonisolated async, runtime pitfalls |
| `references/actors-isolation.md` | Actor model, global actors, custom executors, reentrancy |
| `references/structured-concurrency.md` | Task, TaskGroup, async let, cancellation, priority, named tasks |
| `references/sendable-safety.md` | Sendable protocol, data race safety, @unchecked Sendable + serial queue, @preconcurrency import |
| `references/async-patterns.md` | AsyncSequence, AsyncStream, Observations, continuations, Clock |
| `references/migration-guide.md` | GCD to async/await, Combine to AsyncSequence, Swift 6 migration |
| **SwiftData** | |
| `references/models-schema.md` | @Model, @Attribute options, Codable, transformable, external storage |
| `references/relationships-predicates.md` | Advanced relationships, inverse rules, compound predicates |
| `references/container-context.md` | ModelContainer, ModelContext, background contexts, undo/redo, batch ops |
| `references/cloudkit-sync.md` | CloudKit setup, conflict resolution, sharing, debugging sync |
| `references/migrations.md` | VersionedSchema, lightweight/custom migration, Core Data migration |
