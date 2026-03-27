# Error Modeling

Effect has a two-tier error model. Understanding the distinction is critical for writing correct Effect code.

## Expected Errors vs Defects

**Expected errors** (typed in `E` channel): recoverable failures your program anticipates. These MUST be handled before running.

**Defects** (untyped): unexpected bugs, programmer mistakes, invariant violations. These crash the fiber and are NOT in the type signature.

```typescript
// Expected error - appears in the type
//                            v---- typed error
const fetchUser: Effect<User, NotFoundError | NetworkError>

// Defect - NOT in the type (thrown at runtime)
const bad = Effect.sync(() => { throw new Error("bug") })
//    ^--- Effect<never, never> - defect is invisible in types
```

## Defining Errors

**v3: `Data.TaggedError`**

```typescript
import { Data } from "effect"

class NotFoundError extends Data.TaggedError("NotFoundError")<{
  readonly id: string
}> {}

class NetworkError extends Data.TaggedError("NetworkError")<{
  readonly cause: unknown
}> {}
```

**v4: `Schema.TaggedErrorClass`**

```typescript
import { Schema } from "effect"

class NotFoundError extends Schema.TaggedErrorClass<NotFoundError>()("NotFoundError", {
  id: Schema.String
}) {}

class NetworkError extends Schema.TaggedErrorClass<NetworkError>()("NetworkError", {
  cause: Schema.Defect
}) {}
```

## Handling Errors

### catchTag - handle a specific error by its _tag

```typescript
// v3
const handled = program.pipe(
  Effect.catchTag("NotFoundError", (e) => Effect.succeed(defaultUser))
)

// v4 - also accepts arrays
const handled = program.pipe(
  Effect.catchTag(["NotFoundError", "NetworkError"], (e) => Effect.succeed(fallback))
)
```

### catchAll (v3) / catch (v4) - handle all errors

```typescript
// v3
const handled = program.pipe(
  Effect.catchAll((error) => Effect.succeed(fallback))
)

// v4
const handled = program.pipe(
  Effect.catch((error) => Effect.succeed(fallback))
)
```

### catchTags - handle multiple errors with different handlers

```typescript
const handled = program.pipe(
  Effect.catchTags({
    NotFoundError: (e) => Effect.succeed(defaultUser),
    NetworkError: (e) => Effect.retry(program, Schedule.exponential("1 second"))
  })
)
```

### orDie - convert expected error to defect

Use when an error is logically impossible or unrecoverable at this point:

```typescript
const critical = program.pipe(Effect.orDie)
// Error channel becomes `never` - any failure is a defect
```

### mapError - transform errors

```typescript
const mapped = program.pipe(
  Effect.mapError((e) => new AppError({ cause: e }))
)
```

## Defect Handling (Advanced)

Defects are for debugging, not normal recovery. Use sparingly:

```typescript
// v3
const withDefectHandling = program.pipe(
  Effect.catchAllDefect((defect) => Effect.log(`Bug: ${defect}`))
)

// v4
const withDefectHandling = program.pipe(
  Effect.catchDefect((defect) => Effect.log(`Bug: ${defect}`))
)
```

### Sandbox - expose defects as Cause for inspection

```typescript
import { Cause, Effect } from "effect"

const diagnosed = program.pipe(
  Effect.sandbox,
  Effect.catchCause((cause) => {
    console.log(Cause.pretty(cause))
    return Effect.succeed(fallback)
  })
)
```

## v4: Reason-Based Errors

v4 adds `catchReason` for errors with a tagged `reason` field:

```typescript
// v4 only
const handled = program.pipe(
  Effect.catchReason("AiError", "RateLimitError", (reason) =>
    Effect.retry(program, Schedule.exponential("1 second"))
  )
)
```

## Pattern: Error Hierarchy Design

For services with multiple error types, use a discriminated union:

```typescript
// v3
class ApiError extends Data.TaggedError("ApiError")<{
  readonly kind: "network" | "auth" | "not_found"
  readonly message: string
}> {}

// Better: separate tags for type-safe catchTag
class NetworkError extends Data.TaggedError("NetworkError")<{ cause: unknown }> {}
class AuthError extends Data.TaggedError("AuthError")<{ message: string }> {}
class NotFoundError extends Data.TaggedError("NotFoundError")<{ id: string }> {}

type ApiError = NetworkError | AuthError | NotFoundError
```
