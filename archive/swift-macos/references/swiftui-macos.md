# macOS-Specific SwiftUI

## Table of Contents
- Sidebar & Inspectors
- Table View
- Forms & Controls
- Popovers & Sheets
- Search
- Split Views & Layout
- Liquid Glass (macOS 26)
- macOS Modifiers
- Platform Conditionals

## Sidebar

```swift
struct SidebarView: View {
    @Binding var selection: SidebarItem?

    var body: some View {
        List(selection: $selection) {
            Section("Favorites") {
                ForEach(favorites) { item in
                    Label(item.name, systemImage: item.icon)
                        .tag(item)
                        .badge(item.count)
                }
            }

            Section("Collections") {
                ForEach(collections) { collection in
                    Label(collection.name, systemImage: "folder")
                        .tag(SidebarItem.collection(collection.id))
                }
            }
        }
        .listStyle(.sidebar)
        .frame(minWidth: 200)
        .toolbar {
            ToolbarItem {
                Button(action: addCollection) {
                    Label("New Collection", systemImage: "folder.badge.plus")
                }
            }
        }
    }
}
```

## Inspector

```swift
struct ContentView: View {
    @State private var showInspector = false
    @State private var selectedItem: Item?

    var body: some View {
        MainContentView(selection: $selectedItem)
            .inspector(isPresented: $showInspector) {
                if let item = selectedItem {
                    InspectorView(item: item)
                        .inspectorColumnWidth(min: 200, ideal: 300, max: 400)
                }
            }
            .toolbar {
                ToolbarItem {
                    Button {
                        showInspector.toggle()
                    } label: {
                        Label("Inspector", systemImage: "sidebar.trailing")
                    }
                }
            }
    }
}
```

## Table View

Full-featured macOS table with sorting, selection, and context menus:

```swift
struct FileListView: View {
    @State private var files: [FileItem] = []
    @State private var selectedIDs: Set<FileItem.ID> = []
    @State private var sortOrder = [KeyPathComparator(\FileItem.name)]

    var body: some View {
        Table(files, selection: $selectedIDs, sortOrder: $sortOrder) {
            TableColumn("Name", value: \.name) { file in
                Label(file.name, systemImage: file.icon)
            }
            .width(min: 150, ideal: 250)

            TableColumn("Size", value: \.size) { file in
                Text(file.size, format: .byteCount(style: .file))
            }
            .width(80)

            TableColumn("Modified", value: \.modifiedDate) { file in
                Text(file.modifiedDate, format: .dateTime.month().day().hour().minute())
            }
            .width(min: 100, ideal: 150)

            TableColumn("Kind", value: \.kind)
                .width(100)
        }
        .onChange(of: sortOrder) { _, newOrder in
            files.sort(using: newOrder)
        }
        .contextMenu(forSelectionType: FileItem.ID.self) { ids in
            Button("Open") { openFiles(ids) }
            Button("Reveal in Finder") { revealInFinder(ids) }
            Divider()
            Button("Delete", role: .destructive) { deleteFiles(ids) }
        } primaryAction: { ids in
            openFiles(ids)
        }
    }
}
```

## Forms & Controls

macOS-optimized form layout:

```swift
Form {
    Section("General") {
        TextField("Name", text: $name)
        TextField("Description", text: $description, axis: .vertical)
            .lineLimit(3...6)

        Picker("Category", selection: $category) {
            ForEach(Category.allCases) { cat in
                Text(cat.rawValue).tag(cat)
            }
        }
        .pickerStyle(.menu) // .radioGroup, .segmented, .inline

        DatePicker("Due Date", selection: $dueDate, displayedComponents: [.date])
    }

    Section("Options") {
        Toggle("Enable notifications", isOn: $notificationsEnabled)
            .toggleStyle(.checkbox) // macOS default

        Stepper("Priority: \(priority)", value: $priority, in: 1...5)

        Slider(value: $opacity, in: 0...1) {
            Text("Opacity")
        }
    }
}
.formStyle(.grouped) // macOS grouped form style
```

## Popovers

```swift
Button("Info") {
    showPopover = true
}
.popover(isPresented: $showPopover, arrowEdge: .bottom) {
    VStack(alignment: .leading, spacing: 8) {
        Text("Details").font(.headline)
        Text("Additional information here")
        Link("Learn More", destination: helpURL)
    }
    .padding()
    .frame(width: 250)
}
```

## Sheets (macOS)

