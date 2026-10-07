# App Intents

App Intents on iOS and macOS: intents, App Shortcuts for Siri/Spotlight/Shortcuts and the iPhone Action Button, run modes, authentication, entities, and Control Center controls.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every block built in a scratch XcodeGen iOS app plus WidgetKit extension (`xcodebuild -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO`, deployment target iOS 26, Swift 6 strict concurrency) and typechecked for `arm64-apple-macos26.0`; the App Shortcut build errors quoted below were reproduced. Declarations and availability read from the 27.0 `AppIntents`/`WidgetKit` `.swiftinterface` files. Not run on a device.

## Contents
- [Intent + App Shortcut](#intent--app-shortcut)
- [Reaching app state from perform()](#reaching-app-state-from-perform)
- [App Shortcut rules](#app-shortcut-rules)
- [supportedModes (replaces openAppWhenRun)](#supportedmodes-replaces-openappwhenrun)
- [authenticationPolicy and execution targets](#authenticationpolicy-and-execution-targets)
- [Action Button, Siri, Spotlight](#action-button-siri-spotlight)
- [Parameters and entities](#parameters-and-entities)
- [Controls and widgets](#controls-and-widgets)
- [macOS vs iOS](#macos-vs-ios)

## Intent + App Shortcut

The hey-dan pattern: an App Shortcut that starts a call, assignable to the Action Button.

```swift
struct StartConversationIntent: AppIntent {
    static let title: LocalizedStringResource = "Start conversation"
    static let description = IntentDescription("Calls your agent on its voice line.")
    static let supportedModes: IntentModes = .foreground

    @MainActor
    func perform() async throws -> some IntentResult {
        await CallController.shared.start(calling: "Dan")
        return .result()
    }
}

struct AppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: StartConversationIntent(),
            phrases: ["Talk to \(.applicationName)", "Start a conversation with \(.applicationName)"],
            shortTitle: "Start conversation",
            systemImageName: "waveform"
        )
    }
}
```

- **Stored static properties must be `let`** (`title`, `description`, `supportedModes`); computed `static var` is fine. Under Swift 6 `static var title: LocalizedStringResource = "..."` is an error: "static property 'title' is not concurrency-safe because it is nonisolated global shared mutable state". Older samples (and the pre-Swift-6 docs) use `static var`.
- An `AppShortcut` needs no registration: the build extracts it into `Metadata.appintents`, and it is live as soon as the app is installed.
- The intent type must be in the app target (or a framework/package it links); the build processes App Intents per target.

## Reaching app state from perform()

`AppIntent` is a `Sendable` struct the system creates with `init()`; it cannot hold references to your objects. Default: mark `perform()` `@MainActor` and call the app's `@MainActor` singleton controller, as above (`CallController.shared` is the `@Observable` controller from ios-audio-and-callkit.md - see architecture.md for the pattern). The intent and the UI then drive one object, so a call started from Siri shows up in the open UI.

Escape hatch when the intent must also compile into an extension that cannot see the controller (a control or widget): put the intent behind a protocol and inject it with `@Dependency`.

```swift
protocol CallStarting: Sendable {
    @MainActor func startCall() async
}

struct StartCallIntent: AppIntent {
    static let title: LocalizedStringResource = "Start Call"
    static let supportedModes: IntentModes = .foreground
    @available(iOS 27.0, macOS 27.0, *)
    static var allowedExecutionTargets: IntentExecutionTargets { .main } // never in the widget extension

    @Dependency private var calls: any CallStarting

    func perform() async throws -> some IntentResult {
        await calls.startCall()
        return .result()
    }
}

// App target, in the controller's own file (Sendable conformances must live there):
//   extension CallController: CallStarting { func startCall() async { await start(calling: "Dan") } }
// and as early as App.init():
//   let calls = CallController.shared
//   AppDependencyManager.shared.add(dependency: calls as any CallStarting)
```

## App Shortcut rules

- **Every phrase must contain `\(.applicationName)`.** Not a style rule: the build fails in `ExtractAppIntentsMetadata` with `error: Every App Shortcut utterance should contain '${applicationName}'`. The token also matches the app-name synonyms you configure.
- **At most 10 App Shortcuts per app**, enforced at build time: `error: Found 11 App Shortcuts, but each app may have at most 10`.
- `shortTitle` and `systemImageName` are what Spotlight and the Shortcuts app tile show. `shortcutTileColor` sets the tile color; `negativePhrases` (iOS 17 / macOS 14) lists phrases that must not trigger it.
- A phrase can name a parameter whose values form a closed set (`AppEnum`, or an `AppEntity` whose query suggests entities); call `updateAppShortcutParameters()` whenever that set changes so Siri re-reads it. Uses `ProjectEntity` from [Parameters and entities](#parameters-and-entities):

```swift
struct OpenProjectIntent: OpenIntent {
    static let title: LocalizedStringResource = "Open Project"
    @Parameter(title: "Project") var target: ProjectEntity

    @MainActor
    func perform() async throws -> some IntentResult { .result() }
}

// In appShortcuts:
//   AppShortcut(intent: OpenProjectIntent(), phrases: ["Open \(\.$target) in \(.applicationName)"],
//               shortTitle: "Open Project", systemImageName: "folder")
// and whenever the project list changes:
//   AppShortcuts.updateAppShortcutParameters()
```

- `isDiscoverable` must stay `true` (the default) for intents used in App Shortcuts.
- In-app discovery: `SiriTipView` shows the phrase for an intent; `ShortcutsLink` opens your app's page in Shortcuts.

## supportedModes (replaces openAppWhenRun)

`static var supportedModes: IntentModes` is iOS 26 / macOS 26+ (`@available(anyAppleOS 26.0, *)`). The SDK deprecates both old mechanisms:

```swift
@available(iOS, deprecated: 26.0, message: "Please provide 'supportedModes' instead")
static var openAppWhenRun: Swift::Bool { get }

@available(iOS, introduced: 16.4, deprecated: 26.0, message: "Please include '.foreground(.dynamic)' in the 'supportedModes' of your app intent instead")
public protocol ForegroundContinuableIntent : AppIntents::AppIntent
```

(Same attributes for macOS 13.3/26.0, watchOS, tvOS, visionOS. Implementing the deprecated `openAppWhenRun` produces no warning - only uses of it do - so grep for it.)

`IntentModes` is an `OptionSet`; the 27.0 SDK declares exactly these members:

| Value | Meaning (Apple's [supportedModes](https://developer.apple.com/documentation/appintents/appintent/supportedmodes) docs) |
|---|---|
| `.background` | run entirely in the background |
| `.foreground` | run in a foreground process |
| `.foreground(.immediate)` | bring the app forward before `perform()` runs |
| `.foreground(.dynamic)` | start in the background, optionally move forward |
| `.foreground(.deferred)` | start in the background, move forward before the action completes |
| `[.background, .foreground]` | foreground when possible, background allowed |
| `[.background, .foreground(.dynamic)]` | either, prefer background |
| `[.background, .foreground(.deferred)]` | start in background, finish in foreground |

```swift
struct OpenInboxIntent: AppIntent {
    static let title: LocalizedStringResource = "Open Inbox"
    // Start in the background, come forward only when perform() decides it must.
    static let supportedModes: IntentModes = [.background, .foreground(.dynamic)]
    static let authenticationPolicy: IntentAuthenticationPolicy = .requiresAuthentication

    func perform() async throws -> some IntentResult {
        if systemContext.currentMode.canContinueInForeground {
            try await continueInForeground("Open the inbox?")
        }
        return .result()
    }
}
```

- At runtime `systemContext.currentMode` (`IntentModes.Current`: `.background`/`.foreground`, plus `canContinueInForeground`) tells `perform()` where it is running. `continueInForeground(_:alwaysConfirm:)` (iOS/macOS 26) replaces `requestToContinueInForeground`.
- A deployment target below 26 cannot rely on `supportedModes` alone; there you still need `openAppWhenRun` (and accept the deprecation once you raise the target).
- For an intent that only opens an item in the UI, adopt `OpenIntent` instead: "The system automatically brings your app to the foreground to run this app intent."

## authenticationPolicy and execution targets

`static var authenticationPolicy: IntentAuthenticationPolicy` (iOS 16 / macOS 13+). Cases, from Apple's docs:

| Case | Behavior |
|---|---|
| `.alwaysAllowed` (default) | runs "at any time, including when the device is locked" |
| `.requiresAuthentication` | some device must be unlocked; starting on an unlocked Apple Watch is enough even if the iPhone is locked |
| `.requiresLocalDeviceAuthentication` | the device running the intent must be unlocked, "even if the request originated from an already authenticated Apple Watch or remote device" - use it when the intent reads data-protected files |

An `.alwaysAllowed` intent that reads a Keychain item while locked still needs that item stored `kSecAttrAccessibleAfterFirstUnlock` (keychain.md).

`static var allowedExecutionTargets: IntentExecutionTargets` is new in iOS 27 / macOS 27: `.default` (any available target), `.main`, `.appIntentsExtension`, `.widgetKitExtension`. Use it when an intent compiled into several targets must run in a specific one:

```swift
@available(iOS 27.0, macOS 27.0, *)
struct AddBookmarkIntent: AppIntent {
    static let title: LocalizedStringResource = "Add Bookmark"
    static var allowedExecutionTargets: IntentExecutionTargets { [.main, .appIntentsExtension] }

    func perform() async throws -> some IntentResult { .result() }
}
```

An `@available(iOS 27.0, macOS 27.0, *)` witness compiles fine on an iOS 26 deployment target (see `StartCallIntent` above).

## Action Button, Siri, Spotlight

- **Action Button** (iPhone 15 Pro/Pro Max and every iPhone since, including 16e, 17e and Air - not iPhone 15/15 Plus or earlier): the user assigns it in Settings > Action Button > Shortcut > your app's App Shortcut. Settings > Action Button > Controls accepts a `ControlWidget` (below). Your app cannot assign it programmatically; the button only offers what your App Shortcuts or controls expose. ([Apple Support](https://support.apple.com/guide/iphone/use-and-customize-the-action-button-iphe89d61d66/ios))
- **Siri**: speaking a phrase runs the App Shortcut; any intent is also runnable by name in Shortcuts.
- **Spotlight**: App Shortcuts appear in Spotlight results. To index app data, conform entities to `IndexedEntity` (iOS 18 / macOS 15) and mark attributes with `@Property(indexingKey:)` / `@ComputedProperty(indexingKey:)` ([Making app entities available in Spotlight](https://developer.apple.com/documentation/appintents/making-app-entities-available-in-spotlight)).
- `AudioRecordingIntent` (iOS 18 / macOS 15) tells the system an intent records audio; on iOS "you must start a Live Activity when you begin the audio recording ... If you don't start a Live Activity, the audio recording stops." A CallKit call already has system call UI, so a call intent is a plain `AppIntent`.

## Parameters and entities

```swift
enum ProjectTemplate: String, AppEnum {
    case blank, kanban

    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Template"
    static let caseDisplayRepresentations: [ProjectTemplate: DisplayRepresentation] = [
        .blank: "Blank",
        .kanban: "Kanban",
    ]
}

struct ProjectEntity: AppEntity {
    let id: UUID
    let name: String

    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Project"
    static let defaultQuery = ProjectQuery()
    var displayRepresentation: DisplayRepresentation { DisplayRepresentation(title: "\(name)") }
}

struct ProjectQuery: EntityQuery {
    @MainActor
    func entities(for identifiers: [ProjectEntity.ID]) async throws -> [ProjectEntity] {
        ProjectStore.shared.projects.filter { identifiers.contains($0.id) }
    }

    @MainActor
    func suggestedEntities() async throws -> [ProjectEntity] { ProjectStore.shared.projects }
}

struct CreateProjectIntent: AppIntent {
    static let title: LocalizedStringResource = "Create Project"
    static let supportedModes: IntentModes = .background

    @Parameter(title: "Name") var name: String
    @Parameter(title: "Template", default: .blank) var template: ProjectTemplate

    static var parameterSummary: some ParameterSummary {
        Summary("Create \(\.$name) from \(\.$template)")
    }

    @MainActor
    func perform() async throws -> some IntentResult & ReturnsValue<ProjectEntity> {
        .result(value: ProjectStore.shared.create(name: name, template: template))
    }
}
```

| Type | Role |
|---|---|
| `AppEnum` | fixed choices, shown as a picker; phrases can expand over its cases |
| `AppEntity` | an addressable model object: `id`, `displayRepresentation`, `defaultQuery` |
| `EntityQuery` | how the system resolves entities: `entities(for:)` by id, `suggestedEntities()` for pickers; `EntityStringQuery` adds text search |

- Return values with `ReturnsValue<T>` so Shortcuts can chain the result into the next action.
- `SnippetIntent` (iOS/macOS 26) renders interactive SwiftUI as the result; the system calls its `perform()` again after each button/toggle in the snippet, so re-fetch state every time.

## Controls and widgets

A control (iOS 18+, macOS 26+, watchOS 26+; unavailable on tvOS/visionOS) is a button or toggle in Control Center, on the Lock Screen, or on the Action Button. It lives in a WidgetKit extension and runs an App Intent.

```swift
struct StartCallControl: ControlWidget {
    var body: some ControlWidgetConfiguration {
        StaticControlConfiguration(kind: "com.example.Voice.start-call") {
            ControlWidgetButton(action: StartCallIntent()) {
                Label("Start Call", systemImage: "phone.fill")
            }
        }
        .displayName("Start Call")
        .description("Calls your agent.")
    }
}

@main
struct VoiceControls: WidgetBundle {
    var body: some Widget {
        StartCallControl()
    }
}
```

- Building blocks: `ControlWidget`, `StaticControlConfiguration` / `AppIntentControlConfiguration` (user-configurable via a `ControlConfigurationIntent`), `ControlWidgetButton`, `ControlWidgetToggle` (with a `ControlValueProvider` for state).
- The intent file must compile into both the app and the extension. Keep app-only types out of it (the `@Dependency` pattern above) and pin execution to the app with `allowedExecutionTargets` on iOS 27.
- Unverified: on iOS 26, which process performs a `.foreground` intent fired from a control - check on a device before relying on the app's state there.
- Widgets: WidgetKit (iOS 14 / macOS 11+) - home screen, Lock Screen, macOS desktop and Notification Center. `WidgetAccentedRenderingMode` (iOS 18 / macOS 15) controls image tinting in accented rendering; `WidgetPushHandler` (iOS/macOS 26) drives push-based reloads. Interactive widget buttons also run App Intents.

## macOS vs iOS

| | iOS | macOS |
|---|---|---|
| App Intents, App Shortcuts, Siri, Spotlight | iOS 16+ | macOS 13+ |
| `supportedModes`, `continueInForeground` | 26+ | 26+ |
| `allowedExecutionTargets` | 27+ | 27+ |
| Controls (`ControlWidget`) | 18+ | 26+ |
| Action Button | iPhone 15 Pro and later | none |
| Onscreen-content data sources | `UITableViewAppIntentsDataSource`, `UICollectionViewAppIntentsDataSource` (18.4) | `NSTableViewAppIntentsDataSource`, `NSCollectionViewAppIntentsDataSource` (15.4) |

- The onscreen-content data sources let Siri act on the row the user is looking at; they live in the `_AppIntents_UIKit` / `_AppIntents_AppKit` overlays and import with `AppIntents` plus UIKit/AppKit.
- On macOS a control is often a better fit than a `MenuBarExtra` for a single toggle - no menu-bar space, system-managed placement (see macos-app-lifecycle.md for `MenuBarExtra`).
