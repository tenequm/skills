# Routing Patterns

TanStack Router provides a flexible routing system with multiple approaches: file-based routing (recommended), code-based routing, and virtual file routes. This reference covers all routing patterns, naming conventions, and advanced features.

> Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/file-based-routing

## File-Based Routing

File-based routing uses the filesystem to define route hierarchy. The TanStack Router bundler plugin automatically generates `routeTree.gen.ts` from your route directory.

### Vite Plugin Setup

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  plugins: [
    tanstackRouter({
      target: 'react',
      // routesDirectory defaults to './src/routes'
      // generatedRouteTree defaults to './src/routeTree.gen.ts'
    }),
    react(),
  ],
})
```

The plugin watches `src/routes/` during development and regenerates `routeTree.gen.ts` on route file changes.

### Route File Anatomy

Every route file uses `createFileRoute` (path auto-managed by the plugin):

```tsx
// src/routes/about.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/about')({
  component: AboutComponent,
})

function AboutComponent() {
  return <div>About</div>
}
```

The root route uses `createRootRoute` and must be named `__root.tsx`:

```tsx
// src/routes/__root.tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: () => (
    <div>
      <nav>{/* navigation */}</nav>
      <Outlet />
    </div>
  ),
})
```

### Directory Routes

Directories represent route hierarchy:

```
src/routes/
  __root.tsx                    ->  always rendered
  index.tsx                     ->  / (exact)
  about.tsx                     ->  /about
  posts.tsx                     ->  /posts (layout)
  posts/
    index.tsx                   ->  /posts (exact)
    $postId.tsx                 ->  /posts/$postId
  settings.tsx                  ->  /settings (layout)
  settings/
    profile.tsx                 ->  /settings/profile
    notifications.tsx           ->  /settings/notifications
```

### Flat Routes (Dot Notation)

Use `.` in filenames to denote nesting without directories:

```
src/routes/
  __root.tsx
  index.tsx                        ->  /
  posts.tsx                        ->  /posts
  posts.index.tsx                  ->  /posts (exact)
  posts.$postId.tsx                ->  /posts/$postId
  settings.tsx                     ->  /settings
  settings.profile.tsx             ->  /settings/profile
  settings.notifications.tsx       ->  /settings/notifications
```

Both styles can be freely combined in a single project.

## File Naming Conventions

> Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/file-naming-conventions

### `$param` - Dynamic Segments

The `$` token followed by a label creates a dynamic path parameter:

```tsx
// src/routes/posts.$postId.tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/posts/$postId')({
  loader: ({ params }) => fetchPost(params.postId),
  component: PostComponent,
})

function PostComponent() {
  const { postId } = Route.useParams()
  return <div>Post ID: {postId}</div>
}
```

Multiple dynamic segments work at each level: `/posts/$postId/$revisionId` captures both.

### `$` - Splat / Catch-All

A path of only `$` captures all remaining segments into `params._splat`:

```tsx
// src/routes/files/$.tsx  ->  /files/*
export const Route = createFileRoute('/files/$')({
  component: () => {
    const { _splat } = Route.useParams()
    // URL /files/documents/report.pdf -> _splat = "documents/report.pdf"
    return <div>File path: {_splat}</div>
  },
})
```

### `_` Prefix - Pathless Layout Routes

Wraps children without consuming a URL segment. The part after `_` is the route's unique ID.

```
# Flat                              # Directory
_auth.tsx           (layout only)   _auth/
_auth.login.tsx     /login            route.tsx   (layout only)
_auth.register.tsx  /register         login.tsx   /login
                                      register.tsx /register
```

```tsx
// src/routes/_auth.tsx
import { Outlet, createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_auth')({
  component: () => (
    <div className="auth-layout">
      <h1>Authentication</h1>
      <Outlet />
    </div>
  ),
})
```

| URL | Rendered Components |
|-----|-------------------|
| `/login` | `<Root><AuthLayout><Login>` |
| `/register` | `<Root><AuthLayout><Register>` |

Pathless layout routes cannot use dynamic segments in their ID (no `_$postId/`).

### `_` Suffix - Non-Nested Routes

Breaks a route out of its parent's component nesting while keeping the URL path:

```
src/routes/
  posts.tsx                      ->  /posts (layout)
  posts.$postId.tsx              ->  /posts/$postId (nested under posts)
  posts_.$postId.edit.tsx        ->  /posts/$postId/edit (NOT nested)
