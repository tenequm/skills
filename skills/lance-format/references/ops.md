# Lance v12 reference - object store, capabilities, source map (sections 13, 15, 16)

Part of the Lance v12 reference (`lance-format/lance@v12.0.0-beta.15`). Citations are `path:line`
relative to the repo root; build a permalink as
`https://github.com/lance-format/lance/blob/v12.0.0-beta.15/<path>`. Line numbers drift between
tags - treat them as approximate. Cross-references written as "section N" use the original
16-section numbering; `lance-reference.md` maps every number to its file.

## Contents

- [13. Object store](#13-object-store) - URI schemes, `storage_options`, per-backend config,
  commit handlers per backend, `LANCE_*` env vars
- [15. Capability matrix](#15-capability-matrix) - what Lance can and cannot do
- [16. Source map](#16-source-map) - where each spec, proto, and crate lives in the repo

Other files: `format-file.md` (1-4), `format-table.md` (5-10), `indexes.md` (11-12),
`changelog-v7-v12.md` (14).

---

## 13. Object store

The object store is chosen by URI scheme (`docs/src/guide/object_store.md`): `s3://`,
`s3+ddb://` (S3 + DynamoDB commits), `gs://`, `az://` / `abfss://`, `oss://` (Alibaba),
`cos://` (Tencent), `tos://` (Volcengine, new in v8), `goosefs://` (feature-gated `goosefs`,
new in v8), `file://`, `file+uring://`, `memory://`, `shared-memory://` (in-memory,
cross-component).

`file+uring://` is a **local** store, not a remote one: `is_local()` returns true for both
`file` and `file+uring` (`rust/lance-io/src/object_store.rs:630`), and
`is_uring()` distinguishes it (`:653`). Any rule stated for "the local store" therefore covers
it - a scheme check written as `scheme == "file"` silently excludes uring stores.
Config comes from environment variables or the `storage_options` map passed to
`lance.dataset` / `lance.write_dataset`.

`shared-memory://` is opt-in and distinct from `memory://`: `memory://` mints a fresh
in-memory store per call, while `shared-memory://<authority>` resolves - across object-store
registries, threads, and unrelated components in the same process - to one process-global
`InMemory` backend keyed by the URL authority. The pool is never evicted and grows for the
process lifetime; it is meant for tests and harnesses that coordinate a writer and an
independent reader. Pick distinct authorities for isolation
(`rust/lance-io/src/object_store/providers/shared_memory.rs:16`).

General options: `allow_http` (default false), `connect_timeout` (5s), `timeout` (30s),
`client_max_retries` (3), `download_retry_count` (3), `proxy_url`, `user_agent`.

**`request_timeout` is not a key** - it appears in no Lance source at any recent tag, and #8706
corrected the docs to `timeout`. Anything still passing `request_timeout` is silently setting
nothing. `timeout` bounds the *entire* request, from connection until the response body
finishes, and applies per individual request - so on a large write it must cover one complete
multipart part upload. Raise it alongside `LANCE_INITIAL_UPLOAD_SIZE`.

**Multipart part sizing** - `LANCE_INITIAL_UPLOAD_SIZE` sets the first part's size, clamped to
5 MB..5 GB (values outside the range are clamped with a warning, not rejected;
`rust/lance-io/src/object_writer.rs:55`).

**Bulk copy strategy** (v12, #8770). Set `LANCE_IO_SERVER_SIDE_COPY_ENABLED` to a truthy value
(`1`, `true`, `on`, `yes`, `y`, case-insensitive) to route cloud copies whose source and
destination share the same object-store client into the provider-native server-side copy
operation instead of streaming bytes through the client - the relevant case for index movement
and for copying between two prefixes of one bucket. Deep clone separately bounds non-local file
movement to four concurrent files; `LANCE_DEEP_CLONE_STREAM_CONCURRENCY` overrides that
operation-specific limit (`rust/lance/src/dataset.rs:3352`).

Per-backend highlights:

- **S3** - `aws_region`, `access_key_id` / `secret_access_key` / `session_token`,
  `aws_endpoint` (for S3-compatible stores like MinIO - both region and endpoint required),
  `aws_server_side_encryption` (`AES256` / `aws:kms` / `aws:kms:dsse`) + `aws_sse_kms_key_id`.
  `AWS_PROFILE` is environment-only. New in v11: **`aws_provider_scheme`** (PR #8103) pins a
  dataset to one credential provider instead of the default chain - "useful when two datasets in
  the same process need different AWS auth (for example, one bucket using IRSA and another using
  ECS container credentials)" (`docs/src/guide/object_store.md:118-121`). Exactly three values,
  each failing hard rather than falling back: `token` (static credentials), `ecs` (container
  credentials), and `irsa`, which "Reads `AWS_WEB_IDENTITY_TOKEN_FILE` and `AWS_ROLE_ARN` from
  the environment" (`:127`). Anything else errors with "Invalid aws_provider_scheme '{}'. Valid
  values are: token, ecs, irsa" (`rust/lance-io/src/object_store/providers/aws.rs:550`).
- **S3-compatible endpoints: set the region explicitly, and know why.** The docs state the
  requirement plainly - `aws_region` "must be specified for S3-compatible stores"
  (`object_store.md:102`) - because SigV4 embeds the region in the signed credential scope even
  when the endpoint is not AWS. But the code does **not** enforce it: `resolve_s3_region` returns
  `Ok(None)` precisely in the endpoint-without-region case (`aws.rs:239,264`), and the builder
  then applies `DEFAULT_REGION = "us-west-2"` (`aws.rs:316`, applied at `:103`). There is no
  error path for a missing region, so an omitted `aws_region` **silently signs with `us-west-2`**
  rather than failing fast - producing signature errors, or worse, quiet misrouting on providers
  that accept any region string. Third-party endpoints also usually need
  `virtual_hosted_style_request` (or `aws_virtual_hosted_style_request`) set explicitly - both
  spellings work because the key is passed straight through to the `object_store` crate
  (`aws.rs:99,535`); it defaults to `False` (`object_store.md:107`).
- **S3 Express** - directory buckets; auto-recognized via the `--x-s3` suffix, or set
  `s3_express: "true"`; reachable only from a same-region EC2 instance. Its listing is not
  lexically ordered, so the `latest_version_hint.json` mechanism accelerates latest-version
  lookup there.
- **GCS** - `GOOGLE_SERVICE_ACCOUNT` (JSON file) or `service_account_key`. Default HTTP/1;
  `HTTP1_ONLY=false` for HTTP/2.
- **Azure** - `account_name` / `account_key`, service principal, SAS tokens, managed
  identity, workload-identity federation.
- **Alibaba OSS** - `oss_endpoint` (required), `oss_access_key_id`, `oss_secret_access_key`.
- **Tencent COS** (`object_store.md:333`) - `cos://bucket/path` with `cos_endpoint`,
  `cos_secret_id`, `cos_secret_key`, and optional `cos_enable_versioning`; env vars are read
  from the `COS_` or `TENCENTCLOUD_` prefixes.
- **Volcengine TOS** (new in v8, `object_store.md:303`) - `tos://bucket/path` with
  `tos_endpoint` required (e.g. `https://tos-cn-beijing.volces.com`), plus `tos_region` and
  access-key options.
- **GooseFS** (new in v8, feature-gated `goosefs`, now documented at `object_store.md:396`) -
  `goosefs://host:port/path`; master address comes from `goosefs_master_addr` (HA-aware:
  `"addr1:port,addr2:port"`), the URL host, or default port `9200`. Optional keys:
  `goosefs_write_type` (`MUST_CACHE` / `CACHE_THROUGH` / `THROUGH` / `ASYNC_THROUGH`),
  `goosefs_auth_type` (`nosasl` / `simple`), `goosefs_auth_username`, `goosefs_block_size`,
  `goosefs_chunk_size` (`rust/lance-io/src/object_store/providers/goosefs.rs:24-61`).

  **`storage_options` keys must be lowercase** (#8940, `v12.0.0-beta.12`) - a wrong-case key is
  now a hard error rather than a silently ignored value: "Uppercase or mixed-case spellings such
  as `GOOSEFS_MASTER_ADDR` are rejected with an explicit error - they are not ignored, and they
  are not treated as the matching environment variable" (`object_store.md:547-549`). A config
  that appeared to work by accident will start failing loudly on upgrade.

  **`goosefs_block_size` / `goosefs_chunk_size` accept unit suffixes** (#8943): "Accepts a raw
  byte count or GooseFS suffixes such as `64MB` (binary units: `1KB = 1024`). Optional."
  (`object_store.md:556`).
  **In v11 GooseFS commits became safe** (PR #8134): manifest commits now use
  `ConditionalPutCommitHandler` (`PutMode::Create` / if-not-exists), "backed by GooseFS master's
  atomic no-replace rename so concurrent writers cannot clobber each other's versioned
  manifests" (`object_store.md:404-407`), replacing `UnsafeCommitHandler`. **Mixed-version
  writers are a data-loss hazard during the rollout**: "The `if-not-exists` guarantee only holds
  when **every** writer for a dataset routes through this new handler. A writer running an older
  Lance release still selects `UnsafeCommitHandler` for `goosefs://` and writes the version path
  unconditionally, which can overwrite a manifest that an upgraded writer has already won"
  (`:382-386`). Upgrade all writers before relying on it.

**Multipart upload retries (v11, PR #8174).** A failed part upload used to be retried by calling
`MultipartUpload::put_part` again, but "Native cloud stores allocate a new part number when that
method is called, so the retry skipped the failed part and completion reported `Missing part`."
Retries now happen inside the HTTP connector, preserving part identity, for native S3/Azure/GCS;
"OpenDAL stores retain their existing behavior and are outside this repair." The
`LANCE_CONN_RESET_RETRIES` env var (default 20) was removed along with the old writer-level
resubmission path.

**`LANCE_*` changes in the v11 range.** One removal (`LANCE_CONN_RESET_RETRIES`, above) and two
additions, both from the AMX-FP16 work in `beta.16` (PR #8540):

| Variable | Scope | Effect |
|----------|-------|--------|
| `LANCE_DISABLE_AMX` | runtime | Kill switch for the AMX-FP16 paths. Also reverts IVF partition assignment to the approximate path, so an index built with it set is **not** equivalent to one built without it |
| `LANCE_AMX_FP16_CC` | build time | Overrides the compiler used to build the AMX kernel (`rust/lance-linalg/build.rs:27`); the kernel needs clang >= 16 or gcc >= 13 |

Grep trap: `LANCE_AMX_CFG_SEARCH`, `LANCE_AMX_CFG_GEMM`, and `LANCE_AMX_TILE_COUNT` look like
env vars in a tree-wide `LANCE_[A-Z_]*` grep but are **C preprocessor macros** in
`rust/lance-linalg/src/simd/amx_fp16.c:107-137`. They are not readable from the environment.

**Base-aware access (v7).** `Dataset::object_store` takes an `Option<u32>` base id - `None`
for the primary store, `Some(base_id)` for an additional base. Caching/instrumentation
wrappers are applied per `store_prefix` and propagate to all base stores.

**Per-base `storage_options` (v9, PR #7608).** For multi-base datasets you can scope a storage
option to one base with a `base_<id>.<key>` key (`docs/src/guide/object_store.md:44-70`): "A
storage option key of the form `base_<id>.<key>` applies `<key>` only to the base path with
that manifest id. Every base inherits the unscoped options; base-scoped entries add to or
override them." Base ids are assigned when bases are registered (`initial_bases` ids "assigned
sequentially starting at 1"); keys that don't match the pattern exactly (e.g. `base_url`) are
treated as regular options. Precedence: an exact per-base parameter map (`base_store_params`,
keyed by base-path URI) beats a `base_<id>.<key>` scoped key.

**v10 object-store and runtime changes.**

- **`memory://` datasets could spuriously fail** with `DatasetNotFound` in optimized builds:
  `ObjectStoreParams` Hash/Eq keyed on a trait-object fat pointer, and "Trait object pointers
  include vtable metadata, which is not stable across codegen units. Cache identity must follow
  the Arc allocation instead" (PR #8068).
- **No more panic on tokio runtime shutdown** mid-read - an in-flight parallel read now returns
  an I/O error, "I/O request was dropped before completion ({} of {} reads delivered)"
  (`rust/lance-io/src/scheduler.rs`, PR #7478).
- **`LANCE_CPU_THREADS` and `LANCE_IO_CORE_RESERVATION` are now validated** instead of
  `.parse().unwrap()`-panicking on garbage (`rust/lance-core/src/utils/tokio.rs:50-70`,
  PR #7856). `LANCE_CPU_THREADS` must be at least 1; `LANCE_IO_CORE_RESERVATION` still allows 0
  (reserve no cores for IO); unset still defaults to 2.
- **Namespace behavior change worth auditing call sites for**: the directory namespace no longer
  collapses storage failures into `TableNotFound`. Upstream's motivation - "During a stress run
  on a popular cloud provider, 503 errors when listing objects failed and the dir namespace
  reported the affected tables as non-existent" - meant a create-or-open caller could **overwrite
  a live table** because a transient listing error read as "does not exist". Throttles and 5xx
  now surface as `Throttling` (21) / `ServiceUnavailable` (17) / `Internal` (PR #7931). Callers
  catching `TableNotFound` (4) to mean "absent" must be updated. Alongside it,
  `create_table_version` enforces strict version CAS (only `latest+1`) and is idempotent on
  retry when the resubmitted manifest content matches; `declare_table` returns
  `TableAlreadyExists` when `.lance-reserved` exists; and directory-namespace `query_table` now
  honors `structured_query` FTS, which was previously **silently ignored** - "a `structured_query`
  was silently ignored, so the scan ran with no FTS filter and returned all rows" (PR #7592).
- **`lance-namespace` 0.8.5 -> 0.11.1 at v12** (PR #8903; `python/pyproject.toml` now pins
  `lance-namespace>=0.11.1,<0.12`, Java moved 0.7.7 -> 0.11.1). Four `LanceNamespace` methods
  return a response object instead of a bare value, and callers must unwrap:
  `count_table_rows` -> `CountTableRowsResponse` (`.count` / `.getCount()`), `query_table` ->
  `QueryTableResponse` (`.data` / `.getData()`), `namespace_exists` -> `NamespaceExistsResponse`,
  `table_exists` -> `TableExistsResponse`. Anyone implementing `LanceNamespace` themselves needs
  the same signature updates. Note the Python side is not type-checked against the ABC -
  `python/lance/namespace.py` is outside the pyright allowlist - so a missed unwrap surfaces at
  runtime, not at check time.
- **Latest-version resolution stopped listing the whole prefix** (v12, PR #8679). It previously
  walked all of `_versions/`: on a ~340k-version table that is ~344 sequential `ListObjectsV2`
  pages, "~25s of pure I/O wait", paid by every `open_table` / `describe` / `merge_insert` that
  resolves the latest version. Heals purely on upgrade.

`latest_version_hint.json` (`{"version": N}` under `_versions/`) gives fast latest-version
lookup on stores where listing is not lexicographically ordered (S3 Express, local FS); it is
purely an optimization, always safe to delete, and skipped where listing is already ordered.
Disable globally with `LANCE_USE_VERSION_HINT=0`.

---

## 15. Capability matrix

What Lance can and cannot do at `v12.0.0-beta.15`.

**Storage and format**

| Capability | Status |
|------------|--------|
| Local FS, S3 (+ S3-compatible), S3 Express, GCS, Azure, Alibaba OSS, Tencent COS, Volcengine TOS | yes |
| GooseFS (`goosefs://`) | yes (feature-gated `goosefs`) |
| In-memory store (`memory://`, `shared-memory://`) | yes |
| Multi-base storage (hot/cold, multi-region, shallow clone) | yes (`FLAG_BASE_PATHS`) |
| File format 2.1 (default), 2.0, legacy 0.1 (read-only) | yes |
| File format 2.2 (Map type, Blob v2) | yes, but unstable |
| File format 2.3 sparse structural pages (auto-selected, or forced via `structural-encoding=sparse`) | yes, but `next` / unstable |
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
| Cell-level updates without base-file rewrite (data overlay files) | yes, but unstable (env-gated `LANCE_ENABLE_UNSTABLE_DATA_OVERLAY_FILES`; release builds refuse) |
| Type change / cast | yes (rewrites that column; drops its index) |
| Time travel, tags, branches | yes |
| Stable row IDs (must be enabled at creation) | yes (opt-in) |
| Change data feed | yes (stable row IDs only) |

**Indexes and search**

| Capability | Status |
|------------|--------|
| Vector ANN - IVF + FLAT/HNSW + FLAT/PQ/SQ/RQ (RQ multi-bit, `num_bits` 1..=9; `approx_mode` fast/normal/accurate) | yes |
| ACORN-1 prefiltered HNSW traversal | yes, opt-in (`approx_mode="fast"`) |
| Distance metrics L2 / Cosine / Dot / Hamming | yes |
| Scalar - btree, bitmap, label-list, ngram, zonemap, bloom filter, FM-Index | yes |
| FM-Index substring / prefix / regex search on raw bytes | yes (segment-based) |
| Full-text search - BM25, multilingual tokenizers, phrase queries | yes (Lance-native) |
| Geo / RTree spatial index + geo UDFs | yes (`geo` feature) |
| Distributed / segmented index builds (vector, bitmap, btree, FTS, ngram, rtree, zone map, bloom filter, label-list) | yes (no scheduler) |
| Hamming clustering / near-duplicate detection over binary hashes | yes (v9 utility) |
| `COUNT(*)` pushdown | yes (fast path on stable-row-id datasets) |
| SQL over datasets | via DataFusion (`LanceTableProvider`) - projection / filter / limit only, **no vector search**, see below |

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

**The SQL surface has no vector search.** `LanceTableProvider::scan` pushes down projection,
then filter, then limit, then in-order-ness, and calls `create_plan()`
(`rust/lance/src/datafusion/dataframe.rs:161-164`) - it never calls `Scanner::nearest`, and the
symbol appears nowhere in the DataFusion glue. There is no `ORDER BY vec <-> query LIMIT k`
operator and no vector-distance UDF: `register_functions` adds `contains_tokens`
(`rust/lance-datafusion/src/udf.rs:17`) and the JSON functions, plus geo UDFs
(`st_distance` / `st_area` / `st_intersects`) when the non-default `geo` feature is on
(`udf.rs:30-33,44-53`) - those are geometric, not embedding, distances. **An IVF/HNSW index is
therefore unreachable from `Dataset::sql()`**; use the scanner API (`Scanner::nearest`) for ANN
and reserve SQL for relational work. FTS is the exception - it *is* SQL-reachable through the
registered `fts` table function (`ctx.register_udtf("fts", ...)`,
`rust/lance/src/dataset/udtf.rs:78`), but `Dataset::sql()` itself registers only the table plus
`register_functions`, so there is no vector analogue of that escape hatch.

---

## 16. Source map

Where to look in `lance-format/lance` at `v12.0.0-beta.15`.

| Topic | Path |
|-------|------|
| Format spec overview | `docs/src/format/index.md` |
| File format | `docs/src/format/file/{index,encoding,versioning}.md` |
| Table format | `docs/src/format/table/{index,layout,schema,transaction,versioning,branch_tag,row_id_lineage,mem_wal}.md` |
| Index spec | `docs/src/format/index/{index.md,vector/,scalar/,system/}` (scalar incl. `scalar/fmindex.md`) |
| User guide | `docs/src/guide/{blob,data_evolution,data_types,json,object_store,read_and_write,performance,tags_and_branches,tokenizer,distributed_write,distributed_indexing,migration}.md` |
| Integrations | `docs/src/integrations/{index,datafusion,pytorch,tensorflow}.md` |
| Protobuf schemas | All 12: `protos/{file,file2,table,transaction,rowids,index,index_old,ann,filtered_read,table_identifier,encodings_v2_0,encodings_v2_1}.proto` (`index_old.proto` is a v9 forward-compat shim; `file.proto` is the legacy v1 container; the two `encodings_v2_*` files hold the per-version encoding messages) |
| Rust workspace | `rust/` (entry point `rust/lance/`) |
| Commit / OCC | `rust/lance/src/io/commit.rs`, `rust/lance-table/src/io/commit.rs` |
| Transactions | `rust/lance-table/src/transaction/` (moved out of `rust/lance/src/dataset/transaction.rs` in v11 by #8053/#8054/#8056; `lance::dataset::transaction` survives as a re-export shim) |
| MemWAL | `rust/lance/src/dataset/mem_wal/` |
| Indexes | `rust/lance-index/src/` |
| Object store | `rust/lance-io/src/object_store/` |
| File-version identity | `rust/lance-file/src/version.rs` (both `LanceFileVersion` and `ConcreteFileVersion`; `lance-encoding/src/version.rs` was deleted in v11) |
| Cache keys / backends | `rust/lance-core/src/cache/` (`key.rs`, `quick.rs`) |
| Data overlay resolution | `rust/lance/src/dataset/overlay.rs` |
| Release train / breaking detection | `ci/publish_beta.sh`, `ci/check_breaking_changes.py` |

**`TableIdentifier` (`protos/table_identifier.proto`)** is how a table is handed to a remote
executor for distributed read/write, and it has two modes the filename alone does not reveal:
"1. uri + serialized_manifest (fast): remote executor skips manifest read. 2. uri + version +
etag (lightweight): remote executor loads manifest from storage" (`:10-11`). Mode 1 trades
message size for a saved round trip - the right default when the manifest is already in hand
and the executor count is modest; mode 2 keeps the message small when fanning out widely, at
one manifest read per executor.

Auto-generated API docs and the language-agnostic namespace spec live in sibling repos under
`github.com/lance-format`. The canonical docs site is `lance.org`. To refresh this reference,
see the maintenance note in `../SKILL.md`.
