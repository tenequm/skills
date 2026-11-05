# CloudKit Sync

## Table of Contents
- Setup
- Configuration Options
- Model Constraints
- Conflict Resolution
- Debugging Sync
- Sharing

## Setup

### 1. Enable capabilities in Xcode
- Signing & Capabilities > + Capability > iCloud
- Check "CloudKit"
- Select or create a container (e.g., `iCloud.com.yourapp`)
- Also add "Background Modes" > "Remote notifications" for push-based sync

### 2. Configure container
```swift
// Default: auto-syncs all models to private CloudKit database
@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(for: [Project.self, Task.self])
        // CloudKit sync happens automatically if iCloud capability is enabled
    }
}
```

### 3. Explicit configuration
```swift
let config = ModelConfiguration(
    cloudKitDatabase: .automatic // Uses default container
)

// Or specify database type
let privateConfig = ModelConfiguration(
    cloudKitDatabase: .private("iCloud.com.yourapp")
)

// Disable sync for specific config
let localConfig = ModelConfiguration(
    cloudKitDatabase: .none
)

// Mix synced and local storage
let syncedConfig = ModelConfiguration(
    "Synced",
    schema: Schema([Project.self]),
    cloudKitDatabase: .automatic
)
let localConfig = ModelConfiguration(
    "Local",
    schema: Schema([CacheItem.self]),
    cloudKitDatabase: .none
)

let container = try ModelContainer(
    for: Project.self, CacheItem.self,
    configurations: syncedConfig, localConfig
)
```

## Model Constraints for CloudKit

CloudKit imposes stricter requirements on models:

```swift
@Model
final class SyncableProject {
    // All properties must have default values or be optional
    var name: String = ""
    var description: String?
    var createdAt: Date = .now
    var isArchived: Bool = false

    // Relationships must be optional
    @Relationship(deleteRule: .nullify)
    var tasks: [SyncableTask]? // Optional array

    // NO unique constraints (not supported with CloudKit)
    // @Attribute(.unique) var slug: String // WRONG

    init(name: String) {
        self.name = name
    }
}
```

### Rules
- All properties must have defaults or be optional
- No `@Attribute(.unique)` constraints
- Relationships must be optional
- Delete rule `.deny` not recommended (can fail silently)
- Avoid very large `Data` properties (CloudKit has size limits)
- Model class name becomes the CloudKit record type

## Conflict Resolution

CloudKit uses last-writer-wins by default, and SwiftData handles most merge work transparently. There is **no public SwiftData API** that surfaces conflicts as `NSMergeConflict` objects on `ModelContext.didSave` — that's a Core Data pattern that does not apply here. If you need programmatic conflict inspection and resolution policies today, you must drop down to `NSPersistentCloudKitContainer` + Core Data.

For SwiftData + CloudKit apps, design models to minimize conflicts (see Best Practices below) rather than relying on post-hoc conflict handlers.

### Best practices
- Use server timestamps for ordering (`createdAt`, `updatedAt`)
- Design models to minimize conflicts (separate frequently-changed properties)
- Expect eventual consistency (sync is not instant)
- Test with multiple devices/simulators

## Debugging Sync

### Enable CloudKit logging
```bash
# In Xcode scheme, add launch argument:
-com.apple.CoreData.CloudKitDebug 1

# Verbose logging:
-com.apple.CoreData.CloudKitDebug 3
```

### CloudKit Dashboard
1. Go to https://icloud.developer.apple.com
2. Select your container
3. View records, zones, subscriptions
4. Check for errors in the "Logs" section

### Common issues

**Sync not starting:**
- Verify iCloud is signed in (System Settings > Apple Account)
- Check CloudKit container identifier matches capability
- Ensure network connectivity
- Check Console.app for CloudKit errors

**Data not appearing on other devices:**
- Sync is eventually consistent (can take seconds to minutes)
- Verify both devices use the same iCloud account
- Check that the model schema matches on both versions
- Look for CKError codes in logs

**Schema mismatch:**
- After adding new properties, deploy schema to CloudKit Dashboard
- Development environment: auto-deployed
- Production: must manually deploy via Dashboard

## Sharing (CloudKit Sharing)

Share records with other iCloud users:

```swift
// Note: Direct SwiftData sharing APIs are limited.
// For advanced sharing, bridge to Core Data's NSPersistentCloudKitContainer.

// Basic approach: Share via a unique code/link
@Model
final class SharedProject {
    var name: String
    var shareCode: String? // Generate unique code for sharing
    var ownerID: String    // iCloud user record ID

    init(name: String, ownerID: String) {
        self.name = name
        self.ownerID = ownerID
    }
}
```

For full CloudKit sharing with CKShare records, consider using Core Data's `NSPersistentCloudKitContainer` alongside SwiftData, or build a custom sharing layer using CloudKit framework directly.
