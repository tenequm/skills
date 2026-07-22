# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.2] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format
- metadata.openclaw block (emoji, homepage) for ClawHub display

## [0.3.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.3.0] - 2026-07-01

### Changed
- Refreshed version pins: vite 8.0.16->8.1.2, @vitejs/plugin-react 6.0.2->6.0.3,
  tailwindcss 4.3.0->4.3.2, @biomejs/biome 2.4.16->2.5.2, vitest 4.1.8->4.1.9,
  hono 4.12.25->4.12.27, shadcn CLI table 4.11.0->4.12.0 (metadata.upstream + Version targets + reference intros).
- Biome: `linter.rules.recommended` is deprecated in favor of `linter.rules.preset` (Biome 2.5);
  updated both canonical config examples (SKILL.md + biome.md) to `"preset": "recommended"` and noted `biome migrate`.
- Vite: HMR WebSocket options moved from `server.hmr.*` to `server.ws.*`; corrected the HMR
  troubleshooting entry to `server.ws.clientPort` and noted the deprecation/auto-sync.
- TypeScript: reframed the tsgo/TS 7 section - TS 7.0 is now RC (~10x faster, targeted for stable
  "within the next month"), with `@typescript/typescript6`/`tsc6` side-by-side install and
  `--checkers`/`--builders`/`--singleThreaded` parallelism flags.

### Added
- Vite 8.1: WASM ESM integration (stable direct `.wasm` imports), experimental Bundled Dev Mode
  (`experimental.bundledDev`) and Chunk Import Map (`build.chunkImportMap`), Lightning CSS being
  evaluated as the next-major default CSS transformer.
- React: Partial Pre-rendering (`prerender`/`resume` APIs, 19.2) added to the newer-surface list.
- Biome: `--reporter=concise` (token-saving agent reporter), read-only `--watch` mode,
  `formatter.delimiterSpacing`, and `biome upgrade`.
- shadcn 4.12: chat-interface components + `@shadcn/react` headless package, `scroll-fade`/`shimmer`
  utilities, and `add` inspection flags (`--dry-run`/`--diff`/`--view`).
- Vite caveat: `resolve.tsconfigPaths: true` does not follow tsconfig project references (solution-style
  configs) - use an explicit `resolve.alias` there.
- Tailwind footgun: a utility referencing a token not mapped in `@theme`/`@theme inline` emits no CSS and no error.

### Security
- Bumped Hono pin to 4.12.27, covering two SSR advisories: `hono/jsx` cross-request context
  disclosure (GHSA-hvrm-45r6-mjfj) and `hono/css` `cx()` XSS escaping bypass (GHSA-w62v-xxxg-mg59).

Verified against: vite@8.1.2, @vitejs/plugin-react@6.0.3, tailwindcss@4.3.2, @biomejs/biome@2.5.2, vitest@4.1.9, hono@4.12.27

## [0.2.0] - 2026-06-09

### Added
- references/hono.md - comprehensive Hono 4.12 reference: mental model, routing, Context,
  HonoRequest, middleware (built-in + `createMiddleware` + chained type inference), validation
  (`hono/validator`, `@hono/zod-validator`, Standard Schema), end-to-end type-safe RPC (`hc`,
  status-code inference, larger-app chaining, `hcWithType` IDE-perf fix), OpenAPI
  (`@hono/zod-openapi`), error handling (`HTTPException`/`onError`), helpers (cookie, streaming/SSE,
  JWT sign/verify/decode, context-storage `getContext`, factory), realtime WebSocket
  (`upgradeWebSocket` + RPC `$ws`), auth middleware (basic/bearer/jwt), server-side JSX,
  static files across runtimes, multi-runtime deployment (Workers/Node/Bun/Deno), and testing.
  Includes a prominent pointer to Hono's `llms-full.txt`/`llms.txt` as the authoritative
  long-tail source, plus a categorized resource/link section.
- SKILL.md: Hono added to the stack overview, references list, and version-targets table; new
  cross-cutting rule on the Hono RPC seam (version match, `strict: true`, status codes, no
  `c.notFound()` on RPC routes).
- references/shadcn.md: documented the `search`/`list` command - new `-t, --type` and `--json`
  flags, optional `[registries]` arg (searches all registries in `components.json` when omitted),
  and the 4.11 switch of default output from JSON to human-readable.

### Changed
- Repositioned the skill from "frontend" to full-stack TypeScript: description and intro now
  cover the Hono backend/edge layer and its RPC integration with the React frontend.
- Bumped documented shadcn CLI version 4.10.0 -> 4.11.0 (SKILL.md version table + shadcn.md).

Verified against: hono@4.12.25, @hono/node-server@2.0.4, @hono/zod-validator@0.8.0, @hono/zod-openapi@1.4.0

## [0.1.0] - 2026-06-05

### Added
- Initial release. Merges the former `vite`, `react-typescript`, `shadcn-tailwind`, and `biome`
  skills into one cohesive TypeScript frontend skill, plus net-new Vitest coverage.
- SKILL.md cross-cutting layer: stack overview, version targets, the rules that bite at the
  seams between tools, and one end-to-end working setup (vite.config.ts, tsconfig.json,
  biome.json, styles.css, a canonical component).
- references/vite.md - Vite 8 (Rolldown default), dev server, code splitting, build, deployment.
- references/react.md - React 19.2 patterns and the React Compiler 1.0.
- references/typescript.md - TypeScript 6.0 config and patterns.
- references/tailwind.md - Tailwind CSS v4.3 CSS-first config and theming.
- references/shadcn.md - shadcn/ui CLI 4.10 and component authoring.
- references/biome.md - Biome 2.4 lint/format/imports.
- references/vitest.md - Vitest 4 testing (net-new; not present in any source skill).

### Notes
- Retargets the former Vite content from Vite 7 to Vite 8: Rolldown is the single default
  bundler, object-form `manualChunks` removed in favor of Rolldown `codeSplitting`,
  `build.rollupOptions` -> `build.rolldownOptions`, default minifiers Oxc (JS) and
  Lightning CSS, browser target chrome111/edge111/firefox114/safari16.4, React Compiler wired
  via `reactCompilerPreset` + `@rolldown/plugin-babel`.
- TypeScript content advanced from 5.9 to 6.0 (strict default-on, `types: []`, module/target
  default shifts, `baseUrl` deprecated, `erasableSyntaxOnly`, tsgo note).
- shadcn CLI corrected from 3.0 to 4.10 (`create` is an alias of `init`, unified `radix-ui`
  import, GitHub source registries, new styles). Tailwind advanced 4.2 -> 4.3. Biome 2.4.13 -> 2.4.16.

Verified against: vite@8.0.16, @vitejs/plugin-react@6.0.2, react@19.2.7, typescript@6.0.3, tailwindcss@4.3.0, @biomejs/biome@2.4.16, vitest@4.1.8, babel-plugin-react-compiler@1.0.0, class-variance-authority@0.7.1
