# Server Functions

Server functions let you define server-only logic that can be called from anywhere in your application - route loaders, components, hooks, event handlers, or other server functions. They run on the server but can be invoked from client code seamlessly through an auto-generated RPC layer.

Official docs: https://tanstack.com/start/latest/docs/framework/react/server-functions

## createServerFn Basics

Create server functions with `createServerFn()`. The default HTTP method is GET; use POST for mutations.

```tsx
import { createServerFn } from '@tanstack/react-start'

// GET request (default) - for reading data
export const getServerTime = createServerFn().handler(async () => {
  return new Date().toISOString()
})

// POST request - for mutations
export const saveData = createServerFn({ method: 'POST' }).handler(
  async () => {
    await db.items.create({ title: 'New item' })
    return { success: true }
  },
)
```

Server functions accept a single `data` parameter. All parameters must be passed through this object since data crosses the network boundary.

```tsx
export const greetUser = createServerFn({ method: 'GET' })
  .handler(async ({ data }) => {
    return `Hello, ${data.name}!`
  })

// Calling the function
const greeting = await greetUser({ data: { name: 'John' } })
```

## Input Validation

Since server functions cross the network boundary, validating input ensures type safety and runtime correctness. TanStack Start supports inline validators and schema-library adapters.

### Inline Validator

The simplest approach - pass a function that validates and returns typed data:

```tsx
export const getUser = createServerFn({ method: 'GET' })
  .inputValidator((data: { id: string }) => data)
  .handler(async ({ data }) => {
    // data is typed as { id: string }
    return db.users.findById(data.id)
  })
```

### Zod Validator (Recommended)

The `@tanstack/zod-adapter` provides the `zodValidator` adapter for use with Zod schemas:

```tsx
import { createServerFn } from '@tanstack/react-start'
import { zodValidator } from '@tanstack/zod-adapter'
import { z } from 'zod'

const CreatePostSchema = z.object({
  title: z.string().min(1).max(200),
  body: z.string().min(1),
  tags: z.array(z.string()).optional(),
})

export const createPost = createServerFn({ method: 'POST' })
  .inputValidator(zodValidator(CreatePostSchema))
  .handler(async ({ data }) => {
    // data is fully typed and validated:
    // { title: string; body: string; tags?: string[] }
    return db.posts.create(data)
  })
```

You can also pass a Zod schema directly to `inputValidator` without the adapter:

```tsx
export const createUser = createServerFn({ method: 'POST' })
  .inputValidator(
    z.object({
      name: z.string().min(1),
      age: z.number().min(0),
    }),
  )
  .handler(async ({ data }) => {
    return `Created user: ${data.name}, age ${data.age}`
  })
```

### Other Validator Adapters

Valibot and ArkType adapters follow the same pattern:

```tsx
// Valibot - install @tanstack/valibot-adapter
import { valibotValidator } from '@tanstack/valibot-adapter'
import * as v from 'valibot'

export const updateProfile = createServerFn({ method: 'POST' })
  .inputValidator(valibotValidator(v.object({
    displayName: v.pipe(v.string(), v.minLength(1)),
    bio: v.optional(v.pipe(v.string(), v.maxLength(500))),
  })))
  .handler(async ({ data }) => db.profiles.update(data))

// ArkType - install @tanstack/arktype-adapter
import { arkTypeValidator } from '@tanstack/arktype-adapter'
import { type } from 'arktype'

export const searchItems = createServerFn({ method: 'GET' })
  .inputValidator(arkTypeValidator(type({ query: 'string', page: 'number > 0' })))
  .handler(async ({ data }) => db.items.search(data.query, data.page))
```

## Calling Patterns

Server functions can be called from four main contexts.

### From Route Loaders

The most common pattern for data fetching. Loaders are isomorphic (run on both server and client), so wrapping data access in a server function keeps secrets and database logic server-only.

```tsx
import { createFileRoute } from '@tanstack/react-router'
import { createServerFn } from '@tanstack/react-start'

const getPosts = createServerFn().handler(async () => {
  return db.posts.findMany({ orderBy: { createdAt: 'desc' } })
})

export const Route = createFileRoute('/posts')({
  loader: () => getPosts(),
  component: () => {
    const posts = Route.useLoaderData()
    return <ul>{posts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
  },
})
```

