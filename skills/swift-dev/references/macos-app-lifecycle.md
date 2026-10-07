# macOS App Lifecycle and Scenes

Scenes, windows, Settings, MenuBarExtra, document apps (including the macOS 27 `Document` protocols), app delegate and termination, and menu-bar-only (`LSUIElement`) apps.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every Swift block typechecked with `swiftc -typecheck -swift-version 6` against the macOS 27.0 SDK (target macOS 15, or macOS 27 for the `Document` blocks), both with and without `-default-isolation MainActor`; the C watchdog block passed `clang -fsyntax-only`; API names checked in `SwiftUI.swiftinterface` and AppKit headers; behavior changes checked against the macOS 27 and Xcode 27 release notes.

## Contents
- Scenes and the App entry point
- Opening, closing and configuring windows
- Settings
- MenuBarExtra and its gotchas
- Document apps (`Document`, `ReadableDocument`, `WritableDocument`)
- App delegate and async termination
- Menu-bar-only apps (`LSUIElement`)

## Scenes and the App entry point

| Scene | Use |
|---|---|
| `WindowGroup` | Main resizable windows, multiple instances; `for: T.self` makes one window per value |
| `Window` | Single-instance auxiliary window |
| `UtilityWindow` (macOS 15+) | Floating tool palette / inspector panel without dropping to `NSPanel` |
| `Settings` | Preferences window, wired to Cmd+, |
| `MenuBarExtra` | Status item, `.menu` or `.window` style |
| `DocumentGroup` | Document-based apps |

```swift
@main
struct MyApp: App {
    @State private var appState = AppState()
    @NSApplicationDelegateAdaptor private var delegate: AppDelegate

    var body: some Scene {
        WindowGroup("Projects", id: "projects") {
            ContentView().environment(appState)
        }
        .defaultSize(width: 1000, height: 700)
        .defaultPosition(.center)
        .windowToolbarStyle(.unified)

        // One window per value; openWindow(value:) focuses the existing one if already open
        WindowGroup("Detail", id: "detail", for: Item.ID.self) { $itemID in
            if let itemID { DetailView(itemID: itemID) }
        }

        Window("Activity", id: "activity") { ActivityView() }
            .windowResizability(.contentMinSize)
            .restorationBehavior(.disabled)
            .defaultLaunchBehavior(.suppressed)

        UtilityWindow("Inspector", id: "inspector") { InspectorPanel() }

        Settings { SettingsView().environment(appState) }

        MenuBarExtra("MyApp", systemImage: "app.fill") { MenuBarContentView() }
            .menuBarExtraStyle(.window)
    }
}
```

The value type of a data-driven `WindowGroup` must be `Codable & Hashable` - SwiftUI persists it for state restoration.

## Opening, closing and configuring windows

```swift
struct WindowButtons: View {
    @Environment(\.openWindow) private var openWindow
    @Environment(\.dismissWindow) private var dismissWindow
    @Environment(\.openSettings) private var openSettings
    let item: Item

    var body: some View {
        Button("Activity") { openWindow(id: "activity") }
        Button("Open Detail") { openWindow(id: "detail", value: item.id) }
        Button("Close Activity") { dismissWindow(id: "activity") }
        Button("Preferences...") { openSettings() }
        SettingsLink { Label("Settings", systemImage: "gear") }
    }
}
```

Scene modifiers worth knowing (all verified on the macOS 27 SDK):

| Modifier | Values / note |
|---|---|
| `defaultSize`, `defaultPosition` | First-open geometry only; restoration wins afterwards |
| `windowResizability` | `.automatic`, `.contentSize`, `.contentMinSize` |
| `windowStyle` | `.automatic`, `.titleBar`, `.hiddenTitleBar`, `.plain` - there is no full-screen style; use `NSWindow.toggleFullScreen(_:)` |
| `windowToolbarStyle` | `.automatic`, `.unified`, `.unifiedCompact`, `.expanded` |
| `restorationBehavior` (macOS 15+) | `.automatic` or `.disabled` only - there is no `.enabled` |
| `defaultLaunchBehavior` (macOS 15+) | `.automatic`, `.presented`, `.suppressed` - the supported way to start with no window |
| `windowLevel` (macOS 15+) | `.floating` keeps the window above normal windows |
| `windowIdealSize`, `windowManagerRole`, `windowBackgroundDragBehavior` | Scene modifiers (macOS 15+) |
| `windowResizeAnchor(_:)` | A **View** modifier (macOS 26+), not a Scene one |
| `windowDismissBehavior`, `windowMinimizeBehavior`, `windowFullScreenBehavior` | **View** modifiers that enable/disable those window buttons |

