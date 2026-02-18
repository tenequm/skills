# Complete Bindings Guide

Bindings are how Workers connect to Cloudflare resources and external services. They provide zero-latency access to storage, databases, queues, and other services.

## Storage Bindings

### KV (Key-Value Storage)

Global, low-latency, eventually consistent key-value storage.

**Best for:**
- Configuration data
- User sessions
- Cache
- Small objects (<25 MB)

**Configuration:**

```toml
[[kv_namespaces]]
binding = "MY_KV"
id = "your-namespace-id"
preview_id = "preview-namespace-id"  # For local dev
```

**API:**

```typescript
// Write
await env.MY_KV.put("key", "value");
await env.MY_KV.put("key", "value", {
  expirationTtl: 3600,  // Expire in 1 hour
  metadata: { user: "123" }
});

// Read
const value = await env.MY_KV.get("key");
const json = await env.MY_KV.get("key", "json");
const buffer = await env.MY_KV.get("key", "arrayBuffer");

// With metadata
const { value, metadata } = await env.MY_KV.getWithMetadata("key");

// Delete
await env.MY_KV.delete("key");

// List keys
const keys = await env.MY_KV.list({ prefix: "user:" });
```

**Limits:**
- Key size: 512 bytes
- Value size: 25 MB
- Write rate: 1 write/second per key (eventually consistent)
- Read rate: unlimited

### D1 (SQL Database)

Serverless SQLite database built on SQLite.

**Best for:**
- Structured data
- Relational data
- Complex queries
- ACID transactions

**Configuration:**

```toml
[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "your-database-id"
```

**API:**

```typescript
// Query with bind parameters
const result = await env.DB.prepare(
  "SELECT * FROM users WHERE id = ?"
).bind(userId).all();

// Insert
await env.DB.prepare(
  "INSERT INTO users (name, email) VALUES (?, ?)"
).bind(name, email).run();

// Update
await env.DB.prepare(
  "UPDATE users SET last_login = ? WHERE id = ?"
).bind(new Date().toISOString(), userId).run();

// Transaction
const results = await env.DB.batch([
  env.DB.prepare("INSERT INTO users (name) VALUES (?)").bind("Alice"),
  env.DB.prepare("INSERT INTO users (name) VALUES (?)").bind("Bob"),
]);

// First row only
const user = await env.DB.prepare(
  "SELECT * FROM users WHERE id = ?"
).bind(userId).first();
```

**Read Replication (GA April 2025):**

D1 supports global read replicas for low-latency reads. Use the Sessions API for sequential consistency:

```typescript
// Consistent reads after writes
const bookmark = request.headers.get("x-d1-bookmark") ?? "first-unconstrained";
const session = env.DB.withSession(bookmark);
const result = await session.prepare("SELECT * FROM users").all();

// Return bookmark for subsequent requests
const responseBookmark = result.meta?.bookmark;
```

Session modes: `"first-primary"` (always read primary), `"first-unconstrained"` (read any replica).

**Features:**
- Read replication (global read replicas, no extra cost)
- Time Travel (restore to any point in last 30 days)
- Backups
- Migrations via Wrangler

**Limits:**
- Database size: 10 GB (Paid), 500 MB (Free)
- Rows read: 25M/day (Paid), 5M/day (Free)
- Rows written: 50M/day (Paid), 100K/day (Free)

### R2 (Object Storage)

S3-compatible object storage with zero egress fees.

**Best for:**
- Large files
- Media storage
- Static assets
- Backups

**Configuration:**

```toml
[[r2_buckets]]
binding = "MY_BUCKET"
bucket_name = "my-bucket"
jurisdiction = "eu"  # Optional: eu or fedramp
```

**API:**