### From Components with useServerFn()

The `useServerFn()` hook wraps a server function for use in components, especially with mutations and event handlers:

```tsx
import { useServerFn } from '@tanstack/react-start'
import { useMutation } from '@tanstack/react-query'

const deletePost = createServerFn({ method: 'POST' })
  .inputValidator((data: { id: string }) => data)
  .handler(async ({ data }) => {
    await db.posts.delete({ where: { id: data.id } })
    return { success: true }
  })

function PostActions({ postId }: { postId: string }) {
  const deletePostFn = useServerFn(deletePost)

  const mutation = useMutation({
    mutationFn: () => deletePostFn({ data: { id: postId } }),
    onSuccess: () => {
      // handle success
    },
  })

  return (
    <button onClick={() => mutation.mutate()}>
      Delete Post
    </button>
  )
}
```

### From Other Server Functions

Server functions can compose by calling each other directly:

```tsx
const getCurrentUser = createServerFn().handler(async () => {
  const session = await getSession()
  if (!session) return null
  return db.users.findById(session.userId)
})

const getUserPosts = createServerFn().handler(async () => {
  const user = await getCurrentUser()
  if (!user) throw redirect({ to: '/login' })
  return db.posts.findMany({ where: { authorId: user.id } })
})
```

### From Event Handlers

Call server functions directly from click handlers, form submissions, and other events:

```tsx
function LikeButton({ postId }: { postId: string }) {
  const handleLike = async () => {
    await likePost({ data: { id: postId } })
  }

  return <button onClick={handleLike}>Like</button>
}
```

## Server Context

Access request/response utilities inside server function handlers via `@tanstack/react-start/server`.

```tsx
import { createServerFn } from '@tanstack/react-start'
import {
  getRequest,
  getRequestHeader,
  setResponseHeader,
  setResponseHeaders,
  setResponseStatus,
} from '@tanstack/react-start/server'

export const getCachedData = createServerFn({ method: 'GET' }).handler(
  async () => {
    // Access the full incoming Request object
    const request = getRequest()

    // Read a specific request header
    const authHeader = getRequestHeader('Authorization')

    // Set a single response header
    setResponseHeader('X-Request-Id', crypto.randomUUID())

    // Set multiple response headers via a Headers object
    setResponseHeaders(
      new Headers({
        'Cache-Control': 'public, max-age=300',
        'CDN-Cache-Control': 'max-age=3600, stale-while-revalidate=600',
      }),
    )

    // Set the HTTP status code
    setResponseStatus(200)

    return fetchExpensiveData()
  },
)
```

Available utilities:

| Utility | Description |
|---------|-------------|
| `getRequest()` | Access the full `Request` object |
| `getRequestHeader(name)` | Read a specific request header |
| `setResponseHeader(name, value)` | Set a single response header |
| `setResponseHeaders(headers)` | Set multiple response headers via `Headers` object |
| `setResponseStatus(code)` | Set the HTTP status code |

## Error Handling

Server functions support standard error throws, redirects, and not-found responses. Errors thrown inside handlers are serialized and sent to the client.

### Error Serialization

```tsx
export const riskyOperation = createServerFn({ method: 'POST' }).handler(
  async () => {
    const result = await externalApi.call()

    if (!result.ok) {
      throw new Error('External API failed')
    }

    return result.data
  },
)

// On the client, the error is deserialized
try {
  await riskyOperation()
} catch (error) {
  console.log(error.message) // "External API failed"
}
```

### Redirects

Use `redirect()` from `@tanstack/react-router` to redirect the user. Redirects thrown from server functions are handled automatically when called from route loaders or via `useServerFn()`.

```tsx
import { createServerFn } from '@tanstack/react-start'
import { redirect } from '@tanstack/react-router'

export const requireAuth = createServerFn().handler(async () => {
  const user = await getCurrentUser()

  if (!user) {
    throw redirect({ to: '/login' })
  }

  return user
})

// Use in a loader - redirect is handled automatically
export const Route = createFileRoute('/dashboard')({
  loader: () => requireAuth(),
})
```

