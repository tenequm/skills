# SwiftData Store, Contexts, Migration and Sync

Setting up `ModelContainer`, working with `ModelContext` on and off the main actor, observing changes outside SwiftUI, history, schema migration, CloudKit sync, previews and tests - iOS and macOS.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every block compiled through SIL (`swiftc -emit-sil`, so region-isolation checks ran) for iOS 27 and macOS 27, with and without `-default-isolation MainActor`; container, `@ModelActor`, `ResultsObserver`, `HistoryObserver`, history/tombstone, batch delete and a three-version migration chain were run against an on-disk store in a scratch SPM package on macOS 27.2. CloudKit behavior is from Apple's documentation, not run.

Model examples use `Project` / `Todo` from swiftdata-models.md.

## Contents
- Container setup
- ModelContext basics
- Background work with @ModelActor
- Observing outside SwiftUI: ResultsObserver, HistoryObserver
- History and tombstones
- Schema migration
- CloudKit sync
- Previews and tests

## Container setup

Create the container once, in the `App`, and inject it. Own it explicitly (rather than `.modelContainer(for:)`) whenever anything outside the view tree - an App Intent, a widget, a controller - needs the same store, or when you have a migration plan: the SwiftUI `.modelContainer(for:...)` modifiers take no `migrationPlan:` parameter.

```swift
import SwiftData
import SwiftUI

enum Store {
    static let shared: ModelContainer = {
        let schema = Schema([Project.self, Todo.self, Tag.self])
        let config = ModelConfiguration(
            "Main",
            schema: schema,
            groupContainer: .identifier("group.com.example.app"),
            cloudKitDatabase: .none
        )
        do {
            return try ModelContainer(for: schema, configurations: config)
        } catch {
            fatalError("Store failed to open: \(error)")
        }
    }()
}

@main
struct ExampleApp: App {
    var body: some Scene {
        WindowGroup {
            Text("Root")
        }
        .modelContainer(Store.shared)
    }
}
```

- `cloudKitDatabase` defaults to `.automatic`: the moment the target gains an iCloud/CloudKit entitlement (even for unrelated CloudKit use), SwiftData tries to sync this store and enforces the CloudKit model rules, so container creation can start failing. Say `.none` unless you want sync.
- `groupContainer: .identifier(...)` puts the store in an App Group so widgets, App Intents extensions and the app share it (needs the App Groups entitlement). Without it each process gets its own store.
- Multiple stores: pass several `ModelConfiguration`s, each with its own `schema` (for example a synced user store and a read-only bundled store with `url:` and `allowsSave: false`).
- `ModelConfiguration(isStoredInMemoryOnly: true)` for previews and tests.
- The SwiftUI modifier form is fine for simple apps: `.modelContainer(for: [Project.self], isUndoEnabled: true)`.

## ModelContext basics

```swift
import Foundation
import SwiftData

func editProjects(_ context: ModelContext) throws {
    let project = Project(slug: "q3", name: "Q3 plan")
    context.insert(project)
    project.name = "Q3 roadmap"   // tracked automatically

    try context.transaction {
        context.insert(Todo(title: "Draft"))
        context.insert(Todo(title: "Review"))
    }   // saved once when the block returns (verified)

    try context.delete(model: Todo.self, where: #Predicate { $0.isDone })
    try context.enumerate(FetchDescriptor<Todo>(), batchSize: 200) { todo in
        todo.uploadProgress = 0
    }
    if context.hasChanges { try context.save() }
}
```

- `mainContext` autosaves and `ModelContext(container)` also reports `autosaveEnabled == true` (verified) - but autosave timing is opportunistic. Call `save()` explicitly at the end of any unit of work you care about, and always in background contexts.
- `context.delete(model:where:)` is a batch delete and does apply `.cascade` rules (verified). `includeSubclasses:` controls inheritance.
- `enumerate(_:batchSize:allowEscapingMutations:)` walks large result sets in batches (default 5000). Leave `allowEscapingMutations` false: it traps when the block mutates objects outside the batch, which is the safety net you want. `FetchDescriptor` has no `fetchBatchSize`.
- `rollback()` discards unsaved changes; `context.author = "importer"` tags the next transaction in history.
- Undo: set `container.mainContext.undoManager = UndoManager()` (or `isUndoEnabled: true` on the modifier); SwiftUI's `@Environment(\.undoManager)` then drives it.
- Identity: `persistentModelID` is temporary until the first save; do not store or send it before saving.

## Background work with @ModelActor

