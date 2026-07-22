# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.1] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format

### Changed

- metadata.openclaw audited against the official ClawHub spec

## [1.3.0] - 2026-07-13

### Added
- `gh repo read-file` / `gh repo read-dir` (preview) as the primary no-clone file and directory fetch path; they print raw content, take `--ref`, and handle files past the Contents API's 1MB inline limit.
- `gh api --cache` and `--slurp` for iterative remote analysis and paginated fetches.
- Per-resource search rate limits: 30/min search, 10/min code search, separate from the 5000/hr core budget.
- Preview commands section covering `gh discussion`, `gh skill`, and `gh pr revert`.
- `gh release` idempotency notes: `create` has no upsert or `--clobber` (`upload` does), and draft -> upload -> publish avoids draft orphans and immutable-release failures.
- `gh release download` works unauthenticated against public repos.
- PR gotchas: review-thread resolved state requires GraphQL; `gh pr checks` can surface stale superseded runs.
- `gh pr list` / `gh issue list` `--search` with `updated:>DATE` for date-scoped listing.
- Guidance to pin `--repo OWNER/REPO` in scripted workflows, since `gh` infers the repo from cwd.

### Fixed
- Removed the non-existent `base64decode` template function from all 5 `SKILL.md` examples (live: `template: :1: function "base64decode" not defined`), replacing them with `gh repo read-file`, the raw `Accept` header, or `--jq '.content' | base64 -d`. `SKILL.md` had been contradicting `references/remote-analysis.md`, which already used a working form.
- Corrected `--` guidance: flags must precede `--`, or they are swallowed into the query string as search text; `--` is only required when the query itself starts with a hyphen.
- Removed the false claim that an in-query `filename:` qualifier does not work in code search; it is equivalent to the `--filename` flag.
- `gh search prs` has no `mergedAt` field; documented `closedAt` instead.
- Fixed the "test field names" tip: a bare `--json` writes its field list to stderr and exits non-zero, so `| jq keys` yields nothing.
- Fixed `--sort help-wanted-issues` mislabeled as "most watched repos"; `gh search repos` has no watchers sort.
- Removed the "By recency" code-search example: `created:` is not a code-search qualifier and is matched as literal file text.
- Corrected the wildcard section; GitHub code search has no `*` wildcard, and `function*` matched literally.
- Corrected `SKILL.md`'s description of `references/getting_started.md`, which covers only `gh auth setup-git`.

### Security
- Noted the `gh codespace jupyter` remote code execution fixed in gh 2.96.0 (GHSA-8cg3-r6g9-fpg2); users below 2.96.0 should upgrade.

Verified against: gh@2.96.0

## [1.2.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [1.2.0] - 2026-06-19
### Added
- Quirk note in `references/syntax.md` documenting that `gh search code` has no `--sort`/`--order` and how to scope code search with `--language`/`--filename`/`--extension`/`--match`/`--owner`/`--repo` instead.
- Initial CHANGELOG; upstream tracking established.

### Fixed
- Removed invalid `--sort`/`--order` flags from all `gh search code` examples in `SKILL.md` and `references/discovery.md`; GitHub's legacy code-search engine does not support sorting (live `unknown flag: --sort`).
- Corrected the "find code in popular repos" examples: a `stars:>N` qualifier in a code query is matched as literal file text, not a repo-popularity filter. Replaced with a discover-repos-then-scope-with-`--owner`/`--repo` workflow.

Verified against: gh@2.95.0
