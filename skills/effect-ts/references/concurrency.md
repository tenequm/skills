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
// v3
import { Effect } from "effect"

const semaphore = yield* Effect.makeSemaphore(3)

// Limit concurrency (method-style on the returned semaphore)
const limited = semaphore.withPermits(1)(expensiveOp)
```

```typescript
// v4 — Effect.makeSemaphore is removed. Use the Semaphore module.
import { Semaphore } from "effect"

const semaphore = yield* Semaphore.make(3)

// withPermits is data-first in v4: pass the semaphore as the first arg.
const limited = Semaphore.withPermits(semaphore, 1)(expensiveOp)
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

## Managing Dynamic Sets of Fibers

`FiberHandle` (one fiber), `FiberMap` (keyed) and `FiberSet` (unkeyed) manage fibers whose set changes at runtime. All three are **scoped** — closing the surrounding scope interrupts every managed fiber, and fibers self-remove on completion. `FiberMap.run(map, key, effect)` forks `effect` under `key`, interrupting any prior fiber at that key (pass `{ onlyIfMissing: true }` to keep the existing one).

```typescript
import { Effect, FiberMap } from "effect"

const program = Effect.scoped(
  Effect.gen(function*() {
    const fibers = yield* FiberMap.make<string>()

    // Start (or restart) a background fiber per connection id
    yield* FiberMap.run(fibers, "conn-1", handleConnection(conn1))
    yield* FiberMap.run(fibers, "conn-2", handleConnection(conn2))

    yield* serveRequests()
    // All managed fibers interrupted when this scope closes
  })
)
```

## SubscriptionRef (Observable State)

`SubscriptionRef` is a `Ref` whose updates can be observed as a `Stream`. `.changes` emits the current value first, then every subsequent update — useful for reactive state, config hot-reload, or fan-out to watchers.

```typescript
import { Effect, Stream, SubscriptionRef } from "effect"

const program = Effect.gen(function*() {
  const ref = yield* SubscriptionRef.make(0)

  // Subscribe in the background; receives 0, then each update
  yield* Effect.forkScoped(
    Stream.runForEach(SubscriptionRef.changes(ref), (n) =>
      Effect.log(`value is now ${n}`)
    )
  )

  yield* SubscriptionRef.set(ref, 1)
  yield* SubscriptionRef.update(ref, (n) => n + 1) // 2
})
```

## Request Batching & Caching (Request / RequestResolver)

When the same data is fetched repeatedly (the classic N+1 problem), model each fetch as a typed `Request` and resolve a batch of them through a `RequestResolver`. Effect automatically deduplicates identical requests in flight and batches those collected within the same step, then `Effect.request` reads a single result. The resolver receives all pending entries at once — issue one bulk query, then complete each entry.

```typescript
import { Console, Effect, Exit, Request, RequestResolver } from "effect"

interface GetUser extends Request.Request<string, Error> {
  readonly _tag: "GetUser"
  readonly id: number
}
const GetUser = Request.tagged<GetUser>("GetUser")

// runAll receives the full batch of pending entries; complete each with an Exit
const UserResolver = RequestResolver.make<GetUser>(
  Effect.fnUntraced(function*(entries) {
    const ids = entries.map((e) => e.request.id)
    const rows = yield* bulkFetchUsers(ids) // ONE query for the whole batch
    for (const entry of entries) {
      yield* Request.complete(entry, Exit.succeed(rows[entry.request.id]))
    }
  })
)

const program = Effect.gen(function*() {
  // These two run in the same step -> batched into one runAll call
  const [a, b] = yield* Effect.all(
    [Effect.request(GetUser({ id: 1 }), UserResolver),
     Effect.request(GetUser({ id: 2 }), UserResolver)],
    { concurrency: "unbounded" }
  )
  yield* Console.log([a, b])
})
```

`Request.tagged<T>(tag)` builds the constructor; `Request.Class` is the class form. `RequestResolver.make(runAll)` is the basic batched resolver; `RequestResolver.makeGrouped` partitions entries by a computed key, and `RequestResolver.fromEffect` lifts a per-request effect. Group several resolvers behind a service so callers just `yield* Effect.request(...)`.

## Worker Threads (`effect/unstable/workers`)

There is **no `Worker.makePool` / high-level worker-pool API** in v4. The intended way to offload work to worker threads is **RPC-over-worker**: define an `RpcGroup` (see `references/rpc.md`), run an `RpcServer` inside the worker, and create a pooled client with `RpcClient.layerProtocolWorker({ size })`. Calling a typed RPC method dispatches it onto a worker in the pool.

```typescript
import { Layer } from "effect"
import { RpcClient } from "effect/unstable/rpc"
import { NodeWorker } from "@effect/platform-node"
import { Worker as NodeWorkerThread } from "node:worker_threads"

// Client side: a pool of worker threads; RPC calls run on a worker
const WorkerClientLive = MyRpcClient.layer.pipe(
  Layer.provide(RpcClient.layerProtocolWorker({ size: 4 })),
  Layer.provide(
    NodeWorker.layer(() => new NodeWorkerThread(new URL("./worker.ts", import.meta.url)))
  )
)
// Inside ./worker.ts: RpcServer.layerProtocolWorkerRunner + your handler layer
// + NodeWorkerRunner.layer (see references/rpc.md for the server side).
```

The low-level `Worker` / `WorkerRunner` modules exist but are platform primitives, not an ergonomic pool — prefer the RPC transport above.
