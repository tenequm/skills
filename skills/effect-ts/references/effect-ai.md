# Effect AI

The `@effect/ai` packages provide a provider-agnostic interface for language models. Write AI logic once, swap providers at runtime.

**Status:** Unstable / Alpha (marked "Unstable" in official docs). APIs may change between releases.

## Packages

### v3

| Package                     | Purpose                                          |
|-----------------------------|--------------------------------------------------|
| `@effect/ai`                | Core abstractions (LanguageModel, Tool, Toolkit, Chat, McpServer) |
| `@effect/ai-openai`         | OpenAI provider                                  |
| `@effect/ai-anthropic`      | Anthropic provider                               |
| `@effect/ai-amazon-bedrock` | Amazon Bedrock provider (v3 only)                |
| `@effect/ai-google`         | Google Gemini provider (v3 only)                 |
| `@effect/ai-openrouter`     | OpenRouter provider                              |

### v4

The core AI module is consolidated into `effect/unstable/ai` (no separate `@effect/ai` package). Provider packages still ship separately and currently include only `@effect/ai-anthropic`, `@effect/ai-openai`, `@effect/ai-openai-compat`, and `@effect/ai-openrouter` — Bedrock and Google providers are not yet ported to v4.

```typescript
// v4 imports
import { Chat, LanguageModel, McpSchema, McpServer, Tool, Toolkit } from "effect/unstable/ai"
```

## Basic Text Generation

```typescript
// v3
import { LanguageModel } from "@effect/ai"
import { OpenAiLanguageModel } from "@effect/ai-openai"

// v4 — equivalent imports:
//   import { LanguageModel } from "effect/unstable/ai"
//   import { OpenAiLanguageModel } from "@effect/ai-openai"

const program = Effect.gen(function*() {
  const response = yield* LanguageModel.generateText({
    prompt: "Explain Effect-TS in one sentence"
  })
  return response.text
})

// Provide the OpenAI layer
const main = program.pipe(
  Effect.provide(OpenAiLanguageModel.layer({ model: "gpt-4o" })),
  Effect.provide(OpenAiClient.layer({ apiKey: env.OPENAI_API_KEY }))
)
```

## Structured Output (Schema-Validated)

```typescript
const SentimentResult = Schema.Struct({
  sentiment: Schema.Literal("positive", "negative", "neutral"),
  confidence: Schema.Number
})

const analyze = LanguageModel.generateObject({
  prompt: `Analyze sentiment: "${text}"`,
  schema: SentimentResult
})
// Returns Effect<{ sentiment, confidence }, AiError, LanguageModel>
// Output is Schema-validated at runtime
```

## Streaming

```typescript
const stream = LanguageModel.streamText({
  prompt: "Write a story about..."
})
// Returns Stream<TextChunk, AiError, LanguageModel>

// Per-chunk processing (for token billing, SSE forwarding, etc.)
const processed = stream.pipe(
  Stream.tap((chunk) => incrementTokenCount(chunk)),
  Stream.map((chunk) => chunk.text)
)
```

## Tool Use

`Tool.make` defines only the *schema* of a tool — name, description, parameters, success/failure types. The runtime *handler* is attached separately via `Toolkit.toLayer`, which produces a Layer that the LanguageModel call requires.

```typescript
import { Effect, Schema } from "effect"
import { Tool, Toolkit } from "effect/unstable/ai" // v4 (or "@effect/ai" for v3)

// Define a tool — note: NO `handler` field on Tool.make
const GetWeather = Tool.make("GetWeather", {
  description: "Get current weather for a location",
  parameters: Schema.Struct({ location: Schema.String }),
  success: Schema.Struct({
    temperature: Schema.Number,
    condition: Schema.String
  })
})

// Group tools into a toolkit
const MyToolkit = Toolkit.make(GetWeather)

// Attach handlers via toLayer (handler keys match the tool names)
const MyToolkitLayer = MyToolkit.toLayer({
  GetWeather: ({ location }) => fetchWeather(location)
})

// Use with LanguageModel — provide the toolkit layer
const program = LanguageModel.generateText({
  prompt: "What's the weather in San Francisco?",
  toolkit: MyToolkit
}).pipe(Effect.provide(MyToolkitLayer))
```

## Chat (Stateful Conversations)

The Chat module returns a Service whose instance carries `generateText`, `streamText`, and `generateObject` methods. It threads conversation history through a Ref automatically — there is no static `Chat.send`.

```typescript
import { Chat } from "effect/unstable/ai" // v4 (or "@effect/ai" for v3)

const program = Effect.gen(function*() {
  const chat = yield* Chat.empty // also: Chat.fromPrompt(initial), Chat.makePersisted(...)

  const r1 = yield* chat.generateText({ prompt: "Hello, who are you?" })
  const r2 = yield* chat.generateText({ prompt: "What did I just say?" })
  // r2 sees the prior turn — history is appended in the chat's internal state
  return [r1.text, r2.text]
})
```

## MCP Server (v4)

Effect v4's AI modules include built-in MCP server support:

```typescript
// v4 only
import { McpServer, McpSchema } from "effect/unstable/ai"

// Define MCP tools using Effect's Schema and service patterns
```

## Provider Pattern

The key benefit: write AI logic against the abstract `LanguageModel` interface, then swap providers via layers:

```typescript
// Business logic - no provider dependency
const summarize = (text: string) =>
  LanguageModel.generateText({
    prompt: `Summarize: ${text}`
  })

// Production: OpenAI
const prod = summarize(text).pipe(
  Effect.provide(OpenAiLanguageModel.layer({ model: "gpt-4o" }))
)

// Development: local model via OpenRouter
const dev = summarize(text).pipe(
  Effect.provide(OpenRouterLanguageModel.layer({ model: "llama-3" }))
)

// Testing: mock
const test = summarize(text).pipe(
  Effect.provideService(LanguageModel, {
    generateText: () => Effect.succeed({ text: "mock summary" })
  })
)
```

## Observability

Effect AI integrates with Effect's built-in tracing. Each model call produces spans with:
- Model name and provider
- Input/output token counts
- Duration
- Error details

Use `Effect.withSpan` to create parent spans for multi-step AI workflows:

```typescript
const aiWorkflow = Effect.gen(function*() {
  const summary = yield* LanguageModel.generateText({ prompt: text })
  const analysis = yield* LanguageModel.generateObject({
    prompt: summary.text,
    schema: AnalysisSchema
  })
  return analysis
}).pipe(Effect.withSpan("ai.analyze-document"))
```
