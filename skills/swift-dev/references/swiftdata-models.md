# SwiftData Models, Predicates and Queries

Defining `@Model` types, attributes, relationships, `#Predicate`, `FetchDescriptor` and `@Query` (including sectioned queries) on iOS and macOS.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every block compiled through SIL (`swiftc -emit-sil`, so region-isolation checks ran) for iOS 27 and macOS 27, with and without `-default-isolation MainActor`; the predicate, uniqueness, inheritance, `.ephemeral` and `.codable` behavior was executed against an on-disk SQLite store in a scratch SPM package on macOS 27.2.

## Contents
- @Model basics
- Attributes and options
- Codable values and `.codable`
- Uniqueness and indexes
- Relationships
- Inheritance
- #Predicate: what works, what crashes
- FetchDescriptor
- @Query and sectioned queries

## @Model basics

```swift
import Foundation
import SwiftData

@Model
final class Project {
    @Attribute(.unique) var slug: String
    var name: String
    var createdAt: Date
    var isArchived: Bool = false

    @Relationship(deleteRule: .cascade, inverse: \Todo.project)
    var todos: [Todo] = []

    init(slug: String, name: String) {
        self.slug = slug
        self.name = name
        self.createdAt = .now
    }
}
```

- `@Model` makes the class `PersistentModel`, `Observable`, `Identifiable` and `Hashable` (identity is `persistentModelID`). It must be a class; mark it `final` unless you subclass it.
- Every `@Model` needs an explicit designated initializer. The macro does not synthesize one: omitting it fails with `@Model requires an initializer be provided for '<Type>'`.
- Persistable property types: `String`, numeric types, `Bool`, `Date`, `Data`, `URL`, `UUID`, their optionals, `Codable` enums and structs, arrays of those, and other `@Model` types (relationships).
- Do not name a model `Task`: it shadows Swift concurrency's `Task` in every file of the module. `Todo` / `TaskItem` avoid the fight.
- Default property values (`var isArchived: Bool = false`) become the schema default and are what lightweight migration and CloudKit need. Write enum defaults fully qualified: `var priority: Priority = .medium` fails with `A default value requires a fully qualified domain named value`; use `Priority.medium`.

## Attributes and options

The complete `Schema.Attribute.Option` set in the 27.0 SDK:

| Option | Effect |
|---|---|
| `.unique` | One row per value; inserting a duplicate upserts (updates the existing row). Not allowed with CloudKit. |
| `.externalStorage` | Store large `Data` as a file beside the SQLite store; the column holds a reference. |
| `.spotlight` | Index the value in Core Spotlight. |
| `.preserveValueOnDeletion` | Keep the value in the history tombstone after the row is deleted (see swiftdata-store.md). |
| `.ephemeral` | Tracked for changes but never written: a fresh fetch returns the default value. |
| `.allowsCloudEncryption` | Encrypt the field in CloudKit. Affects only CloudKit-synced stores - it is not local at-rest encryption; use Data Protection for that. |
| `.transformable(by:)` | Store via a `ValueTransformer` (type or registered name). |
| `.codable` | Store the property through its `Codable` representation (iOS 27 / macOS 27). |

`@Attribute` also takes `originalName:` (rename without data loss, see migrations in swiftdata-store.md) and `hashModifier:` (force a property to count as changed in a migration without renaming it). `@Transient` keeps a property out of the schema entirely; it needs a default value.

```swift
import Foundation
import SwiftData

enum Priority: String, Codable, CaseIterable {
    case low, medium, high
}

@Model
final class Todo {
    var title: String
    var isDone: Bool = false
    var priority: Priority = Priority.medium
    var dueDate: Date?
    var project: Project?
    @Relationship(inverse: \Tag.todos) var tags: [Tag] = []

    @Attribute(.externalStorage) var attachment: Data?
    @Attribute(.preserveValueOnDeletion) var remoteID = UUID()
    @Attribute(.ephemeral) var uploadProgress: Double = 0
    @Transient var isSelected = false

    init(title: String, dueDate: Date? = nil, priority: Priority = .medium) {
        self.title = title
        self.dueDate = dueDate
        self.priority = priority
    }
}

@Model
final class Tag {
    @Attribute(.unique) var name: String
    var todos: [Todo] = []

    init(name: String) { self.name = name }
}
```

