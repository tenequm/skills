# macOS System Integration

How a Mac app plugs into the system: keyboard handling, drag and drop, sandboxed file access, notifications, watching other processes, Accessibility (AXUIElement), per-process CoreAudio state, login items, XPC helpers, sleep prevention, unified logging, and privacy usage strings. App Intents, Shortcuts, Spotlight entities, widgets and Control Center controls live in app-intents.md.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every Swift block typechecked with `swiftc -typecheck -swift-version 6` against the macOS 27.0 SDK (target macOS 26 for the `DropSession` and XPC peer-requirement APIs, which are macOS 26+), with and without `-default-isolation MainActor`; symbols checked in the SwiftUI, XPC and AppKit interfaces and headers.

## Contents
- Keyboard handling
- Drag and drop
- Sandboxed file access and app directories
- Notifications
- Watching other apps
- Accessibility API (AXUIElement)
- Which processes use audio (CoreAudio per-process)
- Login items (SMAppService)
- XPC helpers
- Preventing sleep
- Logging and signposts
- Privacy usage strings

## Keyboard handling

```swift
struct KeyHandlingView: View {
    @State private var query = ""
    var body: some View {
        TextField("Search", text: $query)
            .onKeyPress(.return) {
                submit()
                return .handled
            }
            .onKeyPress(.space, phases: .down) { press in
                guard press.modifiers.contains(.shift) else { return .ignored }
                preview()
                return .handled
            }
    }
    private func submit() {}
    private func preview() {}
}

struct DeleteButtons: View {
    var body: some View {
        Button("Delete") {}
            .keyboardShortcut(.delete, modifiers: .command)
    }
}
```

- `onKeyPress` only fires for the focused view - make custom views `.focusable()` or nothing arrives. Return `.ignored` to let the event continue up the chain.
- Menu shortcuts belong on commands (see macos-swiftui.md); `.keyboardShortcut(.defaultAction)` / `.cancelAction` map Return / Esc.
- System-wide hotkeys (when the app is not active) are not a SwiftUI feature; they need a Carbon `RegisterEventHotKey` wrapper or a third-party package. `NSEvent.addGlobalMonitorForEvents` only observes, cannot consume, and needs the Accessibility permission for key events.

## Drag and drop

```swift
nonisolated struct Card: Codable, Identifiable, Transferable {
    var id = UUID()
    var title: String

    static var transferRepresentation: some TransferRepresentation {
        CodableRepresentation(contentType: .card)
        ProxyRepresentation(exporting: \.title)
    }
}

extension UTType {
    nonisolated static let card = UTType(exportedAs: "com.example.card")
}

struct Board: View {
    @State private var cards: [Card] = []
    @State private var importedFiles: [URL] = []

    var body: some View {
        VStack {
            ForEach(cards) { card in
                Text(card.title)
                    .draggable(card) {
                        Label(card.title, systemImage: "rectangle.on.rectangle").padding(8)
                    }
            }
        }
        .dropDestination(for: Card.self) { dropped, session in
            cards.append(contentsOf: dropped)
        }
        .dropDestination(for: URL.self) { urls, session in
            importedFiles.append(contentsOf: urls)
        }
    }
}
```

- `dropDestination(for:isEnabled:action:)` with a `DropSession` (macOS 26+) is current; the `(items, location) -> Bool` form is soft-deprecated - keep it only below macOS 26. `onDropSessionUpdated` and `dropConfiguration` react to the session's phase and pick the operation.
- Representation order matters: the first one the receiver accepts wins, so list your rich type first and the plain-text `ProxyRepresentation` fallback last.
- A custom `UTType(exportedAs:)` must also be declared under `UTExportedTypeDeclarations` in Info.plist, or drags between apps silently fail. Under default MainActor isolation declare the constant `nonisolated` - `transferRepresentation` is nonisolated and cannot read a main-actor static.
- Dropped file URLs in a sandboxed app carry a sandbox extension for that drop only - copy or bookmark them right away.
- In a `List` with the macOS 27 SDK, row-level `dropDestination` now fires (see macos-swiftui.md).

## Sandboxed file access and app directories

URLs the user picks (open panel, `fileImporter`, drops) are readable only for the session. To reopen them after relaunch, persist a security-scoped bookmark (requires the `com.apple.security.files.bookmarks.app-scope` entitlement in a sandboxed app):

