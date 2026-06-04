# Resource Management

Effect guarantees deterministic resource cleanup through `Scope`. Resources are released in LIFO order, even on failure or interruption.

## acquireRelease (Scoped Resource)

Define a resource with its cleanup:

```typescript
import { Effect } from "effect"

const managedConnection = Effect.acquireRelease(
  // Acquire
  Effect.tryPromise(() => pool.connect()),
  // Release (always runs - success, failure, or interruption)
  (conn) => Effect.promise(() => conn.release())
)

// MUST wrap in Effect.scoped to trigger cleanup
const program = Effect.scoped(
  Effect.gen(function*() {
    const conn = yield* managedConnection
    return yield* conn.query("SELECT * FROM users")
  })
)
```

## acquireUseRelease (Inline Pattern)

When you want acquire, use, and release in one expression:

```typescript
const result = yield* Effect.acquireUseRelease(
  // Acquire
  Effect.tryPromise(() => pool.connect()),
  // Use
  (conn) => Effect.tryPromise(() => conn.query("SELECT 1")),
  // Release
  (conn) => Effect.promise(() => conn.release())
)
// No Effect.scoped needed - cleanup is handled inline
```

## Scope and LIFO Ordering

Multiple resources are released in reverse acquisition order:

```typescript
const program = Effect.scoped(
  Effect.gen(function*() {
    const db = yield* acquireDb()       // acquired first
    const cache = yield* acquireCache() // acquired second
    const file = yield* acquireFile()   // acquired third
    // ... use all three
  })
  // Cleanup order: file -> cache -> db (LIFO)
)
```

## Scoped Layers

Layers can manage resource lifecycles:

```typescript
// v3
const DatabaseLayer = Layer.scoped(
  Database,
  Effect.gen(function*() {
    const pool = yield* Effect.acquireRelease(
      Effect.tryPromise(() => createPool()),
      (pool) => Effect.promise(() => pool.end())
    )
    return { query: (sql) => Effect.tryPromise(() => pool.query(sql)) }
  })
)

// v4 — Layer.scoped is removed. Layer.effect strips Scope from R automatically.
const DatabaseLayer = Layer.effect(
  Database,
  Effect.gen(function*() {
    const pool = yield* Effect.acquireRelease(
      Effect.tryPromise(() => createPool()),
      (pool) => Effect.promise(() => pool.end())
    )
    return { query: (sql) => Effect.tryPromise(() => pool.query(sql)) }
  })
)
// Pool is created when the layer is built
// Pool is released when the program exits
```

## Background Fibers in Scopes

```typescript
const program = Effect.scoped(
  Effect.gen(function*() {
    // This fiber is automatically interrupted when scope closes
    yield* Effect.forkScoped(
      Effect.repeat(healthCheck, Schedule.spaced("30 seconds"))
    )
    // Main work
    yield* serveRequests()
  })
)
```

## ensuring - Always-Run Finalizer

For cleanup that doesn't need the acquired resource:

```typescript
const withCleanup = myEffect.pipe(
  Effect.ensuring(Effect.log("Done, regardless of outcome"))
)
```

## addFinalizer - Manual Scope Registration

```typescript
const program = Effect.scoped(
  Effect.gen(function*() {
    yield* Effect.addFinalizer((exit) =>
      Effect.log(`Exiting with: ${exit._tag}`)
    )
    // ... your logic
  })
)
```

## Pooling Resources with `Pool`

When a resource is expensive to create and you need many of them concurrently (DB connections, clients), pool them instead of acquiring per-use. `Pool.make` builds a fixed-size pool; `Pool.makeWithTTL` an elastic one that shrinks idle items. Both the pool and `Pool.get` require a `Scope` — the pool's lifetime is the scope it is built in.

```typescript
import { Effect, Pool } from "effect"

const acquireConn = Effect.acquireRelease(
  openConnection(),
  (conn) => Effect.promise(() => conn.close())
)

const program = Effect.scoped(
  Effect.gen(function*() {
    // Fixed-size pool of 10 connections, all created within this scope
    const pool = yield* Pool.make({ acquire: acquireConn, size: 10 })

    // Borrow inside its own scope so the item returns to the pool promptly
    const rows = yield* Effect.scoped(
      Pool.get(pool).pipe(
        Effect.flatMap((conn) => conn.query("SELECT 1"))
      )
    )
    return rows
  })
)
```

`Pool.get` hands back a **scoped** resource: wrap the borrow in `Effect.scoped` (or a child scope) so it is released back to the pool deterministically when that scope closes. Use `Pool.makeWithTTL({ acquire, min, max, timeToLive })` for elastic sizing, and `Pool.invalidate(pool, item)` to discard a known-bad item.

## v4: Scope Changes

In v4, `Scope` remains conceptually the same. Key change: `Effect.forkScoped` behavior is unchanged, but `Effect.fork` is renamed to `Effect.forkChild` (which is NOT scope-tied - use `Effect.forkScoped` for scope-tied fibers).
