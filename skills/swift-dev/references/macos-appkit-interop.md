# macOS AppKit Interop

Bridging SwiftUI and AppKit: representables, hosting SwiftUI views and scenes in AppKit, AppKit Liquid Glass, menus, pasteboard, workspace and panels, window access, and floating `NSPanel` HUDs.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every block typechecked with `swiftc -typecheck -swift-version 6` against the macOS 27.0 SDK, with and without `-default-isolation MainActor`; symbols checked in `SwiftUI.swiftinterface`, `AppKit.swiftinterface` and the AppKit headers; behavior notes checked against the macOS 27 / 27.2 release notes and Apple's [AppKit updates](https://developer.apple.com/documentation/updates/appkit).

## Contents
- NSViewRepresentable
- NSViewControllerRepresentable and NSGestureRecognizerRepresentable
- Hosting SwiftUI in AppKit (views, scenes, menus)
- Liquid Glass in AppKit
- Menu item images (macOS 27)
- Pasteboard and pasteboard privacy
- NSWorkspace and open/save panels
- Reaching the NSWindow
- NSPanel floating HUD

## NSViewRepresentable

```swift
struct ColorWellView: NSViewRepresentable {
    @Binding var color: Color

    func makeNSView(context: Context) -> NSColorWell {
        let well = NSColorWell()
        well.target = context.coordinator
        well.action = #selector(Coordinator.colorChanged(_:))
        return well
    }

    func updateNSView(_ well: NSColorWell, context: Context) {
        context.coordinator.color = $color
        well.color = NSColor(color)
    }

    func makeCoordinator() -> Coordinator { Coordinator(color: $color) }

    @MainActor final class Coordinator: NSObject {
        var color: Binding<Color>
        init(color: Binding<Color>) { self.color = color }

        @objc func colorChanged(_ sender: NSColorWell) {
            color.wrappedValue = Color(nsColor: sender.color)
        }
    }
}
```

```swift
struct CodeTextView: NSViewRepresentable {
    @Binding var text: String

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSTextView.scrollableTextView()
        let textView = scrollView.documentView as! NSTextView
        textView.delegate = context.coordinator
        textView.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        textView.isRichText = false
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        let textView = scrollView.documentView as! NSTextView
        if textView.string != text { textView.string = text }   // avoid resetting the cursor on every keystroke
    }

    func sizeThatFits(_ proposal: ProposedViewSize, nsView: NSScrollView, context: Context) -> CGSize? {
        nil   // take whatever the parent proposes
    }

    static func dismantleNSView(_ scrollView: NSScrollView, coordinator: Coordinator) {
        (scrollView.documentView as? NSTextView)?.delegate = nil
    }

    func makeCoordinator() -> Coordinator { Coordinator(text: $text) }

    @MainActor final class Coordinator: NSObject, NSTextViewDelegate {
        var text: Binding<String>
        init(text: Binding<String>) { self.text = text }

        func textDidChange(_ notification: Notification) {
            guard let textView = notification.object as? NSTextView else { return }
            text.wrappedValue = textView.string
        }
    }
}
```

Rules:
- `makeNSView` runs once, `updateNSView` on every relevant state change - guard writes (`if view.value != newValue`) or you fight the user's edits and loop.
- The representable struct is recreated constantly; the coordinator persists. Refresh the coordinator's bindings/closures in `updateNSView`, or it keeps calling the first ones.
- Mark coordinators `@MainActor` unless the module uses default MainActor isolation: `@objc` target-action methods are not inferred main-actor-isolated and touching AppKit there warns under Swift 6.
- `sizeThatFits(_:nsView:context:)` overrides sizing; returning `nil` falls back to the view's intrinsic size behavior.
- Below macOS 26, a SwiftUI `WebView` does not exist - wrap `WKWebView` this way; on 26+ prefer `WebView` (see macos-swiftui.md).

## NSViewControllerRepresentable and NSGestureRecognizerRepresentable

```swift
struct PDFPreview: NSViewControllerRepresentable {
    let document: PDFDocument

    func makeNSViewController(context: Context) -> NSViewController {
        let controller = NSViewController()
        let pdfView = PDFView()
        pdfView.autoScales = true
        controller.view = pdfView
        return controller
    }

    func updateNSViewController(_ controller: NSViewController, context: Context) {
        (controller.view as? PDFView)?.document = document
    }
}
```