## Codable values and `.codable`

A plain `Codable` struct property is stored as a composite attribute: SwiftData flattens its fields into columns, so predicates can reach into it (`$0.home.city == "Kyiv"` works). `@Attribute(.codable)` (iOS 27 / macOS 27) instead stores the value through its `Codable` encoding - use it for types you do not control or whose shape does not flatten (Apple: "Uses the property's codable representation to store the property"). Predicates on a `.codable` property's fields still ran correctly on macOS 27.2.

```swift
import Foundation
import SwiftData

nonisolated struct Coordinate: Codable, Hashable {
    var latitude: Double
    var longitude: Double
}

@Model
final class Place {
    var name: String
    @Attribute(.codable) var coordinate: Coordinate

    init(name: String, coordinate: Coordinate) {
        self.name = name
        self.coordinate = coordinate
    }
}
```

Gotcha: in a target with default `MainActor` isolation (the Xcode 26+ app template), a `Codable` struct's conformance is main-actor-isolated, and `@Attribute(.codable)` fails to compile with `main actor-isolated conformance of 'Coordinate' to 'Encodable' cannot be used in nonisolated context`. Declare such value types `nonisolated struct`. Plain composite (non-`.codable`) properties did not hit this.

## Uniqueness and indexes

`@Attribute(.unique)` covers one property. For compound keys and query performance, use the freestanding macros inside the model body (iOS 18 / macOS 15+):

```swift
import Foundation
import SwiftData

@Model
final class Enrollment {
    #Unique<Enrollment>([\.studentID, \.courseID])
    #Index<Enrollment>([\.enrolledAt], [\.courseID, \.enrolledAt])

    var studentID: UUID
    var courseID: UUID
    var enrolledAt: Date

    init(studentID: UUID, courseID: UUID) {
        self.studentID = studentID
        self.courseID = courseID
        self.enrolledAt = .now
    }
}
```

- A duplicate insert under `.unique` or `#Unique` upserts silently: two inserts of the same key leave one row (verified). If you need "reject duplicates", check with a fetch first.
- `#Unique<T>([\.a, \.b], [\.c])` declares several independent constraints.
- Compound index order matters: `[\.courseID, \.enrolledAt]` serves "filter by course, sort by date", not the reverse. Index only what you filter and sort on.
- Unique constraints are unsupported with CloudKit sync; a synced model cannot declare them.

## Relationships

```swift
import Foundation
import SwiftData

@Model
final class Book {
    var title: String
    var author: Author?

    @Relationship(deleteRule: .cascade, minimumModelCount: 1, maximumModelCount: 50, inverse: \Chapter.book)
    var chapters: [Chapter] = []

    init(title: String) { self.title = title }
}

@Model
final class Author {
    var name: String
    @Relationship(deleteRule: .nullify, inverse: \Book.author) var books: [Book] = []
    init(name: String) { self.name = name }
}

@Model
final class Chapter {
    var number: Int
    var book: Book?
    init(number: Int) { self.number = number }
}
```

| Delete rule | On delete of the owner |
|---|---|
| `.nullify` (default) | Related objects' back-reference becomes `nil` |
| `.cascade` | Related objects are deleted too (also applied by `context.delete(model:where:)` batch deletes - verified) |
| `.deny` | Deletion fails while related objects exist (not supported by CloudKit) |
| `.noAction` | Nothing; can leave dangling references |

