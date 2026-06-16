---
name: lance-format
description: Reference for Lance v8 - the open columnar lakehouse format for multimodal AI - and its Rust crate workspace (`lance`, `lance-table`, `lance-file`, `lance-encoding`, `lance-index`, `lance-io`, `lance-namespace`, and more). Use when building directly on the Lance crates - creating or reading `.lance` datasets, manifests, fragments, deletion files, the 2.x file format and structural encodings, vector / scalar / full-text / FM-Index / geo indexes, MemWAL streaming writes, optimistic-concurrency commits and commit handlers, schema evolution, versioning, time-travel, tags, branches, stable row IDs, namespaces, or object-store config. Triggers on lance crate, .lance file, lance dataset, lance file format, structural encoding, IVF_PQ, IVF_HNSW, IVF_RQ, RaBitQ, FM-Index, lance FTS, zonemap, MemWAL, OCC retry, lance schema evolution, lance namespace, pylance. This is the Lance format and engine (the `lance-format/lance` repo), not LanceDB the database product - but also the right reference for what LanceDB builds on.
metadata:
  version: "0.7.0"
  upstream: "lance-format/lance@v8.0.0-beta.14"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/lance-format
    emoji: "🗄️"
---

# Lance v8 reference

Lance is an open columnar format for multimodal AI - "a columnar data format that is 100x
faster than Parquet for random access." It is not one format but a stack of interoperating
specs: a **file format**, a **table format**, **index formats**, **catalog specs**, and a
**namespace client spec**. The Rust workspace at `lance-format/lance` implements all of them
plus Python (`pylance`) and Java bindings.

This skill tracks **`v8.0.0-beta.14`** (the `lance-format/lance` git tag). Pin against tags,
not `main` - Lance ships beta tags every few days and `next`-format encodings can change.

The deep reference is `references/lance-reference.md`. Load it for any concrete schema, parameter,
proto, or constraint. This file is the orientation: read it first, then jump into the
reference section you need.

## Lance vs LanceDB

These are two different things and conflating them produces wrong answers.

- **Lance** - the format and engine. The `lance-format/lance` repo; the `lance` /`lance-*`
  Rust crates; `pylance`. It gives you datasets, the file/table format, indexes, commits,
  scans. Consumed directly by DuckDB, Polars, Ray, Spark, PyTorch, DataFusion, or your own
  Rust/Python code. **This skill is about Lance.**
- **LanceDB** - a separate database *product* (`lancedb/lancedb`) built on top of Lance. It
  adds a query-builder API, an embedding registry, rerankers-as-API, multi-language SDK
  parity, and managed Cloud / Enterprise tiers. Not covered here.

If you are linking the `lance` crate in `Cargo.toml`, you are using Lance directly - use this
skill. If a question is about LanceDB internals, the storage layer underneath it is still
Lance, so this skill remains the authority for the format itself.

## The crate workspace

25 crate directories under `rust/`. `lance` is the public entry point; the rest are layers
beneath it. Full table with descriptions and citations in `references/lance-reference.md` section 2.

