# Models & Schema

## Table of Contents
- @Model Basics
- Property Attributes
- Codable Properties
- Transient Properties
- External Storage
- Transformable
- Unique Constraints
- Custom Hashable/Identifiable

## @Model Basics

`@Model` is a macro that transforms a class into a SwiftData persistent model:

```swift
@Model
final class Note {
    var title: String
    var content: String
    var createdAt: Date
    var updatedAt: Date
    var isPinned: Bool
    var color: NoteColor

    init(title: String, content: String = "") {
        self.title = title
        self.content = content
        self.createdAt = .now
        self.updatedAt = .now
        self.isPinned = false
        self.color = .default
    }
}
```

What `@Model` synthesizes:
- `PersistentModel` conformance (persistence)
- `Observable` conformance (SwiftUI reactivity)
- `Hashable` and `Identifiable` (based on persistent ID)
- Schema definition for the persistence store

### Rules
- Must be a `class` (not struct)
- Prefer `final` for clarity
- Must have at least one stored property
- All stored properties must be persistable types
- Needs a designated initializer

### Supported property types
- Primitives: `String`, `Int`, `Double`, `Float`, `Bool`, `Date`, `Data`, `URL`, `UUID`
- Optional versions of all above
- Enums with `Codable` raw values
- `Codable` structs/enums
- Collections: `[T]` where T is any supported type
- Relationships: Other `@Model` types

## Property Attributes

### @Attribute
```swift
@Model
final class Document {
    // Unique constraint - no two documents with same slug
    @Attribute(.unique) var slug: String

    // Spotlight indexing
    @Attribute(.spotlight) var title: String

    // External storage for large data
    @Attribute(.externalStorage) var thumbnail: Data?

    // Custom original name (for migration)
    @Attribute(originalName: "old_name") var newName: String

    // Preserve value on deletion
    @Attribute(.preserveValueOnDeletion) var archiveID: UUID

    // Per-field encryption at rest in CloudKit (NOT local-store encryption).
    // Apple DTS confirms: `.allowsCloudEncryption` only has effect on CloudKit-
    // synced stores. Use platform Data Protection (`FileProtectionType`) for
    // local at-rest encryption.
    @Attribute(.allowsCloudEncryption) var sensitiveData: Data?

    var content: String

    init(slug: String, title: String, content: String) {
        self.slug = slug
        self.title = title
        self.newName = title
        self.archiveID = UUID()
        self.content = content
    }
}
```

### @Transient

Properties not persisted to store:

```swift
@Model
final class Task {
    var title: String
    var isComplete: Bool

    // Not saved to database
    @Transient var isSelected = false
    @Transient var cachedPreview: NSImage?

    init(title: String) {
        self.title = title
        self.isComplete = false
    }
}
```

**Important**: `@Transient` properties must have default values since they won't be loaded from the store.

## Codable Properties

Store complex types as Codable:

```swift
struct Address: Codable {
    var street: String
    var city: String
    var zip: String
    var country: String
}

struct Preferences: Codable {
    var theme: String
    var fontSize: Int
    var notifications: Bool
}

@Model
final class UserProfile {
    var name: String
    var address: Address       // Stored as encoded data
    var preferences: Preferences

    init(name: String, address: Address, preferences: Preferences) {
        self.name = name
        self.address = address
        self.preferences = preferences
    }
}
```

### Enum properties
```swift
enum Priority: String, Codable, CaseIterable {
    case low, medium, high, critical
}

enum TaskStatus: Int, Codable {
    case todo = 0
    case inProgress = 1
    case done = 2
    case archived = 3
}

@Model
final class Task {
    var title: String
    var priority: Priority
    var status: TaskStatus

    init(title: String, priority: Priority = .medium) {
        self.title = title
        self.priority = priority
        self.status = .todo
    }
}
```

## External Storage

For large binary data (images, files):

```swift
@Model
final class Photo {
    var name: String
    var dateTaken: Date

    // Stored outside the main SQLite file
    @Attribute(.externalStorage) var imageData: Data?
    @Attribute(.externalStorage) var thumbnailData: Data?

    init(name: String, imageData: Data?) {
        self.name = name
        self.dateTaken = .now
        self.imageData = imageData
    }
}
```

External storage stores the data as a file on disk rather than inline in SQLite, improving query performance when you don't need the large data.

## Unique Constraints

