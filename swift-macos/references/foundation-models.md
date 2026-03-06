# Foundation Models Framework

On-device AI using Apple's ~3B parameter LLM. Available on macOS 26+ with Apple Silicon. Free inference, offline, private.

## Table of Contents
- Setup & Basic Usage
- Guided Generation (Structured Output)
- Streaming
- Tool Calling
- Sessions & Context
- Availability & Limitations

## Setup

```swift
import FoundationModels

// Check availability
guard LanguageModelSession.isAvailable else {
    // Model not available (Intel Mac, older OS, etc.)
    return
}
```

Requires: macOS 26+, Apple Silicon, Apple Intelligence enabled in Settings.

## Basic Usage

```swift
let session = LanguageModelSession()
let response = try await session.respond(to: "Summarize this: \(text)")
print(response.content) // String
```

With system prompt:
```swift
let session = LanguageModelSession(
    instructions: """
    You are a helpful writing assistant. Respond concisely.
    Focus on clarity and grammar improvements.
    """
)
let response = try await session.respond(to: "Review: \(userText)")
```

## Guided Generation

Generate Swift types directly (no JSON parsing):

```swift
@Generable
struct RecipeSuggestion {
    @Guide(description: "Name of the recipe")
    var name: String

    @Guide(description: "List of ingredients with quantities")
    var ingredients: [String]

    @Guide(description: "Step by step instructions")
    var steps: [String]

    @Guide(description: "Estimated cooking time in minutes")
    var cookingTime: Int
}

let session = LanguageModelSession()
let recipe: RecipeSuggestion = try await session.respond(
    to: "Suggest a quick pasta recipe",
    generating: RecipeSuggestion.self
)
print(recipe.name)         // "Garlic Butter Pasta"
print(recipe.cookingTime)  // 20
```

Supported types for `@Generable`: `String`, `Int`, `Double`, `Bool`, `[T]`, `Optional<T>`, enums with `String` raw values, nested `@Generable` structs.

### Enum-constrained output
```swift
@Generable
enum Sentiment: String {
    case positive, negative, neutral
}

@Generable
struct SentimentResult {
    var sentiment: Sentiment
    var confidence: Double
}

let result: SentimentResult = try await session.respond(
    to: "Analyze sentiment: '\(review)'",
    generating: SentimentResult.self
)
```

## Streaming

For responsive UI, stream partial results:

```swift
// Text streaming
let stream = session.streamResponse(to: "Write a short story about a robot")

var fullText = ""
for try await partial in stream {
    fullText = partial.content // Updated complete text so far
    // Update UI progressively
}

// Structured streaming (snapshot-based)
let structuredStream = session.streamResponse(
    to: "Plan a weekend trip",
    generating: TripPlan.self
)

for try await snapshot in structuredStream {
    // snapshot is a partial TripPlan, fields fill in progressively
    updateUI(with: snapshot)
}
```

In SwiftUI:
```swift
struct AIResponseView: View {
    @State private var response = ""
    @State private var isGenerating = false

    var body: some View {
        VStack {
            ScrollView {
                Text(response)
                    .textSelection(.enabled)
            }
            if isGenerating {
                ProgressView()
            }
        }
        .task {
            await generate()
        }
    }

    func generate() async {
        isGenerating = true
        defer { isGenerating = false }

        let session = LanguageModelSession()
        let stream = session.streamResponse(to: prompt)

        do {
            for try await partial in stream {
                response = partial.content
            }
        } catch {
            response = "Error: \(error.localizedDescription)"
        }
    }
}
```

## Tool Calling

Let the model call functions to access external data:

```swift
@Toolbox
struct WeatherTools {
    @Tool(description: "Get current weather for a city")
    func getWeather(city: String) async throws -> String {
        let weather = try await WeatherService.current(for: city)
        return "Temperature: \(weather.temp)F, Conditions: \(weather.conditions)"
    }

    @Tool(description: "Get weather forecast for the next N days")
    func getForecast(city: String, days: Int) async throws -> String {
        let forecast = try await WeatherService.forecast(for: city, days: days)
        return forecast.map { "\($0.date): \($0.conditions)" }.joined(separator: "\n")
    }
}

let session = LanguageModelSession(tools: WeatherTools())
let response = try await session.respond(
    to: "Should I bring an umbrella to SF tomorrow?"
)
// Model automatically calls getWeather/getForecast, then synthesizes answer
```

## Sessions & Context

Sessions maintain conversation context:

```swift
let session = LanguageModelSession(
    instructions: "You are a code review assistant."
)

// First message
let r1 = try await session.respond(to: "Review this function: \(code)")

// Follow-up (session remembers context)
let r2 = try await session.respond(to: "How would you refactor it?")

// Reset context
session.reset()
```

## Availability & Limitations

- **Hardware**: Apple Silicon only (M1+)
- **OS**: macOS 26+, iOS 26+, iPadOS 26+, visionOS 26+
- **Model size**: ~3B parameters, optimized for on-device inference
- **Strengths**: Summarization, content generation, structured extraction, classification
- **Limitations**: Not a general-knowledge chatbot; limited context window; no image generation
- **Privacy**: All inference on-device, no data sent to Apple
- **Cost**: Free, no API keys, no rate limits

Check availability before use:
```swift
if LanguageModelSession.isAvailable {
    // Use Foundation Models
} else {
    // Fallback to traditional approach
}
```
