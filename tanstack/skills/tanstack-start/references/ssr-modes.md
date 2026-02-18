# SSR Modes and Rendering Strategies

TanStack Start provides granular control over server-side rendering at the application, route, and even request level. This reference covers every rendering mode, deployment target, and caching strategy.

## Full-Document SSR (Default)

SSR is enabled by default. On the initial request, TanStack Start renders all matched route components on the server, sends complete HTML to the client, and hydrates it into an interactive application.

The default SSR flow:

1. Server receives a request and matches routes
2. `beforeLoad` and `loader` execute on the server for all matched routes
3. Components render to HTML on the server
4. HTML is sent to the client along with serialized loader data
5. Client hydrates the markup into a fully interactive React application

```tsx
// src/routes/posts/$postId.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/posts/$postId')({
  // ssr defaults to true - no configuration needed
  beforeLoad: () => {
    console.log('Runs on the server during initial request')
    console.log('Runs on the client for subsequent navigation')
  },
  loader: async ({ params }) => {
    const post = await fetchPost(params.postId)
    return { post }
  },
  component: PostPage,
})

function PostPage() {
  const { post } = Route.useLoaderData()
  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
    </article>
  )
}
```

After hydration, subsequent navigations run `beforeLoad` and `loader` on the client. Route loaders are isomorphic - they execute on the server during SSR and on the client during client-side navigation.

## Streaming SSR

TanStack Start uses streaming by default for SSR responses. The server streams HTML progressively to the client as components render. Combined with React Suspense boundaries, this enables progressive page loading where above-the-fold content arrives first while deferred data loads asynchronously.

Streaming works with server functions that return `ReadableStream` or use async generators:

```tsx
import { createServerFn } from '@tanstack/react-start'

type Message = {
  content: string
}

// Using ReadableStream
const streamMessages = createServerFn().handler(async () => {
  const messages: Message[] = await getMessages()

  const stream = new ReadableStream<Message>({
    async start(controller) {
      for (const message of messages) {
        controller.enqueue(message)
      }
      controller.close()
    },
  })

  return stream
})

// Using async generators (cleaner approach)
const streamMessagesGenerator = createServerFn().handler(async function* () {
  const messages: Message[] = await getMessages()
  for (const msg of messages) {
    yield msg
  }
})
```

Client consumption with typed streaming:

```tsx
function MessageFeed() {
  const [messages, setMessages] = useState('')

  const loadMessages = useCallback(async () => {
    for await (const msg of await streamMessagesGenerator()) {
      // msg is typed as Message
      setMessages((prev) => prev + msg.content)
    }
  }, [])

  return (
    <div>
      <button onClick={loadMessages}>Load Messages</button>
      <pre>{messages}</pre>
    </div>
  )
}
```

The custom server handler controls streaming behavior through `src/server.ts`:

```tsx
// src/server.ts
import {
  createStartHandler,
  defaultStreamHandler,
  defineHandlerCallback,
} from '@tanstack/react-start/server'
import { createServerEntry } from '@tanstack/react-start/server-entry'

const customHandler = defineHandlerCallback((ctx) => {
  // Add custom logic before streaming
  return defaultStreamHandler(ctx)
})

const fetch = createStartHandler(customHandler)

export default createServerEntry({
  fetch,
})
```

## Per-Route SSR Control (Selective SSR)

The `ssr` property on a route controls server-side behavior during the initial request. There are three values and a functional form.

### ssr: true (Default)

Server runs `beforeLoad` and `loader`, renders the component, and sends full HTML.

```tsx
export const Route = createFileRoute('/posts/$postId')({
  ssr: true,
  beforeLoad: () => {
    console.log('Executes on the server during the initial request')
    console.log('Executes on the client for subsequent navigation')
  },
  loader: () => {
    console.log('Executes on the server during the initial request')
    console.log('Executes on the client for subsequent navigation')
  },
  component: () => <div>This component is rendered on the server</div>,
})
```

### ssr: false (Client-Only Rendering)

Disables server-side execution of `beforeLoad`, `loader`, and component rendering entirely. Everything runs on the client during hydration.

