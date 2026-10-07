# Testing

Swift Testing and XCTest for iOS and macOS code: the test API, its compiler traps, running logic tests without a simulator, UI tests, and the `swift test` / `xcodebuild test` surface.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every Swift Testing snippet compiled and ran under `swift test` in a scratch package (17 tests incl. exit test, attachments, warnings, cancellation, confirmations, known issues); the `.init` trap reproduced verbatim; a 10-test logic package from a voice-call app run with `swift test` (cold and warm timings below); a scratch XcodeGen iOS app with a Swift Testing unit target and an XCUITest target run on an iOS 27.0 simulator; the same package tests run on the simulator through `xcodebuild`; image attachments, the macOS UI test and the polling helper compiled through SIL (`swiftc -emit-sil`) against both SDKs; interop modes exercised with `SWIFT_TESTING_XCTEST_INTEROP_MODE`.

## Contents
- Swift Testing essentials
- Trap: `#expect(x == .init(...))` against a type from another module
- Testing iOS logic without a simulator
- Running tests on an iOS simulator
- Exit tests (not on iOS)
- Attachments
- Issues, cancellation, known issues, confirmations
- Traits and parallelism
- `swift test` command line
- XCTest interop and migration
- UI testing
- macOS only: bundles, TCC and menu-bar apps

## Swift Testing essentials

Swift Testing ships in the toolchain; use it for all new unit tests. XCTest remains for UI tests and performance (`measure`) tests. Both can live in one target.

| XCTest | Swift Testing |
|---|---|
| `class FooTests: XCTestCase` | `@Suite struct FooTests` (the `@Suite` is optional) |
| `func testX()` | `@Test func x()` |
| `XCTAssertEqual(a, b)` / `XCTAssertTrue(x)` | `#expect(a == b)` / `#expect(x)` |
| `try XCTUnwrap(x)` | `try #require(x)` |
| `XCTAssertThrowsError` | `#expect(throws: E.self) { ... }` |
| `setUp` / `tearDown` | `init()` / a `deinit` on a final class suite |
| sequential | parallel, in-process, by default |

```swift
import Foundation
import Testing
import Lab

@Suite("Accounts")
struct AccountTests {
    let tempDir: URL

    init() throws {  // runs before every @Test; each test gets a fresh instance
        tempDir = URL.temporaryDirectory.appending(path: UUID().uuidString)
        try FileManager.default.createDirectory(at: tempDir, withIntermediateDirectories: true)
    }

    @Test("creates an account")
    func create() throws {
        let account = try Account(name: "Test", email: "test@example.com")
        #expect(account.name == "Test")
        #expect(account.isActive)
    }

    @Test func rejectsBadEmail() {
        #expect(throws: ValidationError.self) { try Account(name: "x", email: "nope") }
        #expect(throws: ValidationError.badEmail) { try Account(name: "x", email: "nope") }
        let error = #expect(throws: ValidationError.self) { try parse("") }  // returns the caught error
        #expect(error == .empty)
        #expect(throws: Never.self) { try parse("ok") }
    }

    @Test func requireUnwraps() throws {
        let first = try #require([1, 2, 3].first)  // fails and stops the test if nil
        #expect(first == 1)
    }
}

@Test("validates email", arguments: [
    ("user@example.com", true),
    ("invalid", false),
    ("user@.com", false),
])
func validateEmail(email: String, isValid: Bool) {
    #expect(Email.isValid(email) == isValid)
}

@Test(arguments: zip(["a@b.co", "x"], [true, false]))  // zip pairs; two plain collections give the cartesian product
func zipped(email: String, isValid: Bool) {
    #expect(Email.isValid(email) == isValid)
}
```

Each argument becomes its own test case, reported and re-runnable individually. A `CaseIterable` enum's `allCases` is a natural argument list.

**Main-actor code.** Test functions are nonisolated. If the code under test is `@MainActor` - including every unannotated declaration in a target built with `.defaultIsolation(MainActor.self)` or `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` - mark the test or suite `@MainActor`, otherwise the build fails with `call to main actor-isolated global function '...' in a synchronous nonisolated context`.

