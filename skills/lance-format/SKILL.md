---
name: lance-format
description: Deep reference for Lance v13 columnar format, its Rust crates, and pylance - file encodings, table format, indexes, schema evolution, time travel. Use when building on the Lance crates or reading .lance datasets, not the LanceDB product.
metadata:
  version: "0.20.0"
  categories: "development, integrations"
  topics: "lance, columnar-format, vector-search, rust, lakehouse"
  upstream: "lance-format/lance@v13.0.0-beta.4"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/lance-format
    emoji: "🗄️"
---

# Lance v13 reference

Lance is an open columnar format for multimodal AI - "a columnar data format that is 100x
faster than Parquet for random access." It is not one format but a stack of interoperating
specs: a **file format**, a **table format**, **index formats**, **catalog specs**, and a
**namespace client spec**. The Rust workspace at `lance-format/lance` implements all of them
plus Python (`pylance`) and Java bindings.

This skill tracks **`v13.0.0-beta.4`** (the `lance-format/lance` git tag), the current
development frontier; **`v12.0.0`** is the stable pin, released 2026-09-17. Pin against tags, not
`main` - Lance ships beta tags every few days and `next`-format encodings can change. Version
landscape below.

Three layers of reference, load what the task needs:

- **The deep reference** - any concrete schema, parameter, proto, or constraint. Split by topic:

  | File in `references/` | Covers | Sections |
  |------|--------|----------|
  | `format-file.md` | What Lance is, the 26 crates, file format, data types | 1-4 |
  | `format-table.md` | Dataset layout, manifests, fragments, schema evolution, versioning/tags/branches, row IDs, transactions + OCC, MemWAL | 5-10 |
  | `indexes.md` | Vector / scalar / FTS / geo indexes, distributed builds | 11-12 |
  | `ops.md` | Object store, capability matrix, source map | 13, 15, 16 |
  | `changelog-v7-v13.md` | The full v7 -> v13 delta | 14 |

  Cross-references written as "section N" resolve through `references/lance-reference.md`.
- `references/performance.md` - ALL performance guidance. Part A routes to the official text and
  adds the source-derived changes upstream has not documented; Part B is field-verified
  remote-storage practice. Load for any performance, tuning, maintenance-cost, or "why is this
  slow" question.
- `references/docs/` - a **verbatim mirror of the official docs** (`docs/src` at the tracked
  tag): every guide, quickstart, and format spec, unedited. Load when you need the full official
  text. Directory map below.

`references/maintenance.md` covers refreshing this skill against a new upstream tag.

## Lance vs LanceDB

These are two different things and conflating them produces wrong answers.

- **Lance** - the format and engine. The `lance-format/lance` repo; the `lance` /`lance-*`
  Rust crates; `pylance`. It gives you datasets, the file/table format, indexes, commits,
  scans. Consumed directly by DuckDB, Polars, Ray, Spark, PyTorch, DataFusion, or your own
  Rust/Python code. **This skill is about Lance.**
- **LanceDB** - a separate database *product* (`lancedb/lancedb`) built on top of Lance. It
  adds a query-builder API, an embedding registry, rerankers-as-API, multi-language SDK
  parity, and managed Cloud / Enterprise tiers. Not covered here.