```tsx
export const Route = createFileRoute('/dashboard')({
  ssr: false,
  beforeLoad: () => {
    // Uses browser-only API safely
    const token = localStorage.getItem('auth_token')
    if (!token) throw redirect({ to: '/login' })
  },
  loader: () => {
    console.log('Executes on the client during hydration')
  },
  component: () => <div>This component is rendered on the client</div>,
})
```

Use `ssr: false` when:

- `beforeLoad` or `loader` depends on browser-only APIs (e.g., `localStorage`, `canvas`)
- The route component depends on browser-only APIs
- SEO is not important for this route

### ssr: 'data-only' (Server Data, Client Rendering)

A hybrid option. The server runs `beforeLoad` and `loader` and sends the data to the client, but the component renders only on the client.

```tsx
export const Route = createFileRoute('/charts')({
  ssr: 'data-only',
  beforeLoad: () => {
    console.log('Executes on the server during the initial request')
  },
  loader: async () => {
    // Data fetched on server, but component using canvas renders on client
    return await fetchChartData()
  },
  component: () => {
    const data = Route.useLoaderData()
    // Canvas-based chart that requires browser APIs
    return <CanvasChart data={data} />
  },
})
```

### Functional Form (Runtime Decisions)

For dynamic SSR decisions based on route params or search params:

```tsx
import { z } from 'zod'

export const Route = createFileRoute('/docs/$docType/$docId')({
  validateSearch: z.object({ details: z.boolean().optional() }),
  ssr: ({ params, search }) => {
    // Disable SSR for sheet-type documents
    if (params.status === 'success' && params.value.docType === 'sheet') {
      return false
    }
    // Use data-only for detail views
    if (search.status === 'success' && search.value.details) {
      return 'data-only'
    }
    // Default: full SSR (return undefined or true)
  },
  loader: async ({ params }) => {
    return await fetchDoc(params.docId)
  },
  component: DocViewer,
})
```

The `ssr` function runs only on the server during the initial request and is stripped from the client bundle. The `search` and `params` arguments are passed as discriminated unions after validation:

```tsx
params:
  | { status: 'success'; value: ResolvedParams }
  | { status: 'error'; error: unknown }
search:
  | { status: 'success'; value: ResolvedSearch }
  | { status: 'error'; error: unknown }
```

### Changing the Default SSR Mode

You can change the default for all routes via `createStart`:

```tsx
// src/start.ts
import { createStart } from '@tanstack/react-start'

export const startInstance = createStart(() => ({
  defaultSsr: false, // All routes default to client-only
}))
```

## Inheritance Rules

Child routes inherit the SSR configuration of their parent, but children can only be MORE restrictive, never less. The restrictiveness order is: `true` > `'data-only'` > `false`.

```
Allowed transitions (parent -> child):
  true       -> true, 'data-only', false
  'data-only' -> 'data-only', false
  false      -> false
```

Example hierarchy:

```
root { ssr: undefined }          -> resolves to true (default)
  posts { ssr: 'data-only' }    -> data-only (more restrictive than parent)
    $postId { ssr: true }       -> stays data-only (cannot become LESS restrictive)
      details { ssr: false }    -> false (more restrictive than data-only)
```

Another example:

```
root { ssr: undefined }          -> true
  posts { ssr: false }           -> false
    $postId { ssr: true }        -> stays false (cannot override parent restriction)
```

## Fallback Rendering

When the server encounters the first route with `ssr: false` or `ssr: 'data-only'`, it renders a fallback instead of the route component.

### pendingComponent Fallback

The route's `pendingComponent` is rendered as the fallback. If not configured, `defaultPendingComponent` is used. If neither exists, no fallback is rendered.

```tsx
export const Route = createFileRoute('/dashboard')({
  ssr: false,
  pendingComponent: () => (
    <div className="flex items-center justify-center h-full">
      <Spinner />
      <span>Loading dashboard...</span>
    </div>
  ),
  loader: async () => await fetchDashboardData(),
  component: Dashboard,
})
```

On the client during hydration, this fallback is displayed for at least `minPendingMs` (or `defaultPendingMinMs` if not configured on the route), even if there is no `beforeLoad` or `loader`.

### shellComponent for Root Route

When disabling SSR on the root route, the `<html>` shell still needs to be rendered on the server. Use `shellComponent` for this:

```tsx
import * as React from 'react'
import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRoute,
} from '@tanstack/react-router'

export const Route = createRootRoute({
  shellComponent: RootShell,
  component: RootComponent,
  errorComponent: () => <div>Error</div>,
  notFoundComponent: () => <div>Not found</div>,
  ssr: false,
})

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  )
}

function RootComponent() {
  return (
    <div>
      <h1>This component will be rendered on the client</h1>
      <Outlet />
    </div>
  )
}
```

The `shellComponent` is always SSR-rendered and wraps around the root `component`, `errorComponent`, or `notFoundComponent`.

## SPA Mode

SPA mode completely disables server-side rendering for all routes. The build produces a static HTML shell served from a CDN, and JavaScript takes over entirely on the client.

### Enabling SPA Mode

```tsx
// vite.config.ts
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    tanstackStart({
      spa: {
        enabled: true,
      },
    }),
    viteReact(),
  ],
})
```

### How SPA Mode Works

1. At build time, the root route is prerendered with matched routes replaced by the pending fallback component
2. The resulting HTML is stored as `/_shell.html` (configurable)
3. Default rewrites redirect all 404 requests to the SPA shell
4. On the client, JavaScript hydrates and takes over routing

Server functions and server routes still work - they are served as API endpoints. SPA mode only disables SSR of the HTML document.

### Benefits and Tradeoffs

Benefits:
- Easier to deploy - a CDN serving static assets is all you need
- Cheaper to host - CDNs are inexpensive compared to Lambda functions or persistent servers
- Simpler - no hydration mismatches to debug

Caveats:
- Slower time to full content - all JS must download and execute before rendering
- Less SEO friendly - crawlers may not execute JavaScript or may time out

### SPA Redirect Configuration

Deploy targets need redirects so that all URLs serve the shell. Example for Netlify `_redirects`:

```
# Allow server functions to pass through
/_serverFn/* /_serverFn/:splat 200

# Allow API server routes to pass through
/api/* /api/:splat 200

# Rewrite everything else to the SPA shell
/* /_shell.html 200
```

### SPA Shell Customization

Use `router.isShell()` to detect shell rendering:

```tsx
// src/routes/__root.tsx
function RootComponent() {
  const isShell = useRouter().isShell()

  if (isShell) {
    return <AppShellSkeleton />
  }

  return (
    <div>
      <Navigation />
      <Outlet />
    </div>
  )
}
```

After hydration, `isShell()` returns `false` once the router navigates to the actual route.

### SPA Shell with Dynamic Data

The root route's `loader` runs during prerendering, so its data is baked into the shell:

```tsx
export const Route = createRootRoute({
  loader: async () => {
    return { appName: 'My Application', version: '2.0' }
  },
  component: Root,
})

function Root() {
  const { appName, version } = Route.useLoaderData()
  return (
    <html>
      <head>
        <title>{appName}</title>
      </head>
      <body>
        <Outlet />
      </body>
    </html>
  )
}
```

### SPA Prerender Options

Configure prerendering behavior for the SPA shell:

```tsx
// vite.config.ts
export default defineConfig({
  plugins: [
    tanstackStart({
      spa: {
        enabled: true,
        maskPath: '/', // Pathname used to generate the shell (default: '/')
        prerender: {
          outputPath: '/_shell.html', // Default
          crawlLinks: false,          // Default: false for SPA
          retryCount: 0,              // Default: 0 for SPA
        },
      },
    }),
    viteReact(),
  ],
})
```

## Static Prerendering (SSG)

Static prerendering generates HTML files at build time. Pages are served as static files without on-the-fly server rendering.

### Basic Configuration

```tsx
// vite.config.ts
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    tanstackStart({
      prerender: {
        enabled: true,
        crawlLinks: true,
      },
    }),
    viteReact(),
  ],
})
```

### Full Prerender Options