### Not Found

Throw `notFound()` for missing resources. This triggers the nearest `notFoundComponent` in the route tree.

```tsx
import { createServerFn } from '@tanstack/react-start'
import { notFound } from '@tanstack/react-router'

export const getPost = createServerFn()
  .inputValidator((data: { id: string }) => data)
  .handler(async ({ data }) => {
    const post = await db.posts.findById(data.id)

    if (!post) {
      throw notFound()
    }

    return post
  })
```

## Streaming Responses

Server functions can stream typed data to the client using `ReadableStream` or async generators. This is particularly useful for AI/chat use cases.

Official docs: https://tanstack.com/start/latest/docs/framework/react/streaming-data-from-server-functions

### Typed ReadableStream

Return a `ReadableStream<T>` from a server function. The type parameter flows through to the client.

```tsx
import { createServerFn } from '@tanstack/react-start'

type ChatChunk = {
  choices: Array<{
    delta: { content?: string }
    index: number
    finish_reason: string | null
  }>
}

const streamChat = createServerFn({ method: 'POST' })
  .inputValidator((data: { prompt: string }) => data)
  .handler(async ({ data }) => {
    const aiResponse = await callAIProvider(data.prompt)

    const stream = new ReadableStream<ChatChunk>({
      async start(controller) {
        for await (const chunk of aiResponse) {
          controller.enqueue(chunk)
        }
        controller.close()
      },
    })

    return stream
  })
```

Consuming the stream on the client with `getReader()`:

```tsx
const response = await streamChat({ data: { prompt } })
if (!response) return

const reader = response.getReader()
let done = false
while (!done) {
  const { value, done: doneReading } = await reader.read()
  done = doneReading
  if (value) {
    // value is typed as ChatChunk
    const content = value.choices[0].delta.content
    if (content) setMessage((prev) => prev + content)
  }
}
```

### Async Generators

A cleaner alternative to `ReadableStream`. Use `async function*` as the handler:

```tsx
const streamMessages = createServerFn({ method: 'POST' })
  .inputValidator((data: { prompt: string }) => data)
  .handler(async function* ({ data }) {
    const messages = await generateAIResponse(data.prompt)

    for (const msg of messages) {
      await sleep(100) // simulate latency
      // Yielded values are typed and streamed to the client
      yield msg
    }
  })
```

The client code is significantly simpler with `for await...of`:

```tsx
const handleStream = useCallback(async () => {
  setMessages('')
  for await (const msg of await streamMessages({ data: { prompt } })) {
    const chunk = msg.choices[0].delta.content
    if (chunk) {
      setMessages((prev) => prev + chunk)
    }
  }
}, [prompt])
```

## FormData Handling

Server functions support native `FormData` as input. Validate and extract fields in the `inputValidator`:

```tsx
export const submitContactForm = createServerFn({ method: 'POST' })
  .inputValidator((data) => {
    if (!(data instanceof FormData)) throw new Error('Expected FormData')
    const name = data.get('name')?.toString()
    const email = data.get('email')?.toString()
    const message = data.get('message')?.toString()
    if (!name || !email || !message) throw new Error('All fields are required')
    return { name, email, message }
  })
  .handler(async ({ data }) => {
    await sendEmail({ to: 'support@example.com', subject: `Contact from ${data.name}`, body: data.message })
    return { success: true }
  })
```

Call from a component with `useServerFn`:

```tsx
function ContactForm() {
  const submitFn = useServerFn(submitContactForm)
  return (
    <form onSubmit={async (e) => {
      e.preventDefault()
      await submitFn({ data: new FormData(e.currentTarget) })
    }}>
      <input name="name" required />
      <input name="email" type="email" required />
      <textarea name="message" required />
      <button type="submit">Send</button>
    </form>
  )
}
```

## Execution Model

Understanding how server functions execute across environments is critical for building secure TanStack Start applications.

Official docs: https://tanstack.com/start/latest/docs/framework/react/execution-model

### Isomorphic by Default

All code in TanStack Start is isomorphic by default - included in both server and client bundles unless explicitly constrained. This includes route loaders, which execute on server during SSR AND on client during client-side navigation. Always wrap server-only logic (database access, secrets) in `createServerFn()`.

