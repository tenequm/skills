# Data Loading

TanStack Router provides a built-in data loading system with route loaders, SWR caching, and deep integration points for external libraries like TanStack Query.

Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/data-loading

## Route Loaders

The `loader` function is the primary mechanism for loading data. It runs before the route component renders and receives a single object parameter.

### Loader Function Signature

```tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/posts')({
  loader: async ({
    params,             // Route path params (e.g., { postId: '1' })
    deps,               // Object from loaderDeps, or {} if not defined
    context,            // Merged route context (parent + beforeLoad)
    abortController,    // Cancelled on unload or outdated invocation
    preload,            // true when preloading instead of loading
    cause,              // 'enter' | 'stay' | 'preload'
    location,           // Current location object
    route,              // The route object itself
    parentMatchPromise, // Promise for parent match (undefined for root)
  }) => {
    return await fetchPosts()
  },
})
```

### Basic Examples

```tsx
// Simple data fetch
export const Route = createFileRoute('/posts')({
  loader: () => fetchPosts(),
})

// Using path params
export const Route = createFileRoute('/posts/$postId')({
  loader: ({ params: { postId } }) => fetchPost(postId),
})

// Using the abort signal
export const Route = createFileRoute('/posts')({
  loader: ({ abortController }) =>
    fetch('/api/posts', { signal: abortController.signal }).then((r) => r.json()),
})

// Conditional logic based on preload
export const Route = createFileRoute('/posts')({
  loader: async ({ preload }) =>
    fetchPosts({ maxAge: preload ? 10_000 : 0 }),
})
```

## Consuming Loader Data

### useLoaderData and getRouteApi

```tsx
export const Route = createFileRoute('/posts')({
  loader: () => fetchPosts(),
  component: PostsComponent,
})

function PostsComponent() {
  // Option 1: directly from Route object
  const posts = Route.useLoaderData()
  return <ul>{posts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
}

// Option 2: getRouteApi - avoids circular imports in deep components
import { getRouteApi } from '@tanstack/react-router'
const routeApi = getRouteApi('/posts')

function PostsList() {
  const posts = routeApi.useLoaderData()
  return <ul>{posts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
}
```

### useRouteContext

Access route context (including data injected via `beforeLoad`):

```tsx
function PostsComponent() {
  const { user, permissions } = Route.useRouteContext()
}
```

## Loader Dependencies (loaderDeps)

`loaderDeps` extracts dependencies from search params to serve as cache keys. When deps change between navigations, the loader re-runs regardless of `staleTime`.

Search params are deliberately not available directly in `loader` - this forces explicit dependency declaration which enables correct caching, prevents preloaded data from overwriting the current view, and ensures unique cache entries per set of dependencies.

```tsx
import { z } from 'zod'

export const Route = createFileRoute('/posts')({
  validateSearch: z.object({
    page: z.number().int().nonnegative().catch(0),
    limit: z.number().int().positive().catch(10),
  }),
  loaderDeps: ({ search: { page, limit } }) => ({ page, limit }),
  loader: ({ deps: { page, limit } }) => fetchPosts({ page, limit }),
})
```

### Common Mistake - Returning the Entire Search Object

```tsx
// BAD - reloads when ANY search param changes, even unused ones
loaderDeps: ({ search }) => search,
loader: ({ deps }) => fetchPosts({ page: deps.page }),

// GOOD - only reload when actually-used params change
loaderDeps: ({ search }) => ({ page: search.page, limit: search.limit }),
loader: ({ deps }) => fetchPosts(deps),
```

Deps are compared using deep equality. Returning extraneous fields causes unnecessary reloads.

## Cache Configuration

The built-in SWR cache is keyed on the route's pathname and `loaderDeps`. Cached data is returned immediately while potentially being refetched in the background.

### Key Options

| Option | Route-Level | Router Default | Default Value | Description |
|--------|------------|----------------|---------------|-------------|
| `staleTime` | `routeOptions.staleTime` | `defaultStaleTime` | `0` | How long (ms) data is fresh for navigations |
| `preloadStaleTime` | `routeOptions.preloadStaleTime` | `defaultPreloadStaleTime` | `30_000` | How long (ms) data is fresh for preloads |
| `gcTime` | `routeOptions.gcTime` | `defaultGcTime` | `1_800_000` (30 min) | How long (ms) unused data stays before GC |
| `shouldReload` | `routeOptions.shouldReload` | - | `undefined` | Boolean or function controlling reload |

