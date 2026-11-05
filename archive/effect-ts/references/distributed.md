# Distributed & Durable Execution

Effect's distributed-systems modules — Cluster (sharded stateful entities), Workflow (durable, resumable execution), and EventLog (event sourcing) — all live under `effect/unstable/*` and are explicitly **unstable** (APIs may shift between minor releases). Reach for them only when the architecture calls for it; most apps do not.

All three follow the same convention: the **tag/name is the first argument** (`Entity.make(tag, ...)`, `Workflow.make(tag, ...)`, `Event.make({ tag, ... })`).

## Cluster: Sharded Entities

An `Entity` is a stateful actor addressed by `entityId`; `Sharding` routes messages to the shard owning that id. Messages are typed `Rpc` definitions (see `references/rpc.md`).

```typescript
import { Effect, Schema } from "effect"
import { Entity, ShardingConfig } from "effect/unstable/cluster"
import { Rpc } from "effect/unstable/rpc"

class User extends Schema.Class<User>("User")({
  id: Schema.Number,
  name: Schema.String
}) {}

// Tag first, then an array of Rpc message definitions
const UserEntity = Entity.make("UserEntity", [
  Rpc.make("GetUser", { payload: { id: Schema.Number }, success: User })
])

const UserEntityLayer = UserEntity.toLayer({
  GetUser: (envelope) =>
    Effect.succeed(new User({ id: envelope.payload.id, name: `User ${envelope.payload.id}` }))
})

// In tests, address an entity with an in-memory client:
const program = Effect.gen(function*() {
  const makeClient = yield* Entity.makeTestClient(UserEntity, UserEntityLayer)
  const client = yield* makeClient("user-1") // addressed by entityId
  return yield* client.GetUser({ id: 1 })     // message by rpc tag
}).pipe(Effect.provide(ShardingConfig.layer({})))
```

In production, provide a real `Sharding` layer + a runner backend (SQL/Http/Socket) instead of `makeTestClient`, and obtain the client via `UserEntity.client`.

## Workflow: Durable Execution

A `Workflow` is execution that survives process restarts — steps (`Activity`) are checkpointed so a resumed workflow replays completed steps instead of re-running them.

```typescript
import { Effect, Layer, Schema } from "effect"
import { Workflow, WorkflowEngine } from "effect/unstable/workflow"

const IncrementWorkflow = Workflow.make("IncrementWorkflow", {
  payload: { value: Schema.Number },
  success: Schema.Number,
  idempotencyKey: ({ value }) => String(value)
})

const IncrementLayer = IncrementWorkflow.toLayer(
  ({ value }) => Effect.succeed(value + 1)
)

const program = Effect.gen(function*() {
  return yield* IncrementWorkflow.execute({ value: 1 }) // 2
}).pipe(
  Effect.provide(
    IncrementLayer.pipe(Layer.provideMerge(WorkflowEngine.layerMemory))
  )
)
```

`Workflow.make(tag, { payload, success?, error?, idempotencyKey?, ... })` returns a workflow with `.execute`, `.poll`, `.interrupt`, `.resume`, `.toLayer`, `.withCompensation`. It also supports class form: `class MyWorkflow extends Workflow.make(...) {}` (the tag-first signature landed in beta.75). Inside a workflow, wrap side-effecting steps in `Activity.make({ name, execute, ... })` and use `Activity.retry({ times })`, `DurableClock.sleep`, and `DurableDeferred` for durable waits. `DurableQueue` provides a persistent work queue. Use `WorkflowEngine.layerMemory` for dev/tests; a cluster-backed engine for production.

## EventLog: Event Sourcing

`EventLog` is a full event-sourcing stack: define event groups, write events, and run handlers against a journal (in-memory, IndexedDB, or SQL), with optional encryption and remote replication.

```typescript
import { Effect, Layer, Schema } from "effect"
import * as EventGroup from "effect/unstable/eventlog/EventGroup"
import * as EventJournal from "effect/unstable/eventlog/EventJournal"
import * as EventLog from "effect/unstable/eventlog/EventLog"

const UserEvents = EventGroup.empty.add({
  tag: "UserCreated",
  primaryKey: (payload) => payload.id,
  payload: Schema.Struct({ id: Schema.String })
})

const schema = EventLog.schema(UserEvents)

const HandlersLive = EventLog.group(UserEvents, (handlers) =>
  handlers.handle("UserCreated", ({ payload }) =>
    Effect.log(`created ${payload.id}`)
  )
).pipe(Layer.provide(EventLog.layerRegistry))

const program = Effect.gen(function*() {
  const log = yield* EventLog.EventLog
  yield* log.write({ schema, event: "UserCreated", payload: { id: "user-1" } })
}).pipe(
  Effect.provide(
    EventLog.layer(schema, HandlersLive).pipe(Layer.provide(EventJournal.layerMemory))
  )
)
```

Build events with `EventGroup.empty.add({ tag, primaryKey, payload })` (or standalone `Event.make({ tag, ... })`), register handlers with `EventLog.group`, and assemble with `EventLog.layer(schema, handlers)` over a journal backend (`EventJournal.layerMemory` / `layerIndexedDb` / SQL).