`NSGestureRecognizerRepresentable` (macOS 26+) puts an AppKit recognizer into a SwiftUI hierarchy:

```swift
struct MagnifyRecognizer: NSGestureRecognizerRepresentable {
    var onChange: (CGFloat) -> Void

    func makeNSGestureRecognizer(context: Context) -> NSMagnificationGestureRecognizer {
        NSMagnificationGestureRecognizer()
    }

    func handleNSGestureRecognizerAction(_ recognizer: NSMagnificationGestureRecognizer, context: Context) {
        onChange(recognizer.magnification)
    }
}

struct ZoomableCanvas: View {
    @State private var zoom: CGFloat = 1
    var body: some View {
        Rectangle()
            .scaleEffect(1 + zoom)
            .gesture(MagnifyRecognizer { zoom = $0 })
    }
}
```

macOS 27 gesture changes that affect custom `NSGestureRecognizer` subclasses: only the initially hit-tested view hierarchy activates recognizers until all gestures end (opt out per view with `NSView.exclusiveGestureBehavior` or app-wide with the `NSViewGestureRecognizerIsExclusive` Info.plist key); stuck gestures are cancelled automatically; and the base `location(in:)` now returns `.zero` - subclasses must override it.

## Hosting SwiftUI in AppKit (views, scenes, menus)

```swift
final class MainViewController: NSViewController {
    override func loadView() {
        let hosting = NSHostingView(rootView: ContentView())
        hosting.sizingOptions = [.intrinsicContentSize]
        hosting.sceneBridgingOptions = [.title, .toolbars]
        view = hosting
    }
}

@MainActor func makeWindow() -> NSWindow {
    let controller = NSHostingController(rootView: ContentView())
    controller.sizingOptions = [.preferredContentSize]
    let window = NSWindow(contentViewController: controller)
    window.title = "Main"
    window.makeKeyAndOrderFront(nil)
    return window
}
```

- **A bare `NSHostingView` reports no intrinsic size under Auto Layout** and does not surface its content's `navigationTitle` or `.toolbar` to the window. Both are opt-in: `sizingOptions` (macOS 13+) and `sceneBridgingOptions` (macOS 14+). If a hosted view "has no size", `sizingOptions` is almost always the missing piece.
- `NSHostingController` + `NSWindow(contentViewController:)` with `.preferredContentSize` lets the window track the SwiftUI content size.

**Hosting whole scenes (macOS 26+).** An AppKit-lifecycle app can present a real SwiftUI `Settings` or `Window` scene - Cmd+, handling, restoration, single-instance behavior - instead of rebuilding them around a hand-made `NSWindow`:

```swift
@MainActor
final class AppKitDelegate: NSObject, NSApplicationDelegate {
    private let settingsScene = NSHostingSceneRepresentation {
        Settings { SettingsView() }
    }

    func applicationWillFinishLaunching(_ notification: Notification) {
        NSApp.addSceneRepresentation(settingsScene)
    }

    @objc func showSettings(_ sender: Any?) {
        settingsScene.environment.openSettings()
    }
}
```

The representation's `environment` exposes `openSettings`, `openWindow` and the other scene actions for AppKit code.

**SwiftUI menus in AppKit (macOS 14.4+).** `NSHostingMenu` is an `NSMenu` built from SwiftUI buttons, toggles and pickers - use it for context menus and toolbar menus in AppKit views:

```swift
@MainActor func makeContextMenu() -> NSMenu {
    NSHostingMenu(rootView: Group {
        Button("Rename") {}
        Toggle("Pinned", isOn: .constant(true))
    })
}
```

## Liquid Glass in AppKit

With the Xcode 27 SDK Liquid Glass cannot be opted out of (`UIDesignRequiresCompatibility` is ignored; see macos-swiftui.md). AppKit's own pieces (macOS 26+):

| Type | Purpose |
|---|---|
| `NSGlassEffectView` | Embeds `contentView` in glass; `cornerRadius`, `tintColor`, `style`, and `effectIsInteractive` (macOS 27) |
| `NSGlassEffectContainerView` | Merges descendant glass views within `spacing` of each other |
| `NSBackgroundExtensionView` | Extends content to fill its bounds, e.g. under the titlebar, sidebar or inspector |

