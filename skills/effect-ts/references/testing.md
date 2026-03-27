# Testing Effect Code

## @effect/vitest (Recommended)

```typescript
import { it } from "@effect/vitest"
import { Effect } from "effect"

// Effect-based test
it.effect("fetches user", () =>
  Effect.gen(function*() {
    const user = yield* fetchUser("123")
    expect(user.name).toBe("Alice")
  })
)

// With layers
it.effect("fetches user with db", () =>
  Effect.gen(function*() {
    const user = yield* fetchUser("123")
    expect(user.name).toBe("Alice")
  }).pipe(Effect.provide(TestDatabaseLayer))
)

// With shared layer across tests
const { it: testWithDb } = it.layer(TestDatabaseLayer)

testWithDb.effect("test 1", () => /* ... */)
testWithDb.effect("test 2", () => /* ... */)
```

## Layer-Based Test Doubles

Replace real services with test implementations via layers:

```typescript
// Production service
class Database extends Context.Tag("Database")<Database, {
  readonly query: (sql: string) => Effect.Effect<unknown[]>
}>() {}

// Test layer - deterministic mock
const TestDatabase = Layer.succeed(Database, {
  query: (sql) => Effect.succeed([{ id: 1, name: "test-user" }])
})

// Stateful test double
const TestDatabase = Layer.effect(Database,
  Effect.gen(function*() {
    const store = yield* Ref.make<Map<string, unknown[]>>(new Map())
    return {
      query: (sql) => Effect.gen(function*() {
        const data = yield* Ref.get(store)
        return data.get(sql) ?? []
      })
    }
  })
)
```

## TestClock (Deterministic Time)

Control time in tests for schedule/timeout/delay testing:

```typescript
import { TestClock, TestContext } from "effect"

it.effect("retries 3 times with backoff", () =>
  Effect.gen(function*() {
    // Fork the effect under test
    const fiber = yield* Effect.fork(
      Effect.retry(failingOp, Schedule.exponential("1 second").pipe(
        Schedule.compose(Schedule.recurs(3))
      ))
    )

    // Advance time to trigger retries
    yield* TestClock.adjust("1 second")  // 1st retry
    yield* TestClock.adjust("2 seconds") // 2nd retry
    yield* TestClock.adjust("4 seconds") // 3rd retry

    const result = yield* Fiber.join(fiber)
    // Assert result...
  }).pipe(Effect.provide(TestContext.TestContext))
)
```

## Testing Patterns

### Assert on typed errors

```typescript
it.effect("fails with NotFound", () =>
  Effect.gen(function*() {
    const exit = yield* Effect.exit(fetchUser("nonexistent"))
    expect(exit).toEqual(Exit.fail(new NotFoundError({ id: "nonexistent" })))
  })
)
```

### Assert on Exit

```typescript
import { Exit } from "effect"

it.effect("returns success exit", () =>
  Effect.gen(function*() {
    const exit = yield* Effect.exit(myEffect)
    expect(Exit.isSuccess(exit)).toBe(true)
  })
)
```

### Test with timeout

```typescript
it.effect("completes within 5 seconds", () =>
  myEffect.pipe(
    Effect.timeout("5 seconds"),
    Effect.map((result) => expect(result).toBeDefined())
  )
)
```

### Override a single service

```typescript
it.effect("uses custom logger", () =>
  program.pipe(
    Effect.provideService(Logger, {
      log: (msg) => Effect.sync(() => messages.push(msg))
    })
  )
)
```

## Common Testing Mistakes

1. **Forgetting TestContext**: `TestClock.adjust` requires `TestContext.TestContext` to be provided
2. **Not forking before adjusting time**: `TestClock.adjust` only affects already-running fibers. Fork the effect first, then adjust
3. **Testing implementation instead of behavior**: Use Layer swaps to test service behavior, not internal implementation details
4. **Missing `Effect.exit` for error assertions**: Use `Effect.exit` to inspect the Exit value instead of catching errors
