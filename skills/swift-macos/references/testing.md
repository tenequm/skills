# Testing macOS Apps

## Table of Contents
- Swift Testing Framework
- Test Suites & Organization
- Expectations & Requirements
- Parameterized Tests
- Exit Tests
- Attachments
- Async Testing
- Parallelism Pitfalls for Hardware / Bundle Tests
- Traits
- Swift Testing recent features (6.2 and 6.3)
- UI Testing
- XCTest Migration

## Swift Testing Framework

Swift Testing (bundled with Swift 6.0+, Xcode 16+) replaces XCTest for new tests:

```swift
import Testing

@Test("user can create account")
func createAccount() throws {
    let account = try Account(name: "Test", email: "test@example.com")
    #expect(account.name == "Test")
    #expect(account.isActive)
}
```

### Key differences from XCTest

| Feature | XCTest | Swift Testing |
|---------|--------|---------------|
| Test declaration | `func testX()` | `@Test func x()` |
| Assertions | `XCTAssertEqual` | `#expect(a == b)` |
| Required values | `XCTUnwrap` | `try #require(value)` |
| Test suites | `class: XCTestCase` | `@Suite struct` |
| Parallelism | Sequential | Parallel by default |
| Parameterized | Manual loops | `@Test(arguments:)` |
| Traits | None | Tags, conditions, time limits |

## Test Suites

```swift
@Suite("Document Manager")
struct DocumentManagerTests {
    // Shared setup
    let manager: DocumentManager
    let tempDir: URL

    init() throws {
        tempDir = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: tempDir, withIntermediateDirectories: true)
        manager = DocumentManager(directory: tempDir)
    }

    // Cleanup (deinit not available for structs, use helper)

    @Test func createDocument() throws {
        let doc = try manager.create(name: "test.txt")
        #expect(doc.exists)
    }

    @Test func listDocuments() async throws {
        try manager.create(name: "a.txt")
        try manager.create(name: "b.txt")
        let docs = try await manager.listAll()
        #expect(docs.count == 2)
    }
}
```

### Nested suites
```swift
@Suite("API Client")
struct APIClientTests {
    @Suite("Authentication")
    struct AuthTests {
        @Test func validToken() { /* ... */ }
        @Test func expiredToken() { /* ... */ }
    }

    @Suite("Requests")
    struct RequestTests {
        @Test func getRequest() { /* ... */ }
        @Test func postRequest() { /* ... */ }
    }
}
```

## Expectations & Requirements

```swift
// Basic expectation
#expect(result == 42)
#expect(name.isEmpty == false)
#expect(items.count > 0)

// String contains
#expect(message.contains("success"))

// Optional handling - #require unwraps or fails test
let user = try #require(response.user)
#expect(user.name == "Alice")

// Throws
#expect(throws: ValidationError.self) {
    try validate(invalidInput)
}

// Specific error
#expect {
    try parse("")
} throws: { error in
    guard let parseError = error as? ParseError else { return false }
    return parseError.code == .emptyInput
}

// No throw
#expect(throws: Never.self) {
    try safeOperation()
}
```

## Parameterized Tests

Test multiple inputs without duplication:

```swift
@Test("validates email", arguments: [
    ("user@example.com", true),
    ("invalid", false),
    ("@missing.com", false),
    ("user@.com", false),
    ("a@b.co", true),
])
func validateEmail(email: String, isValid: Bool) {
    #expect(Email.isValid(email) == isValid)
}

// With zip
@Test(arguments: zip(
    ["admin", "user", "guest"],
    [Permission.all, Permission.read, Permission.none]
))
func rolePermissions(role: String, expected: Permission) throws {
    let user = try User(role: role)
    #expect(user.permissions == expected)
}

// From collection
enum FileFormat: CaseIterable {
    case json, xml, csv
}

@Test("exports in all formats", arguments: FileFormat.allCases)
func export(format: FileFormat) throws {
    let data = try exporter.export(items, as: format)
    #expect(!data.isEmpty)
}
```

## Exit Tests (Swift 6.2)

