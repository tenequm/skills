# Advanced Features

Advanced Workers capabilities for complex applications and enterprise use cases.

## Workers for Platforms

Deploy and manage customer-provided Workers on your infrastructure.

**Use cases:**
- SaaS platforms where customers write custom code
- Low-code/no-code platforms
- Plugin systems
- Custom business logic hosting

### Setup

**wrangler.toml:**

```toml
[[dispatch_namespaces]]
binding = "DISPATCHER"
namespace = "my-platform"

# Optional outbound Worker
outbound = { service = "my-outbound-worker" }
```

### Dynamic Dispatch

Route requests to customer Workers dynamically.

**Dispatch Worker:**

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const customerId = url.hostname.split(".")[0];

    // Get customer's Worker
    const userWorker = env.DISPATCHER.get(customerId);

    // Forward request to customer's Worker
    return userWorker.fetch(request);
  },
};
```

### Upload User Workers

**Via API:**

```typescript
async function uploadUserWorker(
  customerId: string,
  code: string,
  env: Env
): Promise<void> {
  const response = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${env.ACCOUNT_ID}/workers/dispatch/namespaces/${env.NAMESPACE}/scripts/${customerId}`,
    {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${env.API_TOKEN}`,
        "Content-Type": "application/javascript",
      },
      body: code,
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to upload: ${await response.text()}`);
  }
}
```

**Via Wrangler:**

```bash
wrangler dispatch-namespace put my-platform customer-123 ./customer-worker.js
```

### Outbound Workers

Control what customer Workers can access.

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Validate request from customer Worker
    const url = new URL(request.url);

    // Block certain domains
    const blockedDomains = ["internal.example.com"];
    if (blockedDomains.some((d) => url.hostname.includes(d))) {
      return new Response("Forbidden", { status: 403 });
    }

    // Add authentication
    request.headers.set("X-Platform-Auth", env.PLATFORM_SECRET);

    // Forward to destination
    return fetch(request);
  },
};
```

### Limits and Quotas

Set limits for customer Workers.

```toml
[[dispatch_namespaces]]
binding = "DISPATCHER"
namespace = "my-platform"

[dispatch_namespaces.outbound]
service = "outbound-worker"
parameters = {
  cpu_ms = 50,
  requests = 1000
}
```

## Containers

Run Docker containers alongside Workers (public beta June 2025). Containers are built on Durable Objects, giving them global deployment, automatic scaling, and persistent state.

**Use cases:**
- Port existing Docker applications to Cloudflare
- Run any language or runtime (Python, Java, Go, etc.)
- Multi-GB memory workloads
- CLI tools and code sandboxes

### Container Class

```typescript
import { Container } from "cloudflare:workers";

export class MyContainer extends Container {
  // Port your container listens on
  defaultPort = 8080;

  // Auto-sleep after inactivity (saves costs)
  sleepAfter = "5 minutes";

  // Optional: override to run setup before container starts
  override async onStart(): Promise<void> {
    console.log("Container starting...");
  }
}
```

### Configuration

```toml
[[containers]]
class_name = "MyContainer"
image = "./Dockerfile"
max_instances = 5

[[durable_objects.bindings]]
class_name = "MyContainer"
name = "MY_CONTAINER"

[[migrations]]
tag = "v1"
new_classes = ["MyContainer"]
```

### Worker Usage

Workers act as orchestrator, service mesh, and API gateway to containers:

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Route to named container instance
    const id = env.MY_CONTAINER.idFromName("my-instance");
    const container = env.MY_CONTAINER.get(id);

    // Forward request - container receives it on defaultPort
    return container.fetch(request);
  },
};
```

## Workflows

Durable execution engine for multi-step, long-running tasks (GA April 2025). Steps automatically persist state and retry on failure.

**Use cases:**
- Order processing pipelines
- Human-in-the-loop approval flows
- Scheduled multi-step batch jobs
- Any process that needs to survive failures

### Workflow Class

```typescript
import { WorkflowEntrypoint, WorkflowStep, WorkflowEvent } from "cloudflare:workers";

interface OrderParams {
  orderId: string;
  items: string[];
}

export class OrderWorkflow extends WorkflowEntrypoint<Env, OrderParams> {
  async run(event: WorkflowEvent<OrderParams>, step: WorkflowStep) {
    // Step 1: Validate (durable - retries on failure)
    const order = await step.do("validate", async () => {
      const result = await this.env.DB.prepare(
        "SELECT * FROM orders WHERE id = ?"
      ).bind(event.payload.orderId).first();
      if (!result) throw new Error("Order not found");
      return result;
    });

    // Step 2: Sleep without holding compute
    await step.sleep("processing-delay", "30 minutes");

    // Step 3: Wait for external event (webhook, human approval)
    const approval = await step.waitForEvent("await-approval", {
      timeout: "24 hours",
    });

    if (!approval.payload.approved) {
      await step.do("cancel", async () => {
        await this.env.DB.prepare(
          "UPDATE orders SET status = 'cancelled' WHERE id = ?"
        ).bind(event.payload.orderId).run();
      });
      return;
    }

    // Step 4: Fulfill
    await step.do("fulfill", async () => {
      await this.env.DB.prepare(
        "UPDATE orders SET status = 'fulfilled' WHERE id = ?"
      ).bind(event.payload.orderId).run();
    });
  }
}
```

