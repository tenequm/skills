# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.19.0] - 2026-09-09

### Added

- v12 delta extended to `v12.0.0-beta.15`: two more `breaking-change`-labeled PRs (#8800
  predecessor-conditioned publication, #8915 namespace merge-insert key list), taking the v12
  line from 3 to 5, plus a full `beta.6 -> beta.15` section in `references/changelog-v7-v12.md`.
- MemWAL `SsTable` accounting fields `in_memory_bytes` / `physical_rows` / `primary_key_bytes`
  (proto fields 3-5, #8981), with the "absent is not zero" reader rule.
- Blob v2 logical Arrow schema: the Minimal and Complete shapes, the row-level invariants, and
  the shape-preservation guarantee across create/append/merge-insert (#8929).
- `FilteredReadOptions` fields 13/14 (`materialization_readahead_bytes`, `batch_size_bytes`) and
  the proto governance rule exempting execution-plan schemas from the format vote.
- Net-new API surface: cleanup of specific versions (#8617), `LanceDataset.slice()` (#8059), six
  scanner options on `LanceFragment` (#8429), restored Python index retraining (#8786),
  `MemTableVisibility` (#8835), namespace-managed clone deprecated to a shim (#8964).
- Correctness fixes needing rebuild or repair rather than an upgrade: #8779 (NGRAM rebuild),
  #8510 (compaction crossed logical columns), #8984 (resurrected index), #8837 (unreopenable
  MemWAL shard), plus #8441, #8935, #8842 and the longer heals-on-upgrade list.
- MemWAL is a parallel stack: `Dataset::scanner()` has no MemWAL integration, no manifest feature
  flag marks a MemWAL table, and no SSTable compactor ships in-tree.
- Field-verified practice: append-commit coalescing via `execute_uncommitted` +
  `CommitBuilder::execute_batch`; `checkout_latest` polling cost and the absence of any
  subscribe/watch API; remote index folding as near fixed-cost per pass (~346 s for a ~200-row
  delta vs 2-4 s for a 424k-row delta locally); what the unindexed-fragment flat arm actually
  does (full scan, post-scan filter not scalar-index-accelerated, no limit/offset pushdown).
- The v2 manifest-path compatibility fence (default on; unreadable by Lance < 0.17.0) and
  `migrate_manifest_paths_v2`.
- Measured `rust-stemmers` -> `frostem` stem drift (~0.2% of English words), which makes a
  v11 binary silently miss forms in a v10-built FTS index.
- Pointers to six concepts that existed only in the docs mirror: SBBF internals, the MemWAL
  bucket-hash transform, MemWAL query planning, distributed-indexing segment grouping, FRI load
  cost and trimming, and off-write-path cleanup strategies.

### Changed

- **Breaking:** tracked tag moves to `v12.0.0-beta.15` (89 commits, 9 beta tags).
- **Breaking:** `stable` now resolves to **2.2**, which is also the enum `#[default]` and the
  default for new datasets (#8657). The skill previously called 2.1 the current default and 2.2
  "the real experimental frontier"; 2.3 remains the only code-unstable version. Upstream did not
  update the docs with this, so the code is the authority.
- **Breaking:** IVF_RQ defaults to **5 bits** per dimension, not 1 (#8936) - roughly a 4.4x
  index-size increase at the default. Per-row sizing is now `dimension/8 + 20` at 1-bit plus a
  separate multi-bit formula.
- `lance-namespace` is no longer one number: the Rust client is 0.12.0 (#8915) while the Java and
  Python pins deliberately stay at 0.11.1.
- GooseFS `storage_options` keys must be lowercase - a wrong-case key is now a hard error rather
  than silently ignored (#8940) - and block/chunk sizes accept `64MB`-style suffixes (#8943).
- `references/maintenance.md` now warns that the `breaking-change` label is a floor, not a
  ceiling, and that a refresh must also scan for `!` commits and diff documented defaults.
- Docs mirror refreshed to `v12.0.0-beta.15` (4 files changed; still 45 markdown + 4 diagrams,
  every per-directory count unchanged).
- `SKILL.md` v11 and v12 delta sections and the version landscape condensed to absorb the new
  material; full detail stays in `references/changelog-v7-v12.md`.

### Removed

- Column slice stitching (#8660). It was reverted at beta.9 (#8926); #8923's caller-managed data
  file parts replace it.

### Fixed

- `is_unstable() = self >= Next` described no recent tag and could not compile - the enum carries
  no `Ord`. The selector delegates to `resolve()`; the concrete version is `matches!(self, V2_3)`.
- Stale workspace metadata in `format-file.md`: `[workspace.package] version` (`11.0.0-beta.2` ->
  `12.0.0-beta.15`), the Python `lance-namespace` pin, the `lance-namespace-reqwest-client`
  version, and the `opendal` / `object_store` / `object_store_opendal` line citations.
- The RQ per-row sizing citation pointed at `guide/performance.md:416`, the KMeans `sample_rate`
  paragraph, rather than `:483`.
- Citation drift from the mirror refresh: `mem_wal.md` cites above line 148 shift +23, `blob.md`
  cites above line 67 shift +19.
- Pre-existing stale `object_store.md` citations (TOS, GooseFS, the GooseFS commit-handler
  quotes, Tencent COS) retargeted against the refreshed mirror.
- `performance.md` claimed `docs/src/guide/performance.md` was byte-identical across the range;
  it changed at beta.12 (#8936), so the provenance note and the RQ figures it implied were wrong.

Verified against: lance-format/lance@v12.0.0-beta.15

## [0.18.1] - 2026-09-09

### Changed
- Description condensed to fit the repo's 250-character limit.

## [0.18.0] - 2026-09-01

### Added

- Covering indexes: `IndexMetadata.covering_fields` (proto field 11), the redefinition of
  `fields` as keyed-then-carried columns, and the widened index-invalidation rule.
- `FLAG_MIXED_DATA_FILE_VERSIONS` (bit 8, reserved *at* the unknown boundary) and the
  `STICKY_PAIRED_FLAGS` carry mechanism.
- A v12 delta section in `SKILL.md` and `references/changelog-v7-v12.md`, plus a
  beta.16 -> v11.0.0-final delta the skill previously stopped short of.
- Object-store surface: `LANCE_IO_SERVER_SIDE_COPY_ENABLED`, `LANCE_DEEP_CLONE_STREAM_CONCURRENCY`,
  `LANCE_INITIAL_UPLOAD_SIZE`, `LANCE_DEFAULT_IO_BUFFER_SIZE`.
- v11-final and v12 API surface: `merge_insert` `write_mode`, `Scanner::with_row_addr_prefilter`,
  `get_deleted_row_ids`, `ObjectStore::read_dir_page`, Python `ObjectStoreProvider` registration.
- Field-verified compaction practice: the `CompactionPlanner` veto pattern, the index-coverage
  bin split, `Dataset::versions()` as an O(history) round-trip cost, and a `Ne`-predicate
  slow path (labelled as observed on an older pin, not re-verified).
- `references/maintenance.md` now warns that finals are not ancestors of `main` and that tags
  can be read without moving `HEAD`.

### Changed

- **Breaking:** tracked tag moves to `v12.0.0-beta.6`; the stable pin becomes `v11.0.0`
  (crates.io `lance` 11.0.0, PyPI `pylance` 11.0.0, GitHub Releases `Latest`).
- **Breaking:** manifest bit 128 is `FLAG_COVERED_INDEX_METADATA`, not
  `FLAG_MEM_WAL_INDEX_CATCHUP` - the MemWAL bit was retired in `v11.0.0` final and the bit
  reclaimed. Builds pinned in `v11.0.0-beta.4`..`beta.17` open a covering dataset instead of
  refusing it.
- MemWAL: a shard absent from `index_catchup` now unconditionally means *unknown*; the
  flag-gated "absence means caught up" reading and the one-way-flag rule are gone.
- Index invalidation keys off any column in `fields`, not only the indexed column.
- `merge_insert` composite keys now index-accelerate per column.
- `ShardManifestStore::read_latest` -> `latest`, `read_latest_uncached` -> `refresh_latest`,
  `write` is crate-private.
- The v11 delta is now stated against the final: 357 commits and 16 breaking PRs, up from
  313 and 14 at `beta.16`.
- The release-train note records **three** consecutive re-rooted lines; the 11.1 line never
  got even one beta tag.
- `references/changelog-v7-v11.md` renamed to `references/changelog-v7-v12.md`.
- Docs mirror refreshed to `v12.0.0-beta.6` (6 files changed; still 45 markdown + 4 diagrams,
  every per-directory count in `SKILL.md` unchanged).

### Removed

- `FLAG_MEM_WAL_INDEX_CATCHUP` and proto field
  `Transaction.UpdateMemWalState.require_index_catchup`.

### Fixed

- `references/ops.md` listed `request_timeout` as a `storage_options` key. It exists in no
  Lance source at any recent tag; the real key is `timeout`.
- Documented the v11 fix whereby address-domain indexes (ZoneMap) lose coverage of rewritten
  fragments under compaction instead of falsely claiming them. New compactions are safe; an
  index damaged under v10 or earlier still needs recreating.
- Corrected the `safe_coerce_scalar` citation (`expr.rs:302` -> `:311`) and added the field
  report plus the three available escape hatches.

Verified against: lance-format/lance@v12.0.0-beta.6

## [0.17.1] - 2026-08-21

### Changed

- Declared ClawHub browse categories (`development, integrations`) and topics in `metadata`, so the release pipeline publishes them instead of leaving the skill in the `other` category.

### Removed

- `skill-card.md`. The ClawHub CLI strips a root `skill-card.md` from every publish and the registry generates its own card, so the authored file never reached ClawHub.

## [0.17.0] - 2026-08-21

### Changed

- Condensed `SKILL.md` from 24,463 to ~18,300 chars by trimming "The v11 delta" from ~10,400
  chars (42% of the file) to a summary plus a pointer. **No information was lost**: all 54 PR
  citations in that section already appeared verbatim in `references/changelog-v7-v11.md`, which
  exists to hold exactly this content. The retained summary keeps the five changes that break
  upgraders, the manifest feature-flag change, the `LANCE_*` grep trap, and the
  heals-on-upgrade vs requires-rewrite split. Rationale: the per-PR delta is needed only by
  someone upgrading across majors, so it satisfies the conditional-loading test for living in a
  reference file, and the entry point was within 550 chars of the 25k recommended budget.
- Corrected the `check_fragment_ids` citation to `rust/lance/src/io/commit.rs:687`.

### Added

- `format-table.md` section 5.3: "Legacy manifests and fragment resolution", documenting that
  `Dataset::get_frags_from_ordered_ids` resolves ids as
  `manifest.fragments[fragment_bitmap.rank(id) - 1]` - correct only when `manifest.fragments` is
  sorted by id, guarded only by a `debug_assert_eq!` that compiles out in release. Its sibling
  `find_fragment` was given a check-and-fall-back guard for exactly these legacy shapes (#8636).
  Covers which legacy shape is reachable (unsorted pre-0.10 manifests pass every commit-time
  check; duplicate-id manifests are largely blocked by `check_fragment_ids`, whose `windows(2)`
  scan only detects *adjacent* duplicates), and how consequences differ by caller -
  `take.rs:305` re-checks the returned id and so drops rows, while `index/scalar.rs:233` does
  not and can train an index on the wrong fragments. **Flagged explicitly as a static finding,
  not a demonstrated defect**: read at `v11.0.0-beta.16`, not reproduced, and not a reported
  upstream issue. Notes that the upstream test which appears to cover this varies only the query
  array order, not the manifest order.

## [0.16.0] - 2026-08-21

### Changed

- Re-grounded from `v11.0.0-beta.6` to `v11.0.0-beta.16` (91 commits, 1 newly
  `breaking-change`-labeled PR: #8235).
- v11 delta figures re-grounded: 222 commits / 13 breaking PRs (accurate at beta.6) ->
  **313 commits / 14 breaking PRs** at beta.16. All other structural invariants re-verified
  and unchanged (26 crates, 16 transaction ops, `num_retries` 20, `next => 2.3` / default 2.1,
  arrow 58, datafusion 54, MSRV 1.91.0, Edition 2024, Python 3.10+, manifest feature flags).
- **Corrected:** "No new `LANCE_*` env vars landed in v11" was false in two places. `LANCE_DISABLE_AMX`
  (runtime kill switch) and `LANCE_AMX_FP16_CC` (build-time compiler override) both landed in
  beta.16. Added the grep trap that `LANCE_AMX_CFG_*` / `LANCE_AMX_TILE_COUNT` are C macros,
  not env vars.
- **Corrected:** the v10 external-manifest note is superseded by #8499 - object storage is now
  authoritative, the external store's put-if-not-exists is a *reservation* rather than the
  commit point, and a stored ETag must be ignored rather than trusted (a retained one makes
  readers reject a good manifest with `Manifest e_tag mismatch`).
- **Corrected:** "stable row IDs cannot be turned on later" is superseded by
  `Dataset::migrate_to_stable_row_ids` (#8521).
- Three citations retargeted: `rust/lance/src/dataset/transaction.rs` was deleted upstream
  (#8053/#8054/#8056); the code now lives in `rust/lance-table/src/transaction/`. Documented
  that the `lance::dataset::transaction` re-export shim survives, so the common surface holds.
- Java SDK doc link fixed: `lance-format.github.io/lance-java-doc` 404s; upstream points at
  javadoc.io. Added the canonical `lance.org` docs domain.
- `references/ops.md` proto list completed (12 protos exist, 9 were listed).
- `references/maintenance.md` mirror-deviation #3 corrected: the trailing-newline hook adds a
  byte to all **four** `.drawio.svg` diagrams, not one; recorded the two-step normalization that
  reproduces the mirror byte-for-byte.
- `references/performance.md` Part A provenance updated - `guide/performance.md` changed again
  at beta.16 (+29 lines, AMX).
- Part B: the fsync-wrapper cost "was not detectable" is superseded by a measured **+4.2%**
  (5.54 s on a 130.86 s sync, macOS `F_FULLFSYNC`), with the per-file amortization that explains it.
- Refreshed the 4 stale files in the `references/docs/` mirror; counts unchanged (45 md + 4 svg).

### Added

- AMX-FP16 IVF acceleration: the three shape gates, the switch from approximate to **exact**
  partition assignment (recall and assignments both change), the `LANCE_DISABLE_AMX` kill switch,
  and the clang >= 16 / gcc >= 13 build requirement.
- `version_refs()` / `VersionRef`; `Dataset::migrate_to_stable_row_ids`; compaction
  `max_source_rows` / `max_source_bytes` / `excluded_fragment_ids`; `FileFragment::write_columns`.
- MemWAL shard pruning; `VersionAuxData`; `IndexSection`; `TableIdentifier`'s two remote
  reconstruction modes; Substrait filter/aggregate parsing; the `DiskAnn` proto stage.
- `file+uring://` added to the object-store scheme list, with the note that `is_local()` covers it.
- Cache and observability guidance: Lance has **no resident data cache**; shared `Arc<Session>`
  via `DatasetBuilder::with_session`; `prewarm_index` for cold search (and what it does not fix);
  `MergeStats` and `Scanner::scan_stats_callback`.
- The `merge_insert` "Ambiguous merge inserts are prohibited" error documented as deterministic
  and **non-retryable** - an OCC retry loop must not swallow it.
- `changelog-v7-v11.md` gained a beta.6 -> beta.16 delta splitting the correctness fixes into
  **heals-on-upgrade** vs **requires rewriting data on disk**, plus the #7966 ZoneMap caveat
  (reads heal, pruning selectivity does not until reindex).

### Security

- Noted #8613: `h2` bumped to 0.4.16 for RUSTSEC-2026-0258.

Verified against: lance-format/lance@v11.0.0-beta.16

## [0.15.0] - 2026-08-12

### Changed

- Re-grounded from `v11.0.0-beta.2` to `v11.0.0-beta.6` (94 commits, 4 newly
  `breaking-change`-labeled PRs: #8027, #8028, #8347, #8360).
- **Breaking (upstream):** the stable pin moved `v9.0.1` -> `v10.0.0`. `v10.0.0` final **was**
  tagged (2026-08-08, annotated, on `release/v10.0`, not an ancestor of `main`); the skill's
  previous claim that it never was is corrected everywhere it appeared. crates.io and PyPI both
  now carry `10.0.0`.
- **Breaking (format):** the v11 delta's "manifest feature flags unchanged" is corrected -
  `FLAG_MEM_WAL_INDEX_CATCHUP` (bit 128) is new and `FLAG_UNKNOWN` moved 128 -> 256. The
  feature-flag table gained bits 32, 64, and 128 (32 and 64 existed before v11 but were
  undocumented).
- v11 delta figures re-grounded: 128 commits / nine breaking PRs (accurate at beta.2) -> 222
  commits / 13 breaking PRs at beta.6.
- Vector-index storage spec: `__ex_codes` -> `__blocked_ex_codes` with a new sizing formula
  (readers still accept the old column); `__pq_code` and `_rabit_codes` sizings corrected; all
  storage columns are now nullable.
- `cos://` no longer routes to `ConditionalPutCommitHandler` - it has a dedicated
  `TencentCosCommitHandler` that fails closed.
- Part B's governing rule softened from "don't tune the store" to "minimize remote calls first",
  presenting upstream's new remote-scan tuning table as a legitimate second move.
- Refreshed the 13 stale files in the `references/docs/` mirror; all directory counts verified
  unchanged (45 md + 4 svg).

### Added

- Scan concurrency controls (`fragment_readahead`, `batch_readahead`, `scan_in_order`,
  `io_buffer_size`) with upstream's suggested starting values and the two counter-intuitive
  caveats (`scan_in_order` does not serialize fragment reads; lowering `batch_size` may not
  shrink the request).
- FTS tokenization surface: `lance.tokenize` / `FtsToken`, the `max_token_length` tri-state,
  `analyze_plan` tokenized-query output, and the conditions under which `CompoundQueryExec`
  abandons the posting-backed scorer.
- Stable row ids in hand-assembled distributed transactions (`row_id_meta`, never minting ids,
  leaving `*_version_meta` as `None`); the Tencent COS `commit_lock` requirement; nested Blob v2
  fields; `preserves_nullability` and its conflict rule.
- A consolidated roundup of v11's eleven silent-corruption and wrong-results fixes, each with its
  triggering condition.
- New changelog section for the `v11.0.0-beta.2 -> v11.0.0-beta.6` delta.
- Field-verified operational findings, each re-grounded at beta.6 before inclusion: the FTS
  `Fixed32` empty-segment merge failure (scoped to `format_version=1`/legacy), bfloat16 rejection
  on both build and query paths, the three-round-trip commit anatomy, `merge_insert` composite-key
  indexing, compaction convergence, the unindexed-backlog API, and ngram relevance/RAM cost.

### Fixed

- `MAX_INLINE_TRANSACTION_BYTES` is gated on `#[cfg(not(test))]`, not "release builds", so every
  non-test build gets 20 MiB.
- Mirror-exclusion note: Spark/Ray/Trino were deleted from the checked-in nav (#8419) rather than
  assembled at build time.
- Part A provenance: `guide/performance.md` is no longer byte-unchanged since `v9.1.0-beta.8` -
  it changed at `v11.0.0-beta.4`.
- `maintenance.md` now documents a third expected pre-commit deviation (a trailing newline added
  to the `.drawio.svg`).
- Corrected a pond-derived lead before publication: the ZoneMap/tz-aware-timestamp issue is a
  latent coercion smell, **not** a "returns 0 rows" bug - the pinned `datafusion-common` 54.x
  `partial_cmp` is timezone-blind, so pruning is currently correct.

Verified against: lance-format/lance@v11.0.0-beta.6

## [0.14.1] - 2026-08-07

### Fixed

- Completeness audit against the pre-split originals rescued three items that the condensation
  would otherwise have dropped: the OpenTelemetry-metrics subsection (the only text unique to
  the embedded performance-guide copy, now its own Part A section); the "authoritative in-repo
  sources" pointer from the old reference preamble (now in the `lance-reference.md` index); and
  the generated per-language SDK docs URL (restored to the ecosystem paragraph in `SKILL.md`).
  Verified by line-level `comm` against `git show HEAD:` originals: zero content lines, zero of
  57 section headings, zero of 271 PR citations, and zero of 48 measured-figure tokens lost.

## [0.14.0] - 2026-08-07

### Changed
- Consolidated the skill's structure. No upstream re-grounding: still `v11.0.0-beta.2`, and no
  benchmark-verified figure was removed - every relocated fact is cited below.
- `SKILL.md` 32,029 -> ~14.6k chars. The four "What's new in v9 / v9.1 / v10 / v11" sections
  collapsed into a `Version landscape` table (one row per major, naming its breaking theme) plus
  a compressed `The v11 delta`; all 66 PR citations were verified present in the reference files
  before cutting. The 45-row docs-mirror file map became one row per directory with a file count
  (the "Not mirrored" paragraph is unchanged, verbatim). The crate-workspace section, the
  release-train prose, and `Navigating the reference` were compressed; the sparse
  auto-selection deep dive was dropped in favour of the fuller treatment in section 3.1.
- `references/lance-reference.md` (170,653 chars) split into five topic files, each with its own
  table of contents: `format-file.md` (sections 1-4), `format-table.md` (5-10), `indexes.md`
  (11-12), `ops.md` (13, 15, 16), `changelog-v7-v11.md` (14). `lance-reference.md` is now a stub
  mapping the original 16 section numbers onto those files, so existing "see section N"
  cross-references still resolve.
- `references/performance.md` 69,077 -> ~38.6k chars, and gained a table of contents. Part A no
  longer re-copies text that already exists byte-identically in `references/docs/`: the embedded
  `guide/performance.md` copy, the full-text-search "Performance Tips", the JSON "Performance
  Considerations", and the transaction "CreateIndex Compatibility" block are replaced by a
  routing table pointing at the mirrored files and headings. The OpenTelemetry-metrics
  subsection, which was the only content unique to the embedded copy, was relocated to its own
  section in Part A. Both "Performance changes not in the guide" subsections and all of Part B
  are unchanged.

### Added
- `references/maintenance.md` - the refresh workflow moved out of `SKILL.md`, extended with the
  reference-file layout table.


## [0.13.0] - 2026-08-07

### Changed
- Re-grounded against upstream `v10.0.0-beta.7` -> `v11.0.0-beta.2` (128 commits, 9
  breaking-labeled PRs). Retitled "Lance v10" -> "Lance v11"; bumped the workspace pin,
  permalink base, and citation tag across `SKILL.md`, both references, and `skill-card.md`.
- **Release-line correction**: `v10.0.0` FINAL was never tagged - `release/v10.0` sits at
  `10.0.0-rc.3` and branched exactly at `v10.0.0-beta.7`. The `10.1.0-beta.*` line was
  re-rooted in place as `11.0.0-beta.*` by the release bot; both release-root tags share
  base `10.0.0-rc.1`. The stable pin is now **`v9.0.1`** (2026-08-06), matching crates.io.
- **Module reorganization** (section 2.1, new): `lance-encoding::version` deleted -
  `LanceFileVersion` and `ConcreteFileVersion` now live in `lance-file::version`. `FileWriter`
  became an enum, `lance_io::encodings` and `lance-encoding::previous` were removed, and
  per-version `versions/v2_{0,1,2,3}` / `array_encoding` trees replaced them.
- **Breaking (format-level)**: fragment ids are now a dataset-lifetime high-water mark -
  overwrite no longer restarts at 0, overwrite fragments carrying a deletion file are
  rejected, and duplicate fragment ids block all commits (#8206).
- Commit-handler routing table corrected: `goosefs` (#8134) plus the already-missing
  `abfss` / `tos` / `shared-memory` all route to `ConditionalPutCommitHandler`.
- Dependency pins: `opendal 0.57 -> 0.58.1`, `object_store_opendal 0.58`; `strum` and
  `goosefs-sdk` dropped from workspace deps; `rust-stemmers -> frostem` (Greek panic fix).
- Doc mirror resynced: 4 changed files (`guide/migration.md`, `guide/object_store.md`,
  `guide/observability.md`, `quickstart/full-text-search.md`). No files added or removed.
- Compressed the v9/v8/v7 history sections in `SKILL.md` to make room for v11 under the
  repo's 500-line cap; stripped stale "(current tag)" labels from historical delta headings.

### Added
- New FTS index axis: `DocumentGranularity` (ROW / LIST_ELEMENT), `posting_format_version`,
  the `_doc_index` column, and `list_element` as a third trigger requiring FTS format v3.
- Zone map `has_null_bitmap` (making `IS NOT NULL` scan-free) and all-type support, with
  null counts only for nested types.
- Compound FTS scoring core - Boolean/Phrase/Boost composition, public `CompoundQueryExec`,
  cost-ordered conjunctions; `AND` clauses are scoring `MUST` clauses that affect `_score`.
- Manifest transaction spilling above 20 MiB; pluggable cache-backend registry (`moka://`);
  `CacheBackend::deep_size_of_entries` and its effect on reported cache sizes.
- Object store: `aws_provider_scheme` (token / ecs / irsa); the GooseFS conditional-put
  migration and its mixed-version overwrite hazard; multipart-retry part-identity fix.
- Query-time vector knobs `nprobes` and `refine_factor`; the `when_not_matched_by_source_*`
  merge-insert family; the FTS 18-language roster and text-vs-json document types;
  jieba/lindera user dictionaries; MemWAL GC and reader-consistency semantics; dense-vs-sparse
  data-overlay shapes; the JSON projection limitation; the Blob v2 rewrite-migration path; and
  the wider ecosystem (Flink, pglance, Lance Graph, named catalog implementations).
- `performance.md`: a new "Local-filesystem crash safety and recovery" subsection (no
  fallback to version N-1 on a corrupt manifest; `latest_version_hint.json` is not read on
  local; `count_rows` cannot validate integrity), plus auto-cleanup gating economics,
  `LANCE_MEM_POOL_SIZE` sizing, `optimize_indices` delta-collapse semantics, WORM/Object Lock
  incompatibility, and `memory://` vs `shared-memory://` test-isolation traps.
- `lance-reference.md`: the SQL/DataFusion surface has no kNN; dataset *creation* is not
  OCC-protected; the FRI is not per-index coverage; NGRAM vs FM-Index matching semantics; the
  benign IVF_PQ empty-partition warning; volume-independent scalar-index pushdown.

### Fixed
- Sparse-writer citation corrected to `encoding.md:373-375`.
- ACORN-1 nuance added: skipped when the prefilter mask passes all rows or leaves under 10%,
  with fallback to `search_basic`.

Verified against: lance-format/lance@v11.0.0-beta.2

## [0.12.0] - 2026-07-30

### Changed
- Re-grounded against upstream `v9.1.0-beta.8` -> `v10.0.0-beta.7` (78 commits, 4 breaking);
  bumped workspace version pin, permalink base, and citation tag. Retitled "Lance v9" ->
  "Lance v10". Resynced the 5 changed doc-mirror files.
- **Release-line correction**: `v9.0.0` FINAL shipped 2026-07-24 and is now the stable pin
  (supersedes `v8.0.0`). The `9.1.0-beta.*` dev line was mechanically re-rooted as
  `10.0.0-beta.*` by CI breaking-change detection, so `v9.1.0` was never tagged. `v9.0.0`
  lives on `release/v9.0` (now `9.0.1-beta.0`) and is not an ancestor of `main`. crates.io
  publishes finals only - newest is `lance 9.0.0`, so beta pins are git dependencies.
- **Crate pins**: `lance-arrow-stats` is also pinned `=58.0.0` (the skill previously named only
  `lance-arrow-scalar`); new workspace dep `blake3 1.8.5`.
- File format 2.3: sparse structural pages are now **auto-selected** by the 2.3 writer under a
  rep/def budget heuristic (PR #7756); `structural-encoding` reworded "Select" -> "Force".
- MemWAL vocabulary overhaul across spec, Rust, Python, Java, and proto (section 10), with a
  full rename map.
- `performance.md`: corrected the "`cleanup_older_than` defaults to ~1 hour" claim - Python
  `cleanup_old_versions` defaults `older_than` to 14 days; the 3600s figure is the docs'
  `lance.auto_cleanup.older_than` example, not a library default.

### Added
- Section 14: `v9.1.0-beta.8 -> v10.0.0-beta.7` delta subsection.
- Section 3.6: `ConcreteFileVersion` exact-identity type, the DataFile encode/decode wire
  table, and the byte-exact writer fixtures.
- Section 3.5: `read_blob_ranges` as the fourth blob read path, plus the null-preservation
  signature table.
- Section 9.4: cache keys and backend - `CACHE_KEY_FORMAT = "blake3-128-v1"`, removed cache
  APIs, `QuickCacheBackend`, and the per-shard admission ceiling that silently refuses
  oversized entries.
- Section 11.1: ACORN-1 prefiltered HNSW traversal (opt-in, `approx_mode="fast"`) with its
  documented recall regression; vector append across heterogeneous segment models.
- Section 11.2/12: segmented index family extended to BLOOMFILTER, RTREE, NGRAM, LABEL_LIST;
  `IndexSegment::new` signature change; the NGRAM merge-before-commit constraint.
- Section 11.3: FTS `total_tokens` metadata key, `LANCE_FTS_SEARCH_CHUNK`, top-k row-id
  resolution, deterministic tie ordering, `bm25_search` removal.
- Sections 5.5/9.1: data-overlay/index correctness work and the proto-rename impact.
- Section 13: `memory://` fix, env-var validation, tokio-shutdown fix, and the namespace
  error-classification change.
- `performance.md` Part A: a source-derived "Performance changes not in the guide" subsection
  (cache admission ceiling, FTS chunking, top-k row-id resolution, concurrent segment commit).
- `performance.md` Part B: `Dataset::versions()` O(history) manifest reads, the 7-day
  unverified-file floor, transient index-set doubling on `replace=true`, typed commit-conflict
  errors, `merge_insert` mode switching on source schema shape, bitmap-index prefix-LIKE
  erroring, blob-column SQL descriptors, and local-FS durability delegation.
- SKILL.md: an explicit note that `docs/src/images/` is not mirrored.

### Changed (breaking, upstream)
- **Blob APIs preserve null selections** (#7903, the PR that triggered the v10 bump): Rust
  `take_blobs*` -> `Vec<Option<BlobFile>>`, `ReadBlob::data` -> `Option<Bytes>`; Python
  `read_blobs -> List[Tuple[int, Optional[bytes]]]`, `take_blobs -> List[Optional[BlobFile]]`;
  Java lists may contain null elements.
- **Cache keys are an opaque 16-byte BLAKE3 digest** (#7878) - all warm/persisted caches
  cold-miss after upgrade, no legacy fallback; `invalidate_prefix`, `LanceCache::keys`, and
  `Session::*_cache_keys` removed.
- **`IndexRemapperOptions::create_remapper` is now async**, returning
  `Result<Option<Box<dyn IndexRemapper>>>` (#7778).
- **MemWAL renames** (#7943, #7957): proto `FlushedGeneration` -> `SsTable`,
  `MergedGeneration` -> `CompactedSsTable`, `flushed_generations` -> `sstables`,
  `merged_generations` -> `compacted_sstables`. Wire-compatible (field numbers unchanged) but
  every generated symbol and binding name changes; no deprecation shims.
- `LanceFileVersion::try_from_major_minor` and `to_numbers` removed (#7879).
- `InvertedPartition::bm25_search` removed (#7863).
- Directory namespace no longer collapses storage failures into `TableNotFound` (#7931).

### Security
- `quinn-proto` 0.11.14 -> 0.11.16 (Dependabot security alert) across the root workspace,
  `/python`, and `/java/lance-jni` (#7983, #7984, #7982).

Verified against: lance-format/lance@v10.0.0-beta.7

## [0.11.1] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format

## [0.11.0] - 2026-07-22

### Changed
- Re-grounded against upstream tag `v9.0.0-beta.18` -> `v9.1.0-beta.8` (127-commit range,
  1 breaking-labeled PR); bumped workspace version pin, permalink base, and citation tag.
  Copied the changed doc-mirror subset (12 files + 1 new) from the new tag.
- **Crate workspace 25 -> 26**: new `lance-index-core` crate (PR #7713).
- **Transaction ops 15 -> 16**: new `DataOverlay` operation (env-gated unstable; release
  builds refuse overlay datasets), sections 9.1 + 5.5.
- **datafusion 53 -> 54** (PR #7793); geodatafusion 0.4 -> 0.5. Build toolchain (not MSRV)
  1.91 -> 1.97 (#7712); MSRV `rust-version` unchanged at 1.91.0. Python min still 3.10
  (3.14 support added, #7728).
- File-format 2.3 is **no longer scaffolding-only**: sparse structural pages shipped
  (PR #7889, `sparse.rs`); `lance-encoding:structural-encoding=sparse` selects it (requires
  2.3). Corrected the "6 refs vs 98, no distinct encodings" claim (now 59 vs 97).

### Added
- Section 5.5: **Data Overlay Files** - cell-level `(row offset, field)` updates without
  rewriting base data files; new `DataOverlay` transaction op, feature flag 64, spec
  `data_overlay_file.md` (unstable, `LANCE_ENABLE_UNSTABLE_DATA_OVERLAY_FILES`) (PR #7535/#7536).
- Section 3.1: sparse structural pages / `sparse` encoding (Lance 2.3, PR #7889).
- Section 11.2: zonemap + bloom-filter indexes now carry a `null_bitmap` -> **exact IS NULL**.
- Section 11.3: FTS configurable posting `block_size` (128/256, 256 experimental, format-v3
  gate) (PR #7466); FTS code-analyzer tokenizer (PR #7681); nested-field FTS (PR #7686);
  bulk MAXSCORE / impact-skip / conjunction paths (#7602/#7603/#7624).
- OpenTelemetry metrics for Python (`instrument_lance_metrics`, `pylance[otel]`, PR #7537),
  noted in `performance.md`.
- Section 14: new `v9.0.0-beta.18 -> v9.1.0-beta.8 delta` subsection.
- `references/docs/format/table/data_overlay_file.md` mirrored; SKILL.md format-specs file map
  gains its row.

### Changed (breaking, upstream)
- **FTS/inverted-index creation takes a `block_size` param** (compressed posting blocks;
  128/256, default 128; 512 rejected). `block_size=256` and the code analyzer require FTS
  on-disk **format v3** (PR #7466, #7866). Section 11.3.

Verified against: lance-format/lance@v9.1.0-beta.8

## [0.10.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.10.0] - 2026-07-08

### Added
- `references/docs/` - a verbatim mirror of the official docs (`docs/src` at the tracked
  tag): all 14 guides, 4 quickstarts, the complete format spec tree (file / table / index,
  including the 4 index-lifecycle SVG diagrams), and `integrations/datafusion.md` -
  48 files, unedited. Ends doc cherry-picking: every official page is now directly
  loadable from the skill.
- `references/performance.md` - all official performance guidance combined in one
  document (the full performance guide incl. the new Fragment Sizing section, the FTS
  quickstart performance tips, JSON performance considerations, and the
  CreateIndex-compatibility passage from the transaction spec), followed by a
  field-verified Part B: benchmark-backed remote-storage practices (commit count as the
  cost unit, append vs merge_insert, index-fold batching, `fast_search` recall rule,
  cleanup gating, manifest-not-scan metadata questions, narrow-column materialization,
  version-gated v7/v8/v9 behavior, benchmarking traps). Part B's governing rule: leave
  store knobs at defaults and optimize by minimizing remote calls.
- SKILL.md: full routing file map for the docs mirror, a "Performance questions" section,
  and a three-layer reference navigation intro.
- Section 14: new `v9.0.0-beta.16 -> v9.0.0-beta.18 delta` subsection (36 commits, no
  breaking changes; pylance prewarm segment selection #7677, object-store metrics #7533,
  RLE v2 widths #7376, FTS/MemWAL/JSON fixes).

### Changed
- Re-grounded against upstream tag `v9.0.0-beta.16` -> `v9.0.0-beta.18`; bumped workspace
  version pin, permalink base, and citation tag. Copied doc files verified identical
  between the tags except `guide/performance.md` (+31 lines, Fragment Sizing),
  `guide/read_and_write.md` (cleanup + auto-cleanup docs), and the new
  `guide/observability.md`.
- Maintenance instructions now cover refreshing the docs mirror and performance.md at
  each version bump.

Verified against: lance-format/lance@v9.0.0-beta.18

## [0.9.0] - 2026-07-06

### Changed
- Re-grounded against upstream tag `v9.0.0-beta.10` -> `v9.0.0-beta.16` (commit
  `78a814b6b`); bumped workspace version pin, permalink base, and citation tag.
  58-commit range, 1 breaking change. All structural invariants reverified
  unchanged: 25 crates, arrow 58, datafusion 53, opendal 0.57, jieba-rs 0.10,
  itertools 0.14, lance-namespace-reqwest-client 0.8.6, rust 1.91.0, resolver 3,
  edition 2024, version enum (`Next => 2.3`, default `V2_1`), 15 transaction ops,
  `CommitConfig num_retries = 20`.
- SKILL.md: `v8.0.0` FINAL shipped 2026-07-01 (was "rc.3, no final tag yet") -
  use `v8.0.0` as the stable pin.
- Section 3.5: blob read APIs reworked in the docs (PR #7530, #7558) - `read_blobs`
  (full payloads, batched through the scheduler) is now the primary path,
  `take_blobs` reserved for streaming/seeking, `scanner(blob_handling="all_binary")`
  for Arrow binary columns. Added Blob v2 auto-tiering defaults (<16 KiB inline /
  mid-size shared `.blob` sidecar / >2 MiB dedicated) and the new
  `lance-encoding:blob-pack-file-size-threshold` field-metadata key (PR #7322).
- Section 13: per-base `storage_options` scoping via `base_<id>.<key>` keys, with
  `initial_bases` id assignment and `base_store_params` precedence (PR #7608).

### Added
- Section 14: new `v9.0.0-beta.10 -> v9.0.0-beta.16 delta` subsection.
- Section 11.2: ZoneMap min/max read without a scan (`zonemap_value_range`, PR #7463);
  BTREE + ZONEMAP scalar indices now accept `large_string`/`LargeUtf8` (PR #7525).
- Section 6: schema evolution now allows adding all-null `Map` columns (PR #7462);
  multi-base merge-insert with target-base routing (PR #7610).
- Section 10: prefiltered LSM vector + FTS search across base/flushed/in-memory
  mem-wal sources (PR #7138).
- DirectoryNamespace now implements `update_table` / `delete_from_table` (PR #6923)
  and `alter_transaction` (PR #6974).

### Changed (breaking, upstream)
- FTS / inverted indexes now default to on-disk **format v2** (PR #7512, 9.0.0
  migration note) - `LANCE_FTS_FORMAT_VERSION` no longer controls new indexes; pass
  `format_version=1` for older-reader compatibility. Existing v1 indexes stay
  queryable and are maintained as v1 (append/optimize/mem-wal flush). Section 11.3.

Verified against: lance-format/lance@v9.0.0-beta.16

## [0.8.0] - 2026-07-01

### Changed
- Re-grounded against upstream tag `v8.0.0-beta.14` -> `v9.0.0-beta.10` (commit
  `e25b71e74`); retitled "Lance v8 reference" -> "Lance v9 reference", bumped the
  workspace version pin, permalink base, and citation tag. 129-commit range, major
  version boundary. All structural invariants reverified unchanged: 25 crates, arrow 58,
  datafusion 53, opendal 0.57, jieba-rs 0.10, rust 1.91.0, resolver 3, edition 2024,
  version enum (`Next => 2.3`, default `V2_1`), 15 transaction ops, `CommitConfig
  num_retries = 20`.
- The v9 major bump is auto-triggered by `ci/check_breaking_changes.py` (GitHub
  `breaking-change` label detection), fired by #7158 and #7345 - not by the FMIndex rename.
- Dep pins: `lance-namespace-reqwest-client` 0.8.4 -> 0.8.6; `itertools` 0.13 -> 0.14.
  pylance runtime `lance-namespace>=0.8.5,<0.9` unchanged.
- Section 3.1: docs version table (`file/versioning.md`) now lists **2.3 as unstable** and
  no longer labels 2.2 unstable (was "docs still list only 2.2").
- Section 3.3: miniblock value chunks now tunable up to 32k via `LANCE_MINIBLOCK_MAX_VALUES`
  (PR #7356; default stays 4096).
- Section 7: `cleanup` / cleanup-explain now exposed to Python and Java (PR #7248).
- Section 6: `alter_columns` now allows Dict <-> value-type casts (PR #7289).

### Added
- Section 14: new "v8.0.0-beta.14 -> v9.0.0-beta.10 delta (major-version boundary)"
  subsection covering the three breaking changes, the `as_vector_index` removal, and
  net-new features.
- SKILL.md: note that v8.0.0 is the concurrent stabilizing release (rc.3) for users who
  need a stable pin instead of the v9 dev betas.
- Section 11.1: hamming clustering / near-dup detection utility over 64-bit binary hashes
  (`pairwise_hamming_distance`, `UnionFind`, `hamming_clustering_for_ivf_partition`,
  PR #7379); COUNT(*) pushdown now works on stable-row-id datasets (PR #7360).
- Section 3.5: per-column blob inline/dedicated thresholds
  (`lance-encoding:blob-inline-size-threshold` / `...-dedicated-size-threshold`, PR #7269).
- Section 11.2: ngram index now accelerates regex and infix LIKE (PR #7139).
- Section 11.3: ICU split tokenizer variant `icu/split` (PR #7474); mixed-language FTS stop
  words (PR #7324).
- Section 12: distributed LabelList scalar index builds (PR #7223).

### Removed
- Section 11.1: `as_vector_index` removed from the public `Index` trait (PR #7392);
  callers downcast via `as_any()`.

### Changed (breaking, upstream)
- FM-Index proto message renamed `FMIndexIndexDetails` -> `FMIndexDetails` (PR #7397) -
  existing FM indexes become unreadable (sections 11.2, 16).
- Python 3.9 dropped; minimum is now 3.10 (PR #7345) - section 2 binding note.
- `alter_columns` cast now fails-fast when the column has an attached index; drop the index
  first (PR #7158) - section 6.

Verified against: lance-format/lance@v9.0.0-beta.10

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