```swift
@MainActor
struct CounterTests {
    @Test func increments() {
        let counter = Counter()
        counter.increment()
        #expect(counter.count == 1)
    }
}
```

## Trap: `#expect(x == .init(...))` against a type from another module

A test target is a separate module. Given a library target with:

```swift
public struct Grant: Decodable, Equatable {
    public let url: String
    public let token: String
}
```

the synthesized memberwise `init(url:token:)` is `internal`, so the only initializer the test module can see is Decodable's `public init(from:)`. Writing `.init(...)` hides that fact behind an operator-overload failure, and the message you get depends on the left-hand side:

Left side `Grant?` (an optional property, `try? decode(...)`, a function returning an optional):

```
error: cannot convert value of type 'Grant?' to expected argument type '(any (~Copyable & ~Escapable).Type)?'
error: type 'any (~Copyable & ~Escapable).Type' has no member 'init'
```

Left side `Grant`, with `import Foundation` in the test file:

```
error: referencing operator function '==' on 'AttributedStringProtocol' requires that 'Grant' conform to 'AttributedStringProtocol'
error: 'AttributedStringProtocol' cannot be constructed because it has no accessible initializers
```

Left side `Grant`, without Foundation:

```
error: binary operator '==' cannot be applied to operands of type 'Grant' and '()'
error: reference to member 'init' cannot be resolved without a contextual type
```

The real cause appears only once you spell the type out, `#expect(grant == Grant(url: "a", token: "b"))`:

```
error: extra arguments at positions #1, #2 in call
error: missing argument for parameter 'from' in call
note: 'init(from:)' declared here
```

It is not a Swift Testing bug: `let same = optionalGrant == .init(url: "a", token: "b")` outside the macro gives the same metatype error. When a `.init(...)` comparison fails with an error naming metatypes, `AttributedStringProtocol` or `'()'`, spell the type out first.

Fixes, best first:

1. Add an explicit `public init(url: String, token: String)` to the type. Right when other modules (the app target, previews) construct it too.
2. Compare fields: `#expect(grant.url == "a")`, `#expect(grant.token == "b")`. Keeps the public API minimal.
3. `@testable import Core`. Under `swift test` this makes the internal memberwise init visible and the original `.init(...)` line compiles and passes - in both `-c debug` and `-c release`, because `swift test` defaults to `--enable-testable-imports`. In an Xcode project it needs `ENABLE_TESTABILITY = YES` on the module under test; a generated XcodeGen project has it `YES` in Debug and `NO` in Release, so `@testable` tests break if you test the Release configuration.

## Testing iOS logic without a simulator

Put protocols, parsing, networking requests and state machines in a local Swift package that declares both platforms, and keep UIKit / CallKit / AVFoundation glue in the app target:

```swift
// swift-tools-version: 6.4
import PackageDescription

let package = Package(
    name: "AppCore",
    platforms: [.iOS(.v26), .macOS(.v15)],
    products: [.library(name: "AppCore", targets: ["AppCore"])],
    targets: [
        .target(name: "AppCore"),
        .testTarget(name: "AppCoreTests", dependencies: ["AppCore"]),
    ]
)
```

The `.macOS` entry is what makes `swift test` work: the package builds and runs natively on the Mac, no simulator, no runtime download, no app launch. Measured on a 10-test logic package from a voice-call app: cold `swift test` 9.6 s, warm 1.4 s. The same tests through `xcodebuild test` on a booted iOS simulator took 36 s warm.

Rules that keep it working:
- Nothing in the package may `import UIKit`, `CallKit` or another iOS-only framework unguarded. Wrap iOS-only code in `#if os(iOS)` or leave it in the app target.
- Platform minimums must be satisfiable by the host Mac: `.macOS(.v15)` runs on macOS 15 and later.
- Exit tests and anything else that is unavailable on iOS compiles under `swift test` but breaks the moment the tests are built for the simulator - guard them (see Exit tests).
- The app target depends on the package; how to wire it with XcodeGen is in ios-project-setup.md.

## Running tests on an iOS simulator