### Configuration

```toml
[[workflows]]
name = "order-workflow"
binding = "ORDER_WORKFLOW"
class_name = "OrderWorkflow"
```

### Managing Workflow Instances

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Create instance
    const instance = await env.ORDER_WORKFLOW.create({
      params: { orderId: "123", items: ["item-1"] },
    });

    // Check status
    const status = await instance.status();

    // Send event to waiting step
    await instance.sendEvent({ approved: true });

    // List all instances
    const instances = await env.ORDER_WORKFLOW.list();

    return Response.json({ id: instance.id, status });
  },
};
```

## MCP Server Support

Host remote Model Context Protocol (MCP) servers on Workers using the Agents SDK.

```typescript
import { McpAgent } from "agents/mcp";

export class MyMcpServer extends McpAgent {
  server = new Server({ name: "my-mcp-server", version: "1.0.0" });

  async init() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [{
        name: "get_weather",
        description: "Get weather for a city",
        inputSchema: { type: "object", properties: { city: { type: "string" } } },
      }],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      if (request.params.name === "get_weather") {
        return { content: [{ type: "text", text: "Sunny, 72F" }] };
      }
    });
  }
}
```

MCP servers on Workers support Streamable HTTP transport and can be secured with OAuth via the `workers-oauth-provider` package.

## Node.js Compatibility Expansion

Workers now supports a much broader set of Node.js APIs via the `nodejs_compat` flag:

| Module | Available Since | Notes |
|--------|----------------|-------|
| `node:net` | Jan 2025 | TCP `Socket` connections |
| `node:dns` | Jan 2025 | DNS resolution |
| `node:timers` | Jan 2025 | Node-compatible timers |
| `node:fs` | Sep 2025 | Virtual per-request file system (ephemeral) |
| `node:http` | Sep 2025 | Port Express-style apps with minimal changes |

**Compat flags:**
- `nodejs_compat` - enables all Node.js built-in modules
- `nodejs_compat_populate_process_env` - auto-populates `process.env` with text bindings
- `enable_nodejs_fs_module` - enables `node:fs` on compat dates before `2025-09-01`

With compat date `2025-09-01` or later, `node:fs` is enabled by default under `nodejs_compat`.

```typescript
// Example: Using node:fs (per-request virtual filesystem)
import { writeFileSync, readFileSync } from "node:fs";

export default {
  async fetch(request: Request): Promise<Response> {
    writeFileSync("/tmp/data.json", JSON.stringify({ key: "value" }));
    const data = readFileSync("/tmp/data.json", "utf-8");
    return new Response(data);
  },
};
```

## Cloudflare Realtime

Managed SFU (Selective Forwarding Unit) and TURN service for WebRTC audio/video (April 2025).

**Use cases:**
- Video/audio calls
- AI-powered voice agents
- Live streaming

Workers integrates with the RealtimeKit SDK for building real-time communication features. TURN service is global anycast and free when used with Realtime SFU.

- **Realtime Docs**: https://developers.cloudflare.com/realtime/

## Smart Placement

Automatically place Workers near data sources to reduce latency.

### Enable Smart Placement

**wrangler.toml:**

```toml
[placement]
mode = "smart"
```

**How it works:**
- Workers monitors where your Worker makes subrequests
- Automatically places future executions near those data sources
- Reduces round-trip time for database/API calls
- No code changes required

**Best for:**
- Database-heavy Workers
- Workers making many external API calls
- Geographically distributed data sources

**Limitations:**
- Not compatible with Durable Objects
- Requires Workers Standard plan

## WebSockets

Build real-time applications with WebSockets. Maximum message size is 32 MiB.

### Basic WebSocket Server

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const upgradeHeader = request.headers.get("Upgrade");

    if (upgradeHeader !== "websocket") {
      return new Response("Expected WebSocket", { status: 426 });
    }

    const [client, server] = Object.values(new WebSocketPair());

    // Handle WebSocket messages
    server.accept();

    server.addEventListener("message", (event) => {
      console.log("Received:", event.data);

      // Echo message back
      server.send(`Echo: ${event.data}`);
    });

    server.addEventListener("close", (event) => {
      console.log("WebSocket closed:", event.code, event.reason);
    });

    server.addEventListener("error", (event) => {
      console.error("WebSocket error:", event);
    });

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  },
};
```

