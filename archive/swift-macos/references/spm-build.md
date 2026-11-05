# Swift Package Manager & Build

## Table of Contents
- Package.swift Basics
- Platform & Version Config
- Dependencies
- Targets & Products
- Build Plugins
- Swift Build (Open Source)
- Macros
- Resources
- Conditional Compilation
- Manual .app Bundle Assembly
- Mixed ObjC Targets
- Swift Testing with CLT (No Xcode)
- Multiple Executable Targets

## Package.swift Basics

```swift
// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "MyMacApp",
    platforms: [
        .macOS(.v14), // minimum deployment target
    ],
    products: [
        .executable(name: "MyMacApp", targets: ["MyMacApp"]),
        .library(name: "MyAppCore", targets: ["MyAppCore"]),
    ],
    dependencies: [
        .package(url: "https://github.com/pointfreeco/swift-composable-architecture", from: "1.17.0"),
        .package(url: "https://github.com/sparkle-project/Sparkle", from: "2.7.0"),
    ],
    targets: [
        .executableTarget(
            name: "MyMacApp",
            dependencies: [
                "MyAppCore",
                .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
                .product(name: "Sparkle", package: "Sparkle"),
            ],
            swiftSettings: [
                .swiftLanguageMode(.v6),
                .defaultIsolation(MainActor.self),
            ]
        ),
        .target(
            name: "MyAppCore",
            dependencies: [],
            swiftSettings: [.swiftLanguageMode(.v6)]
        ),
        .testTarget(
            name: "MyMacAppTests",
            dependencies: ["MyAppCore"]
        ),
    ]
)
```

## Swift Settings

```swift
.executableTarget(
    name: "MyApp",
    swiftSettings: [
        // Swift 6 language mode (strict concurrency)
        .swiftLanguageMode(.v6),

        // Default MainActor isolation (Swift 6.2)
        .defaultIsolation(MainActor.self),

        // Enable upcoming features individually
        .enableUpcomingFeature("ExistentialAny"),
        .enableUpcomingFeature("InternalImportsByDefault"),

        // Strict memory safety - first-class setting since Swift 6.2 (SE-0458).
        // The old .enableExperimentalFeature("StrictMemorySafety") spelling still
        // builds, but prefer the real API.
        .strictMemorySafety(),

        // Warning control (Swift 6.2)
        .treatAllWarnings(as: .error),
        .treatWarning("DeprecatedDeclaration", as: .warning),
    ]
)
```

## Dependencies

### Version requirements
```swift
.package(url: "https://github.com/org/repo", from: "1.0.0"),     // >= 1.0.0, < 2.0.0
.package(url: "https://github.com/org/repo", exact: "1.2.3"),     // exactly 1.2.3
.package(url: "https://github.com/org/repo", "1.0.0"..<"2.0.0"), // range
.package(url: "https://github.com/org/repo", branch: "main"),     // branch (dev only)
.package(url: "https://github.com/org/repo", revision: "abc123"), // specific commit
.package(path: "../LocalPackage"),                                 // local path
```

### Conditional dependencies
```swift
.target(
    name: "MyApp",
    dependencies: [
        .target(name: "MyCore"),
        .product(name: "ArgumentParser", package: "swift-argument-parser",
                 condition: .when(platforms: [.macOS, .linux])),
    ]
)
```

## Resources

Bundle resources with targets:

```swift
.target(
    name: "MyApp",
    resources: [
        .process("Resources/"),      // Optimize for platform
        .copy("Data/config.json"),   // Copy as-is
    ]
)
```

Access in code:
```swift
let url = Bundle.module.url(forResource: "config", withExtension: "json")!
let image = NSImage(resource: .appIcon) // Xcode asset catalogs
```

## Build Plugins

### Build tool plugin
```swift
// Plugins/CodeGenPlugin/plugin.swift
import PackagePlugin

@main
struct CodeGenPlugin: BuildToolPlugin {
    func createBuildCommands(context: PluginContext, target: Target) throws -> [Command] {
        let inputFile = context.package.directory.appending("schema.json")
        let outputFile = context.pluginWorkDirectory.appending("Generated.swift")

        return [
            .buildCommand(
                displayName: "Generate code from schema",
                executable: try context.tool(named: "codegen").url,
                arguments: [inputFile.string, outputFile.string],
                inputFiles: [inputFile],
                outputFiles: [outputFile]
            )
        ]
    }
}
```

