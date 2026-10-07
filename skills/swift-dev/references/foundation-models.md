# Foundation Models

Apple's language-model framework on iOS, iPadOS, macOS and visionOS: the on-device model, the Private Cloud Compute model, guided generation, tools, image input, dynamic sessions and error handling, plus a pointer to Core AI for bringing your own model.

Verified on Xcode 27.0 (Swift 6.4, iOS 27.0 / macOS 27.0 SDKs), 2026-10-07: every block compiled through SIL (`swiftc -emit-sil`, so region-isolation checks ran) for iOS 27 and macOS 27 with and without `-default-isolation MainActor` (the error-handling block also typechecked at an iOS 26 deployment target); a scratch SPM executable on macOS 27.2 with Apple Intelligence enabled ran text, guided, image, tool, dynamic-instruction and profile requests and triggered `contextSizeExceeded`, `concurrentRequests` and a PCC request without the entitlement.

## Contents
- Availability and models
- Sessions, instructions, responses
- Guided generation
- Streaming
- Tools
- Image input
- Context window and options
- Dynamic instructions and profiles
- Errors (27.0 error types)
- Private Cloud Compute
- Other models: LanguageModel protocol and Core AI

## Availability and models

| Model | OS | Context | Notes |
|---|---|---|---|
| `SystemLanguageModel.default` | iOS / macOS / visionOS 26+ | 4096 tokens | On device, offline, free, no limit. Not on watchOS or tvOS. |
| `PrivateCloudComputeLanguageModel()` | iOS / macOS / visionOS / watchOS 27+ | 32K | Server model on PCC, reasoning levels, per-person daily quota, managed entitlement. |
| Your own `LanguageModel` | 27+ | model-defined | Core AI, MLX or a server model behind the same session API. |

On macOS 27.2 the on-device model reported `variant.displayName == "AFM 3 Core"`, `contextSize == 4096`, and capabilities vision, tool calling and guided generation, not reasoning. The on-device model changes with OS updates (26.4, 27.0); re-test prompts on each release.

```swift
import FoundationModels

func onDeviceModelState() -> String {
    let model = SystemLanguageModel.default
    switch model.availability {
    case .available:
        return "ready"
    case .unavailable(.deviceNotEligible):
        return "hide the feature: no Apple Intelligence hardware"
    case .unavailable(.appleIntelligenceNotEnabled):
        return "ask the person to turn on Apple Intelligence in Settings"
    case .unavailable(.modelNotReady):
        return "model still downloading - try later"
    case .unavailable:
        return "unavailable"
    }
}
```

`SystemLanguageModel` is `Observable`, so a SwiftUI view reading `availability` updates when the model finishes downloading. `SystemLanguageModel(useCase: .contentTagging)` selects the tagging-tuned model; `guardrails: .permissiveContentTransformations` relaxes guardrails for transforming user-provided text (summarize, rewrite).

Custom adapters (`SystemLanguageModel.Adapter`, `SystemLanguageModel(adapter:)`) are deprecated since 26.4 and unavailable once the deployment target is iOS / macOS / visionOS 27.0 (`'Adapter' is unavailable in iOS`). Do not start new adapter work.

## Sessions, instructions, responses

```swift
import FoundationModels

func summarize(_ text: String) async throws -> String {
    let session = LanguageModelSession(instructions: """
        You are a concise editor. Return only the rewritten text.
        """)
    let response = try await session.respond(to: "Summarize in two sentences: \(text)")
    print(response.usage.input.totalTokenCount, response.usage.output.totalTokenCount)
    return response.content
}
```

- `respond` returns `LanguageModelSession.Response<Content>`; read `.content`. `usage` (27.0) reports input, cached and output tokens.
- A session keeps its `transcript` across turns. Reuse it for follow-ups; create a new one for unrelated tasks.
- One request at a time per session: a second `respond` while one is in flight throws `LanguageModelSession.Error.concurrentRequests` (verified). Check `isResponding` or use one session per concurrent task.
- `prewarm(promptPrefix:)` loads the model ahead of a likely request (on view appear, not at launch).
- Instructions are fixed for a plain session. For instructions that change with app state, use dynamic instructions (below).
- `@InstructionsBuilder` / `@PromptBuilder` closures assemble text conditionally: `LanguageModelSession { "Base rules."; if compact { "Be brief." } }` and `session.respond { "Summarize:"; for line in lines { line } }`.

