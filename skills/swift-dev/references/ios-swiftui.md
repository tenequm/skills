# iOS SwiftUI

iPhone-specific SwiftUI: the app/scene lifecycle, navigation and presentation, toolbars, text input, opening Settings, Liquid Glass, UIKit bridging, background refresh, and what changes when you rebuild with the iOS 27 SDK.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every code block compiled with `swiftc -emit-sil` against the iOS 27.0 SDK (`-target arm64-apple-ios26.0 -swift-version 6`, with and without `-default-isolation MainActor`); APIs and availability read from the SDK's SwiftUI `.swiftinterface`; the `@State` source break reproduced in an `xcodebuild` build.

## Contents
- App, WindowGroup and scenePhase
- State in observable controllers
- Navigation and presentation
- Toolbars
- Forms, text input and opening Settings
- Liquid Glass
- UIKit bridge
- Background refresh
- Building with the iOS 27 SDK

## App, WindowGroup and scenePhase

```swift
import SwiftUI

@main
struct NotesApp: App {
    @State private var store = NoteStore()
    @Environment(\.scenePhase) private var scenePhase

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(store)
        }
        .onChange(of: scenePhase) { _, phase in
            switch phase {
            case .active: store.resume()
            case .background: store.flush()
            case .inactive: break
            @unknown default: break
            }
        }
    }
}
```

- On iPhone a `WindowGroup` is one full-screen scene; there are no windows to manage (iPad adds multiple scenes from the same group). There is no `Settings` scene, `MenuBarExtra` or termination hook - the macOS lifecycle in macos-app-lifecycle.md does not apply.
- Read in the `App`, `scenePhase` is an aggregate: `.active` if any scene is active, `.inactive` when none is. Read in a view, it is that view's scene.
- **Treat `.background` as possibly final.** SwiftUI's own docs: "Expect an app that enters the `background` phase to terminate." Save and close connections there; there is no later callback. `.inactive` also fires for Control Center and the app switcher, so do not tear down on it.
- An app keeps running in the background only with a background mode doing real work (audio playing, an active CallKit call - see ios-audio-and-callkit.md) or a scheduled background task (below).

## State in observable controllers

```swift
import Observation
import Foundation

struct Note: Identifiable, Hashable {
    let id: UUID
    var title: String
}

@MainActor
@Observable
final class NoteStore {
    private(set) var notes: [Note] = []
    var path: [Note] = []
    var draftTitle = ""

    func resume() {}
    func flush() {}

    func add() {
        let note = Note(id: UUID(), title: draftTitle)
        notes.append(note)
        draftTitle = ""
        path.append(note)
    }

    func delete(_ note: Note) { notes.removeAll { $0.id == note.id } }
}
```

- Own the controller with `@State` in the `App` and inject it with `.environment(store)`; read it with `@Environment(NoteStore.self)`. For bindings into an environment object, re-declare it locally with `@Bindable var store = store` inside `body` (see `RootView` below).
- When something outside the view tree needs the same instance - an App Intent run by the Action Button, a CallKit delegate - make it a `static let shared` and inject `.environment(NoteStore.shared)` instead of creating it in `@State` (see app-intents.md, architecture.md).
- `@MainActor` is explicit here; under `SWIFT_DEFAULT_ACTOR_ISOLATION: MainActor` (the ios-project-setup.md default) it is inferred.

## Navigation and presentation

```swift
import SwiftUI

struct RootView: View {
    @Environment(NoteStore.self) private var store
    @State private var showsSettings = false
    @State private var pendingDelete: Note?

    var body: some View {
        @Bindable var store = store
        NavigationStack(path: $store.path) {
            List(store.notes) { note in
                NavigationLink(note.title, value: note)
                    .swipeActions {
                        Button("Delete", systemImage: "trash", role: .destructive) { pendingDelete = note }
                    }
            }
            .navigationTitle("Notes")
            .navigationDestination(for: Note.self) { note in
                NoteDetail(note: note)
            }
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Settings", systemImage: "gearshape") { showsSettings = true }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Add", systemImage: "plus") { store.add() }
                }
            }
            .sheet(isPresented: $showsSettings) {
                SettingsView()
                    .presentationDetents([.medium, .large])
            }
            .confirmationDialog(
                "Delete this note?",
                isPresented: Binding(get: { pendingDelete != nil }, set: { if !$0 { pendingDelete = nil } }),
                titleVisibility: .visible,
                presenting: pendingDelete
            ) { note in
                Button("Delete", role: .destructive) { store.delete(note) }
            }
        }
    }
}

struct NoteDetail: View {
    let note: Note
    @State private var showsPlayer = false

    var body: some View {
        Text(note.title)
            .navigationTitle(note.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .bottomBar) {
                    Button("Present") { showsPlayer = true }
                }
            }
            .fullScreenCover(isPresented: $showsPlayer) {
                FullScreenView()
            }
    }
}

struct FullScreenView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Text("Full screen")
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) { Button("Close") { dismiss() } }
                }
        }
    }
}
```

