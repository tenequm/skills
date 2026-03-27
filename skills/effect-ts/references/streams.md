# Streams

Effect Streams are pull-based, lazily evaluated sequences of values with typed errors and resource safety.

## Creating Streams

```typescript
import { Stream } from "effect"

// From an iterable
const fromArray = Stream.fromIterable([1, 2, 3])

// From a single effect
const fromEffect = Stream.fromEffect(fetchUser(id))

// From repeated effect on a schedule
const polling = Stream.fromEffectSchedule(
  checkStatus,
  Schedule.spaced("1 second")
)

// Paginated API
const pages = Stream.paginate(1, (page) => [
  fetchPage(page),
  page < totalPages ? Option.some(page + 1) : Option.none()
])

// From an async iterable
const fromAsync = Stream.fromAsyncIterable(
  asyncIterator,
  (err) => new StreamError({ cause: err })
)

// Callback-based (SSE, WebSocket, etc.)
const fromCallback = Stream.async<string, never>((emit) => {
  source.on("data", (chunk) => emit.single(chunk))
  source.on("end", () => emit.end())
  source.on("error", (err) => emit.fail(new StreamError({ cause: err })))
})
```

## Transforming Streams

```typescript
const transformed = myStream.pipe(
  Stream.map((x) => x * 2),
  Stream.filter((x) => x > 10),
  Stream.take(5),
  Stream.tap((x) => Effect.log(`Processing: ${x}`))
)

// Effectful transform
const enriched = Stream.mapEffect(myStream, (item) =>
  fetchDetails(item.id),
  { concurrency: 5 }
)

// FlatMap (one-to-many)
const expanded = Stream.flatMap(usersStream, (user) =>
  Stream.fromIterable(user.posts)
)
```

## Consuming Streams

```typescript
// Collect all into an array
const items = yield* Stream.runCollect(myStream)

// Fold/reduce
const sum = yield* Stream.runFold(myStream, 0, (acc, x) => acc + x)

// Process each item
yield* Stream.runForEach(myStream, (item) => processItem(item))

// Run to completion, discard results
yield* Stream.runDrain(myStream)

// Using Sink for reusable consumption patterns
import { Sink } from "effect"
const count = yield* Stream.run(myStream, Sink.count)
```

## Queue-to-Stream Bridge

```typescript
import { Queue, Stream } from "effect"

const queue = yield* Queue.bounded<string>(100)

// Convert queue to stream (stream pulls from queue)
const stream = Stream.fromQueue(queue)

// Process stream in background, offer to queue from producers
yield* Effect.forkScoped(
  Stream.runForEach(stream, (msg) => handleMessage(msg))
)

// Producers offer to queue
yield* Queue.offer(queue, "new message")
```

## PubSub (Fan-out)

```typescript
import { PubSub, Stream } from "effect"

const pubsub = yield* PubSub.bounded<Event>(100)

// Subscribe returns a Queue (each subscriber gets all messages)
const subscription = yield* PubSub.subscribe(pubsub)
const stream = Stream.fromQueue(subscription)

// Publish
yield* PubSub.publish(pubsub, { type: "user_created", userId: "123" })
```

## Chunked Processing

Streams process data in chunks for efficiency:

```typescript
// Group into fixed-size chunks
const chunked = Stream.grouped(myStream, 100)

// Group by time window
const windowed = Stream.groupedWithin(myStream, 100, "5 seconds")
```

## Error Handling in Streams

```typescript
const resilient = myStream.pipe(
  Stream.retry(Schedule.exponential("1 second").pipe(
    Schedule.compose(Schedule.recurs(3))
  )),
  Stream.catchAll((error) => Stream.fromIterable(fallbackData))
)
```

## SSE / Streaming HTTP Pattern

For bridging HTTP SSE streams into Effect Streams:

```typescript
// Using HttpClient to consume SSE
const sseStream = Effect.gen(function*() {
  const client = yield* HttpClient.HttpClient
  const response = yield* client.execute(
    HttpClientRequest.get(url)
  )
  return response.stream.pipe(
    Stream.decodeText(),
    Stream.splitLines,
    Stream.filter((line) => line.startsWith("data: ")),
    Stream.map((line) => JSON.parse(line.slice(6)))
  )
})
```
