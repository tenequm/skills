# Skill Card

## Description

typescript-dev provides a coherent full-stack TypeScript setup and cross-cutting rules for Vite 8, React 19 (with the React Compiler), TypeScript 6.0, Tailwind CSS v4, shadcn/ui, Biome, Vitest, and Hono 4. It covers how these tools wire together, the sharp edges at their seams, and per-tool deep-dive references.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

Developers setting up or working in a TypeScript project: configuring Vite and tsconfig, writing React components, styling with Tailwind/shadcn, linting with Biome, testing with Vitest, or building a Hono API with an end-to-end type-safe RPC client. Best used when the project targets the modern stack versions the skill pins.

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Instructs the agent to use standard JavaScript tooling in the target project: a package manager (pnpm/npm), Vite, Biome, Vitest, and the shadcn/ui CLI. No MCP servers or external services.

## Known Risks and Mitigations

Risk: The skill pins concrete tool versions (Vite 8.1.x, React 19.2.x, TypeScript 6.0.x, etc.); applying its config verbatim to a project on older majors (Vite 7, Tailwind v3, Biome 1.x) can break builds, since several rules are version-specific (no tailwind.config.js, files.includes key, plugin-react v6 Babel wiring).

Mitigation: Check the project's installed versions against the skill's version-targets table before applying config; the skill's version table makes the mismatch visible, and generated configs should be reviewed in a diff before commit.

Risk: Guidance such as deleting leftover tailwind.config.js or rewriting tsconfig defaults modifies existing project files and could discard intentional legacy configuration.

Mitigation: Apply config migrations as reviewable edits (version control diff), not blind overwrites; keep the old file contents until the build passes.

## References

- Vite (https://vite.dev/guide/), React 19.2 (https://react.dev), TypeScript 6.0, Tailwind CSS v4 (https://tailwindcss.com/docs), shadcn/ui (https://ui.shadcn.com/docs), Biome (https://biomejs.dev/), Vitest, Hono 4 - tracked in metadata.upstream (vite@8.1.2, react@19.2.7, typescript@6.0.3, tailwindcss@4.3.2, @biomejs/biome@2.5.2, vitest@4.1.9, hono@4.12.27, and others)
- Source: https://github.com/tenequm/skills/tree/main/skills/typescript-dev

## Skill Output

Output type(s): Project configuration files (vite.config.ts, tsconfig.json, biome.json, CSS theme files), React/TypeScript source code, Hono API code, and explanations of stack behavior.

Output format: Code in TypeScript, TSX, JSON/JSONC, and CSS; Markdown explanations.

Output parameters: Not applicable

Other properties: SKILL.md is the cross-cutting layer; eight references/ files hold per-tool depth and are loaded on demand.

## Skill Version

0.3.2

## Ethical Considerations

The skill produces development tooling guidance and code only; it handles no personal data. Users remain responsible for reviewing generated configuration and code before shipping it.
