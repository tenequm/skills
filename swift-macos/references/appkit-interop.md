# AppKit Interop

## Table of Contents
- NSViewRepresentable
- NSViewControllerRepresentable
- Hosting SwiftUI in AppKit
- Common Bridges
- NSWindow Access

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
