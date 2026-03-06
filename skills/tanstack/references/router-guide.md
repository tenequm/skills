
# TanStack Router v1

A fully type-safe router for React with first-class search param APIs, built-in data loading with SWR caching, file-based route generation, and 100% inferred TypeScript support.

## When to Use This Skill

- Setting up file-based or code-based routing in a React application
- Building type-safe navigation with Link, useNavigate, or router.navigate
- Validating and managing URL search params as typed state
- Loading data in route loaders with SWR caching
- Code splitting routes for optimal bundle size
- Handling not-found errors and error boundaries per route
- Implementing route context for dependency injection
- Configuring preloading strategies (intent, viewport, render)
- Integrating TanStack Query with route loaders
- Adding navigation blocking for unsaved changes
- Building SSR applications (for full SSR, see `start-guide.md`)

## Quick Start Workflow

### 1. Install and Configure (Vite)

```bash
npm install @tanstack/react-router @tanstack/router-plugin
```

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  plugins: [
    tanstackRouter({ autoCodeSplitting: true }),
    react(),
  ],
})
```

### 2. Create Routes

```tsx
// src/routes/__root.tsx
import { createRootRoute, Link, Outlet } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: () => (
    <>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/about">About</Link>
      </nav>
      <Outlet />
    </>
  ),
})
```

```tsx
// src/routes/index.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: () => <div>Welcome Home</div>,
})
```

### 3. Create and Register the Router

```tsx
// src/router.ts
import { createRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
```

```tsx
// src/main.tsx
import { RouterProvider } from '@tanstack/react-router'
import { router } from './router'

function App() {
  return <RouterProvider router={router} />
}
```

## File-Based Routing

Files in `src/routes/` are automatically converted to route configuration by the Vite plugin or CLI.

### Naming Conventions

| Convention | Purpose | Example |
|---|---|---|
| `__root.tsx` | Root route (always rendered) | `src/routes/__root.tsx` |
| `index.tsx` | Index route for parent path | `src/routes/index.tsx` matches `/` |
| `.` separator | Nested route (flat files) | `posts.tsx` = `/posts` |
| `$param` | Dynamic path parameter | `posts.$postId.tsx` = `/posts/:postId` |
| `_` prefix | Pathless layout route | `_layout.tsx` wraps children, no URL segment |
| `_` suffix | Non-nested route | `posts_.edit.tsx` breaks out of `posts` nesting |
| `-` prefix | Excluded from routing | `-components/Button.tsx` for colocated files |
| `(folder)` | Route group (no URL segment) | `(auth)/login.tsx` = `/login` |
| `.lazy.tsx` | Lazy-loaded component | `posts.lazy.tsx` for code-split components |
| `.route.tsx` | Directory route file | `posts/route.tsx` instead of `posts.tsx` |

Flat (`posts.$postId.tsx`) and directory (`posts/$postId.tsx`) structures can be mixed freely.

## Type-Safe Navigation

All navigation APIs share `to`, `from`, `params`, `search`, and `hash` options.

### Link Component

```tsx
import { Link } from '@tanstack/react-router'

<Link to="/posts/$postId" params={{ postId: '123' }}>View Post</Link>

// Relative navigation
<Link from="/posts/$postId" to="..">Back to Posts</Link>

// Active styling
<Link to="/posts" activeProps={{ className: 'font-bold' }} activeOptions={{ exact: true }}>
  Posts
</Link>
```

### useNavigate Hook

For imperative navigation from side effects:

```tsx
const navigate = useNavigate({ from: '/posts' })

const handleSubmit = async (data: PostInput) => {
  const post = await createPost(data)
  navigate({ to: '/posts/$postId', params: { postId: post.id } })
}
```

### linkOptions Helper

Reusable type-safe link configuration:

```tsx
import { linkOptions } from '@tanstack/react-router'

const postLink = linkOptions({ to: '/posts/$postId', params: { postId: '123' } })
<Link {...postLink}>View Post</Link>
```

Always provide `from` on Link and hooks to narrow types and improve TS performance. Without `from`, TypeScript must check against all routes.

## Search Params

Search params are first-class - validated, typed, JSON-serialized, and subscribable with fine-grained selectors.

### Validation with Zod

```tsx
import { zodValidator, fallback } from '@tanstack/zod-adapter'
import { z } from 'zod'

const productSearchSchema = z.object({
  page: fallback(z.number(), 1).default(1),
  filter: fallback(z.string(), '').default(''),
  sort: fallback(z.enum(['newest', 'oldest', 'price']), 'newest').default('newest'),
})

export const Route = createFileRoute('/shop/products')({
  validateSearch: zodValidator(productSearchSchema),
})
```

Use `fallback(...).default(...)` from the Zod adapter to retain types. Plain `.catch()` causes type loss. Valibot and ArkType work without adapters via Standard Schema support.

### Reading and Writing

```tsx
// Reading (type-safe)
const { page, sort } = Route.useSearch()
// From code-split component (avoids circular imports)
const search = getRouteApi('/shop/products').useSearch()
// Loose typing for shared components
const search = useSearch({ strict: false })

// Writing via Link
<Link from={Route.fullPath} search={(prev) => ({ ...prev, page: prev.page + 1 })}>Next</Link>
// Writing via useNavigate
const navigate = useNavigate({ from: Route.fullPath })
navigate({ search: (prev) => ({ ...prev, page: 2 }) })
```

### Search Middlewares

```tsx
import { retainSearchParams, stripSearchParams } from '@tanstack/react-router'

export const Route = createFileRoute('/shop/products')({
  validateSearch: zodValidator(productSearchSchema),
  search: {
    middlewares: [
      retainSearchParams(['globalFilter']),
      stripSearchParams({ sort: 'newest' }),
    ],
  },
})
```

## Data Loading

Route loaders run in parallel before rendering with built-in SWR caching.

### Basic Loader

```tsx
export const Route = createFileRoute('/posts')({
  loader: () => fetchPosts(),
  component: () => {
    const posts = Route.useLoaderData()
    return <ul>{posts.map(p => <li key={p.id}>{p.title}</li>)}</ul>
  },
})
```

### loaderDeps - Search Params as Cache Keys

```tsx
export const Route = createFileRoute('/posts')({
  validateSearch: z.object({ page: z.number().catch(1), limit: z.number().catch(10) }),
  loaderDeps: ({ search: { page, limit } }) => ({ page, limit }),
  loader: ({ deps: { page, limit } }) => fetchPosts({ page, limit }),
})
```

Only include deps you actually use - returning the entire `search` object causes unnecessary cache invalidation.

### Caching and Staleness

- `staleTime` - How long data is fresh (default: 0 for navigation, 30s for preload)
- `gcTime` - How long unused data stays in cache (default: 30 minutes)
- `shouldReload` - Custom reload logic beyond staleTime

### beforeLoad - Guards and Context

Runs serially before loaders. Use for auth redirects or injecting route-specific context:

```tsx
export const Route = createFileRoute('/dashboard')({
  beforeLoad: ({ context }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({ to: '/login', search: { redirect: '/dashboard' } })
    }
    return { user: context.auth.user }
  },
  loader: ({ context: { user } }) => fetchDashboard(user.id),
})
```

### Pending Components

```tsx
export const Route = createFileRoute('/posts')({
  loader: () => fetchPosts(),
  pendingComponent: () => <Spinner />,
  pendingMs: 1000,     // Wait before showing (default: 1000)
  pendingMinMs: 500,   // Minimum display time to avoid flash (default: 500)
})
```

## Route Context

Hierarchical dependency injection via `createRootRouteWithContext`. Context merges down the tree and is fully type-safe.

```tsx
// src/routes/__root.tsx
import { createRootRouteWithContext } from '@tanstack/react-router'