`@Model` instances and `ModelContext` are not `Sendable`. The compiler enforces it: `PersistentModels are not Sendable, consider utilizing a ModelActor or use N's persistentModelID instead`, and `ModelContext`'s `Sendable` conformance is explicitly unavailable ("contexts cannot be shared across concurrency contexts"). Move `PersistentIdentifier`s (and plain value types) between actors, never models.

```swift
import Foundation
import SwiftData

@ModelActor
actor TodoImporter {
    func importTitles(_ titles: [String]) throws -> [PersistentIdentifier] {
        let todos = titles.map { Todo(title: $0) }
        todos.forEach { modelContext.insert($0) }
        try modelContext.save()
        return todos.map(\.persistentModelID)
    }

    func markDone(_ id: PersistentIdentifier) throws {
        guard let todo = self[id, as: Todo.self] else { return }
        todo.isDone = true
        try modelContext.save()
    }
}

@MainActor
func runImport(container: ModelContainer) async throws {
    let importer = TodoImporter(modelContainer: container)
    let ids = try await importer.importTitles(["a", "b"])
    try await importer.markDone(ids[0])
    let first = container.mainContext.model(for: ids[0]) as? Todo
    _ = first?.isDone
}
```

- `@ModelActor` synthesizes `modelContainer`, `modelContext`, `modelExecutor` and `init(modelContainer:)`. It works unchanged in targets with default `MainActor` isolation (verified): the actor's own isolation wins over the module default.
- A `@ModelActor` does not guarantee background execution. On macOS 27.2 its methods ran on the main thread whenever they were awaited from main-actor code (including a plain `Task {}` started there), wherever the actor was created; awaited from a `@concurrent` function or `Task.detached`, they ran on a background thread. Start heavy imports from a `@concurrent` function, and confirm with the Time Profiler.
- Saves from the actor reach `@Query` views and `ResultsObserver`s on the main context automatically.
- `self[id, as: T.self]` (on `ModelActor`) and `context.registeredModel(for:)` return `nil` for unknown IDs; `context.model(for:)` always returns an instance (a fault), so prefer the optional forms when the row may be gone.

## Observing outside SwiftUI: ResultsObserver, HistoryObserver

`@Query` is view-only. For a controller, an App Intent or a service, use the iOS 27 / macOS 27 observers. Both are `@Observable`.

```swift
import Foundation
import Observation
import SwiftData

@available(iOS 27, macOS 27, *)
@MainActor
@Observable
final class TodoFeed {
    private(set) var open: ResultsObserver<Todo, Never>
    private(set) var tickets: ResultsObserver<Ticket, String>
    @ObservationIgnored private let remote: HistoryObserver
    @ObservationIgnored private var watch: Task<Void, Never>?

    init(container: ModelContainer) throws {
        open = try ResultsObserver(
            filterBy: #Predicate<Todo> { !$0.isDone },
            sortBy: [SortDescriptor(\.title)],
            modelContext: container.mainContext
        )
        tickets = try ResultsObserver(
            sortBy: [SortDescriptor(\Ticket.status)],
            sectionBy: \Ticket.status,
            modelContext: container.mainContext
        )
        remote = try HistoryObserver(observedModels: [Todo.self], modelContainer: container)
        watch = Task { [remote] in
            for await count in Observations({ remote.eventCounter }) {
                print("remote Todo changes:", count)
            }
        }
    }

    var openTitles: [String] { open.results.map(\.title) }
    var ticketStatuses: [String] { tickets.sections?.sectionTitles ?? [] }
}
```

- `ResultsObserver<Model, Never>` is unsectioned; `ResultsObserver<Model, String>` with `sectionBy:` fills `sections`. It tracks local saves, saves from other contexts in the same container, other processes and CloudKit. Results update asynchronously after the save, not synchronously (verified: empty right after a main-context save, populated after the run loop turned).
- `filterBy` and `sortBy` are settable, so one observer can follow a changing search field.
- `element(at:)` / `indexPath(for:)` map to `IndexPath` for UIKit/AppKit table data sources.
- `HistoryObserver` listens for remote-change notifications and bumps `eventCounter` when a transaction touches `observedModels` (empty array = any model). It counted one event per background-context save in testing. Pair it with the history API below to read what changed.
- `sectionBy` must name a stored `String` / `String?` attribute (`Ticket` is in swiftdata-models.md); a computed property typechecks but traps when the observer fetches.

## History and tombstones

Persistent history answers "what changed since I last looked" across launches, processes and sync. Store the last processed token (`HistoryToken` is `Codable`).

