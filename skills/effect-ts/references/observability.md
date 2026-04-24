# Observability

Effect has built-in structured logging, metrics, and distributed tracing. For exporting telemetry, use `effect/unstable/observability` (v4/new projects) or `@effect/opentelemetry` (v3/existing OTel setups).

## Structured Logging

```typescript
import { Effect } from "effect"

yield* Effect.log("Processing request")
yield* Effect.logInfo("User found", userId)
yield* Effect.logWarning("Rate limit approaching")
yield* Effect.logError("Failed to fetch", error)
yield* Effect.logDebug("Cache miss for key:", key)

// Add context to all logs in scope
const withContext = myEffect.pipe(
  Effect.annotateLogs("requestId", requestId),
  Effect.annotateLogs("userId", userId)
)

// Log spans (structured timing)
const timed = Effect.withLogSpan("database.query")(queryEffect)
```

## Distributed Tracing

```typescript
// Add a span to any effect
const traced = myEffect.pipe(
  Effect.withSpan("processPayment", {
    attributes: { amount, currency }
  })
)

// Nested spans create parent-child relationships automatically
const program = Effect.gen(function*() {
  yield* fetchUser(id).pipe(Effect.withSpan("fetch.user"))
  yield* validatePayment().pipe(Effect.withSpan("validate.payment"))
  yield* processCharge().pipe(Effect.withSpan("process.charge"))
}).pipe(Effect.withSpan("handlePayment"))
// Produces: handlePayment -> fetch.user, validate.payment, process.charge

// Annotate spans
const annotated = myEffect.pipe(
  Effect.annotateSpans("http.status_code", 200)
)
```

**v4: `Effect.fn` adds spans automatically:**

```typescript
// v4 - the name string becomes a span
const fetchUser = Effect.fn("fetchUser")(function*(id: string) {
  // ... automatically wrapped in a "fetchUser" span
})
```

## Metrics

```typescript
import { Metric } from "effect"

// Counter
const requestCount = Metric.counter("http.requests.total")
yield* Metric.increment(requestCount)

// Counter with tags
const errorCount = Metric.counter("http.errors.total")
yield* Metric.increment(errorCount).pipe(
  Effect.tagMetrics("status", "500"),
  Effect.tagMetrics("method", "POST")
)

// Gauge
const activeConnections = Metric.gauge("connections.active")
yield* Metric.set(activeConnections, 42)

// Histogram
const latency = Metric.histogram("http.request.duration_ms",
  Metric.Histogram.exponential({ start: 1, factor: 2, count: 10 })
)
yield* Metric.record(latency, durationMs)
```

## OpenTelemetry Export

### v3: @effect/opentelemetry

```typescript
import { NodeSdk } from "@effect/opentelemetry"
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http"
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-http"
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics"

const OtelLayer = NodeSdk.layer(() => ({
  resource: { serviceName: "my-service" },
  spanProcessor: new BatchSpanProcessor(new OTLPTraceExporter({
    url: "http://localhost:4318/v1/traces"
  })),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: "http://localhost:4318/v1/metrics"
    })
  })
}))

// Provide to your program
const main = program.pipe(Effect.provide(OtelLayer))
```

### v4: effect/unstable/observability (fetch-based, no OTel SDK dependency)

v4 ships its own lightweight OTLP exporters under `effect/unstable/observability`. The canonical setup is to compose split modules — `OtlpTracer.layer`, `OtlpLogger.layer` — with an `OtlpSerialization` encoding layer and an `HttpClient` transport. The whole stack depends on `FetchHttpClient.layer` from `effect/unstable/http`; there is no OpenTelemetry SDK dependency.

```typescript
import { Layer } from "effect"
import { FetchHttpClient } from "effect/unstable/http"
import { OtlpLogger, OtlpSerialization, OtlpTracer } from "effect/unstable/observability"

const Tracing = OtlpTracer.layer({
  url: "http://localhost:4318/v1/traces",
  resource: { serviceName: "my-service", serviceVersion: "1.0.0" }
})

const Logging = OtlpLogger.layer({
  url: "http://localhost:4318/v1/logs",
  resource: { serviceName: "my-service" }
})

export const Observability = Layer.merge(Tracing, Logging).pipe(
  Layer.provide(OtlpSerialization.layerJson), // or layerProtobuf
  Layer.provide(FetchHttpClient.layer)
)

const main = program.pipe(Effect.provide(Observability))
```

An aggregator `Otlp.layer` also exists that bundles tracer + logger + metrics, but note its argument shape:

```typescript
import { Otlp } from "effect/unstable/observability"

// aggregator form - baseUrl, NOT url; serviceName under resource, NOT top-level
const All = Otlp.layer({
  baseUrl: "http://localhost:4318",
  resource: { serviceName: "my-service" }
}).pipe(
  Layer.provide(OtlpSerialization.layerJson),
  Layer.provide(FetchHttpClient.layer)
)
```

Do NOT use `Otlp.layer({ url, serviceName })` — neither field exists in that shape. Prefer the split-module form above; it is the pattern in `ai-docs/src/08_observability/20_otlp-tracing.ts`.

The v3 `@effect/opentelemetry` NodeSdk path is not available in v4 — if you need the OpenTelemetry SDK stack you should stay on v3.

## Testing Observability

```typescript
import { InMemorySpanExporter, SimpleSpanProcessor } from "@opentelemetry/sdk-trace-base"

const TestOtelLayer = NodeSdk.layer(() => ({
  resource: { serviceName: "test" },
  spanProcessor: new SimpleSpanProcessor(new InMemorySpanExporter())
}))
```

## Log Level Configuration

```typescript
import { Logger, LogLevel } from "effect"

// Set minimum log level
const withLogLevel = program.pipe(
  Logger.withMinimumLogLevel(LogLevel.Info)
)

// Custom logger
const jsonLogger = Logger.make(({ logLevel, message, annotations }) => {
  console.log(JSON.stringify({ level: logLevel.label, message, ...annotations }))
})

const withCustomLogger = program.pipe(
  Effect.provide(Logger.replace(Logger.defaultLogger, jsonLogger))
)
```
