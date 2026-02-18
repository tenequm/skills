# Search Params

TanStack Router treats URL search params as first-class application state - typed, validated, and managed with the same DX you expect from dedicated state management libraries.

Official docs: https://tanstack.com/router/latest/docs/framework/react/guide/search-params

## Search Params as State

Search params are the "OG" state manager - global state living inside the URL. TanStack Router builds on this with JSON-first serialization that goes far beyond `URLSearchParams`:

- Automatic JSON parsing/serialization of nested structures
- Type-safe validation at the route level
- Structural sharing to preserve referential identity between navigations
- First-level values stay URLSearchParams-compatible while nested values are JSON-encoded

```tsx
<Link
  to="/shop"
  search={{
    pageIndex: 3,
    includeCategories: ['electronics', 'gifts'],
    sortBy: 'price',
    desc: true,
  }}
/>
// URL: /shop?pageIndex=3&includeCategories=%5B%22electronics%22%2C%22gifts%22%5D&sortBy=price&desc=true
// Parsed back: { pageIndex: 3, includeCategories: ["electronics", "gifts"], sortBy: "price", desc: true }
```

First-level primitives (numbers, booleans) are preserved as actual types, not strings. Nested objects and arrays are JSON-stringified. The first level remains flat for compatibility with tools that read `URLSearchParams`.

## Defining Search Params

All definitions start with the `validateSearch` option on a route. It receives raw JSON-parsed search params and must return a typed object.

### Inline Validation

```tsx
// src/routes/shop/products.tsx
type ProductSearch = {
  page: number
  filter: string
  sort: 'newest' | 'oldest' | 'price'
}

export const Route = createFileRoute('/shop/products')({
  validateSearch: (search: Record<string, unknown>): ProductSearch => ({
    page: Number(search?.page ?? 1),
    filter: (search.filter as string) || '',
    sort: (search.sort as ProductSearch['sort']) || 'newest',
  }),
})
```

### Zod (with .catch() Shorthand)

Zod schemas work directly since `validateSearch` accepts objects with a `parse` property:

```tsx
import { z } from 'zod'

const productSearchSchema = z.object({
  page: z.number().catch(1),
  filter: z.string().catch(''),
  sort: z.enum(['newest', 'oldest', 'price']).catch('newest'),
})

export const Route = createFileRoute('/shop/products')({
  validateSearch: productSearchSchema, // shorthand for (s) => productSearchSchema.parse(s)
})
```

`.catch()` silently provides a fallback when validation fails. `.default()` throws an error that triggers `onError`/`errorComponent` (with `error.routerCode === 'VALIDATE_SEARCH'`).

### Zod Adapter for Input/Output Types

When using `.default()`, Zod's input type differs from output. The `zodValidator` adapter handles this so navigation does not require defaulted params:

```tsx
import { zodValidator } from '@tanstack/zod-adapter'
import { z } from 'zod'

const productSearchSchema = z.object({
  page: z.number().default(1),
  filter: z.string().default(''),
  sort: z.enum(['newest', 'oldest', 'price']).default('newest'),
})

export const Route = createFileRoute('/shop/products/')({
  validateSearch: zodValidator(productSearchSchema),
})

// This Link is valid - search params are optional because of defaults
<Link to="/shop/products" />
```

The `fallback` helper retains types while providing fallback values (unlike `.catch()` which makes fields `unknown`):

```tsx
import { fallback, zodValidator } from '@tanstack/zod-adapter'
import { z } from 'zod'

const productSearchSchema = z.object({
  page: fallback(z.number(), 1).default(1),
  filter: fallback(z.string(), '').default(''),
  sort: fallback(z.enum(['newest', 'oldest', 'price']), 'newest').default('newest'),
})

export const Route = createFileRoute('/shop/products/')({
  validateSearch: zodValidator(productSearchSchema),
})
```

You can configure which type to use for navigation vs reading:

```tsx
validateSearch: zodValidator({
  schema: productSearchSchema,
  input: 'output',  // Use output type for navigation
  output: 'input',  // Use input type for reading
})
```

### Valibot (Standard Schema - No Adapter Needed)

Valibot 1.0+ implements Standard Schema, so it works directly:

