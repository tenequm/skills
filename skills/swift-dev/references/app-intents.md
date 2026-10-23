# App Intents

App Intents on iOS and macOS: intents, App Shortcuts for Siri/Spotlight/Shortcuts and the iPhone Action Button, run modes, authentication, entities, and Control Center controls.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every block built in a scratch XcodeGen iOS app plus WidgetKit extension (`xcodebuild -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO`, deployment target iOS 26, Swift 6 strict concurrency) and typechecked for `arm64-apple-macos26.0`; the app target rebuilt as is and with `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`; the App Shortcut build errors quoted below were reproduced. Declarations and availability read from the 27.0 `AppIntents`/`WidgetKit` `.swiftinterface` files. Not run on a device. 2026-10-13: the phone-schema call intent, the Live Activity and the `LongRunningIntent` blocks built in a scratch XcodeGen app with a WidgetKit extension (iOS 26 target, MainActor default isolation), with the two `ExtractAppIntentsMetadata` errors below reproduced; the background-call behavior was observed on a locked iPhone (iOS 27.2) in a shipping voice-call app. 2026-10-24: schema domains and the 27 protocols read from the iOS 27.1 SDK `AppIntents.swiftinterface`; the `LongRunningIntent` block compiled through SIL against it.

## Contents
- [Intent + App Shortcut](#intent--app-shortcut)
- [Reaching app state from perform()](#reaching-app-state-from-perform)
- [App Shortcut rules](#app-shortcut-rules)
- [supportedModes (replaces openAppWhenRun)](#supportedmodes-replaces-openappwhenrun)
- [authenticationPolicy and execution targets](#authenticationpolicy-and-execution-targets)
- [Action Button, Siri, Spotlight](#action-button-siri-spotlight)
- [Starting a call from the background: the phone schema](#starting-a-call-from-the-background-the-phone-schema)
- [Parameters and entities](#parameters-and-entities)
- [App Schemas and newer intent protocols](#app-schemas-and-newer-intent-protocols)
- [Controls and widgets](#controls-and-widgets)
- [Live Activities](#live-activities)
- [macOS vs iOS](#macos-vs-ios)

## Intent + App Shortcut

The voice-call pattern: an App Shortcut that starts a call, assignable to the Action Button.

```swift
struct StartConversationIntent: AppIntent {
    static let title: LocalizedStringResource = "Start conversation"
    static let description = IntentDescription("Calls your agent on its voice line.")
    static let supportedModes: IntentModes = .foreground

    @MainActor
    func perform() async throws -> some IntentResult {
        await CallController.shared.start(calling: "Assistant")
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
//   extension CallController: CallStarting { func startCall() async { await start(calling: "Assistant") } }
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

(Same attributes for macOS 13.3/26.0, watchOS and tvOS; `ForegroundContinuableIntent` has no visionOS line and is `unavailable` in every app-extension context (`iOSApplicationExtension`, `macOSApplicationExtension`, ...), so an intent that also compiles into a widget or control extension cannot adopt it. Implementing the deprecated `openAppWhenRun` produces no warning - only uses of it do - so grep for it.)

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
- `AudioRecordingIntent` (iOS 18 / macOS 15) tells the system an intent records audio; on iOS "you must start a Live Activity when you begin the audio recording ... If you don't start a Live Activity, the audio recording stops." A plain `AppIntent` can start a CallKit call only from the foreground or a freshly launched process - from the background use the phone schema below.

## Starting a call from the background: the phone schema

Observed on a locked iPhone (iOS 27.2, Xcode 27.0): an Action Button press or shortcut that runs a plain `AppIntent` while the app is already resident in the background cannot start a call. `callservicesd` logs `callSourceHasReasonableUserIntent: false`, the `CXStartCallAction` transaction fails with `CXErrorCodeRequestTransactionError` 6, and `Activity.request` fails with `ActivityAuthorizationError` 7. It works only when iOS happens to launch a fresh process. iOS 27's phone App Schema is what lets the system vouch for the user's intent, so CallKit takes the start from the background, locked phone included:

```swift
@available(iOS 27.0, *)
@AppIntent(schema: .phone.startCall)
struct CallLineIntent: AudioRecordingIntent, LiveActivityIntent {
    static let supportedModes: IntentModes = [.background]
    static let authenticationPolicy: IntentAuthenticationPolicy = .alwaysAllowed

    var destination: CallDestination
    var audioVisualMode: CallMode // the schema requires it; a video request is placed as a voice call

    init() {}

    @MainActor
    func perform() async throws -> some IntentResult {
        guard case let .line(line) = destination else { return .result() }
        await CallController.shared.start(calling: line.name) // also starts the call's Live Activity
        return .result()
    }
}

@available(iOS 27.0, *)
@UnionValue
enum CallDestination {
    case line(VoiceLineEntity)
}

@available(iOS 27.0, *)
@AppEnum(schema: .phone.audioVisualMode)
enum CallMode: String {
    case audio
    case video

    static let caseDisplayRepresentations: [Self: DisplayRepresentation] = [.audio: "Audio", .video: "Video"]
}

@available(iOS 27.0, *)
@AppEntity(schema: .phone.phonePerson)
struct VoiceLineEntity {
    static let defaultQuery = VoiceLineQuery()

    let id: UUID
    let name: String
    var person: IntentPerson

    var displayRepresentation: DisplayRepresentation { DisplayRepresentation(title: "\(name)") }

    init(_ line: VoiceLine) { // the app's saved destination (id, name); the controller lists them in `lines`
        id = line.id
        name = line.name
        person = IntentPerson(identifier: .applicationDefined(line.id.uuidString), name: .displayName(line.name), handle: nil)
    }
}

@available(iOS 27.0, *)
struct VoiceLineQuery: EntityStringQuery {
    @MainActor
    func entities(for identifiers: [UUID]) async throws -> [VoiceLineEntity] {
        CallController.shared.lines.filter { identifiers.contains($0.id) }.map(VoiceLineEntity.init)
    }

    @MainActor
    func suggestedEntities() async throws -> [VoiceLineEntity] { CallController.shared.lines.map(VoiceLineEntity.init) }

    @MainActor
    func entities(matching string: String) async throws -> [VoiceLineEntity] {
        try await suggestedEntities().filter { $0.name.localizedStandardContains(string) }
    }

    /// Pre-fills the destination when the user adds the action in Shortcuts.
    @MainActor
    func defaultResult() async -> VoiceLineEntity? { CallController.shared.selectedLine.map(VoiceLineEntity.init) }
}
```

- **All of it is needed together** (observed): the schema; `AudioRecordingIntent` and `LiveActivityIntent` (the call's Live Activity may then start from the background); `.background` with `.alwaysAllowed`, so a locked phone runs it - anything `perform()` reads must be stored `kSecAttrAccessibleAfterFirstUnlock` (keychain.md). Each alone failed: `LiveActivityIntent` fixed only the Live Activity, `AudioRecordingIntent` / `AudioPlaybackIntent` did not satisfy CallKit, and donating `INStartCallIntent` interactions with `NSUserActivityTypes` changed nothing.
- **Build-time rules** (both reproduced, `ExtractAppIntentsMetadata`): the union's entity needs a string query - "AppSchemaIntent 'StartCallIntent' requires UnionValue case 'VoiceLineEntity' to conform to 'IndexedEntity', 'UniqueAppEntity', 'TransientAppEntity', provide a default 'EntityStringQuery', or provide an 'IntentValueQuery'"; and the mode enum must declare `video` even for a voice-only app - "'CallMode' conforming to 'phone.audioVisualMode' requires enum case 'video'". Schema properties take no default value (`= .audio` fails to compile).
- **The user's shortcut** must save the destination and the Audio mode rather than "Ask Each Time" (observed); `defaultResult()` fills the destination in when the action is added. Settings > Action Button > Shortcut then points at that shortcut.
- Keep a foreground path too: a plain intent with `supportedModes = .foreground(.immediate)` and `.requiresAuthentication` brings the app forward (after Face ID on a locked phone), and a start from the app in front passes CallKit's check.
- The `.phone` domain is `anyAppleOS 27` (watchOS/tvOS unavailable); `@available(iOS 27.0, *)` keeps it building on an iOS 26 target.

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

## App Schemas and newer intent protocols

**App Schemas** conform an intent, entity or enum to a system-defined shape with `@AppIntent(schema:)`, `@AppEntity(schema:)` and `@AppEnum(schema:)`. Siri and Apple Intelligence then understand it without phrases you define, and entity schemas feed Spotlight's semantic index. Domains arrive per OS (`.journal`, `.reader` and others since iOS 18). The 27 SDK adds `.audio`, `.calendar`, `.clock`, `.maps`, `.messages`, `.notes`, `.phone` (used above) and `.reminders`; the schema dictates required properties, enforced by the macro and by `ExtractAppIntentsMetadata`. Schemas change between releases: iOS 27 renamed `calendar.deleteEvents` to `calendar.deleteEvent`, and `@AppEntity(schema: .photos.asset)` conformers may need changes to compile (iOS 27 release notes).

| API | Availability | Use |
|---|---|---|
| `.appEntityIdentifier(_:)` / `.appEntityIdentifier(forSelectionType:identifier:)` | iOS 18.4 / macOS 15.4 | View annotation: maps a SwiftUI view or selection to an entity so Siri can act on what is on screen |
| `CancellableIntent` + `withIntentCancellationHandler(operation:onCancel:)` | 26.4 | Cleanup when the system cancels; `IntentCancellationReason` (e.g. `.timeout`) |
| `UndoableIntent` | 26 | Reverse the action through its `undoManager` |
| `LongRunningIntent` + `performBackgroundTask(options:operation:)` | 27 | Extends the background runtime; `LongRunningTaskOptions.requiresGPU`. It refines `ProgressReportingIntent`, so report through `progress` |
| `IndexedEntityQuery` | 27 | `reindexEntities(for:indexDescription:)` / `reindexAllEntities(indexDescription:)` when Spotlight asks |
| `SyncableEntity`, `SyncableEntityIdentifier(local:stable:)` | 27 | Entities whose identity survives sync across devices |
| `EntityCollection<Entity>` | 27 | A parameter holding a set of entity identifiers |
| `AppIntentError(description:)`, `CustomAppIntentErrorConvertible` | 27 | User-facing error text from `perform()`, or map your own error type |
| `RunSystemShortcutIntent(shortcut:)` | iOS 27 | Run an App Shortcut, custom shortcut or system action (or open another app) from an interactive widget |
| `RelevantEntities.shared.updateEntities(_:for:)` / `removeEntities(_:)` | 27 | Register entities as suggestions for a context, e.g. `.audio(...)` feeds the Fitness workout media picker |
| `OwnershipProvidingEntity` (`ownership: EntityOwnership`) | 27 | Gives the system ownership and sharing context for an entity |
| `AppUnionValue` + `AppUnionValueCasesProviding` | 27 | Type identity and metadata for union values, with an `AppEnum` listing the cases |

```swift
@available(iOS 27.0, *)
struct ExportLibraryIntent: LongRunningIntent, CancellableIntent {
    static let title: LocalizedStringResource = "Export Library"

    func perform() async throws -> some IntentResult {
        progress.totalUnitCount = 100
        try await performBackgroundTask {
            for step in 1...100 {
                try await Task.sleep(for: .milliseconds(10)) // one slice of the export
                progress.completedUnitCount = Int64(step)
            }
        } onCancel: { reason in
            print("cancelled: \(reason)")
        }
        return .result()
    }
}
```

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

## Live Activities

A Live Activity (ActivityKit) is the Lock Screen and Dynamic Island card for something in progress - a call, a recording, a delivery. The UI lives in a WidgetKit extension; the app starts, updates and ends it. XcodeGen:

```yaml
targets:
  VoiceApp:
    dependencies:
      - target: VoiceActivity       # embeds the extension
    info:
      properties:
        NSSupportsLiveActivities: true
  VoiceActivity:
    type: app-extension
    platform: iOS
    sources:
      - path: VoiceActivity          # the widget bundle and its views
      - path: VoiceApp/CallActivityAttributes.swift   # shared with the app
    info:
      path: VoiceActivity/Info.plist
      properties:
        CFBundleDisplayName: Voice
        NSExtension:
          NSExtensionPointIdentifier: com.apple.widgetkit-extension
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: com.example.VoiceApp.Activity
```

```swift
import ActivityKit
import SwiftUI
import WidgetKit

// Both targets
struct CallActivityAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var status: String
        var startedAt: Date
    }
}

// Extension: listed in its @main WidgetBundle
struct CallActivityWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: CallActivityAttributes.self) { context in
            Label(context.state.status, systemImage: "phone.fill").padding()
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.bottom) { Text(context.state.status) }
            } compactLeading: {
                Image(systemName: "phone.fill")
            } compactTrailing: {
                Text(context.state.startedAt, style: .timer).monospacedDigit().frame(maxWidth: 44)
            } minimal: {
                Image(systemName: "phone.fill")
            }
        }
    }
}

// App
@MainActor
func startCallActivity() throws -> Activity<CallActivityAttributes> {
    let state = CallActivityAttributes.ContentState(status: "Connecting", startedAt: .now)
    return try Activity.request(attributes: CallActivityAttributes(), content: ActivityContent(state: state, staleDate: nil))
}
```

- Update with `await activity.update(ActivityContent(state:staleDate:))` and end with `await activity.end(_:dismissalPolicy:)`; at launch, end leftovers from `Activity<CallActivityAttributes>.activities`.
- **Local updates need no entitlement**; `aps-environment` is only for push-driven updates. Automatic signing registers the extension's bundle ID on the first signed archive (observed).
- **From the background `Activity.request` fails** with `ActivityAuthorizationError` 7 (`.visibility`, "Target is not foreground") - observed. Start it from the foreground, or from an intent conforming to `LiveActivityIntent`, the documented route for background starts (see the phone schema section).
- iOS 27 shows Live Activities in the Dynamic Island in landscape too; `@Environment(\.isDynamicIslandLimitedInWidth)` (iOS 27) tells the views when the island is narrow.

## macOS vs iOS

| | iOS | macOS |
|---|---|---|
| App Intents, App Shortcuts, Siri, Spotlight | iOS 16+ | macOS 13+ |
| `supportedModes`, `continueInForeground` | 26+ | 26+ |
| `allowedExecutionTargets`, `LongRunningIntent`, `.phone` schema | 27+ | 27+ |
| Controls (`ControlWidget`) | 18+ | 26+ |
| Action Button | iPhone 15 Pro and later | none |
| Onscreen-content data sources | `UITableViewAppIntentsDataSource`, `UICollectionViewAppIntentsDataSource` (18.4) | `NSTableViewAppIntentsDataSource`, `NSCollectionViewAppIntentsDataSource` (15.4) |

- The onscreen-content data sources let Siri act on the row the user is looking at; they live in the `_AppIntents_UIKit` / `_AppIntents_AppKit` overlays and import with `AppIntents` plus UIKit/AppKit.
- On macOS a control is often a better fit than a `MenuBarExtra` for a single toggle - no menu-bar space, system-managed placement (see macos-app-lifecycle.md for `MenuBarExtra`).
