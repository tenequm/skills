# Lance v15 reference - object store, capabilities, source map (sections 13, 15, 16)

Part of the Lance v15 reference (`lance-format/lance@v15.0.0-beta.10`; stable pin `v14.0.2`).
Citations are `path:line` relative to the repo root; build a permalink as
`https://github.com/lance-format/lance/blob/v15.0.0-beta.10/<path>`. Line numbers drift between
tags - treat them as approximate. Cross-references written as "section N" use the original
16-section numbering; `lance-reference.md` maps every number to its file.

## Contents

- [13. Object store](#13-object-store) - URI schemes, `storage_options`, per-backend config,
  commit handlers per backend, `LANCE_*` env vars
- [15. Capability matrix](#15-capability-matrix) - what Lance can and cannot do
- [16. Source map](#16-source-map) - where each spec, proto, and crate lives in the repo

Other files: `format-file.md` (1-4), `format-table.md` (5-10), `indexes.md` (11-12),
`changelog-v7-v15.md` (14).

---

## 13. Object store

The object store is chosen by URI scheme (`docs/src/guide/object_store.md`): `s3://`,
`s3+ddb://` (S3 + DynamoDB commits), `gs://`, `az://` / `abfss://`, `oss://` (Alibaba),
`cos://` (Tencent), `tos://` (Volcengine, new in v8), `goosefs://` (feature-gated `goosefs`,
new in v8), `hf://` (Hugging Face, read-oriented, new in v13), `file://`, `file+uring://`,
`memory://`, `shared-memory://` (in-memory, cross-component). Apache Ozone (documented in v14,
#9601) adds no scheme: its S3 Gateway "exposes the standard S3 REST API, so Lance uses it through
the existing S3 code path" (`object_store.md:860-862`) - plain `s3://` with `endpoint`, the
`ozone s3 getsecret` key pair, and `virtual_hosted_style_request: "false"` for the gateway's
default path-style mode (`:887-939`).

**`hf://` has an opt-in resolve cache with a staleness hazard** (#9236). Setting
`storage_options={"hf_enable_resolve_cache": "true"}` "reuses resolved HTTP download URLs and
XET file metadata across readers"; it "Defaults to `"false"`" (`object_store.md:639`). The caveat
is a correctness one, not a tuning one: "Enable the resolve cache only when existing files will
not change. Updates, including changes behind a moving branch or tag, may remain invisible while
cached results are reused" (`:645-647`). A moving branch or tag is exactly the common Hugging Face
setup, so leave it off unless you are pinned to an immutable revision.

The underlying stack moved in the `v12.0.0` final: `object_store` 0.13 -> **0.14** and OpenDAL
-> **0.59** (#9123), with OpenDAL reaching 0.59.2 in the v13 line. `v14.0.0` moved `object_store`
to **0.14.2** and `reqwest` 0.12 -> **0.13** with aws-lc-rs TLS instead of ring (#10028); both hold
at `v15.0.0-beta.10`. Anything depending on `object_store` types transitively needs the matching
bump.

`file+uring://` is a **local** store, not a remote one: `is_local()` returns true for both
`file` and `file+uring` (`rust/lance-io/src/object_store.rs:818-819`); only the scheme string,
and the `prefers_lite_scheduler()` check built on it (`:870-871`), tells them apart. Any rule
stated for "the local store" therefore covers
it - a scheme check written as `scheme == "file"` silently excludes uring stores.
Config comes from environment variables or the `storage_options` map passed to
`lance.dataset` / `lance.write_dataset`.

`shared-memory://` is opt-in and distinct from `memory://`: `memory://` mints a fresh
in-memory store per call, while `shared-memory://<authority>` resolves - across object-store
registries, threads, and unrelated components in the same process - to one process-global
`InMemory` backend keyed by the URL authority. The pool is never evicted and grows for the
process lifetime; it is meant for tests and harnesses that coordinate a writer and an
independent reader. Pick distinct authorities for isolation
(`rust/lance-io/src/object_store/providers/shared_memory.rs:16-28`).

General options (`object_store.md:58-77`): `allow_http` (default false), `connect_timeout` (5s),
`timeout` (30s), `client_max_retries` (3), `client_retry_timeout` (180s), `download_retry_count`
(3), `proxy_url`, `user_agent`, and **`block_size`** (v13.0.0, #9380) - the read-coalescing gap:
"Gap in bytes below which two reads of one file are merged into a single request. Default, `4096`
for local files and `65536` for object stores" (`object_store.md:65`). It takes a raw byte count (a
`64KiB` suffix is rejected, `rust/lance-io/src/object_store.rs:2007-2022`). Raising it trades
bytes for requests on scattered reads such as a `take` of rows spread across a file - the
remote-storage lever when request count, not bandwidth, is the bottleneck.
`download_retry_count` only reaches every scan and `take` since #10008 (`v14.0.0-beta.22`):
"`Reader::get_range` now goes through `do_get_with_outer_retry`", so before it the setting was
ignored on ranged reads (`rust/lance-io/src/object_reader.rs:141`). The same PR makes an
unsampleable AIMD backoff range fail at store build and rejects an explicit `aws_credentials`
on the OpenDAL S3 path.

**Three options are new on the v15 line** (none is in any v14 tag):

- **`scheduler_error_mode`** (#8780, `v15.0.0-beta.8`) - "`best_effort` preserves the default
  behavior. `fail_fast` returns the first observed error and cancels the remaining physical reads
  in the same logical request. Other requests are not cancelled" (`object_store.md:76`); it can be
  set session-wide (`:79-95`).
- **`object_store_cache_prune_threshold`** (#10385, beta.8) - default `64`, `0` disables the sweep;
  "Mainly relevant when a shared session opens many tables with distinct storage options, such as
  tables opened through a namespace that vends per-table credentials" (`:77`). Before it, dead
  registry entries "accumulate forever" - a few KB per table opened through a shared `Session`.
- **`local_fsync`** (#9609, beta.6) - default `"false"`; when `"true"`, "Lance syncs local data,
  transaction, and manifest files before reporting successful writes, including copied files
  during deep clones" (`:158-163`). "Pass the option again when reopening a dataset for later
  writes; it is a store setting, not a dataset property." Without it a crash could leave "an empty
  latest manifest or data file" (#9609), and such errors now carry the path.

**Explicit cloud options now beat environment variables** (#9719, `v14.0.0-beta.11`). Before it,
"Explicit cloud storage options such as `region` could lose to `AWS_REGION` because environment
merging compared key spellings", and conflicting aliases (`region` and `aws_region` both set)
resolved by HashMap iteration order across the AWS, Azure and GCP conversions. Now any spelling a
caller supplies blocks the environment default for that key, and alias conflicts resolve
deterministically: exact canonical spelling first, then its case variants, then lexical order
(`rust/lance-io/src/object_store.rs:1920-1975`, `aws.rs:655-690`). On an older pin, unset the
conflicting `AWS_*` variable rather than trusting the option. Two exceptions survive at
`v15.0.0-beta.10`: `StorageOptions::new` still overwrites `allow_http`, `client_max_retries` and
`client_retry_timeout` from `AWS_ALLOW_HTTP` / `AZURE_STORAGE_ALLOW_HTTP` /
`AZURE_STORAGE_USE_HTTP` / `OBJECT_STORE_CLIENT_MAX_RETRIES` / `OBJECT_STORE_CLIENT_RETRY_TIMEOUT`
whenever those are set (`object_store.rs:1978-1996`), and GooseFS master addressing ranks the
environment first (below).

**`request_timeout` is not a key** - it appears in no Lance source at any recent tag, and #8706
corrected the docs to `timeout`. Anything still passing `request_timeout` is silently setting
nothing. `timeout` bounds the *entire* request, from connection until the response body
finishes, and applies per individual request - so on a large write it must cover one complete
multipart part upload. Raise it alongside `LANCE_INITIAL_UPLOAD_SIZE`.

**Multipart part sizing** - `LANCE_INITIAL_UPLOAD_SIZE` sets the first part's size, clamped to
5 MB..5 GB minus one byte (values outside the range are clamped with a warning, not rejected;
"AWS rejects single-PUT bodies of exactly 5 GiB", `rust/lance-io/src/object_writer.rs:62-73`).

**AIMD request throttle.** Cloud stores sit behind one AIMD rate controller per operation class
(reads, writes, deletes, lists; `docs/src/guide/performance.md:363-383`). `v14.0.0` raised the
default ceiling **5000 -> 10000 req/s** (#10153; `rust/lance-core/src/utils/aimd.rs:47-49`,
initial rate 2000): "Under sustained success, the default rate grows from 2000 to 10000 requests/s
in about 27 seconds." Tune with `lance_aimd_*` storage options or `LANCE_AIMD_*` env vars
(`performance.md:370-377`). Deletes are budgeted too since #9707 (`v14.0.0-beta.15`):
"`AimdThrottledStore::delete_stream` previously forwarded deletes without acquiring delete
tokens"; now each request attempt takes a token and generic stores issue at most 10 concurrent
deletes (`rust/lance-io/src/object_store/throttle.rs:56`). Cleanup adds its own
`delete_concurrency` / `delete_rate_limit` (#9774; `lance.auto_cleanup.*` table config,
`docs/src/guide/read_and_write.md:916-923`).

**Bulk copy strategy** (v12, #8770). Set `LANCE_IO_SERVER_SIDE_COPY_ENABLED` to a truthy value
(`1`, `true`, `on`, `yes`, `y`, case-insensitive) to route cloud copies whose source and
destination share the same object-store client into the provider-native server-side copy
operation instead of streaming bytes through the client - the relevant case for index movement
and for copying between two prefixes of one bucket (`object_store.md:165-182`). Deep clone
separately bounds non-local file movement to four concurrent files;
`LANCE_DEEP_CLONE_STREAM_CONCURRENCY` overrides that operation-specific limit
(`rust/lance/src/dataset.rs:221,3758`).

Per-backend highlights:

- **S3** - `aws_region`, `access_key_id` / `secret_access_key` / `session_token`,
  `aws_endpoint` (for S3-compatible stores like MinIO - both region and endpoint required),
  `aws_server_side_encryption` (`AES256` / `aws:kms` / `aws:kms:dsse`) + `aws_sse_kms_key_id`.
  `AWS_PROFILE` is environment-only. New in v11: **`aws_provider_scheme`** (PR #8103) pins a
  dataset to one credential provider instead of the default chain - "useful when two datasets in
  the same process need different AWS auth (for example, one bucket using IRSA and another using
  ECS container credentials)" (`docs/src/guide/object_store.md:303-306`). Exactly three values,
  each failing hard rather than falling back: `token` (static credentials), `ecs` (container
  credentials), and `irsa`, which "Reads `AWS_WEB_IDENTITY_TOKEN_FILE` and `AWS_ROLE_ARN` from
  the environment" (`:312`). Anything else errors with "Invalid aws_provider_scheme '{}'. Valid
  values are: token, ecs, irsa" (`rust/lance-io/src/object_store/providers/aws.rs:698`).
- **S3 conditional copy defaults to `multipart`** from `v14.0.1` (#10364, main #10363): the
  builder sets `S3CopyIfNotExists::Multipart` unless the caller overrides
  `aws_copy_if_not_exists` (`aws.rs:148-170`). `v14.0.0` (PyPI / Maven only) instead used a
  git-patched streamed conditional copy, which is why that release never reached crates.io.
- **S3-compatible endpoints: set the region explicitly, and know why.** The docs state the
  requirement plainly - `aws_region` "must be specified for S3-compatible stores"
  (`object_store.md:287`) - because SigV4 embeds the region in the signed credential scope even
  when the endpoint is not AWS. But the code does **not** enforce it: with an endpoint and no
  region option, `resolve_s3_region` returns only the AWS profile's region, possibly `None`
  (`aws.rs:331-365`), and credential building then falls through the AWS SDK default region chain
  to `DEFAULT_REGION = "us-west-2"` (`aws.rs:406-426`). There is no error path for a missing
  region, so an omitted `aws_region` **silently signs with whatever region the environment
  happens to carry, else `us-west-2`**, rather than failing fast - producing signature errors, or
  worse, quiet misrouting on providers that accept any region string. Third-party endpoints also
  usually need `virtual_hosted_style_request` (or `aws_virtual_hosted_style_request`) set
  explicitly - both spellings parse to one `object_store` config key (`aws.rs:686`), and
  since #9719 the canonical `aws_` spelling wins when both are given; it defaults to `False`
  (`object_store.md:292`).
- **S3-compatible stores may fake conditional writes** (docs, #9763, `v15.0.0-beta.2`): "Some
  S3-compatible stores, including Garage, accept this header but ignore the condition and
  overwrite existing objects. Concurrent writers can then both report success while silently
  losing acknowledged data. Lance does not check whether the store enforces this condition"
  (`object_store.md:386-396`). Verify `If-None-Match: *` enforcement, or give every writer the
  same distributed `commit_lock` (Python) / `CommitLock` or `CommitHandler` (Rust) (`:399-414`).
- **S3 Express** - directory buckets; auto-recognized via the `--x-s3` suffix, or set
  `s3_express: "true"`; reachable only from a same-region EC2 instance. Its listing is not
  lexically ordered, so the `latest_version_hint.json` mechanism accelerates latest-version
  lookup there.
- **GCS** - `GOOGLE_SERVICE_ACCOUNT` (JSON file) or `service_account_key`. Default HTTP/1;
  `HTTP1_ONLY=false` for HTTP/2.
- **Azure** - `account_name` / `account_key`, service principal, SAS tokens, managed
  identity, workload-identity federation.
- **Alibaba OSS** - `oss_endpoint` (required), `oss_access_key_id`, `oss_secret_access_key`.
- **Tencent COS** (`object_store.md:566`) - `cos://bucket/path` with `cos_endpoint`,
  `cos_secret_id`, `cos_secret_key`, and optional `cos_enable_versioning`; env vars are read
  from the `COS_` or `TENCENTCLOUD_` prefixes. **Writes need a commit lock**: "Tencent COS does
  not reliably enforce put-if-not-exists on buckets that have ever had versioning enabled, even if
  versioning is now suspended. To prevent silent manifest overwrites, Lance requires a custom
  distributed commit lock for COS writes" (`:616-621`; `TencentCosCommitHandler`,
  `rust/lance-table/src/io/commit.rs:1276`, since #8369 in v11). Reads need none.
- **Volcengine TOS** (new in v8, `object_store.md:536`) - `tos://bucket/path` with
  `tos_endpoint` required (e.g. `https://tos-cn-beijing.volces.com`), plus `tos_region` and
  access-key options; env vars `TOS_*` or `VOLCENGINE_*`.
- **GooseFS** (new in v8, feature-gated `goosefs`, documented at `object_store.md:660`) -
  `goosefs://host:port/path` (default port `9200`), or `goosefs:///path` with an empty authority
  (v13.0.0, #9364). **The master address resolves environment-first**, "highest priority first:
  1. The `GOOSEFS_MASTER_ADDR` environment variable. 2. `goosefs.master.rpc.addresses` or
  `goosefs.master.hostname` in `goosefs-site.properties` ... 3. The `goosefs_master_addr` storage
  option ... 4. The host and port from the URL authority" (`object_store.md:811-822`). That is the
  reverse of the cloud-provider rule above: an exported `GOOSEFS_MASTER_ADDR` or a site file on
  the host silently outranks the address you pass, so a per-dataset `goosefs_master_addr`
  (HA-aware: `"addr1:port,addr2:port"`) only takes effect where neither exists. Optional keys:
  `goosefs_write_type` (`MUST_CACHE` / `CACHE_THROUGH` / `THROUGH` / `ASYNC_THROUGH`),
  `goosefs_auth_type` (`nosasl` / `simple`), `goosefs_auth_username`, `goosefs_block_size`,
  `goosefs_chunk_size` (`rust/lance-io/src/object_store/providers/goosefs.rs:31-39`).

  **`storage_options` keys must be lowercase** (#8940, `v12.0.0-beta.12`) - a wrong-case key is
  now a hard error rather than a silently ignored value: "Uppercase or mixed-case spellings such
  as `GOOSEFS_MASTER_ADDR` are rejected with an explicit error - they are not ignored, and they
  are not treated as the matching environment variable" (`object_store.md:831-833`). A config
  that appeared to work by accident will start failing loudly on upgrade.

  **`goosefs_block_size` / `goosefs_chunk_size` accept unit suffixes** (#8943): "Accepts a raw
  byte count or GooseFS suffixes such as `64MB` (binary units: `1KB = 1024`). Optional."
  (`object_store.md:840-841`).
  **In v11 GooseFS commits became safe** (PR #8134): manifest commits now use
  `ConditionalPutCommitHandler` (`PutMode::Create` / if-not-exists), "backed by GooseFS master's
  atomic no-replace rename so concurrent writers cannot clobber each other's versioned
  manifests" (`object_store.md:674-677`), replacing `UnsafeCommitHandler`. **Mixed-version
  writers are a data-loss hazard during the rollout**: "The `if-not-exists` guarantee only holds
  when **every** writer for a dataset routes through this new handler. A writer running an older
  Lance release still selects `UnsafeCommitHandler` for `goosefs://` and writes the version path
  unconditionally, which can overwrite a manifest that an upgraded writer has already won"
  (`:681-686`). Upgrade all writers before relying on it.

**Unrecognized schemes default to conditional put from `v15.0.0-beta.8`** (#8773). Before it,
"every other scheme fell through to `UnsafeCommitHandler`, which blind-writes the manifest with no
create-if-not-exists guard" - the case for out-of-tree providers registered at runtime. Now the
fallback arm is `_ => Ok(Arc::new(ConditionalPutCommitHandler))`
(`rust/lance-table/src/io/commit.rs:1339-1347`), so concurrent commits "fail loudly with a
conflict instead of silently clobbering each other's manifests"; a store without conditional put
must supply its own commit handler. The v14 line (stable pin included) still falls back to
`UnsafeCommitHandler` - the same mixed-version hazard as GooseFS above.

**Multipart upload retries (v11, PR #8174).** A failed part upload used to be retried by calling
`MultipartUpload::put_part` again, but "Native cloud stores allocate a new part number when that
method is called, so the retry skipped the failed part and completion reported `Missing part`."
Retries now happen inside the HTTP connector, preserving part identity, for native S3/Azure/GCS.
The `LANCE_CONN_RESET_RETRIES` env var (default 20) was removed along with the old writer-level
resubmission path. #9913 (`v14.0.0-beta.16`) closed the completion side: `complete` "drains the
recorded part ids before it sends the completion request", so its retries also failed with
"Missing part"; it is now called once and retried at the HTTP layer. **OpenDAL stores got retries
only in `v15.0.0-beta.8`** (#8363): a shared `RetryLayer` on the OpenDAL S3, Azure, GCS, TOS, OSS,
COS, Hugging Face and GooseFS stores, reusing `client_max_retries` ("the existing default is 3 and
0 disables retries"), for errors OpenDAL marks temporary, with exponential backoff from 100 ms to a
15 s base delay plus jitter. On the v14 line a transient 429 from an OpenDAL backend still fails
the request.

**`LANCE_*` changes in the v11 range.** One removal (`LANCE_CONN_RESET_RETRIES`, above) and two
additions, both from the AMX-FP16 work in `beta.16` (PR #8540):

| Variable | Scope | Effect |
|----------|-------|--------|
| `LANCE_DISABLE_AMX` | runtime | Kill switch for the AMX-FP16 paths. Also reverts IVF partition assignment to the approximate path, so an index built with it set is **not** equivalent to one built without it |
| `LANCE_AMX_FP16_CC` | build time | Overrides the compiler used to build the AMX kernel (`rust/lance-linalg/build.rs:28`); the kernel needs clang >= 16 or gcc >= 13 |

Grep trap: `LANCE_AMX_CFG_SEARCH`, `LANCE_AMX_CFG_GEMM`, and `LANCE_AMX_TILE_COUNT` look like
env vars in a tree-wide `LANCE_[A-Z_]*` grep but are **C preprocessor macros** in
`rust/lance-linalg/src/simd/amx_fp16.c:107-137`. They are not readable from the environment.

**Base-aware access (v7).** `Dataset::object_store` takes an `Option<u32>` base id - `None`
for the primary store, `Some(base_id)` for an additional base. Caching/instrumentation
wrappers are applied per `store_prefix` and propagate to all base stores.

**Per-base `storage_options` (v9, PR #7608).** For multi-base datasets you can scope a storage
option to one base with a `base_<id>.<key>` key (`docs/src/guide/object_store.md:185-216`): "A
storage option key of the form `base_<id>.<key>` applies `<key>` only to the base path with
that manifest id. Every base inherits the unscoped options; base-scoped entries add to or
override them for that base only." Base ids are assigned when bases are registered
(`initial_bases` ids "are assigned sequentially starting at 1, in order"); keys that don't match
the pattern exactly (e.g. `base_url`) are treated as regular options. Precedence: an exact
per-base parameter map (`base_store_params`, keyed by base-path URI) beats a `base_<id>.<key>`
scoped key.

**Storage options are not table config.** Per-dataset settings that persist with each version
(`lance.auto_cleanup.*`, `lance.compaction.*`, ...) live in the manifest `config` map; their
registry is `docs/src/format/table/table_config.md` (new on the v15 line), where "Keys prefixed
with `lance.` are reserved for the Lance library itself" and "Unrecognized keys, including
unrecognized keys with a `lance.` prefix, should be ignored by readers" (`:5-12`).

**v10 object-store and runtime changes.**

- **`memory://` datasets could spuriously fail** with `DatasetNotFound` in optimized builds:
  `ObjectStoreParams` Hash/Eq keyed on a trait-object fat pointer, and "Trait object pointers
  include vtable metadata, which is not stable across codegen units. Cache identity must follow
  the Arc allocation instead" (PR #8068).
- **No more panic on tokio runtime shutdown** mid-read - an in-flight parallel read now returns
  an I/O error, "I/O request was dropped before completion ({} of {} reads delivered)"
  (`rust/lance-io/src/scheduler.rs`, PR #7478).
- **`LANCE_CPU_THREADS` and `LANCE_IO_CORE_RESERVATION` are now validated** instead of
  `.parse().unwrap()`-panicking on garbage (`rust/lance-core/src/utils/tokio.rs:24-75`,
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
- **`lance-namespace` pins split across the bindings in v13-v15.** Rust's
  `lance-namespace-reqwest-client` moved 0.12.0 -> **0.13.0** at `v13.0.0` (#9184) while Python
  stayed at `>=0.11.1,<0.12` and Java at 0.12.0. v14 (#9822, `v14.0.0-beta.10`) moves Python to
  **`>=0.13.0,<0.14`** "so the released Python SDK can be consumed alongside clients using the new
  probe-bound fields" (`maximum_nprobes = 0` now decodes as the unbounded sentinel); Java is still
  0.12.0, and all three pins are unchanged through `v14.0.2` and `v15.0.0-beta.10`. A `v13.0.0`
  pylance therefore cannot be resolved into one environment with a lance-namespace 0.13 client.
- **REST namespace wire changes in `v14.0.0`** (all `v14.0.0-beta.22`). #9993: `count_rows`,
  `tags/list`, `stats` and index stats are POST, and `count_rows` returns a bare integer -
  "Compatibility: a client from an earlier release gets 405 from a new adapter on
  `list_table_tags`." #10190 conforms `RestNamespace` / `RestAdapter` to the spec (identity sent as
  `x-api-key` and `Authorization`, `branch` forwarded on insert / merge_insert / index drop, spec
  `ErrorResponse` 400s). #10192 adds `batch_create_table_versions`, `batch_commit_tables` and
  `update_field_metadata` to `LanceNamespace`, defaulting to not supported. #9998 fixes the
  DirectoryNamespace manifest keying tables and namespaces by one id: "`drop_namespace` on a
  table's id deleted the table's manifest entry and left its data on disk."
- **Latest-version resolution stopped listing the whole prefix** (v12, PR #8679). It previously
  walked all of `_versions/`: on a ~340k-version table that is ~344 sequential `ListObjectsV2`
  pages, "~25s of pure I/O wait", paid by every `open_table` / `describe` / `merge_insert` that
  resolves the latest version. Heals purely on upgrade. A related v14 fix, #9691: on stores
  without ordered listing a retry after partial output could skip keys, and "Latest-manifest
  lookup could then select an older dataset version"; it now errors instead.

`latest_version_hint.json` (`{"version": N}` under `_versions/`) gives fast latest-version
lookup on stores where listing is not lexicographically ordered (S3 Express, local FS); it is
purely an optimization, always safe to delete, and skipped where listing is already ordered.
Disable globally with `LANCE_USE_VERSION_HINT=0`.

---

## 15. Capability matrix

What Lance can and cannot do at `v15.0.0-beta.10`; rows that differ on the `v14.0.2` stable pin
say so.

**Storage and format**

| Capability | Status |
|------------|--------|
| Local FS, S3 (+ S3-compatible, incl. Apache Ozone via its S3 Gateway), S3 Express, GCS, Azure, Alibaba OSS, Tencent COS, Volcengine TOS | yes |
| GooseFS (`goosefs://`) | yes (feature-gated `goosefs`) |
| In-memory store (`memory://`, `shared-memory://`) | yes |
| Durable local writes (`local_fsync`) | yes, opt-in (v15 line only) |
| Multi-base storage (hot/cold, multi-region, shallow clone) | yes (`FLAG_BASE_PATHS`) |
| File format 2.1, 2.0, legacy 0.1 (read-only) | yes |
| File format 2.2 (Map type, Blob v2) - **the current default** | yes, stable |
| Mixed exact V2 versions within one dataset | yes (`FLAG_MIXED_DATA_FILE_VERSIONS`, v12 final) |
| File format 2.3 Planar pages (sparse structure, generic block codecs) | yes, but `next` / unstable; 2.3 files written before `v14.0.0-beta.22` are unreadable (#9921) |
| Concurrent writes on plain `s3://` | yes (native conditional PUT) - only if the provider really enforces `If-None-Match: *`; otherwise a shared commit lock |
| Concurrent writes on `cos://` | only with a custom distributed commit lock |
| Concurrent writes - GCS / Azure / local | yes |
| Concurrent writes on an unrecognized (runtime-registered) scheme | conflict-safe by default from `v15.0.0-beta.8` (#8773); unsafe on v14 |

**Data and schema**

| Capability | Status |
|------------|--------|
| Full Arrow type system, nested structs/lists | yes |
| Map type | yes (file format 2.2) |
| JSON type (JSONB), JSON path filtering and indexing | yes |
| Blob v2 - large binary, lazy `BlobFile` streaming, external URIs | yes (2.2) |
| Managed blobs (`_blobs/<uuid>.blob`, bit `2^14`) | yes, opt-in via `lance.blob.managed=true`; sticky; v14+ readers only |
| Zero-copy add/drop/rename column (metadata-only) | yes |
| Cell-level updates without base-file rewrite (data overlay files) | yes, but unstable (env-gated `LANCE_ENABLE_UNSTABLE_DATA_OVERLAY_FILES`; release builds refuse) |
| Row lineage spilled to hidden data-file columns (`lance.row_lineage.spill`, bit `2^11`) | yes, stable since `v14.0.0-beta.16` (#9802); opt-in per table; `v13.0.0` refuses such a table |
| Fragment metadata tree (fragment records outside the manifest, `_bt/`, bit `2^12`) | no - spec only; readers and writers reject the bit |
| Type change / cast | yes (rewrites that column; drops its index) |
| Time travel, tags, branches | yes |
| Stable row IDs (opt-in at creation; existing datasets can migrate) | yes |
| Change data feed | yes (stable row IDs only) |

**Indexes and search**

| Capability | Status |
|------------|--------|
| Vector ANN - IVF + FLAT/HNSW + FLAT/PQ/SQ/RQ (RQ multi-bit, `num_bits` 1..=9; `approx_mode` fast/normal/accurate) | yes |
| ACORN-1 prefiltered HNSW traversal | yes, opt-in (`approx_mode="fast"`) |
| Distance metrics L2 / Cosine / Dot / Hamming | yes |
| Scalar - btree, bitmap, label-list, ngram, zonemap, bloom filter, FM-Index | yes |
| FM-Index substring / prefix / regex search on raw bytes | yes (segment-based) |
| Full-text search - BM25, multilingual tokenizers, phrase queries | yes (Lance-native); stop-word lists rewritten in `v14.0.0`, rebuild older indexes |
| Geo / RTree spatial index + geo UDFs | yes (`geo` feature) |
| Distributed / segmented index builds (vector, bitmap, btree, FTS, ngram, rtree, zone map, bloom filter, label-list) | yes (no scheduler) |
| Hamming clustering / near-duplicate detection over binary hashes | yes (v9 utility) |
| MinHash LSH near-duplicate text index | yes, **experimental** (v13.0.0; format may change, rebuild required) |
| `COUNT(*)` pushdown | yes (fast path on stable-row-id datasets) |
| SQL over datasets | via DataFusion (`LanceTableProvider`) - projection / filter / limit only, **no vector search**, see below |

**Concurrency and ops**

| Capability | Status |
|------------|--------|
| MVCC + optimistic concurrency, automatic rebase | yes |
| Pluggable commit handlers (conditional-put, DynamoDB, lock) | yes |
| MemWAL high-throughput streaming writes | yes, **experimental** |
| Two-phase distributed write | yes |
| Namespaces (Directory, REST) + DataFusion catalog bridge | yes (REST wire changed in `v14.0.0`, #9993) |
| Compaction, version cleanup, fragment reuse index | yes |
| Retries on OpenDAL-backed stores | yes from `v15.0.0-beta.8` (#8363); none on v14 |

**Not in Lance** - a query-builder API, an embedding registry, rerankers as an API, managed
Cloud/Enterprise tiers (those are LanceDB, a separate product); authentication / user
identity; a built-in cross-dataset join planner (use DuckDB/DataFusion on top); a metrics
dashboard.

**The SQL surface has no vector search.** `LanceTableProvider::scan` pushes down projection,
then filter, then limit, then in-order-ness, and calls `create_plan_with_session()`
(`rust/lance/src/datafusion/dataframe.rs:155-222`) - it never calls `Scanner::nearest`, and the
symbol appears nowhere in the DataFusion glue. There is no `ORDER BY vec <-> query LIMIT k`
operator and no vector-distance UDF: `register_functions` adds `contains_tokens` and the JSON
functions (`rust/lance-datafusion/src/udf.rs:24-36`; on the v15 line `contains_tokens` lives in
`lance-datafusion-exec`), plus geo UDFs (`st_distance` / `st_area` / `st_intersects`) when the
non-default `geo` feature is on, or error-raising stubs when it is off (`udf.rs:38-60`) - those are
geometric, not embedding, distances. **An IVF/HNSW index is therefore unreachable from
`Dataset::sql()`**; use the scanner API (`Scanner::nearest`) for ANN and reserve SQL for
relational work. FTS is the exception - it *is* SQL-reachable through the registered `fts` table
function (`ctx.register_udtf("fts", ...)`, `rust/lance/src/dataset/udtf.rs:309`), but
`Dataset::sql()` itself registers only the table plus `register_functions`, so there is no vector
analogue of that escape hatch.

---

### 15.1 Operational notes that bite

**Migrating an existing dataset to stable row IDs has a prerequisite checklist.** Upstream now
documents the procedure rather than treating creation-time opt-in as the only path, and the
prerequisites are strict: "Before migration, stop all index builds and index commits, drop every
secondary index so no index entry remains in the dataset metadata, and keep index creation
quiesced until migration completes." There is a legacy-manifest pre-step too - run a no-op
`false`-predicate delete first to recompute physical row counts, because "affected releases may
have recorded stale counts, which would produce incomplete row ID sequences." Do not run the
migration directly on such a manifest.

**Lance exposes no dataset-level identity, which quietly breaks external caches.** There is no
dataset UUID, and every candidate identity - fragment ids, row ids, version numbers - **restarts
when a dataset is recreated**. So a cache keyed on any of them still looks current after the
dataset it described was dropped and rebuilt, and silently answers against different data. The
check that actually works needs no new persisted state: sample a few row ids and `take_rows` them
from the dataset; if what comes back disagrees with what the cache recorded, the cache describes
a different dataset - discard and rebuild.

**An index-free copy is not a dataset root minus `_indices`.** `_indices` is part of the root and
manifests can reference index metadata, so copying a dataset directory and deleting the index
subtree produces a root whose manifest points at things that are gone. For an index-free archive,
write fresh dataset roots from scans instead of editing a copied one.

**Net-new surface worth knowing** (v12 final and the v13 line): `Dataset::frag_reuse_index()` is
public (#9112) and returns `None` when the loaded version has no FRI; `FileFragment::write_overlay`
returns a real `OverlayWriter` keyed by `_rowaddr` (#8761, still env-gated behind
`LANCE_ENABLE_UNSTABLE_DATA_OVERLAY_FILES`); Python gained `lance.bitmap.Bitmap` (a real
RoaringBitmap binding, #7837), `deep_clone()` (#9181), `base_paths()` (#9191) and
`update_columns(with_offsets=True)` (#8891); Java gained `DataStorageVersion`, `FileWriteOptions`
and `ScanOptions.indexSegments`. Namespace table listing is finally bounded - #9165 moved
`list_directory_tables` onto the v12 `read_dir_page` so "a bounded caller only pays for what it
asks for", with a 1000-entry page hint.

**A third real `LANCE_*` env var landed**: `LANCE_COMMIT_RETRY_TIMEOUT_SECS` (#9177) overrides
the commit retry timeout, still 30s by default. That makes the full set `LANCE_DISABLE_AMX`,
`LANCE_AMX_FP16_CC` and this one - plus the overlay gate above. The old grep trap still holds:
`LANCE_AMX_CFG_*` and `LANCE_AMX_TILE_COUNT` are C macros, and `LANCE_FACTOR` is a substring of
`BALANCE_FACTOR`.

**Two more arrived in `v13.0.0`; one of them left in `v14.0.0`.**

| Variable | Effect |
|----------|--------|
| `LANCE_ENABLE_UNSTABLE_SPILLED_ROW_LINEAGE` | **Removed in `v14.0.0`** (#9802): bit `2^11` is supported in every build, and table config alone decides whether a writer spills. On `v13.0.0` it opted a release build into reading and writing spilled lineage (#9253), **presence-only** - `std::env::var_os(..).is_some()`, so `=0` or `=false` still enabled it. The overlay gate keeps that pattern (`rust/lance-table/src/feature_flags.rs:446-448`) |
| `LANCE_SHUFFLE_MAX_PRELOADED_OFFSETS_BYTES` | Per-shuffle budget for the IVF two-file shuffler's preloaded offsets table (#9434), default 256 MiB (`rust/lance-index/src/vector/v3/shuffler.rs:606-607`). `0` disables preloading; invalid values error. The limit "applies to each shuffle, so memory use adds up across concurrent builds" and excludes decoded data and index construction (`docs/src/guide/distributed_indexing.md:96-115`) |

No user-facing `LANCE_*` variable was added between `v14.0.0-beta.14` and `v14.0.2`. The v15 line
adds tuning knobs absent from every v14 tag: `LANCE_FTS_POSTING_GROUP_MAX_BYTES` /
`LANCE_FTS_POSTING_GROUP_MAX_TOKENS` (mutually exclusive; byte default 32 KiB,
`rust/lance-index/src/scalar/inverted/index/grouping.rs:7-10`), `LANCE_TUPLE_MAX_SEEKS` (default
8192 seeks per planned tuple query, `rust/lance-index/src/scalar/tuple/planner.rs:86-89`), and the
IVF_RQ residency / latency knobs `LANCE_RQ_ORIGIN_LATENCY`, `LANCE_RQ_RESIDENT_COLUMNS`,
`LANCE_RQ_RESIDENT_LIFETIME`, `LANCE_RQ_ENTRY_COLUMNS` and the benchmark knob
`LANCE_RQ_SEQUENTIAL_PLANE_LOADS` (`rust/lance-index/src/vector/storage.rs:806-1111`).

Grep trap for this range: `LANCE_BTREE_BENCH_MANY_FRAG_ROWS`,
`LANCE_TEST_SHUFFLE_OFFSET_PRELOAD_CHILD`, and on v15 `LANCE_*_TEST*` names such as
`LANCE_SESSION_METRICS_TEST` or `LANCE_THINNING_TEST_URI` match a `LANCE_[A-Z_]*` sweep but are
test and bench hooks, not user knobs.

## 16. Source map

Where to look in `lance-format/lance` at `v15.0.0-beta.10`.

| Topic | Path |
|-------|------|
| Format spec overview | `docs/src/format/index.md` |
| File format | `docs/src/format/file/{index,encoding,versioning}.md` |
| Table format | `docs/src/format/table/{index,layout,schema,transaction,versioning,branch_tag,row_id_lineage,mem_wal,data_overlay_file,fragment_metadata,blob,table_config,clustering}.md` (`fragment_metadata.md` is the experimental fragment tree, new in v13.0.0; `clustering.md` is new in `v14.0.0`; `blob.md` (Blob v2 contract) and `table_config.md` (the `lance.*` config key registry) are new on the v15 line. `jsonb.md`, added in `v14.0.0-beta.14`, was reverted by #9889 in beta.15 and is absent from every final) |
| Index spec | `docs/src/format/index/{index.md,vector/,scalar/,system/}` (scalar incl. `scalar/fmindex.md`, `scalar/minhash_lsh.md`, `scalar/json.md`, `scalar/zone_write_seeds.md`, new in `v14.0.0`) |
| User guide | `docs/src/guide/{arrays,blob,data_evolution,data_types,json,object_store,observability,read_and_write,performance,tags_and_branches,tokenizer,distributed_write,distributed_indexing,migration,full_text_search,indexing,row_ids,scalar_indexing,update_join,vector_search}.md` (the last six are new on the v15 line) |
| Integrations | `docs/src/integrations/{index,datafusion,pytorch,tensorflow}.md` |
| Protobuf schemas | All 17: `protos/{file,file2,table,fragment_metadata,transaction,rowids,index,index_old,ann,filtered_read,table_identifier,encodings_v2_0,encodings_v2_1,encodings_v2_3,clustering,fts,cache_diagnostics}.proto`. `v14.0.0` has 15: `clustering.proto` (#9878) and `encodings_v2_3.proto` (the independent 2.3 Planar grammar, #9920) arrived in `v14.0.0-beta.22`; `fts.proto` (#8938, `v15.0.0-beta.8`) and `cache_diagnostics.proto` (#9781, `v15.0.0-beta.10`) are v15 only. `fragment_metadata.proto` (new in v13.0.0 by #9060) holds `DataFragment` / `DataFile` / `DeletionFile`, moved out of `table.proto`; `index_old.proto` is a v9 forward-compat shim; `file.proto` is the legacy v1 container |
| Rust workspace | `rust/` (entry point `rust/lance/`). **28 crate dirs at `v15.0.0-beta.10`**, the newest `rust/lance-datafusion-exec` (#10251, `v15.0.0-beta.2`: "add lance-datafusion-exec so lance-index skips datafusion"); **27** through the whole v14 line, whose newest is `rust/lance-jsonb` (the JSONB codec vendored from the external `jsonb` crate by #9534, `v14.0.0-beta.9`) |
| Commit / OCC | `rust/lance/src/io/commit.rs`, `rust/lance-table/src/io/commit.rs` (`commit_handler_from_url`, the scheme -> handler table, `:1249-1347`) |
| Transactions | `rust/lance-table/src/transaction/` (moved out of `rust/lance/src/dataset/transaction.rs` in v11 by #8053/#8054/#8056; `lance::dataset::transaction` survives as a re-export shim) |
| MemWAL | `rust/lance/src/dataset/mem_wal/` |
| Indexes | `rust/lance-index/src/` |
| Object store | `rust/lance-io/src/object_store/` (AIMD defaults in `rust/lance-core/src/utils/aimd.rs`) |
| Table config keys | `docs/src/format/table/table_config.md` |
| File-version identity | `rust/lance-file/src/version.rs` (both `LanceFileVersion` and `ConcreteFileVersion`; `lance-encoding/src/version.rs` was deleted in v11) |
| Cache keys / backends | `rust/lance-core/src/cache/` (`key.rs`, `quick.rs`, `moka.rs`, `backend.rs`, `codec.rs`, `registry.rs`) |
| Data overlay resolution | `rust/lance/src/dataset/overlay.rs` |
| Release train / breaking detection | `ci/publish_beta.sh`, `ci/check_breaking_changes.py`; rcs and patch finals via `create-release-branch.yml`, `create-rc.yml`, `approve-rc.yml` on `release/vX.Y` (`release_process.md`) |

**`TableIdentifier` (`protos/table_identifier.proto`)** is how a table is handed to a remote
executor for distributed read/write, and it has two modes the filename alone does not reveal:
"1. uri + serialized_manifest (fast): remote executor skips manifest read. 2. uri + version +
etag (lightweight): remote executor loads manifest from storage" (`:11-12`). Mode 1 trades
message size for a saved round trip - the right default when the manifest is already in hand
and the executor count is modest; mode 2 keeps the message small when fanning out widely, at
one manifest read per executor.

Auto-generated API docs and the language-agnostic namespace spec live in sibling repos under
`github.com/lance-format`. The canonical docs site is `lance.org`. To refresh this reference,
see the maintenance note in `../SKILL.md`.
