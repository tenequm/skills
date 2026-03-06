# System Integration

## Table of Contents
- Keyboard Shortcuts
- Drag & Drop
- File System Access
- UserDefaults & AppStorage
- App Intents
- Notifications
- Process Observation
- Login Items (SMAppService)
- LSUIElement & Background Apps

## Keyboard Shortcuts

### In commands
```swift
.commands {
    CommandMenu("Edit") {
        Button("Find...") { showFind = true }
            .keyboardShortcut("f", modifiers: .command)
        Button("Replace...") { showReplace = true }
            .keyboardShortcut("h", modifiers: [.command, .option])
    }
}
```

### On buttons
```swift
Button("Save") { save() }
    .keyboardShortcut("s", modifiers: .command)

Button("Delete") { delete() }
    .keyboardShortcut(.delete, modifiers: .command)

Button("Cancel") { cancel() }
    .keyboardShortcut(.cancelAction) // Esc

Button("OK") { confirm() }
    .keyboardShortcut(.defaultAction) // Return
```

### Global key handlers
```swift
.onKeyPress(.return) {
    submitForm()
    return .handled
}

.onKeyPress(characters: .alphanumerics) { press in
    handleTyping(press.characters)
    return .handled
}

.onKeyPress(phases: .down) { press in
    if press.key == .space {
        startPreview()
        return .handled
    }
    return .ignored
}
```

## Drag & Drop

### Draggable
```swift
struct ItemCard: View {
    let item: Item

    var body: some View {
        VStack { /* content */ }
            .draggable(item) // Item must conform to Transferable
    }
}

// Transferable conformance
extension Item: Transferable {
    static var transferRepresentation: some TransferRepresentation {
        CodableRepresentation(for: Item.self, contentType: .json)
        ProxyRepresentation(exporting: \.name) // fallback to string
    }
}
```

### Drop target
```swift
.dropDestination(for: Item.self) { items, location in
    // Handle dropped items
    collection.append(contentsOf: items)
    return true
}

// File drops
.dropDestination(for: URL.self) { urls, location in
    importFiles(urls)
    return true
}
```

### Drag preview
```swift
.draggable(item) {
    // Custom preview
    Label(item.name, systemImage: "doc")
        .padding(8)
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 8))
}
```

### Spring-loaded destination
```swift
.springLoadedDestination(for: Item.self) { items in
    // Auto-open folder/collection when hovering with drag
    navigateToCollection(items)
}
```

## File System Access

### Security-scoped bookmarks (for sandboxed apps)
```swift
func saveBookmark(for url: URL) throws {
    let bookmarkData = try url.bookmarkData(
        options: .withSecurityScope,
        includingResourceValuesForKeys: nil,
        relativeTo: nil
    )
    UserDefaults.standard.set(bookmarkData, forKey: "savedBookmark")
}

func resolveBookmark() throws -> URL {
    let data = UserDefaults.standard.data(forKey: "savedBookmark")!
    var isStale = false
    let url = try URL(
        resolvingBookmarkData: data,
        options: .withSecurityScope,
        relativeTo: nil,
        bookmarkDataIsStale: &isStale
    )

    guard url.startAccessingSecurityScopedResource() else {
        throw FileError.accessDenied
    }
    // Remember to call url.stopAccessingSecurityScopedResource() when done

    return url
}
```

### FileManager
```swift
// App support directory
let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
let appDir = appSupport.appendingPathComponent(Bundle.main.bundleIdentifier!)

// Create directory
try FileManager.default.createDirectory(at: appDir, withIntermediateDirectories: true)

// Temporary directory
let tempDir = FileManager.default.temporaryDirectory
```

## App Intents

Expose actions to Shortcuts and Siri:

```swift
import AppIntents

struct CreateProjectIntent: AppIntent {
    static var title: LocalizedStringResource = "Create Project"
    static var description: IntentDescription = "Creates a new project"

    @Parameter(title: "Name")
    var name: String

    @Parameter(title: "Template", default: .blank)
    var template: ProjectTemplate

    func perform() async throws -> some IntentResult & ReturnsValue<String> {
        let project = try await ProjectService.create(name: name, template: template)
        return .result(value: project.id.uuidString)
    }
}

// Register with app
struct MyAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: CreateProjectIntent(),
            phrases: ["Create a project in \(.applicationName)"],
            shortTitle: "Create Project",
            systemImageName: "folder.badge.plus"
        )
    }
}
```

## Notifications (System)

### User Notifications
```swift
import UserNotifications

func requestPermission() async throws -> Bool {
    try await UNUserNotificationCenter.current()
        .requestAuthorization(options: [.alert, .sound, .badge])
}

func scheduleNotification(title: String, body: String) {
    let content = UNMutableNotificationContent()
    content.title = title
    content.body = body
    content.sound = .default

    let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 5, repeats: false)
    let request = UNNotificationRequest(identifier: UUID().uuidString,
                                         content: content, trigger: trigger)

    UNUserNotificationCenter.current().add(request)
}
```