```swift
enum BookmarkStore {
    static func save(_ url: URL, key: String) throws {
        let data = try url.bookmarkData(options: .withSecurityScope,
                                        includingResourceValuesForKeys: nil, relativeTo: nil)
        UserDefaults.standard.set(data, forKey: key)
    }

    static func withAccess<T>(key: String, _ body: (URL) throws -> T) throws -> T? {
        guard let data = UserDefaults.standard.data(forKey: key) else { return nil }
        var isStale = false
        let url = try URL(resolvingBookmarkData: data, options: .withSecurityScope,
                          relativeTo: nil, bookmarkDataIsStale: &isStale)
        guard url.startAccessingSecurityScopedResource() else { return nil }
        defer { url.stopAccessingSecurityScopedResource() }
        if isStale { try save(url, key: key) }
        return try body(url)
    }
}
```

Balance every `startAccessingSecurityScopedResource()` with a stop - leaked accesses exhaust a per-process limit and later starts fail. Refresh stale bookmarks while you still have access.

```swift
func appSupportDirectory() throws -> URL {
    let dir = URL.applicationSupportDirectory.appending(path: Bundle.main.bundleIdentifier ?? "MyApp")
    try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    return dir
}
```

In a sandboxed app `URL.applicationSupportDirectory` already points inside the container. Share data between an app and its extensions or helpers with an app group (`com.apple.security.application-groups`); on macOS the group ID is prefixed with your team ID:

```swift
struct SharedSettingsView: View {
    @AppStorage("refreshInterval", store: UserDefaults(suiteName: "TEAMID.com.example.shared"))
    private var refreshInterval = 60.0
    var body: some View { Text("\(refreshInterval)") }
}
```

macOS 27 tightens cross-app data access: reading another team's app data container or app group container is now denied by default (no prompt) and only the user can grant it in Privacy & Security; XProtect may also block access to other teams' app data. Apps can no longer read the TCC database directly.

## Notifications

```swift
func notify(title: String, body: String) async throws {
    let center = UNUserNotificationCenter.current()
    guard try await center.requestAuthorization(options: [.alert, .sound]) else { return }
    let content = UNMutableNotificationContent()
    content.title = title
    content.body = body
    content.sound = .default
    try await center.add(UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil))
}
```

A `nil` trigger delivers immediately. Notifications posted while the app is frontmost are not shown unless a `UNUserNotificationCenterDelegate` returns presentation options from `willPresent` - set the delegate in `applicationDidFinishLaunching`.

## Watching other apps

`NSRunningApplication` gives `bundleIdentifier`, `processIdentifier`, `localizedName`, `isActive`, `isTerminated`, `launchDate`, `icon` and `activationPolicy`. Launch and quit notifications come from `NSWorkspace.shared.notificationCenter` - **not** `NotificationCenter.default`, where they never arrive:

```swift
@MainActor
final class LaunchObserver {
    private var tokens: [NSObjectProtocol] = []

    func start(onChange: @escaping @MainActor (NSRunningApplication) -> Void) {
        let center = NSWorkspace.shared.notificationCenter
        for name in [NSWorkspace.didLaunchApplicationNotification, NSWorkspace.didTerminateApplicationNotification] {
            tokens.append(center.addObserver(forName: name, object: nil, queue: .main) { note in
                guard let app = note.userInfo?[NSWorkspace.applicationUserInfoKey] as? NSRunningApplication else { return }
                MainActor.assumeIsolated { onChange(app) }
            })
        }
    }

    func stop() {
        tokens.forEach(NSWorkspace.shared.notificationCenter.removeObserver)
        tokens.removeAll()
    }
}
```

On macOS 26+ the typed message form avoids the `userInfo` casting and the isolation dance:

```swift
@MainActor func observeLaunches(_ onLaunch: @escaping @MainActor (NSRunningApplication) -> Void) -> NotificationCenter.ObservationToken {
    NSWorkspace.shared.notificationCenter.addObserver(of: NSWorkspace.shared, for: .didLaunchApplication) { message in
        onLaunch(message.application)
    }
}
```

Other workspace notifications: `didActivateApplicationNotification`, `didDeactivateApplicationNotification`, `didHideApplicationNotification`, `didUnhideApplicationNotification`.

