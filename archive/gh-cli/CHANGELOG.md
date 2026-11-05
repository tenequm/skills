# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2026-09-22

### Added

- Terminal escape-sequence refusal (gh 2.97.0+) on `gh repo read-file`, raw `gh api` bodies, piped `gh pr diff`, `gh release download --output -` and `gh gist view`, with the `--allow-escape-sequences` override.
- Scripting gotchas: `gh api` writes the error body to stdout on failure; `-f`/`-F` switch the method to POST; `--jq` takes no jq flags; `--paginate --slurp` cannot combine with `--jq`; quote endpoints containing `?` for zsh; exit codes 1/2/4 plus `gh pr checks` exit 8.
- `gh search issues --search-type semantic|hybrid` (gh 2.98.0) with its constraints and its separate 10/min `semantic_search` rate-limit bucket; search `--state` accepts only `open|closed`; `--match comments`; phrase-vs-keyword quoting.
- Compare API (`repos/O/R/compare/A...B`, 250 commits / 300 files, same repository network only) for codebase comparison.
- PR gotchas: `--watch --fail-fast` instead of sleep-poll loops, inline review comments via `pulls/N/reviews`, reply and `resolveReviewThread` recipe, `gh pr diff --name-only/--exclude`, `--comments` vs `--json` exclusivity, `gh pr checkout --worktree`.
- Actions gotchas: `gh run view` shows only the latest attempt (`--attempt N`), jobs live on `run view` not `run list`, re-runs reuse the original commit, ref and actor privileges, `rerun --failed` refusal while a run is in progress, `--workflow` file lookup on the default branch.
- `--attach` on issue/PR create/edit/comment and `gh issue develop --worktree` (gh 2.99.0).
- Discussion search/filter flags and the `{discussions, next, totalCount}` JSON shape, `gh skill preview`, `--template` helper functions, "Could not resolve to a Repository" and missing-`--repo` error signatures, auth traps (`GH_TOKEN` precedence, `gh auth refresh` acts on the active account, clipboard device codes).

### Changed

- `references/comparison.md` rebuilt on `gh repo read-dir`/`read-file`, the Git Trees API at `HEAD`, and the compare API.
- Environment variables and config keys updated to gh 2.101.0 (`GH_EXTENSION`, `GH_TELEMETRY`, `DO_NOT_TRACK`, `GH_CONFIG_DIR` defaults, `clipboard`, `api_host`).
- Issue JSON field lists include `blockedBy, blocking, issueType, parent, subIssues, subIssuesSummary`; `gh release list` includes `isImmutable`.
- Hardcoded 2024 "last month" dates replaced with a computed `SINCE` date.

### Fixed

- Multi-qualifier queries packed into one quoted argument are sent mangled by `gh search` (gh 2.97.0+ quotes everything after the first `:`), e.g. `"language:go stars:>500"` becomes `language:"go stars:>500"`; every example now passes one qualifier per argument.
- `gh repo read-dir --json` output is `{"entries":[...]}`; `--jq '.[].name'` failed, now `.entries[].name`.
- Piped `gh search code` prints only matched text lines, so filename- and path-only examples (`--filename Dockerfile`, `--match path`) exited 0 with no output; they now use `--json`, and the trap is documented. The `useWallet` owner-scoped example pointed at an owner with no matches.
- `gh search repos` with no query or filter flag fails (`Invalid search query ""`); examples now carry a qualifier.
- Git Trees examples used `trees/main`, which 404s on repos with another default branch; now `trees/HEAD`.
- Contents API `.content | base64 -d` examples print nothing for files over 1MB; moved to `gh repo read-file`.
- `gh search repos` and `gh api` require authentication (exit 4); only `gh release download` works unauthenticated.
- `gh search repos` has no `repositoryTopics` field; its `watchersCount` equals the star count.
- Unknown-field error text is `Unknown JSON field: "X"`; search `--limit` max is 1000; `gh api` paginates only with `--paginate`; quoted `--json` field lists work; a missing jq field prints `null` rather than erroring; unquoted multi-word queries are keyword-AND, not an error.
- `gh pr revert` is not a preview command; `gh skill install` takes `<repository> [<skill>]`.
- "GitHub search is not semantic" no longer holds for issues.

### Security

- gh 2.97.0 fixed terminal escape-sequence injection (GHSA-3m3g-3wcr-px46), unescaped URL path components (GHSA-4fjg-2h4q-fwg3), partial token disclosure in `gh auth status` (GHSA-cg6r-mpgc-h9mm) and an attestation signer-matcher bypass (GHSA-mm27-mwq9-fr5g); gh 2.98.0 fixed `gh codespace ports forward` binding to all interfaces (GHSA-vfhh-p7hm-pxfh). Upgrade to 2.98.0 or later.

Verified against: gh@2.101.0

## [1.3.3] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`development, integrations`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [1.3.2] - 2026-08-07

### Removed

- `references/index.md`, an orphaned stale scrape artifact never linked from SKILL.md that listed only 9 of the 14 reference files.

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
