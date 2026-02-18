# Development Best Practices

Patterns and best practices for building robust, maintainable Workers applications.

## Testing

### Vitest Integration

Workers has first-class Vitest integration for unit and integration testing.

**Setup:**

```bash
npm install -D vitest @cloudflare/vitest-pool-workers
```

**vitest.config.ts:**

```typescript
import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: "./wrangler.toml" },
      },
    },
  },
});
```

**Basic Test:**

```typescript
import { env, createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "./index";

describe("Worker", () => {
  it("responds with JSON", async () => {
    const request = new Request("http://example.com/api/users");
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty("users");
  });

  it("handles errors gracefully", async () => {
    const request = new Request("http://example.com/api/error");
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);

    expect(response.status).toBe(500);
  });
});
```

**Testing with Bindings:**

```typescript
import { env } from "cloudflare:test";

describe("KV operations", () => {
  it("reads and writes to KV", async () => {
    // env provides access to bindings configured in wrangler.toml
    await env.MY_KV.put("test-key", "test-value");
    const value = await env.MY_KV.get("test-key");
    expect(value).toBe("test-value");
  });
});
```

**Testing Durable Objects:**

```typescript
import { env, runInDurableObject } from "cloudflare:test";

describe("Counter Durable Object", () => {
  it("increments counter", async () => {
    await runInDurableObject(env.COUNTER, async (instance, state) => {
      const request = new Request("http://do/increment");
      const response = await instance.fetch(request);
      const data = await response.json();
      expect(data.count).toBe(1);
    });
  });
});
```

**Run Tests:**

```bash
npm test
# or
npx vitest
```

### Integration Testing

Test full request/response cycles with external services.

```typescript
describe("External API integration", () => {
  it("fetches data from external API", async () => {
    const request = new Request("http://example.com/api/external");
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);

    expect(response.status).toBe(200);

    // Verify external API was called correctly
    const data = await response.json();
    expect(data).toHaveProperty("externalData");
  });
});
```

### Mocking

Mock external dependencies for isolated tests.

```typescript
import { vi } from "vitest";

describe("Mocked fetch", () => {
  it("handles fetch errors", async () => {
    // Mock global fetch
    global.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

    const request = new Request("http://example.com/api/data");
    const ctx = createExecutionContext();
    const response = await worker.fetch(request, env, ctx);

    expect(response.status).toBe(503);
  });
});
```

## Error Handling

### Global Error Handling

Catch all errors and return appropriate responses.

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    try {
      return await handleRequest(request, env, ctx);
    } catch (error) {
      console.error("Uncaught error:", error);

      return Response.json(
        {
          error: "Internal server error",
          message: error instanceof Error ? error.message : "Unknown error",
        },
        { status: 500 }
      );
    }
  },
};

async function handleRequest(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
  // Your handler logic
}
```

### Custom Error Classes

Define custom error types for better error handling.

```typescript
class NotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NotFoundError";
  }
}

class UnauthorizedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "UnauthorizedError";
  }
}

class ValidationError extends Error {
  constructor(public fields: Record<string, string>) {
    super("Validation failed");
    this.name = "ValidationError";
  }
}

async function handleRequest(request: Request, env: Env): Promise<Response> {
  try {
    // Your logic
    const user = await getUser(userId);
    if (!user) {
      throw new NotFoundError("User not found");
    }

    return Response.json(user);
  } catch (error) {
    if (error instanceof NotFoundError) {
      return Response.json({ error: error.message }, { status: 404 });
    }

    if (error instanceof UnauthorizedError) {
      return Response.json({ error: error.message }, { status: 401 });
    }

    if (error instanceof ValidationError) {
      return Response.json(
        { error: "Validation failed", fields: error.fields },
        { status: 400 }
      );
    }

    // Unknown error
    console.error("Unexpected error:", error);
    return Response.json({ error: "Internal server error" }, { status: 500 });
  }
}
```

### Retry Logic

Implement retry logic for transient failures.

```typescript
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  maxRetries = 3
): Promise<Response> {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);

      if (response.ok) {
        return response;
      }

      // Don't retry on client errors (4xx)
      if (response.status >= 400 && response.status < 500) {
        return response;
      }

      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error as Error;
    }

    // Exponential backoff
    if (i < maxRetries - 1) {
      await new Promise((resolve) => setTimeout(resolve, Math.pow(2, i) * 1000));
    }
  }

  throw lastError!;
}
```

## Performance Optimization

### Caching Strategies

Use the Cache API effectively.

```typescript
async function handleCachedRequest(request: Request): Promise<Response> {
  const cache = caches.default;
  const cacheKey = new Request(request.url, request);

  // Try to get from cache
  let response = await cache.match(cacheKey);

  if (!response) {
    // Cache miss - fetch from origin
    response = await fetchFromOrigin(request);

    // Cache successful responses
    if (response.ok) {
      response = new Response(response.body, {
        ...response,
        headers: {
          ...Object.fromEntries(response.headers),
          "Cache-Control": "public, max-age=3600",
        },
      });

      // Don't await - cache in background
      ctx.waitUntil(cache.put(cacheKey, response.clone()));
    }
  }

  return response;
}
```

**Cache with custom keys:**

```typescript
function getCacheKey(request: Request, userId?: string): Request {
  const url = new URL(request.url);

  // Include user ID in cache key for personalized content
  if (userId) {
    url.searchParams.set("userId", userId);
  }

  return new Request(url.toString(), request);
}
```

### Response Streaming

Stream responses for large data.

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();

    // Stream data in background
    (async () => {
      try {
        const data = await fetchLargeDataset();

        for (const item of data) {
          await writer.write(new TextEncoder().encode(JSON.stringify(item) + "\n"));
        }

        await writer.close();
      } catch (error) {
        await writer.abort(error);
      }
    })();

    return new Response(readable, {
      headers: {
        "Content-Type": "application/x-ndjson",
        "Transfer-Encoding": "chunked",
      },
    });
  },
};
```

