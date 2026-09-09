# Lance performance - combined reference

Everything performance-shaped for Lance (`lance-format/lance@v12.0.0-beta.15`) in one place.
**Part A** routes to the official guidance - which lives verbatim in this skill's
`references/docs/` mirror, so it is pointed at rather than re-copied - and then adds the
performance behavior upstream has *not* documented, derived from source and commit history.
**Part B** is field-verified practice from running Lance against remote object storage.

## Contents

- [Part A: Official guidance](#part-a-official-guidance)
  - [Where the official text lives](#where-the-official-text-lives)
  - [OpenTelemetry metrics](#opentelemetry-metrics-not-in-the-performance-guide)
  - [Performance changes not in the guide (v10, source-derived)](#performance-changes-not-in-the-guide-v10-source-derived)
  - [Performance changes not in the guide (v11, source-derived)](#performance-changes-not-in-the-guide-v11-source-derived)
- [Part B: Field-verified remote-storage practices](#part-b-field-verified-remote-storage-practices)
  - [The governing rule: minimize remote calls first](#the-governing-rule-minimize-remote-calls-first)
  - [Write path](#write-path)
  - [Local-filesystem crash safety and recovery](#local-filesystem-crash-safety-and-recovery)
  - [Index maintenance](#index-maintenance)
  - [Read path and query shaping](#read-path-and-query-shaping)
  - [Version-specific behavior (verify on your exact pin)](#version-specific-behavior-verify-on-your-exact-pin)
  - [Benchmarking traps](#benchmarking-traps)

# Part A: Official guidance

## Where the official text lives

Read these directly - they are byte-verbatim copies of the upstream docs at the tracked tag.

| File in `references/docs/` | Heading | Covers |
|----------------------------|---------|--------|
| `guide/performance.md` | (entire file) | Logging; trace events (File Audit, Dataset Events, Object Store Throttle Events, I/O Events, Execution Events); Threading Model; Memory Requirements (Metadata Cache, Index Cache, Scanning Data, Cloud Store Throttling); Fragment Sizing; Conflict Handling + Fragment Reuse Index; Indexes (BTree, Bitmap, Storage Requirements, Performance, Vector Index sizing formulas) |
| `quickstart/full-text-search.md` | "Performance Tips" | FTS index maintenance (incremental `optimize`, coverage monitoring), index configuration best practices, query optimization |
| `guide/json.md` | "Performance Considerations" | `json_get_*` vs `json_extract`, JSON scalar index on hot paths, nesting depth, strict type conversion, array access |
| `format/table/transaction.md` | "CreateIndex Compatibility" | Why index creation is safe concurrently with appends/updates/deletes, and why unindexed fragments are fine |
| `format/index/scalar/fts.md`, `format/index/vector/index.md` | (whole files) | Per-index storage, memory, and training costs |
| `quickstart/vector-search.md` | (whole file) | ANN build and query tuning walkthrough |
| `guide/observability.md` | (whole file) | Logging, trace events, object-store metrics |

Provenance: `docs/src/guide/performance.md` was byte-unchanged from `v9.1.0-beta.8` through
`v11.0.0-beta.2`, then **changed at `v11.0.0-beta.4`** (#8387), which added the "Tuning remote
scans" section and a `row_id_meta` component to the Row Id Sequence cache key, and **again at
`v11.0.0-beta.16`** (#8540), which appended the "AMX Acceleration" section (+29 lines, no other
edit). It then held byte-unchanged through `v12.0.0-beta.6` and **changed again at
`v12.0.0-beta.12`** (#8936), which rewrote the RQ block for the 5-bit default: new per-row sizing
formulas, a new worked example (~10.8 GiB -> ~47.3 GiB), and new `Fast`-mode guidance.

The mirror is refreshed to `v12.0.0-beta.15`, so every number, default, and recommendation in it
is current as written. **Any RQ sizing figure you remember from an earlier read of this guide is
stale** - re-read the block rather than trusting a cached number. The other perf-bearing sections
above remain byte-unchanged across the range.

## OpenTelemetry metrics (not in the performance guide)

Beyond the trace events in `guide/performance.md`, Lance can export metrics through the
`metrics` crate facade (Rust `metrics` feature). The `pylance` wheels are built with the
`metrics` feature enabled: install the OpenTelemetry extra (`pip install "pylance[otel]"`) and
call `instrument_lance_metrics`, which registers Lance's metrics as observable instruments on
your OpenTelemetry `MeterProvider` (`docs/guide/observability.md`, PR #7537).

## Performance changes not in the guide (v10, source-derived)

These are upstream performance behaviors verified against the `v10.0.0-beta.7` source and
commit history. They are **not** in `docs/src/guide/performance.md` - upstream has not
documented them there - so treat this subsection as source-derived rather than official text.

**The cache backend changed, and it can silently refuse entries.** quick_cache is now the
default for both the index cache and the metadata cache, hard-wired in `Session::new` with no
env var or Cargo feature to opt out (PR #7953, #8013). quick_cache splits its weight budget
evenly across shards with no borrowing and **silently refuses entries heavier than a shard's
share**. Shards are `min(cpus / 2, capacity / 4 GiB)`, floor 1, so on a small-CPU or
small-capacity configuration a large index partition may never cache at all - with no error and
no log line, only a persistent miss. If a partition looks uncacheable, compute the per-shard
share before tuning anything else. Measured FTS gain at concurrency 128: 180.7 -> 1340.6 qps,
710 -> 96 ms, 47% -> 93% CPU.

Cache keys also became opaque 16-byte BLAKE3 digests (`CACHE_KEY_FORMAT = "blake3-128-v1"`,
PR #7878) with **no legacy fallback** - every warm or persisted cache cold-misses once after
the upgrade. Budget for one cold window when rolling v10 out; do not read it as a regression.

**FTS query concurrency.** `LANCE_FTS_SEARCH_CHUNK` (default 16, min 1) sets how many
partitions are searched per CPU-pool task; chunking stops query concurrency from flooding the
pool with one small task per partition. Measured 227 -> 428 qps at concurrency 16. `=1` restores
the old per-partition shape. This is one of the few store-adjacent knobs worth knowing exists -
the default is right in the common case.

**FTS row-id resolution moved after the global top-k merge** (PR #7897): at most `limit` lookups
per query instead of per-partition. 4.1 -> 107.7 qps (26x), 3.9 s -> 148 ms on a 100M-doc
benchmark. The tradeoff is memory: each partition's ROW_ID column is now a separate weighed
index-cache entry at ~8 bytes/doc per partition (~800 MB for a 100M-doc index), and it now
counts against `index_cache_size_bytes`. Size the index cache accordingly.

**Segment commit LISTs concurrently** (PR #7657) - measured ~8x faster against remote storage
(2837 ms -> 350 ms at 128 segments, 20 ms RTT). This is a pure win requiring no action, but it
changes the shape of index-commit latency, so re-baseline before comparing against pre-v10
numbers.

**Compaction can now skip row-address map construction** entirely when no remappable data index
exists - FRI-only and system-index-only datasets included (PR #7778). If compaction was
previously dominated by the `_rowid` scan and RoaringTreemap build on such a dataset, that cost
is gone.

## Performance changes not in the guide (v11, source-derived)

Same caveat as above: verified against the `v11.0.0-beta.16` source and commit history, absent
from `docs/src/guide/performance.md`. The section is unchanged at `v12.0.0-beta.15`. The only
edits to `docs/src/guide/performance.md` between `v12.0.0-beta.6` and `v12.0.0-beta.15` are three
hunks from line 483 onward, all in the RQ sizing block (#8936), so the official "Tuning remote
scans" numbers and everything else Part A routes to still stand as written - but the RQ sizing
figures do not, and are restated in `references/indexes.md`.

**Large commits got much cheaper on the manifest side** (PR #7881). Transactions serialized
above 20 MiB are no longer inlined into the manifest and live only in their external
`_transactions/` file. Measured on a large workload: the full-commit manifest shrank from
1576 MiB to ~790 MiB (-50%). There is no configuration to set - it is automatic, and it matters
most on object storage, where manifest size is read on every dataset open.

**Two O(n) fixes on hot paths.** `build_manifest` no longer does `O(n*m)` fragment comparisons
for Update/Delete transactions (PR #8210), which shows up on datasets with many fragments; and
fixed-width decode buffers are now preallocated exactly via a new optional
`decoded_size_bytes` contract on the decompressor traits (PR #8091), cutting **index-cache entry
weight by up to 74%** on IVF_SQ configurations. The latter is a pure accounting improvement -
"This does not change the on-disk format" - but it means the same `index_cache_size_bytes` now
holds substantially more, so re-measure before shrinking the budget.

**FTS conjunctions are cheaper and cold search parallelizes.** Conjunction approximations are
now ordered by iterator cost (PR #8299: 1.50x fewer comparisons, 1.12x speedup, bit-for-bit
identical results and tie order), and doc lengths preload in parallel on the cold deferred
search path (PR #8119).

**The cache backend is no longer a hard-wired choice** (PR #7683), which softens the "no opt-out"
statement in the v10 subsection above. A process-wide registry accepts custom backends, and a
compact URI form (`moka://?capacity=1073741824`) selects one without code. Related: reported
cache sizes shrink after PR #8159, because shared `Arc`/Arrow allocations are no longer charged
once per entry - **recalibrate any alert thresholds keyed on `LanceCache::deep_size_of()`
rather than reading the drop as a regression.**

**Incremental compaction is now expressible** (PR #8116): `compact_files(max_source_fragments=N)`
bounds a run to N source fragments, "allowing compaction to proceed incrementally. Fragments are
processed oldest first." Also settable as the manifest config key
`lance.compaction.max_source_fragments`. This is the clean answer to "compaction takes too long
to ever finish in my maintenance window" - previously the only lever was letting it run to
completion.

**Two more budgets joined it at `beta.8`** (PR #8235, `breaking-change`-labeled):
`max_source_rows: Option<usize>` and `max_source_bytes: Option<u64>`
(`rust/lance/src/dataset/optimize.rs:278,287`), each also settable as
`lance.compaction.max_source_rows` / `lance.compaction.max_source_bytes` (`:363-365`). Prefer
these over `max_source_fragments` when fragments vary widely in size - a fragment count is a
poor proxy for work when one fragment holds 100x the rows of another, and bytes is the closest
proxy to actual IO. And at `beta.14`, `excluded_fragment_ids: Vec<u32>` (`:295`, PR #8532)
keeps named fragments out of planning entirely - the lever for "compact everything except the
partition currently being written".

**AMX-FP16 changes index *results*, not just speed** (PR #8540, `beta.16`). This one is now
documented upstream - the "AMX Acceleration" section of `guide/performance.md` - but it deserves
flagging here because it is the rare performance change that alters what an index contains. On
Linux x86_64 with an AMX-FP16 CPU (Intel Granite Rapids / Xeon 6 and newer), `float16` vector
columns using `dot` route partition assignment through tile instructions. Three gates, all
required, all silently declining the work when unmet: `float16` + `dot`, `dimension >= 32` (one
tile pass covers 32 dimensions), and `num_centroids >= 32` (the GEMM steps its centroid loop by
32 with no partial-tile path). Below those sizes a tile pass costs more than it saves.

Where it does engage, **index build switches from an approximate graph search over the centroids
to comparing every vector against every centroid**. Recall improves and partition assignments
differ from what an older build produced - so a rebuild on new hardware is not a no-op, and an
A/B against an older index is comparing two different indexes. `LANCE_DISABLE_AMX=1` takes the
paths out of service without a rebuild, but because it also reverts assignment to the
approximate path, "an index built with it set is not equivalent to one built without it;
compare recall, not just build time". Availability is also a **build-time** property: the kernel
only exists if the build machine had clang >= 16 or gcc >= 13, with `LANCE_AMX_FP16_CC`
overriding the compiler choice (`rust/lance-linalg/build.rs:27`).

**There is no resident data cache.** A `Session` carries exactly two caches - `index_cache` and
`metadata_cache` (`rust/lance/src/session.rs:49-70`) - holding structural metadata (manifests,
schemas, page tables, row-id maps) and index pages. **Decoded column values are never cached**,
and there is no caching `ObjectStore` wrapper, so repeatedly taking the same rows re-reads their
value buffers from the object store every single call. If a workload does repeated point reads
of a hot row set, the cache to add is your own, above Lance; no amount of `index_cache_size_bytes`
tuning will do it.

What a `Session` *does* buy is sharing. Passing one `Arc<Session>` to several datasets via
`DatasetBuilder::with_session` (`rust/lance/src/dataset/builder.rs:525`) lets them share
index and metadata caches instead of each paying its own cold start - worth doing whenever one
process opens several datasets, which is the normal shape for a namespace of tables.

**Cold first search on remote storage is dominated by paging indexes in**, and the remedy is
`prewarm_index(name)` - or `prewarm_index_segments(name, segment_ids)` to warm only chosen
segments (`rust/lance/src/index/api.rs:194-238`; exposed on the Python `Dataset`). Note what
prewarming does *not* fix: it loads index structures, so a query whose cost is dominated by
**materializing the hit rows' other columns** - scattered point reads, roughly one per
hit-row-fragment - sees little benefit. Diagnose which half you are in before optimizing;
prewarm helps the index half only.

**Two per-operation stats structs that callers routinely discard.** Merge-insert returns
`MergeStats` with `num_inserted_rows` / `num_updated_rows` / `num_deleted_rows` and
`num_attempts` (`rust/lance/src/dataset/write/merge_insert.rs:2739`) - `num_attempts` is the
direct read on how much OCC contention a write is actually hitting, which is otherwise
invisible. And `Scanner::scan_stats_callback` (`rust/lance/src/dataset/scanner.rs:1349`)
delivers `ExecutionSummaryCounts` (see `indexes.md`) per scan, giving `iops`, `requests`, and
`bytes_read` without an `EXPLAIN ANALYZE` round trip - the cheapest way to verify that a
"minimize remote calls" change actually reduced calls.

**Multipart uploads no longer lose parts on retry** (PR #8174). The old path called
`put_part` again on failure, and native cloud stores allocate a fresh part number for that call,
so the retry skipped the failed part and completion failed with `Missing part`. Retries now
happen inside the HTTP connector. If you saw sporadic `Missing part` failures on large writes,
this is the fix; OpenDAL-backed stores were never affected and are unchanged.

## Performance changes not in the guide (v12, source-derived)

Verified against `v12.0.0-beta.15`.

**Latest-version resolution stopped listing the whole `_versions/` prefix** (PR #8679). The
namespace path previously enumerated every historical manifest to find the newest: on a
~340k-version table that is ~344 sequential `ListObjectsV2` pages, "~25s of pure I/O wait",
paid by *every* `open_table` / `describe` / `merge_insert` that resolves the latest version.
Heals purely on upgrade, and it compounds with version bloat - a second reason to keep history
short beyond storage.

**Provider-native bulk copy** (PR #8770). `LANCE_IO_SERVER_SIDE_COPY_ENABLED` routes cloud
copies whose source and destination share an object-store client into the provider's own
server-side copy instead of streaming bytes through the client. The relevant cases are index
movement and copying between prefixes of one bucket. Deep clone separately bounds non-local
file movement to four concurrent files, overridable via `LANCE_DEEP_CLONE_STREAM_CONCURRENCY`.

**`LANCE_DEFAULT_IO_BUFFER_SIZE`** - the input scan for vector shuffling "uses a 2 GiB I/O
readahead buffer by default", configurable through this variable
(`docs/src/guide/performance.md:439`). This is a distinct knob from the per-scan
`io_buffer_size` in the "Tuning remote scans" block, and it is the one that dominates memory
during a large index build.

**Blob v2 materialization got a byte budget** (PR #8919, beta.10), wired through the new
`FilteredReadOptions.materialization_readahead_bytes` (proto field 13). It is "a nonzero upper
bound on bytes reserved by Blob v2 materialization awaiting ordered emission in one scanner
execution"; admission follows output order and "one oversized output batch may exceed the bound
when no other batch is reserved". **If absent, Blob v2 materialization has no independent memory
bound** - which is the state you are in by default, so set it before scanning wide blob columns.
A sibling field 14, `batch_size_bytes`, gives the file reader a byte-based batch boundary
alongside the row-based `batch_size` (PR #8933, also carried through distributed
`FilteredReadOptions`).

**MemWAL memory accounting was wrong in a way that matters for sizing** (PR #7831).
`MemTable::estimated_size` counts buffered batches plus the PK bloom filter - "every in-memory
index is invisible to it." The sharp edge is HNSW: `OnlineHnswBuilder::try_with_capacity`
pre-allocates fixed-size node storage for `max_memtable_rows`, so a vector memtable commits its
**entire** graph on the first insert, not gradually. Measured: 125k rows -> 64.7 MiB, 500k ->
258 MiB, 1M -> 517 MiB, 2M -> 1033 MiB, all charged on row #1. Size `max_memtable_rows` against
that, not against the row count you expect to hold.

---

# Part B: Field-verified remote-storage practices

Everything below comes from production benchmarks of a Lance-based application (2.2M-row
corpus) running against S3-compatible object storage - not from the official docs. Each
practice was measured with a before/after comparison and shipped. Nothing here is
speculative; if an approach was tried and did not clearly win, it is not listed.

## The governing rule: minimize remote calls first

A tool that must work against arbitrary buckets (AWS, Hetzner, R2, MinIO, ...) cannot assume any
particular provider's rate limits or bandwidth. The order-of-magnitude wins in this document all
come from issuing **fewer remote calls** - fewer commits, fewer scans, fewer round trips - not
from tuning the store. Do that first. Explicit per-column compression metadata was tried and
yielded little real-world benefit relative to the effort: reducing what you read beats shrinking
it.

**Tuning the store is a legitimate second move, once call volume is already minimized.** v11
added an official "Tuning remote scans" section (`docs/src/guide/performance.md`, #8387) with a
concrete starting point for bandwidth-constrained access:

| Knob | Suggested start | Why |
|------|-----------------|-----|
| `LANCE_IO_THREADS` | 8 | Cloud stores default to **64**, "intended for high-bandwidth, in-region access and can be too aggressive across regions or over the public internet" |
| `fragment_readahead` | 1 | "Set it to `1` to match the fragment-level I/O pattern, then increase it if the storage connection has spare bandwidth" |
| `batch_readahead` | 2 | Bounds decode-ahead work |
| `io_buffer_size` | 64 MB | Caps in-flight buffered bytes |

These are upstream's numbers for cross-region or public-internet access, not ours - we have not
A/B'd them against the workload behind Part B, and a value tuned for one bucket can misbehave on
another. Treat the table as a documented starting point to measure from, and keep the
benchmark-verified practices below as the primary lever.

Two counter-intuitive caveats from the same section, worth knowing before you tune:

- **`scan_in_order=True` does not serialize fragment reads.** "An ordered dataset scan still
  overlaps I/O from multiple fragments. `scan_in_order=True` controls the order in which batches
  are returned; it does not make fragment reads sequential." This is why a dataset scan issues
  more concurrent requests than scanning one fragment directly.
- **Lowering `batch_size` may not shrink the request.** "Lance reads encoded pages from storage,
  so reducing `batch_size` changes the returned and decoded batch sizes but may not reduce the
  initial range request."

Every practice below is an instance of the governing rule: fewer commits, fewer scans, fewer
round trips.

## Write path

- **Commit count, not row count, is the cost unit.** Each commit is roughly a 1-second
  object-store round trip and rewrites the manifest, which grows with fragment count, and
  every version is retained until cleanup. A full-corpus copy that issued one
  `merge_insert` per batch took 75.7 min / 354 commits; rewritten as a single-commit
  append path the same copy took 18.2 min / 1 commit. A bounded A/B on one delta measured
  3,890 ms (merge) vs 882 ms (append).
- **The anatomy of that cost: a commit is three sequential round trips.** A LIST of `_versions/`
  (the conflict scan - *not* a HEAD of the latest manifest), then an unconditional awaited PUT of
  the `.txn` file, then the conditional PUT of the manifest itself (`PutMode::Create`,
  `rust/lance-table/src/io/commit.rs:1569`). On non-lexically-ordered stores a fourth
  best-effort hint PUT follows. The LIST runs on **every attempt** by design, so a contended
  commit multiplies all three. At 50-100 ms RTT that is 150-300 ms per commit before any data
  moves - which is why commit count dominates.
  Note that inlining a sub-20 MiB transaction into the manifest cuts *read* round trips, not
  write ones: the separate `.txn` file is written either way.
- **Composite `merge_insert` keys are index-accelerated now - re-measure if you avoided them.**
  Lance used to accelerate only a *single-column* merge key, so any composite key fell back to
  scanning the key columns on every merge to locate rows (field-measured at an older pin: 143
  MiB read to write 8 rows, 6.36 s per call). At v12 `indexed_join_keys` probes **each** join
  column that has a scalar index supporting exact equality, ANDs the probes inside one
  `MapIndexExec`, and lets the downstream hash join filter on the full composite key -
  "unindexed columns simply do not prune the candidate set - they are checked by the
  post-filter" (`rust/lance/src/dataset/write/merge_insert.rs:1188`). Fragments outside the
  *intersection* of the participating indexes' bitmaps still scan. The design advice inverts:
  index the key columns rather than collapsing to one synthetic key.
- **`Dataset::versions()` costs O(history) remote round trips, not one.** Manifests are named
  `{u64::MAX - version}.manifest` (`rust/lance-table/src/io/commit.rs:86`) and the call issues a
  `list_manifest_locations` followed by a `read_manifest` **per location**
  (`rust/lance/src/dataset.rs:2608-2610`). On a version-bloated remote store this is a fetch
  storm, with individual reads hitting the 120 s timeout. A second, non-storage reason to keep
  history short - and a reason not to call `versions()` on a hot path at all.
- **Use `Append` for append-shaped data; reserve `merge_insert` for genuine upserts.**
  Merge is commit-latency-bound on object storage; append is bandwidth-bound.
- **`merge_insert` accelerates only when *every* `on` column is indexed.** The v7/v8 rule was
  stricter - exactly one join column - but at v10+ the dispatch requires that all `on` columns
  carry an exact-equality scalar index (`rust/lance/src/dataset/write/merge_insert.rs:1323`),
  plus `use_index == true` and `delete_not_matched_by_source == Keep`. A **partially** indexed
  composite key silently falls through to a full-table join. The cost lands in the read, not the
  write: a measured 8-row update wrote one data file and one deletion vector but **read ~143
  MiB**, scanning the full key columns across 2.1M rows to locate the 8 matches.
- **Manifest *size* grows with fragment count, so `_versions/` can dwarf the data.** Each
  manifest lists every current fragment. Measured on a fragmented store: `_versions/` at 110 MB
  across 178 manifests (~2.3 MB each for the older ones) against a much smaller data footprint;
  on a small-row table, 7.0 MB of data carried 54 MB of `_versions/` and 3.5 MB of
  `_transactions/`. Compaction reduces future manifest size; only cleanup reclaims the old ones.
- **Never commit per item.** A benchmark that committed once per logical unit produced
  3.3 GB of store for 40k tiny rows in ~20 min (manifest churn); the same work batched at
  ~100 units per commit was 17 MB in 1.6 s.
- **When batching is not enough, coalesce the commits themselves.** Lance has a public primitive
  for this that the docs barely surface: write N batches with
  `InsertBuilder::execute_uncommitted()` (`rust/lance/src/dataset/write/insert.rs:133`), which
  writes data files and returns a `Transaction` **without** committing, then publish them all with
  one `CommitBuilder::execute_batch(Vec<Transaction>)`
  (`rust/lance/src/dataset/write/commit.rs:560`) for a single manifest bump. The data-file writes
  can be fanned out concurrently; only the final commit is serialized. **Append-only for now** -
  the API's own warning reads "Only works for append transactions right now. Other kinds of
  transactions will be supported in the future." This is the right shape for a micro-batching
  ingest daemon, where commit count is the binding constraint.
- **Skip no-op merges.** A `merge_insert` where every row matches with
  `WhenMatched::DoNothing` still commits a new (empty) version. Pre-filter to genuinely
  new keys and skip the merge entirely when the set is empty.
- **Compute derived columns before the append.** Embedding-then-merge-back doubles
  commits and rewrites rows; embedding before the append lets the vector ride the row's
  birth commit for free.
- **Append retries are not idempotent.** Unlike `merge_insert` (which no-ops on re-read),
  a retried append after a lost commit ack duplicates rows, and Lance has no unique
  constraint - OCC does not conflict two writers inserting the same new key. Retry only
  on genuine commit-conflict errors, and verify with `COUNT(*)` vs `COUNT(DISTINCT pk)`,
  not just missing-row checks.
- **Match Lance's typed conflict errors before wrapping them.** `CommitConflict`,
  `RetryableCommitConflict`, and `TooMuchWriteContention` are distinct variants
  (`rust/lance-core/src/error.rs:176,193,202`). Erasing them into an opaque application error
  early - `anyhow`, a generic `Storage` variant - makes every exhausted retry indistinguishable
  from a storage outage, and the retry loop can no longer tell "rebase and try again" from
  "give up". Match at the Lance boundary, not after three layers of `?`.
- **`merge_insert` silently changes execution mode with the source schema shape.** When the
  source schema is a strict subset of the target's and unmatched rows are kept, the builder
  routes to `RewriteColumns` (a cheap column update) rather than rewriting whole fragments
  (`rust/lance/src/dataset/write/merge_insert.rs:2232-2260`). Passing a full-schema source for
  what is logically a two-column update therefore costs dramatically more, with no warning.
  Project the source down to the key plus the columns actually being updated.
- **Local-filesystem durability is delegated, not added.** Lance's `file://` store is
  `object_store::LocalFileSystem` (`rust/lance-io/src/object_store/providers/local.rs:26`,
  `object_store 0.13.2`); Lance issues no fsync of its own on the commit path. Whatever
  crash-durability guarantee you get on a local dataset is that crate's, so do not assume a
  returned commit means the manifest bytes survived a power loss. See the next subsection for
  what that costs you in practice.

## Local-filesystem crash safety and recovery

This is the sharpest edge in Part B, because the failure is **permanent and silent** and has no
analogue on object storage. Mechanism, verified at `v11.0.0-beta.2`:

- **Latest-version resolution is "highest number wins", with no fallback.** On a local store
  Lance scans `_versions/` and keeps the maximum
  (`rust/lance-table/src/io/commit.rs:693-694`, `current_manifest_local`, selected first for
  local at `:283-286`). A manifest that exists but is truncated or zero-length is a hard error -
  "Invalid format: file size is smaller than 16 bytes"
  (`rust/lance-table/src/io/manifest.rs:60-63`) or "Invalid format: magic number does not match"
  (`:68`) - propagated straight up by `Dataset::latest_manifest`
  (`rust/lance/src/dataset.rs:1180`). The only error the open path swallows is `NotFound`
  (`rust/lance/src/io/commit.rs:313`), and corruption is not `NotFound`. **There is no
  "fall back to version N-1" anywhere.** So an unclean stop that creates the manifest without
  flushing its bytes leaves a dataset that will not open, even though version N-1 is fully
  intact on disk.
- **Editing `latest_version_hint.json` back does nothing.** On a local store the hint file is
  never read at all - `current_manifest_path` branches on `object_store.is_local()` before the
  hint path is considered (`commit.rs:283-291`). It *is* written on local now (`:79`, gated by
  `version_hint_globally_enabled() && !list_is_lexically_ordered`, `:328`), but writes are
  best-effort and it "never affects correctness (readers verify the hinted version and probe
  upward from there)" (`:340-341`). Rewinding it is inert.
- **The repair is to move the poisoned manifest aside**, not to touch the hint: quarantine
  (never delete) the sub-16-byte `*.manifest` files under `_versions/`, and the next-highest
  intact version becomes latest again. Rename rather than remove, so a misdiagnosis is
  reversible.
- **Then validate with a scan, not with `count_rows`.** `count_rows(None)` sums
  `physical_rows - deletions` straight from fragment metadata and opens no data file when the
  manifest carries the counts (`rust/lance/src/dataset/fragment.rs:1375-1379`, summed at
  `rust/lance/src/dataset.rs:1664-1671`). A zeroed or truncated data file that a surviving
  manifest still references is completely invisible to it - the row count reports fine while
  the data is unreadable. Only a drained scan proves integrity.
- **Object storage is structurally immune to this.** S3-style PUTs are atomic, so a killed
  writer leaves *no object* rather than an empty one, and there is no half-written manifest to
  poison the version sequence. This is a local-store-only failure class.
- If you run Lance on a local filesystem on hardware that can lose power, the mitigation is an
  fsync-on-write `WrappingObjectStore` (file plus parent directory after every put,
  multipart-complete, copy, and rename) installed innermost in the store-wrapper chain and gated
  to local URLs only, plus a `_versions/` walk on open that rename-quarantines undersized
  manifests. A later A/B put a number on the fsync layer's cost, superseding an earlier
  "not detectable" reading: **+5.54 s real on a 130.86 s sync, +4.2%** - and that is with
  macOS's notoriously expensive `F_FULLFSYNC`. It stays small for a structural reason worth
  internalizing: Lance writes **few, large** files, so fsyncs amortize per-file, not per-row.
  Expect the same shape on any workload with that write profile, and expect it to degrade if
  you push Lance into many-small-files territory.
- **Verify recovery with a full-projection scan, not an id-only probe.** A scan that projects
  only the id column reads only that column's data files, so a crash-zeroed data file behind a
  *different* column - the classic case being a column added later, such as an embedding
  vector - stays invisible and the probe passes. Drain a scan that projects every column.
- The local-store rules above cover `file+uring://` as well as `file://`; both report
  `is_local() == true`. A scheme comparison written as `scheme == "file"` silently skips uring
  stores.

## Index maintenance

- **Batch index folds behind a row-count threshold; never fold on every write tick.**
  Folding FTS + vector indexes on each 5-minute sync cost 15-445 s of the sync; deferring
  folds until the unindexed tail reaches ~5,000 rows cut a 80-524 s sync to ~44 s. The
  deferred tail costs only ~50-350 ms extra per query (see next point).
- **A remote fold is close to fixed-cost per pass, not proportional to the delta.** Measured on
  S3-compatible storage, folding a delta of **~200 rows took ~346 s**; the same fold against a
  local store took **2-4 s for a delta of 424k rows**. The dominant cost is neither transfer nor
  verification but the index fold itself on the remote - roughly the same ~100x object-store
  penalty that shows up everywhere else in this document, and essentially a floor you pay to push
  even one new row. This is what makes a row-count threshold non-optional remotely: the amortized
  cost per row falls almost linearly with how much you batch behind it, so the threshold should be
  tuned against fold *frequency*, not against how stale the tail is allowed to get.
- **An unindexed tail is a latency concern, not a correctness one - if `fast_search` is
  off.** Lance answers FTS and vector queries as a union of the index scan and a flat
  scan of unindexed fragments. `fast_search` skips that flat arm, silently dropping the
  newest rows from results. Only enable it when no unindexed tail exists, and keep a
  tail-recall regression test. On v11, an unindexed tail additionally disqualifies the
  posting-backed compound FTS scorer (section 11.3), so it costs plan quality too.
- **Know exactly what the flat arm does, because it bounds your commit cadence.** Read the
  branch at `rust/lance/src/dataset/scanner.rs:5662-5680` (`v12.0.0-beta.15`). It scans **every**
  unindexed fragment, and two properties make that cost scale badly. First, the filter is applied
  as a post-scan `LanceFilterExec` over the scanned rows rather than through scalar indexes - the
  code says so outright: "we could try and use the scalar indices here to reduce the scope of this
  scan but the most common case is that fragments newer than the vector index are also newer than
  the scalar indices." Second, **limit/offset is not pushed down** - "Can't pushdown limit/offset
  in an ANN search" - so a `k` of 10 does not shrink the scan. A selective filter therefore does
  not save you here the way it does on the indexed arm.

  The practical consequence: every commit adds at least one fragment, and every fragment stays on
  this arm until the next `optimize_indices`. Query cost grows roughly linearly with **commits
  since the last fold**, not with rows. A one-second ingest cadence against hourly folds means
  thousands of fragments flat-scanned per query. For a frequent-append workload this - not commit
  throughput - is usually the first thing to fall over, and the fix is fold frequency, not a
  bigger machine.
- **Measuring the backlog: there is no `count_unindexed_rows()`.** The supported API is
  `Dataset::unindexed_fragments(idx_name)` on the `DatasetIndexInternalExt` trait
  (`rust/lance/src/index.rs:2548`) - public, but carrying "Internal use only. No API stability
  guarantees", so pin your Lance version if you depend on it. `index_statistics()` does surface
  `num_unindexed_rows`, but only inside an untyped JSON string and at the cost of a full
  `count_rows`. Prefer counting rows in the returned fragments.
- **Choosing ngrams over `simple`+stem costs relevance, not just RAM.** On a 111-query
  paraphrase set over the same corpus (Success@3, full corpus): word `simple`+stem scored
  **66/111** against production `ngram(3,5)` at **31/111** - roughly 2x better - while using
  ~5x less RAM (379 MB vs 1,868 MB at 2M rows) and ~4x less disk. ngram posting size scales with
  document *bytes*, not document count: a measured ngram(3,5) index over 161,718 text values
  produced 737 MB of postings, about **4.5 KB of index per document**, because every text emits
  one posting per `(length - n + 1)` substrings at each n in the range. Reach for ngrams only
  when you actually need substring/typo matching, and measure recall before assuming it helps.
- **Gate `cleanup_old_versions` to every Nth commit.** Its cost is O(accumulated
  versions), not O(delta): it consumed 8.8 s (58%) of a 200-row incremental sync and gets
  slower as versions pile up. Gating it on `dataset.version_id() % N` cut cleanup walks
  by ~87% with no behavior change.
- **Cleanup does not have to run on the write path at all.** The official guide documents an
  off-write-path alternative under "Other cleanup strategies"
  (`references/docs/guide/read_and_write.md`): drive cleanup from an external scheduler rather
  than from the writer. The tradeoff is stated plainly - it "keeps cleanup off the write path
  entirely, avoiding any impact to write latency, but requires setting up and maintaining
  additional infrastructure." For a latency-sensitive ingest path where the Nth-commit gate still
  shows up in tail latency, this is the next move.
- **"Pending cleanup" bytes are the retention window, not bloat.** Versions younger than the
  retention window are pinned by design, so an optimize pass over a young store legitimately
  reclaims zero. Know your actual window before calling it a leak: Python's
  `cleanup_old_versions` defaults `older_than` to **14 days** when neither `older_than` nor
  `retain_versions` is given (`python/python/lance/dataset.py:3113`), while automatic cleanup
  uses whatever `lance.auto_cleanup.older_than` the dataset config carries - the docs example
  sets `"3600s"` (`docs/src/guide/read_and_write.md:585`), which is where a "one hour" default
  is easily misremembered from. Never benchmark space reclamation on a store younger than the
  window actually in force.
- **A second, independent floor: unverified files are held for 7 days.**
  `UNVERIFIED_THRESHOLD_DAYS = 7` (`rust/lance/src/dataset/cleanup.rs:319`) is hardcoded. With
  the default `delete_unverified=false`, any file not reachable from a manifest but newer than
  7 days is treated as possibly-in-progress and refused for deletion **regardless of
  `older_than`**. Shortening the retention window does not touch this floor, so a store can sit
  well above its expected size for a week after heavy rewriting and still be behaving
  correctly.
- **A `replace=true` index rebuild roughly doubles store size until a later cleanup.**
  `create_index(replace=True)` writes the new index set and leaves the entire superseded set on
  disk as pending-cleanup - a measured rebuild roughly doubled both store size and object count
  until the next cleanup pass. Provision headroom for a full extra index set before rebuilding,
  and do not schedule a rebuild and a tight retention window against each other.
- **Measure maintenance on the real remote store.** A full FTS consolidation rebuild
  measured ~1 min locally but 4.5-5 min (rewriting ~190 MB) against the remote store -
  round trips dominate. If a periodic rebuild can exceed your scheduler interval, rely on
  Lance OCC (conflicting commit -> retry) and keep rebuild cadence low rather than trying
  to serialize externally.
- **`optimize_indices(append())` never collapses anything - and nothing else will either.**
  `append()` sets `num_indices_to_merge: Some(0)` (`rust/lance-index/src/optimize.rs:79-80`) and
  the merge path short-circuits on zero (`rust/lance/src/index/append.rs:408`). **No automatic
  count- or size-based collapse threshold exists in the codebase**, so a pipeline that only ever
  calls `append()` accumulates delta segments without bound until something else breaks - and
  what breaks first depends on the index family, which makes the symptoms look unrelated. Note
  the *default* `OptimizeOptions` is better behaved than `append()`: with `num_indices_to_merge`
  unset it collapses the trailing segment on every call (`append.rs:400-403`), and
  `retrain: true` merges everything into one. Pick an explicit ladder - collapse at a modest
  segment count, full rebuild at a higher one - and treat those numbers as correctness floors
  rather than tuning preferences.
- **`LANCE_MEM_POOL_SIZE` is the hidden ceiling on large from-scratch scalar index builds, and
  the default is smaller than it looks.** BTree/JSON training scans run with `use_spilling: true`
  (`rust/lance/src/index/scalar.rs:166`, `rust/lance-index/src/scalar/btree.rs:1942`), which
  wraps a DataFusion `FairSpillPool` sized from that variable
  (`rust/lance-datafusion/src/exec.rs:364,378`). The default is
  `DEFAULT_LANCE_MEM_POOL_SIZE_PER_PARTITION = 150 MiB` (`exec.rs:309`) multiplied by
  `target_partition.unwrap_or(1)` (`exec.rs:314,324`) - **so with `target_partition` unset the
  pool is 150 MiB total, not 150 MiB per core.** A large sort that fragments into more spill
  files than its fair-share slice can merge fails with a DataFusion `Resources exhausted ...
  ExternalSorterMerge` error rather than spilling further. Raise `LANCE_MEM_POOL_SIZE` (or set
  `LANCE_BYPASS_SPILLING`, `exec.rs:349`, to disable the pool entirely) before concluding the
  index cannot be built.
- **Auto-cleanup is opt-in and interval-gated - but `skip_auto_cleanup` is Rust-only.** The
  per-commit hook returns immediately unless the dataset config carries
  `lance.auto_cleanup.interval` and the current version is a multiple of it
  (`rust/lance/src/dataset/cleanup.rs:1450-1455`), and `auto_cleanup` defaults to `None`
  (`rust/lance/src/dataset/write.rs:434`); the gate itself is an in-memory config read costing no
  I/O. When it *does* fire it is expensive exactly as documented - it "lists and reads every
  manifest in the dataset even when nothing is old enough to delete" (`write.rs:356-357`,
  listing at `cleanup.rs:680`) - so choose the interval against version-accumulation rate, not
  write rate. Rust callers can also set `skip_auto_cleanup: true` (`write.rs:367`, builder at
  `write/commit.rs:212`); **pylance does not expose it** (only `auto_cleanup_options` /
  `enable_auto_cleanup` / `disable_auto_cleanup`), so from Python the lever is the interval or
  disabling the feature.
- **Cleanup runs outside the OCC protocol, which is *why* the 7-day floor exists.** Cleanup
  writes no manifest - it is a list-and-delete pass (`.remove_stream(paths_to_delete)`,
  `cleanup.rs:752`) - and the module doc states the bind directly: "It is also difficult to
  distinguish between a data/tx/idx file which was leftover from an abandoned transaction and a
  data file which is part of an ongoing operation (both will look like unreferenced data files)"
  (`cleanup.rs:20-22`). Hence `maybe_in_progress` holds anything newer than the threshold
  (`:666-667`). The operational rule that follows: **never run cleanup with
  `delete_unverified=true` while writers are live** - that flag removes the only thing standing
  between a concurrent in-flight write and deletion of its data files.
- **Object Lock / WORM retention must be off on the bucket.** Cleanup issues real per-object
  deletes (`store.delete(&location)`, `rust/lance-io/src/object_store.rs:964`) covering
  unreferenced data files, old manifests, and transaction files; index builds also delete temp
  objects (`rust/lance/src/index/vector/ivf.rs:2489`, `ivf/io.rs:501,520`). WORM retention blocks
  those deletes outright, so maintenance fails and the store grows without bound. (Compaction
  itself issues no deletes - it only writes new fragments and lets cleanup reclaim the old ones -
  so the failure surfaces at cleanup time, not at compaction time.)
- **Turning off stable row IDs is not the whole story on remap cost.** The gate is now
  `!uses_stable_row_ids() && !options.defer_index_remap && has_address_style`
  (`rust/lance/src/dataset/optimize.rs:2060-2061`), and row-address capture is skipped entirely
  when nothing will consume it (`:1653-1657`). So a non-stable-row-id dataset with **no**
  address-style index pays no remap cost at all - the "every compaction rewrites every index
  entry" rule only bites when such an index actually exists.

  The correctness half of that gate is covered in `indexes.md` section 11.5: on a
  **stable-row-id** dataset no remap happens either, so an address-domain index (ZoneMap) has
  its rewritten fragments *dropped* from coverage rather than remapped. Before v11 the bitmap
  was instead advanced onto the new fragment ids, leaving zones pointing at dead ones. If your
  datasets predate v11 and carry a ZoneMap, probe payload-vs-live fragment ids with
  `calculate_included_frags` once and recreate any index that mismatches - upgrading does not
  repair existing damage.
- **Replace the compaction planner rather than post-filtering its output.** `CompactionPlanner`
  is a public trait and `compact_files_with_planner` accepts any implementation
  (`rust/lance/src/dataset/optimize.rs:687,928`). The load-bearing detail is that an empty plan
  short-circuits before any commit - `if compaction_plan.tasks().is_empty() { return
  Ok(CompactionMetrics::default()); }` - so a veto-style planner produces **zero churn and zero
  new versions**, which post-filtering cannot promise. Byte-aware policy needs no extra I/O
  either: `DataFile.file_size_bytes` is already carried in the manifest as `CachedFileSize`.
  Measured on a heavy-row table, deriving `target_rows_per_fragment` from bytes instead of the
  1M-row default took daily rewrites from ~190 GB to under ~100 MB.
- **Compaction bins split at index-coverage boundaries, and that will not be relaxed.** The
  planner "cannot mix 'indexed' and 'non-indexed' fragments"
  (`rust/lance/src/dataset/optimize.rs:849`); the split is load-bearing for correctness, because
  a rewrite group straddling an index bitmap creates Rewrite-vs-CreateIndex conflicts (PR
  #6610), and a commit that mixes them fails later at `load_indices` with "split of indexed and
  non-indexed". The consequence to design around: freshly compacted fragments land outside every
  per-index `fragment_bitmap`, so `unindexed_fragments()` keeps reporting them and a naive
  "compact until clean" loop never terminates. Compaction is an **operator-cadence** verb -
  running it at write cadence is the impedance mismatch.
- **Compaction non-convergence is confined to the reencode path.** Candidacy is purely
  `physical_rows < target_rows_per_fragment` (`rust/lance/src/dataset/optimize.rs:728`) - there
  is no byte term anywhere, including bin splitting, and the in-tree `CompactionOptions` doc
  admits it ("This does not affect which frgamnets need compaction", typo upstream). The
  reencode writer flushes on whichever of the row target or byte cap fires first, so a
  byte-capped task can emit fragments that are *still* under the row target and stay candidates
  forever - one measured incident churned 31 rounds x 980 MiB of net-zero rewrites. Binary copy
  cannot loop: it ignores `max_bytes_per_file` entirely and flushes on the row target at whole-
  file granularity. Two caveats before you reach for it: `compaction_mode` defaults to
  `Reencode`, so this divergence only appears after explicitly opting into
  `TryBinaryCopy`/`ForceBinaryCopy`; and a **single blob column disqualifies binary copy for the
  whole dataset**. `max_bytes_per_file` is also effectively inert when unset - the writer
  default is 90 GB.
- **`file_size_bytes` backfill is cheap on Lance-written stores.** `migrate_manifest` runs at
  every commit and issues one `ObjectStore::size` (HEAD) per data file whose size is unknown
  (`rust/lance/src/io/commit.rs:839`), in parallel. Lance's own writers set the field at write
  time, so on a Lance-written store the cost is zero; it only bites data files adopted from
  elsewhere. The larger hidden cost in the same area is that **one** fragment missing
  `physical_rows` forces `migrate_fragments` across all fragments.

## Read path and query shaping

- **Freshness is poll-only, and polling is cheaper than it looks.** There is **no `subscribe`,
  `watch`, or version-notification API anywhere in the workspace** at `v12.0.0-beta.15` - a reader
  that must see new commits polls, full stop. The good news is the cost model:
  `Dataset::checkout_latest()` (`rust/lance/src/dataset.rs:556`) on an **unchanged** version costs
  a single list/head and does **not** re-read the manifest body, so a ~100 ms poll interval is
  affordable even remotely; you only pay manifest decode when the version actually moved. Budget
  for the changed case, not the steady state. The only alternatives are in-process
  `lance::dataset_events` tracing (same process only) and MemWAL's `WalTailer` (cross-process, but
  only for MemWAL tables - and see the parallel-stack caveat in section 10).

- **A latent timezone smell in scalar-index coercion - worth knowing, not currently a bug.**
  `safe_coerce_scalar`'s same-unit arm is
  `DataType::Timestamp(TimeUnit::Microsecond, _) => Some(value.clone())`
  (`rust/lance-datafusion/src/expr.rs:311`, unchanged at `v12.0.0-beta.15`): when the literal's
  time unit already matches the column's, it returns the literal **unchanged, discarding the
  target timezone**. The other-unit branches clone the timezone correctly. At the pinned
  `datafusion-common` 54.x this is harmless - `ScalarValue::partial_cmp` for two same-unit
  timestamps ignores the timezone entirely, so ZoneMap range pruning compares values correctly.
  It is worth tracking because there are **no timezone tests anywhere under
  `rust/lance-index/src/scalar/`**, and the arm has been untouched since 2024: a DataFusion that
  makes `partial_cmp` timezone-aware turns this into silently-pruned zones.

  **Field report, older pin, not re-verified at v12:** this has been observed firing as a real
  bug rather than a latent one - `ScalarValue::partial_cmp` across mismatched timezones returns
  `None`, so `>=`/`<=` are all false, every zone is pruned, and a tz-aware
  `Timestamp(us, "UTC")` column returns 0 rows in *both* directions. It is unescapable from the
  caller: a naive literal, an explicit `+00:00`, `cast(...)`, and
  `arrow_cast(..., 'Timestamp(us,"UTC")')` all return 0, because DataFusion normalizes the
  literal to the column's unit before pushdown and lands in the same-unit arm. The three ways
  out, in increasing order of pain: **drop the index** (the only one that does not rewrite
  data), migrate the column to `Timestamp(us, None)`, or fork the workspace via
  `[patch.crates-io]`. If you see a tz-aware timestamp predicate under-returning on a
  ZoneMap-indexed column, check this first - and pin your DataFusion.
- **A bare `Ne` predicate hits a slow path; And it with `IsNotNull`.** *(Observed on a Lance
  7-10 pin, not re-verified at v12 - treat as a thing to try, not a documented behavior.)* A
  `!=` filter carrying no `IsNotNull` conjunct ran 59.5 s; And-ing `IsNotNull` on a **narrow**
  column brought the same query to 7.35 s (~8x), and a related query went 130 s -> 12-17 s.
  This is distinct from the known "no per-column null metadata" cost below. The companion lever
  from the same investigation: when two columns are written together, filter on the narrow one
  rather than the fat one - swapping `embedding_model IS NULL` for `vector IS NULL` took a scan
  from 1.2 GB read to 149 KB.
- **Answer metadata questions from the manifest, never from a column scan.**
  `count_rows("col IS NOT NULL")` reads the entire column (Lance keeps no per-column null
  metadata to short-circuit it) - on a wide text column that was ~133 MB of reads per
  call. "Does this dataset have embeddings?" is answered by index presence in the
  manifest, not by `IsNotNull("vector")` (measured 6.8-44 s per call on S3). Cache counts
  that only change on ingest.
- **Scalar and JSON indexes accelerate `WHERE` pushdown only.** A `GROUP BY
  json_get_string(col, 'name')` or a join key extracted from JSON evaluates the
  expression per row with no predicate to push down - the whole fat column ships over the
  network. Materialize hot JSON fields as narrow native columns (indexed if selective):
  this took the flagship analytics queries from >30 s timeouts on S3 to 8.5-24 s, and
  35x/14x faster locally.
- **A fat column co-located with narrow rows defeats late materialization.** Even a
  selective predicate over the narrow columns pays the fat column's page I/O when the
  rows interleave on the same pages. Keep wide payload columns out of tables you scan
  analytically, or split the hot fields out.
- **Substring search over an unindexed column is a full scan** - a BTree cannot serve
  `LIKE '%needle%'`. The official substring answers are the NGRAM index (for
  `contains()`) and the FM-Index (v8+, exact-byte only, segmented, no BM25 ranking).
  Until one is built, narrow the scan with indexed/materialized predicates first. Two
  constraints decide which index is even possible: NGRAM requires a `Utf8`/`LargeUtf8` column
  and rejects `LargeBinary` outright, and NGRAM lowercases and ASCII-folds both sides while
  FM-Index matches raw bytes - so the two return different result sets for the same needle
  (`indexes.md` section 11.2). Do not benchmark one against the other without checking
  that they are answering the same question.
- **Tune a slow vector query before rebuilding the index.** `nprobes` (IVF partitions searched)
  and `refine_factor` (candidates re-ranked against full-precision vectors) are query-time
  parameters that trade latency for recall with no reindex
  (`docs/src/quickstart/vector-search.md:208-210`). Sweep those first; a rebuild with different
  build-time parameters is the expensive last resort. Related trap: `approx_mode="fast"` does
  not reliably mean ACORN ran - it is skipped when the prefilter mask passes all rows or leaves
  under 10%, so a null result from that flag may mean the path was never entered.
- **Scalar-index pushdown does not wait for scale.** The planner emits a `ScalarIndexQuery`
  whenever the index exists, with no row-count or selectivity heuristic anywhere in the
  expression module - the plan for four rows and for two thousand is identical. Useful in both
  directions: a small table does benefit from a scalar index, and an unwanted index scan will
  not "optimize itself away" on small data.
- **`Dataset::versions()` is O(history) remote reads, not a metadata lookup.** It lists
  manifests and then **reads every one** to recover its timestamp
  (`rust/lance/src/dataset.rs:2618-2635`, which carries an upstream
  `// TODO: this API should support pagination`). On a dataset with hundreds of versions over
  remote storage this is a fetch storm - it shows up in access logs as reads of historical
  manifest versions in descending order. Use `version()` / the current manifest for "what
  version am I on"; reserve `versions()` for genuine history browsing, and never put it on a
  hot path or a health check.
- **A bitmap index turns prefix `LIKE` into an error, not a scan fallback.** With a BITMAP
  index on the column, `col LIKE 'prefix%'` fails with "LIKE prefix queries are not supported
  for bitmap indexes" (`rust/lance-index/src/scalar/bitmap.rs:823`) rather than degrading to a
  flat scan. Index choice can therefore *remove* a query shape that worked before the index
  existed - if you need both set membership and prefix matching on one column, a bitmap index
  alone is the wrong choice.
- **A blob column in SQL is a `{position, size}` struct descriptor.** Any cast or text
  operation on it surfaces as an opaque planner error (`Unsupported CAST from Struct(...) to
  Utf8View`) with nothing pointing at blobs as the cause. Read blob payloads through the blob
  APIs (`read_blobs` / `read_blob_ranges` / `take_blobs`) or
  `scanner(blob_handling="all_binary")`, not through SQL projection.

## Version-specific behavior (verify on your exact pin)

Same API, different behavior across majors - each of these was discovered in production,
not in release notes:

- **Lance 7.x: `optimize_indices` with `append()` silently full-rebuilds scalar
  (BTree/bitmap) indexes** - the O(delta) delta-segment path only works on v8+. On 7.x
  every fold rescans the whole indexed column.
- **Lance 7.0.0: incremental inverted-index (FTS) merge is broken twice over** - a
  token-id out-of-bounds panic once 4 delta segments accumulate, and an
  empty-delta-segment codec mismatch (`VarintDelta` vs `Fixed32` defaults) that poisons
  every subsequent merge. Consolidate by full rebuild (`create_index` with
  `replace=true`) instead of merging, and guard folds so an all-null tail never creates
  an empty segment.
- **Lance 7.x: `defer_index_remap=true` (Fragment Reuse Index) panics when combined with
  stable row IDs.** They are alternative solutions to the same problem - pick one. (v9
  rejects the combination cleanly.)
- **Stable-row-id datasets: `COUNT(*)` cannot use count pushdown before v9** (fixed
  upstream in PR #7360) - every count is a full scan plus a WARN. Don't count on the hot
  path; silence the warning with a scoped log directive, not a blanket mute.
- **v8 -> v9 renamed the FM-Index proto message** (PR #7397), making existing FM indexes
  unreadable after a bump. Treat any Lance major bump as an index-lifecycle event:
  re-validate fold, merge, compaction, and count behavior end-to-end on the exact pinned
  version rather than trusting API presence.
- **A Lance major bump does not imply a redesign - or a small blast radius.** The major is
  bumped automatically by `ci/publish_beta.sh` on any `breaking-change`-labeled PR, so v9 -> v10
  is the *same dev line* renamed. Read the labeled PRs, not the version delta: v10's four are
  the blob null-selection change, the cache-key change, the compaction remapper signature, and
  the MemWAL rename.
- **v10 cold-misses every cache once.** Cache keys became opaque BLAKE3 digests with no legacy
  fallback (PR #7878), so the first run after upgrading re-populates warm and persisted caches
  from scratch. Expect one slow window; do not chase it as a regression.
- **v10 changed blob API return types to `Optional`** (PR #7903). Code that zipped blob results
  positionally against its inputs was already wrong whenever a null blob appeared (results were
  omitted, not `None`); after v10 it will not compile in Rust, and in Python it silently starts
  yielding `None` entries. Audit blob call sites as part of the bump.
- **v10 may reject a caller's "table not found" assumption.** The directory namespace no longer
  reports transient storage failures as `TableNotFound` (PR #7931) - a create-or-open path that
  treated that error as "absent" could previously overwrite a live table on a 503, and now sees
  `Throttling` / `ServiceUnavailable` / `Internal` instead.
- **crates.io carries finals only.** The newest published crate is `lance 10.0.0` (2026-08-07);
  every beta and rc exists as a git tag with no crate. Pinning a beta means a git dependency,
  which also means no crates.io yank signal if one turns out bad.
- **Do not assume a given major shipped a final.** The auto-bump has now fired on two
  consecutive dev lines, and *neither* `v9.1.0` nor `v10.1.0` was ever released. `v10.0.0` **did**
  ship a final (2026-08-08, on `release/v10.0`) - note that finals are cut on `release/vX.Y`
  branches, so "not an ancestor of `main`" is normal and not a sign the release is unofficial.
  "Upgrade to the latest major" is still not a valid plan without checking which majors actually
  have finals - as of `v12.0.0-beta.15` that is `v11.0.0` and below.
- **v11 changes fragment-id semantics** (PR #8206). Overwrite no longer restarts ids at 0, and
  any commit producing duplicate ids is now rejected. Two audit items on a bump: code that reads
  a fragment by a hardcoded id after an overwrite, and any dataset written by Lance 0.16 or
  earlier that may already contain duplicate ids - those still read but can no longer be
  committed to, so a long-lived store may become read-only at exactly the wrong moment.
- **v11 changes HNSW graphs** (PR #8188): `m < 4` is now rejected, the persisted level layout was
  corrected, and greedy descent stops before level 0. Recall and latency both move. Re-baseline
  vector benchmarks across this bump rather than comparing to pre-v11 numbers.
- **v11 shrinks reported cache sizes** (PR #8159) without shrinking the cache - shared
  `Arc`/Arrow allocations are no longer double-counted per entry. An alert keyed on
  `LanceCache::deep_size_of()` will look like a sudden drop in cache utilization.
- **`lance.json` columns and `compact_files` still take a logical/physical roundtrip.**
  `prepare_reader` in `optimize.rs` uses `scanner.try_into_stream()`
  (`rust/lance/src/dataset/optimize.rs:1376`), whose `DatasetRecordBatchStream` applies
  `to_logical_stream` - converting `lance.json` LargeBinary to `arrow.json` Utf8
  (`rust/lance/src/dataset/scanner.rs:6386`) - and the write side converts back with
  `to_physical_stream` (`rust/lance/src/dataset/write.rs:1292`). The identical asymmetry was
  fixed for `update.rs` (PR #6741, which now uses the raw physical stream at
  `write/update.rs:291`) but **never applied to `optimize.rs`**, and no test combines a JSON
  field with compaction. It is benign only because the JSONB roundtrip is idempotent when the
  stored bytes are genuinely JSONB. The durable rule: **never write plain UTF-8 JSON text into a
  column tagged `lance.json`** - encode JSONB, and let Lance own the representation.

## Benchmarking traps

Each of these produced a wrong conclusion that shipped or nearly shipped:

- **Copy-then-optimize measures `IndexCreate`, never the incremental fold.** To measure
  fold cost: build indexes first, append a small tail, then optimize. An
  always-compact profile also masks the fold signal with compaction noise.
- **A/B on the same warm cache state.** Index/rowmap caches are keyed by store URL; a
  freshly cloned store URL always cold-starts (tens of seconds) and looks exactly like a
  regression. Compare binaries against the same URL, and separate cold from warm runs.
- **Measure memory after the first vector query, at production scale.** The IVF index
  loads lazily on first vector query and stays resident: an FTS-only idle of ~564 MiB
  became ~1,365 MiB after one vector query on a 2.2M-row corpus. Cold or FTS-only numbers
  understate steady-state RSS by ~2x.
- **Benchmark write paths end-to-end including `optimize_indices`.** Freshly written
  fragments are unindexed; different write strategies leave different fragment counts,
  so the maintenance cost differs even when the write cost looks identical.
- **Attribute wins to the metric you actually gated.** Per-sync wall time is dominated by
  compaction and index-append variance (single index-appends spiked 40-70 s); a change
  that reduces cleanup walks by 87% may not move wall time at all. Use paired
  before/after rounds to separate store-latency noise from the change under test.
- **An in-process S3 mock cannot validate OCC.** Mock servers backed by a local filesystem
  typically implement conditional PUT as check-then-write, with a real race window between the
  existence check and the write, so two concurrent `PutMode::Create` calls can both succeed and
  the last one wins. Real S3, R2, GCS, and Azure do this atomically. A concurrency test that
  passes against such a mock proves nothing about commit safety - run OCC tests against a real
  conditional-put store, or against `s3+ddb://`.
- **`memory://` sharing is session-scoped, and the scoping is not what the URI suggests.**
  `MemoryStoreProvider::new_store` mints "a fresh in-memory object store for each call"
  (`rust/lance-io/src/object_store/providers/memory.rs:14,25`), but the registry caches by
  `(prefix, params)` with weak refs and the memory provider returns the **constant** prefix
  `"memory"` (`memory.rs:56`) - so within one `Session` *all* `memory://` URIs collapse to one
  cache key and two opens return the same store, whatever path you wrote in the URI. Across
  sessions they share nothing, because `Session::default()` builds a new `ObjectStoreRegistry`
  (`rust/lance/src/session.rs:326`), and `ObjectStore::memory()` bypasses the registry entirely
  (`rust/lance-io/src/object_store.rs:583-586`). Both halves are test-isolation traps: distinct
  `memory://` paths in one session are *not* isolated from each other, and the same
  `memory://` path in two sessions is *not* shared. Use **`shared-memory://`** when you actually
  want a cross-session in-memory store - that scheme exists precisely because "`memory://` mints
  a fresh `InMemory` per `new_store` call"
  (`rust/lance-io/src/object_store/providers/shared_memory.rs:42`).
