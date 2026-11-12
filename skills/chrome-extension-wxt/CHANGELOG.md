# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.0] - 2026-11-12

### Added
- "Before you start" (confirm a WXT project and its version), "What WXT recommends" (a sourced outline of WXT's and Chrome's own recommendations) and a "Verify your work" loop.
- Firefox runtime differences: `browser.action ?? browser.browserAction` for MV2 builds, `gecko.id` and `data_collection_permissions`.
- Reading a tab's page without the `tabs` permission; the `web_accessible_resources` entry `cssInjectionMode: 'ui'` adds.
- Tables of contents in all three references.

### Changed
- Service worker lifecycle and messaging rules moved from `references/chrome-mv3.md` into `SKILL.md`; duplicate troubleshooting rows folded into the rules.
- Description in third person without a version number; `metadata.upstream` now tracks `chrome@157`.

### Fixed
- shadcn/ui setup: `init` fails in WXT projects and `add` writes outside the project; replaced with a tested manual recipe.

## [2.0.0] - 2026-11-12

### Changed
- **Breaking:** rewritten against WXT 0.21: `npx wxt@latest init`, auto-imports and `#imports`, awaited shadow-root UI, Node 22 and Vite peer requirements.
- Messaging uses `@webext-core/messaging`; tests use `WxtVitest` and `fakeBrowser`; Tailwind v4, zustand v5 and current shadcn setup.
- References consolidated into `chrome-mv3.md`, `react.md` and `testing-publishing.md`.

### Added
- `storage.defineItem` with versioned migrations, entrypoint types, per-browser targeting, main-world injection, `wxt submit`.
- Chrome 141-153 platform changes: `browser` namespace, promise `onMessage`, side panel events.

### Removed
- **Breaking:** generic Chrome API dump, the Chrome 140 reference, generic React patterns, and two stale template links.

### Fixed
- Blocking `webRequest` examples (not available to MV3 extensions), an `'unsafe-eval'` CSP that MV3 rejects, invalid option values and storage keys.

### Security
- Chrome Web Store API v1 stopped working on 2026-10-15; `wxt submit` needs v2 service-account auth.

Verified against: wxt@0.21.5, @wxt-dev/module-react@1.2.2

## [1.1.5] - 2026-11-05
- Initial CHANGELOG; tracking established.
