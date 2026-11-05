# Migrating from Effect v3 to v4

Effect v4 (beta, February 2026) is a major release. The core programming model (Effect, Layer, Schema, Stream) is unchanged, but naming, imports, and some APIs have changed significantly.

Source: https://github.com/Effect-TS/effect-smol/blob/main/MIGRATION.md

## Installation

```bash
npm install effect@beta
# Companion packages must match versions:
npm install @effect/platform-node@beta @effect/opentelemetry@beta
```

## Structural Changes

### Unified Versioning
All packages share a single version (e.g., `effect@4.0.0-beta.X`, `@effect/sql-pg@4.0.0-beta.X`).

### Package Consolidation
Many packages merged into `effect`. Remaining separate: `@effect/platform-*`, `@effect/sql-*`, `@effect/ai-*`, `@effect/opentelemetry`, `@effect/vitest`.

### Unstable Modules
New `effect/unstable/*` paths may break in minor releases: `ai`, `cli`, `cluster`, `devtools`, `http`, `httpapi`, `observability`, `rpc`, `sql`, `workflow`, `workers`, etc.

### Bundle Size
~70KB (v3) -> ~20KB (v4) for Effect + Stream + Schema. Minimal: ~6.3KB gzipped.

## Services: Context.Tag -> Context.Service