### Important Defaults

- `staleTime: 0` - data is always refetched in the background on navigation (SWR).
- `preloadStaleTime: 30_000` - preloaded routes won't re-preload within 30 seconds.
- `gcTime: 1_800_000` - cached data GC'd after 30 minutes of inactivity.
- `router.invalidate()` forces all active loaders to reload and marks all cache as stale.

### Configuring staleTime

```tsx
export const Route = createFileRoute('/posts')({
  loader: () => fetchPosts(),
  staleTime: 10_000,      // fresh for 10 seconds
})

export const Route = createFileRoute('/settings')({
  loader: () => fetchSettings(),
  staleTime: Infinity,    // disable SWR - always fresh once loaded
})

// Or set a global default
const router = createRouter({ routeTree, defaultStaleTime: Infinity })
```

### shouldReload and gcTime for Remix-Style Behavior

Load data only on entry or when deps change (no background refetching):

```tsx
export const Route = createFileRoute('/posts')({
  loaderDeps: ({ search: { page, limit } }) => ({ page, limit }),
  loader: ({ deps }) => fetchPosts(deps),
  gcTime: 0,             // Do not cache after route unmounts
  shouldReload: false,   // Only reload on entry or when deps change
})
```

`shouldReload` can also be a function receiving the same parameters as `loader`:

```tsx
export const Route = createFileRoute('/dashboard')({
  loader: () => fetchDashboardData(),
  shouldReload: ({ cause }) => cause === 'enter',
})
```

## beforeLoad

Runs before `loader` and all child `beforeLoad` functions. Serial and top-down, making it suitable for auth checks, redirects, and context injection.

```
Route Matching (Top-Down, Serial):    1. params.parse  2. validateSearch
Route Pre-Loading (Serial, Top-Down): 3. beforeLoad
Route Loading (Parallel):             4. loader  5. component.preload
```

If `beforeLoad` throws, none of its child routes will attempt to load.

### Auth Guard with Redirect

```tsx
import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async ({ location }) => {
    if (!isAuthenticated()) {
      throw redirect({
        to: '/login',
        search: { redirect: location.href },
      })
    }
  },
})
```

### Injecting Route Context

Return an object from `beforeLoad` to merge into the route's context for `loader` and child routes:

```tsx
export const Route = createFileRoute('/dashboard')({
  beforeLoad: async ({ context }) => {
    const user = await fetchCurrentUser(context.authToken)
    return { user, permissions: user.permissions }
  },
  loader: ({ context: { user, permissions } }) =>
    fetchDashboardData(user.id, permissions),
})
```

### Auth Check with Error Handling

Use `isRedirect()` to distinguish intentional redirects from actual errors in try/catch blocks:

```tsx
import { createFileRoute, redirect, isRedirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async ({ location }) => {
    try {
      const user = await verifySession()
      if (!user) throw redirect({ to: '/login', search: { redirect: location.href } })
      return { user }
    } catch (error) {
      if (isRedirect(error)) throw error     // re-throw intentional redirects
      throw redirect({ to: '/login', search: { redirect: location.href } })
    }
  },
})
```

### Router-Level Context

```tsx
// routes/__root.tsx
import { createRootRouteWithContext } from '@tanstack/react-router'

interface RouterContext {
  queryClient: QueryClient
  auth: AuthState
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootComponent,
})

// router.tsx
const router = createRouter({
  routeTree,
  context: { queryClient, auth: undefined! },
})

// App.tsx - pass dynamic context
function InnerApp() {
  const auth = useAuth()
  return <RouterProvider router={router} context={{ auth }} />
}
```

## Deferred Data Loading

Defer slow non-critical data to render critical content first. Return unawaited promises from the loader.

Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/deferred-data-loading

### Returning Unawaited Promises

```tsx
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params: { postId } }) => {
    const commentsPromise = fetchComments(postId)   // slow - do NOT await
    const post = await fetchPost(postId)             // fast - await

    return { post, deferredComments: commentsPromise }
  },
})
```