### WebSocket with Durable Objects

Use Durable Objects for coordinated WebSocket servers.

**Durable Object:**

```typescript
export class ChatRoom {
  state: DurableObjectState;
  sessions: Set<WebSocket>;

  constructor(state: DurableObjectState) {
    this.state = state;
    this.sessions = new Set();
  }

  async fetch(request: Request): Promise<Response> {
    const [client, server] = Object.values(new WebSocketPair());

    server.accept();
    this.sessions.add(server);

    server.addEventListener("message", (event) => {
      // Broadcast to all connected clients
      this.broadcast(event.data as string);
    });

    server.addEventListener("close", () => {
      this.sessions.delete(server);
    });

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }

  broadcast(message: string) {
    for (const session of this.sessions) {
      try {
        session.send(message);
      } catch (error) {
        // Remove failed sessions
        this.sessions.delete(session);
      }
    }
  }
}
```

**Worker:**

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const roomId = url.pathname.substring(1) || "default";

    // Get Durable Object for this room
    const id = env.CHAT_ROOM.idFromName(roomId);
    const room = env.CHAT_ROOM.get(id);

    return room.fetch(request);
  },
};
```

### WebSocket Hibernation

Reduce costs by hibernating idle WebSocket connections.

```typescript
export class HibernatingChatRoom {
  state: DurableObjectState;

  constructor(state: DurableObjectState) {
    this.state = state;

    // Enable hibernation
    state.setWebSocketAutoResponse(
      new WebSocketRequestResponsePair("ping", "pong")
    );
  }

  async fetch(request: Request): Promise<Response> {
    const [client, server] = Object.values(new WebSocketPair());

    // Accept with hibernation
    this.state.acceptWebSocket(server);

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }

  async webSocketMessage(ws: WebSocket, message: string) {
    // Called when message received (Worker woken up)
    const data = JSON.parse(message);

    // Broadcast to all
    this.state.getWebSockets().forEach((socket) => {
      socket.send(message);
    });
  }

  async webSocketClose(ws: WebSocket, code: number, reason: string) {
    // Cleanup on close
    ws.close(code, reason);
  }
}
```

## Streaming

Stream responses for large datasets.

### Streaming JSON

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    // Stream in background
    (async () => {
      try {
        await writer.write(encoder.encode("["));

        const results = await env.DB.prepare(
          "SELECT * FROM large_table"
        ).all();

        for (let i = 0; i < results.results.length; i++) {
          const item = results.results[i];
          await writer.write(encoder.encode(JSON.stringify(item)));

          if (i < results.results.length - 1) {
            await writer.write(encoder.encode(","));
          }
        }

        await writer.write(encoder.encode("]"));
        await writer.close();
      } catch (error) {
        await writer.abort(error);
      }
    })();

    return new Response(readable, {
      headers: { "Content-Type": "application/json" },
    });
  },
};
```

### Server-Sent Events (SSE)

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    // Send events in background
    (async () => {
      try {
        for (let i = 0; i < 10; i++) {
          await writer.write(
            encoder.encode(`data: ${JSON.stringify({ count: i })}\n\n`)
          );
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }

        await writer.close();
      } catch (error) {
        await writer.abort(error);
      }
    })();

    return new Response(readable, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    });
  },
};
```

## Custom Domains

Configure custom domains for Workers.

### Via Wrangler

```toml
routes = [
  { pattern = "api.example.com/*", zone_name = "example.com" }
]
```

### Via Dashboard

1. Navigate to Workers & Pages
2. Select your Worker
3. Go to Settings > Triggers
4. Add Custom Domain

### Multiple Domains

```toml
routes = [
  { pattern = "api.example.com/*", zone_name = "example.com" },
  { pattern = "api.other-domain.com/*", zone_name = "other-domain.com" }
]
```

## Static Assets

Serve static files with Workers. Limits: 100,000 assets per Worker version on Paid plans (20,000 on Free), 25 MiB per file.

### Configuration

**wrangler.toml:**

```toml
[assets]
directory = "./public"
binding = "ASSETS"

# HTML handling
html_handling = "auto-trailing-slash"

# 404 handling
not_found_handling = "single-page-application"
```

### Custom Asset Handling

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // API routes
    if (url.pathname.startsWith("/api/")) {
      return handleAPI(request, env);
    }

    // Static assets
    try {
      const asset = await env.ASSETS.fetch(request);

      // Add custom headers
      const response = new Response(asset.body, asset);
      response.headers.set("X-Custom-Header", "value");

      return response;
    } catch {
      return new Response("Not found", { status: 404 });
    }
  },
};
```

### Framework Integration