Test bundles for an iOS app target (unit tests hosted in the app, and every UI test) run only on a simulator or device. That needs an installed iOS Simulator runtime: check `xcrun simctl list runtimes`; installing one is covered in ios-devices-and-signing.md.

```bash
xcrun simctl create "Test iPhone" "iPhone 17" com.apple.CoreSimulator.SimRuntime.iOS-27-0

xcodebuild test -project Tiny.xcodeproj -scheme Tiny \
  -destination 'platform=iOS Simulator,name=Test iPhone' \
  -derivedDataPath build -resultBundlePath build/tests.xcresult \
  CODE_SIGNING_ALLOWED=NO
```

Verified with a scratch XcodeGen app (Swift Testing unit target with `@testable import Tiny`, plus an XCUITest target): cold run including simulator boot 85 s, warm `-only-testing:TinyTests` 36 s. `CODE_SIGNING_ALLOWED=NO` is fine for the simulator. A dedicated, named simulator per project or CI lane avoids two jobs fighting over one booted device.

A Swift package can also be tested on the simulator directly - `xcodebuild` treats the package directory as a workspace with a scheme named after the package:

```bash
cd AppCore && xcodebuild test -scheme AppCore -destination 'platform=iOS Simulator,name=Test iPhone'
```

Use it in CI to catch iOS-only compile problems in the package that `swift test` on the Mac never sees.

## Exit tests (not on iOS)

Exit tests run the closure in a child process and assert how it terminates - the way to test `precondition`, `fatalError` and other trapping paths:

```swift
#if os(macOS)
@Test func negativeIndexTraps() async {
    await #expect(processExitsWith: .failure) {
        _ = checkedIndex(-1)
    }
}
#endif
```

Conditions: `.success`, `.failure`, `.exitCode(_:)`, `.signal(_:)`. `#require(processExitsWith:observing:)` returns an `ExitTest.Result`; pass key paths to `observing:` to get the child's output back:

```swift
#if os(macOS)
@Test func exitOutput() async throws {
    let code: Int32 = 7
    let result = try await #require(processExitsWith: .exitCode(code), observing: [\.standardErrorContent]) { [code = code as Int32] in
        FileHandle.standardError.write(Data("boom".utf8))
        exit(code)
    }
    #expect(String(decoding: result.standardErrorContent, as: UTF8.self) == "boom")
}
#endif
```

The body runs in another process, so it cannot implicitly capture locals. Implicit capture fails with `a C function pointer cannot be formed from a closure that captures context`; a bare `[code]` capture fails with `Type of captured value 'code' is ambiguous (from macro 'require')`. Use an explicit, typed capture list (`[code = code as Int32]`); captured values must be `Sendable & Codable`.

On iOS `ExitTest` and the macro are `@available(*, unavailable, message: "Exit tests are not available on this platform.")` - an unguarded exit test in a dual-platform package compiles under `swift test` on the Mac and fails as soon as the package is built for the simulator.

## Attachments

```swift
struct Report: Codable, Attachable {  // Encodable types get Attachable for free once declared
    var rows: Int
}

@Test func attachesDiagnostics() throws {
    Attachment.record(Data(#"{"ok":true}"#.utf8), named: "response.json")
    Attachment.record(Report(rows: 3), named: "report.json")
}
```

Images (`CGImage`, `CIImage`, `UIImage` on iOS, `NSImage` on macOS) attach through `Attachment.record(_:named:as:)` with `.png`, `.jpeg` or `.jpeg(withEncodingQuality:)`:

```swift
import Testing
import UIKit

@MainActor
func snapshot(_ view: UIView) {
    let image = UIGraphicsImageRenderer(bounds: view.bounds).image { _ in
        view.drawHierarchy(in: view.bounds, afterScreenUpdates: true)
    }
    Attachment.record(image, named: "screen", as: .png)
}
```

Files and `Transferable` values attach through an async initializer passed to `Attachment.record(_:)`:

```swift
Attachment.record(try await Attachment(contentsOf: fileURL))
if #available(macOS 15.2, iOS 18.2, *) {  // the Transferable overlay's floor
    Attachment.record(try await Attachment(exporting: note, as: .json))
}
```

