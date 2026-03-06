# Relationships & Predicates

## Table of Contents
- Relationship Types
- Delete Rules
- Inverse Relationships
- Advanced #Predicate
- Compound Predicates
- Relationship Queries

## Relationship Types

### One-to-many
```swift
@Model
final class Folder {
    var name: String

    @Relationship(deleteRule: .cascade, inverse: \Document.folder)
    var documents: [Document] = []

    init(name: String) { self.name = name }
}

@Model
final class Document {
    var title: String
    var folder: Folder?

    init(title: String, folder: Folder? = nil) {
        self.title = title
        self.folder = folder
    }
}

// Usage
let folder = Folder(name: "Projects")
let doc = Document(title: "Proposal", folder: folder)
context.insert(folder)
// doc is automatically associated via the relationship
```

### Many-to-many
```swift
@Model
final class Student {
    var name: String

    @Relationship(inverse: \Course.students)
    var courses: [Course] = []

    init(name: String) { self.name = name }
}

@Model
final class Course {
    var title: String
    var students: [Student] = []

    init(title: String) { self.title = title }
}

// Associate
let student = Student(name: "Alice")
let course = Course(title: "Swift 101")
student.courses.append(course)
// course.students now automatically contains student
```

### One-to-one
```swift
@Model
final class User {
    var name: String

    @Relationship(deleteRule: .cascade, inverse: \Profile.user)
    var profile: Profile?

    init(name: String) { self.name = name }
}

@Model
final class Profile {
    var bio: String
    var avatarURL: URL?
    var user: User?

    init(bio: String) { self.bio = bio }
}
```

## Delete Rules

| Rule | Behavior |
|------|----------|
| `.nullify` (default) | Set related objects' reference to nil |
| `.cascade` | Delete related objects |
| `.deny` | Prevent deletion if related objects exist |
| `.noAction` | Do nothing (can leave orphans) |

```swift
@Relationship(deleteRule: .cascade)    // Delete children when parent deleted
@Relationship(deleteRule: .nullify)    // Set to nil, keep children
@Relationship(deleteRule: .deny)       // Block deletion if children exist
```

### Cascade example
```swift
@Model
final class Project {
    @Relationship(deleteRule: .cascade)
    var tasks: [ProjectTask] = []
}

// Deleting project automatically deletes all its tasks
context.delete(project) // tasks are cascade-deleted
```

## Inverse Relationships

Always specify inverse for bidirectional relationships:

```swift
// Explicit inverse
@Relationship(inverse: \Document.folder)
var documents: [Document] = []

// SwiftData can infer inverse when unambiguous:
// If Document has only one Folder? property, inverse is auto-detected.
// Prefer explicit inverse for clarity.
```

## Advanced #Predicate

### String operations
```swift
// Contains (case-insensitive)
#Predicate<Document> { doc in
    doc.title.localizedStandardContains(searchText)
}

// Starts with
#Predicate<Document> { doc in
    doc.title.starts(with: "Draft")
}

// Not empty
#Predicate<Document> { doc in
    !doc.content.isEmpty
}
```

### Date comparisons
```swift
// Created today
let startOfDay = Calendar.current.startOfDay(for: .now)
#Predicate<Document> { doc in
    doc.createdAt >= startOfDay
}

// Within last week
let weekAgo = Calendar.current.date(byAdding: .day, value: -7, to: .now)!
#Predicate<Document> { doc in
    doc.createdAt >= weekAgo
}

// Between dates
#Predicate<Document> { doc in
    doc.createdAt >= startDate && doc.createdAt <= endDate
}
```

### Optional handling
```swift
// Has value
#Predicate<Task> { task in
    task.dueDate != nil
}

// Optional comparison (use force unwrap inside predicate)
#Predicate<Task> { task in
    task.dueDate != nil && task.dueDate! < Date.now
}
```

### Compound predicates
```swift
// AND
#Predicate<Task> { task in
    !task.isComplete && task.priority == .high
}

// OR
#Predicate<Task> { task in
    task.priority == .high || task.priority == .critical
}

// NOT
#Predicate<Task> { task in
    !(task.status == .archived)
}
```

### Collection predicates
```swift
// Contains element
#Predicate<Project> { project in
    project.tags.contains("urgent")
}

// Any match
#Predicate<Project> { project in
    project.tasks.contains(where: { !$0.isComplete })
}

// Count
#Predicate<Project> { project in
    project.tasks.count > 5
}

// All match
#Predicate<Folder> { folder in
    folder.documents.allSatisfy { $0.isReviewed }
}
```

## Dynamic Predicates

Build predicates based on runtime conditions:

```swift
func buildPredicate(
    searchText: String,
    showCompleted: Bool,
    priority: Priority?
) -> Predicate<Task> {
    #Predicate<Task> { task in
        (searchText.isEmpty || task.title.localizedStandardContains(searchText))
        && (showCompleted || !task.isComplete)
        && (priority == nil || task.priority == priority)
    }
}

// Use in @Query (via init)
struct TaskListView: View {
    @Query private var tasks: [Task]

    init(searchText: String, showCompleted: Bool, priority: Priority?) {
        let predicate = buildPredicate(
            searchText: searchText,
            showCompleted: showCompleted,
            priority: priority
        )
        _tasks = Query(filter: predicate, sort: \.createdAt, order: .reverse)
    }
}
```
