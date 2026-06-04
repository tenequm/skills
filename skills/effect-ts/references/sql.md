# SQL

Effect's SQL toolkit gives typed, composable database access with tagged-template queries, Schema-validated decoding, models, and migrations. Core modules live under `effect/unstable/sql/*`; concrete drivers ship as `@effect/sql-*` packages.

> Key fact: a tagged-template query **is an Effect** — `Statement<A> extends Effect<ReadonlyArray<A>, SqlError>`. You `yield*` it directly; there is no `.execute()`.

## Running Queries

```typescript
import { Effect } from "effect"
import { SqlClient } from "effect/unstable/sql/SqlClient"

interface User {
  readonly id: number
  readonly name: string
}

const program = Effect.gen(function*() {
  const sql = yield* SqlClient.SqlClient

  const id = 1
  const users = yield* sql<User>`SELECT * FROM users WHERE id = ${id}` // ReadonlyArray<User>

  yield* sql`INSERT INTO users ${sql.insert({ name: "Alice" })}`

  return users
})
```

Interpolated values (`${id}`) are bound parameters, not string-concatenated — safe from injection.

### Statement helpers (on `sql`)

`sql.insert(record | records)`, `sql.update(record)`, `sql.updateValues(rows, alias)`, `sql.in(values)` / `sql.in(col, values)`, `sql.and(clauses)`, `sql.or(clauses)`, `sql.csv(values)`, `sql.unsafe(raw, params?)`, `sql.literal(raw)`, `sql.onDialect({ pg, sqlite, ... })`.

### Transactions

```typescript
yield* sql.withTransaction(
  Effect.gen(function*() {
    yield* sql`INSERT INTO accounts ${sql.insert({ id: 1, balance: 100 })}`
    yield* sql`UPDATE accounts SET balance = balance - 50 WHERE id = ${1}`
  })
) // nested withTransaction uses savepoints
```

## Schema-Validated Queries (`SqlSchema`)

Derive queries that decode rows through an Effect `Schema`. Constructors: `SqlSchema.findAll`, `SqlSchema.findNonEmpty`, `SqlSchema.findOne`, `SqlSchema.findOneOption`, `SqlSchema.void` (there is **no `single`**).

```typescript
import { Effect, Schema } from "effect"
import { SqlClient } from "effect/unstable/sql/SqlClient"
import * as SqlSchema from "effect/unstable/sql/SqlSchema"

const getUserById = Effect.gen(function*() {
  const sql = yield* SqlClient.SqlClient
  return SqlSchema.findOne({
    Request: Schema.Number,
    Result: Schema.Struct({ id: Schema.Number, name: Schema.String }),
    execute: (id) => sql`SELECT id, name FROM users WHERE id = ${id}`
  })
})
// findOne fails with NoSuchElementError if no row; findOneOption returns Option
```

## Models and Repositories

`Model.Class` (from `effect/unstable/schema`) defines a table-backed schema with insert/update/json variants. Use `Model.GeneratedByDb` for DB-generated columns (e.g. auto-increment ids) — note this replaced `Model.Generated` (renamed in beta.68). `SqlModel.makeRepository` derives CRUD operations.

```typescript
import { Effect, Schema } from "effect"
import { Model } from "effect/unstable/schema"
import * as SqlModel from "effect/unstable/sql/SqlModel"

const UserId = Schema.Number.pipe(Schema.brand("UserId"))

class User extends Model.Class<User>("User")({
  id: Model.GeneratedByDb(UserId),
  name: Schema.String,
  createdAt: Model.DateTimeInsertFromDate,
  updatedAt: Model.DateTimeUpdateFromDate
}) {}

const makeUserRepo = SqlModel.makeRepository(User, {
  tableName: "users",
  spanPrefix: "UserRepo",
  idColumn: "id"
})
// yields { insert, insertVoid, update, updateVoid, findById, delete }
```

`SqlModel` exports only `makeRepository` and `makeResolvers` (both return Effects requiring `SqlClient`).

## Migrations (`Migrator`)

`Migrator.make({ ... })` runs pending migrations in a transaction. Loaders: `Migrator.fromFileSystem(dir)`, `fromGlob`, `fromBabelGlob`, `fromRecord`. Driver packages expose a ready layer (e.g. `PgMigrator.layer`).

## Providing a Driver

Concrete `@effect/sql-*` packages: `@effect/sql-pg`, `-pglite`, `-mysql2`, `-mssql`, `-clickhouse`, `-libsql`, `-d1`, and SQLite variants (`-sqlite-node`, `-sqlite-bun`, `-sqlite-wasm`, ...). Each layer provides both its specific client and the generic `SqlClient`.

```typescript
import { Effect, Redacted } from "effect"
import { PgClient } from "@effect/sql-pg"

const PgLive = PgClient.layer({
  host: "localhost",
  port: 5432,
  database: "app",
  username: "postgres",
  password: Redacted.make("secret"), // password/url are Redacted
  maxConnections: 10
})

const runnable = program.pipe(Effect.provide(PgLive))
```

Use `PgClient.layerConfig(...)` to source the connection from `Config` instead of literals.

## Errors (`SqlError`)

Every statement fails with `SqlError` (`_tag: "SqlError"`) carrying a `reason`. **Match on `error.reason._tag`, not the top-level `_tag`** (which is always `"SqlError"`):

```typescript
program.pipe(
  Effect.catchTag("SqlError", (e) =>
    e.reason._tag === "UniqueViolation"
      ? Effect.succeed("duplicate")
      : Effect.fail(e)
  )
)
```

Reasons include `ConnectionError`, `UniqueViolation` (carries `constraint`), `ConstraintError`, `DeadlockError`, `SerializationError`, `*TimeoutError`, `SqlSyntaxError`, `Authentication`/`AuthorizationError`. Each exposes `isRetryable` for retry policies.
