# Skill Card

## Description

effect-ts is a comprehensive Effect-TS development guide for TypeScript, focused on Effect v4 (recommended) with full v3 support: typed errors, fibers, Context/Layers, Scope, Schedule, streams, Schema, observability, HTTP, Config, SQL, CLI, RPC, STM, and Effect AI, plus exhaustive wrong-vs-correct API tables that prevent hallucinated Effect code.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

TypeScript developers building, debugging, reviewing, or generating Effect code in either v3 or v4 codebases. Triggers whenever code imports from effect, @effect/platform, @effect/ai, or @effect/sql, or the user works with Effect concepts like Context, Layer, or Schema.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: Optional
Credential Type(s): OPENAI_API_KEY only for running the Effect AI examples with the OpenAI provider; the rest of the skill needs no credentials. Declared as an optional envVar in the openclaw block.

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Works against the effect npm package (and companion packages such as @effect/platform-node) already present in the user's project; no CLIs or MCP servers are required.

## Known Risks and Mitigations

Risk: Effect v4 is in beta with occasional API churn (e.g. the ServiceMap -> Context rename); guidance verified against effect@4.0.0-beta.92 can drift from newer betas, producing code that fails to compile.

Mitigation: The skill instructs pinning an exact beta version, detecting the installed version from package.json before writing code, and verifying every API against the live API index (tim-smart.github.io/effect-io-ai) or source docs.

Risk: Mixing v3 and v4 syntax in one codebase - a failure mode the skill itself documents as common in LLM output - can introduce subtle runtime and type errors.

Mitigation: Version detection is step 1 of the core workflow; the wrong-vs-correct tables and the agent quality checklist (imports, yield*, error channels, run* only at edges) are applied before code is output.

## References

- Effect v4 source and migration guides: https://github.com/Effect-TS/effect-smol (tracked in metadata.upstream as effect@4.0.0-beta.92)
- Effect v3 docs: https://effect.website/docs; API index: https://tim-smart.github.io/effect-io-ai/
- Source: https://github.com/tenequm/skills/tree/main/skills/effect-ts

## Skill Output

Output type(s): Effect-TS application code, code reviews and corrections of existing Effect code, and design guidance (error modeling, layer wiring, concurrency).

Output format: TypeScript code with imports shown in every example; Markdown explanations.

Output parameters: Code follows the skill's output standards (Effect.gen or Effect.fn style, typed E channel, run* only at program edges, return yield* for generator errors).

Other properties: 20+ references/ files loaded per task via progressive disclosure; an evals/ directory ships with the source repository for benchmarking.

## Skill Version

0.6.2

## Ethical Considerations

The skill generates and reviews application code only and handles no personal data; its guardrail tables exist specifically to reduce hallucinated APIs. Users remain responsible for testing and reviewing generated code before production use.
