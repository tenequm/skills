# macOS SwiftUI

Mac-specific SwiftUI: sidebar and inspector layouts, `Table`, menus and commands, forms, popovers and sheets, search, Liquid Glass, Mac modifiers, and the SwiftUI behavior changes that come with building against the macOS 27 SDK.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every block typechecked with `swiftc -typecheck -swift-version 6` against the macOS 27.0 SDK (target macOS 15, 26 or 27 matching each API's minimum), with and without `-default-isolation MainActor`; behavior changes checked against the [macOS 27 release notes](https://developer.apple.com/documentation/macos-release-notes/macos-27-release-notes) and [Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes).

## Contents
- Sidebar and NavigationSplitView
- Inspector
- Table
- Menus and commands
- Forms and controls
- Popovers, sheets, search, split views
- Liquid Glass
- Mac view modifiers
- WebView and rich text (macOS 26+)
- List reordering and drops (macOS 27)
- Building with the macOS 27 SDK: behavior changes

## Sidebar and NavigationSplitView

```swift
struct RootView: View {
    @State private var selection: SidebarItem? = .inbox
    @State private var columnVisibility: NavigationSplitViewVisibility = .all
    let collections: [Collection]

    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            List(selection: $selection) {
                Label("Inbox", systemImage: "tray").tag(SidebarItem.inbox)
                Section("Collections") {
                    ForEach(collections) { collection in
                        Label(collection.name, systemImage: "folder")
                            .badge(collection.count)
                            .tag(SidebarItem.collection(collection.id))
                    }
                }
            }
            .navigationSplitViewColumnWidth(min: 180, ideal: 220)
        } detail: {
            DetailView()
        }
    }
}
```

A `List` in the sidebar column gets the sidebar style automatically. Add `SidebarCommands()` to the scene's `.commands` for the standard View > Show/Hide Sidebar item and shortcut.

## Inspector

```swift
struct EditorScreen: View {
    @State private var showInspector = false
    @State private var selectedItem: Item?

    var body: some View {
        MainContentView(selection: $selectedItem)
            .inspector(isPresented: $showInspector) {
                if let selectedItem { InspectorView(item: selectedItem) }
                else { ContentUnavailableView("No Selection", systemImage: "square.dashed") }
            }
            .inspectorColumnWidth(min: 200, ideal: 280, max: 400)
            .toolbar {
                Button { showInspector.toggle() } label: {
                    Label("Inspector", systemImage: "sidebar.trailing")
                }
            }
    }
}
```

With the macOS 27 SDK a `TabView` inside an inspector looks like one in a sidebar and uses the `.tabs` picker style automatically.

## Table

```swift
nonisolated struct FileItem: Identifiable {
    let id: UUID
    var name: String
    var size: Int
    var modified: Date
}

struct FileTable: View {
    @State private var files: [FileItem] = []
    @State private var selection: Set<FileItem.ID> = []
    @State private var sortOrder = [KeyPathComparator(\FileItem.name)]
    @SceneStorage("FileTableColumns") private var columns = TableColumnCustomization<FileItem>()

    var body: some View {
        Table(files, selection: $selection, sortOrder: $sortOrder, columnCustomization: $columns) {
            TableColumn("Name", value: \.name)
                .width(min: 150, ideal: 250)
                .customizationID("name")
            TableColumn("Size", value: \.size) { file in
                Text(Int64(file.size), format: .byteCount(style: .file))
            }
            .width(80)
            .customizationID("size")
            TableColumn("Modified", value: \.modified) { file in
                Text(file.modified, format: .dateTime.month().day().hour().minute())
            }
            .customizationID("modified")
        }
        .onChange(of: sortOrder, initial: true) { _, order in files.sort(using: order) }
        .contextMenu(forSelectionType: FileItem.ID.self) { ids in
            Button("Open") { open(ids) }
            Divider()
            Button("Delete", role: .destructive) { delete(ids) }
        } primaryAction: { ids in
            open(ids)
        }
    }

    private func open(_ ids: Set<FileItem.ID>) {}
    private func delete(_ ids: Set<FileItem.ID>) { files.removeAll { ids.contains($0.id) } }
}
```

- `Table` only reports the requested order; you sort the data yourself in `onChange(of: sortOrder)`.
- `contextMenu(forSelectionType:)` passes the clicked row set (the selection if the clicked row is selected, otherwise just that row; empty for the background). `primaryAction` is double-click / Return.
- **Under default MainActor isolation, mark the row type `nonisolated`.** `KeyPathComparator` needs a `Sendable` key path, and key paths into a main-actor-isolated struct are not - `[KeyPathComparator(\FileItem.name)]` fails with "type 'KeyPath<FileItem, String>' does not conform to the 'Sendable' protocol" (with or without `@State`).
- `TableColumnCustomization` + `.customizationID` gives user-reorderable, hideable columns; persist it with `@SceneStorage` or `@AppStorage` (it is `Codable`).

## Menus and commands

```swift
extension FocusedValues {
    @Entry var selectedNote: Binding<Item>?
}

struct NoteCommands: Commands {
    @FocusedValue(\.selectedNote) private var note

    var body: some Commands {
        CommandGroup(replacing: .newItem) {
            Button("New Note") {}
                .keyboardShortcut("n")
        }
        CommandMenu("Note") {
            Button("Rename...") { note?.wrappedValue.name += "" }
                .keyboardShortcut("r", modifiers: [.command, .shift])
                .disabled(note == nil)
            Menu("Share") {
                Label("Copy Link", systemImage: "link")
                    .labelStyle(.titleAndIcon)
            }
        }
        SidebarCommands()
        InspectorCommands()
        ToolbarCommands()
    }
}

struct NoteEditor: View {
    @State private var note = Item()
    var body: some View {
        TextField("Name", text: $note.name)
            .focusedSceneValue(\.selectedNote, $note)
    }
}

struct CommandsApp: App {
    var body: some Scene {
        WindowGroup { NoteEditor() }
            .commands { NoteCommands() }
    }
}
```

- Menu bar commands live outside any window, so they reach the active window's state through `@FocusedValue`; publish with `.focusedSceneValue` (whole key window) or `.focusedValue` (focused view only). Disable the item when the value is `nil`.
- `CommandGroup(replacing:/before:/after:)` with placements like `.newItem`, `.saveItem`, `.pasteboard`, `.appSettings`, `.help`.
- **Menu item symbols are hidden by default on macOS 27** (for apps linked on the 26 SDK or later). SwiftUI hides SF Symbol images on menu bar and context menu items in most contexts; Settings, Share and Print keep theirs. Opt an item back in with `.labelStyle(.titleAndIcon)` - Apple's guidance is to do that when the item represents an object or concept, not an action.
- With the 27 SDK a `LabeledContent` inside a `Menu` becomes the item's title plus subtitle.

## Forms and controls

```swift
struct ProjectForm: View {
    @State private var name = ""
    @State private var notes = ""
    @State private var category = Category.a
    @State private var notify = true
    @State private var priority = 3
    @State private var due = Date.now

    var body: some View {
        Form {
            Section("General") {
                TextField("Name", text: $name)
                TextField("Notes", text: $notes, axis: .vertical)
                    .lineLimit(3...6)
                Picker("Category", selection: $category) {
                    ForEach(Category.allCases) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.radioGroup)
                DatePicker("Due", selection: $due, displayedComponents: .date)
            }
            Section("Options") {
                Toggle("Notify me", isOn: $notify)
                Stepper("Priority: \(priority)", value: $priority, in: 1...5)
            }
        }
        .formStyle(.grouped)
    }
}
```

`Toggle` defaults to a checkbox in a Mac form. `.formStyle(.grouped)` gives the System Settings look; the default `.columns` style right-aligns labels.

macOS 27 SDK control changes:

```swift
enum Pane: Hashable { case general, advanced }
struct InspectorTabs: View {
    @State private var pane = Pane.general
    @State private var name = ""

    var body: some View {
        VStack {
            Picker("Pane", selection: $pane) {
                Text("General").tag(Pane.general)
                Text("Advanced").tag(Pane.advanced)
            }
            .pickerStyle(.tabs)
            TextField("Name", text: $name)
                .textFieldStyle(.bordered)
            Menu("Sort") {
                Button { } label: { LabeledContent("Name", value: "A to Z") }
            }
        }
    }
}
```

- `.tabs` picker style (macOS 27+): like `.segmented`, but read by VoiceOver as tabs and drawn distinctly - use it for picking a pane, `.segmented` for picking a value.
- `.textFieldStyle(.bordered)` + `textInputBorderShape(_:)` (27+) replace `.roundedBorder` / `.squareBorder`, which are soft-deprecated (no warning).
- `Slider` no longer uses `NSSlider`, and bordered `Menu` / `Picker` no longer use `NSPopUpButton` - AppKit-level customization of those no longer reaches them.

## Popovers, sheets, search, split views

```swift
struct PresentationExamples: View {
    @State private var showInfo = false
    @State private var showNew = false

    var body: some View {
        HStack {
            Button("Info") { showInfo = true }
                .popover(isPresented: $showInfo, arrowEdge: .bottom) {
                    Text("Details").padding().frame(width: 250)
                }
            Button("New...") { showNew = true }
        }
        .sheet(isPresented: $showNew) {
            NewProjectSheet().frame(minWidth: 400, minHeight: 300)
        }
    }
}

struct NewProjectSheet: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack {
            Spacer()
            HStack {
                Button("Cancel", role: .cancel) { dismiss() }
                    .keyboardShortcut(.cancelAction)
                Spacer()
                Button("Create") { dismiss() }
                    .keyboardShortcut(.defaultAction)
            }
        }
        .padding()
    }
}
```

Mac sheets have no implicit size - give the content a frame or it collapses. With the 27 SDK, `controlSize`, `buttonSizing`, `buttonRepeatBehavior`, `menuIndicatorVisibility` and `ButtonBorderShape` environment values reset to defaults inside sheets and popovers; re-apply them inside the presented content if you relied on inheritance.

```swift
enum SearchScope: Hashable { case all, archived }
struct SearchableList: View {
    @State private var query = ""
    @State private var scope = SearchScope.all
    let items: [Item]

    var body: some View {
        List(items.filter { query.isEmpty || $0.name.localizedStandardContains(query) }) {
            Text($0.name)
        }
        .searchable(text: $query, placement: .toolbar, prompt: "Search")
        .searchScopes($scope) {
            Text("All").tag(SearchScope.all)
            Text("Archived").tag(SearchScope.archived)
        }
    }
}

struct Panels: View {
    var body: some View {
        HSplitView {
            Text("Left").frame(minWidth: 200, maxWidth: 400)
            Text("Right").frame(minWidth: 300)
        }
    }
}
```

`HSplitView` / `VSplitView` are AppKit split views with draggable dividers; use them for editor panes, `NavigationSplitView` for sidebar navigation.

## Liquid Glass

Apps built with the macOS 26 SDK adopt Liquid Glass automatically. **With the Xcode 27 SDK it is mandatory:** the system ignores `UIDesignRequiresCompatibility` when you build for macOS 27 / iOS 27 or later ([Apple docs](https://developer.apple.com/documentation/bundleresources/information-property-list/uidesignrequirescompatibility)). There is no per-view or per-window opt-out. For dense AppKit layouts that grow under the new metrics, see `prefersCompactControlSizeMetrics` in macos-appkit-interop.md.

```swift
struct GlassExamples: View {
    var body: some View {
        VStack {
            Text("Badge").padding().glassEffect()
            Text("Tinted").padding().glassEffect(.regular.tint(.blue).interactive())
            Text("Clear").padding().glassEffect(.clear, in: .rect(cornerRadius: 12))
            Button("Primary") {}.buttonStyle(.glassProminent)
            Button("Secondary") {}.buttonStyle(.glass)
        }
    }
}

struct MorphingCard: View {
    @Namespace private var glass
    @State private var expanded = false

    var body: some View {
        GlassEffectContainer(spacing: 8) {
            if expanded {
                RoundedRectangle(cornerRadius: 24)
                    .frame(width: 400, height: 280)
                    .glassEffect()
                    .glassEffectID("card", in: glass)
            } else {
                Circle()
                    .frame(width: 80, height: 80)
                    .glassEffect()
                    .glassEffectID("card", in: glass)
            }
        }
        .onTapGesture { withAnimation(.smooth) { expanded.toggle() } }
    }
}

struct GlassToolbar: View {
    var body: some View {
        Text("Doc")
            .toolbar {
                ToolbarItem { Button("New", systemImage: "plus") {} }
                ToolbarSpacer(.fixed)
                ToolbarItem { Button("Share", systemImage: "square.and.arrow.up") {} }
            }
    }
}
```

- Apply `.glassEffect()` after layout modifiers (`frame`, `padding`) - it draws behind the view's final shape.
- `GlassEffectContainer` merges nearby glass shapes and is required for `glassEffectID` morphing; glass cannot sample other glass, so overlapping glass outside a container renders wrong.
- `ToolbarSpacer(.fixed)` / `.flexible` splits toolbar items into separate glass groups.

## Mac view modifiers

```swift
struct ModifierExamples: View {
    @State private var isHovered = false
    @FocusState private var nameFocused: Bool
    @State private var name = ""
    @State private var importing = false

    var body: some View {
        VStack {
            TextField("Name", text: $name)
                .focused($nameFocused)
            Text("Link")
                .onHover { isHovered = $0 }
                .pointerStyle(.link)
                .help("Opens the project page")
        }
        .containerBackground(.thinMaterial, for: .window)
        .fileImporter(isPresented: $importing, allowedContentTypes: [.json]) { result in
            if case .success(let url) = result { _ = url }
        }
    }
}

extension EnvironmentValues {
    @Entry var isCompactLayout: Bool = false
}
```

- `pointerStyle(_:)` is macOS 15+; below that, wrap an `NSView` that overrides `resetCursorRects`.
- URLs from `fileImporter` are security-scoped in a sandboxed app - call `startAccessingSecurityScopedResource()` before reading (see macos-system-integration.md).
- `@Entry` replaces hand-written `EnvironmentKey` boilerplate and works in `FocusedValues`, `ContainerValues` and `Transaction` too. With Xcode 27 it warns when the default value is a class instance or closure - the default is re-created on every read, so inject shared objects with `.environment(_:)` instead.

## WebView and rich text (macOS 26+)

```swift
struct DocsView: View {
    @State private var page = WebPage()
    let url: URL

    var body: some View {
        WebView(page)
            .navigationTitle(page.title)
            .task { page.load(URLRequest(url: url)) }
    }
}
```

`WebPage` is `@Observable` (`title`, `url`, `isLoading`, `estimatedProgress`); run JavaScript with `callJavaScript(_:)`. Keep an `NSViewRepresentable` around `WKWebView` only below macOS 26 or for `WKWebView` API the SwiftUI type lacks.

```swift
struct NoteFormatting: AttributedTextFormattingDefinition {
    struct Scope: AttributeScope {
        let font: AttributeScopes.SwiftUIAttributes.FontAttribute
        let foregroundColor: AttributeScopes.SwiftUIAttributes.ForegroundColorAttribute
    }

    var body: some AttributedTextFormattingDefinition<Scope> {
        ValueConstraint(for: \.foregroundColor, values: [nil, .red, .blue], default: nil)
    }
}

struct NotesEditor: View {
    @State private var text = AttributedString("")
    @State private var selection = AttributedTextSelection()

    var body: some View {
        TextEditor(text: $text, selection: $selection)
            .attributedTextFormattingDefinition(NoteFormatting())
    }
}
```

`TextEditor` bound to `AttributedString` is a rich-text editor; the Format menu works against the selection. The formatting definition limits which attributes (and values) can enter the document, so you never post-validate.

## List reordering and drops (macOS 27)

```swift
struct TodoList: View {
    @State private var todos: [TodoItem] = []

    var body: some View {
        List {
            ForEach(todos) { todo in
                Text(todo.title)
            }
            .reorderable()
        }
        .reorderContainer(for: TodoItem.self) { difference in
            let moving = todos.filter { difference.sources.contains($0.id) }
            todos.removeAll { difference.sources.contains($0.id) }
            switch difference.destination.position {
            case .before(let id):
                let index = todos.firstIndex { $0.id == id } ?? todos.endIndex
                todos.insert(contentsOf: moving, at: index)
            case .end:
                todos.append(contentsOf: moving)
            }
        }
    }
}
```

`.reorderable()` (on `ForEach`) plus `.reorderContainer(for:move:)` is the macOS/iOS 27 reordering API; the item's `ID` must be `Sendable`, and you apply the `ReorderDifference` yourself. Use `.onMove` below 27. With the macOS 27 SDK, `List` also accepts drops it used to reject, matching iOS: compatible transfer types dropped into reorderable content, and a `.dropDestination(...)` declared on an individual row. Re-test drop handling after moving to the 27 SDK - rows that previously ignored drops now receive them.

## Building with the macOS 27 SDK: behavior changes

These hit when you rebuild with Xcode 27, before adopting any new API. They apply to iOS too.

- **`@State` is now a macro.** The initial-value expression is evaluated once instead of on every view re-instantiation (back-deploys to iOS 17-aligned OSes). Source breaks: assigning an `@State` property in `init` when it also has an initial value no longer compiles (the assignment never had an effect) - drop the declaration's initial value:

```swift
struct StickerPageView: View {
    @State private var page: StickerPage   // no initial value expression
    let title: String

    init(title: String) {
        self.page = StickerPage(title: title)
        self.title = title
    }

    var body: some View { Text(page.title) }
}
```

  The macro also suppresses the private memberwise initializer used from an extension (assign members explicitly), can infer generic arguments less flexibly (spell out the type), and cannot be combined with other property wrappers or macros.
- **`#Preview` bodies run on the main actor**, so they can call main-actor APIs without concurrency warnings or runtime isolation traps. `#Preview(arguments:)` renders a grid of previews, one per argument.
- **Liquid Glass is mandatory**, menu item symbols are hidden (already on macOS 27 for 26-SDK apps), sheets reset control environment values, and `List` accepts more drops - see the sections above.
- `TextField` honors font/color styling on its `prompt` Text; disabled `.checkbox` toggles are no longer tinted; `defaultAction` buttons no longer stay tinted when disabled.