```tsx
import * as v from 'valibot'

const productSearchSchema = v.object({
  page: v.optional(v.fallback(v.number(), 1), 1),
  filter: v.optional(v.fallback(v.string(), ''), ''),
  sort: v.optional(
    v.fallback(v.picklist(['newest', 'oldest', 'price']), 'newest'),
    'newest',
  ),
})

export const Route = createFileRoute('/shop/products/')({
  validateSearch: productSearchSchema,
})
```

### ArkType (Standard Schema - No Adapter Needed)

```tsx
import { type } from 'arktype'

const productSearchSchema = type({
  page: 'number = 1',
  filter: 'string = ""',
  sort: '"newest" | "oldest" | "price" = "newest"',
})

export const Route = createFileRoute('/shop/products/')({
  validateSearch: productSearchSchema,
})
```

## Reading Search Params

### useSearch in Components

```tsx
export const Route = createFileRoute('/shop/products')({
  validateSearch: productSearchSchema,
})

function ProductList() {
  const { page, filter, sort } = Route.useSearch()
  return <div>Page {page}, Filter: {filter}, Sort: {sort}</div>
}
```

### Fine-Grained Selectors with select

Use `select` to subscribe to a subset of search params. The component only re-renders when the selected value changes:

```tsx
// Only re-renders when page changes
const page = Route.useSearch({ select: (s) => s.page })
```

When `select` returns a new object, enable structural sharing to prevent unnecessary re-renders:

```tsx
const filterState = Route.useSearch({
  select: (s) => ({ filter: s.filter, label: `Filtering by: ${s.filter}` }),
  structuralSharing: true,
})
```

Enable globally via `createRouter({ routeTree, defaultStructuralSharing: true })`. Note: structural sharing only works with JSON-compatible data (not class instances).

### Outside Route Components

Use `getRouteApi` to avoid importing the route (prevents circular deps in code-split routes):

```tsx
import { getRouteApi } from '@tanstack/react-router'

const routeApi = getRouteApi('/shop/products')

function ProductSidebar() {
  const { filter, sort } = routeApi.useSearch()
  return <div>Filter: {filter}, Sort: {sort}</div>
}
```

Or use `useSearch` with `from` for type safety, or `strict: false` for loose access:

```tsx
// Type-safe: requires from
const search = useSearch({ from: '/shop/products' })

// Loose: all params are T | undefined
const search = useSearch({ strict: false })
```

### In Loaders via loaderDeps

Only extract params your loader actually uses - returning the entire search object causes unnecessary cache invalidation:

```tsx
export const Route = createFileRoute('/posts')({
  validateSearch: z.object({
    offset: z.number().catch(0),
    limit: z.number().catch(20),
    viewMode: z.enum(['grid', 'list']).catch('list'),
  }),
  // Only extract what the loader needs
  loaderDeps: ({ search: { offset, limit } }) => ({ offset, limit }),
  loader: ({ deps: { offset, limit } }) => fetchPosts({ offset, limit }),
})
// BAD: loaderDeps: ({ search }) => search  // reloads when viewMode changes too
```

## Writing Search Params

### Link with search Prop

```tsx
// Replace all search params
<Link to="/shop/products" search={{ page: 1, filter: '', sort: 'newest' }}>
  Reset
</Link>

// Functional update - preserves other params
<Link from={Route.fullPath} search={(prev) => ({ ...prev, page: prev.page + 1 })}>
  Next Page
</Link>

// Generic component on multiple routes: use to="." for loose types
<Link to="." search={(prev) => ({ ...prev, page: prev.page + 1 })}>
  Next Page
</Link>

// Component in a specific subtree: specify from
<Link from="/posts" to="." search={(prev) => ({ ...prev, page: prev.page + 1 })}>
  Next Page
</Link>
```

### useNavigate

For programmatic updates in event handlers:

```tsx
const navigate = useNavigate({ from: '/shop/products' })

// Functional update
navigate({ search: (prev) => ({ ...prev, sort: 'price', page: 1 }) })

// Full replacement
navigate({ search: { page: 1, filter: '', sort: 'newest' } })
```

### router.navigate and Navigate Component

```tsx
// Outside React components
router.navigate({ to: '/shop/products', search: (prev) => ({ ...prev, page: 1 }) })

// Declarative redirect inside a component
<Navigate to="/shop/products" search={{ page: 1, filter: '', sort: 'newest' }} />
```

## Search Middlewares

Search middlewares transform search params when generating link hrefs and during navigation after validation. Defined in `search.middlewares` on a route.

### Custom Middleware

Each middleware receives `{ search, next }`. `search` is the current params, `next` produces the result from downstream:

```tsx
export const Route = createRootRoute({
  validateSearch: zodValidator(z.object({ rootValue: z.string().optional() })),
  search: {
    middlewares: [
      ({ search, next }) => {
        const result = next(search)
        return { rootValue: search.rootValue, ...result }  // retain unless overridden
      },
    ],
  },
})
```

### retainSearchParams

Preserves specified params across navigations. If a link explicitly sets a param, that value wins.

```tsx
import { retainSearchParams } from '@tanstack/react-router'

// Retain specific keys
search: { middlewares: [retainSearchParams(['rootValue', 'locale'])] }

// Retain ALL current params
search: { middlewares: [retainSearchParams(true)] }
```

### stripSearchParams

Removes params from URLs when they match defaults, keeping URLs clean.

```tsx
import { stripSearchParams } from '@tanstack/react-router'

// Strip by default values (deep equality comparison)
const defaults = { one: 'abc', two: 'xyz' }
search: { middlewares: [stripSearchParams(defaults)] }
// URL: /hello when one='abc' and two='xyz'
// URL: /hello?one=changed when one differs

// Strip specific keys (always remove, regardless of value)
search: { middlewares: [stripSearchParams(['hello'])] }

// Strip ALL params (only works when no params are required)
search: { middlewares: [stripSearchParams(true)] }
```

### Chaining Middlewares

Middlewares execute in order. Combine for complex behaviors:

```tsx
export const Route = createFileRoute('/search')({
  validateSearch: zodValidator(z.object({
    retainMe: z.string().optional(),
    arrayWithDefaults: z.string().array().default(['foo', 'bar']),
    required: z.string(),
  })),
  search: {
    middlewares: [
      retainSearchParams(['retainMe']),
      stripSearchParams({ arrayWithDefaults: ['foo', 'bar'] }),
    ],
  },
})
```

## Search Param Inheritance

Child routes automatically inherit and merge parent search params. Types merge down the tree:

```tsx
// src/routes/shop/products.tsx - parent defines page, filter, sort
export const Route = createFileRoute('/shop/products')({
  validateSearch: z.object({
    page: z.number().catch(1),
    filter: z.string().catch(''),
    sort: z.enum(['newest', 'oldest', 'price']).catch('newest'),
  }),
})

// src/routes/shop/products/$productId.tsx - child has full access
export const Route = createFileRoute('/shop/products/$productId')({
  validateSearch: z.object({
    tab: z.enum(['details', 'reviews', 'related']).catch('details'),
  }),
  beforeLoad: ({ search }) => {
    search.page   // number (from parent)
    search.filter // string (from parent)
    search.sort   // 'newest' | 'oldest' | 'price' (from parent)
    search.tab    // 'details' | 'reviews' | 'related' (own)
  },
})
```

## Complex Types

### Arrays and Nested Objects

```tsx
import { fallback, zodValidator } from '@tanstack/zod-adapter'
import { z } from 'zod'

const searchSchema = z.object({
  categories: fallback(z.array(z.string()), []).default([]),
  tags: fallback(z.array(z.number()), []).default([]),
  priceRange: fallback(
    z.object({ min: z.number(), max: z.number() }),
    { min: 0, max: 1000 },
  ).default({ min: 0, max: 1000 }),
})

export const Route = createFileRoute('/products/')({
  validateSearch: zodValidator(searchSchema),
})
// <Link to="/products" search={{ categories: ['electronics'], tags: [1, 2], priceRange: { min: 10, max: 500 } }} />
```

### Dates as Strings

Search params must be JSON-serializable, so store dates as ISO strings:

```tsx
const searchSchema = z.object({
  startDate: fallback(z.string(), '').default(''),
  endDate: fallback(z.string(), '').default(''),
})

// In component: parse to Date when needed
const start = startDate ? new Date(startDate) : null
```

### Enum/Union Types

```tsx
const viewModes = ['grid', 'list', 'table'] as const

const searchSchema = z.object({
  view: fallback(z.enum(viewModes), 'grid').default('grid'),
  columns: fallback(z.array(z.string()), ['name', 'date']).default(['name', 'date']),
})
```

## Custom Serialization

Replace the default JSON serializer at the router level via `parseSearch`/`stringifySearch`. The default behavior is `parseSearchWith(JSON.parse)` and `stringifySearchWith(JSON.stringify)`.

### query-string