```

| URL | Rendered Components |
|-----|-------------------|
| `/posts/123` | `<Root><Posts><Post>` |
| `/posts/123/edit` | `<Root><PostEditor>` (outside Posts layout) |

### `-` Prefix - Excluded Files

Files and directories prefixed with `-` are excluded from route generation. Use for colocation:

```
src/routes/
  posts.tsx
  -posts-table.tsx               ->  ignored by router
  -components/                   ->  ignored by router
    header.tsx
```

Import normally: `import { PostsTable } from './-posts-table'`

### `()` - Route Group Directories

Purely organizational directories that do not affect URL or component tree:

```
src/routes/
  (app)/
    dashboard.tsx                ->  /dashboard
    settings.tsx                 ->  /settings
  (auth)/
    login.tsx                    ->  /login
```

### Other Conventions

- **`route.tsx`** - In directories, provides the route config at that path level (e.g., `account/route.tsx` for `/account`)
- **`index` token** - Matches parent route exactly when no child segments follow
- **`[x]` escaping** - Square brackets escape special chars: `script[.]js.tsx` becomes `/script.js`
- **`{-$param}`** - Optional path parameters matching with or without the segment. `/posts/{-$category}` matches both `/posts` and `/posts/tech`. Ranked lower than exact matches.

## Code-Based Routing

Define routes entirely in code using `createRoute` and `createRootRoute`. Use when file-based routing does not fit.

> Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/code-based-routing

```tsx
import { createRootRoute, createRoute, createRouter, Outlet } from '@tanstack/react-router'

const rootRoute = createRootRoute({
  component: () => <div><Outlet /></div>,
})

const aboutRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: 'about',
  component: () => <div>About</div>,
})

const postsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: 'posts',
  component: PostsLayout,
})

const postsIndexRoute = createRoute({
  getParentRoute: () => postsRoute,
  path: '/',  // index route uses '/'
})

const postRoute = createRoute({
  getParentRoute: () => postsRoute,
  path: '$postId',
  loader: ({ params }) => fetchPost(params.postId),
})

// Pathless layout: use 'id' instead of 'path'
const pathlessLayout = createRoute({
  getParentRoute: () => rootRoute,
  id: 'authLayout',
  component: AuthLayout,
})

// Non-nested: set parent to root with full path
const postEditorRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: 'posts/$postId/edit',
})

// Build tree with .addChildren()
const routeTree = rootRoute.addChildren([
  aboutRoute,
  postsRoute.addChildren([postsIndexRoute, postRoute]),
  postEditorRoute,
  pathlessLayout.addChildren([loginRoute, registerRoute]),
])

const router = createRouter({ routeTree })
```

Every route (except root) requires `getParentRoute` for type safety. Use code-based routing for runtime route generation, external config, incremental migration, or projects without bundler plugin support.

## Virtual File Routes

Define route trees programmatically while referencing real files. Gives full control over organization without filesystem constraints.

> Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/virtual-file-routes

### Setup

```ts
// vite.config.ts
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  plugins: [
    tanstackRouter({
      target: 'react',
      virtualRouteConfig: './src/routes.ts',
    }),
    react(),
  ],
})
```

### API Functions

| Function | Purpose |
|----------|---------|
| `rootRoute(file, children)` | Creates root route pointing to a file |
| `route(path, file, children)` | Creates route at path pointing to a file |
| `index(file)` | Creates index route |
| `layout(file, children)` | Creates pathless layout (optional ID as first arg) |
| `physical(pathPrefix, directory)` | Mounts directory using standard file-based conventions |

### Full Example

```tsx
// src/routes.ts
import { rootRoute, route, index, layout, physical } from '@tanstack/virtual-file-routes'

export const routes = rootRoute('root.tsx', [
  index('index.tsx'),
  layout('pathlessLayout.tsx', [
    route('/dashboard', 'app/dashboard.tsx', [
      index('app/dashboard-index.tsx'),
      route('/invoices', 'app/dashboard-invoices.tsx', [
        index('app/invoices-index.tsx'),
        route('$id', 'app/invoice-detail.tsx'),
      ]),
    ]),
    physical('/posts', 'posts'),  // mounts posts/ dir with file-based conventions
  ]),
])
```

Routes without a file set a common path prefix: `route('/hello', [route('/world', 'world.tsx')])`.

Use `physical('features')` (no path prefix) to merge a directory at the current level.

### `__virtual.ts` - Inline Virtual Configuration

Drop a `__virtual.ts` in any directory within a file-based route tree to switch to virtual config for that subtree:

```tsx
// src/routes/posts/__virtual.ts
import { defineVirtualSubtreeConfig, index, route } from '@tanstack/virtual-file-routes'

