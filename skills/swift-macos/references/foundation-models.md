# Foundation Models Framework

On-device AI using Apple's ~3B parameter LLM. Available on macOS 26+ with Apple Silicon. Free inference, offline, private.

All symbol references cite the shipped SDK swiftinterface at `FoundationModels.framework/.../arm64e-apple-macos.swiftinterface` (lines indicated inline) and/or Apple's developer documentation.

## Table of Contents
- Setup & Basic Usage
- Instructions
- Guided Generation (Structured Output)
- Streaming
- Tool Calling
- Sessions & Context
- Generation Options
- Error Handling
- Built-in Use Cases
- Custom Adapters
- Language Support & Limits
- Availability & Limitations

## Setup

```swift
import FoundationModels

let model = SystemLanguageModel.default

switch model.availability {
case .available:
    break
case .unavailable(.deviceNotEligible):
    // Intel Mac, non-A17/M-series, etc.
    return
case .unavailable(.appleIntelligenceNotEnabled):
    // User must enable in Settings > Apple Intelligence & Siri.
    return
case .unavailable(.modelNotReady):
    // Model is still downloading / preparing.
    return
}
```

The four-case `Availability` enum (`.available` plus three `UnavailableReason`s) is defined at swiftinterface lines 555-572. `SystemLanguageModel.default` is at line 576. There is also a `final public var isAvailable: Bool` on the model (line 518) for a quick boolean check.

Requires: macOS 26+ / iOS 26+ / iPadOS 26+ / visionOS 26+, Apple Silicon, Apple Intelligence enabled.

## Basic Usage

```swift
let session = LanguageModelSession()
let response = try await session.respond(to: "Summarize: \(text)")
print(response.content)          // Swift.String
print(response.transcriptEntries) // ArraySlice<Transcript.Entry>
```

The return type is `LanguageModelSession.Response<String>`, not `String` directly (swiftinterface lines 347-354). `Response<Content>` exposes `content`, `rawContent: GeneratedContent`, and `transcriptEntries`.

## Instructions

Set the system prompt at session creation. Instructions are fixed for the lifetime of the session.

```swift
let session = LanguageModelSession(
    instructions: """
    You are a concise writing assistant. Focus on grammar and clarity.
    Never add commentary; return only the rewritten text.
    """
)
let rewritten = try await session.respond(to: "Review: \(userText)").content
```

Correct initializer: `convenience init(model: SystemLanguageModel = .default, tools: [any Tool] = [], instructions: String? = nil)` (swiftinterface line 339). Overloads also accept `Instructions` directly or an `@InstructionsBuilder` closure (lines 340-341).

## Guided Generation

Generate Swift types directly - the framework constrains decoding to your schema, no JSON parsing.

```swift
@Generable
struct RecipeSuggestion {
    @Guide(description: "Name of the recipe")
    var name: String

    @Guide(description: "Ingredients with quantities")
    var ingredients: [String]

    @Guide(description: "Step-by-step instructions")
    var steps: [String]

    @Guide(description: "Estimated cooking time in minutes", .range(5...180))
    var cookingTime: Int
}

let session = LanguageModelSession()
let result: LanguageModelSession.Response<RecipeSuggestion> = try await session.respond(
    to: "Suggest a quick pasta recipe",
    generating: RecipeSuggestion.self
)
let recipe = result.content
print(recipe.name, recipe.cookingTime)
```

`respond(to:generating:...)` returns `Response<Content>` where `Content: Generable` (swiftinterface lines 378-382). The `@Generable` macro is at line 16; `@Guide` overloads at lines 24/28/32. `GenerationGuide` supports `.range(_:)`, `.minimum(_:)`, `.maximum(_:)` for numerics; `.anyOf(_:)`, `.constant(_:)`, `.pattern(_:)` for `String`; `.count(_:)`, `.minimumCount(_:)`, `.maximumCount(_:)`, `.element(_:)` for arrays (lines 254-299).

Built-in `Generable` conformances: `Bool`, `String`, `Int`, `Float`, `Double`, `Decimal`, `Array<Element: Generable>`, `Optional`, plus your own `@Generable` structs and enums (lines 92-195).

### Enum-constrained output
```swift
@Generable
enum Sentiment: String, CaseIterable {
    case positive, negative, neutral
}

@Generable
struct SentimentResult {
    var sentiment: Sentiment
    @Guide(description: "0.0 - 1.0 confidence", .range(0.0...1.0))
    var confidence: Double
}

let analysis = try await session.respond(
    to: "Analyze sentiment: '\(review)'",
    generating: SentimentResult.self
).content
```