**`didLaunch`/`didTerminate` are not posted for background-only or `LSUIElement` apps** - menu bar utilities, helpers and agents are invisible to them. Observe `runningApplications` with KVO, which covers every app:

```swift
@MainActor @Observable
final class ProcessMonitor {
    var watchedBundleIDs: Set<String> = []
    private(set) var runningWatched: [NSRunningApplication] = []
    @ObservationIgnored private var observation: NSKeyValueObservation?

    func start() {
        refresh()
        observation = NSWorkspace.shared.observe(\.runningApplications, options: [.new, .old]) { [weak self] _, _ in
            Task { @MainActor in self?.refresh() }
        }
    }

    func stop() {
        observation?.invalidate()
        observation = nil
    }

    private func refresh() {
        runningWatched = NSWorkspace.shared.runningApplications.filter {
            $0.bundleIdentifier.map(watchedBundleIDs.contains) ?? false
        }
    }
}
```

The KVO callback can arrive off the main thread, hence the hop. Notifications + KVO together, with an occasional safety-net refresh, is the robust combination for long-running monitors.

## Accessibility API (AXUIElement)

`NSWorkspace` tells you *which* apps run; `AXUIElement` reads and drives *another app's* UI - window titles, focused element, selected text, pressing buttons. It underpins window managers, launchers and text expanders.

```swift
func focusedWindowTitle(prompt: Bool) -> String? {
    // String literal: the kAXTrustedCheckOptionPrompt global is a mutable var Swift 6 rejects
    let options = ["AXTrustedCheckOptionPrompt": prompt] as CFDictionary
    guard AXIsProcessTrustedWithOptions(options),
          let app = NSWorkspace.shared.frontmostApplication else { return nil }

    let axApp = AXUIElementCreateApplication(app.processIdentifier)
    var window: CFTypeRef?
    guard AXUIElementCopyAttributeValue(axApp, kAXFocusedWindowAttribute as CFString, &window) == .success,
          let window else { return nil }

    var title: CFTypeRef?
    guard AXUIElementCopyAttributeValue(window as! AXUIElement, kAXTitleAttribute as CFString, &title) == .success
    else { return nil }
    return title as? String
}
```

Constraints that decide whether a feature is viable:
- Needs the **Accessibility** permission (System Settings > Privacy & Security > Accessibility), granted per app. `AXIsProcessTrustedWithOptions` with the prompt option opens the request; poll `AXIsProcessTrusted()` afterwards rather than assuming the user said yes.
- The grant is keyed to the code signature: re-signing with a different identity (or ad-hoc builds) forces a re-grant (see macos-distribution.md).
- **Not available to sandboxed apps** - AX-driven features are Developer ID only.

## Which processes use audio (CoreAudio per-process)

macOS 14.2+ exposes per-process audio state - the basis for "a call started" detection:

```swift
private func processProperty<T: BitwiseCopyable>(_ object: AudioObjectID, _ selector: AudioObjectPropertySelector, default value: T) -> T {
    var address = AudioObjectPropertyAddress(mSelector: selector,
                                             mScope: kAudioObjectPropertyScopeGlobal,
                                             mElement: kAudioObjectPropertyElementMain)
    var result = value
    var size = UInt32(MemoryLayout<T>.size)
    let status = AudioObjectGetPropertyData(object, &address, 0, nil, &size, &result)
    return status == noErr ? result : value
}

func callingProcessIDs() -> [pid_t] {
    var address = AudioObjectPropertyAddress(mSelector: kAudioHardwarePropertyProcessObjectList,
                                             mScope: kAudioObjectPropertyScopeGlobal,
                                             mElement: kAudioObjectPropertyElementMain)
    let system = AudioObjectID(kAudioObjectSystemObject)
    var size: UInt32 = 0
    guard AudioObjectGetPropertyDataSize(system, &address, 0, nil, &size) == noErr else { return [] }
    var objects = [AudioObjectID](repeating: 0, count: Int(size) / MemoryLayout<AudioObjectID>.size)
    guard AudioObjectGetPropertyData(system, &address, 0, nil, &size, &objects) == noErr else { return [] }

    let myPID = ProcessInfo.processInfo.processIdentifier
    return objects.compactMap { object in
        let pid: pid_t = processProperty(object, kAudioProcessPropertyPID, default: -1)
        let input: UInt32 = processProperty(object, kAudioProcessPropertyIsRunningInput, default: 0)
        let output: UInt32 = processProperty(object, kAudioProcessPropertyIsRunningOutput, default: 0)
        // input AND output filters out dictation/Siri (input only); exclude ourselves
        return pid > 0 && pid != myPID && input != 0 && output != 0 ? pid : nil
    }
}
```

