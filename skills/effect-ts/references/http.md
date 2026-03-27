# HTTP Client and Server

## HTTP Client (@effect/platform)

### Making Requests

```typescript
import { HttpClient, HttpClientRequest, HttpClientResponse } from "@effect/platform"

const program = Effect.gen(function*() {
  const client = yield* HttpClient.HttpClient

  // GET request
  const response = yield* client.execute(
    HttpClientRequest.get("https://api.example.com/users")
  )

  // POST with JSON body
  const response = yield* client.execute(
    HttpClientRequest.post("https://api.example.com/users").pipe(
      HttpClientRequest.jsonBody({ name: "Alice", age: 30 })
    )
  )

  // With headers
  const response = yield* client.execute(
    HttpClientRequest.get("https://api.example.com/data").pipe(
      HttpClientRequest.setHeader("Authorization", `Bearer ${token}`)
    )
  )
})
```

### Response Handling

```typescript
// Filter by status (fail on non-2xx)
const okResponse = yield* client.execute(request).pipe(
  HttpClientResponse.filterStatusOk
)

// Parse JSON body with Schema validation
const users = yield* client.execute(request).pipe(
  HttpClientResponse.filterStatusOk,
  HttpClientResponse.schemaBodyJson(Schema.Array(User))
)

// Get raw text
const text = yield* response.text

// Get raw JSON
const json = yield* response.json
```

### Retry with HttpClient

```typescript
const resilientClient = client.pipe(
  HttpClient.retryTransient({
    schedule: Schedule.exponential("200 millis").pipe(
      Schedule.compose(Schedule.recurs(3))
    )
  })
)
```

### Platform Layer

Provide the HTTP client layer for your runtime:

```typescript
import { NodeHttpClient } from "@effect/platform-node"

const main = program.pipe(
  Effect.provide(NodeHttpClient.layer)
)
```

## HTTP Server (@effect/platform)

### Schema-First API Definition

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"
// v4: from "effect/unstable/httpapi"

// Define endpoints
const getUser = HttpApiEndpoint.get("getUser", "/users/:id").pipe(
  HttpApiEndpoint.setPath(Schema.Struct({ id: Schema.String })),
  HttpApiEndpoint.setSuccess(User)
)

const createUser = HttpApiEndpoint.post("createUser", "/users").pipe(
  HttpApiEndpoint.setPayload(CreateUserBody),
  HttpApiEndpoint.setSuccess(User)
)

// Group endpoints
const UsersApi = HttpApiGroup.make("users").pipe(
  HttpApiGroup.add(getUser),
  HttpApiGroup.add(createUser)
)

// Build the API
const MyApi = HttpApi.make("my-api").pipe(
  HttpApi.addGroup(UsersApi)
)
```

### Implement Handlers

```typescript
import { HttpApiBuilder } from "@effect/platform"

const UsersLive = HttpApiBuilder.group(MyApi, "users", (handlers) =>
  handlers.pipe(
    HttpApiBuilder.handle("getUser", ({ path }) =>
      Effect.gen(function*() {
        const db = yield* Database
        return yield* db.findUser(path.id)
      })
    ),
    HttpApiBuilder.handle("createUser", ({ payload }) =>
      Effect.gen(function*() {
        const db = yield* Database
        return yield* db.createUser(payload)
      })
    )
  )
)
```

### Serve

```typescript
import { HttpApiBuilder, HttpMiddleware } from "@effect/platform"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { createServer } from "node:http"

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiBuilder.api(MyApi)),
  Layer.provide(UsersLive),
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

NodeRuntime.runMain(Layer.launch(ServerLive))
```

### OpenAPI / Swagger

```typescript
import { HttpApiSwagger } from "@effect/platform"

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiSwagger.layer()), // adds /docs
  Layer.provide(HttpApiBuilder.api(MyApi)),
  // ...
)
```

## Integrating Effect with Hono

Use `ManagedRuntime` to bridge Effect into Hono routes:

```typescript
import { Hono } from "hono"
import { ManagedRuntime } from "effect"

// Build runtime once from your app layer
const runtime = ManagedRuntime.make(
  Layer.mergeAll(DatabaseLive, CacheLive, LoggerLive)
)

const app = new Hono()

app.get("/users/:id", async (c) => {
  const result = await runtime.runPromise(
    Effect.gen(function*() {
      const db = yield* Database
      return yield* db.findUser(c.req.param("id"))
    })
  )
  return c.json(result)
})
```

Layers are created once and reused across all requests. Do NOT call `Layer.provide` + `Effect.runPromise` per request - that rebuilds layers every time.
