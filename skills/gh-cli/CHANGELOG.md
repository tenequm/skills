# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-06-19
### Added
- Quirk note in `references/syntax.md` documenting that `gh search code` has no `--sort`/`--order` and how to scope code search with `--language`/`--filename`/`--extension`/`--match`/`--owner`/`--repo` instead.
- Initial CHANGELOG; upstream tracking established.

### Fixed
- Removed invalid `--sort`/`--order` flags from all `gh search code` examples in `SKILL.md` and `references/discovery.md`; GitHub's legacy code-search engine does not support sorting (live `unknown flag: --sort`).
- Corrected the "find code in popular repos" examples: a `stars:>N` qualifier in a code query is matched as literal file text, not a repo-popularity filter. Replaced with a discover-repos-then-scope-with-`--owner`/`--repo` workflow.

Verified against: gh@2.95.0