**The wider ecosystem** (separate repos, own version lines, none covered here): Flink streaming
writes (`lance-flink`), PostgreSQL reads via `pglance`, a Cypher graph engine (`lance-graph`), a
dataset browser (`lance-data-viewer`), agentic context management (`lance-context`), and
namespace catalogs for Hive, Polaris, Gravitino, Unity Catalog, and AWS Glue.
The canonical docs site is **`lance.org`**. Generated per-language SDK docs live at
`lance-format.github.io/lance-python-doc` for Python and
[javadoc.io](https://www.javadoc.io/doc/org.lance/lance-core/latest/index.html) for Java - the
matching `lance-format.github.io/lance-java-doc` path 404s.

Linking the `lance` crate in `Cargo.toml` means you are using Lance directly - use this skill.
For LanceDB internals, the storage layer underneath is still Lance, so this skill remains the
authority for the format itself.

**The wrapper can hide format features.** LanceDB's `create_table` cannot enable stable row IDs;
only pylance's `write_dataset(enable_stable_row_ids=True)` can. If a format-level capability
matters to your design, check whether the wrapper exposes it before assuming the underlying
format settles the question - and reach for `pylance` directly when it does not.

## The crate workspace

26 crate directories under `rust/`. **`lance` is the public entry point** - `Dataset`, scanner,
indexes, commits; everything else (`lance-table`, `lance-file`, `lance-encoding`, `lance-index`,
`lance-io`, `lance-core`, `lance-datafusion`, `lance-linalg`, `lance-namespace*`, ...) is a layer
beneath it. Edition 2024, MSRV 1.91.0, arrow 58, datafusion 54; Python bindings need 3.10+. Full
table with roles, versions, and every workspace dep in `references/format-file.md` section 2.

**If you depend on anything below `lance`, v11 will break you** - PRs #8020-#8026 deleted
`lance-encoding::version` with no re-export (`LanceFileVersion` and `ConcreteFileVersion` both
live in `lance-file::version` now), removed `lance_io::encodings` and the `previous` namespaces,
and gave each current format its own `versions/v2_{0,1,2,3}` module. Section 2.1.

The transaction code moved too (#8053/#8054/#8056): `rust/lance/src/dataset/transaction.rs` is
**deleted**, replaced by a `rust/lance-table/src/transaction/` module tree (`builder`,
`conflicts`, `operation`, `proto`, `manifest_build`, `validate`, `index_maintenance`,
`row_version`, `update_map`). A `lance::dataset::transaction` shim still re-exports `Operation`,
`Transaction`, `TransactionBuilder`, `RewriteGroup`, `UpdateMap` and friends, so the common
surface is unbroken - but a symbol the shim omits, or a citation of the old path, needs
retargeting.

## File format versions

The file format carries a single major.minor version. `data_storage_version` is set per dataset
at creation - but as of `v12.0.0` it is **no longer fixed once the dataset exists**. It is the
*default* for writes that omit a target, not a summary of what the dataset holds: "Create and
overwrite establish this default; append, update, merge-insert, and compaction do not change it."
An existing V2 dataset can take `"2.0"`, `"2.1"`, `"2.2"` or `"2.3"` per operation without
rewriting its other files (#8582-#8585), so one dataset can hold data files at several exact V2
versions. **V1 and V2 still cannot be mixed.** Section 3.

| Version | Status | Notes |
|---------|--------|-------|
| `0.1` (`legacy`) | read-only | Original format; no longer writable |
| `2.0` | stable | Removed row groups; null support for lists/FSL/primitives |
| `2.1` | previous default | Adaptive structural encodings; better integer/string compression; nulls in struct fields; better nested random access. Was the default from Lance 5.0.0 until `v12.0.0-beta.15` |
| `2.2` | **current default** (`stable`) | Map type, Blob v2, `VariablePackedStruct`, larger mini-blocks. Required for Map and Blob v2 |
| `2.3` | unstable (`next`) | The current `next` alias target (`V2_3` in the enum). Ships **sparse structural pages**, which the 2.3 writer now auto-selects under a rep/def budget heuristic |

**`stable` now resolves to 2.2, not 2.1** (#8657, beta.15), and `2.2` is the enum `#[default]`,
so a dataset created without an explicit `data_storage_version` is written as 2.2. The change
reaches new-dataset creation through `DataStorageFormat::default() -> stable_file_version()`,
and Python's `write_dataset` inherits it because its default routes through `stable`. **The docs
were not updated with it** - `format/file/versioning.md` still only says `stable` is an "alias
for the default version", so the code is the authority here. `next` resolves to 2.3. Pin an
explicit number for deterministic behavior across builds.

2.3 is the only version the code flags unstable; 2.2 never was, and is now what you get by
default. The release *selectors* (`LanceFileVersion`) are a type distinct from the persisted
identity (`ConcreteFileVersion`). Details, plus the sparse auto-selection rules, in
`references/format-file.md` sections 3.1 and 3.6.

## Version landscape

The major is bumped by a bot, not a human: `ci/publish_beta.sh` re-roots at `MAJOR+1` whenever
any PR since the release root carries the GitHub `breaking-change` label - the marker is the
**label**, not a conventional-commit `!`. A major bump therefore means "some labeled breaking
change landed", not a redesign, and a `!` without the label bumps nothing. It has now fired on
**four consecutive lines**, which is why **none of `v9.1.0`, `v10.1.0`, `v11.1.0`, or `v12.1.0`
was ever released**. The 12.1 line is the clearest case: `main` took a
`chore: bump main to 12.1.0-beta.0` commit, and four commits later the bot re-rooted to 13, so
`release-root/12.1.0-beta.N` and `release-root/13.0.0-beta.N` are the **same base commit**
(`c3c9632a2`) and no `v12.1.0-beta.*` tag exists.

Three recent lines **did** ship a final: `v10.0.0` (2026-08-08), `v11.0.0` (2026-08-30) and
`v12.0.0` (2026-09-17). Each sits on a stabilization branch that is **not an ancestor of `main`**
- normal for a Lance final, not a sign the release is unofficial.

| Major | Its breaking theme |
|-------|--------------------|
| **v13** (current, `v13.0.0-beta.4`) | `WriteParams` gained `file_writer_options` (#9192 - the one labeled PR that re-rooted the major); lazy page-metadata init changed the `StructuralFieldScheduler` signature and the metadata **cache key shape** (#7465); `json_extract`/`json_get` no longer route to JSON indices (#9101). Delta below |
| **v12** (`v12.0.0`, 2026-09-17) | `WrappingObjectStore` implementors must add `wrap_paginated` (no default); MemWAL `ShardManifestStore` renamed and narrowed; `lance-namespace` returns response objects; external stores gained predecessor-conditioned publication; namespace merge-insert keys became a list; the caller-provided Writer / `open_part` flow was removed (#9072). Unlabeled but bigger: `stable` -> 2.2 and the IVF_RQ 5-bit default. Net-new format capability: mixed data-file versions. Delta below |
| **v11** (`v11.0.0`, 2026-08-30) | Fragment ids became a dataset-lifetime high-water mark; large internal reorganization of `lance-file` / `lance-encoding`; the first new manifest feature flag since v7 - which was then **reallocated before the final**. Net-new: covering indexes, `merge_insert` `write_mode`, row-address prefilter. Delta below |
| **v10** | Blob APIs preserve null selections; cache keys became opaque BLAKE3 digests (every warm or persisted cache cold-misses, no legacy fallback); async `create_remapper`; MemWAL renamed generation -> SSTable, merge -> compaction (wire-compatible, symbol-breaking) |
| **v9.1** (never released; renamed into v10) | FTS/inverted creation took a `block_size` param. Net-new: Data Overlay Files (cell-level updates without base-file rewrite, unstable + env-gated), sparse structural pages, `lance-index-core` |
| **v9** | Python 3.9 dropped; `alter_columns` fails fast when casting an indexed column; FM-Index proto rename made existing FM indexes unreadable; FTS/inverted defaults to on-disk format v2 |
| **v8** | All index builds unified onto one segment-based lifecycle. Net-new: `lance-derive`, FM-Index, multi-bit IVF_RQ, public `approx_mode`, TOS + GooseFS object stores |
| **v7** | MemWAL, branches, the geo/RTree index, the `lance-select` crate, ICU FTS |

**`v12.0.0` is the stable pin** and what GitHub Releases marks `Latest`. crates.io carries
**finals only** (newest `lance 12.0.0`, no 13.x); PyPI `pylance` is likewise at `12.0.0`. So a
beta pin means a git dependency - beta wheels publish to fury.io instead, under the renamed org
(`https://pypi.fury.io/lance-format`), which currently carries `pylance-13.0.0b1` through `b4`.

Full per-tag deltas with every PR citation: `references/changelog-v7-v13.md`.

## The v11 delta

357 commits from `v10.0.0-beta.7` to the `v11.0.0` final, with **16 `breaking-change`-labeled
PRs** (14 through `beta.16`, plus #8407 and #8535 in the final). Most structural invariants held:
**26 crates**, **16 transaction ops**, `CommitConfig.num_retries` **20**, arrow 58 / datafusion 54,
MSRV 1.91.0, Edition 2024, Python 3.10+ - and all of them still hold at `v13.0.0-beta.4`.

**`references/changelog-v7-v13.md` has the full delta** - every PR citation, the per-tag
breakdown from v7 forward, the Python/Java surface, and each correctness fix with its trigger
condition. Load it for any "what changed / will this break me" question. What follows is only
what bites hardest.

**Five things that break you at v11:**

- **Fragment ids are a dataset-lifetime high-water mark** (#8206) - a *format* invariant, not
  just an API. Overwrite no longer restarts ids at 0, an overwrite fragment carrying a deletion
  file is rejected, and any commit producing duplicate ids is rejected - so datasets written by
  Lance 0.16 and earlier may still read but no longer commit. `dataset.get_fragment(0)` after an
  overwrite must read ids from the manifest. Section 5 - which also covers a resolution hazard on
  pre-0.10 unsorted manifests that can make a fragment-filtered index cover the wrong fragments.
- **The file-version types and reader/writer composition moved** (#8020-#8026) -
  `lance-encoding::version` deleted with no re-export; `LanceFileVersion` lost `PartialOrd`/`Ord`
  (#8027, #8028), so `v >= LanceFileVersion::Next` no longer compiles. `FileWriter` is now an
  enum with all constructors removed. Most of these break silently at compile time. Section 3.6.
- **Transaction code moved to `lance-table`** (#8053/#8054/#8056) - see the crate-workspace note
  above; the `lance::dataset::transaction` shim covers the common surface.
- **`Operation::Project` / `Merge` gained `preserves_nullability`** (#8347) - a nullability
  *tightening* must not set it, and such a projection now conflicts with any concurrent
  value-write. This closed a real hole where `alter_columns` could let a racing write land nulls
  unreadable under the tightened schema. Section 9.2.
- **The external-manifest protocol changed** (#8499) - object storage is authoritative, the
  external store's put-if-not-exists is a *reservation*, and a stored ETag must be **ignored**;
  a retained one makes readers reject a good manifest with `Manifest e_tag mismatch`. Section 9.

**The manifest feature flags changed - and bit 128 was reallocated before the final.** v11 added
the first new bit since v7 and moved `FLAG_UNKNOWN` 128 -> 256. But the bit it added,
`FLAG_MEM_WAL_INDEX_CATCHUP`, was **retired again** (#8680) and the reclaimed bit handed to
`FLAG_COVERED_INDEX_METADATA = 128` (#8535) before `v11.0.0` shipped. At the final and at v12
there is no index-catchup flag and no `require_index_catchup` proto field; a shard absent from
`index_catchup` now unconditionally means *unknown*. Both reader and writer must hold bit 128 or
refuse the table. Section 7.

**Do not pin anywhere in `v11.0.0-beta.4` through `beta.17`.** Those builds treat bit 128 as a
MemWAL flag they support, so they *open* a covering-index dataset instead of refusing it - wrong
neighbours, no error. The exposure is inherited by whichever flag takes the bit.

**Covering indexes are the v11 net-new format feature** (#8535), **redefined at v13** (#8856).
`IndexMetadata.covering_fields` (proto field 11) names the columns an index *carries* values for,
so a query projecting only those columns is answered without a base-table take. It is **no longer
a trailing suffix of `fields`**: it "must be a subset of `fields`, in the order the index emits
them. A column is carried if and only if it is named here", including a column the index is also
keyed on - and `fields[0]` remains a keyed column. Index invalidation stays wide: **any** index
whose `fields` include the updated column, "whether the index is keyed on it or merely carries
it".

The old "no index builder writes carried values yet" no longer holds. V3 IVF auxiliary files can
physically carry columns, and "a reader discovers carried columns by exclusion, not by position:
any column in the auxiliary file's schema that is not one of the quantizer's internal columns is
a carried column", bound to source fields by a new `covering_field_ids` metadata key. Coverage is
now per-segment, not per-index: "one logical index may hold values for some of its segments and
not others". `VectorQueryProto.covering_projection` (field 15) reserves the query-side tag, where
absent / present-and-empty / present-and-non-empty are three distinct meanings. Section 11.

**Bit 8 was spent in the `v12.0.0` final.** `FLAG_MIXED_DATA_FILE_VERSIONS = 1 << 8` (256) is no
longer a reservation pinned equal to `FLAG_UNKNOWN`: the assert relaxed to
`FLAG_MIXED_DATA_FILE_VERSIONS < FLAG_UNKNOWN`, `FLAG_UNKNOWN` moved `1 << 8` -> `1 << 9` (512),
and the build now both reads and writes mixed-version datasets. It is still carried by
`STICKY_PAIRED_FLAGS`, and a **half-set** manifest is now a hard error: "Manifest has only one of
the mixed data-file-version reader and writer feature bits set, so its semantics are undefined".
Section 7.

**Bit 1024 is where the docs and the code disagree - trust the code.**
`FLAG_FRAGMENT_REUSE_INDEX = 1 << 10` is declared at `rust/lance-table/src/feature_flags.rs:69`
and, at `v13.0.0-beta.4`, **that declaration is its only occurrence in the entire tree**. It sits
*above* `FLAG_UNKNOWN` (512), and the supported set is computed as `FLAG_UNKNOWN - 1`, so a
manifest setting it is **refused**. The spec page meanwhile lists it as reader `Yes` / writer
`Yes` and puts the unknown boundary at 2048. The docs describe the intended end state; the code
has only reserved the constant. Anything you build against tagged FRI today is building against
prose, not behavior.

**Two `LANCE_*` env vars landed** (from the AMX work, #8540): `LANCE_DISABLE_AMX` (runtime kill
switch) and `LANCE_AMX_FP16_CC` (build-time compiler override). Grep trap: `LANCE_AMX_CFG_*` and
`LANCE_AMX_TILE_COUNT` are **C macros in `amx_fp16.c`, not env vars**, and `LANCE_FACTOR` is a
substring of `BALANCE_FACTOR` - a plain `LANCE_*` grep reports all four as if they were real.

**Worth knowing without reading the full delta:** FTS gained a document-boundary axis
(`DocumentGranularity`, #7788) whose `list_element` mode is a third trigger requiring FTS on-disk
format v3; transactions above **20 MiB** spill out of the manifest entirely (#7881); MemWAL
catch-up became derived rather than declared (#8481); transaction proto field 9 is deprecated for
field 10 (#7432); compaction gained row/byte budgets plus fragment exclusion (#8235, #8532);
`merge_insert` gained `write_mode` (#8423); and Python commit conflicts became
`lance.commit.CommitConflictError`, a subclass of `OSError`, so existing handlers keep working
(#8563). Full list with citations in `references/changelog-v7-v13.md`.

**Address-domain indexes stopped falsely claiming compacted fragments** (v11, `beta.16` or
earlier). A rewrite used to advance *every* index's `fragment_bitmap` onto the new fragment ids -
including ZoneMap, whose stored addresses point into the fragments the rewrite dropped. The
Rewrite path now branches on `results_are_row_addrs()`: an address-domain index gets
`drop_rewritten_fragments` and a full-scan fallback, correct-but-slower instead of stale
addresses. **Heals only for new compactions**: an index already damaged under v10 or earlier must
be recreated, and the damage does not self-heal through routine maintenance, because the
refreshed `fragment_bitmap` also makes incremental folds a no-op. Section 11.

**Correctness fixes split by whether upgrading is enough.** Most are read-path only and heal on
upgrade. These do **not** - they need data rewritten or repaired: #8382, #8669, #8509, #7703,
#8539, #8459, #8378, #8482, #8834 (rebuild HNSW - a persisted graph can hold edges to ids it does
not contain; lost recall stays lost), #8101 (**nullable primary keys silently duplicated rows** on
every repeat `merge_insert`; existing duplicates must be removed by hand), #8511, #8427, #8513,
#8839, #8904. Conditions for each in `references/changelog-v7-v13.md`.

## The v12 delta

**225 commits** from `release-root/12.0.0-beta.N` to the `v12.0.0` final, with **7
`breaking-change`-labeled PRs** - the five visible at beta.15 plus **#9072** and **#9101** in the
run-up to the final. No new index types and no new crates; every structural invariant above still
holds. **The label is a floor, not a ceiling** - the two biggest behavior changes in the line
carry a conventional-commit `!` but no label, so the bot never counted them: the `stable` -> 2.2
move (#8657, above) and the IVF_RQ 5-bit default (below).

- **`WrappingObjectStore` implementors must add `wrap_paginated`** (#8606) - "There is
  deliberately no default: getting this wrong is either a silent loss of speed or a silent loss
  of the wrapper, and neither announces itself." Return `Some` to keep listing pushdown through
  the wrapper, `None` to give it up and fall back through `inner`. One wrapper giving it up gives
  it up for the whole chain. Anything wrapping the object store fails to compile until updated.
- **New paged listing: `ObjectStore::read_dir_page`** (#8606) - one page of a prefix's immediate
  children plus an opaque resume token. The trap: "One page is one request, so a page can hold
  fewer children than `limit` asked for and still be followed by more" - walk until the token is
  `None`, never until a page comes back short.
- **MemWAL `ShardManifestStore` renamed and narrowed** (#8640) - `read_latest` -> `latest`,
  `read_latest_uncached` -> `refresh_latest`, and `write` is now crate-private (reach it through
  `commit_update`, `claim_epoch`, or `initialize_shard`). Existing `commit_update` closures need
  no change. Section 10.
- **`lance-namespace` 0.8.5 -> 0.11.1** (#8903) - four `LanceNamespace` methods now return
  response objects instead of bare values: `count_table_rows` -> `CountTableRowsResponse`,
  `query_table` -> `QueryTableResponse`, `namespace_exists` / `table_exists` -> their own
  response types. Callers unwrap; anyone implementing the trait needs the same signature updates.
- **External manifest stores gained predecessor-conditioned publication** (#8800) -
  `put_if_predecessor` reserves a version only while the predecessor still carries the identity
  the writer observed, and `commit_after` refuses with `PrerequisiteFailed`, "never a conflict".
  The hard compile break is the new `ManifestLocation.identity` field, not the trait methods
  (all default-implemented). No built-in store implements it. Section 9.
- **Namespace merge-insert keys became a list** (#8915) - `on` moves from `Option<String>` to
  `Option<Vec<String>>`, with **arity-dependent NULL semantics**: a single-column key treats NULL
  as equal to NULL, a composite key uses SQL equality, "under which a NULL key matches nothing -
  not even a byte-identical NULL".

**The `lance-namespace` pin is no longer one number.** #8915 moved the Rust client to **0.12.0**
and #8979 moved **Java** to 0.12.0 as well; only **Python** still holds `>=0.11.1,<0.12`, because
its generated models still send `on` as a bare string. Quote a language-specific pin, never one
number for all three - and note this split moved once already, so re-check it rather than
carrying the pairing forward.

**IVF_RQ now defaults to 5 bits per dimension, not 1** (#8936) - roughly a **4.4x index-size
increase** at the default (upstream's 100M x 768d example: ~10.8 GiB -> ~47.3 GiB). `Fast` search
mode "uses only the 1-bit sign code even when the index stores additional bits", so it pays the
storage without using it; set `num_bits=1` explicitly to opt out, at the cost of the multi-bit
distance estimate and some recall. Sizing formulas in `references/indexes.md`.

**Column slice stitching (#8660) was reverted** at beta.9 (#8926) - it "should not ship while the
caller-managed replacement in #8923 is being developed". `rust/lance-file/src/concat.rs` exists
again at beta.15, but holds #8923's caller-managed data file parts, not the reverted stitching.

**Two proto additions.** MemWAL `SsTable` gained `in_memory_bytes`, `physical_rows` and
`primary_key_bytes` (fields 3-5, #8981); all optional, and **absence must not be read as zero**.
`FilteredReadOptions` gained `materialization_readahead_bytes` and `batch_size_bytes` (13, 14) -
not a format change under a new rule in `protos/AGENTS.md`: execution-plan schemas "are wire
contracts, not persisted Lance formats". `transaction.proto` / `ann.proto` / `index.proto` are
untouched.

**Net-new, non-breaking:** provider-native bulk copy and a deep-clone concurrency bound (section
13); Python `ObjectStoreProvider` registration (#8522); `BinaryView` in the packed blob writer
(#8700); caller-managed data file parts (#8923); cleanup of specific versions (#8617);
`LanceDataset.slice()` (#8059) and six more `LanceFragment.scanner` options (#8429); restored
Python index retraining (#8786); namespace-managed clone deprecated to a shim (#8964). Namespace
latest-version resolution no longer lists the whole `_versions/` prefix (#8679) - on a
~340k-version table that was ~344 list pages, "~25s of pure I/O wait", paid by every open.

**Fixes needing a rebuild or rewrite, not just an upgrade:** #8779 (rebuild NGRAM indexes), #8510
(rewrite data compacted from uniformly reordered fragments), #8984 (re-drop a resurrected index),
#8837 (repair a MemWAL shard below ~2.7KB/row - it cannot be reopened). Full per-PR conditions,
plus the much longer list that *does* heal on upgrade, in `references/changelog-v7-v13.md`.

**Mixed data-file versions LANDED** - it is no longer "1 of 6". #8581-#8584 shipped in `v12.0.0`
(validation, per-operation V2 write targets, propagation across dataset operations, compaction
targeting) and #8585 exposed it in the bindings in the v13 line. The proto changed with it:
`DataStorageFormat.version` is now "the default format version used when writing data files",
and "each DataFile's version is authoritative for decoding" once the capability is set.

**In flight, not landed - do not treat as shipped:** generic block v5 compression is **still 1 of
10** PRs merged (#8324; #8325-#8333 all remain open). Next big dependency break in the queue:
#8997, "upgrade to arrow 59, DataFusion 55, and pyo3 0.29" - **still open** at `v13.0.0-beta.4`,
so arrow 58 / datafusion 54 still hold. It also gates two outstanding PyO3 advisories
(RUSTSEC-2026-0176/0177); rustls was separately patched to 0.23.45 for RUSTSEC-2026-0285 (#9212).

## The v13 delta

**66 commits** from `release-root/13.0.0-beta.N` to `v13.0.0-beta.4`, with **2
`breaking-change`-labeled PRs**. No new crates and no new index types; 26 crates, 16 transaction
ops, `CommitConfig.num_retries` 20, arrow 58 / datafusion 54, MSRV 1.91.0, Edition 2024 and
Python 3.10+ all still hold.

**The `!`-vs-label rule inverted in this window.** All three conventional-commit `!` commits
(#7465, #9192, #9101) *do* carry the `breaking-change` label. Keep treating the label as a floor
rather than a ceiling - but this window is the counter-example, not more evidence for the gap.

- **`WriteParams` gained `file_writer_options`** (#9192) - the single labeled PR that re-rooted
  the major. `FileWriterOptions { data_cache_bytes, max_page_bytes, keep_original_array }` is now
  reachable from the dataset write APIs in Rust, Python and Java. A zero `max_page_bytes` is
  rejected before encoder construction rather than misbehaving later. Anything constructing
  `WriteParams` by struct literal fails to compile.
- **Page metadata is initialized lazily, and the metadata cache key changed shape** (#7465).
  `StructuralFieldScheduler::initialize` now takes `requested_ranges`, and the page-scheduler
  `initialize` splits into `init_ranges()` and `init_from_buffers(buffers, io)` - any external
  implementor fails to compile. The public `DecodeBatchScheduler::try_new` kept its signature;
  the range-aware entry point is the crate-private `try_new_with_ranges`. The part that bites
  without a compile error: caching moved from a per-column `FieldDataCacheKey` to a per-page
  `PageDataCacheKey { column_index, page_index, view_tag }`, so **every warm or persisted
  metadata cache cold-misses** across this upgrade. The payoff is real - "a cold point/range
  read's metadata IO is invariant to the column's total page count".
- **`json_extract` and `json_get` no longer route to JSON indices** (#9101). Only the four typed
  accessors (`json_get_int` / `_float` / `_bool` / `_string`) reach the index; everything else
  falls back to a full scan. This fixes three real wrong-answer bugs - a quoted-key mismatch that
  "searched for a quoted key and matched nothing", a `Utf8` literal driving an `Int64` btree into
  a panic, and an unsound range because "quoting is not order-preserving (`ab` < `ab!` but
  `"ab"` > `"ab!"`)". **The cost is silent**: a `json_extract` workload that used to hit an index
  now scans, with no error and no plan warning. Rewrite those predicates onto the typed
  accessors.

**The Fragment Reuse Index gained a versioned on-disk contract** (#9136). `InlineContent` field 1
was renamed `versions` -> `legacy_versions` and a tagged `transitions` list added at field 2,
gated on `index_version >= 1`; mappings are now a oneof of `OrderedCompaction` or
`StablePartition`. A stable partition "assigns source rows to destination fragments while
preserving their relative source order within each destination", which lets FRI reuse existing
indices after **reclustering** - a second use case the v0 model had no concept of. Its physical
form is an immutable row-map Lance file with `uint16` labels and an `LSPC`-magic counts matrix.
Two hard rules: **stable row IDs and tagged FRI are mutually exclusive** ("writers must not
publish `index_version >= 1` on them"), and cleanup "must retain intermediate transitions still
needed to translate old addresses". Upstream also softened the old claim - "FRI does not remove
conflicts between overlapping rewrites". Section 11.

**Net-new, non-breaking:** `Dataset::frag_reuse_index()` is public (#9112) and documented in the
performance guide; `FileFragment::write_overlay` returns a real `OverlayWriter` (#8761, still
env-gated); an `hf://` object store with `hf_enable_resolve_cache` (#9236); Python
`lance.bitmap.Bitmap`, `deep_clone()` (#9181), `base_paths()` (#9191) and
`update_columns(with_offsets=True)` (#8891); Java `DataStorageVersion`, `FileWriteOptions` and
`ScanOptions.indexSegments`; and namespace table listing finally bounded by `read_dir_page`
(#9165). `inline_optimization_enabled` **flipped `true` -> `false`** (#9180), which upstream
justifies with a -49% write-p50 measurement at 1M entries.

## Performance questions

For anything performance-shaped - slow scans or searches, remote/object-storage cost, index
maintenance cost, memory sizing, version bloat, benchmarking - load
`references/performance.md` first. Part A routes to the official guidance plus the undocumented
source-derived changes; Part B is field-verified practice against S3-compatible storage. The
governing rule stays **minimize remote calls** - fewer commits, fewer scans, fewer round trips -
because that is where the order-of-magnitude wins are. The official **"Tuning remote scans"**
section (v11, unchanged at v12) gives a starting point for cross-region or public-internet
access, where the cloud default of 64 concurrent requests is too aggressive: `LANCE_IO_THREADS=8`,
`fragment_readahead=1`, `batch_readahead=2`, `io_buffer_size=64MB`. It is a legitimate second
move once call volume is already minimized.

**AMX-FP16** (#8540, beta.16) is the one v11 performance change that alters *results*, not just
speed: where it engages, IVF partition assignment becomes **exact instead of approximate**, so
recall improves *and* assignments differ from an older build. It is shape-gated (`float16` +
`dot`, `dimension >= 32`, `num_centroids >= 32`); everything else keeps the previous path.
`LANCE_DISABLE_AMX=1` disables it, but reverts assignment to the approximate path too - so an
index built with it set is not equivalent to one built without it.

Two cache facts to know before tuning anything remote: Lance has **no resident data cache** (a
`Session` holds only index and metadata caches, never decoded values, so repeated point reads
re-pay object-store IO), and one `Arc<Session>` shared via `DatasetBuilder::with_session` lets
datasets share it. Cold first search is dominated by paging indexes in - `prewarm_index` is the
remedy. Note that **#7465 changes the metadata cache key shape**, so the first run after a v13
upgrade re-pays that paging even against a warm or persisted cache. Details and build-time
requirements in `references/performance.md`.

**Time travel is not an archive mechanism.** Versions look like free history, but the default
cleanup reclaims anything older than 7 days and cleanup is part of routine optimize - so a design
that treats old versions as the durable record loses it on the first maintenance pass. Keep an
explicit archive if you need one.

## Official docs mirror

`references/docs/` mirrors `docs/src` of `lance-format/lance` at the tracked tag, verbatim -
45 markdown files plus 4 diagrams, all directly readable.

| Directory | Files | Covers |
|-----------|-------|--------|
| `guide/` | 14 | CRUD, performance, object store, distributed write + indexing, JSON, tokenizers, data types, data evolution, blob, arrays, tags/branches, migration, observability |
| `quickstart/` | 4 | First dataset, vector search, full-text search, versioning |
| `format/` | 1 | Spec-stack overview |
| `format/file/` | 3 | Container spec, structural encodings + compression, format versions |
| `format/table/` | 9 | Layout, schema, transactions (**conflict-resolution matrix**), versioning, row-id lineage, branch/tag, MemWAL, data overlay files |
| `format/index/` | 1 + 4 svg | Index lifecycle, fragment coverage, compaction interplay |
| `format/index/scalar/` | 9 | fts, fmindex, ngram, btree, bitmap, bloom_filter, label_list (`array_has_any/all`), zonemap, rtree |
| `format/index/vector/` | 1 | IVF / PQ / SQ / RQ / HNSW concepts and storage layout |
| `format/index/system/` | 2 | Fragment reuse index, MemWAL system index |
| `integrations/` | 1 | DataFusion SQL over Lance, incl. JSON functions |

**Not mirrored:** `docs/src/images/` (PNG/GIF assets), so image links in the mirrored pages do
not resolve - the prose is self-contained, and the four `.drawio.svg` diagrams *are* mirrored.
Also out by design: `community/`, `examples/`, `integrations/{index,pytorch,tensorflow}.md`; and
the landing stubs and contributor files (`format/AGENTS.md`, `format/CLAUDE.md`).

**A whole tier of docs is not in this repo at all**, so it cannot be mirrored and cannot be
enumerated from a clone. `docs/make-full-website.sh` assembles `format/catalog`,
`format/namespace`, and the `integrations/{duckdb,huggingface,spark,ray,trino,context}` sections
at build time from six sibling repos with their own version lines - the checked-in
`integrations/index.md` links `spark/`, `duckdb` and `trino` as if they were local, but those
paths do not exist in the tree. **Lance Context** and the **HuggingFace** integration docs are
whole nav sections that exist only on the built site. For any of those, read `lance.org` rather
than this mirror. Protobuf message bodies are likewise expanded at build time from `protos/` by
`mkdocs_protobuf`, so the mirrored spec pages show `%%% proto.message.X %%%` placeholders where
the site shows a rendered schema.