```swift
.sheet(isPresented: $showingNewProject) {
    NewProjectSheet()
        .frame(minWidth: 400, minHeight: 300)
}

struct NewProjectSheet: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack {
            // Content
            HStack {
                Button("Cancel", role: .cancel) { dismiss() }
                    .keyboardShortcut(.cancelAction)
                Spacer()
                Button("Create") { create(); dismiss() }
                    .keyboardShortcut(.defaultAction)
                    .buttonStyle(.borderedProminent)
            }
        }
        .padding()
    }
}
```

## Search

```swift
struct SearchableListView: View {
    @State private var searchText = ""
    @State private var searchScope: SearchScope = .all

    var body: some View {
        List(filteredItems) { item in
            ItemRow(item: item)
        }
        .searchable(text: $searchText, placement: .toolbar, prompt: "Search items")
        .searchScopes($searchScope) {
            Text("All").tag(SearchScope.all)
            Text("Active").tag(SearchScope.active)
            Text("Archived").tag(SearchScope.archived)
        }
        .searchSuggestions {
            ForEach(suggestions) { suggestion in
                Text(suggestion.text)
                    .searchCompletion(suggestion.text)
            }
        }
    }
}
```

## Split Views

### HSplitView / VSplitView (AppKit-backed)
```swift
HSplitView {
    LeftPanel()
        .frame(minWidth: 200, maxWidth: 400)
    RightPanel()
        .frame(minWidth: 300)
}
```

### NavigationSplitView Visibility
```swift
@State private var columnVisibility: NavigationSplitViewVisibility = .all

NavigationSplitView(columnVisibility: $columnVisibility) {
    SidebarView()
} detail: {
    DetailView()
}
.navigationSplitViewStyle(.balanced) // or .prominentDetail
```

## Liquid Glass (macOS 26)

Apps rebuilt with the Xcode 26 SDK automatically adopt Liquid Glass styling. For custom surfaces and animated shape changes, use the dedicated APIs rather than rolling material backgrounds by hand.

### Basic glass surfaces

```swift
// On any view:
Rectangle()
    .glassEffect()                       // .regular by default
Rectangle().glassEffect(.clear)          // less opaque
Rectangle().glassEffect(.regular.tint(.blue).interactive())

// On buttons:
Button("Primary") { /* ... */ }
    .buttonStyle(.glassProminent)
Button("Secondary") { /* ... */ }
    .buttonStyle(.glass)
```

### Morphing transitions between shapes

`GlassEffectContainer` + `.glassEffectID(_:in:)` with a `@Namespace` produces a continuous glass morph when shapes swap rather than a cross-fade:

```swift
struct MorphingCard: View {
    @Namespace private var glassNamespace
    @State private var expanded = false

    var body: some View {
        GlassEffectContainer(spacing: 8) {
            if expanded {
                RoundedRectangle(cornerRadius: 24)
                    .glassEffect()
                    .glassEffectID("card", in: glassNamespace)
                    .frame(width: 400, height: 280)
            } else {
                Circle()
                    .glassEffect()
                    .glassEffectID("card", in: glassNamespace)
                    .frame(width: 80, height: 80)
            }
        }
        .onTapGesture { withAnimation(.smooth) { expanded.toggle() } }
    }
}
```

### Glass toolbars

Use `ToolbarSpacer` to group glass items so they render as distinct glass surfaces rather than one merged shape. Full signature is `init(_ sizing: SpacerSizing = .flexible, placement: ToolbarItemPlacement = .automatic)` — both parameters default, so the short form works:

```swift
.toolbar {
    ToolbarItem { Button("New") { /* ... */ }.buttonStyle(.glass) }
    ToolbarSpacer(.fixed)            // equivalent to: ToolbarSpacer(.fixed, placement: .automatic)
    ToolbarItem { Button("Share") { /* ... */ }.buttonStyle(.glass) }
}
```

Available macOS 26 / iOS 26+. Docs: https://developer.apple.com/documentation/swiftui/toolbarspacer

### Opting out

Set `UIDesignRequiresCompatibility = YES` (Boolean) in Info.plist to keep the legacy visual style app-wide. It's a temporary migration aid — Apple expects to remove it in a future release; there is no per-view or per-window opt-out. Docs: https://developer.apple.com/documentation/bundleresources/information-property-list/uidesignrequirescompatibility

## macOS Modifiers

