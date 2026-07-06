---
name: lance-format
description: Reference for Lance v9 - the open columnar lakehouse format for multimodal AI - and its Rust crate workspace (`lance`, `lance-table`, `lance-file`, `lance-encoding`, `lance-index`, `lance-io`, `lance-namespace`, and more). Use when building directly on the Lance crates - creating or reading `.lance` datasets, manifests, fragments, deletion files, the 2.x file format and structural encodings, vector / scalar / full-text / FM-Index / geo indexes, MemWAL streaming writes, optimistic-concurrency commits and commit handlers, schema evolution, versioning, time-travel, tags, branches, stable row IDs, namespaces, or object-store config. Triggers on lance crate, .lance file, lance dataset, lance file format, structural encoding, IVF_PQ, IVF_HNSW, IVF_RQ, RaBitQ, FM-Index, lance FTS, zonemap, MemWAL, OCC retry, lance schema evolution, lance namespace, pylance. This is the Lance format and engine (the `lance-format/lance` repo), not LanceDB the database product - but also the right reference for what LanceDB builds on.
metadata:
  version: "0.9.0"
  upstream: "lance-format/lance@v9.0.0-beta.16"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/lance-format
    emoji: "🗄️"
---

# Lance v9 reference

Lance is an open columnar format for multimodal AI - "a columnar data format that is 100x
faster than Parquet for random access." It is not one format but a stack of interoperating
specs: a **file format**, a **table format**, **index formats**, **catalog specs**, and a
**namespace client spec**. The Rust workspace at `lance-format/lance` implements all of them
plus Python (`pylance`) and Java bindings.

This skill tracks **`v9.0.0-beta.16`** (the `lance-format/lance` git tag), the current
development frontier. Pin against tags, not `main` - Lance ships beta
tags every few days and `next`-format encodings can change. **`v8.0.0` final shipped
2026-07-01** - if you need a stable pin rather than the v9 dev betas, track `v8.0.0`, whose
format and API are the frozen predecessor of what this reference describes.

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

All share `version = "9.0.0-beta.16"` except `lance-arrow-scalar`, which is pinned at
`58.0.0` to track Arrow. Workspace: edition 2024, `rust-version = 1.91.0`,
`resolver = "3"`; notable deps arrow 58, datafusion 53, opendal 0.57, jieba-rs 0.10,
`lance-namespace-reqwest-client` 0.8.6, itertools 0.14. Python bindings now require
**Python 3.10+** (3.9 dropped in v9, PR #7345).

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
ladder 2.2 sits *below* `next`, so the code does not flag 2.2 as unstable. As of v9 the docs
version table (`docs/src/format/file/versioning.md`) lists **2.3** as the unstable row and no
longer labels 2.2 unstable (it now reads "2.2-era storage features") - code and docs finally
agree that 2.3 is the unstable frontier, though 2.2 still carries the concrete experimental
encodings (Map, Blob v2, `VariablePackedStruct`).

## What's new in v9

The v8 -> v9 boundary is a **light major bump**: structurally v9 is nearly identical to v8
(same **25 crates**, **15 transaction ops**, file-format enum with `next => 2.3` and default
2.1, `CommitConfig.num_retries` still **20**, arrow 58 / datafusion 53 / opendal 0.57 /
jieba 0.10 unchanged). The major version was auto-triggered by Lance's `breaking-change`-label
detector (`ci/check_breaking_changes.py`), fired by two PRs: **Python 3.9 was dropped**
(minimum now 3.10, #7345) and **`alter_columns` now fails fast** when you cast a column that
has an index attached - you must `drop_index()` first instead of relying on the old silent
drop/invalidate (#7158). A third breaking change rode the already-bumped series: the FM-Index
proto message was **renamed `FMIndexIndexDetails` -> `FMIndexDetails`** (#7397), which makes
existing FM indexes unreadable. One public Rust-API removal: **`as_vector_index` is gone from
the `Index` trait** (#7392) - downcast via `as_any()`. A fourth breaking change landed later
in the v9 beta line: **FTS / inverted indexes now default to on-disk format v2** (#7512) -
`LANCE_FTS_FORMAT_VERSION` no longer controls new indexes, pass `format_version=1` if older
Lance readers must read them (existing v1 indexes stay queryable, section 11.3).

Net-new in v9: a **hamming clustering** utility for near-duplicate detection (SIMD union-find
over 64-bit binary hashes, #7379); **COUNT(*) pushdown** now works on stable-row-id datasets
(#7360); **per-column blob size thresholds** (`lance-encoding:blob-inline-size-threshold` /
`...-dedicated-size-threshold`, #7269); **tunable 32k miniblock chunks** via
`LANCE_MINIBLOCK_MAX_VALUES` (#7356, default still 4096); an **`icu/split` FTS tokenizer**
variant (#7474); **distributed LabelList index builds** (#7223); the **ngram index now
accelerates regex and infix LIKE** (#7139); and cleanup-explain plus fragment-reuse remap are
now **exposed to Python and Java** (#7248, #7438). Full delta in
`references/lance-reference.md` section 14.

The **v7 -> v8** boundary (the predecessor line) unified all index builds onto one
segment-based lifecycle: bitmap migrated to the segment workflow (#6869), the standalone
`IndexSegmentBuilder` API was removed (#6997), distributed BTree moved to the segmented
framework (#7013), file writers' `finish()` began returning `FileWriteSummary` (#7096), and
`describe_indices()`/`list_indices()` were reworked (#6903, #7129). v8 also added the
`lance-derive` crate (#6229), the **FM-Index** scalar index, **multi-bit IVF_RQ** (`num_bits`
1..=9), the public vector-search **`approx_mode`** (`fast`/`normal`/`accurate`), and the
**Volcengine TOS** (`tos://`) and feature-gated **GooseFS** (`goosefs://`) object stores.
The v7 era - MemWAL, branches, the geo/RTree index, the `lance-select` crate, ICU FTS - all
carries forward.

## Navigating the reference

`references/lance-reference.md` is the full v9 reference, regrounded against the `v9.0.0-beta.16`
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
14. **What changed** - the full v7 -> v8 -> v9 delta
15. **Capability matrix** - what Lance can and cannot do
16. **Source map** - where each spec and proto lives in the repo

## Maintenance

Citations in `references/lance-reference.md` are `path:line` relative to the `lance-format/lance` repo;
build a permalink as `https://github.com/lance-format/lance/blob/v9.0.0-beta.16/<path>`.

To refresh: `git -C ~/pjv/lance-format/lance fetch --tags`, check out the newest `v9*` tag
(or the v8.0.0 rc/final line for a stable pin), re-read the format spec under
`docs/src/format/` and the user guide under `docs/src/guide/`, re-verify the crate workspace,
and bump `metadata.upstream` plus every `v9.0.0-beta.16` reference. Line numbers in citations
drift between tags - treat them as approximate.
