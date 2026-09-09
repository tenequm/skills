# Lance v12 reference - file format (sections 1-4)

Part of the Lance v12 reference (`lance-format/lance@v12.0.0-beta.15`). Citations are `path:line`
relative to the repo root; build a permalink as
`https://github.com/lance-format/lance/blob/v12.0.0-beta.15/<path>`. Line numbers drift between
tags - treat them as approximate. Cross-references written as "section N" use the original
16-section numbering; `lance-reference.md` maps every number to its file.

This is the Lance *format and engine*. LanceDB (`lancedb/lancedb`) is a separate database
product built on top of Lance and is out of scope - but Lance is what it stores into, so this
reference is still authoritative for the format underneath it.

## Contents

- [1. What Lance is](#1-what-lance-is)
- [2. The crate workspace](#2-the-crate-workspace)
  - [2.1 Module reorganization in v11 (PRs #8020-#8026)](#21-module-reorganization-in-v11-prs-8020-8026)
- [3. File format](#3-file-format)
  - [3.1 Versions](#31-versions)
  - [3.2 Container layout](#32-container-layout)
  - [3.3 Structural encoding (2.1)](#33-structural-encoding-21)
  - [3.4 Compression](#34-compression)
  - [3.5 Blob encoding](#35-blob-encoding)
  - [3.6 Exact file identity: `ConcreteFileVersion`](#36-exact-file-identity-concretefileversion-v10-relocated-in-v11)
- [4. Data types](#4-data-types)

Other files: `format-table.md` (5-10), `indexes.md` (11-12), `ops.md` (13, 15, 16),
`changelog-v7-v12.md` (14).

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

26 crate directories under `rust/`. `[workspace.package]`: `version = "12.0.0-beta.15"`,
`edition = "2024"`, `rust-version = "1.91.0"` (MSRV; the pinned build toolchain in
`rust-toolchain.toml` is `1.97.0`, PR #7712), `license = "Apache-2.0"`,
`resolver = "3"` (`Cargo.toml:32-56`). `exclude = ["python", "java/lance-jni"]`. The crate set
is **unchanged from `v10.0.0-beta.7`** - the `Cargo.toml` inventory under `rust/` is
byte-identical between the two tags; the last addition was `lance-index-core` (PR #7713).
Module *layout inside* several crates changed substantially in v11 - see 2.1.

| Crate dir | Published name | Purpose |
|-----------|----------------|---------|
| `lance` | `lance` | **Public entry point.** `Dataset`, scanner, indexes, commits |
| `lance-table` | `lance-table` | Table format: `feature_flags`, manifest `format`, commit `io`, `rowids` |
| `lance-file` | `lance-file` | File format: file reader/writer, `LanceEncodingsIo`, MAGIC bytes |
| `lance-encoding` | `lance-encoding` | Structural encodings, compression. Internal - not for external use |
| `lance-index` | `lance-index` | Secondary indexes: scalar, vector, FTS, system |
| `lance-index-core` | `lance-index-core` | Shared index primitives extracted from `lance-index`. New in the 9.1/10.0 dev line (PR #7713) so lighter consumers can depend on core index types without the full index crate |
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
| `arrow-scalar` | `lance-arrow-scalar` | Arrow scalar with `Ord`/`Hash`/`Eq`. Pinned `=58.0.0` (tracks Arrow) |
| `arrow-stats` | `lance-arrow-stats` | Statistics accumulator (min, max, null_count, nan_count). Also pinned `=58.0.0` (`Cargo.toml:86-87`) |

`rust/examples` (`lance-examples`) holds non-published example binaries. The workspace
`members` array lists 26 paths; `rust/lance-datafusion` is part of the workspace as a
path dependency rather than an explicit member.

**Bindings.** Python: package `pylance` (`python/pyproject.toml`), built with maturin, imported
as `lance`; the Rust extension crate is `pylance` (`[lib] name = "lance"`); supports Python
**3.10-3.14** (3.9 dropped in v9, PR #7345, breaking; PyO3 abi3 floor raised to `abi3-py310`);
runtime deps `pyarrow>=14`, `numpy>=1.22`, `lance-namespace>=0.11.1,<0.12`. Java: an
SDK under `java/` (Maven `org.lance`), bridged to Rust by the `lance-jni` crate
(`java/lance-jni/`, excluded from the Rust workspace). Notable workspace deps at this tag
(`Cargo.toml`): `arrow 58.0.0` (`:85`), `datafusion 54.0.0` (`:132`), `geodatafusion 0.5.0`,
**`opendal 0.58.1`** (`:180`, was `0.57` at v10 - PR #7823), `object_store 0.13.2` (`:179`),
`object_store_opendal 0.58` (`:181`), `jieba-rs 0.10` (`:166`), `itertools 0.14` (`:165`),
`lance-namespace-reqwest-client 0.12.0` (`:76`, bumped from 0.11.1 by #8915), and
`blake3 1.8.5` (`:113`, backing the cache-key digest, section 9.4). The
`lance-namespace`/`-impls` crates publish at the workspace version (`12.0.0-beta.15`).

**The `lance-namespace` version is no longer a single number.** #8915 moved the *Rust* client to
`0.12.0` while the Java pin (`java/pom.xml:113,118`, `0.11.1`) and the Python pin
(`python/pyproject.toml:4`, `lance-namespace>=0.11.1,<0.12`) deliberately stay on 0.11: "The Java
and Python `lance-namespace` pins stay on 0.11, so their generated models still send `on` as a
bare string and rely on the promotion described above." Quote a language-specific pin, not one
number for all three.

**Dependency deltas in the v11 range.** Only five non-version-bump lines changed in the root
`Cargo.toml`: `opendal`/`object_store_opendal` 0.57 -> 0.58.1/0.58, and **`strum 0.26` plus
`goosefs-sdk =0.1.5` were removed outright**. GooseFS is now reached purely through opendal
(`goosefs = ["dep:opendal", "opendal/services-goosefs", "dep:object_store_opendal"]`,
`rust/lance-io/Cargo.toml:73`), with `goosefs-sdk` pulled transitively at 0.1.8; the
`[patch.crates-io]` opendal git fork was dropped from the root, Python, and Java manifests.
Separately, `lance-tokenizer` swapped **`rust-stemmers 1.2.0` -> `frostem`**
(`rust/lance-tokenizer/Cargo.toml:18`, PR #8183): the unmaintained crate's Greek implementation
"can retain stale UTF-8 byte offsets after shortening a word, then panic while slicing the
shortened string". `frostem` is generated from current upstream Snowball, and only the same 18
Snowball algorithms already exposed by the `Language` API are enabled - the inverted-index
protobuf details and capability versions are unchanged. `Cargo.lock` also gained
`opendal-http-transport-reqwest` and dropped `crc32c`.

### 2.1 Module reorganization in v11 (PRs #8020-#8026)

If you depend on anything below the `lance` crate, this is the largest source-compatibility
event in the v10 -> v11 range. Six PRs moved the file-format reader/writer machinery out of
version-agnostic modules and into per-version ones, with **no re-exports left behind**:

| Was (v10) | Is (v11) |
|-----------|----------|
| `lance-encoding::version` (`LanceFileVersion`, `LEGACY_FORMAT_VERSION`, `V2_FORMAT_2_*`, `resolve`, `is_unstable`, ...) | `lance-file::version` - the module file is **deleted** from `lance-encoding` (#8026) |
| `lance-file::previous::*` | `lance-file::versions::v1::*` (#8020) |
| `lance_io::encodings` (`Encoder`, `Decoder`, `AsyncIndex`, `read_binary_array`, `read_fixed_stride_array`, `bytes_to_array`, ...) | **removed** (#8020) |
| `lance-encoding::previous` public encoder surface (`ArrayEncoder`, `ArrayEncodingStrategy`, `CoreFieldEncodingStrategy`, `EncodedArray`, `BitpackedArrayEncoder`, `FixedSizeBinaryEncoder`, ...) | **removed**; per-version `lance-file::versions::v2_{1,2,3}::compression` (#8021) |
| `struct FileWriter` with `try_new` / `new_lazy` / `create_file_with_batches` | `enum FileWriter { V2_0, V2_1, V2_2, V2_3 }` (`rust/lance-file/src/writer.rs:52,57`); construct via `versions::{create_writer, create_lazy_writer, encode_self_described_batch, encode_mini_batch}` (#8023) |
| `ReaderProjection::{from_field_ids, from_whole_schema, from_column_names}` | free fns `reader_projection_from_*` in `lance-file::versions` (`versions/mod.rs:119,154`) (#8024) |
| `FileReader::version() -> LanceFileVersion`; `FileReader::supports_projection` | `-> ConcreteFileVersion` (`reader.rs:2259`); `supports_projection` **removed** (#8024) |
| `Dataset::storage_version_or_default() -> LanceFileVersion`; `open_writer`; public `do_write_fragments` | `-> ConcreteFileVersion` (`write.rs:458`); `open_writer` **removed**; `do_write_fragments` crate-private (#8025) |

`FileWriterOptions` also lost `encoding_strategy` and `format_version`, and
`initialize_with_external_metadata` was renamed `initialize_with_external_columns`.
`CommitBuilder::with_storage_format(LanceFileVersion)` keeps its public signature (it now
`.into()`s), and `determine_file_version` stopped panicking on a failed `size()` call.
Physically, `lance-file/src/previous/` and `lance-encoding/src/previous/` (22 files) are gone,
replaced by `lance-file/src/versions/{v1,v2_0,v2_1,v2_2,v2_3}/` and
`lance-encoding/src/array_encoding/{logical,physical}/` plus a new `strategy.rs`.

Two more encoder-facing breaks rode along: `MiniBlockCompressor::compress` gained a
`MiniBlockCompressionContext` parameter (#8038 - "It intentionally changes no codec selection or
persisted bytes"), and `DataBlockBuilder::append` became fallible with `DataBlockBuilderImpl`
made private (#8172), so malformed variable-width offsets now return `Error::CorruptFile`
instead of panicking or yielding garbage - a file that previously "read" may now error.

**Published vs tagged.** crates.io carries only final releases - `lance 9.0.1` (2026-08-06) is
the newest, preceded that same day by the sibling patch finals 8.0.1, 7.1.0, 6.1.0, 4.0.2, and
3.0.2. **No 10.x or 11.x version, and no pre-release of any kind, is published.** Beta and rc
tags exist in git only (beta artifacts go to fury.io), so building against `v12.0.0-beta.15`
means a git dependency, not a registry one.

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
| `2.1` | 0.38.1 | previous default | Adaptive structural encodings; better integer/string compression; nulls in struct fields; better nested random access |
| `2.2` | - | **current default** (`stable`) | Map type, Blob v2, `VariablePackedStruct`, larger mini-blocks |
| `2.3` | - | unstable (`next`) | The current `next` alias target. Ships **sparse structural pages** (PR #7889) - the first 2.3-specific encoding; **auto-selected** by the 2.3 writer under a budget heuristic (PR #7756), or forced via `lance-encoding:structural-encoding=sparse` |

`stable` resolves to **2.2** as of `v12.0.0-beta.15` (#8657); `next` resolves to the latest
unstable version. The enum declaration order is
`Legacy, V2_0, V2_1, Stable, V2_2 (#[default]), Next, V2_3`, with `Stable => 2.2` and
`Next => 2.3` (`rust/lance-file/src/version.rs:18-45` - the module **moved out of
`lance-encoding` in v11**, PR #8026, with no re-export). No 2.4 or new variant exists at this
tag.

`#[default]` moved from `V2_1` to `V2_2` in the same PR, and the default reaches new datasets
through `impl Default for DataStorageFormat { fn default() -> Self { Self::new(stable_file_version()) } }`
(`rust/lance-table/src/format/manifest.rs:677-680`). Upstream's framing was that the code lagged
the intent: "Lance 2.2 is the current stable file format, but the centralized release policy and
enum default still resolve new datasets to 2.1." The docs were **not** updated with the change -
`docs/src/format/file/versioning.md` is byte-identical across the range and still describes
`stable` only as an "Alias for the default version for new datasets in the Lance release you are
running", so read the code, not the table, for what `stable` means at a given tag.

Two consequences that surprise readers: (1) **`next` resolves to 2.3, not 2.2** - writing with
`next` produces a 2.3 file; (2) the code does **not** flag 2.2 as unstable, and now writes it by
default.

**`is_unstable()` is not an ordering comparison.** An earlier form of this note read
`is_unstable() = self >= Next`, which describes no recent tag and could not compile:
`LanceFileVersion` derives only `Debug, Default, Clone, Copy, PartialEq, Eq` - it lost
`PartialOrd`/`Ord` in #8027/#8028. The selector delegates
(`pub const fn is_unstable(self) -> bool { self.resolve().is_unstable() }`, `version.rs:71-74`)
and the concrete version matches exactly
(`pub const fn is_unstable(self) -> bool { matches!(self, Self::V2_3) }`, `version.rs:147-150`).
As of v9 the docs version table (`docs/src/format/file/versioning.md:18-27`) agrees: it lists
`2.3 (unstable)` and no longer labels 2.2 unstable (2.2 now reads "Adds support for newer
nested type/encoding capabilities (including map support) and 2.2-era storage features"). As
of v9.1 the 2.3 row reads **"Adds sparse structural pages and other experimental encodings"**
- 2.3 is no longer a placeholder: `V2_3` references in `lance-encoding` jumped 6 -> 59 with the
sparse-page encoding (`rust/lance-encoding/src/encodings/logical/primitive/sparse.rs`, PR
#7889). **Sparse pages** represent flat or nested Arrow structure directly as slot-domain
mappings instead of dense repetition/definition events (`docs/src/format/file/encoding.md:330`);
`structural-encoding` accepts `miniblock`, `fullzip`, or `sparse` (`sparse` requires 2.3).
2.2 still carries Map / Blob v2 / `VariablePackedStruct`.

**Sparse auto-selection (v10, PR #7756).** Sparse is no longer opt-in only. "Without an explicit
structural encoding, the Lance 2.3 writer selects sparse only when the dense mini-block
repetition/definition budget would split the page or one top-level row exceeds that budget, and
only when the value path is supported by the sparse writer"
(`docs/src/format/file/encoding.md:373-376`). Consequences worth knowing: "Unsupported sparse
value paths, including dictionary values and variable-width packed structs, retain their dense
behavior" (`encoding.md:378`), and "Lance 2.2 and earlier writers never select sparse"
(`encoding.md:375-376`). The field-metadata table reworded the key from *Select* to **"Force a
structural encoding; `sparse` requires Lance 2.3"** (`encoding.md:694`) - because leaving it
unset no longer means "never sparse". The policy decision is kept out of serialization: it
"adds no wire-format fields" (PR #7756).
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
  at init time. Default 4096 values/block (`LANCE_MINIBLOCK_MAX_VALUES`), **tunable up to
  32k** via that env var since v9 (PR #7356). 2.2 adds larger chunks (>=64KB) via
  `has_large_chunk`.
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

**The logical Arrow schema became documented contract in v12** (#8929, `v12.0.0-beta.11`).
"A blob v2 field is tagged with `ARROW:extension:name = "lance.blob.v2"`", and writers accept
two logical struct shapes - Minimal and Complete (`blob.md:68-71`). The row-level invariants are
now spelled out: "Every non-null row must set exactly one of `data` and `uri`. For the complete
shape, `position` and `size` must either both be set or both be null, a range requires `uri`, and
an explicit range must have `size > 0`" (`blob.md:78-81`).

The guarantee that matters for round-tripping is preservation: "Lance preserves an accepted
logical shape, including child fields, nullability, and metadata, across create, append, and
merge-insert writes; descriptor scans still return the compact stored descriptor shape"
(`blob.md:83-85`). So the shape you write is the shape you read back - except through a
descriptor scan, which always yields the compact stored form.

**Four read paths** (`docs/src/guide/blob.md:6-7,177-188`). `read_blobs` is the **primary** API -
"For data loaders and batch processing that need complete byte payloads, use `read_blobs`" - it
returns `List[Tuple[int, Optional[bytes]]]` (`(row_address, payload)`) and "plans and executes
batched blob reads through Lance's scheduler." `take_blobs` returns lazy `BlobFile` handles for
streaming/seeking/partial reads (`with blob as f: f.read()`) - "Do not wrap `take_blobs` in your
own thread pool just to call `read()` ... Use `read_blobs` instead." **`read_blob_ranges`**
(v10) returns `List[Tuple[int, int, Optional[bytes]]]` for "selected byte ranges from multiple
rows without materializing complete blobs" (`blob.md:197`) and "accepts the same selector kinds
through its required `selector` argument" (`blob.md:206-207`).
`scanner(..., blob_handling="all_binary")` reads blob columns as Arrow binary columns in a scan
/ `pyarrow.Table`; `LanceTableProvider::with_blob_handling` is the DataFusion-side equivalent
(v10). The selector-taking APIs take **exactly one** of `ids` (logical row-id), `indices`
(positional within a snapshot), or `addresses` (physical, debug). A blob v2 column can mix
inline bytes, an external URI, an external URI slice (`Blob.from_uri(uri, position=, size=)`),
and null - enabling many payloads packed into one container file referenced by
`(position, size)` slices.

**Blob v2 fields nest** (v11): "Blob v2 fields can be nested inside structs and variable-length
lists. Blob-aware scans preserve the surrounding nested layout" (`docs/src/guide/blob.md:137-138`).
v11 also taught `FileFragment::update_columns` to handle blob-v2 columns via their descriptor
representation (#8344), and added `BlobFile.read_ranges(ranges) -> list[bytes]` (#8319) for
vectored reads - "The underlying physical reads may be reordered, coalesced, or split for
efficiency."

**Null selections are preserved (v10, BREAKING, PR #7903).** This is the change that triggered
the major bump. "Blob selection APIs preserve logical result cardinality. `read_blobs()` and
`take_blobs()` return one element per selected row, and `read_blob_ranges()` returns one element
per request. A null blob is returned as `None`; a valid empty blob remains a non-null empty
payload or zero-length `BlobFile`" (`docs/src/guide/blob.md:247-250`). Previously null blobs were
**omitted**, so any caller zipping results positionally against its inputs was silently
misaligned whenever a null appeared. Signature changes:

| Surface | Before | After |
|---------|--------|-------|
| Rust `take_blobs` / `_by_addresses` / `_by_indices` | `Result<Vec<BlobFile>>` | `Result<Vec<Option<BlobFile>>>` (`rust/lance/src/dataset.rs:1757,1790,1817`) |
| Rust `ReadBlob::data`, `ReadBlobRange::data` | `Bytes` | `Option<Bytes>` (`rust/lance/src/dataset/blob.rs:1580,1642`) |
| Python `take_blobs` | `List[BlobFile]` | `List[Optional[BlobFile]]` |
| Python `read_blobs` | `List[Tuple[int, bytes]]` | `List[Tuple[int, Optional[bytes]]]` |
| Java `takeBlobs` | non-null elements | "null blob values are represented by null elements" |

Related v10 blob fixes: `merge_insert` no longer crashes with a `LargeBinary vs Struct schema
mismatch` when the source omits blob columns (PR #7615); storage-2.1 compaction no longer
surfaces a surviving null as a valid zero-length descriptor (PR #8070) and no longer classifies
an inline blob with `position=0/size=0` as null (PR #7965); blob selection by stable row ID no
longer drops deleted/unknown IDs or misattributes bytes to the wrong `request_index` (PR #8003).

**Auto-tiering.** Blob v2 tiers payloads by size (`docs/src/guide/blob.md:373`): "by default it
keeps payloads under 16 KiB inline, packs mid-sized payloads into shared `.blob` sidecars, and
gives payloads over 2 MiB their own dedicated `.blob` file." The blob column avoids the
row-rewrite write amplification that inline binary incurs on compaction/update. The cutoffs are
**per-column configurable** (PR #7269): field metadata `lance-encoding:blob-inline-size-threshold`
/ `lance-encoding:blob-dedicated-size-threshold` (Python `inline_size_threshold` /
`dedicated_size_threshold`), plus `lance-encoding:blob-pack-file-size-threshold`
(`rust/lance-arrow/src/lib.rs:69`; Python `blob_pack_file_size_threshold` on `write_dataset`,
PR #7322) which caps how large a shared packed `.blob` file grows before a new one starts.
Appends that specify a different threshold than the existing column are **rejected**, not
silently ignored.

### 3.6 Exact file identity: `ConcreteFileVersion` (v10; relocated in v11)

v10 split the file-version type in two (PR #7879). `LanceFileVersion` remains the user-facing
type carrying release *selectors* - `stable`, `next` - while `ConcreteFileVersion` is "the exact
persisted identity of a Lance file format ... this type cannot represent release selectors such
as `stable` or `next`. **Exact versions deliberately have no ordering because format
capabilities are not implied by release order.**" Variants: `V1, V2_0, V2_1, V2_2, V2_3`.

**In v11 both types live in `rust/lance-file/src/version.rs`** - `LanceFileVersion` at `:25`,
`ConcreteFileVersion` at `:117`. `lance-encoding::version` was deleted outright (PR #8026) with
no re-export, on the rationale that "`Stable` and `Next` are file-writing selectors, not
encoding mechanisms". A crate that reached `LanceFileVersion` through `lance-encoding` alone no
longer compiles and must add a `lance-file` dependency. Two methods were **removed** from
`LanceFileVersion` back in v10 (BREAKING): `try_from_major_minor` and `to_numbers`; their job
moved into `ConcreteFileVersion`'s persisted codecs.

`ConcreteFileVersion` also spread outward in v11: `FileReader::version()` and
`determine_file_version` now return it, `Dataset::storage_version_or_default()` returns it, and
the whole reader/writer construction path is typed on it (2.1).

Manifest version strings reject aliases: "Public selector aliases such as `legacy`, `0.3`,
`stable`, and `next` are intentionally rejected because manifests only store canonical exact
versions" (`version.rs:139-141`).

The `DataFile` wire mapping is now a locked contract (`version.rs:72-92`). Encode is exact;
decode accepts a wider set for historical files:

| Version | Encodes to | Decodes from |
|---------|-----------|--------------|
| `V1` | `(0,2)` | `(0, 0..=2)` |
| `V2_0` | `(2,0)` | `(0,3)` or `(2,0)` |
| `V2_1` | `(2,1)` | `(2,1)` |
| `V2_2` | `(2,2)` | `(2,2)` |
| `V2_3` | `(2,3)` | `(2,3)` |

Note the dual representation of 2.0: the **standard footer** encodes it as `(0,3)` while the
**embedded / self-described footer** uses `(2,0)`, and both are now pinned by checked-in
byte-exact fixtures with SHA-256 locks - "The compatibility tests require each stable writer to
reproduce its fixture byte-for-byte and each reader to open and read the baseline file"
(`rust/lance-file/test_data/exact_versions/README.md`, PR #8019). 2.3 is excluded from the
fixture set because it is unstable. Existing wire mappings, legacy empty-manifest recovery,
reader compatibility, and mixed-version rejection are otherwise unchanged.

A related policy note now lives in the repo's `AGENTS.md`: legacy is frozen - "Implement new
features in the current format and write paths. Do not extend legacy writers, retrofit new
capabilities into legacy readers, or reuse legacy implementations as the foundation for new
code" (PR #8039).

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
  read back as Arrow's JSON type. Query functions: `json_extract` (JSONPath), `json_get`
  (returns JSONB for chaining), `json_get_string/int/float/bool`, `json_exists`,
  `json_array_contains`, `json_array_length`. Indexable: a scalar index on a JSON path, or an
  inverted (FTS) index over JSON contents (`docs/src/guide/json.md`).
  **"Filter-only" is a hard limitation, not a stylistic note**: "JSON functions are currently
  only available for filtering, not for projection in query results" (`guide/json.md:433`). You
  cannot `SELECT json_get_string(col, 'k')` - extract the whole JSON column and unpack it
  client-side, or materialize the field into its own column at write time if you need it
  projected or grouped.
- **Blob** (`lance.blob.v2` extension type) - large binary objects, lazy file-like loading
  (section 3.5). Migrating an existing dataset is a rewrite, not an alter: the guide has a
  dedicated "Rewrite to a New Blob v2 Dataset" procedure (`docs/src/guide/blob.md:377`) plus a
  troubleshooting section (`:404`). Note Blob v2 needs file format **2.2**, while the default is
  2.1 - so a dataset created without an explicit `data_storage_version` cannot take it, and the
  version is fixed at creation.
- **ML extension arrays** (`docs/src/guide/arrays.md`) - `BFloat16` (16-bit ML float,
  `lance.arrow.BFloat16Array`), `ImageURI`, `EncodedImage` (jpeg/png on disk),
  `FixedShapeImageTensor`.