```typescript
// Put object
await env.MY_BUCKET.put("file.txt", "contents", {
  httpMetadata: {
    contentType: "text/plain",
    cacheControl: "max-age=3600",
  },
  customMetadata: {
    user: "123",
  },
});

// Put from stream
await env.MY_BUCKET.put("large-file.bin", request.body);

// Get object
const object = await env.MY_BUCKET.get("file.txt");
if (object) {
  const text = await object.text();
  const buffer = await object.arrayBuffer();
  const stream = object.body; // ReadableStream

  // Metadata
  console.log(object.httpMetadata);
  console.log(object.customMetadata);
}

// Get with range
const object = await env.MY_BUCKET.get("file.txt", {
  range: { offset: 0, length: 1024 }
});

// Head (metadata only)
const object = await env.MY_BUCKET.head("file.txt");

// Delete
await env.MY_BUCKET.delete("file.txt");

// List objects
const objects = await env.MY_BUCKET.list({
  prefix: "images/",
  limit: 1000,
});

// Multipart upload (for large files)
const upload = await env.MY_BUCKET.createMultipartUpload("large.bin");
const part = await upload.uploadPart(1, data);
await upload.complete([part]);
```

**Features:**
- Automatic multipart uploads
- Object versioning
- Event notifications
- Public buckets
- Custom domains

**Limits:**
- Max object size: 5 TB
- Storage: unlimited
- Operations: unlimited

## Compute Bindings

### Durable Objects

Strongly consistent, coordinated stateful objects with SQLite storage. Available on Free and Paid plans (free tier added April 2025).

**Best for:**
- Real-time collaboration
- WebSocket servers
- Coordination
- Strong consistency
- Per-user/per-room state

**Configuration:**

```toml
[[durable_objects.bindings]]
name = "COUNTER"
class_name = "Counter"
script_name = "my-worker"  # Optional: if in different Worker

[[migrations]]
tag = "v1"
new_classes = ["Counter"]
```

**Durable Object Class:**

```typescript
export class Counter {
  state: DurableObjectState;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    // Get from storage
    let count = (await this.state.storage.get("count")) || 0;

    // Increment
    count++;

    // Put to storage
    await this.state.storage.put("count", count);

    return Response.json({ count });
  }

  // Alarms (scheduled actions)
  async alarm() {
    await this.state.storage.delete("count");
  }
}
```

**Worker Usage:**

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Get Durable Object ID
    const id = env.COUNTER.idFromName("global-counter");

    // Get stub (reference)
    const stub = env.COUNTER.get(id);

    // Call via fetch
    return stub.fetch(request);
  },
};
```

**Storage API:**

```typescript
// Single operations
await this.state.storage.put("key", "value");
const value = await this.state.storage.get("key");
await this.state.storage.delete("key");

// Batch operations
await this.state.storage.put({
  key1: "value1",
  key2: "value2",
});

const values = await this.state.storage.get(["key1", "key2"]);

// List
const entries = await this.state.storage.list();

// SQL (new)
const result = await this.state.storage.sql.exec(
  "SELECT * FROM users WHERE id = ?", userId
);
```

**Features:**
- SQLite-backed storage (GA)
- Automatic persistence
- Alarms (scheduled actions)
- WebSocket Hibernation
- Point-in-time recovery
- Available on Free plan (April 2025)

### Queues

Message queuing for async processing with guaranteed delivery.

**Best for:**
- Background jobs
- Async processing
- Decoupling services
- Retry logic

**Configuration:**

```toml
[[queues.producers]]
binding = "MY_QUEUE"
queue = "my-queue"

[[queues.consumers]]
queue = "my-queue"
max_batch_size = 100
max_batch_timeout = 30
```

**Producer (send messages):**

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Send single message
    await env.MY_QUEUE.send({ userId: 123, action: "process" });

    // Send batch
    await env.MY_QUEUE.sendBatch([
      { body: { userId: 123 } },
      { body: { userId: 456 } },
    ]);

    return Response.json({ queued: true });
  },
};
```

**Consumer (receive messages):**

```typescript
export default {
  async queue(batch: MessageBatch<any>, env: Env): Promise<void> {
    for (const message of batch.messages) {
      try {
        await processMessage(message.body);
        message.ack();  // Mark as processed
      } catch (error) {
        message.retry();  // Retry later
      }
    }
  },
};
```

