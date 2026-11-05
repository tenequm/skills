# Server-Side Rendering (SSR)

TanStack Router provides low-level SSR primitives for rendering your application on the server and hydrating it on the client. It supports both non-streaming and streaming SSR, automatic data serialization, and document head management.

> **For most SSR use cases, [TanStack Start](https://tanstack.com/start/latest) is the recommended approach.** Start provides SSR, streaming, server functions, and deployment with zero configuration. The APIs documented here are lower-level building blocks intended for custom server setups or integration with existing server frameworks. These APIs share internal implementations with TanStack Start and should be considered experimental until Start reaches stable status.

Official documentation: https://tanstack.com/router/latest/docs/framework/react/guide/ssr

## SSR Overview

Two flavors of SSR are supported:

- **Non-Streaming SSR** - The entire page is rendered on the server and sent as a single HTML response, including serialized data needed for client hydration.
- **Streaming SSR** - The critical first paint is sent immediately, and remaining content is progressively streamed to the client as it becomes available.

Key SSR utilities are split across two import paths:

- `@tanstack/react-router/ssr/server` - `createRequestHandler`, `defaultRenderHandler`, `renderRouterToString`, `defaultStreamHandler`, `renderRouterToStream`, `RouterServer`
- `@tanstack/react-router/ssr/client` - `RouterClient`

## Shared Router Configuration

Since your router exists on both the server and the client, create it in a shared file:

```tsx
// src/router.tsx
import { createRouter as createTanstackRouter } from '@tanstack/react-router'
import { routeTree } from './routeTree.gen'

export function createRouter() {
  return createTanstackRouter({
    routeTree,
    context: { head: '' },
    defaultPreload: 'intent',
    scrollRestoration: true,
  })
}

declare module '@tanstack/react-router' {
  interface Register {
    router: ReturnType<typeof createRouter>
  }
}
```

## Non-Streaming SSR

### Server Entry with defaultRenderHandler

The simplest approach - handles wrapping and hydration automatically:

```tsx
// src/entry-server.tsx
import {
  createRequestHandler,
  defaultRenderHandler,
} from '@tanstack/react-router/ssr/server'
import { createRouter } from './router'

export async function render({ request }: { request: Request }) {
  const handler = createRequestHandler({ request, createRouter })
  return await handler(defaultRenderHandler)
}
```

### Server Entry with renderRouterToString

For more control, use `renderRouterToString` with `RouterServer` to manually specify wrapping providers:

```tsx
// src/entry-server.tsx
import {
  createRequestHandler,
  renderRouterToString,
  RouterServer,
} from '@tanstack/react-router/ssr/server'
import { createRouter } from './router'

export function render({ request }: { request: Request }) {
  const handler = createRequestHandler({ request, createRouter })

  return handler(({ responseHeaders, router }) =>
    renderRouterToString({
      responseHeaders,
      router,
      children: <RouterServer router={router} />,
    }),
  )
}
```

### Client Entry

The client entry is the same for both streaming and non-streaming SSR:

```tsx
// src/entry-client.tsx
import { hydrateRoot } from 'react-dom/client'
import { RouterClient } from '@tanstack/react-router/ssr/client'
import { createRouter } from './router'

const router = createRouter()
hydrateRoot(document, <RouterClient router={router} />)
```

## Streaming SSR

Streaming SSR sends the critical first paint immediately, then progressively streams remaining content. Useful for pages with slow or high-latency data fetching.

### Server Entry with defaultStreamHandler

```tsx
// src/entry-server.tsx
import {
  createRequestHandler,
  defaultStreamHandler,
} from '@tanstack/react-router/ssr/server'
import { createRouter } from './router'

export async function render({ request }: { request: Request }) {
  const handler = createRequestHandler({ request, createRouter })
  return await handler(defaultStreamHandler)
}
```

### Server Entry with renderRouterToStream

```tsx
// src/entry-server.tsx
import {
  createRequestHandler,
  renderRouterToStream,
  RouterServer,
} from '@tanstack/react-router/ssr/server'
import { createRouter } from './router'

export function render({ request }: { request: Request }) {
  const handler = createRequestHandler({ request, createRouter })

  return handler(({ request, responseHeaders, router }) =>
    renderRouterToStream({
      request,
      responseHeaders,
      router,
      children: <RouterServer router={router} />,
    }),
  )
}
```

### Vite Configuration for Streaming

Enable streaming support in the router plugin:

```ts
// vite.config.ts
import { tanstackRouter } from '@tanstack/router-plugin/vite'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    tanstackRouter({ autoCodeSplitting: true, enableStreaming: true }),
    react(),
  ],
  ssr: {
    optimizeDeps: {
      include: ['@tanstack/react-router/ssr/server'],
    },
  },
})
```

## Express Integration

`createRequestHandler` requires a Web API standard `Request` and returns a `Response` promise. When using Express, convert between the two:

```tsx
// src/entry-server.tsx
import { pipeline } from 'node:stream/promises'
import {
  RouterServer,
  createRequestHandler,
  renderRouterToStream,
} from '@tanstack/react-router/ssr/server'
import { createRouter } from './router'
import type express from 'express'

export async function render({
  req,
  res,
  head = '',
}: {
  head?: string
  req: express.Request
  res: express.Response
}) {
  const url = new URL(req.originalUrl || req.url, 'https://localhost:3000').href

  const request = new Request(url, {
    method: req.method,
    headers: (() => {
      const headers = new Headers()
      for (const [key, value] of Object.entries(req.headers)) {
        headers.set(key, value as any)
      }
      return headers
    })(),
  })

  const handler = createRequestHandler({
    request,
    createRouter: () => {
      const router = createRouter()
      router.update({
        context: { ...router.options.context, head },
      })
      return router
    },
  })

  const response = await handler(({ request, responseHeaders, router }) =>
    renderRouterToStream({
      request,
      responseHeaders,
      router,
      children: <RouterServer router={router} />,
    }),
  )

  res.statusMessage = response.statusText
  res.status(response.status)
  response.headers.forEach((value, name) => res.setHeader(name, value))
  return pipeline(response.body as any, res)
}
```

## Data Serialization

Resolved loader data is automatically dehydrated on the server and rehydrated on the client. TanStack Router uses a lightweight serializer that supports types beyond `JSON.stringify`/`JSON.parse`:

| Type | Supported |
|------|-----------|
| `string`, `number`, `boolean`, `null` | Yes (standard JSON) |
| `Date` | Yes |
| `Error` | Yes |
| `FormData` | Yes |
| `undefined` | Yes |

For complex types like `Map`, `Set`, or `BigInt`, a custom serializer is needed. Custom serializer support is under active development.

When using deferred data streaming, the streaming SSR pattern (`defaultStreamHandler` or `renderRouterToStream`) is required for proper dehydration/hydration of streamed data.

## History Types

TanStack Router uses `@tanstack/history` to manage routing history. Three types are available:

```tsx
import {
  createBrowserHistory,
  createHashHistory,
  createMemoryHistory,
  createRouter,
} from '@tanstack/react-router'

// Browser history (default on client) - uses browser History API
const browserHistory = createBrowserHistory()

// Hash history - uses URL hash fragment, useful without server URL rewrites
const hashHistory = createHashHistory()

// Memory history - required on the server where window does not exist
const memoryHistory = createMemoryHistory({ initialEntries: ['/'] })

const router = createRouter({ routeTree, history: memoryHistory })
```

When using `RouterServer`, memory history is configured automatically. You do not need to manually create a memory history instance for SSR. On the client, `RouterClient` defaults to browser history.

## Document Head Management

TanStack Router provides built-in document head management for `<title>`, `<meta>`, `<link>`, `<style>`, and `<script>` tags.

Official documentation: https://tanstack.com/router/latest/docs/framework/react/guide/document-head-management

### HeadContent and Scripts Components

`<HeadContent />` renders head-related tags. `<Scripts />` renders body scripts before the main entry point. Both are required for SSR:

```tsx
import {
  HeadContent,
  Outlet,
  Scripts,
  createRootRoute,
} from '@tanstack/react-router'

export const Route = createRootRoute({
  component: () => (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <Outlet />
        <Scripts />
      </body>
    </html>
  ),
})
```

For SPAs without server-rendered HTML structure, render `<HeadContent />` as high as possible in the component tree (no `<head>` wrapper needed).

### ScriptOnce

Renders an inline script that executes before React hydration and removes itself from the DOM. On client-side navigation, nothing renders (prevents duplicate execution):

```tsx
import { ScriptOnce } from '@tanstack/react-router'

const themeScript = `(function() {
  try {
    const theme = localStorage.getItem('theme') || 'auto';
    const resolved = theme === 'auto'
      ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : theme;
    document.documentElement.classList.add(resolved);
  } catch (e) {}
})();`

function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <>
      <ScriptOnce children={themeScript} />
      {children}
    </>
  )
}
```

When `ScriptOnce` modifies the DOM before hydration, add `suppressHydrationWarning` to the affected element (e.g. `<html lang="en" suppressHydrationWarning>`).

### Route head() Property

Define head metadata for any route. Returns an object with `meta`, `links`, `styles`, and `scripts` arrays:

```tsx
export const Route = createRootRouteWithContext<RouterContext>()({
  head: () => ({
    meta: [
      { charSet: 'UTF-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1.0' },
      { name: 'description', content: 'My application description' },
      { title: 'My App' },
    ],
    links: [
      { rel: 'icon', href: '/favicon.ico' },
    ],
    styles: [
      {
        media: 'all and (max-width: 500px)',
        children: `p { color: blue; }`,
      },
    ],
    scripts: [
      { src: 'https://www.google-analytics.com/analytics.js' },
    ],
  }),
})
```

Body scripts use the top-level `scripts` route option (rendered via `<Scripts />`):

```tsx
export const Route = createRootRoute({
  scripts: () => [{ children: 'console.log("Hello from body script")' }],
})
```

### Meta Tag Deduping

TanStack Router automatically dedupes `title` and `meta` tags across nested routes:

- `title` tags in child routes override parent route titles
- `meta` tags with the same `name` or `property` are overridden by the last occurrence in nested routes

### Dynamic Head with loaderData

The `head()` function receives `loaderData` from the route's loader:

```tsx
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params: { postId } }) => {
    const post = await fetchPost(postId)
    return { title: post.title, description: post.excerpt }
  },
  head: ({ loaderData }) => ({
    meta: loaderData
      ? [
          { title: loaderData.title },
          { name: 'description', content: loaderData.description },
        ]
      : undefined,
  }),
  component: PostComponent,
})
```

### Composable Nested Route Heads

Each route in a hierarchy can define its own `head()`. Tags merge from parent to child, with child routes overriding duplicates:

```tsx
// routes/__root.tsx - base defaults
export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: 'UTF-8' },
      { title: 'My App' },
      { name: 'description', content: 'Default description' },
    ],
  }),
})

// routes/blog/$slug.tsx - overrides title and description with loader data
export const Route = createFileRoute('/blog/$slug')({
  loader: async ({ params }) => fetchPost(params.slug),
  head: ({ loaderData }) => ({
    meta: loaderData
      ? [
          { title: `${loaderData.title} - My App` },
          { name: 'description', content: loaderData.excerpt },
        ]
      : undefined,
  }),
})
```

## SEO Patterns

### Open Graph and Twitter Cards

```tsx
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params }) => fetchPost(params.postId),
  head: ({ loaderData }) => ({
    meta: loaderData
      ? [
          { title: loaderData.title },
          { name: 'description', content: loaderData.excerpt },
          { property: 'og:title', content: loaderData.title },
          { property: 'og:description', content: loaderData.excerpt },
          { property: 'og:image', content: loaderData.coverImage },
          { property: 'og:type', content: 'article' },
          { property: 'og:url', content: `https://example.com/posts/${loaderData.slug}` },
          { name: 'twitter:card', content: 'summary_large_image' },
          { name: 'twitter:title', content: loaderData.title },
          { name: 'twitter:description', content: loaderData.excerpt },
          { name: 'twitter:image', content: loaderData.coverImage },
        ]
      : undefined,
    links: loaderData
      ? [{ rel: 'canonical', href: `https://example.com/posts/${loaderData.slug}` }]
      : undefined,
  }),
})
```

### Structured Data (JSON-LD)

Use the `scripts` array in `head()` to inject JSON-LD:

```tsx
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params }) => fetchPost(params.postId),
  head: ({ loaderData }) => ({
    meta: loaderData ? [{ title: loaderData.title }] : undefined,
    scripts: loaderData
      ? [
          {
            type: 'application/ld+json',
            children: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'Article',
              headline: loaderData.title,
              description: loaderData.excerpt,
              image: loaderData.coverImage,
              author: { '@type': 'Person', name: loaderData.author.name },
              datePublished: loaderData.publishedAt,
              dateModified: loaderData.updatedAt,
            }),
          },
        ]
      : undefined,
  }),
})
```

### Reusable SEO Helper

Create a shared utility for consistent meta tags across routes:

```tsx
// src/utils/seo.ts
interface SeoOptions {
  title: string
  description: string
  image?: string
  url?: string
  type?: string
  twitterCard?: 'summary' | 'summary_large_image'
  twitterSite?: string
}

