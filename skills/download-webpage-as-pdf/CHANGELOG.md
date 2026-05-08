# Changelog

All notable changes to this skill are documented here. Format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.3] - 2026-05-08

### Fixed
- Hotfix for the v0.1.2 headless approach. The `--headed false` CLI flag corrupts the session context in agent-browser 0.26.0 (the eval/pdf commands see an empty document even though `open` reports success), producing blank PDFs. Reproduced and confirmed via direct CLI test. Switched to the supported route: setting the `AGENT_BROWSER_HEADED=false` environment variable before running. Verified: returns the correct page title and image count.

## [0.1.2] - 2026-05-08

### Changed
- Recipe now passes `--headed false` to `agent-browser open` so the skill runs headless regardless of the host's `~/.agent-browser/config.json` default. Prevents a real Chrome window from popping up on the user's desktop during background automation. Drop the flag for visual debugging.

### Known issue (fixed in 0.1.3)
- The `--headed false` flag is parsed by agent-browser 0.26.0 but corrupts the session context. Use 0.1.3 or later.

## [0.1.1] - 2026-05-08

### Added
- Note about `agent-browser --session <name>` for isolating concurrent runs (multi-agent test setups share a single host browser by default).
- `pdfinfo` verification step at the end of the recipe so the broken-image count is paired with concrete page-count and byte-size numbers in the agent's report.
- Explicit comment marking the `qpdf ... 1-9` example as illustrative, to prevent agents from copying the page range verbatim.

### Changed
- Frontmatter `metadata.upstream` now tracks the verified `agent-browser` version.

Verified against: agent-browser@0.26.0

## [0.1.0] - 2026-05-08

### Added
- Initial recipe: `open` -> `wait networkidle` -> `eval` (strip `loading`/`decoding`, scroll, await all images) -> `pdf`.
- Optional cleanup pipeline using `qpdf --pages` and `gs -dPDFSETTINGS=/ebook`.
- "When NOT to use this" pointers to `percollate`, `agent-browser screenshot`, `monolith`/SingleFile, and WeasyPrint.
- Tie-break guidance between agent-browser (full layout) and percollate (reader mode).
