# Schema Migrations

## Table of Contents
- Versioned Schemas
- Lightweight Migration
- Custom Migration
- SchemaMigrationPlan
- Core Data Migration
- Best Practices

## Versioned Schemas

Define each version of your schema:

```swift
// Version 1: Original
enum AppSchemaV1: VersionedSchema {
    static var versionIdentifier = Schema.Version(1, 0, 0)
    static var models: [any PersistentModel.Type] {
        [Project.self]
    }

    @Model
    final class Project {
        var name: String
        var isActive: Bool

        init(name: String) {
            self.name = name
            self.isActive = true
        }
    }
}

// Version 2: Added fields
enum AppSchemaV2: VersionedSchema {
    static var versionIdentifier = Schema.Version(2, 0, 0)
    static var models: [any PersistentModel.Type] {
        [Project.self]
    }

    @Model
    final class Project {
        var name: String
        var isActive: Bool
        var createdAt: Date    // New field
        var priority: Int      // New field

        init(name: String) {
            self.name = name
            self.isActive = true
            self.createdAt = .now
            self.priority = 0
        }
    }
}

// Version 3: Renamed + added relationship
enum AppSchemaV3: VersionedSchema {
    static var versionIdentifier = Schema.Version(3, 0, 0)
    static var models: [any PersistentModel.Type] {
        [Project.self, Task.self]
    }

    @Model
    final class Project {
        var title: String      // Renamed from 'name'
        var isActive: Bool
        var createdAt: Date
        var priority: Int

        @Relationship(deleteRule: .cascade)
        var tasks: [Task] = [] // New relationship

        init(title: String) {
            self.title = title
            self.isActive = true
            self.createdAt = .now
            self.priority = 0
        }
    }

    @Model
    final class Task {
        var title: String
        var isComplete: Bool
        var project: Project?

        init(title: String) {
            self.title = title
            self.isComplete = false
        }
    }
}
```

## Lightweight Migration

For additive changes (new properties with defaults, new models):

```swift
enum AppMigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] {
        [AppSchemaV1.self, AppSchemaV2.self]
    }

    static var stages: [MigrationStage] {
        [migrateV1toV2]
    }

    static let migrateV1toV2 = MigrationStage.lightweight(
        fromVersion: AppSchemaV1.self,
        toVersion: AppSchemaV2.self
    )
}
```

Lightweight migration handles:
- Adding new properties (with default values)
- Adding new model types
- Removing properties
- Renaming properties (with `@Attribute(originalName:)`)

### Property rename
```swift
// In V2, rename 'name' to 'title'
@Model
final class Project {
    @Attribute(originalName: "name")
    var title: String
    // ...
}
```

## Custom Migration

For complex transformations:

```swift
enum AppMigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] {
        [AppSchemaV1.self, AppSchemaV2.self, AppSchemaV3.self]
    }

    static var stages: [MigrationStage] {
        [migrateV1toV2, migrateV2toV3]
    }

    static let migrateV1toV2 = MigrationStage.lightweight(
        fromVersion: AppSchemaV1.self,
        toVersion: AppSchemaV2.self
    )

    static let migrateV2toV3 = MigrationStage.custom(
        fromVersion: AppSchemaV2.self,
        toVersion: AppSchemaV3.self
    ) { context in
        // Custom migration logic
        let projects = try context.fetch(FetchDescriptor<AppSchemaV2.Project>())

        for project in projects {
            // Transform data during migration
            // e.g., capitalize all names
            project.name = project.name.capitalized
        }

        try context.save()
    }
}
```

## SchemaMigrationPlan

Register with container:

```swift
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(
            for: AppSchemaV3.Project.self,
            migrationPlan: AppMigrationPlan.self
        )
    }
}
```

### Multiple migration chains
```swift
// Each stage migrates sequentially: V1 -> V2 -> V3
// User on V1 will run both stages
// User on V2 will run only V2 -> V3
static var stages: [MigrationStage] {
    [migrateV1toV2, migrateV2toV3]
}
```

## Migrating from Core Data

### Coexistence approach (recommended)
Run both Core Data and SwiftData side by side, migrating data at runtime:

```swift
@main
struct MyApp: App {
    let swiftDataContainer: ModelContainer
    let coreDataStack: NSPersistentContainer

    init() {
        // Set up SwiftData
        swiftDataContainer = try! ModelContainer(for: Project.self)

        // Set up legacy Core Data
        coreDataStack = NSPersistentContainer(name: "LegacyModel")
        coreDataStack.loadPersistentStores { _, _ in }

        // Migrate on first launch
        if !UserDefaults.standard.bool(forKey: "migrated_to_swiftdata") {
            migrateFromCoreData()
            UserDefaults.standard.set(true, forKey: "migrated_to_swiftdata")
        }
    }

    func migrateFromCoreData() {
        let coreDataContext = coreDataStack.viewContext
        let swiftDataContext = swiftDataContainer.mainContext

        // Fetch from Core Data
        let request = NSFetchRequest<NSManagedObject>(entityName: "CDProject")
        let cdProjects = try! coreDataContext.fetch(request)

        // Insert into SwiftData
        for cdProject in cdProjects {
            let project = Project(
                name: cdProject.value(forKey: "name") as! String
            )
            swiftDataContext.insert(project)
        }

        try! swiftDataContext.save()
    }
}
```

### Direct replacement
If your Core Data model is simple, SwiftData can often read the existing SQLite store:

```swift
// Point SwiftData to the existing Core Data store
let storeURL = NSPersistentContainer.defaultDirectoryURL()
    .appendingPathComponent("MyApp.sqlite")

let config = ModelConfiguration(url: storeURL)
let container = try ModelContainer(
    for: Project.self,
    configurations: config
)
```

Requirements:
- SwiftData model class name must match Core Data entity name
- Property names must match attribute names
- Types must be compatible

## Best Practices

1. **Always version your schema** from the start, even if you only have V1
2. **Use lightweight migration** whenever possible (simpler, safer)
3. **Test migrations** with real data before shipping
4. **Keep migration stages small** - one logical change per stage
5. **Back up user data** before running migrations in production
6. **Use `@Attribute(originalName:)`** for renames instead of delete+add
7. **New properties must have defaults** for lightweight migration to work
8. **Never delete a VersionedSchema** that users might still be running