### Await Component

Resolve deferred promises using `Await`, which triggers the nearest Suspense boundary:

```tsx
import { Await } from '@tanstack/react-router'
import { Suspense } from 'react'

function PostComponent() {
  const { post, deferredComments } = Route.useLoaderData()

  return (
    <div>
      <h1>{post.title}</h1>
      <Suspense fallback={<div>Loading comments...</div>}>
        <Await promise={deferredComments}>
          {(comments) => (
            <ul>
              {comments.map((c) => <li key={c.id}>{c.body}</li>)}
            </ul>
          )}
        </Await>
      </Suspense>
    </div>
  )
}
```

If the promise rejects, `Await` throws the serialized error to the nearest error boundary. In React 19, you can use the `use()` hook instead.

### SSR Streaming

Deferred data supports server-side streaming:

1. Server renders up to Suspense boundaries and streams initial HTML.
2. Deferred promises are tracked as they resolve on the server.
3. Resolved data is serialized and streamed via inline script tags.
4. Client-side placeholder promises resolve with the streamed data.

See the [SSR Streaming Guide](https://tanstack.com/router/latest/docs/framework/react/guide/ssr) for setup.

### Deferred Data with TanStack Query

Use `prefetchQuery` (no await) for deferred data, `ensureQueryData` (await) for critical data:

```tsx
import { useSuspenseQuery } from '@tanstack/react-query'

const postOptions = (postId: string) => queryOptions({
  queryKey: ['post', postId],
  queryFn: () => fetchPost(postId),
})
const commentsOptions = (postId: string) => queryOptions({
  queryKey: ['comments', postId],
  queryFn: () => fetchComments(postId),
})

export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params: { postId }, context: { queryClient } }) => {
    queryClient.prefetchQuery(commentsOptions(postId))          // deferred
    await queryClient.ensureQueryData(postOptions(postId))      // critical
  },
  component: PostComponent,
})

function PostComponent() {
  const { postId } = Route.useParams()
  const { data: post } = useSuspenseQuery(postOptions(postId))
  return (
    <div>
      <h1>{post.title}</h1>
      <Suspense fallback={<div>Loading comments...</div>}>
        <Comments postId={postId} />
      </Suspense>
    </div>
  )
}

function Comments({ postId }: { postId: string }) {
  const { data: comments } = useSuspenseQuery(commentsOptions(postId))
  return <ul>{comments.map((c) => <li key={c.id}>{c.body}</li>)}</ul>
}
```

## External Data Loading - TanStack Query Integration

TanStack Query is the most common integration. The router coordinates when to fetch; TanStack Query handles caching, deduplication, and background refetching.

Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/external-data-loading

### Router Setup

Set `defaultPreloadStaleTime: 0` so every event passes through to your external library:

```tsx
const router = createRouter({
  routeTree,
  defaultPreloadStaleTime: 0,
  context: { queryClient },
})
```

### ensureQueryData Pattern

```tsx
import { queryOptions, useSuspenseQuery } from '@tanstack/react-query'

const postsQueryOptions = queryOptions({
  queryKey: ['posts'],
  queryFn: () => fetchPosts(),
})

export const Route = createFileRoute('/posts')({
  loader: ({ context: { queryClient } }) =>
    queryClient.ensureQueryData(postsQueryOptions),
  component: () => {
    const { data: posts } = useSuspenseQuery(postsQueryOptions)
    return <ul>{posts.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
  },
})
```

### Full SSR Setup

For SSR, use `dehydrate`/`hydrate` options on the router to shuttle TanStack Query state between server and client:

```tsx
import { QueryClient, QueryClientProvider, dehydrate, hydrate } from '@tanstack/react-query'

export function createAppRouter() {
  const queryClient = new QueryClient()
  return createRouter({
    routeTree,
    defaultPreloadStaleTime: 0,
    context: { queryClient },
    dehydrate: () => ({ queryClientState: dehydrate(queryClient) }),
    hydrate: (dehydrated) => { hydrate(queryClient, dehydrated.queryClientState) },
    Wrap: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  })
}
```

### Error Handling with TanStack Query

Reset query error boundaries on mount to allow retry:

```tsx
import { useQueryErrorResetBoundary } from '@tanstack/react-query'

export const Route = createFileRoute('/posts')({
  loader: ({ context: { queryClient } }) =>
    queryClient.ensureQueryData(postsQueryOptions),
  errorComponent: ({ error }) => {
    const router = useRouter()
    const queryErrorResetBoundary = useQueryErrorResetBoundary()

    useEffect(() => { queryErrorResetBoundary.reset() }, [queryErrorResetBoundary])

    return (
      <div>
        <p>{error.message}</p>
        <button onClick={() => router.invalidate()}>Retry</button>
      </div>
    )
  },
})
```

## Data Mutations

TanStack Router has no built-in mutation APIs. It reacts to URL side-effects from external mutation events.

Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/data-mutations

### router.invalidate()

Force all active route loaders to reload after a mutation:

```tsx
const router = useRouter()

const handleCreate = async () => {
  await createPost({ title: 'New Post' })
  router.invalidate()                          // background reload
  // await router.invalidate({ sync: true })   // wait for completion
}
```

### router.subscribe for Mutation State Cleanup

Reset mutation states when navigation completes:

```tsx
router.subscribe('onResolved', () => {
  mutationCache.clear()
})
```

The `onResolved` event fires when a location path change (not just reload) has fully resolved.

### Mutation with TanStack Query

The standard pattern pairs TanStack Query mutations with router invalidation:

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from '@tanstack/react-router'

function EditPost({ postId }: { postId: string }) {
  const router = useRouter()
  const queryClient = useQueryClient()

  const updatePost = useMutation({
    mutationFn: (data: { title: string }) =>
      fetch(`/api/posts/${postId}`, { method: 'PATCH', body: JSON.stringify(data) })
        .then((r) => r.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post', postId] })
      router.invalidate()   // also reload router-cached loader data
    },
  })

  return <button onClick={() => updatePost.mutate({ title: 'Updated' })}>Save</button>
}
```

## Loader Error Handling

### Throwing Errors, redirect(), and notFound()

```tsx
import { createFileRoute, redirect, notFound } from '@tanstack/react-router'

// Errors are caught by the route's error boundary
export const Route = createFileRoute('/posts')({
  loader: async () => {
    const res = await fetch('/api/posts')
    if (!res.ok) throw new Error('Failed to fetch posts')
    return res.json()
  },
})

// redirect() accepts the same options as navigate
export const Route = createFileRoute('/admin')({
  beforeLoad: ({ context }) => {
    if (!context.auth.isAdmin) throw redirect({ to: '/', replace: true })
  },
})

// notFound() renders the nearest notFoundComponent
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params: { postId } }) => {
    const post = await getPost(postId)
    if (!post) throw notFound()
    return { post }
  },
  notFoundComponent: () => {
    const { postId } = Route.useParams()
    return <p>Post {postId} not found</p>
  },
})
```

Note: `notFound()` in `beforeLoad` always triggers the root `notFoundComponent` since layout data may not have loaded.

### errorComponent with Retry

```tsx
import { ErrorComponent, useRouter } from '@tanstack/react-router'