- Declare `inverse:` on exactly one side. Setting either side updates the other: `todo.project = p` makes `p.todos` contain `todo` immediately, before save (verified).
- `minimumModelCount` / `maximumModelCount` are validated on `save()`: a `Book` with zero chapters above fails to save with a Core Data validation error on `chapters`.
- Many-to-many is two array properties with `inverse:` on one of them (`Todo.tags` / `Tag.todos` above).
- `inverse: nil` creates a deliberately one-way relationship.
- Relationships must be optional (to-one) for CloudKit.

## Inheritance

`@Model` subclasses work on iOS 26 / macOS 26+. Fetching the base type returns subclass instances too.

```swift
import Foundation
import SwiftData

@available(iOS 26, macOS 26, *)
@Model class Media {
    var title: String
    init(title: String) { self.title = title }
}

@available(iOS 26, macOS 26, *)
@Model final class Movie: Media {
    var runtime: Int = 0
    init(title: String, runtime: Int) {
        self.runtime = runtime
        super.init(title: title)
    }
}
```

- The `@available` annotation is mandatory on the subclass: without it the macro fails with `A PersistentModel Subclass is required to have platform availability specified`.
- `context.delete(model: Media.self, where: ..., includeSubclasses: false)` limits a batch delete to the exact type (the default is `true`).
- Inheritance costs query performance and complicates migration. Prefer a protocol or an enum discriminator column unless you need polymorphic fetches.

## #Predicate: what works, what crashes

`#Predicate` compiles to SQL. Some Swift that typechecks is rejected by the macro, and a few predicates compile but crash at fetch time. Results below are from runs on macOS 27.2:

| Predicate | Result |
|---|---|
| `$0.name.localizedStandardContains(term)` | Works - the default case- and diacritic-insensitive search |
| `$0.name.starts(with: "Draft")` | Works |
| `$0.name.lowercased().contains(x)` | Compile error: `The lowercased() function is not supported in this predicate` |
| `$0.priority == .high` / `== Priority.high` | Compile error: `key path cannot refer to enum case 'high'` |
| `$0.priority == high` with `let high = Priority.high` captured outside | Works |
| `$0.dueDate != nil && $0.dueDate! < now` | Works |
| `$0.dueDate.flatMap { $0 < now } ?? false` | Works |
| `if let d = $0.dueDate { d < now } else { false }` | Works |
| `$0.project?.slug == "a"` | Works (to-one key path) |
| `$0.todos.contains { !$0.isDone }`, `$0.todos.count > 1`, `$0.todos.allSatisfy { $0.isDone }` | Work (to-many) |
| `$0.home.city == "Kyiv"` (non-optional composite struct) | Works |
| `$0.address?.city == "Kyiv"` (optional composite struct) | Crashes: `NSInvalidArgumentException: keypath 'address' not found in entity` |
| `$0.labels.contains("x")` where `labels: [String]` | Crashes: `EXC_BAD_ACCESS` on the SQL queue |

For tag-like lists you filter on, model them as a relationship (`[Tag]`) rather than `[String]`. For optional structs you filter on, make them non-optional with a default.

Captured values must be local constants: a predicate cannot reach `self` or call methods. Compose predicates with `evaluate`:

```swift
import Foundation
import SwiftData

func todoFilter(search: String, showDone: Bool, priority: Priority?) -> Predicate<Todo> {
    let notDone = #Predicate<Todo> { !$0.isDone }
    let matches = #Predicate<Todo> { search.isEmpty || $0.title.localizedStandardContains(search) }
    let wanted = priority ?? .medium
    let ignorePriority = priority == nil
    return #Predicate<Todo> { todo in
        matches.evaluate(todo)
            && (showDone || notDone.evaluate(todo))
            && (ignorePriority || todo.priority == wanted)
    }
}
```

## FetchDescriptor

