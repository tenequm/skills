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

        // Strict memory safety (Swift 6.2)
        .enableExperimentalFeature("StrictMemorySafety"),

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

Current status: Available as open source, integration with SPM ongoing.

## Macros

### Using macros
```swift
// Add macro package
.package(url: "https://github.com/swiftlang/swift-syntax", from: "600.0.0"),

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
swiftly install 6.2.4

# Switch versions
swiftly use 6.2.4

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