### Command plugin
```swift
@main
struct FormatPlugin: CommandPlugin {
    func performCommand(context: PluginContext, arguments: [String]) throws {
        let swiftformat = try context.tool(named: "swift-format")
        let process = Process()
        process.executableURL = swiftformat.url
        process.arguments = ["--recursive", context.package.directory.string]
        try process.run()
        process.waitUntilExit()
    }
}

// Run: swift package format
```

## Swift Build

Apple open-sourced Xcode's build engine as Swift Build (Feb 2025). Aims to unify the build experience between Xcode and SPM:

- Same build rules for both Xcode projects and Swift packages
- Supports libraries, executables, and GUI applications
- Build graph optimizations for Swift/C parallel compilation
- Future: Replace SPM's simple build engine with Swift Build

Current status: **shipping**, not "integration ongoing". SwiftPM 6.3 exposes it as a preview behind a flag; SwiftPM 6.4 makes it the default build system.

```bash
# Opt in on the 6.3 toolchain
swift build --build-system swiftbuild

# Swift Build supports SwiftPM-native universal binaries
swift build --build-system swiftbuild --arch arm64 --arch x86_64
```

The `--arch` flags are a Swift Build capability - the default 6.3 native build system builds a single architecture, which is why manual `.app` assembly elsewhere in this file hardcodes `.build/arm64-apple-macosx/release/`. Sources: [SwiftPM 6.3 notes](https://docs.swift.org/swiftpm/documentation/packagemanagerdocs/6.3), [Swift Build preview](https://docs.swift.org/swiftpm/documentation/packagemanagerdocs/swiftbuildpreview).

## Package Traits (SE-0450, Swift 6.1+)

Conditional compilation flags for packages - let consumers opt into optional feature sets without separate products:

```swift
let package = Package(
    name: "MyLib",
    traits: [
        .default(enabledTraits: ["Networking"]),
        "Networking",
        .trait(name: "Experimental", enabledTraits: ["Networking"]),
    ],
    targets: [
        .target(name: "MyLib", swiftSettings: [
            .define("NETWORKING", .when(traits: ["Networking"])),
        ]),
    ]
)

// Consumer side
.package(url: "https://github.com/org/mylib", from: "1.0.0", traits: ["Experimental"]),
```

Inspect with `swift package show-traits`. **Traits must be strictly additive - enabling a trait must not remove API.** Breaking that rule makes dependency resolution unsound, since two consumers can enable different trait sets on the same package build.

## Other target kinds

Beyond `.target` / `.executableTarget` / `.testTarget`:

```swift
.binaryTarget(name: "Vendor", path: "Vendor.xcframework"),           // prebuilt .xcframework
.binaryTarget(name: "Remote", url: "https://.../lib.zip", checksum: "..."),
.systemLibrary(name: "CZlib", pkgConfig: "zlib"),                    // wrap a system C library
```

Plugin sandbox permissions must be declared explicitly - a command plugin that writes outside the package or hits the network is denied by default:

```swift
.plugin(name: "Generate", capability: .command(
    intent: .custom(verb: "generate", description: "Generate sources"),
    permissions: [
        .writeToPackageDirectory(reason: "Writes generated sources"),
        .allowNetworkConnections(scope: .all(ports: [443]), reason: "Fetches schema"),
    ]
))
```

## Build fails before compiling your code: unwritable `$HOME` caches

In sandboxed, CI, or agent environments, `swift build` and `swift test` can die during **manifest compilation** - before touching your sources - because SwiftPM's cache and the clang module cache live under the home directory and are not writable. The error names SwiftPM internals, so it reads like a broken package when the package is fine.

```bash
swift build \
  --cache-path "$SCRATCH/spm-cache" \
  --scratch-path "$SCRATCH/build" \
  -Xswiftc -module-cache-path -Xswiftc "$SCRATCH/module-cache"
```

Redirect the caches to a writable scratch directory and re-run before concluding anything about the package itself.

## Consuming packages from `xcodebuild`: two gates that block non-interactive builds

**Plugin and macro validation.** A project whose dependencies carry package plugins or macros stops on a trust prompt that has no answer in a headless build - it surfaces as a stall or failure on `Validate plug-in '<name>' in package '<pkg>'`. Both gates have opt-outs, and both exist for a reason: they are the trust boundary for arbitrary code running at build time, so only skip them for dependencies you have vetted.

```bash
xcodebuild -scheme MyApp \
  -skipPackagePluginValidation \
  -skipMacroValidation
```

**The Metal toolchain is no longer bundled.** Xcode 26 unbundled it, so any target compiling `.metal` shaders - directly, or through a dependency that does - fails with `cannot execute tool 'metal'` on a fresh install. It is a one-time ~688 MB download:

```bash
xcodebuild -downloadComponent MetalToolchain
```

`xcodebuild -help` lists `MetalToolchain` as the only supported component value.

## Macros

### Using macros
```swift
// Add macro package
// Pin to the swift-syntax release matching your toolchain: 6.3 -> 603.x
.package(url: "https://github.com/swiftlang/swift-syntax", from: "603.0.2"),

.target(
    name: "MyApp",
    dependencies: [
        .product(name: "SwiftSyntaxMacros", package: "swift-syntax"),
    ]
)
```

### Swift 6.2 macro performance
Pre-built swift-syntax is now supported, eliminating the need to build swift-syntax from source on every clean build. Significantly faster CI builds.

## Swiftly (Toolchain Manager)

Official Swift toolchain manager for macOS:

```bash
# Install swiftly
curl -L https://swift.org/install | bash

# Install latest stable
swiftly install latest

# Install specific version
swiftly install 6.3.3

# Switch versions
swiftly use 6.3.3

# List installed
swiftly list
```

## Conditional Compilation

```swift
#if os(macOS)
import AppKit
#elseif os(iOS)
import UIKit
#endif

#if canImport(FoundationModels)
import FoundationModels
// Use on-device AI
#endif

#if swift(>=6.2)
// Use Swift 6.2 features
#endif

#if DEBUG
// Debug-only code
#endif

#if targetEnvironment(simulator)
// Simulator-specific code
#endif
```

## Manual .app Bundle Assembly

SPM (`swift build`) produces a bare executable, not a `.app` bundle. macOS requires a proper `.app` for Info.plist keys (LSUIElement, NSMicrophoneUsageDescription), TCC permissions, and framework loading. Assemble manually via Makefile:

```makefile
APP_BUNDLE = build/MyApp.app
BINARY = .build/arm64-apple-macosx/release/MyApp

bundle: build
	@mkdir -p "$(APP_BUNDLE)/Contents/MacOS"
	@mkdir -p "$(APP_BUNDLE)/Contents/Frameworks"
	@mkdir -p "$(APP_BUNDLE)/Contents/Resources"
	# Copy binary
	@cp "$(BINARY)" "$(APP_BUNDLE)/Contents/MacOS/MyApp"
	# CRITICAL: Add rpath for frameworks (SPM default doesn't include it)
	@install_name_tool -add_rpath @executable_path/../Frameworks \
	    "$(APP_BUNDLE)/Contents/MacOS/MyApp"
	# Copy Info.plist and icon
	@cp Info.plist "$(APP_BUNDLE)/Contents/"
	@cp Assets/AppIcon.icns "$(APP_BUNDLE)/Contents/Resources/"
	# Copy dynamic frameworks (e.g., Sparkle)
	@cp -R .build/artifacts/sparkle/Sparkle/Sparkle.framework \
	    "$(APP_BUNDLE)/Contents/Frameworks/"
	# CRITICAL: Copy SPM resource bundles (CoreML models, assets, etc.)
	@for bundle in .build/arm64-apple-macosx/release/*.bundle; do \
	    [ -d "$$bundle" ] && cp -R "$$bundle" "$(APP_BUNDLE)/Contents/Resources/"; \
	done
	# Sign from inside out: nested bundles first, then main app
	@codesign --force --options runtime --sign "$(SIGN_ID)" --timestamp \
	    "$(APP_BUNDLE)/Contents/Frameworks/Sparkle.framework"
	@codesign --force --options runtime --sign "$(SIGN_ID)" --timestamp \
	    --identifier com.example.MyApp --entitlements entitlements.plist "$(APP_BUNDLE)"
```

Key gotchas:
- **`install_name_tool -add_rpath`** is required or dynamic frameworks crash with `dyld: Library not loaded: @rpath/...`
- **SPM resource bundles** (`.bundle` directories from packages with `resources:`) are NOT automatically included. Missing them causes silent crashes on non-dev machines where `Bundle.module` resolves to nil.
- **Sign from inside out**: nested `.xpc` and `.app` bundles within frameworks must be signed before the framework, which must be signed before the top-level app.
- **Stale artifacts** can have read-only permissions from previous builds. Use `chmod -R u+w` or clean before copying.

### make run race condition

`open` won't relaunch an already-running LSUIElement app. Kill and wait before rebuilding:

```makefile
run: build
	@killall MyApp 2>/dev/null; while killall -0 MyApp 2>/dev/null; do sleep 0.1; done
	@$(MAKE) bundle
	@open "$(APP_BUNDLE)"
```

Rebuilding while the old process is running causes `SIGKILL (Code Signature Invalid)` - macOS detects memory-mapped code pages don't match the new binary's signature.

## Mixed ObjC Targets

SPM doesn't allow mixing Swift and ObjC in a single target. Create a separate target:

```swift
targets: [
    .executableTarget(
        name: "MyApp",
        dependencies: ["ObjCExceptionCatcher"],
        exclude: ["ObjCExceptionCatcher"], // Exclude from main target's path scan
        swiftSettings: [.swiftLanguageMode(.v6), .defaultIsolation(MainActor.self)]
    ),
    .target(
        name: "ObjCExceptionCatcher",
        path: "Sources/ObjCExceptionCatcher",
        publicHeadersPath: "include",
        linkerSettings: [.linkedFramework("AVFAudio")]
    ),
]
```

Directory layout:
```
Sources/
  MyApp/
    main.swift
  ObjCExceptionCatcher/
    include/ObjCExceptionCatcher.h
    ObjCExceptionCatcher.m
```

## Swift Testing with CLT (No Xcode)

On machines using CommandLineTools (not Xcode), `import Testing` fails. The framework exists but SPM doesn't search the CLT path. Add three `unsafeFlags`:

```swift
.testTarget(
    name: "MyAppTests",
    dependencies: ["MyApp"],
    swiftSettings: [
        .swiftLanguageMode(.v6),
        // Compiler: find Testing module
        .unsafeFlags(["-F",
            "/Library/Developer/CommandLineTools/Library/Developer/Frameworks"]),
    ],
    linkerSettings: [
        // Linker: resolve Testing framework
        .unsafeFlags(["-F",
            "/Library/Developer/CommandLineTools/Library/Developer/Frameworks"]),
        // Runtime: load Testing framework
        .unsafeFlags(["-Xlinker", "-rpath", "-Xlinker",
            "/Library/Developer/CommandLineTools/Library/Developer/Frameworks"]),
    ]
)
```

## Multiple Executable Targets

When adding helper binaries (e.g., watchdog, CLI tool) to the same package:

```swift
targets: [
    .executableTarget(
        name: "MyApp",
        exclude: ["Watchdog", "ObjCExceptionCatcher"], // Exclude sibling directories
        swiftSettings: [.swiftLanguageMode(.v6), .defaultIsolation(MainActor.self)]
    ),
    .executableTarget(
        name: "MyWatchdog",
        path: "Sources/Watchdog",
        swiftSettings: [
            .swiftLanguageMode(.v6),
            .treatAllWarnings(as: .error),
            // Helper doesn't need defaultIsolation - it's a simple process monitor
        ]
    ),
]
```

The Makefile copies helper binaries into `Contents/MacOS/` and signs them before the main app:

```makefile
@cp .build/arm64-apple-macosx/release/MyWatchdog "$(APP_BUNDLE)/Contents/MacOS/"
@codesign --force --sign "$(SIGN_ID)" "$(APP_BUNDLE)/Contents/MacOS/MyWatchdog"
# Then sign main app last
@codesign --force --sign "$(SIGN_ID)" --entitlements entitlements.plist "$(APP_BUNDLE)"
```
