# Discovery and the Payments Proxy

Two related surfaces: making an existing API payable (`mppx/proxy`), and publishing a machine-readable description of what your service charges for (`mppx/discovery`).

## Payments Proxy (`mppx/proxy`)

Gate an upstream API behind MPP payments without touching it.

```ts
import { Proxy, openai, anthropic, stripe } from 'mppx/proxy'
import { Mppx, tempo } from 'mppx/server'

const mppx = Mppx.create({
  methods: [tempo()],
  secretKey: process.env.MPP_SECRET_KEY,
})

const proxy = Proxy.create({
  title: 'My API Proxy',
  description: 'Paid access to AI APIs',
  basePath: '/api',
  services: [
    openai({
      apiKey: process.env.OPENAI_API_KEY,
      routes: {
        'POST /v1/chat/completions': mppx.charge({ amount: '0.005' }),
        'GET /v1/models': true, // free passthrough
      },
    }),
    anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY,
      routes: { 'POST /v1/messages': mppx.charge({ amount: '0.01' }) },
    }),
  ],
})
```

Built-in service presets, all from `mppx/proxy`: `openai()`, `anthropic()`, `stripe()`.

### Free Routes

A route is free when its value is the literal `true`. There is no `mppx.free()` helper.

```ts
routes: {
  'GET /v1/models': true,                              // free passthrough
  'POST /v1/chat/completions': mppx.charge({ amount: '0.005' }),
}
```

Free routes still run `rewriteRequest`, so header injection and path rewriting apply as normal.

### Custom Services

`Service.from` (exported as `custom`) wraps any upstream:

```ts
import { Proxy, custom } from 'mppx/proxy'

const service = custom({
  title: 'Internal Search',
  baseUrl: 'https://search.internal.example.com',
  bearer: process.env.SEARCH_TOKEN,        // Authorization: Bearer <token>
  headers: { 'X-Client': 'mpp-proxy' },    // static headers on every upstream call
  docs: { homepage: '...', apiReference: '...' },
  docsLlmsUrl: 'https://example.com/llms.txt',
  rewriteRequest: (req, ctx) => req,       // mutate the upstream request
  rewriteResponse: (res, ctx) => res,      // mutate the response on the way back
  routes: {
    'POST /search': { pay: mppx.charge({ amount: '0.002' }), options: { apiKey: '...' } },
    'GET /health': true,
  },
})
```

Route values accept a payment handler, the literal `true`, or a `{ pay, options }` object when a single endpoint needs its own per-endpoint configuration.

### Handlers

```ts
// Fetch API (Cloudflare Workers, Bun, Deno, Next.js, Hono, Elysia, SvelteKit)
export default { fetch: proxy.fetch }

// Node.js http server
import http from 'node:http'
http.createServer(proxy.listener).listen(3000)
```

### Discovery Endpoints

The proxy auto-serves these (all active):

- `GET /discover` - JSON service list
- `GET /discover/{id}` and `GET /discover/{id}.md` - single service detail
- `GET /discover/all` and `GET /discover/all.md` - all services with full route details
- `GET /llms.txt` - LLM-readable overview (`GET /discover.md` is an alias)

Content negotiation is user-agent aware: the proxy returns markdown instead of JSON when the caller is a known AI user agent (for example `ChatGPT-User`, `ClaudeBot`, `PerplexityBot`) or a terminal client (`curl`, `HTTPie`, `mppx`). Agents therefore get readable docs from the same URLs a program gets JSON from.

## Discovery Documents (`mppx/discovery`)

Any server can publish a discovery document without running a proxy. The `discovery()` helper generates a `GET /openapi.json` endpoint from your route configuration, annotating each paid route with canonical `x-payment-info.offers[]` entries, plus service-level `x-service-info`.

```ts
import { discovery } from 'mppx/discovery'

app.route('/', discovery({
  title: 'My API',
  description: 'Paid endpoints',
  routes: {
    'POST /summarize': mppx.charge({ amount: '0.01' }),
  },
}))
```

Helpers for Next.js and a CLI for static generation ship alongside it; `mppx discover generate` and `mppx discover validate` drive the same machinery from the command line.

### Registries

Register the service so agents can find it:

- [MPPScan](https://mppscan.com) - public registry with search and analytics (one-click register)
- [MPP Services directory](https://mpp.dev/services) - curated list (submit a PR)
- `mppx services` browses the registry from the CLI
- [Services MCP](https://mpp.dev/mcp/services) - agent-facing discovery of the curated directory

Note that MPPScan attributes payments by **realm**, not by transaction hash, and session traffic settles off-chain - see `references/production-gotchas.md` for what that means for reported volume.