## Guided generation

`@Generable` constrains decoding to a Swift type; no JSON parsing.

```swift
import FoundationModels

@Generable
struct Recipe {
    var name: String
    @Guide(description: "Ingredients with quantities", .maximumCount(12))
    var ingredients: [String]
    @Guide(.range(5...180))
    var minutes: Int
    var difficulty: Difficulty
}

@Generable
enum Difficulty { case easy, medium, hard }

func suggestRecipe(for request: String) async throws -> Recipe {
    let session = LanguageModelSession()
    return try await session.respond(to: request, generating: Recipe.self).content
}
```

- Guides: numbers `.range`, `.minimum`, `.maximum`; strings `.anyOf`, `.constant`, or a `Regex` (`@Guide(/[A-Z]{3}/)`); arrays `.count`, `.minimumCount`, `.maximumCount`, `.element(...)`.
- Built-in `Generable` types: `String`, `Int`, `Double`, `Float`, `Decimal`, `Bool`, arrays and optionals of `Generable`, plus `GeneratedContent` and `ImageReference`.
- Property names and `@Guide` descriptions are sent as a schema and cost tokens. Start without guides; add them where output is wrong. Properties are generated in declaration order, so put fields that inform others first.
- For enum-like classification use a `@Generable enum` with `GenerationOptions(samplingMode: .greedy)`.
- Shape known only at runtime: build a `DynamicGenerationSchema`, wrap it in `GenerationSchema(root:dependencies:)`, call `respond(to:schema:)` and read `GeneratedContent` with `value(_:forProperty:)`.

## Streaming

```swift
import FoundationModels

@Generable
struct TripPlan {
    var destination: String
    var days: [String]
}

func streamPlan(onUpdate: (TripPlan.PartiallyGenerated) -> Void) async throws -> TripPlan {
    let session = LanguageModelSession()
    let stream = session.streamResponse(to: "Plan a weekend in Lisbon", generating: TripPlan.self)
    for try await snapshot in stream {
        onUpdate(snapshot.content)   // every property optional, filling in over time
    }
    return try await stream.collect().content
}
```

Each snapshot is the whole value so far, not a delta - assign it, do not append. Text streams (`streamResponse(to:)`) yield the full `String` so far. `collect()` returns the final `Response`, also after the loop has consumed the stream (verified).

## Tools

A tool is a type conforming to `Tool`; there is no tool macro. `Arguments` must be a `@Generable` struct (primitive `Arguments` types are explicitly unavailable); `Output` is any `PromptRepresentable`, usually `String`.

```swift
import FoundationModels

struct StockLookup: Tool {
    let description = "Look up the stock count for a product."

    @Generable
    struct Arguments {
        @Guide(description: "Product name")
        var product: String
    }

    func call(arguments: Arguments) async throws -> String {
        "\(arguments.product): 42 in stock"
    }
}

func askAboutStock() async throws -> String {
    let session = LanguageModelSession(tools: [StockLookup()], instructions: "Use tools for stock questions.")
    return try await session.respond(to: "How many widgets are in stock?").content
}
```

- `name` defaults to the type name (`"StockLookup"`). The requirement `call(arguments:)` is `@concurrent`: it runs off the main actor; hop to `MainActor` explicitly for UI state.
- Keep to 3-5 tools per session and short descriptions; definitions consume context.
- `GenerationOptions(toolCallingMode: .required | .allowed | .disallowed)` (27.0) forces or forbids tool use for one request.
- Errors thrown from `call` surface as `LanguageModelSession.ToolCallError` (with `tool` and `underlyingError`).
- Vision ships ready-made tools for image prompts (27.0): `OCRTool()` and `BarcodeReaderTool()` from `import Vision`.

## Image input

iOS / macOS / visionOS 27: put an `Attachment` in a prompt builder. Sources: `CGImage`, `CIImage`, `CVPixelBuffer`, an image file URL (`Attachment(imageURL:)`), and `UIImage` on iOS. The framework scales and converts; pass `orientation:` for unrotated camera frames. The on-device model accepts images (verified: it classified a solid red image correctly).