```swift
// Window background
.containerBackground(.ultraThinMaterial, for: .window)

// Hover effect
.onHover { isHovered in
    self.isHovered = isHovered
}

// Pointer style (macOS 15+)
.pointerStyle(.link)   // also: .grabIdle, .zoomIn, .horizontalText, etc.
// Pre-macOS-15: there is no built-in SwiftUI cursor modifier; wrap an
// NSViewRepresentable that overrides resetCursorRects. Docs:
// https://developer.apple.com/documentation/swiftui/view/pointerstyle(_:)

// Visual effect (vibrancy)
.background(.ultraThinMaterial)

// Focus state (keyboard navigation)
@FocusState private var isFocused: Bool
TextField("Name", text: $name)
    .focused($isFocused)

// Help tag (tooltip)
.help("Click to save your changes")

// File importer/exporter
.fileImporter(isPresented: $importing, allowedContentTypes: [.json]) { result in
    // handle result
}
.fileExporter(isPresented: $exporting, document: doc, contentType: .json) { result in
    // handle result
}
```

## Platform Conditionals

```swift
// Prefer #if over runtime checks
#if os(macOS)
    .frame(minWidth: 800, minHeight: 600)
    .toolbar { MacToolbar() }
#elseif os(iOS)
    .toolbar { IOSToolbar() }
#endif

// Or use view modifiers
.macOS { view in
    view.frame(minWidth: 800)
}

// Multiplatform extension helper
extension View {
    @ViewBuilder
    func macOS<Content: View>(@ViewBuilder modify: (Self) -> Content) -> some View {
        #if os(macOS)
        modify(self)
        #else
        self
        #endif
    }
}
```

## `@Entry` - custom environment keys in one line

The `EnvironmentKey` + `EnvironmentValues` extension boilerplate is obsolete. `@Entry` generates both:

```swift
extension EnvironmentValues {
    @Entry var captureSession: CaptureSession? = nil
    @Entry var isCompactLayout: Bool = false
}

// Unchanged at the use site
.environment(\.captureSession, session)
@Environment(\.captureSession) private var session
```

Works for `FocusedValues`, `ContainerValues`, and `Transaction` too.

## SwiftUI `WebView` (macOS 26+)

WebKit ships a native SwiftUI view - `NSViewRepresentable` around `WKWebView` is no longer the default answer on macOS 26:

```swift
import WebKit
import SwiftUI

struct DocsView: View {
    @State private var page = WebPage()

    var body: some View {
        WebView(page)
            .onAppear { page.load(URLRequest(url: docsURL)) }
            .navigationTitle(page.title)
    }
}
```

`WebPage` is `@Observable` - `page.title`, `page.url`, `page.isLoading`, and `page.estimatedProgress` drive SwiftUI directly with no KVO bridging. Call `page.callJavaScript(_:)` for evaluation. Keep the `NSViewRepresentable` wrapper only for back-deployment below macOS 26 or when you need `WKWebView` API the SwiftUI type does not expose.

## Rich text editing (macOS 26+)

`TextEditor` binds to `AttributedString`, making formatted text a first-class SwiftUI feature:

```swift
struct NotesEditor: View {
    @State private var text = AttributedString("")
    @State private var selection = AttributedTextSelection()

    var body: some View {
        TextEditor(text: $text, selection: $selection)
            .attributedTextFormattingDefinition(NoteFormatting())
    }
}
```

`AttributedTextFormattingDefinition` constrains which attributes users may apply - use it rather than post-validating, so unsupported formatting never enters the document. The standard Format menu commands work against the selection automatically.

## Window and scene APIs beyond `Window`/`WindowGroup`

| API | Use |
|---|---|
| `UtilityWindow` | Panel-style scene (inspector, tool palette) without dropping to `NSPanel` |
| `SettingsLink` | A button that opens Settings - correct across macOS versions, unlike hand-rolled selectors |
| `defaultLaunchBehavior(.presented / .suppressed)` | Whether a scene opens at launch - the supported way to start windowless |
| `WindowManagerRole` | Declares a scene's role to the window manager |
| `windowResizeAnchor` | **View** modifier (macOS 26+), not a Scene one: `windowResizeAnchor(_ anchor: UnitPoint?)` - the anchor point that stays fixed when the window resizes |
| `WindowDragGesture` | Drag the window from arbitrary content, not just the title bar |

`defaultLaunchBehavior(.suppressed)` is the clean replacement for the `LSUIElement`-plus-close-the-window dance when an app should start with no visible window but is not permanently an accessory.
