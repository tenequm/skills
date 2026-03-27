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

### v4: ServiceMap.Service

```typescript
import { Effect, Layer, ServiceMap } from "effect"

class Database extends ServiceMap.Service<Database, {
  readonly query: (sql: string) => Effect.Effect<unknown[]>
}>()(
  "myapp/Database" // include package path for uniqueness
) {}
```

Note the argument order difference: v3 passes `id` first, v4 passes type params first, then `id` to the returned constructor.

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
```

## v4: ServiceMap.Service with make

```typescript
class Database extends ServiceMap.Service<Database, {
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
const LogLevel = ServiceMap.Reference<"info" | "warn" | "error">("LogLevel", {
  defaultValue: () => "info" as const
})
```

References can be `yield*`-ed like services but have a default if not provided.

## Layer Naming Convention

- v3: `DatabaseLive`, `Database.Default`
- v4: `Database.layer`, `Database.layerTest`, `Database.layerConfig`