```swift
import CoreGraphics
import FoundationModels
import Vision

@Generable
enum Subject { case document, receipt, photo, screenshot }

func classify(_ image: CGImage) async throws -> Subject {
    let session = LanguageModelSession()
    return try await session.respond(generating: Subject.self, options: GenerationOptions(samplingMode: .greedy)) {
        "Classify this image."
        Attachment(image)
    }.content
}

func readText(in image: CGImage) async throws -> String {
    let session = LanguageModelSession(tools: [OCRTool()])
    return try await session.respond {
        "Extract the total amount from this receipt."
        Attachment(image).label("receipt")
    }.content
}
```

- `.label(_:)` names an attachment so tools can refer to it; a custom tool takes an `ImageReference` argument and resolves it with `reference.resolved(in: transcript)` to get a `Transcript.ImageAttachment` (`cgImage`, `url`).
- Check `model.capabilities.contains(.vision)` before offering image features on a custom `LanguageModel`.

## Context window and options

The on-device window is 4096 tokens for everything in the session: instructions, tool schemas, `Generable` schemas, prompts, images and responses. PCC has 32K.

```swift
import FoundationModels

func respondWithinBudget(_ prompt: String, session: LanguageModelSession) async throws -> String {
    let model = SystemLanguageModel.default
    let used = try await model.tokenCount(for: session.transcript)
    let next = try await model.tokenCount(for: prompt)
    let target = used + next > model.contextSize * 3 / 4
        ? LanguageModelSession(model: model, transcript: Transcript(entries: session.transcript.suffix(2)))
        : session
    let options = GenerationOptions(samplingMode: .greedy, temperature: 0.2, maximumResponseTokens: 400)
    return try await target.respond(to: prompt, options: options).content
}
```

- `tokenCount(for:)` (iOS / macOS 26.4+) measures prompts, instructions, tools, schemas or transcript entries; `contextSize` is the model maximum. The Foundation Models instrument and `#Playground` show live usage.
- No API trims the transcript for you on a plain session. Recover from overflow by starting a session from a condensed `Transcript` (first instructions entry plus the last turns, or a model-written summary). With profiles, `.historyTransform { Array($0.suffix(20)) }` trims what each request sends.
- `GenerationOptions(samplingMode:temperature:maximumResponseTokens:)`: `samplingMode` replaced the deprecated `sampling:` label in 27.0 (back-deployed). Use `maximumResponseTokens` only as a runaway cap; truncation yields broken output. Ask for length in the prompt or cap arrays with `.maximumCount`.
- `ContextOptions(includeSchemaInPrompt:reasoningLevel:)` (27.0) is a per-request `contextOptions:` argument to `respond`. Despite the name it is not a trimming policy: it controls whether the `Generable` schema text is included and the reasoning level (`.light`, `.moderate`, `.deep`, `.custom(String)`) on models that reason (PCC, not the on-device model).
- `transcriptErrorHandlingPolicy` (27.0): `.revertTranscript` or `.preserveTranscript` on a failed request.

## Dynamic instructions and profiles

iOS / macOS / visionOS / watchOS 27. A `DynamicInstructions` body (SwiftUI-style result builder of `Instructions`, tools and nested dynamic instructions) is re-evaluated before every request, so instructions and tools follow app state. A `LanguageModelSession.DynamicProfile` picks exactly one `Profile` (instructions plus model, temperature, reasoning level, history transform, lifecycle hooks) per request.

```swift
import FoundationModels
import Observation

@MainActor
@Observable
final class EditorState {
    var formal = false
}

@MainActor
struct StyleInstructions: @MainActor DynamicInstructions {
    let state: EditorState

    var body: some DynamicInstructions {
        Instructions { "Reply in one sentence." }
        if state.formal {
            Instructions { "Use a formal tone and no contractions." }
        } else {
            Instructions { "Use a casual tone." }
            StockLookup()
        }
    }
}

@MainActor
struct EditorProfile: @MainActor LanguageModelSession.DynamicProfile {
    let state: EditorState

    var body: some LanguageModelSession.DynamicProfile {
        if state.formal {
            Profile { StyleInstructions(state: state) }
                .temperature(0.1)
        } else {
            Profile { StyleInstructions(state: state) }
                .temperature(0.9)
                .historyTransform { Array($0.suffix(10)) }
                .onToolCall { call in print("tool:", call.toolName) }
        }
    }
}

@MainActor
func makeEditorSession(state: EditorState) -> LanguageModelSession {
    LanguageModelSession(profile: EditorProfile(state: state))
}
```

