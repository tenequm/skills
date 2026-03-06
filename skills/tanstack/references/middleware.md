# TanStack Start Middleware

Middleware in TanStack Start lets you intercept and customize server requests (including SSR) and server functions. Middleware is composable, type-safe, and supports both client-side and server-side logic.

Official docs: https://tanstack.com/start/latest/docs/framework/react/middleware

## Two Types of Middleware

### Request Middleware

Runs on every server request that passes through it - server routes, SSR, and server functions. Created with `createMiddleware()` (type defaults to `'request'`). Only has a `.server()` method.

### Server Function Middleware

Runs specifically for server functions. Created with `createMiddleware({ type: 'function' })`. Has `.client()`, `.server()`, and `.inputValidator()` methods. The `.client()` method wraps the RPC call on the client side.

| Feature          | Request Middleware          | Server Function Middleware     |
|------------------|----------------------------|--------------------------------|
| Scope            | All server requests        | Server functions only          |
| Methods          | `.server()`                | `.client()`, `.server()`       |
| Input Validation | No                         | Yes (`.inputValidator()`)      |
| Client-side Logic| No                         | Yes                            |
| Dependencies     | Request middleware only     | Both request and function types |

## Creating Request Middleware

Request middleware receives `next`, `context`, `request`, `pathname`, and `serverFnMeta` (present only for server function calls) in its `.server()` callback.

```typescript
import { createMiddleware } from '@tanstack/react-start'

const loggingMiddleware = createMiddleware().server(
  async ({ next, context, request }) => {
    const startTime = Date.now()
    const url = new URL(request.url)
    console.log(`[${request.method}] ${url.pathname} - Starting`)
    const result = await next()
    console.log(
      `[${request.method}] ${url.pathname} - ${result.response.status} (${Date.now() - startTime}ms)`,
    )
    return result
  },
)
```

## Creating Server Function Middleware

Method order is enforced by TypeScript: `.middleware()` -> `.inputValidator()` -> `.client()` -> `.server()`.

```typescript
import { createMiddleware } from '@tanstack/react-start'

const timingMiddleware = createMiddleware({ type: 'function' })
  .client(async ({ next }) => {
    const clientStart = Date.now()
    const result = await next() // triggers RPC to server
    console.log(`RPC round-trip: ${Date.now() - clientStart}ms`)
    return result
  })
  .server(async ({ next }) => {
    const serverStart = Date.now()
    const result = await next()
    console.log(`Server execution: ${Date.now() - serverStart}ms`)
    return result
  })
```

The `.client()` callback receives `next`, `context`, `data`, `method`, `signal`, `serverFnMeta`, and `filename`. The `.server()` callback receives `next`, `context`, `data`, `method`, `serverFnMeta`, and `signal`.

### The .inputValidator() Method

Validates and transforms input data before it reaches the middleware chain. Works with `zodValidator`, `valibotValidator`, and `arktypeValidator`.

```typescript
import { createMiddleware } from '@tanstack/react-start'
import { zodValidator } from '@tanstack/zod-adapter'
import { z } from 'zod'

const workspaceMiddleware = createMiddleware({ type: 'function' })
  .inputValidator(zodValidator(z.object({ workspaceId: z.string().uuid() })))
  .server(({ next, data }) => {
    console.log('Validated workspace ID:', data.workspaceId)
    return next()
  })
```

## Middleware Composition

Middleware depends on other middleware through `.middleware()`. Dependencies execute first, and their context accumulates.

```typescript
import { createMiddleware } from '@tanstack/react-start'

const loggingMiddleware = createMiddleware().server(async ({ next }) => {
  console.log('Logging: request started')
  return next()
})

const authMiddleware = createMiddleware()
  .middleware([loggingMiddleware])
  .server(async ({ next }) => {
    // loggingMiddleware runs first, then this
    return next({ context: { userId: 'user-123' } })
  })

const adminMiddleware = createMiddleware()
  .middleware([authMiddleware])
  .server(async ({ next, context }) => {
    // logging -> auth -> admin
    if (context.userId !== 'admin') {
      throw new Error('Forbidden')
    }
    return next()
  })
```

Rules: request middleware can only depend on request middleware. Function middleware can depend on both types.

## next() and Context Management

### Providing Context

Call `next()` with a `context` object to pass typed data downstream. Context merges into the parent context.

```typescript
const featureFlagMiddleware = createMiddleware({ type: 'function' }).server(
  ({ next }) => {
    return next({
      context: { features: { newDashboard: true, betaAPI: false } },
    })
  },
)

const consumer = createMiddleware({ type: 'function' })
  .middleware([featureFlagMiddleware])
  .server(async ({ next, context }) => {
    console.log('Dashboard enabled:', context.features.newDashboard) // typed
    return next()
  })
```