`presentedWindowStyle(_:)` is a View modifier that styles windows the view presents. `WindowDragGesture` makes arbitrary content drag the window.

`@Environment(\.scenePhase)` is per scene on macOS, not an app-foreground signal. For "app became frontmost / lost focus" observe `NSApplication.didBecomeActiveNotification` / `didResignActiveNotification`, or `@Environment(\.appearsActive)` for a single window.

## Settings

```swift
struct SettingsView: View {
    var body: some View {
        TabView {
            Tab("General", systemImage: "gear") { GeneralSettingsView() }
            Tab("Appearance", systemImage: "paintpalette") { AppearanceSettingsView() }
        }
        .frame(width: 450)
    }
}

struct GeneralSettingsView: View {
    @AppStorage("autoSave") private var autoSave = true
    @AppStorage("fontSize") private var fontSize = 14.0

    var body: some View {
        Form {
            Toggle("Auto-save documents", isOn: $autoSave)
            Slider(value: $fontSize, in: 10...24, step: 1) { Text("Font size") }
        }
        .formStyle(.grouped)
    }
}
```

Open Settings with `SettingsLink` or `@Environment(\.openSettings)` - never by sending the `showSettingsWindow:` selector yourself; the selector changed across releases. An AppKit-lifecycle app can present a SwiftUI `Settings` scene with real scene semantics via `NSHostingSceneRepresentation` (see macos-appkit-interop.md).

## MenuBarExtra and its gotchas

```swift
struct MenuBarScenes: Scene {
    @State private var state = AppState()
    @AppStorage("showMenuBarExtra") private var showMenuBarExtra = true
    @Environment(\.openWindow) private var openWindow

    var body: some Scene {
        MenuBarExtra("Status", systemImage: "circle.fill") {
            Button("Show Dashboard") { openWindow(id: "dashboard") }
            Toggle("Monitoring", isOn: $state.isMonitoring)
            Divider()
            Button("Quit") { NSApplication.shared.terminate(nil) }
                .keyboardShortcut("q")
        }
        .menuBarExtraStyle(.menu)

        // Dynamic label; isInserted lets a Settings toggle remove the item
        MenuBarExtra(isInserted: $showMenuBarExtra) {
            MenuBarContentView()
        } label: {
            Image(systemName: state.isConnected ? "wifi" : "wifi.slash")
        }
        .menuBarExtraStyle(.window)
    }
}
```

**`.menu` style renders to a native `NSMenu`.** Consequences:
- SwiftUI font modifiers (`.monospacedDigit()`, `.font(.system(.body, design: .monospaced))`) are silently ignored, so a "0:05" timer jumps width every tick. Give the text a fixed `.frame(width:)`, or render it with `ImageRenderer` into an image so the font is baked in.
- `TimelineView(.periodic(...))` never ticks. Drive the text from an `@Observable` property updated by a task.
- The content's `onAppear` fires only when the user opens the menu. Never start monitoring, request permissions, or set up delegates there - use `applicationDidFinishLaunching`.
- On macOS 27, SwiftUI hides SF Symbol images on menu items by default (see macos-swiftui.md, "Menus and commands").

```swift
@MainActor @Observable
final class ElapsedClock {
    var formatted = "0:00"
    private var ticker: Task<Void, Never>?

    func start(at start: Date) {
        ticker = Task { [weak self] in
            while !Task.isCancelled {
                let elapsed = Duration.seconds(Date.now.timeIntervalSince(start))
                self?.formatted = elapsed.formatted(.time(pattern: .minuteSecond))
                try? await Task.sleep(for: .seconds(1))
            }
        }
    }

    func stop() { ticker?.cancel() }
}
```

**Crash: high-frequency label updates.** A per-second timer driving the `MenuBarExtra` *label* (elapsed time, a live meter) can crash intermittently with `EXC_BREAKPOINT` in `-[NSWindow _postWindowNeedsUpdateConstraints]`: the `NSHostingView` behind the status item is pushed into an AppKit constraint-update exception by repeated re-layout. It compiles, usually runs, and crashes in the field. Keep the SwiftUI label static and put the live readout in an AppKit-owned status item with monospaced digits (which also stops the width oscillation that drives the churn):

```swift
@MainActor
final class LiveStatusItem {
    private let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)

    func show(_ elapsed: String) {
        item.button?.attributedTitle = NSAttributedString(
            string: elapsed,
            attributes: [.font: NSFont.monospacedDigitSystemFont(ofSize: 13, weight: .regular)]
        )
    }
}
```

Throttle anyway: a wall-clock readout rarely needs more than 1 Hz.