export const Route = createFileRoute('/posts')({
  loader: () => fetchPosts(),
  errorComponent: ({ error }) => {
    const router = useRouter()
    if (error instanceof CustomApiError) {
      return <div>API Error: {error.statusCode}</div>
    }
    return (
      <div>
        <p>{error.message}</p>
        <button onClick={() => router.invalidate()}>Retry</button>
      </div>
    )
  },
})
```

Use `router.invalidate()` instead of just `reset()` when the error came from a loader - it coordinates both reloading data and resetting the error boundary.

### onError, onCatch, and Pending Components

```tsx
export const Route = createFileRoute('/posts')({
  loader: () => fetchPosts(),
  onError: ({ error }) => { reportToSentry(error) },         // on loader error
  onCatch: ({ error, errorInfo }) => { console.error(error) }, // on CatchBoundary catch
})

export const Route = createFileRoute('/reports')({
  loader: () => fetchLargeReport(),
  pendingComponent: () => <div>Generating report...</div>,
  pendingMs: 1_000,     // Show pending after 1s (default)
  pendingMinMs: 500,    // Show for at least 500ms to avoid flash (default)
})
```

Configure pending defaults at the router level with `defaultPendingMs` and `defaultPendingMinMs`.

## Common Patterns

### Parallel Data Loading and Preventing Waterfalls

Route loaders across the same navigation run in parallel automatically. Within a single loader, use `Promise.all` for independent requests:

```tsx
// routes/dashboard.tsx - runs in parallel with child loaders
export const Route = createFileRoute('/dashboard')({
  loader: async () => {
    // Independent requests - fetch in parallel
    const [stats, notifications] = await Promise.all([
      fetchStats(),
      fetchNotifications(),
    ])
    return { stats, notifications }
  },
})
```

### Dependent Data Loading

Chain dependent fetches, but parallelize independent work:

```tsx
export const Route = createFileRoute('/users/$userId/posts')({
  loader: async ({ params: { userId } }) => {
    const user = await fetchUser(userId)
    const [team, posts] = await Promise.all([
      fetchTeam(user.teamId),
      fetchUserPosts(userId),
    ])
    return { user, team, posts }
  },
})
```

### Prefetch on Hover

Enable at the router level with `defaultPreload: 'intent'`. Links will automatically preload on hover/focus. Disable per-link with `preload={false}`:

```tsx
const router = createRouter({ routeTree, defaultPreload: 'intent' })
```

### Full Route: TanStack Query with Search Params

Combines `validateSearch`, `loaderDeps`, `ensureQueryData`, and `useSuspenseQuery`:

```tsx
import { z } from 'zod'
import { queryOptions, useSuspenseQuery } from '@tanstack/react-query'

