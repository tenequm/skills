---
name: effect-ts
description: "Effect-TS (Effect) comprehensive development guide for TypeScript. Use when building, debugging, reviewing, or generating Effect code. Covers typed error modeling (expected errors vs defects), structured concurrency (fibers), dependency injection (ServiceMap/Context + Layers), resource management (Scope), retry/scheduling (Schedule), streams, Schema validation, observability (OpenTelemetry), HTTP client/server, Effect AI (LLM integration), and MCP servers. Critical for AI code generation: includes exhaustive wrong-vs-correct API tables preventing hallucinated Effect code. Supports both Effect v3 (stable) and v4 (beta). Use this skill whenever code imports from 'effect', '@effect/platform', '@effect/ai', or the user mentions Effect-TS, typed errors with Effect, functional TypeScript with Effect, ServiceMap, Layer, or Schema from Effect. Also trigger when generating new TypeScript projects that could benefit from Effect patterns, even if the user doesn't explicitly name the library."
metadata:
  version: "0.1.0"
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
- **v4.x** (beta, Feb 2026+): `ServiceMap.Service`, `Effect.catch`, `Effect.forkChild`, `Schema.TaggedErrorClass`

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
| "thread-local storage"                       | "fiber-local storage" via `FiberRef` (v3) / `ServiceMap.Reference` (v4) |
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
| `Context.Tag("X")`               | `ServiceMap.Service<X>(id)` or class syntax           |
| `Effect.catchAll(fn)`            | `Effect.catch(fn)`                                    |
| `Effect.fork(effect)`            | `Effect.forkChild(effect)`                            |
| `Effect.forkDaemon(effect)`      | `Effect.forkDetach(effect)`                           |
| `Data.TaggedError`               | `Schema.TaggedErrorClass`                             |
| `FiberRef.get(ref)`              | `yield* References.X` (ServiceMap.Reference)          |
| `yield* ref` (Ref as Effect)     | `yield* Ref.get(ref)` (Ref is no longer an Effect)    |
| `yield* fiber` (Fiber as Effect) | `yield* Fiber.join(fiber)` (Fiber is no longer Effect) |
| `Logger.Default` / `Logger.Live` | `Logger.layer` (v4 naming convention)                 |
| `Schema.TaggedError`             | `Schema.TaggedErrorClass`                             |

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

## Import Patterns

Always use barrel imports from `"effect"`:

```typescript
import { Effect, Schema, Layer, Option, Stream } from "effect"
```

For companion packages, import from the package name:

```typescript
import { NodeRuntime } from "@effect/platform-node"
import { NodeSdk } from "@effect/opentelemetry"
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