### Build-Time RPC Replacement

The build process replaces server function implementations with RPC stubs in client bundles:

1. You write a server function with `createServerFn().handler()`
2. The compiler extracts the handler to a server-only module
3. The client bundle gets a stub that makes a `fetch` call to the server
4. The server locates the handler using a generated, stable function ID (SHA256 hash by default)

```tsx
// What you write:
import { getUsers } from './db/queries.server'
export const fetchUsers = createServerFn().handler(async () => getUsers())

// What the client build produces (conceptually):
export const fetchUsers = createServerFn({ method: 'GET' }).handler(
  createClientRpc('sha256:abc123...')
)
// The server-only import (getUsers) is removed entirely
```

Server functions can be safely statically imported anywhere, including client components. **Avoid dynamic imports** - the build process cannot replace them with RPC stubs.

You can customize function ID generation via `serverFns.generateFunctionId` in the TanStack Start Vite plugin config (experimental).

## Environment Functions

Environment functions control function execution based on the runtime environment. They complement server functions for cases where you need different implementations per environment rather than RPC calls.

Official docs: https://tanstack.com/start/latest/docs/framework/react/environment-functions

```tsx
import {
  createIsomorphicFn,
  createServerOnlyFn,
  createClientOnlyFn,
} from '@tanstack/react-start'

// Different implementations per environment
const getDeviceInfo = createIsomorphicFn()
  .server(() => ({ type: 'server', platform: process.platform }))
  .client(() => ({ type: 'client', userAgent: navigator.userAgent }))

// Server-only - throws on client
const getDbUrl = createServerOnlyFn(() => process.env.DATABASE_URL)

// Client-only - throws on server
const saveToStorage = createClientOnlyFn((key: string, value: string) => {
  localStorage.setItem(key, value)
})
```

For components that need browser APIs, use `ClientOnly` and `useHydrated` from `@tanstack/react-router`:

```tsx
import { ClientOnly, useHydrated } from '@tanstack/react-router'

function Analytics() {
  return (
    <ClientOnly fallback={null}>
      <GoogleAnalyticsScript />
    </ClientOnly>
  )
}

function TimeZoneDisplay() {
  const hydrated = useHydrated()
  // hydrated: false during SSR and first client render, true after hydration
  const timeZone = hydrated
    ? Intl.DateTimeFormat().resolvedOptions().timeZone
    : 'UTC'
  return <div>Your timezone: {timeZone}</div>
}
```

All environment functions are tree-shaken per bundle: `.client()` code is excluded from server bundles and vice versa. `createClientOnlyFn` and `createServerOnlyFn` are replaced with error-throwing stubs in the wrong environment.

## Import Protection (Experimental)

Import protection prevents server-only code from leaking into client bundles and vice versa. It runs as a Vite plugin, enabled by default. In dev mode violations produce a mock (warning); in production builds they fail with an error.

Official docs: https://tanstack.com/start/latest/docs/framework/react/import-protection

**File conventions** - use `.server.*` / `.client.*` suffixes to restrict files:

```
src/utils/
  auth.server.ts       # Denied in client bundle
  analytics.client.ts  # Denied in server bundle
  helpers.ts           # Available in both bundles
```

**File markers** - alternatively, use side-effect imports for files that do not follow the naming convention:

```tsx
// src/lib/secrets.ts
import '@tanstack/react-start/server-only'
export const API_KEY = process.env.API_KEY
```

**Custom deny rules** - block specific packages or directories:

```ts
// vite.config.ts
tanstackStart({
  importProtection: {
    client: {
      specifiers: ['@prisma/client', 'bcrypt'],
      files: ['**/db/**'],
    },
    server: {
      specifiers: ['localforage'],
    },
  },
})
```

## Static Server Functions (Experimental)

Static server functions execute at build time and cache results as static JSON files when using prerendering/static generation. Apply `staticFunctionMiddleware` (must be the final middleware) from `@tanstack/start-static-server-functions`:

