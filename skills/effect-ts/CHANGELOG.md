# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-07-01
### Added
- `migration-v4.md`: extended the "v4 beta additions" ledger from beta.78 to beta.92 (SchemaError now a tagged `Data.TaggedError`; `Schema.Void` void-return semantics; `Config.make` removed + `Config.withDefault`/`Config.schema` recovery changes; `Effect.try` thunk form; `RpcGroup.toHandlers` definition-first; `Effect.transposeOption`; `Effect.fromOption` callbacks; `Random.choice`; `Latch.isOpen`; `String.configCase`; `Statement.valuesUnprepared`; `Schema.toCodecArrayFromSingle`; `Graph.successors`/`predecessors`; arbitrary-derivation metadata migration; HTTP API streaming responses).
- `concurrency.md`: child-process execution via `effect/unstable/process` (`ChildProcess`, `ChildProcessSpawner`; `spawner.string`/`lines`/`spawn`, `ChildProcess.pipeTo`).
- `dependency-injection.md`: `LayerMap.Service` for per-key dynamic layers, and a `ManagedRuntime` bridge pattern for non-Effect frameworks (Hono/Express) with fiber-local request context via `Context.Reference`.
- `resource-management.md`: `RcRef`/`RcMap` reference-counted shared resources.
- `streams.md`: stream framing/encoding via `Stream.pipeThroughChannel` + `Ndjson`/`Msgpack` (`effect/unstable/encoding`).
- `schema.md`: note that `SchemaError` is a tagged `Data.TaggedError` (catchable via `Effect.catchTag`).
- SKILL.md progressive-disclosure index entries for the new concepts.
### Changed
- `llm-corrections.md` + SKILL.md: corrected `Schema.makeOption`/`makeEffect` to instance methods (`schema.makeOption(...)`); softened the unverified "PR #2057" attribution for HttpApi-errors-as-defects to a source-grounded statement.
### Fixed
- `error-modeling.md`: warn that `Effect.catch`/`catchTag` don't catch defects or interrupts (use `catchDefect`/`catchCause`) and that `Effect.catch(() => Effect.void)` silently swallows the typed error.
- `concurrency.md`: clarify that `Effect.forkDetach` parents to the global scope (survives `runtime.dispose()`); use `Effect.forkScoped` for runtime-tied background fibers.

Verified against: effect@4.0.0-beta.92

## [0.5.0] - 2026-06-09
### Added
- `concurrency.md`: Request / RequestResolver section (batching, dedup, N+1 elimination via `Effect.request`).
- `effect-ai.md` + `retry-scheduling.md`: `ExecutionPlan` for ordered multi-provider fallback (`Effect.withExecutionPlan`).
- `http.md`: Multipart file-upload section (`HttpApiSchema.asMultipart`, `Multipart.SingleFileSchema`/`FilesSchema`, limit references).
- `testing.md`: property-based testing via `Schema.toArbitrary` + `FastCheck` (from `effect/testing`).
- `schema.md`: branded / nominal types (`Brand.nominal`/`check`/`make`/`all`; notes v4 has no `refined`/`error`).
- `resource-management.md`: `Resource` (refreshable scoped value via `Resource.auto`/`manual`/`refresh`).
- `core-patterns.md` + SKILL.md: `Effect.fnUntraced` guidance (use it for helpers that don't need a span/stack-frame; reserve named `Effect.fn` for traced operations).
- SKILL.md progressive-disclosure index entries for the new concepts.

### Changed
- Repositioned the skill to recommend Effect v4 as the default while keeping full v3 support. The stance is now "prefer v4 for new projects; in an existing codebase match the installed version, default to v4 when unclear."
- `SKILL.md` description now leads with v4 (the recommended default) instead of presenting v3/v4 as co-equal.
- Version Detection: lists v4 first, replaces the v3-default guidance, keeps the beta caveat (pin an exact `4.0.0-beta.x`).
- Primary documentation sources grouped as v4 (primary) / v3 (existing codebases) / both.
- Flipped `v3 / v4` orderings to `v4 / v3` in the starter function set, key modules, DI list, and import patterns so v4 reads as primary.

## [0.4.0] - 2026-06-04
### Added
- CHANGELOG; upstream tracking established.
- `references/configuration.md` - Config / ConfigProvider (typed env config, defaults, redacted secrets, schema-validated config, custom providers).
- `references/sql.md` - SQL toolkit (SqlClient tagged-template queries, SqlSchema, Model/SqlModel repositories, Migrator, driver layers, SqlError reasons).
- `references/cli.md` - building command-line apps (Command, Flag, Argument, subcommands).
- `references/rpc.md` - typed client/server RPC (RpcGroup, RpcServer, RpcClient, transports, serialization).
- `references/distributed.md` - Cluster (sharded entities), Workflow (durable execution), EventLog (event sourcing).
- `references/stm.md` - software transactional memory (`Effect.tx`, `TxRef`, `Tx*` collections, `Effect.txRetry`).
- `references/datetime.md` - DateTime (Utc/Zoned, arithmetic, zones, formatting).
- `references/optics.md` - Optic (immutable nested reads/updates, method-chain API).
- `core-patterns.md`: `Match` pattern-matching section.
- `resource-management.md`: `Pool` resource-pooling section.
- `concurrency.md`: FiberHandle/FiberMap/FiberSet, SubscriptionRef, and worker-threads (RPC-over-worker) sections.
- `llm-corrections.md`: `Schema.Defect`/`Schema.Error` are constructor functions in v4; `Random.nextUUIDv4` removed (use `Crypto` service).

### Fixed
- `error-modeling.md`: `cause: Schema.Defect` -> `cause: Schema.Defect()` (Schema.Defect is a constructor function since beta.76).

### Changed
- Bumped tracked `effect` from `4.0.0-beta.58` to `4.0.0-beta.78`.
- `migration-v4.md`: refreshed the "v4 beta additions" log to cover beta.59-78 (Schema.Error/Defect constructors, Random.nextUUIDv4 removal, `Effect.Yieldable`/`Types.MergeRecord` removals, `catch*` error-channel fix, HttpApiTest, and more).
- `SKILL.md`: extended the progressive-disclosure index with the new references; added SQL/CLI/RPC/Config to the description.

Verified against: effect@4.0.0-beta.78