export function seo(options: SeoOptions) {
  const {
    title, description, image, url,
    type = 'website',
    twitterCard = 'summary_large_image',
    twitterSite,
  } = options

  return {
    meta: [
      { title },
      { name: 'description', content: description },
      { property: 'og:title', content: title },
      { property: 'og:description', content: description },
      { property: 'og:type', content: type },
      ...(image ? [{ property: 'og:image', content: image }] : []),
      ...(url ? [{ property: 'og:url', content: url }] : []),
      { name: 'twitter:card', content: twitterCard },
      { name: 'twitter:title', content: title },
      { name: 'twitter:description', content: description },
      ...(image ? [{ name: 'twitter:image', content: image }] : []),
      ...(twitterSite ? [{ name: 'twitter:site', content: twitterSite }] : []),
    ],
    links: url ? [{ rel: 'canonical', href: url }] : [],
  }
}

// Usage in a route:
export const Route = createFileRoute('/posts/$postId')({
  loader: async ({ params }) => fetchPost(params.postId),
  head: ({ loaderData }) => {
    if (!loaderData) return {}
    return seo({
      title: `${loaderData.title} - My Blog`,
      description: loaderData.excerpt,
      image: loaderData.coverImage,
      url: `https://example.com/posts/${loaderData.slug}`,
      type: 'article',
    })
  },
})
```

## Best Practices

1. **Use TanStack Start for new projects.** Start handles SSR, streaming, server functions, code splitting, and deployment out of the box. Only use manual Router SSR when integrating with an existing custom server or when you need fine-grained control over the rendering pipeline.

2. **Always create the router in a shared file.** Both server and client entry points must import the same `createRouter` function to ensure consistent route trees and configuration between environments.

3. **Prefer streaming SSR for pages with slow data.** Use `renderRouterToStream` or `defaultStreamHandler` when routes fetch from slow APIs. The critical first paint arrives immediately while deferred data streams in progressively.

4. **Place HeadContent in the head and Scripts at the end of body.** `<HeadContent />` must be rendered inside `<head>` (or as high as possible in SPAs). `<Scripts />` goes inside `<body>`, after `<Outlet />`, so body scripts load before hydration but after the DOM is available.

5. **Use the seo helper pattern for consistent meta tags.** A shared utility that generates Open Graph, Twitter Card, and canonical URL tags from a single options object prevents tag omissions and keeps structure consistent.

6. **Set `suppressHydrationWarning` on elements modified by ScriptOnce.** If an inline script modifies the DOM before React hydrates (like adding a theme class to `<html>`), add `suppressHydrationWarning` to the affected element.

7. **Handle Express-to-Web-API conversion carefully.** `createRequestHandler` expects a standard `Request` and returns a `Response`. When using Express, convert `req` to `Request` and pipe `response.body` back through `res` using `pipeline` from `node:stream/promises`.
