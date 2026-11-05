# AppKit Interop

## Table of Contents
- NSViewRepresentable
- NSViewControllerRepresentable
- Hosting SwiftUI in AppKit
- Common Bridges
- NSWindow Access
- NSPanel / Floating HUD

## NSViewRepresentable

Wrap an AppKit view for use in SwiftUI:

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
        well.color = NSColor(color)
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(color: $color)
    }

    class Coordinator: NSObject {
        var color: Binding<Color>

        init(color: Binding<Color>) {
            self.color = color
        }

        @objc func colorChanged(_ sender: NSColorWell) {
            color.wrappedValue = Color(nsColor: sender.color)
        }
    }
}
```

### Lifecycle methods

```swift
func makeNSView(context: Context) -> NSView     // Create (called once)
func updateNSView(_ view: NSView, context: Context)  // Update (called on state changes)
static func dismantleNSView(_ view: NSView, coordinator: Coordinator)  // Cleanup

// sizeThatFits for intrinsic sizing
func sizeThatFits(_ proposal: ProposedViewSize, nsView: NSView, context: Context) -> CGSize? {
    nsView.intrinsicContentSize == .zero ? nil : nsView.intrinsicContentSize
}
```

### Coordinator for delegates

```swift
struct TextViewWrapper: NSViewRepresentable {
    @Binding var text: String

    func makeNSView(context: Context) -> NSScrollView {
        let scrollView = NSTextView.scrollableTextView()
        let textView = scrollView.documentView as! NSTextView
        textView.delegate = context.coordinator
        textView.isEditable = true
        textView.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        let textView = scrollView.documentView as! NSTextView
        if textView.string != text {
            textView.string = text
        }
    }

    func makeCoordinator() -> Coordinator { Coordinator(text: $text) }

    class Coordinator: NSObject, NSTextViewDelegate {
        var text: Binding<String>
        init(text: Binding<String>) { self.text = text }

        func textDidChange(_ notification: Notification) {
            guard let textView = notification.object as? NSTextView else { return }
            text.wrappedValue = textView.string
        }
    }
}
```

## NSViewControllerRepresentable

Wrap entire AppKit view controllers:

```swift
struct PDFViewWrapper: NSViewControllerRepresentable {
    let url: URL

    func makeNSViewController(context: Context) -> PDFViewController {
        PDFViewController(url: url)
    }

    func updateNSViewController(_ controller: PDFViewController, context: Context) {
        controller.loadPDF(from: url)
    }
}
```

## Hosting SwiftUI in AppKit

Embed SwiftUI views inside AppKit apps:

```swift
// In an NSViewController
class MainViewController: NSViewController {
    override func viewDidLoad() {
        super.viewDidLoad()

        let swiftUIView = ContentView()
        let hostingView = NSHostingView(rootView: swiftUIView)
        hostingView.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(hostingView)
        NSLayoutConstraint.activate([
            hostingView.topAnchor.constraint(equalTo: view.topAnchor),
            hostingView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            hostingView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            hostingView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
        ])
    }
}

