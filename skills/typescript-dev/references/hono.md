# Hono

Hono (Japanese for "flame") is a small, ultrafast web framework built entirely on Web
Standards (`Request`/`Response`/`fetch`). One codebase runs on Cloudflare Workers, Deno,
Bun, Node.js, Vercel, Netlify, AWS Lambda, Lambda@Edge, and Fastly Compute. Zero
dependencies; the `hono/tiny` preset is under 14kB. It is the backend/edge counterpart to
this stack's React frontend - its RPC client (`hc`) shares server types directly with
React, giving end-to-end type safety without code generation.

Version target: **hono@4.12.27** (Hono 4 is current; there is no v5). Node.js >= 18.14.1.
Adapters/middleware are versioned independently (`@hono/node-server@2`, `@hono/zod-validator`,
`@hono/zod-openapi@1`).

> **Keep Hono patched - the 4.12.x line has shipped frequent security fixes.** 4.12.27 alone
> fixes two SSR issues: `hono/jsx` stored context process-wide instead of per request, so a value
> read after an `await` in an async component could leak across concurrent requests
> (GHSA-hvrm-45r6-mjfj), and `hono/css` `cx()` marked its output as pre-escaped, allowing XSS via
> untrusted class names (GHSA-w62v-xxxg-mg59). Pin to the latest patch, not an older 4.12.x.

