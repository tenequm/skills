---
name: lance-format
description: Deep reference for Lance v14 columnar format, its Rust crates, and pylance - file encodings, table format, indexes, schema evolution, time travel. Use when building on the Lance crates or reading .lance datasets, not the LanceDB product.
metadata:
  version: "0.21.0"
  categories: "development, integrations"
  topics: "lance, columnar-format, vector-search, rust, lakehouse"
  upstream: "lance-format/lance@v14.0.0-beta.14"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/lance-format
    emoji: "🗄️"
---

# Lance v14 reference

Lance is an open columnar format for multimodal AI - "a columnar data format that is 100x
faster than Parquet for random access." It is not one format but a stack of interoperating
specs: a **file format**, a **table format**, **index formats**, **catalog specs**, and a
**namespace client spec**. The Rust workspace at `lance-format/lance` implements all of them
plus Python (`pylance`) and Java bindings.

This skill tracks **`v14.0.0-beta.14`** (the `lance-format/lance` git tag), the current
development frontier; **`v13.0.0`** is the stable pin, released 2026-10-07. Pin against tags, not
`main` - Lance ships beta tags every few days and `next`-format encodings can change. Version
landscape below.

Three layers of reference, load what the task needs:

- **The deep reference** - any concrete schema, parameter, proto, or constraint. Split by topic:

  | File in `references/` | Covers | Sections |
  |------|--------|----------|
  | `format-file.md` | What Lance is, the 27 crates, file format, data types | 1-4 |
  | `format-table.md` | Dataset layout, manifests, fragments, schema evolution, versioning/tags/branches, row IDs, transactions + OCC, MemWAL | 5-10 |
  | `indexes.md` | Vector / scalar / FTS / geo indexes, distributed builds | 11-12 |
  | `ops.md` | Object store, capability matrix, source map | 13, 15, 16 |
  | `changelog-v7-v14.md` | The full v7 -> v14 delta | 14 |

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

