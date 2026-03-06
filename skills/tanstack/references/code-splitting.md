# Code Splitting and Preloading

Optimize TanStack Router applications with code splitting, lazy loading, and preloading for faster initial loads and seamless navigation.

Official docs:
- https://tanstack.com/router/latest/docs/framework/react/guide/code-splitting
- https://tanstack.com/router/latest/docs/framework/react/guide/automatic-code-splitting
- https://tanstack.com/router/latest/docs/framework/react/guide/preloading
- https://tanstack.com/router/latest/docs/framework/react/guide/render-optimizations

## Critical vs Non-Critical Route Configuration

TanStack Router separates route configuration into two categories.

**Critical (always in the main bundle)** - required to match the route and start data loading:

- Path parsing and serialization
- Search parameter validation
- Loaders (`loader`) and before load hooks (`beforeLoad`)
- Route context, static data, styles, scripts, links

**Non-Critical (can be lazy-loaded)** - not required to match the route:

- `component` - the route component
- `errorComponent` - rendered when a loader or component throws
- `pendingComponent` - rendered while the route is loading
- `notFoundComponent` - rendered when a not-found error is thrown

**Why the loader stays in the main bundle:** The loader is already an async boundary, so splitting it adds a second async hop (fetch the chunk, then execute the loader). Loaders are typically smaller than components and are critical for preloading on hover/touch - they must be available without additional async overhead.

## Automatic Code Splitting

Enable it in the bundler plugin and TanStack Router handles everything. Only works with file-based routing and a supported bundler plugin (`@tanstack/router-plugin`), not with the standalone CLI or code-based routing.

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  plugins: [
    tanstackRouter({ autoCodeSplitting: true }),
    react(), // Must come AFTER the TanStack Router plugin
  ],
})
```

The plugin transforms each route file at build time into a **reference file** (original file rewritten with lazy-loading wrappers) and **virtual files** (minimal files containing only the code for a single property like `component`).

### Default Split Groupings

Three separate lazy-loaded chunks are created per route by default:

```ts
[['component'], ['errorComponent'], ['notFoundComponent']]
```

The `pendingComponent` and `loader` remain in the main bundle.

### Customizing Split Groupings

**Global default behavior** - bundle all UI components into one chunk:

```ts
// vite.config.ts
tanstackRouter({
  autoCodeSplitting: true,
  codeSplittingOptions: {
    defaultBehavior: [
      ['component', 'pendingComponent', 'errorComponent', 'notFoundComponent'],
    ],
  },
})
```

**Programmatic per-route-id control** with `splitBehavior`:

```ts
tanstackRouter({
  autoCodeSplitting: true,
  codeSplittingOptions: {
    splitBehavior: ({ routeId }) => {
      if (routeId.startsWith('/admin')) {
        return [['loader', 'component']]
      }
      // All other routes use the defaultBehavior
    },
  },
})
```

**Per-route override** with `codeSplitGroupings` inside the route file:

```tsx
// src/routes/posts.tsx
export const Route = createFileRoute('/posts')({
  codeSplitGroupings: [['loader', 'component']],
  loader: () => fetchPosts(),
  component: PostsComponent,
})

