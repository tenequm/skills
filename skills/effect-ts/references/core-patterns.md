# Core Patterns

## The Effect Type

```typescript
Effect<Success, Error, Requirements>
//      ^        ^       ^
//      |        |       └── Dependencies needed (provided via Layers)
//      |        └── Expected errors (typed, must be handled)
//      └── Success value
```

An `Effect` is a lazy description of a program. Nothing runs until you call `run*` at the edge.

## Creating Effects

```typescript
import { Effect } from "effect"

// From a pure value
const succeed = Effect.succeed(42)

// From a failure
const fail = Effect.fail(new Error("boom"))

// From synchronous code that might throw
const sync = Effect.sync(() => JSON.parse(rawJson))

// From a Promise (typed error on rejection)
const async = Effect.tryPromise({
  try: () => fetch(url),
  catch: (err) => new FetchError({ cause: err })
})

// From a Promise that never rejects
const safe = Effect.promise(() => fs.readFile(path))
```

## Composition with Effect.gen

Use `Effect.gen` for imperative-style multi-step logic:

```typescript
const program = Effect.gen(function*() {
  const user = yield* fetchUser(id)
  const posts = yield* fetchPosts(user.id)
  return { user, posts }
})
```

**v4: Use `Effect.fn` for named functions** (adds automatic span + better stack traces):

```typescript
// v4 only
const fetchUserPosts = Effect.fn("fetchUserPosts")(
  function*(id: string): Effect.fn.Return<UserPosts, ApiError> {
    const user = yield* fetchUser(id)
    const posts = yield* fetchPosts(user.id)
    return { user, posts }
  },
  Effect.catch((e) => Effect.log(`Failed: ${e}`))
)
```

## Composition with Pipes

Use pipes for simple linear transforms:

```typescript
const program = fetchUser(id).pipe(
  Effect.map((user) => user.name),
  Effect.tap((name) => Effect.log(`Found: ${name}`)),
  Effect.catchTag("NotFound", () => Effect.succeed("anonymous"))
)
```

## Running Effects

**Entry points** - use platform-specific `runMain`:

```typescript
import { NodeRuntime } from "@effect/platform-node"

const main = Effect.gen(function*() {
  yield* Effect.log("Starting...")
  // your program here
})

NodeRuntime.runMain(main) // handles SIGINT gracefully
```

**One-off execution** (scripts, tests):

```typescript
await Effect.runPromise(myEffect)       // throws on failure
const exit = await Effect.runPromiseExit(myEffect) // returns Exit
Effect.runSync(myEffect)                // sync only, throws on async
```

**Integrating with non-Effect frameworks** (Hono, Express, etc.) - use `ManagedRuntime`:

```typescript
import { ManagedRuntime } from "effect"

// Create once at startup
const runtime = ManagedRuntime.make(MyAppLayer)

// Use in route handlers
app.get("/users/:id", async (c) => {
  const result = await runtime.runPromise(fetchUser(c.req.param("id")))
  return c.json(result)
})
```

## Effect.all - Parallel/Sequential Collection

```typescript
// Sequential (default)
const results = yield* Effect.all([effectA, effectB, effectC])

// Parallel (bounded)
const results = yield* Effect.all([effectA, effectB, effectC], {
  concurrency: 5
})

// Fully parallel
const results = yield* Effect.all([effectA, effectB, effectC], {
  concurrency: "unbounded"
})

// With error accumulation (collect all errors, not just first)
const results = yield* Effect.all([effectA, effectB], {
  concurrency: "unbounded",
  mode: "validate"
})
```

## Key Combinators

| Combinator       | Purpose                                                |
|------------------|--------------------------------------------------------|
| `Effect.map`     | Transform the success value                            |
| `Effect.flatMap` | Chain effects (success of first feeds into next)       |
| `Effect.tap`     | Side-effect on success without changing the value      |
| `Effect.andThen` | Like flatMap but also accepts plain values/functions   |
| `Effect.all`     | Combine multiple effects (sequential or parallel)      |
| `Effect.forEach` | Map over an iterable with an effectful function        |
| `Effect.if`      | Branch on a boolean condition                          |
| `Effect.match`   | Pattern match on success/failure                       |
| `Effect.zip`     | Combine two effects into a tuple                       |
| `Effect.orDie`   | Convert typed error to defect (unrecoverable)          |