- The state class is non-`Sendable` unless it is main-actor isolated, and the session initializers take the profile as `sending`: without the `@MainActor` annotations and the `@MainActor` (isolated) conformances above, a target without default `MainActor` isolation fails with `sending value of non-Sendable type 'EditorProfile' risks causing data races`. In a default-`MainActor` target the annotations are implied. The isolated conformances ran correctly at runtime.
- Hold changing state in a reference type (an `@Observable` class): the structs are evaluated per request, and flipping `state.formal` between two `respond` calls changed the reply style in testing.
- Use if/else or switch in a `DynamicProfile` body; two parallel `Profile`s fail to compile (`The body of a 'DynamicProfile' must evaluate to a single active profile`).
- Modifier precedence: call-site `GenerationOptions` > the innermost profile modifier > outer dynamic-profile modifiers. Lifecycle hooks (`onPrompt`, `onResponse`, `onToolCall`, `onToolOutput`, `onActivate`, `onDeactivate`) accumulate; throwing from one fails the request.
- `LanguageModelSession(dynamicInstructions:)` takes dynamic instructions without a profile. `@SessionProperty(\.history) var history` reads the session history from inside instructions, profiles and tools; `@SessionPropertyEntry` defines custom keys.
- Append conditional content after the stable part (as above) so the prompt prefix stays cacheable.

## Errors (27.0 error types)

`LanguageModelSession.GenerationError` is deprecated in the 27.0 SDKs. Apple: "Apps built with Xcode 26 will continue to catch this error until you rebuild with Xcode 27. You must update to Xcode 27 to catch the new error types before submitting your app." Built with Xcode 27 and run on 27.0, overflow threw `LanguageModelError.contextSizeExceeded` (verified); a stale `catch GenerationError.exceededContextWindowSize` no longer matches.

| 26.x `GenerationError` case | 27.0 replacement |
|---|---|
| `exceededContextWindowSize` | `LanguageModelError.contextSizeExceeded` (carries `contextSize`, `tokenCount`) |
| `guardrailViolation`, `refusal`, `rateLimited`, `unsupportedLanguageOrLocale` | same-named `LanguageModelError` cases |
| `unsupportedGuide` | `LanguageModelError.unsupportedGenerationGuide` |
| `decodingFailure` | `GeneratedContent.ParsingError` |
| `assetsUnavailable` | `SystemLanguageModel.Error.assetsUnavailable` |
| `concurrentRequests` | `LanguageModelSession.Error.concurrentRequests` |

New in `LanguageModelError`: `unsupportedCapability`, `unsupportedTranscriptContent`, `timeout`. `LanguageModelSession.Error` adds `transcriptMutationWhileResponding`. With a deployment target below 27, catch both families:

```swift
import FoundationModels

enum AIFailure: Error {
    case tooLong, blocked, busy, unavailable, other(String)
}

func classifyFailure(_ error: any Error) -> AIFailure {
    if #available(iOS 27, macOS 27, visionOS 27, *) {
        switch error {
        case LanguageModelError.contextSizeExceeded: return .tooLong
        case LanguageModelError.guardrailViolation, LanguageModelError.refusal: return .blocked
        case LanguageModelError.rateLimited, LanguageModelSession.Error.concurrentRequests: return .busy
        case SystemLanguageModel.Error.assetsUnavailable: return .unavailable
        default: break
        }
    }
    if let legacy = error as? LanguageModelSession.GenerationError {
        switch legacy {
        case .exceededContextWindowSize: return .tooLong
        case .guardrailViolation, .refusal: return .blocked
        case .rateLimited, .concurrentRequests: return .busy
        case .assetsUnavailable: return .unavailable
        default: return .other(legacy.localizedDescription)
        }
    }
    return .other(error.localizedDescription)
}
```

The legacy branch produces deprecation warnings when the deployment target is 27.0; drop it once you require 27. Do not blindly retry `guardrailViolation` or `refusal` - reword or decline. `LanguageModelError.Refusal.explanation` asks the model why it refused.

