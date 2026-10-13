# Lance v14 reference - table format (sections 5-10)

Part of the Lance v14 reference (`lance-format/lance@v14.0.0-beta.14`; stable pin `v13.0.0`).
Citations are `path:line` relative to the repo root; build a permalink as
`https://github.com/lance-format/lance/blob/v14.0.0-beta.14/<path>`. Line numbers drift between
tags - treat them as approximate. Cross-references written as "section N" use the original
16-section numbering; `lance-reference.md` maps every number to its file.

## Contents

- [5. Table format](#5-table-format)
  - [5.1 Dataset directory layout](#51-dataset-directory-layout)
  - [5.2 Manifest](#52-manifest)
  - [5.3 Fragments](#53-fragments)
  - [5.4 Deletion files](#54-deletion-files)
  - [5.5 Data overlay files (unstable, v9.1)](#55-data-overlay-files-unstable-v91)
  - [5.6 Fragment metadata tree (experimental, v13)](#56-fragment-metadata-tree-experimental-v13)
- [6. Schema evolution](#6-schema-evolution)
- [7. Versioning, tags, branches](#7-versioning-tags-branches)
- [8. Row IDs and lineage](#8-row-ids-and-lineage)
- [9. Transactions and concurrency](#9-transactions-and-concurrency)
  - [9.1 Commit protocol](#91-commit-protocol)
  - [9.2 OCC retry and conflict resolution](#92-occ-retry-and-conflict-resolution)
  - [9.3 Commit handlers](#93-commit-handlers)
  - [9.4 Cache keys and backend (v10, BREAKING)](#94-cache-keys-and-backend-v10-breaking)
- [10. MemWAL](#10-memwal)

Other files: `format-file.md` (1-4), `indexes.md` (11-12), `ops.md` (13, 15, 16),
`changelog-v7-v14.md` (14).

---

## 5. Table format

A Lance **dataset** (a "table") is a directory of immutable files plus a sequence of
versioned manifests.

### 5.1 Dataset directory layout

`docs/src/format/table/layout.md:18-44`:

```
{dataset_root}/
  data/          *.lance                    -- column data files
  _versions/     *.manifest                 -- one manifest per version
                 latest_version_hint.json   -- optional latest-version hint
  _transactions/ *.txn                      -- serialized Transaction protobuf per commit
  _deletions/    *.arrow / *.bin            -- deletion vectors (Arrow IPC / roaring bitmap)
  _indices/      {UUID}/...                 -- index content, one dir per index segment
  _refs/         tags/*.json branches/*.json -- tag and branch metadata
  _bt/           ...                        -- fragment tree objects (v13, experimental; 5.6)
  tree/          {branch_name}/...          -- per-branch datasets (v7)
```

All file paths inside Lance files are stored **relative to their containing directory** -
copying the dataset root relocates it with no manifest edits.

**Base paths.** The manifest's `base_paths` array defines alternative storage locations
(`docs/src/format/table/layout.md:46-83`, `protos/table.proto:295-309`). A `BasePath` has an
`id` (uint32, from 0), optional `name`, `is_dataset_root` (true = standard subdirectory
layout; false = a flat file directory), and an absolute `path`. Data files, deletion files,
and index metadata each carry an optional `base_id` referencing a base; absent means relative
to the dataset root. Use cases: hot/cold tiering, multi-region distribution, shallow clones.
Gated by feature flag `FLAG_BASE_PATHS`.

### 5.2 Manifest

A manifest describes a single immutable version of the dataset (`protos/table.proto:36-293`).
Key fields: `fields` (the schema, all fields including nested), `fragments` (the
`DataFragment` list for this version), `version` (monotonically increasing u64), `timestamp`,
`writer_version`, `index_section` (file position of index metadata), `data_format`
(`file_format` + version string - every file in a version shares one format version),
`config` and `table_metadata` (string maps; `lance.`-prefixed config keys reserved),
`base_paths`, `branch` (optional; absent = main), `next_row_id` (only with stable row IDs),
`reader_feature_flags` / `writer_feature_flags`, `transaction_file`. Three fields arrived after
`v13.0.0-beta.4`: `fragment_tree` (22, v13 - the experimental fragment metadata tree, 5.6),
`transaction_section` (23, v14 - the inline transaction's new home, section 9.1) and
`max_allocated_field_id` (24, v14 - non-reusable field IDs, section 6).

Two manifest-adjacent messages worth naming explicitly. **`IndexSection`** is what
`index_section` points at - "a list of index metadata for one dataset version"
(`protos/table.proto:428-431`), so index metadata is versioned with the table rather than
living beside it. **`VersionAuxData`** (`:311-317`) attaches arbitrary key/value metadata to a
version and is explicitly "Only load on-demand", i.e. it is *not* paid for on every dataset
open the way `config` and `table_metadata` are - the right place for per-version annotations
that most readers never need.

**Manifest naming** has two schemes (`transaction.md:24-31`): **V1** = `{version}.manifest`;
**V2** = `{u64::MAX - version:020}.manifest` (20-digit, reverse-sorted, so the latest version
sorts first lexicographically - enables O(1) latest-version discovery on ordered stores).

### 5.3 Fragments

A `DataFragment` is a horizontal partition holding a subset of rows
(`protos/fragment_metadata.proto:13-88` - `DataFragment`, `DataFile`, `DeletionFile` and
`ExternalFile` moved out of `table.proto` in v13, #9060, which `import public`s the new file):
`id` (unique, incrementally assigned), `files` (one or more `DataFile`s, each storing a subset of
columns), an optional `deletion_file` (at most one per fragment per version), `physical_rows`
(total including tombstoned rows - live count = `physical_rows - deletion_file.num_deleted_rows`),
and optional row-id / version sequences, inline or (unstable, v13) spilled to hidden columns
(section 8).

A `DataFile` stores a subset of columns in the Lance file format, with `fields` (the field
IDs it contains), `column_indices`, file major/minor version, and optional `base_id`. **Every
negative field id is reserved for system use**, and "A reader MUST skip any negative id when it
projects the dataset schema onto a data file" (`docs/src/format/table/index.md:136-145`): `-1` is
in-memory only, `-2` is the tombstone, and `-3`/`-4`/`-5` (v13, #9253) are the hidden `_rowid`,
`_row_created_at_version` and `_row_last_updated_at_version` lineage columns. **A field with no
backing data file reads as entirely NULL** - this is the mechanism behind zero-copy schema
evolution.

**Fragment ids are a dataset-lifetime high-water mark (v11, BREAKING, PR #8206).** Previously
an overwrite restarted ids at 0; now the first fragment an overwrite writes takes the next id
after the dataset's highest ever used, because "an id must never name two different sets of
rows, or per-fragment state keyed by id (caches, deletion files, row addresses) can be
attributed to the wrong rows" (`rust/lance-table/src/transaction/manifest_build.rs:704`). Three
consequences:

- Code that assumes a known id after an overwrite (`dataset.get_fragment(0)`) breaks - read ids
  from the manifest instead.
- An overwrite fragment carrying a deletion file is now **rejected**: "Overwrite fragments must
  be newly written, but fragment {} carries deletion file {}. Use Delete to commit deletions
  against existing fragments, or Merge to change their schema"
  (`rust/lance-table/src/transaction/validate.rs:633`). The reason is structural - a deletion file
  cannot follow its fragment to a new id, because its path embeds the old one
  (`_deletions/{fragment_id}-{read_version}-{id}`).
- **Any** commit producing duplicate ids is rejected (`check_fragment_ids`,
  `rust/lance/src/io/commit.rs:867`). Datasets written by Lance 0.16 and earlier could contain
  duplicates: they still read, but "can no longer be committed to" - they must be rewritten or
  rolled back to a version without the duplicate.

`ManifestNamespace::manifest_from_overwrite_transaction` is carved out and still restarts at 0.

#### Legacy manifests and fragment resolution (read this before trusting a fragment subset)

Two manifest shapes predate the current invariants and are **still readable**: fragments not in
id order (Lance 0.10 and earlier) and duplicate fragment ids (Lance 0.16 and earlier). Neither
is rejected on read. `find_fragment` handles both - it binary-searches, then checks the result
and falls back to a linear scan, because "returning some other fragment's data would be silent
corruption" (`rust/lance/src/dataset.rs:2871-2888`).

**Its sibling `Dataset::get_frags_from_ordered_ids` does not have that guard**
(`rust/lance/src/dataset.rs:2850-2867`). It resolves each id as
`manifest.fragments[fragment_bitmap.rank(id) - 1]`. `fragment_bitmap` is built by collecting
fragment ids into a `RoaringBitmap` (`:885`), which is inherently sorted, so `rank(id) - 1` is
the id's index in the **sorted** id set - while the subscript indexes `manifest.fragments` in
**stored** order. The two agree only if the stored vector is sorted by id. On an unsorted legacy
manifest they diverge, and the only guard is a `debug_assert_eq!`, which compiles out in release.
Concretely, a manifest storing `[id=7, id=3, id=5]` resolves 7 -> fragment 5, 3 -> fragment 7,
and 5 -> fragment 3.

Which legacy shape can actually reach this differs:

- **Duplicate ids** - largely self-limiting, since `check_fragment_ids` makes the dataset
  uncommittable, so index-building paths fail loudly first. Note that check scans
  `manifest.fragments.windows(2)` for adjacent equal ids, so it detects duplicates **only when
  the manifest is sorted**; non-adjacent duplicates on an unsorted manifest pass it.
- **Unsorted fragments, no duplicates** - passes every commit-time check and is the shape that
  breaks the rank arithmetic.

Consequences differ by caller, and the difference matters:

- `dataset/take.rs:305` re-looks-up offsets by the returned fragment's own `id()`, so a
  misresolution drops slots rather than mis-attributing values - the failure mode is **silently
  missing rows**, not wrong values.
- `index/scalar.rs:233` zips the requested ids against the resolved fragments and takes
  `frag.metadata()` with **no id re-check**, so a scalar index built over a fragment subset would
  train on the wrong fragments while recording the requested ids as its coverage.
- `index/create.rs:937` discards the result (existence check only) and is unaffected.

**Status: a static finding, not a demonstrated defect.** The mechanism and the call sites above
were read at `v11.0.0-beta.16`; no legacy dataset was constructed to drive the path, and it is
not a reported upstream issue. The upstream test that looks like it covers this,
`test_get_frags_from_ordered_ids_accepts_unsorted_duplicates` (`rust/lance/src/index/create.rs:1348`),
writes a **fresh** dataset and varies only the *query array* order - which is the documented
flexibility ("The ids do not need to be sorted or deduplicated"); the manifest-ordering
assumption is untested. Practical guidance: if you operate datasets written by Lance 0.10 or
earlier, rewrite them before building indexes over fragment subsets, and do not assume a
fragment-filtered index covers the fragments you named.

**Do not key application state on fragment ids.** Independently of the above, any operation
that rewrites a fragment mints new ids, so caches, delta detectors, or coverage checks that
compare "are the base version's fragment ids still a subset of current?" will spuriously
invalidate. Note this is about fragment *identity*, not write volume: a matched `merge_insert`
updating one column writes a new per-column data file plus a deletion vector rather than
rewriting the whole fragment, so the physical cost is small even though the id churns.

### 5.4 Deletion files

Deletes are **soft**: a deletion file (deletion vector) marks deleted row offsets without
rewriting data files; at most one per fragment per version (`docs/src/format/table/index.md:174-185`).
Two formats: **Arrow IPC** (`.arrow`, a flat `Int32Array` of offsets - sparse deletions) and
**roaring bitmap** (`.bin` - dense deletions). Offsets are 0-based within the fragment. Path:
`_deletions/{fragment_id}-{read_version}-{id}.{ext}`. Gated by `FLAG_DELETION_FILES`. Deletes
avoid invalidating indexes; accumulating deletions slow scans until compacted.

### 5.5 Data overlay files (unstable, v9.1)

Overlay files supply **new values for a subset of `(row offset, field)` cells within a
fragment without rewriting the fragment's base data files** (`docs/src/format/table/data_overlay_file.md`)
- the cheap-cell-update counterpart to soft-delete's cheap-row-removal. Written and committed
via the new `DataOverlay` transaction op (section 9.1); a reader resolves each cell by taking
the highest-`committed_version` overlay that covers it, falling back to the base data file.
Overlays interact with indexes: for each overlay whose `committed_version` exceeds an index
segment's `dataset_version`, the covered rows are excluded from index results (they carry
updated values the index has not seen). The exclusion is field-aware, and since v13 the
fields checked range "over the union of the index's `fields` and `covering_fields`"
(`data_overlay_file.md:150`, #9159) - an overlay on a merely-carried column still excludes.

Gated by **feature flag 64** (`FLAG_UNSTABLE_DATA_OVERLAY_FILES`,
`rust/lance-table/src/feature_flags.rs:32`). This is **not a released feature**: writes require
`LANCE_ENABLE_UNSTABLE_DATA_OVERLAY_FILES` (`feature_flags.rs:138`), and in release builds the
flag is treated as unknown so a release reader/writer **refuses** an overlay dataset rather than
silently ignoring an overlay (`feature_flags.rs:291` - the gate is
`cfg!(debug_assertions) || env::var_os(...).is_some()`). Compaction can fold fragments over an
overlay-count limit (PR #7772).

**Two overlay shapes.** "A single overlay is one of two shapes"
(`docs/src/format/table/data_overlay_file.md:74`): a **dense** overlay replaces a contiguous
run of row offsets, while a **sparse** overlay addresses scattered offsets and therefore carries
its own offset mapping. Which shape a writer emits determines how cheaply a reader can skip the
overlay for a given row range. The spec also has a dedicated "Scheduling compaction" section
(`:377`) covering when accumulated overlays should be folded back into base files.

**Writer support is still incomplete upstream**, and the spec says so in-line: "TODO: Fill in as
writer implementation progresses, including the status of single-file sparse overlays
(independent-length columns)" (`data_overlay_file.md:367-368`). Treat the read path as the
better-specified half.

**Overlays vs indexes (v10).** A batch of correctness work made index-served queries
overlay-aware, since an overlay can change a cell the index was built against. Index results now
exclude overlay-superseded rows: "`WHERE age = 25` after an overlay sets a row's age to 26 must
not return that row from the index; `WHERE age = 26` must find it" (PR #7549). The machinery is
a new module `rust/lance/src/dataset/overlay.rs` (`overlay_exclusion_offsets`,
`overlaid_fragments`, `collect_overlay_stale_frags`, `collect_overlay_stale_rows_for_segment`)
plus `with_overlay_block(RowAddrMask)` builders on `DatasetPreFilter`, `FilteredReadOptions`,
`MaterializeIndexExec`, and `ANNIvfSubIndexExec`. Query plans change shape only when stale
overlays exist - BTree and ANN gain a targeted `TakeExec` re-evaluation, FTS drops whole stale
segments to `FlatMatchQueryExec`; with no overlays it is "O(num_fragments) boolean check, zero
allocations". Two follow-up fixes: a `RewriteRows` UPDATE touching only a non-indexed column no
longer drops overlaid rows from index-path results (PR #7926), and with stable row IDs a
fragment carrying both a deletion and an overlay no longer masks the wrong row and leaks the
stale indexed value - unmapped offsets are now a hard error (PR #7918).

### 5.6 Fragment metadata tree (experimental, v13)

**A spec, not a usable layout - this build refuses tree tables.** #9060 (v13.0.0) "adds a fragment
metadata tree to the Version Manifest so fragment updates do not rewrite the full fragment list":
fragment records move into immutable Lance leaves keyed by fragment id, with validated changes
held above the leaves as mutations until a rewrite is worth it (spec
`references/docs/format/table/fragment_metadata.md`, diagram `fragment_metadata_tree.svg`). A tree
table sets `Manifest.fragment_tree` (field 22), leaves `Manifest.fragments` empty, and sets
`FLAG_FRAGMENT_TREE` (bit 12, 4096) in both flag words (`fragment_metadata.md:54-57`) - the flag is
mandatory because "Old readers skip unknown fields and would otherwise see an empty table"
(`protos/table.proto:48`). Tree objects live under `_bt/`, and "Readers must reject absolute
paths and paths outside `_bt/`" (`fragment_metadata.md:93-95`); the messages are in
`protos/fragment_metadata.proto` (`FragmentTreeMetadata` onward, `:318`).

The page itself says "Support for creating or reading tree tables is not yet available in released
Lance versions" (`fragment_metadata.md:9-11`), and the code agrees: the bit is "Reserved for fragment
trees. Readers and writers reject it until implemented" (`rust/lance-table/src/feature_flags.rs:82`)
and is masked out unconditionally in `supported_flags_when` (`:342`), with no env opt-in.

---

## 6. Schema evolution

Every field, including nested fields, has a unique integer **field ID**, assigned in
depth-first order from 0 at table creation (`docs/src/format/table/schema.md:203-290`). An ID is
**preserved** for as long as its field exists, **unique** within a version, and **sparse**; it is
unique only within one branch of one dataset, so an external reference must name the dataset and
branch too (`:280-282`). Internal references always use field IDs, never names or positions.
Nested fields link via `parent_id` (`-1` for top-level). The spec now calls a cast a **type
replacement**: it "creates a replacement field with a new ID and retires the old identity"
(`:358-359`). The `json` logical type is JSONB in an Arrow `LargeBinary` field tagged
`lance.json` (`:191-196`); the byte-level encoding, maintained by the new `lance-jsonb` crate
(v14, #9534), is specified in `references/docs/format/table/jsonb.md` (#9194).

**Non-reusable field IDs (v14.0.0-beta.9, #8658, `format-change`).** In the legacy mode a writer
"may choose the next ID from fields the current version still references. It may therefore reuse
the ID of a dropped field" (`schema.md:235-237`). Setting `Manifest.max_allocated_field_id`
(proto field 24) switches the dataset to a persistent high-water mark: every new field gets an ID
above it, and field-ID metadata a caller puts on new fields is discarded (`:238-244`). The
marker pairs with `FLAG_NON_REUSABLE_FIELD_IDS` (32768) in the **writer** word only - a manifest
with the reader bit is rejected as corrupt, since "non-reusable field IDs only require writer
support" (`rust/lance-table/src/feature_flags.rs:455`). Activation is an explicit, one-way
migration commit (Rust `Dataset::migrate_to_non_reusable_field_ids`,
`rust/lance/src/dataset.rs:3320`): "After activation, a restore must fail if it targets a version
that does not set `max_allocated_field_id`" (`schema.md:260-261`), and an overwrite then gives
every field, nested ones included, a new ID even when names and types are unchanged
(`:360-362`). Before activating, every client that can write the table must enforce writer
feature flags; one that ignores them "may discard the high-water mark and allow field IDs to be
reused" (`:258`).

Schema changes are **metadata-only** wherever possible (`docs/src/guide/data_evolution.md`):

**Per-fragment column writes (v11, #8313; renamed to `write_columns` by #8622).**
`FileFragment::write_columns` writes new column data for a *single* fragment and the result
survives compaction, so a distributed backfill can have each worker materialize its own
fragment's columns independently instead of funneling through one whole-dataset pass. The
API is new enough that it had not appeared in a release tag when it was renamed - pin exactly
if you build on it.

- **Add column** - assign a new field ID, update the schema. Schema-only add is very fast.
  File format <=2.1 cannot add sub-columns under an existing struct; 2.2 can extend nested
  struct fields (including structs nested in lists). Since v9, adding an **all-null `Map`
  column** is allowed (PR #7462; previously rejected because Arrow's non-null `entries`/`key`
  child failed the nullable check).
- **Drop column** - remove the field from the schema; metadata-only, does not delete data on
  disk; reversible while old versions are retained. Physical removal happens only after
  compaction + version cleanup. 2.2 supports nested sub-column removal.
- **Rename / reorder** - change `name` or order; field IDs unchanged.
- **Type change / cast** - may require rewriting that column to new data files (other columns
  untouched). Since v9, `alter_columns` **fails fast** if the column has an index attached -
  it no longer silently drops/invalidates the index; you must `drop_index()` first (PR #7158,
  breaking: `Error::invalid_input("Cannot cast column(s) [...]: they have N index(es) attached
  ... Drop the index(es) with drop_index() before altering")`). v9 also **allows Dict <->
  value-type casts** via `alter_columns` (PR #7289).

**Zero-copy data evolution.** Because each data file holds a distinct set of field IDs and a
missing field reads as NULL, a writer can add and backfill a column by **appending new data
files to existing fragments** with computed values - no full table rewrite. This is the
mechanism for ML feature engineering and adding embeddings to an existing dataset. When a
column is rewritten, the old data file's field ID becomes the tombstone `-2` and a new data
file is appended.

**`FileFragment::merge_columns` lost `max_field_id` (v13.0.0, #9547, `breaking-change`).** It used
to assign the new schema field ids from the caller's `max_field_id` while the `Updater` assigned
data-file field ids from the manifest; "When the two differed, the `Merge` commit succeeded but
the new columns read back as `null` (or, with dropped columns, could alias stale data)". It now
always derives ids from the dataset manifest (`rust/lance/src/dataset/fragment.rs:2313`). Rust-only
signature break - Python `LanceFragment.merge` and Java `Fragment.mergeColumns` are unchanged. The
fix is not retroactive: columns already merged with a mismatched id still read as null.

Lance also supports an **unenforced primary key** and **clustering key**, declared via field
metadata (`lance-schema:unenforced-primary-key`). "Unenforced" - Lance does not always
validate uniqueness; it is used for merge-insert dedup and last-write-wins. PK fields must be
non-nullable leaf primitives; clustering-key fields may be nullable.

**Merge-insert (upsert / find-or-create).** `MergeInsertBuilder` defaults to find-or-create
semantics ("By default this will build a job that has the same semantics as find-or-create",
`rust/lance/src/dataset/write/merge_insert.rs:737`); enable `when_matched(WhenMatched::UpdateAll)`
for upsert - note `UpdateAll` rewrites whole fragments. The default behavior for **duplicate
source rows that match the same target** is to **fail the operation**
(`SourceDedupeBehavior::Fail`, `merge_insert.rs:564,793`); opt into `SourceDedupeBehavior::FirstSeen`
to keep the first and skip later duplicates. Empty `on` keys fall back to the schema's
unenforced primary key.

**That failure is deterministic, and it is not a conflict - do not let an OCC retry loop eat
it.** The error reads "Ambiguous merge inserts are prohibited: multiple source rows match the
same target row on ({})" (`merge_insert.rs:380`) and is raised as `Invalid user input`, i.e. it
describes the *source batch*, not the state of the table. Retrying it re-runs the same
comparison against the same input and fails identically every time, so a generic
"retry the Lance operation on error" wrapper turns one clear error into N attempts and a
misleading exhausted-retries message. Match on the error class at the Lance boundary and retry
only genuine commit conflicts; fix ambiguous input by deduping the source or selecting
`SourceDedupeBehavior::FirstSeen`.

**The third clause: `when_not_matched_by_source_*`.** Beyond "row in both" (`when_matched`) and
"row only in source" (`when_not_matched`), merge-insert can act on **target rows the source did
not mention**. `when_not_matched_by_source_delete()` removes them, and the predicate form
`when_not_matched_by_source_delete("age >= 40")` (`docs/src/guide/read_and_write.md:266`) deletes
only those matching a condition. This is what makes the **"replace a portion of data"** pattern
work (`read_and_write.md:241`): scope a merge to a slice of the table by combining an unmatched
source with a predicate, so one atomic commit replaces exactly that slice rather than requiring
a separate delete-then-append. Without it, "sync this partition to look like my source" is two
transactions and a window where the table is inconsistent.

---

## 7. Versioning, tags, branches

Every commit creates a new immutable version with a monotonically increasing `version`
number; all versions form a serializable history enabling time travel
(`docs/src/format/table/transaction.md:5-7`). Writes (append, overwrite, index ops,
compaction) create versions; **creating or deleting tags or branches does not**. Time travel
is `checkout_version` by version number, tag name, or `(branch, version)` tuple.

**Listing versions cheaply (v11, #8523).** `versions()` reads and deserializes *every* manifest,
which is why it is expensive on a long-lived dataset over object storage. `version_refs()`
returns `VersionRef`s by listing manifest locations only - use it whenever you need version
numbers rather than full metadata (`rust/lance/src/dataset.rs:290,2690`; Python
`dataset.version_refs()`). When only the current branch tip matters, `latest_version` is
cheaper still. `get_fragment` also became a binary search over the manifest at `beta.16`
(#8636), with a check-and-fall-back-to-linear-scan guard for legacy manifests whose fragment
lists are unsorted (Lance <= 0.10) or contain duplicate ids (Lance <= 0.16).

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
| 32 | `FLAG_DISABLE_TRANSACTION_FILE` | Transaction recorded in the manifest, not a separate `.txn` file (writer-only) |
| 64 | `FLAG_UNSTABLE_DATA_OVERLAY_FILES` | Fragments may carry data overlay files; **unstable** - release builds reject it unless explicitly opted in |
| 128 | `FLAG_COVERED_INDEX_METADATA` | Some index declares covering columns (`IndexMetadata.covering_fields`). Without bit 8192 the **legacy suffix contract** holds: the carried columns are the trailing suffix of `fields` in emission order, and a column both keyed and carried appears twice (v11 final; section 11) |
| 256 | `FLAG_MIXED_DATA_FILE_VERSIONS` | **Supported** as of the `v12.0.0` final - the snapshot may reference recognized V2 data files at different exact versions; both reader and writer bits must be set and stay set |
| 512 | `FLAG_FRAG_REUSE_WITH_STABLE_ROW_IDS` | Stable row IDs plus a fragment reuse index (v13, #9119). **Debug builds only** - release builds refuse it, no env override |
| 1024 | `FLAG_FRAGMENT_REUSE_INDEX` | The FRI records tagged transitions (`index_version >= 1`). **Supported since `v13.0.0`** (#9420); paired and sticky |
| 2048 | `FLAG_UNSTABLE_SPILLED_ROW_LINEAGE` | Some fragment keeps lineage sequences in hidden data-file columns (v13, #9253; section 8). **Unstable** - release builds need `LANCE_ENABLE_UNSTABLE_SPILLED_ROW_LINEAGE` |
| 4096 | `FLAG_FRAGMENT_TREE` | Fragment records live in a fragment tree, `Manifest.fragments` empty (v13, #9060; 5.6). **Reserved - always refused** |
| 8192 | `FLAG_INDEPENDENT_COVERING_FIELDS` | `fields` holds only keys and `covering_fields` is an independent declaration; requires bit 128 in both words (v13, #9159). **Reserved - always refused** |
| 16384 | `FLAG_MANAGED_BLOBS` | Blob v2 descriptors address Lance-owned objects (v14.0.0-beta.4, #9293); paired, sticky across restore; **opt-in** since beta.14 (below) |
| 32768 | `FLAG_NON_REUSABLE_FIELD_IDS` | Field-ID high-water mark in force (v14.0.0-beta.9, #8658; section 6). **Writer word only** |

**Flags at or above `1 << 16` (65536) are unknown** and must be rejected as "unsupported"
(`rust/lance-table/src/feature_flags.rs:113`; `versioning.md:45`). The boundary has moved four
times: from 128 in v11 when bit 128 was allocated, to `1 << 9` in the `v12.0.0` final when bit 256
was spent, to `1 << 14` in `v13.0.0` (bits 9-13), and to `1 << 16` in the v14 betas (bits 14-15).
Below it, `supported_flags_when` (`feature_flags.rs:320-345`) still clears five bits per build:
64 and 2048 unless the build is debug or their env var is set, 512 unless debug, and 4096 and
8192 always. Bits 32 and 64 existed in Rust before v11 but were undocumented until the v11 docs
catch-up. Since v12 the constants are written as bit shifts (`1 << 7`) rather than decimals; the
serialized values and compatibility behavior are unchanged.

**Bit 128 changed hands mid-v11 - this is the trap.** v11 first allocated it as
`FLAG_MEM_WAL_INDEX_CATCHUP` (#8263), then **retired that flag** (#8680) and handed the
reclaimed bit to `FLAG_COVERED_INDEX_METADATA` (#8535) before `v11.0.0` shipped. The
index-catchup flag does not exist at the final or at v12, and the proto field
`Transaction.UpdateMemWalState.require_index_catchup` was deleted from the wire with it.

A reader without bit 128 "would answer a query on a merely-carried column with an index keyed on
a different column and return wrong neighbours with no error"; a writer without it "would
maintain the index as though every entry of `fields` were keyed". **Both must refuse the table.**

**The reclamation has a named exposure window.** Upstream chose the bit precisely because the
current released build already treats it as unknown - but "builds from the window where the bit
was allocated to index catch-up (v11.0.0-beta.4 through beta.17) still count it as supported and
will open a covering dataset rather than refuse it; that exposure comes with the reclamation and
is inherited by whichever flag takes the bit." Do not run a pin inside that window against data
a newer writer may touch.

**MemWAL catch-up is no longer flag-gated.** With the flag gone, the semantics are
unconditional: "A shard absent from `index_catchup` for an index means that index is *not* known
to have caught up, so the shard's SSTables must be retained until some commit records that it
has." There is no longer a legacy "absence means fully caught up" reading and no one-way flag to
set - an absent shard simply means *unknown*, and a repair is scheduled.

**Bit 256 was spent in the `v12.0.0` final.** `FLAG_MIXED_DATA_FILE_VERSIONS` is still declared
`1 << 8`, but the compile-time assert relaxed from `== FLAG_UNKNOWN` to `< FLAG_UNKNOWN`, and
`FLAG_UNKNOWN` moved `1 << 8` -> `1 << 9`. Tests now assert both
`can_read_dataset(FLAG_MIXED_DATA_FILE_VERSIONS)` and `can_write_dataset(...)`, so this layer
accepts mixed manifests. The follow-ups landed with it: #8581 (validation), #8582 (per-operation
V2 write targets), #8583 (propagation across dataset operations) and #8584 (compaction
targeting) are in `v12.0.0`; #8585 exposed it in the bindings in the v13 line.

**Sticky and paired sets.** `STICKY_PAIRED_FLAGS` is now `FLAG_MIXED_DATA_FILE_VERSIONS |
FLAG_FRAGMENT_REUSE_INDEX | FLAG_MANAGED_BLOBS`, carried in both words across the reset in
`apply_feature_flags` and into derived manifests by `inherit_sticky_feature_flags`;
`STICKY_WRITER_FLAGS` adds `FLAG_NON_REUSABLE_FIELD_IDS` on the writer side only
(`feature_flags.rs:131-134`). A **half-set** paired bit is a hard error, not an ambiguity:
"Manifest has only one of the {name} reader and writer feature bits set, so its semantics are
undefined" for mixed-version and Managed Blob, and "FRI requires both reader and writer feature
flags" for 1024 (`validate_paired_feature_flags`, `:409-435`). For bit 32768 the high-water mark
and the writer bit must agree and the reader bit must stay clear (`:442-459`). Bit 128 is carried
by its own path, and bit 8192, once implemented, is retained together with it. Mixed-version
flags also "remain set even if compaction later makes the files homogeneous again"
(`docs/src/guide/read_and_write.md:94-95`).

**Docs vs code at `v14.0.0-beta.14` - trust the code.** The old bit-1024 split is closed:
`versioning.md:36` lists it reader/writer `Yes` and the code agrees, since #9420 moved
`FLAG_UNKNOWN` off the bit in `v13.0.0` (at `v13.0.0-beta.4` the declaration was its only
occurrence and the bit was refused). The page's "Flag bit 512 is reserved" sentence is gone - 512
is spent. New splits replace it:

- **512** - the table (`versioning.md:35`) gives reader/writer `Yes` with no caveat; the code says
  "Understood only by debug builds until support is released" (`feature_flags.rs:57-61`;
  `frag_reuse_with_stable_row_ids_enabled() = cfg!(debug_assertions)`, `:304-306`), so a release
  build refuses an FRI-on-stable-row-ID table outright.
- **2048** - the lineage page says "A released build treats bit 11 as an unknown feature flag and
  refuses the dataset" (`row_id_lineage.md:261-262`); the code also accepts it in a release build
  when `LANCE_ENABLE_UNSTABLE_SPILLED_ROW_LINEAGE` is set (`feature_flags.rs:143`, `:297-299`).
- **4096 and 8192** - the table is normative (`versioning.md:38-39`); the code masks both
  unconditionally (`feature_flags.rs:342-343`). Bit 8192 is "Reserved ahead of its implementation.
  This build masks the bit out in `supported_flags_when`, so it cannot open a table and apply the
  legacy suffix contract to independent declarations" (`:94-96`).
- **16384 activation** - the page says "Publishing a new data file containing a Blob v2 field
  activates the Managed Blob capability, including files containing only inline values"
  (`versioning.md:47`). Since #9891 (`v14.0.0-beta.14`, code-only, no doc edit) the code activates
  it only on explicit schema metadata `lance.blob.managed=true` (`MANAGED_BLOBS_META_KEY`,
  `feature_flags.rs:103-106`); default writes and compaction stay on Inline/Packed/Dedicated
  descriptors.

**Managed-blob do-not-pin window: `v14.0.0-beta.4` through `beta.13`.** Managed blobs first shipped
in beta.4, and in those betas "Ordinary Blob V2 writes currently activate `FLAG_MANAGED_BLOBS` and
require newer readers, even when callers never requested managed storage" (#9891). `v13.0.0` and
earlier refuse such a table, and the bit is sticky across restore - "Existing beta-written flagged
datasets retain their fence." Same shape as the bit-128 window above: never write Blob v2 data with
those builds to a table that an older client must still read.

### Tags

A tag labels a specific version. Stored as JSON under `_refs/tags/`, always at the root
regardless of branch. Tag JSON: `branch` (optional; absent = main), `version`, `createdAt` /
`updatedAt` (RFC 3339), `manifestSize`, `metadata`. **Tagged versions are exempt from
`cleanup_old_versions()`** - to remove a tagged version you must delete the tag first
(`docs/src/guide/tags_and_branches.md:61-67`). Tag names: alphanumeric, `.`, `-`, `_`; no
`/`.

### Branches (v7)

Branches are Git-like parallel histories (`docs/src/format/table/branch_tag.md`). A branch
dataset is technically a **shallow clone** of its source, with version-specific files under
`tree/{branch_name}/` carrying their own `_versions/`, `_transactions/`, `_deletions/`,
`_indices/`. Branch metadata is JSON at `_refs/branches/{name}.json` (`/` URL-encoded as
`%2F`): `parentBranch`, `parentVersion`, `createAt`, `manifestSize`, `metadata`. Each branch
has its **own linear version history** - version numbers can overlap across branches, so use
`(branch_name, version)` tuples as global identifiers. **`main` is reserved (v13.0.0, #7180,
`format-change`)**: creating a branch named `main` is rejected, and "The exact name `main` is a
virtual name for the default branch" - no `main.json` is ever written
(`docs/src/format/table/branch_tag.md:20-22`). "In reference contexts, `"main"` is an alias for the
default branch and is equivalent to `None`", so `("main", 2)` and `(None, 2)` name the same version
(`docs/src/guide/tags_and_branches.md:18-23`). Branch names are case-sensitive. Branches hold references to data files - cleanup will not delete files still referenced by a
branch, so unused branches must be deleted to reclaim space.

`cleanup_old_versions(policy)` deletes old manifests, unreferenced data/deletion/index files.
A file referenced by no manifest is deleted only if >=7 days old unless `delete_unverified`
is set. `CleanupPolicy` knobs: `before_timestamp`, `before_version`, `delete_unverified`,
`error_if_tagged_old_versions` (default true), `clean_referenced_branches`,
`delete_rate_limit` (max delete requests/sec, to avoid S3 throttling). A newer
`Dataset::cleanup(policy)` API (new in v8, PR #7147) splits this into `explain()` (returns a
`CleanupExplanation` of what would be removed - a dry run) and `execute()`; v9 exposes both to
**Python and Java** (PR #7248).

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

**Stable row IDs** are normally enabled at dataset creation (manifest flag bit 2). Since
`v11.0.0-beta.15` (#8521) an existing dataset can also be migrated in place with
`Dataset::migrate_to_stable_row_ids`, which supersedes the older "cannot be turned on later"
rule. It is one `Merge` commit that assigns row-id sequences to every fragment and flips the
feature flag atomically; because `Merge` conflicts with all data-modifying operations, "a
successful commit guarantees no concurrent write occurred". Two operational catches:
**no retries are attempted** (`with_max_retries(0)`), so quiesce concurrent writers first and
retry yourself on conflict; and it is idempotent, returning `Ok(())` immediately if the table
already uses stable row IDs (`rust/lance/src/dataset.rs:3266`).

Assignment uses a monotonic `next_row_id` counter in the manifest; on a
commit conflict the writer rebases by re-reading the latest counter. On update, Lance writes a
new physical row, keeps the same `_rowid`, marks the old physical row deleted, and the row-id
index maps `_rowid -> (new fragment, new offset)`.

Row-id sequences are stored per fragment as a `RowIdSequence` protobuf (`protos/rowids.proto`)
with five compact segment encodings (Range, RangeWithHoles, RangeWithBitmap, SortedArray,
Array) - bitpacked. A row-id index is built at table load by aggregating all fragments'
sequences.

**Inline or spilled to hidden columns (v13, #9253, `format-change`; unstable).** The `external_*`
arms of the three sequence oneofs (`DataFragment` fields 6, 8, 10) are **retired and reserved** -
"No Lance writer ever emitted them; the column arms replace that design"
(`docs/src/format/table/row_id_lineage.md:254-258`; `reserved 6, 8, 10`,
`protos/fragment_metadata.proto:79`), and Rust's `RowIdMeta::External` /
`RowDatasetVersionMeta::External` variants went with them. Sequences "small enough (~200KB encoded
and under)" stay inline (`row_id_lineage.md:195-197`); "A larger sequence is **spilled to a hidden
column of one of the fragment's data files**" (`:199-200`). The new arms `column_row_ids` (12),
`column_last_updated_at_versions` (13) and `column_created_at_versions` (14) are empty
`RowLineageColumn` markers: the column is found by reserved field id `-3` (`_rowid`), `-4`
(`_row_created_at_version`) or `-5` (`_row_last_updated_at_version`) in one of the fragment's
`files`, and must hold exactly `physical_rows` non-null values (`:199-237`). Rules worth knowing:

- Only values fixed before the commit spill (ids and created-at versions carried over by
  compaction or row rewrites); commit-assigned values stay inline so a retry can rewrite them
  (`:239-245`). A fragment with a v1 data file must keep every sequence inline (`:211-214`).
- Opt-in per table via the `lance.row_lineage.spill` config key, threshold
  `lance.row_lineage.inline_max_bytes` (default `200 * 1024`,
  `rust/lance/src/dataset/rowids/spill.rs:63-76`); "a table that never sets it is unchanged"
  (`row_id_lineage.md:246-247`).
- Any column arm sets bit 2048 in both words; a reader without it "would take the fragment to have
  no row IDs at all" (`:249-252`). **Not released**: release builds refuse the bit unless
  `LANCE_ENABLE_UNSTABLE_SPILLED_ROW_LINEAGE` is set (section 7). The docs briefly declared it
  stable in `v14.0.0-beta.12` (#9800); #9885 reverted that in beta.13 because it "merged before the
  required format vote completed".

**Change data feed** (stable row IDs only): each row tracks `created_at_version` and
`last_updated_at_version`, queryable via SQL predicates on `_row_created_at_version` and
`_row_last_updated_at_version` to find rows inserted or updated between two versions.

### Stable row IDs in hand-assembled transactions

If you build fragments yourself and commit them (distributed write, Ray/Spark workers), stable
row IDs stop being automatic and become **your** responsibility. Three rules, all of them
silent-failure modes if broken (`docs/src/guide/distributed_write.md`):

- **Populate `row_id_meta` on every fragment you write.** A fragment written without it commits
  successfully while **silently giving every rewritten row a fresh identity**, breaking `_rowid`
  for anything downstream that depends on it. There is no error.
- **Never mint row ids yourself.** Ids come from a counter in the manifest, and a commit that
  loses a race is retried against the version that won - which may have consumed the very ids
  you picked. The commit assigns them after conflict resolution.
- **Leave `created_at_version_meta` and `last_updated_at_version_meta` as `None`.** Lance
  derives both at manifest-build time; supplying them is not needed.

Build the metadata with `lance.fragment.RowIdSequence` (v11, #8356). Duplicate ids are now
rejected outright - previously `[1, 1, 2]` silently encoded to `[1]`, because the segment
encodings represent a sorted run as a range plus its holes, so a repeated value became a shorter
sequence with a spurious hole.

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
`transaction_properties` string map, and a `oneof operation` with **16 wire operation types**
(`protos/transaction.proto:416-433`):

`Append`, `Delete`, `Overwrite`, `CreateIndex`, `Rewrite`, `DataReplacement`, `DataOverlay`,
`Merge`, `Restore`, `ReserveFragments`, `Update`, `Project`, `UpdateConfig`,
`UpdateMemWalState`, `Clone`, `UpdateBases`.

The Rust `Operation` enum has **17 variants** since v14 - those 16 plus `Unknown {}`
(`rust/lance-table/src/transaction/operation.rs:39,261`, #9482), which is never encoded on the
wire (below). `DataOverlay` arrived in the 9.1 dev line (PR #7535/#7536): it attaches overlay files
supplying new values for a subset of `(row offset, field)` cells without rewriting a fragment's
base data files (section 5). It is **unstable** - env-gated by
`LANCE_ENABLE_UNSTABLE_DATA_OVERLAY_FILES`, and release builds refuse overlay datasets (feature
flag 64 treated as unknown). No wire op was added from v10 through `v14.0.0-beta.14`; the `oneof
operation` tag range still ends at `DataOverlay data_overlay = 115` (`:432`), and field numbers
100-199 are now formally reserved for operations (`:410-414`). Do **not** count `RewriteRows` /
`RewriteColumns` toward the total - those are variants of `UpdateMode`, a different enum living
in the same Rust file.

**The inline transaction moved to manifest field 23 (`v14.0.0-beta.2`, #9482).** "Lance v1.0
through v11.0 decode the inline transaction (manifest field 21) while opening a version, and fail
if it contains an operation they don't know" - so any new op type written inline would make that
version unopenable for them. New writers store it in `transaction_section` (field 23), which
those readers ignore; `transaction_section_deprecated` (21) is still read for old manifests but
"New writers must leave it absent" (`docs/src/format/table/transaction.md:41-47`,
`protos/table.proto:202,211`). Decoding is now total: "An undecodable or unsupported Transaction
message must not make the manifest unreadable", and an op number in 100-199 the reader does not
know decodes as `Operation::Unknown`, which "conflicts with every concurrent transaction" and must
never be re-encoded or committed (`transaction.md:45`). Rust-side breaks: exhaustive matches need
an `Operation::Unknown { .. }` arm (the variant is `#[non_exhaustive]` and cannot be constructed
outside `lance-table`), and `From<&Transaction>` for `pb::Transaction` / `format::Transaction`
became `TryFrom`, failing on `Unknown`. The PR is labeled `format-change`, **not**
`breaking-change`, so the release bot did not count it toward the major bump - the label is a floor.

**Large transactions spill out of the manifest (v11, PR #7881).** Transactions whose serialized
size exceeds `MAX_INLINE_TRANSACTION_BYTES` are no longer inlined into the manifest and live
only in their external `_transactions/` file; readers use the existing fallback path. The
shipped threshold is **20 MiB** - `rust/lance/src/io/commit.rs:420` under `#[cfg(not(test))]`;
the 64 KiB figure quoted in the PR description is the `#[cfg(test)]` value only. Applied in all
three commit paths (`:451`, `:1324`, `:1829`). There is no new configuration knob, the
transaction file is retained as long as the manifest referencing it, and the measured effect on
a large workload was a full-commit manifest shrinking from 1576 MiB to ~790 MiB.

**Proto renames (v10, BREAKING for proto consumers).** The MemWAL vocabulary change (section 10)
touched `protos/table.proto` and `protos/transaction.proto`: message `FlushedGeneration` ->
`SsTable`, `MergedGeneration` -> `CompactedSsTable`; `ShardManifest.flushed_generations` ->
`sstables` (tag 8), `MemWalIndexDetails.merged_generations` -> `compacted_sstables` (tag 9),
`Transaction.Merge` field 5 and `Transaction.UpdateMemWalState` field 1 likewise renamed, and
`IndexCatchupProgress.caught_up_generations` keeps its name but changes element type. **No
message or field was deleted and no tag number was reused or renumbered** - "Proto field numbers
are unchanged (wire-compatible), and `ShardManifest` persists as protobuf, so there is no
on-disk change" (PR #7943). The break is at the generated-symbol level: anything compiling these
protos must regenerate. Separately, `cache_key_prefix = 8` was removed and reserved in the
non-`protos/` file `rust/lance-index/protos-cache/cache.proto` (PR #7878).

Notable semantics: `Rewrite` reorganizes data without semantic change (compaction) and
changes row addresses; `Merge` adds columns and is "overly general" / high-conflict (prefer
`Rewrite`/`DataReplacement`/`Append`); `Update` has two modes - `REWRITE_ROWS` (optimal when
few rows change) and `REWRITE_COLUMNS` (optimal when few columns change across many rows);
`Clone` (shallow = metadata-only referencing the source via `base_paths`, or deep = native
object-store copy) can only be the first operation in a dataset so it never conflicts.

**A raw deep `Clone` commit is rejected (v13.0.0, #9555).** A deep clone is two steps -
`Dataset::deep_clone` copies the files, then commits `Clone { is_shallow: false }`, which rewrites
every reference to the target. Python `LanceDataset.commit(LanceOperation.Clone(...))` and Java
`CommitBuilder.execute` could submit that commit without the copy: "The commit succeeds and
`count_rows()` looks right, but the target has no `data/` directory and any scan fails".
`CommitBuilder::execute` now refuses it with `InvalidInput` before any I/O (Python raises
`OSError`, Java `IllegalArgumentException`); shallow clones and `create_branch` are unaffected.
Targets created the old way must be re-cloned with `deep_clone`.

### 9.2 OCC retry and conflict resolution

`commit_transaction` computes `target_version = read_version + 1`, then runs a retry loop
(`rust/lance/src/io/commit.rs`). Each attempt loads concurrent transactions since
`read_version`, builds a `TransactionRebase`, and produces a rebased transaction. The retry
budget is `CommitConfig.num_retries`, **default 20** (`rust/lance-table/src/io/commit.rs:1743`;
settable via `CommitBuilder::with_max_retries`), alongside a wall-clock `retry_timeout`, default
30 s (`DEFAULT_COMMIT_RETRY_TIMEOUT`, `rust/lance/src/io/commit.rs:93`; process-wide override
`LANCE_COMMIT_RETRY_TIMEOUT_SECS`; `CommitBuilder::with_retry_timeout`). Backoff is slot-based,
seeded from the first attempt's observed commit latency. `num_retries == 0` on an `Overwrite`
triggers strict-overwrite mode (not subject to any rebasing; `:1711-1712`).

**The retry clock starts after catch-up (v14 line, #9631).** Previously the `retry_timeout` clock
started before the first attempt, and that attempt first replays every version committed since
the read version - so a long-running index build or compaction thousands of versions behind could
exhaust the budget on catch-up alone and fail its first conflict with `TooMuchWriteContention:
Attempted 1 times, but failed on retry_timeout` (one reported index append lost two hours of
work). Now "The retry budget now starts once the first attempt has caught up, so `retry_timeout`
bounds the conflict-retry phase rather than how far behind the writer started", and the
`SlotBackoff` unit comes from the attempt's own write window rather than including catch-up.
`num_retries` is unchanged; the fix first shipped in `v13.1.0-beta.2` and the v14 betas, not in
`v13.0.0`.

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

Two `v13.0.0` matrix changes, both closing silent-corruption rebases:

- **`Restore` vs `UpdateConfig`** (#9361, `format-change`). An `UpdateConfig` carrying schema or
  field-metadata updates could rebase over a restore in either commit order, reinstating metadata
  the restore discarded. It is now an **incompatible** conflict in both directions - "UpdateConfig
  (only if it updates schema or field metadata, which a restore rewinds)"
  (`docs/src/format/table/transaction.md:345`, symmetric line `:443`). Plain config upserts still
  rebase over a restore.
- **`Update` vs `Project`** (#9436). `Update` used to tolerate any `Project`, so "a column rewrite
  could commit over a projection that removed the very field it rewrote", leaving a data file for
  a field the schema no longer has. `check_update_txn` now returns a **retryable** conflict when a
  concurrent `Project` dropped any field in `fields_modified`
  (`rust/lance/src/io/commit/conflict_resolver.rs:812`, the `Operation::Project` arm) - the same
  rule `DataReplacement` already had. The spec's Update compatibility list (`transaction.md:403-422`)
  does not mention it yet; the code is authoritative.

**`preserves_nullability` on `Project` / `Merge`** (v11, #8347, `protos/transaction.proto:169,
182`). The default `false` means "this operation makes no nullability assertion". A nullability
*tightening* must **not** set it: the producer proved the claim by scanning at its read version,
so a concurrent write can falsify it - which is why such a projection now **conflicts with any
value-write in either commit order**. The hole this closed: `alter_columns` proved NOT NULL by
scanning, then committed a `Project` that conflicted with nothing, so a write racing the scan
could land nulls that then fail to read under the tightened schema.

**Dataset *creation* is not covered by any of this.** OCC protects *commits*; the create path
has no retry loop at all - `do_commit_new_dataset` carries an in-repo
`// TODO: Allow Append or Overwrite mode to retry using` comment
(`rust/lance/src/io/commit.rs:662`) and returns `DatasetAlreadyExists` on collision (`:711`) -
after first checking whether an ambiguously reported write was in fact its own
(`verify_commit_outcome`). The retry classifier matches exactly one arm,
`Error::RetryableCommitConflict` (`rust/lance/src/dataset/write/retry.rs:73`), returning every
other error immediately (`:99`);
and `execute_with_retry` takes an `Arc<Dataset>`, so it structurally cannot cover creation.
Upstream's own concurrency test creates the dataset first and *then* races appends. Racing
`create` from multiple processes is an application-level problem: create once, or treat
`DatasetAlreadyExists` as "someone else won" and re-open.

### 9.3 Commit handlers

The commit strategy is pluggable via the `CommitHandler` trait. Routing by URI scheme
(`rust/lance-table/src/io/commit.rs`):

| Scheme | Handler |
|--------|---------|
| `file` (non-Windows), `s3`, `gs`, `az`, `abfss`, `oss`, `tos`, `memory`, `shared-memory`, `goosefs` | `ConditionalPutCommitHandler` (`rust/lance-table/src/io/commit.rs:1195-1196`) |
| `cos` (Tencent) | `TencentCosCommitHandler` - **fails closed**, see below (v11, #8369) |
| `file` (Windows) | `RenameCommitHandler` |
| `s3+ddb` | `ExternalManifestCommitHandler` (DynamoDB; requires the `dynamodb` feature) |
| anything else | `UnsafeCommitHandler` (no concurrency check; logs a warning) |

`goosefs` joined that list in v11 (PR #8134); `abfss`, `tos`, and `shared-memory` were already
routed there before v10 despite earlier editions of this table omitting them.

**Tencent COS is the one store that cannot self-coordinate** (v11, #8369). COS silently ignores
put-if-not-exists on buckets that have *ever* had versioning enabled - even if versioning is now
suspended - so under the old `ConditionalPutCommitHandler` routing two concurrent writers could
both report success while one manifest overwrote the other. `cos://` now fails closed: a write
**requires** a custom distributed `commit_lock` or a custom `CommitHandler`, and errors without
one. If you have been writing to COS on an older Lance, treat past concurrent commits as
suspect.

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

**v10 commit-path changes.** `CommitBuilder::with_source_store` (`rust/lance/src/dataset/write/
commit.rs:137`, PR #7545) enables cross-store and cross-account `deep_clone`: per-file copy
streams source -> target when the stores differ and keeps the server-side `ObjectStore::copy`
fast path when `store_prefix` matches. The retry backoff gained a cap - `slot_i * unit` could
overflow `u32` and panic in debug or wrap into a tiny sleep in release, so `MAX_SLOTS = 128`
now bounds it (`rust/lance-core/src/utils/backoff.rs:87`, PR #7883); attempts 0-4 are
unchanged, and because "the cap is proportional to `unit`, not absolute, a slow first attempt
can still produce a multi-minute single sleep". External-manifest finalization now always HEADs
the destination after copy: it previously reused staging object metadata for manifests under
5 MiB, which could reject valid tables as corrupt (PR #7964). **Superseded at v11.0.0-beta.8 by
PR #8499** - the HEAD still happens, but its ETag is now returned to the caller as an opaque
physical-generation observation and deliberately *not* persisted; see the protocol change
below. Two correctness fixes:
`Dataset::filter_deleted_ids` returned wrong results on stable-row-id datasets, breaking
`optimize_indices` with `batch.num_rows() != chunk.len()` (PR #7704), and `filter_addr_or_ids`
now errors on mismatched input lengths instead of silently truncating.

**v11 (beta.8): object storage became authoritative for external manifest stores (PR #8499).**
The external store is now described as "the concurrency coordinator and fast version index",
not the commit itself. The protocol re-labels its steps:

1. Stage the manifest under `{dataset}/_versions/{version}.manifest-{uuid}`.
2. **Reserve** the version in the external store with put-if-not-exists. This "selects one
   immutable staging object; it is not yet the canonical commit" - the previous wording called
   this step the commit.
3. Copy staging -> `{dataset}/_versions/{version}.manifest`. "Successful materialization at
   this deterministic path is the commit point."
4. Update the external-store pointer to the finalized path.

The load-bearing rule is about the ETag: **"Do not persist that ETag in the external store."**
Concurrent finalizers can copy the *same* selected immutable bytes into different physical
generations, and COPY plus external-store publication is not atomic, so a retained ETag makes
later readers reject a perfectly good canonical manifest with `Manifest e_tag mismatch` - a
dataset that reads as broken while its bytes are fine. Every helper therefore publishes the
same stable path-and-size tuple, and readers "ignore any legacy stored ETag because it is
neither content identity nor dataset-incarnation identity", validating **size** instead. The
HEAD's ETag is still handed to the current caller, purely so runtime caches do not collapse a
newly committed `Dataset` into an older cached one at the same URI and version.

Fault tolerance was re-cut along the same seam: a failure between steps 2 and 3 leaves a
pending reservation that readers retry; a failure between 3 and 4 leaves the canonical object
**committed** (readers use it and may repair the index); staging deletion is garbage collection
and never affects the commit outcome. Rollout needs no migration or quiesced cutover - new
readers ignore legacy stored ETags and legacy readers already accept finalized rows without
one - but while legacy *finalizers* remain in the fleet the pre-existing race can still
republish a stale ETag that a legacy reader rejects. Full protocol:
`references/docs/format/table/transaction.md`.

**v12 (beta.12): predecessor-conditioned publication (PR #8800), a `breaking-change`-labeled PR.**
`ExternalManifestStore::put_if_predecessor` "reserves a version only if the store's record for the
predecessor still carries the identity the writer observed", and `CommitHandler::commit_after`
publishes on that condition. Its contract is explicit that this is not the ordinary conflict path:
"Commit only if `predecessor` is still the manifest at its version, decided with the reservation;
otherwise [`Error::PrerequisiteFailed`], never a conflict"
(`rust/lance-table/src/io/commit.rs:1020-1022`).

The identity comes from a new `ManifestLocation` field - "A token unique to this manifest record
in the commit handler's store ... A dataset recreated at the same version has a different one"
(`pub identity: Option<String>`). **That field is the actual compile break**: the new trait
methods are all default-implemented, so only code constructing `ManifestLocation` with a struct
literal must change. No built-in store implements the conditioned contract, and unconditioned
commits behave exactly as before.

### v2 manifest paths are a compatibility fence

`CommitBuilder::enable_v2_manifest_paths` is **default true** for new datasets. The v2 naming
scheme is what "allow[s] constant-time lookups for the latest manifest on object storage" instead
of listing `_versions/`, but its own doc carries a warning worth reading before writing a dataset
other systems must read: "turning this on will make the dataset unreadable for older versions of
Lance (prior to 0.17.0)" (`rust/lance/src/dataset/write/commit.rs:181-190`). The parameter has no
effect on an existing dataset - migrate one with `Dataset::migrate_manifest_paths_v2`.

### 9.4 Cache keys and backend (v10, BREAKING)

Cache keys became an opaque 16-byte BLAKE3 digest (PR #7878). The format is stamped as
`pub const CACHE_KEY_FORMAT: &str = "blake3-128-v1"`
(`rust/lance-core/src/cache/key.rs:23`), and `InternalCacheKey` is now a newtype over
`[u8; 16]` (`key.rs:91`) rather than a three-field struct. **There is no runtime legacy-key
fallback**: every warm or persisted cache cold-misses after the upgrade. Upstream's guidance is
"Persistent backends should include `CACHE_KEY_FORMAT` in their physical namespace and allow
entries from older formats to age out."

Removed with it: `CacheBackend::invalidate_prefix`, `LanceCache::keys`, `CacheKeyIterator`,
`LanceCache::with_backend_and_prefix`, `Session::index_cache_keys`,
`Session::metadata_cache_keys`. Migration: "Replace `with_backend_and_prefix` with
`with_backend(...).with_key_prefix(...)`." New exports: `CacheKeySchema`, `CacheNamespace`,
`InternalCacheKey`, `KeyBuilder`, plus `QuickCacheBackend` and `recommended_cache_shards`.

**v11 added a component to the Row Id Sequence key** (#8078): it is now
`Dataset URI, fragment_id, row_id_meta`, up from `Dataset URI, fragment_id`. This was a
correctness fix, not a tuning change - keyed on `fragment_id` alone, a `WriteMode::Overwrite`
against a shared `Session` served the *previous* generation's sequence, corrupting stable row
ids. See the data-loss roundup in `changelog-v7-v14.md`. Java can now also select a registered
native cache backend by URI (e.g. `moka://?capacity=1048576`) or `CacheBackendConfig`, mutually
exclusive with the size options (#8446).

**quick_cache is now the default backend** for both the index cache (PR #7953) and the metadata
cache (PR #8013) - hard-wired in `Session::new`, with no env var or Cargo feature to opt out.
The operationally important consequence is an **admission ceiling**: quick_cache splits its
weight budget evenly across shards with no borrowing and *silently refuses* entries heavier than
a shard's share. Shards are `min(cpus / 2, capacity / 4 GiB)` with a floor of 1, so the
per-shard share bounds the largest cacheable entry - an oversized index partition simply never
caches, with no error. The io_uring handle cache (needs TTL) and the MemWAL SSTable cache (needs
predicate invalidation) stay on moka. Measured FTS effect at concurrency 128: 180.7 -> 1340.6
qps, 710 -> 96 ms, 47% -> 93% CPU.

**Cache backends became pluggable in v11 (PR #7683)**, which reopens the "no opt-out" statement
above. A `BackendConfig { kind, options: HashMap<String, String> }` plus a process-wide registry
(`register_backend`, `build_from_config`, `rust/lance-core/src/cache/registry.rs:29,118`) let
you supply your own implementation, and `parse_backend_uri` / `build_from_uri`
(`cache/backend_uri.rs:51`) accept a compact single-string form -
`moka://?capacity=1073741824`. Wired into sessions via `Session::with_cache_backends`
(`rust/lance/src/session.rs:220`). The only built-in `kind` is `moka`, whose sole option is
`capacity`. Duplicate `kind` registration returns an error rather than silently overriding an
existing constructor.

**Reported cache sizes changed in v11 (PR #8159, behaviourally breaking).** `CacheBackend` gained
a defaulted `deep_size_of_entries` method (`rust/lance-core/src/cache/backend.rs:208`), because
`LanceCache` previously "returned the backend weighted size, whose per-entry weights are each
computed with a fresh `DeepSizeOf` context. Shared `Arc` and Arrow allocations were therefore
charged once per cache entry, and shared `LanceCache` handles could charge the full cache
repeatedly." `approx_size_bytes` is now documented as a fallback "when exact entry traversal is
unavailable". Source-compatible, but **anything budgeting or alerting against
`LanceCache::deep_size_of()` will see smaller numbers after upgrade** - recalibrate thresholds
rather than treating the drop as a cache regression.

---

## 10. MemWAL

**MemWAL is experimental.** It is an LSM-tree architecture layered on a normal Lance table to
absorb high-throughput streaming writes while keeping indexed read performance
(`docs/src/format/table/mem_wal.md`). The Lance table is the **base table**; on top sit
**shards** that take writes and are asynchronously merged back. The spec is an on-disk-layout
contract; in-memory buffering and scheduling are implementation-defined.

### Architecture

> **Terminology changed in v10 (PR #7943, #7957).** What earlier versions called a *flushed
> MemTable* / *flushed generation* is now an **SSTable**, and *merge* into the base table is now
> **compaction**. The rename runs through the spec, Rust, Python, Java, and the protos. Field
> numbers are unchanged, so on-disk data and the wire format are compatible - but every symbol
> and binding name changed, with **no deprecation shims**. Mapping table at the end of this
> section.

- **Shard** - the unit of write scale-out; exactly one active writer per shard. For
  primary-key tables, all rows of a PK must map to one shard (otherwise inter-shard compaction
  order can resurrect stale rows). Append-only MemWAL tables may omit the primary key.
  Sharding is also a **read** optimization, not only a write one: "When sharding specs are
  available, the planner evaluates query predicates against shard fields and skips shards whose
  computed shard values cannot match" (`mem_wal.md:611`). A predicate over the shard field
  therefore prunes whole shards before any data is touched - so choosing shard fields that
  appear in common filters buys read selectivity, not just write parallelism.
- **MemTable** - holds rows before flush; a list of Arrow record batches. **A MemTable does not
  have a generation** - generation numbers belong to SSTables. `current_generation` in the shard
  manifest "is the generation number to assign to the next SSTable created by flushing the
  MemTable" (`docs/src/format/table/mem_wal.md:310`).
- **WAL** - durable storage of all MemTables in a shard, ordered by generation. Each WAL
  entry is an Arrow IPC stream file at `_mem_wal/{shard_id}/wal/`, named with bit-reversed
  64-bit binary (spreads sequential writes across S3 partitions). The writer epoch is in the
  Arrow schema metadata under `writer_epoch` for fencing; since `v14.0.0-beta.5` (#9712,
  `format-change`) a `generation` key records the MemTable generation the entry's batches belong
  to, so replay can rebuild generation boundaries (absent in WAL-only mode, `mem_wal.md:106`). The
  same PR added `ShardWriter::evolve_schema`, which moves a live writer onto a base-table schema
  change by sealing the active MemTable instead of forcing a reopen and WAL replay.
- **SSTable** - "the immutable result of flushing a MemTable" (`mem_wal.md:131`), itself a Lance
  table at `_mem_wal/{shard_id}/{hex}_gen_{i}/`, with pre-built indexes and a PK bloom filter.
  The name is deliberate despite the layout: "Unlike a classic LSM sorted string table, a MemWAL
  SSTable is not sorted by key; random access is instead served by its BTree primary-key
  sidecar. It is called an SSTable because it is an immutable, persisted, indexed run"
  (`mem_wal.md:136`). Its columns "carry the base table's field ids as of the MemTable's schema,
  not ids numbered afresh, since readers and the compactor match them to the base table's columns
  by field id" (`:133`). **`v14.0.0-beta.9` through `beta.12` broke this**: with #8658 "every new
  dataset renumbers its fields from 0, so after a column drop the ids stop lining up and values
  land in the wrong column" in flushed generations. #9857 fixed it in beta.13; generations flushed
  by those betas after a column drop must not be compacted into the base table.

  **v12 added three optional accounting fields** to the `SsTable` proto message (#8981,
  `v12.0.0-beta.14` - the only `format-change`-labeled PR in that range):
  `in_memory_bytes` (field 3), `physical_rows` (field 4), `primary_key_bytes` (field 5)
  (`protos/table.proto:622,627,638`). They record "what the SSTable holds, as the writer's
  MemTable accounted for it at flush" (`mem_wal.md:152-153`).

  Three traps. (1) These are **payload estimates, not read-cost bounds**: `in_memory_bytes`
  "excludes the per-array structure a reader materializes, so a consumer budgeting memory from it
  must add its own headroom." (2) `physical_rows` counts "the older duplicates of a primary key
  that the generation's deletion vector masks. A scan applying the deletion vector yields fewer."
  (3) **Absence is not zero**: "An entry written before they existed records none of them, and a
  reader must not treat an absent value as zero; `primary_key_bytes` is also absent on a table
  with no primary key" (`mem_wal.md:169-171`). Downstream code constructing `SsTable` with a
  struct literal needs updating.
- **Shard manifest** - source of truth per shard: `writer_epoch`, shard assignment, WAL
  pointers, and "**SSTable generation state**: `current_generation` and `sstables`"
  (`mem_wal.md:296`). Versioned, immutable, committed via put-if-not-exists.
  **v12 renamed and narrowed `ShardManifestStore`** (#8640): `read_latest` -> `latest`,
  `read_latest_uncached` -> `refresh_latest`, and `write` became crate-private - callers reach
  it through `commit_update`, `claim_epoch`, or `initialize_shard`
  (`rust/lance/src/dataset/mem_wal/manifest.rs:134,151,251`). Existing `commit_update` closures
  need no change: setting `version: current.version + 1` is exactly what the check expects.
- **MemWAL Index** - one per table, centralizing config, **compaction progress**
  (`compacted_sstables`, "the last SSTable compacted into the base table for each shard",
  `mem_wal.md:43`), index catchup, and shard snapshots. Tied to the `UpdateMemWalState`
  transaction. Config gained **`maintain_all_indexes`** (`MemWalIndexDetails` field 12,
  `protos/table.proto:725`; #9335, v14 line): set, `maintained_indexes` is ignored and the set "is
  resolved from the table's indexes each time a MemTable is built, so an index created after the
  MemWAL was installed is picked up and a dropped one falls out"; an index kind the writer cannot
  mirror is skipped rather than making the table unwritable, while an explicitly named one it
  cannot mirror is an error (`mem_wal.md:364`). "Absent and empty `maintained_indexes` mean maintain
  nothing, while set and empty means maintain everything."

**Two MemWAL internals live only in the mirror.** `references/docs/format/table/mem_wal.md`
carries the reader-side **"Query Planning" / "Indexed Read Plan"** model - how sources are
collected and ranked, where "Each source is tagged with its shard and freshness tier. SSTable
sources are also tagged with their generation" - and, in Appendix 3, the exact **bucket transform
hash** (32-bit wrapping `fmix`/`rotl32` mixing) that decides shard bucketing. Read the mirror for
either; reimplementing bucketing from anything else will not interoperate.

### MemWAL is a parallel stack, not an integration into `Dataset`

Three properties decide whether MemWAL is adoptable for a given system, and none of them are
stated in the spec pages. All three were re-verified at `v14.0.0-beta.14`.

- **`Dataset::scanner()` has no MemWAL integration.** The whole of
  `rust/lance/src/dataset/scanner.rs` mentions MemWAL exactly once, in an unrelated comment about
  phrase matching (`:308`). Fresh rows - MemTable, WAL, and un-compacted SSTables - are reachable
  only through `LsmScanner` (`rust/lance/src/dataset/mem_wal/scanner/builder.rs:195`), which is a
  **narrower** API than the normal scanner: no SQL, no joins, no aggregation, no `take`. A system
  needing DataFusion-grade query over fresh data does not get it from MemWAL.
- **No manifest feature flag marks a MemWAL table.** The flag set is bits 0-15
  (`rust/lance-table/src/feature_flags.rs:11-111`) and none of them means "this table has a
  MemWAL" - the one that briefly existed, `FLAG_MEM_WAL_INDEX_CATCHUP`, was retired before the
  `v11.0.0` final. So an ordinary reader opens the dataset happily and **silently sees only
  base-table data**, missing everything not yet compacted. That is a correctness-of-expectation
  hazard with no error surface, not a format hazard.
- **No SSTable compactor ships in-tree.** The spec fully describes an SSTable Compactor and a
  Garbage Collector, but the workspace contains no struct implementing either - adopting MemWAL
  means writing and operating both yourself.

**Read freshness.** The ordering rules grew from three to five, with the MemTable given its own
explicit tier: "The active MemTable is newer than every published SSTable" (`mem_wal.md:81`),
and any uncompacted SSTable wins over the base table. The background job formerly called the
*MemTable Merger* is now the **SSTable Compactor**: "The compaction uses Lance merge-insert
semantics and updates `compacted_sstables[shard_id]` atomically with the base-table commit"
(`mem_wal.md:521`).

### The appender/tailer/flusher model

Rust write path (`rust/lance/src/dataset/mem_wal/`):

- **`ShardWriter`** - the main per-shard writer interface. `ShardWriter::open` does
  epoch-based fencing once.
- **`WalAppender`** - the lowest-level primitive: single-entry synchronous atomic appends via
  put-if-not-exists, no buffering, owns the object store + epoch + position state.
- **`WalFlusher`** - buffers the WAL for durability.
- **`WalTailer`** - ordered reader of WAL entries from one shard.
- **`MemTableFlusher`** - flushes a frozen MemTable to a Lance file (producing an SSTable).

`ShardWriterConfig.enable_memtable` (default `true`) controls whether a MemTable layer is
maintained. With `enable_memtable == false` (**WAL-only mode**) no MemTable/index is
allocated and `index_specs` must be empty. Key defaults: `durable_write` true,
`max_wal_buffer_size` 10MB, `max_wal_flush_interval` 100ms, `max_memtable_size` 256MB,
`max_memtable_rows` 100,000, `max_unflushed_memtable_bytes` 1GB (backpressure budget - writes
block, never fail).

### In-memory HNSW

The in-memory MemTable can carry a **Lance-native HNSW vector index** (new in v7 - PR #6795;
constructor `MemIndexSpec::hnsw` since v14, formerly `MemIndexConfig::hnsw`). HNSW is
self-contained (no centroids/codebook needed); only the distance metric is inherited from the
base index. Also supported as MemTable indexes: BTree scalar and FTS.

**MemTable index kinds became plugins (v14.0.0-beta.11, #9803-#9805, unlabeled Rust breaks).**
"Removed: `MemIndexKind`, `MemIndexConfig`, `BTreeIndexConfig`, `HnswIndexConfig`,
`FtsIndexConfig`, `validate_index_configs`, `IndexStore::from_configs`. Replacements:
`MemIndexSpec` (with `btree`, `hnsw`, `fts` constructors), `validate_index_specs`,
`IndexStore::from_specs`" (#9803). A `MemIndexPlugin` declares which base-table index it
maintains, and `MemIndexSpec` (`rust/lance/src/dataset/mem_wal/index/plugin.rs:577`) carries the
plugin, field ids, columns, resolved params and the base index's `index_details`; `ShardWriter::open`
and `replace_index_configs` take `Vec<MemIndexSpec>`. #9804 removed `ScalarPredicate` and
`BTreeIndexExec` in favour of `ScalarMemIndexExec`, which "answers a filter from any filter
index"; #9805 added `ShardWriterConfig.index_overrides` for per-index build parameters. Since v9, **prefiltered LSM vector and full-text search** is supported across
all three source tiers (base table, SSTables, in-memory MemTable), threading a prefilter
through the Python and Java bindings (PR #7138).

### Fencing and GC

Writer fencing is epoch-based, single-writer-per-shard: a writer increments `writer_epoch` in
the shard manifest; a writer whose local epoch is below the stored epoch is fenced and must
abort. Fenced writers' WAL entries are not discarded (they were valid when written) and are
replayed by the new writer. SSTables and their WAL files become GC-eligible only
after the SSTable is compacted into the base table, all indexes have caught up, and no retained
base version references them. MemWAL GC is separate from `cleanup_old_versions`.

The spec treats the **garbage collector as a named subsystem** with its own removal preconditions
("The garbage collector may remove obsolete SSTables after:",
`docs/src/format/table/mem_wal.md:530`) rather than as an incidental cleanup step, and carries a
matching **reader-consistency model** ("Reader consistency depends on:", `:576`) plus an
**LSM-tree merging read** section describing how a reader overlays shard state on the base table.
One physical guarantee worth relying on when reasoning about replay and scan order: "SSTable rows
are written in forward insert order" (`:192`).

**API changes in v11.** `force_seal_active` now returns a `SealFence` instead of `()` (PR #8051,
`rust/lance/src/dataset/mem_wal/write.rs:4019`) - existing `.await?;` call sites still compile
since the value is simply dropped, and there is no format or on-disk change. `SealFence`
(`:4398`) exposes `sealed_generation() -> Option<u64>` (`None` on a no-op seal) and a `wait()`,
so a caller can finally learn *which* generation it sealed. Separately, the stringly-typed
`MemIndexConfig::detect_index_type` (which returned `"btree" | "fts" | "vector"`) was removed in
favour of a free `is_maintainable_index_type(type_url) -> bool` plus a typed
`MemIndexKind { BTree, Hnsw, Fts }` (PR #8095). Both are gone again in v14 - the plugin registry
of #9803 (In-memory HNSW above) replaced the closed kind enum.

### The v10 rename map

Everything below changed name only; semantics are unchanged unless noted.

| Layer | Before | After |
|-------|--------|-------|
| Proto message | `FlushedGeneration` | `SsTable` (`protos/table.proto:606`) |
| Proto message | `MergedGeneration` | `CompactedSsTable` (`protos/table.proto:642`) |
| Proto field | `ShardManifest.flushed_generations` (tag 8) | `sstables` |
| Proto field | `MemWalIndexDetails.merged_generations` (tag 9) | `compacted_sstables` |
| Proto field | `Transaction.Merge` field 5, `UpdateMemWalState` field 1 | `compacted_sstables` |
| Rust enum | `LsmDataSource::FlushedMemTable` | `LsmDataSource::SsTable` |
| Rust types | `FlushedMemTableCache`, `GenerationWarmer` | `SsTableCache`, `SsTableWarmer` |
| Rust module | `scanner/flushed_cache.rs` | `scanner/sstable_cache.rs` |
| Rust builders | `with_flushed_cache`, `with_flushed_generation` | `with_sstable_cache`, `with_sstable` |
| Rust fns | `open_flushed_dataset`, `util::flushed_memtable_path` | `open_sstable`, `sstable_path` |
| Rust field | `FlushResult.generation: FlushedGeneration` | `FlushResult.sstable: SsTable` |
| Rust fn | `merged_generation_for_shard` | `compacted_generation_for_shard` |
| Rust builder | `MergeInsertBuilder::mark_generations_as_merged` | `mark_sstables_as_compacted` |
| Python | `lance.MergedGeneration` | `lance.CompactedSsTable` |
| Python | `ShardSnapshot.with_flushed_generation` | `with_sstable` |
| Python | `mark_generations_as_merged(generations=)` | `mark_sstables_as_compacted(sstables=)` |
| Java | `org.lance.memwal.FlushedGeneration` / `MergedGeneration` | `SsTable` / `CompactedSsTable` |
| Java | `ShardSnapshot.withFlushedGeneration`, `flushedGenerations()` | `withSsTable`, `sstables()` |
| Java | `MergeInsertParams.markGenerationsAsMerged`, `markedGenerations()` | `markSstablesAsCompacted`, `getCompactedSstables()` |

**Deliberately kept unchanged**: the flush *verb*, the WAL-durability terms
(`all_flushed_to_wal`, `rows_flushed`, `unflushed_memtable_bytes`), and the generation *number*
concept (`LsmGeneration`, `current_generation`, the on-disk `_gen_{i}` path component).

Two v10 fixes in this area: block-filtered LSM scans returned fewer rows than requested when a
stale prefix consumed the pushed-down source limit (PR #7917, which also removed
`LsmScanPlanner::with_overfetch_factor`), and `TaskExecutor::shutdown_all` now returns the first
handler-cleanup error or task panic instead of always `Ok(())` (PR #7915).

### Fragment reuse index

A related system index (`docs/src/format/index/system/frag_reuse.md`): it lets a compaction
**defer index remap**. Normally compaction must remap every index (so it conflicts with index
optimization); with a fragment reuse index, a compaction that removes fragments A,B and
produces C records the mapping, and at query time row addresses for A,B are translated to C.
This removes the compaction-vs-index-build conflict at the cost of a small per-load remap -
though upstream now qualifies the claim: "FRI does not remove conflicts between overlapping
rewrites" (`frag_reuse.md:218`).

**At v13 the FRI has a versioned on-disk contract** (#9136). `InlineContent` field 1 was renamed
`versions` -> `legacy_versions`, and a `transitions` list added at field 2, gated on
`IndexMetadata.index_version >= 1`; each transition is a oneof of `OrderedCompaction` or
`StablePartition`. "Each legacy group can be interpreted as an ordered-compaction transition,
forming one history with the new records" (`frag_reuse.md:58-60`). A **stable partition** "assigns
source rows to destination fragments while preserving their relative source order within each
destination", which lets FRI reuse existing indices after reclustering - not just after
compaction (`:29-31`). Its payload is an immutable row-map Lance file under
`_fri/<map_id>/stable_partition.lance` with `uint16` labels and an `LSPC`-magic 28-byte-header
counts matrix in a global buffer (`:113-154`).

Two hard rules come with it. **Stable row IDs and tagged histories are mutually exclusive**:
"Tables using stable row IDs do not support tagged histories; writers must not publish
`index_version >= 1` on them" (`:234-235`). And cleanup is no longer "trim anything fully rebuilt
past" - it "must retain intermediate transitions still needed to translate old addresses", and
"External mapping files can be deleted only when no retained dataset version references them"
(`:201-203`).

**Manifest bits.** Publishing FRI index version 1 sets `FLAG_FRAGMENT_REUSE_INDEX` (1024) in both
words, retained thereafter (`frag_reuse.md:230-232`); the bit is supported since `v13.0.0` (#9420,
section 7). Untagged (version 0) FRI needs no flag. Separately, any table version holding both
stable row IDs and an FRI (even untagged) sets `FLAG_FRAG_REUSE_WITH_STABLE_ROW_IDS` (512), because
older systems "could silently corrupt such tables" (`:205-210`, #9119); release builds refuse that
bit, so in a release build an FRI on a stable-row-ID table is unusable (section 7).