```tsx
import qs from 'query-string'

const router = createRouter({
  routeTree,
  stringifySearch: stringifySearchWith((value) => qs.stringify(value)),
  parseSearch: parseSearchWith((value) => qs.parse(value)),
})
// Produces: ?page=1&sort=asc&filters=author%3Dtanner%26min_words%3D800
```

### JSURL2

Compresses URLs while maintaining readability:

```tsx
import { parse, stringify } from 'jsurl2'

const router = createRouter({
  routeTree,
  parseSearch: parseSearchWith(parse),
  stringifySearch: stringifySearchWith(stringify),
})
// Produces: ?page=1&sort=asc&filters=(author~tanner~min*_words~800)~
```

### Base64 Encoding

For maximum compatibility across browsers and URL unfurlers. Use safe binary encoding utilities that handle non-UTF8 characters (not raw `atob`/`btoa`):

```tsx
const router = createRouter({
  routeTree,
  parseSearch: parseSearchWith((value) => JSON.parse(decodeFromBinary(value))),
  stringifySearch: stringifySearchWith((value) => encodeToBinary(JSON.stringify(value))),
})

function decodeFromBinary(str: string): string {
  return decodeURIComponent(
    Array.prototype.map
      .call(atob(str), (c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
      .join(''),
  )
}

function encodeToBinary(str: string): string {
  return btoa(
    encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, (_, p1) =>
      String.fromCharCode(parseInt(p1, 16)),
    ),
  )
}
```

## Sharing Search Params Across Routes

### Global Params via Root Route

Define on the root with `retainSearchParams` so params persist everywhere:

```tsx
// src/routes/__root.tsx
export const Route = createRootRoute({
  validateSearch: zodValidator(z.object({
    locale: z.enum(['en', 'es', 'fr']).optional(),
    debug: z.boolean().optional(),
  })),
  search: { middlewares: [retainSearchParams(['locale', 'debug'])] },
})
// Every route/component can access locale and debug; they survive navigations
```

### Cross-Route Retention on Layout Routes

Use on a layout route so child navigations preserve shared state:

```tsx
// src/routes/dashboard.tsx - navigating between children preserves dateRange/teamId
export const Route = createFileRoute('/dashboard')({
  validateSearch: zodValidator(z.object({
    dateRange: z.enum(['7d', '30d', '90d', '1y']).optional(),
    teamId: z.string().optional(),
  })),
  search: { middlewares: [retainSearchParams(['dateRange', 'teamId'])] },
})
```

### Combining Retention and Stripping

```tsx
const analyticsDefaults = { metric: 'pageviews', interval: 'daily' }

export const Route = createFileRoute('/dashboard/analytics')({
  validateSearch: zodValidator(z.object({
    metric: z.string().default(analyticsDefaults.metric),
    interval: z.enum(['hourly', 'daily', 'weekly']).default(analyticsDefaults.interval),
    compareWith: z.string().optional(),
  })),
  search: {
    middlewares: [
      retainSearchParams(['compareWith']),       // persist across navigations
      stripSearchParams(analyticsDefaults),       // clean URL when at defaults
    ],
  },
})
```

## Common Patterns

### Pagination

```tsx
const defaults = { page: 1, perPage: 20 }

export const Route = createFileRoute('/posts')({
  validateSearch: zodValidator(z.object({
    page: fallback(z.number().int().positive(), defaults.page).default(defaults.page),
    perPage: fallback(z.number().int().positive().max(100), defaults.perPage).default(defaults.perPage),
  })),
  search: { middlewares: [stripSearchParams(defaults)] },
  loaderDeps: ({ search: { page, perPage } }) => ({ page, perPage }),
  loader: ({ deps }) => fetchPosts(deps),
  component: function PostList() {
    const { page } = Route.useSearch()
    return (
      <div>
        <Link from={Route.fullPath} search={(prev) => ({ ...prev, page: Math.max(1, prev.page - 1) })}>
          Previous
        </Link>
        <span>Page {page}</span>
        <Link from={Route.fullPath} search={(prev) => ({ ...prev, page: prev.page + 1 })}>
          Next
        </Link>
      </div>
    )
  },
})
```

### Filters and Sorting