### Sending Client Context to the Server

Client context is NOT sent to the server by default. Use `sendContext` in `.client()` to explicitly transmit data.

```typescript
const workspaceMiddleware = createMiddleware({ type: 'function' })
  .client(async ({ next, context }) => {
    return next({ sendContext: { workspaceId: context.workspaceId } })
  })
  .server(async ({ next, context }) => {
    // Validate dynamic data before trusting it
    const workspaceId = zodValidator(z.string().uuid()).parse(context.workspaceId)
    return next({ context: { validatedWorkspaceId: workspaceId } })
  })
```

### Sending Server Context to the Client

Use `sendContext` in `.server()` to send data back. Access it via `result.context` in the `.client()` method.

```typescript
const serverTimer = createMiddleware({ type: 'function' }).server(
  async ({ next }) => {
    return next({ sendContext: { serverTimestamp: new Date().toISOString() } })
  },
)

const clientLogger = createMiddleware({ type: 'function' })
  .middleware([serverTimer])
  .client(async ({ next }) => {
    const result = await next()
    console.log('Server time:', result.context.serverTimestamp) // typed
    return result
  })
```

## Authentication Middleware - Complete Flow

### Session Setup

```typescript
// utils/session.ts
import { useSession } from '@tanstack/react-start/server'

type SessionData = {
  userId?: string
  email?: string
  role?: 'user' | 'admin' | 'moderator'
}

export function useAppSession() {
  return useSession<SessionData>({
    name: 'app-session',
    password: process.env.SESSION_SECRET!, // at least 32 characters
    cookie: {
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      httpOnly: true,
      maxAge: 7 * 24 * 60 * 60,
    },
  })
}
```

### Auth Server Functions

```typescript
// utils/auth.ts
import { createServerFn } from '@tanstack/react-start'
import { redirect } from '@tanstack/react-router'
import { useAppSession } from './session'

export const loginFn = createServerFn({ method: 'POST' })
  .inputValidator((d: { email: string; password: string }) => d)
  .handler(async ({ data }) => {
    const user = await authenticateUser(data.email, data.password)
    if (!user) {
      return { error: true, message: 'Invalid credentials' }
    }
    const session = await useAppSession()
    await session.update({ userId: user.id, email: user.email, role: user.role })
    throw redirect({ to: '/dashboard' })
  })

export const getCurrentUserFn = createServerFn({ method: 'GET' }).handler(
  async () => {
    const session = await useAppSession()
    if (!session.data.userId) return null
    return getUserById(session.data.userId)
  },
)
```

### Auth Middleware and Route Protection

```typescript
// middleware/auth.ts
import { createMiddleware } from '@tanstack/react-start'
import { useAppSession } from '../utils/session'

export const authMiddleware = createMiddleware().server(async ({ next }) => {
  const session = await useAppSession()
  return next({
    context: {
      userId: session.data.userId ?? null,
      userRole: session.data.role ?? null,
      isAuthenticated: !!session.data.userId,
    },
  })
})
```

```typescript
// routes/_authed.tsx - layout route guard
import { createFileRoute, redirect } from '@tanstack/react-router'
import { getCurrentUserFn } from '../utils/auth'

export const Route = createFileRoute('/_authed')({
  beforeLoad: async ({ location }) => {
    const user = await getCurrentUserFn()
    if (!user) {
      throw redirect({ to: '/login', search: { redirect: location.href } })
    }
    return { user }
  },
})
```

```typescript
// routes/_authed/dashboard.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authed/dashboard')({
  component: () => {
    const { user } = Route.useRouteContext()
    return <h1>Welcome, {user.email}!</h1>
  },
})
```

```typescript
// routes/_authed/admin.tsx - role-based guard
import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authed/admin')({
  beforeLoad: async ({ context }) => {
    if (context.user.role !== 'admin') {
      throw redirect({ to: '/unauthorized' })
    }
  },
})
```

## Global Middleware

Configure in `src/start.ts` (not included in the default template - create it when needed).

```typescript
// src/start.ts
import { createStart, createMiddleware } from '@tanstack/react-start'

const globalLogger = createMiddleware().server(async ({ request, next }) => {
  const start = Date.now()
  const result = await next()
  console.log(`${request.method} ${new URL(request.url).pathname} ${result.response.status} ${Date.now() - start}ms`)
  return result
})

const fnTimer = createMiddleware({ type: 'function' }).server(
  async ({ next, serverFnMeta }) => {
    const start = Date.now()
    const result = await next()
    console.log(`ServerFn ${serverFnMeta.id}: ${Date.now() - start}ms`)
    return result
  },
)

export const startInstance = createStart(() => ({
  requestMiddleware: [globalLogger],     // runs on every request (SSR, routes, fns)
  functionMiddleware: [fnTimer],          // runs on every server function
}))
```

