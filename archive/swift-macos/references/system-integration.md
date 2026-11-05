# System Integration

## Table of Contents
- Keyboard Shortcuts
- Drag & Drop
- File System Access
- UserDefaults & AppStorage
- App Intents
- Widgets & Control Center
- Notifications
- Process Observation
- Accessibility API (AXUIElement)
- CoreAudio Per-Process APIs
- Login Items (SMAppService)
- XPC (XPCSession / XPCListener)
- LSUIElement & Background Apps
- Idle Sleep Prevention
- Logging & Diagnostics
- Privacy usage descriptions

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

### Beyond primitives: entities

An `AppIntent` whose parameters are only `String`/`Int` can never reference your app's actual data. `AppEntity` is the type system that fixes that - "an interface for making a custom type or app-specific concept discoverable by Apple Intelligence and experiences like Siri or the Shortcuts app" (macOS 13+). The three pieces:

| Type | Role |
|---|---|
| `AppEntity` | A model object addressable from Shortcuts/Siri - has an `id`, a `displayRepresentation`, and a query |
| `EntityQuery` | How the system finds entities: by id, by string match, or by suggestion |
| `AppEnum` | A fixed set of choices surfaced as a picker (what `ProjectTemplate` above should be) |

### Spotlight indexing

Conform an entity to `IndexedEntity` to put your app's records in Spotlight:

> Make app entities available in Spotlight that conform to `IndexedEntity` and use the `@ComputedProperty(indexingKey:)` or `@Property(indexingKey:)` Swift macros for attributes you want to add to the Spotlight index.

### Interactive snippets (macOS 26)

`SnippetIntent` renders an interactive SwiftUI snippet as the intent's result rather than a plain value. One trap Apple calls out explicitly:

> If an app intent conforms to `SnippetIntent` and only returns a snippet ... it's nondiscoverable by the Shortcuts app and in Spotlight. To make such an intent discoverable, explicitly set `isDiscoverable` to `true`.

### Foreground continuation: use `supportedModes`

`ForegroundContinuableIntent` is **deprecated at macOS 26.0**. Apple's replacement note: "Please include `.foreground(.dynamic)` in the `supportedModes` of your app intent instead." Declare `supportedModes` (`IntentModes`) on the intent rather than conforming to the old protocol.

### macOS-only onscreen-content bridges

The `UI*` data sources in Apple's App Intents documentation are iOS-only. The Mac equivalents are `NSTableViewAppIntentsDataSource` and `NSCollectionViewAppIntentsDataSource` (macOS 15.4+) - "the methods that an object adopts to make items in a table view or outline view discoverable by Apple Intelligence and Siri." Adopt them so Siri can act on the row a user is looking at.

## Widgets & Control Center

WidgetKit is macOS 11+ and covers desktop and Notification Center widgets. Two macOS-specific points the MenuBarExtra crowd usually wants:

**Control Center controls reached macOS in 26.0.** Previously watchOS/iOS only:

> Create controls that use `ControlWidgetButton` to execute an action and `ControlWidgetToggle` to toggle some state in your app in watchOS **and macOS**.

The building blocks are `ControlWidget` (a SwiftUI widget kind), `ControlWidgetButton`, `ControlWidgetToggle`, and `ControlConfigurationIntent` for a configurable control. A control is often a better fit than a `MenuBarExtra` for a single toggle - it costs no menu-bar real estate and the system handles placement.

**Liquid Glass rendering.** Use `WidgetAccentedRenderingMode` to control how widget images are treated under the macOS 26 rendering modes; `WidgetPushHandler` drives push-based timeline reloads.

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

## Accessibility API (AXUIElement)

`NSWorkspace` and KVO tell you *which* apps are running. `AXUIElement` - "a structure used to refer to an accessibility object" - is how a Mac utility reads and drives *another app's* UI: window titles, focused element, text selection, button presses. It is the foundation of window managers, launchers, text-expansion tools, and automation utilities.

Practical constraints that decide whether a feature is even viable:

- Requires the **Accessibility** TCC permission (System Settings > Privacy & Security > Accessibility), granted per app by the user. Check with `AXIsProcessTrusted()`; prompt with `AXIsProcessTrustedWithOptions` passing `kAXTrustedCheckOptionPrompt`.
- Like screen recording, the grant keys off the app's code signature, so re-signing forces a re-grant (see the TCC notes in `distribution.md`).
- It is a C API (`ApplicationServices`) with `AXUIElementCopyAttributeValue` returning `CFTypeRef` - the same Create-Rule bridging care as the CoreAudio CFString trap in `core-audio-tap.md` applies.
- **Not available under the App Sandbox.** An accessibility-driven feature is Developer ID-only.