```tsx
// vite.config.ts
export default defineConfig({
  plugins: [
    tanstackStart({
      prerender: {
        // Enable prerendering
        enabled: true,

        // Generate /page/index.html instead of /page.html
        autoSubfolderIndex: true,

        // Auto-discover static routes from the route tree
        // When disabled, only root and explicitly listed pages are prerendered
        autoStaticPathsDiscovery: true,

        // Number of concurrent prerender jobs
        concurrency: 14,

        // Extract links from rendered HTML and prerender those pages too
        crawlLinks: true,

        // Filter which pages to prerender
        filter: ({ path }) => !path.startsWith('/admin'),

        // Retry count for failed prerender jobs
        retryCount: 2,

        // Delay between retries in milliseconds
        retryDelay: 1000,

        // Maximum redirects to follow during prerendering
        maxRedirects: 5,

        // Abort the build if any prerender fails
        failOnError: true,

        // Callback on successful render
        onSuccess: ({ page }) => {
          console.log(`Prerendered: ${page.path}`)
        },
      },

      // Explicit page configuration (merged with auto-discovered routes)
      pages: [
        {
          path: '/landing',
          prerender: { enabled: true, outputPath: '/landing/index.html' },
        },
      ],
    }),
    viteReact(),
  ],
})
```

### Automatic Static Route Discovery

Static routes are discovered automatically when `autoStaticPathsDiscovery` is enabled (the default). Routes excluded from auto-discovery:

- Routes with path parameters (e.g., `/users/$userId`) - they require specific parameter values
- Layout routes (prefixed with `_`) - they do not render standalone pages
- Routes without components (e.g., API routes)

Dynamic routes can still be prerendered if linked from other pages when `crawlLinks` is enabled.

### Link Crawling

When `crawlLinks: true`, TanStack Start extracts links from each prerendered page and prerenders those linked pages too. For example, if `/` contains a `<Link to="/posts">`, then `/posts` is also prerendered.

## Incremental Static Regeneration (ISR)

TanStack Start implements ISR through standard HTTP `Cache-Control` headers rather than proprietary APIs. This works with any CDN that respects cache headers.

### How ISR Works

1. Pages are prerendered at build time (static prerendering)
2. CDN caches the HTML based on `Cache-Control` headers
3. After cache expires, the next request triggers server-side regeneration
4. `stale-while-revalidate` serves stale content while fresh content generates in the background

### Route-Level Cache Headers

```tsx
// src/routes/blog/posts/$postId.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/blog/posts/$postId')({
  loader: async ({ params }) => {
    const post = await fetchPost(params.postId)
    return { post }
  },
  headers: () => ({
    // Cache at CDN for 1 hour, serve stale for up to 1 day while revalidating
    'Cache-Control':
      'public, max-age=3600, s-maxage=3600, stale-while-revalidate=86400',
  }),
  component: BlogPost,
})

function BlogPost() {
  const { post } = Route.useLoaderData()
  return (
    <article>
      <h1>{post.title}</h1>
      <div>{post.content}</div>
    </article>
  )
}
```

### Cache-Control Directives

| Directive | Purpose |
|-----------|---------|
| `public` | Response can be cached by any cache (CDN, browser) |
| `private` | Only the browser can cache (not CDN) |
| `max-age=N` | Content is fresh for N seconds in the browser |
| `s-maxage=N` | Overrides max-age for shared/CDN caches |
| `stale-while-revalidate=N` | Serve stale content for up to N seconds while fetching fresh content in the background |
| `immutable` | Content never changes (for hashed assets) |

### ISR with Prerendering

Combine build-time prerendering with runtime ISR:

```tsx
// vite.config.ts
export default defineConfig({
  plugins: [
    tanstackStart({
      prerender: {
        enabled: true,
        crawlLinks: true,
      },
    }),
    viteReact(),
  ],
})
```

```tsx
// src/routes/products/$productId.tsx
export const Route = createFileRoute('/products/$productId')({
  loader: async ({ params }) => {
    return await fetchProduct(params.productId)
  },
  // CDN caching (ISR)
  headers: () => ({
    'Cache-Control': 'public, max-age=300, stale-while-revalidate=3600',
  }),
  // Client-side caching (TanStack Router)
  staleTime: 30_000,
  gcTime: 5 * 60_000,
  component: ProductPage,
})
```

This creates a multi-tier caching strategy:

1. CDN edge: 5-minute cache, stale-while-revalidate for 1 hour
2. Client memory: 30 seconds fresh, 5 minutes in cache

### On-Demand Revalidation (CDN Purge)

For immediate invalidation when content changes, purge the CDN cache via API:

