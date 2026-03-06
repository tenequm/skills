# Architecture Patterns for macOS Apps

## Table of Contents
- SwiftUI + @Observable (Recommended Default)
- MVVM with @Observable
- The Composable Architecture (TCA)
- Dependency Injection
- Project Structure
- Decision Guide

## SwiftUI + @Observable (Simple Apps)

Best for small-medium apps, solo developers, or prototypes. Direct @Observable objects owned by views:

```swift
@Observable
final class ProjectManager {
    var projects: [Project] = []
    var selectedProject: Project?
    var searchText = ""
    private let store: ProjectStore

    var filteredProjects: [Project] {
        searchText.isEmpty ? projects : projects.filter {
            $0.name.localizedStandardContains(searchText)
        }
    }

    init(store: ProjectStore = .shared) {
        self.store = store
    }

    func load() async throws {
        projects = try await store.fetchAll()
    }

    func create(name: String) async throws {
        let project = try await store.create(name: name)
        projects.append(project)
    }

    func delete(_ project: Project) async throws {
        try await store.delete(project)
        projects.removeAll { $0.id == project.id }
    }
}

struct ProjectsView: View {
    @State private var manager = ProjectManager()

    var body: some View {
        NavigationSplitView {
            List(manager.filteredProjects, selection: $manager.selectedProject) { project in
                Text(project.name)
            }
            .searchable(text: $manager.searchText)
            .task { try? await manager.load() }
        } detail: {
            if let project = manager.selectedProject {
                ProjectDetailView(project: project)
            }
        }
    }
}
```

### Environment sharing
```swift
// Root
ContentView()
    .environment(manager)

// Child views
@Environment(ProjectManager.self) private var manager
```

## MVVM with @Observable (Medium Apps)

Separate ViewModel per view for clearer responsibilities:

```swift
@Observable
final class ProjectListViewModel {
    var projects: [Project] = []
    var searchText = ""
    var isLoading = false
    var error: Error?

    private let service: ProjectServiceProtocol

    init(service: ProjectServiceProtocol = ProjectService()) {
        self.service = service
    }

    var filteredProjects: [Project] {
        guard !searchText.isEmpty else { return projects }
        return projects.filter { $0.name.localizedStandardContains(searchText) }
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            projects = try await service.fetchAll()
        } catch {
            self.error = error
        }
    }

    func delete(_ project: Project) async {
        do {
            try await service.delete(project.id)
            projects.removeAll { $0.id == project.id }
        } catch {
            self.error = error
        }
    }
}

struct ProjectListView: View {
    @State private var viewModel: ProjectListViewModel

    init(service: ProjectServiceProtocol = ProjectService()) {
        _viewModel = State(initialValue: ProjectListViewModel(service: service))
    }

    var body: some View {
        List(viewModel.filteredProjects) { project in
            ProjectRow(project: project)
                .swipeActions {
                    Button("Delete", role: .destructive) {
                        Task { await viewModel.delete(project) }
                    }
                }
        }
        .searchable(text: $viewModel.searchText)
        .overlay {
            if viewModel.isLoading { ProgressView() }
        }
        .task { await viewModel.load() }
    }
}
```

## The Composable Architecture (TCA)

For large apps requiring strict testability, modular composition, and predictable state management. Uses `pointfreeco/swift-composable-architecture`:

```swift
import ComposableArchitecture

@Reducer
struct ProjectListFeature {
    @ObservableState
    struct State: Equatable {
        var projects: IdentifiedArrayOf<Project> = []
        var searchText = ""
        var isLoading = false
        @Presents var destination: Destination.State?
    }

    enum Action: BindableAction {
        case binding(BindingAction<State>)
        case onAppear
        case projectsLoaded([Project])
        case deleteProject(Project.ID)
        case destination(PresentationAction<Destination.Action>)
    }

    @Dependency(\.projectClient) var projectClient

    var body: some ReducerOf<Self> {
        BindingReducer()
        Reduce { state, action in
            switch action {
            case .onAppear:
                state.isLoading = true
                return .run { send in
                    let projects = try await projectClient.fetchAll()
                    await send(.projectsLoaded(projects))
                }

            case let .projectsLoaded(projects):
                state.isLoading = false
                state.projects = IdentifiedArray(uniqueElements: projects)
                return .none

            case let .deleteProject(id):
                state.projects.remove(id: id)
                return .run { _ in try await projectClient.delete(id) }

            case .binding, .destination:
                return .none
            }
        }
    }

    @Reducer
    enum Destination {
        case detail(ProjectDetailFeature)
    }
}
```

### Testing TCA
```swift
@Test func loadProjects() async {
    let store = TestStore(initialState: ProjectListFeature.State()) {
        ProjectListFeature()
    } withDependencies: {
        $0.projectClient.fetchAll = { [Project(name: "Test")] }
    }

    await store.send(.onAppear) {
        $0.isLoading = true
    }
    await store.receive(\.projectsLoaded) {
        $0.isLoading = false
        $0.projects = [Project(name: "Test")]
    }
}
```

## Dependency Injection

### Protocol-based (for MVVM)
```swift
protocol ProjectServiceProtocol: Sendable {
    func fetchAll() async throws -> [Project]
    func create(name: String) async throws -> Project
    func delete(_ id: Project.ID) async throws
}

struct ProjectService: ProjectServiceProtocol { /* real impl */ }
struct MockProjectService: ProjectServiceProtocol { /* test impl */ }
```

### TCA Dependencies
```swift
struct ProjectClient: Sendable {
    var fetchAll: @Sendable () async throws -> [Project]
    var create: @Sendable (String) async throws -> Project
    var delete: @Sendable (Project.ID) async throws -> Void
}

extension ProjectClient: DependencyKey {
    static let liveValue = ProjectClient(
        fetchAll: { try await APIClient.shared.get("/projects") },
        create: { try await APIClient.shared.post("/projects", body: ["name": $0]) },
        delete: { try await APIClient.shared.delete("/projects/\($0)") }
    )

    static let testValue = ProjectClient(
        fetchAll: { [] },
        create: { Project(name: $0) },
        delete: { _ in }
    )
}
```

## Project Structure

### Small-medium app
```
MyApp/
├── MyAppApp.swift           # @main, scenes
├── Models/                  # Data models
├── Views/                   # SwiftUI views
├── ViewModels/              # @Observable view models (MVVM only)
├── Services/                # API clients, persistence
└── Utilities/               # Extensions, helpers
```

### Large app (modular)
```
MyApp/
├── App/                     # Entry point, scenes, commands
├── Features/
│   ├── Projects/
│   │   ├── ProjectListView.swift
│   │   ├── ProjectDetailView.swift
│   │   └── ProjectListViewModel.swift
│   ├── Settings/
│   └── Dashboard/
├── Core/
│   ├── Models/
│   ├── Services/
│   └── Networking/
├── Shared/
│   ├── Components/          # Reusable views
│   └── Extensions/
└── Resources/
```

## Decision Guide

| Factor | @Observable | MVVM | TCA |
|--------|-------------|------|-----|
| Team size | 1-2 | 2-5 | 5+ |
| Testability | Basic | Good | Excellent |
| Boilerplate | Minimal | Low | Medium |
| Learning curve | Low | Low | High |
| State predictability | Good | Good | Excellent |
| Navigation handling | SwiftUI native | SwiftUI native | Tree-based |
| Dependencies | Protocol injection | Protocol injection | Built-in DI |

**Rule of thumb**: Start with @Observable. Graduate to MVVM when you need testable view models. Use TCA when you need strict state management and modular composition.