Docs: <https://developer.apple.com/documentation/applicationservices/axuielement>

## CoreAudio Per-Process APIs

macOS 14.2+ provides per-process audio state APIs for detecting which apps are using audio I/O. Useful for call detection, audio monitoring, or building audio routing tools.

```swift
import CoreAudio

/// Find all processes with active audio input AND output (e.g., call apps)
func findActiveCallingProcesses() -> [(pid: pid_t, bundleID: String)] {
    var addr = AudioObjectPropertyAddress(
        mSelector: kAudioHardwarePropertyProcessObjectList,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain
    )

    var size: UInt32 = 0
    guard AudioObjectGetPropertyDataSize(
        AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size
    ) == noErr else { return [] }

    let count = Int(size) / MemoryLayout<AudioObjectID>.size
    var objectIDs = [AudioObjectID](repeating: 0, count: count)
    guard AudioObjectGetPropertyData(
        AudioObjectID(kAudioObjectSystemObject), &addr, 0, nil, &size, &objectIDs
    ) == noErr else { return [] }

    let myPID = ProcessInfo.processInfo.processIdentifier
    var results: [(pid_t, String)] = []

    for objID in objectIDs {
        // Get PID
        var pidAddr = AudioObjectPropertyAddress(
            mSelector: kAudioProcessPropertyPID,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
        var pid: pid_t = 0
        var pidSize = UInt32(MemoryLayout<pid_t>.size)
        guard AudioObjectGetPropertyData(objID, &pidAddr, 0, nil, &pidSize, &pid) == noErr,
              pid != myPID else { continue }

        // Check IsRunningInput AND IsRunningOutput (dual check filters dictation/Siri)
        var inputAddr = AudioObjectPropertyAddress(
            mSelector: kAudioProcessPropertyIsRunningInput,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
        var isInput: UInt32 = 0
        var boolSize = UInt32(MemoryLayout<UInt32>.size)
        guard AudioObjectGetPropertyData(objID, &inputAddr, 0, nil, &boolSize, &isInput) == noErr,
              isInput != 0 else { continue }

        var outputAddr = inputAddr
        outputAddr.mSelector = kAudioProcessPropertyIsRunningOutput
        var isOutput: UInt32 = 0
        guard AudioObjectGetPropertyData(objID, &outputAddr, 0, nil, &boolSize, &isOutput) == noErr,
              isOutput != 0 else { continue }

        // Get bundle ID
        if let bundleID = getBundleID(for: objID) {
            results.append((pid, bundleID))
        }
    }
    return results
}
```

Key gotchas:
- **Filter out own PID** and ScreenCaptureKit helper PIDs (`com.apple.screencapturekit*`, `com.apple.replayd`).
- **Input+Output dual check** filters out dictation, Siri, voice memos (input only). Real call apps (Zoom, Meet, Teams) have both active.
- **`AudioBufferList` is a variable-length C struct**. `UnsafeMutablePointer<AudioBufferList>.allocate(capacity: 1)` only reserves space for one buffer. Multi-channel devices cause heap overflow. Allocate exact `bufSize` bytes from `GetPropertyDataSize`.
- **Chrome reports helper subprocess bundle IDs** (e.g., `com.google.Chrome.helper.renderer`). Strip `.helper*` suffix to resolve to the parent app.
- **Polling (3s interval) is simpler than listeners**. CoreAudio property listeners require `Unmanaged.passUnretained(self)` pointer dance, complex deinit cleanup, and are unreliable with some browser audio pipelines. For call detection, 0-3s delay is negligible.
- **`CoreAudio.RemovePropertyListenerBlock`** has a known Swift bug where block-copied closures get different addresses, causing removal to fail. Use the C function pointer variant instead.

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

## XPC (XPCSession / XPCListener)

`SMAppService` registers a LaunchAgent or LaunchDaemon; it does not give you a way to **talk** to it. That is XPC. Since macOS 14 there is a Swift-native API - `XPCSession` ("a type that sends messages to a server process") on the app side, `XPCListener` ("a type that performs tasks for clients across process boundaries") in the helper - so a privileged helper no longer requires the Objective-C `NSXPCConnection` dance.

```swift
import XPC

// Client: talk to the registered helper
let session = try XPCSession(machService: "com.example.MyHelper")
let reply = try session.sendSync(MyRequest(command: .status))

// Helper: serve
let listener = try XPCListener(service: "com.example.MyHelper") { request in
    request.accept { (message: MyRequest) -> MyResponse in
        handle(message)
    }
}
```