Verify code terminates under specific conditions:

```swift
@Test func preconditionFailsForNegativeIndex() async {
    await #expect(processExitsWith: .failure) {
        let array = [1, 2, 3]
        _ = array[-1] // Should trigger precondition failure
    }
}

@Test func fatalErrorOnInvalidState() async {
    await #expect(processExitsWith: .failure) {
        StateMachine.transition(from: .completed, to: .idle)
    }
}
```

Exit tests run in a separate process - safe for testing fatal paths.

## Attachments (Swift 6.2)

Include diagnostic data in test results:

```swift
@Test func renderChart() throws {
    let chart = try ChartRenderer.render(data: sampleData)

    // Attach PNG bytes for debugging
    let imageData = try chart.pngData()
    Attachment.record(imageData, named: "chart.png")

    #expect(chart.width == 800)
    #expect(chart.height == 600)
}

@Test func apiResponse() async throws {
    let response = try await api.fetchUsers()

    // Attach raw JSON for diagnosis
    Attachment.record(response.rawData, named: "response.json")

    #expect(response.users.count > 0)
}
```

Attachments appear in Xcode test reports and can be written to disk.

## Async Testing

```swift
@Test func fetchData() async throws {
    let service = DataService()
    let items = try await service.fetchAll()
    #expect(!items.isEmpty)
}

// With timeout trait
@Test(.timeLimit(.minutes(1)))
func longRunningOperation() async throws {
    let result = try await processor.processLargeFile(url)
    #expect(result.isComplete)
}

// Testing async sequences
@Test func streamEvents() async throws {
    let stream = EventSource.events()
    var count = 0
    for await event in stream.prefix(5) {
        #expect(event.isValid)
        count += 1
    }
    #expect(count == 5)
}
```

## Parallelism Pitfalls for Hardware / Bundle Tests

Swift Testing runs tests **in parallel by default**. For tests that launch the same `.app` bundle, drive CoreAudio, or touch shared hardware state (microphone, Screen Recording TCC, a running process), this causes non-obvious races:
- Two tests launch the same bundle, fight for the CATap, one ends up with silent buffers.
- Two hardware tests both request microphone access, the second one's `AVCaptureDevice.requestAccess(...)` returns spuriously `false`.
- Two UI-driving tests try to `open -a MyApp.app` concurrently and `NSWorkspace.runningApplications` reports inconsistent state.

### Serialize with `.serialized`

Apply the `.serialized` trait on the suite (or individual tests) that share a resource:

```swift
@Suite("Hardware Smoke", .serialized)
struct HardwareSmokeTests {
    @Test func recordsFaceTime() async throws { /* launches bundle, records */ }
    @Test func recordsSystemAudio() async throws { /* launches bundle, records */ }
    @Test func handlesDeviceSwitch() async throws { /* launches bundle, switches device */ }
}
```

Tests outside the suite still run in parallel with suites that don't share the resource.

### Kill by bundle identifier, not by path

Test harnesses that tear down a stale app instance between tests commonly use:

```swift
// WRONG: only kills instances of THIS copy of the bundle.
// A stale /Applications/MyApp.app running from a previous install stays alive
// and keeps holding CoreAudio / SCStream resources.
for app in NSWorkspace.shared.runningApplications where app.bundleURL == testBundleURL {
    app.terminate()
}
```

For LSUIElement / menu-bar apps especially, a stale `/Applications` copy from a previous `make install` is invisible (no Dock icon, no Cmd+Tab, no Force Quit listing) but contends for the CATap / microphone / Screen Recording TCC. Kill by bundle ID instead:

```swift
for app in NSWorkspace.shared.runningApplications
    where app.bundleIdentifier == "com.example.MyApp" {
    app.terminate()
}
// Or via AppKit's async termination for a cleaner shutdown before yielding.
```

### Polling helpers must be tolerant of transient errors

Bundle-based tests often poll a JSON / IPC state file the app writes. Under full parallel suite load the app can briefly miss its poll interval; if the helper rethrows the inner read error, the outer deadline doesn't get a chance to govern:

```swift
// FRAGILE: any transient read failure aborts the wait, even though the outer
// deadline hasn't been reached.
func waitUntil<T>(_ timeout: Duration = .seconds(15),
                  _ condition: () async throws -> T?) async throws -> T {
    let deadline = Date().addingTimeInterval(timeout.seconds)
    while Date() < deadline {
        if let v = try await condition() { return v } // rethrows transient errors
        try await Task.sleep(for: .milliseconds(200))
    }
    throw WaitError.timedOut
}

// ROBUST: outer deadline governs; inner errors are treated as "not yet".
func waitUntil<T>(_ timeout: Duration = .seconds(15),
                  _ condition: () async throws -> T?) async throws -> T {
    let deadline = Date().addingTimeInterval(timeout.seconds)
    while Date() < deadline {
        if let v = try? await condition() { return v }
        try await Task.sleep(for: .milliseconds(200))
    }
    throw WaitError.timedOut
}
```

### Gate hardware tests behind an env var

Tests that need live TCC permissions (screen recording, microphone) or specific hardware (AirPods, a running FaceTime call) shouldn't run on developer machines by default:

```swift
@Test(.enabled(if: ProcessInfo.processInfo.environment["RUN_HARDWARE_SMOKE"] == "1"))
func recordsAgainstLiveSystem() async throws { /* ... */ }
```

A `Makefile` or `justfile` target that sets the env var is the canonical wrapper (`make smoke-test`). `swift test` without the var shows these as "skipped", which is the desired default.

### Pipe buffering and `make` swallow test output

Running `swift test` through `make` / `rtk` / any command that pipes through a second process can truncate Swift Testing output at ~120 lines and lose the exit code. When you need the full output (e.g. to see which test crashed and where), invoke `swift test --parallel` directly.

## Traits

```swift
// Tags for filtering
extension Tag {
    @Tag static var networking: Self
    @Tag static var database: Self
    @Tag static var slow: Self
}

@Test(.tags(.networking))
func apiCall() async throws { /* ... */ }

// Conditional execution
@Test(.enabled(if: ProcessInfo.processInfo.environment["CI"] != nil))
func ciOnlyTest() { /* ... */ }

// Disabled with reason
@Test(.disabled("Waiting for server fix"))
func brokenTest() { /* ... */ }

// Bug reference
@Test(.bug("https://github.com/org/repo/issues/123"))
func regressionTest() { /* ... */ }

// Time limit
@Test(.timeLimit(.seconds(30)))
func quickTest() async throws { /* ... */ }

// Serial execution (see Parallelism Pitfalls above)
@Suite(.serialized)
struct HardwareTests { /* ... */ }
```

## Swift Testing recent features (6.2 and 6.3)

A handful of workflow wins scattered across Swift Testing 6.2 (Xcode 26) and 6.3 (Xcode 26.4). Version gate noted per feature — they did not all ship at the same time.

### Warning-severity issues (non-failing) — Swift 6.2

```swift
@Test func parsesPayload() throws {
    let parsed = try parser.parse(payload)
    #expect(parsed.id != nil)
    if parsed.deprecatedField != nil {
        // Does NOT fail the test, but surfaces in reports.
        Issue.record("payload still uses deprecatedField", severity: .warning)
    }
}
```

