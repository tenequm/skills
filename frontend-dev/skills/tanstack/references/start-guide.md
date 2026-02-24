
# TanStack Start

Full-stack React framework powered by TanStack Router and Vite. Adds SSR, streaming, server functions, middleware, server routes, and universal deployment to TanStack Router's type-safe routing.

> TanStack Start is in Release Candidate stage. API is stable and feature-complete. No RSC support yet (in active development).

## When to Use This Skill

- Building full-stack React with SSR, SSG, or streaming
- Adding server functions (type-safe RPCs) to a React app
- Creating API/server routes alongside frontend routes
- Implementing middleware for auth, logging, or request handling
- Deploying to Cloudflare Workers, Netlify, Vercel, Node.js, Bun, or Docker
- Need SPA mode with optional server functions (no SSR required)

**Use TanStack Router alone** (see `router-guide.md`) when you only need client-side routing without server features.

> For routing concepts (file-based routing, search params, nested layouts, loaders, preloading), see `router-guide.md`. This guide covers Start-specific full-stack features.

## Quick Start Workflow

### 1. Create Project

```bash
pnpm create @tanstack/start@latest
```

### 2. Manual Setup

```bash
npm i @tanstack/react-start @tanstack/react-router react react-dom
npm i -D vite @vitejs/plugin-react typescript @types/react @types/react-dom vite-tsconfig-paths
```

### 3. Vite Configuration

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import tsConfigPaths from 'vite-tsconfig-paths'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  server: { port: 3000 },
  plugins: [
    tsConfigPaths(),
    tanstackStart(),
    viteReact(), // MUST come after tanstackStart()
  ],
})
```

### 4. Router and Root Route

```tsx
// src/router.tsx
import { createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

export function getRouter() {
  return createRouter({ routeTree, scrollRestoration: true })
}
```

```tsx
// src/routes/__root.tsx
/// <reference types="vite/client" />
import type { ReactNode } from 'react'
import { Outlet, createRootRoute, HeadContent, Scripts } from '@tanstack/react-router'

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { title: 'My TanStack Start App' },
    ],
  }),
  component: () => (
    <html>
      <head><HeadContent /></head>
      <body><Outlet /><Scripts /></body>
    </html>
  ),
})
```

### 5. Route with Server Function

```tsx
// src/routes/index.tsx
import { createFileRoute } from '@tanstack/react-router'
import { createServerFn } from '@tanstack/react-start'

const getServerTime = createServerFn({ method: 'GET' }).handler(async () => {
  return new Date().toISOString()
})

export const Route = createFileRoute('/')({
  loader: () => getServerTime(),
  component: () => {
    const time = Route.useLoaderData()
    return <div>Server time: {time}</div>
  },
})
```

### File Structure

```
src/
├── routes/
│   ├── __root.tsx        # HTML shell, always rendered
│   └── index.tsx
├── router.tsx            # Router config
├── routeTree.gen.ts      # Auto-generated
├── start.ts              # Optional: global middleware
└── server.ts             # Optional: custom server entry
```

## Execution Model

All code is **isomorphic by default** - runs in both server and client bundles unless constrained. Route `loader`s run on the server during SSR AND on the client during navigation.

```tsx
// WRONG - secret exposed to client bundle
export const Route = createFileRoute('/users')({
  loader: () => {
    const secret = process.env.SECRET
    return fetch(`/api/users?key=${secret}`)
  },
})

// CORRECT - server function keeps secrets server-side
const getUsers = createServerFn().handler(async () => {
  return fetch(`/api/users?key=${process.env.SECRET}`)
})

export const Route = createFileRoute('/users')({
  loader: () => getUsers(),
})
```

| API | Runs On | Client Behavior |
|-----|---------|-----------------|
| `createServerFn()` | Server | Network request (RPC) |
| `createServerOnlyFn(fn)` | Server | Throws error |
| `createClientOnlyFn(fn)` | Client | Works normally |
| `createIsomorphicFn()` | Both | Environment-specific impl |
| `<ClientOnly>` | Client | Renders fallback on server |

## Server Functions

Type-safe RPCs via `createServerFn()`. Server code is extracted from client bundles at build time; client calls become `fetch` requests.

```tsx
import { createServerFn } from '@tanstack/react-start'
import { z } from 'zod'
import { redirect, notFound } from '@tanstack/react-router'

// GET with no input
export const getData = createServerFn({ method: 'GET' }).handler(async () => {
  return { message: 'Hello from server!' }
})

// POST with Zod validation
const CreatePostSchema = z.object({
  title: z.string().min(1).max(200),
  body: z.string().min(1),
})

