# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