interface RouterContext { queryClient: QueryClient }

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
})

// src/router.ts - context is required by the type
const router = createRouter({ routeTree, context: { queryClient } })

// Child routes access context in loaders
export const Route = createFileRoute('/posts')({
  loader: ({ context: { queryClient } }) => queryClient.ensureQueryData(postsQueryOptions()),
})
```

Pass React hooks/state at runtime via `RouterProvider`:

```tsx
function App() {
  const auth = useAuth()
  return <RouterProvider router={router} context={{ auth }} />
}
```

## Error Handling

### errorComponent

```tsx
export const Route = createFileRoute('/posts/$postId')({
  loader: ({ params }) => fetchPost(params.postId),
  errorComponent: ({ error }) => {
    const router = useRouter()
    return (
      <div>
        <p>{error.message}</p>
        <button onClick={() => router.invalidate()}>Retry</button>
      </div>
    )
  },
})
```

### notFoundComponent

Two modes via `notFoundMode` on the router (default: `'fuzzy'`):
- **fuzzy** - nearest parent route with children and a notFoundComponent handles it
- **root** - root route always handles it

```tsx
import { notFound } from '@tanstack/react-router'

export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params }) => {
    const post = await getPost(params.postId)
    if (!post) throw notFound()
    return { post }
  },
  notFoundComponent: () => <p>Post not found</p>,
})
```

Set `defaultNotFoundComponent` on the router for app-wide fallback.

## Code Splitting

**Automatic (recommended):** Enable `autoCodeSplitting: true` in the Vite plugin. Non-critical config (component, errorComponent, pendingComponent, notFoundComponent) is split into separate chunks automatically.

**Manual with .lazy.tsx:** Split into two files - critical config in `posts.tsx` (loader, validateSearch), non-critical in `posts.lazy.tsx` (component via `createLazyFileRoute`).

The root route (`__root.tsx`) does not support code splitting since it always renders.

## Preloading

```tsx
const router = createRouter({
  routeTree,
  defaultPreload: 'intent',   // Preload on hover/touch
  defaultPreloadDelay: 50,     // ms delay (default: 50)
})
```

Strategies: `'intent'` (hover/touch), `'viewport'` (Intersection Observer), `'render'` (on mount). Override per-link with `preload` prop. Manual: `router.preloadRoute({ to, params })`.

## TanStack Query Integration

```tsx
const postQueryOptions = (postId: string) =>
  queryOptions({ queryKey: ['post', postId], queryFn: () => fetchPost(postId) })