## UserDefaults & AppStorage

```swift
// @AppStorage in views
@AppStorage("selectedTheme") private var theme = "system"

// UserDefaults directly
extension UserDefaults {
    var lastSyncDate: Date? {
        get { object(forKey: "lastSyncDate") as? Date }
        set { set(newValue, forKey: "lastSyncDate") }
    }
}

// App group (for sharing between app and extensions)
let sharedDefaults = UserDefaults(suiteName: "group.com.myapp")
@AppStorage("shared_key", store: UserDefaults(suiteName: "group.com.myapp"))
private var sharedValue = ""
```

## Process Observation

### Currently running apps

```swift
import AppKit

let runningApps = NSWorkspace.shared.runningApplications
let isTargetRunning = runningApps.contains { $0.bundleIdentifier == "com.example.target" }

// NSRunningApplication properties
app.localizedName       // String?
app.bundleIdentifier    // String?
app.processIdentifier   // pid_t (Int32)
app.isActive            // Bool (frontmost)
app.isTerminated        // Bool
app.launchDate          // Date?
app.icon                // NSImage?
app.activationPolicy    // .regular, .accessory, .prohibited
```

### Notification-based observation

Use `NSWorkspace.shared.notificationCenter` (NOT `NotificationCenter.default`):

```swift
// App launched
NSWorkspace.shared.notificationCenter.addObserver(
    forName: NSWorkspace.didLaunchApplicationNotification,
    object: nil, queue: .main
) { notification in
    if let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey]
        as? NSRunningApplication {
        print("Launched: \(app.localizedName ?? "?") (\(app.bundleIdentifier ?? "?")")
    }
}

// App terminated
NSWorkspace.shared.notificationCenter.addObserver(
    forName: NSWorkspace.didTerminateApplicationNotification,
    object: nil, queue: .main
) { notification in
    if let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey]
        as? NSRunningApplication {
        print("Terminated: \(app.localizedName ?? "?")")
    }
}
```

All workspace notifications:

| Notification | Fires when |
|-------------|------------|
| `didLaunchApplicationNotification` | App starts (not background/LSUIElement apps) |
| `didTerminateApplicationNotification` | App terminates (not background/LSUIElement apps) |
| `didActivateApplicationNotification` | App becomes frontmost |
| `didDeactivateApplicationNotification` | App loses frontmost |
| `didHideApplicationNotification` | App hidden |
| `didUnhideApplicationNotification` | App unhidden |

### KVO for ALL apps (including background/LSUIElement)

`didLaunchApplicationNotification` does NOT fire for background or LSUIElement apps. Use KVO instead:

```swift
class AppMonitor: NSObject {
    private var observation: NSKeyValueObservation?

    func startObserving() {
        observation = NSWorkspace.shared.observe(
            \.runningApplications, options: [.new, .old]
        ) { workspace, change in
            let oldPIDs = Set(change.oldValue?.map(\.processIdentifier) ?? [])
            let newPIDs = Set(change.newValue?.map(\.processIdentifier) ?? [])

            let launched = newPIDs.subtracting(oldPIDs)
            for app in workspace.runningApplications where launched.contains(app.processIdentifier) {
                print("Launched: \(app.localizedName ?? "?")")
            }
        }
    }

    func stopObserving() {
        observation?.invalidate()
        observation = nil
    }
}
```

### Background monitoring pattern

Combine notifications + KVO + optional safety-net poll:

```swift
@Observable
class ProcessMonitor {
    var watchedBundleIDs: Set<String> = []
    private(set) var activeWatchedApps: [NSRunningApplication] = []

    private var tokens: [NSObjectProtocol] = []
    private var kvoObservation: NSKeyValueObservation?

    func startMonitoring() {
        refreshActiveApps()

        // Notifications for regular apps
        tokens.append(NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didLaunchApplicationNotification,
            object: nil, queue: .main
        ) { [weak self] _ in self?.refreshActiveApps() })

        tokens.append(NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didTerminateApplicationNotification,
            object: nil, queue: .main
        ) { [weak self] _ in self?.refreshActiveApps() })

        // KVO for background/LSUIElement apps
        kvoObservation = NSWorkspace.shared.observe(\.runningApplications, options: [.new]) {
            [weak self] _, _ in
            DispatchQueue.main.async { self?.refreshActiveApps() }
        }
    }

    func stopMonitoring() {
        tokens.forEach { NSWorkspace.shared.notificationCenter.removeObserver($0) }
        tokens.removeAll()
        kvoObservation?.invalidate()
    }

    private func refreshActiveApps() {
        activeWatchedApps = NSWorkspace.shared.runningApplications.filter {
            guard let id = $0.bundleIdentifier else { return false }
            return watchedBundleIDs.contains(id)
        }
    }
}
```

