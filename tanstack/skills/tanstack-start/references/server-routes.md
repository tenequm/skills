# Server Routes (API Routes)

Server routes are server-side HTTP endpoints defined alongside your application routes using the same file-based routing conventions as TanStack Router. They handle raw HTTP requests, form submissions, webhooks, and authentication callbacks.

Official docs: https://tanstack.com/start/latest/docs/framework/react/server-routes

## Defining Server Routes

Add a `server` property to `createFileRoute()` with a `handlers` object mapping HTTP methods to handler functions. Each handler must return a standard Web `Response`.

```ts
// src/routes/api/health.ts
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/api/health')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        return Response.json({ status: 'ok', timestamp: Date.now() })
      },
    },
  },
})
```

Supported HTTP methods: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`.

## Co-location with App Routes

Server routes and UI routes can share the same file. The `server` property defines API handlers while `component` and other options define the page.

```tsx
// src/routes/contact.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/contact')({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const body = await request.json()
        await sendContactEmail(body.email, body.message)
        return Response.json({ success: true })
      },
    },
  },
  component: () => {
    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      const form = new FormData(e.currentTarget)
      await fetch('/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.get('email'), message: form.get('message') }),
      })
    }
    return (
      <form onSubmit={handleSubmit}>
        <input name="email" type="email" required />
        <textarea name="message" required />
        <button type="submit">Send</button>
      </form>
    )
  },
})
```

## File Routing Conventions

Server routes follow the same file-based routing as TanStack Router. Files with a `server` property in `createFileRoute` become API endpoints.

| File path | API endpoint |
|-----------|-------------|
| `routes/api/users.ts` | `/api/users` |
| `routes/api/users/$id.ts` | `/api/users/$id` |
| `routes/api/users.$id.posts.ts` | `/api/users/$id/posts` |
| `routes/api/file/$.ts` | `/api/file/$` (wildcard) |
| `routes/sitemap[.]xml.ts` | `/sitemap.xml` (escaped dot) |

Each route path must resolve to a single handler file. Flat file names and nested directories can be mixed freely - `routes/api/users.$id.ts` and `routes/api/users/$id.ts` produce the same endpoint.

## Handler Context

Every handler receives an object with three properties:

- **`request`** - Standard Web `Request` object. Use `request.json()`, `request.text()`, `request.formData()`, `request.headers`, `request.url`.
- **`params`** - Typed path parameters. For `/api/users/$id/posts/$postId`, params is `{ id: string, postId: string }`.
- **`context`** - Data passed from middleware via `next({ context: { ... } })`. Empty by default.

```ts
export const Route = createFileRoute('/api/users/$id')({
  server: {
    handlers: {
      GET: async ({ request, params, context }) => {
        return Response.json({ userId: params.id, url: request.url })
      },
    },
  },
})
```

## Handler Definition

### Simple Handlers Object

Pass handler functions directly for straightforward use cases:

```ts
export const Route = createFileRoute('/api/posts')({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const url = new URL(request.url)
        const page = Number(url.searchParams.get('page') || '1')
        return Response.json(await fetchPosts(page))
      },
      POST: async ({ request }) => {
        const body = await request.json()
        return Response.json(await createPost(body), { status: 201 })
      },
    },
  },
})
```

### createHandlers for Per-Handler Middleware

Use `createHandlers` to attach middleware to individual HTTP methods:

```ts
export const Route = createFileRoute('/api/admin/settings')({
  server: {
    handlers: ({ createHandlers }) =>
      createHandlers({
        GET: {
          middleware: [adminMiddleware],
          handler: async ({ context }) => Response.json(context.settings),
        },
        PUT: {
          middleware: [adminMiddleware, validationMiddleware],
          handler: async ({ request }) => {
            const body = await request.json()
            return Response.json(await updateSettings(body))
          },
        },
      }),
  },
})
```

### Route-Level and Combined Middleware

Apply middleware to all handlers with the top-level `middleware` property. Route-level middleware runs first, then handler-specific middleware:

```ts
export const Route = createFileRoute('/api/documents')({
  server: {
    middleware: [authMiddleware], // Runs for every handler
    handlers: ({ createHandlers }) =>
      createHandlers({
        GET: async ({ context }) => {
          return Response.json(await getDocuments(context.user.id))
        },
        POST: {
          middleware: [rateLimitMiddleware], // Runs after authMiddleware, POST only
          handler: async ({ request, context }) => {
            const body = await request.json()
            return Response.json(await createDocument(context.user.id, body), { status: 201 })
          },
        },
      }),
  },
})
```

## Dynamic Path Params

### Single and Multiple Parameters

```ts
// src/routes/api/users/$userId/posts/$postId.ts
export const Route = createFileRoute('/api/users/$userId/posts/$postId')({
  server: {
    handlers: {
      GET: async ({ params }) => {
        const { userId, postId } = params
        const post = await findPost(userId, postId)
        if (!post) return Response.json({ error: 'Not found' }, { status: 404 })
        return Response.json(post)
      },
    },
  },
})
```

### Wildcard (Splat) Parameter

A trailing `$` with no name captures the remaining path as `_splat`:

```ts
// src/routes/api/files/$.ts
export const Route = createFileRoute('/api/files/$')({
  server: {
    handlers: {
      GET: async ({ params }) => {
        const filePath = params._splat // e.g. "documents/report.pdf"
        const file = await readFile(filePath)
        return new Response(file, {
          headers: { 'Content-Type': getMimeType(filePath) },
        })
      },
    },
  },
})
// GET /api/files/documents/report.pdf -> _splat = "documents/report.pdf"
```

## Pathless Layout Routes

Pathless layout routes (prefixed with `_`) group server routes under shared middleware without adding a URL segment:

```
src/routes/api/
  _authenticated.ts          # Middleware-only, no path segment
  _authenticated/
    users.ts                 # /api/users (requires auth)
    posts.ts                 # /api/posts (requires auth)
  public/
    health.ts                # /api/public/health (no auth)