v4 briefly introduced a `ServiceMap` module for service definitions. On 2026-04-07 (PR #1961) it was renamed back to `Context`. Any doc or older beta code that says `ServiceMap.Service` / `ServiceMap.Reference` should be read as the current `Context.Service` / `Context.Reference`.

| v3                                    | v4                                        |
|---------------------------------------|-------------------------------------------|
| `Context.GenericTag<T>(id)`           | `Context.Service<T>(id)`                  |
| `Context.Tag(id)<Self, Shape>()`      | `Context.Service<Self, Shape>()(id)`      |
| `Effect.Tag(id)<Self, Shape>()`       | `Context.Service<Self, Shape>()(id)`      |
| `Effect.Service<Self>()(id, opts)`    | `Context.Service<Self>()(id, { make })`   |
| `Context.Reference<Self>()(id, opts)` | `Context.Reference<T>(id, opts)`          |

```typescript
// v3
class Database extends Context.Tag("Database")<Database, {
  readonly query: (sql: string) => Effect.Effect<unknown[]>
}>() {}

// v4
class Database extends Context.Service<Database, {
  readonly query: (sql: string) => Effect.Effect<unknown[]>
}>()(
  "myapp/Database"
) {}
```

**Static accessors removed.** Use `Service.use()` or `yield*` in generators:

```typescript
// v3: Notifications.notify("hello") (proxy accessor)
// v4: Notifications.use((n) => n.notify("hello"))
// v4 preferred: yield* Notifications in Effect.gen
```

**Layer naming:** `.Default` / `.Live` -> `.layer`, `.layerTest`, `.layerConfig`

**No auto-generated layers in v4.** Build explicitly with `Layer.effect(this, this.make)`.

## Error Handling Renames

| v3                       | v4                             |
|--------------------------|--------------------------------|
| `Effect.catchAll`        | `Effect.catch`                 |
| `Effect.catchAllCause`   | `Effect.catchCause`            |
| `Effect.catchAllDefect`  | `Effect.catchDefect`           |
| `Effect.catchSome`       | `Effect.catchFilter`           |
| `Effect.catchSomeCause`  | `Effect.catchCauseFilter`      |
| `Effect.catchSomeDefect` | Removed                        |
| `Effect.catchTag`        | Unchanged (also accepts arrays)|
| `Effect.catchTags`       | Unchanged                      |

**New in v4:** `Effect.catchReason`, `Effect.catchReasons`, `Effect.catchEager`

## Forking Renames

| v3                            | v4                  |
|-------------------------------|---------------------|
| `Effect.fork`                 | `Effect.forkChild`  |
| `Effect.forkDaemon`           | `Effect.forkDetach` |
| `Effect.forkScoped`           | Unchanged           |
| `Effect.forkIn`               | Unchanged           |
| `Effect.forkAll`              | Removed             |
| `Effect.forkWithErrorHandler` | Removed             |

Fork options: `{ startImmediately?: boolean, uninterruptible?: boolean | "inherit" }`

## FiberRef -> Context.Reference

`FiberRef`, `FiberRefs`, `FiberRefsPatch`, `Differ` are removed. Fiber-local state is now handled by `Context.Reference` — the same mechanism used for services with default values. Built-in fiber-local values are exported from the `References` namespace.

| v3                              | v4                                 |
|---------------------------------|------------------------------------|
| `FiberRef.currentLogLevel`      | `References.CurrentLogLevel`       |
| `FiberRef.currentConcurrency`   | `References.CurrentConcurrency`    |
| `FiberRef.get(ref)`             | `yield* References.X`             |
| `Effect.locally(e, ref, value)` | `Effect.provideService(e, Ref, v)` |

## Either -> Result

| v3                | v4                 |
|-------------------|--------------------|
| `Either`          | `Result`           |
| `Either.right(x)` | `Result.ok(x)`    |
| `Either.left(e)`  | `Result.err(e)`   |
| `Effect.either`   | `Effect.result`    |

## Yieldable (Types No Longer Effect Subtypes)

In v3, `Ref`, `Deferred`, `Fiber`, `Option`, `Either`, `Config` etc. were structural subtypes of `Effect`. In v4, they implement `Yieldable` instead - `yield*` still works in generators, but they can't be passed directly to Effect combinators.

```typescript
// v3: yield* ref      -> reads the ref value
// v4: yield* Ref.get(ref)

// v3: yield* fiber    -> joins the fiber
// v4: yield* Fiber.join(fiber)

// v3: yield* deferred -> awaits the deferred
// v4: yield* Deferred.await(deferred)

// v3: Effect.map(option, fn) -> worked because Option was Effect
// v4: Effect.map(option.asEffect(), fn) -> explicit conversion needed
```

## Runtime<R> Removed

| v3                               | v4                                    |
|----------------------------------|---------------------------------------|
| `Effect.runtime<R>()`           | `Effect.services<R>()`               |
| `Runtime.runFork(runtime)(eff)` | `Effect.runForkWith(services)(eff)`   |

## Effect.fn (New in v4)

Preferred way to write functions returning Effects. Adds automatic span + better stack traces:

```typescript
const fetchUser = Effect.fn("fetchUser")(
  function*(id: string): Effect.fn.Return<User, NotFoundError> {
    const db = yield* Database
    return yield* db.findUser(id)
  },
  // Additional combinators (no .pipe needed)
  Effect.catch((e) => Effect.log(`Error: ${e}`))
)
```

## Schema Changes (Major)

### Renames

| v3                            | v4                                    |
|-------------------------------|---------------------------------------|
| `Schema.TaggedError`          | `Schema.TaggedErrorClass`             |
| `Schema.decodeUnknown`        | `Schema.decodeUnknownEffect`          |
| `Schema.decode`               | `Schema.decodeEffect`                 |
| `Schema.encode`               | `Schema.encodeEffect`                 |
| `Schema.decodeUnknownEither`  | `Schema.decodeUnknownExit`            |
| `Schema.Literal("a","b")`    | `Schema.Literals(["a","b"])`          |
| `Schema.Union(A, B)`         | `Schema.Union([A, B])`               |
| `Schema.Tuple(A, B)`         | `Schema.Tuple([A, B])`               |
| `Schema.pick("a")`           | `.mapFields(Struct.pick(["a"]))`      |
| `Schema.omit("a")`           | `.mapFields(Struct.omit(["a"]))`      |
| `Schema.partial`             | `.mapFields(Struct.map(Schema.optional))` |
| `Schema.extend(B)`           | `.mapFields(Struct.assign(fieldsB))`  |
| `Schema.filter(pred)`        | `.check(Schema.makeFilter(pred))`     |
| `Schema.positive()`          | `Schema.isGreaterThan(0)`             |
| `Schema.int()`               | `Schema.isInt()`                      |
| `Schema.minLength(n)`        | `Schema.isMinLength(n)`              |

### Transform syntax change

```typescript
// v3
Schema.transform(FromSchema, ToSchema, { decode, encode })

// v4
FromSchema.pipe(
  Schema.decodeTo(ToSchema, SchemaTransformation.transform({ decode, encode }))
)
```

### optionalWith changes

| v3 options                    | v4                                                        |
|-------------------------------|-----------------------------------------------------------|
| `{ exact: true }`            | `Schema.optionalKey(schema)`                              |
| `{ default }`                | `schema.pipe(Schema.withDecodingDefaultType(...))`        |
| `{ exact: true, default }`   | `schema.pipe(Schema.withDecodingDefaultTypeKey(...))`     |

> The non-`Type` variants (`withDecodingDefault`, `withDecodingDefaultKey`) also exist in v4 but apply the default to the **Encoded** side. v3's `optionalWith({ default })` applied the default on the Type (decoded) side, so the `*Type*` variants are the correct migration target.

### Equality

`Equal.equals` performs deep structural comparison by default in v4. `Schema.Data` is removed (unnecessary).

## Other API Removals & Renames

| v3                                       | v4                                                                                |
|------------------------------------------|-----------------------------------------------------------------------------------|
| `Layer.scoped(Tag, eff)`                 | `Layer.effect(Tag, eff)` — strips `Scope` from requirements automatically         |
| `Effect.async((resume) => ...)`          | `Effect.callback((resume, signal) => ...)` — `signal: AbortSignal` is positional  |
| `Effect.makeSemaphore(n)`                | `Semaphore.make(n)` (import `Semaphore` from `"effect"`)                          |
| `semaphore.withPermits(n)(eff)`          | `Semaphore.withPermits(semaphore, n)(eff)` — data-first                           |
| `Schedule.compose(Schedule.recurs(n))`   | `Schedule.take(n)` (bound by attempt count) or `Effect.retry(_, { schedule, times })` |
| `Schedule.once`                          | `Schedule.recurs(0)`                                                              |
| `import { RateLimiter } from "effect"`   | `import { RateLimiter } from "effect/unstable/persistence"` — Service-based API; no `withCost`, use `tokens` option |

## Quick Checklist for v3 -> v4

1. Replace `Context.Tag` / `Effect.Tag` / `Effect.Service` with `Context.Service`
2. Replace `Effect.catchAll` with `Effect.catch` (and similar renames)
3. Replace `Effect.fork` with `Effect.forkChild`, `Effect.forkDaemon` with `Effect.forkDetach`
4. Replace `FiberRef.*` with `Context.Reference` / `References.*`
5. Replace `yield* ref` with `yield* Ref.get(ref)`, same for Fiber/Deferred
6. Replace `Data.TaggedError` with `Schema.TaggedErrorClass`
7. Update Schema API calls (variadic to array, filter renames, transform syntax)
8. Replace `Effect.either` with `Effect.result`
9. Update layer naming (`.Default` -> `.layer`)
10. Use `Effect.fn("name")` for new functions
11. Replace `Layer.scoped` with `Layer.effect`
12. Replace `Effect.async` with `Effect.callback`
13. Replace `Effect.makeSemaphore` with `Semaphore.make`; switch `withPermits` to data-first
14. Replace `Schedule.compose(Schedule.recurs(n))` with `Schedule.take(n)`; replace `Schedule.once` with `Schedule.recurs(0)`
15. Move `RateLimiter` import from `"effect"` to `"effect/unstable/persistence"` and switch to its Service-based API

## v4 beta additions (through beta.92)

These landed in later betas and are worth knowing if you are currently on an older beta. The skill tracks `effect@4.0.0-beta.92`; companion packages share that single version.

### beta.55-58 (through 2026-04-28)

- `Effect.abortSignal` for bridging AbortController-based APIs (beta.57, PR #2085)
- `@effect/sql-pglite` package wrapping `@electric-sql/pglite` (beta.57, PR #2073)
- `Effectable` module for lifting existing types into Effect (beta.55-ish)
- `Socket.make` constructor (beta.57, PR #2078)
- `RpcGroup.omit` for deriving subsets of RPC groups
- `AtomRpc.query` requires an explicit serialization option for serializable atoms (PR #2040)
- **HttpApi schema errors now default to defects** unless transformed (PR #2057, 2026-04-20). See `references/http.md` for how to surface them as typed errors via `HttpApiSchema` transforms.
- `Schema.withDecodingDefaultType` / `...TypeKey` added alongside the Encoded-side variants (PR #2013, 2026-04-10)
- `AsyncResult.builder` (`effect/unstable/reactivity`) gained `.onInterrupt(...)` and an `.exhaustive()` finalizer; `.onDefect` / `.onFailure` typing refined so `.exhaustive()` is only callable when every case (success, error, initial, defect, interrupt) is handled (beta.58, PR #2097, 2026-04-28). Use `.exhaustive(): Out` instead of `.render(): Out | null` when you want a non-nullable result.
- Stream -> `Uint8Array` conversion and HTTP body consumption now use fewer buffer copies - internal perf only, no public API change (beta.58, PR #2098, 2026-04-27).

### beta.59-78 (2026-04-29 through 2026-06)

Breaking / behavioral:

- **`Schema.Error` / `Schema.Defect` are now constructor functions**, not constants — write `Schema.Error()` / `Schema.Defect()`. `ErrorWithStack` / `DefectWithStack` folded into `{ includeStack: true }`. `Schema.Defect()` now models defects as `unknown` with a JSON-encoded form, so non-`Error` objects no longer round-trip unchanged (beta.76, PR #2318).
- **`Random.nextUUIDv4` removed** — `Random` is not cryptographically secure. Use the new platform-agnostic `Crypto` service's `randomUUIDv4` / `randomUUIDv7` (beta.68, PR #2180).
- **`Effect.Yieldable` export removed** (beta.66, PR #2163). The Yieldable *concept* still applies (Ref/Deferred/Fiber/Option/Config implement it); only the re-export off `Effect` is gone.
- `Types.MergeRecord` removed -> use `Types.MergeLeft` (beta.75, PR #2298).
- `SchemaParser.makeUnsafe` -> `SchemaParser.make` (beta.67, PR #2172).
- `Schema.asserts` signature changed to `asserts(schema, input)`; `Schema.Codec.ToAsserts` removed (beta.68, PR #2221).
- `Model.Generated` -> `Model.GeneratedByDb` (beta.68, PR #2207). See `references/sql.md`.
- `Workflow.make` now takes the tag as its **first** argument and supports `class X extends Workflow.make(...) {}` (beta.75, PR #2294). See `references/distributed.md`.
- `Inspectable.stringifyCircular` removed (beta.60, PR #2119).

Fixes / additions worth knowing:

- `catch*` combinators no longer silently drop unhandled error types — the residual error channel is now preserved (beta.71, PR #2257).
- `Effect.firstSuccessOf` ported from v3 (beta.61, PR #2120); `Effect.acquireDisposable` added (beta.63, PR #2123).
- `Schedule.tap` added — observe full schedule metadata without altering inputs/outputs (beta.71, PR #2252).
- `Stream.broadcastN` for fixed-size stream broadcasts (beta.68, PR #2210); `Channel.decodeText` UTF-8-across-chunk fix (beta.68, PR #2209).
- `HttpApiTest` module added for testing HttpApi servers (beta.63, PR #2136); `HttpApiSecurity.http` for custom schemes (beta.73, PR #2291).
- `Schema.DurationFromString` (beta.60, PR #2117); `Schema.isGUID` + RFC 9562 max-UUID support in `Schema.isUUID` (beta.76, PR #2320).
- OTLP observability now reads `OTEL_*` environment variables and prefers them over explicit `OtlpResource.fromConfig` options (beta.77, PRs #2325/#2326).
- `Config.literals` convenience constructor for `Schema.Literals` (beta.60, PR #2116).

### beta.79-92 (2026-06 through 2026-07)

Breaking / behavioral:

- **`SchemaError` now extends `Data.TaggedError`** (beta.84, PR #2407) — it is also a native `Error` with `_tag: "SchemaError"`, catchable via `Effect.catchTag`. The `SchemaParser` Promise APIs reject an `Error` whose `cause` is the `SchemaIssue.Issue`; the `is`/`asserts`/`Promise`/`Sync`/`Result`/`Option`/`make`/`makeOption` adapters now distinguish schema issues from non-schema causes.
- **`Schema.Void` now models ignored `void` return values** (beta.89, PR #2475) — it accepts any present value and discards it as `undefined`. Use `Schema.Undefined` when you need to match `undefined` exactly.
- **`Config.make` low-level constructor removed** (beta.84, PR #2383) — use the config constructors/combinators or `ConfigProvider.make`. `ConfigProvider.fromDir` now returns `undefined` when neither file nor dir exists, so you can chain `orElse` fallbacks.
- **`Config.withDefault` recovery narrowed** (beta.81, PRs #2387/#2388) — it now only recovers from *missing* data for literal/union schemas; present-but-invalid values and filter failures propagate the validation error instead of falling back to the default. `Config.schema` also treats a missing array value as missing data so `withDefault` applies (beta.90, PR #2483).
- **`Effect.try` accepts a thunk directly** (beta.84, PR #2415), matching `Effect.tryPromise`; `tryPromise` only creates an `AbortController` when the thunk declares an `AbortSignal` parameter.
- **`RpcGroup.toHandlers` is now definition-first** (beta.84, PR #2423); RpcClient HTTP requests fail with a *defect* when the response stream closes before a terminal response (beta.86, PR #2461).
- **Schema arbitrary-derivation metadata migrated** (beta.79, PR #2348) — custom filter annotations use `arbitrary: { constraint }` instead of `toArbitraryConstraint`, bucketed constraints are flattened (`string.minLength` -> `minLength`, `number.isInteger` -> `integer`), `ctx.constraints` -> `ctx.constraint`, and `Schema.toArbitrary(schema, { report: true })` returns `{ value, report }`. Plain `Schema.toArbitrary(schema)` (as shown in `references/testing.md`) is unaffected.
- `keepDeclarations` option removed from `Schema.toCodecStringTree` (beta.86, PR #2452).
- `Graph.neighborsDirected` deprecated in favor of `Graph.successors` / `Graph.predecessors` (beta.80, PR #2376).

Fixes / additions worth knowing:

- `Effect.transposeOption` turns `Option<Effect<A, E, R>>` into `Effect<Option<A>, E, R>` (beta.84, PR #2420); `Effect.fromOption` gained custom error callbacks (beta.89, PR #2479).
- `Random.choice` selects a random element from an iterable (beta.85, PR #2425); `Latch.isOpen` queries latch state (beta.88, PR #2428).
- `String.configCase` for configuration-key casing, plus a numeric-segment fix in `camelCase`/`pascalCase` (beta.91, PR #2488).
- HTTP API streaming response support (beta.81, PR #2270); malformed JSON request bodies now return 400 (unreleased, PR #2492).
- `Statement.valuesUnprepared` returns unprepared SQL rows as arrays (beta.86, PR #2462); `Schema.toCodecArrayFromSingle` added (beta.86, PR #2442); the original input schema is now exposed on `Schema.toType`/`toEncoded`/`toCodecJson`/`toCodecStringTree` via a `.schema` property (beta.87, PR #2468).
- `RequestResolver` interruption fixed (beta.91, PR #2485); `Schedule.andThenResult` now emits `self` outputs as `Failure` and `other` as `Success` (beta.91, PR #2497); `Schema.toTaggedUnion(...).isAnyOf` narrowing fixed for custom discriminant keys (beta.81, PR #2386).
- Adaptive consume + feedback operations on the unstable persistent `RateLimiterStore` API (in-memory + Redis, 429 Retry-After feedback) (beta.88, PR #2472).
- `OtlpTracer` now renders causes in exception events (beta.89, PR #2480); excess-property handling fixed in schema-backed class constructors (beta.92, PR #2499).
- `@effect/ai-anthropic`: non-streaming responses no longer throw on tool-call `caller` metadata (emits `null` for `caller.toolId`, beta.88, PR #2450).
