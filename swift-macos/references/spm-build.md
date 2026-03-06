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