## Streaming

Stream partial results for responsive UI. Snapshots contain `Content.PartiallyGenerated` which fills in progressively (swiftinterface lines 463-468).

```swift
// Text streaming - snapshots are String snapshots
for try await snapshot in session.streamResponse(to: "Write a short story.") {
    view.text = snapshot.content // current complete text so far
}

// Structured streaming — given a @Generable target type:
@Generable
struct TripPlan {
    @Guide(description: "Destination city")
    var destination: String
    @Guide(description: "Day-by-day itinerary")
    var days: [String]
    @Guide(description: "Estimated budget in USD", .range(0...10_000))
    var budgetUSD: Int
}

// Pick one: iterate for live updates, OR collect once for the final value.
// The stream is single-pass; iterating consumes it.
let stream = session.streamResponse(
    to: "Plan a weekend trip",
    generating: TripPlan.self
)
for try await snapshot in stream {
    // snapshot.content: TripPlan.PartiallyGenerated (optionals fill in over time)
    render(snapshot.content)
}

// Or, without iterating, collect the final value:
let finalResponse = try await session.streamResponse(
    to: "Plan a weekend trip",
    generating: TripPlan.self
).collect() // Response<TripPlan>
```

`ResponseStream.collect()` is at swiftinterface line 491. The stream conforms to `AsyncSequence` (line 473).

## Tool Calling

`Tool` is a protocol, not a macro. There is no `@Toolbox` or `@Tool` annotation in the framework. Each tool is a `Sendable` type with an associated `Arguments: Generable` and `Output: PromptRepresentable` (swiftinterface lines 1186-1196).

```swift
struct GetWeather: Tool {
    let name = "getWeather"
    let description = "Get current weather for a city."

    @Generable
    struct Arguments {
        @Guide(description: "City name, e.g. 'San Francisco'")
        var city: String
    }

    func call(arguments: Arguments) async throws -> String {
        let w = try await WeatherService.current(for: arguments.city)
        return "\(w.tempF)F, \(w.conditions)"
    }
}

struct GetForecast: Tool {
    let name = "getForecast"
    let description = "Get an N-day forecast for a city."

    @Generable
    struct Arguments {
        var city: String
        @Guide(description: "Number of days", .range(1...10))
        var days: Int
    }

    func call(arguments: Arguments) async throws -> String {
        let f = try await WeatherService.forecast(for: arguments.city, days: arguments.days)
        return f.map { "\($0.date): \($0.conditions)" }.joined(separator: "\n")
    }
}

let session = LanguageModelSession(
    tools: [GetWeather(), GetForecast()],
    instructions: "Use the weather tools when asked about weather."
)
let answer = try await session.respond(
    to: "Should I bring an umbrella to SF tomorrow?"
).content
```

Notes from the framework:
- `Arguments` must be `Generable`. `String`, `Int`, `Double`, `Float`, `Decimal`, and `Bool` are *explicitly unavailable* as `Arguments` (swiftinterface lines 1219-1268) - use an `@Generable` struct that wraps them.
- `Output` must be `PromptRepresentable`. `String` and `Array<PromptRepresentable>` already conform (lines 1131, 1139).
- `call(arguments:)` runs on the `@concurrent` executor; make it `async throws`.
- TN3193 recommends a maximum of 3-5 tools per session to keep schemas small in the context window.

## Sessions & Context

Sessions are stateful and thread-safe (`final public class` marked `@unchecked Sendable`, swiftinterface lines 321-397). Re-use one across turns; the transcript grows automatically.

```swift
let session = LanguageModelSession(instructions: "You are a code reviewer.")
session.prewarm() // Optional: start loading the model in the background.

let r1 = try await session.respond(to: "Review: \(code)")
let r2 = try await session.respond(to: "How would you refactor it?")
// session.transcript contains all instructions/prompts/responses so far.

// Check whether a response is in flight
if !session.isResponding {
    // safe to start another respond(...)
}
```

There is no `session.reset()` method. To start fresh, create a new session. To preserve partial state across the reset, rebuild a `Transcript` from the old session's entries:

```swift
// Start a new session that carries the first and last turns only.
func condensed(from old: LanguageModelSession) -> LanguageModelSession {
    let kept = [old.transcript.first, old.transcript.last].compactMap { $0 }
    let transcript = Transcript(entries: kept)
    let session = LanguageModelSession(transcript: transcript)
    session.prewarm()
    return session
}
```