**Next.js:**

```bash
npm create cloudflare@latest my-next-app -- --framework=next
```

**Remix:**

```bash
npm create cloudflare@latest my-remix-app -- --framework=remix
```

**Astro:**

```bash
npm create cloudflare@latest my-astro-app -- --framework=astro
```

## TCP Sockets

Connect to external services via TCP.

```typescript
export default {
  async fetch(request: Request): Promise<Response> {
    const socket = connect({
      hostname: "example.com",
      port: 6379, // Redis
    });

    const writer = socket.writable.getWriter();
    const encoder = new TextEncoder();

    // Send Redis command
    await writer.write(encoder.encode("PING\r\n"));

    // Read response
    const reader = socket.readable.getReader();
    const { value } = await reader.read();
    const response = new TextDecoder().decode(value);

    return Response.json({ response });
  },
};
```

## HTML Rewriter

Transform HTML on the fly.

```typescript
class LinkRewriter {
  element(element: Element) {
    const href = element.getAttribute("href");

    if (href && href.startsWith("/")) {
      // Make absolute
      element.setAttribute("href", `https://example.com${href}`);
    }

    // Add tracking
    element.setAttribute("data-tracked", "true");
  }
}

export default {
  async fetch(request: Request): Promise<Response> {
    const response = await fetch(request);

    return new HTMLRewriter()
      .on("a", new LinkRewriter())
      .on("img", {
        element(element) {
          // Lazy load images
          element.setAttribute("loading", "lazy");
        },
      })
      .transform(response);
  },
};
```

## Scheduled Events (Cron)

Run Workers on a schedule.

**wrangler.toml:**

```toml
[triggers]
crons = [
  "0 0 * * *",     # Daily at midnight
  "*/15 * * * *",  # Every 15 minutes
  "0 9 * * 1-5"    # Weekdays at 9 AM
]
```

**Handler:**

```typescript
export default {
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    console.log("Cron trigger:", event.cron);

    // Cleanup old data
    await env.DB.prepare("DELETE FROM logs WHERE created_at < ?")
      .bind(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .run();

    // Send daily report
    ctx.waitUntil(sendDailyReport(env));
  },
};
```

## Email Handler

Process incoming emails.

**wrangler.toml:**

```toml
[email]
name = "support@example.com"
```

**Handler:**

```typescript
export default {
  async email(message: ForwardableEmailMessage, env: Env) {
    console.log("From:", message.from);
    console.log("Subject:", message.headers.get("subject"));

    // Forward to support team
    await message.forward("support-team@example.com");

    // Or process email
    const rawEmail = await new Response(message.raw).text();
    await env.EMAILS.put(message.headers.get("message-id"), rawEmail);
  },
};
```

## Tail Workers

Monitor and log other Workers.

**wrangler.toml:**

```toml
[tail_consumers]
service = "my-logging-worker"
```

**Tail Worker:**

```typescript
export default {
  async tail(events: TraceItem[], env: Env) {
    for (const event of events) {
      if (event.outcome === "exception") {
        // Log errors to external service
        await fetch("https://logs.example.com", {
          method: "POST",
          body: JSON.stringify({
            scriptName: event.scriptName,
            error: event.exceptions,
            timestamp: event.event.request.timestamp,
          }),
        });
      }
    }
  },
};
```

## Multi-Region Deployments

Deploy Workers to specific regions (Enterprise only).

```toml
[placement]
mode = "regional"
regions = ["us-east", "eu-west"]
```

## Workers Analytics Engine

Write custom metrics.

```toml
[[analytics_engine_datasets]]
binding = "ANALYTICS"
```

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const start = Date.now();
    const response = await handleRequest(request, env);
    const duration = Date.now() - start;

    // Write custom metrics
    env.ANALYTICS.writeDataPoint({
      blobs: [request.url, request.method, String(response.status)],
      doubles: [duration],
      indexes: [request.headers.get("user-agent") || "unknown"],
    });

    return response;
  },
};
```

## Additional Resources

- **Containers**: https://developers.cloudflare.com/containers/
- **Workflows**: https://developers.cloudflare.com/workflows/
- **MCP Servers**: https://developers.cloudflare.com/agents/model-context-protocol/
- **Workers for Platforms**: https://developers.cloudflare.com/cloudflare-for-platforms/workers-for-platforms/
- **Smart Placement**: https://developers.cloudflare.com/workers/configuration/smart-placement/
- **WebSockets**: https://developers.cloudflare.com/workers/runtime-apis/websockets/
- **Static Assets**: https://developers.cloudflare.com/workers/static-assets/
- **Scheduled Events**: https://developers.cloudflare.com/workers/configuration/cron-triggers/
- **Node.js Compat**: https://developers.cloudflare.com/workers/runtime-apis/nodejs/
