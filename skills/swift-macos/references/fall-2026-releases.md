# Fall 2026 Releases (WWDC 2026)

Announced at WWDC 2026 (June 8, 2026), shipping fall 2026. Developer betas are out now. Build against the shipping stack (Swift 6.3.3 / Xcode 26.6 / macOS 26 Tahoe) unless you specifically target these betas.

Sources: [Apple Newsroom, 2026-06-08](https://www.apple.com/newsroom/2026/06/apple-aids-app-development-with-new-intelligence-frameworks-and-advanced-tools/); [WWDC26 "What's new in Swift"](https://developer.apple.com/videos/play/wwdc2026/262).

## OS and toolchain

- **macOS 27 Golden Gate** - next macOS; Apple-silicon only. macOS 26.5 Tahoe remains the current shipping release until fall.
- **Xcode 27** - agentic coding with Anthropic/Google/OpenAI models plus MCP plug-ins and the Agent Client Protocol; Apple-silicon only, ~30% smaller. Gemini also landed in stable Xcode 26.6.
- **Swift 6.4** (beta; shipping toolchain is still 6.3.3) - `anyAppleOS` availability shorthand, targeted warning suppression, `~Sendable` (explicitly mark a type non-Sendable), `weak let`, a new memberwise initializer, and improved compiler diagnostics.

## Frameworks

- **Foundation Models next-gen** - the single native Swift API now accepts image input and adds server models running on Private Cloud Compute. `DynamicProfile` swaps model/tools/instructions mid-session. A new `LanguageModel` protocol makes third-party models (Claude, Gemini) pluggable behind the same API.
- **Core AI** - a brand-new framework, distinct from Foundation Models, for loading and running full-scale LLMs on device, optimized for the Neural Engine and unified memory.
- **SwiftUI** - reorderable list/grid containers, faster layout, and lazier `@State` initialization (back-deployed). New **Spatial Preview** framework streams 3D content from a Mac to Apple Vision Pro.

## Liquid Glass becomes mandatory

Apps rebuilt with the Xcode 27 SDK can no longer opt out of Liquid Glass - the `UIDesignRequiresCompatibility` key is ignored. Under Xcode 26 the key still works as a temporary migration aid. A new system transparency slider lets users tune the effect.