**Reach the delegate through the adaptor property.** `(NSApplication.shared.delegate as? AppDelegate)?.monitor = monitor` in `App.init()` can silently do nothing because the delegate is not installed yet. Use the adaptor:

```swift
struct AdaptorApp: App {
    @NSApplicationDelegateAdaptor private var delegate: AppDelegate
    private let monitor = AudioMonitor()

    init() {
        delegate.monitor = monitor
    }

    var body: some Scene { Settings { EmptyView() } }
}
```

## Document apps

With the macOS 27 SDK (also iOS/visionOS 27), documents are reference types conforming to `ReadableDocument`, `WritableDocument`, or `Document` (both). I/O happens in separate `DocumentReader` / `DocumentWriter` values off the main actor; the document object itself is `@Observable` and touched on the main actor. Apple's [SwiftUI release notes](https://developer.apple.com/documentation/macos-release-notes/macos-27-release-notes) say to use `Document` instead of `FileDocument` / `ReferenceFileDocument`.

The protocol shape in the SDK:
- `DocumentReader`: `@concurrent func read(from: sending Source, progress: consuming Subprogress) async throws -> sending Snapshot` (`Source` defaults to `URL`).
- `DocumentWriter`: `@concurrent func write(snapshot: sending Snapshot, to: sending Destination, previous: sending Snapshot?, progress: consuming Subprogress) async throws` (`Destination` defaults to `URL`). The release notes call it `write(content:...)`; the shipping label is `snapshot:`.
- `ReadableDocument`: `static var readableContentTypes`, `func reader(configuration:)`, `@MainActor func apply(snapshot:previous:) async throws`.
- `WritableDocument`: `writableContentTypes` (defaulted to the readable ones when you conform to both), `func writer(configuration:)`, `@MainActor func snapshot(contentType:) async throws`.

```swift
@Observable
final class TextDocument: Document {
    static var readableContentTypes: [UTType] { [.plainText] }

    var text = ""

    struct Reader: DocumentReader {
        @concurrent func read(from source: sending URL, progress: consuming Subprogress) async throws -> sending String {
            let progress = progress.start(totalCount: 1)
            defer { progress.complete(count: 1) }
            return try String(contentsOf: source, encoding: .utf8)
        }
    }

    struct Writer: DocumentWriter {
        @concurrent func write(snapshot: sending String, to destination: sending URL,
                               previous: sending String?, progress: consuming Subprogress) async throws {
            try snapshot.write(to: destination, atomically: true, encoding: .utf8)
        }
    }

    func reader(configuration: sending ReadConfiguration) -> sending Reader { Reader() }
    func writer(configuration: sending WriteConfiguration) -> sending Writer { Writer() }

    @MainActor func apply(snapshot: sending String, previous: sending String?) async throws {
        text = snapshot
    }

    @MainActor func snapshot(contentType: UTType) async throws -> sending String { text }
}

struct EditorView: View {
    @Bindable var document: TextDocument
    var body: some View { TextEditor(text: $document.text) }
}

@main
struct TextApp: App {
    var body: some Scene {
        DocumentGroup { (document: TextDocument) in
            EditorView(document: document)
        } makeDocument: { configuration, context in
            TextDocument()
        }
    }
}
```

