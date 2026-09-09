# Observability

Monitoring, logging, and debugging Workers in production.

## Logging

### Real-time Logs (Wrangler Tail)

View logs in real-time during development and production.

```bash
# Tail all logs
wrangler tail

# Tail specific environment
wrangler tail --env production

# Filter by status
wrangler tail --status error
wrangler tail --status ok

# Filter by HTTP method
wrangler tail --method POST

# Filter by header
wrangler tail --header "User-Agent: Chrome"

# Filter by IP
wrangler tail --ip 203.0.113.1

# Search in logs
wrangler tail --search "database error"

# Sample rate (% of requests)
wrangler tail --sampling-rate 0.1  # 10%

# Pretty format
wrangler tail --format pretty
```

### Console Logging

Use console methods in your Worker.

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Log levels
    console.log("Info message", { userId: 123 });
    console.info("Info message");
    console.warn("Warning message");
    console.error("Error message", error);
    console.debug("Debug message", { data });

    // Structured logging
    console.log(JSON.stringify({
      level: "info",
      timestamp: Date.now(),
      message: "Request processed",
      userId: 123,
      duration: 45,
    }));

    return new Response("OK");
  },
};
```

### Workers Logs

Persistent logs stored in Cloudflare (Enterprise feature).

**Enable via Dashboard:**
1. Workers & Pages → Logs
2. Enable Workers Logs
3. Set retention period (1-30 days)

**Query logs:**

```bash
# Via GraphQL API
curl -X POST https://api.cloudflare.com/client/v4/graphql \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { viewer { accounts(filter: {accountTag: \"$ACCOUNT_ID\"}) { workersLogsData(filter: {datetime_gt: \"2025-09-01T00:00:00Z\"}) { logs { timestamp message } } } } }"
  }'
```

**Filter logs:**

```typescript
// Add custom fields for filtering
console.log(JSON.stringify({
  level: "error",
  service: "api",
  endpoint: "/users",
  userId: "123",
  error: error.message,
}));
```

### Logpush Integration

Stream logs to external services.

**Supported destinations:**
- Amazon S3
- Google Cloud Storage
- Azure Blob Storage
- Datadog
- Splunk
- New Relic
- HTTP endpoint

**Setup via Dashboard:**
1. Logs → Workers Logs → Create Job
2. Select destination
3. Configure filters
4. Set fields to include

**Fields available:**
- `timestamp` - Request timestamp
- `level` - Log level (log, error, warn, info, debug)
- `message` - Log message
- `scriptName` - Worker name
- `outcome` - Request outcome (ok, exception, exceededCpu, etc.)
- `logs` - Array of console.log() messages

### Custom Logging Service

Send logs to your own service.

```typescript
interface LogEntry {
  level: "info" | "warn" | "error";
  message: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

class Logger {
  constructor(private env: Env) {}

