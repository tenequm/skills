# Lance v8 reference

Capability reference for **Lance** - the open columnar lakehouse format for multimodal AI -
regrounded against the `lance-format/lance` repository at git tag **`v8.0.0-beta.14`**
(commit `c188de59f`).

Citations are `path:line` relative to the repo root. Build a permalink as
`https://github.com/lance-format/lance/blob/v8.0.0-beta.14/<path>`. Line numbers drift
between tags; treat them as approximate. The authoritative in-repo sources are the format
spec under `docs/src/format/`, the user guide under `docs/src/guide/`, the protobuf schemas
under `protos/`, and the Rust workspace under `rust/`.

This is the Lance *format and engine*. LanceDB (`lancedb/lancedb`) is a separate database
product built on top of Lance and is out of scope - but Lance is what it stores into, so
this reference is still authoritative for the format underneath it.

## Contents

1. [What Lance is](#1-what-lance-is)
2. [The crate workspace](#2-the-crate-workspace)
3. [File format](#3-file-format)
4. [Data types](#4-data-types)
5. [Table format](#5-table-format)
6. [Schema evolution](#6-schema-evolution)
7. [Versioning, tags, branches](#7-versioning-tags-branches)
8. [Row IDs and lineage](#8-row-ids-and-lineage)
9. [Transactions and concurrency](#9-transactions-and-concurrency)
10. [MemWAL](#10-memwal)
11. [Indexes](#11-indexes)
12. [Distributed write and indexing](#12-distributed-write-and-indexing)
13. [Object store](#13-object-store)
14. [What changed (v7 -> v8)](#14-what-changed-v7---v8)
15. [Capability matrix](#15-capability-matrix)
16. [Source map](#16-source-map)

---

## 1. What Lance is

Lance is "a columnar data format that is 100x faster than Parquet for random access"
(`Cargo.toml:37`, workspace description). It is not a single format but a **stack of
interoperating specifications**, deliberately decoupled so each layer evolves independently
(`docs/src/format/index.md:3-19`):

- **File format** - stores column data in large random-access-friendly pages, no row groups.
  Only table readers/writers and index readers/writers need to know the on-disk layout.
- **Table format** - the dataset: manifests, fragments, deletion files, schema, transactions.
- **Index formats** - scalar, vector, full-text, geo, and system indexes. The file format
  deliberately keeps statistics and search structures *out* of the file so indexes evolve
  as independent specs (`docs/src/format/index.md:25`).
- **Catalog specs** - Directory Catalog and REST Catalog: how datasets are discovered.
- **Namespace client spec** - a unified client interface for engines to talk to any catalog,
  Lance-native or third-party, in any language.

Lance uses **Apache Arrow** as its in-memory type system and is consumed directly by DuckDB,
Polars, Ray, Spark, PyTorch, TensorFlow, and DataFusion, or by your own Rust/Python/Java
code. The format itself is the product - there is no server.

---

## 2. The crate workspace

25 crate directories under `rust/`. `[workspace.package]`: `version = "8.0.0-beta.14"`,
`edition = "2024"`, `rust-version = "1.91.0"`, `license = "Apache-2.0"`, `resolver = "3"`
(`Cargo.toml:31-55`). `exclude = ["python", "java/lance-jni"]`.

| Crate dir | Published name | Purpose |
|-----------|----------------|---------|
| `lance` | `lance` | **Public entry point.** `Dataset`, scanner, indexes, commits |
| `lance-table` | `lance-table` | Table format: `feature_flags`, manifest `format`, commit `io`, `rowids` |
| `lance-file` | `lance-file` | File format: file reader/writer, `LanceEncodingsIo`, MAGIC bytes |
| `lance-encoding` | `lance-encoding` | Structural encodings, compression. Internal - not for external use |
| `lance-index` | `lance-index` | Secondary indexes: scalar, vector, FTS, system |
| `lance-io` | `lance-io` | Object store, I/O schedulers, local FS, FFI |
| `lance-core` | `lance-core` | Shared `Error`/`Result`, `cache`, `datatypes`, `traits`, `utils` |
| `lance-datafusion` | `lance-datafusion` | DataFusion glue: `exec`, `expr`, `planner`, `projection`, UDFs |
| `lance-linalg` | `lance-linalg` | SIMD L2 / dot / cosine / hamming kernels |
| `lance-arrow` | `lance-arrow` | Arrow extensions (`RecordBatchExt`, `SchemaExt`). Considered never-stable |
| `lance-select` | `lance-select` | Row-selection primitives: `RowAddrMask`/`NullableRowAddrMask`, `RowIdMask`, `IndexExprResult`. Extracted from `lance-core`/`lance-index` in v7.1.0-beta.2 (PR #6879) so benchmarks and filter consumers can depend on masks without pulling in either larger crate |
| `lance-tokenizer` | `lance-tokenizer` | FTS tokenizer stack: `TextAnalyzer`, jieba/lindera/ngram, filters |
| `lance-derive` | `lance-derive` | Proc-macro crate (`proc-macro = true`): `#[derive(DeepSizeOf)]` for Arrow-aware memory accounting. New in v8 (PR #6229), replacing the external `deepsize` crate, which double-counts Arrow buffers shared across `Arc` |
| `lance-geo` | `lance-geo` | Geospatial UDFs. Feature-gated `geo` |
| `lance-namespace` | `lance-namespace` | `LanceNamespace` trait + data models |
| `lance-namespace-impls` | `lance-namespace-impls` | `DirectoryNamespace`, `RestNamespace`, REST adapter, credential vendors |
| `lance-namespace-datafusion` | `lance-namespace-datafusion` | DataFusion catalog/schema provider bridge |
| `lance-tools` | `lance-tools` | `cli` / `meta` / `util`; ships a `lance-tools` binary |
| `lance-datagen` | `lance-datagen` | Random Arrow array/batch generation for tests/benchmarks |
| `lance-test-macros` | `lance-test-macros` | Test-only proc macros |
| `lance-testing` | `lance-testing` | Shared test helpers/fixtures |
| `compression/fsst` | `fsst` | FSST string compression |
| `compression/bitpacking` | `lance-bitpacking` | Vendored SIMD bit-packing (from spiraldb/fastlanes) |
| `arrow-scalar` | `lance-arrow-scalar` | Arrow scalar with `Ord`/`Hash`/`Eq`. Pinned `58.0.0` (tracks Arrow) |
| `arrow-stats` | `lance-arrow-stats` | Statistics accumulator (min, max, null_count, nan_count) |

`rust/examples` (`lance-examples`) holds non-published example binaries. The workspace
`members` array lists 25 paths; `rust/lance-datafusion` is part of the workspace as a
path dependency rather than an explicit member.

**Bindings.** Python: package `pylance` (`python/pyproject.toml`), built with maturin, imported
as `lance`; the Rust extension crate is `pylance` (`[lib] name = "lance"`); supports Python
3.9-3.14; runtime deps `pyarrow>=14`, `numpy>=1.22`, `lance-namespace>=0.8.5,<0.9`. Java: an
SDK under `java/` (Maven `org.lance`), bridged to Rust by the `lance-jni` crate
(`java/lance-jni/`, excluded from the Rust workspace). Notable workspace deps at this tag
(`Cargo.toml`): `arrow 58.0.0`, `datafusion 53.0.0`, `opendal 0.57`, `jieba-rs 0.10`,
`lance-namespace-reqwest-client 0.8.4`. The `lance-namespace`/`-impls` crates publish at
the workspace version (`8.0.0-beta.14`); note the `[workspace.dependencies]` declaration
still pins `lance-namespace-datafusion` consumers to `=7.0.0-beta.9` even though that crate
itself publishes at the workspace version.

**Building.** Five workspace crates carry a protobuf build script - `lance-encoding`,
`lance-file`, `lance-index`, `lance-table`, `lance-datafusion` - so a `protoc` compiler must
be reachable to build them. The `lance` crate's `protoc` feature vendors one (`protobuf-src`)
and cascades it to the first four, but **not** to `lance-datafusion`, which still needs a
system `protoc` (`Cargo.toml:140-146`, `rust/lance-datafusion/Cargo.toml`).

---

## 3. File format

### 3.1 Versions

The file format has one major.minor version: the major changes when the container changes,
the minor when only the encoding strategy changes (`docs/src/format/file/versioning.md:3-5`).
The footer stores `u16` major and `u16` minor (`protos/file2.proto:90-91`).

| Version | Min Lance | Status | Description (`docs/src/format/file/versioning.md:18-26`) |
|---------|-----------|--------|-------------|
| `0.1` (`legacy`) | any | read-only, no longer writable | Initial Lance format |
| `2.0` | 0.16.0 | stable | Removed row groups; null support for lists, fixed-size lists, primitives |
| `2.1` | 0.38.1 | **current default** | Adaptive structural encodings; better integer/string compression; nulls in struct fields; better nested random access |
| `2.2` | - | unstable | Map type, Blob v2, `VariablePackedStruct`, larger mini-blocks; encodings may still change. The real experimental frontier |
| `2.3` | - | unstable (`next`) | The current `next` alias target. Scaffolding only - present in the enum but with no distinct encoding behavior yet |

`stable` resolves to the default (2.1); `next` resolves to the latest unstable version. The
enum order is `Legacy < 2.0 < 2.1 (#[default]) < Stable < 2.2 < Next < 2.3`, with
`Stable => 2.1` and `Next => 2.3`, and `is_unstable() = self >= Next`
(`rust/lance-encoding/src/version.rs:21-46`). Two consequences that surprise readers: (1)
**`next` now resolves to 2.3, not 2.2** - writing with `next` produces a 2.3 file; (2)
because 2.2 sits *below* `Next` in the ladder, the code does **not** flag 2.2 as unstable,
yet the docs version table (`docs/src/format/file/versioning.md:21-29`) still lists only 2.2
and labels it unstable. 2.3 is currently a placeholder (6 refs vs 98 for 2.2 across
`lance-encoding`) - 2.2 is the version actually carrying Map / Blob v2 / `VariablePackedStruct`.
`next` encodings can change and files written with them may become unreadable - "should only
be used for experimentation and benchmarking" (`docs/src/format/file/versioning.md:8-11`).
The default storage version became 2.1 in Lance 5.0.0 (`docs/src/guide/migration.md`); 2.2 is
required for the Map type and Blob v2. Selected per-dataset via `data_storage_version` and
**fixed at dataset creation** - to change it you write a new dataset.

### 3.2 Container layout

A `.lance` file, top to bottom (`docs/src/format/file/index.md:123-161`, `protos/file2.proto`):

1. **Data pages** - sector-aligned data buffers.
2. **Column metadata** - one standalone protobuf `ColumnMetadata` per column. A subset of
   columns can be read without reading all metadata (column projection).
3. **Column metadata offset table** - position + size per column.
4. **Global buffers offset table** - position + size per global buffer (file schema, file
   indexes, column statistics).
5. **Footer** (fixed-size) - offsets to the above, column/buffer counts, `u16` major + `u16`
   minor version, magic `"LANC"`. All fields little-endian.

**No row groups.** "Unlike similar formats, there is no 'row group' concept, only pages. We
believe the concept of row groups to be fundamentally harmful to performance"
(`docs/src/format/file/index.md:41-42`). A disk page holds rows for a single column; each
column has its own page count. Default recommended page size is 8MB. A reader can split a
file at any row boundary via partial page reads with minimal read amplification - the unit of
parallelism is decoupled from physical layout.

Buffers are referenced by absolute offset, aligned to 64 bytes (SIMD) or 4096 (direct I/O).
The file container has **no type system** - columns are integer-indexed; the schema lives in
a global buffer and the file format is unaware of it. Encodings are extensions, designed to
be added/removed without recompiling the reader.

### 3.3 Structural encoding (2.1)

A structural encoding "breaks the data into smaller units which can be independently
decoded" and encodes structure (struct/list validity, list offsets) via **repetition and
definition levels** - one combined buffer instead of separate validity bitmaps and offset
arrays, to avoid multiple IOPS (`docs/src/format/file/encoding.md:48-69`). Note: Lance uses
**0 for the inner-most item** (Parquet uses 0 for the outer-most).

Data types and layouts are orthogonal. The top-level `PageLayout` has four page types
(`protos/encodings_v2_1.proto:197-210`):

- **Mini-block** - default for "smallish" types (integers, floats, booleans, small strings).
  Data split into mini-blocks of a power-of-two value count, each <32KiB compressed; reading
  any value reads the whole block, so blocks are kept small. Rep/def levels are sliced into
  the blocks. A random-access metadata buffer (2 bytes/block) is loaded into the search cache
  at init time. Default 4096 values/block (`LANCE_MINIBLOCK_MAX_VALUES`). 2.2 adds larger
  chunks (>=64KB) via `has_large_chunk`.
- **Full-zip** - for larger values (e.g. vector embeddings) above a 256-byte cutoff. Rep/def
  levels and compressed buffers are zipped into one buffer; a per-row repetition index gives
  random access. Requires *transparent* compression (individual values indexable after
  compression).
- **Constant** - all visible values in the page are the same scalar; also the all-null case.
  Generalizes the old `AllNullLayout` for file version >=2.2.
- **Blob** - large binary values stored out-of-line; the page stores `(position, size)`
  descriptions. See 3.5.

**Search cache.** Random access needs encoding + page-location info; this forms an LRU
"search cache" loaded during an initialization phase, amortized over the reader's lifetime.
Cold full scans can skip loading it.

Semi-structural transforms applied before structural encoding: **dictionary encoding**
(decided per leaf value page, so `List<u32>` can dictionary-encode its values), **struct
packing** (row-major struct storage - `PackedStruct` for fixed-width children in 2.1,
`VariablePackedStruct` for variable-width in 2.2), and **fixed-size-list flattening**.

### 3.4 Compression

Compression schemes and the contexts they apply in (`docs/src/format/file/encoding.md:441-450`):

| Scheme | Notes |
|--------|-------|
| Flat | Uncompressed fixed-width; bits-per-value need not be a multiple of 8 |
| Variable | Uncompressed variable-width (values + offsets) |
| Bitpacking | Drops unused high bits. `InlineBitpacking` (per-chunk width, opaque) and `OutOfLineBitpacking` (fixed width, transparent) |
| FSST | "The primary compression algorithm for variable-width data" - fast and transparent |
| RLE | Runs of identical values; applied when `run_count/num_values` < threshold (default 0.5) |
| ByteStreamSplit | Splits multi-byte values into per-byte streams; only helps if general compression also runs; f32/f64/timestamps only |
| General | Opaque back-referencing compressors: LZ4, ZStandard, Snappy. Auto-applied in full-zip for values >=32KiB; otherwise opt-in |

Configured via field metadata (`docs/src/format/file/encoding.md:536-552`): keys
`lance-encoding:compression` (`lz4`/`zstd`/`none`/`fsst`), `:compression-level`,
`:rle-threshold` (default 0.5), `:bss` (`off`/`on`/`auto`), `:general` (`off`/`on`),
`:packed`, plus dictionary tuning (`:dict-divisor`, `:dict-size-ratio`,
`:dict-values-compression`). Compression sub-crates: `fsst` (`rust/compression/fsst`) and
`lance-bitpacking` (`rust/compression/bitpacking`, a vendored copy of spiraldb/fastlanes).
`lance-encoding` default features: `lz4`, `zstd`, `bitpacking`.

The encoding strategy "tends to evolve more quickly than the file format itself"
(`encoding.md:3-4`); several layout details are explicitly marked as likely to change (the
FSST per-page symbol table, full-zip value-size encoding, constant-layout rep/def storage).
Only **1-dimensional random access** is currently supported.

### 3.5 Blob encoding

Blob page layout stores large binary values out-of-line (`docs/src/format/file/encoding.md:351-375`).
The disk page holds a struct array of `(position, size)` descriptions; actual bytes live in
external buffers. Validity is smuggled into the description: `size==0 && position==0` =
empty; `size==0 && position!=0` = null. Recommended only when one IOP per value is justified
(values >=1MiB).

**Blob v2** (`lance.blob.v2` extension type) is the path for file format >=2.2; for >=2.2 the
legacy `lance-encoding:blob` metadata is rejected on write (`docs/src/guide/blob.md:45-52`).
Blob columns are read lazily as `BlobFile` handles - callers stream bytes on demand
(`with blob as f: f.read()`). `take_blobs` takes exactly one of `ids` (logical row-id),
`indices` (positional within a snapshot), or `addresses` (physical, debug). A blob v2 column
can mix inline bytes, an external URI, an external URI slice (`Blob.from_uri(uri,
position=, size=)`), and null - enabling many payloads packed into one container file
referenced by `(position, size)` slices.

---

## 4. Data types

Lance supports the full Apache Arrow type system; Arrow types auto-map to Lance's internal
representation (`docs/src/guide/data_types.md`).

- **Primitive** - `Boolean`; `Int8/16/32/64`; `UInt8/16/32/64`; `Float16/32/64`;
  `Decimal128`, `Decimal256`; `Date32`, `Date64`; `Time32`, `Time64`; `Timestamp` (with
  timezone); `Duration`.
- **String/binary** - `Utf8`, `LargeUtf8` (64-bit offsets), `Binary`, `LargeBinary`,
  `FixedSizeBinary(n)`.
- **Nested** - `Struct` (arbitrarily nestable; 2.1 added null support in struct fields),
  `List` / `LargeList` (variable-length), `Map(K,V)` (**requires file format 2.2+**).
- **FixedSizeList** - the recommended type for fixed-dimension vector embeddings; optimized
  for columnar storage, SIMD distance computation, and vector indexing. Best practice:
  dimensions divisible by 8.
- **JSON** (`lance.json` extension type) - stored internally as **JSONB** (binary JSON),
  read back as Arrow's JSON type. Filter-only query functions: `json_extract` (JSONPath),
  `json_get` (returns JSONB for chaining), `json_get_string/int/float/bool`, `json_exists`,
  `json_array_contains`, `json_array_length`. Indexable: a scalar index on a JSON path, or an
  inverted (FTS) index over JSON contents (`docs/src/guide/json.md`).
- **Blob** (`lance.blob.v2` extension type) - large binary objects, lazy file-like loading
  (section 3.5).
- **ML extension arrays** (`docs/src/guide/arrays.md`) - `BFloat16` (16-bit ML float,
  `lance.arrow.BFloat16Array`), `ImageURI`, `EncodedImage` (jpeg/png on disk),
  `FixedShapeImageTensor`.

---

## 5. Table format

A Lance **dataset** (a "table") is a directory of immutable files plus a sequence of
versioned manifests.

### 5.1 Dataset directory layout

`docs/src/format/table/layout.md:18-42`:

```
{dataset_root}/
  data/          *.lance                    -- column data files
  _versions/     *.manifest                 -- one manifest per version
                 latest_version_hint.json   -- optional latest-version hint
  _transactions/ *.txn                      -- serialized Transaction protobuf per commit
  _deletions/    *.arrow / *.bin            -- deletion vectors (Arrow IPC / roaring bitmap)
  _indices/      {UUID}/...                 -- index content, one dir per index segment
  _refs/         tags/*.json branches/*.json -- tag and branch metadata
  tree/          {branch_name}/...          -- per-branch datasets (v7)
```

All file paths inside Lance files are stored **relative to their containing directory** -
copying the dataset root relocates it with no manifest edits.

**Base paths.** The manifest's `base_paths` array defines alternative storage locations
(`docs/src/format/table/layout.md:46-79`, `protos/table.proto:211-222`). A `BasePath` has an
`id` (uint32, from 0), optional `name`, `is_dataset_root` (true = standard subdirectory
layout; false = a flat file directory), and an absolute `path`. Data files, deletion files,
and index metadata each carry an optional `base_id` referencing a base; absent means relative
to the dataset root. Use cases: hot/cold tiering, multi-region distribution, shallow clones.
Gated by feature flag `FLAG_BASE_PATHS`.

### 5.2 Manifest

A manifest describes a single immutable version of the dataset (`protos/table.proto:36-208`).
Key fields: `fields` (the schema, all fields including nested), `fragments` (the
`DataFragment` list for this version), `version` (monotonically increasing u64), `timestamp`,
`writer_version`, `index_section` (file position of index metadata), `data_format`
(`file_format` + version string - every file in a version shares one format version),
`config` and `table_metadata` (string maps; `lance.`-prefixed config keys reserved),
`base_paths`, `branch` (optional; absent = main), `next_row_id` (only with stable row IDs),
`reader_feature_flags` / `writer_feature_flags`, `transaction_file`.

**Manifest naming** has two schemes (`transaction.md:24-32`): **V1** = `{version}.manifest`;
**V2** = `{u64::MAX - version:020}.manifest` (20-digit, reverse-sorted, so the latest version
sorts first lexicographically - enables O(1) latest-version discovery on ordered stores).

### 5.3 Fragments

A `DataFragment` is a horizontal partition holding a subset of rows
(`protos/table.proto:308-349`): `id` (unique, incrementally assigned), `files` (one or more
`DataFile`s, each storing a subset of columns), an optional `deletion_file` (at most one per
fragment per version), `physical_rows` (total including tombstoned rows - live count =
`physical_rows - deletion_file.num_deleted_rows`), and optional inline-or-external row-id /
version sequences.

A `DataFile` stores a subset of columns in the Lance file format, with `fields` (the field
IDs it contains; `-2` = tombstoned), `column_indices`, file major/minor version, and optional
`base_id`. **A field with no backing data file reads as entirely NULL** - this is the
mechanism behind zero-copy schema evolution.

### 5.4 Deletion files

Deletes are **soft**: a deletion file (deletion vector) marks deleted row offsets without
rewriting data files; at most one per fragment per version (`docs/src/format/table/index.md:149-160`).
Two formats: **Arrow IPC** (`.arrow`, a flat `Int32Array` of offsets - sparse deletions) and
**roaring bitmap** (`.bin` - dense deletions). Offsets are 0-based within the fragment. Path:
`_deletions/{fragment_id}-{read_version}-{id}.{ext}`. Gated by `FLAG_DELETION_FILES`. Deletes
avoid invalidating indexes; accumulating deletions slow scans until compacted.

---

## 6. Schema evolution

Every field, including nested fields, has a unique integer **field ID**, assigned in
depth-first order from 0 at table creation; new fields get the next available ID
(`docs/src/format/table/schema.md:195-236`). Field IDs are immutable, unique, stable across
evolution, and sparse. Internal references always use field IDs, never names or positions.
Nested fields link via `parent_id` (`-1` for top-level).

Schema changes are **metadata-only** wherever possible (`docs/src/guide/data_evolution.md`):

- **Add column** - assign a new field ID, update the schema. Schema-only add is very fast.
  File format <=2.1 cannot add sub-columns under an existing struct; 2.2 can extend nested
  struct fields (including structs nested in lists).
- **Drop column** - remove the field from the schema; metadata-only, does not delete data on
  disk; reversible while old versions are retained. Physical removal happens only after
  compaction + version cleanup. 2.2 supports nested sub-column removal.
- **Rename / reorder** - change `name` or order; field IDs unchanged.
- **Type change / cast** - may require rewriting that column to new data files (other columns
  untouched); an index on the column is dropped on type change.

**Zero-copy data evolution.** Because each data file holds a distinct set of field IDs and a
missing field reads as NULL, a writer can add and backfill a column by **appending new data
files to existing fragments** with computed values - no full table rewrite. This is the
mechanism for ML feature engineering and adding embeddings to an existing dataset. When a
column is rewritten, the old data file's field ID becomes the tombstone `-2` and a new data
file is appended.

Lance also supports an **unenforced primary key** and **clustering key**, declared via field
metadata (`lance-schema:unenforced-primary-key`). "Unenforced" - Lance does not always
validate uniqueness; it is used for merge-insert dedup and last-write-wins. PK fields must be
non-nullable leaf primitives; clustering-key fields may be nullable.

**Merge-insert (upsert / find-or-create).** `MergeInsertBuilder` defaults to find-or-create
semantics ("By default this will build a job that has the same semantics as find-or-create",
`rust/lance/src/dataset/write/merge_insert.rs:418`); enable `when_matched(WhenMatched::UpdateAll)`
for upsert - note `UpdateAll` rewrites whole fragments. The default behavior for **duplicate
source rows that match the same target** is to **fail the operation**
(`SourceDedupeBehavior::Fail`, `merge_insert.rs:322,472`); opt into `SourceDedupeBehavior::FirstSeen`
to keep the first and skip later duplicates. Empty `on` keys fall back to the schema's
unenforced primary key.

---

## 7. Versioning, tags, branches

Every commit creates a new immutable version with a monotonically increasing `version`
number; all versions form a serializable history enabling time travel
(`docs/src/format/table/transaction.md:5-7`). Writes (append, overwrite, index ops,
compaction) create versions; **creating or deleting tags or branches does not**. Time travel
is `checkout_version` by version number, tag name, or `(branch, version)` tuple.

### Feature flags

The manifest carries `reader_feature_flags` and `writer_feature_flags` bitmaps; an
implementation seeing an unknown flag must return "unsupported" (`docs/src/format/table/versioning.md`):

| Bit | Flag | Meaning |
|-----|------|---------|
| 1 | `FLAG_DELETION_FILES` | Fragments may carry deletion files |
| 2 | `FLAG_STABLE_ROW_IDS` | Stable row IDs; fragments carry a row-id-to-address index |
| 4 | `FLAG_USE_V2_FORMAT_DEPRECATED` | Deprecated, unused |
| 8 | `FLAG_TABLE_CONFIG` | Table config present in the manifest |
| 16 | `FLAG_BASE_PATHS` | Dataset uses multiple base paths |

### Tags

A tag labels a specific version. Stored as JSON under `_refs/tags/`, always at the root
regardless of branch. Tag JSON: `branch` (optional; absent = main), `version`, `createdAt` /
`updatedAt` (RFC 3339), `manifestSize`, `metadata`. **Tagged versions are exempt from
`cleanup_old_versions()`** - to remove a tagged version you must delete the tag first
(`docs/src/guide/tags_and_branches.md:59-65`). Tag names: alphanumeric, `.`, `-`, `_`; no
`/`.

### Branches (v7)

Branches are Git-like parallel histories (`docs/src/format/table/branch_tag.md`). A branch
dataset is technically a **shallow clone** of its source, with version-specific files under
`tree/{branch_name}/` carrying their own `_versions/`, `_transactions/`, `_deletions/`,
`_indices/`. Branch metadata is JSON at `_refs/branches/{name}.json` (`/` URL-encoded as
`%2F`): `parentBranch`, `parentVersion`, `createAt`, `manifestSize`, `metadata`. Each branch
has its **own linear version history** - version numbers can overlap across branches, so use
`(branch_name, version)` tuples as global identifiers. `main` is the reserved default branch.
Branches hold references to data files - cleanup will not delete files still referenced by a
branch, so unused branches must be deleted to reclaim space.

`cleanup_old_versions(policy)` deletes old manifests, unreferenced data/deletion/index files.
A file referenced by no manifest is deleted only if >=7 days old unless `delete_unverified`
is set. `CleanupPolicy` knobs: `before_timestamp`, `before_version`, `delete_unverified`,
`error_if_tagged_old_versions` (default true), `clean_referenced_branches`,
`delete_rate_limit` (max delete requests/sec, to avoid S3 throttling). A newer
`Dataset::cleanup(policy)` API (new in v8, PR #7147) splits this into `explain()` (returns a
`CleanupExplanation` of what would be removed - a dry run) and `execute()`.

---

## 8. Row IDs and lineage

A row has two identifier forms (`docs/src/format/table/row_id_lineage.md`):

- **Row address** - the current physical location. A 64-bit value:
  `row_address = (fragment_id << 32) | local_row_offset`. Exposed as `_rowaddr`. Changes when
  data is reorganized by compaction or updates. Secondary indexes currently reference rows by
  row address.
- **Row ID** - a logical identifier. With **stable row IDs disabled (the default), the row ID
  equals the row address.** With stable row IDs enabled, each row gets a unique
  auto-incrementing u64 (exposed as `_rowid`) that stays constant for the row's lifetime even
  as physical location changes.

**Stable row IDs** must be enabled at dataset creation (manifest flag bit 2) - they cannot be
turned on later. Assignment uses a monotonic `next_row_id` counter in the manifest; on a
commit conflict the writer rebases by re-reading the latest counter. On update, Lance writes a
new physical row, keeps the same `_rowid`, marks the old physical row deleted, and the row-id
index maps `_rowid -> (new fragment, new offset)`.

Row-id sequences are stored per fragment as a `RowIdSequence` protobuf (`protos/rowids.proto`)
with five compact segment encodings (Range, RangeWithHoles, RangeWithBitmap, SortedArray,
Array) - bitpacked, stored inline when <200KB else in an external file. A row-id index is
built at table load by aggregating all fragments' sequences.

**Change data feed** (stable row IDs only): each row tracks `created_at_version` and
`last_updated_at_version`, queryable via SQL predicates on `_row_created_at_version` and
`_row_last_updated_at_version` to find rows inserted or updated between two versions.

---

## 9. Transactions and concurrency

Lance uses **MVCC**: each commit creates a new immutable version; concurrency is **optimistic
with automatic conflict resolution** (`docs/src/format/table/transaction.md`).

### 9.1 Commit protocol

A transaction commits by writing the next manifest file, which must be written exactly once
even under concurrent writers. This relies on atomic object-store primitives -
**rename-if-not-exists** or **put-if-not-exists** (conditional PUT). A `Transaction` protobuf
is written to `_transactions/{read_version}-{uuid}.txn` first, then the manifest. A
conflict-free commit is 1 read IOP + 2 write IOPs.

The `Transaction` message carries `read_version`, `uuid`, optional `tag`, a
`transaction_properties` string map, and a `oneof operation` - **15 operation types**
(`protos/transaction.proto`):

`Append`, `Delete`, `Overwrite`, `CreateIndex`, `Rewrite`, `Merge`, `Restore`,
`ReserveFragments`, `Update`, `Project`, `UpdateConfig`, `DataReplacement`,
`UpdateMemWalState`, `Clone`, `UpdateBases`.

Notable semantics: `Rewrite` reorganizes data without semantic change (compaction) and
changes row addresses; `Merge` adds columns and is "overly general" / high-conflict (prefer
`Rewrite`/`DataReplacement`/`Append`); `Update` has two modes - `REWRITE_ROWS` (optimal when
few rows change) and `REWRITE_COLUMNS` (optimal when few columns change across many rows);
`Clone` (shallow = metadata-only referencing the source via `base_paths`, or deep = native
object-store copy) can only be the first operation in a dataset so it never conflicts.

### 9.2 OCC retry and conflict resolution

`commit_transaction` computes `target_version = read_version + 1`, then runs a retry loop
(`rust/lance/src/io/commit.rs`). Each attempt loads concurrent transactions since
`read_version`, builds a `TransactionRebase`, and produces a rebased transaction. The retry
budget is `CommitConfig.num_retries`, **default 20** (settable via
`CommitBuilder::with_max_retries`). Backoff is slot-based, seeded from the first attempt's
observed commit latency. `num_retries == 0` triggers strict-overwrite mode (an `Overwrite`
not subject to any rebasing).

Three conflict outcomes:

- **Rebasable** - the transaction is transformed to incorporate the concurrent change while
  preserving intent, then retried automatically inside the commit layer.
- **Retryable** - cannot rebase but can be re-executed at the application level against the
  new version; returns a retryable conflict error.
- **Incompatible** - a fundamental conflict; the commit fails non-retryably.

Compatibility is per-operation and not bidirectional. Examples: `Append` is compatible with
almost everything including itself (conflicts only with `Overwrite`/`Restore`/
`UpdateMemWalState`); `Rewrite` is incompatible with `CreateIndex` by default because it
changes row addresses - **unless a fragment reuse index or stable row IDs are in use**, which
decouple logical identity from physical address and let those operations proceed without
conflict.

### 9.3 Commit handlers

The commit strategy is pluggable via the `CommitHandler` trait. Routing by URI scheme
(`rust/lance-table/src/io/commit.rs`):

| Scheme | Handler |
|--------|---------|
| `file` (non-Windows), `s3`, `gs`, `az`, `oss`, `cos`, `memory` | `ConditionalPutCommitHandler` |
| `file` (Windows) | `RenameCommitHandler` |
| `s3+ddb` | `ExternalManifestCommitHandler` (DynamoDB; requires the `dynamodb` feature) |
| anything else | `UnsafeCommitHandler` (no concurrency check; logs a warning) |

`ConditionalPutCommitHandler` is the current default for nearly all stores. It uses the
object store's native conditional write (`PutMode::Create`, i.e. `If-None-Match: *`):

- **Plain `s3://`** works for safe concurrent writes - S3 supports conditional PUT natively,
  so no external lock is needed.
- **S3 Express** (directory buckets) - auto-detected; routed the same way.
- **GCS / Azure** - native atomic writes.
- **`s3+ddb://`** remains available for environments where conditional writes are
  unavailable: a DynamoDB table coordinates commits via conditional writes
  (`?ddbTableName=...`). The `ExternalManifestStore` remembers `(uri, version) -> manifest
  path` and stages then finalizes the manifest in the object store.

Note: the `commit.rs` module doc still says the S3 default is `UnsafeCommitHandler` - that
comment is stale; the actual routing sends `s3://` to `ConditionalPutCommitHandler`.

---

## 10. MemWAL

**MemWAL is experimental.** It is an LSM-tree architecture layered on a normal Lance table to
absorb high-throughput streaming writes while keeping indexed read performance
(`docs/src/format/table/mem_wal.md`). The Lance table is the **base table**; on top sit
**shards** that take writes and are asynchronously merged back. The spec is an on-disk-layout
contract; in-memory buffering and scheduling are implementation-defined.

### Architecture

- **Shard** - the unit of write scale-out; exactly one active writer per shard. For
  primary-key tables, all rows of a PK must map to one shard (otherwise inter-shard merge
  order can resurrect stale rows). Append-only MemWAL tables may omit the primary key.
- **MemTable** - holds rows before flush; a list of Arrow record batches. **Generation
  numbers** start at 1 and increase; the base table is generation 0.
- **WAL** - durable storage of all MemTables in a shard, ordered by generation. Each WAL
  entry is an Arrow IPC stream file at `_mem_wal/{shard_id}/wal/`, named with bit-reversed
  64-bit binary (spreads sequential writes across S3 partitions). The writer epoch is in the
  Arrow schema metadata under `writer_epoch` for fencing.
- **Flushed MemTable** - itself a Lance table at `_mem_wal/{shard_id}/{hex}_gen_{i}/`, with
  pre-built indexes and a PK bloom filter.
- **Shard manifest** - source of truth per shard: `writer_epoch`, shard assignment, WAL
  pointers, generation trackers. Versioned, immutable, committed via put-if-not-exists.
- **MemWAL Index** - one per table, centralizing config, merge progress, index catchup, and
  shard snapshots. Tied to the `UpdateMemWalState` transaction.

### The appender/tailer/flusher model

Rust write path (`rust/lance/src/dataset/mem_wal/`):

- **`ShardWriter`** - the main per-shard writer interface. `ShardWriter::open` does
  epoch-based fencing once.
- **`WalAppender`** - the lowest-level primitive: single-entry synchronous atomic appends via
  put-if-not-exists, no buffering, owns the object store + epoch + position state.
- **`WalFlusher`** - buffers the WAL for durability.
- **`WalTailer`** - ordered reader of WAL entries from one shard.
- **`MemTableFlusher`** - flushes a frozen MemTable to a Lance file.

`ShardWriterConfig.enable_memtable` (default `true`) controls whether a MemTable layer is
maintained. With `enable_memtable == false` (**WAL-only mode**) no MemTable/index is
allocated and `index_configs` must be empty. Key defaults: `durable_write` true,
`max_wal_buffer_size` 10MB, `max_wal_flush_interval` 100ms, `max_memtable_size` 256MB,
`max_memtable_rows` 100,000, `max_unflushed_memtable_bytes` 1GB (backpressure budget - writes
block, never fail).

### In-memory HNSW

The in-memory MemTable can carry a **Lance-native HNSW vector index** (`MemIndexConfig::hnsw`,
new in v7 - PR #6795). HNSW is self-contained (no centroids/codebook needed); only the
distance metric is inherited from the base index. Also supported as MemTable indexes: BTree
scalar and FTS.

### Fencing and GC

Writer fencing is epoch-based, single-writer-per-shard: a writer increments `writer_epoch` in
the shard manifest; a writer whose local epoch is below the stored epoch is fenced and must
abort. Fenced writers' WAL entries are not discarded (they were valid when written) and are
replayed by the new writer. Flushed MemTables and their WAL files become GC-eligible only
after the generation is merged, all indexes have caught up, and no retained base version
references them. MemWAL GC is separate from `cleanup_old_versions`.

### Fragment reuse index

A related system index (`docs/src/format/index/system/frag_reuse.md`): it lets a compaction
**defer index remap**. Normally compaction must remap every index (so it conflicts with index
optimization); with a fragment reuse index, a compaction that removes fragments A,B and
produces C records the mapping, and at query time row addresses for A,B are translated to C.
This removes the compaction-vs-index-build conflict at the cost of a small per-load remap.

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
`Any`), `version`.

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

**Distance metrics** (`VectorMetricType`): `L2` (0), `Cosine` (1), `Dot` (2), `Hamming` (3).
SIMD kernels in `lance-linalg`; the `fp16kernels` feature compiles C SIMD kernels for fp16.

**Compression** (bytes per vector vs float32):

| Quantization | Storage | Ratio |
|--------------|---------|-------|
| FLAT | `dimension * 4` | 1x (exact) |
| SQ (8-bit) | `dimension` | ~4x |
| PQ | `num_sub_vectors` (one uint8 code per sub-vector) | ~`(dimension*4)/m` |
| RQ (RaBitQ, `num_bits` bits/dim) | `ceil(dimension * num_bits / 8)` + correction factors | ~32x at 1 bit |

**IVF_RQ requires the vector dimension to be divisible by 8** - enforced with the error
"vector dimension must be divisible by 8 for IVF_RQ" (`rust/lance-index/src/vector/bq/builder.rs`).
**RaBitQ is now multi-bit** (new in v8, PR #7038): `num_bits` is "in the range 1..=9"
(`docs/src/format/index/vector/index.md:255`). IVF_RQ always stores the 1-bit binary sign
code in `_rabit_codes`; "for `num_bits > 1`, the remaining `num_bits - 1` ex-code bits are
stored in `__ex_codes` instead of widening the binary code path"
(`index.md:282-284`), alongside `__add_factors_ex` / `__scale_factors_ex` correction columns.
A new `query_estimator` metadata field selects the distance-estimator layout: "`residual_query`
or `raw_query`. Missing values are read as `residual_query` for compatibility with released
1-bit IVF_RQ indexes" (`index.md:258`); raw-query search (PR #7078) adds an `__error_factors`
column "for raw-query lower-bound pruning" (`index.md:201`). The metadata schema also carries
`code_dim` (u32, the rotated-vector dimension). Per-row storage is `dimension/8 + 16` bytes
(8 for the row ID + 8 for the factors) **only at `num_bits=1`**
(`docs/src/guide/performance.md:416`); multi-bit adds the `__ex_codes` and ex-factor columns.

**Approx mode** (new in `v8.0.0-beta.10`, PR #7179). Vector search takes a public
`approx_mode` with three values - "`fast`, `normal`, and `accurate`" - to pick the
speed/accuracy tradeoff "when the backing index supports it" (RaBitQ today). "The public API
avoids exposing RaBitQ/HACC terminology" (commit `e25620710`). It threads through the Rust
scanner, the ANN proto, and Python query parsing; serialized as `VectorApproxMode approx_mode`
(`protos/ann.proto:16,45`) - a **breaking ANN-proto change**, so any consumer matching Lance's
serialized ANN query proto must regenerate. Multi-bit RaBitQ ex-code reranking also got
dedicated SIMD kernels (PR #7205, `rust/lance-index/src/vector/bq/ex_dot.rs`). **IVF_RQ now
defaults `target_partition_size` to 4096** (was the generic fallback, PR #7273).

On-disk layout (format V3): each vector index is two Lance files - an **index file**
(`index.idx`, the search structure: IVF metadata, HNSW graph) and an **auxiliary file**
(`auxiliary.idx`, quantized vector storage). HNSW construction defaults: `max_level` 7, `m`
20, `ef_construction` 150. The PQ codebook and the RaBitQ rotation matrix are stored as
tensors in the auxiliary file's global buffer.

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

### 11.2 Scalar indexes

`docs/src/format/index/scalar/`. Results are **exact** (BTREE, BITMAP, LABEL_LIST) or
**inexact / AtMost** (BLOOM_FILTER, NGRAM, ZONEMAP, RTREE).

| Index | For | Structure |
|-------|-----|-----------|
| BTREE | Range queries, sorted access, high-cardinality columns | Two-level: in-memory page lookup + on-disk sorted leaves, default 4096 rows/page |
| BITMAP | Low-cardinality columns, fast set membership | One bitmap (serialized `RowAddrTreeMap`) per distinct value |
| LABEL_LIST | Multi-value / tag columns | Built on a bitmap index; supports `array_has`/`_all`/`_any` |
| NGRAM | Substring matching | Overlapping trigrams (ASCII-folded, lowercased); query `contains` |
| ZONEMAP | Scan pruning / predicate pushdown | Per-zone min/max/null stats (default 8192 rows/zone); a *primary skipping structure* |
| BLOOM_FILTER | Probabilistic membership | Zone-based Split Block Bloom Filters (xxHash64; default 8192 items/zone, FPP 0.00057) |
| FM_INDEX | Substring / prefix / regex search on raw bytes | Compressed BWT index over raw byte arrays; built on the Segmented Index architecture (see 11.5). New in v8 |
| RTREE | 2D spatial pruning | See 11.4 |

NGRAM, ZONEMAP, and BLOOM_FILTER are newer additions. A JSON scalar index wraps another
index's details with a JSON path.

**FM-Index** (new in v8, `docs/src/format/index/scalar/fmindex.md`,
`protos/index.proto` `FMIndexIndexDetails`). The Ferragina-Manzini index is "a compressed
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

Tokenizer pipeline (`InvertedIndexParams`): a base tokenizer (`simple`, `whitespace`, `raw`,
`ngram`, `icu`, `jieba/*` for Chinese, `lindera/*` for Japanese) followed by token filters
(`RemoveLong`, `LowerCase`, `Stemmer`, `StopWords`, `AsciiFolding`). The `icu` tokenizer
(PR #6956) does ICU4X dictionary-based Unicode word segmentation with **bundled segmenter
data** - unlike jieba/lindera it needs no external language model
(`rust/lance-index/src/scalar/inverted/tokenizer.rs:390`, `docs/src/guide/tokenizer.md:1`). The
default base tokenizer remains **`simple`** (`tokenizer.rs:187`); a PR making ICU the default
(#6968) was reverted (#7006) because "ICU showed behavior differences that are too large for
the default path." Config keys:
`base_tokenizer`, `language`, `with_position` (store positions for phrase queries),
`lower_case`, `stem`, `remove_stop_words`, `ascii_folding`, ngram `min_gram`/`max_gram`/
`prefix_only`. 18 stemming/stop-word languages.

Query types (all inexact): `contains_tokens`, `match` (AND/OR), `phrase` (requires
`with_position`), `boolean` (must/should/must_not), `multi_match`, `boost`. FTS over JSON
documents breaks them into `path,type,value` triplet tokens.

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
covering segment's `fragment_bitmap`, flagging them for reindexing. After compaction, three
strategies handle changed row addresses: do nothing (segment stops covering those fragments),
rewrite segments with remapped addresses, or use a **fragment reuse index** (remap in memory
at read time). Stable row IDs avoid remapping entirely at the cost of a lookup.

The caller-facing API for folding new data in is `optimize_indices(&OptimizeOptions)`
(`rust/lance/src/index/api.rs:297`). `OptimizeOptions` (`rust/lance-index/src/optimize.rs:65`)
has three constructors: `append()` adds a new delta segment over the new fragments;
`merge(N)` folds the delta updates plus the latest N segments into one; `retrain()` rebuilds
the whole index from current data (v3 vector indices only). This is incremental maintenance -
distinct from dropping and recreating an index from scratch.

---

## 12. Distributed write and indexing

Lance exposes APIs for distributed work but provides **no scheduler** - the caller drives the
workflow (Ray and Spark integrations exist for the common cases).

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

`merge_existing_index_segments(...)` "currently supports vector, inverted, bitmap, BTree, and
zone map segments" (`distributed_indexing.md:109-110`); other scalar families can still be
committed without merging. **Vector model scope**: workers may share one trained IVF/PQ model
*or* use **independent segment models** - "each worker trains the IVF/PQ model for its own
`fragment_ids`. The resulting segments can be committed together as one logical index without
sharing centroids or codebooks" (`distributed_indexing.md:124`, PR #7148). Distributed builds
cover vector indexes, bitmap, segmented btree, segmented inverted (FTS), and zone map; the
`filtered_read` proto serializes the `FilteredReadExec` scan operator for plan-then-execute
distributed scans.

---

## 13. Object store

The object store is chosen by URI scheme (`docs/src/guide/object_store.md`): `s3://`,
`s3+ddb://` (S3 + DynamoDB commits), `gs://`, `az://` / `abfss://`, `oss://` (Alibaba),
`cos://` (Tencent), `tos://` (Volcengine, new in v8), `goosefs://` (feature-gated `goosefs`,
new in v8), `file://`, `memory://`, `shared-memory://` (in-memory, cross-component).
Config comes from environment variables or the `storage_options` map passed to
`lance.dataset` / `lance.write_dataset`.

`shared-memory://` is opt-in and distinct from `memory://`: `memory://` mints a fresh
in-memory store per call, while `shared-memory://<authority>` resolves - across object-store
registries, threads, and unrelated components in the same process - to one process-global
`InMemory` backend keyed by the URL authority. The pool is never evicted and grows for the
process lifetime; it is meant for tests and harnesses that coordinate a writer and an
independent reader. Pick distinct authorities for isolation
(`rust/lance-io/src/object_store/providers/shared_memory.rs:16`).

General options: `allow_http` (default false), `connect_timeout` (5s), `request_timeout`
(30s), `client_max_retries` (3), `download_retry_count` (3), `proxy_url`, `user_agent`.

Per-backend highlights:

- **S3** - `aws_region`, `access_key_id` / `secret_access_key` / `session_token`,
  `aws_endpoint` (for S3-compatible stores like MinIO - both region and endpoint required),
  `aws_server_side_encryption` (`AES256` / `aws:kms` / `aws:kms:dsse`) + `aws_sse_kms_key_id`.
  `AWS_PROFILE` is environment-only.
- **S3 Express** - directory buckets; auto-recognized via the `--x-s3` suffix, or set
  `s3_express: "true"`; reachable only from a same-region EC2 instance. Its listing is not
  lexically ordered, so the `latest_version_hint.json` mechanism accelerates latest-version
  lookup there.
- **GCS** - `GOOGLE_SERVICE_ACCOUNT` (JSON file) or `service_account_key`. Default HTTP/1;
  `HTTP1_ONLY=false` for HTTP/2.
- **Azure** - `account_name` / `account_key`, service principal, SAS tokens, managed
  identity, workload-identity federation.
- **Alibaba OSS** - `oss_endpoint` (required), `oss_access_key_id`, `oss_secret_access_key`.
- **Tencent COS** (`object_store.md:252`) - `cos://bucket/path` with `cos_endpoint`,
  `cos_secret_id`, `cos_secret_key`, and optional `cos_enable_versioning`; env vars are read
  from the `COS_` or `TENCENTCLOUD_` prefixes.
- **Volcengine TOS** (new in v8, `object_store.md:222-246`) - `tos://bucket/path` with
  `tos_endpoint` required (e.g. `https://tos-cn-beijing.volces.com`), plus `tos_region` and
  access-key options.
- **GooseFS** (new in v8, feature-gated `goosefs`, now documented at `object_store.md:306`) -
  `goosefs://host:port/path`; master address comes from `goosefs_master_addr` (HA-aware:
  `"addr1:port,addr2:port"`), the URL host, or default port `9200`. Optional keys:
  `goosefs_write_type` (`MUST_CACHE` / `CACHE_THROUGH` / `THROUGH` / `ASYNC_THROUGH`),
  `goosefs_auth_type` (`nosasl` / `simple`), `goosefs_auth_username`, `goosefs_block_size`,
  `goosefs_chunk_size` (`rust/lance-io/src/object_store/providers/goosefs.rs:24-61`).

**Base-aware access (v7).** `Dataset::object_store` takes an `Option<u32>` base id - `None`
for the primary store, `Some(base_id)` for an additional base. Caching/instrumentation
wrappers are applied per `store_prefix` and propagate to all base stores.

`latest_version_hint.json` (`{"version": N}` under `_versions/`) gives fast latest-version
lookup on stores where listing is not lexicographically ordered (S3 Express, local FS); it is
purely an optimization, always safe to delete, and skipped where listing is already ordered.
Disable globally with `LANCE_USE_VERSION_HINT=0`.

---

## 14. What changed (v7 -> v8)

The v7 tag line ran `v7.0.0-beta.1` through `v7.0.0-beta.17`, then `v7.0.0-rc.1` and
`v7.0.0`. The v7.1 line opened at `v7.1.0-beta.1`, continued through `v7.1.0-beta.4` and
`v7.1.0-rc.1`; the v7.2 line ran through `v7.2.0-beta.5`; then the **v8 line opened** and the
crates now pin `8.0.0-beta.14`. This section keeps the full v7 history below (still useful
context), the **v7.2.0-beta.5 -> v8.0.0-beta.9 delta** (the major-version boundary - the most
important part for a v8 reader), and finally the **v8.0.0-beta.9 -> v8.0.0-beta.14 delta**
(the current tag) at the very end.

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

### The v8.0.0-beta.9 -> v8.0.0-beta.14 delta (current tag)

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
  sections (`docs/src/guide/object_store.md:252,306`); GooseFS is no longer undocumented. See
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

---

## 15. Capability matrix

What Lance can and cannot do at `v8.0.0-beta.14`.

**Storage and format**

| Capability | Status |
|------------|--------|
| Local FS, S3 (+ S3-compatible), S3 Express, GCS, Azure, Alibaba OSS, Tencent COS, Volcengine TOS | yes |
| GooseFS (`goosefs://`) | yes (feature-gated `goosefs`) |
| In-memory store (`memory://`, `shared-memory://`) | yes |
| Multi-base storage (hot/cold, multi-region, shallow clone) | yes (`FLAG_BASE_PATHS`) |
| File format 2.1 (default), 2.0, legacy 0.1 (read-only) | yes |
| File format 2.2 (Map type, Blob v2) | yes, but `next` / unstable |
| Concurrent writes on plain `s3://` | yes (native conditional PUT) |
| Concurrent writes - GCS / Azure / local | yes |

**Data and schema**

| Capability | Status |
|------------|--------|
| Full Arrow type system, nested structs/lists | yes |
| Map type | yes (file format 2.2) |
| JSON type (JSONB), JSON path filtering and indexing | yes |
| Blob v2 - large binary, lazy `BlobFile` streaming, external URIs | yes (2.2) |
| Zero-copy add/drop/rename column (metadata-only) | yes |
| Type change / cast | yes (rewrites that column; drops its index) |
| Time travel, tags, branches | yes |
| Stable row IDs (must be enabled at creation) | yes (opt-in) |
| Change data feed | yes (stable row IDs only) |

**Indexes and search**

| Capability | Status |
|------------|--------|
| Vector ANN - IVF + FLAT/HNSW + FLAT/PQ/SQ/RQ (RQ multi-bit, `num_bits` 1..=9; `approx_mode` fast/normal/accurate) | yes |
| Distance metrics L2 / Cosine / Dot / Hamming | yes |
| Scalar - btree, bitmap, label-list, ngram, zonemap, bloom filter, FM-Index | yes |
| FM-Index substring / prefix / regex search on raw bytes | yes (segment-based) |
| Full-text search - BM25, multilingual tokenizers, phrase queries | yes (Lance-native) |
| Geo / RTree spatial index + geo UDFs | yes (`geo` feature) |
| Distributed index builds (vector, bitmap, btree, FTS, zone map) | yes (no scheduler) |
| SQL over datasets | via DataFusion (`LanceTableProvider`) |

**Concurrency and ops**

| Capability | Status |
|------------|--------|
| MVCC + optimistic concurrency, automatic rebase | yes |
| Pluggable commit handlers (conditional-put, DynamoDB, lock) | yes |
| MemWAL high-throughput streaming writes | yes, **experimental** |
| Two-phase distributed write | yes |
| Namespaces (Directory, REST) + DataFusion catalog bridge | yes |
| Compaction, version cleanup, fragment reuse index | yes |

**Not in Lance** - a query-builder API, an embedding registry, rerankers as an API, managed
Cloud/Enterprise tiers (those are LanceDB, a separate product); authentication / user
identity; a built-in cross-dataset join planner (use DuckDB/DataFusion on top); a metrics
dashboard.

---

## 16. Source map

Where to look in `lance-format/lance` at `v8.0.0-beta.14`.

| Topic | Path |
|-------|------|
| Format spec overview | `docs/src/format/index.md` |
| File format | `docs/src/format/file/{index,encoding,versioning}.md` |
| Table format | `docs/src/format/table/{index,layout,schema,transaction,versioning,branch_tag,row_id_lineage,mem_wal}.md` |
| Index spec | `docs/src/format/index/{index.md,vector/,scalar/,system/}` (scalar incl. `scalar/fmindex.md`) |
| User guide | `docs/src/guide/{blob,data_evolution,data_types,json,object_store,read_and_write,performance,tags_and_branches,tokenizer,distributed_write,distributed_indexing,migration}.md` |
| Integrations | `docs/src/integrations/{index,datafusion,pytorch,tensorflow}.md` |
| Protobuf schemas | `protos/{file2,table,transaction,rowids,index,ann,filtered_read,table_identifier}.proto` |
| Rust workspace | `rust/` (entry point `rust/lance/`) |
| Commit / OCC | `rust/lance/src/io/commit.rs`, `rust/lance-table/src/io/commit.rs` |
| MemWAL | `rust/lance/src/dataset/mem_wal/` |
| Indexes | `rust/lance-index/src/` |
| Object store | `rust/lance-io/src/object_store/` |

Auto-generated API docs and the language-agnostic namespace spec live in sibling repos under
`github.com/lance-format`. To refresh this reference, see the maintenance note in
`../SKILL.md`.