- `NavigationStack(path:)` with value-based `NavigationLink` + `navigationDestination(for:)` keeps navigation as data: push by appending to `path`, pop to root with `path.removeAll()`. Attach `navigationDestination` to a view inside the stack but outside lazy containers (`List` rows, `LazyVStack` children).
- Presented content (`sheet`, `fullScreenCover`) gets no navigation bar of its own - wrap it in a `NavigationStack` for a title and toolbar, and close it with `@Environment(\.dismiss)`.
- `fullScreenCover` has no swipe-to-dismiss; always give it a close button. `.interactiveDismissDisabled()` stops swipe-dismissal of a sheet with unsaved input.
- `confirmationDialog` is the iOS action sheet. With Liquid Glass it anchors to the control that triggered it rather than the bottom edge, so attach it near that control. Use `sheet(item:)` / `presenting:` forms to carry the value being acted on.

## Toolbars

| Placement | Where on iPhone |
|---|---|
| `.topBarLeading` / `.topBarTrailing` | navigation bar edges (replace the deprecated `.navigationBarLeading/Trailing`) |
| `.topBarPinnedTrailing` (iOS 27+) | trailing edge; moves to the overflow menu only while search is active |
| `.bottomBar` | bottom toolbar |
| `.cancellationAction` / `.confirmationAction` | leading/trailing in a sheet's bar, with the right semantics |
| `.keyboard` | bar above the keyboard |

```swift
import SwiftUI

struct EditableHeader: View {
    @State var editing = false

    var body: some View {
        Text("x").toolbar {
            if editing {
                ToolbarItem(placement: .topBarTrailing) { Button("Done") { editing = false } }
            }
            ToolbarItem(placement: .topBarTrailing) { Button("Share", systemImage: "square.and.arrow.up") {} }
                .sharedBackgroundVisibility(.hidden)
        }
    }
}
```

- **Hide a toolbar item with `if`, not by hiding its view.** `ToolbarContent.hidden(_:)` is macOS-only - on iOS it fails with `'hidden' is unavailable in iOS`. Hiding the button inside a `ToolbarItem` leaves an empty glass capsule.
- With Liquid Glass, items sharing a placement are grouped on one glass background. Separate groups with `ToolbarSpacer(.fixed, placement: .topBarTrailing)` (iOS 26+); take one item off the shared background with `.sharedBackgroundVisibility(.hidden)` (iOS 26+). Apple's guidance: icons rather than text for common actions, and do not mix text and icons in one group.

## Forms, text input and opening Settings

```swift
import SwiftUI
import UIKit

struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @State private var serverURL = ""
    @State private var token = ""
    @FocusState private var focused: Field?

    enum Field { case server, token }

    var body: some View {
        NavigationStack {
            Form {
                Section("Server") {
                    TextField("https://example.com", text: $serverURL)
                        .keyboardType(.URL)
                        .textContentType(.URL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .submitLabel(.next)
                        .focused($focused, equals: .server)
                        .onSubmit { focused = .token }
                    SecureField("Token", text: $token)
                        .textContentType(.password)
                        .submitLabel(.done)
                        .focused($focused, equals: .token)
                        .onSubmit(save)
                }
                Section {
                    Button("Open Settings") {
                        if let url = URL(string: UIApplication.openSettingsURLString) { openURL(url) }
                    }
                } footer: {
                    Text("Microphone access is off. Turn it on in Settings.")
                }
            }
            .scrollDismissesKeyboard(.interactively)
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save", action: save).disabled(serverURL.isEmpty)
                }
            }
            .onAppear { focused = .server }
        }
    }

    private func save() { dismiss() }
}
```

- URLs, tokens and codes need `.textInputAutocapitalization(.never)` and `.autocorrectionDisabled()`, or iOS capitalizes and "corrects" them. `textContentType` drives AutoFill (`.password`, `.oneTimeCode`, `.username`, `.URL`); `keyboardType(.URL)` swaps the keyboard.
- `UIApplication.openSettingsURLString` opens this app's page in Settings - the only fix once the user denied a permission (the system never re-prompts). `openNotificationSettingsURLString` goes to its notification settings.
- A `Form` is the grouped settings style on iOS by default; the macOS `.formStyle(.grouped)` advice is unnecessary here.
- Secrets typed here belong in the Keychain, not `@AppStorage` (see keychain.md).