// As a window
let window = NSWindow(
    contentRect: NSRect(x: 0, y: 0, width: 600, height: 400),
    styleMask: [.titled, .closable, .resizable],
    backing: .buffered,
    defer: false
)
window.contentView = NSHostingView(rootView: ContentView())
window.makeKeyAndOrderFront(nil)
```

### Sizing and window bridging options

A bare `NSHostingView` has **no intrinsic content size** and does not surface its content's title or toolbar to the enclosing window - both are opt-in:

```swift
let hosting = NSHostingView(rootView: ContentView())
hosting.sizingOptions = [.intrinsicContentSize]              // macOS 13+
hosting.sceneBridgingOptions = [.title, .toolbars]           // macOS 14+
```

`NSHostingSizingOptions` controls how the hosting view reflects its content's size into Auto Layout constraints; `NSHostingSceneBridgingOptions` controls which window aspects the SwiftUI content is allowed to manage. If a hosted view "has no size" under Auto Layout, `sizingOptions` is almost always the missing piece.

### Hosting whole SwiftUI scenes (macOS 26+)

Hand-rolling an `NSWindow` for a Settings screen, as above, is the old way. macOS 26 adds `NSHostingSceneRepresentation` - an AppKit type that hosts and presents SwiftUI **scenes** - registered via `NSApplication.addSceneRepresentation(_:)`. An AppKit-lifecycle app can present a SwiftUI `Settings` or `Window` scene with its real scene semantics (Cmd+, handling, restoration, single-instance behaviour) instead of reimplementing them around a manually created window. Prefer it over the manual `NSWindow` recipe when your deployment target allows.

### Gesture recognizers

`NSGestureRecognizerRepresentable` (macOS 26+) is the third `Representable` protocol alongside `NSViewRepresentable` and `NSViewControllerRepresentable`. It wraps an `NSGestureRecognizer` for use in a SwiftUI hierarchy - the way to reuse an existing AppKit recognizer, or to get recognizer behaviour SwiftUI's built-in gestures do not expose.

## Liquid Glass in AppKit (macOS 26+)

The SwiftUI half of Liquid Glass is `.glassEffect()` / `GlassEffectContainer`. AppKit has its own:

| Type | Purpose |
|---|---|
| `NSGlassEffectView` | "A view that embeds its content view in a dynamic glass effect." |
| `NSGlassEffectContainerView` | "A view that efficiently merges descendant glass effect views together when they are within a specified proximity to each other." |
| `NSBackgroundExtensionView` | "A view that extends content to fill its own bounds" - lay it out past the safe area to run content under the titlebar, sidebar, or inspector. |

The single most useful migration escape hatch is on `NSView` itself:

```swift
view.prefersCompactControlSizeMetrics = true
```

> When this property is `YES`, any `NSControl`s in the view or its descendants will be sized with compact metrics compatible with macOS 15.0 and earlier. Defaults to `NO`.

That is the fix when Liquid Glass inflates an existing dense AppKit layout - a toolbar or inspector that was tuned for pre-26 metrics and now overflows. All four symbols are in the macOS 26.5 SDK (`AppKit.framework/Headers/NSGlassEffectView.h`, `NSBackgroundExtensionView.h`, `NSView.h`).

## Common Bridges

### NSPasteboard (Clipboard)
```swift
// Copy
NSPasteboard.general.clearContents()
NSPasteboard.general.setString(text, forType: .string)

// Paste
if let string = NSPasteboard.general.string(forType: .string) {
    // use string
}
```

**Reading the general pasteboard is becoming user-visible.** macOS 15.4 added `NSPasteboard.accessBehavior`, and Apple is rolling out an alert shown when an app programmatically reads the general pasteboard - the `string(forType:)` call above is exactly what triggers it:

> Prepare your app for an upcoming feature in macOS that alerts a person using a device when your app programmatically reads the general pasteboard. ... New `detect` methods in NSPasteboard and NSPasteboardItem make it possible for an app to examine the kinds of data on the pasteboard without actually reading them and showing the alert.

If you only need to know *whether* the pasteboard holds something you can handle - to enable a Paste menu item, say - use `detectedValues(for:)` / `detectedPatterns(for:)` rather than reading. Read the contents only in response to an explicit user paste action, which is what the alert is designed to permit. Test the behaviour ahead of the rollout:

```bash
defaults write <your_app_bundle_id> EnablePasteboardPrivacyDeveloperPreview -bool yes
```

Apps using the standard responder-chain paste (`NSTextView`, `Cmd+V` through first responder) are unaffected; this hits polling and clipboard-manager patterns.

### NSWorkspace
```swift
// Open file in default app
NSWorkspace.shared.open(fileURL)

// Open URL in browser
NSWorkspace.shared.open(URL(string: "https://example.com")!)

