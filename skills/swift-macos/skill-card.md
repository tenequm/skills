# Skill Card

## Description

swift-macos is a comprehensive development reference for building native macOS apps with Swift 6.3, SwiftUI, SwiftData, Swift Concurrency, Foundation Models, Swift Testing, ScreenCaptureKit, and App Store / Developer ID distribution.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers building or maintaining native Mac apps who want current, version-accurate patterns for SwiftUI scenes and windows, SwiftData models and migrations, Swift 6 concurrency, on-device AI, screen/audio capture, AppKit interop, testing, and app distribution. macOS-only (declared via os restriction in the openclaw metadata).

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None (Apple Developer credentials are only mentioned in distribution examples the user runs themselves, e.g. notarytool with their own Apple ID)

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

- Swift toolchain and Xcode (swift, xcodebuild, xcrun) when the user asks to build, test, or distribute - not required to consult the reference content
- Swift Package Manager for package-based projects

## Known Risks and Mitigations

Risk: Distribution examples invoke code signing and notarization (xcodebuild archive, xcrun notarytool, stapler) with the user's Apple Developer identity and app-specific password; careless handling could expose credentials or ship a mis-signed binary.

Mitigation: Examples reference credentials via keychain items (e.g. @keychain:AC_PASSWORD) rather than inline secrets, and signing/notarization only runs when the user explicitly requests a distribution workflow.

Risk: ScreenCaptureKit and Core Audio tap guidance produces code that captures screen content, system audio, and microphone input - privacy-sensitive capabilities gated by macOS TCC permissions.

Mitigation: The references document the TCC permission prompts and entitlements involved, so generated apps request user consent through the standard macOS permission flow rather than bypassing it.

Risk: Version-specific guidance (Swift 6.3, macOS 26, Xcode 26) can go stale as Apple ships new toolchains, leading to code that no longer compiles.

Mitigation: The skill pins tracked upstream versions in metadata.upstream, records verification dates in its CHANGELOG, and isolates forward-looking beta material in a dedicated fall-2026-releases reference.

## References

- Swift (tracked upstream: swift@6.3.3): https://www.swift.org
- Xcode (tracked upstream: xcode@26.6): https://developer.apple.com/xcode/
- Apple developer documentation (SwiftUI, SwiftData, ScreenCaptureKit, Foundation Models): https://developer.apple.com/documentation/
- Source: https://github.com/tenequm/skills/tree/main/skills/swift-macos

## Skill Output

Output type(s): Swift source code (SwiftUI views, SwiftData models, concurrency code, tests), Package.swift manifests, and build/distribution shell commands.

Output format: Swift code, YAML/plist snippets, and bash commands in Markdown.

Output parameters: Not applicable

Other properties: Reference-only by default; build, test, notarization, and capture commands execute only when the user asks for them and require a local Xcode installation on macOS.

## Skill Version

0.6.3

## Ethical Considerations

Screen and audio capture code enables recording of user activity; apps built from this guidance must obtain user consent via macOS permission prompts and disclose recording behavior. Distribution guidance assumes the developer signs software under their own verified Apple identity.