const postsQueryOptions = (params: { page: number; limit: number }) =>
  queryOptions({ queryKey: ['posts', params], queryFn: () => fetchPosts(params) })

export const Route = createFileRoute('/posts')({
  validateSearch: z.object({
    page: z.number().int().nonnegative().catch(0),
    limit: z.number().int().positive().catch(20),
  }),
  loaderDeps: ({ search: { page, limit } }) => ({ page, limit }),
  loader: ({ deps, context: { queryClient } }) =>
    queryClient.ensureQueryData(postsQueryOptions(deps)),
  component: () => {
    const { page, limit } = Route.useSearch()
    const { data: posts } = useSuspenseQuery(postsQueryOptions({ page, limit }))
    return (
      <div>
        <ul>{posts.items.map((p) => <li key={p.id}>{p.title}</li>)}</ul>
        <Link to="/posts" search={{ page: page + 1, limit }}>Next Page</Link>
      </div>
    )
  },
})
```

## Router Cache vs External Cache

**Use the built-in router cache when:** your app shares little data between routes, you want zero extra dependencies, coarse invalidation is acceptable, and SSR "just works" is a priority.

**Use TanStack Query (or another external cache) when:** you need shared caching/deduplication across routes, fine-grained cache invalidation by query key, optimistic update APIs, mutation management, persistence adapters, or offline support.

## Best Practices

1. **Always declare loaderDeps explicitly.** Only extract search params your loader uses. Never return the entire `search` object - it causes unnecessary cache invalidation.

2. **Use beforeLoad for auth and redirects, loader for data.** `beforeLoad` runs serially and blocks children - right for access control. `loader` runs in parallel - right for data fetching.

3. **Set `defaultPreloadStaleTime: 0` with external caches.** Ensures every event passes through to your library, which handles its own deduplication.

4. **Pass the abort signal to fetch calls.** Use `abortController.signal` to cancel in-flight requests on navigation, preventing wasted bandwidth and race conditions.

5. **Prefer `router.invalidate()` over `reset()` in error components.** It coordinates both reloading data and resetting the error boundary.

6. **Defer non-critical data with unawaited promises.** Use `Await` or `useSuspenseQuery` with `prefetchQuery` to render deferred data progressively.

7. **Use `Promise.all` for independent fetches within a loader.** Sequential awaits create waterfalls. Parallelize independent requests.

8. **Avoid throwing `notFound()` in `beforeLoad`.** It always triggers the root `notFoundComponent`. Throw in `loader` instead for proper propagation.