## Liquid Glass

Apps built with the iOS 26+ SDK get Liquid Glass on standard bars, tab bars, sheets, popovers, menus and controls automatically. **Building with the iOS 27 SDK there is no opt-out:** the system ignores `UIDesignRequiresCompatibility` "when you build for iOS 27 or later" ([Apple](https://developer.apple.com/documentation/bundleresources/information-property-list/uidesignrequirescompatibility)). Remove custom backgrounds from navigation bars, tab bars and toolbars - they fight the glass and the scroll-edge effect ([Adopting Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass)). Partial-height sheets are inset with glass and turn opaque at full height.

```swift
import SwiftUI

struct CallControls: View {
    @Namespace private var glass
    @State private var expanded = false

    var body: some View {
        GlassEffectContainer(spacing: 16) {
            HStack(spacing: 16) {
                Button("Mute", systemImage: "mic.slash.fill") {}
                    .labelStyle(.iconOnly)
                    .frame(width: 64, height: 64)
                    .glassEffect(.regular.interactive(), in: .circle)
                    .glassEffectID("mute", in: glass)
                if expanded {
                    Button("Speaker", systemImage: "speaker.wave.2.fill") {}
                        .labelStyle(.iconOnly)
                        .frame(width: 64, height: 64)
                        .glassEffect(.regular.tint(.blue).interactive(), in: .circle)
                        .glassEffectID("speaker", in: glass)
                }
            }
        }
        .onTapGesture { withAnimation(.smooth) { expanded.toggle() } }
    }
}

struct GlassButtons: View {
    var body: some View {
        HStack {
            Button("Cancel") {}.buttonStyle(.glass)
            Button("Call") {}.buttonStyle(.glassProminent)
        }
    }
}

struct MainTabs: View {
    var body: some View {
        TabView {
            Tab("Calls", systemImage: "phone") {
                NavigationStack {
                    List(0..<50, id: \.self) { Text("Call \($0)") }
                        .navigationTitle("Calls")
                        .toolbar {
                            ToolbarItem(placement: .topBarTrailing) { Button("Edit") {} }
                            ToolbarSpacer(.fixed, placement: .topBarTrailing)
                            ToolbarItem(placement: .topBarTrailing) { Button("Add", systemImage: "plus") {} }
                        }
                }
            }
            Tab("Settings", systemImage: "gearshape") { Text("Settings") }
            Tab(role: .search) { Text("Search") }
        }
        .tabBarMinimizeBehavior(.onScrollDown)
        .tabViewBottomAccessory {
            Label("On a call", systemImage: "waveform")
        }
    }
}
```

- `glassEffect(_:in:)` (iOS 26+) takes a `Glass` (`.regular`, `.clear`, `.identity`, plus `.tint(_:)` and `.interactive()`) and a shape (default capsule). Prefer `.buttonStyle(.glass)` / `.glassProminent` for buttons over hand-applied glass.
- Wrap neighbouring custom glass in one `GlassEffectContainer(spacing:)`: Apple recommends it for rendering performance, and it blends and morphs shapes within `spacing`. `glassEffectID(_:in:)` with a `@Namespace` morphs shapes as they appear and disappear.
- Use glass sparingly - for the few functional controls floating over content, not for content itself.
- Tab bar: `Tab(role: .search)` is placed apart at the trailing end; `.tabBarMinimizeBehavior(.onScrollDown)` (iOS 26+) shrinks the bar while scrolling; `.tabViewBottomAccessory` (iOS 26+) adds a glass accessory above it (a now-playing or in-call bar). On iOS 27+ `toolbarMinimizationBehavior(_:for:)` generalizes minimization to any bar, e.g. `.toolbarMinimizationBehavior(.onScrollDown, for: .tabBar)`.

## UIKit bridge

```swift
import AVKit
import SwiftUI

/// The system audio route picker (speaker, AirPods, car) as a SwiftUI view.
struct RoutePicker: UIViewRepresentable {
    var tint: Color = .accentColor

    func makeUIView(context: Context) -> AVRoutePickerView {
        let view = AVRoutePickerView()
        view.prioritizesVideoDevices = false
        return view
    }

    func updateUIView(_ view: AVRoutePickerView, context: Context) {
        view.activeTintColor = UIColor(tint)
    }
}

/// A UIKit control whose delegate feeds back into SwiftUI state through a Coordinator.
struct SearchBar: UIViewRepresentable {
    @Binding var text: String

    func makeCoordinator() -> Coordinator { Coordinator(text: $text) }

    func makeUIView(context: Context) -> UISearchBar {
        let bar = UISearchBar()
        bar.delegate = context.coordinator
        return bar
    }

    func updateUIView(_ bar: UISearchBar, context: Context) {
        if bar.text != text { bar.text = text }
    }

    final class Coordinator: NSObject, UISearchBarDelegate {
        @Binding var text: String
        init(text: Binding<String>) { _text = text }

        func searchBar(_ searchBar: UISearchBar, textDidChange searchText: String) {
            text = searchText
        }
    }
}
```

- Create the view once in `makeUIView`; `updateUIView` runs on every SwiftUI update, so compare before writing to avoid fighting the delegate's own updates.
- Delegates and target-actions go on the `Coordinator`, which lives as long as the view. `UIViewControllerRepresentable` is the same shape for whole controllers (pickers, mail compose). The macOS twin is in macos-appkit-interop.md.

## Background refresh

```swift
import BackgroundTasks
import SwiftUI

struct RefreshingApp: App {
    var body: some Scene {
        WindowGroup { Text("Hello") }
            .backgroundTask(.appRefresh("com.example.app.refresh")) {
                await Self.scheduleRefresh()
                // Fetch here; the system suspends the app again when this returns.
            }
    }

    static func scheduleRefresh() {
        let request = BGAppRefreshTaskRequest(identifier: "com.example.app.refresh")
        request.earliestBeginDate = .now.addingTimeInterval(15 * 60)
        try? BGTaskScheduler.shared.submit(request)
    }
}
```

- Requires `UIBackgroundModes: [fetch]` and the identifier in `BGTaskSchedulerPermittedIdentifiers` in Info.plist. Submit the first request yourself (e.g. on `.background`), and resubmit from the handler - each request runs at most once, at a time the system picks.
- `earliestBeginDate` is a floor, not a schedule. Do not use refresh tasks for anything time-critical.
- A user-initiated job that must finish after the user leaves (export, upload) is `BGContinuedProcessingTaskRequest` (iOS 26+), submitted from the foreground in response to a user action; the system shows it with the request's `title` and `subtitle`.
- Keeping a call or audio alive is not a background task - that is background modes plus CallKit / `AVAudioSession` (see ios-audio-and-callkit.md).

## Building with the iOS 27 SDK

These hit when you rebuild with Xcode 27, before adopting any new API (same list for macOS in macos-swiftui.md, from the [iOS 27 release notes](https://developer.apple.com/documentation/ios-ipados-release-notes/ios-ipados-27-release-notes)):

- **`@State` is a macro.** The initial-value expression is now evaluated once rather than on every view re-instantiation (back-deploys to iOS 17-aligned OSes). Assigning an `@State` property in `init` when its declaration also has an initial value never had an effect, and now can fail to compile with a misleading error:

```swift
struct CounterView: View {
    var name: String
    @State private var counter: Int   // no initial value when init assigns it
    init(name: String) {
        self.counter = 42
        self.name = name
    }
    var body: some View { Text("\(name): \(counter)") }
}
```

  With `@State private var counter: Int = 0` the same `init` fails with `variable 'self.name' used before being initialized` - fix it by dropping the declaration's initial value, not by reordering. The macro also removes the private memberwise init used from an extension (assign members explicitly), can infer generic arguments less flexibly (spell out the type), and cannot be combined with other property wrappers or macros. **`swiftc -typecheck` does not report this** (it is a definite-initialization error, emitted later) - check with `swiftc -emit-sil` or a real build.
- **`#Preview` bodies are `@MainActor`**, so they can call main-actor APIs directly. `#Preview("Name", arguments: [...]) { value in ... }` (iOS 26+) renders one preview per argument.
- **Sheets and popovers reset control environment values:** `controlSize`, `buttonSizing`, `buttonRepeatBehavior`, `menuIndicatorVisibility` and `ButtonBorderShape` revert to defaults inside presented content - re-apply them inside the sheet.
- **`TabView` selection must name a visible tab**; setting it to a hidden or unavailable tab can crash.
- Status bar: `.toolbarVisibility(.hidden, for: .statusBar)` hides it and `.toolbarColorScheme(_:for: .statusBar)` sets its scheme.
- Liquid Glass opt-out is gone (above).