```tsx
// src/routes/api/revalidate.ts
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/api/revalidate')({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const { path, secret } = await request.json()

        if (secret !== process.env.REVALIDATE_SECRET) {
          return Response.json({ error: 'Invalid token' }, { status: 401 })
        }

        // Purge via Cloudflare API (adapt for your CDN)
        await fetch(
          `https://api.cloudflare.com/client/v4/zones/${process.env.CF_ZONE_ID}/purge_cache`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${process.env.CF_API_TOKEN}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              files: [`https://yoursite.com${path}`],
            }),
          },
        )

        return Response.json({ revalidated: true })
      },
    },
  },
})
```

### CDN-Specific Cache Headers

```tsx
// Cloudflare Workers
export const Route = createFileRoute('/products/$id')({
  headers: () => ({
    'Cache-Control': 'public, max-age=3600',
    'CDN-Cache-Control': 'max-age=7200', // Cloudflare-specific override
  }),
})
```

Netlify supports `_headers` files:

```
# public/_headers
/blog/*
  Cache-Control: public, max-age=3600, stale-while-revalidate=86400

/api/*
  Cache-Control: public, max-age=300
```

### Common ISR Patterns

Blog posts (infrequent updates):

```tsx
export const Route = createFileRoute('/blog/$slug')({
  loader: async ({ params }) => fetchPost(params.slug),
  headers: () => ({
    'Cache-Control': 'public, max-age=3600, stale-while-revalidate=604800',
  }),
  staleTime: 5 * 60_000,
})
```

E-commerce product pages (inventory changes):

```tsx
export const Route = createFileRoute('/products/$id')({
  loader: async ({ params }) => fetchProduct(params.id),
  headers: () => ({
    'Cache-Control': 'public, max-age=300, stale-while-revalidate=3600',
  }),
  staleTime: 30_000,
})
```

User-specific pages (no CDN caching):

```tsx
export const Route = createFileRoute('/dashboard')({
  loader: async () => fetchUserData(),
  headers: () => ({
    'Cache-Control': 'private, max-age=60',
  }),
  staleTime: 30_000,
})
```

## Deployment Targets

### Cloudflare Workers (Official Partner)

Install dependencies:

```bash
pnpm add -D @cloudflare/vite-plugin wrangler
```

Vite configuration:

```tsx
// vite.config.ts
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { cloudflare } from '@cloudflare/vite-plugin'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    cloudflare({ viteEnvironment: { name: 'ssr' } }),
    tanstackStart(),
    viteReact(),
  ],
})
```

Wrangler config (`wrangler.jsonc`):

```json
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "tanstack-start-app",
  "compatibility_date": "2025-09-02",
  "compatibility_flags": ["nodejs_compat"],
  "main": "@tanstack/react-start/server-entry"
}
```

Package scripts:

```json
{
  "scripts": {
    "dev": "vite dev",
    "build": "vite build && tsc --noEmit",
    "preview": "vite preview",
    "deploy": "npm run build && wrangler deploy"
  }
}
```

### Netlify (Official Partner)

Install the plugin:

```bash
pnpm add -D @netlify/vite-plugin-tanstack-start
```

Vite configuration:

```tsx
// vite.config.ts
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import netlify from '@netlify/vite-plugin-tanstack-start'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    tanstackStart(),
    netlify(),
    viteReact(),
  ],
})
```

Deploy:

```bash
npx netlify deploy
```

Optional `netlify.toml`:

```toml
[build]
  command = "vite build"
  publish = "dist/client"
[dev]
  command = "vite dev"
  port = 3000
```

### Railway (Official Partner)

Railway provides zero-config deployment. Follow the Nitro setup, then:

1. Push code to a GitHub repository
2. Connect the repository at railway.com
3. Railway auto-detects build settings and deploys

Railway provides automatic deployments on push, built-in databases, preview environments for PRs, automatic HTTPS, and custom domains.

### Nitro (Multi-Target)

Nitro is an agnostic deployment layer supporting a wide range of hosting providers.

Install nitro nightly in `package.json`:

```json
{
  "dependencies": {
    "nitro": "npm:nitro-nightly@latest"
  }
}
```

Vite configuration:

```tsx
// vite.config.ts
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { nitro } from 'nitro/vite'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [tanstackStart(), nitro(), viteReact()],
})
```

#### FastResponse for Node.js

When deploying to Node.js with Nitro, replace the global `Response` with srvx's optimized `FastResponse` for approximately 5% throughput improvement:

```bash
npm install srvx
```

```tsx
// src/server.ts
import { FastResponse } from 'srvx'
globalThis.Response = FastResponse

import handler, { createServerEntry } from '@tanstack/react-start/server-entry'

export default createServerEntry({
  fetch(request) {
    return handler.fetch(request)
  },
})
```

### Vercel

Follow the Nitro setup. Deploy via Vercel's one-click deployment or CLI.

### Node.js / Docker

Follow the Nitro setup. Package scripts:

```json
{
  "scripts": {
    "build": "vite build",
    "start": "node .output/server/index.mjs"
  }
}
```

### Bun

Requires React 19+. Follow the Nitro setup with the `bun` preset:

```tsx
// vite.config.ts
import { defineConfig } from 'vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import { nitro } from 'nitro/vite'
import viteReact from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [tanstackStart(), nitro({ preset: 'bun' }), viteReact()],
})
```

Build and run:

```bash
bun run build
bun run .output/server/index.mjs
```

## Entry Points

Both entry points are optional. TanStack Start provides defaults if they are not present.

### Server Entry Point (src/server.ts)

The server entry point uses the universal fetch handler format (WinterCG-compatible).

Default implementation:

```tsx
// src/server.ts
import handler, { createServerEntry } from '@tanstack/react-start/server-entry'

export default createServerEntry({
  fetch(request) {
    return handler.fetch(request)
  },
})
```

Custom server handler with additional logic:

```tsx
// src/server.ts
import {
  createStartHandler,
  defaultStreamHandler,
  defineHandlerCallback,
} from '@tanstack/react-start/server'
import { createServerEntry } from '@tanstack/react-start/server-entry'

const customHandler = defineHandlerCallback((ctx) => {
  // Custom logic before rendering
  return defaultStreamHandler(ctx)
})

const fetch = createStartHandler(customHandler)

export default createServerEntry({
  fetch,
})
```

#### Typed Request Context

Pass typed data through the request lifecycle via module augmentation:

```tsx
// src/server.ts
import handler, { createServerEntry } from '@tanstack/react-start/server-entry'

type MyRequestContext = {
  hello: string
  foo: number
}

declare module '@tanstack/react-start' {
  interface Register {
    server: {
      requestContext: MyRequestContext
    }
  }
}

export default createServerEntry({
  async fetch(request) {
    return handler.fetch(request, { context: { hello: 'world', foo: 123 } })
  },
})
```

The registered context is available throughout global middleware, request/function middleware, server routes, server functions, and the router.

### Client Entry Point (src/client.tsx)

Hydrates the server-rendered HTML into an interactive application.

Default implementation:

```tsx
// src/client.tsx
import { StartClient } from '@tanstack/react-start/client'
import { StrictMode } from 'react'
import { hydrateRoot } from 'react-dom/client'

hydrateRoot(
  document,
  <StrictMode>
    <StartClient />
  </StrictMode>,
)
```

With error boundary:

```tsx
// src/client.tsx
import { StartClient } from '@tanstack/react-start/client'
import { StrictMode } from 'react'
import { hydrateRoot } from 'react-dom/client'
import { ErrorBoundary } from './components/ErrorBoundary'

hydrateRoot(
  document,
  <StrictMode>
    <ErrorBoundary>
      <StartClient />
    </ErrorBoundary>
  </StrictMode>,
)
```

## Environment Variables

### Client vs Server Access

| Prefix | Accessible Where | Access Pattern |
|--------|-----------------|----------------|
| `VITE_` | Client + Server | `import.meta.env.VITE_*` |
| No prefix | Server only | `process.env.*` |

```tsx
// Server function - access any variable
const getUser = createServerFn().handler(async () => {
  const db = await connect(process.env.DATABASE_URL) // Server-only, no prefix
  return db.user.findFirst()
})

// Client component - only VITE_ prefixed variables
function AppHeader() {
  return <h1>{import.meta.env.VITE_APP_NAME}</h1>
}
```

### .env File Hierarchy

Files are loaded in this order (later files override earlier ones):

```
.env                # Default variables (commit to git)
.env.development    # Development-specific
.env.production     # Production-specific
.env.local          # Local overrides (add to .gitignore)
```

### Type Safety for Environment Variables

```tsx
// src/env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_NAME: string
  readonly VITE_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare global {
  namespace NodeJS {
    interface ProcessEnv {
      readonly DATABASE_URL: string
      readonly JWT_SECRET: string
    }
  }
}

export {}
```

### Runtime Client Environment Variables

`VITE_` variables are replaced at build time. For runtime variables on the client, pass them from the server via a loader:

```tsx
const getRuntimeVar = createServerFn({ method: 'GET' }).handler(() => {
  return process.env.MY_RUNTIME_VAR
})

export const Route = createFileRoute('/')({
  loader: async () => {
    const runtimeValue = await getRuntimeVar()
    return { runtimeValue }
  },
  component: RouteComponent,
})

function RouteComponent() {
  const { runtimeValue } = Route.useLoaderData()
  // Use the runtime variable
}
```

## Route-Level Headers

The `headers` property on a route sets response headers. This is the primary mechanism for cache control, ISR, and custom headers:

```tsx
export const Route = createFileRoute('/products/$id')({
  loader: async ({ params }) => fetchProduct(params.id),
  headers: () => ({
    'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
    'X-Custom-Header': 'my-value',
  }),
  component: ProductPage,
})
```

Headers can also be dynamic based on loader data or other runtime state.

## Best Practices

### 1. Use Full SSR for SEO-Critical Pages

Content pages, blog posts, product pages, and landing pages should use `ssr: true` (the default) so crawlers receive complete HTML.

### 2. Use ssr: false for Authenticated Dashboards

User dashboards, admin panels, and account settings rarely need SEO. Disabling SSR avoids serializing user data in the initial HTML and simplifies hydration.

```tsx
export const Route = createFileRoute('/dashboard')({
  ssr: false,
  pendingComponent: DashboardSkeleton,
  loader: () => fetchDashboardData(),
  component: Dashboard,
})
```

### 3. Use ssr: 'data-only' for Browser-API-Dependent Components

When you need server-fetched data but the component itself requires browser APIs (canvas, WebGL, etc.), use `'data-only'` to get server data performance without SSR rendering issues.

### 4. Combine Static Prerendering with ISR

Prerender at build time for instant first loads, then use `Cache-Control` headers for ongoing freshness. This gives the best of both worlds - fast initial deployment and automatic content updates.

### 5. Start with Conservative Cache Times

Begin with shorter cache durations and increase as you understand your content update patterns:

```tsx
// Start conservative
headers: () => ({
  'Cache-Control': 'public, max-age=300, stale-while-revalidate=600',
})

// Increase after monitoring
headers: () => ({
  'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
})
```

### 6. Keep Secrets Server-Side

Never use `VITE_` prefix for sensitive values. Access secrets via `process.env` inside server functions:

```tsx
// WRONG: secret in client bundle
const key = import.meta.env.VITE_SECRET_KEY

// CORRECT: secret stays on server
const getData = createServerFn().handler(async () => {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${process.env.SECRET_KEY}` },
  })
  return response.json()
})
```

### 7. Use SPA Mode for Internal Tools

Internal dashboards, admin tools, and other apps without SEO requirements benefit from SPA mode's simpler deployment and lower hosting costs.

### 8. Always Provide pendingComponent for Non-SSR Routes

Routes with `ssr: false` or `ssr: 'data-only'` should define a `pendingComponent` to avoid blank screens during client-side loading.

## Official Documentation

- [Selective SSR](https://tanstack.com/start/latest/docs/framework/react/selective-ssr)
- [SPA Mode](https://tanstack.com/start/latest/docs/framework/react/spa-mode)
- [Static Prerendering](https://tanstack.com/start/latest/docs/framework/react/static-prerendering)
- [ISR](https://tanstack.com/start/latest/docs/framework/react/isr)
- [Hosting](https://tanstack.com/start/latest/docs/framework/react/hosting)
- [Server Entry Point](https://tanstack.com/start/latest/docs/framework/react/server-entry-point)
- [Client Entry Point](https://tanstack.com/start/latest/docs/framework/react/client-entry-point)
- [Environment Variables](https://tanstack.com/start/latest/docs/framework/react/environment-variables)
- [Execution Model](https://tanstack.com/start/latest/docs/framework/react/execution-model)
