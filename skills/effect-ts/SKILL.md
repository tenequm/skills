---
name: effect-ts
description: "Effect-TS (Effect) comprehensive development guide for TypeScript. Use when building, debugging, reviewing, or generating Effect code. Covers typed error modeling (expected errors vs defects), structured concurrency (fibers), dependency injection (Context + Layers), resource management (Scope), retry/scheduling (Schedule), streams, Schema validation, observability (OpenTelemetry), HTTP client/server, Effect AI (LLM integration), and MCP servers. Critical for AI code generation: includes exhaustive wrong-vs-correct API tables preventing hallucinated Effect code. Supports both Effect v3 (stable) and v4 (beta). Use this skill whenever code imports from 'effect', '@effect/platform', '@effect/ai', or the user mentions Effect-TS, typed errors with Effect, functional TypeScript with Effect, Context, ServiceMap, Layer, or Schema from Effect. Also trigger when generating new TypeScript projects that could benefit from Effect patterns, even if the user doesn't explicitly name the library."
metadata:
  version: "0.2.1"
---

# Effect-TS

Effect is a TypeScript library for building production-grade software with typed errors, structured concurrency, dependency injection, and built-in observability.

## Version Detection

Before writing Effect code, detect which version the user is on:

```bash
# Check installed version
cat package.json | grep '"effect"'
```

- **v3.x** (stable, most production codebases): `Context.Tag`, `Effect.catchAll`, `Effect.fork`, `Data.TaggedError`
- **v4.x** (beta, Feb 2026+): `Context.Service`, `Effect.catch`, `Effect.forkChild`, `Schema.TaggedErrorClass`