`prewarm(promptPrefix:)` is at swiftinterface line 343. The `LanguageModelSession(transcript:)` initializer is at line 342. This pattern is the one Apple recommends for recovering from context-window errors (TN3193).

## Generation Options

```swift
let options = GenerationOptions(
    sampling: .greedy,              // or .random(top: 40), .random(probabilityThreshold: 0.9)
    temperature: 0.2,               // lower = more deterministic
    maximumResponseTokens: 512      // cap response size
)

let r = try await session.respond(to: prompt, options: options).content
```

`GenerationOptions` is a `struct` with `sampling: SamplingMode?`, `temperature: Double?`, `maximumResponseTokens: Int?` (swiftinterface lines 1311-1328). `SamplingMode` offers `.greedy`, `.random(top:seed:)`, `.random(probabilityThreshold:seed:)` (lines 1315-1322).

TN3193 warns: use `maximumResponseTokens` only as a safety cap against runaway generations; hard truncation can produce malformed partial output. To shorten responses, ask in the prompt ("In 3 sentences...") or use `.maximumCount(_:)` on `Generable` arrays.

## Error Handling

`LanguageModelSession.GenerationError` is an enum with these cases (swiftinterface lines 405-443):

```swift
do {
    let response = try await session.respond(to: prompt, options: options)
    return response.content
} catch LanguageModelSession.GenerationError.guardrailViolation(let ctx) {
    // Apple safety guardrail tripped. Don't blindly retry - reword or decline.
    log("guardrail: \(ctx.debugDescription)")
    return fallback
} catch LanguageModelSession.GenerationError.exceededContextWindowSize(let ctx) {
    // Context window full (4096 tokens). Start a new session with a condensed transcript.
    log("context full: \(ctx.debugDescription)")
    return try await condensed(from: session).respond(to: prompt).content
} catch LanguageModelSession.GenerationError.unsupportedLanguageOrLocale(let ctx) {
    return "Language not supported: \(ctx.debugDescription)"
} catch LanguageModelSession.GenerationError.assetsUnavailable(let ctx) {
    // Model / adapter assets not downloaded yet.
    return "Model unavailable: \(ctx.debugDescription)"
} catch LanguageModelSession.GenerationError.rateLimited {
    return "Too many requests - back off."
} catch LanguageModelSession.GenerationError.concurrentRequests {
    return "Only one request per session at a time."
} catch LanguageModelSession.GenerationError.refusal(let refusal, _) {
    // Model refused. `refusal.explanation` is an async call to fetch the reason.
    return try await refusal.explanation.content
} catch LanguageModelSession.GenerationError.decodingFailure(let ctx) {
    // Guided generation produced content that failed to decode into your type.
    throw NSError(domain: "decoding", code: 0, userInfo: [NSLocalizedDescriptionKey: ctx.debugDescription])
} catch LanguageModelSession.GenerationError.unsupportedGuide(let ctx) {
    // A @Guide constraint isn't supported (e.g. unsupported regex feature).
    throw NSError(domain: "guide", code: 0, userInfo: [NSLocalizedDescriptionKey: ctx.debugDescription])
}
```

Every case carries a `GenerationError.Context` with a `debugDescription`. The `.refusal` case additionally carries a `Refusal` whose `explanation` / `explanationStream` let you ask the model why it refused (swiftinterface lines 416-433).

Tool errors surface as a separate `LanguageModelSession.ToolCallError` that wraps your tool and the underlying error (lines 447-454).

## Built-in Use Cases

`SystemLanguageModel.UseCase` is a struct (not an enum). Only two values ship on macOS 26 (swiftinterface lines 524-528):

- `.general` - the default model.
- `.contentTagging` - optimized for generating tags/topics/classifications from text.

```swift
// Content tagging model - better than .general for tag/topic extraction.
let taggingModel = SystemLanguageModel(useCase: .contentTagging)
let session = LanguageModelSession(model: taggingModel)

@Generable
struct Tags {
    @Guide(description: "3-7 topical tags", .maximumCount(7))
    var tags: [String]
}
let tags = try await session.respond(
    to: "Tag this article: \(text)",
    generating: Tags.self
).content.tags
```

`SystemLanguageModel(useCase:guardrails:)` is at swiftinterface line 582. Guardrails are either `.default` or `.permissiveContentTransformations` (lines 543-547); use the permissive option only for transformation tasks on user-provided content (summarize, translate, rewrite).