export default defineVirtualSubtreeConfig([
  index('home.tsx'),
  route('$id', 'details.tsx'),
])
```

Virtual and file-based routing can be nested as many levels deep as needed.

## Layout Routes

Layout routes wrap child routes with shared UI, loaders, search param validation, error boundaries, and context.

**Path-based layout** - A route with children uses `<Outlet />` to render child content:

```tsx
// src/routes/app.tsx
import { Outlet, createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/app')({
  component: () => (
    <div>
      <h1>App Layout</h1>
      <Outlet />
    </div>
  ),
})
```

**Pathless layout** - Wraps children without adding a URL segment. Use `_` prefix in file-based or `id` in code-based:

```tsx
// src/routes/_authenticated.tsx
export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async ({ context }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({ to: '/login' })
    }
  },
  component: () => <Outlet />,
})
```

## Route Masking

Displays a different URL in the browser than the one actually navigated to. When shared or reloaded, the displayed (masked) URL is used.

> Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/route-masking

### Imperative (Link / navigate)

```tsx
<Link
  to="/photos/$photoId/modal"
  params={{ photoId: '5' }}
  mask={{ to: '/photos/$photoId', params: { photoId: '5' } }}
>
  Open Photo
</Link>
```

```tsx
const navigate = useNavigate()
navigate({
  to: '/photos/$photoId/modal',
  params: { photoId: '5' },
  mask: { to: '/photos/$photoId', params: { photoId: '5' } },
})
```

### Declarative (createRouteMask)

```tsx
import { createRouteMask, createRouter } from '@tanstack/react-router'

const photoModalMask = createRouteMask({
  routeTree,
  from: '/photos/$photoId/modal',
  to: '/photos/$photoId',
  params: (prev) => ({ photoId: prev.photoId }),
})

const router = createRouter({ routeTree, routeMasks: [photoModalMask] })
```

### unmaskOnReload

By default, masked URLs persist through reloads. To unmask: pass `unmaskOnReload: true` on Link, createRouteMask, or as a router default.

Route masking stores the actual target in `location.state.__tempLocation`. When copied/shared, mask data is lost and the displayed URL is used directly.

## Navigation Blocking

Prevents route transitions for unsaved form data or in-progress operations.

> Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/navigation-blocking

### useBlocker Hook

```tsx
import { useBlocker } from '@tanstack/react-router'

function EditForm() {
  const [formIsDirty, setFormIsDirty] = useState(false)

  useBlocker({
    shouldBlockFn: () => {
      if (!formIsDirty) return false
      return !confirm('Are you sure you want to leave?')
    },
  })
}
```

### Custom UI with withResolver

```tsx
const { proceed, reset, status } = useBlocker({
  shouldBlockFn: () => formIsDirty,
  withResolver: true,
})

// Render custom dialog when status === 'blocked'
// Call proceed() to allow navigation, reset() to cancel
```

### shouldBlockFn with Type-Safe Locations

```tsx
useBlocker({
  shouldBlockFn: ({ current, next }) => {
    return current.routeId === '/foo' && next.fullPath === '/bar/$id'
  },
  withResolver: true,
})
```

### enableBeforeUnload

Controls the browser's native beforeunload dialog independently:

```tsx
useBlocker({
  shouldBlockFn: () => !formIsDirty ? false : !confirm('Leave?'),
  enableBeforeUnload: formIsDirty,  // or () => formIsDirty
})
```

### Block Component

Declarative alternative:

```tsx
<Block shouldBlockFn={() => formIsDirty} enableBeforeUnload={formIsDirty} withResolver>
  {({ status, proceed, reset }) => (
    status === 'blocked' && <ConfirmDialog onConfirm={proceed} onCancel={reset} />
  )}