```

```ts
// src/routes/api/_authenticated.ts
import { createFileRoute } from '@tanstack/react-router'
import { authMiddleware } from '~/middleware/auth'

export const Route = createFileRoute('/api/_authenticated')({
  server: { middleware: [authMiddleware] },
})
```

All routes inside `_authenticated/` inherit the auth middleware. Break-out routes can escape parent middleware.

## Response Handling

Handlers return standard Web `Response` objects:

```ts
// JSON (preferred) - sets Content-Type automatically
return Response.json({ message: 'Hello' })
return Response.json(created, { status: 201 })
return Response.json({ error: 'Not found' }, { status: 404 })

// Plain text
return new Response('Hello, World!', { headers: { 'Content-Type': 'text/plain' } })

// Custom headers
return new Response(JSON.stringify(data), {
  headers: { 'Content-Type': 'application/json', 'Cache-Control': 'public, max-age=3600' },
})

// Redirect
return new Response(null, { status: 302, headers: { Location: '/new-location' } })
```

### Streaming Response

```ts
export const Route = createFileRoute('/api/events')({
  server: {
    handlers: {
      GET: async () => {
        const stream = new ReadableStream({
          async start(controller) {
            const encoder = new TextEncoder()
            for (let i = 0; i < 5; i++) {
              await new Promise((resolve) => setTimeout(resolve, 1000))
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ count: i })}\n\n`))
            }
            controller.close()
          },
        })
        return new Response(stream, {
          headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
        })
      },
    },
  },
})
```

## Database Integration

Server routes run entirely on the server, giving direct access to databases and environment variables.

### With Neon (Serverless PostgreSQL)

```ts
import { createFileRoute } from '@tanstack/react-router'
import { neon } from '@neondatabase/serverless'

const sql = neon(process.env.DATABASE_URL!)

export const Route = createFileRoute('/api/products')({
  server: {
    handlers: {
      GET: async () => {
        const products = await sql`SELECT id, name, price FROM products WHERE active = true LIMIT 50`
        return Response.json(products)
      },
      POST: async ({ request }) => {
        const { name, price } = await request.json()
        const [product] = await sql`INSERT INTO products (name, price) VALUES (${name}, ${price}) RETURNING *`
        return Response.json(product, { status: 201 })
      },
    },
  },
})
```

### With Prisma / Drizzle

The same pattern works with any ORM - import your client and call it from handlers:

```ts
// Prisma
const users = await prisma.user.findMany({ skip: (page - 1) * 20, take: 20 })

// Drizzle
const allPosts = await db.select().from(posts).orderBy(desc(posts.createdAt)).limit(25)
```

## Authentication in Server Routes

### Auth Middleware

```ts
// src/middleware/auth.ts
import { createMiddleware } from '@tanstack/react-start'
import { useAppSession } from '~/utils/session'

export const authMiddleware = createMiddleware().server(async ({ next }) => {
  const session = await useAppSession()
  if (!session.data.userId) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 })
  }
  const user = await getUserById(session.data.userId)
  if (!user) return Response.json({ error: 'User not found' }, { status: 401 })
  return next({ context: { user } })
})
```

### Role-Based Authorization

```ts
// src/middleware/roles.ts
import { createMiddleware } from '@tanstack/react-start'

export function requireRole(role: string) {
  return createMiddleware().server(async ({ next, context }) => {
    if (context.user?.role !== role) {
      return Response.json({ error: 'Forbidden' }, { status: 403 })
    }
    return next()
  })
}
```

```ts
export const Route = createFileRoute('/api/admin/users')({
  server: {
    middleware: [authMiddleware],
    handlers: ({ createHandlers }) =>
      createHandlers({
        GET: {
          middleware: [requireRole('admin')],
          handler: async () => Response.json(await getAllUsers()),
        },
      }),
  },
})
```

## Complete CRUD Example

```ts
// src/routes/api/tasks.ts
import { createFileRoute } from '@tanstack/react-router'
import { authMiddleware } from '~/middleware/auth'
import { prisma } from '~/lib/prisma'

export const Route = createFileRoute('/api/tasks')({
  server: {
    middleware: [authMiddleware],
    handlers: {
      GET: async ({ request, context }) => {
        const url = new URL(request.url)
        const status = url.searchParams.get('status')
        const where: Record<string, unknown> = { userId: context.user.id }
        if (status) where.status = status
        const tasks = await prisma.task.findMany({ where, orderBy: { createdAt: 'desc' } })
        return Response.json(tasks)
      },
      POST: async ({ request, context }) => {
        const body = await request.json()
        if (!body.title || typeof body.title !== 'string') {
          return Response.json({ error: 'Title is required' }, { status: 400 })
        }
        const task = await prisma.task.create({
          data: { title: body.title, description: body.description || null, status: 'pending', userId: context.user.id },
        })
        return Response.json(task, { status: 201 })
      },
    },
  },
})
```

```ts
// src/routes/api/tasks/$taskId.ts
import { createFileRoute } from '@tanstack/react-router'
import { authMiddleware } from '~/middleware/auth'
import { prisma } from '~/lib/prisma'

export const Route = createFileRoute('/api/tasks/$taskId')({
  server: {
    middleware: [authMiddleware],
    handlers: {
      GET: async ({ params, context }) => {
        const task = await prisma.task.findFirst({ where: { id: params.taskId, userId: context.user.id } })
        if (!task) return Response.json({ error: 'Not found' }, { status: 404 })
        return Response.json(task)
      },
      PUT: async ({ request, params, context }) => {
        const existing = await prisma.task.findFirst({ where: { id: params.taskId, userId: context.user.id } })
        if (!existing) return Response.json({ error: 'Not found' }, { status: 404 })
        const body = await request.json()
        const updated = await prisma.task.update({
          where: { id: params.taskId },
          data: { title: body.title ?? existing.title, description: body.description ?? existing.description, status: body.status ?? existing.status },
        })
        return Response.json(updated)
      },
      DELETE: async ({ params, context }) => {
        const existing = await prisma.task.findFirst({ where: { id: params.taskId, userId: context.user.id } })
        if (!existing) return Response.json({ error: 'Not found' }, { status: 404 })
        await prisma.task.delete({ where: { id: params.taskId } })
        return Response.json({ deleted: true })
      },
    },
  },
})
```

## Head Management

Routes define a `head()` function for SEO metadata. Use `HeadContent` and `Scripts` in the root layout to render tags into the document.

### Root Layout Setup

```tsx
// src/routes/__root.tsx
import { HeadContent, Outlet, Scripts, createRootRoute } from '@tanstack/react-router'

export const Route = createRootRoute({
  head: () => ({
    meta: [{ charSet: 'utf-8' }, { name: 'viewport', content: 'width=device-width, initial-scale=1' }],
    links: [{ rel: 'icon', href: '/favicon.ico' }],
  }),
  component: () => (
    <html>
      <head><HeadContent /></head>
      <body><Outlet /><Scripts /></body>
    </html>
  ),
})
```

### Dynamic Meta Tags

```tsx
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params }) => ({ post: await fetchPost(params.postId) }),
  head: ({ loaderData }) => ({
    meta: [
      { title: loaderData.post.title },
      { name: 'description', content: loaderData.post.excerpt },
      { property: 'og:title', content: loaderData.post.title },
      { property: 'og:image', content: loaderData.post.coverImage },
      { name: 'twitter:card', content: 'summary_large_image' },
    ],
    scripts: [{
      type: 'application/ld+json',
      children: JSON.stringify({
        '@context': 'https://schema.org', '@type': 'Article',
        headline: loaderData.post.title, image: loaderData.post.coverImage,
        datePublished: loaderData.post.publishedAt,
      }),
    }],
  }),
  component: PostPage,
})
```

## Global Middleware via start.ts

Register middleware that runs on every server request (SSR, server functions, and server routes):

```ts
// src/start.ts
import { createStart, createMiddleware } from '@tanstack/react-start'

const loggingMiddleware = createMiddleware().server(async ({ next, request }) => {
  const start = Date.now()
  const result = await next()
  console.log(`${request.method} ${request.url} - ${Date.now() - start}ms`)
  return result
})

export const startInstance = createStart(() => ({
  requestMiddleware: [loggingMiddleware],
}))
```

## Best Practices

1. **Use `Response.json()` over manual serialization** - Sets Content-Type automatically and avoids forgetting to stringify.

2. **Validate request bodies before processing** - Check required fields and types before database calls. Return 400 with descriptive error messages.

3. **Scope server routes under `/api` by convention** - Placing API routes under `src/routes/api/` makes the boundary between UI and API endpoints clear.

4. **Use middleware for cross-cutting concerns** - Extract auth, logging, rate limiting into reusable middleware rather than duplicating in each handler.

5. **Return appropriate HTTP status codes** - 201 for creation, 404 for not found, 401 for unauthenticated, 403 for forbidden, 400 for bad input.

6. **Prefer pathless layout routes for auth boundaries** - Group protected endpoints under a pathless layout with auth middleware instead of repeating it per route.

7. **Keep handlers thin** - Move business logic to service modules. Handlers should parse input, call services, and format responses.

## References

- Server Routes: https://tanstack.com/start/latest/docs/framework/react/server-routes
- Middleware: https://tanstack.com/start/latest/docs/framework/react/middleware
- SEO: https://tanstack.com/start/latest/docs/framework/react/seo
- Databases: https://tanstack.com/start/latest/docs/framework/react/databases
- Authentication: https://tanstack.com/start/latest/docs/framework/react/authentication
- File-based routing: https://tanstack.com/router/latest/docs/framework/react/routing/file-based-routing
- MDN Request API: https://developer.mozilla.org/en-US/docs/Web/API/Request
- MDN Response API: https://developer.mozilla.org/en-US/docs/Web/API/Response
