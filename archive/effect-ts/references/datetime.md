# DateTime

`DateTime` is Effect's timezone-aware date/time type. It has two variants, both carrying an absolute instant (`epochMillis`):

- `DateTime.Utc` (`_tag: "Utc"`) - an instant with no zone
- `DateTime.Zoned` (`_tag: "Zoned"`) - an instant plus a `TimeZone`

```typescript
import { DateTime, Effect } from "effect"
```

> v4 naming: the unsafe constructors use `Unsafe` as a **suffix** (not a v3-style `unsafe*` prefix): `DateTime.makeUnsafe`, `DateTime.nowUnsafe`, `DateTime.makeZonedUnsafe`, `DateTime.zoneMakeNamedUnsafe`, `DateTime.fromDateUnsafe`. The safe `make` / `makeZoned` / `zoneMakeNamed` return `Option`, not `Effect`.

## Getting "now"

```typescript
const program = Effect.gen(function*() {
  const utc = yield* DateTime.now        // Effect<DateTime.Utc> (uses the Clock)
  return utc
})

// Outside Effect (impure):
const nowImpure = DateTime.nowUnsafe()
```

Prefer `yield* DateTime.now` inside effects — it reads the `Clock` service, so it is controllable in tests via `TestClock`.

## Constructing

```typescript
// Safe: returns Option
const maybe = DateTime.make("2026-06-04T12:00:00Z") // Option<Utc>

// Unsafe: throws on invalid input
const utc = DateTime.makeUnsafe("2026-06-04T12:00:00Z")
const fromDate = DateTime.fromDateUnsafe(new Date())
```

## Arithmetic

```typescript
const utc = DateTime.makeUnsafe("2026-06-04T12:00:00Z")

const later = utc.pipe(DateTime.addDuration("5 minutes")) // stays Utc
const tomorrow = utc.pipe(DateTime.add({ days: 1 }))       // calendar-aware
const startOfDay = utc.pipe(DateTime.startOf("day"))
```

`addDuration` / `subtractDuration` shift by a `Duration`; `add` / `subtract` take calendar parts (`{ days, months, hours, ... }`). These are variant-preserving — a `Utc` stays `Utc`.

## Time Zones

```typescript
const utc = DateTime.makeUnsafe("2026-06-04T12:00:00Z")

// Attach a named zone -> Zoned
const london = DateTime.setZone(utc, DateTime.zoneMakeNamedUnsafe("Europe/London"))

// Run an effect with an ambient current zone
const withZone = program.pipe(
  DateTime.withCurrentZone(DateTime.zoneMakeNamedUnsafe("America/New_York"))
)
```

`setZone` always returns a `Zoned`. `withCurrentZone` / `nowInCurrentZone` use a `CurrentTimeZone` service (provide it once via `DateTime.layerCurrentZoneNamed("...")`).

## Formatting

```typescript
DateTime.formatIso(utc)        // "2026-06-04T12:00:00.000Z"
DateTime.formatIsoDate(utc)    // "2026-06-04"
DateTime.format(london, { dateStyle: "full", timeStyle: "short" }) // Intl-based, zone-aware
```

Other formatters: `formatLocal`, `formatUtc`, `formatIntl`, `formatIsoOffset`, `formatIsoZoned`.
