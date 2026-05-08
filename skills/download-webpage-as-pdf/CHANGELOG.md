# Changelog

All notable changes to this skill are documented here. Format follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
