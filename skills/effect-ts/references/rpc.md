# RPC

`effect/unstable/rpc` provides typed, Schema-validated client/server RPC. Define requests once as an `RpcGroup`; implement them as a handler layer on the server; call them as typed methods on the client. Transport (HTTP, WebSocket, worker) and serialization (JSON, NDJSON, MsgPack) are pluggable layers. (Unstable module, `@since 4.0.0`.)

```typescript
import { Rpc, RpcGroup, RpcServer, RpcClient, RpcSerialization } from "effect/unstable/rpc"
```

## Define a Group

```typescript
import { Schema } from "effect"
import { Rpc, RpcGroup } from "effect/unstable/rpc"

class User extends Schema.Class<User>("User")({
  id: Schema.String,
  name: Schema.String
}) {}

const UserRpcs = RpcGroup.make(
  Rpc.make("GetUser", { payload: { id: Schema.String }, success: User }),
  Rpc.make("ListUsers", { success: Schema.Array(User), stream: true })
)
```

`Rpc.make(tag, { payload?, success?, error?, stream?, primaryKey? })` — `payload` accepts struct fields or a Schema; `stream: true` makes the result a stream of `success`.

## Implement Handlers (server)

```typescript
import { Effect, Layer, Stream } from "effect"
import { RpcServer } from "effect/unstable/rpc"

const UsersLive = UserRpcs.toLayer(
  UserRpcs.of({
    GetUser: ({ id }) => Effect.succeed(new User({ id, name: "Ada" })),
    ListUsers: () => Stream.fromIterable([new User({ id: "1", name: "Ada" })])
  })
)

// Server = handlers + protocol + serialization
const ServerLive = RpcServer.layer(UserRpcs).pipe(
  Layer.provide(UsersLive),
  Layer.provide(RpcSerialization.layerJson)
  // + a protocol layer, e.g. RpcServer.layerProtocolHttp({ path: "/rpc" })
)
```

`group.toLayer(handlers)` builds the handler layer; `group.of({...})` is an identity helper that gives the handler object its types. Handler keys are the rpc tags.

## Call from the Client

```typescript
import { Effect } from "effect"
import { RpcClient } from "effect/unstable/rpc"

const program = Effect.gen(function*() {
  const client = yield* RpcClient.make(UserRpcs)
  const user = yield* client.GetUser({ id: "1" }) // typed call by tag
  return user
})

// Wire the client transport: e.g.
// RpcClient.layerProtocolHttp({ url }) + RpcSerialization.layerJson + HttpClient.HttpClient
```

`RpcClient.make(group)` returns a client whose methods are keyed by rpc tag. Streaming rpcs return a `Stream`.

## Transports and Testing

- Serialization: `RpcSerialization.layerJson` / `layerNdjson` / `layerMsgPack` / `layerJsonRpc()`.
- Server protocols: `RpcServer.layerProtocolHttp`, `layerProtocolWebsocket`, `layerProtocolSocketServer`, `layerProtocolWorkerRunner`.
- Client protocols: `RpcClient.layerProtocolHttp`, `layerProtocolWorker({ size })` (a worker-thread pool — see `references/concurrency.md`).
- Testing without a transport: `RpcTest.makeClient(group)` runs the group in-memory.
