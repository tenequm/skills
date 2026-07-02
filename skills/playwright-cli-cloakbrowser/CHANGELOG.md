# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-07-02

### Added

- Initial release: drive CloakBrowser Manager stealth profiles with @playwright/cli over per-profile CDP endpoints.
- Field-tested gotchas: attach hangs on stale tabs, Target.createTarget rejection, JS-rendered content via eval, --raw output, consent overlays.
- `references/local-setup.md`: run the Manager locally on a laptop with Docker, including the built-in noVNC login/live-view flow and headless profile creation via API.

Verified against: @playwright/cli@0.1.14
