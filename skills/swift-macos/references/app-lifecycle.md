# App Lifecycle & Scenes

## Table of Contents
- App Protocol & Entry Point
- WindowGroup
- Window (Single Instance)
- Settings Scene
- MenuBarExtra
- MenuBarExtra Gotchas
- DocumentGroup
- Window Management
- Scene Phases
- Async Termination Cleanup
- LSUIElement Operational Issues

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

## MenuBarExtra Gotchas

### .menu style strips SwiftUI font modifiers

With `.menuBarExtraStyle(.menu)`, content renders to native `NSMenu` items via `NSStatusBarButton`. All SwiftUI font modifiers (`.monospacedDigit()`, `.font(.system(.body, design: .monospaced))`) are silently ignored. Timer displays like "0:05" jump width as digits change.

Fix options:
1. **Fixed-width frame**: `.frame(width: 38)` on the timer text
2. **ImageRenderer trick** (used by AeroSpace app): render `Text` with proper font into a `CGImage`, display as `Image`. Font modifiers are baked into the rendered image, bypassing the bridge.

### TimelineView doesn't work in .menu style

`TimelineView(.periodic(from: .now, by: 1))` doesn't tick - `.menu` style renders to static `NSMenu` items. Use a `Timer` firing every second that updates an `@Observable` property instead:

```swift
@Observable
class AppState {
    var formattedElapsed = "0:00"
    private var timer: Timer?

    func startTimer() {
        timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            self?.formattedElapsed = self?.computeElapsed() ?? "0:00"
        }
    }
}
```

### onAppear never fires until menu is opened

With `.menuBarExtraStyle(.menu)`, the content view's `onAppear` only fires when the user clicks the menu bar icon. Never place initialization code (monitoring start, permission requests, delegate setup) in `onAppear`. Use `applicationDidFinishLaunching` instead.

### @NSApplicationDelegateAdaptor reference timing

`(NSApplication.shared.delegate as? AppDelegate)?.monitor = monitor` in `App.init()` may silently fail. Use the adaptor property directly:

```swift
@main
struct MyApp: App {
    @NSApplicationDelegateAdaptor private var delegate: AppDelegate

    init() {
        delegate.monitor = monitor // Works - uses adaptor property directly
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

### Restore behavior (macOS 15+)
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

### Presented window style

`presentedWindowStyle` is a `View` modifier that styles windows this view presents. The complete set of `WindowStyle` values in the macOS 26.5 SDK is `.automatic`, `.titleBar`, `.hiddenTitleBar`, and `.plain` - there is no `.fullScreen` member.

```swift
.presentedWindowStyle(.hiddenTitleBar) // .automatic, .titleBar, .plain
```

Full-screen is not a `WindowStyle`. Drive it from AppKit (`NSWindow.toggleFullScreen(_:)`) or let the user use the standard green-button behavior.

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

## Async Termination Cleanup

For apps that need async cleanup before quitting (finalizing file writers, stopping streams):

```swift
class AppDelegate: NSObject, NSApplicationDelegate {
    var monitor: AudioMonitor?
    private var hasReplied = false
    private var isTerminating = false

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        // A second quit during the window (menu pressed twice, Sparkle, logout)
        // re-enters here; resetting `hasReplied` would let both paths reply.
        guard !isTerminating else { return .terminateLater }
        isTerminating = true

        // Cleanup task
        Task { @MainActor in
            await monitor?.stopAndSave()
            guard !hasReplied else { return }
            hasReplied = true
            NSApplication.shared.reply(toApplicationShouldTerminate: true)
        }