```tsx
const defaults = { search: '', category: 'all', sortBy: 'name' as const, sortOrder: 'asc' as const }

export const Route = createFileRoute('/products')({
  validateSearch: zodValidator(z.object({
    search: fallback(z.string(), '').default(''),
    category: fallback(z.string(), 'all').default('all'),
    sortBy: fallback(z.enum(['name', 'price', 'rating']), 'name').default('name'),
    sortOrder: fallback(z.enum(['asc', 'desc']), 'asc').default('asc'),
  })),
  search: { middlewares: [stripSearchParams(defaults)] },
  loaderDeps: ({ search }) => search,
  loader: ({ deps }) => fetchProducts(deps),
  component: function ProductsPage() {
    const search = Route.useSearch()
    const navigate = useNavigate({ from: Route.fullPath })
    return (
      <div>
        <input
          value={search.search}
          onChange={(e) => navigate({ search: (prev) => ({ ...prev, search: e.target.value }) })}
        />
        <Link from={Route.fullPath} search={defaults}>Reset</Link>
      </div>
    )
  },
})
```

### Modal State via Search Params

```tsx
export const Route = createFileRoute('/users')({
  validateSearch: zodValidator(z.object({
    editUserId: fallback(z.string(), '').default(''),
    showCreateModal: fallback(z.boolean(), false).default(false),
  })),
  search: { middlewares: [stripSearchParams({ editUserId: '', showCreateModal: false })] },
  component: function UsersPage() {
    const { editUserId, showCreateModal } = Route.useSearch()
    const navigate = useNavigate({ from: Route.fullPath })
    const closeModals = () => navigate({
      search: (prev) => ({ ...prev, editUserId: '', showCreateModal: false }),
    })
    return (
      <div>
        <Link from={Route.fullPath} search={(prev) => ({ ...prev, showCreateModal: true })}>
          Create User
        </Link>
        {showCreateModal && <CreateUserModal onClose={closeModals} />}
        {editUserId && <EditUserModal userId={editUserId} onClose={closeModals} />}
      </div>
    )
  },
})
```

### Tab State

```tsx
const tabs = ['general', 'security', 'notifications'] as const

export const Route = createFileRoute('/settings')({
  validateSearch: zodValidator(z.object({
    tab: fallback(z.enum(tabs), 'general').default('general'),
  })),
  search: { middlewares: [stripSearchParams({ tab: 'general' as const })] },
  component: function SettingsPage() {
    const { tab } = Route.useSearch()
    return (
      <nav>
        {tabs.map((t) => (
          <Link key={t} from={Route.fullPath} search={{ tab: t }}>{t}</Link>
        ))}
      </nav>
    )
  },
})
```

## Best Practices

1. **Always validate search params.** Never trust raw URL input. Use `validateSearch` with `.catch()` or `fallback()` to provide sensible defaults so malformed URLs do not break the user experience.

2. **Use schema-based validation with adapters.** Prefer Zod with `zodValidator` or Valibot/ArkType via Standard Schema over manual validation. This gives you correct input/output type inference for both navigation and reading.

3. **Use `fallback()` + `.default()` with the Zod adapter.** Plain `.catch()` loses type information. The `fallback` helper from `@tanstack/zod-adapter` preserves types while handling malformed values.

4. **Strip default values from URLs.** Use `stripSearchParams` to keep URLs clean. Users should only see params that differ from defaults.

5. **Retain cross-cutting params with `retainSearchParams`.** For params like `locale`, `debug`, or `theme` that should survive navigations, define them on a parent route with `retainSearchParams`.

6. **Be selective with `loaderDeps`.** Only extract search params your loader actually uses. Returning the entire search object causes unnecessary cache invalidation when unrelated params change.

7. **Use `select` for fine-grained subscriptions.** When a component only needs one search param, use `Route.useSearch({ select })` to prevent re-renders when other params change. Enable `structuralSharing: true` when selectors return objects.

8. **Prefer functional updates for search.** Use `search={(prev) => ({ ...prev, page: prev.page + 1 })}` instead of replacing the entire object. This preserves other params and avoids dropping state.

## Related Documentation

- Search Params Guide: https://tanstack.com/router/latest/docs/framework/react/guide/search-params
- Custom Serialization: https://tanstack.com/router/latest/docs/framework/react/guide/custom-search-param-serialization
- Render Optimizations: https://tanstack.com/router/latest/docs/framework/react/guide/render-optimizations
- Data Loading (loaderDeps): https://tanstack.com/router/latest/docs/framework/react/guide/data-loading
- Type Safety: https://tanstack.com/router/latest/docs/framework/react/guide/type-safety
