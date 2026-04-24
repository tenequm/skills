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

## v4 beta additions since 2026-03

These landed in later betas and are worth knowing if you are currently on an older beta:

- `Effect.abortSignal` for bridging AbortController-based APIs (beta.57, PR #2085)
- `@effect/sql-pglite` package wrapping `@electric-sql/pglite` (beta.57, PR #2073)
- `Effectable` module for lifting existing types into Effect (beta.55-ish)
- `Socket.make` constructor (beta.57, PR #2078)
- `RpcGroup.omit` for deriving subsets of RPC groups
- `AtomRpc.query` requires an explicit serialization option for serializable atoms (PR #2040)
- **HttpApi schema errors now default to defects** unless transformed (PR #2057, 2026-04-20). See `references/http.md` for how to surface them as typed errors via `HttpApiSchema` transforms.
- `Schema.withDecodingDefaultType` / `...TypeKey` added alongside the Encoded-side variants (PR #2013, 2026-04-10)