## Custom Adapters

A custom LoRA adapter lets you specialize the base model's behavior. Training happens out-of-band with Apple's Python toolkit; the deployed artifact is an `.fmadapter` package.

Key rules (from Apple's "Loading and using a custom adapter" doc):
- Adapter files are 160 MB or larger - **do not bundle them in your app**. Download on demand via Background Assets or a Managed Asset Pack.
- Each adapter is locked to a specific base model version. You must retrain for every new base model release.
- Shipping adapters requires the `com.apple.developer.foundation-model-adapter` entitlement. Local testing does not.
- Adapters run only on physical devices (not Simulator).

### Local testing (file URL)

```swift
let url = URL(filePath: "/absolute/path/to/my.fmadapter")
let adapter = try SystemLanguageModel.Adapter(fileURL: url)
let model = SystemLanguageModel(adapter: adapter)
let session = LanguageModelSession(model: model)
let response = try await session.respond(to: "...")
```

`Adapter(fileURL:)` is at swiftinterface line 663; `SystemLanguageModel(adapter:)` is at line 586.

### Shipping (Background Assets)

```swift
// Clear out any adapters from older base-model versions.
try SystemLanguageModel.Adapter.removeObsoleteAdapters()

// Load by base name. Triggers a Background Assets download if needed.
let adapter = try SystemLanguageModel.Adapter(name: "myAdapter")

// Optional: compile the draft model once (if your adapter has one) for faster inference.
try await adapter.compile()

let model = SystemLanguageModel(adapter: adapter)
let session = LanguageModelSession(model: model)
```

`Adapter(name:)`, `removeObsoleteAdapters()`, `compile()`, `compatibleAdapterIdentifiers(name:)`, and `isCompatible(_:)` are all on `SystemLanguageModel.Adapter` (swiftinterface lines 664-673). The asset-downloader extension's `shouldDownload(_:)` should delegate adapter-compatibility checks to `SystemLanguageModel.Adapter.isCompatible(assetPack)`.

See: <https://developer.apple.com/documentation/foundationmodels/loading-and-using-a-custom-adapter-with-foundation-models> and <https://developer.apple.com/apple-intelligence/foundation-models-adapter> for the Python toolkit.

## Language Support & Limits

```swift
let model = SystemLanguageModel.default
model.supportedLanguages     // Set<Locale.Language>
model.supportsLocale(.current) // Bool
model.contextSize            // Int (4096 on macOS 26)
```

`supportedLanguages`, `supportsLocale(_:)`, and `contextSize` are at swiftinterface lines 587-590 and 635-644.

**Context window**: 4096 tokens per `LanguageModelSession`, covering instructions, prompts, tool definitions, tool outputs, `Generable` schemas, and all responses (TN3193). When you exceed it, the framework throws `.exceededContextWindowSize` - create a fresh session with a condensed transcript (see "Sessions & Context" above).

**Token counting** (macOS 26.4+): `SystemLanguageModel` exposes `tokenCount(for:)` overloads for `Prompt`, `Instructions`, `[Tool]`, `GenerationSchema`, and transcript-entry collections (swiftinterface lines 600-624). Use these plus the Foundation Models Instruments template (Xcode > Instruments > Foundation Models) to profile consumption.

## Availability & Limitations

- **Hardware**: Apple Silicon only (A17 Pro / M1 and later where Apple Intelligence is supported).
- **OS**: macOS 26+, iOS 26+, iPadOS 26+, visionOS 26+. Unavailable on tvOS and watchOS (swiftinterface `@available ... tvOS, unavailable; watchOS, unavailable`).
- **Model size**: ~3B parameters on-device.
- **Strengths**: summarization, content generation, structured extraction, classification, tagging, light tool use.
- **Limitations**: not a general-knowledge chatbot, 4096-token context window, no image generation, one in-flight request per session (`.concurrentRequests`).
- **Privacy**: all inference runs on device. No data sent to Apple.
- **Cost**: free; no API keys, no quotas beyond hardware throughput.

Primary references:
- <https://developer.apple.com/documentation/foundationmodels>
- <https://developer.apple.com/documentation/foundationmodels/generating-content-and-performing-tasks-with-foundation-models>
- <https://developer.apple.com/documentation/technotes/tn3193-managing-the-on-device-foundation-model-s-context-window>
- <https://developer.apple.com/documentation/foundationmodels/loading-and-using-a-custom-adapter-with-foundation-models>