```tsx
import { createServerFn } from '@tanstack/react-start'
import { staticFunctionMiddleware } from '@tanstack/start-static-server-functions'

const getStaticConfig = createServerFn({ method: 'GET' })
  .middleware([staticFunctionMiddleware])
  .handler(async () => ({ siteName: 'My App', version: '1.0.0' }))
```

At build time the result is cached as a static JSON file. On initial load the data is embedded in prerendered HTML and hydrated. On subsequent client navigations the static JSON file is fetched directly. See: https://tanstack.com/start/latest/docs/framework/react/static-server-functions

## File Organization

For larger applications, separate server function definitions from server-only helpers and shared schemas.

```
src/utils/
  users.functions.ts   # Server function wrappers (createServerFn) - safe to import anywhere
  users.server.ts      # Server-only helpers (DB queries, internal logic) - server-only
  schemas.ts           # Shared validation schemas (Zod/Valibot) - client-safe
```

### Example Structure

```tsx
// schemas.ts - Shared validation (safe for both environments)
import { z } from 'zod'

export const CreateUserSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
})
```

```tsx
// users.server.ts - Server-only database logic
import { db } from '~/db'

export async function findUserById(id: string) {
  return db.query.users.findFirst({ where: eq(users.id, id) })
}
```

```tsx
// users.functions.ts - Server function wrappers (safe to import anywhere)
import { createServerFn } from '@tanstack/react-start'
import { zodValidator } from '@tanstack/zod-adapter'
import { findUserById } from './users.server'
import { CreateUserSchema } from './schemas'

export const getUser = createServerFn({ method: 'GET' })
  .inputValidator((data: { id: string }) => data)
  .handler(async ({ data }) => findUserById(data.id))

export const createUser = createServerFn({ method: 'POST' })
  .inputValidator(zodValidator(CreateUserSchema))
  .handler(async ({ data }) => db.insert(users).values(data).returning())
```

## Middleware Integration

Server functions support composable middleware for authentication, logging, and shared logic. Use `createMiddleware({ type: 'function' })` for server-function-specific middleware.

```tsx
import { createMiddleware, createServerFn } from '@tanstack/react-start'

const authMiddleware = createMiddleware({ type: 'function' }).server(
  async ({ next }) => {
    const user = await getCurrentUser()
    if (!user) throw redirect({ to: '/login' })
    return next({ context: { user } })
  },
)

// Server function using middleware - context.user is typed
export const getUserSettings = createServerFn()
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    return db.settings.findByUserId(context.user.id)
  })
```

Middleware can also validate input via `inputValidator` and run client-side logic via `.client()`. Apply middleware globally to all server functions through `src/start.ts`:

```tsx
// src/start.ts
import { createStart } from '@tanstack/react-start'
import { loggingMiddleware } from './middleware'

export const startInstance = createStart(() => ({
  functionMiddleware: [loggingMiddleware],
}))
```

See the dedicated Middleware guide for full details: https://tanstack.com/start/latest/docs/framework/react/middleware

## Best Practices

1. **Always use server functions for sensitive operations.** Route loaders are isomorphic (run on both server and client). Never access secrets, database connections, or server-only APIs directly in loaders - wrap them in `createServerFn()`.

2. **Validate all input with schemas.** Server functions cross a network boundary. Use Zod, Valibot, or ArkType to validate data at runtime, not just TypeScript types.

3. **Use POST for mutations, GET for reads.** GET server functions can be cached and preloaded by the router. POST is appropriate for any operation that modifies state.

4. **Separate concerns with file conventions.** Use `.functions.ts` for `createServerFn` wrappers, `.server.ts` for database queries and internal helpers, and plain `.ts` for shared types and schemas.

5. **Prefer async generators for streaming.** They produce cleaner code on both server and client compared to manual `ReadableStream` construction. Use `for await...of` on the client side.

6. **Compose with middleware for cross-cutting concerns.** Authentication, authorization, logging, and input validation are ideal candidates for middleware rather than repeated logic inside each handler.

7. **Always use static imports for server functions.** The build process cannot replace dynamic imports with RPC stubs, which leads to bundler issues.

8. **Use import protection file conventions.** Name server-only files with `.server.ts` and client-only files with `.client.ts` to get automatic build-time protection against cross-environment leaks.