  private async send(entry: LogEntry) {
    // Send to logging service
    await fetch("https://logs.example.com/ingest", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.env.LOG_TOKEN}`,
      },
      body: JSON.stringify(entry),
    });
  }

  info(message: string, metadata?: Record<string, any>) {
    const entry: LogEntry = {
      level: "info",
      message,
      timestamp: Date.now(),
      metadata,
    };

    console.log(JSON.stringify(entry));
    this.send(entry).catch(console.error);
  }

  error(message: string, error: Error, metadata?: Record<string, any>) {
    const entry: LogEntry = {
      level: "error",
      message,
      timestamp: Date.now(),
      metadata: {
        ...metadata,
        error: error.message,
        stack: error.stack,
      },
    };

    console.error(JSON.stringify(entry));
    this.send(entry).catch(console.error);
  }
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const logger = new Logger(env);

    try {
      logger.info("Request received", {
        url: request.url,
        method: request.method,
      });

      const response = await handleRequest(request, env);

      logger.info("Request completed", {
        status: response.status,
      });

      return response;
    } catch (error) {
      logger.error("Request failed", error as Error, {
        url: request.url,
      });

      throw error;
    }
  },
};
```

## Metrics and Analytics

### Workers Analytics

View request metrics in the dashboard.

**Available metrics:**
- Requests (count, rate)
- Errors (count, rate)
- Success rate
- CPU time (p50, p99)
- Duration (p50, p99)
- Subrequests

**Filter by:**
- Time range
- Status code
- Path
- User agent
- Country

### GraphQL Analytics API

Query analytics programmatically.

```typescript
const query = `
  query {
    viewer {
      accounts(filter: {accountTag: "${accountId}"}) {
        workersInvocationsAdaptive(
          filter: {
            datetime_gt: "2025-09-01T00:00:00Z"
            datetime_lt: "2025-01-02T00:00:00Z"
            scriptName: "my-worker"
          }
          limit: 100
        ) {
          sum {
            requests
            errors
            subrequests
          }
          quantiles {
            cpuTimeP50
            cpuTimeP99
            durationP50
            durationP99
          }
        }
      }
    }
  }
`;

const response = await fetch("https://api.cloudflare.com/client/v4/graphql", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ query }),
});

const data = await response.json();
```

### Custom Metrics (Analytics Engine)

Write custom metrics to Analytics Engine.

**Configuration:**

```toml
[[analytics_engine_datasets]]
binding = "ANALYTICS"
```

**Write data points:**

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const start = Date.now();

    try {
      const response = await handleRequest(request, env);
      const duration = Date.now() - start;

      // Write metrics
      ctx.waitUntil(
        env.ANALYTICS.writeDataPoint({
          // String fields (up to 20)
          blobs: [
            request.url,
            request.method,
            String(response.status),
            request.headers.get("user-agent") || "unknown",
          ],
          // Numeric fields (up to 20)
          doubles: [
            duration,
            response.headers.get("content-length")
              ? parseInt(response.headers.get("content-length")!)
              : 0,
          ],
          // Indexed fields (up to 20) - for filtering
          indexes: [
            request.cf?.country as string || "unknown",
            request.cf?.colo as string || "unknown",
          ],
        })
      );

      return response;
    } catch (error) {
      const duration = Date.now() - start;

      ctx.waitUntil(
        env.ANALYTICS.writeDataPoint({
          blobs: [request.url, request.method, "error"],
          doubles: [duration],
          indexes: ["error"],
        })
      );

      throw error;
    }
  },
};
```

**Query metrics:**

```sql
SELECT
  blob1 AS url,
  blob2 AS method,
  blob3 AS status,
  COUNT() AS requests,
  AVG(double1) AS avg_duration,
  MAX(double1) AS max_duration
FROM ANALYTICS_DATASET
WHERE
  timestamp >= NOW() - INTERVAL '1' DAY
  AND index1 = 'US'
GROUP BY blob1, blob2, blob3
ORDER BY requests DESC
LIMIT 100
```

## Traces (OpenTelemetry)

Export traces to observability platforms.

**Supported platforms:**
- Datadog
- New Relic
- Honeycomb
- Grafana Cloud
- Sentry

### Export to Honeycomb

```typescript
import { trace } from "@opentelemetry/api";
import { WorkersSDK } from "@cloudflare/workers-honeycomb-logger";

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const sdk = new WorkersSDK(request, env, ctx, {
      apiKey: env.HONEYCOMB_API_KEY,
      dataset: "my-worker",
    });

    const tracer = trace.getTracer("my-worker");

    return tracer.startActiveSpan("fetch", async (span) => {
      try {
        span.setAttribute("http.method", request.method);
        span.setAttribute("http.url", request.url);

        const response = await handleRequest(request, env);

        span.setAttribute("http.status_code", response.status);
        span.end();

        return response;
      } catch (error) {
        span.recordException(error as Error);
        span.end();
        throw error;
      }
    });
  },
};
```

### Export to Datadog

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const startTime = Date.now();

    try {
      const response = await handleRequest(request, env);
      const duration = Date.now() - startTime;

      // Send trace to Datadog
      ctx.waitUntil(
        fetch("https://http-intake.logs.datadoghq.com/v1/input", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "DD-API-KEY": env.DATADOG_API_KEY,
          },
          body: JSON.stringify({
            ddsource: "cloudflare-workers",
            service: "my-worker",
            message: "Request completed",
            duration,
            status: response.status,
            url: request.url,
            method: request.method,
          }),
        })
      );

      return response;
    } catch (error) {
      // Log error to Datadog
      ctx.waitUntil(
        fetch("https://http-intake.logs.datadoghq.com/v1/input", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "DD-API-KEY": env.DATADOG_API_KEY,
          },
          body: JSON.stringify({
            ddsource: "cloudflare-workers",
            service: "my-worker",
            status: "error",
            error: {
              message: (error as Error).message,
              stack: (error as Error).stack,
            },
          }),
        })
      );

      throw error;
    }
  },
};
```

## Error Tracking

### Error Boundaries

Catch and track errors globally.

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    try {
      return await handleRequest(request, env, ctx);
    } catch (error) {
      // Log error
      console.error("Unhandled error:", error);

      // Send to error tracking service
      ctx.waitUntil(reportError(error as Error, request, env));

      // Return error response
      return Response.json(
        {
          error: "Internal server error",
          requestId: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }
  },
};