> Note: v4 beta briefly used a `ServiceMap` module, renamed back to `Context` on 2026-04-07 (PR #1961). If you see `ServiceMap.*` in any doc or older beta code, it is the current `Context.*`. Both v3 and v4 import `Context` from `"effect"`; the exports inside differ (`Context.Tag` in v3 vs `Context.Service` in v4).

If the version is unclear, ask the user. Default to v3 patterns for existing codebases, v4 for new projects.

## Primary Documentation Sources

- https://effect.website/docs (v3 stable docs)
- https://effect.website/llms.txt (LLM topic index)
- https://effect.website/llms-full.txt (full docs for large context)
- https://tim-smart.github.io/effect-io-ai/ (concise API list)
- https://github.com/Effect-TS/effect-smol (v4 source + migration guides)
- https://github.com/Effect-TS/effect-smol/blob/main/LLMS.md (v4 LLM guide)

## AI Guardrails: Critical Corrections

LLM outputs frequently contain incorrect Effect APIs. Verify every API against the reference docs before using it.

**Common hallucinations (both versions):**

| Wrong (AI often generates)                   | Correct                                                       |
|----------------------------------------------|---------------------------------------------------------------|
| `Effect.cachedWithTTL(...)`                  | `Cache.make({ capacity, timeToLive, lookup })`                |
| `Effect.cachedInvalidateWithTTL(...)`        | `cache.invalidate(key)` / `cache.invalidateAll()`             |
| `Effect.mapError(effect, fn)`                | `Effect.mapError(fn)` in pipe, or use `Effect.catchTag`       |
| `import { Schema } from "@effect/schema"`    | `import { Schema } from "effect"` (v3.10+ and all v4)         |
| `import { JSONSchema } from "@effect/schema"`| `import { JSONSchema } from "effect"` (v3.10+)                |
| JSON Schema Draft 2020-12                    | Effect Schema generates **Draft-07**                          |
| "thread-local storage"                       | "fiber-local storage" via `FiberRef` (v3) / `Context.Reference` (v4) |
| fibers are "cancelled"                       | fibers are "interrupted"                                      |
| all queues have back-pressure                | only **bounded** queues; sliding/dropping do not               |
| `new MyError("message")`                     | `new MyError({ message: "..." })` (Schema errors take objects) |

**v3-specific hallucinations:**

| Wrong                              | Correct (v3)                                        |
|------------------------------------|-----------------------------------------------------|
| `Effect.Service` (function call)   | `class Foo extends Effect.Service<Foo>()("id", {})` |
| `Effect.match(effect, { ... })`    | `Effect.match(effect, { onSuccess, onFailure })`    |
| `Effect.provide(layer1, layer2)`   | `Effect.provide(Layer.merge(layer1, layer2))`       |

**v4-specific hallucinations (AI may mix v3/v4):**

| Wrong (v3 API used in v4 code)    | Correct (v4)                                         |
|-----------------------------------|------------------------------------------------------|
| `Context.Tag("X")` (v3 shape)    | `Context.Service<X>(id)` or class syntax              |
| `ServiceMap.Service` / `ServiceMap.Reference` | Renamed back to `Context.Service` / `Context.Reference` on 2026-04-07 |
| `Effect.catchAll(fn)`            | `Effect.catch(fn)`                                    |
| `Effect.fork(effect)`            | `Effect.forkChild(effect)`                            |
| `Effect.forkDaemon(effect)`      | `Effect.forkDetach(effect)`                           |
| `Data.TaggedError`               | `Schema.TaggedErrorClass`                             |
| `FiberRef.get(ref)`              | `yield* References.X` (a `Context.Reference`)         |
| `yield* ref` (Ref as Effect)     | `yield* Ref.get(ref)` (Ref is no longer an Effect)    |
| `yield* fiber` (Fiber as Effect) | `yield* Fiber.join(fiber)` (Fiber is no longer Effect) |
| `Logger.Default` / `Logger.Live` | `Logger.layer` (v4 naming convention)                 |
| `Schema.TaggedError`             | `Schema.TaggedErrorClass`                             |
| `Schema.makeUnsafe(input)`       | `Schema.make(input)` (throws `SchemaError`); also `Schema.makeOption`, `Schema.makeEffect` |
| `ParseResult` (from `"effect"`)  | `SchemaIssue` module + `SchemaError` class; narrow with `Schema.isSchemaError` |
| `HttpApiEndpoint.get(n, p).pipe(HttpApiEndpoint.setPath(...), setPayload(...), setSuccess(...))` | `HttpApiEndpoint.get(n, p, { params, query, payload, success, error })` (object-option form) |
| `Otlp.layer({ url, serviceName })` | `OtlpTracer.layer({ url, resource: { serviceName } })` + `OtlpSerialization.layerJson` + `FetchHttpClient.layer` |
| `import { HttpApi } from "@effect/platform"` (v4) | `import { HttpApi } from "effect/unstable/httpapi"` |
| HttpApi endpoint schema errors are typed errors by default | Since PR #2057 (2026-04-20) they default to **defects** unless transformed |

**Read `references/llm-corrections.md` for the exhaustive corrections table.**

## Progressive Disclosure

Read only the reference files relevant to your task:

- Error modeling or typed failures → `references/error-modeling.md`
- Services, DI, or Layer wiring → `references/dependency-injection.md`
- Retries, timeouts, or backoff → `references/retry-scheduling.md`
- Fibers, forking, or parallel work → `references/concurrency.md`
- Streams, queues, or SSE → `references/streams.md`
- Resource lifecycle or cleanup → `references/resource-management.md`
- Schema validation or decoding → `references/schema.md`
- Logging, metrics, or tracing → `references/observability.md`
- HTTP clients or API calls → `references/http.md`
- HTTP API servers → `references/http.md` (covers both client and server)
- LLM/AI integration → `references/effect-ai.md`
- Testing Effect code → `references/testing.md`
- Migrating from async/await → `references/migration-async.md`
- Migrating from v3 to v4 → `references/migration-v4.md`
- Core types, gen, pipe, running → `references/core-patterns.md`
- Full wrong-vs-correct API table → `references/llm-corrections.md`

## Core Workflow

1. **Detect version** from `package.json` before writing any code
2. **Clarify boundaries**: identify where IO happens, keep core logic as `Effect` values
3. **Choose style**: use `Effect.gen` for sequential logic, pipelines for simple transforms. In v4, prefer `Effect.fn("name")` for named functions
4. **Model errors explicitly**: type expected errors in the `E` channel; treat bugs as defects
5. **Model dependencies** with services and layers; keep interfaces free of construction logic
6. **Manage resources** with `Scope` when opening/closing things (files, connections, etc.)
7. **Provide layers** and run effects only at program edges (`NodeRuntime.runMain` or `ManagedRuntime`)
8. **Verify APIs exist** before using them - consult https://tim-smart.github.io/effect-io-ai/ or source docs

## Starter Function Set

Start with these ~20 functions (the official recommended set):

**Creating effects:** `Effect.succeed`, `Effect.fail`, `Effect.sync`, `Effect.tryPromise`

**Composition:** `Effect.gen` (+ `Effect.fn` in v4), `Effect.andThen`, `Effect.map`, `Effect.tap`, `Effect.all`

**Running:** `Effect.runPromise`, `NodeRuntime.runMain` (preferred for entry points)

**Error handling:** `Effect.catchTag`, `Effect.catchAll` (v3) / `Effect.catch` (v4), `Effect.orDie`

**Resources:** `Effect.acquireRelease`, `Effect.acquireUseRelease`, `Effect.scoped`

**Dependencies:** `Effect.provide`, `Effect.provideService`

**Key modules:** `Effect`, `Schema`, `Layer`, `Option`, `Either` (v3) / `Result` (v4), `Array`, `Match`

**DI (v3):** `Context.Tag`, `Context.Reference`
**DI (v4):** `Context.Service`, `Context.Reference`, `Layer.effect`, `Effect.fn("name")`

## Import Patterns

Always use barrel imports from `"effect"`:

```typescript
import { Context, Effect, Schema, Layer, Option, Stream } from "effect"
```

For companion packages, import from the package name. v3 and v4 differ here:

```typescript
// v3 (stable) companion packages
import { NodeRuntime } from "@effect/platform-node"
import { HttpClient } from "@effect/platform"
import { NodeSdk } from "@effect/opentelemetry"

// v4 (beta) - platform transports still separate, but HttpApi / observability
// moved under effect/unstable/*
import { NodeRuntime } from "@effect/platform-node"
import { FetchHttpClient } from "effect/unstable/http"
import { HttpApi, HttpApiEndpoint, HttpApiGroup, HttpApiBuilder, HttpApiScalar } from "effect/unstable/httpapi"
import { OtlpLogger, OtlpSerialization, OtlpTracer } from "effect/unstable/observability"
```

Avoid deep module imports (`effect/Effect`) unless your bundler requires it for tree-shaking.

## Output Standards

- Show imports in every code example
- Prefer `Effect.gen` (imperative) for multi-step logic; pipelines for transforms
- In v4, use `Effect.fn("name")` instead of bare `Effect.gen` for named functions
- Never call `Effect.runPromise` / `Effect.runSync` inside library code - only at program edges
- Use `NodeRuntime.runMain` for CLI/server entry points (handles SIGINT gracefully)
- Use `ManagedRuntime` when integrating Effect into non-Effect frameworks (Hono, Express, etc.)
- Always `return yield*` when raising an error in a generator (ensures TS understands control flow)
- Avoid point-free/tacit usage: write `Effect.map((x) => fn(x))` not `Effect.map(fn)` (generics get erased)
- Keep dependency graphs explicit (services, layers, tags)
- State the `Effect<A, E, R>` shape when it helps design decisions

## Agent Quality Checklist

Before outputting Effect code, verify:

- [ ] Every API exists (check against tim-smart API list or source docs)
- [ ] Imports are from `"effect"` (not `@effect/schema`, `@effect/io`, etc.)
- [ ] Version matches the user's codebase (v3 vs v4 syntax)
- [ ] Expected errors are typed in `E`; unexpected failures are defects
- [ ] `run*` is called only at program edges, not inside library code
- [ ] Resources opened with `acquireRelease` are wrapped in `Effect.scoped`
- [ ] Layers are provided before running (no missing `R` requirements)
- [ ] Generator bodies use `yield*` (not `yield` without `*`)
- [ ] Error raises in generators use `return yield*` pattern
