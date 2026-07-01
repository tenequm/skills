# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.1] - 2026-07-01
### Changed
- Moved the "Fall 2026 Releases (WWDC 2026)" section out of SKILL.md into `references/fall-2026-releases.md` (progressive disclosure), keeping SKILL.md under the 500-line policy limit. Content unchanged, expanded slightly with sources.

## [0.6.0] - 2026-07-01
### Changed
- Current toolchain updated to Swift 6.3.3 / Xcode 26.6 (macOS 26.5 Tahoe SDK); dropped the stale "Swift 6.2.4, Feb 2026 latest" framing.
- Liquid Glass section notes the `UIDesignRequiresCompatibility` opt-out is removed for apps built with Xcode 27.

### Added
- Forward-looking "Fall 2026 Releases (WWDC 2026, beta)" section: macOS 27 Golden Gate, Xcode 27, Swift 6.4, Foundation Models next-gen (image input, server models, Dynamic Profiles, pluggable models), Core AI, Spatial Preview.
- CoreAudio CFString Create-Rule trap (`takeRetainedValue`) in core-audio-tap.md.
- `SIGKILL (Code Signature Invalid)` dev-loop gotcha in distribution.md.
- CHANGELOG and upstream tracking established.

Verified against: swift@6.3.3, xcode@26.6
