# Lance changelog - v7 -> v12 (section 14)

Part of the Lance v12 reference (`lance-format/lance@v12.0.0-beta.15`). Citations are `path:line`
relative to the repo root; build a permalink as
`https://github.com/lance-format/lance/blob/v12.0.0-beta.15/<path>`. Line numbers drift between
tags - treat them as approximate. Cross-references written as "section N" use the original
16-section numbering; `lance-reference.md` maps every number to its file.

**Release-line shape.** The major is bumped by a bot, not a human: `ci/publish_beta.sh:65,87`
re-roots at `MAJOR+1` whenever any PR since the release root carries the GitHub
`breaking-change` label (`ci/check_breaking_changes.py:31`). The marker is the **label**, not a
conventional-commit `!` - of the 13 labeled PRs in the v11 window (#8024, #8025, #8026, #8027,
#8028, #8051, #8095, #8159, #8172, #8188, #8206, #8347, #8360) only two carry `!` in the
subject. It has now fired on two
consecutive lines: `9.1.0-beta.*` -> `10.0.0-beta.*` (2026-07-23), then `10.1.0-beta.*` ->
`11.0.0-beta.*` (2026-08-05, `649076df1 chore: bump to 11.0.0-beta.1 based on breaking change
detection`). So **neither `v9.1.0` nor `v10.1.0` was ever released**, and `v10.1.0-beta.2` is
the direct ancestor of `v11.0.0-beta.1`, one bump commit apart. The re-root renumbers in place:
`release-root/10.1.0-beta.N` and `release-root/11.0.0-beta.N` point at the same commit
(`ee0a60d0c`), both recording `Base: 10.0.0-rc.1`.

**`v10.0.0` final was tagged on 2026-08-08** - an annotated, PGP-signed tag ("Release version
10.0.0") on `release/v10.0`, one commit past `v10.0.0-rc.3` (2026-08-02). That branch forked at
`v10.0.0-beta.7` and took one substantive backport (`10d0c9f2e fix: backport encoding and FTS
fixes to release/v10.0`, #8146). It is **not** an ancestor of `main` - finals are cut on
`release/vX.Y` branches, so that is normal. `v10.0.0-beta.7` **is** an ancestor of
`v11.0.0-beta.16`, but `v10.0.0-rc.3` and `v10.0.0` are not.

**`v10.0.0` is the stable pin** (2026-08-08, superseding `v9.0.1`), and it is what GitHub
Releases marks `Latest`. `v9.0.1` (2026-08-06, superseding `v9.0.0`, 2026-07-24) shipped with
five sibling patch finals that day - `v8.0.1`, `v7.1.0`, `v6.1.0`, `v4.0.2`, `v3.0.2` - each on
its own `release/vX.Y` branch. `v5.0.0` still has no final despite `v5.0.0-rc.2`. crates.io
publishes **finals only** (`max_stable_version` = `10.0.0`; no 11.x, and the only pre-release
among ~186 versions is the ancient `0.0.1-alpha0`); PyPI `pylance` is likewise at `10.0.0`. So
any beta pin is a git dependency; beta artifacts publish to fury.io
(`.github/workflows/publish-beta.yml:114`) under the renamed org,
`https://pypi.fury.io/lance-format`.

## Contents

- [The v7.1.0-beta.1 delta](#the-v710-beta1-delta)
- [The v7.1.0-beta.2 delta](#the-v710-beta2-delta)
- [The v7.1.0-beta.2 -> v7.2.0-beta.5 delta](#the-v710-beta2---v720-beta5-delta)
- [The v7.2.0-beta.5 -> v8.0.0-beta.9 delta (major-version boundary)](#the-v720-beta5---v800-beta9-delta-major-version-boundary)
- [The v8.0.0-beta.9 -> v8.0.0-beta.14 delta](#the-v800-beta9---v800-beta14-delta)
- [The v8.0.0-beta.14 -> v9.0.0-beta.10 delta (v8 -> v9 major boundary)](#the-v800-beta14---v900-beta10-delta-v8---v9-major-boundary)
- [The v9.0.0-beta.10 -> v9.0.0-beta.16 delta](#the-v900-beta10---v900-beta16-delta)
- [The v9.0.0-beta.16 -> v9.0.0-beta.18 delta](#the-v900-beta16---v900-beta18-delta)
- [The v9.0.0-beta.18 -> v9.1.0-beta.8 delta](#the-v900-beta18---v910-beta8-delta)
- [The v9.1.0-beta.8 -> v10.0.0-beta.7 delta](#the-v910-beta8---v1000-beta7-delta)
- [The v10.0.0-beta.7 -> v11.0.0-beta.2 delta](#the-v1000-beta7---v1100-beta2-delta)
- [The v11.0.0-beta.2 -> v11.0.0-beta.6 delta](#the-v1100-beta2---v1100-beta6-delta)
- [The v11.0.0-beta.6 -> v11.0.0-beta.16 delta (the v11 beta frontier)](#the-v1100-beta6---v1100-beta16-delta-the-v11-beta-frontier)
- [v11 silent-corruption and wrong-results fixes](#v11-silent-corruption-and-wrong-results-fixes)
- [v11.0.0 final (the beta.16 -> final delta)](#v1100-final-the-beta16---final-delta)
- [v12 (release-root/12.0.0-beta.N -> v12.0.0-beta.6)](#v12-release-root1200-betan---v1200-beta6)
- [The v12.0.0-beta.6 -> v12.0.0-beta.15 delta](#the-v1200-beta6---v1200-beta15-delta)

Other files: `format-file.md` (1-4), `format-table.md` (5-10), `indexes.md` (11-12),
`ops.md` (13, 15, 16).

---

## 14. What changed (v7 -> v12)

The v7 tag line ran `v7.0.0-beta.1` through `v7.0.0-beta.17`, then `v7.0.0-rc.1` and
`v7.0.0`. The v7.1 line opened at `v7.1.0-beta.1`, continued through `v7.1.0-beta.4` and
`v7.1.0-rc.1`; the v7.2 line ran through `v7.2.0-beta.5`; the **v8 line** ran through
`v8.0.0-beta.19` to `v8.0.0` final (2026-07-01); the **v9 line opened** (auto-bumped from
a `breaking-change`-labeled PR) and ran through `v9.0.0-rc.2` to **`v9.0.0` final** (2026-07-24,
on the `release/v9.0` branch, later `v9.0.1` on 2026-08-06 - **the current stable pin**); the
**v9.1 line opened** at `9.1.0-beta.0` when `v9.0.0-rc.1` was cut and ran to `9.1.0-beta.8`; on
2026-07-23 that same dev line was **mechanically re-rooted as `10.0.0-beta.*`** by the
breaking-change detector, so `v9.1.0` was never tagged; the **v10 line** ran to
`v10.0.0-beta.7`, then stabilization forked to `release/v10.0`, reached `v10.0.0-rc.3` and
shipped **`v10.0.0` final on 2026-08-08 - the current stable pin** - while `main` opened
`10.1.0-beta.1/2`; and on 2026-08-05 **that** line was re-rooted in place as `11.0.0-beta.*`, so
`v10.1.0` was never tagged. This section keeps
the full v7 history below (still useful context), the **v7.2.0-beta.5 -> v8.0.0-beta.9 delta**
(the v7->v8 major boundary), the **v8.0.0-beta.9 -> v8.0.0-beta.14 delta**, the
**v8.0.0-beta.14 -> v9.0.0-beta.10 delta** (the v8->v9 major boundary), the
**v9.0.0-beta.10 -> v9.0.0-beta.16 delta**, the **v9.0.0-beta.16 -> v9.0.0-beta.18 delta**,
the **v9.0.0-beta.18 -> v9.1.0-beta.8 delta**, the **v9.1.0-beta.8 -> v10.0.0-beta.7 delta**,
the **v10.0.0-beta.7 -> v11.0.0-beta.2 delta**, the **v11.0.0-beta.2 -> v11.0.0-beta.6 delta**,
and finally the **v11.0.0-beta.6 -> v11.0.0-beta.16 delta** (most important
for a v11 reader) plus a consolidated list of v11's silent-corruption and wrong-results fixes
at the very end.

**The v6 -> v7 breaking change.** `feat!: make dataset object store access base-aware`
(PR #6647, commit `456198cd`), immediately followed by the automated bump to `7.0.0-beta.1`.
Object-store access is now scoped to a dataset *base* instead of a flat global path -
groundwork for multi-base storage (hot/cold tiering, multi-region, shallow clones). The
related `refactor!: vendor the tokenizer stack into lance` (PR #6512) is what created the
`lance-tokenizer` crate.

**MemWAL / LSM** is the dominant v7 theme: the WAL appender/tailer primitives (PR #6669), the
`shared-memory://` object-store scheme, `ShardWriter` manual-compaction APIs (#6766), a
builder-style MemWAL init API (#6815), append-only tables without primary keys (#6848), and
`ShardSpec` renamed to `ShardingSpec` (#6813). See section 10 - MemWAL is experimental.

**Lance-native in-memory HNSW** for the MemWAL shard writer (PR #6795).

**Indexes** - segmented btree indexes (#6605), zonemap index segments (#6593), incremental /
segmented FTS index merging (#6737, #6790), distributed bitmap index build (#6598), segmented
inverted index build and search (#6305), FTS exec internals exposed for distributed planning
(#6648). The geo / RTree index and the `lance-geo` crate; an RTree index-type parsing fix
(#6568).

**Branches and tags** - branch/tag metadata maps and tag timestamps (PR #6364); the `tree/`
and `_refs/branches/` layout (section 7).

**Commits** - manifest version hint for fast latest-version lookup (PR #6752); uncommitted
delete transactions exposed (#6781); the `Clone` transaction (shallow / deep).

**Spec restructuring** - the lakehouse spec was formally split into separate catalog /
namespace / table / index specifications (PR #6750x), reflected in `docs/src/format/`.

### The v7.1.0-beta.1 delta

The 19 commits in `v7.0.0-beta.16..v7.1.0-beta.1` are mostly bug fixes and internal
performance work (serializable BTree/Bitmap/LabelList index caches, deterministic HNSW
graph builds, roaring range-iterator speedups). The user-facing additions:

- **Materialized-view namespace API** (PR #6891) - `create_materialized_view` and
  `refresh_materialized_view` on the `LanceNamespace` trait. A materialized view is a
  query / UDTF / chunker backed by a stored spec, with an optional initial refresh. The
  `RestNamespace` implements both (`POST /v1/materialized_view/{id}/create` and
  `/refresh`); `DirectoryNamespace` and the default trait return `not_supported`.
- **Typed vector index details** (PR #6099) - the `VectorIndexDetails` and
  `HnswParameters` messages moved into `protos/index.proto` (section 11.1).
- **Multi-base `write_fragments`** (PR #6855) - multi-base storage config is now reachable
  from the Python and Java `write_fragments` API, not just Rust.
- **Granular tracing targets** (PR #6853) - `pylance` emits trace events under a
  `lance::events::` prefix so they filter separately from log records; new
  `lance::dataset_events` and `lance::object_store::throttle` targets. Example:
  `LANCE_LOG="warn,lance::events::object_store::throttle=info"`
  (`docs/src/guide/performance.md`).
- **MemWAL** - a sharding evaluator (PR #6854), L0 flushed-generation dataset caching
  (PR #6816), and exact primary-key dedup fixes for LSM point lookup and vector search
  (PR #6881).

### The v7.1.0-beta.2 delta

Seven commits in `v7.1.0-beta.1..v7.1.0-beta.2`, mostly MemWAL correctness work plus one
workspace refactor:

- **New `lance-select` crate** (PR #6879, commit `52c6ac34`) - mask code (`RowAddrMask`,
  `NullableRowAddrMask`, `RowIdMask`, set types, `bitmap_to_ranges`/`ranges_to_bitmap`) and
  scalar-index expression-result types (`IndexExprResult`, `NullableIndexExprResult` with
  their `Not`/`BitAnd`/`BitOr` boolean algebra) were extracted from `lance-core` and
  `lance-index` into `rust/lance-select/`. Downstream filtering code and the new
  `index_expr_result` / `row_addr_mask` benches can now depend on masks without pulling in
  either larger crate.
- **MemWAL: build secondary indexes when flushing the active memtable** (PR #6901, commit
  `cee7d32f`) - `MemTableFlushHandler` previously called `flush`, persisting the data file
  and bloom filter but **building no secondary indexes**, and never received the shard's
  `index_configs` in the first place. Over flushed generations this made flushed vector rows
  invisible to `fast_search()` (a correctness bug for KNN, not just perf), and point lookups
  fell back to a full scan instead of routing through a scalar index. The fix threads
  `index_configs` into the handler and calls `flush_with_indexes` when any index is
  configured, while keeping plain `flush` when none are so empty-index shards avoid an extra
  pass.
- **MemWAL: per-source PK-hash block-list post-filter** (PR #6899, commit `77db998a`)
  fixes a stale-read in LSM vector search. `LsmGlobalPkDedupExec` (introduced in #6881) is
  exact only over candidates each source surfaces; if a primary key's fresh row is pushed
  out of its source's top-k by closer rows, the dedup never sees it and a superseded copy
  from an older generation can win. The fix makes staleness a per-source PK-hash post-filter
  (`PkHashFilterExec`) applied to each source's KNN *before* the cross-source union, so a
  stale row never reaches the merge. Each generation's membership is an
  `Arc<HashSet<u64>>` of PK hashes (`compute_pk_hash`, the same hash the dedup nodes use).
- **Docs** - new integrations landing page at `docs/src/integrations/index.md` (PR #6915);
  Java doc URL updated from `com.lancedb` to `org.lance` (#6467).

Note: there is **no Tantivy-FTS-removal commit in the v7 range**. Lance FTS at this tag is
already its own native inverted-index implementation; the tokenizer vendoring (#6512)
predates `v7.0.0-beta.1`. Do not attribute a Tantivy removal to v7.

### The v7.1.0-beta.2 -> v7.2.0-beta.5 delta

66 commits, **no breaking change** (no `!:` commit, no `BREAKING CHANGE` footer), **no new
crate** (still 24), **no new transaction op** (still 15), no proto change. User-facing
additions:

- **ICU FTS tokenizer** (PR #6956) - `base_tokenizer="icu"`, ICU4X dictionary segmentation
  with bundled data, no external model. A PR making ICU the default (#6968) was reverted
  (#7006); the default base tokenizer stays `simple`. See section 11.3.
- **Scalar-index fast search** (PR #6784) - `fast_search` routes through scalar/BTREE-indexed
  fragments and skips unindexed ones (not on legacy file version). See section 11.2.
- **Batched vector queries** (PR #6828) - `Scanner::nearest` takes a batch of query vectors
  and exposes a synthetic 0-based `query_index` column. See section 11.1.
- **Streaming IVF k-means** (PR #6913) - `streaming_sample_rate` / `streaming_coreset_rate` /
  `streaming_refine_passes` for bounded-memory IVF training. See section 11.1.
- **Arrow view-type support** (PR #6985) - `Utf8View` / `BinaryView` now encode (fixes an
  encoder `todo!()` panic) and coerce correctly in filters.
- **HuggingFace `download_mode`** (PR #7022) - storage-option keys `hf_download_mode` /
  `download_mode` select the OpenDAL `http` (default) or `xet` backend on the existing
  `hf://` provider; not a new object-store scheme.
- **MemWAL LSM local-scoring FTS** (PR #6951) - `LsmScanner::full_text_search(column, query, k)`,
  contained entirely in the `mem_wal` module.
- Dependency bumps: pylance `lance-namespace>=0.8.0,<0.9` (PR #7031), `opendal 0.57`
  (PR #7018), `jieba-rs 0.10` (PR #6955).
- Doc clarification: RaBitQ (RQ) is documented 1-bit-only with multi-bit as future work, and
  the RQ metadata schema gained a `code_dim` field (`docs/src/format/index/vector/index.md`).

Unchanged and reverified at this tag: 15 transaction ops, the scalar/vector index-type set,
all `protos/*.proto`, file-format `version.rs`, `rust-version 1.91.0`, `resolver 3`, edition
2024, `CommitConfig num_retries=20`, MemWAL still experimental.

### The v7.2.0-beta.5 -> v8.0.0-beta.9 delta (major-version boundary)

86 commits. This is a **major version bump** whose unifying theme is moving *every* index
build onto one segment-based lifecycle. **Six breaking changes** (`!:` commits):

- **`feat!: migrate bitmap to index segment based`** (PR #6869) - the defining v8 change.
  Bitmap now flows through the segment workflow; the old public Python Bitmap shard path
  (`create_scalar_index(..., fragment_ids=)` + `merge_index_metadata(..., "BITMAP")`) "is no
  longer exposed; callers should use the segment workflow instead." `execute_uncommitted`
  writes canonical `bitmap_page_lookup.lance` segment roots
  (`rust/lance-index/src/scalar/bitmap.rs:59`).
- **`refactor!: remove index segment builder`** (PR #6997) - the `IndexSegmentBuilder` API
  was removed from Rust, Python, and Java; staged publishing routes through
  `create_index_uncommitted` / `execute_uncommitted` + `merge_existing_index_segments` +
  `commit_existing_index_segments`. `build_all()` and `target_segment_bytes` size-based
  grouping are gone with no direct replacement (`docs/src/guide/migration.md` "7.2.0").
- **`refactor(index)!: move distributed BTree build to segmented index framework`** (PR #7013)
  - distributed BTree now uses the same `create_index_uncommitted` / merge / commit path.
- **`feat!: return write summaries from file writers`** (PR #7096) - `finish()` changed from
  `Result<u64>` to `Result<FileWriteSummary>` (`{ num_rows: u64, size_bytes: u64 }`,
  `rust/lance-file/src/writer.rs:54-58,768`). Python `LanceFileWriter.finish` keeps its
  row-count return.
- **`fix(python)!: derive index type from details`** (PR #6903) - `describe_indices()` "now
  reports nested and special-character field names as full field paths (e.g. `meta.lang`)
  instead of just the leaf name"; `list_indices()` is a thin typed `IndexInformation` wrapper
  that no longer opens each index; the `load_indices()` Python binding was removed.
- **`perf!: avoid listing index files after writes`** (PR #7129) - `IndexFile` metadata is
  propagated from writer/builder APIs into manifest metadata instead of listing index
  directories after writes (a writer/builder trait-level break).

Net-new user-facing features:

- **`lance-derive` crate** (PR #6229) - `#[derive(DeepSizeOf)]` for Arrow-aware memory
  accounting, replacing the external `deepsize` crate. Crate workspace 24 -> 25. See section 2.
- **FM-Index scalar index** (`docs/src/format/index/scalar/fmindex.md`,
  `protos/index.proto` `FMIndexIndexDetails`) - BWT substring/prefix/regex search on raw
  bytes via the Segmented Index architecture (`num_segments`). See section 11.2.
- **Multi-bit IVF_RQ** (PR #7038) - RaBitQ `num_bits` 1..=9; ex-code bits in `__ex_codes`
  (+ `__add_factors_ex` / `__scale_factors_ex`). **Raw-query RQ search** (PR #7078) adds the
  `query_estimator` field and `__error_factors` lower-bound pruning. See section 11.1.
- **Independent per-worker vector index models** (PR #7148) for distributed builds; zone-map
  segments now mergeable via `merge_existing_index_segments` (PR #7128); HNSW segment merge
  (PR #7178); segmented BTree merge (PR #6889). See section 12.
- **Volcengine TOS** (`tos://`) and feature-gated **GooseFS** (`goosefs://`, PR #7034) object
  stores. See section 13.
- Smaller: `tracked_files` / `all_files` on `LanceDataset` (PR #6011); multi-segment FM-Index
  build config; `add_columns` UDFs no longer require pandas (PR #7131); FTS flat match now
  searches all unindexed fragments (PR #7188); AVX-512 distance tables compiled for the
  target CPU (PR #7121).
- Dependency facts: arrow 58, datafusion 53, opendal 0.57, jieba-rs 0.10,
  lance-namespace-reqwest-client 0.8.2; pylance `lance-namespace>=0.8.0,<0.9`.

Unchanged and reverified at `v8.0.0-beta.9`: **15 transaction ops** (`protos/transaction.proto`
diff empty); file-format `version.rs` (`Next => 2.3`, `#[default]` still `V2_1`, no 2.4 - so
section 3 holds unchanged); `CommitConfig num_retries = 20`
(`rust/lance-table/src/io/commit.rs:1530`); the feature-flag bits; the
`ConditionalPutCommitHandler` routing; `rust-version 1.91.0`, `resolver 3`, edition 2024;
MemWAL docs and system-index docs byte-identical; MemWAL still experimental.

### The v8.0.0-beta.9 -> v8.0.0-beta.14 delta

31 commits, **two breaking changes** - both vector/RaBitQ. No new crate (still 25), no new
transaction op (still 15), no file-format change.

- **`feat(vector)!: add approx mode for RaBitQ search`** (PR #7179) - a public
  `approx_mode` with values `fast` / `normal` / `accurate` for vector search "when the backing
  index supports it" (commit `e25620710`), threaded through the Rust scanner, Python query
  parsing, and ANN proto serialization. **Breaking proto change**: the ANN query proto now
  carries `VectorApproxMode approx_mode` (`protos/ann.proto:16,45`) - regenerate any consumer
  that matches the serialized ANN proto. See section 11.1.
- **`perf(vector)!: add dedicated SIMD kernels for RaBitQ ex-code reranking`** (PR #7205,
  `rust/lance-index/src/vector/bq/ex_dot.rs`).
- **IVF_RQ default `target_partition_size` is now 4096** (was the generic fallback, PR #7273).
- **Cleanup explain API** (PR #7147) - `Dataset::cleanup(policy)` splits into `explain()`
  (returns a `CleanupExplanation`, a dry run) and `execute()`. See section 7.
- **Object-store docs** (PR #7151) - the guide gained full Tencent COS and GooseFS config
  sections (`docs/src/guide/object_store.md:333,396`); GooseFS is no longer undocumented. See
  section 13.
- **Smaller adds**: Python zonemap segment builds exposed (PR #7177); per-query I/O metrics
  (`bytes_read` / `iops` / `requests`) on `ANNSubIndex` / `ANNIvfPartition` in EXPLAIN ANALYZE
  (PR #7204); branch-aware version ops in the Directory/REST namespaces (CreateTableBranch /
  ListTableBranches / DeleteTableBranch, PR #7166); enriched `IndexContent` fields in dir
  namespace `ListTableIndices` (PR #7109).
- **Fixes**: resolve Blob v2 external URIs and clean failed writes in `add_columns`
  (PR #7152); coerce filter literals for dictionary-encoded columns (PR #7003);
  composite-key `merge_insert` probes every indexed key column (PR #6878).
- **Removals**: `table_version_storage_enabled` and the `__manifest`-backed table-version path
  removed - version ops now use `_versions/` exclusively (PR #7222); brotli dropped from the
  dependency graph (PR #7270).
- **Dep pins**: `lance-namespace-reqwest-client` 0.8.2 -> 0.8.4; pylance `lance-namespace`
  `>=0.8.0,<0.9` -> `>=0.8.5,<0.9`. arrow 58 / datafusion 53 / opendal 0.57 / jieba-rs 0.10
  unchanged.

Unchanged and reverified at `v8.0.0-beta.14`: 25 crates; 15 transaction ops; file-format
`version.rs` (`Next => 2.3`, `#[default] V2_1`, no 2.4); `CommitConfig num_retries = 20`
(`rust/lance-table/src/io/commit.rs:1550`); `rust-version 1.91.0`, `resolver 3`, edition 2024;
feature-flag bits; `ConditionalPutCommitHandler` routing.

### The v8.0.0-beta.14 -> v9.0.0-beta.10 delta (v8 -> v9 major boundary)

129 commits. A **light major bump** - structurally v9 is nearly identical to v8. The major
version was auto-triggered by `ci/check_breaking_changes.py` (GitHub `breaking-change`-label
detection), fired by two PRs merged before the 2026-06-22 bump: the Python 3.9 drop (#7345)
and the `alter_columns` fail-fast cast (#7158). The FMIndex rename (#7397) carries the label
too but merged after the bump, so it rode the already-bumped 9.0.0 series rather than
triggering it. **Three breaking changes:**

- **`refactor!: rename FMIndexIndexDetails to FMIndexDetails`** (PR #7397) - proto message
  `protos/index.proto:251` `FMIndexDetails {}` (was `FMIndexIndexDetails`); Rust type
  `pb::FmIndexDetails`; the `get_plugin_name_from_details_name` `fmindex`->`fm` special-case
  was deleted. Author's note: "This change would be a breaking change to any existing FM
  indexes!" - existing FM indexes become unreadable. See section 11.2.
- **Drop Python 3.9** (PR #7345) - `python/pyproject.toml` `requires-python = ">=3.10"`; the
  `Python :: 3.9` classifier removed; PyO3 abi3 floor raised `abi3-py39` -> `abi3-py310`;
  release wheels no longer built for 3.9. See section 2.
- **`fix(dataset)!`: `alter_columns` cast fails fast with an attached index** (PR #7158) -
  previously a cast silently dropped/invalidated the index; now it errors and you must
  `drop_index()` first. See section 6.

**Removal (Rust API, not conventional-`!`):** `as_vector_index` removed from the public
`Index` trait (PR #7392) - callers downcast via `as_any()`. See section 11.1.

**Net-new features:**

- **Hamming clustering** (PR #7379) - SIMD near-duplicate detection over 64-bit binary
  hashes (`pairwise_hamming_distance`, `UnionFind`, `hamming_clustering_for_ivf_partition`).
  See section 11.1.
- **COUNT(*) pushdown on stable-row-id datasets** (PR #7360) - the fast path no longer falls
  back to a full scan when stable row IDs are enabled. See section 11.1.
- **Per-column blob size thresholds** (PR #7269) - `lance-encoding:blob-inline-size-threshold`
  / `...-dedicated-size-threshold`; appends with a different threshold are rejected. See
  section 3.5.
- **Tunable 32k miniblock chunks** via `LANCE_MINIBLOCK_MAX_VALUES` (PR #7356; default still
  4096). See section 3.3.
- **`icu/split` FTS tokenizer** (PR #7474) and **mixed-language stop words** (PR #7324). See
  section 11.3.
- **Distributed LabelList index builds** (PR #7223). See section 12.
- **ngram index accelerates regex + infix LIKE** (PR #7139). See section 11.2.
- `alter_columns` **Dict <-> value-type casts** (PR #7289, section 6); cleanup-explain
  exposed to **Python and Java** (PR #7248, section 7); Python **fragment-reuse remap +
  delete-by-offset** (PR #7438); v2 file writer/reader support **columns of unequal length**
  (PR #7406); a `SpillStore` trait with local-disk impl (PR #7311); a versioned cache-codec
  envelope (PR #7163).

**Notable fixes:** compaction rejects `defer_index_remap` with stable row IDs (#7468);
nested legacy blobs rejected in v2.2 and blob v2 supported in nested structs (#7278, #7281);
`merge_insert` no longer drops matches when a leading payload column is all-null (#7251); SQ
offset accounted for in dot distance (#7481); manifests >5 GB via size-aware copy (#7047);
double percent-encoding in object-store paths resolved (#6643/#6695).

**Dependency changes:** `lance-namespace-reqwest-client` 0.8.4 -> 0.8.6 (#7254); `itertools`
0.13 -> 0.14 (#7424). The pylance runtime pin `lance-namespace>=0.8.5,<0.9` is unchanged.

Unchanged and reverified at `v9.0.0-beta.10`: **25 crates**; **15 transaction ops**
(`protos/transaction.proto` unchanged); file-format `version.rs` (`Next => 2.3`,
`#[default] V2_1`, no 2.4); `CommitConfig num_retries = 20`
(`rust/lance-table/src/io/commit.rs:1550`); `rust-version 1.91.0`, `resolver 3`, edition 2024;
arrow 58 / datafusion 53 / opendal 0.57 / jieba-rs 0.10; feature-flag bits;
`ConditionalPutCommitHandler` routing; MemWAL still experimental.

### The v9.0.0-beta.10 -> v9.0.0-beta.16 delta

58 commits. **One breaking change**; no new crate (still 25), no new transaction op (still 15),
no file-format change, no dependency-pin change. **`v8.0.0` final also shipped** in this window
(tag `v8.0.0`, commit `15f2ff594`, 2026-07-01) - use it as the stable pin (section intro).

**Breaking change:**

- **`feat(fts)!: make v2 the default index format`** (PR #7512) - newly created FTS / inverted
  indexes default to on-disk **format v2**; `LANCE_FTS_FORMAT_VERSION` no longer controls new
  indexes; pass `format_version=1` for older-reader compatibility. Existing v1 indexes stay
  queryable and are maintained as v1. See section 11.3.

**Net-new features:**

- **Blob read-API rework** (PR #7530, #7558) - `read_blobs` is now the primary full-payload
  API, `take_blobs` is for streaming/seeking, `scanner(blob_handling="all_binary")` reads blobs
  as Arrow binary; documented auto-tiering defaults (16 KiB inline / 2 MiB dedicated) and a new
  `lance-encoding:blob-pack-file-size-threshold` field key (PR #7322). `dataset.update()` now
  works on blob-encoded columns (PR #7579). See section 3.5.
- **Per-base `storage_options`** via `base_<id>.<key>` keys (PR #7608); **multi-base
  merge-insert** with target-base routing (`MergeInsertBuilder::target_bases`, round-robin new
  fragments, `DataFile.base_id` stamped; PR #7610). See sections 13 and 6.
- **ZoneMap `value_range`** min/max without a scan (PR #7463); **BTREE + ZONEMAP accept
  `LargeUtf8`** (PR #7525). See section 11.2.
- **Prefiltered LSM vector + FTS search** across base/flushed/in-memory sources (PR #7138). See
  section 10.
- **Schema evolution allows all-null `Map` columns** (PR #7462). See section 6.
- **DirectoryNamespace** now implements `update_table` / `delete_from_table` (PR #6923) and
  `alter_transaction` (PR #6974) - previously `not_supported`.
- Compaction `RowAddrRemap` structure to avoid remap HashMap OOM (PR #7237); single-flight
  scalar-index opens (PR #7464); session-cached manifest reuse on open (PR #7576).

**Notable fixes:** `DataReplacement` commits preserve `DataFile.base_id` on multi-base datasets
(#7609); blob descriptor views kept opaque - the reader no longer recurses into `position`/
`size` child fields (#7618); stable row-id index tolerates sparse/overlapping chunks (#7480);
ngram posting-list writes chunked by byte size to avoid i32 offset overflow (#7607); scheduler
deadlock on same-priority chunks fixed (#7588).

Unchanged and reverified at `v9.0.0-beta.18`: **25 crates**; **15 transaction ops**
(`protos/transaction.proto` unchanged); file-format `version.rs` (`Next => 2.3`,
`#[default] V2_1`, no 2.4); `CommitConfig num_retries = 20`; `rust-version 1.91.0`,
`resolver 3`, edition 2024; arrow 58 / datafusion 53 / opendal 0.57 / jieba-rs 0.10 /
itertools 0.14 / lance-namespace-reqwest-client 0.8.6; pylance `lance-namespace>=0.8.5,<0.9`;
feature-flag bits; `ConditionalPutCommitHandler` routing; MemWAL still experimental.

### The v9.0.0-beta.16 -> v9.0.0-beta.18 delta

36 commits. **No breaking changes**; no new crate (still 25), no new transaction op
(`rust/lance/src/dataset/transaction.rs` untouched), no file-format change. Mostly fixes
plus three additive features:

- **pylance prewarm gains segment selection** (#7677) - warm only chosen index segments.
- **Object-store metrics published via the `metrics` crate** (#7533).
- **RLE v2 run-length widths** (#7376), with width selection by encoded size (#7636).

**Docs:** the performance guide gained a **Fragment Sizing** section (#6606); cleanup and
automatic-cleanup documentation added to the read-and-write guide (#6546); a new
`guide/observability.md` page; MemWAL format spec updated (#7655). All reproduced in this
skill's `references/docs/` mirror.

**Notable fixes:** FTS list columns indexed as row documents (#7656); fuzzy
`max_expansions` enforced globally across index partitions instead of per-partition; FTS
tail-partition merge split by the worker memory budget and a `num_tokens`-only DocSet
cached on `LazyDocSet` (#7600); MemWAL writer fenced on WAL persistence failure (#7547)
and slice-aware memtable flush-threshold size estimate; Arrow-JSON -> Lance-JSON
conversion fixed across the merge/update, single-fragment-create, and merge-insert
full-fragment-rewrite paths (`take` now returns Arrow JSON, #7470/#7471);
`object_store::Error::NotFound` mapped to `Error::NotFound` instead of a generic IO
error; PQ `num_bits` respected for numpy codebooks (#7586); hang fixed in
`train_streaming_coreset_ivf_model` (#7676).

### The v9.0.0-beta.18 -> v9.1.0-beta.8 delta

127 commits straddling the tail of the 9.0.0 beta line (through `rc.2`) and the new 9.1.0 dev
line. The 9.1.0 minor bump is **automatic release-train cadence**, not a breaking change: when
`v9.0.0-rc.1` was cut, `main` advanced to `9.1.0-beta.0`. **One breaking-labeled PR** in the
window: FTS `block_size` (#7466, below). Structural changes reverified at `v9.1.0-beta.8`:
**26 crates** (new `lance-index-core`, #7713); **16 transaction ops** (new `DataOverlay`);
**datafusion 53 -> 54** (#7793), geodatafusion 0.4 -> 0.5, build toolchain 1.91 -> 1.97 (#7712,
MSRV `rust-version` unchanged at 1.91.0). Unchanged: arrow 58, opendal 0.57, jieba 0.10,
`lance-namespace-reqwest-client` 0.8.6, itertools 0.14, edition 2024, resolver 3,
`lance-arrow-scalar =58.0.0`; `CommitConfig num_retries = 20`; file-format `version.rs`
(`Next => 2.3`, `#[default] V2_1`); Python min 3.10 (3.14 added, #7728).

**Breaking (labeled):**
- **FTS configurable posting `block_size`** (#7466) - `InvertedIndexParams` gains `block_size`
  (128/256, default 128, 512 rejected). `block_size=256` and the code analyzer require FTS
  on-disk **format v3** (#7866). Sections 11.3.

**Additive features:**
- **Data Overlay Files** (#7535 write path, #7536 read path, #7540 Python commit op) - the new
  16th transaction op `DataOverlay`, feature flag 64, spec `data_overlay_file.md`. Cell-level
  `(offset, field)` updates without rewriting base data files; **unstable**, env-gated by
  `LANCE_ENABLE_UNSTABLE_DATA_OVERLAY_FILES` (release builds refuse overlay datasets).
  Compaction folds fragments over an overlay-count limit (#7772). Section 5.5.
- **Sparse structural pages** (#7889) - first real 2.3 encoding; `structural-encoding=sparse`.
  Section 3.1.
- **Exact `IS NULL`** for ZONEMAP and BLOOM_FILTER via a new `null_bitmap`. Section 11.2.
- **Nested-field FTS** (#7686) index leaf fields like `data.text`; code-analyzer tokenizer
  (#7681); impact-skip / bulk MAXSCORE top-k / bulk conjunction FTS paths (#7602/#7603/#7624);
  read inverted-index params without opening the segment (#7816). Section 11.3.
- **OpenTelemetry metrics for Python** (`instrument_lance_metrics`, `pylance[otel]`, #7537);
  zone-map seeds written into data-file footers during append (#7427).
- **AWS creds via `AssumeRoleWithWebIdentity`** to avoid role chaining (#7757); batch/list
  blob reads (#7864, #7664) and a bulk packed-blob writer (#7743); MemWAL flush-interval
  ticker (#7894) and Python/Java shard delete (#7649, #7688); wider hamming hashes and
  multi-segment hamming clustering (#7767, #7758); RLE child-buffer zstd compression (#7663);
  cached file-metadata APIs on `FileFragment` (#7820); `TableProvider` write inputs for
  `merge_insert`/`insert` (#7368); runtime SIMD dispatch for pre-Haswell x86_64 from-source
  builds (#6630).

**Other:** writes now reject system column names (#7797). The TensorFlow integration moved
from built-in to an external `lance-tensorflow` package, and the image array decoder/encoder
is now Pillow-only (not vendored in this skill's docs mirror - integrations mirror is
`datafusion.md` only).

### The v9.1.0-beta.8 -> v10.0.0-beta.7 delta

78 commits. The major bump is **mechanical**, not a redesign: `ci/publish_beta.sh` re-roots at
`MAJOR+1` on any `breaking-change`-labeled PR, and `fb88621f8 chore: bump to 10.0.0-beta.1 based
on breaking change detection` landed immediately after `3a72f8a61 fix(blob)!: preserve null
selections across blob APIs (#7903)`. Only one bump happens per series, so the two later `!`
commits rode the already-bumped line. Structural invariants **all reverified unchanged**:
26 crates (no crate added or removed), 16 transaction ops, `CommitConfig num_retries = 20`,
file-format `version.rs` (`Next => 2.3`, `#[default] V2_1`), feature-flag bits (newest still 64,
data overlay), MSRV 1.91.0, toolchain 1.97.0, edition 2024, resolver 3, arrow 58 /
datafusion 54 / opendal 0.57 / jieba 0.10 / itertools 0.14 /
`lance-namespace-reqwest-client` 0.8.6, Python 3.10-3.14.

**Breaking (four):**

- **`fix(blob)!: preserve null selections across blob APIs`** (#7903) - the bump trigger. Every
  selection API returns one result per request, nulls as `None` instead of omitted. Rust,
  Python, and Java signatures all change. Section 3.5.
- **`perf(cache)!: use fixed-size cache keys`** (#7878) - opaque 16-byte BLAKE3 keys
  (`CACHE_KEY_FORMAT = "blake3-128-v1"`); all warm/persisted caches cold-miss, no legacy
  fallback; prefix-invalidation and key-inventory APIs removed. Section 9.4.
- **`perf(compaction)!: skip building row-address maps when index remapping is not needed`**
  (#7778) - `IndexRemapperOptions::create_remapper` becomes async and returns
  `Result<Option<Box<dyn IndexRemapper>>>`; compaction skips the `_rowid` scan and
  RoaringTreemap entirely for FRI-only or system-index-only datasets.
- **MemWAL rename** (#7943, #7957) - flushed generation -> SSTable, merge -> compaction, across
  spec, Rust, Python, Java, and protos. Wire-compatible, symbol-breaking, no shims. Section 10.

**Additive:**

- **`ConcreteFileVersion`** (#7879) exact file identity, unordered by design; manifests reject
  selector aliases; `try_from_major_minor` / `to_numbers` removed; byte-exact writer fixtures
  with SHA-256 locks (#8019). Section 3.6.
- **Sparse structural pages auto-select** in the 2.3 writer (#7756). Section 3.1.
- **Segment-native BLOOMFILTER / RTREE / NGRAM / LABEL_LIST** (#7925, #7932, #7244, #7884);
  `IndexSegment::new` 4 -> 6 params; merged segments inherit the minimum source
  `dataset_version`; concurrent LIST on segment commit, ~8x faster remote (#7657). Section 12.
- **ACORN-1 prefiltered HNSW** (#7927), opt-in via `approx_mode="fast"`, with a documented
  recall regression on uniform-random masks. Section 11.1.
- **FTS**: `total_tokens` metadata key and `bm25_search` removal (#7863),
  `LANCE_FTS_SEARCH_CHUNK` (#7950), top-k row-id resolution 26x (#7897), deterministic tie
  order (#8073), segment-uuid-scoped exec nodes (#7976). Section 11.3.
- **Data-overlay/index correctness** (#7549, #7926, #7918) - index results exclude
  overlay-superseded rows. Sections 5.5 and 9.1.
- **quick_cache** as the default index and metadata cache backend (#7953, #8013), with a
  per-shard admission ceiling that silently refuses oversized entries. Section 9.4.
- Cross-store `deep_clone` via `CommitBuilder::with_source_store` (#7545); commit-retry backoff
  overflow capped at `MAX_SLOTS = 128` (#7883); external-manifest finalization always HEADs
  (superseded at beta.8 by #8499 - the ETag from that HEAD must not be persisted; see below)
  (#7964); `memory://` `DatasetNotFound` fix (#8068); tokio-shutdown panic becomes an I/O error
  (#7478); `LANCE_CPU_THREADS` / `LANCE_IO_CORE_RESERVATION` validated (#7856); dir namespace
  surfaces throttles instead of `TableNotFound` (#7931) and honors `structured_query` FTS
  (#7592); Java `CacheStats` + `Session.metadataCacheStats()` (#7885); vector index append
  across heterogeneous segment models (#8047).

**Fixes worth knowing:** `Dataset::filter_deleted_ids` was wrong on stable-row-id datasets,
breaking `optimize_indices` (#7704); filtered scans and `add_columns(AllNulls)` returned a valid
struct with null children instead of a null struct on storage 2.1 (#8049); `LIKE ... ESCAPE ''`
was treated as no-escape and `ESCAPE 'ab'` silently truncated - both now error (#7810);
`list_indices` no longer backtick-quotes ordinary column names (#7503).

**Security:** `quinn-proto` 0.11.14 -> 0.11.16 via Dependabot security alert, applied to the
root workspace, `/python`, and `/java/lance-jni` (#7983, #7984, #7982) - "proto: yield error on
too many gaps in assembler". Plus bulk Dependabot cargo-group bumps (38 root, 28 python,
27 java-jni).

### The v10.0.0-beta.7 -> v11.0.0-beta.2 delta

128 commits. The bump is again **mechanical** - nine PRs carried the `breaking-change` label
(#8024, #8025, #8026, #8051, #8095, #8159, #8172, #8188, #8206), of which only two carry `!` in
the subject, and the bot re-rooted `10.1.0-beta.2` as `11.0.0-beta.1` in place. Structural
invariants **all reverified unchanged**: **26 crates** (the `rust/` `Cargo.toml` inventory is
byte-identical across the two tags), **16 transaction ops** (`protos/transaction.proto` is
byte-identical), `CommitConfig.num_retries` **20**, file-format enum `next => 2.3` / default 2.1
with no 2.4, manifest feature flags 1-128 unchanged, MSRV 1.91.0 / toolchain 1.97.0, Python
3.10-3.14, arrow 58 / datafusion 54 / `object_store` 0.13.2 / jieba 0.10 / blake3 1.8.5, and the
`=58.0.0` pins on `lance-arrow-scalar` / `lance-arrow-stats`. The only proto change in the whole
range is `protos/index_old.proto` (+17 lines).

**Breaking (labeled):**

- **#8206** - fragment ids became a dataset-lifetime high-water mark; overwrite no longer
  restarts at 0, overwrite fragments with deletion files are rejected, duplicate ids block all
  commits. A format invariant, not just an API change. Section 5.3.
- **#8024 / #8025 / #8026** - the exact-version reader/writer composition: `ReaderProjection`
  constructors became free functions, `FileReader::version()` and
  `Dataset::storage_version_or_default()` return `ConcreteFileVersion`,
  `FileReader::supports_projection` and `open_writer` were removed, and
  `lance-encoding::version` was deleted with no re-export. Section 2.1.
- **#8051** - `force_seal_active` returns `SealFence`. **#8095** -
  `MemIndexConfig::detect_index_type` replaced by `is_maintainable_index_type` + `MemIndexKind`.
  Section 10.
- **#8159** - `CacheBackend::deep_size_of_entries`; reported cache sizes shrink. Section 9.4.
- **#8172** - `DataBlockBuilder::append` is fallible; corrupt variable-width offsets now error
  instead of panicking. **#8188** - HNSW `try_with_capacity`, `m >= 4` enforced, persisted level
  layout corrected; different graphs and recall. Sections 2.1 and 11.1.

**Breaking (unlabeled but source-breaking - the #7877 series):** #8020 removed
`lance_io::encodings` and moved `lance-file::previous` to `versions::v1`; #8021 deleted the
`lance-encoding::previous` public encoder surface; #8023 turned `FileWriter` into an enum and
removed all its constructors plus two `FileWriterOptions` fields; #8038 added a context parameter
to `MiniBlockCompressor::compress`. Also `#8141` removed `GraphBuilderStats`, and `#7788` added a
third parameter to `load_segments`. Section 2.1.

**Net-new:**

- **FTS document granularity** (#7788) - `DocumentGranularity` ROW/LIST_ELEMENT,
  `posting_format_version`, `_doc_index` column, and a third FTS-v3 trigger. Section 11.3.
- **Compound FTS scoring core** (#8092, #8093, #8094, #8131, #8299) - Boolean/Phrase/Boost
  composition, public `CompoundQueryExec`, cost-ordered conjunctions, `AND` as scoring `MUST`.
  Section 11.3.
- **Zone maps**: `has_null_bitmap` making `IS NOT NULL` scan-free (#8088) and all-type support
  including nested (#8017). Section 11.2.
- **Manifest transaction spilling** above 20 MiB (#7881, ~50% manifest shrink measured).
  Section 9.1. **Pluggable cache backends** with a `moka://` URI form (#7683). Section 9.4.
- **`aws_provider_scheme`** token/ecs/irsa (#8103); **`goosefs://` via
  `ConditionalPutCommitHandler`** (#8134) with a mixed-version overwrite hazard; multipart
  part-identity retry fix (#8174) and removal of `LANCE_CONN_RESET_RETRIES`. Section 13.
- **Encoding performance**: exact decode-buffer preallocation via `decoded_size_bytes` (#8091,
  index-cache weight down up to 74% on IVF_SQ, no on-disk change); a zero-copy typed view for
  inline bitpacking (#7696, 13-22% faster unchunk); `O(n*m)` fragment compares removed from
  `build_manifest` for Update/Delete (#8210); parallel doc-length preload on the cold deferred
  FTS search path (#8119).
- **Python**: pydantic auto-conversion in `write_dataset` plus
  `LanceDataset.from_pydantic_model(model_class, data, uri=None, **kwargs)` (#7383);
  `LanceFileWriteSummary` giving `LanceFileWriter` a `size_bytes` (#7876); `max_source_fragments`
  on `compact_files` for incremental compaction, also settable via the manifest config key
  `lance.compaction.max_source_fragments` (#8116); `blob_handling` on the SQL/DataFrame builder
  (#8087).
- **Java** got the biggest build-out of any binding: an OpenTelemetry metrics bridge
  (`org.lance.otel.LanceMetrics`, #8064 - the docs now say metrics are available "from the Rust,
  Python, and Java APIs"); scanner tuning via `ScanOptions` (`batchSizeBytes`, `ioBufferSize`,
  `fragmentReadahead`, `scanInOrder`) and a typed `MaterializationStyle` (#8288);
  `FragmentStatistics` (#8072); a typed `LanceException` replacing bare `RuntimeException`
  (#8184); and `IndexBuildProgress` callbacks (#8090).
- Minor: `QuantizationType` accepts `"RQ"` (#8214); HNSW greedy descent stops at level 1
  (#8035, +3.7% recall@10); `BlobV2Layout` classification helper (#8266); a
  `ConditionalPutCommitHandler` test matrix covering every routed scheme.

**Security / supply chain:** `rust-stemmers 1.2.0` -> **`frostem`** (#8183) - the unmaintained
crate's "Greek implementation can retain stale UTF-8 byte offsets after shortening a word, then
panic while slicing the shortened string." `frostem` is generated from current upstream Snowball
and exposes the same 18 algorithms. `strum` and the direct `goosefs-sdk` dependency were dropped;
`crc32c` left the lockfile and `opendal-http-transport-reqwest` entered it.

**It is not a drop-in for existing FTS indexes.** The two stemmers disagree on a small but
non-trivial slice of ordinary English. Measured over `/usr/share/dict/words`, **484 of 235,976
words (0.2%) stem differently** - most are the `-ogist` family (`anthropologist` ->
`anthropolog`), but the rest are everyday vocabulary: `internal` (old `intern`, new `internal`),
`added` (`ad` vs `add`), `emergency`, `evening`, `interfering`, `erring`. An index built with
`.stem(true)` under v10 and queried by a v11 binary therefore **silently misses those forms** -
the query stems to `internal` while the index holds `intern`. There is no error and no version
check. Two consequences for a rollout: a mixed v10/v11 fleet appending FTS segments to the same
store produces segments stemmed two ways, so the upgrade wants to be fleet-coordinated, and any
stemmed FTS index built before the swap needs one rebuild to become self-consistent.

---

### The v11.0.0-beta.2 -> v11.0.0-beta.6 delta

94 commits, 90 PRs, **four `breaking-change`-labeled**: #8027, #8028, #8347, #8360. At that tag
the full v11 delta from `v10.0.0-beta.7` stood at **222 commits and 13 breaking PRs** (#8024,
#8025, #8026, #8027, #8028, #8051, #8095, #8159, #8172, #8188, #8206, #8347, #8360).

**Breaking:**

- **`LanceFileVersion` lost its ordering** (#8028). `PartialOrd`/`Ord` are gone, so
  `v >= LanceFileVersion::Next` no longer compiles, and both `From` conversions between selector
  and concrete version were deleted. Index readers, writers, shufflers and distributed mergers
  now take an exact `ConcreteFileVersion`. Per the PR: "Remaining version decisions are
  exhaustive matches at declared boundaries rather than `>=`, `max`, or selector round-trips."
- **`LanceFileVersion::resolve` changed signature** (#8027):
  `pub fn resolve(&self) -> Self` became `pub const fn resolve(self) -> ConcreteFileVersion`.
  Deleted: `iter_non_legacy()`, `support_add_sub_column()`, `support_remove_sub_column(&Field)`.
  Added: `stable_file_version() -> ConcreteFileVersion` (V2_1), `next_file_version()` (V2_3),
  `ConcreteFileVersion::to_selector()` and `::is_unstable()`. #8027 also centralized dataset
  version policies.
- **`Operation::Project` / `Merge` gained `preserves_nullability: bool`** (#8347). See section
  9.2 - a nullability tightening must not set it, and setting it makes the operation conflict
  with concurrent value-writes in either commit order.
- **`is_maintainable_index_type(&str)` removed** (#8360), replaced by
  `validate_maintained_indexes(dataset, index_names) -> Result<()>`. Type-URL filtering was
  unsound: an IVF-PQ over `FixedSizeList<Float64>` passed the check and then made the table
  unwritable. The replacement is all-or-nothing - it "reports the first index it cannot maintain
  rather than returning a usable subset". Error text: "index '{}' has type {}, which the MemWAL
  cannot maintain. Supported: BTree, Inverted, Vector".

**Format-level:**

- **New manifest feature flag at bit 128** (#8263); `FLAG_UNKNOWN` moved 128 -> 256. Reader and
  writer must both hold it. **The flag added here did not survive the major.** It was
  `FLAG_MEM_WAL_INDEX_CATCHUP` from `beta.4` to `beta.17`, then #8680 retired it and #8535 gave
  the reclaimed bit to `FLAG_COVERED_INDEX_METADATA`, which is what `v11.0.0` shipped. The proto
  field `Transaction.UpdateMemWalState.require_index_catchup` was deleted with it, and MemWAL
  catch-up lost its flag gate: an absent `index_catchup` shard now unconditionally means
  *unknown*. Builds pinned inside `beta.4`..`beta.17` still treat bit 128 as supported and will
  open a covering dataset instead of refusing it. Section 7.
- **Transaction proto field 9 deprecated** (#7432): `updated_fragment_offsets` gives way to
  field 10 `updated_fragment_offset_bitmaps`, "Per-fragment matched offsets as portable
  RoaringBitmap bytes". Writers emit field 10 only; readers prefer 10, falling back to 9 for
  manifests written before the change.
- `MemWalIndexDetails.index_catchup` added as `table.proto` field 10.
- **`IndexCatchupAdvance` never shipped.** #8263 added the message and
  `CreateIndex.mem_wal_index_catchup_advances`; #8481 deleted both within the same beta window,
  replacing them with catch-up derived from the version the transaction read. Present at
  `v11.0.0-beta.5`, absent at `v11.0.0-beta.6`.

**Net-new:**

- MemWAL backpressure is observable: `MemTableStats.frozen_count` / `frozen_bytes` and
  `ShardWriter::backpressure_stats()` (#8241) - "Heap bytes still owed to flush".
- MemWAL splits logical from storage schema, widening non-PK top-level fields to nullable, so
  `ShardWriter::delete` no longer requires nullable base columns (#8352).
- `write_fragments(session=...)` / Java `WriteFragmentBuilder.session(...)` (#8034); a foreign
  session against a dataset-backed target is rejected.
- `analyze_plan` appends `tokenized_query=` to FTS leaves (#8414); `explain_plan` deliberately
  unchanged. Python `lance.tokenize(...)` / `lance.FtsToken(text, position)` preview tokenization
  with no dataset or index (#8415).
- `LanceFragment.validate()` (#8428) validates one fragment rather than the whole dataset;
  `Dataset::validate()` gained stable-row-id invariant checks (#8258, no-op when unused).
- `BlobFile.read_ranges(ranges) -> list[bytes]` (#8319) - "The underlying physical reads may be
  reordered, coalesced, or split for efficiency."
- `lance.fragment.RowIdSequence` (#8356); duplicate ids now rejected.
- `LanceOperation.Update` carries `updated_fragment_offsets` in Python (#8447) and
  `updatedFragmentOffsets` in Java (#6748).
- Java: `Session.Builder` selects registered native cache backends by URI or
  `CacheBackendConfig`, e.g. `moka://?capacity=1048576` (#8446); `Index.getSizeBytes()` and
  `IndexDescription.getSegments()` (#8355).
- Blob v2 supported in `FileFragment::update_columns` (#8344).

**Performance / build:**

- FTS same-column `MUST + SHOULD` scores optional clauses lazily (#8448); conjunction
  confirmations ordered by `match_cost`, measured **200 -> 120** two-phase `matches()` calls per
  query (#8354).
- Release JNI cdylib stripped: `liblance_jni.so` linux-x86-64 **278.35 MB -> 221.0 MB**
  (-20.6%), `.dynsym` preserved (#8314).
- x86_64-linux build baseline dropped `target-cpu=haswell` -> **`x86-64-v2`** (#8377), so
  binaries no longer trap on import on pre-AVX2 hosts.
- The `time = "=0.3.47"` pin was removed from `lance-namespace-impls` (#8296).
- `retain_versions=0` now errors instead of panicking (#8467); deleting a branch referenced by a
  tag is rejected (#8365).

---

### The v11.0.0-beta.6 -> v11.0.0-beta.16 delta (the v11 beta frontier)

91 commits, **one newly `breaking-change`-labeled**: #8235. This brings the full v11 delta from
`v10.0.0-beta.7` to **313 commits and 14 breaking PRs** (#8024, #8025, #8026, #8027, #8028,
#8051, #8095, #8159, #8172, #8188, #8206, #8235, #8347, #8360). Structural invariants all held
at beta.16: 26 crates, 16 transaction ops, `num_retries` 20, `next => 2.3` / default 2.1 (no
2.4), arrow 58, datafusion 54, MSRV 1.91.0, Edition 2024, Python 3.10+, manifest feature flags
unchanged (bit 128 allocated, `FLAG_UNKNOWN` 256).

The **final** added two more breaking PRs (#8407, #8535) for **357 commits and 16 breaking PRs**
to `v11.0.0`, and reallocated bit 128 to `FLAG_COVERED_INDEX_METADATA` as described above. Every
structural invariant above still holds at `v12.0.0-beta.15`.

**Breaking:**

- **Compaction gained row and byte budgets** (#8235) - `max_source_rows: Option<usize>` and
  `max_source_bytes: Option<u64>` join `max_source_fragments` on `CompactionOptions`
  (`rust/lance/src/dataset/optimize.rs:278,287`), each with a matching `lance.compaction.*`
  config key. The label is on the options struct changing shape; the feature itself is additive.

**Net-new:**

- **Lightweight version references** (#8523) - `Dataset::version_refs()` -> `Vec<VersionRef>`
  lists manifest locations without deserializing every manifest, unlike `versions()`. Section 7.
- **`Dataset::migrate_to_stable_row_ids`** (#8521) - one `Merge` commit converts an existing
  dataset to stable row IDs and flips the flag atomically; `with_max_retries(0)`, so quiesce
  writers first. Supersedes "stable row IDs cannot be turned on later". Section 8.
- **Per-fragment column writes** (#8313, renamed `write_columns` by #8622) - survive compaction.
- **Compaction fragment exclusion** (#8532) - `excluded_fragment_ids: Vec<u32>` (`optimize.rs:295`).
- **AMX-FP16 IVF acceleration** (#8540) - ships `LANCE_DISABLE_AMX` and `LANCE_AMX_FP16_CC`, the
  only new `LANCE_*` env vars in the whole v11 line, and makes partition assignment exact where
  it engages. See `performance.md`.
- **External manifest stores: object storage became authoritative** (#8499). Section 9.3.
- FTS: MAXSCORE for pure SHOULD queries and its metrics (#8474, #8475), exact posting load
  policies (#8667), chunked posting reads during segment merge (#8668). Java: manifest writer
  version and location metadata (#8450, #8451), efficient dataset version count (#8453).
- `perf(dataset)`: `get_fragment` binary-searches the manifest (#8636), with a fall-back to
  linear scan for legacy manifests that are unsorted (Lance <= 0.10) or hold duplicate fragment
  ids (Lance <= 0.16) - the same legacy shapes #8206 made uncommittable.

**Correctness fixes in this window, split by whether upgrading is enough.**

*Requires rewriting or repairing data already on disk - upgrading alone does not heal it:*

- #8382 - malformed variable-width Arrow offsets. Reachable in practice via `slice_arrays`
  page-splitting, so not theoretical.
- #8669 - JSON columns updated from string expressions hold raw text. Rows updated with an
  explicit `jsonb '...'` were always fine.
- #8509 - reordered sources in indexed merge insert; re-run the affected merges (the old
  statistics were misleading too).
- #7703, #8539 - invalid manifests already committed; validation is commit-time only, so
  existing bad manifests stay bad.
- #8459 - non-atomic tag creation. A clobbered tag is **unrecoverable and undetectable**;
  re-create it manually.
- #8378 - Windows UNC share roots. Data "written to a UNC URL" actually landed on the local drive.
- #8482 - FTS metadata not written when a distributed build had no partitions; re-run the build.

*Read-path only, heals on upgrade:* #7371, #7966, #8443, #8525, #8534, #8536, #8542, #8577,
#8587, #8588, #8591, #8592, #8593, #8594, #8595, #8596, #8597, #8598, #8599, #8600, #8602,
#8603, #8609, #8613, #8618, #8620, #8636, #8650, #8666, #8668, #8682, #8687, #8388, #8381.

Three worth calling out individually:

- **#7966** is not purely a type-support widening. ZoneMap zones over Decimal128/256 columns
  written by **Lance 8.0.0** carry typed-null extrema despite holding real values, and the old
  `zone_has_finite_min` guard skipped those zones - silently dropping matching rows. Reading
  heals on upgrade, but **pruning selectivity stays degraded until the index is rebuilt**
  (`rust/lance-index/src/scalar/zonemap.rs:203-205`).
- **#8542** - `multivec_distance` with a query length that is not a positive multiple of `dim`
  silently scored every row `1.0 - 0.0` instead of erroring (`rust/lance-linalg/src/distance.rs:411`).
- **#8499** is the special case: legacy external-store rows still carry `e_tag`, but new readers
  set `e_tag: None` and ignore them, so mixed-version rows converge with **no migration**. The
  stale-ETag race can still fire while legacy *finalizers* remain in the fleet.

**Security:** #8613 bumps `h2` to 0.4.16 for RUSTSEC-2026-0258.

---

### v11 silent-corruption and wrong-results fixes

Eleven fixes in the v11 line address failures that produced **no error** - wrong data, missing
rows, or a hang. Each names the condition that triggers it, so you can tell whether a dataset
written on an earlier v11 beta is affected. The `beta.6 -> beta.16` window added more; they are
listed in that delta above, split by whether upgrading is enough.

**Data-loss class:**

- **Cleanup irreversibly deleted live overlay data** (#8267). Six manifest/fragment walkers read
  only `Fragment::files` and missed overlay data files; `process_manifest` builds the cleanup
  keep set, "so an overlay old enough to be a deletion candidate is irreversibly deleted from the
  live dataset". Affects datasets using data overlay files (`FLAG_UNSTABLE_DATA_OVERLAY_FILES`).
- **A fragment-less manifest could be published** (#8438). `Operation::UpdateMemWalState` rebuilt
  its manifest without `final_fragments`, "so the commit publishes a manifest with **no
  fragments**. Every row in the table disappears." MemWAL tables only.
- **Stale row-id sequences after overwrite** (#8078). `RowIdSequenceKey` was keyed on
  `fragment_id` alone, so after `WriteMode::Overwrite` with a shared `Session`, reads got the
  previous generation's sequence: "row ids are reported for rows that no longer exist, row counts
  disagree with the manifest, compaction rechunks more ids than the fragments physically hold,
  and the same id can look live in two fragments at once." The cache key now includes
  `row_id_meta`.
- **Tencent COS double-commit** (#8369) - see section 9.3.
- **MemWAL compaction generation mixup** (#8262): progress kept the larger generation, so a late
  job's rows were written under another job's marker - "mutations under a generation it did not
  produce, and anything reading only the marker could then stop serving SSTables whose rows were
  never inserted."
- **Stale `index_section` offset** (#8308): a manifest reused after its last index was dropped
  kept the prior offset, which "would point at unrelated bytes in the new manifest file".
- **Dictionary index width mismatch** (#8220): nullable dictionary normalization could widen
  indices to UInt32 while the page stayed declared Int8.

**Wrong-results class** - these directly contradict "this index returns correct results":

- **A KNN row returned twice, one ranked by a stale vector** (#8342).
  `optimize_indices(num_indices_to_merge >= 1)` "can leave two copies of the same row in a vector
  index, and a KNN query then returns that row twice, one ranked by its pre-update vector."
- **BloomFilter matches silently disappeared** (#8223): after deferred-remap compaction the index
  "returned the original zone ranges without applying that mapping", so matches on moved rows
  vanished.
- **Every approximate cosine distance was shifted** (#8393): IVF_RQ's query-factor match "still
  grouped Cosine with Dot and subtracted `1.0`".
- **FTS could prune a competitive document** (#8473) - WAND score upper bounds were not
  conservative against f32 accumulation order. Separately, fragment-restricted FTS scans used
  only the first segment's coverage bitmap, so "matching rows in later segments could be filtered
  out" (#8211).
- **A query could hang indefinitely** (#8350): an IVF delta taking the no-more-probes early
  return never decremented the late-search barrier. "Every delta must reach the barrier, even if
  it has no partitions left to search, so that siblings waiting for the initial search can
  proceed."

### v11.0.0 final (the beta.16 -> final delta)

Two more `breaking-change`-labeled PRs landed after `beta.16`, plus net-new surface the beta
never carried. 44 commits.

**Breaking:**

- **Bit 128 reallocated** - `FLAG_MEM_WAL_INDEX_CATCHUP` retired (#8680), replaced by
  `FLAG_COVERED_INDEX_METADATA` (#8535). Covered above and in section 7.
- **DataFusion filter planning uses the caller's session** (#8407, labeled `breaking-change` /
  `A-python`).

**Net-new:**

- **Covering indexes** (#8535). `IndexMetadata.covering_fields` (proto field 11) is "the
  trailing subset of `fields` whose values the index carries but is not keyed on, letting a
  query that only projects those columns be answered without a fragment take." `fields` is
  redefined - `fields[0]` is always keyed, trailing entries may be merely carried. Index
  invalidation widens to any column in `fields`, keyed or carried. Additive on the wire, and
  "no index builder writes carried values yet, so today every declaration is ahead of its
  storage." Section 11.
- **`merge_insert` gained `write_mode`** (#8423): `Auto` (default), `RewriteRows`, or
  `RewriteColumns`. Under `RewriteColumns` an updates-only partial-schema merge "patches the
  source columns into the fragments that already hold the matched rows instead of rewriting
  whole rows", through a new `InPlaceMergeInsertExec`.
- **`Scanner::with_row_addr_prefilter(RowAddrMask)`** (#7288) - pass a precomputed row-address
  allow/block mask as a prefilter into vector and plain scans.
- **Deleted-row-id diff between two versions** (#8589) - `get_deleted_row_ids` returns "the ids
  live at the begin version and absent at the end version". Version 0 is the empty snapshot;
  reversed ranges and endpoints without stable row ids are rejected. Exposed in Python and Java.
- **Typed Python commit conflicts** (#8563) - `lance.commit.CommitConflictError` with a
  `retryable` attribute, on the standard `LanceDataset.commit` path and on `add_columns`,
  replacing "a bare `OSError` whose message clients must string-match". It subclasses `OSError`,
  so existing `except OSError` handlers keep working; switch them to the typed class to use
  `retryable`.

**Fixes needing action beyond upgrading:**

- **#8834 - rebuild affected HNSW indexes.** "An insert landing mid-write can append itself to a
  node the writer already emitted, so the written index holds edges to ids it does not contain.
  Nothing catches it at write time." The reader now self-heals - `load` drops ids naming no node,
  no rewrite required - but the dropped edges are permanently lost recall until a rebuild. A bad
  `entry_point` is still refused outright: "one edge lost beats every query over the index lost".
  The same PR covers a MemWAL case where "the generation's index then covered fewer rows than its
  own SSTable, and SSTable vector search is index-only - no brute-force scan - so those rows
  stopped answering once the frozen memtable retired."
- **#8101 - de-duplicate by hand.** With a **nullable primary key**, "a row holding a null in its
  key never matches its own earlier copy, so `merge_insert` inserts a second row rather than
  overwriting, and every repeat write adds another", and MemWAL compaction folds flushed data in
  by matching on the key, duplicating silently. The fix only blocks future manifests - it goes in
  `write_manifest_file`, rejecting a nullable PK with "Primary key column and all its ancestors
  must not be nullable". **Existing duplicates are not repaired.**
- **#8427 - recreate the index.** An index a newer Lance wrote was silently *deleted* by an older
  build: "For an index whose version this build cannot read, that turns 'ignore it' into 'delete
  it' on the next commit of any kind." Invisible in-process, since `commit_transaction` seeds the
  cache with the unfiltered list - "only a cold reader sees the loss."
- **#8511 - rebuild LabelList.** "A complete reordered source was misclassified as partial,
  causing an in-place column rewrite whose LabelList index still claimed coverage of the
  rewritten fragment."
- **#8513 - re-compact.** "Execution applied that target again as a hard `max_rows_per_file`, so
  each task above the target produced a full fragment followed by a small remainder that could
  become isolated."
- **#8839 - chmod existing files.** Data and index files were created rejecting `group` and
  `other` permissions, "which caused us trouble when using NFS"; the default is now 0o666. Files
  already written keep their old mode.
- **#8904 - restart long-lived sessions.** The index metadata cache was keyed by dataset
  URI/store identity and version, "but a recreated dataset starts its version history over, so a
  long-lived session could reuse index metadata from the previous incarnation." Now keyed on the
  manifest ETag.

**Heals on upgrade:**

- **#8512** - ZoneMap "retained physical row addresses from index creation. Deferred-remap
  compaction moved those rows and supplied a fragment-reuse remapper when the index was loaded,
  but ZoneMap search never applied it," silently dropping live rows. (Distinct from the
  stable-row-id path below.)
- **Address-domain indexes stopped falsely claiming compacted fragments.** On a stable-row-id
  dataset a rewrite used to advance every index's `fragment_bitmap` onto the new fragment ids.
  The Rewrite path now branches on `results_are_row_addrs()`: address-domain indexes get
  `drop_rewritten_fragments` instead, since "claiming coverage of the new fragments would make it
  answer queries with addresses that no longer resolve"
  (`rust/lance-table/src/transaction/manifest_build.rs:818-833`). New compactions are safe;
  an index damaged under v10 or earlier must be recreated. Section 11.5.
- **#8410** - Pylance 6.0.1 "cast each miniblock structural level count to `u16`", so list pages
  with a dense prefix and many trailing empty or null lists wrapped the header while the RLE
  payload kept every level. Restores read compatibility for files already written.
- **#8529** - unknown index detail types "were retained in the manifest but still entered the
  usable-index view and maintenance paths", so maintenance could try to open opaque metadata or
  rewrite fragments without preserving foreign index coverage.
- **#8671** - the row-id high-water mark was lost across restore.
- **#8708** - data files were not deleted when cleanup retained an older tag (storage leak;
  already-leaked files need a cleanup re-run).

### v12 (release-root/12.0.0-beta.N -> v12.0.0-beta.6)

81 commits, **exactly 3 `breaking-change`-labeled PRs** (#8606, #8640, #8903 - verified by
querying labels for all 74 PR numbers in the range). No new index types; the only format-spec
proto change in the whole range is the bit-8 reservation.

**Breaking:**

- **`WrappingObjectStore` implementors must add `wrap_paginated`** (#8606). "BREAKING CHANGE:
  `WrappingObjectStore` implementors must add `wrap_paginated`. There is no default, so the
  compiler points at every one of them." A wrapper returns `Some` to keep pushing listings down
  or `None` "to give the pushdown up and have them fall back through the wrapped `inner`", and
  one wrapper giving it up gives it up for the whole chain.
- **MemWAL `ShardManifestStore` renamed and narrowed** (#8640): `read_latest` -> `latest`,
  `read_latest_uncached` -> `refresh_latest`, `write` crate-private (reached via `commit_update`,
  `claim_epoch`, `initialize_shard`). "Downstream `commit_update` closures need no change:
  setting `version: current.version + 1` is exactly what the check expects."
- **`lance-namespace` 0.8.5 -> 0.11.1** in Python, 0.7.7 -> 0.11.1 in Java (#8903). Four
  `LanceNamespace` methods return response objects instead of bare values - `count_table_rows`,
  `query_table`, `namespace_exists`, `table_exists`. "Anyone implementing `LanceNamespace`
  themselves will need the same signature updates." Section 13.

**Format:**

- **Bit 8 reserved without being spent** (#8580). `FLAG_MIXED_DATA_FILE_VERSIONS = 1 << 8`,
  declared equal to `FLAG_UNKNOWN` and enforced by a compile-time assert, plus a
  `STICKY_PAIRED_FLAGS` carry mechanism. Spec text: implementations "that do not support the
  per-file exact-version contract must treat this bit as unknown." Only this reservation merged;
  #8581-#8585 (activation, per-op write targets, propagation, compaction targets, bindings) are
  **not in the tree**. Datasets with the bit set are still refused.
- Flag constants are now written as bit shifts rather than decimals (#8893) - "so the bit layout
  is visible at the declaration site without changing serialized values or compatibility
  behavior."

**Net-new:**

- **`ObjectStore::read_dir_page`** (#8606) - "one page of the immediate children of a prefix plus
  an opaque token that resumes after it." The trap: "One page is one request, so a page can hold
  fewer children than `limit` asked for and still be followed by more ... Callers walk until the
  returned token is `None`, not until a page comes back short."
- **Python `ObjectStoreProvider` registration** (#8522) - registers an out-of-tree provider at
  process runtime for transparent use by `lance.dataset(...)` / `lance.write_dataset(...)`. New
  surface: `_ObjectStoreRegistry()`, `registry.register_provider(scheme, provider)`,
  `Session(store_registry=...)`, `_ObjectStoreProvider.memory()`.
- **`BinaryView` accepted by the packed blob writer** (#8700) - "No changes to the on-disk format
  or persisted bytes. Existing `Binary` and `LargeBinary` inputs produce identical output."
- **Column slice stitching** (#8660) - stage immutable physical row slices during long fragment-
  local rewrites and publish only after "exact, gap-free coverage has been validated against the
  fragment snapshot". Compatible files are concatenated by relocating encoded pages; others fall
  back to decode/re-encode. "The public surface in this PR is intentionally Rust-only."
- **Two new `LANCE_*` env vars, and only these two in the whole range**:
  `LANCE_IO_SERVER_SIDE_COPY_ENABLED` and `LANCE_DEEP_CLONE_STREAM_CONCURRENCY`. Section 13.
- **Format-spec changes now require a PMC vote**, enforced by a `format-spec-vote` CI gate
  (#7399): "Keep a spec change in its own PR, together with the matching `protos/` change and
  only the library edits needed to compile."

**Fixes:**

- **#8679** - latest-version resolution no longer lists the whole `_versions/` prefix. On a
  ~340k-version table that was "~344 sequential `ListObjectsV2` pages: **~25s of pure I/O
  wait**", paid by every `open_table`/`describe`/`merge_insert`. Heals on upgrade.

**In flight, not landed** - do not treat as shipped behavior: generic block v5 sequence
compression (1 of 10 merged, #8324, which "introduces no protobuf variants or production
selector changes"), and mixed data-file versions (1 of 6, #8580). Several `xuanwo/*` remote
branches touch blob reuse indexes, stable field ids and sparse writers; none is merged into a
v12 beta.

---

### The v12.0.0-beta.6 -> v12.0.0-beta.15 delta

89 commits across nine beta tags (beta.7 .. beta.15), **exactly 2 `breaking-change`-labeled PRs**
(#8800, #8915 - verified by intersecting the 80 PR numbers in the range with every merged
`breaking-change` PR), taking the v12 line to **5**. The line has not re-rooted: no
`release-root/13.0.0-beta.N` exists and no `v12.0.0` final has been cut. No new index types, no
new crates.

**Every structural invariant still holds** at beta.15: 26 crate directories, 16 transaction ops,
`CommitConfig.num_retries = 20`, arrow 58.0.0, datafusion 54.0.0, MSRV 1.91.0, edition 2024,
`requires-python = ">=3.10"`, `FLAG_COVERED_INDEX_METADATA = 128`,
`FLAG_MIXED_DATA_FILE_VERSIONS == FLAG_UNKNOWN` (bit 8, still reserved and unspent, with the
`const _: () = assert!(...)` still pinning them together), and no new manifest feature flag.

**The label is a floor, not a ceiling.** The two largest behavior changes in the range carry a
conventional-commit `!` but **no** `breaking-change` label, so the release bot did not count them
and the major did not re-root on them.

- **`stable` now resolves to 2.2, and 2.2 is the default file version** (#8657, beta.15).
  `stable_file_version()` returns `ConcreteFileVersion::V2_2` and `#[default]` moved from `V2_1`
  to `V2_2` (`rust/lance-file/src/version.rs:18-45`). It reaches new datasets through
  `impl Default for DataStorageFormat` (`rust/lance-table/src/format/manifest.rs:677-680`), and
  Python's `write_dataset` inherits it because its default routes through `"stable"`
  (`python/python/lance/dataset.py:8059`). Upstream's framing: "Lance 2.2 is the current stable
  file format, but the centralized release policy and enum default still resolve new datasets to
  2.1. As a result, the `stable` selector and default writes lag behind the intended stable
  format." **The docs were not updated** - `docs/src/format/file/versioning.md` is byte-identical
  across the range. `next` still resolves to 2.3, `is_unstable()` is still
  `matches!(self, Self::V2_3)`, and no 2.4 exists. Section 3.1.
- **IVF_RQ defaults to 5 bits per dimension, not 1** (#8936, beta.12).
  `RABIT_DEFAULT_NUM_BITS: u8 = 5` (`rust/lance-index/src/vector/bq.rs`) drives both
  `RQBuildParams::default` and `RabitBuildParams::default`; the Python `build_rq_model` stub
  default moved with it. Roughly a **4.4x index-size increase** at the default - upstream's
  100M x 768d example went from ~10.8 GiB to ~47.3 GiB. `Fast` search mode "uses only the 1-bit
  sign code even when the index stores additional bits", so it pays the storage without using it;
  set `num_bits=1` explicitly to opt out. Section 11.1.

**Breaking (labeled):**

- **Predecessor-conditioned publication for external manifest stores** (#8800, beta.12).
  `ExternalManifestStore::put_if_predecessor` "reserves a version only if the store's record for
  the predecessor still carries the identity the writer observed"; `CommitHandler::commit_after`
  publishes on that condition and "refuses with `PrerequisiteFailed`", "never a conflict". The new
  trait methods are default-implemented, so the hard compile break is the new
  `ManifestLocation.identity: Option<String>` field killing struct-literal construction - "A
  dataset recreated at the same version has a different one". No built-in store implements the
  contract; unconditioned commits are unaffected. Section 9.
- **Namespace merge-insert accepts multiple key columns** (#8915, beta.12).
  `MergeInsertIntoTableRequest.on` moves from `Option<String>` to `Option<Vec<String>>`; Rust
  callers wrap a single column in a list. The subtle part is arity-dependent NULL handling: "a
  single-column key treats NULL as equal to NULL, while a composite key uses standard SQL
  equality, under which a NULL key matches nothing - not even a byte-identical NULL." This also
  moved the **Rust** `lance-namespace-reqwest-client` to `0.12.0` while Java and Python stay on
  `0.11.1` on purpose: "The Java and Python `lance-namespace` pins stay on 0.11, so their
  generated models still send `on` as a bare string and rely on the promotion described above."

**Reverted - do not treat as shipped:**

- **Column slice stitching (#8660) was reverted at beta.9** (#8926). "The ColumnSlice lifecycle
  introduced in #8660 should not ship while the caller-managed replacement in #8923 is being
  developed." The revert removed `concat.rs`, encoded-file concatenation, and the stitching path,
  "restoring the previous binary-copy compaction implementation". `rust/lance-file/src/concat.rs`
  exists again at beta.15, but it holds #8923's caller-managed parts, not the reverted work.

**Proto changes:**

- **MemWAL `SsTable` gained three optional accounting fields** (#8981, beta.14 - the range's only
  `format-change`-labeled PR): `in_memory_bytes` (3), `physical_rows` (4), `primary_key_bytes` (5)
  (`protos/table.proto:781,786,797`). All optional; "a reader must not treat an absent value as
  zero". Downstream struct literals for `SsTable` need updating. Section 10.
- **`FilteredReadOptions` gained `materialization_readahead_bytes` (13) and `batch_size_bytes`
  (14)** (`protos/filtered_read.proto:71,76`; #8919, #8933). These are **not** format changes
  under a new governance rule in `protos/AGENTS.md`: execution-plan schemas ("`ann.proto`,
  `filtered_read.proto`, and `table_identifier.proto`") "are wire contracts, not persisted Lance
  formats. Changes to them belong with their implementation and do not require a format vote or a
  `docs/src/format/` change."
- `transaction.proto`, `ann.proto` and `index.proto` have **zero** field-number changes in the
  range. Proto comment style is now CI-enforced (#8991, `ci/check_proto_comments.py`), which
  accounts for a large but semantically empty proto diffstat.

**Net-new, non-breaking:**

- **Caller-managed data file parts** (#8923, beta.12) - `DataFileTarget`
  (`rust/lance/src/dataset/data_file.rs:49`), `DataFilePart` and `BlobTargetId`
  (`rust/lance-file/src/concat.rs:121,:46`). Explicitly format-neutral: "No new Lance file,
  manifest, transaction, target, or part format is introduced. The completed output is an ordinary
  DataFile committed through the existing transaction path; readers cannot distinguish it from a
  normally written file."
- **Cleanup of specific versions** (#8617, beta.7) - `versions: Option<HashSet<u64>>` on the
  cleanup params (`rust/lance/src/dataset/cleanup.rs:1351`), surfaced as
  `dataset.cleanup_old_versions(versions=[2])` and Java `CleanupPolicy.withVersions`. "The filter
  combines with existing cleanup filters; current and tagged versions remain protected."
- **`LanceDataset.slice(start, end, columns=None)`** (#8059, beta.12) - "equivalent to
  take(list(range(start, end))) but implemented as a thin wrapper over scanner(offset=start,
  limit=end-start), reusing the existing offset/limit scan pushdown instead of materializing an
  index list."
- **Six more scanner options on `LanceFragment.scanner`** (#8429, beta.7): `use_scalar_index`,
  `io_buffer_size`, `late_materialization`, `include_deleted_rows`, `batch_size_bytes`,
  `strict_batch_size`.
- **Python index retraining restored** (#8786, beta.7) - `optimize_indices(retrain=...)` had been
  silently unreachable from Python since #4726; #8047 restored the Rust path "but the PyLance
  binding, documentation, and test were not restored with it."
- **`MemTableVisibility`** (#8835, beta.7) lets a MemWAL writer read its own indexed prefix -
  "Sound only for a writer reading its own prefix under the lock that makes it the sole writer."
- **Blob materialization readahead budget** (#8919, beta.10) - a scanner-level byte budget that
  "admits a single oversized batch for forward progress" and preserves output order.
- **Namespace-managed clone removed** (#8964, beta.13): "That clone mode is no longer supported
  ... `with_source_dataset` remains as a deprecated compatibility shim because published v12 beta
  releases exposed it."
- **Env vars:** the only three new `LANCE_*` names in the range are bench-only and confined to
  `rust/lance-index/benches/two_file_shuffle_read.rs` - `LANCE_SHUFFLE_BENCH_DISTRIBUTION`,
  `LANCE_SHUFFLE_BENCH_FIXTURE_ROOT`, `LANCE_SHUFFLE_BENCH_IMPLEMENTATION`. None user-facing, none
  removed.

**Correctness fixes that need a rebuild, rewrite, or repair** (they do *not* heal on upgrade):

- **#8779** (beta.12) - NGRAM FTS defaults were not substring-safe. "Existing NGRAM indexes retain
  their persisted analyzer behavior and must be rebuilt to adopt the corrected defaults."
- **#8510** (beta.11) - compaction crossed logical columns. "Binary-copy eligibility only required
  source files to agree with one another ... so uniformly reordered source files crossed logical
  columns after compaction." Data already compacted from uniformly reordered fragments is wrong on
  disk and must be rewritten.
- **#8984** (beta.14) - index maintenance could resurrect a dropped index: "A drop is encoded with
  an empty `new_indices` list, so stale optimize or append operations could be rebased after it and
  publish index metadata again." Index metadata already republished must be re-dropped.
- **#8837** (beta.7) - a MemWAL shard whose rows average below ~2.7KB never sealed on the byte arm
  and then could not be reopened: "Replay hits the same wall while rebuilding the tail memtable's
  indexes, so the shard cannot be reopened either." A shard already in this state needs repair.
  "A 1024-dim f32 vector is safe; 512-dim or 128-dim is not."

**Correctness fixes that heal on upgrade** (read-path, query-time, or write-blocking):

- **#8842** (beta.15) - RaBitQ FastScan above 1024 rotated dimensions overflowed: "a distance
  becomes `true_sum % 65536` and the ranking collapses." Query-time, but recall measured on an
  affected index before the fix is invalid.
- **#8855** (beta.14) - FM indexes on stable-row-id datasets "dropped matches outside fragment 0"
  because `FMIndexScalarIndex` declared logical row IDs instead of row addresses.
- **#8351** (beta.7) - stale vector-segment rows displaced correct top-k: "Ownership was applied
  only after the sub-index local top-k."
- **#8832** (beta.12) - PyArrow/Substrait timestamp literals decoded as the wrong unit: a filter
  "matched 0 of 100 rows where 49 was correct ... the literal arrived a million times too large."
  Any result set computed through such a filter before the fix is suspect.
- **#6236** (beta.7) - float filters compared bit encodings, so `value < 0.0` returned `-0.0` and
  `value = 0.0` missed it.
- **#8441** (beta.11) - an index this build could not open "fails that commit and every one after
  it, leaving the dataset unwritable rather than merely unreadable". Stuck datasets become
  writable again on upgrade.
- **#8935** (beta.12) - rebasing against a read version a concurrent cleanup had removed unwrapped
  a `DatasetNotFound`; under `panic = "abort"` (common under FFI) "this aborts the entire host
  process".
- **#7740** (beta.12) - an undecodable inline transaction no longer fails `load_manifest`, so an
  older build can open a dataset whose transaction uses a newer op type.
- **#9020** (beta.14) - the 2.1+ writer could not re-write what it had just written: "`write(read(write(x)))`
  fails on data this writer had just accepted." Blocks the write; no bad data lands.
- **#9048** (beta.15) - a sliced boolean column "reads from `2 * offset` and runs off the end of
  its values buffer". Panic, not silent corruption.
- **#7962** (beta.15) - the scalar index cache served results from a rotated-away store.
- Also: #8827 / #8841 (out-of-range and empty all-null dictionary keys), #8379 (nested column
  casts during schema evolution), #8929 (blob v2 complete schema collapsing to minimal), #8934
  (1-bit booleans in the single-row full-zip fallback), #7494 (duplicate field when merging
  identical `List<Struct>`), #8612 (fully deleted batch with no row to copy), #8888 / #8737 (u8
  distance accumulator overflow, unchecked cosine length), #8922 (FTS v1 merge reads), #8845
  (`distance_range` dropped for the MemWAL fresh tier), #8626 (system columns missing from SQL
  queries), #8772 (`analyze_plan` profiling the wrong join side).

**Behavior change worth calling out separately:** **#8940** (beta.12) made wrong-case GooseFS
`storage_options` keys a hard error - "Uppercase or mixed-case spellings such as
`GOOSEFS_MASTER_ADDR` are rejected with an explicit error - they are not ignored, and they are not
treated as the matching environment variable." A config that appeared to work by accident now
fails loudly. Paired with **#8943**, which added `64MB`-style binary-unit suffix parsing to
`goosefs_block_size` / `goosefs_chunk_size`. Section 13.

**In flight, not landed** - unchanged from beta.6: generic block v5 compression is still **1 of 10
merged** (#8324; #8325-#8333 all open) and mixed data-file versions still **1 of 6** (#8580, the
reservation only). New to watch: **#8997**, "upgrade to arrow 59, DataFusion 55, and pyo3 0.29",
open at beta.15 - the next big dependency break, and the reason arrow 58 / datafusion 54 still hold.