```swift
@MainActor func makeGlassBadge(content: NSView) -> NSView {
    let glass = NSGlassEffectView()
    glass.contentView = content
    glass.cornerRadius = 12
    glass.tintColor = .controlAccentColor.withAlphaComponent(0.3)

    let container = NSGlassEffectContainerView()
    container.spacing = 8
    container.contentView = glass
    return container
}

@MainActor func keepDenseLayout(_ inspector: NSView) {
    inspector.prefersCompactControlSizeMetrics = true
}
```

`prefersCompactControlSizeMetrics` (macOS 26+) sizes every `NSControl` in the view's subtree with pre-26 compact metrics - the fix when a dense toolbar or inspector tuned for macOS 15 overflows under the larger Liquid Glass controls. With the macOS 27 SDK, `NSTitlebarAccessoryViewController` may draw outside its bounds by default (for shadows and interactive glass).

## Menu item images (macOS 27)

Apps linked on the macOS 27 SDK get both symbol and non-symbol menu item images hidden automatically in menu bar and context menus (on the 26 SDK only symbol images are hidden). Settings, Share and Print keep default images. When an image must stay - for example an item that is only an icon - opt in per item:

```swift
@MainActor func makeShareItem() -> NSMenuItem {
    let item = NSMenuItem(title: "Share Project", action: nil, keyEquivalent: "")
    item.image = NSImage(systemSymbolName: "square.and.arrow.up", accessibilityDescription: nil)
    item.preferredImageVisibility = .visible
    return item
}
```

`preferredImageVisibility` (`.automatic`, `.visible`, `.hidden`) is macOS 27+; xib menu items honor the "macOS 26.0 only" checkbox in the inspector. The SwiftUI equivalent is `.labelStyle(.titleAndIcon)`.

## Pasteboard and pasteboard privacy

```swift
@MainActor func copyToPasteboard(_ text: String) {
    NSPasteboard.general.clearContents()
    NSPasteboard.general.setString(text, forType: .string)
}

@MainActor func pasteFromUserAction() -> String? {
    NSPasteboard.general.string(forType: .string)
}

@MainActor func pasteboardHasLink() async -> Bool {
    let found = try? await NSPasteboard.general.detectedPatterns(for: [\.probableWebURL])
    return found?.contains(\.probableWebURL) ?? false
}
```

