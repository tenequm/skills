# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