### Execution Order

Dependency-first, then global middleware, then the chain:

```typescript
// With globalMiddleware1, globalMiddleware2 in start.ts:
const a = createMiddleware({ type: 'function' }).server(async ({ next }) => { console.log('a'); return next() })
const b = createMiddleware({ type: 'function' }).middleware([a]).server(async ({ next }) => { console.log('b'); return next() })
const c = createMiddleware({ type: 'function' }).server(async ({ next }) => { console.log('c'); return next() })
const d = createMiddleware({ type: 'function' }).middleware([b, c]).server(async ({ next }) => { console.log('d'); return next() })
const fn = createServerFn().middleware([d]).handler(async () => { console.log('fn') })
// Order: globalMiddleware1 -> globalMiddleware2 -> a -> b -> c -> d -> fn
```

## Usage with Server Functions

```typescript
import { createServerFn } from '@tanstack/react-start'

const getProtectedDataFn = createServerFn()
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    if (!context.isAuthenticated) throw new Error('Unauthorized')
    return fetchDataForUser(context.userId)
  })
```

## Usage with Server Routes

### Route-Level Middleware (All Methods)

```typescript
export const Route = createFileRoute('/api/data')({
  server: {
    middleware: [corsMiddleware, authMiddleware],
    handlers: {
      GET: async () => Response.json({ items: await fetchItems() }),
      POST: async ({ request }) => Response.json({ created: await createItem(await request.json()) }),
    },
  },
})
```

### Handler-Specific Middleware

Use `createHandlers` to attach middleware to individual HTTP methods. Route-level middleware runs first, then handler-specific.

```typescript
export const Route = createFileRoute('/api/items')({
  server: {
    middleware: [corsMiddleware],
    handlers: ({ createHandlers }) =>
      createHandlers({
        GET: async () => Response.json({ items: await fetchItems() }),
        POST: {
          middleware: [writeAuthMiddleware],
          handler: async ({ request }) => Response.json(await createItem(await request.json())),
        },
      }),
  },
})
```

## Client Request Modification

### Custom Headers

```typescript
const authHeaderMiddleware = createMiddleware({ type: 'function' }).client(
  async ({ next }) => {
    return next({ headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } })
  },
)
```

Headers merge across middleware. Precedence: call-site headers > later middleware > earlier middleware.

### Custom Fetch

Provide a custom `fetch` for retries, logging, or testing. Precedence (highest to lowest): call site > later middleware > earlier middleware > `createStart({ serverFns: { fetch } })` > default `fetch`. Custom fetch only applies client-side; during SSR, server functions are called directly.

```typescript
import type { CustomFetch } from '@tanstack/react-start'

const retryMiddleware = createMiddleware({ type: 'function' }).client(
  async ({ next }) => {
    const retryFetch: CustomFetch = async (url, init) => {
      for (let attempt = 0; attempt < 3; attempt++) {
        try { return await fetch(url, init) }
        catch { await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt))) }
      }
      throw new Error('Max retries exceeded')
    }
    return next({ fetch: retryFetch })
  },
)
```

## Validation Adapters

```typescript
// Zod
import { zodValidator } from '@tanstack/zod-adapter'
import { z } from 'zod'

const paginationMiddleware = createMiddleware({ type: 'function' })
  .inputValidator(zodValidator(z.object({ page: z.number().default(1), limit: z.number().max(100).default(20) })))
  .server(({ next, data }) => { console.log(`Page ${data.page}`); return next() })

// Valibot
import { valibotValidator } from '@tanstack/valibot-adapter'
import * as v from 'valibot'

const vMiddleware = createMiddleware({ type: 'function' })
  .inputValidator(valibotValidator(v.object({ workspaceId: v.pipe(v.string(), v.uuid()) })))
  .server(({ next, data }) => next({ context: { workspaceId: data.workspaceId } }))

// ArkType
import { arktypeValidator } from '@tanstack/arktype-adapter'
import { type } from 'arktype'

const aMiddleware = createMiddleware({ type: 'function' })
  .inputValidator(arktypeValidator(type({ tenantId: 'string' })))
  .server(({ next, data }) => next({ context: { tenantId: data.tenantId } }))
```

## Common Patterns

### CORS Middleware

