# Dependency Injection

Effect's DI system tracks dependencies through the type system. The `R` parameter in `Effect<A, E, R>` lists required services. The compiler enforces that all dependencies are provided before running.

## Defining Services

### v3: Context.Tag

```typescript
import { Context, Effect, Layer } from "effect"

class Database extends Context.Tag("Database")<Database, {
  readonly query: (sql: string) => Effect.Effect<unknown[]>
}>() {}
```

### v4: Context.Service

```typescript
import { Context, Effect, Layer } from "effect"

class Database extends Context.Service<Database, {
  readonly query: (sql: string) => Effect.Effect<unknown[]>
}>()(
  "myapp/Database" // include package path for uniqueness
) {}
```

Note the argument order difference: v3's `Context.Tag` takes `id` first and types second; v4's `Context.Service` takes types first and `id` on the returned constructor. The module name is the same (`Context`); only the exported factory differs.

> v4 briefly exported this under a `ServiceMap` module; it was renamed back to `Context` on 2026-04-07 (PR #1961). Older beta docs or code may still say `ServiceMap.Service` / `ServiceMap.Reference` — treat as `Context.Service` / `Context.Reference`.

## Building Layers

Layers construct services and wire their dependencies:

```typescript
// Pure implementation (no dependencies)
const DatabaseLive = Layer.succeed(Database, {
  query: (sql) => Effect.tryPromise(() => pgClient.query(sql))
})

// Effectful construction (with dependencies)
const DatabaseLive = Layer.effect(
  Database,
  Effect.gen(function*() {
    const config = yield* AppConfig
    const pool = yield* createPool(config.dbUrl)
    return {
      query: (sql) => Effect.tryPromise(() => pool.query(sql))
    }
  })
)

// Scoped (with resource lifecycle)
// v3
const DatabaseLive = Layer.scoped(
  Database,
  Effect.gen(function*() {
    const pool = yield* Effect.acquireRelease(
      createPool(),
      (pool) => Effect.promise(() => pool.end())
    )
    return { query: (sql) => Effect.tryPromise(() => pool.query(sql)) }
  })
)

// v4 — Layer.scoped is removed. Use Layer.effect; it strips Scope from the
// requirements automatically when the inner effect uses acquireRelease.
const DatabaseLive = Layer.effect(
  Database,
  Effect.gen(function*() {
    const pool = yield* Effect.acquireRelease(
      createPool(),
      (pool) => Effect.promise(() => pool.end())
    )
    return { query: (sql) => Effect.tryPromise(() => pool.query(sql)) }
  })
)
```

## v4: Context.Service with make

```typescript
import { Context, Effect, Layer } from "effect"

class Database extends Context.Service<Database, {
  readonly query: (sql: string) => Effect.Effect<unknown[]>
}>()(
  "myapp/Database",
  {
    make: Effect.gen(function*() {
      const config = yield* AppConfig
      return {
        query: (sql) => Effect.tryPromise(() => pgClient.query(sql))
      }
    })
  }
) {
  // Build layer explicitly from make (v4 does NOT auto-generate layers)
  static readonly layer = Layer.effect(this, this.make).pipe(
    Layer.provide(AppConfig.layer)
  )
}
```

## Composing Layers

```typescript
// Merge independent layers
const AppLayer = Layer.merge(DatabaseLive, CacheLive)

// Wire dependencies between layers
const FullLayer = Layer.provide(ServiceLayer, DatabaseLive)
// ServiceLayer depends on Database, DatabaseLive provides it

// Compose multiple with provideMerge
const FullApp = DatabaseLive.pipe(
  Layer.provideMerge(CacheLive),
  Layer.provideMerge(LoggerLive)
)
```

## Providing Dependencies

```typescript
// Provide a full layer
const runnable = program.pipe(Effect.provide(AppLayer))

// Provide a single service inline
const runnable = program.pipe(
  Effect.provideService(Database, { query: mockQuery })
)
```

## Accessing Services

### In generators (preferred)

```typescript
const program = Effect.gen(function*() {
  const db = yield* Database
  const results = yield* db.query("SELECT * FROM users")
  return results
})
```

### v4: Service.use (one-liner access)

```typescript
// v4 only
const program = Database.use((db) => db.query("SELECT * FROM users"))
```

Prefer `yield*` in generators over `.use()` because it makes dependencies explicit and avoids accidentally leaking service requirements.

## Testing with Layer Swaps

```typescript
// Production layer
const DatabaseLive = Layer.effect(Database, /* real implementation */)

// Test layer
const DatabaseTest = Layer.succeed(Database, {
  query: (sql) => Effect.succeed([{ id: 1, name: "test" }])
})

// In tests, provide the test layer
const result = await Effect.runPromise(
  program.pipe(Effect.provide(DatabaseTest))
)
```

## v4: References (Services with Defaults)

For configuration values and feature flags that have sensible defaults:

```typescript
// v3
class LogLevel extends Context.Reference<LogLevel>()("LogLevel", {
  defaultValue: () => "info" as const
}) {}

// v4
const LogLevel = Context.Reference<"info" | "warn" | "error">("LogLevel", {
  defaultValue: () => "info" as const
})
```

References can be `yield*`-ed like services but have a default if not provided.

## Layer Naming Convention

- v3: `DatabaseLive`, `Database.Default`
- v4: `Database.layer`, `Database.layerTest`, `Database.layerConfig`

## v4: Per-Key Dynamic Layers (`LayerMap`)

When you need one instance of a service *per key* — a connection pool per tenant, a client per region — build a `LayerMap.Service`. Its `lookup` builds the layer for a key on first access, caches it, and releases it after `idleTimeToLive`. Downstream code stays key-agnostic (`yield* DatabasePool`); the correct instance is chosen by whichever `MyMap.get(key)` layer is provided.

```typescript
import { Context, Effect, Layer, LayerMap } from "effect"

class DatabasePool extends Context.Service<DatabasePool, {
  readonly query: (sql: string) => Effect.Effect<ReadonlyArray<unknown>>
}>()("app/DatabasePool") {
  // one layer per tenant, cleaned up on scope close
  static readonly layer = (tenantId: string) =>
    Layer.effect(
      DatabasePool,
      Effect.acquireRelease(
        Effect.sync(() => DatabasePool.of({ query: (sql) => Effect.succeed([]) })),
        () => Effect.log(`Closing pool for ${tenantId}`)
      )
    )
}

class PoolMap extends LayerMap.Service<PoolMap>()("app/PoolMap", {
  lookup: (tenantId: string) => DatabasePool.layer(tenantId),
  idleTimeToLive: "1 minute"
}) {}

const queryUsers = Effect.gen(function*() {
  const pool = yield* DatabasePool // tenant-agnostic
  return yield* pool.query("SELECT id FROM users")
})

const program = queryUsers.pipe(
  Effect.provide(PoolMap.get("acme")), // builds/caches the "acme" pool
  Effect.provide(PoolMap.layer)
)
// PoolMap.invalidate("acme") forces a rebuild on next access.
```

## Bridging Effect into Non-Effect Frameworks (`ManagedRuntime`)

To call Effect from an imperative framework (Hono, Express, a webhook handler), build **one** `ManagedRuntime` from your application layer at startup and reuse it — never construct a runtime per request, and never chain two `runPromise` calls where one Effect would do.

Carry per-request state through a fiber-local `Context.Reference` set with `Effect.provideService` inside the run, **not** as an extra "bag" parameter threaded through every function. This keeps the request context off the `R` channel (it stays `never` at the edge) and prevents cross-request leakage. Pass a plain object into the reference — never the framework's own request/context object.

```typescript
import { Context, Effect, Layer, ManagedRuntime } from "effect"

interface RequestInfo { readonly requestId: string; readonly userId: string }
const RequestInfo = Context.Reference<RequestInfo>("app/RequestInfo", {
  defaultValue: () => ({ requestId: "", userId: "" })
})

const runtime = ManagedRuntime.make(AppLayer) // once, at startup

// In a Hono handler:
app.post("/charge", async (c) => {
  const info: RequestInfo = { requestId: c.req.header("x-request-id") ?? "", userId: c.get("userId") }
  const result = await runtime.runPromise(
    chargeUser.pipe(Effect.provideService(RequestInfo, info))
  )
  return c.json(result)
})
// On shutdown: await runtime.dispose()
```

Anti-patterns to avoid: two sequential `runPromise` calls in one handler, a `ChargeOpts`-style parameter bag instead of a `Context.Reference`, telemetry/logging buried inside a `tryPromise` thunk, and re-running `setup()` without disposing the previous runtime (leaks the old runtime and any detached fibers).