// Reveal in Finder
NSWorkspace.shared.activateFileViewerSelecting([fileURL])

// Get running applications
let apps = NSWorkspace.shared.runningApplications
```

### NSSavePanel / NSOpenPanel
```swift
func selectFile() async -> URL? {
    let panel = NSOpenPanel()
    panel.allowedContentTypes = [.json, .plainText]
    panel.allowsMultipleSelection = false
    panel.canChooseDirectories = false

    let result = await panel.begin()
    return result == .OK ? panel.url : nil
}

func saveFile() async -> URL? {
    let panel = NSSavePanel()
    panel.allowedContentTypes = [.json]
    panel.nameFieldStringValue = "export.json"

    let result = await panel.begin()
    return result == .OK ? panel.url : nil
}
```

## NSWindow Access

Access the underlying NSWindow from SwiftUI:

```swift
struct WindowAccessor: NSViewRepresentable {
    let callback: (NSWindow) -> Void

    func makeNSView(context: Context) -> NSView {
        let view = NSView()
        DispatchQueue.main.async {
            if let window = view.window {
                callback(window)
            }
        }
        return view
    }

    func updateNSView(_ nsView: NSView, context: Context) {}
}

// Usage
ContentView()
    .background(WindowAccessor { window in
        window.titlebarAppearsTransparent = true
        window.isOpaque = false
        window.backgroundColor = .clear
    })
```

## NSPanel / Floating HUD

For toast notifications, recording indicators, or floating widgets that must appear above all apps (including full-screen):

```swift
class HUDPanel: NSPanel {
    init(content: some View) {
        super.init(
            contentRect: .zero,
            styleMask: [.nonactivatingPanel, .fullSizeContentView],
            backing: .buffered,
            defer: true
        )
        level = .floating
        isOpaque = false
        backgroundColor = .clear
        hidesOnDeactivate = false // CRITICAL for menu bar apps
        isReleasedWhenClosed = false // Prevent dangling reference
        collectionBehavior = [
            .canJoinAllSpaces,        // Visible on all Spaces/desktops
            .fullScreenAuxiliary,     // Visible over full-screen apps
            .transient,               // Don't appear in Mission Control
        ]

        let hostingView = NSHostingView(rootView: content)
        hostingView.frame.size = hostingView.fittingSize
        contentView = hostingView
        setContentSize(hostingView.fittingSize)
    }

    func show(on screen: NSScreen? = NSScreen.main) {
        guard let screen else { return }
        let size = contentView?.fittingSize ?? .zero
        // Use visibleFrame (not frame) to avoid menu bar overlap
        let origin = NSPoint(
            x: screen.visibleFrame.maxX - size.width - 16,
            y: screen.visibleFrame.maxY - size.height - 16
        )
        setFrameOrigin(origin)
        orderFrontRegardless()

        // Auto-dismiss after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
            self?.close()
        }
    }
}
```

Key gotchas:
- **`hidesOnDeactivate = false`**: Required for menu bar apps - the HUD must stay visible when the app isn't frontmost.
- **Use `screen.visibleFrame`** not `screen.frame` - `frame` includes the menu bar area.
- **`.fixedSize()`** on the SwiftUI content - without it, `fittingSize` compresses the content and text truncates.
- **`isReleasedWhenClosed = false`**: Prevents a dangling reference crash if you hold a strong reference to the panel.

### HUD actions bridging to SwiftUI

NSPanel can't access `@Environment(\.openWindow)`. Use NotificationCenter to bridge:

```swift
// In HUD - post notification on click:
static let showMainWindowNotification = Notification.Name("ShowMainWindow")
NSNotificationCenter.default.post(name: Self.showMainWindowNotification, object: nil)

// In SwiftUI MenuBarExtra content - receive and act:
.onReceive(NotificationCenter.default.publisher(for: HUDPanel.showMainWindowNotification)) { _ in
    openWindow(id: "main")
    NSApp.activate(ignoringOtherApps: true)
}
```