> **For anything this file does not cover, fetch Hono's own LLM-optimized docs** - they are
> the fastest authoritative source and are kept in sync with releases:
> - Full docs (one file, ~360KB): https://hono.dev/llms-full.txt
> - Core-only (smaller): https://hono.dev/llms-small.txt
> - Index of all doc pages: https://hono.dev/llms.txt
>
> This reference is the curated 80% you need most often; the `llms-*.txt` files are the
> exhaustive long tail (every middleware option, every runtime's getting-started, edge cases).

```sh
npm create hono@latest my-app          # scaffold (prompts for a template)
npm create hono@latest my-app -- --template cloudflare-workers --pm pnpm --install
npm i hono                              # add to an existing project
```

## Mental model

- A handler returns a `Response` (or `c.text()`/`c.json()`/etc., which build one). Exactly
  one handler runs per request.
- Middleware is `async (c, next) => { ... await next() ... }`. Code before `next()` runs on
  the way in; code after runs on the way out (onion model). Return a `Response` from
  middleware to short-circuit. Returning nothing (after `await next()`) continues the chain.
- Execution order = registration order. Register middleware (`app.use`) and fallbacks
  (`app.get('*', ...)`) relative to routes accordingly.
- Hono catches throws from handlers/middleware and routes them to `app.onError` (or a 500),
  so `next()` never throws - no try/catch needed around it.

```ts
import { Hono } from 'hono'

const app = new Hono()
app.get('/', (c) => c.text('Hono!'))

export default app // entry point for Cloudflare Workers, Bun, Deno
```

## Routing

```ts
app.get('/', (c) => c.text('GET /'))
app.post('/', (c) => c.text('POST /'))
app.put('/', (c) => c.text('PUT /'))
app.delete('/', (c) => c.text('DELETE /'))
app.all('/hello', (c) => c.text('Any method'))          // any HTTP method
app.on('PURGE', '/cache', (c) => c.text('PURGE'))       // custom method
app.on(['PUT', 'DELETE'], '/post', (c) => c.text('..')) // multiple methods
app.on('GET', ['/a', '/b'], (c) => c.text('..'))        // multiple paths

app.get('/wild/*/card', (c) => c.text('wildcard'))      // wildcard
app.get('/user/:name', (c) => c.text(c.req.param('name')))           // param
app.get('/api/animal/:type?', (c) => c.text('..'))                   // optional param
app.get('/post/:date{[0-9]+}/:title{[a-z]+}', (c) => c.text('..'))   // regexp param
app.get('/posts/:filename{.+\\.png}', (c) => c.text('..'))           // slashes via regexp

// Chained routes on one path
app
  .get('/endpoint', (c) => c.text('GET'))
  .post((c) => c.text('POST'))
  .delete((c) => c.text('DELETE'))
```

**Priority is registration order**, and the first matching handler wins and stops dispatch.
Put middleware and specific routes *above* wildcard fallbacks:

```ts
app.get('/book/a', (c) => c.text('a'))        // GET /book/a -> 'a'
app.get('/book/:slug', (c) => c.text('common')) // GET /book/b -> 'common'

app.use(logger())                              // middleware first
app.get('/foo', (c) => c.text('foo'))
app.get('*', (c) => c.text('fallback'))        // fallback last
```

**HEAD is automatic.** Hono converts HEAD to GET and strips the body before route matching,
so `app.head(...)` / `app.on('HEAD', ...)` handlers are never called. Add HEAD-specific
headers in middleware checking `c.req.method === 'HEAD'`.

### Grouping and sub-apps

`app.route(path, subApp)` mounts a sub-`Hono`. This is how you split a large app into files
*without* losing type inference (see RPC). `basePath()` prefixes all routes on an instance.

```ts
// books.ts
const books = new Hono()
books.get('/', (c) => c.text('List'))     // GET /books
books.get('/:id', (c) => c.text('One'))   // GET /books/:id
export default books

// index.ts
const app = new Hono()
app.route('/books', books)
const api = new Hono().basePath('/api')   // all routes under /api
```

Watch grouping order: `app.route('/two', two)` snapshots `two`'s routes *at call time*, so
register child routes onto `two` before mounting `two` onto `app`, or you get 404s.

## Context (`c`)

The `Context` is created per request and lives until the response is returned.

**Responders** (each returns a `Response`):

```ts
c.text('Hello', 201, { 'X-Msg': 'hi' })   // text/plain
c.json({ ok: true }, 200)                  // application/json
c.html('<h1>Hi</h1>')                      // text/html
c.body('raw', 201, { 'Content-Type': 'text/plain' })
c.redirect('/', 301)                       // default 302
c.notFound()                               // customizable via app.notFound()
c.status(201)                              // set status without returning yet
c.header('X-Message', 'hi')                // set a response header
c.res                                      // the in-progress Response (read/mutate in mw)
```

**Per-request state** - `c.set` / `c.get` / `c.var`. Type it via the `Variables` generic so
handlers see the right types:

```ts
type Variables = { user: { id: string } }
const app = new Hono<{ Variables: Variables }>()

app.use(async (c, next) => {
  c.set('user', { id: '123' })
  await next()
})
app.get('/', (c) => c.json(c.get('user')))   // or c.var.user
```

State lives only for the current request; it is never shared across requests.

**Bindings / env** - on Cloudflare Workers, KV/D1/R2/secrets are `c.env.*`. Type them with
the `Bindings` generic:

```ts
type Bindings = { MY_KV: KVNamespace; TOKEN: string }
const app = new Hono<{ Bindings: Bindings }>()

app.get('/', async (c) => {
  const v = await c.env.MY_KV.get('key')
  c.executionCtx.waitUntil(c.env.MY_KV.put('k', 'v')) // background work
  return c.text(v ?? '')
})
```

`c.render()` / `c.setRenderer()` set a layout in middleware then render content per route.
`c.error` holds a thrown error inside post-`next()` middleware.

## HonoRequest (`c.req`)

```ts
c.req.param('id')          // single path param (literal-typed from the route)
c.req.param()              // all path params
c.req.query('q')           // single query value
c.req.query()              // all query values
c.req.queries('tags')      // repeated query -> string[]
c.req.header('User-Agent') // single header (pass the exact name)
c.req.header()             // all headers, keys LOWERCASED

await c.req.json()         // parse application/json body
await c.req.text()         // text/plain body
await c.req.parseBody()    // multipart/form-data or x-www-form-urlencoded
await c.req.formData()     // FormData
await c.req.arrayBuffer()  // ArrayBuffer
await c.req.blob()         // Blob

c.req.valid('json')        // validated data (see Validation)
c.req.path                 // pathname
c.req.url                  // full URL string
c.req.method               // 'GET'
c.req.raw                  // the underlying Web `Request` (e.g. c.req.raw.cf on Workers)
await cloneRawRequest(c.req) // clone even after body was consumed by a validator
```

`parseBody()` notes: `body['foo[]']` is always `(string | File)[]`; `{ all: true }` collects
repeated same-name fields into arrays; `{ dot: true }` expands `obj.key` keys into nested
objects.

## Middleware

```ts
app.use(logger())              // all methods, all routes
app.use('/posts/*', cors())    // scoped by path
app.post('/posts/*', basicAuth({ username, password })) // method + path

// Inline custom middleware
app.use('/message/*', async (c, next) => {
  await next()
  c.header('x-message', 'after handler')
})
```

For reusable, type-safe middleware use `createMiddleware` from `hono/factory` - it preserves
`Context`/`next` types and lets you declare the `Variables` it sets:

```ts
import { createMiddleware } from 'hono/factory'

const auth = createMiddleware<{ Variables: { user: { id: string } } }>(
  async (c, next) => {
    c.set('user', { id: '123' })
    await next()
  }
)
```

**Type inference accumulates across chained `.use()`.** Each `.use()` returns a new instance
with merged `Variables`, so later handlers see every preceding middleware's variables without
declaring a combined `Env` upfront:

```ts
const app = new Hono()
  .use(authMiddleware)   // sets `user`
  .use(dbMiddleware)     // sets `db`
  .get('/', (c) => c.json({ user: c.var.user, hasDb: !!c.var.db }))
```

To configure middleware from `c.env` (Workers can't read env at module scope), wrap it:

```ts
app.use('*', async (c, next) => cors({ origin: c.env.CORS_ORIGIN })(c, next))
```

`ContextVariableMap` module augmentation adds variable types *globally* - convenient for
app-wide middleware, but it makes `c.get(...)` look typed even in handlers where the
middleware never ran, hiding `undefined` bugs. Prefer the `Variables` generic or chained
`.use()` typing.

### Built-in middleware (import from `hono/<name>`)

Auth & security: `basic-auth`, `bearer-auth`, `jwt`, `jwk`, `cors`, `csrf`, `secure-headers`,
`ip-restriction`. Body/response: `body-limit`, `compress`, `etag`, `cache`, `pretty-json`,
`trailing-slash`. Observability: `logger`, `timing`, `request-id`. Control flow: `combine`,
`method-override`, `context-storage`, `timeout`, `language`. Plus the `powered-by` and
`jsx-renderer` middleware.

```ts
import { cors } from 'hono/cors'
app.use('/api/*', cors({
  origin: ['https://example.com'],           // string | string[] | (origin, c) => string
  allowMethods: ['GET', 'POST', 'OPTIONS'],
  allowHeaders: ['X-Custom-Header'],
  exposeHeaders: ['Content-Length'],
  credentials: true,
  maxAge: 600,
}))
// `origin`/`allowMethods` accept callbacks for per-origin logic. CORS must run before routes.

import { jwt } from 'hono/jwt'
import type { JwtVariables } from 'hono/jwt'
const app = new Hono<{ Variables: JwtVariables }>()
app.use('/auth/*', jwt({ secret: 'very-secret', alg: 'HS256', issuer: 'me' }))
app.get('/auth/page', (c) => c.json(c.get('jwtPayload')))
// Reads `Authorization: Bearer <token>` by default; set `cookie` or `headerName` to change.
// `alg`: HS256/384/512, RS*, PS*, ES*, EdDSA. For c.env secrets, wrap like cors above.

import { secureHeaders } from 'hono/secure-headers'
import { csrf } from 'hono/csrf'
import { logger } from 'hono/logger'
app.use(secureHeaders(), csrf({ origin: 'https://example.com' }), logger())

import { basicAuth } from 'hono/basic-auth'
import { bearerAuth } from 'hono/bearer-auth'
app.use('/admin/*', basicAuth({ username: 'hono', password: 'secret' }))
app.use('/api/*', bearerAuth({ token: 'a-static-token' }))  // or { verifyToken: async (t, c) => boolean }
```

## Validation

Hono ships a thin `validator`; pair it with a schema library for real validation. The
validated value is read with `c.req.valid(target)`. Targets: `json`, `form`, `query`,
`header`, `param`, `cookie`.

```ts
import { validator } from 'hono/validator'
app.post('/posts', validator('form', (value, c) => {
  if (typeof value.body !== 'string') return c.text('Invalid!', 400)
  return { body: value.body }            // return = the validated value
}), (c) => c.json({ body: c.req.valid('form').body }))
```

Prefer the **Zod validator middleware** (Zod 4 supported):

```ts
import { z } from 'zod'
import { zValidator } from '@hono/zod-validator'

const app = new Hono().post(
  '/posts',
  zValidator('form', z.object({ title: z.string(), body: z.string() })),
  (c) => {
    const { title, body } = c.req.valid('form') // fully typed
    return c.json({ ok: true }, 201)
  }
)
```

Or `@hono/standard-validator`'s `sValidator` for any [Standard Schema](https://standardschema.dev)
library (Zod, Valibot, ArkType) with one adapter. Run multiple validators to check different
parts: `validator('param', ...)`, `validator('query', ...)`, `validator('json', ...)`.

Gotchas: validating `json`/`form` requires the matching `Content-Type` on the request or the
body parses to `{}` (set it in tests too). For `header`, use **lowercase** keys
(`value['idempotency-key']`).

## RPC - end-to-end type safety

The flagship feature: export the server app's type, and the `hc` client infers every input
and output - no codegen, no schema duplication. This is the natural way to connect a Hono
backend to the React frontend in this stack.

```ts
// server.ts
import { Hono } from 'hono'
import { z } from 'zod'
import { zValidator } from '@hono/zod-validator'

const route = new Hono()
  .post('/posts',
    zValidator('form', z.object({ title: z.string(), body: z.string() })),
    (c) => c.json({ ok: true, message: 'Created!' }, 201)
  )
  .get('/posts/:id',
    zValidator('query', z.object({ page: z.coerce.number().optional() })),
    (c) => c.json({ title: 'Night', body: 'sleep' }, 200)
  )

export type AppType = typeof route   // share the type with the client
export default route
```

```ts
// client.ts (runs in the React app)
import { hc } from 'hono/client'
import type { AppType } from './server'

const client = hc<AppType>('http://localhost:8787/')

const res = await client.posts.$post({ form: { title: 'Hi', body: '...' } })
if (res.ok) console.log((await res.json()).message)  // typed

// Path params via [':id']; params/query MUST be strings even if validated to numbers
const res2 = await client.posts[':id'].$get({ param: { id: '123' }, query: { page: '1' } })
```

Status codes flow through types: `c.json(data, 404)` makes `res.status === 404` narrow the
JSON type. Helpers: `InferRequestType<typeof client.x.$post>`, `InferResponseType<...>`,
`client.x.$url()` (needs absolute base URL), `client.x.$path()`, `parseResponse(...)` (parses
by Content-Type and throws on non-ok). Pass `{ init: { credentials: 'include' } }` or
`{ headers: { Authorization: '...' } }` to `hc` for cookies/auth.

**Do not** use `c.notFound()` on routes the client calls - its result can't be inferred. Use
`c.json({ error: '...' }, 404)` instead. Global `onError` responses aren't auto-inferred;
merge them with `ApplyGlobalResponse<typeof app, { 500: { json: { error: string } } }>`.

Larger apps: chain `.route()` and export the chained result's type:

```ts
const routes = app.route('/authors', authors).route('/books', books)
export type AppType = typeof routes
```

**Two RPC requirements that bite:**
1. `"strict": true` in `tsconfig.json` on *both* client and server (a monorepo split needs
   matching Hono versions, or you get "Type instantiation is excessively deep").
2. Type instantiation is heavy - many routes slow the IDE. The recommended fix is to compile
   the client type once so `tsserver` doesn't recompute it:

```ts
import { hc } from 'hono/client'
import { app } from './app'
export type Client = ReturnType<typeof hc<typeof app>>
export const hcWithType = (...args: Parameters<typeof hc>): Client =>
  hc<typeof app>(...args)   // use hcWithType instead of hc
```

## OpenAPI

`@hono/zod-openapi` extends Hono so the same Zod schema validates requests *and* generates an
OpenAPI 3 document. Serve interactive docs with Swagger UI (`@hono/swagger-ui`) or Scalar.

```ts
import { OpenAPIHono, createRoute, z } from '@hono/zod-openapi'

const UserSchema = z.object({
  id: z.string().openapi({ example: '123' }),
  name: z.string().openapi({ example: 'John' }),
}).openapi('User')   // registers as #/components/schemas/User

const route = createRoute({
  method: 'get',
  path: '/users/{id}',
  request: { params: z.object({ id: z.string().min(3) }) },
  responses: {
    200: { content: { 'application/json': { schema: UserSchema } }, description: 'A user' },
  },
})

const app = new OpenAPIHono()
app.openapi(route, (c) => {
  const { id } = c.req.valid('param')
  return c.json({ id, name: 'Ultra-man' }, 200)  // specify the status code, even 200
})
app.doc('/doc', { openapi: '3.0.0', info: { version: '1.0.0', title: 'My API' } })
```

`OpenAPIHono` is a drop-in `Hono` (supports `.route()`, RPC `typeof`, etc.). Same
Content-Type rule as validation: a JSON body needs `Content-Type: application/json` or
`c.req.valid('json')` is `{}`.

## Error handling

```ts
import { HTTPException } from 'hono/http-exception'

throw new HTTPException(401, { message: 'Unauthorized' })          // text response
throw new HTTPException(401, { res: customResponse })              // full Response control
throw new HTTPException(401, { message, cause })                   // attach arbitrary cause

app.onError((err, c) => {
  if (err instanceof HTTPException) return err.getResponse()
  console.error(err)
  return c.text('Internal Server Error', 500)
})
app.notFound((c) => c.text('Custom 404', 404))
```

`notFound`/`onError` fire only on the top-level app; route-level `onError` takes priority over
a parent's. `HTTPException.getResponse()` is not `Context`-aware - reapply context headers if
needed.

## Helpers (import from `hono/<name>`)

```ts
// hono/cookie
import { getCookie, setCookie, deleteCookie, getSignedCookie, setSignedCookie } from 'hono/cookie'
setCookie(c, 'name', 'value', { httpOnly: true, secure: true, sameSite: 'Lax', maxAge: 3600 })
const v = getCookie(c, 'name')
await setSignedCookie(c, 'name', 'value', secret)   // signed cookies are async (WebCrypto)

// hono/streaming - streaming & Server-Sent Events
import { stream, streamText, streamSSE } from 'hono/streaming'
app.get('/sse', (c) => streamSSE(c, async (stream) => {
  while (!stream.aborted) {
    await stream.writeSSE({ data: new Date().toISOString(), event: 'tick', id: String(id++) })
    await stream.sleep(1000)
  }
}))
// Note: errors thrown inside the stream callback do NOT trigger app.onError (response started).

// hono/jwt - mint/verify tokens yourself (the jwt() middleware only verifies incoming ones)
import { sign, verify, decode } from 'hono/jwt'
const token = await sign({ sub: 'user123', exp: Math.floor(Date.now() / 1000) + 300 }, secret)
const payload = await verify(token, secret, 'HS256')  // throws JwtTokenExpired/-Invalid/... on failure
const { header, payload: p } = decode(token)          // inspect WITHOUT verifying (debug only)
// verify() auto-checks exp/nbf/iat/iss when those claims are present. alg default HS256;
// supports HS*/RS*/PS*/ES*/EdDSA. Catch the typed errors (JwtTokenExpired, etc.) to branch.

// hono/context-storage - reach the Context from outside a handler (DB layer, logger, util)
import { contextStorage, getContext } from 'hono/context-storage'
app.use(contextStorage())                       // requires AsyncLocalStorage support
const currentUser = () => getContext<Env>().var.user  // works anywhere downstream
// Cloudflare Workers: needs the `nodejs_compat` (or `nodejs_als`) compatibility flag.
// `tryGetContext()` returns undefined instead of throwing when no context is active.
```

Other helpers: `hono/factory` (`createFactory`, `createMiddleware`, `createHandlers`,
`createApp`), `hono/jwt` (sign/verify/decode utilities), `hono/adapter` (`env(c)` for
runtime-agnostic env access), `hono/html`, `hono/css`, `hono/ssg`, `hono/proxy`,
`hono/conninfo`, `hono/accepts`, `hono/route`, `hono/testing` (`testClient`).

The Factory helper keeps `Env` types DRY and enables RoR-style "controllers" without losing
inference (the one sanctioned way - see Best practices):

```ts
import { createFactory } from 'hono/factory'

type Env = { Bindings: { MY_DB: D1Database }; Variables: { db: DrizzleD1Database } }
const factory = createFactory<Env>({
  initApp: (app) => app.use(async (c, next) => { c.set('db', drizzle(c.env.MY_DB)); await next() }),
})
const app = factory.createApp()          // Env applied once
const handlers = factory.createHandlers(logger(), (c) => c.json(c.var.db.select()))
app.get('/posts', ...handlers)
```

## JSX (server-side rendering)

`hono/jsx` renders HTML on the server (and works on the client). Configure
`tsconfig.json`: `"jsx": "react-jsx"`, `"jsxImportSource": "hono/jsx"`, and use a `.tsx`
file. Components are plain functions typed with `FC`. This is separate from the React
frontend - use it for server-rendered HTML responses, not as a React replacement.

```tsx
import type { FC } from 'hono/jsx'
const Layout: FC = (props) => <html><body>{props.children}</body></html>
app.get('/', (c) => c.html(<Layout><h1>Hello</h1></Layout>))
```

## Runtimes & deployment

Same app, different entry point. Pick the matching `create-hono` template.

**Cloudflare Workers** (`export default app`) - develop/deploy with Wrangler (`npm run dev`
serves on :8787, `npm run deploy`). Bindings (KV/D1/R2/secrets) come in via `c.env`; type
them with the `Bindings` generic and generate types with `wrangler types`.

**Node.js** - needs the adapter `@hono/node-server`:

```ts
import { serve } from '@hono/node-server'
import { serveStatic } from '@hono/node-server/serve-static'
const app = new Hono()
app.use('/static/*', serveStatic({ root: './' }))
serve({ fetch: app.fetch, port: 3000 }, (info) => console.log(info.port))
// graceful shutdown:
const server = serve(app)
process.on('SIGINT', () => { server.close(); process.exit(0) })
```

**Bun** - `export default { port: 3000, fetch: app.fetch }`. **Deno** -
`Deno.serve(app.fetch)`; import from `jsr:@hono/hono` and keep all hono imports on one
version. **Vercel / Netlify / AWS Lambda / Lambda@Edge / Fastly / Supabase Edge Functions /
Next.js** each have a template and a thin adapter; the handler logic is identical.

**Static files** - `serveStatic` is runtime-specific: `hono/cloudflare-workers`,
`@hono/node-server/serve-static`, `hono/bun`, or `hono/deno`. All take `{ root, path,
rewriteRequestPath, onFound }`; mount it on a wildcard route (`app.use('/static/*', serveStatic({ root: './' }))`).

## Realtime (WebSocket)

`upgradeWebSocket()` adds server-side WebSockets, imported from the runtime adapter
(`hono/cloudflare-workers`, `hono/deno`, `hono/bun`, or `@hono/node-server`). It returns a
handler that supplies `onOpen`/`onMessage`/`onClose`/`onError` callbacks. WS routes also work
with RPC: the client gets a typed `client.ws.$ws()`.

```ts
// Cloudflare Workers / Deno
import { upgradeWebSocket } from 'hono/cloudflare-workers'
const wsApp = app.get('/ws', upgradeWebSocket((c) => ({
  onMessage(event, ws) { ws.send(`echo: ${event.data}`) },
  onClose() { console.log('closed') },
})))
export type WsApp = typeof wsApp   // hc<WsApp>(...).ws.$ws() on the client

// Bun: export `{ fetch: app.fetch, websocket }` (import websocket from 'hono/bun')
// Node: install `ws`; pass a WebSocketServer to serve({ fetch, websocket: { server: wss } })
```

Gotcha: `onOpen` is not supported on Cloudflare Workers, and header-modifying middleware
(e.g. CORS) on a WS route throws "immutable headers" because `upgradeWebSocket` sets headers
internally - keep such middleware off WS routes.

## Testing

`app.request()` runs the app in-process against a Web `Request` - no server needed, works on
every runtime. Pass mock bindings as the 3rd arg.

```ts
import { describe, it, expect } from 'vitest'

describe('api', () => {
  it('GET /posts', async () => {
    const res = await app.request('/posts')
    expect(res.status).toBe(200)
  })

  it('POST /posts (json)', async () => {
    const res = await app.request('/posts', {
      method: 'POST',
      body: JSON.stringify({ message: 'hi' }),
      headers: { 'Content-Type': 'application/json' }, // required for json validators
    })
    expect(res.status).toBe(201)
  })

  it('uses mock env', async () => {
    const res = await app.request('/posts', {}, { DB: mockD1, API_HOST: 'example.com' })
  })
})
```

For a typed test client mirroring the RPC client, use `testClient(app)` from `hono/testing`.
On Cloudflare Workers, Cloudflare recommends `@cloudflare/vitest-pool-workers`. (This skill's
[vitest.md](vitest.md) covers the runner itself.)

## Best practices

1. **Write handlers inline after the path** - `app.get('/books/:id', (c) => ...)`. A separate
   `const handler = (c: Context) => ...` loses path-param inference. If you must extract,
   use `factory.createHandlers()`.
2. **Chain routes** (`.get(...).post(...)`) and export `typeof app` - that's what makes RPC
   types work. Split large apps with `.route()`, chaining the mounts.
3. **Let the compiler accumulate types** via chained `.use()` instead of hand-writing a
   combined `Env`. Reserve `ContextVariableMap` for truly app-wide middleware.
4. **Always specify the status code** in `c.json(data, status)` on routes the client or
   OpenAPI consumes - the status is part of the inferred/documented type.
5. **Avoid `c.notFound()`** on RPC routes; return `c.json({ error }, 404)`.
6. **Order matters**: middleware and specific routes before wildcards; CORS before routes.
7. **Set `Content-Type`** on `json`/`form` requests (including tests) or the body is `{}`.
8. **Keep Hono one version** across client/server, and compile the RPC client type
   (`hcWithType`) once the route count grows, to keep the IDE fast.
9. **Pick the right preset/router**: `hono` (default, `SmartRouter` = fast + full features),
   `hono/quick` (fast registration, good for per-request init like some edges), `hono/tiny`
   (smallest). Override with `new Hono({ router: new RegExpRouter() })` only if needed.

## Resources

**LLM-optimized docs (fetch these first when this file falls short):**
- Full docs, one file: https://hono.dev/llms-full.txt
- Core-only / smaller: https://hono.dev/llms-small.txt
- Doc-page index: https://hono.dev/llms.txt

**Official docs:**
- Home / getting started: https://hono.dev/docs/
- API reference - App: https://hono.dev/docs/api/hono - Context:
  https://hono.dev/docs/api/context - Request: https://hono.dev/docs/api/request - Routing:
  https://hono.dev/docs/api/routing
- Guides - RPC: https://hono.dev/docs/guides/rpc - Validation:
  https://hono.dev/docs/guides/validation - Middleware:
  https://hono.dev/docs/guides/middleware - Testing: https://hono.dev/docs/guides/testing -
  Best practices: https://hono.dev/docs/guides/best-practices - JSX:
  https://hono.dev/docs/guides/jsx
- Built-in middleware index: https://hono.dev/docs/middleware/builtin/basic-auth
- Helpers (cookie, jwt, streaming, factory, websocket, ...): https://hono.dev/docs/helpers/cookie
- Third-party middleware catalog: https://hono.dev/docs/middleware/third-party

**Repos & packages:**
- Core: https://github.com/honojs/hono
- Official middleware monorepo (47 packages incl. zod-validator, zod-openapi, swagger-ui,
  clerk-auth, oauth-providers, otel, mcp, trpc-server): https://github.com/honojs/middleware
- Examples (basic, blog, durable-objects, nextjs-stack, pages-stack, jsx-ssr):
  https://github.com/honojs/examples
- Node.js adapter: https://github.com/honojs/node-server - Scaffolder:
  https://github.com/honojs/create-hono

**Key ecosystem packages:** `@hono/zod-validator`, `@hono/standard-validator`,
`@hono/zod-openapi` + `@hono/swagger-ui` (OpenAPI), `@hono/node-server` (Node), Zod
(https://zod.dev), Valibot (https://valibot.dev), ArkType (https://arktype.io), Standard
Schema (https://standardschema.dev).
</content>
</invoke>