function PostsComponent() {
  const posts = Route.useLoaderData()
  return <ul>{posts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
}
```

**Precedence order:** Per-route `codeSplitGroupings` (highest) > `splitBehavior` function > `defaultBehavior` (lowest).

### Splitting the Data Loader (Automatic)

Introduces an extra network round trip. Only recommended when a route's loader is unusually large:

```ts
tanstackRouter({
  autoCodeSplitting: true,
  codeSplittingOptions: {
    defaultBehavior: [['loader'], ['component'], ['errorComponent'], ['notFoundComponent']],
  },
})
```

### Rules for Automatic Code Splitting

Do not export route properties. Exporting prevents the bundler from splitting them:

```tsx
export const Route = createFileRoute('/posts')({ component: PostsComponent })

// BAD - exporting prevents code splitting
export function PostsComponent() { return <div>Posts</div> }

// GOOD - keep it as a local function
function PostsComponent() { return <div>Posts</div> }
```

## Manual Code Splitting with .lazy.tsx

Use the `.lazy.tsx` convention when you cannot use automatic code splitting. The root route (`__root.tsx`) does not support code splitting.

Split a route into two files - main for critical config, `.lazy.tsx` for non-critical:

```tsx
// src/routes/posts.tsx - critical configuration
import { createFileRoute } from '@tanstack/react-router'
import { fetchPosts } from '../api'

export const Route = createFileRoute('/posts')({
  loader: fetchPosts,
})
```

```tsx
// src/routes/posts.lazy.tsx - non-critical (lazy-loaded)
import { createLazyFileRoute } from '@tanstack/react-router'

export const Route = createLazyFileRoute('/posts')({
  component: Posts,
})

function Posts() {
  const posts = Route.useLoaderData()
  return <ul>{posts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
}
```

`createLazyFileRoute` only supports: `component`, `errorComponent`, `pendingComponent`, `notFoundComponent`. Everything else must stay in the main route file.

### Multiple Non-Critical Properties

```tsx
// src/routes/dashboard.lazy.tsx
import { createLazyFileRoute } from '@tanstack/react-router'

export const Route = createLazyFileRoute('/dashboard')({
  component: Dashboard,
  errorComponent: DashboardError,
  pendingComponent: () => <div>Loading dashboard...</div>,
  notFoundComponent: () => <div>Dashboard not found</div>,
})

function Dashboard() { return <div>Dashboard content</div> }
function DashboardError({ error }: { error: Error }) { return <div>Error: {error.message}</div> }
```

### Virtual Routes

If a main route file becomes empty, delete it. TanStack Router generates a virtual route in the route tree:

```tsx
// src/routes/about.lazy.tsx (no src/routes/about.tsx needed)
import { createLazyFileRoute } from '@tanstack/react-router'

export const Route = createLazyFileRoute('/about')({
  component: () => <div>About page</div>,
})
```

### Directory Encapsulation

Move route files into a directory for organization. Behavior is identical:

```
src/routes/posts/route.tsx       # was posts.tsx
src/routes/posts/route.lazy.tsx  # was posts.lazy.tsx
```

## Code-Based Route Splitting

For code-based routing, use `createLazyRoute` and the `.lazy()` method:

```tsx
// src/posts.lazy.tsx
import { createLazyRoute } from '@tanstack/react-router'

export const Route = createLazyRoute('/posts')({
  component: () => <div>Posts</div>,
})
```

```tsx
// src/app.tsx
const postsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/posts',
  loader: () => fetchPosts(),
}).lazy(() => import('./posts.lazy').then((d) => d.Route))
```

**Manual loader splitting** with `lazyFn`:

```tsx
import { createRoute, lazyFn } from '@tanstack/react-router'

const postsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/posts',
  loader: lazyFn(() => import('./posts-loader'), 'loader'),
})
```

```tsx
// src/posts-loader.ts
import type { LoaderContext } from '@tanstack/react-router'

export const loader = async (context: LoaderContext) => {
  const response = await fetch('/api/posts')
  return response.json()
}
```

## Accessing Route APIs from Split Files

Use `getRouteApi` for type-safe access to route hooks without importing the route:

```tsx
import { getRouteApi } from '@tanstack/react-router'

const postsRoute = getRouteApi('/posts')

