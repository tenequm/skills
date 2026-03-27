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

## Services: Context.Tag -> ServiceMap.Service

| v3                                    | v4                                         |
|---------------------------------------|--------------------------------------------|
| `Context.GenericTag<T>(id)`           | `ServiceMap.Service<T>(id)`                |
| `Context.Tag(id)<Self, Shape>()`      | `ServiceMap.Service<Self, Shape>()(id)`    |
| `Effect.Tag(id)<Self, Shape>()`       | `ServiceMap.Service<Self, Shape>()(id)`    |
| `Effect.Service<Self>()(id, opts)`    | `ServiceMap.Service<Self>()(id, { make })` |
| `Context.Reference<Self>()(id, opts)` | `ServiceMap.Reference<T>(id, opts)`        |

```typescript
// v3
class Database extends Context.Tag("Database")<Database, {
  readonly query: (sql: string) => Effect.Effect<unknown[]>
}>() {}

// v4
class Database extends ServiceMap.Service<Database, {
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

## FiberRef -> ServiceMap.Reference

`FiberRef`, `FiberRefs`, `FiberRefsPatch`, `Differ` are removed.

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

| v3 options                    | v4                                              |
|-------------------------------|-------------------------------------------------|
| `{ exact: true }`            | `Schema.optionalKey(schema)`                    |
| `{ default }`                | `schema.pipe(Schema.withDecodingDefault(...))`   |
| `{ exact: true, default }`   | `schema.pipe(Schema.withDecodingDefaultKey(...))` |

### Equality

`Equal.equals` performs deep structural comparison by default in v4. `Schema.Data` is removed (unnecessary).

## Quick Checklist for v3 -> v4

1. Replace `Context.Tag` / `Effect.Tag` / `Effect.Service` with `ServiceMap.Service`
2. Replace `Effect.catchAll` with `Effect.catch` (and similar renames)
3. Replace `Effect.fork` with `Effect.forkChild`, `Effect.forkDaemon` with `Effect.forkDetach`
4. Replace `FiberRef.*` with `ServiceMap.Reference` / `References.*`
5. Replace `yield* ref` with `yield* Ref.get(ref)`, same for Fiber/Deferred
6. Replace `Data.TaggedError` with `Schema.TaggedErrorClass`
7. Update Schema API calls (variadic to array, filter renames, transform syntax)
8. Replace `Effect.either` with `Effect.result`
9. Update layer naming (`.Default` -> `.layer`)
10. Use `Effect.fn("name")` for new functions