## Private Cloud Compute

```swift
import FoundationModels

@available(iOS 27, macOS 27, visionOS 27, watchOS 27, *)
func analyzeLongDocument(_ text: String) async throws -> String {
    let pcc = PrivateCloudComputeLanguageModel()
    guard pcc.isAvailable, !pcc.quotaUsage.isLimitReached else {
        let session = LanguageModelSession(model: SystemLanguageModel.default)
        return try await session.respond(to: "Summarize briefly: \(text.prefix(6000))").content
    }
    let session = LanguageModelSession(model: pcc)
    do {
        return try await session.respond(
            to: "Analyze this document: \(text)",
            contextOptions: ContextOptions(reasoningLevel: .moderate)
        ).content
    } catch PrivateCloudComputeLanguageModel.Error.quotaLimitReached(let info) {
        return "Daily limit reached; resets \(info.resetDate?.formatted() ?? "later")"
    } catch PrivateCloudComputeLanguageModel.Error.networkFailure {
        let session = LanguageModelSession(model: SystemLanguageModel.default)
        return try await session.respond(to: "Summarize briefly: \(text.prefix(6000))").content
    }
}
```

- Same session API: only the `model:` argument changes. Requires the managed entitlement `com.apple.developer.private-cloud-compute`, granted on request (see [Adding server-side intelligence with Private Cloud Compute](https://developer.apple.com/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute)).
- Without the entitlement, `availability` still reported `.available` on macOS 27.2, and `respond` failed with an untyped `NSError` in domain `FoundationModels.LanguageModelError`, code -1 - not one of the typed cases. Check the entitlement first when PCC "fails for no reason".
- Availability reasons: `.deviceNotEligible`, `.systemNotReady`. It needs the network; fall back to the on-device model on `networkFailure` / `serviceUnavailable`.
- Quota is per person per day. Show `quotaUsage.status` (`.belowLimit(info)` with `info.isApproachingLimit`, or `.limitReached`) in the UI and call `quotaUsage.limitIncreaseSuggestion?.show()` to present the system upgrade (iCloud+) sheet. The Xcode scheme can simulate approaching and exceeded limits.
- `contextSize` and `supportedLanguages` are `async throws` on the PCC model (they ask the server).

## Other models: LanguageModel protocol and Core AI

`SystemLanguageModel` and `PrivateCloudComputeLanguageModel` both conform to `LanguageModel` (27.0), and any conforming type works with `LanguageModelSession(model:)`, tools, guided generation and profiles. A conformance declares `capabilities` (`.vision`, `.guidedGeneration`, `.reasoning`, `.toolCalling`) and an `Executor: LanguageModelExecutor` that translates a `LanguageModelExecutorGenerationRequest` and streams events into a `LanguageModelExecutorGenerationChannel`. Apple recommends shipping providers as Swift packages; see the WWDC26 session [Bring an LLM provider to the Foundation Models framework](https://developer.apple.com/videos/play/wwdc2026/339).

Core AI (`import CoreAI`, all Apple platforms 27.0) is the separate framework for running your own models on CPU, GPU and Neural Engine from `.aimodel` files produced by Apple's `coreai-torch` / `coreai-optimization` Python tools. SDK surface: `AIModel(contentsOf:options:)`, `AIModel.specialize(contentsOf:options:cache:cachePolicy:)`, `AIModelCache` (`.default`, or `init?(appGroup:)`), `SpecializationOptions` / `ComputeUnitKind`, `AIModel.loadFunction(named:)` returning an `InferenceFunction`, and `NDArray`. For language models, the open-source [coreai-models](https://github.com/apple/coreai-models) package provides `CoreAILanguageModel(resourcesAt:)`, a `LanguageModel` you pass straight to `LanguageModelSession(model:)` - see [Running a Core AI model in a Foundation Models session](https://developer.apple.com/documentation/foundationmodels/running-a-core-ai-model-in-a-foundation-models-session). Background inference uses the `com.apple.developer.background-tasks.continued-processing.inference` entitlement ([Core AI](https://developer.apple.com/documentation/coreai)).

Unverified: `CoreAILanguageModel` and the `coreai-models` package were not built here; the Core AI types above are from the 27.0 SDK interface only.