export function PostsPage() {
  const loaderData = postsRoute.useLoaderData()
  const search = postsRoute.useSearch()
  const params = postsRoute.useParams()
  return <div>{/* render */}</div>
}
```

Available hooks: `useLoaderData`, `useSearch`, `useParams`, `useRouteContext`, `useMatch`, `useLoaderDeps`.

## Preloading Strategies

Preloading loads a route's code and data before the user navigates to it.

**Intent** (recommended default) - preloads on hover/touch of a `<Link>`:

```tsx
const router = createRouter({ routeTree, defaultPreload: 'intent' })
```

**Viewport** - uses Intersection Observer to preload when a `<Link>` scrolls into view:

```tsx
<Link to="/posts" preload="viewport">Posts</Link>
```

**Render** - preloads as soon as the `<Link>` mounts in the DOM:

```tsx
<Link to="/settings" preload="render">Settings</Link>
```

## Preload Configuration

### Router-Level Defaults

```tsx
const router = createRouter({
  routeTree,
  defaultPreload: 'intent',           // 'intent' | 'viewport' | 'render' | false
  defaultPreloadDelay: 50,             // ms before preloading starts (default: 50)
  defaultPreloadStaleTime: 30_000,     // ms before preloaded data is re-fetched (default: 30_000)
  defaultPreloadMaxAge: 30_000,        // ms before unused preloaded data is removed (default: 30_000)
})
```

### Per-Link Overrides

```tsx
<Link to="/posts/$postId" params={{ postId: post.id }} preload="intent" preloadDelay={100}>
  {post.title}
</Link>
```

### Per-Route Stale Time

```tsx
// src/routes/posts.$postId.tsx
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params }) => fetchPost(params.postId),
  preloadStaleTime: 10_000, // Re-preload if older than 10s
})
```

### Disabling Preloading

```tsx
<Link to="/expensive-route" preload={false}>Expensive Route</Link>
```

### Preloading with External Libraries

When using TanStack Query alongside TanStack Router, set `defaultPreloadStaleTime: 0` so React Query manages cache freshness:

```tsx
const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
  defaultPreloadStaleTime: 0, // Let React Query handle stale/fresh decisions
})
```

## Manual Preloading

**`router.preloadRoute()`** - preload a route's code and data programmatically:

```tsx
function Component() {
  const router = useRouter()

  useEffect(() => {
    router.preloadRoute({
      to: '/posts/$postId',
      params: { postId: '1' },
    }).catch(() => { /* preload is best-effort */ })
  }, [router])

  return <div />
}
```

**`router.loadRouteChunk()`** - load only the JS chunk without executing the loader:

```tsx
function AppShell() {
  const router = useRouter()

  useEffect(() => {
    Promise.all([
      router.loadRouteChunk(router.routesByPath['/dashboard']),
      router.loadRouteChunk(router.routesByPath['/settings']),
    ]).catch(() => {})
  }, [router])

  return <div>{/* app content */}</div>
}
```

## Render Optimizations

### Structural Sharing

TanStack Router preserves referential identity for unchanged parts of URL-derived state. Navigating from `/details?foo=f1&bar=b1` to `/details?foo=f1&bar=b2`:

- `search.foo` retains the same reference (referentially stable)
- Only `search.bar` is replaced

### Fine-Grained Selectors with select

Subscribe to a specific subset so the component only re-renders when that subset changes:

```tsx
function DetailsPage() {
  // Only re-renders when foo changes, not when bar changes
  const foo = Route.useSearch({ select: (search) => search.foo })
  return <div>Foo: {foo}</div>
}
```

### Structural Sharing with Selectors

When `select` returns a new object, the component re-renders every time. Enable structural sharing to preserve referential stability:

```tsx
// Enable globally
const router = createRouter({ routeTree, defaultStructuralSharing: true })

