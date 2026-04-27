# Retry and Scheduling

Effect's `Schedule` module provides composable, typed retry and repetition policies.

## Basic Retry

```typescript
import { Effect, Schedule } from "effect"

// Retry up to 3 times
const retried = Effect.retry(unstableOp, Schedule.recurs(3))

// Retry with exponential backoff
const retried = Effect.retry(unstableOp, Schedule.exponential("100 millis"))

// Retry with exponential backoff + jitter + max retries (v3)
const policy = Schedule.exponential("200 millis", 2).pipe(
  Schedule.compose(Schedule.recurs(5)),
  Schedule.jittered
)
const retried = Effect.retry(unstableOp, policy)

// v4 — Schedule.compose is removed. Use Schedule.take(n) to bound by attempts:
const policyV4 = Schedule.exponential("200 millis", 2).pipe(
  Schedule.take(5),
  Schedule.jittered
)
const retriedV4 = Effect.retry(unstableOp, policyV4)

// Version-agnostic alternative: pass `times` in the retry options object
const retriedAny = Effect.retry(unstableOp, {
  schedule: Schedule.exponential("200 millis", 2).pipe(Schedule.jittered),
  times: 5
})
```

## Built-In Schedules

| Schedule                        | Behavior                                      |
|---------------------------------|-----------------------------------------------|
| `Schedule.recurs(n)`           | Retry/repeat up to n times                     |
| `Schedule.spaced("1 second")`  | Fixed spacing between iterations               |
| `Schedule.exponential("100 millis")` | Exponential backoff (doubles each time)  |
| `Schedule.exponential("100 millis", 1.5)` | Custom growth factor             |
| `Schedule.fibonacci("100 millis")` | Fibonacci backoff                          |
| `Schedule.fixed("5 seconds")`  | Fixed interval (accounts for elapsed time)     |
| `Schedule.forever`             | Repeat indefinitely                            |
| `Schedule.once` (v3 only)      | Run once more — v4: use `Schedule.recurs(0)`   |
| `Schedule.jittered`            | Add randomness (combine with other schedules)  |
| `Schedule.take(n)`             | Bound any schedule to n iterations (v4 idiom)  |
| `Schedule.cron("0 * * * *")`  | Cron-based scheduling                          |

## Composing Schedules

```typescript
// Sequential: first policy, then second (recurs 3 times, then exponential)
const sequential = Schedule.recurs(3).pipe(
  Schedule.andThen(Schedule.exponential("1 second"))
)

// Intersection: both constraints must be satisfied
// (exponential backoff, but max 5 retries)
// v3: Schedule.compose
const bounded = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)

// v4: Schedule.compose is removed. Use Schedule.take(n) for the same intent.
const boundedV4 = Schedule.exponential("100 millis").pipe(
  Schedule.take(5)
)

// Union: either constraint can trigger
const either = Schedule.spaced("1 second").pipe(
  Schedule.either(Schedule.recurs(10))
)
```

## Conditional Retry (only on specific errors)

```typescript
// Retry only on retryable errors
// Pass `times` in the options object (works in both v3 and v4); the schedule
// itself just controls delay shape.
const retried = Effect.retry(fetchFromApi, {
  schedule: Schedule.exponential("200 millis").pipe(Schedule.jittered),
  times: 4,
  while: (error) => error._tag === "NetworkError" || error._tag === "RateLimitError"
})

// Or using until (inverse condition)
const retriedUntil = Effect.retry(fetchFromApi, {
  schedule: Schedule.exponential("200 millis").pipe(Schedule.jittered),
  times: 4,
  until: (error) => error._tag === "AuthError" // stop retrying on auth errors
})
```

## Repetition (success-based)

```typescript
// Repeat an effect 5 times
const repeated = Effect.repeat(pollStatus, Schedule.recurs(5))

// Repeat every second forever
const polling = Effect.repeat(checkHealth, Schedule.spaced("1 second"))

// Repeat until a condition is met
const waitForReady = Effect.repeat(checkStatus, {
  until: (status) => status === "ready"
})
```

## Timeout

```typescript
// Timeout after 5 seconds (returns Option - None on timeout)
const withTimeout = Effect.timeout(slowOp, "5 seconds")

// Timeout with fallback
const withFallback = Effect.timeoutTo(slowOp, {
  duration: "5 seconds",
  onTimeout: () => Effect.succeed(defaultValue)
})

// Timeout that fails
const withError = Effect.timeoutFail(slowOp, {
  duration: "5 seconds",
  onTimeout: () => new TimeoutError({ message: "operation timed out" })
})
```

## Combining Retry + Timeout

```typescript
const resilient = fetchFromUpstream(params).pipe(
  Effect.timeout("10 seconds"),
  // Version-agnostic retry shape — `times` caps the attempts and works in v3 + v4.
  Effect.retry({
    schedule: Schedule.exponential("200 millis").pipe(Schedule.jittered),
    times: 3
  }),
  Effect.withSpan("upstream.fetch")
)
```

## HttpClient.retryTransient (v3 @effect/platform)

For HTTP calls, `@effect/platform` provides a built-in retry for transient failures (connection errors, 429, 503):

```typescript
import { HttpClient } from "@effect/platform"

// v3 — Schedule.compose still works
const resilientClient = HttpClient.retryTransient({
  schedule: Schedule.exponential("200 millis").pipe(
    Schedule.compose(Schedule.recurs(3))
  )
})

// v4 (effect/unstable/http) — use Schedule.take(n) instead of compose
const resilientClientV4 = HttpClient.retryTransient({
  schedule: Schedule.exponential("200 millis").pipe(Schedule.take(3))
})
```

## RateLimiter

```typescript
// v3 — top-level module with make/withCost
import { RateLimiter } from "effect"

const limiter = yield* RateLimiter.make({ limit: 10, interval: "1 second" })
const limited = RateLimiter.withCost(limiter, 1)(fetchFromApi(params))
```

```typescript
// v4 — moved to effect/unstable/persistence and uses a Service-based API.
// There is no withCost; per-call cost is the `tokens` option on consume.
import { Effect, Layer } from "effect"
import { RateLimiter } from "effect/unstable/persistence"

const program = Effect.gen(function*() {
  const withLimiter = yield* RateLimiter.makeWithRateLimiter
  return yield* fetchFromApi(params).pipe(
    withLimiter({
      key: "fetchFromApi",
      limit: 10,
      window: "1 second",
      algorithm: "fixed-window",
      onExceeded: "delay",
      tokens: 1 // per-call cost
    })
  )
})

// Provide the in-memory store + RateLimiter service
const Live = RateLimiter.layer.pipe(Layer.provide(RateLimiter.layerStoreMemory))
const main = program.pipe(Effect.provide(Live))
```