export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ context: { queryClient }, params: { postId } }) => {
    await queryClient.ensureQueryData(postQueryOptions(postId))
  },
  component: () => {
    const { postId } = Route.useParams()
    const { data } = useSuspenseQuery(postQueryOptions(postId))
    return <div>{data.title}</div>
  },
})
```

Set `defaultPreloadStaleTime: 0` on the router when using external caching so loaders always fire.

## Advanced Topics

See reference files for deep dives:
- `search-params.md` - Custom serialization, Standard Schema validation, arrays/objects, sharing across routes
- `data-loading.md` - Deferred data loading with Await, external data loading, shouldReload, streaming SSR
- `routing-patterns.md` - Virtual file routes, route masking, navigation blocking, authenticated routes, parallel routes
- `code-splitting.md` - Automatic splitting options, loader splitting, directory encapsulation, code-based splitting
- `router-ssr.md` - SSR setup, streaming, dehydration/hydration, data serialization, TanStack Start integration

## DevTools

```bash
npm install @tanstack/react-router-devtools
```

```tsx
// src/routes/__root.tsx
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'

export const Route = createRootRoute({
  component: () => (
    <>
      <Outlet />
      <TanStackRouterDevtools />
    </>
  ),
})
```

Automatically excluded from production. Use `TanStackRouterDevtoolsInProd` if needed in prod.

## Best Practices

1. **Use file-based routing with autoCodeSplitting** - Generates the route tree and optimizes bundles. Fall back to code-based only when you need programmatic control.
2. **Always validate search params** - Use `validateSearch` with Zod (via `zodValidator`) or any Standard Schema library. Use `fallback(...).default(...)` to retain types.
3. **Provide `from` on navigation hooks and components** - Narrows types, improves TS performance, catches route mismatches at runtime.
4. **Extract only needed deps in loaderDeps** - Return only params your loader uses, not the full search object.
5. **Use route context for dependency injection** - Pass QueryClient, auth, or services via `createRootRouteWithContext` instead of importing singletons.
6. **Set preload to 'intent' globally** - Dramatically improves perceived performance with minimal effort.
7. **Use router.invalidate() in error components** - Reloads data and resets the error boundary together.

## Resources

- **Official Docs**: https://tanstack.com/router/latest/docs/framework/react/overview
- **GitHub**: https://github.com/TanStack/router
- **Examples**: https://tanstack.com/router/latest/docs/framework/react/examples
- **Query Integration**: https://tanstack.com/router/latest/docs/router/integrations/query
- **Discord**: https://discord.gg/tanstack
- **Migrate from React Router**: https://tanstack.com/router/latest/docs/framework/react/installation/migrate-from-react-router