**Features:**
- Guaranteed delivery
- Automatic retries
- Dead letter queues
- Batch processing
- Pull consumers (API-based)

### Workflows

Durable execution engine for multi-step, long-running tasks (GA April 2025).

**Best for:**
- Multi-step processes with automatic retries
- Human-in-the-loop approvals
- Long-running background jobs
- Tasks that need state persistence across failures

**Configuration:**

```toml
[[workflows]]
name = "order-workflow"
binding = "ORDER_WORKFLOW"
class_name = "OrderWorkflow"
```

**Workflow Class:**

```typescript
import { WorkflowEntrypoint, WorkflowStep, WorkflowEvent } from "cloudflare:workers";

export class OrderWorkflow extends WorkflowEntrypoint<Env, Params> {
  async run(event: WorkflowEvent<Params>, step: WorkflowStep) {
    // Each step is durable - survives restarts
    const order = await step.do("validate-order", async () => {
      return validateOrder(event.payload);
    });

    // Sleep without holding compute
    await step.sleep("wait-for-processing", "1 hour");

    // Wait for external event (human approval, webhook, etc.)
    const approval = await step.waitForEvent("await-approval", {
      timeout: "24 hours",
    });

    await step.do("fulfill-order", async () => {
      return fulfillOrder(order, approval);
    });
  }
}
```

**Worker Usage:**

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Create workflow instance
    const instance = await env.ORDER_WORKFLOW.create({
      params: { orderId: "123", items: ["item-1"] },
    });

    // Get status
    const status = await instance.status();

    // Send event to waiting workflow
    await instance.sendEvent({ approved: true });

    return Response.json({ id: instance.id, status });
  },
};
```

### Containers

Run Docker containers alongside Workers (public beta June 2025). Built on Durable Objects.

**Best for:**
- Porting existing Docker applications
- Running any language/runtime
- Multi-GB memory workloads
- CLI tools and code sandboxes

**Configuration:**

```toml
[[containers]]
class_name = "MyContainer"
image = "./Dockerfile"
max_instances = 5

[[durable_objects.bindings]]
class_name = "MyContainer"
name = "MY_CONTAINER"
```

**Container Class:**

```typescript
import { Container } from "cloudflare:workers";

export class MyContainer extends Container {
  defaultPort = 8080;

  // Optional: auto-sleep after inactivity
  sleepAfter = "5 minutes";
}
```

**Worker Usage:**

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const id = env.MY_CONTAINER.idFromName("my-instance");
    const container = env.MY_CONTAINER.get(id);
    return container.fetch(request);
  },
};
```

## AI & ML Bindings

### Workers AI

Run AI models directly from Workers.

**Best for:**
- Text generation (LLMs)
- Embeddings
- Image generation
- Speech recognition
- Translation

**Configuration:**

```toml
[ai]
binding = "AI"
```

**API:**

```typescript
// Text generation (with speculative decoding for 2-4x speed)
const response = await env.AI.run("@cf/meta/llama-3.3-70b-instruct-fp8-fast", {
  messages: [
    { role: "system", content: "You are a helpful assistant" },
    { role: "user", content: "What is Cloudflare?" }
  ],
});

// Embeddings (multilingual with bge-m3, or English with bge-base-en-v1.5)
const embeddings = await env.AI.run("@cf/baai/bge-m3", {
  text: "The quick brown fox jumps over the lazy dog",
});

// Reranking (for RAG post-processing)
const reranked = await env.AI.run("@cf/baai/bge-reranker-base", {
  query: "What is Workers?",
  documents: ["Workers runs on V8", "R2 is object storage"],
});

// Image generation
const image = await env.AI.run("@cf/stabilityai/stable-diffusion-xl-base-1.0", {
  prompt: "A sunset over the ocean",
});

// Speech to text
const result = await env.AI.run("@cf/openai/whisper-large-v3-turbo", {
  audio: audioData,
});

// Text to speech
const audio = await env.AI.run("@cf/myshell-ai/melotts", {
  text: "Hello from Cloudflare Workers",
});

// Streaming
const stream = await env.AI.run("@cf/meta/llama-3.3-70b-instruct-fp8-fast", {
  messages: [{ role: "user", content: "Tell me a story" }],
  stream: true,
});
```

