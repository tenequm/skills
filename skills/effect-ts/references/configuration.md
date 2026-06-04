# Configuration (Config / ConfigProvider)

Effect's `Config` module reads configuration (env vars by default) as typed, validated values inside the type system. A `Config<T>` *is* an `Effect<T, ConfigError>`, so you consume it with `yield*` and it resolves against the `ConfigProvider` in the fiber's services. Always import from `"effect"`.

```typescript
import { Config, Effect } from "effect"
```

> v4 note: in v4 `Config` is schema-backed — every constructor delegates to `Config.schema`, and several constructors (`Config.schema`, `Config.int`, `Config.finite`, `Config.literals`) are `@since 4.0.0`. The consumption model (`yield* Config.string(...)`) is the same across v3 and v4.

## Reading Values

```typescript
const program = Effect.gen(function*() {
  const host = yield* Config.string("HOST")
  const port = yield* Config.port("PORT")            // validates 1-65535
  const debug = yield* Config.boolean("DEBUG")       // "true"/"yes"/"on"/"1" -> true
  const timeout = yield* Config.duration("TIMEOUT")  // "10 seconds" -> Duration
  const apiKey = yield* Config.redacted("API_KEY")   // Redacted<string> (won't print)
  return { host, port, debug, timeout, apiKey }
})
```

Common constructors: `Config.string`, `Config.nonEmptyString`, `Config.number`, `Config.int`, `Config.boolean`, `Config.duration`, `Config.port`, `Config.url`, `Config.date`, `Config.literal` / `Config.literals`, `Config.logLevel`, `Config.redacted`.

## Defaults, Optional, Nesting

```typescript
// Fall back to a default (only on MISSING data, not on validation failure)
const port = yield* Config.port("PORT").pipe(Config.withDefault(8080))

// Option<T> when absent
const proxy = yield* Config.option(Config.string("PROXY_URL"))

// Group related config and namespace it (reads DATABASE_HOST / DATABASE_PORT)
const db = yield* Config.all({
  host: Config.string("HOST"),
  port: Config.number("PORT")
}).pipe(Config.nested("DATABASE"))
```

`Config.all` accepts a struct (object) or a tuple/iterable of configs and combines them. `withDefault` / `option` only recover from *missing* data — a present-but-invalid value (wrong type, out of range) still fails with a `ConfigError`.

## Schema-Validated Config

`Config.schema` decodes raw config through an Effect `Schema`, giving full validation and transformation:

```typescript
import { Config, Schema } from "effect"

const AppConfig = Config.schema(
  Schema.Struct({ host: Schema.String, port: Schema.Int }),
  "APP"
)
```

## Providing a ConfigProvider

The default provider reads from `process.env`. Override it (tests, embedded config) by providing a `ConfigProvider` via its layer. There is **no `ConfigProvider.fromJson`** — use `ConfigProvider.fromUnknown(obj)` for an in-memory object or `ConfigProvider.fromEnv({ env })` for an explicit env map.

```typescript
import { Config, ConfigProvider, Effect, Layer } from "effect"

const TestConfig = ConfigProvider.layer(
  ConfigProvider.fromUnknown({ HOST: "localhost", PORT: "8080", DEBUG: "yes" })
)

const runnable = program.pipe(Effect.provide(TestConfig))
```

Other provider helpers: `ConfigProvider.fromEnv`, `ConfigProvider.fromDotEnv`, `ConfigProvider.fromDir`, plus combinators `orElse`, `nested`, `constantCase`, `mapInput`. The provider is a `Context.Reference` service, so you can also set it inline with `Effect.provideService(ConfigProvider.ConfigProvider, provider)`.