### Batching Operations

Batch multiple operations for better performance.

```typescript
// Bad: Sequential operations
for (const userId of userIds) {
  await env.KV.get(`user:${userId}`);
}

// Good: Batch operations
const users = await Promise.all(
  userIds.map((id) => env.KV.get(`user:${id}`))
);

// Even better: Use batch APIs when available
const results = await env.DB.batch([
  env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(1),
  env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(2),
  env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(3),
]);
```

### Background Tasks

Use `ctx.waitUntil()` for non-critical work.

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // Process request
    const response = await handleRequest(request, env);

    // Log analytics in background (don't block response)
    ctx.waitUntil(
      env.ANALYTICS.writeDataPoint({
        blobs: [request.url, request.method],
        doubles: [performance.now()],
      })
    );

    // Update cache in background
    ctx.waitUntil(updateCache(request, response, env));

    return response;
  },
};
```

## Debugging

### Console Logging

Use console methods for debugging.

```typescript
console.log("Info:", { userId, action });
console.error("Error occurred:", error);
console.warn("Deprecated API used");
console.debug("Debug info:", data);

// Structured logging
console.log(JSON.stringify({
  level: "info",
  timestamp: Date.now(),
  userId,
  action,
}));
```

### Wrangler Tail

View real-time logs during development.

```bash
# Tail logs
wrangler tail

# Filter by status
wrangler tail --status error

# Filter by method
wrangler tail --method POST

# Pretty format
wrangler tail --format pretty
```

### Source Maps

Enable source maps for better error traces.

**tsconfig.json:**

```json
{
  "compilerOptions": {
    "sourceMap": true
  }
}
```

**wrangler.toml:**

```toml
upload_source_maps = true
```

### Local Debugging

Use DevTools for debugging.

```bash
# Start with inspector
wrangler dev --inspector
```

Then open `chrome://inspect` in Chrome and connect to the worker.

### Breakpoints

Set breakpoints in your code.

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    debugger;  // Execution will pause here

    const data = await fetchData();
    return Response.json(data);
  },
};
```

## Code Organization

### Router Pattern

Organize routes cleanly.

```typescript
interface Route {
  pattern: URLPattern;
  handler: (request: Request, env: Env, params: URLPatternResult) => Promise<Response>;
}

const routes: Route[] = [
  {
    pattern: new URLPattern({ pathname: "/api/users" }),
    handler: handleGetUsers,
  },
  {
    pattern: new URLPattern({ pathname: "/api/users/:id" }),
    handler: handleGetUser,
  },
  {
    pattern: new URLPattern({ pathname: "/api/users" }),
    handler: handleCreateUser,
  },
];

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    for (const route of routes) {
      const match = route.pattern.exec(request.url);
      if (match) {
        return route.handler(request, env, match);
      }
    }

    return Response.json({ error: "Not found" }, { status: 404 });
  },
};

async function handleGetUsers(request: Request, env: Env): Promise<Response> {
  const users = await env.DB.prepare("SELECT * FROM users").all();
  return Response.json(users.results);
}
```

### Middleware Pattern

Chain middleware for cross-cutting concerns.

```typescript
type Middleware = (
  request: Request,
  env: Env,
  next: () => Promise<Response>
) => Promise<Response>;

const corsMiddleware: Middleware = async (request, env, next) => {
  if (request.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
      },
    });
  }

  const response = await next();
  response.headers.set("Access-Control-Allow-Origin", "*");
  return response;
};

const authMiddleware: Middleware = async (request, env, next) => {
  const token = request.headers.get("Authorization");

  if (!token) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Validate token
  const isValid = await validateToken(token, env);
  if (!isValid) {
    return Response.json({ error: "Invalid token" }, { status: 401 });
  }

  return next();
};

const loggingMiddleware: Middleware = async (request, env, next) => {
  const start = Date.now();
  const response = await next();
  const duration = Date.now() - start;

  console.log({
    method: request.method,
    url: request.url,
    status: response.status,
    duration,
  });

  return response;
};

function applyMiddleware(
  handler: (request: Request, env: Env) => Promise<Response>,
  middlewares: Middleware[]
): (request: Request, env: Env) => Promise<Response> {
  return (request: Request, env: Env) => {
    let index = -1;

    const dispatch = async (i: number): Promise<Response> => {
      if (i <= index) {
        throw new Error("next() called multiple times");
      }

      index = i;

      if (i === middlewares.length) {
        return handler(request, env);
      }

      const middleware = middlewares[i];
      return middleware(request, env, () => dispatch(i + 1));
    };

    return dispatch(0);
  };
}