**Async Batch API:** Submit large workloads asynchronously instead of waiting for each inference call synchronously. Useful for batch processing embeddings or large document sets.

### Vectorize

Vector database for similarity search.

**Best for:**
- Semantic search
- RAG (Retrieval Augmented Generation)
- Recommendations
- Embeddings storage

**Configuration:**

```toml
[[vectorize]]
binding = "VECTORIZE"
index_name = "my-index"
```

**API:**

```typescript
// Insert vectors
await env.VECTORIZE.insert([
  { id: "1", values: [0.1, 0.2, ...], metadata: { text: "..." } },
  { id: "2", values: [0.3, 0.4, ...], metadata: { text: "..." } },
]);

// Query (similarity search)
const results = await env.VECTORIZE.query(
  [0.15, 0.25, ...],  // Query vector
  {
    topK: 5,
    returnMetadata: true,
  }
);

// With metadata filtering
const results = await env.VECTORIZE.query(vector, {
  topK: 5,
  filter: { category: "technology" },
});
```

## Database Bindings

### Hyperdrive

Accelerate access to existing databases via connection pooling and caching.

**Best for:**
- Connecting to existing Postgres/MySQL
- Reducing latency to traditional databases
- Connection pooling

**Configuration:**

```toml
[[hyperdrive]]
binding = "HYPERDRIVE"
id = "your-hyperdrive-id"
```

**Usage with postgres:**

```typescript
import { Client } from "pg";

const client = new Client({
  connectionString: env.HYPERDRIVE.connectionString,
});

await client.connect();
const result = await client.query("SELECT * FROM users");
await client.end();
```

**Features:**
- Connection pooling
- Query caching
- Read replicas support

## Service Bindings

Call other Workers via RPC or HTTP. For private network access, see Workers VPC Service Bindings below.

**Configuration:**

```toml
[[services]]
binding = "AUTH_SERVICE"
service = "auth-worker"
environment = "production"
```

**HTTP-based:**

```typescript
const response = await env.AUTH_SERVICE.fetch(new Request("http://auth/verify"));
```

**RPC-based (recommended):**

```typescript
// In auth-worker
export class AuthService extends WorkerEntrypoint {
  async verifyToken(token: string): Promise<boolean> {
    // Verify logic
    return true;
  }
}

// In calling worker
const isValid = await env.AUTH_SERVICE.verifyToken(token);
```

## Additional Bindings

### Analytics Engine

Write custom analytics and metrics.

```toml
[[analytics_engine_datasets]]
binding = "ANALYTICS"
```

```typescript
env.ANALYTICS.writeDataPoint({
  blobs: ["user-123", "click"],
  doubles: [1.5],
  indexes: ["button-1"],
});
```

### Browser Rendering

Control headless browsers.

```toml
browser = { binding = "BROWSER" }
```

```typescript
const browser = await puppeteer.launch(env.BROWSER);
const page = await browser.newPage();
await page.goto("https://example.com");
const screenshot = await page.screenshot();
```

### Rate Limiting

Built-in rate limiting.

```toml
[[unsafe.bindings]]
name = "RATE_LIMITER"
type = "ratelimit"
namespace_id = "your-namespace-id"
simple = { limit = 100, period = 60 }
```

```typescript
const { success } = await env.RATE_LIMITER.limit({ key: userId });
if (!success) {
  return new Response("Rate limited", { status: 429 });
}
```

### mTLS

Present client certificates.

```toml
[[mtls_certificates]]
binding = "CERT"
certificate_id = "your-cert-id"
```

```typescript
const response = await fetch("https://api.example.com", {
  certificate: env.CERT,
});
```

### AI Gateway

Proxy and manage AI API calls with logging, caching, and rate limiting.

```toml
[ai.gateway]
binding = "AI_GATEWAY"
gateway_id = "my-gateway"
```