```swift
import Foundation
import SwiftData

func processChanges(since token: DefaultHistoryToken?, context: ModelContext) throws -> DefaultHistoryToken? {
    var descriptor = HistoryDescriptor<DefaultHistoryTransaction>()
    if let token {
        descriptor.predicate = #Predicate { $0.token > token }
    }
    let transactions = try context.fetchHistory(descriptor)
    for transaction in transactions {
        for change in transaction.changes {
            switch change {
            case .insert(let insert):
                print("inserted", insert.changedPersistentIdentifier)
            case .update(let update):
                print("updated", update.changedPersistentIdentifier)
            case .delete(let delete as DefaultHistoryDelete<Todo>):
                print("deleted remote id", delete.tombstone[\.remoteID] as Any)
            case .delete:
                break
            @unknown default:
                break
            }
        }
    }
    if let last = transactions.last?.token {
        try context.deleteHistory(HistoryDescriptor<DefaultHistoryTransaction>(
            predicate: #Predicate { $0.token < last }
        ))
    }
    return transactions.last?.token ?? token
}
```

- A delete leaves only a tombstone. Only attributes marked `@Attribute(.preserveValueOnDeletion)` survive in it (verified: `remoteID` present, `title` nil). Mark the identifier you need to mirror deletes to a server before you ship.
- `transaction.author` is whatever `context.author` was at save time; filter out your own writes with it.
- Prune consumed history (`deleteHistory`) or the store grows without bound. If several consumers read history (app, widget, sync), prune to the oldest token any of them has consumed.

## Schema migration

Version the schema from the first release. Each version is a `VersionedSchema` with its own nested model types; the app uses the latest through a typealias.

```swift
import Foundation
import SwiftData

enum NotesV1: VersionedSchema {
    static let versionIdentifier = Schema.Version(1, 0, 0)
    static var models: [any PersistentModel.Type] { [Note.self] }

    @Model final class Note {
        var name: String
        init(name: String) { self.name = name }
    }
}

enum NotesV2: VersionedSchema {
    static let versionIdentifier = Schema.Version(2, 0, 0)
    static var models: [any PersistentModel.Type] { [Note.self] }

    @Model final class Note {
        @Attribute(originalName: "name") var title: String
        var wordCount: Int = 0
        init(title: String) { self.title = title }
    }
}

enum NotesV3: VersionedSchema {
    static let versionIdentifier = Schema.Version(3, 0, 0)
    static var models: [any PersistentModel.Type] { [Note.self] }

    @Model final class Note {
        // originalName stays: a V1 store migrating through V2 still needs it.
        @Attribute(.unique, originalName: "name") var title: String
        var wordCount: Int = 0
        init(title: String) { self.title = title }
    }
}

typealias Note = NotesV3.Note

enum NotesMigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] { [NotesV1.self, NotesV2.self, NotesV3.self] }
    static var stages: [MigrationStage] { [v1ToV2, v2ToV3] }

    static let v1ToV2 = MigrationStage.lightweight(fromVersion: NotesV1.self, toVersion: NotesV2.self)

    static let v2ToV3 = MigrationStage.custom(
        fromVersion: NotesV2.self,
        toVersion: NotesV3.self,
        willMigrate: { context in
            // Adding .unique fails on existing duplicates: dedupe in the old schema first.
            var seen = Set<String>()
            for note in try context.fetch(FetchDescriptor<NotesV2.Note>()) where !seen.insert(note.title).inserted {
                context.delete(note)
            }
            try context.save()
        },
        didMigrate: { context in
            for note in try context.fetch(FetchDescriptor<NotesV3.Note>()) {
                note.wordCount = note.title.split(separator: " ").count
            }
            try context.save()
        }
    )
}

func openNotesStore(at url: URL) throws -> ModelContainer {
    try ModelContainer(
        for: Note.self,
        migrationPlan: NotesMigrationPlan.self,
        configurations: ModelConfiguration(url: url)
    )
}
```

- `static let versionIdentifier`. The `static var` form found in many examples fails under Swift 6 with `static property 'versionIdentifier' is not concurrency-safe because it is nonisolated global shared mutable state`.
- Keep `@Attribute(originalName:)` on a renamed property in every later version. With it dropped from V3 above, opening a V1 store through the V1 -> V2 -> V3 chain failed with `Cannot migrate store in-place: Validation error missing attribute values on mandatory destination attribute` (entity `Note`, attribute `title`); with it kept, the chain ran and produced `["hello world:2", "solo:1"]` from three V1 rows (verified).
- Lightweight covers: new properties with defaults, new models, removed properties, renames via `originalName`. Anything needing data rewriting is `.custom`: `willMigrate` sees the old schema's types, `didMigrate` the new one's. Both closures are `@Sendable (ModelContext) throws -> Void` and optional.
- Never delete a shipped `VersionedSchema` from `schemas`; a user can skip versions and the plan replays every stage in order.
- Test migrations against a copy of a real store built by the previous release, not only fresh stores.
- Core Data apps can adopt SwiftData over the same SQLite file when entity and attribute names match (`ModelConfiguration(url:)` at the Core Data store URL), or run both stacks side by side and copy data once.

