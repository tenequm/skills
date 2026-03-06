# App Lifecycle & Scenes

## Table of Contents
- App Protocol & Entry Point
- WindowGroup
- Window (Single Instance)
- Settings Scene
- MenuBarExtra
- DocumentGroup
- Window Management
- Scene Phases

## App Protocol & Entry Point

```swift
@main
struct MyApp: App {
    // App-level state
    @State private var appState = AppState()

    // App delegate for system events
    @NSApplicationDelegateAdaptor private var delegate: AppDelegate

    var body: some Scene {
        WindowGroup("Projects", id: "projects") {
            ContentView()
                .environment(appState)
        }
        .defaultSize(width: 1000, height: 700)
        .defaultPosition(.center)
        .keyboardShortcut("1", modifiers: .command)

        Window("Activity", id: "activity") {
            ActivityView()
        }
        .defaultSize(width: 400, height: 600)
        .windowResizability(.contentMinSize)

        Settings {
            SettingsView()
                .environment(appState)
        }

        MenuBarExtra("MyApp", systemImage: "app.fill") {
            MenuBarContentView()
        }
        .menuBarExtraStyle(.window)
    }
}
```

## WindowGroup

Creates standard resizable windows. Multiple instances allowed by default:

```swift
// Basic
WindowGroup {
    ContentView()
}

// With identifier for programmatic opening
WindowGroup("Editor", id: "editor") {
    EditorView()
}

// With data binding - open window for specific item
WindowGroup("Detail", id: "detail", for: Item.ID.self) { $itemID in
    if let itemID {
        DetailView(itemID: itemID)
    }
}

// Open programmatically
@Environment(\.openWindow) private var openWindow

Button("Open Editor") {
    openWindow(id: "editor")
}

Button("Show Detail") {
    openWindow(value: selectedItem.id)
}
```

Window modifiers:
```swift
WindowGroup {
    ContentView()
}
.defaultSize(width: 800, height: 600)
.defaultSize(CGSize(width: 800, height: 600))
.defaultPosition(.center)          // .leading, .trailing, .topLeading, etc.
.windowResizability(.automatic)     // .contentSize, .contentMinSize
.windowStyle(.automatic)            // .hiddenTitleBar, .titleBar
.windowToolbarStyle(.unified)       // .unifiedCompact, .expanded, .automatic
.keyboardShortcut("n", modifiers: .command)
```

## Window (Single Instance)

For utility/auxiliary windows that should have only one instance:

```swift
Window("Inspector", id: "inspector") {
    InspectorView()
}
.defaultSize(width: 300, height: 500)
.windowResizability(.contentSize)
.commandsRemoved()  // Remove default window commands
```

Dismiss from within:
```swift
@Environment(\.dismissWindow) private var dismissWindow

Button("Close") {
    dismissWindow(id: "inspector")
}
```

## Settings Scene

Preferences window accessible via Cmd+,:

```swift
Settings {
    TabView {
        GeneralSettingsView()
            .tabItem { Label("General", systemImage: "gear") }
        AppearanceSettingsView()
            .tabItem { Label("Appearance", systemImage: "paintpalette") }
        AdvancedSettingsView()
            .tabItem { Label("Advanced", systemImage: "wrench") }
    }
    .frame(width: 450)
}
```

Use `@AppStorage` for UserDefaults-backed preferences:
```swift
struct GeneralSettingsView: View {
    @AppStorage("autoSave") private var autoSave = true
    @AppStorage("fontSize") private var fontSize = 14.0
    @AppStorage("theme") private var theme = "system"

    var body: some View {
        Form {
            Toggle("Auto-save documents", isOn: $autoSave)
            Slider(value: $fontSize, in: 10...24, step: 1) {
                Text("Font Size: \(Int(fontSize))pt")
            }
            Picker("Theme", selection: $theme) {
                Text("System").tag("system")
                Text("Light").tag("light")
                Text("Dark").tag("dark")
            }
        }
        .formStyle(.grouped)
        .padding()
    }
}
```

## MenuBarExtra

Two styles - menu or window:

```swift
// Menu style (dropdown menu)
MenuBarExtra("Status", systemImage: "circle.fill") {
    Button("Show Dashboard") { openWindow(id: "dashboard") }
    Divider()
    Toggle("Monitoring", isOn: $isMonitoring)
    Divider()
    Button("Quit") { NSApplication.shared.terminate(nil) }
}
.menuBarExtraStyle(.menu)

// Window style (popover window)
MenuBarExtra("Status", systemImage: "circle.fill") {
    VStack {
        Text("System Status")
            .font(.headline)
        StatusDashboard()
    }
    .frame(width: 300, height: 400)
}
.menuBarExtraStyle(.window)
```

Dynamic icon:
```swift
MenuBarExtra {
    MenuBarContent()
} label: {
    Image(systemName: isConnected ? "wifi" : "wifi.slash")
    if showBadge {
        Text("\(unreadCount)")
    }
}
```

## DocumentGroup

For document-based apps:

```swift
@main
struct TextEditorApp: App {
    var body: some Scene {
        DocumentGroup(newDocument: TextDocument()) { file in
            TextEditorView(document: file.$document)
        }
    }
}

// Document type
struct TextDocument: FileDocument {
    static var readableContentTypes: [UTType] { [.plainText] }

    var text: String

    init(text: String = "") {
        self.text = text
    }

    init(configuration: ReadConfiguration) throws {
        guard let data = configuration.file.regularFileContents,
              let text = String(data: data, encoding: .utf8)
        else { throw CocoaError(.fileReadCorruptFile) }
        self.text = text
    }

    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper {
        let data = text.data(using: .utf8)!
        return FileWrapper(regularFileWithContents: data)
    }
}
```

For `ReferenceFileDocument` (class-based, supports undo):
```swift
class RichDocument: ReferenceFileDocument {
    static var readableContentTypes: [UTType] { [.rtf] }

    @Published var content: AttributedString

    required init(configuration: ReadConfiguration) throws { /* ... */ }

    func snapshot(contentType: UTType) throws -> Data { /* ... */ }

    func fileWrapper(snapshot: Data, configuration: WriteConfiguration) throws -> FileWrapper {
        FileWrapper(regularFileWithContents: snapshot)
    }
}
```

## Window Management

### Restore behavior (macOS 26)
```swift
WindowGroup {
    ContentView()
}
.restorationBehavior(.enabled) // .disabled, .enabled
```

### Window level
```swift
.windowLevel(.floating) // Keep window above others
```

### Full-screen support
```swift
.presentedWindowStyle(.automatic) // .fullScreen
```

## Scene Phases

React to app lifecycle:
```swift
@Environment(\.scenePhase) private var scenePhase

var body: some View {
    ContentView()
        .onChange(of: scenePhase) { oldPhase, newPhase in
            switch newPhase {
            case .active:
                // App is active and visible
                refreshData()
            case .inactive:
                // App is visible but not interactive
                break
            case .background:
                // App is in background
                saveState()
            @unknown default:
                break
            }
        }
}
```

## NSApplicationDelegateAdaptor

Bridge to AppKit delegate for system events:

```swift
class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        // Register URL scheme handlers, set up global state
    }

    func applicationWillTerminate(_ notification: Notification) {
        // Cleanup
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        false // Keep menu bar app alive
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        // Handle URL scheme
    }
}
```