// Or per hook
const result = Route.useSearch({
  select: (search) => ({ foo: search.foo, greeting: `hello ${search.foo}` }),
  structuralSharing: true,
})
```

**Constraint:** Structural sharing only works with JSON-compatible data. Class instances, Dates, Maps, and Sets are not supported. TypeScript will error if you return non-JSON values with `structuralSharing: true`. Disable it per hook with `structuralSharing: false`.

## Common Patterns

### Lazy-Loading a Heavy Component

Keep the route lean, push heavy dependencies into the lazy file:

```tsx
// src/routes/analytics.tsx
export const Route = createFileRoute('/analytics')({
  validateSearch: (s: Record<string, unknown>) => ({ range: (s.range as string) || '7d' }),
  loader: ({ context }) => context.api.fetchAnalytics(),
})
```

```tsx
// src/routes/analytics.lazy.tsx
import { createLazyFileRoute } from '@tanstack/react-router'
import { BarChart, LineChart, PieChart } from 'recharts' // Heavy - only loaded when needed

export const Route = createLazyFileRoute('/analytics')({
  component: AnalyticsDashboard,
  pendingComponent: () => <div>Loading analytics...</div>,
})

function AnalyticsDashboard() {
  const data = Route.useLoaderData()
  return (
    <div>
      <LineChart data={data.revenue} />
      <BarChart data={data.signups} />
      <PieChart data={data.sources} />
    </div>
  )
}
```

### Preloading on Hover for List-to-Detail Navigation

```tsx
function PostCard({ post }: { post: Post }) {
  return (
    <Link to="/posts/$postId" params={{ postId: post.id }} preload="intent" preloadDelay={75}>
      <h3>{post.title}</h3>
      <p>{post.excerpt}</p>
    </Link>
  )
}
```

### Prefetching the Next Page in Pagination

```tsx
export const Route = createFileRoute('/items')({
  validateSearch: (s: Record<string, unknown>) => ({ page: Number(s.page) || 1 }),
  loaderDeps: ({ search }) => ({ page: search.page }),
  loader: async ({ deps }) => fetchItems(deps.page),
  component: ItemsList,
})

function ItemsList() {
  const router = useRouter()
  const items = Route.useLoaderData()
  const { page } = Route.useSearch()

  useEffect(() => {
    if (items.hasNextPage) {
      router.preloadRoute({ to: '/items', search: { page: page + 1 } })
    }
  }, [router, page, items.hasNextPage])

  return (
    <div>
      <ul>{items.data.map((item) => <li key={item.id}>{item.name}</li>)}</ul>
      <Link to="/items" search={{ page: page - 1 }} disabled={page === 1}>Previous</Link>
      <Link to="/items" search={{ page: page + 1 }} disabled={!items.hasNextPage}>Next</Link>
    </div>
  )
}
```

### Preloading Critical Routes on App Startup

```tsx
function AppLayout() {
  const router = useRouter()

  useEffect(() => {
    Promise.all([
      router.loadRouteChunk(router.routesByPath['/dashboard']),
      router.loadRouteChunk(router.routesByPath['/settings']),
    ]).catch(() => {})
  }, [router])

  return <div><Sidebar /><main><Outlet /></main></div>
}
```

## Best Practices

1. **Start with automatic code splitting.** Set `autoCodeSplitting: true` in the Vite plugin. It handles the common case with zero route file changes. Only reach for manual `.lazy.tsx` splitting if you cannot use the bundler plugin.

2. **Keep loaders in the main bundle.** The double async hop from splitting a loader outweighs bundle size savings in most cases. The loader is critical for preloading performance.

3. **Enable intent preloading globally.** Setting `defaultPreload: 'intent'` is the single highest-impact preloading optimization. It eliminates perceived loading for most click-driven navigations.

4. **Do not export route properties.** Exporting `component`, `errorComponent`, or other split-eligible properties prevents the bundler from extracting them into separate chunks.

5. **Use `getRouteApi` in split files.** Access `useLoaderData`, `useSearch`, and `useParams` from `.lazy.tsx` files without importing the route definition directly.

6. **Set `defaultPreloadStaleTime: 0` with TanStack Query.** Defers cache freshness decisions to React Query's `staleTime`, avoiding double-caching between the router and the query library.

7. **Prefetch the next page in paginated views.** Call `router.preloadRoute()` with the next page's search params on render. Forward pagination becomes instant.