## CloudKit sync

Requirements (from [Syncing model data across a person's devices](https://developer.apple.com/documentation/swiftdata/syncing-model-data-across-a-persons-devices)):

- Capabilities: iCloud with CloudKit and a container, plus Background Modes > Remote notifications.
- Model rules: no `.unique` / `#Unique`; every relationship optional; every attribute optional or defaulted; no `.deny` delete rule. Set the inverse explicitly when SwiftData cannot infer it.
- SwiftData picks the first container in the entitlements; pin one with `ModelConfiguration(cloudKitDatabase: .private("iCloud.com.example.app"))`. Only the private database syncs; there is no SwiftData API for the public database or `CKShare` sharing - use `NSPersistentCloudKitContainer` (Core Data) or CloudKit directly for those.
- Production CloudKit schemas are additive only: once promoted you cannot delete record types or change attribute types. Promote the development schema in the [CloudKit Console](https://icloud.developer.apple.com) before release, or production clients silently fail to sync new fields.
- Sync is last-writer-wins with no SwiftData conflict API. Design models so concurrent edits touch different records or fields.
- Debug with the launch argument `-com.apple.CoreData.CloudKitDebug 1` (higher numbers are more verbose) and watch for `CKError` in the console. Sync needs a signed-in iCloud account on the device or simulator.

Initialize the development schema once in DEBUG builds, before creating the `ModelContainer` (Apple's pattern, condensed):

```swift
import CoreData
import SwiftData

func initializeCloudKitSchema(for types: [any PersistentModel.Type], config: ModelConfiguration, containerID: String) throws {
    #if DEBUG
    try autoreleasepool {
        let description = NSPersistentStoreDescription(url: config.url)
        description.cloudKitContainerOptions = NSPersistentCloudKitContainerOptions(containerIdentifier: containerID)
        description.shouldAddStoreAsynchronously = false
        guard let model = NSManagedObjectModel.makeManagedObjectModel(for: types) else { return }
        let container = NSPersistentCloudKitContainer(name: "Schema", managedObjectModel: model)
        container.persistentStoreDescriptions = [description]
        container.loadPersistentStores { _, error in
            if let error { fatalError(error.localizedDescription) }
        }
        try container.initializeCloudKitSchema()
        if let store = container.persistentStoreCoordinator.persistentStores.first {
            try container.persistentStoreCoordinator.remove(store)
        }
    }
    #endif
}
```

## Previews and tests

```swift
import SwiftData
import SwiftUI

struct SampleData: PreviewModifier {
    static func makeSharedContext() async throws -> ModelContainer {
        let container = try ModelContainer(
            for: Project.self, Todo.self, Tag.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: true)
        )
        let project = Project(slug: "demo", name: "Demo")
        container.mainContext.insert(project)
        let todo = Todo(title: "Try previews")
        container.mainContext.insert(todo)
        todo.project = project
        return container
    }

    func body(content: Content, context: ModelContainer) -> some View {
        content.modelContainer(context)
    }
}

#Preview(traits: .modifier(SampleData())) {
    List { Text("Projects") }
}
```

`PreviewModifier.makeSharedContext()` builds the container once and shares it across every preview that uses the trait, which keeps previews fast.

```swift
import Foundation
import SwiftData
import Testing

@MainActor
struct TodoStoreTests {
    let container: ModelContainer

    init() throws {
        container = try ModelContainer(
            for: Project.self, Todo.self, Tag.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: true)
        )
    }

    @Test func openTodosExcludeDone() throws {
        let context = container.mainContext
        let done = Todo(title: "old")
        done.isDone = true
        context.insert(done)
        context.insert(Todo(title: "new"))
        try context.save()

        let open = try context.fetch(FetchDescriptor<Todo>(predicate: #Predicate { !$0.isDone }))
        #expect(open.map(\.title) == ["new"])
    }
}
```

Each test gets a fresh in-memory container because Swift Testing creates a new suite instance per test. Logic that must run under `swift test` without a simulator belongs in a local package (see architecture.md); SwiftData itself runs fine in macOS-hosted package tests.
