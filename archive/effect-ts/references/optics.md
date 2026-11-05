# Optics

`Optic` provides composable, type-safe access into immutable nested data — read, replace, and modify deeply nested fields without hand-written spreads. The v4 module is **instance/method-chain based** (a departure from v3's standalone-combinator `@fp-ts/optic` style): build an optic from `Optic.id<S>()` and chain `.key(...)` / `.at(...)`.

```typescript
import { Optic } from "effect"
```

## Building and Using an Optic

```typescript
interface State {
  readonly user: { readonly profile: { readonly age: number } }
}

// Focus a deeply nested field
const ageOptic = Optic.id<State>().key("user").key("profile").key("age")

const s: State = { user: { profile: { age: 30 } } }

ageOptic.get(s)                 // 30
const s2 = ageOptic.replace(31, s)        // { user: { profile: { age: 31 } } }
const s3 = ageOptic.modify((n) => n + 1)(s) // modify returns (s) => s
```

`Optic.id<S>()` is the identity optic over `S`. Chain to focus deeper:

- `.key(k)` - a struct field (always present) -> a `Lens`
- `.at(k)` - a map/array entry that may be absent -> an `Optional` (fails to focus if missing)
- `.optionalKey(k)`, `.pick(...)`, `.omit(...)`, `.tag(...)` / `.refine(...)`, `.check(...)`, `.compose(other)`

## Reading vs. Fallible Focus

`.get(s)` exists on lenses/isos (always-present focus). For optics that may fail to focus (`.at`, prisms), use `.getResult(s)`, which returns a `Result` (v4 renamed `Either` -> `Result`):

```typescript
import { Optic, Result } from "effect"

const firstTag = Optic.id<{ tags: ReadonlyArray<string> }>().key("tags").at(0)

const r = firstTag.getResult({ tags: ["a", "b"] }) // Result<string, string>
Result.isSuccess(r) // true
```

`.replace` and `.modify` never throw: if the optic can't focus the target, they return the original `S` unchanged.