27 crate directories under `rust/` at `v14.0.0-beta.14` - #9534 vendored the jsonb codec as
**`lance-jsonb`** (26 at `v13.0.0`). **`lance` is the public entry point** - `Dataset`, scanner,
indexes, commits; everything else (`lance-table`, `lance-file`, `lance-encoding`, `lance-index`,
`lance-io`, `lance-core`, `lance-datafusion`, `lance-linalg`, `lance-namespace*`, ...) is a layer
beneath it. Edition 2024, arrow 58, datafusion 54, pyo3 0.28; Python bindings need 3.10+. **MSRV
is 1.94.0** in the v14 line (#8997), up from 1.91.0 through `v13.0.0`. Full table with roles,
versions, and every workspace dep in `references/format-file.md` section 2.

**If you depend on anything below `lance`, expect moves.** v11 deleted `lance-encoding::version`
with no re-export (`LanceFileVersion` and `ConcreteFileVersion` live in `lance-file::version`),
removed `lance_io::encodings`, and gave each format its own `versions/v2_{0,1,2,3}` module
(#8020-#8026). The transaction code moved to a `rust/lance-table/src/transaction/` module tree
(#8053/#8054/#8056); a `lance::dataset::transaction` shim still re-exports `Operation`,
`Transaction`, `TransactionBuilder`, `RewriteGroup` and `UpdateMap`, so the common surface is
unbroken - but a symbol the shim omits, or a citation of the old path, needs retargeting.
Section 2.1.

## File format versions

The file format carries a single major.minor version. `data_storage_version` is set per dataset
at creation - but since `v12.0.0` it is **no longer fixed once the dataset exists**. It is the
*default* for writes that omit a target: "Create and overwrite establish this default; append,
update, merge-insert, and compaction do not change it." An existing V2 dataset can take `"2.0"`,
`"2.1"`, `"2.2"` or `"2.3"` per operation without rewriting its other files (#8582-#8585), so one
dataset can hold data files at several exact V2 versions. **V1 and V2 still cannot be mixed.**
Section 3.

| Version | Status | Notes |
|---------|--------|-------|
| `0.1` (`legacy`) | read-only | Original format; no longer writable |
| `2.0` | stable | Removed row groups; null support for lists/FSL/primitives |
| `2.1` | previous default | Adaptive structural encodings; better integer/string compression; nulls in struct fields; better nested random access. Was the default from Lance 5.0.0 until `v12.0.0-beta.15` |
| `2.2` | **current default** (`stable`) | Map type, Blob v2, `VariablePackedStruct`, larger mini-blocks. Required for Map and Blob v2 |
| `2.3` | unstable (`next`) | Sparse structural pages (auto-selected by the 2.3 writer), the generic block v5 codecs (#8325-#8333, all landed by `v14.0.0-beta.9`), and compressed mini-block offsets (#8331). Stable readers refuse it |

**`stable` resolves to 2.2** (#8657), and `2.2` is the enum `#[default]`, so a dataset created
without an explicit `data_storage_version` is written as 2.2 - Python's `write_dataset` inherits
it. **The docs still do not say so** - `format/file/versioning.md` only calls `stable` an "alias
for the default version" - so the code is the authority. `next` resolves to 2.3. Pin an explicit
number for deterministic behavior across builds: anything relying on `WriteParams::default()`
(tests, benches) silently changed format at the 2.2 switch.

On v12, a writer defaulting to 2.2 rejected legacy blob metadata outright. **Since `v13.0.0`**
(#9459) legacy blob metadata written to 2.2+ is converted to Blob v2, and a 2.0/2.1 table can
append Blob v2 without a rewrite. Blob v2 tiers by size: **64 KiB inline, 4 MiB dedicated**,
packed `.blob` sidecars between (the pre-v14 docs said 16 KiB / 2 MiB; the code never did).

The release *selectors* (`LanceFileVersion`) are a type distinct from the persisted identity
(`ConcreteFileVersion`). Details in `references/format-file.md` sections 3.1 and 3.6.

## Version landscape

The major is bumped by a bot, not a human: `ci/publish_beta.sh` re-roots at `MAJOR+1` whenever
any PR since the release root carries the GitHub `breaking-change` label - the marker is the
**label**, not a conventional-commit `!`. A major bump therefore means "some labeled breaking
change landed", not a redesign. It has fired on **five consecutive lines**: none of `v9.1.0`,
`v10.1.0`, `v11.1.0`, `v12.1.0` or `v13.1.0` was released. 13.1 got further than the rest -
`v13.1.0-beta.1` and `beta.2` were tagged (fury `13.1.0b1`/`b2`) before #9518 re-rooted it to 14
- so a 13.1 beta pin is a dead end, not an early 13.1.

Four recent lines **did** ship a final: `v10.0.0` (2026-08-08), `v11.0.0` (2026-08-30),
`v12.0.0` (2026-09-17) and `v13.0.0` (2026-10-07). Each sits on a stabilization branch that is
**not an ancestor of `main`** - normal for a Lance final. `v13.0.0` is the 14 release root plus
two release commits, so **every v13-final change is also in every v14 beta**.

| Major | Its breaking theme |
|-------|--------------------|
| **v14** (current, `v14.0.0-beta.14`) | `ScalarIndexPlugin::load_index` takes `index_version` (#9518, re-rooted the major); jsonb vendored as `lance-jsonb` (#9534); compressed 2.3 mini-block offsets (#8331). Unlabeled: inline transaction moved to manifest field 23 plus `Operation::Unknown` (#9482). Delta below |
| **v13** (`v13.0.0`, 2026-10-07) | `WriteParams.file_writer_options` (#9192); lazy page-metadata init with a per-page metadata cache key (#7465); `json_extract`/`json_get` stop routing to JSON indices (#9101); BM25F (#7905); JSON accessor API (#9479); `merge_columns` field ids (#9547); duplicate-pair output (#9551); covering-fields spec split (#9159). Net-new: tagged FRI supported, fragment metadata tree spec, MinHash LSH. Delta below |
| **v12** (`v12.0.0`, 2026-09-17) | `WrappingObjectStore::wrap_paginated` (no default); MemWAL `ShardManifestStore` narrowed; `lance-namespace` response objects; predecessor-conditioned external stores; namespace merge-insert key lists; caller-provided Writer / `open_part` removed (#9072). Unlabeled but bigger: `stable` -> 2.2 and the IVF_RQ 5-bit default. Net-new: mixed data-file versions |
| **v11** (`v11.0.0`, 2026-08-30) | Fragment ids became a dataset-lifetime high-water mark; `lance-file` / `lance-encoding` reorganization; transaction code moved to `lance-table`. Net-new: covering indexes, `merge_insert` `write_mode`, row-address prefilter |
| **v10** | Blob APIs preserve null selections; cache keys became opaque BLAKE3 digests; async `create_remapper`; MemWAL renamed generation -> SSTable |
| **v9.1** (never released; renamed into v10) | FTS/inverted creation took a `block_size` param. Net-new: Data Overlay Files (unstable, env-gated), sparse structural pages, `lance-index-core` |
| **v9** | Python 3.9 dropped; `alter_columns` fails fast when casting an indexed column; FM-Index proto rename; FTS defaults to on-disk format v2 |
| **v8** | All index builds unified onto one segment-based lifecycle. Net-new: `lance-derive`, FM-Index, multi-bit IVF_RQ, `approx_mode`, TOS + GooseFS |
| **v7** | MemWAL, branches, the geo/RTree index, the `lance-select` crate, ICU FTS |

**`v13.0.0` is the stable pin** and what GitHub Releases marks `Latest`. crates.io carries
**finals only** (newest `lance 13.0.0`); PyPI `pylance` is likewise at `13.0.0`. A beta pin
means a git dependency - beta wheels publish to fury.io (`https://pypi.fury.io/lance-format`),
which carries `pylance-14.0.0b1` through `b14`.

Full per-tag deltas with every PR citation: `references/changelog-v7-v14.md`.

## Manifest feature flags

A reader or writer refuses a manifest that sets a bit it does not support. The supported set is
`FLAG_UNKNOWN - 1` minus whatever the build masks out, so **the docs table is not the authority -
`rust/lance-table/src/feature_flags.rs` is**. Bits 0-6 are long-standing (deletion files, stable
row IDs, the deprecated v2 marker, table config, base paths, disabled transaction file, and the
env-gated data overlay files). Everything from bit 7 up arrived in the last four majors, and
`FLAG_UNKNOWN` moved `1 << 9` (v12.0.0) -> `1 << 14` (v13.0.0) -> `1 << 16` (v14 line):

| Bit | Flag | Status at `v14.0.0-beta.14` |
|-----|------|-----------------------------|
| 7 | `FLAG_COVERED_INDEX_METADATA` | Supported since v11 final (#8535) |
| 8 | `FLAG_MIXED_DATA_FILE_VERSIONS` | Supported since v12 final; sticky; a half-set manifest is a hard error |
| 9 | `FLAG_FRAG_REUSE_WITH_STABLE_ROW_IDS` | **Debug builds only** - release builds refuse it. Docs say reader/writer `Yes` |
| 10 | `FLAG_FRAGMENT_REUSE_INDEX` (tagged FRI) | Supported since `v13.0.0` (#9420); sticky |
| 11 | `FLAG_UNSTABLE_SPILLED_ROW_LINEAGE` | Unstable: debug builds or `LANCE_ENABLE_UNSTABLE_SPILLED_ROW_LINEAGE` |
| 12 | `FLAG_FRAGMENT_TREE` | Reserved; rejected until implemented, though the spec exists (#9060) |
| 13 | `FLAG_INDEPENDENT_COVERING_FIELDS` | Reserved and **masked out**. Docs present it as normative |
| 14 | `FLAG_MANAGED_BLOBS` | v14 only; sticky; opt-in via `lance.blob.managed=true` since beta.14 |
| 15 | `FLAG_NON_REUSABLE_FIELD_IDS` | v14 only (#8658); writer-only, sticky |

"Sticky" means the bit survives every later commit (`STICKY_PAIRED_FLAGS` / `STICKY_WRITER_FLAGS`),
so setting it once permanently raises the reader floor of the table.

**Two pin windows open a table they should refuse - or brick it for older readers.**

- **Do not pin `v11.0.0-beta.4` through `beta.17`.** Those builds read bit 7 as a retired MemWAL
  flag they support, so they *open* a covering-index dataset instead of refusing it - wrong
  neighbours, no error.
- **Do not pin `v14.0.0-beta.4` through `beta.13`.** Any ordinary Blob v2 write there sets
  `FLAG_MANAGED_BLOBS`, which is sticky, so `v13.0.0` can never open the table again. #9891
  (beta.14) made it explicit opt-in - "Ordinary Blob V2 writes currently activate
  `FLAG_MANAGED_BLOBS` and require newer readers" - but **the beta.14 docs still describe
  automatic activation**. Trust the code.

**Covering indexes** (#8535) - `IndexMetadata.covering_fields` (proto field 11) names the
columns an index *carries* values for, so a query projecting only those is answered without a
base-table take. Under the contract every released build implements, **the carried columns are
the trailing suffix of `fields`** in emission order, and a column the index is both keyed on and
carries appears twice: "`fields = [1, 1]` with `covering_fields = [1]` is keyed on `1` and
carries `1`." #9159 specified an independent contract behind bit 13 (`fields` holds only keys),
but the build masks that bit, so it is spec only. Invalidation is wide either way: **any** index
whose `fields` include the updated column. V3 IVF auxiliary files can physically carry columns
("a reader discovers carried columns by exclusion, not by position"), bound by a
`covering_field_ids` metadata key, and coverage is per-segment. Section 11.

## The v13 final and v14 delta

**161 commits** from `v13.0.0-beta.4` to the `v13.0.0` final, then **137** more on the v14 line
to `beta.14`. **8 `breaking-change`-labeled PRs**: #7905, #9479, #9551, #9547, #9159 in v13
final; #9518, #9534, #8331 in v14. Invariants: **27 crates** (v14), **17 transaction ops**
(`Operation::Unknown`, v14), `CommitConfig.num_retries` still 20 (in v14 the retry clock starts
after catch-up, #9631), arrow 58 / datafusion 54.

**The label missed the format break again.** #9482 (v14.0.0-beta.2) moved the inline
transaction from manifest field 21 to **field 23**, added `Operation::Unknown` so unknown
operations decode instead of failing, and turned `From` conversions into `TryFrom` - labeled
`format-change`, never `breaking-change`, so the bot did not count it. Exhaustive `match` on
`Operation` fails to compile.

- **`merge_columns` field ids come from the manifest** (#9547) - the Rust `max_field_id`
  argument is gone. The bug it fixed made merged columns **silently read back as null**.
- **BM25F cross-field search** (#7905) - `combined_fields` / `CombinedFieldsQuery` scores one
  query across several FTS-indexed columns as a single field. Section 11.
- **JSON API moved** (#9479, #9534) - one accessor (`JsonTextStream::try_new`), `jsonb_to_json`
  removed, and jsonb vendored as `lance-jsonb` with its own spec (`format/table/jsonb.md`). The
  v13 rule still stands: only `json_get_int` / `_float` / `_bool` / `_string` reach a JSON index
  (#9101); `json_extract` / `json_get` silently full-scan.
- **`ScalarIndexPlugin::load_index` takes `index_version`** (#9518) - every third-party scalar
  index plugin fails to compile.
- **Duplicate-pair enumeration** (#9493) changed output order and cosine values in #9551.
- **Default IVF probing moved, unlabeled.** #9184 leaves probes unset so queries get adaptive
  bounds, #9467 recalibrated dot-product profiles, and #9798 (beta.12) added `search_effort`
  (0 to 1, resolved to 0.5; it overrides a fixed `nprobes`) and dropped the Python binding's
  `DEFAULT_NPROBES = 1` minimum-probes floor. Latency and recall at default settings shift
  across these upgrades - re-benchmark rather than carry numbers forward.

**Net-new format surface:** tagged FRI is supported (bit 10, #9420), extending reuse to
reclustering via `StablePartition`; the **fragment metadata tree** spec (#9060 -
`fragment_metadata.proto`, `Manifest` field 22, a `_bt/` directory; bit 12 still rejected);
**spilled row lineage** replacing the retired `DataFragment.external_*` fields (#9253, hidden
columns at field ids -3/-4/-5, unstable); **non-reusable field ids** (#8658, bit 15,
`max_allocated_field_id`); and an experimental **MinHash LSH** index (type 12, #9076/#9114).

**Behavior changes without a label:** explicit cloud storage options now beat env vars (#9719);
`fast_search` no longer adds `_rowid` (#9699); `main` is reserved as the default-branch alias
(#7180); Restore conflicts with an UpdateConfig touching schema or field metadata (#9361); raw
deep-Clone commits are rejected (#9555); the DataFusion memory pool is 150MB per *effective*
partition - all cores when `target_partitions` is unset - with per-execution pools (#9183,
#9408).

**Fixes needing a rebuild, rewrite or repair, not just an upgrade:** rewrite data hit by #9018,
#9239 (NULL written as 0) or #9394; rebuild scalar indexes hit by #9421 (segment merge produced an
empty index), #9352 (LABEL_LIST) or #9203; repair or restore after #9218, #9219, #9573, #9447,
#9176, #9595, #9085; v14: #9760, #9524, #9620, #7706, and #9857 (MemWAL, beta.9-12 only).
Address-domain indexes - **ZoneMap, BloomFilter and FM-Index** - still lose coverage of
compacted fragments rather than claim them (v14 recalculates instead when a fragment reuse index
is present, #9514), and one damaged under v10 or earlier needs recreating. Conditions for each in `references/changelog-v7-v14.md`.

**Still not landed:** the arrow 59 / DataFusion 55 / pyo3 0.29 upgrade. #8997 merged only as
"prepare" ("Not in this PR: the dependency bumps and lockfiles"); the real bump is #9647, open and
blocked on upstream releases. It also gates PyO3 RUSTSEC-2026-0176/0177, still outstanding.

## Earlier majors in brief

**v13 betas** - `WriteParams.file_writer_options` (#9192, struct literals fail to compile);
**lazy page-metadata init** (#7465): `StructuralFieldScheduler::initialize` takes
`requested_ranges`, and caching moved from per-column `FieldDataCacheKey` to per-page
`PageDataCacheKey`, so **every warm or persisted metadata cache cold-misses** across the upgrade -
the payoff is that "a cold point/range read's metadata IO is invariant to the column's total page
count". The FRI got a versioned on-disk contract (#9136; stable row IDs and tagged FRI
mutually exclusive outside debug builds). `inline_optimization_enabled` flipped `true` -> `false`
(#9180). `hf://` object store (#9236).

**v12** - mixed data-file versions shipped (#8581-#8585); `stable` -> 2.2 (#8657); **IVF_RQ
defaults to 5 bits**, ~4.4x the 1-bit index size (#8936; set `num_bits=1` to opt out);
`WrappingObjectStore` implementors must add `wrap_paginated` - "There is deliberately no default"
- and paged listing via `read_dir_page` means walking until the token is `None`, never until a
page comes back short; namespace merge-insert keys have **arity-dependent NULL semantics** (a
composite key's NULL "matches nothing"); `lance-namespace` pins now differ by language (Rust
0.13.0, Java 0.12.0 since #8979, Python `>=0.13.0,<0.14` in v14 - re-check rather than carry forward).

**v11** - fragment ids are a dataset-lifetime high-water mark (#8206): overwrite no longer
restarts at 0, and datasets with duplicate ids read but no longer commit. `LanceFileVersion` lost
`Ord` (#8027/#8028). `Operation::Project` / `Merge` gained `preserves_nullability` (#8347). The
external-manifest protocol made object storage authoritative (#8499) - a retained ETag makes
readers reject a good manifest with `Manifest e_tag mismatch`. #8101 silently duplicated rows on
nullable primary keys under repeat `merge_insert`; existing duplicates must be removed by hand.
Rebuild HNSW indexes hit by #8834 (v11) or #9053 (v13 betas).

## Performance questions

For anything performance-shaped - slow scans or searches, remote/object-storage cost, index
maintenance cost, memory sizing, version bloat, benchmarking - load
`references/performance.md` first. Part A routes to the official guidance plus the undocumented
source-derived changes; Part B is field-verified practice against S3-compatible storage. The
governing rule stays **minimize remote calls** - fewer commits, fewer scans, fewer round trips -
because that is where the order-of-magnitude wins are. The official **"Tuning remote scans"**
section gives a starting point for cross-region or public-internet access, where the cloud
default of 64 concurrent requests is too aggressive: `LANCE_IO_THREADS=8`,
`fragment_readahead=1`, `batch_readahead=2`, `io_buffer_size=64MB`. It is a legitimate second
move once call volume is already minimized.

**AMX-FP16** (#8540) is the one performance change that alters *results*, not just speed: where
it engages, IVF partition assignment becomes **exact instead of approximate**, so recall improves
*and* assignments differ from an older build. It is shape-gated (`float16` + `dot`,
`dimension >= 32`, `num_centroids >= 32`). `LANCE_DISABLE_AMX=1` disables it and reverts
assignment to the approximate path too.

Two cache facts to know before tuning anything remote: Lance has **no resident data cache** (a
`Session` holds only index and metadata caches, never decoded values, so repeated point reads
re-pay object-store IO), and one `Arc<Session>` shared via `DatasetBuilder::with_session` lets
datasets share it. Cold first search is dominated by paging indexes in - `prewarm_index` is the
remedy, and for FTS it loads the whole inverted index into RAM. #7465 changed the metadata cache
key shape, so the first run after a v13 upgrade re-pays that paging even against a warm cache.

**Layout debt is version-dependent.** Binary-copy compaction of small appends preserves tiny
pages; a reader that pays per page (v12) turns that into tens of thousands of GETs per lookup.
Re-encode append-heavy tables, and benchmark on a fresh copy of the real store - details and
measurements in `references/performance.md` Part B.

**Time travel is not an archive mechanism.** Versions look like free history, but the default
cleanup reclaims anything older than 7 days and cleanup is part of routine optimize - so a design
that treats old versions as the durable record loses it on the first maintenance pass. Keep an
explicit archive if you need one. The reverse also holds: `delete` alone does not erase data -
old versions, unrewritten fragments, and indexes (deletes do not conflict with index creation)
all keep it until rewritten, cleaned up, and rebuilt.

## Official docs mirror

`references/docs/` mirrors `docs/src` of `lance-format/lance` at the tracked tag, verbatim -
49 markdown files plus 5 diagrams, all directly readable.

| Directory | Files | Covers |
|-----------|-------|--------|
| `guide/` | 14 | CRUD, performance, object store, distributed write + indexing, JSON, tokenizers, data types, data evolution, blob, arrays, tags/branches, migration, observability |
| `quickstart/` | 4 | First dataset, vector search, full-text search, versioning |
| `format/` | 1 | Spec-stack overview |
| `format/file/` | 3 | Container spec, structural encodings + compression, format versions |
| `format/table/` | 11 + 1 svg | Layout, schema, transactions (**conflict-resolution matrix**), versioning, row-id lineage, branch/tag, MemWAL, data overlay files, fragment metadata tree, JSONB |
| `format/index/` | 1 + 4 svg | Index lifecycle, fragment coverage, compaction interplay, covering contracts |
| `format/index/scalar/` | 11 | fts, fmindex, ngram, btree, bitmap, bloom_filter, label_list (`array_has_any/all`), zonemap, rtree, json, minhash_lsh |
| `format/index/vector/` | 1 | IVF / PQ / SQ / RQ / HNSW concepts and storage layout |
| `format/index/system/` | 2 | Fragment reuse index, MemWAL system index |
| `integrations/` | 1 | DataFusion SQL over Lance, incl. JSON functions |

**Not mirrored:** `docs/src/images/` and the `format/*.png` assets, so image links in the
mirrored pages do not resolve - the prose is self-contained, and the five `.svg` diagrams *are*
mirrored. Also out by design: `community/`, `examples/`,
`integrations/{index,pytorch,tensorflow}.md`; and the landing stubs and contributor files
(`format/AGENTS.md`).

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