```swift
import Foundation
import SwiftData

func overdueTodos(in context: ModelContext, page: Int) throws -> [Todo] {
    let now = Date.now
    var descriptor = FetchDescriptor<Todo>(
        predicate: #Predicate { !$0.isDone && $0.dueDate != nil && $0.dueDate! < now },
        sortBy: [SortDescriptor(\.dueDate), SortDescriptor(\.title)]
    )
    descriptor.fetchLimit = 50
    descriptor.fetchOffset = page * 50
    descriptor.relationshipKeyPathsForPrefetching = [\.project]
    descriptor.propertiesToFetch = [\.title, \.dueDate]
    return try context.fetch(descriptor)
}

func counts(in context: ModelContext) throws -> (open: Int, ids: [PersistentIdentifier]) {
    let open = try context.fetchCount(FetchDescriptor<Todo>(predicate: #Predicate { !$0.isDone }))
    let ids = try context.fetchIdentifiers(FetchDescriptor<Todo>())
    return (open, ids)
}

func scanAll(in context: ModelContext) throws -> Int {
    var descriptor = FetchDescriptor<Todo>()
    descriptor.includePendingChanges = false
    let lazy = try context.fetch(descriptor, batchSize: 500)
    return lazy.count
}
```

- `relationshipKeyPathsForPrefetching` is the highest-leverage knob: a list showing `todo.project.name` for 500 rows otherwise faults each project in separately.
- `propertiesToFetch` loads only those columns; others fault in on access.
- `fetchIdentifiers` returns `PersistentIdentifier`s without materializing models - the cheap way to diff or hand work to another context.
- `fetch(_:batchSize:)` returns a lazily faulting `FetchResultsCollection`. It throws `SwiftDataError.includePendingChangesWithBatchSize` unless you set `includePendingChanges = false` first (verified).
- `fetchCount` runs `COUNT` in SQL; never `fetch(...).count`.

## @Query and sectioned queries

`@Query` is the SwiftUI read path: it fetches on the main context and re-renders when matching rows change.

```swift
import SwiftData
import SwiftUI

struct TodoList: View {
    @Query(filter: #Predicate<Todo> { !$0.isDone }, sort: \Todo.dueDate, order: .forward, animation: .default)
    private var open: [Todo]

    var body: some View {
        List(open) { todo in Text(todo.title) }
    }
}

struct SearchableTodoList: View {
    @Query private var todos: [Todo]

    init(search: String, showDone: Bool) {
        _todos = Query(filter: todoFilter(search: search, showDone: showDone, priority: nil),
                       sort: [SortDescriptor(\Todo.title)])
    }

    var body: some View {
        List(todos) { todo in Text(todo.title) }
    }
}
```

- To change the filter at runtime, rebuild the `Query` in `init` (above) and let the parent pass new inputs; the query property itself is read-only.
- For a limit or offset, build a `FetchDescriptor` in `init` and assign `_todos = Query(descriptor)`.
- `@Query` only works inside a `View` with a `modelContainer` in the environment; outside SwiftUI use `ResultsObserver` (swiftdata-store.md).

### Sectioned results (iOS 27 / macOS 27)

`@Query(..., sectionBy:)` groups rows by a `String` (or `String?`) key path and yields `SectionedResults<Model, String>`; each element is a `ResultsSection` with a `title` and the rows. Sort by the section key first so sections are contiguous. The key path must be a stored attribute: a computed property typechecks but traps at runtime with `Couldn't find \Project.statusTitle on Project`.

```swift
import SwiftData
import SwiftUI

@Model
final class Ticket {
    var title: String
    var status: String = "Open"
    init(title: String) { self.title = title }
}

@available(iOS 27, macOS 27, *)
struct TicketsByStatus: View {
    @Query(sort: \Ticket.status, sectionBy: \Ticket.status)
    private var sections: SectionedResults<Ticket, String>

    var body: some View {
        List {
            ForEach(sections) { section in
                Section(section.title) {
                    ForEach(section) { ticket in Text(ticket.title) }
                }
            }
        }
    }
}
```

`SectionedResults` also offers `sectionTitles`, `subscript(sectionTitle:)`, `contains(sectionTitle:)` and `index(ofSectionTitled:)`.