export const createPost = createServerFn({ method: 'POST' })
  .inputValidator(CreatePostSchema)
  .handler(async ({ data }) => {
    return await db.posts.create(data)
  })

// Redirect and notFound
export const getPost = createServerFn()
  .inputValidator((data: { id: string }) => data)
  .handler(async ({ data }) => {
    const post = await db.findPost(data.id)
    if (!post) throw notFound()
    return post
  })
```

### Calling Server Functions

```tsx
// From loader
export const Route = createFileRoute('/posts')({
  loader: () => getPosts(),
})

// From component with useServerFn
import { useServerFn } from '@tanstack/react-start'

function CreatePostForm() {
  const mutation = useServerFn(createPost)
  return <button onClick={() => mutation({ data: { title: 'New', body: 'Content' } })}>Create</button>
}

// Direct call with router.invalidate()
function DeleteButton({ id }: { id: string }) {
  const router = useRouter()
  return <button onClick={() => deletePost({ data: { id } }).then(() => router.invalidate())}>Delete</button>
}
```

### Server Context Utilities

Access request/response from `@tanstack/react-start/server`: `getRequest()`, `getRequestHeader(name)`, `setResponseHeaders(headers)`, `setResponseStatus(code)`.

## Middleware

Two types: **request middleware** (all server requests including SSR) and **server function middleware** (server functions only, with client-side hooks and input validation).

### Request Middleware

```tsx
import { createMiddleware } from '@tanstack/react-start'

const loggingMiddleware = createMiddleware().server(async ({ next, request }) => {
  const start = Date.now()
  const result = await next()
  console.log(`${request.method} ${request.url} - ${Date.now() - start}ms`)
  return result
})
```

### Server Function Middleware with Context

```tsx
const authMiddleware = createMiddleware({ type: 'function' })
  .server(async ({ next }) => {
    const user = await getCurrentUser()
    if (!user) throw redirect({ to: '/login' })
    return next({ context: { user } })
  })

const getProfile = createServerFn()
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    return context.user // typed
  })
```

### Client + Server Middleware

```tsx
const authHeaderMiddleware = createMiddleware({ type: 'function' })
  .client(async ({ next }) => {
    return next({ headers: { Authorization: `Bearer ${getToken()}` } })
  })
  .server(async ({ next }) => {
    const user = await verifyToken(getRequestHeader('Authorization'))
    return next({ context: { user } })
  })
```

### Global Middleware (src/start.ts)

```tsx
import { createStart, createMiddleware } from '@tanstack/react-start'

export const startInstance = createStart(() => ({
  requestMiddleware: [globalLogger],  // ALL requests (SSR, routes, fns)
  functionMiddleware: [globalAuth],   // ALL server functions
}))
```

## Server Routes

HTTP endpoints alongside frontend routes using file-based routing. Handlers receive `{ request, params, context }` and return `Response`.

```tsx
// src/routes/api/users.ts
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/api/users')({
  server: {
    middleware: [authMiddleware],
    handlers: {
      GET: async ({ request }) => {
        return Response.json(await db.users.findMany())
      },
      POST: async ({ request }) => {
        const body = await request.json()
        return Response.json(await db.users.create(body), { status: 201 })
      },
    },
  },
})
```

Per-handler middleware via `createHandlers`:

```tsx
server: {
  handlers: ({ createHandlers }) => createHandlers({
    GET: async ({ request }) => Response.json({ ok: true }),
    DELETE: {
      middleware: [adminOnlyMiddleware],
      handler: async ({ request }) => Response.json({ deleted: true }),
    },
  }),
}
```

Server routes and components can co-exist in the same file. Dynamic params (`$id`), wildcards (`$`), and escaped matching (`[.]json`) all work identically to Router.

## SSR Modes

Per-route SSR control via the `ssr` property:

| Mode | Loaders | Component | Use Case |
|------|---------|-----------|----------|
| `true` (default) | Server + Client | Server + Client | SEO, performance |
| `false` | Client only | Client only | Browser APIs, canvas |
| `'data-only'` | Server + Client | Client only | Dashboards |
| `(params, search) => ...` | Dynamic | Dynamic | Conditional SSR |

```tsx
export const Route = createFileRoute('/dashboard')({
  ssr: 'data-only',
  loader: () => getDashboardData(),
  component: Dashboard,
})
```

### SPA Mode

Ship static HTML shells with server function support but no SSR:

```ts
// vite.config.ts
tanstackStart({ spa: { enabled: true } })
```

### Global Default

```tsx
// src/start.ts
export const startInstance = createStart(() => ({ defaultSsr: false }))
```

## Head Management and SEO

```tsx
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params }) => ({ post: await getPost({ data: { id: params.postId } }) }),
  head: ({ loaderData }) => ({
    meta: [
      { title: loaderData.post.title },
      { name: 'description', content: loaderData.post.excerpt },
      { property: 'og:title', content: loaderData.post.title },
      { property: 'og:image', content: loaderData.post.coverImage },
      { name: 'twitter:card', content: 'summary_large_image' },
    ],
    links: [{ rel: 'canonical', href: `https://myapp.com/posts/${loaderData.post.id}` }],
  }),
  component: PostPage,
})
```

## Authentication

### Session Management

```tsx
// utils/session.ts
import { useSession } from '@tanstack/react-start/server'