Xcode shows attachments in the test report. **`swift test` discards them unless you pass `--attachments-path <existing-dir>`**; with it, each is written as a file named after `named:`.

## Issues, cancellation, known issues, confirmations

```swift
@Test func softWarning() {
    // Reported, but the test still passes.
    Issue.record("payload still uses deprecatedField", severity: .warning)
}

@Test func cancelsEarly() throws {
    try Test.cancel("nothing to check on this host")  // throws -> Never; reported as cancelled, not failed or skipped
}

@Test func knownBug() {
    withKnownIssue("parser drops the extension bit") {
        #expect(Email.isValid("a@b") == true)
    }
}
```

`withKnownIssue` beats `.disabled`: the test keeps running, records the failure as known, and **fails once the bug stops reproducing**, so you learn it was fixed. Pass `isIntermittent: true` for flaky paths that sometimes pass.

`confirmation` asserts that a callback fired an exact number of times - the tool for delegate and closure-based APIs:

```swift
@Test func callbackFiresThreeTimes() async {
    let monitor = Monitor()
    await confirmation("changes", expectedCount: 3) { changed in
        monitor.onChange = { _ in changed() }
        await monitor.pump(3)
    }
    await confirmation(expectedCount: 0) { changed in  // asserts it never fires
        monitor.onChange = { _ in changed() }
        await monitor.pump(0)
    }
}
```

The count is checked when the closure returns, so the events must arrive before it returns - await the work inside the closure. Ranges (`1...`, `...5`) are accepted for "at least" or "at most".

## Traits and parallelism

```swift
extension Tag {
    @Tag static var networking: Self
}

@Test(.tags(.networking), .timeLimit(.minutes(1)), .enabled(if: ProcessInfo.processInfo.environment["CI"] == nil))
func taggedAndLimited() async throws { /* ... */ }

@Test(.disabled("waiting for server fix"), .bug("https://github.com/org/repo/issues/123"))
func disabled() {}

@Suite(.serialized)
struct SharedResourceTests {
    @Test func first() {}
    @Test func second() {}
}
```

- `.timeLimit` takes minutes only; `.seconds` and `.milliseconds` are `unavailable` with "Time limit must be specified in minutes".
- Tests run in parallel by default. Apply `.serialized` to every suite whose tests share a resource - the microphone, an audio tap, a TCC prompt, a keychain item, a fixed file path, a launched app. Two such tests in parallel produce silent buffers, a spurious `false` from a permission request, or inconsistent process state, and look flaky rather than wrong. Tests outside the suite still run in parallel with it.
- Gate tests that need live permissions or hardware behind an env var so `swift test` skips them by default: `.enabled(if: ProcessInfo.processInfo.environment["RUN_HARDWARE_SMOKE"] == "1")`, and add a `just`/`make` recipe that sets it.

Polling helpers must let the outer deadline govern. A helper that rethrows a transient read error from the condition aborts on the first hiccup under parallel load:

```swift
struct WaitTimedOut: Error {}

func waitUntil<T>(
    timeout: Duration = .seconds(15),
    _ condition: () async throws -> T?
) async throws -> T {
    let deadline = ContinuousClock.now + timeout
    while ContinuousClock.now < deadline {
        if let value = try? await condition() { return value }  // errors mean "not yet"
        try await Task.sleep(for: .milliseconds(200))
    }
    throw WaitTimedOut()
}
```

## `swift test` command line

```bash
swift test --list-tests                       # enumerate without running
swift test --filter AccountTests              # regex over <target>.<suite>/<test>
swift test --skip SlowTests                   # regex to exclude
swift test --disable-xctest                   # Swift Testing only
swift test --attachments-path ./test-output   # keep Attachment.record(...) output (dir must exist)
swift test --maximum-repetitions 50 --repeat-until fail   # hunt a flaky test (Swift Testing only)
swift test --xunit-output results.xml         # JUnit-style report for CI
swift test --enable-code-coverage && swift test --show-codecov-path
```