Use for soft expectations (deprecations, perf regressions short of a hard bar, drift warnings). Shipped in [swift-testing 6.2](https://github.com/swiftlang/swift-testing/releases/tag/swift-6.2-RELEASE) (ST-0013).

### Exit tests: `processExitsWith:` — Swift 6.2

The `#expect(exitsWith:)` spelling was renamed to `#expect(processExitsWith:)` in swift-testing 6.2:

```swift
@Test func preconditionFailsForNegativeIndex() async {
    await #expect(processExitsWith: .failure) {
        let array = [1, 2, 3]
        _ = array[-1]
    }
}
```

### `Attachment.record(...)` — Swift 6.2 (rename), Swift 6.3 (AppKit/CoreImage/UIKit images)

The static `Attachment.record(_:named:...)` replaces the old instance `.attach()` method (rename shipped in [PR #1032](https://github.com/swiftlang/swift-testing/pull/1032), Swift 6.2). `CGImage` support landed in Swift 6.2 as well; the `NSImage` (AppKit), `CIImage` (CoreImage), `UIImage` (UIKit) overlays shipped in Swift 6.3 (ST-0014).

```swift
// Swift 6.2+ — bytes / CGImage
Attachment.record(imageData, named: "chart.png")
Attachment.record(cgImage, named: "chart", as: .png)

// Swift 6.3+ — NSImage / UIImage / CIImage overlays
@Test func rendersChart() throws {
    let image: NSImage = try ChartRenderer.render(data)
    Attachment.record(image, named: "chart", as: .png)
    #expect(image.size == CGSize(width: 800, height: 600))
}
```

Xcode's test report displays attached images inline; useful for golden-image tests and visual regressions.

### Cooperative mid-test cancellation — Swift 6.3

`Test.cancel(_:)` has signature `throws -> Never`: it always throws, so the call never returns normally and callers must use `try`. The comment argument is positional (no `reason:` label).

```swift
@Test func longRunningCheck() async throws {
    for _ in 0..<1_000_000 {
        if shouldStop() {
            try Test.cancel("condition met early")
        }
        try await doOneStep()
    }
}
```

Cleaner than `throw XCTSkip("...")` — the test reports cancelled, not failed or skipped. (ST-0016, [swift-testing 6.3](https://github.com/swiftlang/swift-testing/releases/tag/swift-6.3-RELEASE) / Xcode 26.4.) The 6.2 release does not correctly handle task cancellation in all conditions, per the proposal note — require 6.3.

### `SourceLocation.filePath` — Swift 6.3

Non-underscored file-path access on `SourceLocation` for custom reporters:

```swift
let loc = #_sourceLocation
print(loc.filePath)   // String
```

(ST-0020, PR #1538.)

### ST-0021 XCTest / Swift Testing interop — accepted, not yet shipped

Proposal status is `Accepted`, not `Implemented`. Only fallback-event-handler plumbing landed in swift-testing 6.3 (PRs #1369, #1503, #1543). The full interop-mode semantics and SwiftPM integration are not yet marked as shipped — don't rely on the `SWIFT_TESTING_XCTEST_INTEROP_MODE` surface yet. Source: https://github.com/swiftlang/swift-evolution/blob/main/proposals/testing/0021-targeted-interoperability-swift-testing-and-xctest.md

## UI Testing (XCTest-based)

UI testing still uses XCTest (Swift Testing doesn't support UI tests yet):

```swift
import XCTest

final class ProjectUITests: XCTestCase {
    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launch()
    }

    func testCreateProject() throws {
        app.buttons["New Project"].click()

        let nameField = app.textFields["projectName"]
        nameField.click()
        nameField.typeText("My Project")

        app.buttons["Create"].click()

        XCTAssertTrue(app.staticTexts["My Project"].exists)
    }
}
```

## XCTest Migration

Migrate incrementally - both frameworks coexist in the same target:

```swift
// Old (XCTest)
class OldTests: XCTestCase {
    func testAdd() {
        XCTAssertEqual(add(2, 3), 5)
    }
}

// New (Swift Testing)
@Test func add() {
    #expect(add(2, 3) == 5)
}
```

Migration checklist:
1. `XCTestCase` class -> `@Suite` struct
2. `func testX()` -> `@Test func x()`
3. `XCTAssertEqual(a, b)` -> `#expect(a == b)`
4. `XCTAssertTrue(x)` -> `#expect(x)`
5. `XCTAssertNil(x)` -> `#expect(x == nil)`
6. `XCTAssertThrowsError` -> `#expect(throws:)`
7. `XCTUnwrap(x)` -> `try #require(x)`
8. `setUp/tearDown` -> `init/deinit` or test-local setup
9. `measure { }` -> Use Instruments (no direct equivalent yet)