Apple is moving macOS to iOS-style pasteboard privacy: reading the **general** pasteboard programmatically, outside a paste-related user action, shows an alert ([AppKit updates](https://developer.apple.com/documentation/updates/appkit)). Design for it now:
- Read contents only in response to an explicit paste (menu item, Cmd+V). Responder-chain paste into `NSTextView` and friends is unaffected; clipboard managers and pasteboard pollers are what break.
- To enable a Paste item or offer "open copied link", inspect without reading: `detectedPatterns(for:)` / `detectedValues(for:)` / `detectedMetadata(for:)` (macOS 15.4+, async) do not trigger the alert.
- `NSPasteboard.accessBehavior` (macOS 15.4+) reports the user's per-app setting: `.default`, `.ask`, `.alwaysAllow`, `.alwaysDeny`.
- The `EnablePasteboardPrivacyDeveloperPreview` user default that simulated the alert was removed in macOS 27.2.

Unverified: whether macOS 27.x shows the alert to users by default - neither the macOS 27 nor 27.2 release notes say so.

## NSWorkspace and open/save panels

```swift
@MainActor func workspaceExamples(fileURL: URL) {
    NSWorkspace.shared.open(fileURL)
    NSWorkspace.shared.activateFileViewerSelecting([fileURL])
}

@MainActor func chooseFile() async -> URL? {
    let panel = NSOpenPanel()
    panel.allowedContentTypes = [.json, .plainText]
    panel.allowsMultipleSelection = false
    return await panel.begin() == .OK ? panel.url : nil
}

@MainActor func chooseSaveLocation() async -> URL? {
    let panel = NSSavePanel()
    panel.allowedContentTypes = [.json]
    panel.nameFieldStringValue = "export.json"
    return await panel.begin() == .OK ? panel.url : nil
}
```

With the macOS 27 SDK, setting `allowedContentTypes` on `NSOpenPanel` also updates `canChooseFiles` / `canChooseDirectories` to match whether the types are file or directory types. In SwiftUI prefer `fileImporter` / `fileExporter`. Panel URLs are security-scoped in sandboxed apps - persist them as bookmarks (see macos-system-integration.md).

## Reaching the NSWindow

SwiftUI scene modifiers cover most window configuration (see macos-app-lifecycle.md). For the rest, get the hosting window when the view is attached:

```swift
struct WindowAccessor: NSViewRepresentable {
    let configure: (NSWindow) -> Void

    func makeNSView(context: Context) -> WindowObservingView {
        WindowObservingView(configure: configure)
    }

    func updateNSView(_ nsView: WindowObservingView, context: Context) {}

    final class WindowObservingView: NSView {
        let configure: (NSWindow) -> Void
        init(configure: @escaping (NSWindow) -> Void) {
            self.configure = configure
            super.init(frame: .zero)
        }
        required init?(coder: NSCoder) { fatalError() }

        override func viewDidMoveToWindow() {
            super.viewDidMoveToWindow()
            if let window { configure(window) }
        }
    }
}

struct TransparentTitlebarView: View {
    var body: some View {
        ContentView()
            .background(WindowAccessor { window in
                window.titlebarAppearsTransparent = true
                window.isMovableByWindowBackground = true
            })
    }
}
```

`viewDidMoveToWindow` is reliable; the common `DispatchQueue.main.async { view.window }` trick in `makeNSView` races window attachment and sometimes sees `nil`.

## NSPanel floating HUD

For toasts, recording indicators and floating widgets that must sit above every app, including full-screen ones:

```swift
final class HUDPanel: NSPanel {
    init(content: some View) {
        super.init(contentRect: .zero,
                   styleMask: [.nonactivatingPanel, .fullSizeContentView, .borderless],
                   backing: .buffered, defer: true)
        level = .floating
        isOpaque = false
        backgroundColor = .clear
        hasShadow = true
        hidesOnDeactivate = false
        isReleasedWhenClosed = false
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .transient]

        let hosting = NSHostingView(rootView: content.fixedSize())
        contentView = hosting
        setContentSize(hosting.fittingSize)
    }

    override var canBecomeKey: Bool { false }

    func show(on screen: NSScreen? = .main, for duration: Duration = .seconds(3)) {
        guard let screen else { return }
        let size = frame.size
        setFrameOrigin(NSPoint(x: screen.visibleFrame.maxX - size.width - 16,
                               y: screen.visibleFrame.maxY - size.height - 16))
        orderFrontRegardless()
        Task { [weak self] in
            try? await Task.sleep(for: duration)
            self?.orderOut(nil)
        }
    }
}
```

Gotchas:
- **`hidesOnDeactivate = false`** - an `NSPanel` hides when its app is not frontmost, which for a menu bar app is almost always.
- **`.nonactivatingPanel`** + `orderFrontRegardless()` shows it without stealing focus from the user's app.
- **`.canJoinAllSpaces` + `.fullScreenAuxiliary`** to appear on every Space and over full-screen apps; `.transient` keeps it out of Mission Control.
- **`.fixedSize()` on the SwiftUI content** - otherwise `fittingSize` compresses it and text truncates.
- **Use `screen.visibleFrame`**, not `frame` - `frame` includes the menu bar and Dock area.
- **`isReleasedWhenClosed = false`** when you hold a strong reference, or closing it leaves a dangling pointer.

An `NSPanel` has no SwiftUI scene environment, so it cannot call `openWindow`. Bridge through a notification observed by a SwiftUI view that is alive when the HUD is clicked:

```swift
extension Notification.Name {
    static let showMainWindow = Notification.Name("ShowMainWindow")
}

struct MenuBarRoot: View {
    @Environment(\.openWindow) private var openWindow

    var body: some View {
        Button("Open") {}
            .onReceive(NotificationCenter.default.publisher(for: .showMainWindow)) { _ in
                openWindow(id: "main")
                NSApp.activate()
            }
    }
}

@MainActor func hudClicked() {
    NotificationCenter.default.post(name: .showMainWindow, object: nil)
}
```

Pick the observer carefully: `MenuBarExtra` content is not built until the user first opens the extra (see macos-app-lifecycle.md), so an observer there can miss early clicks - a long-lived window's root view is safer. For scenes hosted through `NSHostingSceneRepresentation` (macOS 26+), call `representation.environment.openWindow(id:)` directly and skip the notification.