export function useAppSession() {
  return useSession<{ userId?: string; email?: string }>({
    name: 'app-session',
    password: process.env.SESSION_SECRET!,
    cookie: { secure: process.env.NODE_ENV === 'production', sameSite: 'lax', httpOnly: true },
  })
}
```

### Route Protection

```tsx
// src/routes/_authed.tsx - layout route guard
export const Route = createFileRoute('/_authed')({
  beforeLoad: async ({ location }) => {
    const user = await getCurrentUserFn()
    if (!user) throw redirect({ to: '/login', search: { redirect: location.href } })
    return { user }
  },
})

// src/routes/_authed/dashboard.tsx - automatically protected
export const Route = createFileRoute('/_authed/dashboard')({
  component: () => {
    const { user } = Route.useRouteContext()
    return <h1>Welcome, {user.email}!</h1>
  },
})
```

## Environment Functions

```tsx
import { createIsomorphicFn, createServerOnlyFn, createClientOnlyFn } from '@tanstack/react-start'
import { ClientOnly } from '@tanstack/react-router'

const getDeviceInfo = createIsomorphicFn()
  .server(() => ({ type: 'server', platform: process.platform }))
  .client(() => ({ type: 'client', userAgent: navigator.userAgent }))

const getDbUrl = createServerOnlyFn(() => process.env.DATABASE_URL) // throws on client
const saveLocal = createClientOnlyFn((k: string, v: string) => localStorage.setItem(k, v)) // throws on server

// Component-level: renders fallback during SSR, children after hydration
<ClientOnly fallback={<div>Loading...</div>}><InteractiveChart /></ClientOnly>
```

## Deployment

### Cloudflare Workers (Official Partner)

Install `@cloudflare/vite-plugin` and `wrangler`, add `cloudflare({ viteEnvironment: { name: 'ssr' } })` to vite plugins (before `tanstackStart()`), and set `"main": "@tanstack/react-start/server-entry"` in `wrangler.jsonc`.

### Netlify (Official Partner)

Install `@netlify/vite-plugin-tanstack-start`, add `netlify()` to vite plugins alongside `tanstackStart()`.

### Nitro (Node.js, Vercel, Bun, Docker)

Install `nitro@npm:nitro-nightly@latest`, add `nitro()` to vite plugins. Build with `vite build`, run with `node .output/server/index.mjs`.

### Static Prerendering

```ts
tanstackStart({ prerender: { enabled: true, crawlLinks: true } })
```

## Best Practices

1. **Never put secrets in loaders** - Loaders are isomorphic. Use `createServerFn()` for server-only access.
2. **Server functions are the boundary** - Primary mechanism for safe server-only execution from client code.
3. **Organize by concern** - `.functions.ts` for server fn wrappers, `.server.ts` for internal helpers, `.ts` for shared types/schemas.
4. **Compose middleware hierarchically** - Global for cross-cutting concerns, route-level for groups, function-level for specifics.
5. **Use `head()` on every content route** - Title, description, OG tags. Use loader data for dynamic pages.
6. **Choose SSR mode per route** - `true` for SEO, `false` for browser-only, `'data-only'` for dashboards.
7. **Validate all server function inputs** - Zod or custom validators via `.inputValidator()`.

## Advanced Topics

For deeper coverage, see reference files:

- `server-functions.md` - Streaming, FormData, progressive enhancement, request cancellation, custom function IDs
- `middleware.md` - sendContext, custom fetch, global config, environment tree shaking
- `ssr-modes.md` - Selective SSR inheritance, functional form, shellComponent, fallback rendering
- `server-routes.md` - Dynamic params, wildcards, escaped matching, pathless layouts

## Resources

- [Official Docs](https://tanstack.com/start/latest/docs/framework/react/overview)
- [GitHub](https://github.com/TanStack/router) (Start lives in the router repo)
- [Examples](https://github.com/TanStack/router/tree/main/examples/react) - Basic, Auth, React Query, Cloudflare, Clerk, Supabase
- [Start vs Next.js](https://tanstack.com/start/latest/docs/framework/react/comparison)
- Cross-reference: `router-guide.md` for routing, `query-guide.md` for data fetching