Gotchas:
- **Do not use `kAudioDevicePropertyDeviceIsRunningSomewhere` as a "mic in use" trigger.** It is system-wide and includes your own process: once you open the mic in response, it stays `true` after the other app stops, so auto-stop never fires. Use the per-process list and exclude your PID.
- Also exclude ScreenCaptureKit helpers (`com.apple.screencapturekit*`, `com.apple.replayd`). Map a PID to a bundle ID with `NSRunningApplication(processIdentifier:)`; browsers report helper processes (`com.google.Chrome.helper.renderer`), so strip `.helper*` to find the parent app.
- Polling every ~3 s is simpler and more reliable than property listeners for call detection; listeners need `Unmanaged` context juggling and miss some browser audio pipelines. If you do use the block-based `AudioObjectRemovePropertyListenerBlock`, removal can fail because the Swift closure is re-bridged to a different block - prefer the function-pointer `AudioObjectAddPropertyListener` / `AudioObjectRemovePropertyListener` pair.
- When reading `AudioBufferList`-shaped properties, allocate the byte size returned by `AudioObjectGetPropertyDataSize`; `UnsafeMutablePointer<AudioBufferList>.allocate(capacity: 1)` has room for one buffer and overflows on multi-channel devices.
- These APIs are not reliably available under the App Sandbox - plan mic/call auto-triggers as Developer ID only, or provide a manual start. Capturing the audio itself is in macos-core-audio-tap.md.

## Login items (SMAppService)

```swift
func setLaunchAtLogin(_ enabled: Bool) {
    do {
        if enabled { try SMAppService.mainApp.register() }
        else { try SMAppService.mainApp.unregister() }
    } catch {
        Logger(subsystem: "com.example.MyApp", category: "login").error("login item: \(error.localizedDescription, privacy: .public)")
    }
    if SMAppService.mainApp.status == .requiresApproval {
        SMAppService.openSystemSettingsLoginItems()
    }
}

struct LaunchAtLoginToggle: View {
    @State private var isOn = SMAppService.mainApp.status == .enabled
    @Environment(\.appearsActive) private var appearsActive

    var body: some View {
        Toggle("Launch at login", isOn: $isOn)
            .onChange(of: isOn) { _, newValue in setLaunchAtLogin(newValue) }
            .onChange(of: appearsActive) { _, active in
                // The user may have changed it in System Settings
                if active { isOn = SMAppService.mainApp.status == .enabled }
            }
    }
}
```

Never persist login-item state yourself - the user can flip it in System Settings at any time; `status` is the truth.

| Service | Bundle location | Runs as | Starts |
|---|---|---|---|
| `SMAppService.mainApp` | the app | user | at login |
| `.loginItem(identifier:)` | `Contents/Library/LoginItems/Helper.app` | user | now + login |
| `.agent(plistName:)` | `Contents/Library/LaunchAgents/<name>.plist` | user | now + login |
| `.daemon(plistName:)` | `Contents/Library/LaunchDaemons/<name>.plist` | root | after admin approval |

All of them show the "Background Items Added" notification and can be disabled by the user. Agent and daemon plists point at the executable with `BundleProgram` (a path relative to the app bundle, e.g. `Contents/Resources/MyHelper`) instead of `Program`, and declare `MachServices` if a client will connect over XPC. Since macOS 27, `launchd` refuses plists that carry the quarantine extended attribute.

## XPC helpers

`SMAppService` registers a helper; XPC is how you talk to it. The Swift `XPCSession` / `XPCListener` API (macOS 14+) uses `Codable` messages; the `requirement:` initializers (macOS 26+) enforce the peer's code signature at connection time - use them instead of trusting whoever connects:

