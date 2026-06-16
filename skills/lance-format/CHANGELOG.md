# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-06-16

### Changed
- Re-grounded against upstream tag `v8.0.0-beta.9` -> `v8.0.0-beta.14` (commit
  `c188de59f`); bumped the workspace version pin, permalink base, and citation tag.
  31-commit range, 2 breaking changes (both RaBitQ/vector). All structural invariants
  reverified unchanged: 25 crates, arrow 58, datafusion 53, opendal 0.57, jieba-rs 0.10,
  rust 1.91.0, resolver 3, edition 2024, version enum (`Next => 2.3`, default `V2_1`),
  15 transaction ops, `CommitConfig num_retries = 20`.
- Dep pins: `lance-namespace-reqwest-client` 0.8.2 -> 0.8.4; pylance `lance-namespace`
  `>=0.8.0,<0.9` -> `>=0.8.5,<0.9`.
- IVF_RQ default `target_partition_size` is now 4096 (was the generic fallback) (PR #7273).

### Added
- Public vector-search `approx_mode` (`fast` / `normal` / `accurate`) for RaBitQ-backed
  indexes; serialized as `VectorApproxMode approx_mode` in `protos/ann.proto` (PR #7179,
  breaking proto change). Dedicated SIMD kernels for RaBitQ ex-code reranking (PR #7205).
  (Section 11.1)
- Cleanup explain API: `Dataset::cleanup(policy)` with `explain()` / `execute()` returning
  a `CleanupExplanation` (PR #7147). (Section 7)
- Tencent COS and GooseFS object-store config keys now documented in the object-store guide
  (COS: `cos_endpoint` / `cos_secret_id` / `cos_secret_key` / `cos_enable_versioning`,
  `COS_`/`TENCENTCLOUD_` env prefixes; GooseFS: `goosefs_write_type` / `goosefs_auth_type` /
  `goosefs_block_size` / `goosefs_chunk_size`, default port 9200) (PR #7151). (Section 13)
- Python zonemap segment builds exposed (PR #7177); per-query I/O metrics
  (`bytes_read`/`iops`/`requests`) on ANN operators in EXPLAIN ANALYZE (PR #7204);
  branch-aware version ops in Directory/REST namespaces (PR #7166). (Section 14 delta)

### Removed
- Upstream removed `table_version_storage_enabled` and the `__manifest`-backed table-version
  path (version ops now use `_versions/` exclusively, PR #7222); brotli dropped from the
  dependency graph (PR #7270).

### Fixed
- Corrected the reference-file H1 and table-of-contents, which still read "Lance v7" though
  the body is v8 (carryover miss from the 0.6.0 v7->v8 re-grounding).
- Dropped the stale claim that GooseFS is "not in the object-store guide" - it now has a
  full guide section.

Verified against: lance-format/lance@v8.0.0-beta.14

## [0.6.0] - 2026-06-10

### Changed
- Re-grounded against upstream tag `v7.2.0-beta.5` -> `v8.0.0-beta.9` (annotated tag,
  commit `a0664baf1`); bumped every version pin, permalink base, and the title from
  "Lance v7 reference" to "Lance v8 reference". 86-commit range, 6 breaking changes.
- The v8 boundary is the unification of all index builds onto one segment-based
  lifecycle. Bitmap migrated to the segment-based distributed workflow (PR #6869); the
  old public `create_scalar_index(..., fragment_ids=)` + `merge_index_metadata(...,
  "BITMAP")` Bitmap shard path is no longer exposed. Distributed BTree moved to the same
  segmented framework (PR #7013).
- RaBitQ (IVF_RQ) is no longer 1-bit-only: multi-bit shipped (`num_bits` 1..=9). Ex-code
  bits store in `__ex_codes` (+ `__add_factors_ex`/`__scale_factors_ex`); a `query_estimator`
  field selects `residual_query` (legacy default) or `raw_query`; raw-query search adds
  `__error_factors` for lower-bound pruning (PR #7038, #7078). The `dimension/8 + 16`
  per-row formula now holds only for `num_bits=1`.
- Crate workspace 24 -> 25 (see Added). Workspace dep versions: arrow 58, datafusion 53,
  opendal 0.57, jieba-rs 0.10, lance-namespace 8.0.0-beta.9, lance-namespace-reqwest-client
  0.8.2; pylance `lance-namespace>=0.8.0,<0.9`.
- Distributed indexing: `merge_existing_index_segments(...)` now covers vector, inverted,
  bitmap, BTree, and zone map segments (was vector/bitmap/btree/FTS); added independent
  per-worker vector models (each worker trains its own IVF/PQ model) (PR #7148, #7128).
- File/index writers' `finish()` now returns `FileWriteSummary { num_rows, size_bytes }`
  instead of a bare row count (PR #7096). `describe_indices()` reports full nested field
  paths and derives type from index details without opening the index; `list_indices()` is
  now a typed `IndexInformation` wrapper; the `load_indices()` Python binding was removed
  (PR #6903).
- Added a merge-insert (upsert / find-or-create) note to section 6: default
  `SourceDedupeBehavior::Fail` on duplicate source PKs (opt into `FirstSeen`); empty `on`
  keys fall back to the schema PK; `WhenMatched::UpdateAll` rewrites whole fragments.

### Added
- New `lance-derive` crate (PR #6229): `#[derive(DeepSizeOf)]` proc-macro for Arrow-aware
  memory accounting, replacing the external `deepsize` crate (which double-counts Arc-shared
  Arrow buffers). Crate workspace count goes 24 -> 25.
- FM-Index scalar index (Section 11.2): a Ferragina-Manzini / Burrows-Wheeler compressed
  substring index for arbitrary substring, prefix, and regex search on raw bytes. Built on
  the Segmented Index architecture (`num_segments`), normalization-independent, sanitizes
  `\x00`/`\xFF` to space at build time.
- Volcengine TOS object store (`tos://`, `tos_endpoint`/`tos_region`/...) and a feature-gated
  GooseFS provider (`goosefs://`, `goosefs_master_addr` with HA) (Section 13).

### Removed
- `IndexSegmentBuilder` API removed from Rust, Python, and Java (PR #6997); staged segments
  now publish directly via `create_index_uncommitted` / `execute_uncommitted` +
  `merge_existing_index_segments` + `commit_existing_index_segments`. `build_all()` is gone.
  The old builder's `target_segment_bytes` size-based grouping has no direct replacement.

Verified against: lance-format/lance@v8.0.0-beta.9

## [0.5.0] - 2026-06-05

### Changed
- Re-grounded against upstream tag `v7.1.0-beta.2` -> `v7.2.0-beta.5` (annotated tag,
  commit `1506693b`); bumped every version pin, permalink base, and the workspace crate
  version to `7.2.0-beta.5`. No breaking changes, no new crate (still 24), no new
  transaction op (still 15) across the 66-commit range.
- Corrected the file-format `next` alias: in code `next` resolves to **2.3** (a `V2_3`
  enum scaffolding version with no distinct encodings yet, 6 refs vs 98 for 2.2 across
  `lance-encoding`), while 2.2 remains the actual unstable frontier carrying Map / Blob v2 /
  `VariablePackedStruct`. The docs version table still lists only 2.2 as unstable.
- Updated the pylance runtime dependency to `lance-namespace>=0.8.0,<0.9` (was
  `>=0.7.7,<0.8`); noted `lance-namespace-reqwest-client 0.8.0`, `opendal 0.57`,
  `jieba-rs 0.10` workspace-dep bumps.
- Refined the RaBitQ (RQ) note: explicitly 1-bit-only (multi-bit is future work), added the
  `code_dim` metadata field and the `dimension/8 + 16` per-row storage formula.
- Fixed stale "all 23 crates" reference-nav line to 24.

### Added
- ICU FTS base-tokenizer (`base_tokenizer="icu"`, bundled ICU4X segmenter data, no external
  language model). Default tokenizer stays `simple` (an ICU-default PR was reverted).
  (PR #6956, revert #7006)
- Scalar-index fast search: `fast_search=True` routes through scalar/BTREE-indexed fragments
  and skips unindexed ones (not on legacy file version). (PR #6784)
- Batched vector queries via `Scanner::nearest` (no separate API), exposing a synthetic
  0-based `query_index` discriminator column. (PR #6828)
- Streaming IVF k-means training params (`streaming_sample_rate`, `streaming_coreset_rate`,
  `streaming_refine_passes`) for bounded-memory IVF training. (PR #6913)
- Section 14 delta subsection for v7.1.0-beta.2 -> v7.2.0-beta.5, also covering Arrow
  Utf8View/BinaryView encoding (PR #6985), HuggingFace `download_mode` (PR #7022), and
  MemWAL LSM local-scoring FTS (PR #6951).

Verified against: lance-format/lance@v7.2.0-beta.5

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