</Block>
```

## URL Rewrites

Bidirectional URL transformation between browser display and router interpretation.

> Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/url-rewrites

### Basic Configuration

```tsx
const router = createRouter({
  routeTree,
  rewrite: {
    input: ({ url }) => { /* browser URL -> router internal */ return url },
    output: ({ url }) => { /* router internal -> browser URL */ return url },
  },
})
```

Rewrite functions receive a `URL` object and return the mutated `url`, a new `URL`, a string href, or `undefined` to skip.

### i18n Locale Prefix

```tsx
const router = createRouter({
  routeTree,
  rewrite: {
    input: ({ url }) => {
      const segments = url.pathname.split('/').filter(Boolean)
      if (segments[0] && locales.includes(segments[0])) {
        url.pathname = '/' + segments.slice(1).join('/') || '/'
      }
      return url
    },
    output: ({ url }) => {
      url.pathname = `/${getLocale()}${url.pathname === '/' ? '' : url.pathname}`
      return url
    },
  },
})
```

### Subdomain Routing

```tsx
rewrite: {
  input: ({ url }) => {
    const subdomain = url.hostname.split('.')[0]
    if (subdomain === 'admin') url.pathname = '/admin' + url.pathname
    return url
  },
  output: ({ url }) => {
    if (url.pathname.startsWith('/admin')) {
      url.hostname = 'admin.example.com'
      url.pathname = url.pathname.replace(/^\/admin/, '') || '/'
    }
    return url
  },
}
```

### Composing Rewrites

```tsx
import { composeRewrites } from '@tanstack/react-router'
const router = createRouter({ routeTree, rewrite: composeRewrites([localeRewrite, legacyRewrite]) })
```

Input rewrites execute first-to-last. Output rewrites execute last-to-first (reverse).

### location.href vs location.publicHref

- `location.href` - Internal URL (after input rewrite), used for routing
- `location.publicHref` - External URL (after output rewrite), shown in browser

Use `publicHref` for sharing links, canonical URLs, analytics, and clipboard operations.

## History Types

TanStack Router supports three history types from `@tanstack/history`:

| Type | Function | Use Case |
|------|----------|----------|
| Browser | `createBrowserHistory()` | Default. Uses browser History API |
| Hash | `createHashHistory()` | Servers without URL rewriting support |
| Memory | `createMemoryHistory()` | Testing, SSR, non-browser environments |

```tsx
import { createMemoryHistory, createRouter } from '@tanstack/react-router'

const memoryHistory = createMemoryHistory({ initialEntries: ['/'] })
const router = createRouter({ routeTree, history: memoryHistory })
```

## Route Types Summary

| Route Type | File Convention | URL Behavior | Component Behavior |
|-----------|----------------|-------------|-------------------|
| Root | `__root.tsx` | Always matches | Always rendered, wraps all routes |
| Index | `index.tsx` | Exact parent match | Rendered when parent matches exactly |
| Static | `about.tsx` | `/about` | Rendered at exact path |
| Dynamic | `$postId.tsx` | `/123` (captures param) | Receives params via `useParams()` |
| Splat | `$.tsx` | Captures all remaining | Receives `_splat` param |
| Optional | `{-$param}.tsx` | With or without segment | Param `undefined` when absent |
| Layout | `posts.tsx` + `posts/` | Matches path prefix | Wraps children via `<Outlet />` |
| Pathless Layout | `_layout.tsx` | No URL segment consumed | Wraps children without URL impact |
| Non-Nested | `posts_.$id.edit.tsx` | Matches full path | Renders outside parent layout |
| Excluded | `-helpers.tsx` | Not a route | Ignored by router, for colocation |
| Group | `(auth)/login.tsx` | Directory ignored | Organizational only |

## Best Practices

1. **Prefer file-based routing for most projects.** It provides automatic code splitting, type-safe route generation, and eliminates manual route tree assembly. Use code-based routing only when runtime generation or non-standard tooling requires it.

2. **Mix flat and directory structures intentionally.** Use directories for route groups with multiple siblings. Use dot notation for isolated deep routes (e.g., `posts.$postId.edit.tsx`).

3. **Use pathless layouts for shared UI without URL segments.** Common patterns include authentication wrappers (`_auth`), dashboard shells (`_dashboard`), and sidebar layouts. Name descriptively since the `_` prefix ID must be unique.

4. **Colocate route-specific code with the `-` prefix.** Place helper components, utilities, and data-fetching logic next to route files using `-` prefixed names. They are ignored by the router but accessible via standard imports.

5. **Use route masking for modal patterns.** When a modal has its own route for deep-linking but should display a simpler URL, masking keeps URLs clean. Set `unmaskOnReload: true` if masks should not persist across reloads.

6. **Use `enableBeforeUnload` intentionally.** Only trigger the native beforeunload dialog for genuinely unsaved data. Pair `shouldBlockFn` with `enableBeforeUnload` tied to the same dirty state.

7. **Use virtual file routes for custom project structures.** Map existing file organizations to routes with full programmatic control while retaining file-based routing performance benefits.

8. **Use `publicHref` for external-facing URLs.** When URL rewrites are active, always use `location.publicHref` for sharing, canonical URLs, and analytics.
