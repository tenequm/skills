# Software Transactional Memory (STM)

Effect's transactional layer lets you compose atomic updates across multiple mutable cells with no locks and no race conditions. Transactions are **optimistic with retry** (MVCC-style: versions are checked at commit; on conflict the whole block re-runs), not lock-based.

The driver is `Effect.tx` — there is **no `Effect.atomic` and no `Effect.transaction`**. Transactional cells are the `Tx*` modules (`TxRef`, `TxQueue`, `TxHashMap`, `TxChunk`, `TxSemaphore`, ...).

```typescript
import { Effect, TxRef } from "effect"
```

## Atomic Updates Across Cells

```typescript
const transfer = Effect.gen(function*() {
  const from = yield* TxRef.make(100)
  const to = yield* TxRef.make(0)

  // Both writes commit together, or neither does
  yield* Effect.tx(
    Effect.gen(function*() {
      yield* TxRef.update(from, (n) => n - 50)
      yield* TxRef.update(to, (n) => n + 50)
    })
  )

  return [yield* TxRef.get(from), yield* TxRef.get(to)] // [50, 50]
})
```

- `Effect.tx(effect)` is the transaction **boundary** — the outermost call commits/rolls back atomically. Nested `Effect.tx` calls compose into the same journal (they do not start a separate transaction).
- `TxRef` operations: `TxRef.make`, `TxRef.get`, `TxRef.set`, `TxRef.update`, `TxRef.modify`. Inside a `tx` block they read/write the transaction journal; outside one they run in a singleton transaction.

## Waiting for a Condition (`Effect.txRetry`)

To block until some transactional state changes, call `Effect.txRetry`. It marks the transaction for retry and suspends until one of the `TxRef`s it read is modified, then re-runs the block:

```typescript
import { Effect, TxRef } from "effect"

// Wait until the queue ref is non-empty, then take one item
const takeWhenReady = (queue: TxRef.TxRef<ReadonlyArray<string>>) =>
  Effect.tx(
    Effect.gen(function*() {
      const items = yield* TxRef.get(queue)
      if (items.length === 0) {
        return yield* Effect.txRetry // suspend; re-run when `queue` changes
      }
      yield* TxRef.set(queue, items.slice(1))
      return items[0]
    })
  )
```

## Transactional Collections

Beyond `TxRef`, the same atomicity applies to: `TxQueue`, `TxPubSub`, `TxSubscriptionRef`, `TxHashMap`, `TxHashSet`, `TxChunk`, `TxPriorityQueue`, `TxDeferred`, `TxSemaphore`, `TxReentrantLock`. Compose operations on any mix of these inside a single `Effect.tx` for all-or-nothing semantics.