Messages are `Codable`. The Mach service name must match the `MachServices` key in the helper's launchd plist, and the two binaries must share a team identifier for the connection to be accepted - verify the peer's code signing requirement rather than trusting the connection.

Docs: <https://developer.apple.com/documentation/xpc/xpcsession>

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

## Idle Sleep Prevention

Prevent macOS from sleeping during long operations (recording, encoding, uploads):

```swift
// Start activity (prevents idle sleep)
let activity = ProcessInfo.processInfo.beginActivity(
    .userInitiated, reason: "Recording audio"
)

// ... long-running operation ...

// End activity (allow sleep again)
ProcessInfo.processInfo.endActivity(activity)
```

Use `.userInitiated` for operations the user started. The system will not idle-sleep while the activity is active, but the user can still manually put the machine to sleep.

## Trap: "is the mic in use?" latches on with a system-wide property

`kAudioDevicePropertyDeviceIsRunningSomewhere` on the default input device looks like the way to auto-trigger recording when another app starts using the microphone. It is not: the property is system-wide and includes **your** process. Once your app opens the mic in response to the trigger, the property stays `true` after the other app stops, so the trigger never releases and auto-stop never fires.

Use the per-process CoreAudio APIs (macOS 14.2+) and exclude yourself:

```swift
import CoreAudio

func otherProcessIsUsingInput() -> Bool {
    var address = AudioObjectPropertyAddress(
        mSelector: kAudioHardwarePropertyProcessObjectList,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain
    )
    var size: UInt32 = 0
    guard AudioObjectGetPropertyDataSize(
        AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &size) == noErr else { return false }

    var processes = [AudioObjectID](repeating: 0, count: Int(size) / MemoryLayout<AudioObjectID>.size)
    guard AudioObjectGetPropertyData(
        AudioObjectID(kAudioObjectSystemObject), &address, 0, nil, &size, &processes) == noErr else { return false }

    let myPID = ProcessInfo.processInfo.processIdentifier
    for process in processes {
        guard pid(for: process) != myPID else { continue }
        if isRunningInput(process) { return true }   // kAudioProcessPropertyIsRunningInput
    }
    return false
}
```

Two caveats before designing around this:

- **App Sandbox**: these low-level per-process APIs are not reliably available under sandboxing, which makes a mic-activity auto-trigger a Mac App Store blocker. Plan the feature as Developer ID-only, or provide a manual path.
- Poll on a timer or install a property listener on the process list; there is no single "someone started using the mic" notification.

## Logging & Diagnostics

`print` does not survive shipping. The unified logging system is the standard instrument for a Mac app: `os.Logger` is "an object for writing interpolated string messages to the unified logging system" (macOS 11+), and it is what `log stream` / `log show` and Console.app read.

```swift
import os

private let log = Logger(subsystem: "com.example.MyApp", category: "capture")

log.debug("frame \(index, privacy: .public) queued")
log.error("stream stopped: \(error.localizedDescription, privacy: .public)")
```

Points that matter in practice:

- **Interpolated values default to `.private`** and render as `<private>` when read back from another process. Mark non-sensitive diagnostic values `.public` explicitly or your shipped logs are useless. Do the opposite for anything user-derived.
- **Levels have different persistence.** `.debug` is memory-only and discarded aggressively; `.info` persists only when collected; `.notice` (the default), `.error`, and `.fault` go to the on-disk store. Ship at `.notice` and above for anything you want to see in a user's sysdiagnose.
- **Read logs for a menu-bar-only app** - which has no console output anywhere - with `log stream --predicate 'subsystem == "com.example.MyApp"' --level debug`.

For performance work, `OSSignposter` brackets intervals that show up as regions in Instruments:

```swift
let signposter = OSSignposter(subsystem: "com.example.MyApp", category: "render")
let state = signposter.beginInterval("compose")
defer { signposter.endInterval("compose", state) }
```

Docs: <https://developer.apple.com/documentation/os/logger>

## Privacy usage descriptions

The capture-heavy parts of this skill cover screen recording and microphone TCC in depth. One easily missed sibling:

- **`NSLocalNetworkUsageDescription`** - "a message that tells people why the app is requesting access to the local network" (macOS 11+). Required for **any** Bonjour/mDNS discovery or local-subnet traffic. Without it the app is denied local network access, and the failure looks like a networking bug: discovery returns nothing, connections to `.local` names time out. Apps that stream to a local device, discover a companion app, or run a local server for a helper all need it, alongside `NSBonjourServices` listing the service types you browse.

Docs: <https://developer.apple.com/documentation/bundleresources/information-property-list/nslocalnetworkusagedescription>
