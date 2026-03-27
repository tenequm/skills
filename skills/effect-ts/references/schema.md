# Schema

Effect Schema provides bidirectional validation: decode (external input -> typed data) and encode (typed data -> wire format). Always import from `"effect"`, not `"@effect/schema"`.

```typescript
import { Schema } from "effect"
```

## Defining Schemas

```typescript
const User = Schema.Struct({
  id: Schema.String,
  name: Schema.String,
  age: Schema.Number,
  email: Schema.optionalWith(Schema.String, { exact: true }) // v3
  // v4: Schema.optionalKey(Schema.String)
})

// Infer the TypeScript type
type User = typeof User.Type
// { id: string; name: string; age: number; email?: string }
```

## Common Schema Types

| Schema                       | Decoded Type                    |
|------------------------------|---------------------------------|
| `Schema.String`              | `string`                        |
| `Schema.Number`              | `number`                        |
| `Schema.Boolean`             | `boolean`                       |
| `Schema.Literal("a", "b")`  | `"a" \| "b"` (v3 variadic)     |
| `Schema.Literals(["a","b"])`| `"a" \| "b"` (v4 array)        |
| `Schema.Array(Schema.String)`| `string[]`                     |
| `Schema.NullOr(Schema.String)` | `string \| null`             |
| `Schema.Union(A, B)` (v3)   | `A \| B`                       |
| `Schema.Union([A, B])` (v4) | `A \| B`                       |
| `Schema.Record(Schema.String, Schema.Number)` | `Record<string, number>` (v4) |
| `Schema.NumberFromString`    | string on wire, number decoded  |
| `Schema.DateFromString`      | string on wire, Date decoded    |

## Decoding (Parse)

```typescript
// Sync (throws on failure)
const user = Schema.decodeUnknownSync(User)(rawData)

// Effect-based (typed error)
// v3:
const user = yield* Schema.decodeUnknown(User)(rawData)
// v4:
const user = yield* Schema.decodeUnknownEffect(User)(rawData)

// Returns Exit instead of throwing
// v3: Schema.decodeUnknownEither(User)(rawData)
// v4: Schema.decodeUnknownExit(User)(rawData)
```

## Encoding

```typescript
// Sync
const json = Schema.encodeSync(User)(user)

// Effect-based
// v3: yield* Schema.encode(User)(user)
// v4: yield* Schema.encodeEffect(User)(user)
```

## Filters and Validation

### v3

```typescript
const PositiveAge = Schema.Number.pipe(
  Schema.positive(),
  Schema.int()
)

const ShortString = Schema.String.pipe(
  Schema.minLength(1),
  Schema.maxLength(100)
)
```

### v4

```typescript
const PositiveAge = Schema.Number.check(
  Schema.isGreaterThan(0),
  Schema.isInt()
)

const ShortString = Schema.String.check(
  Schema.isMinLength(1),
  Schema.isMaxLength(100)
)
```

## Tagged Error Classes

### v3

```typescript
import { Data } from "effect"

class NotFoundError extends Data.TaggedError("NotFoundError")<{
  readonly id: string
}> {}
```

### v4

```typescript
import { Schema } from "effect"

class NotFoundError extends Schema.TaggedErrorClass<NotFoundError>()("NotFoundError", {
  id: Schema.String
}) {}
```

## JSON Schema Generation

Effect Schema generates **JSON Schema Draft-07** (not 2020-12):

```typescript
import { JSONSchema, Schema } from "effect"

const jsonSchema = JSONSchema.make(User)
// { "$schema": "http://json-schema.org/draft-07/schema#", ... }
```

## Struct Operations

### v3

```typescript
const Picked = User.pipe(Schema.pick("id", "name"))
const Omitted = User.pipe(Schema.omit("age"))
const Extended = User.pipe(Schema.extend(Schema.Struct({ role: Schema.String })))
const Partial = User.pipe(Schema.partial)
```

### v4

```typescript
import { Struct } from "effect"

const Picked = User.mapFields(Struct.pick(["id", "name"]))
const Omitted = User.mapFields(Struct.omit(["age"]))
const Extended = User.mapFields(Struct.assign({ role: Schema.String }))
const Partial = User.mapFields(Struct.map(Schema.optional))
```

## Transforms

### v3

```typescript
const BoolFromString = Schema.transform(
  Schema.Literal("on", "off"),
  Schema.Boolean,
  {
    decode: (s) => s === "on",
    encode: (b) => b ? "on" : "off"
  }
)
```

### v4

```typescript
import { SchemaTransformation } from "effect"

const BoolFromString = Schema.Literals(["on", "off"]).pipe(
  Schema.decodeTo(
    Schema.Boolean,
    SchemaTransformation.transform({
      decode: (s) => s === "on",
      encode: (b) => b ? "on" : "off"
    })
  )
)
```

## TypeScript Configuration

Effect Schema requires `strict: true` in tsconfig. Optionally enable `exactOptionalPropertyTypes: true` for precise optional field handling.
