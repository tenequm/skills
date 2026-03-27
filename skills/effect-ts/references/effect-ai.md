# Effect AI

The `@effect/ai` packages provide a provider-agnostic interface for language models. Write AI logic once, swap providers at runtime.

**Status:** Unstable / Alpha (marked "Unstable" in official docs). APIs may change between releases.

## Packages

| Package                    | Purpose                           |
|----------------------------|-----------------------------------|
| `@effect/ai`              | Core abstractions (LanguageModel, Tool, Chat) |
| `@effect/ai-openai`       | OpenAI provider                    |
| `@effect/ai-anthropic`    | Anthropic provider                 |
| `@effect/ai-amazon-bedrock` | Amazon Bedrock provider          |
| `@effect/ai-google`       | Google Gemini provider             |
| `@effect/ai-openrouter`   | OpenRouter provider (undocumented, in repo) |

v4 consolidates AI modules into `effect/unstable/ai` (import from `"effect/unstable/ai/LanguageModel"` etc.).

## Basic Text Generation

```typescript
import { LanguageModel } from "@effect/ai"
import { OpenAiLanguageModel } from "@effect/ai-openai"

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

```typescript
import { Tool, Toolkit } from "@effect/ai"

// Define a tool
const weatherTool = Tool.make("getWeather", {
  description: "Get current weather for a location",
  parameters: Schema.Struct({
    location: Schema.String
  }),
  handler: ({ location }) => fetchWeather(location)
})

// Group tools into a toolkit
const tools = Toolkit.make(weatherTool, calculatorTool)

// Use with LanguageModel
const response = yield* LanguageModel.generateText({
  prompt: "What's the weather in San Francisco?",
  tools
})
```

## Chat (Stateful Conversations)

```typescript
import { Chat } from "@effect/ai"

const chatSession = yield* Chat.make()

const response1 = yield* Chat.send(chatSession, "Hello, who are you?")
const response2 = yield* Chat.send(chatSession, "What did I just say?")
// Chat maintains conversation history automatically
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
