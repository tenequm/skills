# LLM Corrections: Wrong vs Correct Effect APIs

This is the exhaustive reference for preventing hallucinated Effect code. Check this before using any API you're unsure about.

## Non-Existent APIs (frequently hallucinated)

| Hallucinated API                      | What to use instead                                          |
|---------------------------------------|--------------------------------------------------------------|
| `Effect.cachedWithTTL`                | `Cache.make({ capacity, timeToLive, lookup })`               |
| `Effect.cachedInvalidateWithTTL`      | `cache.invalidate(key)` / `cache.invalidateAll()`            |
| `Effect.retryN(n)`                    | `Effect.retry(Schedule.recurs(n))`                           |
| `Effect.retryWithBackoff`             | `Effect.retry(Schedule.exponential("100 millis"))`           |
| `Effect.timeout(effect, ms)`          | `Effect.timeout(effect, "5 seconds")` (Duration string)      |
| `Effect.timeoutTo`                    | `Effect.timeoutTo(effect, { duration, onTimeout })`          |
| `Effect.parallel`                     | `Effect.all([...], { concurrency: "unbounded" })`            |
| `Effect.race(a, b)` (array form)     | `Effect.race(a, b)` takes exactly two effects                |
| `Effect.raceAll([...])`              | `Effect.raceAll(effects)` (single iterable argument)         |
| `Effect.withTimeout`                  | `Effect.timeout("5 seconds")` in a pipe                      |
| `Effect.bracket`                      | `Effect.acquireUseRelease(acquire, use, release)`            |
| `Effect.ensuring(effect, finalizer)`  | `Effect.ensuring(finalizer)` in a pipe                       |
| `Effect.supervised`                   | Use `Effect.forkScoped` or manual fiber management            |
| `Effect.blocking`                     | `Effect.sync` or `Effect.tryPromise` (no separate blocking)  |
| `Stream.fromSSE`                      | Build from `HttpClient` response + chunk parsing              |
| `Layer.fromEffect`                    | `Layer.effect(Tag, effect)`                                   |
| `Layer.fromFunction`                  | `Layer.succeed(Tag, implementation)`                          |
| `Layer.fromService`                   | `Layer.effect(Tag, Effect.gen(function*() { ... }))`          |
| `Schema.nullable`                     | `Schema.NullOr(schema)`                                      |
| `Schema.optional` (standalone)        | `Schema.optional(schema)` for struct fields only              |

## Wrong Import Paths

| Wrong                                        | Correct                                    |
|----------------------------------------------|--------------------------------------------|
| `import { Schema } from "@effect/schema"`    | `import { Schema } from "effect"`          |
| `import { JSONSchema } from "@effect/schema"`| `import { JSONSchema } from "effect"`      |
| `import { ParseResult } from "@effect/schema"` | `import { ParseResult } from "effect"` (v3) / removed in v4 |
| `import { Effect } from "@effect/io"`        | `import { Effect } from "effect"`          |
| `import { Layer } from "@effect/io"`         | `import { Layer } from "effect"`           |
| `import { Stream } from "@effect/stream"`    | `import { Stream } from "effect"`          |
| `import { HttpClient } from "@effect/platform"` | `import { HttpClient } from "@effect/platform"` (v3) or `"effect/unstable/http"` (v4) |

## Wrong Patterns

### Running effects inside effects (DO NOT)

```typescript
// WRONG - calling runPromise inside an Effect pipeline
const bad = Effect.gen(function*() {
  const result = Effect.runPromise(someEffect) // NO!
  return result
})

// CORRECT - compose effects, run only at the edge
const good = Effect.gen(function*() {
  const result = yield* someEffect
  return result
})
```

### Missing scope for acquireRelease (DO NOT)

```typescript
// WRONG - acquireRelease without scoped
const bad = Effect.gen(function*() {
  const conn = yield* Effect.acquireRelease(
    openConn(),
    (conn) => closeConn(conn)
  )
  return yield* conn.query("SELECT 1")
})

// CORRECT - wrap in Effect.scoped
const good = Effect.scoped(
  Effect.gen(function*() {
    const conn = yield* Effect.acquireRelease(
      openConn(),
      (conn) => closeConn(conn)
    )
    return yield* conn.query("SELECT 1")
  })
)
```

### Generator yield without star (DO NOT)

```typescript
// WRONG - yield without *
const bad = Effect.gen(function*() {
  const x = yield someEffect // Missing *! This yields the Effect object itself
})

// CORRECT - yield*
const good = Effect.gen(function*() {
  const x = yield* someEffect
})
```

### Not returning on error raise (DO NOT)

```typescript
// WRONG - error doesn't stop execution in TS's view
const bad = Effect.gen(function*() {
  if (!input) {
    yield* Effect.fail(new InputError({ message: "missing" }))
  }
  // TS thinks this code runs even after fail ^
  yield* doWork(input) // input might be undefined
})

// CORRECT - return yield* to signal control flow
const good = Effect.gen(function*() {
  if (!input) {
    return yield* Effect.fail(new InputError({ message: "missing" }))
  }
  yield* doWork(input) // TS knows input is defined here
})
```

### Point-free/tacit function passing (DO NOT)

```typescript
// WRONG - generics get erased, overloads break
const bad = Effect.map(myEffect, JSON.parse)

// CORRECT - explicit lambda preserves types
const good = Effect.map(myEffect, (x) => JSON.parse(x))
```

## Terminology Corrections

| Wrong term               | Correct term                               |
|--------------------------|--------------------------------------------|
| "cancel a fiber"         | "interrupt a fiber"                        |
| "thread-local storage"   | "fiber-local storage" (FiberRef / Reference) |
| "worker pool"            | `concurrency` option on `Effect.all/forEach` |
| "dependency container"   | "Layer" / "ServiceMap" (v4) / "Context" (v3) |
| "middleware" (for layers)| "Layer" (layers compose, not chain)          |
| "async effect"           | Effects are lazy by default, both sync/async |
| "Observable" / "RxJS"    | Effect is single-shot (like lazy Promise), not multi-shot |

## Myths to Not Repeat

1. **"Effect is 500x slower"** - Only for trivial `1+1` micro-ops. For real IO-bound services, fiber overhead is unmeasurable
2. **"Huge bundle size"** - v3 minimum ~25KB gzipped; v4 minimum ~6.3KB gzipped. Tree-shaking friendly
3. **"Generators are slow"** - Effect internals are NOT built on generators. Generator API is equally performant to async/await
4. **"Same as RxJS"** - Effect's base type is single-shot (like a lazy Promise), not multi-shot like Observables
