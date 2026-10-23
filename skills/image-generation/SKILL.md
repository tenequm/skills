---
name: image-generation
description: Generate logos, icons, illustrations and other images with the newest OpenAI, Gemini and Grok image models, with Claude as art director and SVG finisher. Use when asked to create, draw, render or compare images, or to find the latest image model.
metadata:
  version: "0.1.0"
  categories: "creative, integrations"
  topics: "image-generation, logos, gpt-image, nano-banana, grok-imagine"
  last-verified: "2026-10-23"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/image-generation
    emoji: "🎨"
---

# Image Generation

Claude cannot generate pixels: every Claude model is images-in, text-out (the
[vision docs](https://platform.claude.com/docs/en/build-with-claude/vision) say so
outright). Claude's job is the parts the image models are bad at: the brief, the
prompts, judging every output with vision, and redrawing the winner as clean SVG.

## Step 1 - find the newest model (never trust a remembered ID)

Model IDs churn monthly. The IDs below were the newest on the `last-verified` date;
re-check before any real job. Ask the key first (it answers "what can I call"), then
the docs (they answer "which one is best for what").

| Provider | What the key can call | What the docs recommend |
|---|---|---|
| OpenAI | `GET https://api.openai.com/v1/models`, filter ids on `image` | [image generation guide](https://platform.openai.com/docs/guides/image-generation) (Overview names the current models) |
| Gemini | `GET https://generativelanguage.googleapis.com/v1beta/models?pageSize=300`, filter `image\|banana` | [image generation](https://ai.google.dev/gemini-api/docs/image-generation) "Model selection", [models](https://ai.google.dev/gemini-api/docs/models) |
| xAI (Grok) | `GET https://api.x.ai/v1/models` | [Imagine overview](https://docs.x.ai/developers/model-capabilities/imagine), [pricing](https://docs.x.ai/developers/pricing) |
| OpenRouter (any of the above with one key) | `GET https://openrouter.ai/api/v1/models?output_modalities=image` | the model's page, `https://openrouter.ai/<id>` |

Snapshot at `last-verified`:

| Model | Strength | Price (1K square) |
|---|---|---|
| `gpt-image-2.5-sunburst` | most capable, best edit precision, ~28s | ~$0.053 at `quality: high` |
| `gpt-image-2.5-flare` | fast everyday default, ~18s, same token rates | same |
| `gemini-nano-banana-2.1` | Google's default, better text rendering, 1K/2K/4K, `thinkingConfig.thinkingLevel: minimal\|medium\|high` | $0.034 (1K), $0.050 (2K), +~$0.01 at high thinking |
| `gemini-3-pro-image` (Nano Banana Pro) | precise text and brand work, slightly cleaner geometry and type than 2.1 | $0.134 (1K/2K) |
| `grok-imagine-image-2.0` | xAI headline model, flat clean vector look, 1K/2K; use `quality: medium` for fine detail (`grok-imagine-image-quality` retires 2026-11-02) | $0.04-0.08 |

When one key reaches several providers, run the same brief on each and compare: the
models differ more per concept than per benchmark.

## Step 2 - call it without leaking the key

Never echo a key or pass it as an argument. Pipe it from the secret store into curl's
header-from-stdin (`-H @-`); the body comes from a file. With gopass:

```bash
gopass env --stdin <entry> -- bash -c \
  'sed "s/^/Authorization: Bearer /" | curl -s -H @- -H "Content-Type: application/json" \
   -d @req.json <endpoint> -o resp.json'
```

Gemini takes `x-goog-api-key: ` instead of `Authorization: Bearer `.

| Provider | Endpoint | Body essentials | Image in response |
|---|---|---|---|
| OpenAI | `POST /v1/images/generations` | `model`, `prompt`, `size: "1024x1024"`, `quality: low\|medium\|high\|xhigh\|max`, `background: "transparent"` + `output_format: "png"` for cut-out logos | `.data[0].b64_json` |
| Gemini (new) | `POST /v1beta/interactions` | `model`, `input: [{type:"text",text}]`, `response_format: {type:"image", aspect_ratio:"1:1", image_size:"2K"}` | `output_image.data` (base64) |
| Gemini (classic) | `POST /v1beta/models/<model>:generateContent` | `contents`, `generationConfig: {responseModalities: ["TEXT","IMAGE"], imageConfig: {aspectRatio: "1:1", imageSize: "2K"}}` | `.candidates[0].content.parts[].inlineData.data` |
| xAI | `POST https://api.x.ai/v1/images/generations` | `model`, `prompt`, `aspect_ratio: "1:1"`, `resolution: "1k"\|"2k"`, `quality: low\|medium`, `response_format: "b64_json"` (default is a temporary URL) | `.data[0].b64_json` or `.data[0].url` |
| OpenRouter | `POST https://openrouter.ai/api/v1/images` | `model`, `prompt`, `aspect_ratio`, `resolution: "1K"\|"2K"`, plus the provider's own knobs (`quality` for Grok 2.0) | `.data[0].b64_json` |

Decode: `jq -r '<path>' resp.json | base64 -d > out.png`, then check `file out.png`:
Grok and Gemini bytes arrive as JPEG even when you asked for PNG (convert with `sips -s format png` or
ImageMagick). Strip base64 out of saved responses before reading them, or one JSON
file eats the context.

## Step 3 - Claude as art director

1. **Brief once, reuse everywhere.** Who it is for, the product in one line, the vibe,
   the exact wordmark text, and 4-6 named concept directions. The same brief across
   models makes the comparison fair.
2. **Prompt per direction.** Describe shapes, not adjectives: "single continuous
   line forming a W, ending in an upward spike" beats "dynamic W". State the
   background colour, "flat vector, centered, no mockup, no extra text", and quote
   the wordmark exactly. Letterform concepts ("a W made of a line") default to an
   outlined letter. What fixed it: describe the path stroke by stroke ("falls to a low
   point, climbs, falls, spikes up"), call it "a monoline polyline, an open path with
   two loose ends, never a hollow outlined letter", and give hex colours.
3. **Look at every output** (Read the PNG). Reject on: misspelled or warped text,
   detached parts, a concept that reads as something else first, detail that dies at
   32px. Retry once with a tightened prompt naming the defect; past two retries,
   change the concept, not the wording.
4. **Run providers in parallel**, one subagent per provider, each writing
   `<nn>-<direction>-<model>.png` into its own dir, then copy all into one dir
   prefixed with the provider for side-by-side review.

## Step 4 - finish as vector (logos, icons)

A raster logo is a mock-up, not a deliverable. Claude writes SVG well: geometric
marks, exact text, brand colours, and favicon-size variants. Take the winning raster
as the reference, have Claude redraw it as hand-written SVG (paths plus a real font
or outlined text), then render both at 512px and 32px and compare. Text that must be
perfect (names, prices) always belongs in the SVG layer, never in the generated pixels.

For whole layouts, slides or prototypes rather than single images, use Claude's HTML
and SVG artifacts or Claude Design on claude.ai instead of an image model.

## Troubleshooting

| Symptom | Fix |
|---|---|
| OpenAI 403 on gpt-image | org needs [API Organization Verification](https://help.openai.com/en/articles/10910291-api-organization-verification) |
| OpenAI `moderation_blocked` | rephrase the flagged part; never auto-retry the same prompt |
| Gemini returns text only | missing image modality / `response_format`, or the model id is not an image model |
| Wordmark keeps misspelling | shorter text, quote it, put it on its own line in the prompt; or drop text and add it in SVG |
| Model id 404 | it rotated: redo Step 1 |
