---
name: lance-format
description: Reference for Lance v7 - the open columnar lakehouse format for multimodal AI - and its Rust crate workspace (`lance`, `lance-table`, `lance-file`, `lance-encoding`, `lance-index`, `lance-io`, `lance-namespace`, and more). Use when building directly on the Lance crates - creating or reading `.lance` datasets, manifests, fragments, deletion files, the 2.x file format and structural encodings, vector / scalar / full-text / geo indexes, MemWAL streaming writes, optimistic-concurrency commits and commit handlers, schema evolution, versioning, time-travel, tags, branches, stable row IDs, namespaces, or object-store config. Triggers on lance crate, .lance file, lance dataset, lance file format, structural encoding, IVF_PQ, IVF_HNSW, IVF_RQ, RaBitQ, lance FTS, zonemap, MemWAL, OCC retry, lance schema evolution, lance namespace, pylance. This is the Lance format and engine (the `lance-format/lance` repo), not LanceDB the database product - but also the right reference for what LanceDB builds on.
metadata:
  version: "0.5.0"
  upstream: "lance-format/lance@v7.2.0-beta.5"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/lance-format
    emoji: "🗄️"
---

# Lance v7 reference

Lance is an open columnar format for multimodal AI - "a columnar data format that is 100x
faster than Parquet for random access." It is not one format but a stack of interoperating
specs: a **file format**, a **table format**, **index formats**, **catalog specs**, and a
**namespace client spec**. The Rust workspace at `lance-format/lance` implements all of them
plus Python (`pylance`) and Java bindings.

This skill tracks **`v7.2.0-beta.5`** (the `lance-format/lance` git tag). Pin against tags,
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

24 crate directories under `rust/`. `lance` is the public entry point; the rest are layers
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
| `lance-geo` | Geospatial UDFs (feature-gated `geo`) |
| `lance-namespace` / `-impls` / `-datafusion` | Namespace trait, Directory/REST impls, DataFusion catalog bridge |
| `lance-arrow`, `lance-tools`, `fsst`, `lance-bitpacking`, ... | Arrow extensions, CLI, compression sub-crates |

All share `version = "7.2.0-beta.5"` except `lance-arrow-scalar`, which is pinned at
`58.0.0` to track Arrow. Workspace: edition 2024, `rust-version = 1.91.0`,
`resolver = "3"`.

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

## What's new in v7

The v6 -> v7 boundary is one breaking change: **`feat!: make dataset object store access
base-aware` (#6647)** - object-store access is now scoped to a dataset *base* rather than a
flat global path, which underpins multi-base storage (hot/cold tiering, shallow clones).

The dominant theme across the v7 betas is **MemWAL** - an experimental LSM / write-ahead-log
architecture for high-throughput streaming writes (WAL appender/tailer primitives, shard
writers, a Lance-native in-memory HNSW index, the `shared-memory://` object-store scheme).
Also landing in the v7 era: **branches** (Git-like, alongside tags), **segmented and
distributed index builds** (FTS, bitmap, btree), newer **scalar indexes** (zonemap, bloom
filter, ngram), the **geo / RTree** index and `lance-geo` crate, **manifest version hints**
for fast latest-version lookup, and a formal split of the catalog / namespace / table /
index specifications. The `v7.1.0-beta.1` tag opens the v7.1 line and adds a
**materialized-view namespace API**. `v7.1.0-beta.2` then extracts mask code into a new
**`lance-select`** crate (#6879) and lands two MemWAL correctness fixes - flushed
memtables now build their secondary indexes so vector rows are visible to `fast_search`
(#6901), and a per-source PK-hash block-list post-filter suppresses stale LSM vector reads
when the fresh row falls out of its source's top-k (#6899). The v7.2 line
(`v7.2.0-beta.5`, the current pin) adds an **ICU FTS tokenizer** (#6956), **scalar-index
fast search** (#6784), **batched vector queries** (#6828), and **streaming IVF k-means**
(#6913) - no breaking changes, no new crate (still 24), no new transaction op (still 15).
Details in `references/lance-reference.md` section 14.

## Navigating the reference

`references/lance-reference.md` is the full v7 reference, regrounded against the `v7.2.0-beta.5`
source. Load the section for your task:

1. **What Lance is** - the lakehouse spec stack
2. **Crate workspace** - all 24 crates, what each does, the public entry point
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
11. **Indexes** - vector (IVF/HNSW/PQ/SQ/RQ), scalar (btree/bitmap/bloom/labellist/ngram/
    zonemap), full-text (BM25, tokenizers), geo/RTree
12. **Distributed write and indexing** - two-phase commits, segmented index builds
13. **Object store** - URI schemes, storage options, per-backend config
14. **What changed in v7** - the full v7 delta
15. **Capability matrix** - what Lance can and cannot do
16. **Source map** - where each spec and proto lives in the repo

## Maintenance

Citations in `references/lance-reference.md` are `path:line` relative to the `lance-format/lance` repo;
build a permalink as `https://github.com/lance-format/lance/blob/v7.2.0-beta.5/<path>`.

To refresh: `git -C ~/pjv/lance-format/lance fetch --tags`, check out the newest `v7*` tag,
re-read the format spec under `docs/src/format/` and the user guide under `docs/src/guide/`,
re-verify the crate workspace, and bump `metadata.upstream` plus every `v7.2.0-beta.5`
reference. Line numbers in citations drift between tags - treat them as approximate.
