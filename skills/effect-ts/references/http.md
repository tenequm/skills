# HTTP Client and Server

Import paths differ between versions:

- **v3:** `@effect/platform` for client + API, `@effect/platform-node` for Node transports.
- **v4:** `effect/unstable/http` for the client and transport helpers, `effect/unstable/httpapi` for the schema-first API layer. `@effect/platform-node` still provides Node-specific `NodeHttpServer` / `NodeHttpClient`.

## HTTP Client (v3 — @effect/platform)

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

## HTTP Server (v3 — @effect/platform)

### Schema-First API Definition

```typescript
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "@effect/platform"

// Define endpoints (chained setters - v3 style)
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

### Implement Handlers (v3)

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

### Serve (v3)

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

### OpenAPI / Swagger (v3)

```typescript
import { HttpApiSwagger } from "@effect/platform"

const ServerLive = HttpApiBuilder.serve(HttpMiddleware.logger).pipe(
  Layer.provide(HttpApiSwagger.layer()), // adds /docs
  Layer.provide(HttpApiBuilder.api(MyApi)),
  // ...
)
```

## HTTP API Server (v4 — effect/unstable/httpapi)

v4 replaces the chained endpoint setters with an **object-option** form and moves all the HttpApi modules to `effect/unstable/httpapi`. Transport helpers live in `effect/unstable/http`. `HttpApiScalar` replaces `HttpApiSwagger` as the canonical docs UI (Swagger still exists).

### Define endpoints with object options

```typescript
import { Schema } from "effect"
import { HttpApi, HttpApiEndpoint, HttpApiGroup } from "effect/unstable/httpapi"

const User = Schema.Struct({
  id: Schema.Number,
  name: Schema.String,
  email: Schema.String
})

class UserNotFound extends Schema.TaggedErrorClass<UserNotFound>()("UserNotFound", {
  id: Schema.Number
}) {}

// Endpoints take (name, path, options) — no chained setters
const Users = HttpApiGroup.make("users")
  .add(
    HttpApiEndpoint.get("list", "/", {
      query: { search: Schema.optional(Schema.String) },
      success: Schema.Array(User)
    })
  )
  .add(
    HttpApiEndpoint.get("getById", "/:id", {
      params: { id: Schema.NumberFromString },
      success: User,
      error: UserNotFound
    })
  )
  .add(
    HttpApiEndpoint.post("create", "/", {
      payload: Schema.Struct({ name: Schema.String, email: Schema.String }),
      success: User
    })
  )

export const Api = HttpApi.make("api").add(Users)
```

### Implement handlers with `Effect.fn`

```typescript
import { Effect, Layer } from "effect"
import { HttpApiBuilder } from "effect/unstable/httpapi"

const UsersApiHandlers = HttpApiBuilder.group(
  Api,
  "users",
  Effect.fn(function*(handlers) {
    const db = yield* Database
    return handlers
      .handle("list", ({ urlParams }) => db.listUsers(urlParams.search))
      .handle("getById", ({ path }) => db.findUser(path.id))
      .handle("create", ({ payload }) => db.createUser(payload))
  })
)
```

### Serve + docs UI

```typescript
import { FetchHttpClient } from "effect/unstable/http"
import { HttpApiBuilder, HttpApiScalar } from "effect/unstable/httpapi"
import { NodeHttpServer, NodeRuntime } from "@effect/platform-node"
import { createServer } from "node:http"

const DocsRoute = HttpApiScalar.layer(Api, { path: "/docs" })

const ApiRoutes = HttpApiBuilder.layer(Api, {
  openapiPath: "/openapi.json"
}).pipe(Layer.provide([UsersApiHandlers]))

const ServerLive = Layer.mergeAll(ApiRoutes, DocsRoute).pipe(
  Layer.provide(NodeHttpServer.layer(createServer, { port: 3000 }))
)

NodeRuntime.runMain(Layer.launch(ServerLive))
```

### HttpApi schema errors default to defects (v4, since PR #2057)

Endpoint parse/schema failures no longer appear in the typed error channel by default — they surface as defects. If you want typed error responses (e.g. `400 Bad Request` with a structured body), transform the failure through `HttpApiSchema` helpers or add an explicit `error` schema on the endpoint:

```typescript
import { HttpApiSchema } from "effect/unstable/httpapi"

class BadInput extends Schema.TaggedErrorClass<BadInput>()("BadInput", {
  message: Schema.String
}) {}

HttpApiEndpoint.post("create", "/", {
  payload: CreateUserBody.pipe(HttpApiSchema.withBadRequest(BadInput)),
  success: User,
  error: BadInput
})
```

Without this transform, bad payloads cause a defect (500-style) instead of a typed error. This is a deliberate 2026-04-20 change (commit `8e04bfc9`).

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
