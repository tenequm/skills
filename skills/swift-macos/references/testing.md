# Testing macOS Apps

## Table of Contents
- Swift Testing Framework
- Test Suites & Organization
- Expectations & Requirements
- Parameterized Tests
- Exit Tests
- Attachments
- Async Testing
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
    await #expect(exitsWith: .failure) {
        let array = [1, 2, 3]
        _ = array[-1] // Should trigger precondition failure
    }
}

@Test func fatalErrorOnInvalidState() async {
    await #expect(exitsWith: .failure) {
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

    // Attach screenshot for debugging
    let imageData = try chart.pngData()
    Attachment(data: imageData, name: "chart.png", contentType: .png)
        .attach()

    #expect(chart.width == 800)
    #expect(chart.height == 600)
}

@Test func apiResponse() async throws {
    let response = try await api.fetchUsers()

    // Attach raw JSON for diagnosis
    Attachment(data: response.rawData, name: "response.json", contentType: .json)
        .attach()

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
```

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
