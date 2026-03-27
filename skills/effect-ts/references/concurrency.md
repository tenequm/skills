# Concurrency

Effect uses fiber-based structured concurrency. Fibers are lightweight virtual threads managed by the Effect runtime.

## Forking Fibers

### v3

```typescript
import { Effect, Fiber } from "effect"

// Fork as child (interrupted when parent ends)
const fiber = yield* Effect.fork(myEffect)

// Fork as daemon (outlives parent)
const fiber = yield* Effect.forkDaemon(longRunning)

// Fork tied to a Scope
const fiber = yield* Effect.forkScoped(background)
```

### v4

```typescript
import { Effect, Fiber } from "effect"

// Fork as child
const fiber = yield* Effect.forkChild(myEffect)

// Fork detached (outlives parent)
const fiber = yield* Effect.forkDetach(longRunning)

// Fork tied to a Scope (unchanged)
const fiber = yield* Effect.forkScoped(background)

// New options
const fiber = yield* Effect.forkChild(myEffect, {
  startImmediately: true,   // begin executing immediately
  uninterruptible: true     // cannot be interrupted
})
```

## Joining and Interrupting

```typescript
// Wait for a fiber to complete
const result = yield* Fiber.join(fiber)

// Interrupt a fiber
yield* Fiber.interrupt(fiber)

// v4: Fiber is NOT an Effect - must use Fiber.join explicitly
// v3: yield* fiber was allowed (Fiber was an Effect subtype)
```

## Parallel Execution

```typescript
// Process items with bounded concurrency
const results = yield* Effect.all(
  items.map((item) => processItem(item)),
  { concurrency: 5 }
)

// forEach variant
const results = yield* Effect.forEach(
  items,
  (item) => processItem(item),
  { concurrency: 10 }
)
```

## Racing

```typescript
// First to succeed wins, loser is interrupted
const result = yield* Effect.race(fetchFromCache, fetchFromDb)

// Race multiple effects
const result = yield* Effect.raceAll([
  fetchFromCdn1,
  fetchFromCdn2,
  fetchFromCdn3
])
```

## Interruption

Interruption is cooperative, not preemptive. Fibers check for interruption at yield points.

```typescript
// Register cleanup on interruption
const withCleanup = myEffect.pipe(
  Effect.onInterrupt(() => Effect.log("Interrupted! Cleaning up..."))
)

// Make a region uninterruptible
const critical = Effect.uninterruptible(
  Effect.gen(function*() {
    yield* beginTransaction()
    yield* doWork()
    yield* commitTransaction()
  })
)

// Interruptible region inside an uninterruptible one
const mixed = Effect.uninterruptible(
  Effect.gen(function*() {
    yield* criticalSetup()
    yield* Effect.interruptible(longComputation)
    yield* criticalTeardown()
  })
)
```

## Queue

Bounded queues provide back-pressure; dropping/sliding queues do not.

```typescript
import { Queue } from "effect"

// Bounded queue (back-pressure: offer suspends when full)
const queue = yield* Queue.bounded<string>(100)

// Dropping queue (discards new items when full)
const queue = yield* Queue.dropping<string>(100)

// Sliding queue (discards oldest items when full)
const queue = yield* Queue.sliding<string>(100)

// Offer and take
yield* Queue.offer(queue, "hello")
const item = yield* Queue.take(queue)

// Take all available
const items = yield* Queue.takeAll(queue)
```

## Semaphore

```typescript
import { Effect } from "effect"

const semaphore = yield* Effect.makeSemaphore(3)

// Limit concurrency
const limited = semaphore.withPermits(1)(expensiveOp)
```

## Deferred (one-shot signal)

```typescript
import { Deferred, Effect } from "effect"

const deferred = yield* Deferred.make<string, never>()

// Complete the deferred (can only be done once)
yield* Deferred.succeed(deferred, "done")

// Wait for completion
// v3: yield* deferred (Deferred was an Effect subtype)
// v4: must use Deferred.await
const value = yield* Deferred.await(deferred)
```

## Structured Concurrency Pattern: Background Worker

```typescript
const withWorker = Effect.scoped(
  Effect.gen(function*() {
    // Background fiber tied to scope - auto-interrupted on scope exit
    yield* Effect.forkScoped(
      Effect.repeat(
        processQueue,
        Schedule.spaced("100 millis")
      )
    )
    // Main work continues...
    yield* handleRequests()
  })
)
```
