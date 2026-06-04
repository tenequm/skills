# CLI

`effect/unstable/cli` builds command-line apps where handlers are Effects — flags and arguments are parsed and typed, and the whole program runs through the Effect runtime. (Unstable module, `@since 4.0.0`.)

```typescript
import { Command, Flag, Argument } from "effect/unstable/cli"
```

## A Minimal Command

```typescript
import { Console, Effect } from "effect"
import { Command, Flag } from "effect/unstable/cli"
import { NodeRuntime, NodeServices } from "@effect/platform-node"

const greet = Command.make(
  "greet",
  {
    name: Flag.string("name"),
    loud: Flag.boolean("loud")
  },
  (config) =>
    Effect.gen(function*() {
      const msg = `Hello, ${config.name}!`
      yield* Console.log(config.loud ? msg.toUpperCase() : msg)
    })
)

Command.run(greet, { version: "1.0.0" }).pipe(
  Effect.provide(NodeServices.layer),
  NodeRuntime.runMain
)
```

`Command.make(name, config?, handler?)` — `config` maps option names to `Flag.*` / `Argument.*` params (and can nest: `server: { host, port }`); the handler receives the parsed, typed values and returns an Effect.

> `Command.run` takes `{ version }` only — the command's name comes from the command itself, **not** a `{ name, version }` object. Use `Command.runWith(command, { version })(argv)` to pass args explicitly.

## Flags and Arguments

```typescript
const port = Flag.integer("port").pipe(Flag.withDefault(3000))
const verbose = Flag.boolean("verbose").pipe(Flag.withAlias("v"))
const config = Flag.file("config").pipe(Flag.optional)
const env = Flag.choice("env", ["dev", "prod"])

const file = Argument.string("file")
const rest = Argument.variadic(Argument.string("paths"))
```

`Flag.*` constructors: `string`, `boolean`, `integer`, `float`, `date`, `choice`, `path` / `file` / `directory`, `redacted`, `fileText` / `fileParse` / `fileSchema`, `keyValuePair`. Modifiers: `withDefault`, `withAlias`, `withDescription`, `optional`. `Argument.*` mirrors these and adds `Argument.variadic`. Both are built on the shared `Param` layer.

## Subcommands

```typescript
const root = Command.make("mytool").pipe(
  Command.withSubcommands([greet, otherCommand])
)
```

`Command.run` / `runWith` require the `FileSystem | Path | Terminal | ...` environment, all provided by `NodeServices.layer`; finish with `NodeRuntime.runMain` so SIGINT is handled.