Isolation rules that bite:
- **Write `@concurrent` on `read`/`write`, not `nonisolated`.** Under default MainActor isolation (`-default-isolation MainActor` / Xcode's Default Actor Isolation = MainActor, with `nonisolated(nonsending)` semantics), a `nonisolated async` or unannotated method runs on the main actor. Both variants still compile with no diagnostic - the I/O just silently moves onto the main thread.
- `makeDocument` / `makeReadableDocument` closures are `@MainActor`; they receive a `URLDocumentConfiguration` (`@MainActor`, `@Observable`, not `Sendable`: `fileURL`, `lastContentModificationDate`, `makeFileCoordinator()`) and a `DocumentCreationContext`.
- Under default MainActor isolation, a `UTType` constant declared in an extension is main-actor-isolated and cannot be read from a `nonisolated` document type - declare it `nonisolated static let`.
- Progress reported through `Subprogress` might not be shown yet (known issue in the macOS 27.0 notes).

Other initializers and helpers (all macOS 27+):
- `DocumentGroup(viewer:makeReadableDocument:)` for a `ReadableDocument` viewer; `DocumentGroup(allowCreating: false, editor:makeDocument:)` for edit-only apps with no New command.
- `FileWrapperDocumentReader` / `FileWrapperDocumentWriter` adapt `FileWrapper` code. The writer closure gets `(snapshot, previous: FileWrapper?)`; reuse `previous` for packages so only changed children are rewritten.
- `@Environment(\.newDocument)` accepts an in-memory `ReadableDocument` - the hook for "New from Template".
- `fileExporter(isPresented:documents:contentTypes:onCompletion:onCancellation:)` exports a collection of `WritableDocument`s in one dialog.

```swift
extension UTType { nonisolated static let notesPackage = UTType(exportedAs: "com.example.notes") }

// nonisolated: the @Sendable newDocument autoclosure must be able to construct it
@Observable
nonisolated final class NotesPackage: Document {
    static var readableContentTypes: [UTType] { [.notesPackage] }
    var notes: [String: Data]

    init(notes: [String: Data] = [:]) { self.notes = notes }

    func reader(configuration: sending ReadConfiguration) -> sending FileWrapperDocumentReader<[String: Data]> {
        FileWrapperDocumentReader(configuration) { wrapper in
            (wrapper.fileWrappers ?? [:]).compactMapValues(\.regularFileContents)
        }
    }

    func writer(configuration: sending WriteConfiguration) -> sending FileWrapperDocumentWriter<[String: Data]> {
        FileWrapperDocumentWriter(configuration) { snapshot, previous in
            // Reuse the previous package so only changed children are rewritten
            let package = previous ?? FileWrapper(directoryWithFileWrappers: [:])
            for (name, data) in snapshot where package.fileWrappers?[name]?.regularFileContents != data {
                if let old = package.fileWrappers?[name] { package.removeFileWrapper(old) }
                let child = FileWrapper(regularFileWithContents: data)
                child.preferredFilename = name
                package.addFileWrapper(child)
            }
            return package
        }
    }

    @MainActor func apply(snapshot: sending [String: Data], previous: sending [String: Data]?) async throws {
        notes = snapshot
    }

    @MainActor func snapshot(contentType: UTType) async throws -> sending [String: Data] { notes }
}

struct NewFromTemplateCommands: Commands {
    @Environment(\.newDocument) private var newDocument

    var body: some Commands {
        CommandGroup(after: .newItem) {
            Button("New from Template") {
                newDocument(NotesPackage(notes: ["README.md": Data("# Notes".utf8)]))
            }
        }
    }
}
```

**Deploying below macOS 27** keeps `FileDocument` (value type) / `ReferenceFileDocument` (class, snapshot-based undo). They are deprecated as "to be deprecated" (`deprecated: 100000.0`), so the compiler emits no warning yet - do not read a clean build as "still recommended".

```swift
struct LegacyTextDocument: FileDocument {
    static var readableContentTypes: [UTType] { [.plainText] }
    var text = ""

    init() {}

    init(configuration: ReadConfiguration) throws {
        guard let data = configuration.file.regularFileContents else {
            throw CocoaError(.fileReadCorruptFile)
        }
        text = String(decoding: data, as: UTF8.self)
    }

    func fileWrapper(configuration: WriteConfiguration) throws -> FileWrapper {
        FileWrapper(regularFileWithContents: Data(text.utf8))
    }
}

struct LegacyApp: App {
    var body: some Scene {
        DocumentGroup(newDocument: LegacyTextDocument()) { file in
            TextEditor(text: file.$document.text)
        }
    }
}
```

Document types must be declared in Info.plist (`CFBundleDocumentTypes`, plus `UTExportedTypeDeclarations` for your own UTType) or the open panel greys files out.

## App delegate and async termination

`NSApplicationDelegate` conformance does not make the whole class main-actor-isolated - helper methods stay nonisolated and calls into `NSApp` warn. Mark the delegate `@MainActor` (redundant, but harmless, under default MainActor isolation).

For async cleanup before quitting (finalizing an `AVAssetWriter`, stopping streams), return `.terminateLater` and reply exactly once, with a timeout so a hung cleanup cannot block logout or shutdown:

```swift
@MainActor
final class AudioMonitor {
    func stopAndSave() async { /* finalize writers, stop streams */ }
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    var monitor: AudioMonitor?
    private var hasReplied = false

    func applicationDidFinishLaunching(_ notification: Notification) {}

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        false
    }

    func application(_ application: NSApplication, open urls: [URL]) {}

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        guard let monitor else { return .terminateNow }
        hasReplied = false

        Task {
            await monitor.stopAndSave()
            reply()
        }
        Task {
            try? await Task.sleep(for: .seconds(8))
            reply()
        }
        return .terminateLater
    }

    private func reply() {
        guard !hasReplied else { return }
        hasReplied = true
        NSApp.reply(toApplicationShouldTerminate: true)
    }
}
```

Replying twice is undefined behavior; both tasks run on the main actor, so the flag check is race-free. Keep the monitor main-actor-isolated (or `Sendable`): a plain non-Sendable class with a `nonisolated async` method fails with `sending 'monitor' risks causing data races` - a region-isolation error that `swiftc -typecheck` never shows, only a full build. Pair this with `AVAssetWriter.movieFragmentInterval` so a fired timeout loses at most one fragment. `applicationShouldTerminateAfterLastWindowClosed` returning `false` keeps a menu bar app alive with no windows.

## Menu-bar-only apps (`LSUIElement`)

| Info.plist key | Dock / Cmd+Tab | Can show UI | Use |
|---|---|---|---|
| neither | yes | yes | Normal app |
| `LSUIElement` = YES | no | yes | Menu bar apps |
| `LSBackgroundOnly` = YES | no | no | Faceless helpers |

To toggle the Dock icon at runtime instead, call `NSApp.setActivationPolicy(.regular)` / `.accessory`. To merely start without a window, prefer `defaultLaunchBehavior(.suppressed)` over `LSUIElement`.

Operational gotchas:
- **Always ship a Quit item.** No Dock icon means no Dock menu, and the app does not appear in the Force Quit dialog.
- **Windows open behind other apps.** An accessory app is not activated when you open a window. Call `NSApp.activate()` (macOS 14+; `activate(ignoringOtherApps:)` is slated for deprecation) right after `openWindow`.
- **Cmd+, does nothing.** There is no app menu for `CommandGroup(replacing: .appSettings)` to attach to. Put a `SettingsLink` with `.keyboardShortcut(",")` in the menu content; the shortcut works only while the menu is open.
- **`NSWorkspace.didLaunchApplicationNotification` does not fire for `LSUIElement` apps** - other tools watching for your app must use KVO on `runningApplications` (see macos-system-integration.md).
- **Onboarding** must appear before any user interaction, so host it in a manually created `NSWindow`, and finish via a callback - `@Environment(\.dismiss)` has nothing to dismiss in a hand-made window. Set `isReleasedWhenClosed = false` and drop your reference before `close()`:

```swift
final class OnboardingPresenter {
    private var window: NSWindow?

    @MainActor func showIfNeeded() {
        guard !UserDefaults.standard.bool(forKey: "hasCompletedOnboarding") else { return }
        if CGPreflightScreenCaptureAccess() {
            UserDefaults.standard.set(true, forKey: "hasCompletedOnboarding")
            return
        }
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 500, height: 400),
                              styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.isReleasedWhenClosed = false
        window.contentView = NSHostingView(rootView: OnboardingView { [weak self] in
            UserDefaults.standard.set(true, forKey: "hasCompletedOnboarding")
            let shown = self?.window
            self?.window = nil
            shown?.close()
        })
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate()
        self.window = window
    }
}
```

- **Restarting.** `NSWorkspace.OpenConfiguration.createsNewApplicationInstance = true` starts a duplicate while the old one is still running, and a plain `open` of a running app only re-activates it. Wait for this PID to exit, then relaunch:

```swift
@MainActor func restartApp() throws {
    let pid = ProcessInfo.processInfo.processIdentifier
    let script = "while kill -0 \(pid) 2>/dev/null; do sleep 0.2; done; /usr/bin/open \"$0\""
    try Process.run(URL(fileURLWithPath: "/bin/sh"), arguments: ["-c", script, Bundle.main.bundlePath])
    NSApp.terminate(nil)
}
```

- **Crashes are invisible.** macOS suppresses the "quit unexpectedly" dialog for `LSUIElement` apps: the icon disappears and the user keeps believing a recorder or monitor is running. `NSSetUncaughtExceptionHandler` only logs. Bundle a small watchdog that waits on the app's PID with `kqueue`; since the watchdog is not the app's parent it cannot read the exit status, so have the app write a clean-exit marker in `applicationWillTerminate` and treat an exit without it as a crash:

```c
int kq = kqueue();
struct kevent change;
EV_SET(&change, targetPID, EVFILT_PROC, EV_ADD | EV_ENABLE, NOTE_EXIT, 0, NULL);
kevent(kq, &change, 1, NULL, 0, NULL);

struct kevent event;
kevent(kq, NULL, 0, &event, 1, NULL);   // blocks until the app exits
if (!cleanExitMarkerExists()) showCrashAlert();
```

| Watchdog hosting | Pros | Cons |
|---|---|---|
| Spawned by the app at launch (default) | No system prompt, nothing in System Settings | Misses crashes before it is spawned |
| `SMAppService.loginItem` in `Contents/Library/LoginItems/` | Survives reboot, catches startup crashes | "Background Items Added" notification; user can disable it silently |