// Usage
const handler = applyMiddleware(
  async (request, env) => {
    return Response.json({ message: "Hello!" });
  },
  [loggingMiddleware, corsMiddleware, authMiddleware]
);

export default { fetch: handler };
```

### Dependency Injection

Use environment for dependencies.

```typescript
interface Env {
  DB: D1Database;
  CACHE: KVNamespace;
}

class UserService {
  constructor(private env: Env) {}

  async getUser(id: string) {
    // Try cache first
    const cached = await this.env.CACHE.get(`user:${id}`);
    if (cached) return JSON.parse(cached);

    // Fetch from database
    const user = await this.env.DB.prepare(
      "SELECT * FROM users WHERE id = ?"
    ).bind(id).first();

    // Update cache
    if (user) {
      await this.env.CACHE.put(`user:${id}`, JSON.stringify(user), {
        expirationTtl: 3600,
      });
    }

    return user;
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const userService = new UserService(env);
    const user = await userService.getUser("123");
    return Response.json(user);
  },
};
```

### Top-level Env Access

Since March 2025, `import { env } from "cloudflare:workers"` enables accessing bindings outside of handlers. This eliminates prop-drilling `env` through function signatures:

```typescript
import { env } from "cloudflare:workers";

// Module-level initialization using bindings
const config = {
  async getFeatureFlags() {
    return env.CONFIG_KV.get("feature-flags", "json");
  },
};

// Utility functions without env parameter
export async function logEvent(event: string, data: Record<string, unknown>) {
  await env.LOGS_QUEUE.send({ event, data, timestamp: Date.now() });
}
```

This works alongside the traditional `env` parameter approach. Use whichever pattern fits your codebase.

### Runtime Feature Detection

Modern V8 features available in Workers (compat date `2025-09-01`+):

```typescript
// Explicit Resource Management (using keyword)
{
  using handle = getResource();
  // Automatically disposed when scope exits
}

// Uint8Array Base64/Hex encoding
const encoded = new Uint8Array([72, 101, 108, 108, 111]).toBase64(); // "SGVsbG8="
const decoded = Uint8Array.fromBase64("SGVsbG8=");
const hex = new Uint8Array([255, 0]).toHex(); // "ff00"

// MessageChannel / MessagePort for structured communication
const channel = new MessageChannel();
channel.port1.onmessage = (e) => console.log(e.data);
channel.port2.postMessage("hello");
```

## Security Best Practices

### Input Validation

Always validate and sanitize user input.

```typescript
import { z } from "zod";

const userSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().positive().max(150),
});

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    try {
      const body = await request.json();
      const validated = userSchema.parse(body);

      // Use validated data
      await createUser(validated, env);

      return Response.json({ success: true });
    } catch (error) {
      if (error instanceof z.ZodError) {
        return Response.json(
          { error: "Validation failed", issues: error.errors },
          { status: 400 }
        );
      }

      throw error;
    }
  },
};
```

### Rate Limiting

Implement rate limiting to prevent abuse.

```typescript
async function checkRateLimit(
  identifier: string,
  env: Env,
  limit = 100,
  window = 60
): Promise<boolean> {
  const key = `ratelimit:${identifier}`;
  const current = await env.CACHE.get(key);

  if (!current) {
    await env.CACHE.put(key, "1", { expirationTtl: window });
    return true;
  }

  const count = parseInt(current);

  if (count >= limit) {
    return false;
  }

  await env.CACHE.put(key, String(count + 1), { expirationTtl: window });
  return true;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";

    const allowed = await checkRateLimit(ip, env);

    if (!allowed) {
      return Response.json({ error: "Rate limit exceeded" }, { status: 429 });
    }

    return handleRequest(request, env);
  },
};
```

### CSRF Protection

Protect against cross-site request forgery.

```typescript
function generateCSRFToken(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return btoa(String.fromCharCode(...array));
}

async function validateCSRFToken(
  token: string,
  sessionId: string,
  env: Env
): Promise<boolean> {
  const stored = await env.SESSIONS.get(`csrf:${sessionId}`);
  return stored === token;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "POST") {
      const sessionId = request.headers.get("X-Session-ID");
      const csrfToken = request.headers.get("X-CSRF-Token");

      if (!sessionId || !csrfToken) {
        return Response.json({ error: "Missing tokens" }, { status: 403 });
      }

      const isValid = await validateCSRFToken(csrfToken, sessionId, env);

      if (!isValid) {
        return Response.json({ error: "Invalid CSRF token" }, { status: 403 });
      }
    }

    return handleRequest(request, env);
  },
};
```

## Additional Resources

- **Testing**: https://developers.cloudflare.com/workers/testing/
- **Observability**: https://developers.cloudflare.com/workers/observability/
- **Best Practices**: https://developers.cloudflare.com/workers/best-practices/
- **Examples**: https://developers.cloudflare.com/workers/examples/
