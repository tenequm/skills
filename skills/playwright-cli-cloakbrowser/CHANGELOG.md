# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.2] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format
- metadata.openclaw block (emoji, homepage, requires.bins, install, envVars) for ClawHub display

## [0.3.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.3.0] - 2026-07-02

### Added

- "Patterns for logged-in & JS-heavy sites" section: reverse-engineering same-origin APIs via eval-fetch, CDP-level network inspection (`requests`/`response-body`), scroll-until-count for lazy lists, and fresh-context retry for hard blocks.
- Importing-a-login guidance: storage-state transfer as the bypass for flagged CDP-driven logins, and the IP-bound-session limit (proxy geo must match where the session was minted).
- Gotchas for false "logged-in" state, non-fatal `goto` timeouts, unreliable CSS-selector clicks, eval-poll-instead-of-sleep waits, and mid-run anti-automation logout.
- `snapshot --depth`, parallel `-s=<name>` sessions, and an `Accept-Language` geo-override note.

### Changed

- Pin `@playwright/cli` 0.1.14 -> 0.1.15 (`screenshot --hires` added upstream; command catalog still deferred to the bundled skill).

Verified against: @playwright/cli@0.1.15

## [0.2.0] - 2026-07-02

### Added

- "Remote Manager on a Linux VM over SSH" section: Docker install, localhost-bound run with a restart policy, SSH tunnel as the auth boundary, VM sizing.
- Notes surfaced by live end-to-end testing: port-8080 conflict fallback, the `.playwright-cli/` scratch dir written to cwd, and the implicit `default` session created by `attach`.

### Changed

- Merged `references/local-setup.md` into SKILL.md (single file; setup content is small enough to inline).
- Accuracy fixes from a live test run: the Docker image bundles the CloakBrowser binary (no slow first-launch download); non-`--raw` output wraps in markdown header blocks that vary by command (not always a snapshot block); `--raw` eval values are JSON-serialized.

## [0.1.0] - 2026-07-02

### Added

- Initial release: drive CloakBrowser Manager stealth profiles with @playwright/cli over per-profile CDP endpoints.
- Field-tested gotchas: attach hangs on stale tabs, Target.createTarget rejection, JS-rendered content via eval, --raw output, consent overlays.
- `references/local-setup.md`: run the Manager locally on a laptop with Docker, including the built-in noVNC login/live-view flow and headless profile creation via API.

Verified against: @playwright/cli@0.1.14
