# Lance v12 reference - indexes and distributed builds (sections 11-12)

Part of the Lance v12 reference (`lance-format/lance@v12.0.0-beta.15`). Citations are `path:line`
relative to the repo root; build a permalink as
`https://github.com/lance-format/lance/blob/v12.0.0-beta.15/<path>`. Line numbers drift between
tags - treat them as approximate. Cross-references written as "section N" use the original
16-section numbering; `lance-reference.md` maps every number to its file.

## Contents

- [11. Indexes](#11-indexes)
  - [11.1 Vector indexes](#111-vector-indexes)
  - [11.2 Scalar indexes](#112-scalar-indexes)
  - [11.3 Full-text search](#113-full-text-search)
  - [11.4 Geo / RTree](#114-geo--rtree)
  - [11.5 Index updates and reindexing](#115-index-updates-and-reindexing)
- [12. Distributed write and indexing](#12-distributed-write-and-indexing)

Other files: `format-file.md` (1-4), `format-table.md` (5-10), `ops.md` (13, 15, 16),
`changelog-v7-v12.md` (14).

---

## 11. Indexes

Lance treats indexes as **independent, redundant structures layered on top of row
identifiers** - the file format has no built-in search structures, so index formats evolve
independently (`docs/src/format/index/index.md`). Three categories: scalar, vector, system.

Index design: loaded on demand (a dataset opens without loading any index), loaded
progressively, immutable once written. An index is composed of **segments**, each with a
UUID, each covering a disjoint subset of fragments recorded in a `fragment_bitmap`. **Segments
need not cover all fragments** - an index can lag; engines split queries into indexed and
unindexed subplans and merge results. When a column has **no index at all**, both vector
search and full-text search transparently fall back to a flat scan rather than erroring
(`rust/lance/src/dataset/scanner.rs:3419,3697`). Index content lives at `_indices/{UUID}`.
`IndexMetadata` carries `uuid`, `name`, `fields`, `fragment_bitmap`, `index_details` (a typed
`Any`), `version`, and - since v11 - `covering_fields` (proto field 11).

**Covering indexes / carried columns** (v11, PR #8535; manifest flag
`FLAG_COVERED_INDEX_METADATA = 128`, section 7). `covering_fields` is "the trailing subset of
`fields` whose values the index carries but is not keyed on, letting a query that only projects
those columns be answered without a fragment take." This **redefines `fields`**: `fields[0]` is
always a keyed column, but trailing entries "may instead be merely carried, not keyed on". A
reader without the flag would select an index by plain membership of `fields` and so answer a
query on a merely-carried column with an index keyed on a different one - wrong neighbours, no
error - which is why both reader and writer must refuse a covering dataset without the bit.

The declaration is ahead of the storage: "No index builder writes carried values yet, so today
every declaration is ahead of its storage." Treat this as capability-in-place, not a speedup you
can use. The wire change itself is additive.

**The fence is deliberately not permanent, which is why the flag costs nothing today.** Bit 128
is set only while some index actually carries values:

```rust
if final_indices.iter().any(|index| !index.covering_fields.is_empty()) {
    manifest.reader_feature_flags |= FLAG_COVERED_INDEX_METADATA;
    manifest.writer_feature_flags |= FLAG_COVERED_INDEX_METADATA;
}
```

(`rust/lance-table/src/transaction/manifest_build.rs:1323-1329`.) Upstream un-sets it rather than
inheriting it, precisely so the fence lifts again: "fence by simply not setting it again.
Inheriting it from the previous manifest instead would make the fence permanent." The practical
consequence is that because no builder writes `covering_fields`, the bit is never set in normal
operation - so v11/v12-written datasets stay openable by older builds despite the flag existing.

### 11.1 Vector indexes

Every vector index has **three orthogonal parts: clustering, sub-index, quantization**, named
`{clustering}_{sub_index}_{quantization}` (`docs/src/format/index/vector/index.md`).

- **Clustering** - only **IVF** (Inverted File): k-means partitioning; search examines only
  the most relevant clusters.
- **Sub-index** - `FLAT` (exact, scans all vectors) or `HNSW` (approximate graph search).
- **Quantization** - `FLAT` (none, exact), `PQ` (Product Quantization), `SQ` (Scalar
  Quantization), `RQ` (RaBitQ - random rotation + binary quantization).

The seven documented combinations: `IVF_FLAT`, `IVF_PQ`, `IVF_SQ`, `IVF_RQ`,
`IVF_HNSW_FLAT`, `IVF_HNSW_SQ`, `IVF_HNSW_PQ`.

`protos/index.proto:115` also carries a **`DiskAnn`** stage message. It is part of the persisted
wire format rather than one of the seven documented builder combinations - expect to encounter
it when reading index protos, not when choosing an index type.

**Distance metrics** (`VectorMetricType`): `L2` (0), `Cosine` (1), `Dot` (2), `Hamming` (3).
SIMD kernels in `lance-linalg`; the `fp16kernels` feature compiles C SIMD kernels for fp16.

**Compression** (bytes per vector vs float32):

| Quantization | Storage | Ratio |
|--------------|---------|-------|
| FLAT | `dimension * 4` | 1x (exact) |
| SQ (8-bit) | `dimension` | ~4x |
| PQ | `num_sub_vectors` (one uint8 code per sub-vector) | ~`(dimension*4)/m` |
| RQ (RaBitQ, `num_bits` bits/dim) | `ceil(dimension * num_bits / 8)` + correction factors | ~32x at 1 bit; ~6.5x at the 5-bit default |

**IVF_RQ requires the vector dimension to be divisible by 8** - enforced with the error
"vector dimension must be divisible by 8 for IVF_RQ" (`rust/lance-index/src/vector/bq/builder.rs`).
**RaBitQ is now multi-bit** (new in v8, PR #7038): `num_bits` is "in the range 1..=9"
(`docs/src/format/index/vector/index.md:255`). IVF_RQ always stores the 1-bit binary sign
code in `_rabit_codes`; for `num_bits > 1`, the remaining `num_bits - 1` ex-code bits are stored
in a separate column instead of widening the binary code path, alongside `__add_factors_ex` /
`__scale_factors_ex` correction columns.

**The ex-code column was renamed in v11** (#8407). Writers now emit **`__blocked_ex_codes`**,
sized `next_multiple_of(code_dim, 64) * (num_bits - 1) / 8`. The old column is still readable:
"Indexes written before the blocked ex-code layout store the same bits in `__ex_codes`, sized
`ceil(dimension * (num_bits - 1) / 8)`. Readers still accept that column and repack it at load
time; writers no longer emit it" (`docs/src/format/index/vector/index.md:207-209`). Two sibling
sizing corrections landed with it: `__pq_code` is
`list<uint8>[num_sub_vectors * num_bits / 8]` (not `[m]`), and `_rabit_codes` is
`ceil(code_dim / 8)` (not `dimension / 8`). Every vector-index storage column is also now
declared **nullable**, and the RQ rows gained a separate "Present when" column.
A new `query_estimator` metadata field selects the distance-estimator layout: "`residual_query`
or `raw_query`. Missing values are read as `residual_query` for compatibility with released
1-bit IVF_RQ indexes" (`index.md:258`); raw-query search (PR #7078) adds an `__error_factors`
column "for raw-query lower-bound pruning" (`index.md:201`). The metadata schema also carries
`code_dim` (u32, the rotated-vector dimension).

**`num_bits` now defaults to 5, not 1** (#8936, `v12.0.0-beta.12`) - the PR carries a
conventional-commit `!` but no `breaking-change` label, so the release bot did not count it.
`RABIT_DEFAULT_NUM_BITS: u8 = 5` (`rust/lance-index/src/vector/bq.rs`) drives both
`RQBuildParams::default` and `RabitBuildParams::default`, and the Python `build_rq_model` stub
default moved with it. Per-row storage (`docs/src/guide/performance.md:483-501`):

- 1-bit: `dimension / 8 + 20` bytes
- Multi-bit: `dimension / 8 + round_up(dimension, 64) * (num_bits - 1) / 8 + 28` bytes

"Every bit width stores a 1-bit sign code plus three 4-byte correction factors." Multi-bit adds
the `__blocked_ex_codes` and ex-factor columns on top of the sign code.

**Budget for a ~4.4x jump if you relied on the default.** Upstream's own worked example moved
from `100M * (768 / 8 + 16) = ~10.8 GiB` to
`100M * (768 / 8 + 768 * 4 / 8 + 28) = ~47.3 GiB`. The escape hatch is explicit and documented:
"`Fast` search mode uses only the 1-bit sign code even when the index stores additional bits. Set
`num_bits=1` explicitly to minimize index size and build I/O; the same 100M-row example uses about
10.8 GiB, but searches cannot use the multi-bit distance estimate and may have lower recall."
So `Fast` mode gains nothing from the wider default while paying its full storage cost.

**A separate multi-bit correctness fix landed at beta.15**: RaBitQ FastScan above 1024 rotated
dimensions overflowed its accumulator (#8842) - "the scalar path saturates and the AVX2/AVX-512/NEON
kernels wrap, so a distance becomes `true_sum % 65536` and the ranking collapses. At rotated dim
4096 a full-range sum reaches 261120, four times the ceiling." Query-time only, so it heals on
upgrade - but any recall figure measured on an affected index before the fix is invalid.

**bfloat16 is not usable for vector indexes**, despite the docs recommending it as an embedding
type directly above an IVF_PQ `create_index` example (`docs/src/guide/data_types.md:406`). The
`lance.bfloat16` extension stores as `FixedSizeBinary(2)`, and the accepted element types are
only `Float16 | Float32 | Float64 | UInt8 | Int8`
(`rust/lance/src/index/vector/utils.rs:244`). The rejection fires on **both** the index-build
and the query path (`scanner.rs:1647`, `knn.rs:397`), so it is not a build-time-only limit. The
in-tree error message is itself stale - it omits `Int8` from the list it actually accepts.

**Approx mode** (new in `v8.0.0-beta.10`, PR #7179). Vector search takes a public
`approx_mode` with three values - "`fast`, `normal`, and `accurate`" - to pick the
speed/accuracy tradeoff "when the backing index supports it" (RaBitQ today). "The public API
avoids exposing RaBitQ/HACC terminology" (commit `e25620710`). It threads through the Rust
scanner, the ANN proto, and Python query parsing; serialized as `VectorApproxMode approx_mode`
(`protos/ann.proto:16,45`) - a **breaking ANN-proto change**, so any consumer matching Lance's
serialized ANN query proto must regenerate. Multi-bit RaBitQ ex-code reranking also got
dedicated SIMD kernels (PR #7205, `rust/lance-index/src/vector/bq/ex_dot.rs`). **IVF_RQ now
defaults `target_partition_size` to 4096** (was the generic fallback, PR #7273).

**Query-time knobs: `nprobes` and `refine_factor`.** Distinct from the build-time parameters
above, and the two the docs put front-and-center for tuning a live query: "The latency vs recall
is tunable via: **nprobes**: how many IVF partitions to search / **refine_factor**: determines
how many vectors are retrieved during re-ranking"
(`docs/src/quickstart/vector-search.md:208-210`). `nprobes` trades read volume for recall by
widening the partition sweep; `refine_factor` over-fetches quantized candidates and re-ranks
them against full-precision vectors, so it recovers accuracy lost to PQ/SQ/RQ compression at the
cost of extra `take`s. Reach for these before rebuilding an index with different parameters -
they need no reindex.

On-disk layout (format V3): each vector index is two Lance files - an **index file**
(`index.idx`, the search structure: IVF metadata, HNSW graph) and an **auxiliary file**
(`auxiliary.idx`, quantized vector storage). HNSW construction defaults: `max_level` 7, `m`
20, `ef_construction` 150. The PQ codebook and the RaBitQ rotation matrix are stored as
tensors in the auxiliary file's global buffer.

**HNSW construction changed in v11 (PR #8188, BREAKING).** Three things at once:
`OnlineHnswBuilder::with_capacity` is `#[deprecated]` in favour of a fallible
`try_with_capacity` that runs shared parameter validation
(`rust/lance-index/src/vector/hnsw/online.rs:161,174`); **`m < 4` is now rejected** ("must be at
least {MIN_HNSW_M} to avoid severely fragmented graphs", `builder.rs:144`); and the persisted
level layout was corrected from `max_level` offsets to `max_level + 1`, because "truncating
persisted levels to the sampled height also broke version-1 readers that index the configured
level count directly". `HnswBuildParams::default()` is unchanged (`m: 20`). **Expect different
graphs and different recall from the same inputs** after upgrading. Separately, greedy descent
now stops before level 0 - "the greedy (ef=1) descent should cover only levels `max_level-1`
down to 1; level 0 must be searched solely by the ef-bounded beam search" (PR #8035,
`builder.rs:396,546`) - worth +3.7% recall@10 at ef=16.

Minor v11 fix: `QuantizationType`'s `FromStr` now accepts `"RQ"` as well as `"RABIT"`
(`rust/lance-index/src/vector/quantizer.rs:86`, PR #8214) - `Display` wrote `"RQ"` but `FromStr`
rejected it, so the two never round-tripped.

**"partition N is empty, skipping" is benign by design.** During an IVF build, an empty
partition emits `log::warn!("partition {} is empty, skipping", part_id)`
(`rust/lance/src/index/vector/builder.rs:1174`) and then registers a zero-sized partition in both
the storage and index IVF models and continues the merge loop (`:1176-1180`). There is no
`Result::Err` and no exception to catch, so on a skewed or sparse dataset this floods logs
without indicating a failure - suppress it with a scoped tracing filter rather than hunting a
bug. (The one genuine error mentioning empty partitions is a guarded inconsistency case at
`:1100`, reachable only when a partition reports a non-zero size yet reads back `None`.)

**Typed index details.** A vector index records a typed `VectorIndexDetails` message in the
manifest's `index_details` field (`protos/index.proto:188-241`; moved out of `table.proto`
in `v7.1.0-beta.1`): `metric_type`, `target_partition_size` (0 = unset), an optional
`HnswParameters` (`max_connections` = M, `construction_ef`, `max_level`), a `compression`
oneof (`ProductQuantization` / `ScalarQuantization` / `RabitQuantization` with a `FAST` or
`MATRIX` rotation / `FlatCompression`), and a free-form `runtime_hints` string map. Hint
keys use reverse-DNS namespacing (e.g. `lance.ivf.max_iters`) and unrecognized keys must be
silently ignored by all runtimes.

**Build prerequisites.** A vector index cannot be built on an empty table -
`build_empty_vector_index` returns `not_supported` ("Creating empty vector indices with
train=False is not yet implemented", `rust/lance/src/index/vector.rs:1437`). PQ training
needs at least `2^num_bits` rows for its codebook centroids, so a default 8-bit PQ index
hard-errors below **256 rows** ("Not enough rows to train PQ. Requires {n} rows but only {m}
available", `rust/lance-index/src/vector/pq/builder.rs:177`); IVF k-means separately needs at
least `num_partitions` rows. Build vector indexes lazily, once the table holds data.

**Batched vector queries** (PR #6828). `Scanner::nearest` accepts a batch of query vectors on
a fixed-size-list column - there is no separate `nearest_batch` API. Batched results carry a
synthetic 0-based `query_index` discriminator column (`QUERY_INDEX_COL`) so each result row is
attributable to its source query (`rust/lance/src/dataset/scanner.rs:104,1972`).

**Streaming IVF k-means training** (PR #6913). For bounded-memory IVF training on large
datasets, the IVF builder exposes `streaming_sample_rate`, `streaming_coreset_rate`, and
`streaming_refine_passes` (exposed through Python). When set, training loads at most
`num_partitions * streaming_sample_rate` vectors and keeps the total sampled set bounded
(`rust/lance-index/src/vector/ivf/builder.rs:44-51`).

**ACORN-1 prefiltered HNSW traversal (v10, PR #7927).** A prefilter-aware graph traversal for
HNSW, **opt-in only**: it is gated on `ApproxMode::Fast` (Python `approx_mode="fast"`), with no
env var. "`Normal` (the default) and `Accurate` keep the existing traversal, so default behavior
is unchanged." Do not reach for it reflexively - upstream documents a real regression on
low-selectivity uniform-random masks: "uniform random masks at 2% selectivity drop recall (0.775
vs 0.975 on GIST1M), and at 50% random the waypoint bookkeeping makes it slower than the current
traversal (15.3 vs 4.1 ms)." It pays off on *clustered* prefilters, not random ones. Its
constants are not tunable: 16 mask-sampled seeds (`ACORN_SEED_COUNT`,
`rust/lance-index/src/vector/graph.rs:550`) and a `4 * ef` waypoint budget. Narrow API break: the
all-public `HnswQueryParams` gained a required `use_acorn: bool` field
(`rust/lance-index/src/vector/hnsw/builder.rs:1104`), so struct-literal construction no longer
compiles.

Two runtime escapes make `approx_mode="fast"` weaker than "ACORN is on": even when requested,
ACORN is **skipped** when the mask passes all rows or when fewer than 10% of rows survive it,
and an under-delivering traversal falls back to `search_basic`
(`rust/lance-index/src/vector/hnsw/builder.rs:1367-1388`). So a benchmark that sees no change
from `fast` may simply never have entered the ACORN path. The opt-in gate itself is unchanged in
v11 despite the surrounding HNSW rework (PRs #8188, #8035 both leave `use_acorn: query.approx_mode
== ApproxMode::Fast` at `:1170` intact).

**Vector index append across heterogeneous models (v10, PR #8047).** Appending to a vector index
whose segments were trained with different IVF/quantizer models previously failed. Append now
writes **one** new segment over the unindexed fragments, using the manifest-suffix segment's
model. Explicit `OptimizeOptions::retrain` remains the only operation that rebuilds from source
and unifies models.

**v9 vector changes.** `as_vector_index` was **removed from the public `Index` trait**
(PR #7392) - downcast via `as_any()` instead. A new **hamming clustering** utility (PR #7379,
`rust/lance-linalg` + `rust/lance`) does SIMD-accelerated (AVX-512/AVX2) pairwise Hamming
distance over 64-bit binary hashes plus union-find grouping for near-duplicate detection:
`pairwise_hamming_distance[_parallel]`, `UnionFind`, and `hamming_clustering_for_ivf_partition`
/ `_for_sample` / `_for_range` / `_from_hashes` returning a `RecordBatchReader` of clusters.
This is a clustering *utility* over binary vectors, distinct from the `Hamming` distance
*metric* already listed above. Separately, `COUNT(*)` pushdown now works on **stable-row-id**
datasets (PR #7360) - the `CountFromMaskExec` fast path no longer falls back to a full scan
when stable row IDs are enabled. A vector-search correctness fix also accounts for the SQ
offset in dot-distance (PR #7481).

### 11.2 Scalar indexes

`docs/src/format/index/scalar/`. Results are **exact** (BTREE, BITMAP, LABEL_LIST) or
**inexact / AtMost** (BLOOM_FILTER, NGRAM, ZONEMAP, RTREE) - except that ZONEMAP and
BLOOM_FILTER now answer **`IS NULL` exactly** (see the `null_bitmap` note below).

| Index | For | Structure |
|-------|-----|-----------|
| BTREE | Range queries, sorted access, high-cardinality columns | Two-level: in-memory page lookup + on-disk sorted leaves, default 4096 rows/page |
| BITMAP | Low-cardinality columns, fast set membership | One bitmap (serialized `RowAddrTreeMap`) per distinct value |
| LABEL_LIST | Multi-value / tag columns | Built on a bitmap index; supports `array_has`/`_all`/`_any` |
| NGRAM | Substring matching | Overlapping trigrams (ASCII-folded, lowercased); query `contains`. Since v9 also accelerates regex and infix `LIKE` (PR #7139) |
| ZONEMAP | Scan pruning / predicate pushdown | Per-zone min/max/null stats (default 8192 rows/zone); a *primary skipping structure* |
| BLOOM_FILTER | Probabilistic membership | Zone-based Split Block Bloom Filters (xxHash64; default 8192 items/zone, FPP 0.00057) |
| FM_INDEX | Substring / prefix / regex search on raw bytes | Compressed BWT index over raw byte arrays; built on the Segmented Index architecture (see 11.5). New in v8 |
| RTREE | 2D spatial pruning | See 11.4 |

NGRAM, ZONEMAP, and BLOOM_FILTER are newer additions. A JSON scalar index wraps another
index's details with a JSON path. Since v9, **BTREE and ZONEMAP accept `large_string`
(`LargeUtf8`) columns** (PR #7525), not just `Utf8`. A ZoneMap index also exposes a column's
global **min/max without a scan** via `zonemap_value_range(column)` (`DatasetIndexExt`;
`ZoneMapIndex::value_range` / `value_range_over(segments)`, PR #7463) - cheap stats and a
range-pruning planning input.

As of v9.1, both **ZONEMAP and BLOOM_FILTER carry a `null_bitmap`** (a serialized
`RowAddrTreeMap` of null rows) that upgrades **`IS NULL` from inexact to Exact** - "since
finding NULLs is a common query pattern, the index also maintains a bitmap of null rows which
allows it to return exact results for IS NULL queries" (`docs/src/format/index/scalar/bloom_filter.md`,
`.../zonemap.md`). Other predicates on these indexes stay inexact/`AtMost`.

**For SBBF internals, read the spec page directly.** `references/docs/format/index/scalar/bloom_filter.md`
carries the block structure ("The SBBF divides the bit array into blocks of 256 bits, where each
block consists of 8 contiguous 32-bit words"), the 8 salt constants, and the binary-search sizing
algorithm behind the FPP figure. None of that is restated here - go to the mirror when you need to
reimplement or validate a filter rather than just use one.

**In v11 that capability became wire-explicit and grew a second half** (PR #8088). The zone-map
details proto gained `optional bool has_null_bitmap = 3` (`protos/index_old.proto:44`),
documented as: "Absent or false means legacy format: null positions are not tracked and IS NULL
searches fall back to approximate zone-level statistics. Present true means IS NULL is exact
**and IS NOT NULL can be answered without a full scan**" (`:42-47`). The flag is set from
`builder.null_rows.is_some()` (`rust/lance-index/src/scalar/zonemap.rs:1189`), so an index built
before v11 keeps the legacy behaviour until rebuilt - check the flag before assuming exactness.

**Zone maps now cover every data type, including nested ones** (PR #8017): "We are using zonemap
as our 'statistics' and it is also important for recording nullability bitmaps. As a result, we
need it to support all types. For nested types we don't track the min/max but we still track the
nullability bitmap and the null count." For List, FixedSizeList, Struct, and Map columns, min and
max are stored as typed null values (`rust/lance-index/src/scalar/zonemap.rs`) - so a zone map on
a nested column buys null statistics and nothing range-related.

**Scalar-index pushdown is volume-independent.** The planner emits a `ScalarIndexQuery` whenever
an index exists for the column - `apply_scalar_indices` is driven purely by whether
`index_info.get_index(col)` answers (`rust/lance-index/src/scalar/expression.rs:2612`), with no
row-count, cardinality, or selectivity heuristic anywhere in the module. The plan for a 4-row
table and a 2000-row table is identical. Only two non-volume gates exist: `use_scalar_index` is
suppressed for a non-prefiltered vector search (`let use_scalar_index = self.use_scalar_index &&
(self.prefilter || self.nearest.is_none())`, `rust/lance/src/dataset/scanner.rs:2812`), and
scalar indexes are skipped entirely when any fragment lacks `physical_rows` metadata ("We need
row counts to use scalar indices", `scanner.rs:2668`) - that is metadata *presence*, not
magnitude. Practical consequence: "indexes only pay off at scale" is false here; a scalar index
on a small table is used, for better or worse.

**FM-Index** (new in v8, `docs/src/format/index/scalar/fmindex.md`,
`protos/index.proto:251` `FMIndexDetails` - **renamed from `FMIndexIndexDetails` in v9**,
PR #7397, a **breaking change that makes existing FM indexes unreadable**; the rename also
dropped the `get_plugin_name_from_details_name` `fmindex`->`fm` special-case). The
Ferragina-Manzini index is "a compressed
substring index based on the Burrows-Wheeler Transform (BWT)" that "enables efficient
**arbitrary substring search**, **prefix match**, and **suffix/regular-expression search**
directly on raw bytes" (`fmindex.md:3`) - unlike the NGRAM index (fixed trigrams) or FTS
(distinct words). It indexes columns of strings or binary as raw byte arrays, so it is
**normalization-independent by design**: any case-folding / Unicode / stemming normalization
is the caller's job and must be applied identically to the column at build time and to the
query (`fmindex.md`). Two bytes are reserved as BWT sentinels (`\x00` terminator, `\xFF`
row separator) and any incoming `\x00`/`\xFF` are sanitized to space (`\x20`) at build time.
Because a BWT suffix array cannot be merged by concatenation, FM-Index is partitioned via
the Segmented Index architecture: a `num_segments` parameter (set at index creation) splits
fragments into disjoint subsets, each a self-contained FM-Index; appends build a new segment
over the unindexed fragments, and `merge_segments` re-reads the covered fragments' raw text
to rebuild a unified segment (`fmindex.md:53`). Queries (`CONTAINS(column, "...")`) return an
inexact candidate set; the engine verifies.

**Choosing between NGRAM, FM-Index, and FTS for substring work.** These three are not
interchangeable, and two column-level constraints decide the choice before performance does:

- **NGRAM requires a real text column.** "A ngram index can only be created on a Utf8 or
  LargeUtf8 field" (`rust/lance-index/src/scalar/ngram.rs:1690-1692`) - a `LargeBinary` column
  (a JSONB/`lance.json` column, for instance) is rejected outright. FM-Index *will* build on
  binary, but DataFusion's `contains` refuses to coerce `LargeBinary` to `Utf8`, so the query
  cannot reach it; a `CAST(... AS VARCHAR)` makes the plan legal but defeats index pushdown and
  falls back to a full scan. If you need substring search on a column, store it as text.
- **NGRAM and FM-Index disagree on matching semantics, silently.** NGRAM is always case- and
  accent-insensitive: "Currently we ALWAYS use trigrams with ascii folding and lower casing. We
  may want to make this configurable in the future" (`ngram.rs:93`), applied through the shared
  `TEXT_PREPPER` (`LowerCaser` + `AsciiFoldingFilter`, `:87-91`) on **both** the build and query
  paths (`:1150`, `:507`). FM-Index has no case handling at all - queries go straight to
  `search_string_contains(pattern.as_bytes())` (`fmindex.rs:1638`). The same needle therefore
  returns different result sets from the two indexes, with no warning.
- **FTS answers a different question.** It matches whole tokens, so it is the wrong tool for
  identifier or mid-token lookup: a needle that appears inside larger tokens matches nothing
  under FTS while NGRAM/FM find it, and a needle that is also a common token can match orders of
  magnitude more rows than the exact substring occurrences.

**v10 scalar-index changes.** BTREE + ZONEMAP `large_string` support (v9) is joined by
**LABEL_LIST accepting `LargeList`** (PR #7884) - previously a `LargeList` LABEL_LIST filter
silently fell back to a full scan because `ScalarValue::LargeList` was not accepted. Two
planner fixes: same-column range predicates with *differing* index fragment coverage were
merged unconditionally, claiming coverage they did not have - `index_type` is now part of the
merge key (PR #6782); and an index built from a stale handle and committed after a concurrent
`Operation::Update` no longer retains coverage over fragments whose indexed column changed -
"The fix applies to all index types" (PR #8011). A new optimizer rule drops an exact
`IS NOT NULL` when another exact same-index query is already null-intolerant (disabled under
`NOT`). Two new per-query metrics, `index_cache_hits` / `index_cache_misses`, surface in
EXPLAIN ANALYZE, `ExecutionSummaryCounts`, Python `ScanStatistics`, and Java `ScanStats`
(PR #7862) - with a caveat: "IVF v2 streaming scans and legacy v1 IVF partitions run
`load_partition` with `write_cache=false`. Those loads always execute the loader and never write
the result back, so they are reported as a miss on every call."

**Scalar-index fast search** (PR #6784). `fast_search` now routes through scalar/BTREE-indexed
fragments and skips unindexed ones, so a filtered query can return from the index without a
flat scan of recently appended (still-unindexed) fragments. Not supported on the legacy file
version (`LanceFileVersion::Legacy`). This mirrors the long-standing vector `fast_search`
behavior - both return only what the index covers, trading completeness for latency until
`optimize_indices` folds the new fragments in.

### 11.3 Full-text search

The FTS (inverted) index maps terms to documents with **BM25** scoring
(`docs/src/format/index/scalar/fts.md`). It is **Lance-native** - there is no Tantivy
dependency; the tokenizer stack lives in the `lance-tokenizer` crate (one tokenizer, the
ngram tokenizer, is noted as adapted from Tantivy, but the FTS engine is Lance's own).

Storage: `tokens.lance` (dictionary), `docs.lance` (doc metadata), `invert.lance`
(compressed posting lists, optional positions), `metadata.lance`. An FTS index may be
**partitioned** - every partition is searched at query time and results combined.

**On-disk format version (v9, breaking).** Newly created FTS / inverted indexes now default to
**format v2** (PR #7512, `docs/src/guide/migration.md:9-30`): "Newly created FTS / inverted
indexes now default to format v2 instead of v1. The `LANCE_FTS_FORMAT_VERSION` environment
variable no longer controls the format used for newly created indexes ... pass the index
creation parameter `format_version` explicitly." Pass `format_version=1` (accepts `1`/`2`/`"v1"`
/`"v2"`, `create_scalar_index("text", "INVERTED", format_version=1)`) when older Lance readers
must read the index - "older Lance readers may not be able to read them" otherwise. Existing v1
indexes stay queryable and are **maintained as v1**: "append, incremental indexing, optimize,
and mem-wal maintained-index flush ... continue preserving the v1 format."

**Configurable posting `block_size` (v9.1, breaking, PR #7466).** FTS index creation takes a
`block_size` param - documents per compressed posting block, "must be 128 or 256" (default
128; missing values in older indexes read as 128; unsupported values like 512 are rejected by
`validate_format_version_block_size`, `rust/lance-index/src/scalar/inverted/builder.rs:229`).
"`256` is experimental and may introduce breaking changes." Both `block_size=256` and the new
**code analyzer** require FTS on-disk **format v3** (the capability gate moved to v3, PR #7866):
"The code analyzer and `block_size=256` require format v3, so readers must support v3 before an
index using either option is created" (`docs/src/guide/migration.md`). As of v11 there is a
**third** v3 trigger, independent of the other two: "`document_granularity=\"list_element\"` also
requires v3 reader capability, independently of the posting format"
(`docs/src/guide/migration.md:13-14`).

**Document granularity (v11, PR #7788).** FTS gained an explicit document-boundary axis. The
index details proto carries `DocumentGranularity document_granularity = 14` with values
`ROW = 0` / `LIST_ELEMENT = 1` - "The logical FTS document boundary. The protobuf default
preserves the legacy row-document behavior when this field is absent"
(`protos/index_old.proto:96-97`) - so existing indexes keep row-granularity semantics with no
migration. `LIST_ELEMENT` treats each element of a list column as its own document, which
changes what BM25 scores and what a phrase can span. A companion output column
`_doc_index` (`DOC_INDEX_COL`, storage prefix `_doc_index_`,
`rust/lance-index/src/scalar/inverted/index.rs:140-141`) identifies which element matched.
Exposed as `create_scalar_index(..., document_granularity=...)` plus `MatchQuery` / `PhraseQuery`
parameters in Python (`python/python/lance/query.py:25,108,169`), and
`InvertedIndexParams.Builder.documentGranularity(..)` with `FullTextQuery` overloads in Java.
Rust callers note: `load_segments` gained a third `document_granularity` parameter.

The same PR added **`posting_format_version = 15`**, deliberately separate from `index_version`:
"The posting-list payload format. This is separate from index_version, which identifies the
overall inverted-index layout" (`protos/index_old.proto:99-100`). Do not conflate the two when
reasoning about reader compatibility - the maximum inverted-list format is still V3.

**Nested-field FTS (PR #7686).** FTS can now index leaf fields inside nested columns
(e.g. `data.text`), not just top-level string columns. Query-side bulk paths were added too:
impact-skip data for posting lists (#7602), a bulk MAXSCORE top-k path for disjunctions
(#7603), and a bulk conjunction path for AND / phrase queries (#7624).

**v10 FTS changes.** Format versions at this tag are V1/V2/V3; the **written default is still
V2**, max supported is V3, and `block_size=256` still requires `format_version=3` ("FTS
format_version={} is incompatible with block_size=256; use format_version=3",
`rust/lance-index/src/scalar/inverted/index.rs:101,279`). Compatibility fixtures pin v1 and v2
only - "FTS v3 is intentionally deferred until it is written by a stable release" (PR #7890) -
and readers must keep tolerating the retired `skip_merge` parameter written by Lance 3.0.1.

- **Optional `total_tokens` metadata key** (PR #7863): "Partitioned `docs.lance` files may
  include the optional schema metadata key `total_tokens`. Its decimal `UInt64` value is the sum
  of `_num_tokens` in that file" (`docs/src/format/index/scalar/fts.md:37-38`); when absent,
  readers compute the sum. Back-compatible on-disk addition, no format bump.
- **`LANCE_FTS_SEARCH_CHUNK`** (PR #7950) - partitions searched per CPU-pool task, default
  **16**, minimum 1, non-numeric values ignored (`inverted/index.rs:115`). Chunking stops query
  concurrency from flooding the pool with one small task per partition; `=1` restores the old
  per-partition shape. Measured 227 -> 428 qps at concurrency 16.
- **Row-id resolution moved after the global top-k merge** (PR #7897) - at most `limit` lookups
  per query instead of per-partition resolution: 4.1 -> 107.7 qps (26x), 3.9 s -> 148 ms on a
  100M-doc benchmark. The cost is that each partition's ROW_ID column is now its own weighed
  index-cache entry (~8 bytes/doc per partition; ~800 MB for a 100M-doc index), and it now
  counts against `index_cache_size_bytes` - budget for it.
- **Deterministic tie ordering** - compound FTS ties are now ordered `_score DESC, _rowid ASC`
  (PR #8073), which also fixed nested `MultiMatchQuery` taking its fetch limit from the ambient
  scanner limit instead of the recursive FTS params (omitting the true top-k under
  MUST/SHOULD/BoostQuery).
- **BREAKING (Rust)**: public `InvertedPartition::bm25_search` was removed, split into private
  `bm25_search_legacy` / `bm25_search_modern` (PR #7863). New legacy indexes are no longer
  written; `metadata.lance` is unchanged. New public
  `MatchQueryExec::new_with_segment_uuids` / `PhraseQueryExec::new_with_segment_uuids` plus an
  `fts_segment_bind_duration` metric (PR #7976).

Tokenizer pipeline (`InvertedIndexParams`): a base tokenizer (`simple`, `whitespace`, `raw`,
`ngram`, `icu`, `icu/split`, `code` (the v9.1 code analyzer / `CodeLexTokenizer` +
`WordDelimiterFilter`, PR #7681 - splits identifiers like `getUserName`/`snake_case`),
`jieba/*` for Chinese, `lindera/*` for Japanese) followed by
token filters (`RemoveLong`, `LowerCase`, `Stemmer`, `StopWords`, `AsciiFolding`) - stop
words can now be **mixed-language** (PR #7324). The `icu` tokenizer
(PR #6956) does ICU4X dictionary-based Unicode word segmentation with **bundled segmenter
data** - unlike jieba/lindera it needs no external language model; the v9 **`icu/split`**
variant (PR #7474) applies ICU segmentation with simple-style delimiter splitting
(`rust/lance-index/src/scalar/inverted/tokenizer.rs:390`, `docs/src/guide/tokenizer.md:1`). The
default base tokenizer remains **`simple`** (`tokenizer.rs:187`); a PR making ICU the default
(#6968) was reverted (#7006) because "ICU showed behavior differences that are too large for
the default path." Config keys:
`base_tokenizer`, `language`, `with_position` (store positions for phrase queries),
`lower_case`, `stem`, `remove_stop_words`, `ascii_folding`, ngram `min_gram`/`max_gram`/
`prefix_only`.

**The 18 stemming / stop-word languages**, in full: Arabic, Danish, Dutch, English, Finnish,
French, German, Greek, Hungarian, Italian, Norwegian, Portuguese, Romanian, Russian, Spanish,
Swedish, Tamil, Turkish (`docs/src/format/index/scalar/fts.md:159`). Anything outside that set
needs a base tokenizer that segments it (`icu`, `jieba/*`, `lindera/*`) rather than a stemmer.

**User dictionaries and custom language models.** The jieba and lindera tokenizers both accept
**user dictionaries** to override segmentation of domain terms, and the guide has a dedicated
"Create your own language model" procedure (`docs/src/guide/tokenizer.md:45,77,89`) for building
a model Lance can load from disk. This is the escape hatch when the bundled Chinese/Japanese
models split your vocabulary wrongly - reach for it before abandoning FTS for ngram.

**Two document types, two tokenization rules.** "Lance supports 2 kinds of documents: text and
json. Different document types have different tokenization rules, and parse tokens in different
format" (`docs/src/format/index/scalar/fts.md:162-163`). FTS over JSON documents breaks them
into `path,type,value` triplet tokens rather than plain terms, so a JSON-typed FTS index and a
text FTS index over the same bytes are not query-compatible. The spec also covers distributed
training for FTS at `fts.md:262`.

Query types (all inexact): `contains_tokens`, `match` (AND/OR), `phrase` (requires
`with_position`), `boolean` (must/should/must_not), `multi_match`, `boost`.

**Compound scoring core (v11, PRs #8092-#8094, #8131, #8299).** Compound FTS queries moved onto
a posting-backed scoring core: an internal `ComposableScorer` protocol, a cross-partition
`TopKCollector`, incremental `WandCursor` support, and `CompoundQueryExec` integration
(`rust/lance-index/src/scalar/inverted/compound.rs`, new at this tag). Semantics to know:

- **Boolean composition** - `SHOULD` clauses sum scores; `MUST` clauses intersect membership
  while preserving the existing first-`MUST` scoring contract; `MUST NOT` filters confirmed
  matches. Concretely, at the query level: "Every query combined with `AND` becomes a scoring
  `MUST` clause: all clauses must match, and every matching clause contributes to the final
  `_score`" (`docs/src/quickstart/full-text-search.md:245-246`) - so adding an `AND` term changes
  ranking, not just filtering.
- **Phrase leaves** use a two-phase `matches()` hook for positional confirmation, so
  **phrase-containing compound queries require an index built `with_position`**.
- **Boost** composes as a nested node inside same-column Boolean/Phrase scorer trees, with
  signed score bounds; match and boost multipliers "are rejected unless finite and non-negative".
- **`CompoundQueryExec` is now public** (`rust/lance/src/io/exec/fts.rs:378-478`) with an
  injectable base scorer and `new_with_segments` / `new_with_segment_uuids` constructors, for
  distributed engines driving FTS themselves.
- Conjunction approximations are ordered by iterator cost (#8299): "Keep scorer children in query
  order so score summation, score bounds, document keys, and ties remain bit-for-bit stable" -
  1.50x fewer comparisons, 1.12x speedup, with results unchanged.
- Conjunction confirmations are ordered by `match_cost` (#8354), measured **200 -> 120**
  two-phase `matches()` calls per query; same-column `MUST + SHOULD` scores the optional side
  lazily, "only touch[ing] the optional side when it can change competitiveness or an exact
  score is requested" (#8448).

**When the posting-backed scorer bails out.** `CompoundQueryExec` refuses the fast path and
reverts to the materializing hash-join plan whenever the table has **any unindexed fragment**,
the query spans **more than one column**, granularity is **`ListElement`**, or the overlay plan
is not `Unchanged` (`rust/lance/src/dataset/scanner.rs:3940-3948`). The first condition is the
one that bites in practice: a table with an unindexed tail silently gets the slower plan, so
benchmark compound FTS only after the backlog is folded in.

#### Inspecting tokenization (v11)

`lance.tokenize(...)` previews the tokens a full-text query will produce **without creating a
dataset or index** (#8415): "Use `lance.tokenize` to inspect the tokens that a full-text query
will produce without creating a dataset or index" (`docs/src/guide/tokenizer.md:17-18`). It
returns `lance.FtsToken(text, position)`. On the query side, `analyze_plan` appends
`tokenized_query=` to FTS leaves (#8414); `explain_plan` is deliberately unchanged.

**`max_token_length` is the one tri-state option.** Every other analyzer option treats `None` as
"use the analyzer default"; this one does not: "omitting it keeps the default length limit of
40, while `max_token_length=None` disables the limit" (`tokenizer.md:45-46`).

**`InvertedIndexParams` is a closed set.** It exposes base-tokenizer selection, ngram range,
`lower_case`, `ascii_folding`, and stemming - there is **no** hook for a custom token filter and
**no non-English stemmer**. If your corpus needs either (camelCase splitting, a non-English
language), Lance FTS cannot be configured for it; the options are to pre-tokenize into your own
column or to use ngrams.

**The `Fixed32` empty-segment merge failure.** A fold whose batch contributes zero tokens - an
all-NULL tail, but also empty or whitespace-only documents - still writes a delta segment. On
read-back, `posting_tail_codec()` aggregates over partitions and a partitionless segment falls
back to `PostingTailCodec::default()` (`VarintDelta`) rather than reading its file metadata
(`rust/lance-index/src/scalar/inverted/index/inverted_index.rs:72`). The root cause is two
disagreeing defaults: the `Default` impl is `VarintDelta` while `parse_posting_tail_codec`
defaults to `Fixed32` when the key is absent. **Scope: this only bites `Fixed32` indexes** - FTS
`format_version=1` or legacy indexes missing the `posting_tail_codec` key. The V2 default is
`VarintDelta`, which happens to match the `Default` impl, so a default-configured FTS index never
trips it. Where it applies, once delta segments reach the merge threshold with an empty one among
them, `merge_segments` fails deterministically every time. Guard by skipping the fold when the
unindexed tail has no non-null, non-empty values.

**The `fts()` table function does not declare `_score`.** `FtsTableProvider` declares its logical
schema as dataset columns plus optional `_rowid`/`_rowaddr` and never `_score`
(`rust/lance/src/dataset/udtf.rs:39`), while the scan's scoring autoprojection force-appends
`_score` physically. So `COUNT(*)` and `GROUP BY` over `fts()` are **rejected by DataFusion**
(the logical and physical column counts disagree), and `_score` cannot be named in a projection
or ordered by. Plain `SELECT` shapes work only because nothing downstream validates - the
`_score` you see is the undeclared column leaking through.

### 11.4 Geo / RTree

New in v7. The **RTREE** index is a static immutable 2D spatial index on bounding boxes
(`docs/src/format/index/scalar/rtree.md`): a multi-level packed hierarchy, items sorted by
**Hilbert curve** value, leaf pages of `(bbox, rowid)`. Files: `page_data.lance` (all pages)
and `nulls.lance`. Accelerated queries return a candidate set (AtMost), with exact geometry
verification done by the engine: `Intersects`, `Contains`, `Within`, `Touches`, `Crosses`,
`Overlaps`, `Covers`, `CoveredBy`.

The **`lance-geo`** crate provides geospatial UDFs registered into a DataFusion context -
measurement (`Area`, `Distance`, `Length`), relationships (`Contains`, `Intersects`,
`Within`, ...), and validation (`IsValid`) - via `geodatafusion` and `geoarrow`. Gated behind
the `geo` feature.

### 11.5 Index updates and reindexing

There is no monolithic delta-index format - new data is folded in at the **segment** level. A
new index segment covers new fragments; engines query indexed and unindexed subplans and
merge. In-place updates to an indexed column remove the affected fragment IDs from the
covering segment's `fragment_bitmap`, flagging them for reindexing. **Since v11 that rule keys
off any column in `fields`, not just the keyed one**: the engine "must remove the affected
fragment IDs from the `fragment_bitmap` field of any index segment whose `fields` include that
column - whether the index is keyed on it or merely carries it." The same widening applies to
overlay exclusion, where the field range "is every field in the index's `fields`, not only the
ones it is keyed on."

After compaction, three strategies handle changed row addresses: do nothing (segment stops
covering those fragments), rewrite segments with remapped addresses, or use a **fragment reuse
index** (remap in memory at read time). Stable row IDs avoid remapping entirely at the cost of a
lookup.

**Address-domain indexes under compaction on a stable-row-id dataset** (v11 fix). Stable row IDs
keep *row ids* stable across a rewrite, but not row *addresses* - so an index whose payload is
address-domain cannot simply follow its data. The Rewrite commit path now branches on
`index.results_are_row_addrs()`: a row-id-domain index gets `recalculate_fragment_bitmap` and
follows its data to the new fragments, while an address-domain one gets
`drop_rewritten_fragments`, because "its stored addresses point into the fragments the rewrite
dropped. Claiming coverage of the new fragments would make it answer queries with addresses that
no longer resolve, so drop the rewritten fragments from its coverage instead and let the scanner
fall back to a full scan for them"
(`rust/lance-table/src/transaction/manifest_build.rs:818-833`).

ZoneMap is the address-domain case: `results_are_row_addresses() -> true`, `can_remap() ->
false`, and `remap()` returns `"ZoneMapIndex does not support remap"`
(`rust/lance-index/src/scalar/zonemap.rs:732,736,743`). Two consequences worth planning around:
before v11 the bitmap was advanced unconditionally, so a compacted ZoneMap claimed fragments its
zones had no entries for - **that damage is not repaired by upgrading, and such an index must be
recreated**. After v11 the compacted fragments read as *unindexed* instead, so an incremental
`optimize_indices(append)` picks them up on the next maintenance pass rather than no-oping.

The caller-facing API for folding new data in is `optimize_indices(&OptimizeOptions)`
(`rust/lance/src/index/api.rs:297`). `OptimizeOptions` (`rust/lance-index/src/optimize.rs:65`)
has three constructors: `append()` adds a new delta segment over the new fragments;
`merge(N)` folds the delta updates plus the latest N segments into one; `retrain()` rebuilds
the whole index from current data (v3 vector indices only). This is incremental maintenance -
distinct from dropping and recreating an index from scratch.

**`append()` never collapses anything.** It sets `num_indices_to_merge: Some(0)`
(`rust/lance-index/src/optimize.rs:79-80`), and the merge path short-circuits on
`num_to_merge == 0` (`rust/lance/src/index/append.rs:408`) - "append mode (`num_to_merge == 0`)
defers cleanup to a real merge". The *default* `OptimizeOptions` is more useful than that:
`num_indices_to_merge` unset means `unwrap_or(1)`, so a plain `optimize_indices` collapses the
trailing segment on every call (`append.rs:400-403`). `retrain: true` ignores
`num_indices_to_merge` entirely and merges everything into one. Critically, **no automatic
count- or size-based collapse threshold exists anywhere in the codebase** - nothing stops delta
segments accumulating if a pipeline only ever calls `append()`. Bounding segment count is the
caller's responsibility; see `performance.md` Part B for the operational consequences.

**A fragment reuse index is not per-index coverage.** `unindexed_fragments` is computed purely
from the union of each index's own `fragment_bitmap` and does not consult the FRI at all
(`rust/lance/src/index.rs:2977-2985`). With `defer_index_remap = true` the remapper is `None`,
so `rewritten_indices` is empty and `handle_rewrite_indices` is a no-op - the per-index bitmaps
keep the *old* fragment ids while the FRI is appended separately as its own index entry
(`rust/lance-table/src/transaction/index_maintenance.rs:338`). Consequence: deferring remap does **not**
stop `unindexed_fragments(<idx>)` from reporting the new fragments, so a "is my index caught up?"
check built on that call will still see churn after every compaction. The FRI removes the cost of
*rewriting* index entries, not the bookkeeping that says an index does not cover a fragment.

**The FRI has an operational cost model the spec page states and this file does not restate.**
`references/docs/format/index/system/frag_reuse.md` covers index *load* cost (every reader pays
remap work proportional to the accumulated reuse versions) and the growth/cleanup duty: "Once all
scalar and vector indices have been rebuilt past a given reuse version, that version is no longer
needed and can be trimmed. Users should schedule a periodic process to trim stale reuse"
versions. An FRI left untrimmed is a slow, silent tax on open - read that page before running
compaction continuously.

---

## 12. Distributed write and indexing

Lance exposes APIs for distributed work but provides **no scheduler** - the caller drives the
workflow (Ray and Spark integrations exist for the common cases). How a table is handed to a
remote executor is `TableIdentifier` (`protos/table_identifier.proto`) - two modes, see
`ops.md` section 16.

**Substrait.** `lance-datafusion` parses Substrait filter and aggregate expressions
(`parse_substrait` / `parse_substrait_aggregate`, `rust/lance-datafusion/src/substrait.rs:385,473`),
exposed through the Python bindings and the filtered-read exec node. This is the path for
handing Lance a language-agnostic serialized predicate rather than a SQL string - useful when
the planner producing the filter is not itself Rust or Python.

**Two-phase distributed write** (`docs/src/guide/distributed_write.md`):

1. **Parallel writes** - each worker generates `LanceFragment`s in parallel via
   `write_fragments(data, data_uri, schema=)`, returning `FragmentMetadata`.
2. **Commit** - gather all `FragmentMetadata` on one worker, serialize via
   `FragmentMetadata.to_json`/`from_json`, and commit in a single `LanceOperation`
   (`Overwrite`, `Append`, `Merge`, or `Update`) via `lance.LanceDataset.commit(uri, op,
   read_version=)`.

**Distributed indexing** (`docs/src/guide/distributed_indexing.md`). v8 unifies **all** index
builds onto one segment-based lifecycle: workers each build an index **segment** for a
fragment subset via `create_index_builder(...).fragments(...).execute_uncommitted()` (Rust;
`create_index_uncommitted(..., fragment_ids=)` in Python), writing under
`_indices/<segment_uuid>/`. The caller then commits segments as-is via
`commit_existing_index_segments(...)` or groups and merges them via
`merge_existing_index_segments(...)`. Within one commit, segments must have **disjoint
fragment coverage**. Uncommitted staging directories are cleaned by `cleanup_old_versions`.
The standalone `IndexSegmentBuilder` API (and its `build_all()` / `target_segment_bytes`
size-based grouping) was **removed in v8** from Rust, Python, and Java (PR #6997); use the
`execute_uncommitted` path above. Distributed BTree and bitmap builds were folded into this
same framework (PR #7013, #6869) - the old Python Bitmap shard path
(`create_scalar_index(..., fragment_ids=)` + `merge_index_metadata(..., "BITMAP")`) is gone.

**Segment grouping is a separate decision from worker build, and it is yours to make.** The guide
is explicit that the two are not the same knob: "The grouping decision is separate from worker
build. Workers only build segments; Lance applies the segment build policy when it plans physical
segments." Grouping sets commit granularity - how many logical builds land per physical segment -
so it drives both commit count and later merge cost. Full treatment in
`references/docs/guide/distributed_indexing.md` ("Segment Grouping").

**v10 extends the segment lifecycle to the rest of the scalar family.** BLOOMFILTER (PR #7925),
RTREE (PR #7932), NGRAM (PR #7244), and LABEL_LIST (PR #7884) all gained segment-native
build/merge/commit, giving Python this cumulative segment-native set:
`BTREE, BITMAP, INVERTED, FTS, NGRAM, RTREE, ZONEMAP, BLOOMFILTER, LABEL_LIST`
(`python/python/lance/dataset.py:3301`). Consequences:

- **`IndexSegment::new` is BREAKING** - 4 params to 6 (adds `fields` and `dataset_version`) plus
  a second generic; `into_parts` widens from a 4-tuple to a 6-tuple; new accessors
  `fields() -> &[i32]` and `dataset_version() -> u64` (`rust/lance/src/index/api.rs:74,95`).
- Merged segments now inherit the **minimum** source `dataset_version` rather than the current
  manifest version (PR #7925) - so a merged segment's coverage claim stays honest.
- **NGRAM has a hard ordering constraint**: "NGRAM segments built before a deferred compaction
  must be merged before commit so their postings can be rebuilt against current row addresses"
  (`python/python/lance/dataset.py:4305`). Creating an NGram index also now raises a *retryable*
  conflict against a concurrent deferred rewrite over overlapping fragments.
- Segment commit now issues its LIST calls concurrently (`buffered(io_parallelism)`,
  `rust/lance/src/index.rs:319`, PR #7657) - measured ~8x faster against remote storage
  (2837 ms -> 350 ms at 128 segments / 20 ms RTT).

`merge_existing_index_segments(...)` "currently supports vector, inverted, bitmap, BTree, and
zone map segments" (`distributed_indexing.md:109-110`); other scalar families can still be
committed without merging. **Vector model scope**: workers may share one trained IVF/PQ model
*or* use **independent segment models** - "each worker trains the IVF/PQ model for its own
`fragment_ids`. The resulting segments can be committed together as one logical index without
sharing centroids or codebooks" (`distributed_indexing.md:124`, PR #7148). Distributed builds
cover vector indexes, bitmap, segmented btree, segmented inverted (FTS), zone map, and
**LabelList** (added in v9, PR #7223); the
`filtered_read` proto serializes the `FilteredReadExec` scan operator for plan-then-execute
distributed scans.