```typescript
// Universal request to any AI provider via gateway
const response = await env.AI_GATEWAY.run("openai/chat/completions", {
  model: "gpt-4",
  messages: [{ role: "user", content: "Hello" }],
});

// Retrieve log information
const log = await env.AI_GATEWAY.getLog(logId);

// Send feedback and update metadata
await env.AI_GATEWAY.patchLog(logId, { feedback: "good", metadata: { user: "123" } });
```

### Secrets Store

Account-level centralized secrets shared across Workers (April 2025).

```toml
[[secrets_store_secrets]]
binding = "API_KEY"
store_id = "abc123"
secret_name = "open_ai_key"  # pragma: allowlist secret
```

```typescript
const key = await env.API_KEY.get();
```

Unlike per-Worker secrets, Secrets Store entries are managed centrally and reusable across all Workers in your account.

### AutoRAG / AI Search

Managed RAG pipeline - upload docs to R2, AutoRAG handles embeddings, indexing, retrieval, and generation (open beta April 2025).

```toml
[[autorag]]
binding = "AI_SEARCH"
name = "my-autorag-instance"
```

```typescript
const answer = await env.AI_SEARCH.aiSearch("What is the refund policy?");
// Returns generated answer with source citations
```

AutoRAG continuously syncs with your R2 data source, so updates are automatic.

### Pipelines

Streaming data ingestion to R2 as Apache Iceberg or Parquet/JSON files (beta).

```toml
[[pipelines]]
binding = "MY_PIPELINE"
pipeline = "my-clickstream-pipeline"
```

```typescript
await env.MY_PIPELINE.send({
  event: "page_view",
  path: "/pricing",
  timestamp: Date.now(),
});
```

Supports up to 100 MB/second per pipeline. Data is auto-batched and delivered to R2.

### Workers VPC Service Bindings

Connect Workers to private APIs inside AWS, GCP, Azure, or on-premise via Cloudflare Tunnel (beta November 2025).

```toml
[[vpc_services]]
binding = "PRIVATE_API"
service_id = "<your-vpc-service-id>"
```

```typescript
const response = await env.PRIVATE_API.fetch("https://internal-api/data");
```

## Best Practices

### Binding Selection

- **KV**: Configuration, sessions, cache
- **D1**: Structured data, complex queries
- **R2**: Large files, media, backups
- **Durable Objects**: Real-time, strong consistency, coordination
- **Queues**: Background jobs, async processing
- **Workflows**: Multi-step durable processes, long-running tasks
- **Containers**: Docker workloads, any language/runtime
- **Workers AI**: AI/ML inference
- **Vectorize**: Similarity search, RAG
- **AutoRAG**: Managed RAG pipeline over R2 documents

### Performance

- Use `ctx.waitUntil()` for non-critical writes
- Batch operations when possible
- Use appropriate consistency models
- Cache frequently accessed data

### Error Handling

Always handle errors from bindings:

```typescript
try {
  const value = await env.MY_KV.get("key");
} catch (error) {
  // Handle error
  console.error("KV error:", error);
  return new Response("Service unavailable", { status: 503 });
}
```

### Local Development

Use Wrangler for local testing with bindings:

```bash
# Create resources
wrangler d1 create my-database
wrangler kv:namespace create MY_KV

# Local dev (uses local storage by default in Wrangler v4)
wrangler dev

# Local dev with real remote bindings (GA September 2025)
wrangler dev --remote
```

## Additional Resources

- **Bindings Reference**: https://developers.cloudflare.com/workers/runtime-apis/bindings/
- **KV**: https://developers.cloudflare.com/kv/
- **D1**: https://developers.cloudflare.com/d1/
- **R2**: https://developers.cloudflare.com/r2/
- **Durable Objects**: https://developers.cloudflare.com/durable-objects/
- **Queues**: https://developers.cloudflare.com/queues/
- **Workers AI**: https://developers.cloudflare.com/workers-ai/
- **Vectorize**: https://developers.cloudflare.com/vectorize/
- **Workflows**: https://developers.cloudflare.com/workflows/
- **Containers**: https://developers.cloudflare.com/containers/