```swift
nonisolated struct StatusRequest: Codable { var verbose = false }
nonisolated struct StatusReply: Codable { var running: Bool }

// App side
func queryHelper() throws -> StatusReply {
    let session = try XPCSession(machService: "com.example.MyHelper",
                                 requirement: .isFromSameTeam())
    defer { session.cancel(reason: "done") }
    return try session.sendSync(StatusRequest())
}

// Helper side (its main.swift)
func runHelper() throws -> XPCListener {
    try XPCListener(service: "com.example.MyHelper", requirement: .isFromSameTeam()) { request in
        request.accept { (message: StatusRequest) -> StatusReply in
            StatusReply(running: true)
        }
    }
}
```

- The name must match a `MachServices` key in the helper's launchd plist (or be the bundle ID of an embedded XPC service, using `XPCSession(xpcService:)`).
- The helper must keep the listener alive and park the main thread (`dispatchMain()`), or it exits immediately.
- `sendSync` blocks the calling thread - call it off the main actor, or use `send(_:replyHandler:)`.
- `XPCPeerRequirement` also offers `.hasEntitlement(_:)`, `.isPlatformCode(...)` and `isFromSameTeam(andMatchesSigningIdentifier:)` for a stricter match.

## Preventing sleep

```swift
func exportWhileAwake(_ work: () throws -> Void) rethrows {
    let activity = ProcessInfo.processInfo.beginActivity(options: .userInitiated,
                                                         reason: "Exporting recording")
    defer { ProcessInfo.processInfo.endActivity(activity) }
    try work()
}
```

`.userInitiated` disables App Nap throttling and already includes `.idleSystemSleepDisabled`; use `.userInitiatedAllowingIdleSystemSleep` when the Mac may sleep, and add `.idleDisplaySleepDisabled` to keep the screen on. The user can still sleep the Mac manually. Always end the activity - a leaked one keeps the machine awake.

## Logging and signposts

`print` output goes nowhere in a shipped app - and a menu-bar-only app has no console at all. Use `os.Logger`, which feeds `log stream`, `log show` and Console.app:

```swift
private let log = Logger(subsystem: "com.example.MyApp", category: "capture")

func logExamples(index: Int, error: any Error, userEmail: String) {
    log.debug("frame \(index, privacy: .public) queued")
    log.error("stream stopped: \(error.localizedDescription, privacy: .public)")
    log.notice("signed in as \(userEmail, privacy: .private(mask: .hash))")
}

let signposter = OSSignposter(subsystem: "com.example.MyApp", category: "render")

func renderFrame() {
    let state = signposter.beginInterval("compose")
    defer { signposter.endInterval("compose", state) }
    composeLayers()
}
```

- **Interpolated dynamic values are private by default** and show as `<private>` outside a debugger. Mark diagnostic values `.public`, keep user data private (`.private(mask: .hash)` still lets you correlate).
- **Levels persist differently.** `.debug` is memory-only, `.info` is kept only when collected; `.notice` (default), `.error` and `.fault` go to the on-disk store. Use `.notice`+ for anything you need from a user's sysdiagnose.
- Stream your app's logs: `log stream --predicate 'subsystem == "com.example.MyApp"' --level debug`.
- Log archives written on macOS 27 cannot be read on macOS 26.1 or earlier (need 26.2+).
- `OSSignposter` intervals show up as regions in Instruments' Points of Interest / os_signpost tracks.

## Privacy usage strings

Missing purpose strings either crash on first access (camera, microphone) or fail silently. The capture-related ones (`NSMicrophoneUsageDescription`, `NSCameraUsageDescription`, screen recording) are covered in macos-audio-pipeline.md and macos-screencapturekit.md. The easily missed one:

- **`NSLocalNetworkUsageDescription`** (+ `NSBonjourServices` listing every service type you browse, e.g. `_myapp._tcp`). Without it, local network access is denied and it looks like a networking bug: Bonjour discovery returns nothing, connections to `.local` hosts time out. Needed for streaming to a local device, finding a companion app, or talking to a LAN server. See [NSLocalNetworkUsageDescription](https://developer.apple.com/documentation/bundleresources/information-property-list/nslocalnetworkusagedescription).
- `NSAppleEventsUsageDescription` - required before sending Apple Events to another app (scripting Music, Finder, etc.), together with the `com.apple.security.automation.apple-events` entitlement under the hardened runtime; without them the send fails with a permission error (`-1743`) and no prompt appears.
