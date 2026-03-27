# Retry and Scheduling

Effect's `Schedule` module provides composable, typed retry and repetition policies.

## Basic Retry

```typescript
import { Effect, Schedule } from "effect"

// Retry up to 3 times
const retried = Effect.retry(unstableOp, Schedule.recurs(3))

// Retry with exponential backoff
const retried = Effect.retry(unstableOp, Schedule.exponential("100 millis"))

// Retry with exponential backoff + jitter + max retries
const policy = Schedule.exponential("200 millis", 2).pipe(
  Schedule.compose(Schedule.recurs(5)),
  Schedule.jittered
)
const retried = Effect.retry(unstableOp, policy)
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
| `Schedule.once`                | Run once more                                  |
| `Schedule.jittered`            | Add randomness (combine with other schedules)  |
| `Schedule.cron("0 * * * *")`  | Cron-based scheduling                          |

## Composing Schedules

```typescript
// Sequential: first policy, then second (recurs 3 times, then exponential)
const sequential = Schedule.recurs(3).pipe(
  Schedule.andThen(Schedule.exponential("1 second"))
)

// Intersection: both constraints must be satisfied
// (exponential backoff, but max 5 retries)
const bounded = Schedule.exponential("100 millis").pipe(
  Schedule.compose(Schedule.recurs(5))
)

// Union: either constraint can trigger
const either = Schedule.spaced("1 second").pipe(
  Schedule.either(Schedule.recurs(10))
)
```

## Conditional Retry (only on specific errors)

```typescript
// Retry only on retryable errors
const policy = Schedule.exponential("200 millis").pipe(
  Schedule.compose(Schedule.recurs(4)),
  Schedule.jittered
)

const retried = Effect.retry(fetchFromApi, {
  schedule: policy,
  while: (error) => error._tag === "NetworkError" || error._tag === "RateLimitError"
})

// Or using until (inverse condition)
const retried = Effect.retry(fetchFromApi, {
  schedule: policy,
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
  Effect.retry(
    Schedule.exponential("200 millis").pipe(
      Schedule.compose(Schedule.recurs(3)),
      Schedule.jittered
    )
  ),
  Effect.withSpan("upstream.fetch")
)
```

## HttpClient.retryTransient (v3 @effect/platform)

For HTTP calls, `@effect/platform` provides a built-in retry for transient failures (connection errors, 429, 503):

```typescript
import { HttpClient } from "@effect/platform"

const resilientClient = HttpClient.retryTransient({
  schedule: Schedule.exponential("200 millis").pipe(
    Schedule.compose(Schedule.recurs(3))
  )
})
```

## RateLimiter

```typescript
import { RateLimiter } from "effect"

const limiter = yield* RateLimiter.make({ limit: 10, interval: "1 second" })

// Wrap calls with the limiter
const limited = RateLimiter.withCost(limiter, 1)(fetchFromApi(params))
```
