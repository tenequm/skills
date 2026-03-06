# macOS-Specific SwiftUI

## Table of Contents
- Sidebar & Inspectors
- Table View
- Forms & Controls
- Popovers & Sheets
- Search
- Split Views & Layout
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

## macOS Modifiers

```swift
// Window background
.containerBackground(.ultraThinMaterial, for: .window)

// Hover effect
.onHover { isHovered in
    self.isHovered = isHovered
}

// Cursor
.cursor(.pointingHand)

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
