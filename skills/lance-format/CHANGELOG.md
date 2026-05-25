# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-05-25

### Changed
- Re-grounded against upstream tag `v7.1.0-beta.2` (commit `24b8afec`); bumped every
  version pin, permalink base, and the workspace crate version to `7.1.0-beta.2`.
- Removed stale claim that `lance-namespace-datafusion` is pinned at `7.0.0-beta.9` -
  it has used `version.workspace = true` since v7.1.0-beta.1.
- Fixed stale workspace-member count (22 -> 24) and dropped the wrong claim that
  `rust/arrow-stats` is a path dependency rather than an explicit member.

### Added
- New `lance-select` crate (PR #6879): mask code (`RowAddrMask`, `RowIdMask`,
  `IndexExprResult`) extracted from `lance-core` and `lance-index`. Crate workspace
  count goes from 23 to 24.
- v7.1.0-beta.2 delta section: MemWAL correctness fixes - flushed memtables now
  build secondary indexes (PR #6901, fixes invisible vector rows in `fast_search`)
  and a per-source PK-hash block-list post-filter suppresses stale LSM vector reads
  when the fresh row falls out of its source's top-k (PR #6899).
- Section 16: integrations `index.md` landing page (PR #6915).

Verified against: lance-format/lance@v7.1.0-beta.2

## [0.3.0] - 2026-05-21

### Added
- Section 11.1: IVF_PQ build prerequisites - no empty-table build; 256-row floor for
  default 8-bit PQ; IVF k-means needs >= num_partitions rows.
- Section 11 / 11.5: no-index queries flat-scan transparently (vector and FTS); the
  `optimize_indices(&OptimizeOptions)` API (`append` / `merge(N)` / `retrain`).
- Section 13: `shared-memory://` is an opt-in, authority-keyed, never-evicted
  process-global pool intended for tests and harnesses.
- Section 2: protoc build requirement and the `lance-datafusion` feature-cascade gap.

## [0.2.0] - 2026-05-21

### Changed
- Re-grounded against upstream tag `v7.1.0-beta.1` (commit `cffa8cb5`); bumped every
  version pin, permalink base, and the workspace crate version to `7.1.0-beta.1`.
- Updated the `pylance` runtime dependency to `lance-namespace>=0.7.7,<0.8`.

### Added
- Materialized-view namespace API (`create_materialized_view` / `refresh_materialized_view`).
- Typed `VectorIndexDetails` / `HnswParameters` index-details messages (`protos/index.proto`).
- v7.1.0-beta.1 delta section: granular tracing event targets, multi-base `write_fragments`
  bindings, MemWAL primary-key dedup fixes.

Verified against: lance-format/lance@v7.1.0-beta.1

## [0.1.0] - 2026-05-20
- Initial CHANGELOG; tracking established.