| Crate | Role |
|-------|------|
| `lance` | Public entry point - `Dataset`, scanner, indexes, commits |
| `lance-table` | Table format - manifest, feature flags, commit handlers, row IDs |
| `lance-file` | File format - file reader/writer |
| `lance-encoding` | Structural encodings, compression (internal, not for external use) |
| `lance-index` | Scalar / vector / FTS / system indexes |
| `lance-io` | Object store, I/O schedulers |
| `lance-core` | Shared `Error`/`Result`, cache, datatypes |
| `lance-datafusion` | DataFusion glue (exec, expr, planner, UDFs) |
| `lance-linalg` | SIMD L2 / dot / cosine / hamming kernels |
| `lance-select` | Row-selection primitives - `RowAddrMask`, `RowIdMask`, `IndexExprResult` (extracted from `lance-core`/`lance-index` in v7.1.0-beta.2) |
| `lance-tokenizer` | FTS tokenizer stack (simple, ngram, jieba, lindera, stemmers) |
| `lance-derive` | `#[derive(DeepSizeOf)]` proc-macro for Arrow-aware memory accounting (new in v8, PR #6229; replaced the external `deepsize` crate) |
| `lance-geo` | Geospatial UDFs (feature-gated `geo`) |
| `lance-namespace` / `-impls` / `-datafusion` | Namespace trait, Directory/REST impls, DataFusion catalog bridge |
| `lance-arrow`, `lance-tools`, `fsst`, `lance-bitpacking`, ... | Arrow extensions, CLI, compression sub-crates |

All share `version = "8.0.0-beta.14"` except `lance-arrow-scalar`, which is pinned at
`58.0.0` to track Arrow. Workspace: edition 2024, `rust-version = 1.91.0`,
`resolver = "3"`; notable deps arrow 58, datafusion 53, opendal 0.57, jieba-rs 0.10.

## File format versions

The file format carries a single major.minor version. Selected per-dataset at creation via
`data_storage_version` and **fixed once the dataset exists** (to change it, rewrite the
dataset).

| Version | Status | Notes |
|---------|--------|-------|
| `0.1` (`legacy`) | read-only | Original format; no longer writable |
| `2.0` | stable | Removed row groups; null support for lists/FSL/primitives |
| `2.1` | **current default** (`stable`) | Adaptive structural encodings; better integer/string compression; nulls in struct fields; better nested random access. Default since Lance 5.0.0 |
| `2.2` | unstable | Map type, Blob v2, `VariablePackedStruct`, larger mini-blocks. Required for Map and Blob v2; the real experimental frontier - encodings may still change |
| `2.3` | unstable (`next`) | The current `next` alias target (`V2_3` in the enum). Scaffolding only - no distinct encodings yet (6 refs vs 98 for 2.2 in `lance-encoding`); the docs version table still lists only 2.2 |

`stable` resolves to the default (2.1); `next` now resolves to **2.3** (not 2.2) in the
running Lance release - pin an explicit number for deterministic behavior. In the version
ladder 2.2 sits *below* `next`, so the code does not flag 2.2 as unstable even though the
docs do; 2.2 is the version actually carrying the experimental features.

## What's new in v8

The v7 -> v8 boundary unifies **all index builds onto one segment-based lifecycle**. The
spine is `feat!: migrate bitmap to index segment based` (#6869): the old public Python
Bitmap shard workflow (`create_scalar_index(..., fragment_ids=)` + `merge_index_metadata(...,
"BITMAP")`) is gone, and bitmap now flows through the same `create_index_uncommitted` ->
`merge_existing_index_segments` -> `commit_existing_index_segments` path as everything else.
Five more breaking changes land with it: the standalone **`IndexSegmentBuilder` API was
removed** from Rust/Python/Java (#6997, `build_all()` and `target_segment_bytes` gone);
**distributed BTree build moved to the segmented framework** (#7013); file/index writers'
**`finish()` now returns `FileWriteSummary { num_rows, size_bytes }`** instead of a bare row
count (#7096); **`describe_indices()`/`list_indices()`** report full nested field paths and
derive type from index details without opening the index (`load_indices()` removed, #6903);
and **index directories are no longer listed after writes** - `IndexFile` metadata is
propagated into the manifest instead (#7129).

Net-new in v8: the **`lance-derive`** crate (#6229, `#[derive(DeepSizeOf)]`, replacing the
external `deepsize`; workspace 24 -> 25 crates); the **FM-Index** scalar index (Ferragina-
Manzini / Burrows-Wheeler substring, prefix, and regex search on raw bytes, built on the
Segmented Index architecture); **multi-bit IVF_RQ** (RaBitQ `num_bits` 1..=9, no longer
1-bit-only, plus a raw-query distance estimator); **independent per-worker vector index
models** for distributed builds; and the **Volcengine TOS** (`tos://`) and feature-gated
**GooseFS** (`goosefs://`) object stores. `merge_existing_index_segments` now also covers
zone-map segments. Unchanged at v8: still **15 transaction ops**, `next` still resolves to
**2.3** (default still 2.1), `CommitConfig.num_retries` still **20**, the feature-flag bits,
and the `ConditionalPutCommitHandler` routing. The v7 era - MemWAL, branches, the geo/RTree
index, the `lance-select` crate, ICU FTS - all carry forward.

Later v8 betas (`beta.9` -> `beta.14`) add a public vector-search **`approx_mode`**
(`fast`/`normal`/`accurate`) for RaBitQ indexes (a breaking `ann.proto` change), a 4096
default IVF_RQ `target_partition_size`, a **cleanup explain** API, and full Tencent COS /
GooseFS object-store config docs; they remove the `table_version_storage_enabled` /
`__manifest` version path and brotli. All structural invariants above are unchanged.
Details in `references/lance-reference.md` section 14.

## Navigating the reference

`references/lance-reference.md` is the full v8 reference, regrounded against the `v8.0.0-beta.14`
source. Load the section for your task:

1. **What Lance is** - the lakehouse spec stack
2. **Crate workspace** - all 25 crates, what each does, the public entry point
3. **File format** - versions, container layout, structural encoding (mini-block / full-zip /
   constant / blob page types), compression schemes, blob encoding
4. **Data types** - Arrow type coverage, FixedSizeList for vectors, JSON (JSONB), blob, ML
   extension arrays (bfloat16, image types)
5. **Table format** - dataset directory layout, manifest contents, fragments, deletion
   files, base paths
6. **Schema evolution** - field IDs, zero-copy column add/drop/alter, why old rows read NULL
7. **Versioning, tags, branches** - manifest versions, time travel, tag pinning, branches
8. **Row IDs** - row address vs stable row ID, lineage, change-data-feed columns
9. **Transactions and concurrency** - the 15 transaction ops, OCC retry/rebase, commit
   handlers (conditional-put, DynamoDB), conflict resolution matrix
10. **MemWAL** - shards, MemTable/WAL/flush, the appender/tailer/flusher model, fencing
11. **Indexes** - vector (IVF/HNSW/PQ/SQ/RQ, multi-bit RQ), scalar (btree/bitmap/bloom/
    labellist/ngram/zonemap/FM-Index), full-text (BM25, tokenizers), geo/RTree
12. **Distributed write and indexing** - two-phase commits, segment-based index builds
13. **Object store** - URI schemes, storage options, per-backend config
14. **What changed in v8** - the full v7 -> v8 delta
15. **Capability matrix** - what Lance can and cannot do
16. **Source map** - where each spec and proto lives in the repo

## Maintenance

Citations in `references/lance-reference.md` are `path:line` relative to the `lance-format/lance` repo;
build a permalink as `https://github.com/lance-format/lance/blob/v8.0.0-beta.14/<path>`.

To refresh: `git -C ~/pjv/lance-format/lance fetch --tags`, check out the newest `v8*` tag,
re-read the format spec under `docs/src/format/` and the user guide under `docs/src/guide/`,
re-verify the crate workspace, and bump `metadata.upstream` plus every `v8.0.0-beta.14`
reference. Line numbers in citations drift between tags - treat them as approximate.