- Swift Testing parallelizes in-process regardless of `--parallel` (whose default is `--no-parallel`); `--parallel` spreads XCTest across worker processes.
- When `swift test` runs inside a pipe (`swift test | tee log`, `| xcbeautify`), the pipeline's exit status is the last command's. Use `set -o pipefail` in CI scripts or a failing suite reports green.
- In CI, assert on a known non-zero test count in the final `Test run with N tests` line rather than trusting the exit code alone.

## XCTest interop and migration

An XCTest assertion inside a Swift Testing test (or the reverse) is governed by `SWIFT_TESTING_XCTEST_INTEROP_MODE` (`none`, `limited`, `complete`, `strict`) and, in Xcode, by the test plan's "Swift Testing and XCTest Interoperability" setting. Observed under `swift test` with a failing `XCTAssertEqual(1, 2)` inside an `@Test`:

| Mode | Result |
|---|---|
| unset (default) | test fails, plus an "An API was misused" warning |
| `limited` | test passes with two warnings |
| `complete` | same as default |
| `strict` | test fails |
| `none` | **test passes silently** - the assertion is lost |

Never set `none`. Migrate assertions as you touch tests:

1. `XCTestCase` subclass -> struct (or final class if you need `deinit`)
2. `func testX()` -> `@Test func x()`
3. `XCTAssertEqual(a, b)` -> `#expect(a == b)`; `XCTAssertNil(x)` -> `#expect(x == nil)`
4. `XCTAssertThrowsError` -> `#expect(throws:)`; `XCTUnwrap` -> `try #require`
5. `setUp`/`tearDown` -> `init`/`deinit`
6. `expectation`/`wait(for:)` -> `confirmation` or plain `await`
7. `throw XCTSkip(...)` -> `try Test.cancel(...)` or an `.enabled(if:)` trait
8. `measure { }` -> stays in XCTest (no Swift Testing equivalent)

## UI testing

UI tests use XCTest (`XCUIApplication`); Swift Testing has no UI testing API. On iOS use `tap()`, on macOS `click()`. Prefer `accessibilityIdentifier` over visible text for lookups.

```swift
import XCTest

final class TinyUITests: XCTestCase {
    @MainActor
    func testAddIncrementsCount() {
        let app = XCUIApplication()
        app.launchArguments = ["--ui-test-mode"]
        app.launch()
        app.buttons["Add"].tap()
        XCTAssertEqual(app.staticTexts["countLabel"].label, "Count 1")
    }
}
```

Use `waitForExistence(timeout:)` rather than sleeps for anything that appears asynchronously. Xcode 27 adds `XCUIVoiceOverService` for driving VoiceOver from UI tests and test-plan control over how target-app crashes are reported (off / warning / failure / fatal) - see the [Xcode 27 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes).

A UI test target in XcodeGen is `type: bundle.ui-testing` with a dependency on the app target; it must be in the scheme's `test.targets`.

## macOS only: bundles, TCC and menu-bar apps

**Kill stale instances by bundle identifier, not path.** A harness that terminates only `app.bundleURL == testBundleURL` leaves an older copy (for example `/Applications/MyApp.app` from a previous install) running and holding the audio tap, microphone or Screen Recording session. For `LSUIElement` apps that copy is invisible - no Dock icon, no Cmd-Tab, not in Force Quit:

```swift
import AppKit

@MainActor
func terminateStaleInstances(of bundleID: String) {
    for app in NSRunningApplication.runningApplications(withBundleIdentifier: bundleID) {
        app.terminate()
    }
}
```

**Menu-bar-only apps are a dead end for UI automation.** An `LSUIElement` app does not show up to harnesses that enumerate apps through Launch Services or accessibility the way a regular app does, so XCUITest-style automation of its menu bar UI is unreliable. Drive the real bundle through a narrow, explicitly flagged test surface instead, and assert on the artifacts it produces:

```swift
if CommandLine.arguments.contains("--ui-test-mode") {
    TestControlSurface.install()  // start/stop hooks only; never reachable without the flag
}
```

**TCC-gated tests** (microphone, screen recording, accessibility): gate them behind an env var as above and serialize them.

Unverified: TCC attributes the request to the responsible process - for `swift test` started from a terminal, the terminal app - so a grant made to the shipped app does not cover the test run.

Command Line Tools-only machines: see spm-and-builds.md.