```typescript
export const corsMiddleware = createMiddleware().server(async ({ next }) => {
  const result = await next()
  result.response.headers.set('Access-Control-Allow-Origin', process.env.ALLOWED_ORIGIN || '*')
  result.response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  result.response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  result.response.headers.set('Access-Control-Max-Age', '86400')
  return result
})
```

### Security Headers

```typescript
export const securityHeaders = createMiddleware().server(async ({ next }) => {
  const result = await next()
  result.response.headers.set('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'")
  result.response.headers.set('X-Content-Type-Options', 'nosniff')
  result.response.headers.set('X-Frame-Options', 'DENY')
  result.response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
  return result
})
```

### Rate Limiting

```typescript
const rateLimitStore = new Map<string, { count: number; resetTime: number }>()

export const rateLimitMiddleware = createMiddleware().server(
  async ({ request, next }) => {
    const ip = request.headers.get('x-forwarded-for') || 'unknown'
    const now = Date.now()
    const entry = rateLimitStore.get(ip)

    if (!entry || now > entry.resetTime) {
      rateLimitStore.set(ip, { count: 1, resetTime: now + 15 * 60 * 1000 })
    } else if (entry.count >= 100) {
      return new Response('Too Many Requests', {
        status: 429,
        headers: { 'Retry-After': Math.ceil((entry.resetTime - now) / 1000).toString() },
      })
    } else {
      entry.count++
    }
    return next()
  },
)
```

### Composition Chain Example

```typescript
import { createMiddleware, createServerFn } from '@tanstack/react-start'
import { useAppSession } from '../utils/session'

// Layer 1: Logging
const logging = createMiddleware().server(async ({ request, next }) => {
  const start = Date.now()
  const result = await next()
  console.log(`${request.method} ${new URL(request.url).pathname} ${Date.now() - start}ms`)
  return result
})

// Layer 2: Auth context - depends on logging
const auth = createMiddleware()
  .middleware([logging])
  .server(async ({ next }) => {
    const session = await useAppSession()
    return next({
      context: { userId: session.data.userId ?? null, isAuthenticated: !!session.data.userId },
    })
  })

// Layer 3: Require auth - depends on auth
const requireAuth = createMiddleware()
  .middleware([auth])
  .server(async ({ next, context }) => {
    if (!context.isAuthenticated) return new Response('Unauthorized', { status: 401 })
    return next()
  })

// Usage: logging -> auth -> requireAuth -> handler
const getProfileFn = createServerFn()
  .middleware([requireAuth])
  .handler(async ({ context }) => fetchUserProfile(context.userId))
```

## Response Modification and Short-Circuiting

Request middleware can modify responses or return a `Response` directly to short-circuit.

```typescript
const debugMiddleware = createMiddleware().server(async ({ next }) => {
  const result = await next()
  if (process.env.NODE_ENV === 'development') {
    result.response.headers.set('X-Debug-Timestamp', new Date().toISOString())
  }
  return result
})

const maintenanceMiddleware = createMiddleware().server(async ({ next }) => {
  if (process.env.MAINTENANCE_MODE === 'true') {
    return new Response('Service temporarily unavailable', { status: 503 })
  }
  return next()
})
```

## Environment Tree Shaking

- **Server bundle**: All middleware code is included
- **Client bundle**: `.server()` and `data` validation code are removed

You can safely import server-only dependencies in `.server()` callbacks.

## Best Practices

1. **Start with request middleware for cross-cutting concerns.** Logging, security headers, CORS, and auth session resolution apply to all requests including SSR.

2. **Use function middleware only when you need `.client()` or `.inputValidator()`.** If you only need server-side logic, request middleware is simpler.

3. **Always return the result of next().** Forgetting to return breaks the pipeline.

4. **Validate sendContext on the server.** Client-sent context is type-safe but not runtime-validated. Validate dynamic data before trusting it.

5. **Create src/start.ts for global middleware.** This file is not in the default template. Create it for `requestMiddleware` or `functionMiddleware`.

6. **Compose small units.** Build focused middleware and compose via `.middleware([...])` rather than duplicating logic.

7. **Combine middleware with beforeLoad for auth.** Middleware provides context; `beforeLoad` on layout routes like `_authed.tsx` provides redirect behavior. Use both together.

## Official References

- Middleware: https://tanstack.com/start/latest/docs/framework/react/middleware
- Authentication: https://tanstack.com/start/latest/docs/framework/react/authentication
- Server functions: https://tanstack.com/start/latest/docs/framework/react/server-functions
- Server routes: https://tanstack.com/start/latest/docs/framework/react/server-routes
- DIY auth example: https://github.com/TanStack/router/tree/main/examples/react/start-basic-auth