## Login Items (SMAppService)

macOS 13+ API for registering login items, agents, and daemons.

### Register main app as login item

```swift
import ServiceManagement

// Register (launches on subsequent logins)
try SMAppService.mainApp.register()

// Unregister
try SMAppService.mainApp.unregister()

// Check status
switch SMAppService.mainApp.status {
case .notRegistered: print("Not registered")
case .enabled:       print("Enabled")
case .requiresApproval:
    SMAppService.openSystemSettingsLoginItems()
case .notFound:      print("Service not found")
@unknown default:    break
}
```

### SwiftUI Settings toggle

Never persist login-item state locally - always read from `SMAppService.mainApp.status`:

```swift
import ServiceManagement
import SwiftUI

struct LaunchAtLoginToggle: View {
    @State private var launchAtLogin = false
    @Environment(\.appearsActive) var appearsActive

    var body: some View {
        Toggle("Launch at login", isOn: $launchAtLogin)
            .onChange(of: launchAtLogin) { _, newValue in
                if newValue {
                    try? SMAppService.mainApp.register()
                } else {
                    try? SMAppService.mainApp.unregister()
                }
            }
            .onAppear {
                launchAtLogin = (SMAppService.mainApp.status == .enabled)
            }
            .onChange(of: appearsActive) { _, active in
                guard active else { return }
                // Re-sync: user may have toggled in System Settings
                launchAtLogin = (SMAppService.mainApp.status == .enabled)
            }
    }
}
```

### Service types

```swift
// Main app login item
SMAppService.mainApp

// Helper app (in Contents/Library/LoginItems/)
SMAppService.loginItem(identifier: "com.example.helper")

// LaunchAgent (in Contents/Library/LaunchAgents/)
SMAppService.agent(plistName: "com.example.agent.plist")

// LaunchDaemon (in Contents/Library/LaunchDaemons/ - requires admin approval)
SMAppService.daemon(plistName: "com.example.daemon.plist")
```

| Type | Runs as | Starts | Can show UI | Approval |
|------|---------|--------|-------------|----------|
| mainApp | Current user | Next login | Yes | Background item notification |
| loginItem | Current user | Immediately + login | Yes | Background item notification |
| agent | Current user | Immediately + login | If not LSBackgroundOnly | Background item notification |
| daemon | root | After admin approval | No | Admin authentication |

### Bundle structure for agents/daemons

```
MyApp.app/Contents/
    Library/
        LoginItems/MyHelper.app/       # loginItem bundles
        LaunchAgents/com.example.agent.plist
        LaunchDaemons/com.example.daemon.plist
    Resources/MyHelper                 # helper executable
```

Agent plist uses `BundleProgram` (path relative to app bundle):

```xml
<dict>
    <key>Label</key>
    <string>com.example.agent</string>
    <key>BundleProgram</key>
    <string>Contents/Resources/MyHelper</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
```

## LSUIElement & Background Apps

### LSUIElement (menu-bar-only apps)

Set in Info.plist (`Application is agent (UIElement)`):

```xml
<key>LSUIElement</key>
<true/>
```

App does NOT appear in Dock or Cmd+Tab. CAN still show UI (windows, menus, popovers). **This is what menu-bar-only apps use.**

### LSBackgroundOnly (faceless helpers)

```xml
<key>LSBackgroundOnly</key>
<true/>
```

App runs ONLY in background. Cannot show any UI.

| Key | Dock Icon | Can Show UI | Use Case |
|-----|-----------|-------------|----------|
| Neither | Yes | Yes | Normal app |
| `LSUIElement` | No | Yes | Menu bar apps |
| `LSBackgroundOnly` | No | No | Faceless helpers |

### Menu-bar-only app pattern

```swift
@main
struct MyMenuBarApp: App {
    var body: some Scene {
        MenuBarExtra("Status", systemImage: "star") {
            VStack {
                ContentView()
                Divider()
                Button("Quit") { NSApp.terminate(nil) }
            }
            .frame(width: 300, height: 200)
        }
        .menuBarExtraStyle(.window)
    }
}
```

With `LSUIElement = true`: no Dock icon, no Cmd+Tab entry, no Force Quit listing. **Always include a Quit button** since users can't right-click the Dock icon.

### Caveat

`NSWorkspace.didLaunchApplicationNotification` does NOT fire for LSUIElement or background apps. Use KVO on `runningApplications` to detect them (see Process Observation section).
