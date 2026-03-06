# ModelContainer & ModelContext

## Table of Contents
- ModelContainer Configuration
- ModelContext Operations
- Background Contexts
- Batch Operations
- Undo/Redo
- Previews & Testing

## ModelContainer Configuration

### Basic setup
```swift
// Default (SQLite, app's default location)
.modelContainer(for: [Project.self, Task.self])

// With configuration
let config = ModelConfiguration(
    "MyDB",
    schema: Schema([Project.self, Task.self]),
    url: .applicationSupportDirectory.appending(path: "myapp.store"),
    allowsSave: true
)
let container = try ModelContainer(
    for: Project.self, Task.self,
    configurations: config
)
```

### Multiple stores
```swift
// User data in one store, reference data in another
let userData = ModelConfiguration(
    "UserData",
    schema: Schema([Project.self, Task.self])
)
let referenceData = ModelConfiguration(
    "ReferenceData",
    schema: Schema([Template.self, Category.self]),
    url: bundledDBURL,
    allowsSave: false
)

let container = try ModelContainer(
    for: Project.self, Task.self, Template.self, Category.self,
    configurations: userData, referenceData
)
```

### In-memory (previews/testing)
```swift
let config = ModelConfiguration(isStoredInMemoryOnly: true)
let container = try ModelContainer(
    for: Project.self,
    configurations: config
)
```

### Injecting container
```swift
// Scene level
WindowGroup {
    ContentView()
}
.modelContainer(container)

// Or in a view
ContentView()
    .modelContainer(for: Project.self)
```

## ModelContext Operations

### CRUD
```swift
@Environment(\.modelContext) private var context

// Create
let project = Project(name: "New Project")
context.insert(project)

// Read
let descriptor = FetchDescriptor<Project>(
    predicate: #Predicate { !$0.isArchived },
    sortBy: [SortDescriptor(\.name)]
)
let projects = try context.fetch(descriptor)

// Update (just modify properties - auto-tracked)
project.name = "Updated Name"
project.updatedAt = .now

// Delete
context.delete(project)

// Save explicitly
try context.save()

// Check for unsaved changes
if context.hasChanges {
    try context.save()
}
```

### Auto-save
By default, ModelContext auto-saves on the next run loop iteration. To control:
```swift
// Disable auto-save
context.autosaveEnabled = false

// Manual save
try context.save()

// Rollback unsaved changes
context.rollback()
```

### Fetch count
```swift
let count = try context.fetchCount(
    FetchDescriptor<Project>(predicate: #Predicate { $0.isArchived })
)
```

### Fetch with pagination
```swift
var descriptor = FetchDescriptor<Project>(sortBy: [SortDescriptor(\.name)])
descriptor.fetchLimit = 20
descriptor.fetchOffset = page * 20

let page = try context.fetch(descriptor)
```

## Background Contexts

Perform heavy operations off the main thread:

```swift
// Create background context from container
let container = // your ModelContainer
let backgroundContext = ModelContext(container)

// Use in a detached task
@concurrent
func importData(_ data: [ImportRow]) async throws {
    let context = ModelContext(container)
    context.autosaveEnabled = false

    for row in data {
        let item = Item(from: row)
        context.insert(item)
    }

    try context.save()
}
```

### ModelActor (actor-isolated context)
```swift
@ModelActor
actor DataImporter {
    // modelContext and modelContainer are auto-provided

    func importItems(_ items: [ImportData]) throws {
        for item in items {
            let model = Project(name: item.name)
            modelContext.insert(model)
        }
        try modelContext.save()
    }

    func countProjects() throws -> Int {
        try modelContext.fetchCount(FetchDescriptor<Project>())
    }
}

// Usage
let importer = DataImporter(modelContainer: container)
try await importer.importItems(data)
```

## Batch Operations

### Batch delete
```swift
// Delete all archived projects
try context.delete(
    model: Project.self,
    where: #Predicate { $0.isArchived }
)
```

### Enumerate for bulk processing
```swift
let descriptor = FetchDescriptor<Project>()
descriptor.fetchBatchSize = 100

try context.enumerate(descriptor) { project in
    project.lastSyncedAt = .now
}
try context.save()
```

## Undo/Redo

```swift
// Enable undo manager
let container = try ModelContainer(for: Project.self)
container.mainContext.undoManager = UndoManager()

// In SwiftUI
@Environment(\.undoManager) private var undoManager

// Undo/redo
undoManager?.undo()
undoManager?.redo()

// Check availability
undoManager?.canUndo
undoManager?.canRedo
```

Toolbar integration:
```swift
.toolbar {
    ToolbarItem {
        Button(action: { undoManager?.undo() }) {
            Label("Undo", systemImage: "arrow.uturn.backward")
        }
        .disabled(!(undoManager?.canUndo ?? false))
    }
    ToolbarItem {
        Button(action: { undoManager?.redo() }) {
            Label("Redo", systemImage: "arrow.uturn.forward")
        }
        .disabled(!(undoManager?.canRedo ?? false))
    }
}
```

## Previews & Testing

### Preview container
```swift
struct ProjectListView_Previews: PreviewProvider {
    static var previews: some View {
        let config = ModelConfiguration(isStoredInMemoryOnly: true)
        let container = try! ModelContainer(for: Project.self, configurations: config)

        // Seed data
        let context = container.mainContext
        let project = Project(name: "Sample Project")
        context.insert(project)

        return ProjectListView()
            .modelContainer(container)
    }
}

// Or with @Previewable macro
#Preview {
    @Previewable @State var container = {
        let config = ModelConfiguration(isStoredInMemoryOnly: true)
        let container = try! ModelContainer(for: Project.self, configurations: config)
        let project = Project(name: "Preview Project")
        container.mainContext.insert(project)
        return container
    }()

    ProjectListView()
        .modelContainer(container)
}
```

### Testing
```swift
@Suite("Project Repository")
struct ProjectRepositoryTests {
    let container: ModelContainer

    init() throws {
        container = try ModelContainer(
            for: Project.self, Task.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: true)
        )
    }

    @Test func fetchActiveProjects() throws {
        let context = ModelContext(container)
        context.insert(Project(name: "Active"))

        let archived = Project(name: "Old")
        archived.isArchived = true
        context.insert(archived)
        try context.save()

        let descriptor = FetchDescriptor<Project>(
            predicate: #Predicate { !$0.isArchived }
        )
        let active = try context.fetch(descriptor)
        #expect(active.count == 1)
        #expect(active.first?.name == "Active")
    }
}
```