```swift
@Model
final class Tag {
    @Attribute(.unique) var name: String
    var color: String

    init(name: String, color: String = "blue") {
        self.name = name
        self.color = color
    }
}

// Inserting a Tag with a duplicate name will upsert (update existing)
let tag = Tag(name: "swift")      // Creates new
let tag2 = Tag(name: "swift")     // Updates existing
context.insert(tag2)              // No duplicate
```

**Note**: Unique constraints are not supported with CloudKit sync.

## Identifiable & Hashable

`@Model` types automatically conform to `Identifiable` using the persistent model ID:

```swift
// Automatic - no need to define 'id'
@Model
final class Item {
    var name: String
    init(name: String) { self.name = name }
}

// item.id is PersistentIdentifier (auto-generated)
// item.persistentModelID is the same value

// In SwiftUI Lists
ForEach(items) { item in  // Identifiable via @Model
    Text(item.name)
}
```

If you need a custom ID:
```swift
@Model
final class Item {
    @Attribute(.unique) var customID: UUID
    var name: String

    init(name: String) {
        self.customID = UUID()
        self.name = name
    }
}
```

## Compound uniqueness: `#Unique`

`@Attribute(.unique)` constrains a single property. For multi-property (compound) uniqueness, use the freestanding `#Unique` macro inside the model body:

```swift
@Model
final class Enrollment {
    #Unique<Enrollment>([\.studentID, \.courseID])   // the pair must be unique

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

Multiple constraint sets are allowed: `#Unique<T>([\.a, \.b], [\.c])`. Same CloudKit caveat as `.unique` - unique constraints are unsupported when syncing, so a CloudKit-backed model cannot declare them.

## Indexes: `#Index`

Declares single or compound indexes so predicates and sorts can use them instead of scanning:

```swift
@Model
final class LogEntry {
    #Index<LogEntry>([\.timestamp], [\.level, \.timestamp])

    var timestamp: Date
    var level: String
    var message: String

    init(level: String, message: String) {
        self.level = level
        self.message = message
        self.timestamp = .now
    }
}
```

Index the properties you actually filter and sort on. Compound index column order matters - `[\.level, \.timestamp]` serves "filter by level, sort by timestamp" but not the reverse.

## Model inheritance

`@Model` classes can subclass other `@Model` classes (**macOS 26.0+**). Fetches on the parent type return subclass instances by default:

```swift
@available(macOS 26, *)
@Model class Media {
    var title: String
    init(title: String) { self.title = title }
}

@available(macOS 26, *)
@Model final class Movie: Media {
    var runtime: Int = 0
    init(title: String, runtime: Int) {
        self.runtime = runtime
        super.init(title: title)
    }
}

@available(macOS 26, *)
@Model final class Podcast: Media {
    var episodeCount: Int = 0
    init(title: String, episodeCount: Int) {
        self.episodeCount = episodeCount
        super.init(title: title)
    }
}

// Returns Movies and Podcasts too
let all = try context.fetch(FetchDescriptor<Media>())
```

The `@available` annotation is not optional: a `PersistentModel` subclass without one fails to compile with `A PersistentModel Subclass is required to have platform availability specified`, and annotating it below 26.0 fails with `A PersistentModel Subclass requires macOS 26.0 or greater`. Subclasses need explicit initializers like every other `@Model`.

Control this on deletes with `includeSubclasses` (defaults to `true`):

```swift
try context.delete(model: Media.self,
                   where: #Predicate { $0.title.isEmpty },
                   includeSubclasses: false)   // only exact Media rows
```

Inheritance costs query performance and complicates migration - prefer a shared protocol or an enum discriminator column unless you genuinely need polymorphic fetches.

## `.ephemeral`

The complete `Schema.Attribute.Option` set in the macOS 26.5 SDK is exactly: `.unique`, `.transformable(by:)`, `.externalStorage`, `.allowsCloudEncryption`, `.preserveValueOnDeletion`, `.ephemeral`, `.spotlight`. There is no `.encrypt` option - CloudKit field encryption is `.allowsCloudEncryption` (covered above).

`.ephemeral` is the one not documented elsewhere in this file: the property participates in the model but is never persisted. Use it for transient state - a computed progress value, a cached thumbnail - that should not survive a relaunch.

```swift
@Model final class Download {
    var url: URL
    @Attribute(.ephemeral) var bytesReceived: Int = 0   // reset on every launch
    init(url: URL) { self.url = url }
}
```
