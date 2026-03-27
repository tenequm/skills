# Migrating from async/await to Effect

Mechanical conversion patterns for moving Promise-based code to Effect.

## Promise -> Effect

```typescript
// BEFORE: async/await
async function fetchUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`)
  if (!response.ok) throw new Error("Not found")
  return response.json()
}

// AFTER: Effect (v3)
const fetchUser = (id: string): Effect.Effect<User, FetchError> =>
  Effect.tryPromise({
    try: () => fetch(`/api/users/${id}`).then((r) => {
      if (!r.ok) throw new Error("Not found")
      return r.json()
    }),
    catch: (err) => new FetchError({ cause: err })
  })

// AFTER: Effect (v4 with Effect.fn)
const fetchUser = Effect.fn("fetchUser")(
  function*(id: string): Effect.fn.Return<User, FetchError> {
    return yield* Effect.tryPromise({
      try: () => fetch(`/api/users/${id}`).then((r) => {
        if (!r.ok) throw new Error("Not found")
        return r.json()
      }),
      catch: (err) => new FetchError({ cause: err })
    })
  }
)
```

## try/catch -> typed errors

```typescript
// BEFORE
async function processPayment(amount: number) {
  try {
    const result = await chargeCard(amount)
    return result
  } catch (err) {
    if (err instanceof InsufficientFunds) {
      return { status: "declined" }
    }
    throw err // re-throw unknown errors
  }
}

// AFTER
const processPayment = (amount: number) =>
  chargeCard(amount).pipe(
    Effect.catchTag("InsufficientFunds", () =>
      Effect.succeed({ status: "declined" as const })
    )
    // Unknown errors become defects automatically
  )
```

## Promise.all -> Effect.all

```typescript
// BEFORE
const [user, posts] = await Promise.all([
  fetchUser(id),
  fetchPosts(id)
])

// AFTER (parallel)
const [user, posts] = yield* Effect.all(
  [fetchUser(id), fetchPosts(id)],
  { concurrency: "unbounded" }
)

// With bounded concurrency
const results = yield* Effect.all(
  urls.map((url) => fetchUrl(url)),
  { concurrency: 5 }
)
```

## Callback APIs -> Effect.async

```typescript
// BEFORE
function readFile(path: string): Promise<string> {
  return new Promise((resolve, reject) => {
    fs.readFile(path, "utf-8", (err, data) => {
      if (err) reject(err)
      else resolve(data)
    })
  })
}

// AFTER
const readFile = (path: string): Effect.Effect<string, FileError> =>
  Effect.async((resume) => {
    fs.readFile(path, "utf-8", (err, data) => {
      if (err) resume(Effect.fail(new FileError({ cause: err })))
      else resume(Effect.succeed(data))
    })
  })
```

## Class with state -> Service + Ref

```typescript
// BEFORE
class Counter {
  private count = 0
  increment() { this.count++ }
  getCount() { return this.count }
}

// AFTER
class Counter extends Context.Tag("Counter")<Counter, {
  readonly increment: Effect.Effect<void>
  readonly getCount: Effect.Effect<number>
}>() {}

const CounterLive = Layer.effect(Counter,
  Effect.gen(function*() {
    const ref = yield* Ref.make(0)
    return {
      increment: Ref.update(ref, (n) => n + 1),
      getCount: Ref.get(ref)
    }
  })
)
```

## Key Principles

1. **Effects are lazy**: nothing runs until `run*` is called. Don't mix `await` and `yield*`
2. **Errors are typed**: convert thrown exceptions to typed errors at boundaries with `Effect.tryPromise`
3. **Dependencies are explicit**: extract shared state/clients into services with Context.Tag / ServiceMap.Service
4. **run* at edges only**: libraries return `Effect` values. Only call `runPromise` / `runMain` at the program boundary
5. **Incremental adoption**: you can wrap individual functions with `Effect.tryPromise` and gradually expand