async function reportError(error: Error, request: Request, env: Env) {
  await fetch("https://errors.example.com/report", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${env.ERROR_TOKEN}`,
    },
    body: JSON.stringify({
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name,
      },
      request: {
        url: request.url,
        method: request.method,
        headers: Object.fromEntries(request.headers),
      },
      timestamp: Date.now(),
    }),
  });
}
```

### Sentry Integration

```bash
npm install @sentry/browser
```

```typescript
import * as Sentry from "@sentry/browser";

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    Sentry.init({
      dsn: env.SENTRY_DSN,
      environment: env.ENVIRONMENT,
    });

    try {
      return await handleRequest(request, env);
    } catch (error) {
      Sentry.captureException(error);
      throw error;
    }
  },
};
```

## Performance Monitoring

### Request Timing

Track request performance.

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const timings = {
      start: Date.now(),
      auth: 0,
      database: 0,
      external: 0,
      total: 0,
    };

    // Auth
    const authStart = Date.now();
    const user = await authenticate(request, env);
    timings.auth = Date.now() - authStart;

    // Database
    const dbStart = Date.now();
    const data = await env.DB.prepare("SELECT * FROM users WHERE id = ?")
      .bind(user.id)
      .first();
    timings.database = Date.now() - dbStart;

    // External API
    const apiStart = Date.now();
    const externalData = await fetch("https://api.example.com/data");
    timings.external = Date.now() - apiStart;

    timings.total = Date.now() - timings.start;

    // Log timings
    console.log("Performance:", timings);

    // Add to response headers
    return Response.json(data, {
      headers: {
        "X-Timing-Auth": String(timings.auth),
        "X-Timing-Database": String(timings.database),
        "X-Timing-External": String(timings.external),
        "X-Timing-Total": String(timings.total),
      },
    });
  },
};
```

### Performance API

Use the Performance API for detailed timing.

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    performance.mark("start");

    performance.mark("db-start");
    await queryDatabase();
    performance.mark("db-end");
    performance.measure("database", "db-start", "db-end");

    performance.mark("api-start");
    await fetchExternal();
    performance.mark("api-end");
    performance.measure("external", "api-start", "api-end");

    performance.mark("end");
    performance.measure("total", "start", "end");

    // Get measurements
    const measurements = performance.getEntriesByType("measure");

    console.log("Performance measurements:", measurements);

    return Response.json({ ok: true });
  },
};
```

## Debugging

### Local Debugging

Debug Workers locally with DevTools.

```bash
# Start with inspector
wrangler dev --inspector

# Connect Chrome DevTools
# Open chrome://inspect in Chrome
# Click "inspect" on your Worker
```

**Features:**
- Set breakpoints
- Step through code
- Inspect variables
- View console logs
- Profile performance

### Remote Debugging

Debug production Workers.

**Using console.log:**

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    console.log("Request:", {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers),
    });

    const response = await handleRequest(request, env);

    console.log("Response:", {
      status: response.status,
      headers: Object.fromEntries(response.headers),
    });

    return response;
  },
};
```

**View logs:**

```bash
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

### Debugging Tips

1. **Use structured logging** - JSON format for easier parsing
2. **Log request IDs** - Track requests across services
3. **Time operations** - Identify performance bottlenecks
4. **Test locally first** - Use `wrangler dev` before deploying
5. **Use staging environment** - Test in production-like environment
6. **Monitor after deploy** - Watch logs and metrics after deployment

## Alerting

### Custom Alerts

Send alerts based on metrics.

```typescript
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    try {
      const response = await handleRequest(request, env);

      // Alert on slow requests
      const duration = Date.now() - startTime;
      if (duration > 5000) {
        ctx.waitUntil(sendAlert("Slow request", { duration, url: request.url }, env));
      }

      return response;
    } catch (error) {
      // Alert on errors
      ctx.waitUntil(sendAlert("Request error", { error: error.message }, env));
      throw error;
    }
  },
};

async function sendAlert(message: string, data: any, env: Env) {
  // Send to Slack
  await fetch(env.SLACK_WEBHOOK, {
    method: "POST",
    body: JSON.stringify({
      text: `🚨 ${message}`,
      blocks: [
        {
          type: "section",
          text: { type: "mrkdwn", text: `*${message}*` },
        },
        {
          type: "section",
          text: { type: "mrkdwn", text: `\`\`\`${JSON.stringify(data, null, 2)}\`\`\`` },
        },
      ],
    }),
  });
}
```

## Health Checks

Implement health check endpoints.

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return healthCheck(env);
    }

    return handleRequest(request, env);
  },
};

async function healthCheck(env: Env): Promise<Response> {
  const checks = {
    database: false,
    kv: false,
    external: false,
  };

  // Check database
  try {
    await env.DB.prepare("SELECT 1").first();
    checks.database = true;
  } catch (error) {
    console.error("Database check failed:", error);
  }

  // Check KV
  try {
    await env.MY_KV.get("health-check");
    checks.kv = true;
  } catch (error) {
    console.error("KV check failed:", error);
  }

  // Check external API
  try {
    const response = await fetch("https://api.example.com/health", {
      signal: AbortSignal.timeout(2000),
    });
    checks.external = response.ok;
  } catch (error) {
    console.error("External API check failed:", error);
  }

  const allHealthy = Object.values(checks).every((c) => c);

  return Response.json(
    { healthy: allHealthy, checks },
    { status: allHealthy ? 200 : 503 }
  );
}
```

## Additional Resources

- **Observability**: https://developers.cloudflare.com/workers/observability/
- **Logs**: https://developers.cloudflare.com/workers/observability/logs/
- **Metrics**: https://developers.cloudflare.com/workers/observability/metrics-and-analytics/
- **Traces**: https://developers.cloudflare.com/workers/observability/traces/
- **Dev Tools**: https://developers.cloudflare.com/workers/observability/dev-tools/