        // Timeout task - bounds slow cleanup, but cannot run if the main queue is blocked (see below)
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(8))
            guard !hasReplied else { return }
            hasReplied = true
            NSApplication.shared.reply(toApplicationShouldTerminate: true)
        }

        return .terminateLater
    }
}
```

The `hasReplied` flag prevents double-reply (undefined behavior). Both Tasks are MainActor (serial), so the flag check is race-free. Use `movieFragmentInterval` on AVAssetWriter to bound data loss to ~10s even if timeout fires.

### Never call `terminate` from a main-queue block

`.terminateLater` spins a nested run loop until the reply arrives. The main dispatch queue is serial and never starts a block while another is running - and a `Task { @MainActor in }` job *is* a main-queue block. So if `terminate` is called from inside one (a `DispatchQueue.main.async` closure, a dispatch source on `.main`, a main-actor `Task`), both reply tasks above are starved: no reply, no timeout, and the app hangs until Force Quit. The compiler cannot see it. Menu Quit, Apple Events and Sparkle call `terminate` from run-loop event handling and are safe; anything else hops to the run loop first:

```swift
// Routing SIGTERM (killall, launchd) into the same cleanup. Its default action
// exits on the spot, before any writer is finalized.
signal(SIGTERM, SIG_IGN)
let source = DispatchSource.makeSignalSource(signal: SIGTERM, queue: .main)
source.setEventHandler {
    RunLoop.main.perform {
        MainActor.assumeIsolated { NSApplication.shared.terminate(nil) }
    }
}
source.resume()  // keep a strong reference, or the source is cancelled
```

### Prevent idle sleep during recording

```swift
var activity: NSObjectProtocol?
activity = ProcessInfo.processInfo.beginActivity(
    .userInitiated, reason: "Recording audio"
)
// ... later:
if let a = activity { ProcessInfo.processInfo.endActivity(a) }
```

## LSUIElement Operational Issues

### Windows open behind other apps

LSUIElement apps don't auto-activate. When opening windows from the menu:

```swift
Button("Show Settings") {
    openWindow(id: "settings")
    NSApplication.shared.activate(ignoringOtherApps: true)
}
```

### Cmd+, doesn't work

LSUIElement apps have no app menu bar, so `CommandGroup(replacing: .appSettings)` has nowhere to attach. Add `.keyboardShortcut(",", modifiers: .command)` to a button in the menu dropdown (only works when menu is open).

### Crash detection

When an LSUIElement menu bar app crashes, the icon silently disappears - no crash dialog. Use a watchdog helper binary that monitors the main process via `kqueue`/`kevent(EVFILT_PROC, NOTE_EXIT)` and shows an alert on crash signals (SIGTRAP, SIGABRT, SIGSEGV).

### Onboarding for LSUIElement apps

Host onboarding in a manually-created `NSWindow` (not a SwiftUI `Window` scene), since the window must appear before any user interaction:

```swift
func applicationDidFinishLaunching(_ notification: Notification) {
    guard !UserDefaults.standard.bool(forKey: "hasCompletedOnboarding") else { return }
    // Skip onboarding for existing users who already have permissions
    if CGPreflightScreenCaptureAccess() {
        UserDefaults.standard.set(true, forKey: "hasCompletedOnboarding")
        return
    }
    let window = NSWindow(contentRect: .init(x: 0, y: 0, width: 500, height: 400),
                          styleMask: [.titled, .closable], backing: .buffered, defer: false)
    window.isReleasedWhenClosed = false // Prevent dangling reference crash
    window.contentView = NSHostingView(rootView: OnboardingView(onComplete: { ... }))
    window.center()
    window.makeKeyAndOrderFront(nil)
    NSApp.activate(ignoringOtherApps: true)
}
```

Use `onComplete` callback instead of `@Environment(\.dismiss)` - dismiss has no backing in a manually-created NSWindow. Set `isReleasedWhenClosed = false` and nil the window reference before calling `close()` if you also use `NSWindowDelegate.windowWillClose`.

### Restarting the app

Don't use `NSWorkspace.OpenConfiguration(createsNewApplicationInstance: true)` - it spawns a duplicate before the first exits. Use `Process` + terminate:

```swift
func restartApp() {
    let path = Bundle.main.bundlePath
    Process.launchedProcess(launchPath: "/usr/bin/open", arguments: [path])
    NSApplication.shared.terminate(nil)
}
```

## Crash: high-frequency MenuBarExtra label updates

A per-second timer driving the `MenuBarExtra` label (an elapsed-time readout, a live meter) can crash intermittently with `EXC_BREAKPOINT` inside `-[NSWindow _postWindowNeedsUpdateConstraints]`. The `NSHostingView` backing the status item is pushed into an AppKit constraint-update exception by the repeated re-layout. It compiles, usually runs, and crashes in the field.

Keep the SwiftUI label static and push frequent text through AppKit directly:

```swift
// Static label - SwiftUI never re-lays-out on every tick
MenuBarExtra("Recorder", systemImage: "record.circle") { MenuBarView() }

// Update the status item's title from AppKit instead
statusItem.button?.attributedTitle = NSAttributedString(
    string: elapsed,
    attributes: [.font: NSFont.monospacedDigitSystemFont(ofSize: 13, weight: .regular)]
)
```

Monospaced digits stop the width from oscillating each tick, which is what drives the constraint churn. If you must render SwiftUI, pre-render with `ImageRenderer` and assign the resulting image, and lower the update frequency - a wall-clock readout rarely needs more than 1 Hz, and a meter can be throttled well below its sample rate.

## Crash visibility for menu-bar-only apps

When an `LSUIElement` app crashes, macOS suppresses the "quit unexpectedly" dialog. The icon simply disappears and the user keeps believing the app is running - the worst failure mode for anything doing background recording or monitoring. An in-app `NSSetUncaughtExceptionHandler` only logs, and a crash notice shown at next launch lands in a dropdown nobody opens.

Bundle a small helper that watches the main app's PID and reports unexpected exits:

```c
int fd = kqueue();
struct kevent change;
EV_SET(&change, targetPID, EVFILT_PROC, EV_ADD | EV_ENABLE, NOTE_EXIT, 0, NULL);
kevent(fd, &change, 1, NULL, 0, NULL);

struct kevent event;
kevent(fd, NULL, 0, &event, 1, NULL);   // blocks until the process exits
// Inspect exit status, then show a dialog if it was not a clean quit
```

Choose the hosting model deliberately:

| Model | Pros | Cons |
|---|---|---|
| Spawned by the app at launch | No system prompt, dies with the parent, nothing in System Settings | Cannot catch very early startup crashes |
| `SMAppService` login item in `Contents/Library/LoginItems/` | Survives reboot, catches startup crashes | Triggers a one-time "Background Items Added" notification, and the user can silently disable it in System Settings |

The spawned helper is the lighter default. Reach for the registered login item only if crashes during startup are the ones you actually need to see.
